import contextlib
import http.client
import io
import json
import threading
import unittest
from http.server import HTTPServer

from studyforge.cli import main, parser, request_from_args
from studyforge.gui import make_handler


class FakeController:
    def __init__(self):
        self.requests = []

    def handle(self, command_name, **params):
        self.requests.append((command_name, params))
        if command_name == "fail":
            raise ValueError("Invalid request")
        return {"id": "saved", "action": command_name, "params": params}


class CLITests(unittest.TestCase):
    def test_every_feature_has_a_shared_controller_request(self):
        cases = [
            (["material", "import", "notes.md", "--course", "c"], "import_materials"),
            (["summarize", "--course", "c"], "summarize"),
            (["concepts", "--course", "c"], "concepts"),
            (["ask", "--course", "c", "why?"], "ask"),
            (["plan", "--course", "c", "--goal", "learn", "--deadline", "2027-01-01"], "plan_create"),
            (["flashcards", "--course", "c"], "flashcards"),
            (["quiz", "--course", "c"], "quiz"),
            (["grade", "--quiz-id", "q", "--answers", '{"i":"answer"}'], "grade"),
            (["adapt", "--course", "c"], "adapt"),
            (["progress", "--course", "c"], "progress"),
            (["reminder", "--plan-id", "p"], "reminder_schedule"),
            (["session", "--course", "c", "--goal", "learn"], "session_start"),
        ]
        for argv, expected in cases:
            with self.subTest(command=argv[0]):
                action, params = request_from_args(parser().parse_args(argv))
                self.assertEqual(action, expected)
                self.assertNotIn("db", params)

    def test_plan_start_date_is_explicit_or_omitted(self):
        base = ["plan", "--course", "c", "--goal", "learn", "--deadline", "2027-01-10"]
        action, params = request_from_args(parser().parse_args(base))
        self.assertEqual(action, "plan_create")
        self.assertNotIn("start_date", params)
        _, blank_params = request_from_args(parser().parse_args(base + ["--start-date", ""]))
        self.assertNotIn("start_date", blank_params)
        action, params = request_from_args(parser().parse_args(base + ["--start-date", "2027-01-05"]))
        self.assertEqual(params["start_date"], "2027-01-05")

    def test_session_control_preserves_nested_action_parameter(self):
        controller = FakeController()
        with contextlib.redirect_stdout(io.StringIO()):
            code = main(["session-action", "--session-id", "session-1", "pause"], controller)
        self.assertEqual(code, 0)
        self.assertEqual(controller.requests, [("session_action", {"session_id": "session-1", "action": "pause"})])

    def test_cli_calls_controller_and_reports_json_errors(self):
        controller = FakeController()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main(["ask", "--course", "c", "question"], controller), 0)
        self.assertEqual(controller.requests, [("ask", {"course": "c", "question": "question"})])
        self.assertEqual(json.loads(out.getvalue())["id"], "saved")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(main(["grade", "--quiz-id", "q", "--answers", "{"], controller), 1)
        self.assertIn("error", json.loads(err.getvalue()))


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.controller = FakeController()
        self.server = HTTPServer(("127.0.0.1", 0), make_handler(self.controller, "test-token"))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = http.client.HTTPConnection("127.0.0.1", self.server.server_port)

    def tearDown(self):
        self.client.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, method, path, body=None, headers=None):
        self.client.request(method, path, body, headers or {})
        response = self.client.getresponse()
        return response.status, response.read(), response.getheaders()

    def test_assets_and_bootstrap(self):
        status, body, headers = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"StudyForge", body)
        self.assertIn("Content-Security-Policy", dict(headers))
        status, body, _ = self.request("GET", "/api/bootstrap")
        self.assertEqual(json.loads(body)["token"], "test-token")
        self.assertEqual(self.request("GET", "/../core.py")[0], 404)

    def test_shared_controller_and_validation(self):
        headers = {"Content-Type": "application/json", "X-StudyForge-Token": "test-token"}
        status, body, _ = self.request("POST", "/api/action", json.dumps({"action": "ask", "params": {"course": "c", "question": "why"}}), headers)
        self.assertEqual(status, 200)
        self.assertEqual(self.controller.requests[0], ("ask", {"course": "c", "question": "why"}))
        self.assertEqual(json.loads(body)["result"]["id"], "saved")
        self.assertEqual(self.request("POST", "/api/action", "{", headers)[0], 400)
        self.assertEqual(self.request("POST", "/api/action", json.dumps({"action": "fail"}), headers)[0], 400)

    def test_cross_site_and_rebinding_requests_rejected(self):
        payload = '{"action":"ask"}'
        self.assertEqual(self.request("POST", "/api/action", payload, {"Content-Type": "application/json"})[0], 403)
        headers = {"Content-Type": "application/json", "X-StudyForge-Token": "test-token", "Origin": "https://example.com"}
        self.assertEqual(self.request("POST", "/api/action", payload, headers)[0], 403)
        self.assertEqual(self.request("GET", "/api/bootstrap", headers={"Host": "evil.example"})[0], 403)
        self.assertEqual(self.controller.requests, [])


if __name__ == "__main__":
    unittest.main()
