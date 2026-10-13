# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The oracle for tasks that ship no oracle.

Some benchmarks provide a reference solution but no mechanical way to check a
different one. Rather than let those tasks silently reuse another benchmark's
oracle, they name this one, which always reports that it cannot decide. Gates that
need an oracle then record an explicit skip instead of an unearned pass.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from ..core.task import Task
from .base import Candidate, Oracle, OracleResult

__all__ = ["NullOracle"]


class NullOracle(Oracle):
    """Declines to judge, by design."""

    name: ClassVar[str] = "none"
    summary: ClassVar[str] = "no mechanical correctness check for this benchmark"

    def judge(
        self,
        task: Task,
        candidate: Candidate,
        *,
        workdir: Path,
        timeout_s: float = 300.0,
    ) -> OracleResult:
        """Report that this task has no oracle."""
        return OracleResult.unavailable(
            f"{task.benchmark} declares no tests to judge correctness by"
        )
