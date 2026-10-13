# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""What a smoke case is, and what running one produces.

A case answers one question about the installed Benchproofer: can this benchmark be
ingested here, does this backend accept its own template, is a bundle whose
specification restates the golden patch rejected. What a case needs from the
machine is declared as a requirement string and probed before it runs, so a missing
container runtime or a hermetic run skips the case with the reason attached.

Four outcomes are kept distinct, because collapsing them is how a suite starts
reporting green for work it never did:

==========  ==================================================================
`PASSED`    the tool did what the case requires
`FAILED`    the tool did something else, and the message says what
`SKIPPED`   this machine does not meet a requirement the case declared
`ERROR`     the case itself fell over, which is a defect in the suite or the
            environment rather than a finding about the tool
==========  ==================================================================
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from ..config import Settings
from .probe import Probes

__all__ = [
    "Case",
    "CaseResult",
    "CaseStatus",
    "Context",
    "Failure",
    "Observation",
    "Unmet",
    "check",
    "equals",
]


class CaseStatus(str, Enum):
    """How one case ended."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

    def __str__(self) -> str:
        return self.value


class Unmet(Exception):
    """A case needs something this machine does not offer.

    Raised from inside a case for a requirement that can only be discovered while
    it runs, such as a dataset that is not in the cache during a hermetic run.
    Requirements known in advance belong in `Case.requires`, which is probed first.
    """


class Failure(Exception):
    """The tool did not do what a case requires."""


def check(condition: object, message: str) -> None:
    """Fail the running case unless ``condition`` holds.

    Raises:
        Failure: The condition does not hold. The message is what the report shows,
            so it should state what was expected and what happened.
    """
    if not condition:
        raise Failure(message)


def equals(actual: object, expected: object, what: str) -> None:
    """Fail the running case unless two values are equal.

    Raises:
        Failure: The values differ.
    """
    if actual != expected:
        raise Failure(f"{what}: expected {expected!r}, got {actual!r}")


@dataclass(frozen=True, slots=True)
class Observation:
    """One thing a case measured, and what it saw.

    Observations are the case's output. A passing case that reports none proves
    little, so cases are written to record the numbers they checked.
    """

    label: str
    detail: str = ""

    def describe(self) -> str:
        """One line for a terminal or a report."""
        return f"{self.label}: {self.detail}" if self.detail else self.label


@dataclass(frozen=True, slots=True)
class Context:
    """Everything a case is given.

    Each case gets its own workspace and its own bundle root, so cases can run
    concurrently and one case's artifacts can never satisfy another's assertions.
    The dataset cache is shared, because downloading the same rows once per case
    would make the suite unusable.
    """

    case_id: str
    settings: Settings
    workspace: Path
    probes: Probes

    def path(self, *parts: str) -> Path:
        """A directory inside this case's workspace, created on demand."""
        target = self.workspace.joinpath(*parts)
        target.mkdir(parents=True, exist_ok=True)
        return target

    def tuned(self, **overrides: Any) -> Settings:
        """This case's settings with a few fields replaced."""
        return self.settings.model_copy(update=overrides)


#: What a case does. It receives its context and returns what it observed; it
#: raises `Failure` when the tool misbehaved and `Unmet` when it could not look.
Procedure = Callable[[Context], Sequence[Observation]]


@dataclass(frozen=True, slots=True)
class Case:
    """One question the suite asks of the installed tool."""

    id: str
    summary: str
    procedure: Procedure
    #: Requirement strings, resolved by `probe.Probes`. All must be met to run.
    requires: tuple[str, ...] = ()
    #: True for a case that takes minutes, usually because it downloads a dataset
    #: or builds a container. Skipped unless the run asks for slow cases.
    slow: bool = False

    @property
    def group(self) -> str:
        """The part of the id before the first dot, which names the suite group."""
        return self.id.split(".", 1)[0]


@dataclass(frozen=True, slots=True)
class CaseResult:
    """One case, run."""

    case: Case
    status: CaseStatus
    duration_s: float = 0.0
    observations: tuple[Observation, ...] = field(default_factory=tuple)
    #: Why it failed, was skipped, or errored. Empty for a case that passed.
    message: str = ""

    @property
    def detail(self) -> str:
        """Why it did not pass, or what it observed when it did."""
        return self.message or "; ".join(item.describe() for item in self.observations)
