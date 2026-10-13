# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""audit_note: the account a passing mechanized role publishes about itself.

Every clause the composer writes is a restatement of a per-attack label the
runner recorded. These tests pin that -- and, more importantly, pin where it
DECLINES, since a note that describes evidence the record does not contain is a
false claim about a specification, whereas a declined one is merely the counter
the derivation already wrote.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from swebench_unified.construct import audit_note as an

ROOT = Path(__file__).resolve().parents[1]

REJECTED = "rejected (same spec, does not verify — good)"
ECHO = "correct echo (verifies AND its patch resolves — not a weakness)"
OFF_SPEC = "not a counterexample (changed the spec region)"
TIMED_OUT = "inconclusive (verifier timed out)"
HOLDS = "holds on the patched tree (good)"

NOTE = ("eq: 6 admissible attacks re-run of 6 submitted, none breaks the spec; "
        "positive control verifies")
PROBE_NOTE = ("eq: 4 requirement probes hold on the patched tree; 3/3 "
              "weak-candidate(s) rejected by the probe suite; positive control "
              "discriminates base vs patched.")


def atks(*labels: str, stem: str = "atk") -> list[dict]:
    return [{"name": f"{stem}_{i}.lean", "result": lab}
            for i, lab in enumerate(labels, 1)]


# ---------------------------------------------------------------------------
# the label is the graded outcome; the gloss and the detail are not
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("recorded,label", [
    (REJECTED, "rejected"),
    (ECHO + " [resolved on attempt 2]", "correct echo"),
    ("rejected", "rejected"),
    ("  rejected (x)  ", "rejected"),
])
def test_the_outcome_reduces_to_its_vocabulary_word(recorded, label):
    assert an.outcome_label(recorded) == label


def test_a_gloss_that_opens_with_a_bracket_is_not_a_label():
    """Cutting at the first ` [` as well as the first ` (`: the runner appends a
    test-result detail to an echo, and that detail is about this run."""
    assert an.outcome_label("correct echo [resolved on attempt 3]") == "correct echo"


# ---------------------------------------------------------------------------
# the graded path: candidate wrong implementations, judged by a verifier
# ---------------------------------------------------------------------------

def test_the_composed_note_keeps_the_recorded_sentence_and_adds_a_table():
    body, why = an.compose(NOTE, atks(*[REJECTED] * 5, ECHO),
                           control="atk_0_control.lean", prepatch=True)
    assert body, why
    assert body.startswith(NOTE)
    assert an.TABLE_MARKER in body
    # one row per distinct outcome, most frequent first, with its count
    assert "| 5 |" in body and "| 1 |" in body
    assert "`atk_6.lean`" in body


def test_every_row_is_an_outcome_the_record_carries():
    body, why = an.compose(NOTE, atks(REJECTED, OFF_SPEC), control="c.lean")
    assert body, why
    rows = [ln for ln in body.split("\n") if ln.startswith("| ") and "---" not in ln]
    assert len(rows) == 3, rows  # header + two outcomes
    assert "changed the specification rather than only the implementation" in body


def test_an_outcome_outside_the_whitelist_is_declined_not_smoothed_over():
    """`inconclusive` names a grading that did not happen. Meeting one on a role
    recorded as passing is the record's evidence contradicting its status, so it
    is reported rather than described."""
    body, why = an.compose(NOTE, atks(REJECTED, TIMED_OUT), control="c.lean")
    assert body is None
    assert "not in the whitelist" in why and "inconclusive" in why


def test_the_control_sentence_is_written_only_when_a_control_is_recorded():
    with_ctl, _ = an.compose(NOTE, atks(*[REJECTED] * 5), control="ctl.lean")
    without, _ = an.compose(NOTE, atks(*[REJECTED] * 5), control="")
    assert with_ctl and "positive control `ctl.lean` verifies" in with_ctl
    # the recorded sentence names one; the composed account does not invent one
    assert without and "**Non-vacuity.**" not in without


@pytest.mark.parametrize("flag,expected", [
    (True, "re-encoded as one of the attacks above"),
    (False, "not among the attacks above"),
])
def test_the_prepatch_clause_says_what_the_flag_says(flag, expected):
    body, why = an.compose(NOTE, atks(*[REJECTED] * 5), control="c.lean",
                           prepatch=flag)
    assert body, why
    assert expected in body


def test_an_unrecorded_prepatch_flag_asserts_no_default():
    body, why = an.compose(NOTE, atks(*[REJECTED] * 5), control="c.lean",
                           prepatch=None)
    assert body, why
    assert "prepatch" not in body.lower() and "bug this instance fixes" not in body


def test_the_summary_does_not_claim_every_attack_kept_the_spec():
    """The `not a counterexample` outcome exists precisely because some do not,
    so a summary asserting otherwise would be contradicted by its own table."""
    body, _ = an.compose(NOTE, atks(REJECTED, OFF_SPEC), control="c.lean")
    assert body and "candidate wrong implementation" in body
    assert "same spec" not in body


# ---------------------------------------------------------------------------
# the name column: informative, bounded, and never rewritten
# ---------------------------------------------------------------------------

def test_a_long_name_list_is_cut_and_counted():
    many = atks(*[REJECTED] * 30, stem="atk_with_a_fairly_long_descriptive_name")
    body, why = an.compose(NOTE, many, control="c.lean")
    assert body, why
    assert re.search(r"\+\d+ more", body)


def test_a_name_carrying_router_vocabulary_moves_the_column_not_the_name():
    """A filename is not something this may rewrite, and the note may not carry
    the vocabulary the defect router keys on. So the column says where the names
    are; verdict.md is rendered by the card immediately below."""
    named = atks(*[REJECTED] * 5)
    named[2]["name"] = "atk13_weak_stub.lean"
    body, why = an.compose(NOTE, named, control="c.lean")
    assert body, why
    assert not an.FORBIDDEN.search(body)
    assert "listed per attack in the audit record below" in body
    assert "atk13_weak_stub" not in body


# ---------------------------------------------------------------------------
# the probe path: no verifier, so holding is the good outcome
# ---------------------------------------------------------------------------

def test_the_probe_account_restates_the_suite_and_the_candidate_search():
    body, why = an.compose(PROBE_NOTE, atks(*[HOLDS] * 4, stem="probe"),
                           control="probe_1.lean", prepatch=True)
    assert body, why
    assert an.PROBE_TABLE_MARKER in body
    assert "no verifier" in body and "gold-patched tree" in body
    assert "The suite rejected all 3" in body
    assert "separates the two trees" in body


def test_the_probe_counts_are_parsed_from_the_sentence_never_recomputed():
    """K and M are the whole record of the candidate-patch search: the ledger
    carries the probes and never the candidates, so a sentence that is not this
    shape is declined rather than described."""
    body, why = an.compose("eq: probes were fine", atks(HOLDS, stem="probe"))
    assert body is None and "not the probe-suite shape" in why


def test_a_sentence_that_disagrees_with_the_ledger_is_declined():
    body, why = an.compose(PROBE_NOTE, atks(*[HOLDS] * 3, stem="probe"))
    assert body is None
    assert "sentence records 4 probes" in why


def test_a_candidate_search_that_rejected_nothing_is_not_a_passing_shape():
    """Probes that merely hold prove conformance, not discriminating power."""
    note = PROBE_NOTE.replace("3/3", "0/3")
    body, why = an.compose(note, atks(*[HOLDS] * 4, stem="probe"))
    assert body is None and "not a passing shape" in why


def test_a_partial_rejection_says_only_what_the_record_says():
    note = PROBE_NOTE.replace("3/3", "2/3")
    body, why = an.compose(note, atks(*[HOLDS] * 4, stem="probe"))
    assert body, why
    assert "The suite rejected 2 of the 3" in body
    assert "The other 1 was not rejected by the suite." in body


def test_the_probe_control_is_not_described_as_a_satisfiability_witness():
    body, _ = an.compose(PROBE_NOTE, atks(*[HOLDS] * 4, stem="probe"),
                         control="probe_2.lean")
    assert body and "satisfiable" not in body
    assert "It is one of the probes above, counted in the table there." in body


def test_the_composed_probe_note_never_adds_the_router_vocabulary():
    """The recorded sentence itself carries `weak-candidate`, which is
    `build_one`'s to change; the ban applies in full to what is composed here."""
    body, why = an.compose(PROBE_NOTE, atks(*[HOLDS] * 4, stem="probe"),
                           control="probe_1.lean")
    assert body, why
    added = body[len(PROBE_NOTE.strip()):]
    assert not an.FORBIDDEN.search(added)


# ---------------------------------------------------------------------------
# the dispatch, the guards, idempotence
# ---------------------------------------------------------------------------

def test_the_vocabulary_and_not_the_backend_name_chooses_the_account():
    graded, _ = an.compose(NOTE, atks(*[REJECTED] * 5), control="c.lean")
    probes, _ = an.compose(PROBE_NOTE, atks(*[HOLDS] * 4, stem="probe"))
    assert graded and an.TABLE_MARKER in graded
    assert probes and an.PROBE_TABLE_MARKER in probes


def test_a_mixed_vocabulary_is_not_composed_by_halves():
    """One role has one arbiter, so a record drawing on both falls to the
    wrong-impl path, which reports the probe labels as outside its whitelist."""
    body, why = an.compose(NOTE, atks(REJECTED, HOLDS), control="c.lean")
    assert body is None and "not in the whitelist" in why
    assert "holds on the patched tree" in why


def test_a_record_with_no_outcomes_is_declined():
    body, why = an.compose(NOTE, [], control="c.lean")
    assert body is None and "no per-attack outcomes" in why


def test_a_note_that_opens_with_inconclusive_is_never_composed():
    body, why = an.compose("eq: INCONCLUSIVE — only 2 admissible attacks",
                           atks(*[REJECTED] * 5), control="c.lean")
    assert body is None and "INCONCLUSIVE" in why


def test_the_composition_is_idempotent():
    once, why = an.compose(NOTE, atks(*[REJECTED] * 5), control="c.lean")
    assert once, why
    twice, why2 = an.compose(once, atks(*[REJECTED] * 5), control="c.lean")
    assert twice is None and why2 == "already composed"
    assert an.already_composed(once)


def test_a_composition_outside_the_band_is_declined():
    """Over the ceiling is the failure at the other end from a bare counter, and
    one card renders all of these. The name column is budgeted, so what can still
    run long is the part that is quoted whole: a recorded filename."""
    lo, hi = an.BODY_BAND
    body, _ = an.compose(NOTE, atks(*[REJECTED] * 5), control="c.lean")
    assert body and lo <= len(body) <= hi
    many = atks(*[REJECTED] * 200, stem="a" * 60)
    still_in_band, why = an.compose(NOTE, many, control="c.lean")
    assert still_in_band, why
    over, why = an.compose(NOTE, atks(*[REJECTED] * 5), control="c" * 2600)
    assert over is None and "outside" in why


def test_the_first_line_is_preserved_byte_for_byte():
    """The defect router reads this field, so what it sees must not change."""
    for note, attacks in ((NOTE, atks(*[REJECTED] * 5)),
                          (PROBE_NOTE, atks(*[HOLDS] * 4, stem="probe"))):
        body, why = an.compose(note, attacks, control="c.lean")
        assert body, why
        assert body.partition("\n")[0] == note.strip().partition("\n")[0]


# ---------------------------------------------------------------------------
# the recorded corpus: the composer reproduces what it published
# ---------------------------------------------------------------------------

BENCH = ROOT / "benchmark-verified"
_ROLE_RE = re.compile(r"^## Role \d+ — (G-[A-Z0-9-]+) ")
_CTRL_RE = re.compile(r"^\*\*Positive control\*\*[^`]*`([^`]+)`")


def _controls(md: str) -> dict[str, str]:
    """Each role's control filename, read off the caption rather than the fence.

    A control byte-identical to the cell's spec file is rendered with a caption
    and no fenced body -- which is the evidence it is the unmodified correct
    implementation -- so a fence-based reader misses exactly those.
    """
    out: dict[str, str] = {}
    gate = None
    for line in md.split("\n"):
        m = _ROLE_RE.match(line)
        if m:
            gate = m.group(1)
            continue
        m = _CTRL_RE.match(line)
        if m and gate and gate not in out:
            out[gate] = m.group(1)
    return out


@pytest.mark.skipif(not BENCH.is_dir(), reason="corpus not present")
def test_the_composer_reproduces_the_notes_it_published():
    """Byte-for-byte, over a deterministic sample of the published records.

    The strongest available check that this module is the composer the shipped
    corpus was written by: the inputs are read back out of verdict.md and the
    output is compared against the note in meta.json.
    """
    from audit_recheck import parse_verdict

    cells = sorted(BENCH.glob("*/*/meta.json"))[::40]
    checked = 0
    for meta_p in cells:
        meta = json.loads(meta_p.read_text())
        vp = meta_p.parent / "verdict.md"
        if not vp.exists():
            continue
        md = vp.read_text(errors="replace")
        parsed, ctrls = parse_verdict(md), _controls(md)
        for gate in ("G-EQ", "G-PANEL-1"):
            entry = (meta.get("gates") or {}).get(gate)
            if not isinstance(entry, dict):
                continue
            note = str(entry.get("note") or "")
            sec = parsed.get(gate)
            if not an.already_composed(note) or not sec:
                continue
            attacks = [{"name": n, "result": o or ""} for n, _s, o in sec["attacks"]]
            body, why = an.compose(note.partition("\n")[0], attacks,
                                   control=ctrls.get(gate, ""),
                                   prepatch=sec.get("prepatch_reproduced"))
            assert body, f"{meta_p.parent}/{gate}: declined: {why}"
            assert body.strip() == note.strip(), f"{meta_p.parent}/{gate}"
            checked += 1
    assert checked > 20, f"only {checked} composed notes in the sample"
