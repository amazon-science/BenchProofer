# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A nagini front-end failure is not a rejection.

Nagini exits 1 -- the rejection code -- when it never reached Viper: a type
error, an unsupported construct, a ConsistencyException, a re-raised JException,
or the unhandled `TypeError` from `translate()` returning None. Read as "does not
verify", every one of those becomes evidence the SPEC turned an impl down, and
nagini is the backend where that reading is unguarded: it is exempt from the
witness rule (`pbt.WITNESS_REQUIRED`) precisely because Viper discharges the
postcondition itself, so its reject lane concludes a rejection from "did not
verify" alone.

The same frozen `expect="verify"` case can therefore come back "rejected
(verification failed)" on one run and verified on the next, and the two are
told apart by their stderr rather than by their exit code. These tests pin the
screen, and pin that a real Viper rejection still reads as one.
"""
from __future__ import annotations

from pathlib import Path

from swebench_unified.backends.nagini import (
    FAILURE_MARKER, SUCCESS_MARKER, _dead_siblings, _no_verdict, _private_cwd,
)
from swebench_unified.gates._common import no_verdict, no_verdict_reason
from swebench_unified.verify import VerifyResult

ROOT = Path(__file__).resolve().parents[1]

# Real bytes, captured from the pinned verifier environment.
REJECTED = (f"{FAILURE_MARKER}\nErrors:\n"
            "model.py:152:16:152:41: error: The precondition of method "
            "del_present might not hold. Assertion (k in d) might not hold.\n"
            "Verification took 16.84 seconds.\n")
VERIFIED = f"{SUCCESS_MARKER}\nVerification took 18.02 seconds.\n"
TYPE_ERROR = ("Translation failed\n"
              "Type error: Incompatible types in assignment (expression has "
              'type "str", variable has type "int") (model.py@158.0)\n')
SYNTAX = "Translation failed\nType error: invalid syntax (model.py@157.0)\n"


def _r(out: str, rc: int) -> VerifyResult:
    """A result the way `NaginiBackend.check` builds one."""
    return VerifyResult(rc == 0 and SUCCESS_MARKER in out, 12.0, out, "",
                        timed_out=rc == 124, returncode=rc,
                        no_verdict_detail=_no_verdict(rc, out))


def test_a_viper_rejection_is_still_a_rejection():
    """The screen must not cost the gate the verdicts it is built on: every
    nagini reject case passes through here."""
    r = _r(REJECTED, 1)
    assert not r.success and not r.crashed
    assert not no_verdict(r)
    assert r.summary == "verification failed"


def test_a_verified_file_is_untouched():
    r = _r(VERIFIED, 0)
    assert r.success and not r.crashed and not no_verdict(r)
    assert r.summary == "verified"


def test_a_translation_failure_reaches_no_verdict():
    for out in (TYPE_ERROR, SYNTAX):
        r = _r(out, 1)
        assert not r.success, out
        assert r.crashed, "a front end that never built a Viper program judged nothing"
        assert no_verdict(r), "the reject lane concludes from this"
        assert no_verdict_reason(r) == "crash", "not a wall clock: it reproduces"


def test_the_reason_is_recorded_not_just_the_fact():
    """`_run_case` writes `r.summary` into the case record, and a battery whose
    only trace of a failure was "verification failed" is why this defect took a
    cross-driver log comparison to find."""
    r = _r(TYPE_ERROR, 1)
    assert "did not reach a verdict" in r.summary
    assert "Translation failed" in r.summary
    assert "exit 1" not in r.summary, \
        "exit 1 is the REJECTION code; naming it here reads as the verdict"


def test_an_exit_with_no_banner_at_all_reaches_no_verdict():
    """`raise e` on a JException and `modules, prog = translate(...)` unpacking
    None both exit 1 with a bare Python traceback. A list of failure banners
    would miss them, which is why the screen asks whether Viper ANNOUNCED."""
    r = _r("", 1)
    assert r.crashed and no_verdict(r)
    r2 = _r("Traceback (most recent call last):\n  File \"main.py\"\n", 1)
    assert r2.crashed and "Traceback" in r2.summary


def test_a_timeout_is_not_reclassified():
    """A wall clock is a statement about the host and `restamp_gate` restores a
    green record over one; a crash is a finding and it must not."""
    r = _r("", 124)
    assert r.timed_out and not r.crashed
    assert no_verdict_reason(r) == "timeout"
    assert not _no_verdict(124, ""), "124 is not this screen's to name"


def test_an_env_failure_keeps_its_exit_code():
    """Exit 2 is the wrapper's env-problem code and `crashed` already has it, so
    the screen must not relabel it as a missing banner."""
    r = _r("[sbn] verifier env not found", 2)
    assert r.crashed and not r.no_verdict_detail
    assert r.summary == "verifier did not reach a verdict (exit 2)"


def test_the_screen_is_nagini_only():
    """velvet and lean set no detail, so `crashed` is the function that judged
    every one of their records: a shared default must keep it that way."""
    r = VerifyResult(False, 1.0, "error: unsolved goals", "", returncode=1)
    assert not r.crashed and not no_verdict(r)
    assert r.summary == "verification failed"


# ---- the cache directory, which is why the failure wandered ----

def test_the_cwd_is_private_to_this_process():
    """nagini writes mypy's cache to the RELATIVE `.mypy_cache_strict`, so the
    cwd IS the cache. Concurrent verifications shared one under
    `cwd=PROJECT_ROOT`, all colliding on module id `__main__` for a scratch file
    each had already deleted."""
    d = _private_cwd()
    assert d.is_dir()
    assert d.name == str(__import__("os").getpid())
    assert ROOT not in d.parents and d != ROOT, \
        "never inside the project tree: it is a cache, and a pid-named " \
        "directory must not be creatable inside a bundle"


def test_the_cwd_is_stable_across_calls():
    """Per-process, not per-run: cold 18.4s against warm 16.7s/15.6s on one
    model, so a fresh directory per verification pays ~12% on every nagini run."""
    assert _private_cwd() == _private_cwd()


def test_a_live_sibling_is_never_reaped(tmp_path):
    """The reaper runs on every check; deleting a running verifier's cache
    mid-mypy would be a new way to fail a good file."""
    import os
    (tmp_path / str(os.getpid())).mkdir()
    (tmp_path / "999999999").mkdir()          # not a pid on any Linux
    (tmp_path / "notapid").mkdir()
    dead = {p.name for p in _dead_siblings(tmp_path)}
    assert dead == {"999999999"}, dead
