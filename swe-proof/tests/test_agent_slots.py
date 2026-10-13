# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Cap concurrent agent CLIs across processes, and never block a launch forever.

Past some number of simultaneous CLIs a launch fails with no diagnostic (a result
carrying is_error=true, errors=[], subtype="success"). The consequence is not a
slow run but a wrong artifact, because a role that never ran is recorded fail and
reads as "this spec admits a wrong implementation". So launches queue.

The slots are flock'd files rather than a counter, so a killed holder releases its
slot; and exhaustion fails OPEN, because a launch that might fail is recoverable
by the caller's retry while a launch that never happens is not.
"""
from __future__ import annotations

import multiprocessing as mp
import sys
import time
from pathlib import Path

import pytest


def _reload(monkeypatch, slot_dir: Path, slots: str):
    # delitem, not del: monkeypatch restores the original module object at
    # teardown, so a reload here cannot leave a second copy of the agent module
    # installed for every test that runs after this file (see the same note in
    # test_agent_auth.py -- a leaked copy makes a later string-target patch
    # silently miss).
    #
    # The package attribute needs the same undo, and for the same reason:
    # `import_module` rebinds `swebench_unified.agent`, `delitem` restores only
    # `sys.modules`, and afterwards `import swebench_unified.agent as m` and
    # `from ..agent import f` resolve to DIFFERENT module objects. Registered
    # before the re-import so the remembered value is the original.
    import swebench_unified

    monkeypatch.setenv("SBU_AGENT_SLOTS", slots)
    monkeypatch.setenv("SBU_AGENT_SLOT_DIR", str(slot_dir))
    monkeypatch.setattr(swebench_unified, "agent",
                        getattr(swebench_unified, "agent", None), raising=False)
    for mod in [m for m in list(sys.modules) if m.endswith("swebench_unified.agent")]:
        monkeypatch.delitem(sys.modules, mod, raising=False)
    import importlib
    return importlib.import_module("swebench_unified.agent")


def test_slots_are_exclusive_up_to_the_cap(tmp_path, monkeypatch):
    ag = _reload(monkeypatch, tmp_path / "slots", "2")
    with ag._agent_slot(1) as a, ag._agent_slot(1) as b:
        assert a is True and b is True
        # the third waits out its budget and then proceeds anyway (fail-open)
        t0 = time.monotonic()
        with ag._agent_slot(1) as c:
            assert c is False, "a third holder must not get a slot"
        assert time.monotonic() - t0 >= 1.0, "it must actually have waited"


def test_a_released_slot_is_reusable(tmp_path, monkeypatch):
    ag = _reload(monkeypatch, tmp_path / "slots", "1")
    with ag._agent_slot(1) as a:
        assert a is True
    with ag._agent_slot(1) as b:
        assert b is True, "the slot must be free again after the block exits"


def test_zero_disables_the_gate_entirely(tmp_path, monkeypatch):
    """An operator on a machine where the limit does not bite should pay nothing
    for it, and must not be able to deadlock on it."""
    ag = _reload(monkeypatch, tmp_path / "slots", "0")
    with ag._agent_slot(0) as a, ag._agent_slot(0) as b, ag._agent_slot(0) as c:
        assert (a, b, c) == (True, True, True)
    assert not (tmp_path / "slots").exists(), "no slot dir when disabled"


def _hold(slot_dir: str, secs: float, q) -> None:
    """Hold a slot in a separate process, reporting the config it holds it under.

    The config goes over the queue because `got=True` alone cannot distinguish
    "acquired the slot" from "the cap was disabled in this process", and a test
    that cannot tell those apart passes when the cap does not work.
    """
    import importlib
    import os
    import sys as _sys
    os.environ["SBU_AGENT_SLOTS"] = "1"
    os.environ["SBU_AGENT_SLOT_DIR"] = slot_dir
    for k in [k for k in list(_sys.modules) if k.endswith("swebench_unified.agent")]:
        del _sys.modules[k]
    ag = importlib.import_module("swebench_unified.agent")
    with ag._agent_slot(1) as got:
        q.put(("got", bool(got), ag.AGENT_SLOTS, str(ag._SLOT_DIR)))
        time.sleep(secs)


@pytest.mark.skipif(sys.platform == "win32", reason="flock/fork")
def test_the_cap_holds_across_processes(tmp_path, monkeypatch):
    """The point of flock: two DRIVERS on one host share the cap. An in-process
    semaphore would not have caught the failure this exists for."""
    ag = _reload(monkeypatch, tmp_path / "slots", "1")
    assert ag.AGENT_SLOTS == 1
    ctx = mp.get_context("fork")
    q = ctx.Queue()
    p = ctx.Process(target=_hold, args=(str(tmp_path / "slots"), 6.0, q))
    p.start()
    try:
        got, holds, slots, sdir = q.get(timeout=20)
        assert (got, holds, slots) == ("got", True, 1), (got, holds, slots)
        assert sdir == str(tmp_path / "slots"), sdir
        t0 = time.monotonic()
        with ag._agent_slot(1) as mine:
            assert mine is False, "the other process holds the only slot"
        # and it gave up on ITS OWN budget, not on the holder's release: a wait
        # that silently outlives timeout_s is how a bounded queue becomes a stall.
        assert 1.0 <= time.monotonic() - t0 < 5.0, "fail-open must honour timeout_s"
    finally:
        p.join(timeout=20)
        if p.is_alive():  # pragma: no cover - only on a stuck child
            p.terminate()


# --------------------------------------------------------------------------
# the queue budget
#
# Queueing and running are spent from the same wall clock. A launch that queues
# for its whole step cap and THEN fails open has nothing left to run with: it is
# killed at the cap having measured nothing, and the harness records that
# non-measurement as a failed audit role -- "this spec admits a wrong
# implementation" -- about a bundle no agent ever looked at. Seen in practice:
# roles killed at the 5400s cap having submitted ZERO attacks, with CLIs still
# alive past the cap that was supposed to bound them.


def test_the_queue_budget_is_a_fraction_of_the_step_cap(tmp_path, monkeypatch):
    """The bug this pins: queueing for the step's WHOLE cap.

    Waiting `timeout_s` for a slot and then failing open is the worst of both --
    the launch happens (so it adds to the oversubscription that caused the wait)
    and it happens too late to do anything (so it is recorded as a verdict).
    """
    ag = _reload(monkeypatch, tmp_path / "slots", "64")
    assert ag._slot_wait_budget(5400) == 300, "must not queue for the whole cap"
    assert ag._slot_wait_budget(600) == 60
    assert ag._slot_wait_budget(3600) == 300, "and is capped in absolute terms"


def test_a_short_step_still_gets_a_usable_queue(tmp_path, monkeypatch):
    """A fraction of a small cap rounds down to a queue too brief to ever win a
    slot on a busy host, which makes the cap advisory in exactly the conditions
    it exists to enforce. So the budget floors."""
    ag = _reload(monkeypatch, tmp_path / "slots", "64")
    assert ag._slot_wait_budget(120) == ag.SLOT_WAIT_MIN_S


def test_the_queue_never_outlasts_the_step_it_serves(tmp_path, monkeypatch):
    """Below the floor the cap wins: a 10s step must not queue for 30s, or the
    wait alone overruns the budget the caller is holding a deadline against."""
    ag = _reload(monkeypatch, tmp_path / "slots", "64")
    assert ag._slot_wait_budget(10) == 10
    assert ag._slot_wait_budget(0) == 0
    assert ag._slot_wait_budget(-5) == 0, "a nonsense cap must not become a wait"


def test_the_queue_budget_is_tunable(tmp_path, monkeypatch):
    """An operator whose host queues legitimately needs to raise it without
    editing code, and the fraction and the ceiling bind independently."""
    ag = _reload(monkeypatch, tmp_path / "slots", "64")
    monkeypatch.setenv("SBU_AGENT_SLOT_WAIT_MAX", "1200")
    monkeypatch.setenv("SBU_AGENT_SLOT_WAIT_FRAC", "0.5")
    ag = _reload(monkeypatch, tmp_path / "slots2", "64")
    assert ag._slot_wait_budget(1000) == 500, "the fraction binds below the ceiling"
    assert ag._slot_wait_budget(5400) == 1200, "the ceiling binds above it"


def test_a_dead_holder_does_not_leak_its_slot(tmp_path, monkeypatch):
    """A killed driver is the normal case on a long run, and a counter in a file
    would strand a slot forever."""
    ag = _reload(monkeypatch, tmp_path / "slots", "1")
    ctx = mp.get_context("fork")
    q = ctx.Queue()
    p = ctx.Process(target=_hold, args=(str(tmp_path / "slots"), 60.0, q))
    p.start()
    try:
        got, holds, slots, _ = q.get(timeout=20)
        assert (got, holds, slots) == ("got", True, 1), (got, holds, slots)
        p.kill()
        p.join(timeout=20)
        with ag._agent_slot(10) as mine:
            assert mine is True, "the OS must have released the dead holder's slot"
    finally:
        if p.is_alive():  # pragma: no cover
            p.terminate()
