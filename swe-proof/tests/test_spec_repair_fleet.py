# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""spec_repair_fleet: not letting a retry re-tread a refuted repair.

The supervisor re-derives its lanes from the corpus every cycle, so a cell that
is still not green comes back around. Each attempt reads the same audit record,
so without a history the second agent starts from exactly the state the first
one did and reaches the same dead end. The outcomes that recur are the ones a
driver can name and an agent cannot see: a REPAIRED claim that edited nothing, a
clause that left one of the audit's own attacks still verifying, a realignment a
fresh audit refuted again.

These cover the carry-forward itself: what gets recorded, what deliberately does
not, and that the note an agent receives names the earlier refutation. No agents
and no verifier here.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import spec_repair_fleet as srf


@pytest.fixture()
def attempts(tmp_path, monkeypatch):
    monkeypatch.setattr(srf, "ATTEMPTS_DIR", tmp_path / "attempts")
    return tmp_path / "attempts"


def test_no_history_adds_nothing_to_the_prompt(attempts):
    # A first attempt must get the prompt the templates render, byte for byte:
    # an empty "previous attempts" section would read as "nothing worked yet".
    assert srf.attempts_note("astropy__astropy-1", "velvet") == ""


def test_the_note_names_the_earlier_refutation(attempts):
    srf.record_attempt("django__django-1", "nagini", "repair", {
        "status": "no-edit", "verdict": "REPAIRED",
        "detail": "claimed REPAIRED but the spec files are byte-identical"})
    note = srf.attempts_note("django__django-1", "nagini")
    assert "no-edit" in note
    assert "byte-identical" in note
    # and the vocabulary is explained, so the agent can act on the label
    assert "nothing was repaired" in note


def test_attempts_accumulate_in_order(attempts):
    for st in ("no-edit", "attack-verifies", "audit-fail"):
        srf.record_attempt("sympy__sympy-1", "lean", "panel", {"status": st})
    hist = srf.prior_attempts("sympy__sympy-1", "lean")
    assert [h["status"] for h in hist] == ["no-edit", "attack-verifies",
                                           "audit-fail"]


def test_only_the_last_few_are_recalled(attempts):
    for i in range(srf.ATTEMPT_RECALL + 3):
        srf.record_attempt("sympy__sympy-2", "lean", "repair",
                           {"status": f"st{i}", "detail": f"detail {i}"})
    note = srf.attempts_note("sympy__sympy-2", "lean")
    assert "detail 0" not in note          # dropped: the oldest repeat
    assert f"detail {srf.ATTEMPT_RECALL + 2}" in note
    # One rendered line per recalled attempt. Counted on the mode tick alone: an
    # age follows it, so anchoring on "`repair` ->" would tie this to whatever
    # the age happens to render as.
    assert note.count("`repair`") == srf.ATTEMPT_RECALL


def test_history_is_per_cell(attempts):
    srf.record_attempt("psf__requests-1", "velvet", "repair",
                       {"status": "no-edit"})
    assert srf.attempts_note("psf__requests-1", "lean") == ""
    assert srf.attempts_note("psf__requests-2", "velvet") == ""


def test_bookkeeping_never_fails_a_repair(attempts, monkeypatch):
    # The record is written after the repair already happened. An unwritable
    # log must not turn a landed repair into a crash.
    monkeypatch.setattr(srf, "ATTEMPTS_DIR", Path("/proc/nonexistent/attempts"))
    srf.record_attempt("astropy__astropy-2", "velvet", "repair",
                       {"status": "repaired"})


def test_a_corrupt_line_does_not_hide_the_rest(attempts):
    srf.record_attempt("astropy__astropy-3", "velvet", "repair",
                       {"status": "no-edit"})
    p = attempts / "astropy__astropy-3.velvet.jsonl"
    p.write_text(p.read_text() + "{ truncated\n")
    srf.record_attempt("astropy__astropy-3", "velvet", "repair",
                       {"status": "attack-verifies"})
    assert [h["status"] for h in srf.prior_attempts("astropy__astropy-3",
                                                   "velvet")] \
        == ["no-edit", "attack-verifies"]


def test_detail_is_bounded(attempts):
    srf.record_attempt("astropy__astropy-4", "velvet", "repair",
                       {"status": "gates-fail", "detail": "x" * 5000})
    line = json.loads((attempts / "astropy__astropy-4.velvet.jsonl")
                      .read_text().splitlines()[0])
    assert len(line["detail"]) <= 400


@pytest.mark.parametrize("status", ["busy", "already-green"])
def test_scheduling_outcomes_are_not_attempts(attempts, monkeypatch, status):
    """A cell nobody worked has not been attempted.

    Both statuses mean no agent ran: `busy` is another driver holding the lock,
    `already-green` is the cell having been finished between launch and its
    turn. Recording either would push a real refutation out of the recalled
    window with a scheduling artifact.
    """
    monkeypatch.setattr(srf, "_locked",
                        lambda *a, **k: {"iid": "i", "backend": "velvet",
                                         "status": status})
    monkeypatch.setattr(srf, "cell_lock", lambda b: _null())
    args = type("A", (), {"benchmark_dir": ".", "mode": "repair"})()
    srf.run_cell("i", "velvet", args, Path("."))
    assert not list(attempts.glob("*.jsonl")) if attempts.exists() else True


class _null:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


# ---- a disputed verdict is settled by re-deriving it, not by the dispute -----
#
# A repair agent that reads the audit record and argues NO-REPAIR-NEEDED used to
# end the attempt there. The cell stayed not-green with the same stamp, and the
# next round handed the same argument to another agent, which reached the same
# conclusion: the cell could never leave the lane. Now the driver re-runs the
# audit on the UNEDITED spec, which is the arbiter the whole pipeline already
# uses, and records which of the three things happened.

def _dispute_args(tmp_path, **kw):
    # Every flag `_locked` reads before it dispatches, defaulted the way argparse
    # defaults it. A stub that omits one does not fall back to the default -- it
    # raises AttributeError at the guard, so the test dies before reaching what it
    # is about, and the suite reports a driver bug where there is a fixture gap.
    a = {"benchmark": "swe_bench_verified", "benchmark_dir": ".",
         "mode": "repair", "no_reaudit": False, "reaudit_timeout": 60,
         "audit_role_timeout": 60, "attack_verify_timeout": 60,
         "no_stale_fast_path": True, "no_misroute_guard": True, "resume": False}
    a.update(kw)
    return type("A", (), a)()


def _meta(bundle: Path, eq_note: str, status: str = "fail") -> None:
    bundle.mkdir(parents=True, exist_ok=True)
    gates = {"G-EQ": {"status": status, "note": eq_note},
             "G-PANEL-1": {"status": "pass"}, "G-PANEL-2": {"status": "pass"},
             "G-PANEL-3": {"status": "pass"}}
    (bundle / "meta.json").write_text(json.dumps({"gates": gates}))


def test_a_disputed_verdict_triggers_one_fresh_audit(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(srf, "reaudit",
                        lambda *a, **k: calls.append(1) or True)
    monkeypatch.setattr(srf, "is_green", lambda b: (True, "ok"))
    monkeypatch.setattr(srf, "gate_status", lambda b, ks: {"G-EQ": "pass"})
    b = tmp_path / "nagini"
    _meta(b, "", status="pass")
    row = srf._reaudit_disputed("i__i-1", "nagini", _dispute_args(tmp_path),
                                tmp_path, b, {}, {"notes": "atk_7 is an echo"})
    assert len(calls) == 1, "exactly one re-audit: retrying until one passes " \
        "is how a weak spec would sneak through"
    assert row["status"] == "dispute-upheld"


def test_a_fresh_audit_that_finds_the_weakness_again_settles_the_dispute(
        tmp_path, monkeypatch):
    monkeypatch.setattr(srf, "reaudit", lambda *a, **k: True)
    monkeypatch.setattr(srf, "is_green", lambda b: (False, "G-EQ=fail"))
    monkeypatch.setattr(srf, "gate_status", lambda b, ks: {"G-EQ": "fail"})
    b = tmp_path / "nagini"
    _meta(b, "BROKEN (verify⇏correct): atk_2 verifies but its patch does not "
             "resolve — FAIL_TO_PASS fails 1/1: t::bug")
    row = srf._reaudit_disputed("i__i-1", "nagini", _dispute_args(tmp_path),
                                tmp_path, b, {}, {"notes": "not a defect"})
    assert row["status"] == "dispute-refused"


def test_an_inconclusive_fresh_audit_leaves_the_dispute_open(
        tmp_path, monkeypatch):
    """The distinction that keeps the attempt history honest.

    A verifier that hit its cap under load answers nothing. Calling that a
    refutation would tell the next agent its predecessor's argument had been
    tested and beaten, and the history is precisely what the next agent is told
    not to re-litigate.
    """
    monkeypatch.setattr(srf, "reaudit", lambda *a, **k: True)
    monkeypatch.setattr(srf, "is_green", lambda b: (False, "G-EQ=fail"))
    monkeypatch.setattr(srf, "gate_status", lambda b, ks: {"G-EQ": "fail"})
    b = tmp_path / "nagini"
    _meta(b, "eq: INCONCLUSIVE — 2 attack(s) inconclusive")
    row = srf._reaudit_disputed("i__i-1", "nagini", _dispute_args(tmp_path),
                                tmp_path, b, {}, {"notes": "not a defect"})
    assert row["status"] == "dispute-unsettled"
    assert "dispute-refused" != row["status"]


def test_a_reaudit_that_times_out_is_not_a_refutation(tmp_path, monkeypatch):
    monkeypatch.setattr(srf, "reaudit", lambda *a, **k: False)
    b = tmp_path / "nagini"
    _meta(b, "BROKEN (verify⇏correct): atk_2 verifies but its patch does not "
             "resolve")
    row = srf._reaudit_disputed("i__i-1", "nagini", _dispute_args(tmp_path),
                                tmp_path, b, {}, {"notes": "not a defect"})
    assert row["status"] == "no-repair-claimed"
    assert "timed out" in row["detail"]


def test_no_reaudit_keeps_the_old_reporting_behaviour(tmp_path, monkeypatch):
    monkeypatch.setattr(srf, "reaudit",
                        lambda *a, **k: pytest.fail("must not run"))
    b = tmp_path / "nagini"
    _meta(b, "BROKEN (verify⇏correct): x")
    row = srf._reaudit_disputed("i__i-1", "nagini",
                                _dispute_args(tmp_path, no_reaudit=True),
                                tmp_path, b, {}, {"notes": "no defect here"})
    assert row["status"] == "no-repair-claimed"
    assert row["detail"] == "no defect here"


# ---- a post-repair audit that reached no verdict is not a refutation ---------
#
# The same distinction as the dispute path above, on the other branch: after a
# repair lands and every mechanical gate passes, the cell is re-audited. If that
# audit does not run -- an agent launch failure, a saturated host -- all four
# roles are stamped fail and the cell is not green, which is indistinguishable by
# status alone from four roles that read the new spec and condemned it. Left
# unsplit, the legend tells every later agent that a fresh audit refuted the
# edit, so the one route that had never been tested is the one it is told to
# abandon.

_ALL_GATES = srf.STATIC_GATES + ("G-RESOLVE", "G-CONF", "G-AX")
_NO_VERDICT = ("eq: INCONCLUSIVE — the audit role did not run: "
               "Claude Code returned an error result")


def _post_repair_meta(bundle: Path, roles: dict) -> None:
    """A bundle whose mechanical gates all pass and whose roles are `roles`."""
    bundle.mkdir(parents=True, exist_ok=True)
    gates = {k: {"status": "pass"} for k in _ALL_GATES}
    gates.update(roles)
    (bundle / "meta.json").write_text(json.dumps({"gates": gates}))


def _drive_post_repair(tmp_path, monkeypatch, roles: dict, why: str) -> dict:
    b = tmp_path / "i__i-1" / "nagini"
    _post_repair_meta(b, roles)
    shas = iter(("before", "after"))
    monkeypatch.setattr(srf, "spec_sha", lambda *a, **k: next(shas))
    monkeypatch.setattr(srf, "agent", lambda *a, **k: {
        "payload": {"verdict": "REPAIRED", "witness_agrees": True},
        "wall_s": 1.0})
    monkeypatch.setattr(srf, "run_gates", lambda *a, **k: True)
    monkeypatch.setattr(srf, "reaudit", lambda *a, **k: True)
    monkeypatch.setattr(srf, "is_green", lambda bundle: (False, why))
    args = _dispute_args(tmp_path, mode="panel", resume=False,
                         gate_timeout=60, no_reaudit=False)
    return srf._locked("i__i-1", "nagini", args, tmp_path, b,
                       {"iid": "i__i-1", "backend": "nagini"})


def test_an_unrun_post_repair_audit_is_recorded_as_unmeasured(tmp_path,
                                                             monkeypatch):
    roles = {k: {"status": "fail", "note": _NO_VERDICT}
             for k in srf.AUDIT_GATES}
    row = _drive_post_repair(tmp_path, monkeypatch, roles,
                             "G-EQ=fail;G-PANEL-1=fail;G-PANEL-2=fail")
    assert row["status"] == "audit-unmeasured", \
        "no role judged this repair, so nothing about it was refuted"
    assert "NOT JUDGED" in row["detail"]
    assert "G-PANEL-2" in row["detail"]      # which roles owe a verdict


def test_one_adjudicating_role_still_refutes_the_repair(tmp_path, monkeypatch):
    """The direction that must survive: a real verdict outranks the outage.

    A repair that a role read and condemned is refuted even if the other three
    roles never ran, and softening that into "unmeasured" would let a weakened
    spec come back around with its refutation dropped from the history.
    """
    roles = {k: {"status": "fail", "note": _NO_VERDICT}
             for k in srf.AUDIT_GATES}
    roles["G-PANEL-2"] = {"status": "fail", "note":
                          "UNFAITHFUL: model returns 'a, b', real callee 'ab'"}
    row = _drive_post_repair(tmp_path, monkeypatch, roles, "G-PANEL-2=fail")
    assert row["status"] == "audit-fail"
    assert "refuted by G-PANEL-2" in row["detail"]
    # and the roles that owe a verdict are still disclosed
    assert "no verdict from" in row["detail"] and "G-EQ" in row["detail"]


def test_a_mechanical_regression_after_the_audit_is_not_an_audit_verdict(
        tmp_path, monkeypatch):
    """Every role passed and the cell is still not green, so the cause is a gate
    the re-audit re-stamped (it re-runs G-CONF and G-RESOLVE). Calling that an
    audit failure would send the cell to a review lane over a mechanical fault."""
    roles = {k: {"status": "pass"} for k in srf.AUDIT_GATES}
    row = _drive_post_repair(tmp_path, monkeypatch, roles, "G-CONF=fail")
    assert row["status"] == "gates-fail"
    assert "G-CONF=fail" in row["detail"]


def test_a_green_repair_is_recorded_repaired(tmp_path, monkeypatch):
    b = tmp_path / "i__i-1" / "nagini"
    _post_repair_meta(b, {k: {"status": "pass"} for k in srf.AUDIT_GATES})
    shas = iter(("before", "after"))
    monkeypatch.setattr(srf, "spec_sha", lambda *a, **k: next(shas))
    monkeypatch.setattr(srf, "agent", lambda *a, **k: {
        "payload": {"verdict": "REPAIRED", "witness_agrees": True},
        "wall_s": 1.0})
    monkeypatch.setattr(srf, "run_gates", lambda *a, **k: True)
    monkeypatch.setattr(srf, "reaudit", lambda *a, **k: True)
    monkeypatch.setattr(srf, "is_green", lambda bundle: (True, "GREEN"))
    args = _dispute_args(tmp_path, mode="panel", resume=False,
                         gate_timeout=60, no_reaudit=False)
    row = srf._locked("i__i-1", "nagini", args, tmp_path, b, {})
    assert row["status"] == "repaired"


def test_a_missing_meta_splits_into_nothing(tmp_path):
    # Fail SAFE: with no record to read, claim neither a refutation nor an
    # outage, so the caller falls through to the classifier's own reason.
    assert srf._audit_split(tmp_path / "absent") == ([], [])


# ---- the same distinction on the GATE branch, plus one re-measure ------------
#
# Before the audit runs, the repaired cell is re-gated. A gate that says `fail`
# refuted the edit; a gate that says `error` did not run at all. The shape that
# makes the distinction pay is every static gate erroring at once -- the runner
# failing, not five independent refutations. So the label is split, and because
# the agent hour is already spent, an all-unmeasured sweep is repeated once
# before the attempt is given up.

def _drive_gate_stage(tmp_path, monkeypatch, statuses: dict,
                      on_retry: dict | None = None,
                      battery_why: str = "") -> tuple[dict, list]:
    """Drive _locked to the gate stage. `statuses` is the first sweep's result;
    `on_retry`, if given, replaces the not-OK entries on the second sweep.

    `battery_why` is what `battery_load_error` reports. It defaults to "" -- the
    battery imports -- so that a test about gates not running is not also a test
    about a broken battery. Left to the real implementation it would inspect this
    fixture's bundle, which has no properties.py at all, and every erroring G-PBT
    here would come back `battery-broken`.
    """
    b = tmp_path / "i__i-1" / "nagini"
    b.mkdir(parents=True, exist_ok=True)
    gates = {k: {"status": "pass"} for k in srf.AUDIT_GATES}
    gates.update({k: {"status": v} for k, v in statuses.items()})
    (b / "meta.json").write_text(json.dumps({"gates": gates}))
    tags = []

    def _run_gates(iid, backend, args, log_dir, gs, tag):
        tags.append((tag, tuple(gs)))
        if tag == "gates-retry" and on_retry is not None:
            g = json.loads((b / "meta.json").read_text())["gates"]
            g.update({k: {"status": v} for k, v in on_retry.items()})
            (b / "meta.json").write_text(json.dumps({"gates": g}))
        return True

    shas = iter(("before", "after"))
    monkeypatch.setattr(srf, "spec_sha", lambda *a, **k: next(shas))
    monkeypatch.setattr(srf, "agent", lambda *a, **k: {
        "payload": {"verdict": "REPAIRED"}, "wall_s": 1.0})
    monkeypatch.setattr(srf, "run_gates", _run_gates)
    monkeypatch.setattr(srf, "reaudit", lambda *a, **k: True)
    monkeypatch.setattr(srf, "is_green", lambda bundle: (True, "GREEN"))
    monkeypatch.setattr(srf, "battery_load_error", lambda *a, **k: battery_why)
    args = _dispute_args(tmp_path, mode="repair", resume=False,
                         gate_timeout=60, no_reaudit=False)
    row = srf._locked("i__i-1", "nagini", args, tmp_path, b, {})
    return row, tags


def _all_pass() -> dict:
    keys = srf.STATIC_GATES + ("G-RESOLVE", "G-CONF", "G-AX")
    return {k: "pass" for k in keys}


def test_an_all_error_sweep_is_re_measured_once_and_clears(tmp_path,
                                                          monkeypatch):
    first = _all_pass() | {k: "error" for k in
                           ("G-VERIFY", "G-DIFF", "G-GOLD", "G-MUT", "G-PBT")}
    row, tags = _drive_gate_stage(tmp_path, monkeypatch, first,
                                  on_retry={k: "pass" for k in
                                            ("G-VERIFY", "G-DIFF", "G-GOLD",
                                             "G-MUT", "G-PBT")})
    assert row["status"] == "repaired", \
        "the runner failed, and on a second look the spec passes every gate"
    retries = [t for t in tags if t[0] == "gates-retry"]
    assert len(retries) == 1, "exactly one re-measure, never a loop"
    assert set(retries[0][1]) == {"G-VERIFY", "G-DIFF", "G-GOLD", "G-MUT",
                                  "G-PBT"}, "re-measure only what did not run"


def test_a_gate_that_will_not_run_twice_is_reported_unmeasured(tmp_path,
                                                               monkeypatch):
    first = _all_pass() | {"G-VERIFY": "error", "G-PBT": "error"}
    row, tags = _drive_gate_stage(tmp_path, monkeypatch, first, on_retry=None)
    assert row["status"] == "gates-unmeasured"
    assert "no verdict, twice" in row["detail"]
    assert len([t for t in tags if t[0] == "gates-retry"]) == 1


def test_a_battery_that_will_not_import_is_named_as_the_cause(tmp_path,
                                                              monkeypatch):
    """A G-PBT that errored because properties.py does not IMPORT is a measured
    mechanical defect with a named cause, not an absent verdict. Reported as
    `gates-unmeasured` it reads to the next agent as "the host was busy, try the
    same thing again", and the anchor keeps not importing, so no gate ever judges
    the repair -- which is how a cell becomes permanently unrepairable."""
    first = _all_pass() | {"G-PBT": "error"}
    row, _ = _drive_gate_stage(tmp_path, monkeypatch, first,
                               battery_why="AssertionError: prove_correct "
                                           "commitLimits body drifted")
    assert row["status"] == "battery-broken"
    assert "commitLimits body drifted" in row["detail"], \
        "the exact anchor has to reach the agent; 'it does not import' is not " \
        "actionable"
    assert "re-sync" in row["detail"]


def test_a_refuting_gate_outranks_a_broken_battery(tmp_path, monkeypatch):
    """A real refutation is about the edit and must win. The battery diagnosis
    only applies when nothing reached a verdict."""
    first = _all_pass() | {"G-PBT": "error", "G-VERIFY": "fail"}
    row, _ = _drive_gate_stage(tmp_path, monkeypatch, first,
                               battery_why="ImportError: no module named x")
    assert row["status"] == "gates-fail"
    assert "G-VERIFY=fail" in row["detail"]


def test_a_real_gate_refutation_is_not_re_measured(tmp_path, monkeypatch):
    """The load-bearing direction: a gate that reached a verdict against the edit
    must stop the attempt immediately. Re-running it would spend the gate budget
    on a question already answered, and a flaky pass would then let a refuted
    spec through to the audit."""
    first = _all_pass() | {"G-PBT": "fail"}
    row, tags = _drive_gate_stage(tmp_path, monkeypatch, first)
    assert row["status"] == "gates-fail"
    assert row["detail"].startswith("G-PBT=fail")
    assert not [t for t in tags if t[0] == "gates-retry"]


def test_a_refutation_alongside_an_outage_reports_the_refutation(tmp_path,
                                                                monkeypatch):
    first = _all_pass() | {"G-PBT": "fail", "G-VERIFY": "error"}
    row, tags = _drive_gate_stage(tmp_path, monkeypatch, first)
    assert row["status"] == "gates-fail"
    assert "G-PBT=fail" in row["detail"]
    assert not [t for t in tags if t[0] == "gates-retry"]


def test_the_unmeasured_vocabulary_reaches_the_next_agent(attempts):
    srf.record_attempt("django__django-3", "nagini", "panel", {
        "status": "audit-unmeasured", "verdict": "REPAIRED",
        "detail": "audit G-EQ=fail || NOT JUDGED: no verdict from G-EQ"})
    note = srf.attempts_note("django__django-3", "nagini")
    assert "audit-unmeasured" in note
    assert "untested rather than beaten" in note, \
        "the label misleads the next agent unless the note says it refutes nothing"


def test_the_dispute_vocabulary_reaches_the_next_agent(attempts):
    srf.record_attempt("django__django-2", "nagini", "repair", {
        "status": "dispute-refused", "verdict": "NO-REPAIR-NEEDED",
        "detail": "disputed the verdict; fresh audit G-EQ=fail"})
    note = srf.attempts_note("django__django-2", "nagini")
    assert "dispute-refused" in note
    assert "found it again" in note, \
        "the label is useless to the next agent unless the note explains it"


# ---- an agent that never ran is not an attempt ------------------------------
#
# The most expensive failure this driver had. `run_agent_step` retries a launch
# and eventually raises, so the subprocess exits non-zero having written no
# submission and touched no file. The driver used to carry on: a full gate sweep
# and a fresh audit against the spec that was already stamped, tens of minutes of
# verifier time to read the same stamp back, then recorded THAT as the attempt's
# outcome. A legend can fill up with lines written that way, and then every later
# agent on those cells is told its route was already refuted when nothing had
# ever been tried.

def _launch_failed_row(tmp_path, monkeypatch, *, rc=1, payload=None,
                       edited=False):
    b = tmp_path / "i__i-1" / "nagini"
    _post_repair_meta(b, {k: {"status": "fail"} for k in srf.AUDIT_GATES})
    shas = iter(("before", "after" if edited else "before"))
    monkeypatch.setattr(srf, "spec_sha", lambda *a, **k: next(shas))
    monkeypatch.setattr(srf, "agent", lambda *a, **k: {
        "rc": rc, "payload": payload or {}, "wall_s": 4.1})
    measured = []
    monkeypatch.setattr(srf, "run_gates",
                        lambda *a, **k: measured.append("gates") or True)
    monkeypatch.setattr(srf, "reaudit",
                        lambda *a, **k: measured.append("audit") or True)
    monkeypatch.setattr(srf, "is_green", lambda bundle: (False, "G-EQ=fail"))
    args = _dispute_args(tmp_path, mode="repair", resume=False,
                         gate_timeout=60, no_reaudit=False)
    row = srf._locked("i__i-1", "nagini", args, tmp_path, b, {})
    return row, measured


def test_an_agent_that_produced_nothing_is_not_measured(tmp_path, monkeypatch):
    row, measured = _launch_failed_row(tmp_path, monkeypatch)
    assert row["status"] == "launch-failed"
    assert measured == [], \
        "re-measuring an untouched spec spends an hour to read its own stamp"


def test_a_launch_failure_is_not_recorded_against_the_cell(attempts,
                                                           monkeypatch):
    monkeypatch.setattr(srf, "_locked",
                        lambda *a, **k: {"status": "launch-failed"})
    monkeypatch.setattr(srf, "cell_lock", lambda b: _null())
    args = type("A", (), {"benchmark_dir": ".", "mode": "repair"})()
    srf.run_cell("i", "velvet", args, Path("."))
    assert not (attempts.exists() and list(attempts.glob("*.jsonl")))


def test_an_agent_that_edited_and_then_died_is_still_measured(tmp_path,
                                                             monkeypatch):
    """The conjunct that makes the short-circuit safe.

    A non-zero exit says nothing about whether work happened. If the spec moved,
    the edit is live in the corpus and has to be judged on its own terms --
    skipping it would leave an unmeasured change in a released artifact.
    """
    row, measured = _launch_failed_row(tmp_path, monkeypatch, edited=True)
    assert row["status"] != "launch-failed"
    assert "gates" in measured


def test_a_submitted_verdict_outranks_a_bad_exit_code(tmp_path, monkeypatch):
    """An agent that submitted then crashed on the way out did the work."""
    row, measured = _launch_failed_row(
        tmp_path, monkeypatch, payload={"verdict": "REPAIRED"})
    assert row["status"] == "no-edit", \
        "its own claim is what it is judged on, not its exit status"


def test_the_history_drops_lines_written_before_the_label_existed(attempts):
    """The legacy signature: no verdict, an outcome that is the pre-existing
    stamp read back, and an agent that returned faster than the prompt takes to
    read. Filtered on the way OUT, so no history file has to be rewritten."""
    srf.record_attempt("django__django-9", "nagini", "repair", {
        "status": "gates-fail", "verdict": "",
        "detail": "G-PBT=fail G-MUT=fail", "agent_s": 4.1})
    srf.record_attempt("django__django-9", "nagini", "repair", {
        "status": "audit-fail", "verdict": "REPAIRED",
        "detail": "audit G-EQ=fail", "agent_s": 3800.0})
    hist = srf.prior_attempts("django__django-9", "nagini")
    assert [h["status"] for h in hist] == ["audit-fail"], \
        "the real refutation is kept; the non-event is not"
    assert "G-PBT" not in srf.attempts_note("django__django-9", "nagini")


def test_a_fast_refutation_by_a_real_verdict_is_kept(attempts):
    """A cell whose gates refuted a REPAIRED claim in seconds is evidence: the
    agent reported a verdict, so the speed is the gate's, not a dead launch."""
    srf.record_attempt("django__django-8", "lean", "repair", {
        "status": "gates-fail", "verdict": "REPAIRED",
        "detail": "G-HYGIENE=fail", "agent_s": 5.0})
    assert len(srf.prior_attempts("django__django-8", "lean")) == 1


# --- the guard that keeps a host outage out of a repair agent's hands ---------
#
# A role whose agent CLI never came up is stamped `fail`, because the gates fail
# closed and an unjudged spec is not a green spec. But it names no attack, so a
# repair agent is handed a premise ("this spec admits a wrong implementation")
# with no counterexample to study. The honest outcome costs a whole agent step;
# the dishonest one writes a clause into a spec nothing found a defect in.
#
# `_stale_only` does not catch these: a role can time out against the exact bytes
# on disk, so the stamp is FRESH.

_INC = "eq: INCONCLUSIVE — the audit role did not run (agent CLI timed out)"
_REAL = ("BROKEN (verify⇏correct): atk_4.py verifies but its patch does not "
         "resolve — FAIL_TO_PASS fails 1/3")


def _gates(bundle: Path, gates: dict) -> Path:
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "meta.json").write_text(json.dumps({"gates": gates}))
    return bundle


def test_an_audit_that_never_ran_is_diverted_to_a_measurement(tmp_path):
    b = _gates(tmp_path / "nagini", {
        "G-EQ": {"status": "fail", "detail": _INC},
        "G-PANEL-1": {"status": "fail", "detail": "panel_1: INCONCLUSIVE — the "
                                                 "audit role did not run"},
        "G-VERIFY": {"status": "pass"}})
    assert srf._unmeasured_only(b) == ["G-EQ", "G-PANEL-1"]


def test_one_real_finding_alongside_an_outage_still_gets_an_agent(tmp_path):
    """The safety property. A substantive fail is a reproducible counterexample
    and an agent must see it, however many roles failed to launch beside it."""
    b = _gates(tmp_path / "nagini", {
        "G-EQ": {"status": "fail", "detail": _REAL},
        "G-PANEL-1": {"status": "fail", "detail": "panel_1: INCONCLUSIVE — the "
                                                  "audit role did not run"}})
    assert srf._unmeasured_only(b) == []


def test_a_mechanical_gate_is_not_a_re_audits_to_fix(tmp_path):
    """A re-audit re-runs the reviewer roles and nothing else, so it is no remedy
    for a battery that hit its verifier cap. That cell needs a re-gate at a
    higher cap, and diverting it here would record a re-audit that could not
    have addressed it."""
    b = _gates(tmp_path / "nagini", {
        "G-EQ": {"status": "fail", "detail": _INC},
        "G-PBT": {"status": "error",
                  "detail": "TIMED-OUT: 1 case(s) hit the 1800s verifier cap"}})
    assert srf._unmeasured_only(b) == []


def test_the_panel_aggregate_does_not_decide_for_its_roles(tmp_path):
    """G-PANEL restates the roles it is derived from. Counting it would let its
    inherited text answer a question the roles themselves already answered --
    here it carries a role's real finding, and the roles are all unmeasured."""
    b = _gates(tmp_path / "nagini", {
        "G-EQ": {"status": "fail", "detail": _INC},
        "G-PANEL": {"status": "fail", "detail": f"G-PANEL-1: {_REAL}"},
        "G-PANEL-1": {"status": "fail", "detail": "panel_1: INCONCLUSIVE"}})
    assert srf._unmeasured_only(b) == ["G-EQ", "G-PANEL-1"]


def test_a_green_cell_is_never_diverted(tmp_path):
    b = _gates(tmp_path / "nagini", {"G-EQ": {"status": "pass"},
                                     "G-PANEL-1": {"status": "skip"}})
    assert srf._unmeasured_only(b) == []


def test_an_unreadable_bundle_is_not_a_reason_to_skip_an_agent(tmp_path):
    assert srf._unmeasured_only(tmp_path / "absent") == []
    b = tmp_path / "torn"
    b.mkdir()
    (b / "meta.json").write_text("{not json")
    assert srf._unmeasured_only(b) == []


def test_the_diverted_cell_is_labelled_for_what_was_wrong_with_it(
        tmp_path, monkeypatch):
    """Not `stale-*`: that label means the spec had been repaired and nobody had
    looked yet, which is a different fact about the cell."""
    monkeypatch.setattr(srf, "reaudit", lambda *a, **k: True)
    monkeypatch.setattr(srf, "is_green", lambda b: (True, "ok"))
    monkeypatch.setattr(srf, "gate_status", lambda b, ks: {"G-EQ": "pass"})
    b = _gates(tmp_path / "nagini", {"G-EQ": {"status": "fail",
                                              "detail": _INC}})
    row = srf._reaudit_stale("i__i-1", "nagini", _dispute_args(tmp_path),
                             tmp_path, b, {}, ["G-EQ"], label="unmeasured",
                             because="reached no verdict")
    assert row["status"] == "unmeasured-cleared"
    assert "reached no verdict" in row["detail"]
    assert row["agent_s"] == 0.0, "no agent ran, so it cost no agent time"


def test_a_stale_diversion_keeps_its_own_label(tmp_path, monkeypatch):
    monkeypatch.setattr(srf, "reaudit", lambda *a, **k: True)
    monkeypatch.setattr(srf, "is_green", lambda b: (True, "ok"))
    monkeypatch.setattr(srf, "gate_status", lambda b, ks: {"G-EQ": "pass"})
    b = _gates(tmp_path / "nagini", {"G-EQ": {"status": "fail", "detail": ""}})
    row = srf._reaudit_stale("i__i-1", "nagini", _dispute_args(tmp_path),
                             tmp_path, b, {}, ["G-EQ"])
    assert row["status"] == "stale-cleared"
    assert "no longer on disk" in row["detail"]


# --- an errored MECHANICAL gate must not force a repair agent ----------------
#
# `_stale_only` needs every failing gate to be provably stale. A gate that
# recorded `error` and carries no `sources` is unknowable, so it used to
# disqualify the whole cell -- and that is inverted rather than conservative: an
# `error` reached no verdict at all, so it cannot be the live hole the guard
# protects, while the audit findings beside it were provably about a spec that is
# gone. The cost of the inversion is a repair agent spent on findings that were
# void, on a cell held out only by an errored G-MUT or G-PBT.


def _stale(h="deadbeef"):
    return {"model.py": h}


def _bundle_with_spec(tmp_path, gates, body="current spec\n"):
    b = tmp_path / "nagini"
    b.mkdir(parents=True, exist_ok=True)
    (b / "model.py").write_text(body)
    (b / "meta.json").write_text(json.dumps({"gates": gates}))
    return b


def test_an_errored_mechanical_gate_does_not_veto_the_stale_fast_path(tmp_path):
    """The cell still stays red on G-MUT; what this unlocks is the re-audit that
    settles the spec question without spending an agent on a void finding."""
    b = _bundle_with_spec(tmp_path, {
        "G-EQ": {"status": "fail", "detail": _REAL, "sources": _stale()},
        "G-PANEL-1": {"status": "fail", "detail": _REAL, "sources": _stale()},
        "G-MUT": {"status": "error", "detail": "2 mutant(s) reached no verdict"}})
    assert srf._stale_only(b) == ["G-EQ", "G-PANEL-1"]


def test_a_failing_mechanical_gate_still_vetoes_it(tmp_path):
    """`fail` is a verdict about the artifact. Undigested, it cannot be shown
    stale, so it may be a live refutation and the agent must see it."""
    b = _bundle_with_spec(tmp_path, {
        "G-EQ": {"status": "fail", "detail": _REAL, "sources": _stale()},
        "G-MUT": {"status": "fail", "detail": "killed 12/20 (60%)"}})
    assert srf._stale_only(b) == []


def test_an_errored_audit_role_stays_in_the_quorum(tmp_path):
    """An errored ROLE is a spec question nobody answered. Excluding it would let
    a scoped re-audit clear the stale roles and leave it standing."""
    b = _bundle_with_spec(tmp_path, {
        "G-EQ": {"status": "fail", "detail": _REAL, "sources": _stale()},
        "G-PANEL-2": {"status": "error", "detail": "role did not run"}})
    assert srf._stale_only(b) == [], "undigested errored role is unknowable"


def test_a_fresh_finding_beside_an_errored_gate_still_gets_an_agent(tmp_path):
    """The safety property, unchanged: a live hole outranks everything."""
    import hashlib
    body = "current spec\n"
    fresh = {"model.py": hashlib.sha256(body.encode()).hexdigest()}
    b = _bundle_with_spec(tmp_path, {
        "G-EQ": {"status": "fail", "detail": _REAL, "sources": fresh},
        "G-MUT": {"status": "error", "detail": "no verdict"}}, body=body)
    assert srf._stale_only(b) == []


def test_an_errored_mechanical_gate_alone_is_not_a_stale_cell(tmp_path):
    """Nothing was shown stale, so there is no basis to skip anything."""
    b = _bundle_with_spec(tmp_path, {
        "G-MUT": {"status": "error", "detail": "no verdict"}})
    assert srf._stale_only(b) == []


def test_both_diversion_vocabularies_reach_the_next_agent(attempts):
    srf.record_attempt("sympy__sympy-7", "lean", "repair",
                       {"status": "unmeasured-refuted", "verdict": "",
                        "detail": "the fresh audit found a weakness"})
    note = srf.attempts_note("sympy__sympy-7", "lean")
    assert "unmeasured-refuted" in note
    assert "fail closed" in note, "the label has to be explained to be usable"


# --- the age that makes a refutation placeable against the spec on disk -------


def test_an_attempt_is_stamped_with_a_comparable_time(attempts):
    """Same key and format as a gate entry's `checked_at`, so a history line and
    a gate verdict can be ordered against each other."""
    srf.record_attempt("django__django-7", "nagini", "repair",
                       {"status": "no-edit"})
    rec = srf.prior_attempts("django__django-7", "nagini")[0]
    from datetime import datetime, timezone
    when = datetime.fromisoformat(rec["at"])
    assert when.tzinfo is not None, "a naive stamp cannot be compared across hosts"
    assert abs((datetime.now(timezone.utc) - when).total_seconds()) < 300


@pytest.mark.parametrize("hours,expect", [
    (0.2, "under an hour"), (5, "5h ago"), (30, "30h ago"), (72, "3d ago")])
def test_the_age_is_coarse_and_human(hours, expect):
    from datetime import datetime, timedelta, timezone
    at = (datetime.now(timezone.utc) - timedelta(hours=hours))
    assert expect in srf._attempt_age({"at": at.isoformat(timespec="seconds")})


@pytest.mark.parametrize("rec", [
    {}, {"at": ""}, {"at": "not-a-date"}, {"at": 17}])
def test_an_unstamped_line_claims_no_age_rather_than_guessing_zero(rec):
    """A line written before stamping has an UNKNOWN vintage. Rendering it as
    "under an hour ago" would present the oldest refutation on the cell as the
    freshest evidence about it."""
    assert srf._attempt_age(rec) == ""


def test_a_naive_stamp_is_read_as_utc_not_as_local(attempts):
    """Records are compared across hosts, so a stamp with no offset has to be
    read the way it was written rather than reinterpreted in the reader's zone."""
    from datetime import datetime, timedelta, timezone
    naive = (datetime.now(timezone.utc) - timedelta(hours=9)).replace(tzinfo=None)
    assert srf._attempt_age({"at": naive.isoformat(timespec="seconds")}) \
        == " (9h ago)"


def test_the_guard_stops_the_agent_before_it_is_launched(tmp_path, monkeypatch):
    """The claim at the level it matters: no agent process for an outage cell.

    Checked through `_locked` with the guards ENABLED, because the unit tests
    above call the diversion directly and would still pass if nothing ever
    reached it -- which is exactly the bug this closes.
    """
    launched = []
    monkeypatch.setattr(srf, "agent",
                        lambda *a, **k: launched.append(1) or {
                            "rc": 0, "payload": {}, "wall_s": 1.0})
    monkeypatch.setattr(srf, "reaudit", lambda *a, **k: True)
    monkeypatch.setattr(srf, "is_green", lambda b: (True, "ok"))
    monkeypatch.setattr(srf, "gate_status", lambda b, ks: {"G-EQ": "pass"})
    b = _gates(tmp_path / "nagini", {"G-EQ": {"status": "fail",
                                             "detail": _INC},
                                     "G-VERIFY": {"status": "pass"}})
    args = _dispute_args(tmp_path, no_stale_fast_path=False,
                         no_misroute_guard=True)
    row = srf._locked("i__i-1", "nagini", args, tmp_path, b, {})
    assert launched == [], "an outage cell must not cost an agent step"
    assert row["status"] == "unmeasured-cleared"


def test_the_guard_lets_a_real_finding_through_to_the_agent(tmp_path,
                                                            monkeypatch):
    """The other half, and the one a bug here would break silently: a cell with a
    reproducible counterexample still reaches an agent."""
    launched = []
    monkeypatch.setattr(srf, "agent",
                        lambda *a, **k: launched.append(1) or {
                            "rc": 0, "payload": {"verdict": "REPAIRED"},
                            "wall_s": 1.0})
    monkeypatch.setattr(srf, "spec_sha", lambda *a, **k: object())
    monkeypatch.setattr(srf, "run_gates", lambda *a, **k: True)
    monkeypatch.setattr(srf, "reaudit", lambda *a, **k: True)
    monkeypatch.setattr(srf, "is_green", lambda b: (True, "GREEN"))
    monkeypatch.setattr(srf, "gate_status", lambda b, ks: {"G-EQ": "pass"})
    b = _gates(tmp_path / "nagini", {"G-EQ": {"status": "fail",
                                             "detail": _REAL}})
    args = _dispute_args(tmp_path, no_stale_fast_path=False,
                         no_misroute_guard=True, gate_timeout=60)
    srf._locked("i__i-1", "nagini", args, tmp_path, b, {})
    assert launched == [1], "a reproducible finding must still reach an agent"
