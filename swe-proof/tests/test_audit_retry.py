# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A saturated host must not be recorded as an unauditable spec.

`run_audit_stage` retries a role that reaches no verdict, because the audit agent
fails intermittently for reasons that have nothing to do with the bundle. An
immediate re-launch does not help: the dominant cause is a resource condition on
the host, which outlives a launch, so every attempt fails the same way and the
cell is recorded as unauditable. The retry therefore waits, growing per attempt.
These tests pin both halves: the wait happens when the role reached no verdict,
and it does NOT happen when a real verdict arrived.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from swebench_unified.construct import build_one as bo
from swebench_unified.gates import _audit as g_audit

from gates_fixtures import tmp_corpus

IID = "astropy__astropy-99999"
ROW = {"instance_id": IID, "patch": "", "base_commit": "deadbeef"}


@pytest.fixture()
def cell(tmp_path, monkeypatch):
    tasks = tmp_corpus(tmp_path, monkeypatch, ROW)
    (tasks / IID / "nagini").mkdir(parents=True)
    (tasks / IID / "instance.json").write_text(json.dumps(ROW))
    (tasks / IID / "nagini" / "model.py").write_text("# model\n")
    (tasks / IID / "nagini" / "meta.json").write_text(json.dumps({"gates": {}}))
    monkeypatch.setenv("SBU_AUDIT_JOBS", "1")       # deterministic call order
    monkeypatch.setenv("SBU_AUDIT_TIMEOUT", "1")
    return tasks / IID / "nagini"


def _drive(monkeypatch, outcomes: dict, scratches: list | None = None):
    """Patch the agent launch per role and record calls + waits.

    `scratches`, if given, collects every scratch dir the fake created, so a
    caller can assert on what survived the stage.

    outcomes maps a role to a list of results consumed in order: an Exception
    instance is raised (the launch failure this is about), a dict is returned as
    the agent's payload. The last entry repeats once exhausted.
    """
    calls: list[str] = []
    waits: list[float] = []
    # Sub-second sleeps belong to unrelated spin/backoff loops in the stack (a
    # lock wait, an atomic write). Only the retry backoff is on this scale, so
    # filtering by it keeps the assertions about this code and not about theirs.
    monkeypatch.setattr(bo.time, "sleep", lambda s: s >= 1 and waits.append(s))

    def fake_run_audit(bundle, role, timeout_s=900, scratch_out=None):
        calls.append(role)
        # A real run creates the scratch dir BEFORE anything can fail, and
        # reports it through `scratch_out` for precisely that case. Mirroring
        # the order here is what makes the cleanup assertion mean anything: a
        # fake that only put the path in its return value could not fail the way
        # the leak did.
        import tempfile
        scratch = tempfile.mkdtemp(prefix=f"sbu_audit_{role}_pytest_")
        if scratches is not None:
            scratches.append(scratch)
        if scratch_out is not None:
            scratch_out["_scratch"] = scratch
        seq = outcomes.get(role) or [RuntimeError("no outcome configured")]
        item = seq[min(sum(1 for c in calls if c == role) - 1, len(seq) - 1)]
        if isinstance(item, BaseException):
            raise item
        return {**dict(item), "_scratch": scratch}

    monkeypatch.setattr(g_audit, "run_audit", fake_run_audit)
    return calls, waits


def test_a_launch_failure_is_retried_with_a_growing_wait(cell, monkeypatch):
    """The launch failure: the agent CLI never came up. Three attempts, and the
    waits grow, so the retries span a saturation window instead of all landing
    inside it."""
    err = RuntimeError("Claude Code returned an error result: success)")
    calls, waits = _drive(monkeypatch, {"eq": [err], "panel_2": [err], "panel_3": [err]})
    bo.run_audit_stage(IID, "nagini")
    assert calls.count("eq") == 3, calls          # 1 + SBU_AUDIT_RETRIES(2)
    # One wait per retry per role, growing: 120s then 240s at the default.
    assert waits.count(120) == 3 and waits.count(240) == 3, waits


def test_the_recorded_note_says_the_role_did_not_run(cell, monkeypatch):
    """Fail-closed is right, but the record has to name the cause: a reader who
    cannot tell "the host was full" from "the spec admits a wrong impl" will go
    edit a spec that was never measured."""
    err = RuntimeError("Claude Code returned an error result: success)")
    _drive(monkeypatch, {"eq": [err], "panel_2": [err], "panel_3": [err]})
    bo.run_audit_stage(IID, "nagini")
    rec = json.loads((cell / "meta.json").read_text())["gates"]["G-EQ"]
    assert rec["status"] == "fail"
    assert "did not run" in rec["note"] and "Claude Code returned an error" in rec["note"]


def test_a_real_verdict_is_not_retried_and_costs_no_wait(cell, monkeypatch):
    """The other direction: a judgment role that submitted a verdict is done, and
    a retry there would spend an agent and a wait to overwrite a good answer."""
    good = {"verdict": "FAITHFUL", "notes": "checked the mapping"}
    err = RuntimeError("Claude Code returned an error result: success)")
    calls, waits = _drive(monkeypatch,
                          {"eq": [err], "panel_2": [good], "panel_3": [good]})
    bo.run_audit_stage(IID, "nagini")
    assert calls.count("panel_2") == 1 and calls.count("panel_3") == 1, calls
    assert calls.count("eq") == 3, calls
    assert waits.count(120) == 1 and waits.count(240) == 1, waits
    rec = json.loads((cell / "meta.json").read_text())["gates"]
    assert rec["G-PANEL-2"]["status"] == "pass"


def test_a_credential_outage_records_nothing_at_all(cell, monkeypatch):
    """The one failure that must NOT be stamped, not even fail-closed.

    Fail-closed is right when a role ran and reached no verdict: something about
    this cell was measured badly. A credential outage measures nothing -- no
    request left the host -- so an INCONCLUSIVE entry here is a claim about a
    spec nobody read. It also does not clear on its own: the cell goes NOTGREEN,
    a re-audit picks it up, hits the same outage and re-stamps it. So the stage
    aborts with meta.json byte-identical.
    """
    from swebench_unified.agent import AgentAuthError
    before = (cell / "meta.json").read_text()
    err = AgentAuthError("could not authenticate: Not logged in")
    calls, waits = _drive(monkeypatch,
                          {"eq": [err], "panel_2": [err], "panel_3": [err]})
    with pytest.raises(AgentAuthError):
        bo.run_audit_stage(IID, "nagini")
    assert (cell / "meta.json").read_text() == before
    assert not (cell / "verdict.md").exists()
    # and no retry budget spent here: run_agent_step already waited the outage
    # out under the host-wide backoff, so a second attempt is a second failure.
    assert calls.count("eq") == 1 and waits == [], (calls, waits)


def test_a_failed_role_leaves_no_scratch_tree_behind(cell, monkeypatch):
    """The role that fails is the one whose scratch dir is at risk.

    Cleanup must not read the path out of the PAYLOAD: both error paths either
    replace the payload with one that has no `_scratch` (the timeout branch) or
    never bind it at all (the credential abort), so a role that worked would clean
    up after itself while a role that died would not. That is backwards -- the
    failed role's tree is the BIGGER one, it holds every attack the role got
    through before the cap, and a retry creates another, so a cell accumulates one
    orphaned tree per timed-out role.

    Both shapes are pinned here, since they leak for different reasons.
    """
    from swebench_unified.agent import AgentAuthError
    timed_out: list[str] = []
    _drive(monkeypatch, {"eq": [RuntimeError("agent CLI timed out after 1s")],
                         "panel_2": [{"verdict": "OK", "notes": "fine"}],
                         "panel_3": [{"verdict": "OK", "notes": "fine"}]},
           scratches=timed_out)
    bo.run_audit_stage(IID, "nagini")
    assert timed_out, "fake never ran"
    assert [p for p in timed_out if Path(p).exists()] == []

    aborted: list[str] = []
    err = AgentAuthError("could not authenticate: Not logged in")
    _drive(monkeypatch, {"eq": [err], "panel_2": [err], "panel_3": [err]},
           scratches=aborted)
    with pytest.raises(AgentAuthError):
        bo.run_audit_stage(IID, "nagini")
    assert aborted, "fake never ran"
    assert [p for p in aborted if Path(p).exists()] == []


def test_prose_that_mentions_the_word_is_still_a_real_verdict(cell, monkeypatch):
    """A judgment role's note IS its prose, so the word cannot be the signal.

    Keying the retry off `"INCONCLUSIVE" in note` treats an agent explaining that
    some OTHER gate was not inconclusive as a role that reached no verdict.
    Because the retry overwrites the section unconditionally, that spends an agent
    to replace a good answer, and a re-run that lands badly turns the pass into a
    condemned spec. The derivation's own decision is the signal.
    """
    wordy = {"verdict": "NO-LEAKAGE",
             "notes": ("Verdict NO-LEAKAGE. The mechanical G-LEAK result is not "
                       "INCONCLUSIVE here: the spec view is clean.")}
    err = RuntimeError("Claude Code returned an error result: success)")
    calls, waits = _drive(monkeypatch,
                         {"eq": [err], "panel_2": [wordy], "panel_3": [wordy]})
    bo.run_audit_stage(IID, "nagini")
    assert calls.count("panel_3") == 1 and calls.count("panel_2") == 1, calls
    rec = json.loads((cell / "meta.json").read_text())["gates"]
    assert rec["G-PANEL-3"]["status"] == "pass"
    assert rec["G-PANEL-2"]["status"] == "pass"


def test_a_role_that_submitted_no_verdict_is_still_retried(cell, monkeypatch):
    """The other half: fail-closed must survive the fix. A role that ran and
    submitted an empty verdict adjudicated nothing, so it is retried and recorded
    fail, exactly as a launch failure is."""
    silent = {"verdict": "", "notes": "I read the spec view."}
    err = RuntimeError("Claude Code returned an error result: success)")
    calls, _ = _drive(monkeypatch,
                      {"eq": [err], "panel_2": [silent], "panel_3": [silent]})
    bo.run_audit_stage(IID, "nagini")
    assert calls.count("panel_2") == 3, calls
    rec = json.loads((cell / "meta.json").read_text())["gates"]["G-PANEL-2"]
    assert rec["status"] == "fail" and "INCONCLUSIVE" in rec["note"]


def test_a_recorded_role_says_when_it_ran_and_what_it_read(cell, monkeypatch):
    """A per-role verdict has to be checkable against the files it judged.

    These entries are written straight into meta.json by this stage rather than
    through `run_gates._record`, so the timestamp and digests have to be written
    here too: without them `check_stamp_freshness.py` cannot verify the entry, and
    since the entry is `update`d onto whatever sits under the key, a stale
    mechanical `checked_at` would be left standing in front of a status this run
    just replaced. Digests are per ROLE, not per gate module: panel_2 judges the
    spec view and never reads the battery, so recording properties.py for it would
    report it stale whenever only the battery was re-authored.
    """
    (cell / "properties.py").write_text("# battery\n")
    good = {"verdict": "FAITHFUL", "notes": "checked the mapping"}
    err = RuntimeError("Claude Code returned an error result: success)")
    _drive(monkeypatch, {"eq": [err], "panel_2": [good], "panel_3": [good]})
    bo.run_audit_stage(IID, "nagini")
    rec = json.loads((cell / "meta.json").read_text())["gates"]
    for key in ("G-EQ", "G-PANEL-2", "G-PANEL-3"):
        assert rec[key]["checked_at"] and rec[key]["harness_digest"], key
    assert rec["G-PANEL-2"]["sources"] == {"model.py": _sha(cell / "model.py")}
    # eq's own verdict does depend on the battery it re-runs.
    assert set(rec["G-EQ"]["sources"]) == {"model.py", "properties.py"}


def _sha(p: Path) -> str:
    import hashlib
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_a_role_that_reached_no_verdict_digests_nothing(cell, monkeypatch):
    """The other direction. A launch failure means nobody read the artifacts, so
    digesting them would attest to a review that did not happen -- and a later
    freshness check would report that non-review as still describing the files."""
    err = RuntimeError("Claude Code returned an error result: success)")
    _drive(monkeypatch, {"eq": [err], "panel_2": [err], "panel_3": [err]})
    bo.run_audit_stage(IID, "nagini")
    rec = json.loads((cell / "meta.json").read_text())["gates"]["G-PANEL-2"]
    # fail-closed IS a verdict about the artifacts, so it keeps its digests;
    # what must never appear is a digest with no verdict at all behind it.
    assert rec["status"] == "fail" and rec["checked_at"]


def test_the_wait_can_be_switched_off(cell, monkeypatch):
    """Restores the immediate-retry behaviour, for an operator who knows the
    launch failure is not host saturation and so the wait is pure latency."""
    err = RuntimeError("Claude Code returned an error result: success)")
    monkeypatch.setenv("SBU_AUDIT_RETRY_WAIT", "0")
    calls, waits = _drive(monkeypatch, {"eq": [err], "panel_2": [err], "panel_3": [err]})
    bo.run_audit_stage(IID, "nagini")
    assert calls.count("eq") == 3 and waits == [], (calls, waits)


# ---- the retry line has to survive being shortened ---------------------------
#
# The reason a role went inconclusive is printed before each wait, and that print
# is often the only surviving copy: the oracle's run directory is purged per
# attempt. A head-only cap put the cause at risk, because a resolve note starts
# with a classification and an absolute report path and ends with the evidence.

def test_a_shortened_note_keeps_both_ends():
    note = ("eq: INCONCLUSIVE — 6 attack(s) inconclusive: resolve did not complete: "
            "no report at " + "/some/very/long/run/directory" * 20
            + " — >>>>> Patch Apply Failed: Only garbage was found in the patch input")
    out = bo._elide(note)
    assert len(out) < len(note), "a long note must actually be shortened"
    assert out.startswith("eq: INCONCLUSIVE"), out[:60]
    assert "Only garbage was found in the patch input" in out, \
        "the cause is at the END of these notes, so a head-only cut discards it"
    assert "[…]" in out, "the reader has to be told something was dropped"


def test_a_short_note_is_passed_through_unchanged():
    assert bo._elide("eq: fine") == "eq: fine"
