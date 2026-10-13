# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A cap the HOST ran into is not a measurement, so it buys a re-run.

check_attack already refuses to read a timeout as "the spec rejected this
attack": it reports verify_completed=False and the audit derivation fails the
role closed. That is safe and useless -- the cell comes back for a re-audit that
hits the same load. Re-derived at falling width on the sibling corpus, the
audit-fail queue went 73 -> 51 -> 24 -> 8 with the recovery rate holding near
55% at every narrowing, which is the signature of contamination rather than of a
population of real defects.

So a timed-out verification is retried once with room. These pin that the retry
happens only for a timeout, only once, and that a real verdict is never re-run --
re-running a verification that CONCLUDED would let a flaky second answer
overwrite a real one.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from swebench_unified import adversary as adv
from swebench_unified.verify import VerifyResult

ROOT = Path(__file__).resolve().parents[1]


def _res(success: bool, timed_out: bool = False, wall: float = 1.0):
    return VerifyResult(success, wall, "", "", timed_out=timed_out,
                        returncode=124 if timed_out else 0)


@pytest.fixture()
def calls(monkeypatch):
    """Record every (timeout) _verify_once is asked for, and script replies."""
    seen: list[int] = []
    replies: list[VerifyResult] = []

    def fake_once(backend, instance_id, attack, fe, t):
        seen.append(t)
        return replies[min(len(seen) - 1, len(replies) - 1)]

    monkeypatch.setattr(adv, "_verify_once", fake_once)
    monkeypatch.setenv("SBU_ATTACK_VERIFY_TIMEOUT", "300")
    return seen, replies


def test_a_verdict_is_never_re_run(calls):
    seen, replies = calls
    replies.append(_res(False))                      # concluded: does not verify
    r = adv._verify_attack("nagini", "i", Path("a.py"), None)
    assert r.success is False
    assert seen == [300], seen


def test_a_timeout_is_re_run_with_room(calls):
    seen, replies = calls
    replies += [_res(False, timed_out=True), _res(True)]
    r = adv._verify_attack("nagini", "i", Path("a.py"), None)
    # the second answer is the measurement: the first one is a statement about
    # the host, and reporting it would fail the audit on a spec nobody read
    assert r.success is True
    assert seen == [300, 900], seen


def test_the_retry_is_bounded_and_happens_once(calls):
    """Two timeouts in a row is a host condition, not something to loop on."""
    seen, replies = calls
    replies.append(_res(False, timed_out=True))
    r = adv._verify_attack("nagini", "i", Path("a.py"), None)
    assert getattr(r, "timed_out") is True           # still reported honestly
    assert seen == [300, 900], seen


def test_the_roomy_cap_has_a_ceiling(calls, monkeypatch):
    """A base cap already generous must not multiply into hours of a core."""
    seen, replies = calls
    monkeypatch.setenv("SBU_ATTACK_VERIFY_TIMEOUT", "1200")
    replies += [_res(False, timed_out=True), _res(True)]
    adv._verify_attack("nagini", "i", Path("a.py"), None)
    assert seen == [1200, adv.ATTACK_VERIFY_RETRY_CAP], seen


def test_the_retry_can_be_turned_off(calls, monkeypatch):
    """For a deliberate divergence hunt, where a timeout IS the finding."""
    seen, replies = calls
    monkeypatch.setenv("SBU_ATTACK_VERIFY_RETRY", "0")
    replies.append(_res(False, timed_out=True))
    adv._verify_attack("nagini", "i", Path("a.py"), None)
    assert seen == [300], seen


def test_check_attack_still_calls_a_retried_timeout_inconclusive(monkeypatch):
    """The contract above check_attack does not change.

    A verification that timed out twice is still not a rejection: reading it as
    one would retire the attack and take the weakness it was probing with it.
    """
    monkeypatch.setattr(adv, "_verify_attack",
                        lambda *a, **k: _res(False, timed_out=True))
    monkeypatch.setattr(adv, "same_spec", lambda *a, **k: True)
    monkeypatch.setattr(adv, "unsound_evasions", lambda *a, **k: [])

    class _B:
        class solution:
            @staticmethod
            def read_text():
                return "frozen"

        class backend:
            language = None

    monkeypatch.setattr(adv, "_bundle", lambda *a, **k: _B())
    p = ROOT / "tests" / "test_attack_verify_retry.py"    # any existing file
    out = adv.check_attack("nagini", "i", p)
    assert out["verify_completed"] is False
    assert out["verifies"] is False
    assert "inconclusive" in out["summary"]
