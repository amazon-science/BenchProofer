# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A gate that could not measure never overwrites one that did.

A crash, a timeout, a missing toolchain or oracle say nothing about the bundle. Where the
`manifest.json` already holds a measurement the same gate code reached from the same inputs,
that measurement is the answer about this bundle, and the failed attempt is kept beside it.
"""

from __future__ import annotations

import importlib
from typing import ClassVar

import pytest

from benchproofer.backends.base import Backend
from benchproofer.config import Settings
from benchproofer.core.bundle import Bundle
from benchproofer.core.verdict import Level, SkipReason, Status, Verdict
from benchproofer.gates.base import Gate, GateContext
from benchproofer.pipeline.adjudicate import adjudicate, certify
from benchproofer.pipeline.report import summarize
from benchproofer.registries import BACKENDS
from benchproofer.util.fsio import read_text, write_text

#: The module, which `benchproofer.pipeline` shadows with the function of the same name.
judging = importlib.import_module("benchproofer.pipeline.adjudicate")


class Answering(Gate):
    """A gate whose answer each case sets, reading the solution file."""

    id: ClassVar[str] = "spec.verifies"
    title: ClassVar[str] = "scripted"
    rationale: ClassVar[str] = "scripted"
    sources: ClassVar[tuple[str, ...]] = ("solution.*",)

    def __init__(self) -> None:
        self.answers: list[Verdict] = []

    def judge(self, context: GateContext) -> Verdict:
        return self.answers.pop(0)


@pytest.fixture
def gate(monkeypatch: pytest.MonkeyPatch) -> Answering:
    found = Answering()
    monkeypatch.setattr(judging, "_gates", lambda only: [found])
    return found


@pytest.fixture
def falsifier() -> Backend:
    return BACKENDS.get("falsifier")


def judge(bundle: Bundle, backend: Backend, settings: Settings) -> Verdict:
    return adjudicate(bundle, backend=backend, settings=settings).verdicts["spec.verifies"]


def test_a_crash_leaves_the_measurement_from_the_same_inputs_standing(
    sound: Bundle, settings: Settings, falsifier: Backend, gate: Answering
) -> None:
    gate.answers = [gate.passed("accepted"), gate.errored("the translator crashed")]

    judge(sound, falsifier, settings)
    again = judge(sound, falsifier, settings)

    assert again.status is Status.PASS and again.summary == "accepted"
    assert again.details["remeasured"]["status"] == "error"
    assert "crashed" in again.details["remeasured"]["summary"]
    assert sound.manifest().verdicts["spec.verifies"].status is Status.PASS


def test_a_missing_toolchain_leaves_a_failure_standing_too(
    sound: Bundle, settings: Settings, falsifier: Backend, gate: Answering
) -> None:
    """The rule is about what was measured, not about which answer it was."""
    absent = gate.undecided(SkipReason.TOOLCHAIN_ABSENT, "no toolchain here")
    gate.answers = [gate.failed("refuted"), absent]

    judge(sound, falsifier, settings)

    assert judge(sound, falsifier, settings).status is Status.FAIL


def test_a_changed_input_records_the_new_verdict_whatever_it_is(
    sound: Bundle, settings: Settings, falsifier: Backend, gate: Answering
) -> None:
    gate.answers = [gate.passed("accepted"), gate.timed_out("no answer in time")]

    judge(sound, falsifier, settings)
    write_text(sound.solution_path, read_text(sound.solution_path) + "\n# edited\n")

    assert judge(sound, falsifier, settings).status is Status.TIMEOUT


def test_an_undecided_reading_is_a_measurement_and_replaces_a_pass(
    sound: Bundle, settings: Settings, falsifier: Backend, gate: Answering
) -> None:
    """Inconclusive is what a gate concluded -- a stale judgment, a short review."""
    inconclusive = gate.undecided(SkipReason.INCONCLUSIVE, "too few attacks decided")
    gate.answers = [gate.passed("accepted"), inconclusive]

    judge(sound, falsifier, settings)

    assert judge(sound, falsifier, settings).status is Status.SKIP


def test_what_counts_as_measuring_nothing(gate: Answering) -> None:
    unmeasured = judging._unmeasured
    assert unmeasured(gate.errored("crash"))
    assert unmeasured(gate.timed_out("slow"))
    assert unmeasured(gate.undecided(SkipReason.ORACLE_UNAVAILABLE, "no docker"))
    assert not unmeasured(gate.undecided(SkipReason.INCONCLUSIVE, "short"))
    assert not unmeasured(gate.failed("refuted"))


class Reviewing(Answering):
    """A gate that reads the review, which a round that stops before the review leaves."""

    id: ClassVar[str] = "audit.faithfulness"


@pytest.mark.parametrize("said", [Status.FAIL, Status.PASS])
def test_a_review_s_verdict_about_files_since_changed_is_stale_whatever_it_said(
    sound: Bundle,
    settings: Settings,
    falsifier: Backend,
    monkeypatch: pytest.MonkeyPatch,
    said: Status,
) -> None:
    """It judged a solution the bundle no longer ships, so it is neither a failure nor a pass.

    The gates a program decides are judged again in every round that changed the bundle;
    one that reads the review is judged again only once the bundle gets that far.
    """
    reviewing = Reviewing()
    monkeypatch.setattr(judging, "_gates", lambda only: [reviewing])
    answer = reviewing.failed if said is Status.FAIL else reviewing.passed
    reviewing.answers = [answer("the review's answer")]
    adjudicate(sound, backend=falsifier, settings=settings, level=Level.AUDITED)
    assert ("audit.faithfulness" in certify(sound, Level.AUDITED).failed) is (
        said is Status.FAIL
    )

    write_text(sound.solution_path, read_text(sound.solution_path) + "\n# repaired\n")

    certification = certify(sound, Level.AUDITED)
    assert certification.stale == ["audit.faithfulness"]
    assert "audit.faithfulness" not in certification.failed + certification.undecided
    assert "stale: audit.faithfulness" in certification.describe()
    (row,) = summarize([sound], level=Level.AUDITED).rows
    assert row.stale == ("audit.faithfulness",) and "stale audit.faithfulness" in row.reason()
