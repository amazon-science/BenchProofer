# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""SMT-LIB2 backend, solved by Z3.

A solution is an SMT-LIB2 script whose specification region asserts the negation of
the obligation. The file is verified when the solver reports ``unsat``: no input
makes the implementation violate the specification. ``sat`` is a refutation with a
model, and ``unknown`` is the solver declining to decide, which is neither.

Install with ``pip install -e ".[smt]"``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import ClassVar

from ..core.markers import wrap
from ..core.plugin import Availability
from ..util.proc import run
from .base import Backend, BackendKind, CheckResult

__all__ = ["SmtBackend"]

_DRIVER = "benchproofer.backends._z3_driver"


class SmtBackend(Backend):
    """Discharge an SMT-LIB2 obligation with Z3."""

    name: ClassVar[str] = "smt"
    language: ClassVar[str] = "SMT-LIB2"
    extension: ClassVar[str] = ".smt2"
    comment: ClassVar[str] = ";"
    kind: ClassVar[BackendKind] = BackendKind.PROVER
    summary: ClassVar[str] = "Z3 over SMT-LIB2 obligations"
    #: An inconsistent premise proves everything, so an outright contradiction is
    #: rejected before the solver is asked.
    banned_tokens: ClassVar[tuple[str, ...]] = ("(assert false", "(assert (= 0 1)")

    def availability(self) -> Availability:
        """Report whether Z3's Python distribution is installed."""
        result = run(
            (sys.executable, "-c", "import z3; print(z3.get_version_string())"),
            timeout_s=120,
        )
        if not result.ok:
            return Availability.missing(
                "z3 is not installed",
                hint='pip install -e ".[smt]"',
            )
        return Availability.ok(version=result.stdout.strip() or None)

    def check(self, source: str, *, workdir: Path, timeout_s: float = 120.0) -> CheckResult:
        """Solve one script and translate what the solver printed into a verdict."""
        workdir.mkdir(parents=True, exist_ok=True)
        path = workdir / self.solution_filename()
        path.write_text(source, encoding="utf-8")

        result = run(
            (sys.executable, "-m", _DRIVER, str(path), f"{timeout_s:.1f}"),
            cwd=workdir,
            timeout_s=timeout_s + 15,
        )
        answer = result.stdout.strip().splitlines()[-1].strip() if result.stdout.strip() else ""

        if result.timed_out:
            return CheckResult.unknown(
                f"no verdict within {timeout_s:.0f}s",
                duration_s=result.duration_s,
                output=result.tail(),
                timed_out=True,
            )
        if result.returncode == 2:
            complaint = result.stderr.strip()
            return CheckResult.malformed(
                complaint.splitlines()[0][:300] if complaint else "unreadable script",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        if not result.ok:
            return CheckResult.unknown(
                f"solver driver exited {result.returncode}",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        if answer == "unsat":
            return CheckResult.ok(
                "obligation is unsatisfiable",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        if answer == "sat":
            return CheckResult.no(
                "counterexample exists", duration_s=result.duration_s, output=result.tail()
            )
        return CheckResult.unknown(
            f"solver returned {answer or 'nothing'}",
            duration_s=result.duration_s,
            output=result.tail(),
        )

    def template(self) -> str:
        """A script whose obligation is discharged by the implementation."""
        impl = wrap(
            self.comment,
            "impl",
            "(define-fun impl ((x Int)) Int (+ x x))",
        )
        spec = wrap(
            self.comment,
            "spec",
            "(define-fun spec ((x Int) (r Int)) Bool (= r (* 2 x)))\n"
            "(assert (not (forall ((x Int)) (spec x (impl x)))))",
        )
        return f"{impl}\n\n{spec}\n"

    def guidance(self) -> str:
        """SMT-specific instructions for the formalization stage."""
        return (
            "Write one SMT-LIB2 script. The impl region defines the implementation "
            "with define-fun. The spec region defines the specification predicate "
            "and asserts the negation of the obligation, so that the script is "
            "unsat exactly when the implementation satisfies the specification. Do "
            "not assert anything false, and do not include (check-sat)."
        )
