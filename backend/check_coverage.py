#!/usr/bin/env python3
import json
import sys
from pathlib import Path

OVERALL_LINE = 85.0
OVERALL_BRANCH = 70.0

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
print(f"Overall: line={line:.2f}% branch={branch:.2f}%")
if failures:
    print("Coverage thresholds failed:", *failures, sep="\n- ", file=sys.stderr)
    raise SystemExit(1)
print("Overall coverage thresholds: line>=85% PASS, branch>=70% PASS")
