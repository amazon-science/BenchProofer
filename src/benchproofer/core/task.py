# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The normalized task model.

A benchmark adapter turns its upstream rows into `Task` objects, and everything downstream
is written against this shape, so one pipeline serves benchmarks as different as HumanEval
(a function stub and a `check()` routine) and SWE-bench (a repository at a commit and a
container image).
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..util.digest import digest_json

__all__ = [
    "OracleSpec",
    "Reference",
    "Repository",
    "SourceFile",
    "Task",
    "TaskContext",
]

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


class SourceFile(BaseModel):
    """A file belonging to a task, either inline or by path in a repository."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    content: str | None = None


class Repository(BaseModel):
    """A repository-level task's code location and environment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    url: str | None = None
    commit: str | None = None
    image: str | None = None
    subdir: str | None = None


class TaskContext(BaseModel):
    """Where the code under specification lives."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    files: tuple[SourceFile, ...] = ()
    repository: Repository | None = None
    entry_points: tuple[str, ...] = ()


class Reference(BaseModel):
    """The benchmark's own solution, in whichever form it ships."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    patch: str | None = None
    files: tuple[SourceFile, ...] = ()
    symbols: tuple[str, ...] = ()
    answer: str | None = None

    @property
    def is_empty(self) -> bool:
        """True when the task ships no reference solution at all."""
        return not (self.patch or self.files or self.answer)


class OracleSpec(BaseModel):
    """How to decide mechanically whether a candidate solves the task.

    `kind` names a registered oracle; the other fields are the union of what the built-in
    oracles need. `tests` and `regression` must pass: the tests the change fixes and the
    tests it must not break. `targets` is what to *run*, for a runner driven by file or
    module rather than test name; when it is empty the two lists are run directly.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: str = "none"
    tests: tuple[str, ...] = ()
    regression: tuple[str, ...] = ()
    targets: tuple[str, ...] = ()
    files: tuple[SourceFile, ...] = ()
    setup: tuple[str, ...] = ()
    command: tuple[str, ...] = ()
    #: Name of the reader in `benchproofer.oracles.summaries` for this runner's output.
    log_format: str = "pytest"
    #: True when the tests need network access. Oracles run sandboxed by default, since a
    #: suite that reaches a live service decides a different question on every run.
    network: bool = False
    image: str | None = None
    expected: str | None = None
    timeout_s: int = 300


class Task(BaseModel):
    """One benchmark row, normalized.

    `metadata` carries what the adapter kept but did not model, and is left out of
    `digest()` so annotating a task does not invalidate its bundles. `source_digest` pins
    the upstream row, so the integrity gate can detect a row that changed after a bundle
    was built.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1] = 1
    benchmark: str
    task_id: str
    statement: str
    language: str = "python"
    context: TaskContext = TaskContext()
    reference: Reference = Reference()
    oracle: OracleSpec = OracleSpec()
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_digest: str = ""

    @property
    def slug(self) -> str:
        """A filesystem-safe form of `task_id`."""
        return _UNSAFE.sub("_", self.task_id).strip("_") or "task"

    @property
    def key(self) -> str:
        """The globally unique identifier of this task."""
        return f"{self.benchmark}/{self.task_id}"

    def digest(self) -> str:
        """Digest the normalized task, excluding volatile fields."""
        payload = self.model_dump(mode="json", exclude={"metadata"})
        return digest_json(payload)

    def reference_code(self) -> str:
        """The code the benchmark's own solution adds.

        For a patch, the added lines; for whole-file references, the lines the reference
        has and the starting files do not, so a stub a specification is supposed to
        repeat is excluded.
        """
        if self.reference.patch:
            return "\n".join(
                line[1:]
                for line in self.reference.patch.splitlines()
                if line.startswith("+") and not line.startswith("+++")
            )

        starting = {
            line.strip()
            for source in self.context.files
            if source.content
            for line in source.content.splitlines()
        }
        added: list[str] = []
        for source in self.reference.files:
            if not source.content:
                continue
            added.extend(
                line for line in source.content.splitlines() if line.strip() not in starting
            )
        return "\n".join(added)
