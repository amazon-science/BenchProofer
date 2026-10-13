# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Where a verdict that is not a pass goes: one table, and a case it lacks raises.

A repair resolves a finding, an auditor that showed too little is asked again, a missing
toolchain or oracle holds the review, and the rest goes nowhere. These cases pin each
route, and that a status or skip reason added without a row is found here rather than sent
somewhere by default.
"""

from __future__ import annotations

import re
from typing import ClassVar

import pytest

from benchproofer.config import Settings
from benchproofer.core.bundle import Bundle
from benchproofer.core.verdict import Level, SkipReason, Status, Verdict
from benchproofer.gates.base import Gate, GateContext
from benchproofer.pipeline.adjudicate import DISQUALIFYING
from benchproofer.pipeline.route import ROUTES, Route, _mark, ask_again, route, routed
from benchproofer.registries import BACKENDS

BATTERY = "spec.strength.battery"
TASK_GATE = DISQUALIFYING[0]


def finding(
    gate: str,
    summary: str = "the specification accepts wrong implementation(s): uniqueness-1",
    *,
    status: Status = Status.FAIL,
    reason: SkipReason | None = None,
    **details: object,
) -> Verdict:
    """One unfavorable verdict, in the shape a gate records it."""
    return Verdict(
        gate=gate, status=status, summary=summary, skip_reason=reason, details=dict(details)
    )


def skipped(gate: str, reason: SkipReason, **details: object) -> Verdict:
    return finding(gate, f"{gate} skipped", status=Status.SKIP, reason=reason, **details)


# ---- the table -------------------------------------------------------------------


@pytest.mark.parametrize(
    "gate", ["spec.verifies", TASK_GATE], ids=["the bundle's", "the task's"]
)
@pytest.mark.parametrize(
    ("status", "reason"),
    [
        *((status, None) for status in Status if status is not Status.SKIP),
        *((Status.SKIP, reason) for reason in SkipReason),
    ],
    ids=str,
)
def test_every_status_and_skip_reason_a_gate_records_has_a_route(
    gate: str, status: Status, reason: SkipReason | None
) -> None:
    """A status or skip reason added without a row fails here, not in a run."""
    verdict = finding(gate, status=status, reason=reason)

    assert (route(verdict) is None) is verdict.ok


@pytest.mark.parametrize(
    "verdict",
    [
        pytest.param(finding(BATTERY, traceback="..."), id="a failure with a traceback"),
        pytest.param(finding(BATTERY, status=Status.SKIP), id="a skip that gives no reason"),
        pytest.param(
            skipped(
                "audit.spec_completeness",
                SkipReason.INCONCLUSIVE,
                required=5,
                unruled={"attack-1": "cannot be determined by execution"},
            ),
            id="two marks at once",
        ),
    ],
)
def test_a_verdict_the_table_has_no_row_for_raises(verdict: Verdict) -> None:
    with pytest.raises(ValueError, match=re.escape(verdict.gate)):
        route(verdict)


def test_every_row_of_the_table_is_reached_by_a_case_below() -> None:
    """So a row nothing exercises is found, as well as a case no row covers."""
    reached = {(verdict.status, verdict.skip_reason, _mark(verdict)) for verdict, _ in ROUTED}

    assert reached == set(ROUTES)


#: At least one case per row of the table: a verdict, and where it goes.
ROUTED: list[tuple[Verdict, Route]] = [
    # A finding, and a falsifier's report that a specification accepted a wrong
    # implementation: no counterexample within a budget is not a proof of none, and
    # strengthening the specification is still the answer.
    (finding(BATTERY), Route.REPAIR),
    (finding(BATTERY, status=Status.SKIP, reason=SkipReason.INCONCLUSIVE), Route.REPAIR),
    # Submissions aimed at a specification the bundle no longer ships did not show too
    # little: they answer nothing about it.
    (
        skipped("audit.spec_completeness", SkipReason.INCONCLUSIVE, drifted=["attack-1"]),
        Route.REPAIR,
    ),
    # A translator crash or a search that did not finish stops on what the file says, and
    # a repair can say it another way: the solution, a pre-fix implementation's own proof,
    # a mutant of the solution.
    (
        finding(
            "spec.verifies",
            "the checker gave no verdict: nagini crashed: AssertionError",
            status=Status.ERROR,
            backend="nagini",
        ),
        Route.REPAIR,
    ),
    (
        finding(
            "spec.discriminates",
            "the checker reached no verdict on pre-fix implementation(s): twin",
            status=Status.TIMEOUT,
            undecided=["twin"],
        ),
        Route.REPAIR,
    ),
    # An auditor that showed too little.
    (
        skipped("audit.spec_completeness", SkipReason.INCONCLUSIVE, filed=5, required=5),
        Route.ASK_AGAIN,
    ),
    (
        skipped(
            "audit.spec_soundness",
            SkipReason.INCONCLUSIVE,
            unruled={"control-1": "the prover refuses it"},
        ),
        Route.ASK_AGAIN,
    ),
    (
        skipped("audit.faithfulness", SkipReason.INCONCLUSIVE, stale=["solution:spec"]),
        Route.ASK_AGAIN,
    ),
    # What the gate needed is not here, and the review needs it as much.
    (skipped("spec.verifies", SkipReason.TOOLCHAIN_ABSENT), Route.HOLD),
    (skipped("impl.conformance", SkipReason.ORACLE_UNAVAILABLE), Route.HOLD),
    (skipped(TASK_GATE, SkipReason.TOOLCHAIN_ABSENT), Route.HOLD),
    (skipped(TASK_GATE, SkipReason.ORACLE_UNAVAILABLE), Route.HOLD),
    # A gate that raised records its traceback: that defect is the tool's.
    (
        finding(
            "spec.strength.mutation",
            "KeyError: 'solution'",
            status=Status.ERROR,
            traceback="...",
        ),
        Route.STOP,
    ),
    # No review to read: the review is what the loop runs next, not a repair.
    (skipped("audit.equivalence", SkipReason.ARTIFACT_ABSENT), Route.STOP),
    # Nothing drafted for the task answers a check of the task itself.
    (finding(TASK_GATE), Route.STOP),
    (finding(TASK_GATE, status=Status.ERROR, traceback="..."), Route.STOP),
    (finding(TASK_GATE, status=Status.TIMEOUT), Route.STOP),
    (skipped(TASK_GATE, SkipReason.INCONCLUSIVE), Route.STOP),
    (skipped(TASK_GATE, SkipReason.ARTIFACT_ABSENT), Route.STOP),
]


@pytest.mark.parametrize(
    ("verdict", "where"),
    [
        pytest.param(
            verdict, where, id=f"{verdict.gate} {verdict.status} {verdict.skip_reason}"
        )
        for verdict, where in ROUTED
    ],
)
def test_where_each_kind_of_verdict_goes(verdict: Verdict, where: Route) -> None:
    assert route(verdict) is where


class Crashing(Gate):
    """A gate whose own code raises."""

    id: ClassVar[str] = "spec.strength.mutation"
    title: ClassVar[str] = "crashing"
    rationale: ClassVar[str] = "crashing"

    def judge(self, context: GateContext) -> Verdict:
        raise KeyError("solution")


def test_a_gate_that_raised_stops_there(sound: Bundle, settings: Settings) -> None:
    """`Gate.run` records the crash with its traceback, which is what the table reads."""
    verdict = Crashing().run(
        GateContext(bundle=sound, backend=BACKENDS.get("falsifier"), settings=settings)
    )

    assert verdict.status is Status.ERROR
    assert route(verdict) is Route.STOP


# ---- a bundle's verdicts ------------------------------------------------------------


def test_a_bundle_whose_task_fails_its_own_tests_is_not_repaired_at_all() -> None:
    """The task is dropped, so even the suite's finding beside it is no one's to resolve."""
    verdicts = {TASK_GATE: finding(TASK_GATE), BATTERY: finding(BATTERY)}

    routes = routed(verdicts, Level.ORACLE)

    assert [verdict.gate for verdict in routes[Route.STOP]] == [BATTERY, TASK_GATE]
    assert routes[Route.REPAIR] == []


def test_an_oracle_that_could_not_check_the_task_is_not_repaired_but_drops_nothing() -> None:
    """A redraft cannot meet the oracle, and a check that did not run says nothing of it."""
    verdicts = {
        TASK_GATE: finding(TASK_GATE, status=Status.ERROR),
        BATTERY: finding(BATTERY),
    }

    assert [verdict.gate for verdict in routed(verdicts, Level.ORACLE)[Route.REPAIR]] == [
        BATTERY
    ]


def test_a_review_that_showed_too_little_asks_for_a_review_not_a_repair() -> None:
    """Nothing it showed found fault with the specification; a finding beside it is repaired."""
    short = [
        skipped("audit.spec_completeness", SkipReason.INCONCLUSIVE, filed=5, required=5),
        skipped("audit.faithfulness", SkipReason.INCONCLUSIVE, stale=["solution:spec"]),
        skipped("audit.equivalence", SkipReason.INCONCLUSIVE, stale=["solution:impl"]),
    ]
    beside = finding("audit.no_disclosure", "the spec gives it away")

    routes = routed({verdict.gate: verdict for verdict in (*short, beside)}, Level.AUDITED)

    assert routes[Route.ASK_AGAIN] == short
    assert routes[Route.REPAIR] == [beside]


def test_a_case_without_a_ruling_asks_the_attack_validation_auditor_once_per_state() -> None:
    """Not the attack auditor whose submissions the gate reads, and not twice on one bundle."""
    unruled = {
        gate: skipped(
            gate,
            SkipReason.INCONCLUSIVE,
            unruled={f"{noun}-1": "cannot be determined by execution"},
        )
        for gate, noun in (
            ("audit.spec_completeness", "attack"),
            ("audit.spec_soundness", "control"),
        )
    }
    asked: set[tuple[str, tuple[str, ...]]] = set()

    assert ask_again(unruled, Level.AUDITED, asked) == ("validation",)
    assert ask_again(unruled, Level.AUDITED, asked) == ()
    assert asked == {
        ("audit.spec_completeness", ("attack-1",)),
        ("audit.spec_soundness", ("control-1",)),
    }


@pytest.mark.parametrize(
    ("gate", "mark"),
    [
        ("audit.faithfulness", "unruled"),
        ("audit.faithfulness", "unshown"),
        ("audit.equivalence", "unruled"),
        ("audit.no_disclosure", "required"),
        ("audit.axiom_soundness", "stale"),
        ("audit.faithfulness", "required"),
    ],
)
def test_a_mark_is_read_only_off_the_gates_that_write_it(gate: str, mark: str) -> None:
    """The judging verdicts decide; the fuzz auditor files no judgment.

    And the faithfulness auditor is asked again only for a stale judgment: it rules on no
    submission, so no listing of them marks its verdict.
    """
    verdict = skipped(gate, SkipReason.INCONCLUSIVE, **{mark: True})

    assert route(verdict) is Route.REPAIR


def test_a_finding_from_a_gate_this_level_does_not_require_is_left_out() -> None:
    """Otherwise a static run would repair a bundle over a review it never read."""
    verdicts = {"audit.faithfulness": finding("audit.faithfulness", "the spec drops a case")}

    assert routed(verdicts, Level.STATIC)[Route.REPAIR] == []
    assert [verdict.gate for verdict in routed(verdicts, Level.AUDITED)[Route.REPAIR]] == [
        "audit.faithfulness"
    ]


def test_findings_reach_the_model_in_gate_order() -> None:
    """One order, fixed by the required set, so two runs show the same brief."""
    verdicts = {
        gate: finding(gate) for gate in ("spec.strength.mutation", "spec.no_leakage", BATTERY)
    }

    found = [verdict.gate for verdict in routed(verdicts, Level.STATIC)[Route.REPAIR]]

    assert found == ["spec.no_leakage", "spec.strength.mutation", BATTERY]
