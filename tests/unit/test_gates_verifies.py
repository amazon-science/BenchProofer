# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The gate that asks the question a bundle exists to answer.

Two answers are needed from a checker that replays a proof the file writes, not one.
`check` reports that the file elaborated, which `sorry` does; `Backend.closure` reports
which axioms each claim rests on. What the cases here pin down is the arithmetic between
them: a pass requires both, a proof found open is a failure of the bundle, and a closure
question that went unanswered is an error to be re-measured rather than a finding about
the artifact.
"""

from __future__ import annotations

from pathlib import Path

from benchproofer.backends.base import CheckResult, Closure
from benchproofer.config import Settings
from benchproofer.core.bundle import Bundle
from benchproofer.core.verdict import Level, Status
from benchproofer.gates.verifies import VerifiesGate
from doubles import Proving, Rigged, Screening


class Replaying(Proving):
    """A prover that also reports what its accepted proof rests on.

    The answer is scripted rather than derived, because what is under test is what the
    gate makes of it. `asked` records the source the question was put about, so a case
    can tell a closure question about the shipped file from one about anything else.
    """

    name = "replaying"

    def __init__(self, answer: Closure | None) -> None:
        self.answer = answer
        self.asked: list[str] = []

    def closure(
        self, source: str, *, workdir: Path, timeout_s: float = 120.0
    ) -> Closure | None:
        self.asked.append(source)
        return self.answer


def context(
    bundle: Bundle,
    settings: Settings,
    *,
    backend: Screening | None = None,
    answer: CheckResult | None = None,
) -> Rigged:
    """A context whose checker accepts the shipped file unless a case says otherwise."""
    return Rigged(
        bundle=bundle,
        backend=backend or Proving(),
        settings=settings,
        level=Level.STATIC,
        answers={"solution": answer or CheckResult.ok("proved")},
    )


def test_a_checker_that_accepted_the_file_and_a_closed_proof_pass(
    sound: Bundle, settings: Settings
) -> None:
    backend = Replaying(Closure(True, "2 claim(s) closed", depends={"c": ["propext"]}))
    rigged = context(sound, settings, backend=backend)

    verdict = VerifiesGate().judge(rigged)

    assert verdict.status is Status.PASS
    assert "2 claim(s) closed" in verdict.summary
    assert verdict.details["axioms"] == {"c": ["propext"]}
    assert backend.asked == [rigged.solution]


def test_a_proof_found_open_fails_the_bundle_even_though_the_file_elaborated(
    sound: Bundle, settings: Settings
) -> None:
    """This is the whole point of asking twice.

    An accepting exit code from a file whose proof is a hole is what every verdict
    downstream would otherwise read as a proof.
    """
    backend = Replaying(Closure(False, "the proof rests on `sorryAx`"))

    verdict = VerifiesGate().judge(context(sound, settings, backend=backend))

    assert verdict.status is Status.FAIL
    assert "sorryAx" in verdict.summary


def test_a_closure_question_that_went_unanswered_is_an_error_not_a_failure(
    sound: Bundle, settings: Settings
) -> None:
    """A re-elaboration that starved found nothing about the proof.

    Recording it as a rejection is how load on a machine becomes an apparent defect in
    an artifact; an error says the cell is to be measured again.
    """
    backend = Replaying(Closure(False, "reached no result: heartbeats", settled=False))

    verdict = VerifiesGate().judge(context(sound, settings, backend=backend))

    assert verdict.status is Status.ERROR
    assert "reached no result" in verdict.summary


def test_a_checker_that_replays_no_declaration_is_judged_on_its_verdict_alone(
    sound: Bundle, settings: Settings
) -> None:
    """Nagini, Dafny, CrossHair, Velvet: the obligation is attached to the code.

    There is no separate claim, so there is nothing whose axioms could differ, and the
    gate must not invent a second question to fail the bundle on.
    """
    verdict = VerifiesGate().judge(context(sound, settings, backend=Replaying(None)))

    assert verdict.status is Status.PASS
    assert "axioms" not in verdict.details


def test_a_rejected_file_is_never_asked_what_its_proof_rests_on(
    sound: Bundle, settings: Settings
) -> None:
    """One verifier invocation is minutes under Velvet, and the answer changes nothing."""
    backend = Replaying(Closure(True, "closed"))
    rigged = context(sound, settings, backend=backend, answer=CheckResult.no("cents=40"))

    verdict = VerifiesGate().judge(rigged)

    assert verdict.status is Status.FAIL
    assert backend.asked == []
