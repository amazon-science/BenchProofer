# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""pbt_port_fleet: at most one author per cell.

`--resume` filters the id list at LAUNCH, on the RECORDED gate status, which says
nothing about a cell that is mid-flight. So the filter cannot be the mutual
exclusion: a second driver started while the first is still running re-selects
every unfinished cell, and two agents then write the same `properties.py`. A torn
manifest would at least fail to load and surface as a gate error; the danger is
the clean interleaving -- a battery neither agent designed, gated and shipped as
if it were. The claim is a per-cell flock instead, and these pin it.

No agents and no verifier here: these cover the claim itself.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

import pbt_port_fleet
from pbt_port_fleet import CellBusy, cell_lock, recorded_pbt, timed_out


def test_one_holder_at_a_time(tmp_path):
    with cell_lock(tmp_path):
        with pytest.raises(CellBusy):
            with cell_lock(tmp_path):
                pass


def test_the_loser_learns_who_holds_the_cell(tmp_path, monkeypatch):
    """`busy` has to name a holder to be actionable, which constrains the open
    mode: `"w"` TRUNCATES before the flock is attempted, so every driver that
    LOST the race would wipe the winner's own pid line and a busy cell could only
    be traced by walking /proc/*/fd."""
    monkeypatch.setenv("SBU_WAVE_TAG", "w9/port")
    with cell_lock(tmp_path):
        with pytest.raises(CellBusy) as e:
            with cell_lock(tmp_path):
                pass
        assert f"pid {os.getpid()}" in str(e.value)
        assert "w9/port" in str(e.value)
        # and the record survived the loser's attempt
        assert "w9/port" in (tmp_path / ".pbt_port.lock").read_text()


def test_a_fresh_cell_does_not_race_on_creation(tmp_path):
    """Two drivers arriving at a never-locked cell at once: with an "x+" create
    the loser would die on FileExistsError rather than acquire or skip."""
    a = tmp_path / "fresh"
    script = textwrap.dedent(f"""
        import sys
        sys.path.insert(0, {str(Path(__file__).resolve().parents[1] / 'scripts')!r})
        from pathlib import Path
        from pbt_port_fleet import CellBusy, cell_lock
        try:
            with cell_lock(Path({str(a)!r})):
                print("ACQUIRED")
        except CellBusy:
            print("BUSY")
    """)
    with cell_lock(a):
        out = subprocess.run([sys.executable, "-c", script],
                             capture_output=True, text=True, timeout=60)
    assert out.stdout.strip() == "BUSY", out.stderr


def test_the_claim_is_released_on_exit(tmp_path):
    with cell_lock(tmp_path):
        pass
    with cell_lock(tmp_path):   # must not raise
        pass


def test_the_claim_is_released_even_when_the_cell_raises(tmp_path):
    """An authoring agent that dies must not leave the cell claimed forever."""
    with pytest.raises(RuntimeError):
        with cell_lock(tmp_path):
            raise RuntimeError("agent died")
    with cell_lock(tmp_path):
        pass


def test_the_sidecar_outlives_the_claim_but_names_no_holder(tmp_path):
    """The lock file is truncated on release, NOT unlinked.

    Unlinking it breaks mutual exclusion: an flock lives on the inode, so a
    driver descheduled between its `open` and its `flock` locks an inode the
    releasing holder has already unlinked, while the next arrival creates a fresh
    file and locks that -- two drivers each holding the same cell.

    Truncating keeps the second property too: the released file names no holder,
    so `release_misrouted` reads no pid and leaves the cell alone, and the file is
    gitignored and excluded from bundle content."""
    import fcntl
    lock = tmp_path / ".pbt_port.lock"
    with cell_lock(tmp_path):
        assert lock.is_file()
        assert lock.read_text().startswith("pid ")
    assert lock.is_file()
    assert lock.read_text() == ""
    # And it is genuinely unlocked afterwards, not merely empty.
    with lock.open("r+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(fh, fcntl.LOCK_UN)


def test_a_releasing_holder_cannot_hand_the_cell_to_two_drivers(tmp_path):
    """The race the truncate closes, driven directly: a driver that opened the
    sidecar before the holder released must not be able to lock it afterwards
    while a NEW arrival locks the current file. Both `flock` calls succeeding is
    the two-holder bug."""
    import fcntl
    lock = tmp_path / ".pbt_port.lock"
    with cell_lock(tmp_path):
        # The descheduled driver: it has a descriptor, not yet a lock.
        slow = lock.open("r+")
    # The holder has released. A new arrival takes the cell.
    with cell_lock(tmp_path):
        try:
            fcntl.flock(slow, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            pass                      # correct: the cell is held
        else:
            fcntl.flock(slow, fcntl.LOCK_UN)
            slow.close()
            raise AssertionError("two drivers hold the same cell")
    slow.close()


def test_different_cells_do_not_block_each_other(tmp_path):
    """The whole point is a wave of many cells running concurrently."""
    a, b = tmp_path / "a", tmp_path / "b"
    with cell_lock(a), cell_lock(b):
        pass


def test_the_claim_holds_across_processes(tmp_path):
    """The exclusion has to hold between SEPARATE drivers, so a lock private to
    one process would not provide it. flock is held by the kernel against the
    file, which is why the sidecar lives with the bundle rather than in a
    driver's log directory."""
    script = textwrap.dedent(f"""
        import sys
        sys.path.insert(0, {str(Path(__file__).resolve().parents[1] / 'scripts')!r})
        from pbt_port_fleet import CellBusy, cell_lock
        try:
            with cell_lock({str(tmp_path)!r} and __import__('pathlib').Path({str(tmp_path)!r})):
                print("ACQUIRED")
        except CellBusy:
            print("BUSY")
    """)
    with cell_lock(tmp_path):
        out = subprocess.run([sys.executable, "-c", script],
                             capture_output=True, text=True, timeout=60)
    assert out.stdout.strip() == "BUSY", out.stderr


def test_a_dead_holder_does_not_wedge_the_cell(tmp_path):
    """A driver killed mid-run must not leave its cells unclaimable: the kernel
    drops an flock when the holding process dies, even on SIGKILL."""
    script = textwrap.dedent(f"""
        import os, signal, sys
        sys.path.insert(0, {str(Path(__file__).resolve().parents[1] / 'scripts')!r})
        from pathlib import Path
        from pbt_port_fleet import cell_lock
        lk = cell_lock(Path({str(tmp_path)!r}))
        lk.__enter__()
        print("HELD", flush=True)
        os.kill(os.getpid(), signal.SIGKILL)
    """)
    out = subprocess.run([sys.executable, "-c", script],
                         capture_output=True, text=True, timeout=60)
    assert "HELD" in out.stdout
    with cell_lock(tmp_path):   # the sidecar survives; the claim does not
        pass


# ---------------------------------------------------------------------------
# recorded_pbt: the only truth about a cell's status
# ---------------------------------------------------------------------------

def test_unrecorded_cell(tmp_path):
    assert recorded_pbt(tmp_path) == (None, "")


def test_a_gate_entry_without_a_stamp_is_not_a_record(tmp_path):
    (tmp_path / "meta.json").write_text('{"gates": {"G-PBT": {"status": "pass"}}}')
    assert recorded_pbt(tmp_path) == (None, "")


def test_a_recorded_pass_reads_back(tmp_path):
    (tmp_path / "meta.json").write_text(
        '{"gates": {"G-PBT": {"status": "pass", "checked_at": "t",'
        ' "data": {"verdict": "SOUND"}}}}')
    assert recorded_pbt(tmp_path) == ("pass", "SOUND")


def test_a_missing_manifest_reads_as_skip(tmp_path):
    """The mid-construction convention: no properties.py is a skip, and
    `--resume` must not treat it as done."""
    (tmp_path / "meta.json").write_text(
        '{"gates": {"G-PBT": {"status": "skip", "checked_at": "t",'
        ' "data": {"pbt_missing_manifest": true}}}}')
    assert recorded_pbt(tmp_path) == ("skip", "missing-manifest")


# ---------------------------------------------------------------------------
# timed_out: which repair a non-passing cell needs
# ---------------------------------------------------------------------------
# A verifier timeout judges no case, so it says nothing about the battery. The
# two repairs are opposite: MALFORMED-TESTS means re-author (discarding the
# manifest), TIMED-OUT means re-gate the same manifest at a higher cap. Getting
# this backwards is what throws away sound work, so `--resume` keys on the
# gate's `pbt_timed_out` flag rather than on the verdict string.

def _stamp(bundle: Path, body: str) -> None:
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "meta.json").write_text(json.dumps(
        {"gates": {"G-PBT": {"status": "error", "checked_at": "t",
                             "data": json.loads(body)}}}))


def test_an_unstamped_cell_did_not_time_out(tmp_path):
    assert timed_out(tmp_path) is False


def test_a_timed_out_cell_is_recognised(tmp_path):
    _stamp(tmp_path, '{"verdict": "TIMED-OUT", "pbt_timed_out": true}')
    assert timed_out(tmp_path) is True


def test_a_malformed_battery_is_not_a_timeout(tmp_path):
    """The expensive mistake in the other direction: re-gating a genuinely
    defective battery at a higher cap just spends the builds again."""
    _stamp(tmp_path, '{"verdict": "MALFORMED-TESTS"}')
    assert timed_out(tmp_path) is False


def test_a_pre_flag_record_is_recognised_from_its_cases(tmp_path):
    """`pbt_timed_out` postdates the verdict split, so a record stamped before it
    reads MALFORMED-TESTS with a purely-inconclusive case list.

    Trusting the flag alone re-authors those records, discarding batteries that
    would pass SOUND unchanged once re-gated at a higher cap.
    """
    _stamp(tmp_path, json.dumps({"verdict": "MALFORMED-TESTS", "cases": [
        {"id": "a", "ok": True, "outcome": "verified"},
        {"id": "b", "ok": False, "outcome": "inconclusive"}]}))
    assert timed_out(tmp_path) is True


def test_a_real_defect_beside_a_timeout_is_not_a_timeout(tmp_path):
    """One judged failure means the battery WAS judged, so it must be
    re-authored: re-gating would leave a known-defective battery in place."""
    _stamp(tmp_path, json.dumps({"verdict": "MALFORMED-TESTS", "cases": [
        {"id": "a", "ok": False, "outcome": "inconclusive"},
        {"id": "b", "ok": False, "outcome": "witness-unproven"}]}))
    assert timed_out(tmp_path) is False


def test_an_all_passing_case_list_is_not_a_timeout(tmp_path):
    """No failing case at all: `all()` over an empty set is vacuously true, so
    without the emptiness guard this would read as a timeout."""
    _stamp(tmp_path, json.dumps({"verdict": "SOUND", "cases": [
        {"id": "a", "ok": True, "outcome": "verified"}]}))
    assert timed_out(tmp_path) is False


def test_a_gate_entry_without_a_stamp_is_not_a_timeout(tmp_path):
    (tmp_path / "meta.json").write_text(
        '{"gates": {"G-PBT": {"status": "error",'
        ' "data": {"pbt_timed_out": true}}}}')
    assert timed_out(tmp_path) is False


# ---------------------------------------------------------------------------
# and what the wave actually does with it
# ---------------------------------------------------------------------------

def _args(**kw) -> SimpleNamespace:
    """The subset of the CLI namespace _run_cell_locked reads."""
    return SimpleNamespace(**{
        "benchmark": "b", "benchmark_dir": "d", "resume": False,
        "gate_only": False, "regate_passing": False, "agent_timeout": 1,
        "gate_timeout": 1, "gate_workers": 1, "verify_timeout": 1,
        "lean_slots": 0, "model": None, **kw})


def _spy(monkeypatch, bundle: Path, *, gate_writes: str | None = None):
    """Record whether the wave authored, and whether it gated."""
    calls: list[str] = []

    def fake_author(*a, **k):
        calls.append("author")
        (bundle / "properties.py").write_text("SPEC_TESTS = []\n")
        return {"rc": 0, "wall_s": 0.0}

    def fake_gate(*a, **k):
        calls.append("gate")
        if gate_writes is not None:
            _stamp_status(bundle, gate_writes)
        return {"timed_out": False, "wall_s": 0.0}

    monkeypatch.setattr(pbt_port_fleet, "author", fake_author)
    monkeypatch.setattr(pbt_port_fleet, "gate", fake_gate)
    return calls


def _stamp_status(bundle: Path, status: str) -> None:
    (bundle / "meta.json").write_text(json.dumps(
        {"gates": {"G-PBT": {"status": status, "checked_at": "t",
                             "data": {"verdict": "SOUND"}}}}))


def test_a_timed_out_cell_is_regated_not_reauthored(tmp_path, monkeypatch):
    """The whole point of the flag. A cell whose cases all hit the verifier cap
    has a battery nobody judged; authoring a new one discards it for nothing and
    costs a full agent."""
    bundle = tmp_path / "django__django-1" / "lean"
    _stamp(bundle, '{"verdict": "TIMED-OUT", "pbt_timed_out": true}')
    (bundle / "properties.py").write_text("SPEC_TESTS = []\n")
    calls = _spy(monkeypatch, bundle, gate_writes="pass")
    row = pbt_port_fleet._run_cell_locked(
        "django__django-1", "lean", _args(resume=True), tmp_path, bundle,
        {"iid": "django__django-1"})
    assert calls == ["gate"], "a timed-out battery must not be re-authored"
    assert row["regated"] is True
    assert row["status"] == "pass"


def test_a_malformed_cell_is_reauthored(tmp_path, monkeypatch):
    """The contrast case: a defective battery is exactly what a new agent is
    for, so the skip must not widen to every non-passing cell."""
    bundle = tmp_path / "django__django-2" / "lean"
    _stamp(bundle, '{"verdict": "MALFORMED-TESTS"}')
    (bundle / "properties.py").write_text("SPEC_TESTS = []\n")
    calls = _spy(monkeypatch, bundle, gate_writes="pass")
    pbt_port_fleet._run_cell_locked(
        "django__django-2", "lean", _args(resume=True), tmp_path, bundle,
        {"iid": "django__django-2"})
    assert calls == ["author", "gate"]


def test_an_explicit_reauthor_overrides_the_timeout_skip(tmp_path, monkeypatch):
    """Without --resume the wave was asked to author, so it authors: the skip is
    an optimisation for repair waves, not a refusal."""
    bundle = tmp_path / "django__django-3" / "lean"
    _stamp(bundle, '{"verdict": "TIMED-OUT", "pbt_timed_out": true}')
    (bundle / "properties.py").write_text("SPEC_TESTS = []\n")
    calls = _spy(monkeypatch, bundle, gate_writes="pass")
    pbt_port_fleet._run_cell_locked(
        "django__django-3", "lean", _args(resume=False), tmp_path, bundle,
        {"iid": "django__django-3"})
    assert calls == ["author", "gate"]


# ---------------------------------------------------------------------------
# --regate-passing: re-certifying the corpus after the GATE gets stricter
# ---------------------------------------------------------------------------
# A recorded pass attests to the harness that judged it. When the gate itself
# gains a check, every earlier pass is unverified against the new rule, and
# `--resume` (which the supervisor always passes) filters exactly those cells out.

def test_a_passing_cell_is_regated_when_asked(tmp_path, monkeypatch):
    bundle = tmp_path / "django__django-5" / "lean"
    bundle.mkdir(parents=True)
    _stamp_status(bundle, "pass")
    (bundle / "properties.py").write_text("SPEC_TESTS = []\n")
    calls = _spy(monkeypatch, bundle, gate_writes="pass")
    row = pbt_port_fleet._run_cell_locked(
        "django__django-5", "lean",
        _args(resume=True, regate_passing=True, gate_only=True), tmp_path,
        bundle, {"iid": "django__django-5"})
    assert calls == ["gate"]
    assert row["status"] == "pass"


def test_a_regate_never_authors(tmp_path, monkeypatch):
    """The manifest is what is on trial, so replacing it destroys the evidence --
    and a fresh agent would be judged by the new rule while the battery that
    actually shipped never was."""
    bundle = tmp_path / "django__django-6" / "lean"
    bundle.mkdir(parents=True)
    _stamp_status(bundle, "pass")
    (bundle / "properties.py").write_text("SPEC_TESTS = []  # the one on trial\n")
    calls = _spy(monkeypatch, bundle, gate_writes="pass")
    pbt_port_fleet._run_cell_locked(
        "django__django-6", "lean",
        _args(resume=True, regate_passing=True, gate_only=True), tmp_path,
        bundle, {"iid": "django__django-6"})
    assert calls == ["gate"]
    assert "on trial" in (bundle / "properties.py").read_text()


def test_a_regate_that_now_fails_is_recorded(tmp_path, monkeypatch):
    """The point of the exercise: a cell the stricter gate rejects must come back
    as a failure, not be reported green off its stale stamp."""
    bundle = tmp_path / "django__django-7" / "lean"
    bundle.mkdir(parents=True)
    _stamp_status(bundle, "pass")
    (bundle / "properties.py").write_text("SPEC_TESTS = []\n")
    _spy(monkeypatch, bundle, gate_writes="error")
    row = pbt_port_fleet._run_cell_locked(
        "django__django-7", "lean",
        _args(resume=True, regate_passing=True, gate_only=True), tmp_path,
        bundle, {"iid": "django__django-7"})
    assert row["status"] == "error"


def test_without_the_flag_a_passing_cell_is_still_skipped(tmp_path, monkeypatch):
    """The default must not change: ordinary repair waves run alongside this one
    and re-gating every passing cell by accident is hours of builds."""
    bundle = tmp_path / "django__django-8" / "lean"
    bundle.mkdir(parents=True)
    _stamp_status(bundle, "pass")
    (bundle / "properties.py").write_text("SPEC_TESTS = []\n")
    calls = _spy(monkeypatch, bundle, gate_writes="pass")
    row = pbt_port_fleet._run_cell_locked(
        "django__django-8", "lean", _args(resume=True), tmp_path, bundle,
        {"iid": "django__django-8"})
    assert calls == [] and row["status"] == "already-passing"


def test_a_regate_still_needs_a_manifest(tmp_path, monkeypatch):
    """Belt and braces: the stamp is written by the gate, so a TIMED-OUT record
    with no properties.py should be impossible -- but if the two ever disagree,
    the driver must not run the gate on nothing and record `unrecorded`."""
    bundle = tmp_path / "django__django-4" / "lean"
    _stamp(bundle, '{"verdict": "TIMED-OUT", "pbt_timed_out": true}')
    calls = _spy(monkeypatch, bundle)
    row = pbt_port_fleet._run_cell_locked(
        "django__django-4", "lean", _args(resume=True), tmp_path, bundle,
        {"iid": "django__django-4"})
    assert calls == [] and row["status"] == "no-manifest"


# ---------------------------------------------------------------------------
# the agent environment: a shell incompatibility that costs a cell's lock
# ---------------------------------------------------------------------------

def test_a_bare_redirect_does_not_hang_an_agent_shell(tmp_path):
    """`> file` must TRUNCATE, not read stdin forever.

    When an agent's shell is zsh, a bare output redirect runs $NULLCMD instead of
    nothing -- and $NULLCMD defaults to `cat`, so `> results.txt` becomes
    `cat > results.txt`, reads the agent's stdin and blocks forever while holding
    that cell's lock. `> file` is the ordinary bash idiom for emptying a file, so
    an agent hits it without doing anything unusual.

    So this asserts the fix end to end, in a real zsh with a live stdin (the
    condition that makes it hang), rather than just that the variable is set.
    """
    import shutil
    zsh = shutil.which("zsh")
    if not zsh:
        pytest.skip("zsh not available")
    target = tmp_path / "results.txt"
    target.write_text("stale content that must be truncated\n")
    env = pbt_port_fleet._env("swe_bench_verified", "benchmark-verified")
    # `sleep` as stdin stands in for the agent's own stdin: a fd that stays OPEN,
    # so a `cat` would wait on it. Without the fix this times out instead of
    # returning.
    with subprocess.Popen(["sleep", "30"], stdout=subprocess.PIPE) as feed:
        try:
            p = subprocess.run([zsh, "-c", f"> {target}"], env=env,
                               stdin=feed.stdout, capture_output=True,
                               timeout=15)
        except subprocess.TimeoutExpired:
            pytest.fail("a bare `> file` redirect hung: $NULLCMD is still `cat`")
        finally:
            feed.kill()
    assert p.returncode == 0, p.stderr
    assert target.read_text() == "", "the redirect did not truncate the file"


def test_the_null_command_is_overridable(tmp_path):
    """A caller's own NULLCMD wins, so this cannot fight a future setting."""
    os.environ["NULLCMD"] = "true"
    try:
        assert pbt_port_fleet._env("b", "d")["NULLCMD"] == "true"
    finally:
        del os.environ["NULLCMD"]


# ---- a cap that expires must not leave the tree running ----------------------
#
# Every command a driver caps is a python step that launches an agent CLI, which
# launches a shell, which launches a verifier or a container. `subprocess.run`'s
# timeout kills only the direct child, so the rest is reparented to init and left
# running with nobody waiting on its result. The leak feeds itself: the CPU an
# orphan holds is what makes the next step overrun its own cap.

def _pidfile_tree(tmp_path: Path) -> list[str]:
    """A parent that spawns a long-lived grandchild and reports its pid."""
    prog = textwrap.dedent("""
        import os, subprocess, sys, time
        kid = subprocess.Popen(["sleep", "300"])
        open(sys.argv[1], "w").write(str(kid.pid))
        time.sleep(300)
    """)
    script = tmp_path / "spawner.py"
    script.write_text(prog)
    return [sys.executable, str(script), str(tmp_path / "kid.pid")]


def _alive(pid: int) -> bool:
    return Path(f"/proc/{pid}").exists()


def test_a_timed_out_step_takes_its_grandchildren_with_it(tmp_path):
    import time
    log = tmp_path / "out.log"
    kidfile = tmp_path / "kid.pid"
    ok = pbt_port_fleet.run_capped(_pidfile_tree(tmp_path), log,
                                   dict(os.environ), timeout_s=3)
    assert ok is False, "the step outran its cap, so it must report a timeout"
    assert kidfile.is_file(), "the spawner never reached its grandchild"
    kid = int(kidfile.read_text())
    for _ in range(50):                       # SIGKILL delivery is not instant
        if not _alive(kid):
            break
        time.sleep(0.1)
    assert not _alive(kid), \
        f"grandchild {kid} survived the cap -- this is the orphan leak"


def test_a_step_that_finishes_in_time_reports_success(tmp_path):
    log = tmp_path / "out.log"
    ok = pbt_port_fleet.run_capped([sys.executable, "-c", "print('done')"],
                                   log, dict(os.environ), timeout_s=60)
    assert ok is True
    assert "done" in log.read_text(), "output must still reach the log"


def test_an_uncapped_step_is_allowed(tmp_path):
    # The authoring step passes timeout_s=None deliberately: an agent's own cap
    # bounds it, and a second outer cap would truncate work already paid for.
    log = tmp_path / "out.log"
    assert pbt_port_fleet.run_capped([sys.executable, "-c", "pass"], log,
                                     dict(os.environ), timeout_s=None) is True


def test_a_sibling_step_is_not_killed(tmp_path):
    """The hazard the /proc walk has to avoid: these drivers are THREADED, so a
    kill scoped to anything wider than this child's own subtree would take out
    every other in-flight cell when one of them overruns."""
    import time
    sibling = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        pbt_port_fleet.run_capped(_pidfile_tree(tmp_path), tmp_path / "l.log",
                                  dict(os.environ), timeout_s=3)
        time.sleep(1)
        assert sibling.poll() is None, \
            "a concurrent sibling was killed by another cell's timeout"
    finally:
        sibling.kill()
        sibling.wait()
