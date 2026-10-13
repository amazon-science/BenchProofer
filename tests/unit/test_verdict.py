# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The certification rule.

`classify` is the only authority for whether a bundle is certified, so these tests
are about one thing: no absence of evidence is ever read as evidence.
"""

from __future__ import annotations

import pytest

from benchproofer.core.verdict import Level, Outcome, SkipReason, Status, Verdict, classify

REQUIRED = ["spec.verifies", "spec.no_leakage"]


def passed(gate: str) -> Verdict:
    return Verdict(gate=gate, status=Status.PASS, summary="ok")


def skipped(gate: str, reason: SkipReason, summary: str = "") -> Verdict:
    return Verdict(gate=gate, status=Status.SKIP, skip_reason=reason, summary=summary)


def test_every_required_gate_favorable_is_certified() -> None:
    verdicts = {gate: passed(gate) for gate in REQUIRED}

    result = classify(verdicts, REQUIRED)

    assert result.outcome is Outcome.CERTIFIED
    assert result.certified
    assert not result.failed and not result.undecided and not result.missing
    assert "certified" in result.describe()


def test_a_gate_with_no_record_is_never_certified() -> None:
    result = classify({REQUIRED[0]: passed(REQUIRED[0])}, REQUIRED)

    assert result.outcome is Outcome.INCOMPLETE
    assert result.missing == [REQUIRED[1]]
    assert REQUIRED[1] in result.describe()


def test_a_failure_outranks_an_undecided_gate() -> None:
    """A bundle with one refuted claim is rejected, not merely unfinished.

    The explanation names why each gate failed or decided nothing, so whoever reads it can
    act on the undecided one as on the failed one.
    """
    verdicts = {
        REQUIRED[0]: Verdict(gate=REQUIRED[0], status=Status.FAIL, summary="counterexample"),
        REQUIRED[1]: skipped(REQUIRED[1], SkipReason.INCONCLUSIVE, "no counterexample found"),
    }

    result = classify(verdicts, REQUIRED)

    assert result.outcome is Outcome.REJECTED
    assert result.failed == [REQUIRED[0]]
    assert result.undecided == [REQUIRED[1]]
    assert result.describe().endswith(
        f"failed: {REQUIRED[0]} (counterexample); "
        f"undecided: {REQUIRED[1]} (no counterexample found)"
    )


def test_a_failed_check_about_the_task_drops_it_whatever_else_failed() -> None:
    """No artifact could address it, so the bundle is neither rejected nor unfinished."""
    task_check = "oracle.reference_resolves"
    verdicts = {
        REQUIRED[0]: Verdict(gate=REQUIRED[0], status=Status.FAIL, summary="counterexample"),
        REQUIRED[1]: passed(REQUIRED[1]),
        task_check: Verdict(gate=task_check, status=Status.FAIL, summary="own tests fail"),
    }

    dropped = classify(verdicts, [*REQUIRED, task_check], disqualifying=(task_check,))
    plain = classify(verdicts, [*REQUIRED, task_check])

    assert dropped.outcome is Outcome.DROPPED
    assert not dropped.certified
    assert dropped.failed == [REQUIRED[0], task_check]
    assert plain.outcome is Outcome.REJECTED


@pytest.mark.parametrize(
    "status", [Status.ERROR, Status.TIMEOUT, Status.WAIVED], ids=["error", "timeout", "waived"]
)
def test_a_check_about_the_task_that_did_not_fail_drops_nothing(status: Status) -> None:
    """Only a measured failure drops the task: a check that could not run said nothing."""
    task_check = "oracle.reference_resolves"
    verdicts = {gate: passed(gate) for gate in REQUIRED}
    verdicts[task_check] = Verdict(gate=task_check, status=status, summary=str(status))

    result = classify(verdicts, [*REQUIRED, task_check], disqualifying=(task_check,))

    assert result.outcome is not Outcome.DROPPED


def test_only_a_not_applicable_skip_is_compatible_with_certification() -> None:
    for reason in SkipReason:
        verdict = skipped("spec.verifies", reason, str(reason))
        assert verdict.ok is (reason is SkipReason.NOT_APPLICABLE)


@pytest.mark.parametrize(
    "verdict",
    [
        skipped(REQUIRED[0], SkipReason.INCONCLUSIVE, "budget exhausted"),
        Verdict(gate=REQUIRED[0], status=Status.ERROR, summary="crash"),
    ],
    ids=["inconclusive", "crashed"],
)
def test_a_gate_that_did_not_decide_leaves_the_bundle_incomplete(verdict: Verdict) -> None:
    """A refuter that found nothing, or a gate that crashed, has shown no defect either."""
    verdicts = {gate: passed(gate) for gate in REQUIRED}
    verdicts[REQUIRED[0]] = verdict

    result = classify(verdicts, REQUIRED)

    assert result.outcome is Outcome.INCOMPLETE
    assert result.undecided == [REQUIRED[0]]
    assert not result.failed


def test_a_waived_gate_counts_as_favorable() -> None:
    verdicts = {gate: passed(gate) for gate in REQUIRED}
    verdicts[REQUIRED[1]] = Verdict(
        gate=REQUIRED[1], status=Status.WAIVED, summary="waived by the run"
    )

    assert classify(verdicts, REQUIRED).outcome is Outcome.CERTIFIED


def test_the_level_is_carried_into_the_classification() -> None:
    result = classify({}, [], level=Level.ORACLE)

    assert result.level is Level.ORACLE
    assert "level=oracle" in result.describe()


def test_verdicts_that_pass_or_fail_are_marked_decided() -> None:
    assert passed("g").decided
    assert Verdict(gate="g", status=Status.FAIL).decided
    assert not skipped("g", SkipReason.TOOLCHAIN_ABSENT, "dafny is not installed").decided
    assert not Verdict(gate="g", status=Status.TIMEOUT).decided
