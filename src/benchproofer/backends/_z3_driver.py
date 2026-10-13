# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Solve one SMT-LIB2 script in a child process.

Running the solver out of process keeps a solver crash from taking the tool down
with it, and keeps a runaway search bounded by the caller's own timeout as well as
the solver's.

Usage: ``python -m benchproofer.backends._z3_driver <file> <timeout-seconds>``.
Prints ``sat``, ``unsat``, or ``unknown`` on success; exits 2 on a script the
solver could not read.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    """Parse and solve one script, reporting the result on stdout."""
    if len(argv) != 2:
        print("usage: _z3_driver <file> <timeout-seconds>", file=sys.stderr)
        return 64
    path, budget = Path(argv[0]), float(argv[1])

    try:
        import z3
    except ImportError as exc:  # pragma: no cover - reported to the caller
        print(f"z3 is not installed: {exc}", file=sys.stderr)
        return 3

    try:
        assertions = z3.parse_smt2_string(path.read_text(encoding="utf-8"))
    except z3.Z3Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2

    solver = z3.Solver()
    solver.set("timeout", max(1, int(budget * 1000)))
    solver.add(assertions)
    result = solver.check()
    print(result)
    if repr(result) == "unknown":
        print(solver.reason_unknown(), file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover - process entry point
    raise SystemExit(main(sys.argv[1:]))
