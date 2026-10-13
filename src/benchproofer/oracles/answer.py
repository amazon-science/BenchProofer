# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Exact-answer oracle.

For benchmarks whose ground truth is a value rather than a program, such as GSM8K. A
candidate states its answer either as a literal, which is how the benchmark's own
reference states it, or as a Python program that prints one, which is how a bundle
states it: what a verified artifact stands behind is a computation, so the gates hand
this oracle the Python copy of the implementation that was checked rather than a
number somebody typed.

Comparison is numeric when both sides parse as numbers and textual otherwise, and the
normalization applied to each side is recorded on the result so a disagreement about
formatting is not mistaken for a disagreement about the answer.

A candidate's program is executed, so run untrusted bundles in a sandbox.
"""

from __future__ import annotations

import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import ClassVar

from ..core.task import Task
from ..util.proc import run
from .base import Candidate, Oracle, OracleResult
from .programs import missing_module

__all__ = ["AnswerOracle", "normalize"]

_STRIP = re.compile(r"[,$%\s]")
_TRAILING = re.compile(r"[.\s]+$")


def normalize(value: str) -> str:
    """Reduce an answer to the form comparison uses."""
    text = _TRAILING.sub("", value.strip())
    text = _STRIP.sub("", text)
    return text.lower()


class AnswerOracle(Oracle):
    """Compare a candidate's answer with the task's expected answer."""

    name: ClassVar[str] = "answer"
    summary: ClassVar[str] = "compares an answer, stated or computed, with the benchmark's own"

    def judge(
        self,
        task: Task,
        candidate: Candidate,
        *,
        workdir: Path,
        timeout_s: float = 300.0,
    ) -> OracleResult:
        """Decide whether the candidate's answer matches."""
        expected = task.oracle.expected
        if expected is None:
            return OracleResult.unavailable(f"{task.key} declares no expected answer")
        if candidate.answer is not None:
            return _compare(candidate.answer, expected)
        program = _program(candidate)
        if program is None:
            return OracleResult.unavailable(
                "candidate states neither an answer nor a program that prints one"
            )
        return _computed(task, program, expected, workdir=workdir, timeout_s=timeout_s)


def _program(candidate: Candidate) -> str | None:
    """The Python program a candidate answers with, when it answers with one."""
    for source in candidate.files:
        if source.path.endswith(".py") and source.content is not None:
            return source.content
    return None


def _computed(
    task: Task,
    program: str,
    expected: str,
    *,
    workdir: Path,
    timeout_s: float,
) -> OracleResult:
    """Run a program that answers the task, and judge the answer it printed.

    The answer is the last line the program writes to standard output, which is what
    the drafting prompt asks a shadow for. Only standard output is read, so a warning
    on the way past is not taken for the answer.
    """
    workdir.mkdir(parents=True, exist_ok=True)
    script = workdir / "answer.py"
    script.write_text(program, encoding="utf-8")
    budget = min(timeout_s, task.oracle.timeout_s)
    result = run((sys.executable, str(script)), cwd=workdir, timeout_s=budget)

    if result.timed_out:
        return OracleResult.timeout(
            f"the program did not answer within {budget:.0f}s",
            duration_s=result.duration_s,
            output=result.tail(),
        )
    absent = missing_module(result.output)
    if absent is not None:
        return OracleResult.unavailable(
            f"the program imports {absent!r}, which is not installed here",
            duration_s=result.duration_s,
            output=result.tail(),
        )
    if not result.ok:
        return OracleResult.no(
            f"the program exited {result.returncode} without printing an answer",
            duration_s=result.duration_s,
            output=result.tail(),
        )
    printed = _last_line(result.stdout)
    if printed is None:
        return OracleResult.no(
            "the program printed nothing, so it states no answer",
            duration_s=result.duration_s,
            output=result.tail(),
        )
    return _compare(printed, expected, duration_s=result.duration_s, output=result.tail())


def _compare(
    answer: str, expected: str, *, duration_s: float = 0.0, output: str = ""
) -> OracleResult:
    """Judge one answer against the expected one."""
    left, right = normalize(answer), normalize(expected)
    if left == right or _numerically_equal(left, right):
        return OracleResult.ok(
            f"answer matches ({right})", duration_s=duration_s, output=output
        )
    return OracleResult.no(
        f"answer is {left!r}, expected {right!r}", duration_s=duration_s, output=output
    )


def _last_line(text: str) -> str | None:
    """The last line with anything on it, or None when there is none."""
    for line in reversed(text.splitlines()):
        if line.strip():
            return line
    return None


def _numerically_equal(left: str, right: str) -> bool:
    try:
        return Decimal(left) == Decimal(right)
    except (InvalidOperation, ValueError):
        return False
