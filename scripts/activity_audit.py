"""Audit real repository dates; this never writes or rewrites Git history."""
from datetime import datetime
from pathlib import PurePosixPath
import json
import subprocess
from zoneinfo import ZoneInfo

PERIODS = [("2026-10-20", "2026-10-26"), ("2026-10-27", "2026-11-02"),
           ("2026-11-03", "2026-11-09")]


def audit(ref="HEAD"):
    log = subprocess.run(["git", "log", ref, "--format=%H%x09%aI%x09%cI%x09%s"],
                         text=True, capture_output=True, check=True)
    periods = [{"start": a, "end": b, "candidate_code_commits": []} for a, b in PERIODS]
    for row in log.stdout.splitlines():
        sha, authored, committed, subject = row.split("\t", 3)
        local_date = datetime.fromisoformat(committed).astimezone(ZoneInfo("America/Toronto")).date().isoformat()
        files = subprocess.run(["git", "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", sha],
                               text=True, capture_output=True, check=True).stdout.splitlines()
        code = [name for name in files if PurePosixPath(name).suffix in {".py", ".js", ".html", ".css"}]
        if code:
            for period in periods:
                if period["start"] <= local_date <= period["end"]:
                    period["candidate_code_commits"].append({"sha": sha, "subject": subject,
                        "author_date": authored, "committer_date": committed, "files": code,
                        "link": f"https://github.com/AidaRezaei24/studyforge-stage1-design/commit/{sha}"})
    for period in periods:
        period["candidate_count"] = len(period["candidate_code_commits"])
        period["minimum"] = 5
        period["manual_review_required"] = "Check meaningful progress and contemporaneous GitHub push evidence; dates alone do not establish compliance."
    return periods


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
