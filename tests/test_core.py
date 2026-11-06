import io
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import urllib.error

from studyforge.core import (SQLiteRepository, StudyAgentFacade, StudyController,
                             ReviewScheduler, CalendarAdapter, EventBus)
from studyforge.model import OpenAIModelAdapter, ModelError


class FakeModel:
    def generate(self, task, evidence, payload):
        if task == 'plan':
            return {'topics': ['Observer', 'Strategy']}
        if task == 'grade':
            return {'score': .5, 'confidence': .4, 'feedback': 'Partially addresses rubric.'}
        raise ValueError('No fake response for ' + task)


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.repo = SQLiteRepository(':memory:')
        self.facade = StudyAgentFacade(self.repo, FakeModel())
        self.controller = StudyController(self.facade)
        self.course = self.controller.handle('course_create', name='Software Design')['id']
        self.facade.learning.retrieval.execute = lambda *a, **k: [{'id': 'c1', 'text': 'Observer notifies subscribers.', 'location': 'p1'}]

    def tearDown(self):
        self.repo.close()

    def test_transaction_rolls_back_all_records(self):
        with self.assertRaises(ValueError):
            with self.repo.transaction():
                self.repo.save('plan', self.course, {'id': 'not-saved'})
                raise ValueError('fail')
        self.assertEqual([], self.repo.list('plan', self.course))

    def test_records_cannot_change_course(self):
        item = self.repo.save('quiz', self.course, {'items': []})
        with self.assertRaises(ValueError):
            self.repo.save('quiz', 'another', item)

    def test_scope_and_actions_are_validated(self):
        with self.assertRaises(ValueError):
            self.controller.handle('progress', course='missing')
        with self.assertRaises(ValueError):
            self.controller.handle('__getattribute__')

    def test_plan_approval_replacement_and_infeasibility(self):
        deadline = (date.today() + timedelta(days=2)).isoformat()
        plan = self.facade.plan_create(self.course, 'patterns', deadline, approve=True)
        second = self.facade.plan_create(self.course, 'patterns', deadline)
        with self.assertRaises(ValueError):
            self.facade.plan_approve(second['id'])
        self.facade.plan_approve(second['id'], replace=True)
        self.assertEqual('replaced', self.repo.get(plan['id'])['status'])
        with self.assertRaisesRegex(ValueError, 'Infeasible'):
            self.facade.plan_create(self.course, 'patterns', date.today().isoformat(), 25, 25)
        with self.assertRaises(ValueError):
            self.facade.plan_create(self.course, 'patterns', (date.today() - timedelta(days=1)).isoformat())

    def test_review_intervals_and_observer_progress(self):
        self.repo.save('deck', self.course, {'cards': [{'id': 'card1', 'front': 'x', 'back': 'y', 'topic': 'Observer'}]})
        first = self.facade.review('card1', 0)
        second = self.facade.review('card1', 3)
        self.assertEqual(1, first['interval'])
        self.assertEqual(3, second['interval'])
        topic = self.facade.progress(self.course)['topics'][0]
        self.assertEqual(2, topic['sample_size'])
        self.assertEqual(.5, topic['mastery'])
        with self.assertRaises(ValueError):
            ReviewScheduler.schedule_next({}, True)

    def test_grading_scores_and_low_confidence_exclusion(self):
        quiz = self.repo.save('quiz', self.course, {'items': [
            {'id': 'a', 'type': 'choice', 'question': 'Choose', 'answer': 'A', 'topic': 'Observer'},
            {'id': 'b', 'type': 'free', 'question': 'Explain', 'answer': 'rubric', 'topic': 'Observer'}]})
        attempt = self.facade.grade(quiz['id'], {'a': 'A', 'b': 'partial'}, 'attempt1')
        self.assertEqual(.75, attempt['score'])
        self.assertTrue(attempt['results'][1]['needs_review'])
        self.assertEqual(1, self.facade.progress(self.course)['topics'][0]['sample_size'])
        with self.assertRaises(ValueError):
            self.facade.grade(quiz['id'], {'a': 'A', 'b': 'x'}, 'attempt1')
        with self.assertRaises(ValueError):
            self.facade.grade(quiz['id'], {'a': 'A'})

    def test_adaptation_requires_evidence_and_confirmation(self):
        self.assertEqual('insufficient_evidence', self.facade.adapt(self.course)['status'])
        self.repo.save('deck', self.course, {'cards': [{'id': 'c', 'topic': 'Observer'}]})
        self.facade.review('c', 0)
        self.facade.review('c', 0)
        proposal = self.facade.adapt(self.course)
        self.assertEqual('proposed', proposal['status'])
        self.assertNotIn('practice', proposal)
        self.facade.learning.quiz = lambda *args, **kwargs: {'id': 'practice'}
        self.assertEqual('generated', self.facade.adapt(self.course, confirm=True)['status'])

    def test_schedule_confirmation_conflict_and_idempotency(self):
        plan = self.facade.plan_create(self.course, 'patterns', (date.today() + timedelta(days=2)).isoformat(), approve=True)
        proposal = self.facade.schedule(plan['id'])
        self.assertEqual('confirmation_required', proposal['status'])
        self.assertEqual([], self.repo.list('reminder', self.course))
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'plan.ics'
            confirmed = self.facade.schedule(plan['id'], confirm=True, export_path=path)
            self.facade.schedule(plan['id'], confirm=True)
            self.assertEqual(2, len(self.repo.list('reminder', self.course)))
            text = path.read_text()
            self.assertIn('BEGIN:VALARM', text)
            self.assertIn('DTSTART:', text)
            self.assertEqual(2, text.count('BEGIN:VEVENT'))
        other = self.facade.plan_create(self.course, 'patterns', (date.today() + timedelta(days=2)).isoformat(), approve=True, replace=True)
        with self.assertRaisesRegex(ValueError, 'conflicts'):
            self.facade.schedule(other['id'], confirm=True)
        with self.assertRaises(ValueError):
            self.facade.schedule(other['id'], timezone='Bad/Zone')

    def test_sessions_pause_recover_and_terminal_state(self):
        session = self.facade.session_start(self.course, 'Observer', 10)
        session = self.controller.handle('session_action', session_id=session['id'], action='pause')
        with self.assertRaises(ValueError):
            self.facade.session_action(session['id'], 'advance')
        self.facade.session_action(session['id'], 'resume')
        # Fake model rejects generation: failed activity checkpoints a recoverable pause.
        failed = self.facade.session_action(session['id'], 'advance')
        self.assertEqual('paused', failed['state'])
        self.assertEqual([], failed['results'])
        self.facade.session_action(session['id'], 'resume')
        self.facade.orchestrator.tools.tools['explain'] = lambda **kw: {'text': 'An explanation'}
        learned = self.facade.session_action(session['id'], 'advance')
        self.assertEqual('practice', learned['state'])
        self.assertEqual(1, len(learned['results']))
        self.facade.session_action(session['id'], 'skip')
        done = self.facade.session_action(session['id'], 'advance')
        self.assertEqual('completed', done['state'])
        with self.assertRaises(ValueError):
            self.facade.session_action(session['id'], 'resume')

    def test_expired_session_obeys_state_and_never_runs_tools(self):
        session = self.facade.session_start(self.course, 'Observer', 5)
        session['started_at'] = (datetime.now(timezone.utc) - timedelta(minutes=6)).isoformat()
        self.repo.save('session', self.course, session)
        completed = self.controller.handle('session_action', session_id=session['id'], action='advance')
        self.assertEqual('completed', completed['state'])
        self.assertEqual([], completed['results'])
        with self.assertRaises(ValueError):
            self.controller.handle('session_action', session_id=session['id'], action='advance')

    def test_rejected_cards_do_not_change_progress(self):
        self.repo.save('deck', self.course, {'cards': [{'id': 'reject', 'topic': 'Observer', 'rejected': True}]})
        with self.assertRaisesRegex(ValueError, 'Rejected'):
            self.facade.review('reject', 3)
        self.assertEqual([], self.facade.progress(self.course)['topics'])

    def test_broad_exam_goal_can_plan_existing_course_material(self):
        self.repo.save('material', self.course, {'chunks': [
            {'id': 'c', 'text': 'Observer notifies subscribers. Strategy encapsulates algorithms.',
             'material_id': 'm', 'location': 'notes, text'}]})
        from studyforge.learning import RetrievalTool
        self.facade.learning.retrieval = RetrievalTool(self.repo)
        plan = self.facade.plan_create(self.course, 'Prepare for midterm',
                                       (date.today() + timedelta(days=2)).isoformat())
        self.assertEqual('draft', plan['status'])
        self.assertEqual('c', plan['evidence'][0]['id'])

    def test_known_prerequisites_constrain_planner(self):
        self.repo.save('graph', self.course, {'nodes': [], 'edges': [
            {'source': 'Strategy', 'target': 'Observer', 'type': 'prerequisite'}]})
        with self.assertRaisesRegex(ValueError, 'prerequisite'):
            self.facade.plan_create(self.course, 'patterns', (date.today() + timedelta(days=2)).isoformat())
        self.assertEqual([], self.repo.list('plan', self.course))

    def test_cross_course_calendar_conflicts(self):
        end = (date.today() + timedelta(days=2)).isoformat()
        plan = self.facade.plan_create(self.course, 'patterns', end, approve=True)
        self.facade.schedule(plan['id'], confirm=True)
        other_course = self.facade.course_create('Another course')['id']
        other = self.facade.plan_create(other_course, 'patterns', end, approve=True)
        with self.assertRaisesRegex(ValueError, 'conflicts'):
            self.facade.schedule(other['id'], confirm=True)

    def test_calendar_injection_escaped(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'a.ics'
            CalendarAdapter.export([{'id':'safe', 'title':'Study\nEND:VEVENT',
                                     'start':'2026-11-20T10:00:00-05:00', 'end':'2026-11-20T10:25:00-05:00'}],path)
            self.assertIn('SUMMARY:Study\\nEND:VEVENT', path.read_text())


class AdapterTests(unittest.TestCase):
    def setUp(self):
        # Contract tests must not inspect or depend on the developer's local key.
        config = patch('studyforge.model.load_local_config')
        config.start()
        self.addCleanup(config.stop)

    def test_live_request_contract_without_network(self):
        captured = []
        def opener(request, timeout):
            captured.append(json.loads(request.data))
            return io.BytesIO(json.dumps({'status':'completed', 'usage':{'input_tokens': 8,'output_tokens':4},
                'output':[{'type':'message','content':[{'type':'output_text','text':'{"text":"ok"}'}]}]}).encode())
        adapter = OpenAIModelAdapter(api_key='test-only', opener=opener)
        self.assertEqual({'text':'ok'}, adapter.generate('ask', [], {}))
        self.assertEqual({'type':'json_object'}, captured[0]['text']['format'])
        self.assertFalse(captured[0]['store'])
        self.assertEqual(8, adapter.usage['input_tokens'])

    def test_json_mode_instruction_is_in_input_with_structure_preserved(self):
        captured = []
        def opener(request, timeout):
            body = json.loads(request.data)
            captured.append(body)
            if 'json' not in body['input'].casefold():
                raise urllib.error.HTTPError('url', 400, 'JSON instruction missing from input', None, None)
            return io.BytesIO(json.dumps({'status': 'completed', 'output': [
                {'type': 'message', 'content': [{'type': 'output_text', 'text': '{"text":"ok"}'}]}
            ]}).encode())
        adapter = OpenAIModelAdapter(api_key='test-only', opener=opener)
        evidence = [{'id': 'chunk-1', 'text': 'Strategy encapsulates algorithms.'}]
        payload = {'question': 'What does Strategy do?'}
        for supplied_evidence, supplied_payload in [([], {}), (evidence, payload)]:
            with self.subTest(evidence=supplied_evidence):
                adapter.generate('answer', supplied_evidence, supplied_payload)
                body = captured[-1]
                self.assertEqual({'type': 'json_object'}, body['text']['format'])
                self.assertIn('json', body['input'].casefold())
                self.assertEqual({
                    'output_instruction': 'Return one JSON object matching the task schema.',
                    'task': 'answer', 'evidence': supplied_evidence, 'request': supplied_payload,
                }, json.loads(body['input']))
        self.assertEqual({'question': 'What does Strategy do?'}, payload)
        self.assertEqual([{'id': 'chunk-1', 'text': 'Strategy encapsulates algorithms.'}], evidence)

    def test_exhausted_credit_is_actionable_without_exposing_provider_details(self):
        for identifiers in [{'code': 'credit_balance_exhausted'}, {'type': 'insufficient_quota'}]:
            with self.subTest(identifiers=identifiers):
                calls = []
                def opener(*args, **kwargs):
                    calls.append(True)
                    body = {'error': {**identifiers, 'message': 'provider-private-message test-private-key'}}
                    raise urllib.error.HTTPError('url', 429, 'private-reason', None,
                                                 io.BytesIO(json.dumps(body).encode()))
                with self.assertRaises(ModelError) as raised:
                    OpenAIModelAdapter(api_key='test-private-key', opener=opener).generate('answer', [], {})
                self.assertEqual('OpenAI API credit is exhausted. Add API credits in your OpenAI billing settings, then retry.',
                                 str(raised.exception))
                self.assertNotIn('test-private-key', str(raised.exception))
                self.assertNotIn('provider-private-message', str(raised.exception))
                self.assertNotIn('private-reason', str(raised.exception))
                self.assertEqual(1, len(calls))

    def test_other_http_errors_and_unreadable_bodies_use_safe_fallback(self):
        cases = [(429, None), (429, b'not-json-private-message'),
                 (429, b'{"error":null}'), (429, b'{"error":{"code":"rate_limit_exceeded"}}'),
                 (401, b'{"error":{"type":"insufficient_quota"}}'),
                 (429, b'{"error":{"type":"' + b'x' * 16_384 + b'"}}')]
        for status, body in cases:
            with self.subTest(status=status, body_present=body is not None):
                def opener(*args, **kwargs):
                    raise urllib.error.HTTPError('url', status, 'provider-private-message', None,
                                                 io.BytesIO(body) if body is not None else None)
                with self.assertRaises(ModelError) as raised:
                    OpenAIModelAdapter(api_key='test-private-key', opener=opener).generate('answer', [], {})
                self.assertEqual(f'LLM request failed (HTTP {status}); check local configuration or retry later.',
                                 str(raised.exception))
                self.assertNotIn('test-private-key', str(raised.exception))
                self.assertNotIn('provider-private-message', str(raised.exception))

    def test_missing_key_and_safe_http_error(self):
        with self.assertRaisesRegex(ModelError, 'OPENAI_API_KEY'):
            OpenAIModelAdapter(api_key='').generate('ask', [], {})
        def opener(*a, **k):
            raise urllib.error.HTTPError('url',401,'secret-error',None,None)
        with self.assertRaises(ModelError) as raised:
            OpenAIModelAdapter(api_key='private-value', opener=opener).generate('ask', [], {})
        self.assertNotIn('private-value', str(raised.exception))
        self.assertNotIn('secret-error', str(raised.exception))
