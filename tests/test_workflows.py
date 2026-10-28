"""Full feature journeys with real persistence; only the remote model is a test double."""
import contextlib
from datetime import date, timedelta
import http.client
from http.server import HTTPServer
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest

from studyforge.cli import main, parser, request_from_args
from studyforge.core import SQLiteRepository, StudyAgentFacade, StudyController
from studyforge.gui import make_handler
from studyforge.learning import LearningError, LearningService
from studyforge.model import InvalidModelOutput, ModelError


class EvidenceModel:
    """Schema-valid responses exclusively for deterministic integration tests."""
    def __init__(self):
        self.requests = []

    def generate(self, task, evidence, payload):
        self.requests.append((task, evidence, payload))
        self_citations = [evidence[0]["id"]] if evidence else []
        if task == "summary":
            return {"text": "Observer notifies subscribers; Strategy exchanges algorithms.", "citations": self_citations}
        if task == "answer":
            return {"text": "Observer notifies subscribers on state changes.", "citations": self_citations, "confidence": "high"}
        if task == "concepts":
            return {"nodes": [{"name": name, "confidence": .9, "citations": self_citations} for name in ["Observer", "Strategy"]],
                    "edges": [{"source": "Observer", "target": "Strategy", "type": "related-to", "confidence": .8, "citations": self_citations}]}
        if task == "flashcards":
            return {"cards": [{"front": f"Explain Observer case {i + 1}.", "back": "It notifies subscribers.", "topic": "Observer", "citations": self_citations} for i in range(payload["count"])]}
        if task == "quiz":
            return {"items": [{"question": f"Explain Observer case {i + 1}.", "type": "choice" if i % 2 == 0 else "free",
                               "options": ["Observer", "Adapter"], "answer": "Observer", "rubric": "Identify notification of subscribers.",
                               "topic": "Observer", "citations": self_citations} for i in range(payload["count"])]}
        if task == "plan":
            return {"topics": ["Observer", "Strategy"]}
        if task == "grade":
            return {"score": .8, "confidence": .9, "feedback": "Names subscriber notification; misses details."}
        raise AssertionError(f"Unexpected model task {task}")


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "workspace.db"
        self.repo = SQLiteRepository(self.db)
        self.addCleanup(lambda: self.repo.close())
        self.model = EvidenceModel()
        self.controller = StudyController(StudyAgentFacade(self.repo, self.model))
        self.material = Path(self.temp.name) / "patterns.md"
        self.material.write_text("Observer notifies subscribers when state changes. Strategy defines interchangeable algorithms. Adapter translates interfaces.")

    def cli(self, argv):
        output, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            code = main(argv, self.controller)
        self.assertEqual(code, 0, error.getvalue())
        return json.loads(output.getvalue())

    def journey(self, invoke):
        course = invoke(["course", "create", "Design course"])["id"]
        scope = ["--course", course]
        imported = invoke(["material", "import", str(self.material), *scope])
        self.assertEqual(len(imported["imported"]), 1)
        material = imported["imported"][0]
        summary = invoke(["summarize", *scope, "--material", material["id"]])
        graph = invoke(["concepts", *scope])
        answer = invoke(["ask", *scope, "How does Observer notify subscribers?"])
        deadline = (date.today() + timedelta(days=2)).isoformat()
        plan = invoke(["plan", *scope, "--goal", "Observer and Strategy", "--deadline", deadline, "--approve"])
        self.assertEqual(plan["status"], "approved")
        deck = invoke(["flashcards", *scope, "--topic", "Observer", "--count", "2"])
        due = invoke(["due-cards", *scope, "--deck-id", deck["id"]])
        self.assertEqual(len(due["cards"]), 2)
        for _ in range(2):
            invoke(["review", "--card-id", deck["cards"][0]["id"], "--rating", "0"])
        quiz = invoke(["quiz", *scope, "--topic", "Observer", "--count", "2"])
        answers = {item["id"]: "Observer" for item in quiz["items"]}
        attempt = invoke(["grade", "--quiz-id", quiz["id"], "--attempt-id", "submission-one", "--answers", json.dumps(answers)])
        self.assertEqual(attempt["score"], .9)
        self.assertEqual([r["confidence"] for r in attempt["results"]], [1, .9])
        adaptation = invoke(["adapt", *scope, "--minutes", "10", "--confirm"])
        self.assertEqual(adaptation["status"], "generated")
        self.assertEqual(adaptation["practice"]["difficulty"], "intermediate")
        progress = invoke(["progress", *scope])
        self.assertEqual(progress["topics"][0]["sample_size"], 4)
        self.assertEqual(progress["topics"][0]["mastery"], .45)
        reminders = invoke(["reminder", "--plan-id", plan["id"], "--confirm"])
        self.assertEqual(len(reminders["reminders"]), 2)
        session = invoke(["session", *scope, "--goal", "Observer", "--minutes", "10"])
        invoke(["session-action", "--session-id", session["id"], "pause"])
        invoke(["session-action", "--session-id", session["id"], "resume"])
        for _ in range(3):
            session = invoke(["session-action", "--session-id", session["id"], "advance"])
        self.assertEqual(session["state"], "completed")
        self.assertEqual([s["step"] for s in session["results"]], ["learn", "practice", "review"])
        for artifact in [summary, answer, graph, deck, quiz, adaptation["practice"]]:
            allowed = {e["id"] for e in artifact["evidence"]}
            rows = artifact.get("cards", artifact.get("items", artifact.get("nodes", [artifact])))
            self.assertTrue(all(set(row["citations"]) <= allowed for row in rows))
            self.assertTrue(all(e["location"].startswith("patterns.md") for e in artifact["evidence"]))
        return course, material, session, attempt

    def assert_reopened(self, snapshots):
        course, material, session, attempt = snapshots
        self.repo.close()
        self.repo = SQLiteRepository(self.db)
        self.assertEqual(self.repo.get(material["id"], "material")["chunks"], material["chunks"])
        self.assertEqual(self.repo.get(session["id"], "session")["state"], "completed")
        self.assertEqual(self.repo.get(attempt["id"], "attempt")["rubric_snapshot"], attempt["rubric_snapshot"])
        fresh = StudyController(StudyAgentFacade(self.repo, self.model))
        self.assertEqual(fresh.handle("progress", course=course)["completed_sessions"], 1)

    def test_cli_full_feature_journey_and_reopen(self):
        self.assert_reopened(self.journey(self.cli))

    def test_http_full_feature_journey_and_reopen(self):
        server = HTTPServer(("127.0.0.1", 0), make_handler(self.controller, "workflow-token"))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        client = http.client.HTTPConnection("127.0.0.1", server.server_port)
        def invoke(argv):
            action, params = request_from_args(parser().parse_args(argv))
            client.request("POST", "/api/action", json.dumps({"action": action, "params": params}),
                           {"Content-Type": "application/json", "X-StudyForge-Token": "workflow-token"})
            response = client.getresponse()
            value = json.loads(response.read())
            self.assertEqual(response.status, 200, value)
            return value["result"]
        try:
            snapshots = self.journey(invoke)
        finally:
            client.close()
            server.shutdown()
            server.server_close()
            thread.join()
        self.assert_reopened(snapshots)

    def test_malformed_json_retries_once_but_configuration_does_not(self):
        course = self.controller.handle("course_create", name="Course")["id"]
        self.controller.handle("import_materials", course=course, paths=[str(self.material)])
        class BrokenModel:
            def __init__(self, error):
                self.calls, self.error = 0, error
            def generate(self, *args, **kwargs):
                self.calls += 1
                raise self.error
        for error, count in [(InvalidModelOutput("malformed JSON"), 2), (ModelError("missing key"), 1)]:
            gateway = BrokenModel(error)
            learning = LearningService(self.repo, gateway, self.controller.facade.events)
            with self.assertRaises(ValueError):
                learning.summarize(course)
            self.assertEqual(gateway.calls, count)
        self.assertEqual(self.repo.list("summary", course), [])


if __name__ == "__main__":
    unittest.main()
