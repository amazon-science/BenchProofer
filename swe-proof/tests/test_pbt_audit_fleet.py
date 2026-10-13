# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""pbt_audit_fleet: recording an audit without letting it grade itself.

The audit agent is allowed to EDIT the battery it audits, which is the whole
point (repairing a bad case is the deliverable) and also the hazard: an agent
that edits a cell and then reports SHIP has attested to its own repair. So the
driver's contract is narrow and worth pinning:

  * only a cell whose gate already records a pass is auditable -- otherwise an
    audit could "fix" a failing cell into passing and then vouch for it;
  * the status the driver records is the RE-RUN gate's, never the agent's;
  * a cell that was passing and is not passing afterwards is reported as a
    REGRESSION rather than folded into a clean summary.

No agents and no verifier here: these cover the record/read logic and the
payload extraction.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pbt_audit_fleet import (
    AUDIT_KEY,
    audited,
    is_complete,
    normalize,
    record_audit,
    reports_a_spec_hole,
    wanted,
)


# ---------------------------------------------------------------------------
# payload normalization
#
# `submit_result`'s schema is loose by design, so nothing forces the field names
# the prompt lists, and agents submit many shapes for the same fact. Reading only
# the documented names discards a real audit and reports the cell as
# `no-payload`, so each alias below is accepted.
# ---------------------------------------------------------------------------

def test_documented_names_pass_through():
    p = normalize({"verdict": "SHIP", "cases": [{"id": "c1"}],
                   "witnesses_rebuilt": 8})
    assert p["verdict"] == "SHIP" and p["witnesses_rebuilt"] == 8


def test_audit_verdict_alias_is_read():
    """An agent that submits `audit_verdict` has really audited the cell, so
    reading only `verdict` records an empty verdict and labels the row `audited`
    with detail `no-payload`."""
    assert normalize({"audit_verdict": "SHIP"})["verdict"] == "SHIP"


@pytest.mark.parametrize("key", ["edits_made", "battery_edited",
                                 "properties_py_edited", "repairs_made"])
def test_edited_aliases(key):
    assert normalize({"verdict": "REPAIRED", key: True})["edited"] is True


def test_a_prose_denial_of_editing_is_not_an_edit():
    """`edits_made` carries a DESCRIPTION of the edits as often as it carries a
    flag, and a description can be a denial, so an exact-match negative set does
    not catch it and the cell reads as edited when nothing was."""
    p = normalize({"verdict": "SHIP", "edits_made":
                   "none to properties.py or any frozen artifact; removed a "
                   "__pycache__/ directory a Python import created"})
    assert p["edited"] is False
    # ...and the description is kept, because it is the audit's own account
    assert "__pycache__" in p["edits_described"]


def test_a_prose_description_of_a_real_edit_still_counts():
    p = normalize({"verdict": "REPAIRED", "edits_made":
                   "added weak-absent-choice rival and retargeted 2 witnesses"})
    assert p["edited"] is True


def test_prose_negation_does_not_leak_into_the_evidence_fields():
    """Asymmetric on purpose. Misreading a denial as an edit is cosmetic;
    misreading a spec hole whose description opens with "no" as "nothing
    reported" would DISCARD a real finding, so leading-negation is honoured for
    the boolean only."""
    p = normalize({"verdict": "SPEC-DEFECT",
                   "spec_defect": "no clamp is applied, so it verifies at -1"})
    assert p["spec_holes"] == "no clamp is applied, so it verifies at -1"


@pytest.mark.parametrize("key", ["attacks", "attacks_run", "probes"])
def test_attack_aliases(key):
    assert normalize({"verdict": "SHIP", key: ["wrong-impl-1"]})[
        "attacks_tried"] == ["wrong-impl-1"]


@pytest.mark.parametrize("val", ["none", "None", "no spec defect", "n/a", "",
                                 [], ["none"], False, None])
def test_a_negative_spec_defect_is_not_a_finding(val):
    """Agents write `spec_defect: "none"` as prose, and a bare truthiness test
    reads that STRING as a reported spec hole -- escalating a clean cell as a
    frozen-spec defect."""
    assert normalize({"verdict": "SHIP", "spec_defect": val})["spec_holes"] == []


def test_a_real_spec_defect_survives():
    p = normalize({"verdict": "SPEC-DEFECT",
                   "spec_defect": "verifies at (true, none)"})
    assert p["spec_holes"] == "verifies at (true, none)"


def test_witness_exit_codes_become_a_count_and_are_kept():
    """Agents often send the exit codes themselves, which is strictly more
    evidence than a count. Keep both rather than dropping either."""
    p = normalize({"verdict": "SHIP",
                   "witness_exit_codes": [{"id": "r1", "rival": 0, "gold": 1},
                                          {"id": "r2", "rival": 0, "gold": 1}]})
    assert p["witnesses_rebuilt"] == 2
    assert len(p["witness_evidence"]) == 2


def test_unrecognized_keys_are_preserved():
    """An audit's report is the one thing a re-run gate cannot reproduce, so
    normalization must never be lossy."""
    p = normalize({"verdict": "SHIP", "leak_discipline": "clean",
                   "environment_checks": ["elan on PATH"]})
    assert p["leak_discipline"] == "clean" and p["environment_checks"]


def test_normalize_tolerates_junk():
    assert normalize(None) == {} and normalize("SHIP") == {} == normalize([])


def test_canonical_field_wins_over_an_alias():
    p = normalize({"verdict": "SHIP", "conclusion": "CORRUPT"})
    assert p["verdict"] == "SHIP"


def test_an_empty_canonical_falls_back_to_the_alias():
    """The shape that motivates checking emptiness rather than presence: an
    agent that emits both, leaving the documented one blank."""
    p = normalize({"verdict": "", "audit_verdict": "REPAIRED"})
    assert p["verdict"] == "REPAIRED"


# ---------------------------------------------------------------------------
# escalating a spec hole: the one row a human has to read
#
# `normalize` already erases the fixed negatives ("none", "n/a", []). What is
# left for this predicate is the case it cannot: a whole SENTENCE of denial,
# which is truthy and which the driver used to report as a frozen-spec defect.
# ---------------------------------------------------------------------------

def test_a_prose_denial_under_ship_is_not_escalated():
    """The cleanest possible audit: verdict SHIP, every attack passing, a
    re-gate of pass/SOUND, and `spec_holes` a sentence saying so. Escalating on
    the truthy sentence reports `spec-defect` for exactly that cell."""
    p = normalize({"verdict": "SHIP", "spec_holes":
                   "none — attacks D and E found no hole in the frozen spec."})
    assert p["spec_holes"]           # normalize cannot recognize the sentence
    assert reports_a_spec_hole(p) is False


@pytest.mark.parametrize("verdict", ["SPEC-DEFECT", "CORRUPT", "", "no-verdict",
                                     "NEEDS-REVIEW"])
def test_a_prose_denial_under_any_other_verdict_is_escalated(verdict):
    """The asymmetry is the point. A denial is trusted only where the VERDICT
    corroborates it, because SHIP/REPAIRED are the verdicts that cannot express a
    hole. Under anything else the two fields disagree, and a disagreement about
    the frozen spec is exactly what a human should look at."""
    assert reports_a_spec_hole(
        {"verdict": verdict,
         "spec_holes": "none that I could confirm, but see the note"}) is True


def test_a_real_hole_opening_with_no_is_still_escalated():
    """The finding this predicate must never discard: a genuine hole whose
    description happens to begin with a negation. Under SPEC-DEFECT it stands."""
    assert reports_a_spec_hole(
        {"verdict": "SPEC-DEFECT",
         "spec_holes": "no clamp is applied, so the spec verifies at -1"}) is True


def test_a_real_hole_under_ship_is_still_escalated():
    """A denial is recognized by its OPENING negation, not by the verdict alone:
    SHIP plus a hole description is a self-contradicting submission, and the hole
    wins."""
    assert reports_a_spec_hole(
        {"verdict": "SHIP",
         "spec_holes": "the postcondition admits (true, none)"}) is True


def test_a_list_of_holes_is_never_read_as_prose():
    """The documented shape. `_NEGATIVE_LEAD` is a string check, so a list can
    only ever escalate -- which is the safe direction."""
    assert reports_a_spec_hole(
        {"verdict": "SHIP", "spec_holes": ["admits (true, none)"]}) is True


@pytest.mark.parametrize("val", ["none", "n/a", "", [], ["none"], None, False])
def test_a_normalized_negative_is_not_a_finding(val):
    """The fixed negatives are `normalize`'s job; this pins that the predicate
    agrees with it rather than re-escalating what it cleared."""
    assert reports_a_spec_hole(
        normalize({"verdict": "SHIP", "spec_holes": val})) is False


def test_a_recorded_audit_reads_back_the_same_way(tmp_path):
    """The predicate has two callers with two shapes, and they must agree.

    `record_audit` stores the agent's claim as `agent_verdict`, to keep it
    visibly distinct from the gate's `gate_verdict_after`. So anything that
    re-reads a SHIPPED audit out of meta.json and asks "was a hole reported"
    hands over a dict with no `verdict` key at all -- which is neither SHIP nor
    REPAIRED, so the corroboration branch cannot fire and every prose denial
    reads back as a frozen-spec defect that the driver had recorded as clean.

    Same audit, same answer, whether it is read live or from the bundle."""
    payload = normalize({"verdict": "SHIP", "spec_holes":
                         "none — attacks D and E found no hole in the spec."})
    assert reports_a_spec_hole(payload) is False
    (tmp_path / "meta.json").write_text('{"gates": {}}')
    record_audit(tmp_path, payload, ("pass", "SOUND"), "t")
    rec = audited(tmp_path)
    assert rec is not None and "verdict" not in rec
    assert reports_a_spec_hole(rec) is False


def test_a_recorded_spec_defect_still_reads_as_one(tmp_path):
    """The direction that must not be broken by accepting the alias: a real
    finding recorded under SPEC-DEFECT stays a finding when re-read."""
    payload = normalize({"verdict": "SPEC-DEFECT",
                         "spec_holes": [{"input": "-1", "clause": "ensures"}]})
    (tmp_path / "meta.json").write_text('{"gates": {}}')
    record_audit(tmp_path, payload, ("pass", "SOUND"), "t")
    assert reports_a_spec_hole(audited(tmp_path)) is True


def _bundle(tmp_path: Path, meta: dict) -> Path:
    (tmp_path / "meta.json").write_text(json.dumps(meta))
    return tmp_path


# ---------------------------------------------------------------------------
# reading a prior audit (what --resume skips)
# ---------------------------------------------------------------------------

def test_unaudited_cell_reads_as_none(tmp_path):
    assert audited(_bundle(tmp_path, {"gates": {}})) is None


def test_missing_meta_reads_as_none(tmp_path):
    assert audited(tmp_path) is None


def test_audit_without_a_stamp_does_not_count(tmp_path):
    """Same rule the gates use: an entry with no timestamp is a placeholder,
    not a record, and --resume must not skip the cell on the strength of it."""
    assert audited(_bundle(tmp_path, {AUDIT_KEY: {"agent_verdict": "SHIP"}})) is None


def test_stamped_audit_is_found(tmp_path):
    b = _bundle(tmp_path, {AUDIT_KEY: {"audited_at": "w1", "agent_verdict": "SHIP"}})
    rec = audited(b)
    assert rec and rec["agent_verdict"] == "SHIP"


@pytest.mark.parametrize("verdict", ["", "   ", None])
def test_an_audit_with_no_verdict_does_not_count_as_done(tmp_path, verdict):
    """The record exists because the RE-GATE ran, and that status is worth
    keeping -- but it attests to nothing about which cases were examined, which is
    the only thing an audit contributes that a gate cannot re-derive.

    A run that loses its payload to an error inside the agent subprocess stamps
    cells with an empty `agent_verdict`; `--resume` then skips every one of them,
    so they would ship unaudited with an audit record attached."""
    b = _bundle(tmp_path, {AUDIT_KEY: {"audited_at": "a4",
                                       "agent_verdict": verdict,
                                       "cases": None, "spec_holes": []}})
    assert audited(b) is None


# ---------------------------------------------------------------------------
# recording: the gate's word overrides the agent's
# ---------------------------------------------------------------------------

def test_record_keeps_the_gate_status_alongside_the_claim(tmp_path):
    """The agent's verdict is retained as a CLAIM -- it carries the per-case
    reasoning nothing else has -- but the gate's status is recorded separately so
    a reader never has to take the claim as the outcome."""
    b = _bundle(tmp_path, {"instance_id": "x", "gates": {"G-PBT": {}}})
    record_audit(b, {"verdict": "SHIP", "edited": False, "witnesses_rebuilt": 8,
                     "cases": [{"id": "c1", "verdict": "earned"}]},
                 ("pass", "SOUND"), "w1")
    rec = json.loads((b / "meta.json").read_text())[AUDIT_KEY]
    assert rec["gate_status_after"] == "pass"
    assert rec["gate_verdict_after"] == "SOUND"
    assert rec["agent_verdict"] == "SHIP"
    assert rec["witnesses_rebuilt"] == 8


def test_record_preserves_the_rest_of_meta(tmp_path):
    """meta.json is the bundle's gate record; an audit appends to it and must
    not disturb what the gates stamped."""
    b = _bundle(tmp_path, {"instance_id": "x",
                           "gates": {"G-PBT": {"status": "pass"}}})
    record_audit(b, {"verdict": "SHIP"}, ("pass", "SOUND"), "w1")
    meta = json.loads((b / "meta.json").read_text())
    assert meta["instance_id"] == "x"
    assert meta["gates"]["G-PBT"]["status"] == "pass"


def test_record_captures_a_disagreement(tmp_path):
    """The case that motivates keeping both: the agent says SHIP, the re-run
    gate says fail. Recording only the agent's word would publish the SHIP."""
    b = _bundle(tmp_path, {"gates": {}})
    record_audit(b, {"verdict": "SHIP", "edited": True},
                 ("fail", "MALFORMED-TESTS"), "w1")
    rec = json.loads((b / "meta.json").read_text())[AUDIT_KEY]
    assert rec["agent_verdict"] == "SHIP"
    assert rec["gate_status_after"] == "fail"
    assert rec["edited"] is True


def test_record_survives_an_empty_payload(tmp_path):
    """A crashed agent submits nothing. The re-gate still happened and its
    result is still worth recording, so this must not raise."""
    b = _bundle(tmp_path, {"gates": {}})
    record_audit(b, {}, ("pass", "SOUND"), "w1")
    rec = json.loads((b / "meta.json").read_text())[AUDIT_KEY]
    assert rec["agent_verdict"] == "" and rec["gate_status_after"] == "pass"


def test_record_on_unreadable_meta_is_a_noop(tmp_path):
    (tmp_path / "meta.json").write_text("{not json")
    record_audit(tmp_path, {"verdict": "SHIP"}, ("pass", "SOUND"), "w1")
    assert (tmp_path / "meta.json").read_text() == "{not json"


def test_notes_are_truncated(tmp_path):
    """An audit narrating 200 KB of build output into meta.json would bloat
    every released bundle."""
    b = _bundle(tmp_path, {"gates": {}})
    record_audit(b, {"verdict": "SHIP", "notes": "x" * 20000},
                 ("pass", "SOUND"), "w1")
    assert len(json.loads((b / "meta.json").read_text())[AUDIT_KEY]["notes"]) == 4000


# ---------------------------------------------------------------------------
# re-auditing a cell must not cost the first audit
# ---------------------------------------------------------------------------

def _full(**over) -> dict:
    """A payload carrying all three pieces of evidence `is_complete` asks for."""
    return normalize({"verdict": "SHIP",
                      "cases": [{"id": "r1", "verdict": "earned"}],
                      "witnesses_rebuilt": [{"id": "r1", "rival_exit": 0,
                                             "gold_exit": 1}],
                      "attacks_tried": [{"id": "D-1", "kind": "wrong-impl",
                                         "outcome": "does not verify"}],
                      **over})


def test_a_second_audit_keeps_the_first_under_history(tmp_path):
    """A re-audit runs under a sharpened prompt, so it is the stronger check --
    but the earlier record is independent evidence from a different agent, and
    overwriting it would trade two audits for one."""
    b = _bundle(tmp_path, {"gates": {}})
    record_audit(b, normalize({"verdict": "SHIP", "notes": "first"}),
                 ("pass", "SOUND"), "a1")
    record_audit(b, _full(notes="second"), ("pass", "SOUND"), "a6")
    rec = json.loads((b / "meta.json").read_text())[AUDIT_KEY]
    assert rec["audited_at"] == "a6" and rec["notes"] == "second"
    assert [h["audited_at"] for h in rec["history"]] == ["a1"]
    assert rec["history"][0]["notes"] == "first"


def test_history_stays_one_level_deep(tmp_path):
    """Nesting each record inside the next would make the oldest audit
    arbitrarily deep and unreadable."""
    b = _bundle(tmp_path, {"gates": {}})
    for stamp in ("a1", "a3", "a5", "a6"):
        record_audit(b, normalize({"verdict": "SHIP", "notes": stamp}),
                     ("pass", "SOUND"), stamp)
    rec = json.loads((b / "meta.json").read_text())[AUDIT_KEY]
    assert [h["audited_at"] for h in rec["history"]] == ["a1", "a3", "a5"]
    assert all("history" not in h for h in rec["history"])


def test_a_first_audit_records_no_history_key(tmp_path):
    """So a single-audit bundle reads exactly as it did before."""
    b = _bundle(tmp_path, {"gates": {}})
    record_audit(b, normalize({"verdict": "SHIP"}), ("pass", "SOUND"), "a1")
    assert "history" not in json.loads((b / "meta.json").read_text())[AUDIT_KEY]


def test_a_placeholder_record_is_replaced_not_archived(tmp_path):
    """A record with no stamp is a placeholder, not an audit; keeping it would
    put an empty entry in the evidence list."""
    b = _bundle(tmp_path, {AUDIT_KEY: {"agent_verdict": "SHIP"}, "gates": {}})
    record_audit(b, normalize({"verdict": "SHIP"}), ("pass", "SOUND"), "a6")
    assert "history" not in json.loads((b / "meta.json").read_text())[AUDIT_KEY]


# ---------------------------------------------------------------------------
# is_complete: which records --resume-incomplete re-runs
# ---------------------------------------------------------------------------

def test_a_full_record_is_complete(tmp_path):
    b = _bundle(tmp_path, {"gates": {}})
    record_audit(b, _full(), ("pass", "SOUND"), "a5")
    assert is_complete(audited(b)) is True


@pytest.mark.parametrize("missing", ["cases", "witnesses_rebuilt",
                                     "attacks_tried"])
def test_a_record_missing_any_of_the_three_is_incomplete(tmp_path, missing):
    """None of the three is recoverable from the artifact afterwards: which cases
    were examined, the witness exit codes, and the rivals the attacks built."""
    b = _bundle(tmp_path, {"gates": {}})
    record_audit(b, _full(**{missing: None}), ("pass", "SOUND"), "a5")
    assert is_complete(audited(b)) is False


def test_attacks_recorded_as_a_dict_still_count(tmp_path):
    """Attacks are sometimes recorded as a dict keyed by attack letter rather
    than as a list of dicts. Both are real evidence, so the shape is not the test
    -- reading only the list shape scores a real audit as having run none."""
    b = _bundle(tmp_path, {"gates": {}})
    record_audit(b, _full(attacks_tried={
        "A_statement_integrity": "PASS — byte-identical in all 8 cases",
        "D_wrong_impl_probe": "2 novel wrong impls, neither verifies"}),
        ("pass", "SOUND"), "a1")
    assert is_complete(audited(b)) is True


def test_a_prose_denial_does_not_count_as_evidence(tmp_path):
    """`_is_empty` reads "none" as nothing, so an agent writing "none" into the
    evidence fields does not mark the audit complete."""
    b = _bundle(tmp_path, {"gates": {}})
    record_audit(b, _full(cases="none", witnesses_rebuilt="n/a"),
                 ("pass", "SOUND"), "a1")
    assert is_complete(audited(b)) is False


# ---------------------------------------------------------------------------
# `wanted`: the skip predicate, applied at launch AND under the lock
#
# The resume filter has to be re-checked under the lock, not only at launch:
# otherwise a second audit driver re-audits whatever the first finished after the
# id list was built. The flock serializes the two in time, it does not stop them
# doing the same cell one after the other -- and a redundant audit is a full
# agent plus a re-gate, on a cell that gains nothing from it.
# ---------------------------------------------------------------------------

def test_an_unaudited_cell_is_always_wanted(tmp_path):
    b = _bundle(tmp_path, {"gates": {}})
    assert wanted(b, resume=True, resume_incomplete=False) is None
    assert wanted(b, resume=False, resume_incomplete=True) is None


def test_a_complete_record_is_not_wanted_under_either_flag(tmp_path):
    b = _bundle(tmp_path, {"gates": {}})
    record_audit(b, _full(), ("pass", "SOUND"), "a5")
    assert wanted(b, resume=True, resume_incomplete=False)["audited_at"] == "a5"
    assert wanted(b, resume=False, resume_incomplete=True)["audited_at"] == "a5"


def test_an_incomplete_record_is_wanted_only_by_resume_incomplete(tmp_path):
    """The whole point of the flag: a record that predates the payload spec is a
    recorded audit that attests to nothing re-derivable."""
    b = _bundle(tmp_path, {"gates": {}})
    record_audit(b, _full(cases=None), ("pass", "SOUND"), "a1")
    assert wanted(b, resume=True, resume_incomplete=False)["audited_at"] == "a1"
    assert wanted(b, resume=False, resume_incomplete=True) is None


def test_a_full_wave_wants_every_cell(tmp_path):
    """With neither flag the wave re-audits unconditionally, however complete
    the existing record is."""
    b = _bundle(tmp_path, {"gates": {}})
    record_audit(b, _full(), ("pass", "SOUND"), "a5")
    assert wanted(b, resume=False, resume_incomplete=False) is None
