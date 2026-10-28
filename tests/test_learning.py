import copy
from pathlib import Path
import tempfile
import unittest
import zipfile

from studyforge.learning import LearningError, LearningService, RetrievalTool


class Repository:
    def __init__(self):
        self.records = []

    def save(self, kind, course, data):
        record = dict(copy.deepcopy(data), kind=kind, course=course)
        record.setdefault("id", str(len(self.records)))
        self.records = [r for r in self.records if r["id"] != record["id"]]
        self.records.append(record)
        return record

    def get(self, record_id, kind=None):
        return next(r for r in self.records if r["id"] == record_id and (kind is None or r["kind"] == kind))

    def list(self, kind, course=None):
        return [r for r in self.records if r["kind"] == kind and (course is None or r["course"] == course)]


class Events:
    def __init__(self):
        self.events = []

    def publish(self, name, payload):
        self.events.append((name, payload))


class Model:
    def __init__(self, responses):
        self.responses, self.calls = responses, []

    def generate(self, task, evidence, payload):
        self.calls.append((task, evidence, payload))
        value = self.responses[min(len(self.calls) - 1, len(self.responses) - 1)]
        return copy.deepcopy(value(evidence) if callable(value) else value)


class LearningTests(unittest.TestCase):
    def setUp(self):
        self.repo, self.events = Repository(), Events()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "patterns.md"
        self.path.write_text("Strategy selects interchangeable algorithms. Observer notifies subscribers of events. " * 30)
        self.model = Model([])
        self.learning = LearningService(self.repo, self.model, self.events)
        self.material = self.learning.import_materials("design", [self.path])["imported"][0]

    def test_import_isolates_failure_and_duplicate_without_losing_success(self):
        other = Path(self.temp.name) / "notes.txt"
        other.write_text("Adapter translates interfaces.")
        report = self.learning.import_materials("design", [self.path, other, other.with_suffix(".bad")])
        self.assertEqual([len(report[k]) for k in ("imported", "duplicates", "errors")], [1, 1, 1])
        self.assertEqual(len(self.repo.list("material", "design")), 2)
        self.assertEqual(len(self.events.events), 2)
        self.assertTrue(all(c["location"] for c in self.material["chunks"]))

    def test_retrieval_is_scoped_ranked_and_reports_missing_evidence(self):
        other = Path(self.temp.name) / "other.txt"
        other.write_text("Secret astronomy content.")
        self.learning.import_materials("astronomy", [other])
        evidence = RetrievalTool(self.repo).execute("design", "Strategy")
        self.assertTrue(evidence)
        self.assertTrue(all("Strategy" in e["text"] for e in evidence))
        self.assertEqual(RetrievalTool(self.repo).execute("design", "astronomy"), [])
        with self.assertRaisesRegex(LearningError, "Insufficient"):
            self.learning.ask("design", "astronomy")
        self.assertEqual(self.model.calls, [])

    def test_invalid_citations_retry_once_and_do_not_persist(self):
        self.model.responses = [{"text": "bad", "citations": ["another-course:1"]}]
        with self.assertRaisesRegex(LearningError, "one retry"):
            self.learning.summarize("design")
        self.assertEqual(len(self.model.calls), 2)
        self.assertEqual(self.repo.list("summary", "design"), [])

    def test_summary_persists_resolvable_evidence(self):
        self.model.responses = [lambda e: {"text": "Strategy varies algorithms.", "citations": [e[0]["id"]]}]
        result = self.learning.summarize("design", self.material["id"], "detailed")
        self.assertEqual(result["detail"], "detailed")
        self.assertIn(result["citations"][0], {e["id"] for e in result["evidence"]})

    def test_answer_loads_prior_memory_and_remains_scoped(self):
        self.model.responses = [lambda e: {"text": "It selects algorithms.", "citations": [e[0]["id"]], "confidence": "high"}]
        self.learning.ask("design", "Strategy algorithms")
        self.learning.ask("design", "Strategy selects")
        self.assertEqual(self.model.calls[-1][2]["memory"][0]["question"], "Strategy algorithms")
        self.assertEqual(len(self.repo.list("conversation", "design")), 2)

    def test_graph_merges_names_and_rejects_invalid_relations(self):
        def graph(e):
            citation = [e[0]["id"]]
            return {"nodes": [{"name": "Strategy", "confidence": 0.9, "citations": citation},
                              {"name": " strategy ", "confidence": 0.9, "citations": citation},
                              {"name": "Algorithm", "confidence": 0.9, "citations": citation}],
                    "edges": [{"source": "strategy", "target": "Algorithm", "type": "related-to", "confidence": 0.8, "citations": citation}]}
        self.model.responses = [graph]
        result = self.learning.concepts("design")
        self.assertEqual(len(result["nodes"]), 2)
        self.assertEqual(result["edges"][0]["source"], "Strategy")
        broken = graph(self.material["chunks"])
        broken["edges"][0]["target"] = "Imaginary"
        self.model.responses = [broken]
        with self.assertRaises(LearningError):
            self.learning.concepts("design")

    def test_flashcards_are_reviewable_and_duplicate_cards_rejected(self):
        self.model.responses = [lambda e: {"cards": [{"front": "What is Strategy?", "back": "Interchangeable algorithms", "topic": "Strategy", "citations": [e[0]["id"]]}]}]
        deck = self.learning.flashcards("design", "Strategy", 1)
        self.assertTrue(deck["cards"][0]["id"])
        self.assertEqual(deck["cards"][0]["interval"], 0)
        bad = dict(deck)
        bad["cards"] = deck["cards"] * 2
        self.model.responses = [bad]
        with self.assertRaisesRegex(LearningError, "Duplicate"):
            self.learning.flashcards("design", "Strategy", 2)

    def test_quiz_rejects_wrong_choice_key_and_accepts_rubric(self):
        def question(e):
            return {"items": [{"question": "Which varies algorithms?", "type": "choice", "options": ["Strategy", "Observer"], "answer": "Adapter", "topic": "Strategy", "citations": [e[0]["id"]]}]}
        self.model.responses = [question]
        with self.assertRaisesRegex(LearningError, "unique option"):
            self.learning.quiz("design", "Strategy", 1)
        item = question(self.material["chunks"])["items"][0]
        item.update(type="free", answer="Strategy", rubric="Names interchangeable algorithms.")
        self.model.responses = [{"items": [item]}]
        self.assertTrue(self.learning.quiz("design", "Strategy", 1)["items"][0]["id"])

    def test_invalid_counts_never_call_model(self):
        for count in [0, 21, True, "2"]:
            with self.assertRaises(LearningError):
                self.learning.quiz("design", count=count)
        self.assertEqual(self.model.calls, [])

    def test_docx_extraction_and_empty_file_failure(self):
        docx = Path(self.temp.name) / "course.docx"
        with zipfile.ZipFile(docx, "w") as archive:
            archive.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Facade simplifies interfaces.</w:t></w:r></w:p></w:body></w:document>')
        empty = Path(self.temp.name) / "empty.txt"
        empty.write_text("   ")
        report = self.learning.import_materials("design", [docx, empty])
        self.assertIn("Facade simplifies", report["imported"][0]["chunks"][0]["text"])
        self.assertIn("No extractable text", report["errors"][0]["error"])

    def test_card_edit_reject_and_due_queue(self):
        self.model.responses = [lambda e: {"cards": [{"front": "What is Strategy?", "back": "Interchangeable algorithms", "topic": "Strategy", "citations": [e[0]["id"]]}]}]
        deck = self.learning.flashcards("design", "Strategy", 1)
        card_id = deck["cards"][0]["id"]
        self.assertEqual(len(self.learning.due_queue("design")["cards"]), 1)
        updated = self.learning.card_update("design", deck["id"], card_id, back="An algorithm family.", reject=True)
        self.assertTrue(updated["cards"][0]["user_edited"])
        self.assertEqual(self.learning.due_queue("design")["cards"], [])
        with self.assertRaisesRegex(LearningError, "belong"):
            self.learning.card_update("other-course", deck["id"], card_id, reject=False)

    def test_schema_rejects_nonobject_generated_items(self):
        self.model.responses = [{"cards": ["not a card"]}]
        with self.assertRaisesRegex(LearningError, "JSON objects"):
            self.learning.flashcards("design", "Strategy", 1)

    def test_import_rolls_back_failed_observer_with_real_repository(self):
        from studyforge.core import EventBus, SQLiteRepository
        repo, events = SQLiteRepository(":memory:"), EventBus()
        self.addCleanup(repo.close)
        def fail(name, payload):
            raise RuntimeError("Observer failed")
        events.subscribe("MaterialIndexed", fail)
        learning = LearningService(repo, self.model, events)
        report = learning.import_materials("design", [self.path])
        self.assertEqual(report["imported"], [])
        self.assertEqual(repo.list("material", "design"), [])
        self.assertIn("Observer failed", report["errors"][0]["error"])


if __name__ == "__main__":
    unittest.main()
