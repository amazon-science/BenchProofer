# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Where a verdict that is not a pass goes, read off one table.

Every caller asks `route`, or `routed` for a bundle's verdicts, rather than reading a
verdict's status and details itself: two readings of it, however carefully mirrored,
disagree eventually. `ROUTES` sends a verdict one of four ways (`Route`) by its status,
its skip reason and its mark, the one thing beside them that changes where it goes
(`MARKS`, and `TASK` for a gate about the task itself):

* to the **repair**: a finding, a file the bundle lacks among them, since nothing else
  writes it once the first draft is written; an undecided verdict
  a repair can address (`inconclusive`), as when a bounded search found no counterexample
  to a wrong implementation; and an error or a timeout of the checker or a program on one
  of the bundle's own files, since what stopped it is in the file and a repair can say it
  another way.
* to the auditor, **asked again**: an auditor that showed too little (below).
* **holding the review**: a toolchain or an oracle that is not here, which the review needs
  as much as the gate did. No repair addresses it.
* nowhere, so it **stops** there: a crash of Benchproofer's own, which `Gate.run` records
  with its traceback; a bundle or a review that is not there to read; and every verdict of a
  gate about the task itself (`adjudicate.DISQUALIFYING`) but a missing toolchain or
  oracle, since nothing drafted for the task addresses it. A verdict that stops does not
  hold the review back. Every verdict of a bundle whose task failed such a gate stops:
  the task is dropped.

A verdict whose status, skip reason and mark have no row raises, so a gate that records a
detail on a status it does not belong with is found rather than sent somewhere by default.
A mark is read only off the gates that write it (`MARKS`).

An auditor is asked again, before any repair, about the unchanged bundle when it showed too
little: fewer of its attacks or controls were decided than the run asks for (`required`), it
holds a judgment that is stale (`stale`), or, for the attack validation auditor, an attack or a
control that cannot be determined by execution has no ruling of its (`gates.audit.UNRULED`,
which lists them). A repair would be told to correct what nothing showed wrong. Each question,
the gate with the ids it lists under `UNRULED`, is asked once per state of the bundle
(`ask_again`): asked the same question of the same files, the auditor would fall short the same
way, round after round. An attack or a control listed after the auditor last reported makes it a
new question, and so does a repair that changes the bundle. One the attack validation auditor
still leaves without a ruling after that is discarded by its gate rather than asked a third
time. Asking again spends no repair, so an auditor is asked even when the budget is spent, and
the round that asks it judges only the gates that read the review (`pipeline.run`). A finding
beside the shortfall waits for the auditor's report, so the repair that follows addresses both;
with nothing beside it, an auditor that fell short again ends the task.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum

from ..audit.session import LANE_OF, SUBMISSION_GATES, Lane
from ..core.verdict import Level, SkipReason, Status, Verdict
from ..gates.audit import UNRULED
from .adjudicate import DISQUALIFYING, required_gates

__all__ = ["MARKS", "ROUTES", "TASK", "Question", "Route", "ask_again", "route", "routed"]


class Route(str, Enum):
    """Where a verdict that is not a pass goes."""

    REPAIR = "repair"
    ASK_AGAIN = "ask again"
    HOLD = "hold the review"
    STOP = "stop"

    def __str__(self) -> str:
        return self.value


#: The details that change where a verdict goes, each with the gates that write it, the only
#: ones it is read off, or None where every gate may: `Gate.run` records a crash with its
#: traceback.
MARKS: dict[str, frozenset[str] | None] = {
    "traceback": None,
    "required": frozenset(SUBMISSION_GATES),
    UNRULED: frozenset(SUBMISSION_GATES),
    "stale": frozenset({"audit.faithfulness", "audit.equivalence", "audit.no_disclosure"}),
}
#: The mark of every verdict of a gate about the task itself (`adjudicate.DISQUALIFYING`).
TASK = "task"

#: Where a verdict goes, by its status, skip reason and mark ("" for none). A verdict
#: compatible with certification goes nowhere and has no row.
ROUTES: dict[tuple[Status, SkipReason | None, str], Route] = {
    (Status.FAIL, None, ""): Route.REPAIR,
    (Status.ERROR, None, ""): Route.REPAIR,
    (Status.TIMEOUT, None, ""): Route.REPAIR,
    (Status.SKIP, SkipReason.INCONCLUSIVE, ""): Route.REPAIR,
    (Status.SKIP, SkipReason.INCONCLUSIVE, "required"): Route.ASK_AGAIN,
    (Status.SKIP, SkipReason.INCONCLUSIVE, UNRULED): Route.ASK_AGAIN,
    (Status.SKIP, SkipReason.INCONCLUSIVE, "stale"): Route.ASK_AGAIN,
    (Status.SKIP, SkipReason.TOOLCHAIN_ABSENT, ""): Route.HOLD,
    (Status.SKIP, SkipReason.ORACLE_UNAVAILABLE, ""): Route.HOLD,
    (Status.SKIP, SkipReason.TOOLCHAIN_ABSENT, TASK): Route.HOLD,
    (Status.SKIP, SkipReason.ORACLE_UNAVAILABLE, TASK): Route.HOLD,
    (Status.ERROR, None, "traceback"): Route.STOP,
    (Status.SKIP, SkipReason.ARTIFACT_ABSENT, ""): Route.STOP,
    (Status.FAIL, None, TASK): Route.STOP,
    (Status.ERROR, None, TASK): Route.STOP,
    (Status.TIMEOUT, None, TASK): Route.STOP,
    (Status.SKIP, SkipReason.INCONCLUSIVE, TASK): Route.STOP,
    (Status.SKIP, SkipReason.ARTIFACT_ABSENT, TASK): Route.STOP,
}


#: What an auditor is asked again about: the gate whose verdict fell short, and the ids
#: of the submissions the gates list for it to rule on (`gates.audit.UNRULED`).
Question = tuple[str, tuple[str, ...]]


def route(verdict: Verdict) -> Route | None:
    """Where ``verdict`` goes (`ROUTES`), or None when it is compatible with certification.

    Raises:
        ValueError: The table has no row for its status, skip reason and mark, or it
            carries more than one mark.
    """
    if verdict.ok:
        return None
    mark = _mark(verdict)
    found = ROUTES.get((verdict.status, verdict.skip_reason, mark))
    if found is None:
        raise ValueError(
            f"no route for a {verdict.gate} verdict with status {verdict.status}, skip "
            f"reason {verdict.skip_reason} and mark {mark or 'none'}: {verdict.summary}"
        )
    return found


def routed(verdicts: Mapping[str, Verdict], level: Level) -> dict[Route, list[Verdict]]:
    """The verdicts of the gates ``level`` requires that do not pass, by where each goes.

    In gate order within each route. Every one stops where a gate about the task itself
    failed, at whatever level: the task is dropped, and nothing drafted for it addresses that.
    """
    dropped = any(
        (verdict := verdicts.get(gate)) is not None and verdict.status is Status.FAIL
        for gate in DISQUALIFYING
    )
    found: dict[Route, list[Verdict]] = {where: [] for where in Route}
    for verdict in (verdicts[gate] for gate in required_gates(level) if gate in verdicts):
        where = route(verdict)
        if where is not None:
            found[Route.STOP if dropped else where].append(verdict)
    return found


def ask_again(
    verdicts: Mapping[str, Verdict], level: Level, asked: set[Question]
) -> tuple[Lane, ...]:
    """The auditors to ask again about the bundle as it stands, before any repair.

    The auditors of the verdicts `routed` sends to `Route.ASK_AGAIN` whose question is not in
    ``asked``, which records it; in gate order, each auditor named once. ``asked`` holds the
    questions asked of the bundle as it stands, so the caller empties it when a repair
    changes the bundle.
    """
    new = [
        verdict
        for verdict in routed(verdicts, level)[Route.ASK_AGAIN]
        if _question(verdict) not in asked
    ]
    asked.update(_question(verdict) for verdict in new)
    return tuple(dict.fromkeys(_lane(verdict) for verdict in new))


def _lane(verdict: Verdict) -> Lane:
    """The auditor a verdict `routed` sends to `ASK_AGAIN` asks again.

    The one whose work its gate reads (`LANE_OF`), except a submission gate's that lists,
    without a ruling, attacks or controls that cannot be determined by execution (`UNRULED`),
    which asks the attack validation auditor.
    """
    return "validation" if _mark(verdict) == UNRULED else LANE_OF[verdict.gate]


def _mark(verdict: Verdict) -> str:
    """The one thing beside its status and skip reason that changes where ``verdict`` goes.

    `TASK` for a gate about the task itself; otherwise the detail of `MARKS` it carries, read
    only off a gate that writes it, or "" for none.

    Raises:
        ValueError: It carries more than one.
    """
    if verdict.gate in DISQUALIFYING:
        return TASK
    found = [
        key
        for key, gates in MARKS.items()
        if key in verdict.details and (gates is None or verdict.gate in gates)
    ]
    if len(found) > 1:
        raise ValueError(f"a {verdict.gate} verdict carries {' and '.join(found)}")
    return found[0] if found else ""


def _question(verdict: Verdict) -> Question:
    """What an auditor is asked again about, for a verdict `routed` sends to `ASK_AGAIN`."""
    listed = verdict.details.get(UNRULED) or ()
    return verdict.gate, tuple(sorted(str(name) for name in listed))
