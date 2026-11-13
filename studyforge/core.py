"""Shared application commands, persistence, learning policies, and session orchestration."""
from collections import defaultdict
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone as tz
import json
from pathlib import Path
import sqlite3
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .model import OpenAIModelAdapter


def uid():
    return uuid.uuid4().hex


def now():
    return datetime.now(tz.utc).isoformat()


class SQLiteRepository:
    """JSON aggregates in SQLite, with nested transaction support for use cases."""
    def __init__(self, path='studyforge.db'):
        if str(path) != ':memory:':
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(path), check_same_thread=False)
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.connection.execute('CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, kind TEXT NOT NULL, course TEXT NOT NULL, data TEXT NOT NULL)')
        self.connection.execute('CREATE INDEX IF NOT EXISTS scope ON records(kind,course)')
        self.connection.commit()
        self.depth = 0

    @contextmanager
    def transaction(self):
        self.depth += 1
        try:
            yield
            if self.depth == 1:
                self.connection.commit()
        except Exception:
            if self.depth == 1:
                self.connection.rollback()
            raise
        finally:
            self.depth -= 1

    def save(self, kind, course, data):
        record = dict(data)
        record.setdefault('id', uid())
        record['course'] = course
        record.setdefault('created_at', now())
        previous = self.connection.execute('SELECT kind,course FROM records WHERE id=?', (record['id'],)).fetchone()
        if previous and previous != (kind, course):
            raise ValueError('A record cannot change its kind or course.')
        self.connection.execute('INSERT INTO records VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data',
                                (record['id'], kind, course, json.dumps(record, allow_nan=False)))
        if not self.depth:
            self.connection.commit()
        return record

    def get(self, id, kind=None):
        row = self.connection.execute('SELECT kind,data FROM records WHERE id=?', (id,)).fetchone()
        if not row or (kind and row[0] != kind):
            raise ValueError(f'{kind or "Record"} not found: {id}')
        return json.loads(row[1])

    def list(self, kind, course=None):
        query = 'SELECT data FROM records WHERE kind=?'
        args = [kind]
        if course is not None:
            query += ' AND course=?'
            args.append(course)
        return [json.loads(row[0]) for row in self.connection.execute(query + ' ORDER BY rowid', args)]

    def close(self):
        self.connection.close()


class EventBus:
    """Observer subject decouples domain changes from activity projections."""
    def __init__(self):
        self.observers = defaultdict(list)

    def subscribe(self, name, callback):
        self.observers[name].append(callback)

    def publish(self, name, payload):
        for callback in self.observers[name] + self.observers['*']:
            callback(name, payload)


class ProgressProjector:
    def __init__(self, repo):
        self.repo = repo

    def update(self, name, payload):
        self.repo.save('event', payload.get('course', ''), {'name': name, 'payload': payload})


class ProgressService:
    def __init__(self, repo):
        self.repo = repo

    def get_snapshot(self, course):
        topics = defaultdict(list)
        attempts = self.repo.list('attempt', course)
        for attempt in attempts:
            for item in attempt['results']:
                if not item.get('needs_review'):
                    topics[item['topic']].append(item['score'])
        for event in self.repo.list('event', course):
            payload = event['payload']
            if event['name'] == 'CardReviewed':
                topics[payload['topic']].append(payload['rating'] / 3)
        mastery = [{'topic': key, 'mastery': round(sum(scores) / len(scores), 3),
                    'sample_size': len(scores)} for key, scores in sorted(topics.items())]
        plans = self.repo.list('plan', course)
        sessions = self.repo.list('session', course)
        return {'course': course, 'topics': mastery, 'attempts': len(attempts),
                'completed_sessions': sum(s['state'] == 'completed' for s in sessions),
                'plans': len(plans), 'events': len(self.repo.list('event', course)),
                'as_of': now(), 'method': 'Mean accepted item scores and card ratings; evidence counts shown.'}


class ReviewScheduler:
    @staticmethod
    def schedule_next(card, rating):
        if type(rating) is not int or rating not in range(4):
            raise ValueError('Rating must be an integer from 0 (forgot) to 3 (easy).')
        interval = 1 if rating < 2 else max(1, round(max(card.get('interval', 0), 1) * (2 if rating == 2 else 3)))
        return {**card, 'interval': interval, 'due': (date.today() + timedelta(days=interval)).isoformat(),
                'last_rating': rating, 'reviews': card.get('reviews', 0) + 1}


class AssessmentService:
    def __init__(self, repo, gateway, events):
        self.repo, self.gateway, self.events = repo, gateway, events

    def grade(self, quiz_id, answers, attempt_id=None):
        quiz = self.repo.get(quiz_id, 'quiz')
        if not quiz.get('items'):
            raise ValueError('Cannot grade an empty quiz.')
        attempt_id = attempt_id or uid()
        if any(a['id'] == attempt_id for a in self.repo.list('attempt', quiz['course'])):
            raise ValueError('This attempt has already been submitted.')
        if not isinstance(answers, dict) or set(answers) != {i['id'] for i in quiz['items']}:
            raise ValueError('Submit one answer keyed by item ID for every quiz item, with no extras.')
        if any(not isinstance(a, str) or not a.strip() for a in answers.values()):
            raise ValueError('Answers must be nonempty strings.')
        results = []
        for item in quiz['items']:
            if item['type'] == 'choice':
                score = float(answers[item['id']].strip().casefold() == item['answer'].strip().casefold())
                feedback, confidence = 'Expected answer: ' + item['answer'], 1.0
            else:
                verdict = self.gateway.generate('grade', quiz.get('evidence', []), {
                    'question': item['question'], 'answer': answers[item['id']], 'rubric': item.get('rubric', item['answer']),
                    '_instructions': 'Grade only against supplied rubric. Return {score:number between 0 and 1,feedback:string,confidence:number between 0 and 1}.'})
                score, confidence = verdict.get('score'), verdict.get('confidence')
                feedback = verdict.get('feedback')
                if not all(type(n) in (int, float) and 0 <= n <= 1 for n in (score, confidence)) or not isinstance(feedback, str) or not feedback:
                    raise ValueError('The model returned an invalid grade; no attempt was saved.')
            results.append({'item_id': item['id'], 'topic': item.get('topic', 'General'), 'score': score,
                            'feedback': feedback, 'confidence': confidence, 'needs_review': confidence < .7,
                            'citations': item.get('citations', [])})
        result = self.repo.save('attempt', quiz['course'], {'id': attempt_id, 'quiz_id': quiz_id,
                    'answers': answers, 'results': results, 'score': round(sum(r['score'] for r in results) / len(results), 3),
                    'rubric_snapshot': quiz['items'], 'evidence': quiz.get('evidence', [])})
        self.events.publish('AttemptRecorded', {'course': quiz['course'], 'attempt_id': result['id']})
        return result


class CalendarAdapter:
    """Exports confirmed reminders as RFC5545 UTC events; no remote calendar credentials."""
    @staticmethod
    def export(reminders, path):
        def escape(value):
            return str(value).replace('\\', '\\\\').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,').replace('\r', '')
        lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//StudyForge//Study schedule//EN', 'CALSCALE:GREGORIAN']
        for event in reminders:
            lines += ['BEGIN:VEVENT', 'UID:' + event['id'] + '@studyforge.local',
                      'DTSTAMP:' + datetime.now(tz.utc).strftime('%Y%m%dT%H%M%SZ'),
                      'DTSTART:' + datetime.fromisoformat(event['start']).astimezone(tz.utc).strftime('%Y%m%dT%H%M%SZ'),
                      'DTEND:' + datetime.fromisoformat(event['end']).astimezone(tz.utc).strftime('%Y%m%dT%H%M%SZ'),
                      'SUMMARY:' + escape(event['title']), 'BEGIN:VALARM', 'TRIGGER:-PT10M', 'ACTION:DISPLAY',
                      'DESCRIPTION:StudyForge study reminder', 'END:VALARM', 'END:VEVENT']
        lines.append('END:VCALENDAR')
        # Fold at 75 UTF-8 octets as required by iCalendar.
        folded = []
        for line in lines:
            part = ''
            for char in line:
                if len((part + char).encode()) > 75:
                    folded.append(part)
                    part = ' '
                part += char
            folded.append(part)
        Path(path).write_bytes(('\r\n'.join(folded) + '\r\n').encode())
        return str(Path(path).resolve())


class SessionState:
    def handle(self, session, action):
        raise ValueError(f'Cannot {action} a {session["state"]} session.')


class ActiveState(SessionState):
    def handle(self, session, action):
        if action == 'pause':
            session['resume_state'], session['state'] = session['state'], 'paused'
        elif action == 'stop':
            session['state'] = 'stopped'
        elif action in {'advance', 'skip'}:
            return True
        else:
            return super().handle(session, action)
        return False


class PausedState(SessionState):
    def handle(self, session, action):
        if action == 'resume':
            session['state'] = session.pop('resume_state', 'learn')
        elif action == 'stop':
            session['state'] = 'stopped'
        else:
            return super().handle(session, action)
        return False


class TerminalState(SessionState):
    pass


class ToolRegistry:
    def __init__(self, **tools):
        self.tools = tools

    def execute(self, name, **kwargs):
        if name not in self.tools:
            raise ValueError('Unknown session tool.')
        return self.tools[name](**kwargs)


class AgentOrchestrator:
    states = {'learn': ActiveState(), 'practice': ActiveState(), 'review': ActiveState(),
              'paused': PausedState(), 'completed': TerminalState(), 'stopped': TerminalState()}

    def __init__(self, repo, learning, events):
        self.repo, self.learning, self.events = repo, learning, events
        self.tools = ToolRegistry(explain=learning.ask, practice=learning.quiz)

    def start(self, course, goal, minutes):
        if not isinstance(goal, str) or not goal.strip() or type(minutes) is not int or not 5 <= minutes <= 120:
            raise ValueError('A goal and session duration of 5-120 minutes are required.')
        self.repo.get(course, 'course')
        return self.repo.save('session', course, {'goal': goal.strip(), 'minutes': minutes, 'state': 'learn',
                              'started_at': now(), 'results': [], 'steps': ['learn', 'practice', 'review'], 'step': 0})

    def run(self, session_id, action):
        session = self.repo.get(session_id, 'session')
        execute = self.states[session['state']].handle(session, action)
        if execute and datetime.now(tz.utc) >= datetime.fromisoformat(session['started_at']) + timedelta(minutes=session['minutes']):
            session['state'] = 'completed'
            session['completion_reason'] = 'Time budget reached.'
            saved = self.repo.save('session', session['course'], session)
            self.events.publish('SessionAdvanced', {'course': session['course'], 'session_id': session_id, 'state': 'completed'})
            return saved
        if execute:
            state = session['state']
            try:
                if action == 'skip':
                    result = {'skipped': state}
                elif state == 'learn':
                    result = self.tools.execute('explain', course=session['course'], question=session['goal'])
                elif state == 'practice':
                    progress = ProgressService(self.repo).get_snapshot(session['course'])
                    weak = sorted(progress['topics'], key=lambda t: t['mastery'])
                    topic = weak[0]['topic'] if weak else session['goal']
                    difficulty = 'introductory' if weak and weak[0]['mastery'] < .4 else 'intermediate'
                    result = self.tools.execute('practice', course=session['course'], topic=topic, count=2, difficulty=difficulty)
                else:
                    result = {'summary': 'Session activities completed. Review saved explanations and submit the generated quiz for feedback.',
                              'progress': ProgressService(self.repo).get_snapshot(session['course'])}
                session['results'].append({'step': state, 'result': result})
                session['step'] += 1
                session['state'] = session['steps'][session['step']] if session['step'] < len(session['steps']) else 'completed'
                session.pop('error', None)
            except (ValueError, OSError):
                session['resume_state'], session['state'] = state, 'paused'
                session['error'] = 'Activity failed. Check model configuration or evidence, then resume and retry.'
        saved = self.repo.save('session', session['course'], session)
        self.events.publish('SessionAdvanced', {'course': session['course'], 'session_id': session_id, 'state': session['state']})
        return saved

