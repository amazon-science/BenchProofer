# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""run_resolve's retry policy (harness.run_resolve).

The distinction under test: a NOT-RESOLVED verdict is a statement about the
patch, while a NOT-COMPLETED attempt (harness timeout, image pull failure) is a
failed measurement. Both are retried, and "resolved on ANY attempt" wins, so a
loaded host cannot turn a sound cell's resolving patch into an INCONCLUSIVE
audit. No docker needed: the harness subprocess and report read are faked.
"""
from __future__ import annotations

import json
import shlex
import subprocess
import sys
import time
from pathlib import Path

import pytest

from swebench_unified import harness

IID = "x__x-1"


def _fake_harness(monkeypatch, tmp_path, outcomes):
    """Drive run_resolve over a scripted sequence of per-attempt outcomes.

    Each outcome is "resolved" | "unresolved" | "incomplete". Returns the list
    of run_ids actually attempted, so a test can assert how many runs happened
    and that each used a distinct (single-use) run_id.
    """
    seen: list[str] = []
    seq = list(outcomes)

    monkeypatch.setattr(harness, "_frozen_row", lambda iid: {"instance_id": iid})
    monkeypatch.setattr(harness, "_write_predictions",
                        lambda iid, patch: tmp_path / "preds" / "p.json")
    monkeypatch.setattr(harness, "REPORTS_ROOT", tmp_path / "reports")
    monkeypatch.setattr(harness, "EXPERIMENTS_ROOT", tmp_path / "exp")

    class _Bench:
        supports_docker_oracle = True
        resolve_style = "verified"
        dataset_name = "d"
        namespace = None
        image_tag = "t"
        name = "swe_bench_verified"

    monkeypatch.setattr(harness, "active", lambda: _Bench(), raising=False)
    monkeypatch.setattr("swebench_unified.benchmarks.active", lambda: _Bench())

    def _run(cmd, **kw):
        # the run_id is the token after --run_id in the inner shell command
        parts = cmd[-1].split()
        seen.append(parts[parts.index("--run_id") + 1])
        return type("P", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(harness, "_run_capped", lambda cmd, timeout: _run(cmd))

    def _report(run_id, instance_id):
        outcome = seq[len(seen) - 1] if len(seen) <= len(seq) else seq[-1]
        p = tmp_path / f"rep-{len(seen)}.json"
        if outcome == "incomplete":
            return tmp_path / "nonexistent" / "report.json"  # no report => not completed
        p.write_text(json.dumps({instance_id: {"resolved": outcome == "resolved"}}))
        return p

    monkeypatch.setattr(harness, "_per_instance_report", _report)
    return seen


def test_incomplete_first_attempt_is_retried_and_resolves(monkeypatch, tmp_path):
    # The regression: a dropped attempt used to return immediately, so a patch
    # that resolves fine on a second look was recorded as "did not complete" and
    # the audit gate went INCONCLUSIVE on a sound cell.
    seen = _fake_harness(monkeypatch, tmp_path, ["incomplete", "resolved"])
    r = harness.run_resolve(IID, "PATCH", retries=2)
    assert r.resolved and r.completed
    assert r.attempts == 2 and r.flaky
    assert len(seen) == 2 and len(set(seen)) == 2  # distinct single-use run_ids


def test_all_attempts_incomplete_reports_measurement_failure(monkeypatch, tmp_path):
    seen = _fake_harness(monkeypatch, tmp_path, ["incomplete"] * 3)
    r = harness.run_resolve(IID, "PATCH", retries=2)
    assert not r.completed and not r.resolved
    assert r.attempts == 3 and "no attempt completed in 3 tries" in r.note
    assert len(seen) == 3


def test_consistent_nonresolve_is_not_flaky(monkeypatch, tmp_path):
    # The load-bearing direction for `verify => correct`: a patch that genuinely
    # does not resolve must stay not-resolved across every retry, so WEAK/BROKEN
    # findings are never softened into an inconclusive.
    seen = _fake_harness(monkeypatch, tmp_path, ["unresolved"] * 3)
    r = harness.run_resolve(IID, "PATCH", retries=2)
    assert r.completed and not r.resolved and not r.flaky
    assert r.attempts == 3 and "consistent" in r.note
    assert len(seen) == 3


def test_mixed_incomplete_and_nonresolve_reports_the_verdict(monkeypatch, tmp_path):
    # A real not-resolved verdict outranks a dropped attempt, but the dropped
    # attempt is disclosed rather than silently presented as a clean check.
    _fake_harness(monkeypatch, tmp_path, ["unresolved", "incomplete", "incomplete"])
    r = harness.run_resolve(IID, "PATCH", retries=2)
    assert r.completed and not r.resolved
    assert "2 attempt(s) did not complete" in r.note


def test_retries_zero_does_a_single_attempt(monkeypatch, tmp_path):
    seen = _fake_harness(monkeypatch, tmp_path, ["incomplete"])
    r = harness.run_resolve(IID, "PATCH", retries=0)
    assert not r.completed and len(seen) == 1


def test_resolved_on_first_attempt_is_not_flagged_flaky(monkeypatch, tmp_path):
    seen = _fake_harness(monkeypatch, tmp_path, ["resolved"])
    r = harness.run_resolve(IID, "PATCH", retries=2)
    assert r.resolved and not r.flaky and r.attempts == 1
    assert len(seen) == 1


def test_no_report_note_carries_the_harness_output(monkeypatch, tmp_path):
    # "no report" is the dominant failure under load; without the harness's own
    # output it cannot be told apart from a real defect after the fact.
    _fake_harness(monkeypatch, tmp_path, ["incomplete"])

    def _run(cmd, **kw):
        return type("P", (), {"returncode": 1, "stdout": "",
                              "stderr": "Cannot connect to the Docker daemon"})()

    monkeypatch.setattr(harness, "_run_capped", lambda cmd, timeout: _run(cmd))
    r = harness.run_resolve(IID, "PATCH", retries=0)
    assert not r.completed
    assert "rc=1" in r.note and "Cannot connect to the Docker daemon" in r.note


# ---- WHY there was no report: the harness's per-instance run log --------------
#
# The process output only ever carries the run SUMMARY ("Instances with errors: 1"),
# which is identical for a patch that will not apply and for a container that never
# started. Those call for opposite responses -- redo the auditor's payload, or repeat
# the measurement -- and the per-instance log is the only place they differ. It is
# deleted once the attempt ends, so it has to be read here or not at all.

def _write_run_log(tmp_path, run_id: str, body: str):
    d = (tmp_path / "exp" / "logs" / "run_evaluation" / run_id /
         harness.MODEL_NAME / IID)
    d.mkdir(parents=True)
    (d / "run_instance.log").write_text(body)


def test_the_run_log_names_a_patch_apply_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(harness, "EXPERIMENTS_ROOT", tmp_path / "exp")
    _write_run_log(tmp_path, "r1", (
        "2026-01-01 - INFO - Container started\n"
        "  File \"run_evaluation.py\", line 182, in run_instance\n"
        "    raise EvaluationError(\n"
        "swebench.harness.utils.EvaluationError: x__x-1: >>>>> Patch Apply Failed:\n"
        "patch: **** Only garbage was found in the patch input.\n"
        "2026-01-01 - INFO - Attempting to stop container\n"))
    why = harness._no_report_reason("r1", IID)
    assert "Patch Apply Failed" in why
    assert "Only garbage was found in the patch input" in why, \
        "`patch`'s own complaint is on the line AFTER the marker, and it is the " \
        "part that says what was wrong with the diff"


def test_the_run_log_reader_takes_the_last_traceback(monkeypatch, tmp_path):
    """The harness logs the same traceback more than once; an early hit would
    report a failure that a later attempt inside the same run superseded."""
    monkeypatch.setattr(harness, "EXPERIMENTS_ROOT", tmp_path / "exp")
    _write_run_log(tmp_path, "r2",
                   "EvaluationError: first: >>>>> Patch Apply Failed\n"
                   + "filler\n" * 50
                   + "EvaluationError: last: >>>>> Test Timeout after 900s\n")
    why = harness._no_report_reason("r2", IID)
    assert "Test Timeout" in why and "Patch Apply Failed" not in why


def test_a_missing_run_log_is_not_an_attribution(monkeypatch, tmp_path):
    """Fail SAFE: with nothing to read, claim nothing. The generic note stands."""
    monkeypatch.setattr(harness, "EXPERIMENTS_ROOT", tmp_path / "exp")
    assert harness._no_report_reason("absent", IID) == ""


def test_a_huge_run_log_is_read_from_the_tail(monkeypatch, tmp_path):
    """These logs run to hundreds of KB of pip and container transcript. Only the
    tail is read, so the cause must be findable there rather than by scanning."""
    monkeypatch.setattr(harness, "EXPERIMENTS_ROOT", tmp_path / "exp")
    _write_run_log(tmp_path, "r3", "noise\n" * 200_000
                   + "EvaluationError: x: >>>>> Patch Apply Failed\n")
    assert "Patch Apply Failed" in harness._no_report_reason("r3", IID)


def test_the_cause_precedes_the_truncatable_tail_in_the_note(monkeypatch, tmp_path):
    """Ordering is load-bearing. Callers elide long notes, and the report path plus
    the run summary are long enough on their own to push a trailing cause out of
    any cap -- which is how this evidence was being lost."""
    _fake_harness(monkeypatch, tmp_path, ["incomplete"])
    monkeypatch.setattr(harness, "_no_report_reason",
                        lambda run_id, iid: ">>>>> Patch Apply Failed: garbage")
    r = harness.run_resolve(IID, "PATCH", retries=0)
    assert not r.completed
    assert r.note.index("Patch Apply Failed") < r.note.index("rc="), r.note


def test_a_host_failure_keeps_the_generic_note(monkeypatch, tmp_path):
    """The complement: no readable cause must not be dressed up as one."""
    _fake_harness(monkeypatch, tmp_path, ["incomplete"])
    monkeypatch.setattr(harness, "_no_report_reason", lambda run_id, iid: "")
    r = harness.run_resolve(IID, "PATCH", retries=0)
    assert "harness error or image pull failure" in r.note


# ---- host-wide resolve slots (cross-process concurrency bound) ----

def test_resolve_slot_bounds_concurrency_across_processes(monkeypatch, tmp_path):
    """The invariant: never more than SBU_RESOLVE_SLOTS holders at once.

    Uses real subprocesses, since the point of the flock semaphore is to bound
    concurrency across PROCESSES (a threading.Semaphore in one driver cannot see
    another driver's containers).
    """
    import subprocess as sp
    import textwrap

    slot_dir = tmp_path / "slots"
    prog = textwrap.dedent(f"""
        import sys, time, os
        sys.path.insert(0, {str(Path(__file__).resolve().parents[1] / "src")!r})
        os.environ["SBU_RESOLVE_SLOTS"] = "2"
        os.environ["SBU_RESOLVE_SLOT_DIR"] = {str(slot_dir)!r}
        import importlib, swebench_unified.harness as h
        importlib.reload(h)
        with h.resolve_slot():
            # announce, hold briefly, so overlap is observable
            print("IN", flush=True)
            time.sleep(1.5)
        print("OUT", flush=True)
    """)
    script = tmp_path / "hold.py"
    script.write_text(prog)
    procs = [sp.Popen([sys.executable, str(script)], stdout=sp.PIPE, text=True)
             for _ in range(6)]
    try:
        # Each process prints IN then OUT. With 2 slots and 6 contenders, the
        # holders must serialize: total wall clock >= 3 batches * 1.5s.
        t0 = time.monotonic()
        outs = [p.communicate(timeout=120)[0] for p in procs]
        elapsed = time.monotonic() - t0
    finally:
        for p in procs:
            if p.poll() is None:
                p.kill()
    assert all("IN" in o and "OUT" in o for o in outs)
    assert elapsed >= 4.0, f"6 procs / 2 slots finished in {elapsed:.1f}s — not bounded"


def test_resolve_slot_disabled_by_zero(monkeypatch, tmp_path):
    monkeypatch.setenv("SBU_RESOLVE_SLOTS", "0")
    monkeypatch.setattr(harness, "_SLOT_DIR", tmp_path / "unused")
    with harness.resolve_slot():
        pass
    assert not (tmp_path / "unused").exists()  # no semaphore state created


def test_resolve_slot_releases_on_exception(monkeypatch, tmp_path):
    # A raising body must not leak the slot, else one crash permanently shrinks
    # the oracle capacity for every later run.
    monkeypatch.setenv("SBU_RESOLVE_SLOTS", "1")
    monkeypatch.setattr(harness, "_SLOT_DIR", tmp_path / "slots")
    for _ in range(3):
        try:
            with harness.resolve_slot():
                raise RuntimeError("boom")
        except RuntimeError:
            pass
    # if the slot leaked, this would block forever
    with harness.resolve_slot():
        pass


# ---- the timeout has to reach the GRANDCHILD ---------------------------------
#
# The oracle is spawned as `sg docker -c '... python -m run_evaluation ...'`, so
# the process the timeout can signal is a wrapper two levels above the work.
# `subprocess.run(timeout=...)` kills only that wrapper; the shell and the
# harness under it keep running, with their containers, and nobody will read
# their result. Before the fix, such trees accumulated over a run and survived
# for hours after the attempt that spawned them. They are not idle -- they compete for docker
# and cores with the cells still to be measured, and a resolve that cannot
# complete is reported downstream as INCONCLUSIVE, i.e. as a defect in the
# artifact rather than in the host.

def test_a_timed_out_harness_leaves_no_surviving_grandchild(tmp_path):
    """The shape of the leak, reproduced with `sh` standing in for `sg docker`."""
    marker = tmp_path / "alive"
    # An outer shell whose child outlives it: the child writes its own pid and
    # then sleeps well past the cap, exactly as the harness does.
    inner = f"echo $$ > {marker}; sleep 120"
    outer = f"sh -c {shlex.quote(inner)} & wait"
    with pytest.raises(subprocess.TimeoutExpired):
        harness._run_capped(["sh", "-c", outer], timeout=3)
    # The grandchild announced itself, so the test is not passing vacuously.
    child = int(marker.read_text().strip())
    for _ in range(50):                        # the kill is asynchronous
        if not Path(f"/proc/{child}").exists():
            break
        time.sleep(0.1)
    assert not Path(f"/proc/{child}").exists(), (
        f"pid {child} survived the timeout: the group kill did not reach it")


# ---- two runs on ONE instance destroy each other ------------------------------
#
# `--cache_level env` deletes the instance image when a run finishes, so a second
# concurrent run on the SAME instance 404s at container-create. An audit role
# resolves gold, prepatch and its attacks -- all one instance -- so the collision
# is the normal case, not a corner. Three concurrent runs on one instance delete
# every image for it, the gold CONTROL among them, and with no certified gold the
# whole audit is INCONCLUSIVE whatever the spec is.

def test_two_resolves_on_one_instance_do_not_overlap(monkeypatch, tmp_path):
    monkeypatch.setattr(harness, "_SLOT_DIR", tmp_path / "slots")
    monkeypatch.delenv("SBU_RESOLVE_SLOTS", raising=False)
    # Two processes, not two threads: the holders are separate agent processes, so
    # only a kernel lock can see both.
    prog = (
        "import sys, time;"
        f"sys.path.insert(0, {str(Path(__file__).resolve().parents[1] / 'src')!r});"
        "from swebench_unified import harness;"
        "from pathlib import Path;"
        f"harness._SLOT_DIR = Path({str(tmp_path / 'slots')!r});"
        "print('IN', flush=True);"
        "ts = []\n"
        "with harness.instance_slot('x__x-1'):\n"
        "    ts.append(time.time()); time.sleep(1.5); ts.append(time.time())\n"
        "print('OUT %.3f %.3f' % (ts[0], ts[1]), flush=True)"
    )
    procs = [subprocess.Popen([sys.executable, "-c", prog], stdout=subprocess.PIPE,
                              text=True) for _ in range(2)]
    spans = []
    try:
        for p in procs:
            out = p.communicate(timeout=60)[0]
            line = [ln for ln in out.splitlines() if ln.startswith("OUT")][0]
            spans.append(tuple(float(x) for x in line.split()[1:]))
    finally:
        for p in procs:
            if p.poll() is None:
                p.kill()
    (a0, a1), (b0, b1) = sorted(spans)
    assert b0 >= a1 - 0.05, (
        f"the two critical sections overlapped: {a0:.3f}-{a1:.3f} and "
        f"{b0:.3f}-{b1:.3f}; the same instance image can be deleted under a "
        "live run")


def test_a_different_instance_is_not_blocked(monkeypatch, tmp_path):
    """The lock is per instance, so normal breadth is untouched -- only the
    same-instance case, which was duplicated work anyway (resolving is a pure
    function of instance and patch)."""
    monkeypatch.setattr(harness, "_SLOT_DIR", tmp_path / "slots")
    monkeypatch.delenv("SBU_RESOLVE_SLOTS", raising=False)
    with harness.instance_slot("a__a-1"):
        with harness.instance_slot("b__b-2"):   # would deadlock if shared
            pass


def test_an_instance_id_with_path_characters_cannot_escape_the_slot_dir(monkeypatch,
                                                                       tmp_path):
    """Instance ids come from a dataset, so they are sanitized before becoming a
    filename: a `/` would otherwise point the lock outside the slot directory and
    fail to open, silently disabling the serialization."""
    monkeypatch.setattr(harness, "_SLOT_DIR", tmp_path / "slots")
    monkeypatch.delenv("SBU_RESOLVE_SLOTS", raising=False)
    with harness.instance_slot("../evil/x y"):
        pass
    made = [p.name for p in (tmp_path / "slots").iterdir()]
    assert made == ["inst_.._evil_x_y"], made


def test_a_completing_command_returns_its_output(tmp_path):
    """The common path: `_run_capped` still behaves like `subprocess.run`, so a
    caller reading `.returncode`/`.stdout` is unaffected by the group handling."""
    got = harness._run_capped(["sh", "-c", "echo hi; exit 3"], timeout=30)
    assert got.returncode == 3 and got.stdout.strip() == "hi"


def test_a_timed_out_attempt_removes_the_container_it_left_behind(monkeypatch,
                                                                  tmp_path):
    """The docker daemon owns the container, so killing the tree does not stop
    it, and the harness's own cleanup is in a `finally` that SIGKILL skips. The
    note says so too: an operator reading "harness timed out" needs to know
    whether the expensive half was reclaimed."""
    _fake_harness(monkeypatch, tmp_path, ["incomplete"])
    removed: list[str] = []

    def _boom(cmd, timeout):
        raise subprocess.TimeoutExpired(cmd, timeout)

    monkeypatch.setattr(harness, "_run_capped", _boom)
    monkeypatch.setattr(harness, "_kill_eval_containers",
                        lambda run_id: (removed.append(run_id), 1)[1])
    r = harness.run_resolve(IID, "PATCH", timeout=60, retries=0)
    assert not r.completed and not r.resolved
    assert "harness timed out" in r.note and "1 orphaned container" in r.note
    assert len(removed) == 1 and IID in removed[0]
