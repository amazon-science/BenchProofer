# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The correctness-oracle interface.

An oracle decides the benchmark's own question: does this candidate solve the
task? It is deliberately separate from the verification backends. A backend
decides whether an implementation meets a specification; an oracle decides
whether a change satisfies the benchmark. Comparing the two verdicts is what makes
a specification auditable rather than merely plausible.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import ClassVar

from ..core.plugin import Availability
from ..core.task import SourceFile, Task

__all__ = ["Candidate", "Oracle", "OracleResult", "OracleStatus", "Program"]


class OracleStatus(str, Enum):
    """The outcome of asking an oracle about one candidate.

    `UNAVAILABLE` and `ERROR` are not failures of the candidate. They mean the
    question was not decided, and a caller that treats them as `UNRESOLVED`
    converts its own missing dependency into an apparent defect in an artifact.
    """

    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    UNAVAILABLE = "unavailable"
    ERROR = "error"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Candidate:
    """A proposed solution, in whichever form the task accepts.

    Exactly one form is normally populated: a unified diff for repository tasks,
    replacement file contents for single-file tasks, or a literal answer for
    question-answering benchmarks.
    """

    patch: str | None = None
    files: tuple[SourceFile, ...] = ()
    answer: str | None = None
    label: str = "candidate"

    @classmethod
    def reference(cls, task: Task) -> Candidate:
        """Build the candidate that the benchmark itself considers correct."""
        return cls(
            patch=task.reference.patch,
            files=task.reference.files,
            answer=task.reference.answer,
            label="reference",
        )

    @property
    def is_empty(self) -> bool:
        """True when there is nothing for an oracle to apply."""
        return not (self.patch or self.files or self.answer)


@dataclass(frozen=True, slots=True)
class Program:
    """A Python program to run where the benchmark's own tests run.

    A program about the repository's code -- a conformance comparison, or a check of
    an unchanged callee -- is worth something only if it reaches the code the task's
    tests would: the same interpreter, the same installed packages, and the same
    working copy.
    """

    source: str
    label: str = "probe"
    #: True to run against the benchmark's own solution rather than the unsolved
    #: task, for a program about a callee the task itself introduces or changes.
    with_reference: bool = False
    #: A diff applied in place of the benchmark's own solution, for a program about the code
    #: another change to the task produces, such as an attack's equivalent patch. Set, it
    #: is applied whatever `with_reference` says.
    patch: str | None = None


@dataclass(frozen=True, slots=True)
class OracleResult:
    """One oracle invocation."""

    status: OracleStatus
    detail: str = ""
    duration_s: float = 0.0
    output: str = ""
    timed_out: bool = False
    passed: tuple[str, ...] = field(default_factory=tuple)
    failed: tuple[str, ...] = field(default_factory=tuple)
    #: Why an unresolved result says nothing about how the candidate behaves, empty when
    #: it does: the candidate never applied, or it broke the code so thoroughly that no
    #: test the task keeps passing still passed. Either tests the candidate's editing
    #: rather than the implementation it was written to carry.
    inert: str = ""

    @property
    def resolved(self) -> bool:
        """True when the candidate solved the task."""
        return self.status is OracleStatus.RESOLVED

    @property
    def decided(self) -> bool:
        """True when the oracle reached a verdict either way."""
        return self.status in (OracleStatus.RESOLVED, OracleStatus.UNRESOLVED)

    @classmethod
    def ok(
        cls,
        detail: str = "",
        *,
        duration_s: float = 0.0,
        output: str = "",
        passed: tuple[str, ...] = (),
        failed: tuple[str, ...] = (),
    ) -> OracleResult:
        """Build a resolved result."""
        return cls(
            status=OracleStatus.RESOLVED,
            detail=detail,
            duration_s=duration_s,
            output=output,
            passed=passed,
            failed=failed,
        )

    @classmethod
    def no(
        cls,
        detail: str = "",
        *,
        duration_s: float = 0.0,
        output: str = "",
        passed: tuple[str, ...] = (),
        failed: tuple[str, ...] = (),
        inert: str = "",
    ) -> OracleResult:
        """Build an unresolved result."""
        return cls(
            status=OracleStatus.UNRESOLVED,
            detail=detail,
            duration_s=duration_s,
            output=output,
            passed=passed,
            failed=failed,
            inert=inert,
        )

    @classmethod
    def unavailable(
        cls, detail: str, *, duration_s: float = 0.0, output: str = ""
    ) -> OracleResult:
        """Build a result recording that the oracle could not run here."""
        return cls(
            status=OracleStatus.UNAVAILABLE,
            detail=detail,
            duration_s=duration_s,
            output=output,
        )

    @classmethod
    def timeout(cls, detail: str, *, duration_s: float = 0.0, output: str = "") -> OracleResult:
        """Build a result recording that the oracle ran but never reached a verdict."""
        return cls(
            status=OracleStatus.ERROR,
            detail=detail,
            duration_s=duration_s,
            output=output,
            timed_out=True,
        )

    @classmethod
    def error(cls, detail: str, *, duration_s: float = 0.0, output: str = "") -> OracleResult:
        """Build a result recording a defect in the oracle run itself."""
        return cls(
            status=OracleStatus.ERROR,
            detail=detail,
            duration_s=duration_s,
            output=output,
        )


class Oracle(ABC):
    """Base class for correctness oracles."""

    #: Registry name, matching the entry point.
    name: ClassVar[str]
    #: One-line description shown by ``benchproofer doctor``.
    summary: ClassVar[str] = ""
    #: True when the oracle needs a container runtime.
    needs_docker: ClassVar[bool] = False

    @abstractmethod
    def judge(
        self,
        task: Task,
        candidate: Candidate,
        *,
        workdir: Path,
        timeout_s: float = 300.0,
    ) -> OracleResult:
        """Decide whether ``candidate`` solves ``task``.

        Args:
            task: The task, whose `oracle` field configures this call.
            candidate: The proposed solution.
            workdir: A scratch directory the oracle owns for this call.
            timeout_s: Wall-clock budget.

        Returns:
            An `OracleResult`. Implementations must not report `UNRESOLVED` for a
            missing dependency, a timeout, or a crash.
        """

    def probe(
        self,
        task: Task,
        program: Program,
        *,
        workdir: Path,
        timeout_s: float = 300.0,
    ) -> OracleResult:
        """Run one program in the environment this oracle runs tests in.

        `RESOLVED` means the program exited zero and `UNRESOLVED` that it exited
        non-zero; what either says is the caller's business, since the program is the
        caller's. The default declines, because an oracle that judges an answer
        string, say, has no environment to offer.

        Args:
            task: The task whose environment the program runs in.
            program: The program to run.
            workdir: A scratch directory the oracle owns for this call.
            timeout_s: Wall-clock budget.
        """
        return OracleResult.unavailable(
            f"the runner of the benchmark's tests ({self.name}) cannot run a program in "
            "the task's environment"
        )

    def export(self, task: Task, *, into: Path) -> Path | None:
        """Put the task's own working copy on this machine, for something to read.

        A stage that has to decide what to write by *looking* -- which function in the
        repository a specification is about, which callee cannot be modelled -- needs the
        repository, and for a benchmark whose environment is a container the repository
        is only in the container. This is how it comes out: at the commit the task starts
        from, which is the version a solver would be given.

        The default declines. An oracle with no environment has nothing to export, and a
        caller that needs a working copy then has the task's own context files and
        nothing more, which is a weaker thing and has to be treated as one.

        Returns:
            The directory the working copy is rooted at, or None when this oracle cannot
            produce one.
        """
        return None

    def availability(self) -> Availability:
        """Report whether this oracle can run here."""
        return Availability.ok()

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r}>"
