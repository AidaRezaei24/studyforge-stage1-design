"""Scoped accounting tested only with synthetic, temporary Codex metadata."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/export_codex_usage.py"
SPEC = importlib.util.spec_from_file_location("codex_usage_exporter", SCRIPT)
exporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exporter)


class UsageAccountingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "codex"
        self.home.mkdir()
        self.database = self.home / "state_5.sqlite"
        self.output = Path(self.temp.name) / "usage.json"
        with sqlite3.connect(self.database) as connection:
            connection.execute("CREATE TABLE threads (id TEXT PRIMARY KEY, source TEXT, model TEXT, tokens_used, created_at, cwd TEXT, title TEXT)")
        self.add_thread("root", 100)
        self.add_thread("child", 40, parent="root", model="model-b")
        self.add_thread("grandchild", 5, parent="child")
        # Same workspace and title never establish accounting scope.
        self.add_thread("unrelated", 900000)

    def add_thread(self, thread_id, tokens, parent=None, model="model-a"):
        source = json.dumps({"subagent": {"thread_spawn": {"parent_thread_id": parent,
                             "depth": 1, "agent_path": "/root/private-agent"}}}) if parent else "vscode"
        with sqlite3.connect(self.database) as connection:
            connection.execute("INSERT INTO threads VALUES (?,?,?,?,?,?,?)",
                               (thread_id, source, model, tokens, 1700000000,
                                "/private/workspace", "private conversation title"))

    def test_scoped_descendants_deduplicated_with_model_totals_and_private_ids(self):
        result = exporter.export_usage(self.database, ["root", "root", "child"])
        self.assertEqual(145, result["total_tokens"])
        self.assertEqual(3, result["thread_count"])
        self.assertEqual({"root": 2, "delegate": 1}, result["role_counts"])
        self.assertEqual({"model-a": {"thread_count": 2, "total_tokens": 105},
                          "model-b": {"thread_count": 1, "total_tokens": 40}}, result["by_model"])
        rows = {row["thread_hash"]: row for row in result["threads"]}
        self.assertNotIn(exporter.thread_hash("unrelated"), rows)
        self.assertEqual(exporter.thread_hash("child"),
                         rows[exporter.thread_hash("grandchild")]["parent_thread_hash"])
        self.assertIsNone(rows[exporter.thread_hash("root")]["parent_thread_hash"])
        self.assertEqual("2023-11-14T22:13:20+00:00", rows[exporter.thread_hash("root")]["created_at_utc"])
        encoded = json.dumps(result)
        for private in ["unrelated", "grandchild", "private conversation title", "/private/workspace"]:
            self.assertNotIn(private, encoded)
        self.assertTrue(result["snapshot_at_utc"].endswith("+00:00"))

    def test_missing_roots_and_invalid_selected_counters_write_no_output(self):
        for invalid in [-1, 1.5, "private-invalid-counter"]:
            with self.subTest(counter=invalid):
                with sqlite3.connect(self.database) as connection:
                    connection.execute("UPDATE threads SET tokens_used=? WHERE id='child'", (invalid,))
                for roots in [["root"], ["root", "missing-private-id"]]:
                    args = ["--codex-home", str(self.home), "--output", str(self.output)]
                    for root in roots:
                        args.extend(["--root-thread", root])
                    errors = io.StringIO()
                    with contextlib.redirect_stderr(errors):
                        self.assertEqual(1, exporter.main(args))
                    self.assertFalse(self.output.exists())
                    self.assertNotIn("private", errors.getvalue())
        with self.assertRaises(ValueError):
            exporter.export_usage(self.database, [])

    def test_spawn_source_forms_and_explicit_subtree_do_not_include_ancestors(self):
        self.assertEqual("root", exporter.parent_thread('{"thread_spawn":{"parent_thread_id":"root"}}'))
        for source in ["vscode", "null", "[]", '{"subagent":null}',
                       '{"subagent":{"thread_spawn":{"parent_thread_id":123}}}']:
            with self.subTest(source=source):
                self.assertIsNone(exporter.parent_thread(source))
        result = exporter.export_usage(self.database, ["child"])
        self.assertEqual(45, result["total_tokens"])
        self.assertEqual({"root": 1, "delegate": 1}, result["role_counts"])
        selected = {row["thread_hash"]: row for row in result["threads"]}
        self.assertNotIn(exporter.thread_hash("root"), selected)
        self.assertIsNone(selected[exporter.thread_hash("child")]["parent_thread_hash"])

    def test_unrelated_invalid_counter_is_ignored_and_database_is_read_only(self):
        with sqlite3.connect(self.database) as connection:
            connection.execute("UPDATE threads SET tokens_used=-1 WHERE id='unrelated'")
        before = self.database.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, exporter.main(["--codex-home", str(self.home), "--root-thread", "root",
                                               "--output", str(self.output)]))
        self.assertEqual(145, json.loads(self.output.read_text())["total_tokens"])
        self.assertEqual(before, self.database.read_bytes())

    def test_rejects_output_inside_codex_home(self):
        auth = self.home / "auth.json"
        auth.write_text("private credentials must survive")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(1, exporter.main(["--codex-home", str(self.home), "--root-thread", "root",
                                               "--output", str(auth)]))
        self.assertEqual("private credentials must survive", auth.read_text())

    def test_requires_explicit_root_and_does_not_create_missing_database(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                exporter.main(["--codex-home", str(self.home), "--output", str(self.output)])
        self.assertEqual(2, raised.exception.code)
        missing = Path(self.temp.name) / "missing.sqlite"
        with self.assertRaises(ValueError):
            exporter.export_usage(missing, ["root"])
        self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
