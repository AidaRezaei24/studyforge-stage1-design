#!/usr/bin/env python3
"""Paid live acceptance against bundled public sample data, never user workspaces.

Run explicitly: python scripts/verify_live.py --output docs/live-verification.json
Requires the local configuration documented in README. No fake model is available.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studyforge.core import SQLiteRepository, StudyAgentFacade, StudyController
from studyforge.model import InvalidModelOutput, ModelError, OpenAIModelAdapter


class InstrumentedGateway:
    def __init__(self):
        self.adapter = OpenAIModelAdapter()
        self.calls = []
        self.stopped = False

    def generate(self, task, evidence, payload):
        if self.stopped:
            raise ModelError("Live acceptance stopped after a provider or configuration failure.")
        before = dict(self.adapter.usage)
        started = time.monotonic()
        call = {"task": task, "evidence_chunks": len(evidence)}
        try:
            result = self.adapter.generate(task, evidence, payload)
            call["status"] = "PASS"
            return result
        except ModelError as error:
            call.update(status="FAIL", error_type=type(error).__name__)
            # Malformed JSON has one bounded application retry. HTTP, configuration,
            # transport, and incomplete-provider responses stop all further calls.
            self.stopped = not isinstance(error, InvalidModelOutput)
            raise
        finally:
            call["seconds"] = round(time.monotonic() - started, 3)
            call["reported_tokens"] = {key: self.adapter.usage[key] - before[key] for key in before}
            self.calls.append(call)


def excerpt(value):
    """Bound public sample outputs for a compact human-reviewable evidence file."""
    if isinstance(value, dict):
        return {key: excerpt(item) for key, item in value.items() if key not in {"memory", "rubric_snapshot"}}
    if isinstance(value, list):
        return [excerpt(item) for item in value[:12]]
    if isinstance(value, str):
        return value[:2400]
    return value


def cited(artifact):
    evidence = artifact.get("evidence", [])
    allowed = {chunk["id"] for chunk in evidence}
    assert allowed, "Generated artifact has no source evidence"
    rows = artifact.get("cards", artifact.get("items", artifact.get("nodes", [artifact])))
    rows = list(rows) + artifact.get("edges", [])
    for row in rows:
        assert row.get("citations"), "Generated item has no citations"
        assert set(row["citations"]) <= allowed, "Generated citation does not resolve"
    return artifact


def run(controller, repo, gateway, report, directory):
    def step(feature, description, operation):
        record = {"feature": feature, "check": description}
        report["steps"].append(record)
        print(f"{feature}: {description}", flush=True)
        try:
            result = operation()
            record.update(status="PASS", result=excerpt(result))
            return result
        except Exception as error:
            # No provider body, full exception, local configuration, or key is logged.
            record.update(status="FAIL", error_type=type(error).__name__,
                          message="Check failed; inspect application state and the named assertion locally.")
            raise

    def require(value, condition, message):
        assert condition, message
        return value

    course = controller.handle("course_create", name="LIVE ACCEPTANCE TEST - public design patterns")["id"]
    material = step("F01", "Import safe sample and verify traceable chunks", lambda: controller.handle(
        "import_materials", course=course, paths=[str(ROOT / "samples/design-patterns.md")]))
    assert len(material["imported"]) == 1 and not material["errors"]
    material_id = material["imported"][0]["id"]
    step("F01", "Duplicate import is detected", lambda: require(
        controller.handle("import_materials", course=course, paths=[str(ROOT / "samples/design-patterns.md")]),
        len(repo.list("material", course)) == 1, "Material must not be duplicated"))
    step("F02", "Real grounded summary and citation resolution", lambda: cited(controller.handle(
        "summarize", course=course, material=material_id, detail="concise")))
    step("F03", "Real concept graph, supported edges and confidence", lambda: cited(controller.handle("concepts", course=course)))
    step("F04", "Real answer grounded in Strategy source", lambda: cited(controller.handle(
        "ask", course=course, question="How does the Strategy pattern support interchangeable algorithms?")))
    plan = step("F05", "Generate and approve feasible seven-day plan", lambda: controller.handle(
        "plan_create", course=course, goal="Study Strategy and Observer design patterns",
        deadline=(date.today() + timedelta(days=7)).isoformat(), minutes_per_day=60, approve=True))
    assert plan["status"] == "approved" and plan["sessions"]
    deck = step("F06", "Generate two real cited flashcards", lambda: cited(controller.handle(
        "flashcards", course=course, topic="Strategy", count=2)))
    assert len(deck["cards"]) == 2
    card = deck["cards"][0]
    for review in range(2):
        step("F06", f"Synthetic learner review {review + 1}: forgot (rating 0)", lambda: controller.handle(
            "review", card_id=card["id"], rating=0))
    step("F06", "Inspect persisted spaced-review queue", lambda: controller.handle("due_queue", course=course))
    quiz = step("F07", "Generate two real source-backed quiz questions", lambda: cited(controller.handle(
        "quiz", course=course, topic="Strategy", count=2)))
    assert len(quiz["items"]) == 2

    def grade_generated(target):
        # Reference answers are deliberate synthetic test-learner inputs, not
        # an assertion that a human learner knew the correct answers.
        result = controller.handle("grade", quiz_id=target["id"],
                                   answers={item["id"]: item["answer"] for item in target["items"]})
        assert 0 <= result["score"] <= 1 and len(result["results"]) == len(target["items"])
        for item, grade in zip(target["items"], result["results"]):
            if item["type"] == "choice":
                assert grade["score"] == 1, "Objective reference answer must grade correctly"
        return result

    step("F08", "Grade generated quiz with synthetic reference-answer submission", lambda: grade_generated(quiz))
    if not any(item["type"] == "free" for item in quiz["items"]):
        # Generation may legitimately choose all objective questions. This fixture
        # specifically exercises real rubric-based model grading, transparently.
        report["manual_fixture_used"] = True
        evidence = repo.get(material_id, "material")["chunks"][:1]
        fixture = repo.save("quiz", course, {"acceptance_fixture": True, "evidence": evidence,
            "items": [{"id": "manual-free-response-acceptance", "type": "free", "topic": "Manual grading check",
                       "question": "Explain how Strategy permits interchangeable algorithms.",
                       "answer": "A context delegates to a selected strategy through a common interface, so algorithms can change without changing the context.",
                       "rubric": "Award full credit for a family of algorithms behind a common interface and delegation by a context, allowing runtime exchange without context changes.",
                       "citations": [evidence[0]["id"]]}]})
        step("F08", "Real free-response grading of labelled manual source-backed fixture", lambda: grade_generated(fixture))
    recommendation = step("F09", "Diagnose synthetic review weakness and generate real adaptive practice", lambda: controller.handle(
        "adapt", course=course, minutes=10, confirm=True))
    assert recommendation["status"] == "generated" and recommendation["sample_size"] >= 2
    cited(recommendation["practice"])
    assert recommendation["practice"]["difficulty"] == recommendation["difficulty"]
    step("F10", "Reproducible progress includes synthetic learner evidence", lambda: controller.handle("progress", course=course))
    reminders = step("F11", "Confirm conflict-checked schedule and export local calendar", lambda: controller.handle(
        "schedule", plan_id=plan["id"], start_time="18:00", confirm=True,
        export_path=str(directory / "live-acceptance.ics")))
    assert all(datetime.fromisoformat(item["start"]) > datetime.now(timezone.utc)
               for item in reminders["reminders"]), "New reminders must start in the future"
    before = len(repo.list("reminder", course))
    repeated = step("F11", "Repeated confirmation is idempotent", lambda: controller.handle(
        "schedule", plan_id=plan["id"], start_time="18:00", confirm=True))
    assert before == len(repo.list("reminder", course)) == len(plan["sessions"])
    assert len(repeated["reminders"]) == len(reminders["reminders"])
    assert "BEGIN:VEVENT" in (directory / "live-acceptance.ics").read_text()
    session = step("F12", "Start bounded study session", lambda: controller.handle(
        "session_start", course=course, goal="Explain Strategy", minutes=20))
    session_id = session["id"]
    learned = step("F12", "Execute actual retrieval and explanation tool", lambda: controller.handle(
        "session_action", session_id=session_id, action="advance"))
    assert learned["state"] == "practice", "Explanation step must succeed"
    cited(learned["results"][0]["result"])
    paused = step("F12", "Checkpoint pause", lambda: controller.handle("session_action", session_id=session_id, action="pause"))
    assert paused["state"] == "paused"
    step("F12", "Resume same persisted session", lambda: controller.handle("session_action", session_id=session_id, action="resume"))
    practiced = step("F12", "Execute adaptive practice tool", lambda: controller.handle(
        "session_action", session_id=session_id, action="advance"))
    assert practiced["state"] == "review", "Practice step must succeed"
    practice_quiz = practiced["results"][-1]["result"]
    cited(practice_quiz)
    step("F12", "Submit synthetic session-practice answers before final progress review", lambda: grade_generated(practice_quiz))
    completed = step("F12", "Complete review with current persisted progress", lambda: controller.handle(
        "session_action", session_id=session_id, action="advance"))
    assert completed["state"] == "completed" and len(completed["results"]) == 3
    assert repo.get(session_id, "session")["state"] == "completed"
    report["course_id"] = course
    report["source"] = "samples/design-patterns.md"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--db", type=Path, help="New isolated acceptance database; must not already exist")
    args = parser.parse_args(argv)
    if args.db and args.db.exists():
        parser.error("--db must name a fresh, nonexistent acceptance database; existing work is never overwritten")
    report = {"status": "RUNNING", "started_at": datetime.now(timezone.utc).isoformat(),
              "learner_data": "Synthetic acceptance inputs: two forgot card ratings and reference-answer quiz submissions. No real learner performance is claimed.",
              "scope": "Real model execution through application services; does not record GUI/CLI videos or establish semantic correctness of every model statement.",
              "manual_fixture_used": False, "steps": []}
    gateway = InstrumentedGateway()
    report["model"] = gateway.adapter.model
    with tempfile.TemporaryDirectory(prefix="studyforge-live-acceptance-") as temporary:
        directory = Path(temporary)
        database = args.db or directory / "workspace.sqlite3"
        repo = SQLiteRepository(database)
        try:
            controller = StudyController(StudyAgentFacade(repo, gateway))
            run(controller, repo, gateway, report, directory)
            report["status"] = "PASS"
        except Exception as error:
            if report["steps"] and report["steps"][-1]["status"] == "PASS":
                report["steps"][-1].update(status="FAIL", error_type=type(error).__name__,
                                           message="Post-operation assertion failed; inspect recorded result.")
            report.update(status="FAIL", error_type=type(error).__name__,
                          failure="Stopped at first failing check. Provider response bodies and secrets are omitted.")
        finally:
            repo.close()
            report["completed_at"] = datetime.now(timezone.utc).isoformat()
            report["requests"] = gateway.calls
            report["total_reported_tokens"] = gateway.adapter.usage
            report["money_cost"] = "Not calculated; consult account billing for measured charges."
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"Live acceptance {report['status']}; evidence: {args.output}", flush=True)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
