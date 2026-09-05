#!/usr/bin/env python3
import json
import sys
from pathlib import Path

OVERALL_LINE = 90.0
OVERALL_BRANCH = 85.0
FILE_LINE = 80.0
FILE_BRANCH = 75.0

path = Path(sys.argv[1] if len(sys.argv) > 1 else "coverage.json")
data = json.loads(path.read_text())
failures = []

def percent(covered, total):
    return 100.0 if total == 0 else covered * 100.0 / total

totals = data["totals"]
line = percent(totals["covered_lines"], totals["num_statements"])
branch = percent(totals["covered_branches"], totals["num_branches"])
if line < OVERALL_LINE:
    failures.append(f"overall line {line:.2f}% < {OVERALL_LINE:.0f}%")
if branch < OVERALL_BRANCH:
    failures.append(f"overall branch {branch:.2f}% < {OVERALL_BRANCH:.0f}%")
for filename, details in sorted(data["files"].items()):
    summary = details["summary"]
    file_line = percent(summary["covered_lines"], summary["num_statements"])
    file_branch = percent(summary["covered_branches"], summary["num_branches"])
    if file_line < FILE_LINE:
        failures.append(f"{filename}: line {file_line:.2f}% < {FILE_LINE:.0f}%")
    if file_branch < FILE_BRANCH:
        failures.append(f"{filename}: branch {file_branch:.2f}% < {FILE_BRANCH:.0f}%")
print(f"Overall: line={line:.2f}% branch={branch:.2f}%")
if failures:
    print("Coverage thresholds failed:", *failures, sep="\n- ", file=sys.stderr)
    raise SystemExit(1)
print("Per-file thresholds: line>=80% PASS, branch>=75% PASS")
