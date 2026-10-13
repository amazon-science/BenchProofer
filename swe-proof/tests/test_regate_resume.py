# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""regate_resume: the invariants a consolidated re-judge driver has to keep.

This is the only entry point for "re-judge a whole cell", after absorbing the
single-cell and fleet-fan-out scripts that used to sit beside it. Four properties
are what made that safe to do, and each one is a failure that has been paid for:

* it writes a cell only under the per-cell flock, because the fan-out version
  spawned children that took no lock and ran in parallel with live repair agents;
* `--benchmark-dir` reaches the GATES, not just the classification, because the
  flag it inherited was decorative -- `paths.TASKS_ROOT` is read from the
  environment at import and the gates take no root argument;
* it re-derives greenness nowhere; `green_check.classify` is asked;
* a skipped audit stage says whether the records left in place still describe the
  spec that is shipping, which the single-cell script claimed to do and did not.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import regate_resume

ROOT = Path(__file__).resolve().parents[1]


def _cell(tmp_path: Path, *, gates: dict | None = None, solution: bool = True,
          backend: str = "velvet", blocked: bool = False) -> Path:
    cell = tmp_path / "django__django-1" / backend
    cell.mkdir(parents=True, exist_ok=True)
    (cell / "meta.json").write_text(json.dumps(
        {"schema_version": 1, "gates": gates or {}}, indent=2) + "\n")
    if solution:
        (cell / regate_resume.SOLUTION[backend]).write_text("-- spec\n")
    if blocked:
        (cell / "BLOCKED.md").write_text("parked\n")
    return cell


# ---------------------------------------------------------------- classify --

def test_a_green_cell_is_skipped_and_forced_only_on_request(tmp_path,
                                                           monkeypatch):
    """The default resume: a green cell costs one classify and is left alone.

    `--force` is the case the deleted `regate_one.py` served, and it cannot be
    the default: `classify` reads gate STATUSES and says nothing about stamp
    freshness, so "green" here does not mean "measured against these bytes", and
    forcing every green cell in the corpus is a fresh agentic audit -- hours per
    cell -- for cells nothing said were wrong.
    """
    _cell(tmp_path)
    monkeypatch.setattr(regate_resume, "SOLUTION", regate_resume.SOLUTION)
    monkeypatch.setitem(sys.modules, "green_check", _green("GREEN", "ok"))
    assert regate_resume.plan_cell(tmp_path, "django__django-1",
                                   "velvet")[0] == "green"
    assert regate_resume.plan_cell(tmp_path, "django__django-1", "velvet",
                                   force=True)[0] == "regate"


def test_a_parked_cell_stays_parked_even_under_force(tmp_path, monkeypatch):
    """A principled BLOCKED bundle has no solution to measure, so forcing it
    would only re-derive "there is nothing here"."""
    _cell(tmp_path, solution=False, blocked=True)
    monkeypatch.setitem(sys.modules, "green_check", _green("NOTGREEN", "no sol"))
    assert regate_resume.plan_cell(tmp_path, "django__django-1", "velvet",
                                   force=True)[0] == "blocked"


def test_a_forced_green_cell_with_no_solution_is_not_regated(tmp_path,
                                                             monkeypatch):
    """Force means "measure these bytes again"; with no bytes it must fall
    through to the construct/blocked decision rather than gate an empty cell."""
    _cell(tmp_path, solution=False)
    monkeypatch.setitem(sys.modules, "green_check", _green("GREEN", "ok"))
    assert regate_resume.plan_cell(tmp_path, "django__django-1", "velvet",
                                   force=True)[0] == "construct"


def _green(verdict: str, why: str):
    """A stand-in `green_check` module, so these tests pin the DRIVER's routing
    rather than re-testing the classifier. That the driver asks it at all is the
    invariant: a driver that decides greenness itself starts disagreeing with the
    release gate about the very cells it is repairing."""
    import types
    m = types.ModuleType("green_check")
    m.classify = lambda bundle, backend, iid: (verdict, why)
    return m


# ------------------------------------------------------------- audit staleness --

def test_a_skipped_audit_over_a_moved_spec_says_so(tmp_path, monkeypatch):
    """The case the earlier single-cell script missed entirely.

    `check_stamp_freshness` reports an audit gate's digest mismatch as `deferred`
    -- deferred TO `audit_freshness`, since a comment edit or an added obligation
    does not stale an audit -- and reading only `changed`/`vanished` therefore
    never reported a moved spec at all. So the G-EQ / G-PANEL records of a spec
    that has since been rewritten read as a fresh judgment of what is shipping.
    """
    cell = _cell(tmp_path)
    monkeypatch.setitem(sys.modules, "audit_freshness",
                        _stub(verdict_for=lambda c, b: ("RE-AUDIT", "3 lines removed")))
    monkeypatch.setitem(sys.modules, "check_stamp_freshness",
                        _stub(check_cell=lambda c, g: []))
    note = regate_resume._audit_skip_note(cell, "velvet")
    assert note.startswith("stale-not-rerun(")
    assert "3 lines removed" in note


def test_a_lost_control_clause_is_reported_too(tmp_path, monkeypatch):
    """The two findings a CONTENT check can still make about an audit record: a
    positive control that no longer carries what it certified (`changed`), and a
    cited artifact that is gone (`vanished`)."""
    cell = _cell(tmp_path)
    monkeypatch.setitem(sys.modules, "audit_freshness",
                        _stub(verdict_for=lambda c, b: ("SPEC-IDENTICAL", "-")))
    monkeypatch.setitem(sys.modules, "check_stamp_freshness", _stub(
        check_cell=lambda c, g: [("G-EQ", "ctl.lean", "changed"),
                                 ("G-PANEL-1", "atk_1.lean", "vanished"),
                                 ("G-PANEL-2", "Solution.lean", "deferred")]))
    note = regate_resume._audit_skip_note(cell, "velvet")
    assert "G-EQ" in note and "G-PANEL-1" in note
    # `deferred` is audit_freshness's question, and it answered SPEC-IDENTICAL.
    assert "G-PANEL-2" not in note


def test_a_fresh_audit_reads_as_a_plain_skip(tmp_path, monkeypatch):
    cell = _cell(tmp_path)
    monkeypatch.setitem(sys.modules, "audit_freshness",
                        _stub(verdict_for=lambda c, b: ("STRENGTHENED", "+1 obl")))
    monkeypatch.setitem(sys.modules, "check_stamp_freshness",
                        _stub(check_cell=lambda c, g: []))
    assert regate_resume._audit_skip_note(cell, "velvet") == "skipped"


def test_the_freshness_report_never_breaks_a_regate(tmp_path, monkeypatch):
    """An unreadable bundle is the gates' problem to report, and a checkout with
    no git history must not turn a re-gate into a crash: both authorities are
    advisory here, so both are allowed to fail."""
    cell = _cell(tmp_path)

    def boom(*a, **k):
        raise RuntimeError("no git")

    monkeypatch.setitem(sys.modules, "audit_freshness", _stub(verdict_for=boom))
    monkeypatch.setitem(sys.modules, "check_stamp_freshness",
                        _stub(check_cell=boom))
    assert regate_resume._audit_skip_note(cell, "velvet") == "skipped"


def _stub(**attrs):
    import types
    m = types.ModuleType("stub")
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


# ------------------------------------------------------------------- the lock --

def test_a_cell_another_driver_holds_is_not_measured(tmp_path, monkeypatch):
    """The invariant the deleted fan-out script broke: it shelled out per cell,
    24-way, and the child took no lock at all. Two writers on one meta.json means
    the loser's stamps are the ones that survive, and an artifact an agent is
    mid-edit gets gated in a half-written state."""
    from pbt_port_fleet import cell_lock
    cell = _cell(tmp_path)
    called = []
    monkeypatch.setattr(regate_resume, "do_regate",
                        lambda *a, **k: called.append(a) or "regate -> GREEN")
    with cell_lock(cell):
        _iid, _bk, note, _w = regate_resume.run_cell(
            tmp_path, "django__django-1", "velvet", "regate", audit=False)
    assert note.startswith("busy: held by")
    assert called == [], "measured a cell another driver was writing"


def test_a_crashing_cell_does_not_take_the_pool_down(tmp_path, monkeypatch):
    _cell(tmp_path)

    def boom(*a, **k):
        raise ValueError("bad bundle")

    monkeypatch.setattr(regate_resume, "do_regate", boom)
    _iid, _bk, note, _w = regate_resume.run_cell(
        tmp_path, "django__django-1", "velvet", "regate", audit=False)
    assert "CRASHED: ValueError" in note


# ------------------------------------------------------------------ the root --

def test_the_benchmark_dir_flag_reaches_the_gates(monkeypatch):
    """Without this the flag reached only the classification: an invocation that
    passed `--benchmark-dir benchmark-verified` and forgot the variable read the
    real corpus and then stamped a freshly created `benchmark/<iid>/<backend>/`
    full of "model.py missing or empty"."""
    monkeypatch.delenv("SBU_BENCHMARK_DIR", raising=False)
    regate_resume._export_benchmark_dir(["x", "--benchmark-dir", "bench-v"])
    import os
    assert os.environ["SBU_BENCHMARK_DIR"] == "bench-v"
    monkeypatch.delenv("SBU_BENCHMARK_DIR", raising=False)
    regate_resume._export_benchmark_dir(["x", "--benchmark-dir=bench-v"])
    assert os.environ["SBU_BENCHMARK_DIR"] == "bench-v"


def test_an_absolute_variable_agrees_with_the_relative_flag(monkeypatch):
    """The documented invocation spells the variable absolutely and the flag
    relatively. They name the same directory, so that must not be refused -- and
    the comparison hangs a relative value off the PROJECT ROOT, the way
    `paths.TASKS_ROOT` does, not off the cwd."""
    monkeypatch.setenv("SBU_BENCHMARK_DIR", str(ROOT / "benchmark-verified"))
    regate_resume._export_benchmark_dir(["x", "--benchmark-dir",
                                        "benchmark-verified"])


def test_a_disagreeing_variable_is_refused(monkeypatch):
    """Whichever root won, the caller asked for something it did not get, and the
    two halves of the driver would report about different cells."""
    monkeypatch.setenv("SBU_BENCHMARK_DIR", "benchmark-pro")
    with pytest.raises(SystemExit) as e:
        regate_resume._export_benchmark_dir(["x", "--benchmark-dir",
                                            "benchmark-verified"])
    assert "disagrees" in str(e.value)


# ------------------------------------------------------------------- caps --

def test_nagini_gets_one_mutant_verifier():
    """A nagini cell fans a mutant out over many Z3 invocations and the driver
    multiplies that by --jobs. A mutant that misses its cap returns NO VERDICT,
    which is not a
    killed rival, so oversubscribing converts spec-strength evidence into
    unjudged mutants."""
    assert regate_resume._mutation_workers("nagini") == "1"
    assert regate_resume._mutation_workers("lean") == "2"
    assert regate_resume._mutation_workers("velvet") == "2"


def test_forcing_the_whole_corpus_is_refused(monkeypatch, tmp_path):
    """`--force` runs a fresh agentic audit per cell. Without a named target that
    is the whole corpus, which is hours of agent time each for cells nothing said
    were wrong."""
    monkeypatch.setattr(sys, "argv",
                        ["regate_resume.py", "--benchmark-dir", str(tmp_path),
                         "--backends", "velvet", "--force", "--dry-run"])
    with pytest.raises(SystemExit) as e:
        regate_resume.main()
    assert e.value.code != 0


# ---------------------------------------------------------------- do_regate --

def _wire(monkeypatch, cell: Path, *, verdict="GREEN", audit=None):
    """Stub out everything `do_regate` reaches for, recording what it asked for.

    The stub `run_gates` STAMPS meta.json, because the driver re-reads the record
    between stages rather than trusting the return value it just got -- which is
    the property worth keeping under test: the recorded stamp is the only thing
    `green_check` will read later.
    """
    ran: list[list[str]] = []
    audits: list[tuple] = []

    def run_gates(iid, backend, gates, **kw):
        ran.append(list(gates))
        meta = json.loads((cell / "meta.json").read_text())
        for g in gates:
            meta.setdefault("gates", {})[g] = {"status": "pass"}
        (cell / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
        return [_stub(gate=g, status="pass") for g in gates]

    monkeypatch.setitem(sys.modules, "green_check", _green(verdict, "ok"))
    monkeypatch.setitem(sys.modules, "swebench_unified.gates", _stub(
        STATIC_GATES=("G-VERIFY", "G-PBT"), DOCKER_GATES=("G-CONF",),
        run_gates=run_gates))
    monkeypatch.setitem(sys.modules, "swebench_unified.construct.build_one",
                        _stub(final_status_of=lambda rs: "ok",
                              run_audit_stage=lambda *a, **k: audits.append(a)
                              or [_stub(gate="G-EQ", status="pass")]))
    monkeypatch.setitem(sys.modules, "swebench_unified.agent",
                        _stub(AgentAuthError=type("AgentAuthError", (Exception,), {})))
    monkeypatch.setitem(sys.modules, "audit_freshness",
                        _stub(verdict_for=lambda c, b: (audit or "SPEC-IDENTICAL", "-")))
    monkeypatch.setitem(sys.modules, "check_stamp_freshness",
                        _stub(check_cell=lambda c, g: []))
    return ran, audits


def test_a_plain_regate_reruns_only_what_is_not_ok(tmp_path, monkeypatch):
    """Recorded ok stamps are trusted; a fresh judgment of a FAILING gate is the
    point of a re-gate. Re-running the passing ones would spend a verifier per
    cell to re-derive what is already recorded."""
    cell = _cell(tmp_path, gates={"G-VERIFY": {"status": "pass"},
                                  "G-PBT": {"status": "fail"},
                                  "G-CONF": {"status": "pass"},
                                  "G-EQ": {"status": "pass"},
                                  "G-PANEL": {"status": "pass"}})
    ran, audits = _wire(monkeypatch, cell)
    note = regate_resume.do_regate(tmp_path, "django__django-1", "velvet",
                                   audit=True)
    assert ran == [["G-PBT"]]
    assert audits == [], "a complete audit must not be re-run for free"
    assert "audit=skipped" in note


def test_force_reruns_every_mechanical_gate_static_first(tmp_path, monkeypatch):
    """Static before docker, so a static block does not spend Docker time, and
    the audit stage runs even though the recorded audit is complete -- which is
    what makes --force usable after a spec edit that `classify` cannot see."""
    cell = _cell(tmp_path, gates={"G-VERIFY": {"status": "pass"},
                                  "G-PBT": {"status": "pass"},
                                  "G-CONF": {"status": "pass"},
                                  "G-EQ": {"status": "pass"},
                                  "G-PANEL": {"status": "pass"}})
    ran, audits = _wire(monkeypatch, cell)
    regate_resume.do_regate(tmp_path, "django__django-1", "velvet",
                            audit=True, force=True)
    assert ran == [["G-VERIFY", "G-PBT"], ["G-CONF"]]
    assert len(audits) == 1


def test_a_static_block_does_not_spend_docker_time(tmp_path, monkeypatch):
    """The ordering has to be observable, not just intended: an attack battery or
    a container run aimed at a bundle whose proof does not close measures
    nothing."""
    cell = _cell(tmp_path, gates={})
    ran, audits = _wire(monkeypatch, cell)

    def run_gates_failing_static(iid, backend, gates, **kw):
        ran.append(list(gates))
        meta = json.loads((cell / "meta.json").read_text())
        for g in gates:
            meta.setdefault("gates", {})[g] = {
                "status": "fail" if g == "G-VERIFY" else "pass"}
        (cell / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
        return [_stub(gate=g, status="pass") for g in gates]

    sys.modules["swebench_unified.gates"].run_gates = run_gates_failing_static
    note = regate_resume.do_regate(tmp_path, "django__django-1", "velvet",
                                   audit=True, force=True)
    assert ran == [["G-VERIFY", "G-PBT"]], "ran docker gates over a static block"
    assert audits == []
    assert "audit=skipped" in note


def test_a_regate_that_skips_the_audit_reports_a_moved_spec(tmp_path,
                                                            monkeypatch):
    """End to end through `do_regate`: the note an operator reads has to name the
    condition, because it is created here and otherwise only surfaces in a later
    corpus sweep."""
    cell = _cell(tmp_path, gates={"G-VERIFY": {"status": "pass"},
                                  "G-PBT": {"status": "pass"},
                                  "G-CONF": {"status": "pass"},
                                  "G-EQ": {"status": "pass"},
                                  "G-PANEL": {"status": "pass"}})
    _wire(monkeypatch, cell, audit="RE-AUDIT")
    note = regate_resume.do_regate(tmp_path, "django__django-1", "velvet",
                                   audit=True)
    assert "audit=stale-not-rerun(" in note


# ------------------------------------------------------- the ax_apply_gold write --

def test_the_apply_gold_opt_in_is_written_atomically(tmp_path, monkeypatch):
    """Every writer of a corpus record goes through `atomic_io`. A plain
    `write_text` leaves meta.json truncated if the driver is killed mid-write, and
    `green_check.classify` reads a truncated record as NOTGREEN for a cell whose
    real state nobody measured."""
    from swebench_unified import atomic_io
    cell = _cell(tmp_path, backend="nagini", gates={"G-AX": {"status": "fail"}})
    (cell / "axiom_check.py").write_text("# probe\n")
    (tmp_path / "django__django-1" / "patch.diff").write_text("diff\n")

    wrote: list[Path] = []
    real = atomic_io.write_json_atomic

    def spy(path, obj, **kw):
        wrote.append(Path(path))
        real(path, obj, **kw)

    monkeypatch.setattr(atomic_io, "write_json_atomic", spy)
    monkeypatch.setitem(sys.modules, "swebench_unified.docker_exec", _stub(
        run_in_container=lambda *a, **k: _stub(returncode=0)))
    monkeypatch.setitem(sys.modules, "swebench_unified.gates", _stub(
        run_gates=lambda *a, **k: [_stub(gate="G-AX", status="pass")]))

    note = regate_resume._fix_ax_apply_gold(tmp_path, "django__django-1",
                                            "nagini")
    assert "ax_apply_gold set" in (note or "")
    assert wrote == [cell / "meta.json"]
    got = json.loads((cell / "meta.json").read_text())
    assert got["ax_apply_gold"] is True
    assert got["schema_version"] == 1, "the rest of the record has to survive"
