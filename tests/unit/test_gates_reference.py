# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The gate that asks whether the benchmark's own solution passes the benchmark's tests.

A failure here drops the task from both sides of a comparison, so one unlucky run must not
decide it: the reference is run again, and resolving on any attempt counts.
"""

from __future__ import annotations

from benchproofer.config import Settings
from benchproofer.core.bundle import Bundle
from benchproofer.core.verdict import Level, Status
from benchproofer.gates.reference import ATTEMPTS, ReferenceResolvesGate
from benchproofer.oracles.base import OracleResult
from doubles import Proving, Rigged


def judged(bundle: Bundle, settings: Settings, *answers: OracleResult) -> tuple[Status, Rigged]:
    """The gate's verdict when the oracle gives ``answers`` in order, the last one reused."""
    rigged = Rigged(
        bundle=bundle,
        backend=Proving(),
        settings=settings,
        level=Level.ORACLE,
        rulings={"reference": answers},
    )
    return ReferenceResolvesGate().judge(rigged).status, rigged


def test_a_reference_that_resolves_on_a_later_attempt_passes(
    sound: Bundle, settings: Settings
) -> None:
    status, rigged = judged(
        sound, settings, OracleResult.no("1 PASS_TO_PASS test broke"), OracleResult.ok("passed")
    )

    assert status is Status.PASS
    assert len(rigged.judged) == 2


def test_a_reference_that_never_resolves_fails_after_every_attempt(
    sound: Bundle, settings: Settings
) -> None:
    status, rigged = judged(sound, settings, OracleResult.no("1 PASS_TO_PASS test broke"))

    assert status is Status.FAIL
    assert len(rigged.judged) == ATTEMPTS


def test_a_reference_that_resolves_at_once_is_run_once(
    sound: Bundle, settings: Settings
) -> None:
    status, rigged = judged(sound, settings, OracleResult.ok("passed"))

    assert status is Status.PASS
    assert len(rigged.judged) == 1


def test_a_verdict_recorded_from_the_same_task_is_kept_and_the_tests_are_not_run_again(
    sound: Bundle, settings: Settings
) -> None:
    gate = ReferenceResolvesGate()
    first = Rigged(
        bundle=sound,
        backend=Proving(),
        settings=settings,
        level=Level.ORACLE,
        rulings={"reference": OracleResult.ok("passed")},
    )
    sound.record([gate.run(first)])

    again = Rigged(bundle=sound, backend=Proving(), settings=settings, level=Level.ORACLE)

    assert gate.run(again).status is Status.PASS
    assert again.judged == []


def test_a_task_whose_frozen_files_changed_is_run_again(
    sound: Bundle, settings: Settings
) -> None:
    gate = ReferenceResolvesGate()
    first = Rigged(
        bundle=sound,
        backend=Proving(),
        settings=settings,
        level=Level.ORACLE,
        rulings={"reference": OracleResult.ok("passed")},
    )
    sound.record([gate.run(first)])
    sound.reference_path.write_text(sound.reference_path.read_text() + "\n")

    again = Rigged(bundle=sound, backend=Proving(), settings=settings, level=Level.ORACLE)

    assert gate.run(again).status is Status.FAIL
    assert len(again.judged) == ATTEMPTS


def test_a_verdict_that_measured_nothing_is_not_kept(sound: Bundle, settings: Settings) -> None:
    gate = ReferenceResolvesGate()
    first = Rigged(
        bundle=sound,
        backend=Proving(),
        settings=settings,
        level=Level.ORACLE,
        rulings={"reference": OracleResult.unavailable("no image")},
    )
    sound.record([gate.run(first)])

    again = Rigged(
        bundle=sound,
        backend=Proving(),
        settings=settings,
        level=Level.ORACLE,
        rulings={"reference": OracleResult.ok("passed")},
    )

    assert gate.run(again).status is Status.PASS
    assert again.judged == ["reference"]
