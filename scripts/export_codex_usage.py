"""Export scoped Codex token counters without conversation content or billing guesses."""
import argparse
from collections import defaultdict
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys


def thread_hash(thread_id):
    return hashlib.sha256(thread_id.encode("utf-8")).hexdigest()


def parent_thread(source):
    """Recognize Codex subagent sources and the older unwrapped spawn form."""
    try:
        value = json.loads(source)
    except (TypeError, ValueError):
        return None
    if not isinstance(value, dict):
        return None
    if isinstance(value.get("subagent"), dict):
        value = value["subagent"]
    spawn = value.get("thread_spawn")
    if not isinstance(spawn, dict):
        return None
    parent = spawn.get("parent_thread_id")
    return parent if isinstance(parent, str) and parent else None


def export_usage(database, root_threads):
    """Read one consistent SQLite snapshot; include only roots and their descendants."""
    database = Path(database).expanduser().resolve()
    roots = set(root_threads)
    if not roots or any(not isinstance(root, str) or not root for root in roots):
        raise ValueError("Provide at least one nonempty root thread ID.")
    if not database.is_file():
        raise ValueError("The Codex metadata database does not exist.")
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as connection:
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        parents = {row[0]: parent_thread(row[1])
                   for row in connection.execute("SELECT id, source FROM threads")}
        if not roots <= parents.keys():
            raise ValueError("One or more requested root threads were not found; no export was written.")
        children = defaultdict(list)
        for child, parent in parents.items():
            if parent is not None:
                children[parent].append(child)
        selected = set(roots)
        pending = list(roots)
        while pending:
            for child in children[pending.pop()]:
                if child not in selected:
                    selected.add(child)
                    pending.append(child)
        rows = []
        by_model = {}
        roles = {"root": 0, "delegate": 0}
        for thread_id in sorted(selected):
            model, tokens, created = connection.execute(
                "SELECT model, tokens_used, created_at FROM threads WHERE id=?", (thread_id,)).fetchone()
            if type(tokens) is not int or tokens < 0:
                raise ValueError("A selected thread has an invalid token counter; no export was written.")
            if not isinstance(model, str) or not model.strip():
                raise ValueError("A selected thread has an invalid model; no export was written.")
            if type(created) is not int:
                raise ValueError("A selected thread has an invalid creation timestamp; no export was written.")
            try:
                created_utc = datetime.fromtimestamp(created, timezone.utc).isoformat()
            except (ValueError, OverflowError, OSError):
                raise ValueError("A selected thread has an invalid creation timestamp; no export was written.") from None
            role = "root" if thread_id in roots else "delegate"
            roles[role] += 1
            bucket = by_model.setdefault(model, {"thread_count": 0, "total_tokens": 0})
            bucket["thread_count"] += 1
            bucket["total_tokens"] += tokens
            parent = parents[thread_id]
            rows.append({"thread_hash": thread_hash(thread_id),
                         "parent_thread_hash": thread_hash(parent) if parent in selected else None,
                         "role": role, "model": model, "total_tokens": tokens,
                         "created_at_utc": created_utc})
        return {
            "snapshot_at_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "Explicit root threads and transitive thread_spawn descendants only.",
            "source": "Codex SQLite per-thread tokens_used counters; each selected thread counted once.",
            "thread_count": len(rows), "role_counts": roles,
            "total_tokens": sum(row["total_tokens"] for row in rows),
            "by_model": dict(sorted(by_model.items())), "threads": rows,
            "limitations": [
                "Cumulative counters include repeated cached context; they are not unique document tokens.",
                "Counters are a snapshot and may increase while a selected thread is active.",
                "These counters are not invoices. No Codex dollar estimate is derived from API rates.",
                "No input/output/cache breakdown or billing amount is available from these counters.",
            ],
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-thread", action="append", required=True,
                        help="Include this thread and its descendants; repeat for multiple roots")
    parser.add_argument("--codex-home", type=Path, default=Path.home() / ".codex",
                        help="Codex home containing state_5.sqlite (default: ~/.codex)")
    parser.add_argument("--output", type=Path, required=True, help="Destination JSON snapshot")
    args = parser.parse_args(argv)
    database = args.codex_home.expanduser().resolve() / "state_5.sqlite"
    output = args.output.expanduser().resolve()
    try:
        if output.is_relative_to(database.parent):
            # Exports must never replace Codex state, credentials, or configuration.
            raise ValueError("Write the export outside the Codex home directory.")
        result = export_usage(database, args.root_thread)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except (ValueError, OSError, sqlite3.Error):
        print("Usage export failed. Check the metadata database, explicit root IDs, counters, and output path. No conversation content was exported.", file=sys.stderr)
        return 1
    print(f"Exported {result['thread_count']} scoped threads and {result['total_tokens']} tokens.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
