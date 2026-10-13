# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Gate verdicts and the certification rule.

`classify` is the single authority for whether a bundle is certified. Every consumer
calls it rather than re-deriving the rule, because two implementations of "is this one
done" eventually disagree.
"""

from __future__ import annotations

from collections.abc import Collection, Sequence
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "Certification",
    "Level",
    "Outcome",
    "SkipReason",
    "Status",
    "Verdict",
    "classify",
    "one_line",
]


class Status(str, Enum):
    """The outcome of running one gate against one bundle."""

    PASS = "pass"  # noqa: S105 - a gate outcome, not a credential
    FAIL = "fail"
    SKIP = "skip"
    WAIVED = "waived"
    ERROR = "error"
    TIMEOUT = "timeout"

    def __str__(self) -> str:
        return self.value


class SkipReason(str, Enum):
    """Why a gate declined to judge.

    Only `NOT_APPLICABLE` is compatible with certification; the others record an absence
    of judgment. `INCONCLUSIVE` is for a result that does not support the conclusion it
    would be used for, as when a bounded refuter finds no counterexample.
    """

    NOT_APPLICABLE = "not_applicable"
    ARTIFACT_ABSENT = "artifact_absent"
    TOOLCHAIN_ABSENT = "toolchain_absent"
    ORACLE_UNAVAILABLE = "oracle_unavailable"
    INCONCLUSIVE = "inconclusive"

    def __str__(self) -> str:
        return self.value


class Level(str, Enum):
    """How much evidence a run is asking for.

    A ladder, declared weakest first: each level requires everything the one below it
    requires. `STATIC` covers what is decidable from the bundle and a verifier. `ORACLE`
    adds the benchmark's own correctness oracle, usually its tests in a container.
    `AUDITED` adds the adversarial review by a reviewer that did not build the bundle; it
    sits above `ORACLE` because a review shows the specification admits a *wrong*
    implementation only when an oracle can say the reference implementation is wrong.
    """

    STATIC = "static"
    ORACLE = "oracle"
    AUDITED = "audited"

    @property
    def rank(self) -> int:
        """Position on the ladder, so two levels can be compared."""
        return list(type(self)).index(self)

    def covers(self, other: Level) -> bool:
        """True when a run at this level also gathers `other`'s evidence."""
        return self.rank >= other.rank

    def __str__(self) -> str:
        return self.value


class Outcome(str, Enum):
    """The result of applying `classify` to a bundle's verdicts."""

    CERTIFIED = "certified"
    REJECTED = "rejected"
    INCOMPLETE = "incomplete"
    #: A check about the task itself failed, such as the benchmark's own solution failing
    #: its own tests. No artifact could address that, so the task is set aside unjudged.
    DROPPED = "dropped"

    def __str__(self) -> str:
        return self.value


class Verdict(BaseModel):
    """One gate's judgment about one bundle, with the evidence to re-check it."""

    model_config = ConfigDict(extra="forbid")

    gate: str
    status: Status
    summary: str = ""
    level: Level = Level.STATIC
    skip_reason: SkipReason | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)
    inputs: dict[str, str] = Field(default_factory=dict)
    judged_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    judge_digest: str = ""
    tool_version: str = ""
    duration_s: float = 0.0

    @property
    def ok(self) -> bool:
        """True when this verdict is compatible with certification."""
        if self.status in (Status.PASS, Status.WAIVED):
            return True
        return self.status is Status.SKIP and self.skip_reason is SkipReason.NOT_APPLICABLE

    @property
    def decided(self) -> bool:
        """True when the gate reached a judgment, whether favorable or not."""
        return self.status in (Status.PASS, Status.FAIL, Status.WAIVED) or self.ok


#: How much of a gate's summary a one-line explanation carries: enough to say why, short
#: enough that a run's log keeps one line per task readable.
_REASON = 160


def one_line(text: str, limit: int = _REASON) -> str:
    """``text`` on one line, cut to ``limit`` characters."""
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[: limit - 1].rstrip() + "…"


class Certification(BaseModel):
    """The classification of one bundle at one evidence level."""

    model_config = ConfigDict(extra="forbid")

    outcome: Outcome
    level: Level
    required: list[str] = Field(default_factory=list)
    failed: list[str] = Field(default_factory=list)
    undecided: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    #: Required gates whose recorded verdict is about files the bundle no longer has. Each
    #: is undecided, whatever it said: it judged another bundle.
    stale: list[str] = Field(default_factory=list)
    #: The summary of each failed or undecided gate's verdict, by gate id.
    reasons: dict[str, str] = Field(default_factory=dict)

    @property
    def certified(self) -> bool:
        """True when every required gate reached a favorable judgment."""
        return self.outcome is Outcome.CERTIFIED

    def describe(self) -> str:
        """One-line human-readable explanation, naming why each gate failed or is undecided."""
        if self.outcome is Outcome.CERTIFIED:
            return f"certified at level={self.level} ({len(self.required)} gates)"
        parts: list[str] = []
        for heading, gates in (("failed", self.failed), ("undecided", self.undecided)):
            if gates:
                parts.append(
                    f"{heading}: "
                    + ", ".join(
                        f"{gate} ({one_line(self.reasons[gate])})"
                        if self.reasons.get(gate)
                        else gate
                        for gate in gates
                    )
                )
        if self.stale:
            parts.append("stale: " + ", ".join(self.stale))
        if self.missing:
            parts.append("missing: " + ", ".join(self.missing))
        return f"{self.outcome} at level={self.level}; " + "; ".join(parts)


def classify(
    verdicts: dict[str, Verdict],
    required: list[str],
    level: Level = Level.STATIC,
    *,
    disqualifying: Sequence[str] = (),
    stale: Collection[str] = (),
) -> Certification:
    """Classify a bundle from its recorded verdicts.

    Args:
        verdicts: Recorded verdicts, keyed by gate id.
        required: Gate ids that must be favorable at this level.
        level: The evidence level being claimed.
        disqualifying: Required gates that judge the task rather than the bundle.
        stale: Gates whose recorded verdict was reached from files that have changed
            since, which count as undecided and are named as stale.

    Returns:
        `Outcome.DROPPED` when a required gate in ``disqualifying`` failed, `REJECTED`
        when another required gate failed, `INCOMPLETE` when a required gate is missing,
        undecided or stale, `CERTIFIED` otherwise.
    """
    failed: list[str] = []
    undecided: list[str] = []
    missing: list[str] = []
    expired: list[str] = []

    for gate_id in required:
        verdict = verdicts.get(gate_id)
        if verdict is None:
            missing.append(gate_id)
        elif gate_id in stale:
            expired.append(gate_id)
        elif verdict.status is Status.FAIL:
            failed.append(gate_id)
        elif not verdict.ok:
            undecided.append(gate_id)

    if any(gate_id in disqualifying for gate_id in failed):
        outcome = Outcome.DROPPED
    elif failed:
        outcome = Outcome.REJECTED
    elif undecided or missing or expired:
        outcome = Outcome.INCOMPLETE
    else:
        outcome = Outcome.CERTIFIED

    return Certification(
        outcome=outcome,
        level=level,
        required=list(required),
        failed=failed,
        undecided=undecided,
        missing=missing,
        stale=expired,
        reasons={gate_id: verdicts[gate_id].summary for gate_id in failed + undecided},
    )
