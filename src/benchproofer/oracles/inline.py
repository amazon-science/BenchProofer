# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Inline-test oracle for single-module tasks.

HumanEval, MBPP, and benchmarks shaped like them ship a test program as a string.
The candidate module and that program are concatenated and run as one script in a
child process: the script exits zero exactly when the candidate solves the task.
`probe` runs a program the caller supplies beside the same module, with the same
interpreter.

The benchmark's own code is executed, so run untrusted benchmarks in a sandbox.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import ClassVar

from ..core.task import Task
from ..util.proc import run
from .base import Candidate, Oracle, OracleResult, Program
from .programs import missing_module, outcome, sources, stage, unstaged

__all__ = ["InlineTestOracle"]


class InlineTestOracle(Oracle):
    """Run a task's inline test program against a candidate module."""

    name: ClassVar[str] = "inline-tests"
    summary: ClassVar[str] = "runs the task's own test program in a child process"

    def judge(
        self,
        task: Task,
        candidate: Candidate,
        *,
        workdir: Path,
        timeout_s: float = 300.0,
    ) -> OracleResult:
        """Concatenate the candidate with the task's tests and run the result."""
        if not task.oracle.tests:
            return OracleResult.unavailable(f"{task.key} declares no inline tests")
        module = _module_source(task, candidate)
        if module is None:
            return OracleResult.unavailable("candidate provides no module source")

        workdir.mkdir(parents=True, exist_ok=True)
        script = workdir / "check.py"
        script.write_text(
            module.rstrip("\n") + "\n\n" + "\n\n".join(task.oracle.tests) + "\n",
            encoding="utf-8",
        )

        result = run(
            (sys.executable, str(script)),
            cwd=workdir,
            timeout_s=min(timeout_s, task.oracle.timeout_s),
        )
        if result.timed_out:
            return OracleResult.timeout(
                f"tests did not finish within {timeout_s:.0f}s",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        if result.ok:
            return OracleResult.ok(
                "inline tests passed", duration_s=result.duration_s, output=result.tail()
            )
        absent = missing_module(result.output)
        if absent is not None:
            return OracleResult.unavailable(
                f"the tests import {absent!r}, which is not installed here",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        return OracleResult.no(
            _first_failure(result.tail()),
            duration_s=result.duration_s,
            output=result.tail(),
        )

    def probe(
        self,
        task: Task,
        program: Program,
        *,
        workdir: Path,
        timeout_s: float = 300.0,
    ) -> OracleResult:
        """Run a program beside the task's module, with the same interpreter."""
        tree = sources(task, program)
        if tree is None:
            return unstaged(task, program, "solved module")
        stage((tree,), workdir)
        script = workdir / f"{program.label}.py"
        script.write_text(program.source, encoding="utf-8")
        budget = min(timeout_s, task.oracle.timeout_s)
        result = run((sys.executable, str(script)), cwd=workdir, timeout_s=budget)
        return outcome(result, program, budget)


def _module_source(task: Task, candidate: Candidate) -> str | None:
    """Choose the module text to test.

    A candidate may supply whole files or nothing at all, in which case the task's
    own context files are used, which is how a reference candidate for a
    stub-and-solution benchmark is expressed.
    """
    for source in candidate.files:
        if source.content is not None:
            return source.content
    if candidate.patch:
        return None
    for source in task.context.files:
        if source.content is not None:
            return source.content
    return None


def _first_failure(output: str) -> str:
    for line in reversed(output.splitlines()):
        stripped = line.strip()
        if stripped and not stripped.startswith("File "):
            return stripped[:300]
    return "inline tests failed"
