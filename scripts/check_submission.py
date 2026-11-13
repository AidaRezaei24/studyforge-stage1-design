"""Fail reproducibility checks without claiming missing evidence is complete."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
required = ["README.md", ".gitignore", ".env.example", "pyproject.toml",
            "stage2-report.pdf", "docs/demonstrations.md", "docs/architecture.md",
            "docs/live-verification.json", "docs/runtime-usage.json"]
failures = [f"Missing required file: {name}" for name in required if not (ROOT / name).is_file()]
result = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                        cwd=ROOT, text=True, capture_output=True, check=True)
secret_pattern = re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")
for name in result.stdout.splitlines():
    path = ROOT / name
    if path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example"):
        failures.append(f"Local configuration would be submitted: {name}")
    if path.is_file() and path.suffix in {".py", ".md", ".js", ".html", ".json", ".toml", ".yml"}:
        if secret_pattern.search(path.read_text(errors="replace")):
            failures.append(f"Possible credential found in: {name}")
if failures:
    print("\n".join(failures), file=sys.stderr)
    raise SystemExit(1)
print("Reproducibility files and source credential scan: PASS")
print("Manual gates: real feature videos, accessible links, measured usage accounting, final publication and course submission.")
