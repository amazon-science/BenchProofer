# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Running a program where a benchmark's own code runs.

An oracle that runs tests has an environment: a directory laid out with the task's
files, an interpreter, and whatever is installed beside it. `Oracle.probe` lends that
environment to a `Program` the caller supplies.

What the oracles that run Python agree on lives here: how a task's files land on
disk, and what an exit code means. Zero is `RESOLVED` and non-zero `UNRESOLVED`; a
program that never finished is a timeout rather than a refutation, for the same
reason a verifier that never finished is not one, and a program that could not import
what it needs has said nothing at all.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from ..core.task import SourceFile, Task
from ..util.proc import Completed
from .base import OracleResult, Program

__all__ = ["missing_module", "outcome", "sources", "stage", "unstaged"]

#: A program that imports a library this machine does not have says nothing about the
#: candidate, so the run is reported as unavailable rather than failed.
_MISSING_MODULE = re.compile(r"ModuleNotFoundError: No module named '(?P<name>[^']+)'")


def missing_module(output: str) -> str | None:
    """The module a run needed and did not find, if that is why it failed."""
    match = _MISSING_MODULE.search(output)
    return match.group("name") if match else None


def stage(groups: Iterable[tuple[SourceFile, ...]], workdir: Path) -> list[Path]:
    """Write out every file of every group, later groups overwriting earlier ones."""
    written: list[Path] = []
    workdir.mkdir(parents=True, exist_ok=True)
    for group in groups:
        for source in group:
            if source.content is None:
                continue
            target = workdir / source.path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source.content, encoding="utf-8")
            written.append(target)
    return written


def sources(task: Task, program: Program) -> tuple[SourceFile, ...] | None:
    """The task's tree as ``program`` asked to see it.

    Returns None when the program wants the benchmark's own solution in place and the
    benchmark expresses that solution as a patch, or names a patch of its own
    (`Program.patch`): an oracle that stages files has no working copy to apply one to, and
    staging the unsolved task instead would run the program against other code than it asked
    for.
    """
    if program.patch is not None:
        return None
    if not program.with_reference:
        return task.context.files
    if not task.reference.files:
        return None
    return (*task.context.files, *task.reference.files)


def unstaged(task: Task, program: Program, tree: str) -> OracleResult:
    """Why an oracle that stages files cannot give ``program`` the tree it asks for (`sources`).

    ``tree`` names what the oracle stages, for the message.
    """
    if program.patch is not None:
        why = f"{program.label} asks for a patch applied in place of {task.key}'s own solution"
    else:
        why = f"{task.key} states its own solution as something other than whole files"
    return OracleResult.unavailable(f"{why}, so {program.label} has no {tree} to run against")


def outcome(result: Completed, program: Program, timeout_s: float) -> OracleResult:
    """Read one program run as an oracle result."""
    if result.timed_out:
        return OracleResult.timeout(
            f"{program.label} did not finish within {timeout_s:.0f}s",
            duration_s=result.duration_s,
            output=result.output,
        )
    detail = f"{program.label} exited {result.returncode}"
    if result.ok:
        return OracleResult.ok(detail, duration_s=result.duration_s, output=result.output)
    return OracleResult.no(detail, duration_s=result.duration_s, output=result.output)
