# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Pytest oracle for tasks that ship test files.

The candidate's files and the task's test files are written into a scratch
directory and pytest is run over the named tests. Per-test outcomes are read from
pytest's short summary, so a task that lists which tests must pass is judged test
by test rather than on the process exit code alone.

`probe` lays out the same directory and runs a program the caller supplies in it
instead of pytest.

`OracleSpec.tests` and `OracleSpec.regression` name what must pass. An entry that
contains ``::`` is a node id and must appear in the summary as passing; an entry
without one is a file or directory, and the tests it contains are only known once
pytest has collected them. Requiring a path to appear in the summary would report a
healthy run as unavailable, so only node ids are treated as obligations.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import ClassVar

from ..core.task import Task
from ..util.proc import run
from .base import Candidate, Oracle, OracleResult, Program
from .programs import outcome, sources, stage, unstaged
from .summaries import PASSING, READERS, UNANSWERED, read, status_of

__all__ = ["PytestOracle"]


class PytestOracle(Oracle):
    """Run pytest over a candidate and the task's tests."""

    name: ClassVar[str] = "pytest"
    summary: ClassVar[str] = "runs pytest over the task's test files"

    def judge(
        self,
        task: Task,
        candidate: Candidate,
        *,
        workdir: Path,
        timeout_s: float = 300.0,
    ) -> OracleResult:
        """Write the files out, run pytest, and compare against the task's list."""
        if task.oracle.log_format not in READERS:
            return OracleResult.unavailable(
                f"{task.key} reports its tests as {task.oracle.log_format!r}, which "
                "no reader in benchproofer.oracles.summaries understands"
            )
        written = stage((task.context.files, task.oracle.files, candidate.files), workdir)
        if not written:
            return OracleResult.unavailable("neither the task nor the candidate provides files")

        command = list(task.oracle.command) or [
            sys.executable,
            "-m",
            "pytest",
            "-rA",
            "--tb=short",
            "-p",
            "no:cacheprovider",
        ]
        targets = task.oracle.targets or tuple(
            dict.fromkeys((*task.oracle.tests, *task.oracle.regression))
        )
        result = run(
            (*command, *targets),
            cwd=workdir,
            timeout_s=min(timeout_s, task.oracle.timeout_s),
        )
        if result.timed_out:
            return OracleResult.timeout(
                f"pytest did not finish within {timeout_s:.0f}s",
                duration_s=result.duration_s,
                output=result.tail(),
            )

        outcomes = read(task.oracle.log_format, result.output)
        if not outcomes:
            if result.ok:
                return OracleResult.ok(
                    "pytest exited zero", duration_s=result.duration_s, output=result.tail()
                )
            return OracleResult.unavailable(
                "pytest produced no per-test summary",
                duration_s=result.duration_s,
                output=result.tail(),
            )

        ignore = PASSING + UNANSWERED
        passed = tuple(sorted(n for n, o in outcomes.items() if o in PASSING))
        failed = tuple(sorted(n for n, o in outcomes.items() if o not in ignore))
        obligations = (*task.oracle.tests, *task.oracle.regression)
        required = tuple(name for name in obligations if "::" in name)
        missing = [n for n in required if status_of(n, outcomes) in UNANSWERED]

        if missing:
            return OracleResult.unavailable(
                f"{len(missing)} required test(s) did not run: {', '.join(missing[:3])}",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        if failed:
            return OracleResult.no(
                f"{len(failed)} test(s) failed: {', '.join(failed[:3])}",
                duration_s=result.duration_s,
                output=result.tail(),
                passed=passed,
                failed=failed,
            )
        if not passed:
            return OracleResult.unavailable(
                "pytest reported no passing test, so nothing was checked",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        return OracleResult.ok(
            f"{len(passed)} test(s) passed",
            duration_s=result.duration_s,
            output=result.tail(),
            passed=passed,
        )

    def probe(
        self,
        task: Task,
        program: Program,
        *,
        workdir: Path,
        timeout_s: float = 300.0,
    ) -> OracleResult:
        """Run a program in a directory laid out as pytest would find it."""
        tree = sources(task, program)
        if tree is None:
            return unstaged(task, program, "solved tree")
        stage((tree, task.oracle.files), workdir)
        script = workdir / f"{program.label}.py"
        script.write_text(program.source, encoding="utf-8")
        budget = min(timeout_s, task.oracle.timeout_s)
        result = run((sys.executable, str(script)), cwd=workdir, timeout_s=budget)
        return outcome(result, program, budget)
