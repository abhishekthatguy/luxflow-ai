#!/usr/bin/env python3
"""Run simple, medium, and complex QA walkthroughs; report combined results."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
CASES = [
    ("Simple", "qa_simple_case.py"),
    ("Medium", "qa_medium_case.py"),
    ("Complex", "qa_complex_case.py"),
]


def main() -> int:
    results: list[tuple[str, int]] = []
    print("\n########## LexFlow QA — All Sample Cases ##########\n")

    for label, script in CASES:
        print(f"\n{'=' * 60}\n>>> Starting {label} case\n{'=' * 60}")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / script)],
            cwd=str(SCRIPTS),
        )
        results.append((label, proc.returncode))
        if proc.returncode != 0 and label != CASES[-1][0]:
            time.sleep(3)

    print(f"\n{'=' * 60}\n########## COMBINED RESULTS ##########\n")
    failed = 0
    for label, code in results:
        status = "PASS" if code == 0 else "FAIL"
        if code != 0:
            failed += 1
        print(f"  {status}  {label} case (exit {code})")

    print(f"\nTotal: {len(results) - failed}/{len(results)} passed\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
