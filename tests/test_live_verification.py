"""Live-runner safeguards checked without configuration access or network calls."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from studyforge.model import ModelError


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/verify_live.py"
SPEC = importlib.util.spec_from_file_location("studyforge_live_verification_runner", SCRIPT)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class LiveRunnerSafetyTests(unittest.TestCase):
    def test_first_provider_failure_stops_after_one_call_and_redacts_evidence(self):
        class FailingAdapter:
            model = "offline-safety-test-model"
            usage = {"input_tokens": 0, "output_tokens": 0}
            def __init__(self):
                self.calls = 0
            def generate(self, *args, **kwargs):
                self.calls += 1
                raise ModelError("private-provider-error and sk-test-private-value")
        # Bypass construction of the real adapter, which is the only component
        # that would load .env. Exercise the real instrumentation and controller.
        gateway = runner.InstrumentedGateway.__new__(runner.InstrumentedGateway)
        gateway.adapter = FailingAdapter()
        gateway.calls = []
        gateway.stopped = False
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "failure.json"
            with patch.object(runner, "InstrumentedGateway", return_value=gateway), \
                    patch("studyforge.model.load_local_config", side_effect=AssertionError("Configuration must not be read")), \
                    patch("urllib.request.urlopen", side_effect=AssertionError("Network must not be used")), \
                    contextlib.redirect_stdout(io.StringIO()):
                code = runner.main(["--output", str(output)])
            evidence_text = output.read_text()
            evidence = json.loads(evidence_text)
        self.assertEqual(code, 1)
        self.assertEqual(gateway.adapter.calls, 1)
        self.assertTrue(gateway.stopped)
        self.assertEqual(len(gateway.calls), 1)
        self.assertEqual(evidence["status"], "FAIL")
        self.assertEqual(evidence["steps"][-1]["feature"], "F02")
        self.assertEqual(evidence["steps"][-1]["status"], "FAIL")
        self.assertNotIn("private-provider-error", evidence_text)
        self.assertNotIn("sk-test-private-value", evidence_text)

    def test_existing_database_is_refused_before_adapter_or_configuration(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "existing.sqlite3"
            database.write_bytes(b"existing-user-work-must-survive")
            output = Path(temporary) / "not-created.json"
            with patch.object(runner, "InstrumentedGateway", side_effect=AssertionError("Adapter must not be created")) as factory, \
                    patch("studyforge.model.load_local_config", side_effect=AssertionError("Configuration must not be read")), \
                    patch("urllib.request.urlopen", side_effect=AssertionError("Network must not be used")), \
                    contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    runner.main(["--output", str(output), "--db", str(database)])
            self.assertEqual(raised.exception.code, 2)
            factory.assert_not_called()
            self.assertEqual(database.read_bytes(), b"existing-user-work-must-survive")
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
