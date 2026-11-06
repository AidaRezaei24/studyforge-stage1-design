"""Command-line boundary over the shared application controller."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def create_controller(db: str):
    from .core import SQLiteRepository, StudyAgentFacade, StudyController
    from .model import OpenAIModelAdapter
    return StudyController(StudyAgentFacade(SQLiteRepository(db), OpenAIModelAdapter()))


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="studyforge", description="A local, evidence-grounded study workspace.")
    p.add_argument("--db", default=os.getenv("STUDYFORGE_DB", ".studyforge/studyforge.sqlite3"), help="SQLite workspace path")
    sub = p.add_subparsers(dest="command", required=True)
    gui = sub.add_parser("serve", help="Open the graphical workspace")
    gui.add_argument("--port", type=int, default=8765)
    course = sub.add_parser("course").add_subparsers(dest="operation", required=True)
    course.add_parser("list")
    course.add_parser("create").add_argument("name")
    material = sub.add_parser("material").add_subparsers(dest="operation", required=True)
    imp = material.add_parser("import")
    imp.add_argument("paths", nargs="+")
    imp.add_argument("--course", required=True)
    listing = sub.add_parser("list", help="Inspect saved workspace records")
    listing.add_argument("kind", choices=["material", "summary", "conversation", "graph", "plan", "deck", "quiz", "attempt", "session", "reminder"])
    listing.add_argument("--course", required=True)
    for name in ["summarize", "concepts", "ask", "flashcards", "quiz", "plan", "progress", "adapt", "reminder", "session"]:
        cmd = sub.add_parser(name)
        if name != "reminder":
            cmd.add_argument("--course", required=True)
        if name == "summarize":
            cmd.add_argument("--material")
            cmd.add_argument("--focus", default="")
            cmd.add_argument("--detail", choices=["concise", "detailed"], default="concise")
        elif name == "concepts":
            cmd.add_argument("--material")
            cmd.add_argument("--topic", default="")
        elif name == "ask":
            cmd.add_argument("question")
        elif name in ("flashcards", "quiz"):
            cmd.add_argument("--topic", default="")
            cmd.add_argument("--count", type=int, default=5)
            cmd.add_argument("--difficulty", choices=["mixed", "introductory", "intermediate", "advanced"], default="mixed")
        elif name == "plan":
            cmd.add_argument("--goal", required=True)
            cmd.add_argument("--deadline", required=True)
            cmd.add_argument("--start-date", help="First study date (ISO YYYY-MM-DD). Defaults to tomorrow, or today for same-day deadlines.")
            cmd.add_argument("--minutes-per-day", type=int, default=30)
            cmd.add_argument("--approve", action="store_true")
            cmd.add_argument("--replace", action="store_true")
        elif name == "adapt":
            cmd.add_argument("--minutes", type=int, default=15)
            cmd.add_argument("--confirm", action="store_true")
        elif name == "reminder":
            cmd.add_argument("--plan-id", required=True)
            cmd.add_argument("--start-time", default="18:00", help="Local start time, e.g. 18:00")
            cmd.add_argument("--timezone", default="America/Toronto")
            cmd.add_argument("--export-path", help="Optional .ics calendar output path")
            cmd.add_argument("--confirm", action="store_true")
        elif name == "session":
            cmd.add_argument("--goal", required=True)
            cmd.add_argument("--minutes", type=int, default=20)
    due = sub.add_parser("due-cards", help="List cards due for review")
    due.add_argument("--course", required=True)
    due.add_argument("--deck-id")
    edit = sub.add_parser("edit-card", help="Edit or reject a generated card")
    edit.add_argument("--course", required=True)
    edit.add_argument("--deck-id", required=True)
    edit.add_argument("--card-id", required=True)
    edit.add_argument("--front")
    edit.add_argument("--back")
    edit.add_argument("--reject", action="store_true")
    approval = sub.add_parser("plan-approve")
    approval.add_argument("--plan-id", required=True)
    approval.add_argument("--replace", action="store_true")
    review = sub.add_parser("review", help="Record a flashcard review")
    review.add_argument("--card-id", required=True)
    review.add_argument("--rating", type=int, required=True, choices=range(0, 4))
    grade = sub.add_parser("grade", help="Grade one quiz submission")
    grade.add_argument("--quiz-id", required=True)
    grade.add_argument("--attempt-id")
    grade.add_argument("--answers", required=True, help='JSON object mapping item IDs to answers')
    session = sub.add_parser("session-action", help="Advance, pause, resume, skip, or stop a focused session")
    session.add_argument("--session-id", required=True)
    session.add_argument("action", choices=["advance", "pause", "resume", "skip", "stop"])
    return p


def request_from_args(args):
    values = vars(args).copy()
    command = values.pop("command")
    values.pop("db", None)
    operation = values.pop("operation", None)
    if command == "plan" and values.get("start_date") in (None, ""):
        values.pop("start_date", None)
    if command == "course":
        return "course_" + operation, values
    if command == "material":
        return "import_materials", values
    actions = {"plan": "plan_create", "review": "review", "grade": "grade", "reminder": "reminder_schedule", "session": "session_start", "session-action": "session_action", "plan-approve": "plan_approve", "due-cards": "due_queue", "edit-card": "card_update"}
    if command == "grade":
        values["answers"] = json.loads(values["answers"])
    return actions.get(command, command), values


def main(argv=None, controller=None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "serve":
            from .gui import serve
            serve(controller or create_controller(args.db), args.port)
            return 0
        action, params = request_from_args(args)
        result = (controller or create_controller(args.db)).handle(action, **params)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, OSError, RuntimeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
