# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""judgment_note: the frame a role publishes when nothing was graded for it.

Two shapes, one discipline. A role judged rather than run (G-PANEL-2, G-PANEL-3)
gets the recorded verdict token, its sibling gates' recorded statuses and a
`stat` for each file it cites; a mechanized role whose round wrote no outcome
table gets its own machine sentence's count and a paragraph naming the gap. These
tests pin both -- and, more importantly, pin every DECLINE, because a sentence
this module invents is a false claim about a specification on a release surface,
whereas a declined note is merely the record as the harness already wrote it.

Nothing here may be read out of a reviewer's argument, so the essays in the
fixtures below carry counts and findings that the composed text must not repeat.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from swebench_unified.construct import audit_note as an
from swebench_unified.construct import judgment_note as jn

ROOT = Path(__file__).resolve().parents[1]

# A reviewer's essay of the shape this module must never read: it states a count,
# a finding and an absence, none of which may reach the composed text.
ESSAY = ("panel_2: Checked the abstract model against the reference on 4 "
         "families of inputs. No divergence was found, and the postcondition is "
         "not strengthened past the function it stands in for; see model.py and "
         "refinement.md for the mapping I read.")
LEAK_ESSAY = ("panel_3: The spec view names the same invariant the public "
              "problem statement does. Nothing in mapping.md discloses the "
              "reference edit.")
# The harness's own sentence for a mechanized role whose round wrote no table.
COUNTER = ("eq: 7 attacks re-run, none breaks the spec; positive control "
           "verifies")
OF_SUBMITTED = ("eq: 9 admissible attacks re-run of 12 submitted, none breaks "
                "the spec; positive control verifies")
PROBE_COUNTER = ("eq: 4 requirement probes hold on the patched tree; 3/3 "
                 "weak-candidate(s) rejected by the probe suite; positive "
                 "control discriminates base vs patched.")
# The disclosure a class-A record writes about itself, and a heading that
# identifies the pre-composer round. Both are properties of the audit record.
ABSENT_RECORD = ("## Role 1 — G-EQ: pass\n\n"
                 "_The attack bodies behind this role's verdict were not "
                 "retained._\n")
LEGACY_RECORD = "## Per-gate verdicts\n\n| gate | verdict |\n| --- | --- |\n"

SHIPPED = ("model.py", "properties.py", "mapping.md", "refinement.md",
           "meta.json", "verdict.md")


def gates(**status: str) -> dict[str, dict]:
    return {gk: {"status": st} for gk, st in status.items()}


def p2(note: str = ESSAY, verdict: str = "FAITHFUL", **kw):
    kw.setdefault("gates", gates(**{"G-CONF": "pass", "G-AX": "pass"}))
    kw.setdefault("shipped", SHIPPED)
    return jn.compose("G-PANEL-2", note, agent_verdict=verdict, **kw)


def p3(note: str = LEAK_ESSAY, verdict: str = "NO-LEAKAGE", **kw):
    kw.setdefault("gates", gates(**{"G-LEAK": "pass"}))
    kw.setdefault("shipped", SHIPPED)
    return jn.compose("G-PANEL-3", note, agent_verdict=verdict, **kw)


# ---------------------------------------------------------------------------
# the judgment frame: the record, and never the argument
# ---------------------------------------------------------------------------

def test_the_composed_note_keeps_the_account_and_adds_the_frame():
    body, why = p2()
    assert body, why
    assert body.startswith(ESSAY)
    assert jn.JUDGMENT_LEAD in body and jn.UNGRADED_MARKER in body


def test_the_frame_says_which_question_this_role_asks_and_not_the_other_one():
    """Four roles publish notes of the same shape on one card. The question is
    what tells them apart, and each role's is its own."""
    faith, _ = p2()
    leak, _ = p3()
    assert faith and "diverges from that function" in faith
    assert leak and "reconstruct the fix" in leak
    assert "reconstruct the fix" not in faith
    assert "diverges from that function" not in leak


def test_nothing_is_read_out_of_the_reviewers_argument():
    """No count, no finding, no "no divergence was found": a sentence like that
    is prose republished as a measurement, and being wrong about one in the
    reassuring direction is the failure mode of a release surface."""
    body, why = p2()
    assert body, why
    added = body[len(ESSAY):]
    assert "divergence" not in added and "4 families" not in added
    assert not re.search(r"\b\d+ (?:famil|input|check)", added)


def test_the_recorded_verdict_token_is_quoted_and_nothing_is_derived_from_it():
    body, why = p2(verdict="faithful")
    assert body, why
    assert "The reviewer recorded FAITHFUL." in body
    assert "judgment and not a machine re-run" in body


@pytest.mark.parametrize("verdict", ["FAITHFUL", "PASS", "SOUND"])
def test_each_word_of_the_roles_own_vocabulary_is_accepted(verdict):
    body, why = p2(verdict=verdict)
    assert body, why
    assert f"The reviewer recorded {verdict}." in body


@pytest.mark.parametrize("verdict", ["NO-LEAKAGE", "TIGHT", "OK", "", "  "])
def test_a_verdict_outside_this_roles_vocabulary_is_declined(verdict):
    """A disagreement between what the reviewer said and what the cell records is
    a finding about the cell, not a layout to smooth over. `NO-LEAKAGE` is the
    other judgment role's word and is declined here for the same reason."""
    body, why = p2(verdict=verdict)
    assert body is None
    assert "not in this role's vocabulary" in why and verdict.strip() in why


def test_an_empty_recorded_note_has_nothing_to_frame():
    body, why = p2(note="   ")
    assert body is None and why == "no recorded note to compose from"


# ---------------------------------------------------------------------------
# the accepted-relaxation record: a pass whose ground is a disclosure
# ---------------------------------------------------------------------------

def test_an_accepted_relaxation_is_composed_as_the_disposition_it_is():
    """`LEAKAGE` + `pass` is a valid record and its meaning is the opposite of
    the ordinary one. Composing it as "no leakage found" would publish the status
    over the evidence."""
    body, why = p3(verdict="LEAKAGE",
                   gates=gates(**{"G-LEAK": "relaxed"}))
    assert body, why
    assert "The reviewer recorded LEAKAGE." in body
    assert "had already been accepted by a reviewer" in body
    assert "`relaxed` is not a status it may take" in body
    assert "judgment and not a machine re-run" not in body


def test_a_relaxation_the_record_does_not_carry_is_declined():
    """A pass whose only stated ground is a leak nothing accepted; writing the
    sentence anyway would manufacture the acceptance it rests on."""
    body, why = p3(verdict="LEAKAGE", gates=gates(**{"G-LEAK": "pass"}))
    assert body is None and "not `relaxed`" in why and "'pass'" in why
    body, why = p3(verdict="LEAKAGE", gates={})
    assert body is None and "unrecorded" in why


def test_the_relaxation_word_is_not_a_verdict_the_other_role_may_take():
    body, why = p2(verdict="LEAKAGE", gates=gates(**{"G-LEAK": "relaxed"}))
    assert body is None and "not in this role's vocabulary" in why


def test_an_ordinary_leakage_pass_next_to_a_relaxation_says_so():
    """The two are not in conflict, and a reader of `NO-LEAKAGE` next to a
    `relaxed` gate should not have to guess which one the pass rests on."""
    body, why = p3(gates=gates(**{"G-LEAK": "relaxed"}))
    assert body, why
    assert "separately records G-LEAK as `relaxed`" in body
    plain, _ = p3()
    assert plain and "separately records" not in plain


# ---------------------------------------------------------------------------
# the sibling gates: re-runnable evidence next to a verdict that is not
# ---------------------------------------------------------------------------

def test_the_sibling_gates_are_quoted_with_the_status_the_cell_records():
    body, why = p2(gates=gates(**{"G-CONF": "pass", "G-AX": "fail",
                                  "G-LEAK": "relaxed"}))
    assert body, why
    assert "The mechanical checks over the same artifact are" in body
    assert "G-CONF `pass` (the conformance battery" in body
    assert "G-AX `fail` (the axiom battery)" in body
    # only the gates over the artifact THIS role judges: G-LEAK is recorded on the
    # cell and is the other role's sibling, so naming it here would be this role
    # reporting a measurement it did not stand next to
    assert "G-LEAK" not in body and "relaxed" not in body


def test_a_skipped_sibling_reached_no_verdict_and_is_not_described():
    """G-AX is a skip on many cells, and a sentence explaining why one is absent
    would be about the pipeline, so the clause claims only what the cell records
    and never completeness."""
    body, why = p2(gates=gates(**{"G-CONF": "pass", "G-AX": "skip"}))
    assert body, why
    assert "The mechanical check over the same artifact is" in body
    assert "G-AX" not in body


def test_a_cell_recording_no_sibling_verdict_gets_no_sibling_sentence():
    body, why = p2(gates=gates(**{"G-CONF": "skip", "G-AX": "skip"}))
    assert body, why
    assert "mechanical check" not in body and "G-CONF" not in body
    assert jn.UNGRADED_MARKER in body


def test_only_the_status_token_is_read_out_of_a_sibling_entry():
    recorded = jn.recorded_statuses({
        "G-CONF": {"status": " pass ", "note": "13/13 properties hold"},
        "G-AX": {"status": None}, "G-LEAK": "pass", "G-EQ": {"status": "pass"}})
    assert recorded == {"G-CONF": "pass"}


# ---------------------------------------------------------------------------
# the cited files: a `stat`, never a citation restated
# ---------------------------------------------------------------------------

def test_only_a_file_the_bundle_ships_is_named():
    """A note may cite `RELAXED_LEAKAGE.md` without the bundle shipping it, and
    restating that citation in composed prose would entrench a dangling one under
    a fresh heading."""
    note = LEAK_ESSAY + " See RELAXED_LEAKAGE.md and mapping.md."
    body, why = p3(note=note)
    assert body, why
    assert "`mapping.md`" in body
    assert "RELAXED_LEAKAGE.md`," not in body[len(note):]


def test_a_shipped_file_the_account_never_names_is_not_named_either():
    """The list is what the ACCOUNT cites, of what the bundle ships -- not an
    inventory of the bundle."""
    body, why = p2(note="panel_2: the model matches. See mapping.md.")
    assert body, why
    assert "The account names `mapping.md`, which ships in this bundle" in body
    assert "`model.py`" not in body and "`properties.py`" not in body


def test_the_cited_list_is_a_starting_point_and_not_an_inventory():
    note = ("panel_2: read model.py, properties.py, conformance_check.py, "
            "axiom_check.py, mapping.md and refinement.md.")
    shipped = SHIPPED + ("conformance_check.py", "axiom_check.py")
    body, why = p2(note=note, shipped=shipped)
    assert body, why
    named = re.search(r"The account names (.*?), all of which ship", body)
    assert named and len(named.group(1).split(", ")) == jn.CITED_BUDGET


def test_the_cited_list_is_in_the_modules_order_and_not_the_essays():
    note = "panel_2: refinement.md, then mapping.md, then model.py."
    body, why = p2(note=note)
    assert body, why
    assert "`model.py`, `mapping.md`, `refinement.md`" in body


def test_a_name_the_role_may_not_print_is_dropped_not_declined_over():
    """`RELAXED_LEAKAGE.md` contains the substring G-PANEL-2's ban keys on, and 2
    cells ship it and cite it from a faithfulness account. Losing one entry from
    a "start here" list costs a reader nothing re-checkable; declining would have
    cost those cells the whole block."""
    note = ESSAY + " The disclosure is argued in RELAXED_LEAKAGE.md."
    shipped = SHIPPED + ("RELAXED_LEAKAGE.md",)
    body, why = p2(note=note, shipped=shipped)
    assert body, why
    assert not jn.JUDGMENT_TAIL_BAN["G-PANEL-2"].search(body[len(note):])
    assert "`model.py`, `refinement.md`" in body
    # the leakage role prints it, because its own vocabulary is not banned there
    leak, why = p3(note=LEAK_ESSAY + " See RELAXED_LEAKAGE.md.", shipped=shipped)
    assert leak, why
    assert "`RELAXED_LEAKAGE.md`" in leak


def test_a_citation_is_a_stat_over_the_shipped_names():
    assert jn.cited_files("read model.py and RELAXED_LEAKAGE.md", SHIPPED) \
        == ["model.py"]
    assert jn.cited_files("no names here", SHIPPED) == []


# ---------------------------------------------------------------------------
# the judgment guards
# ---------------------------------------------------------------------------

def test_the_added_text_never_carries_the_routers_repair_vocabulary():
    """This is the field the repair router reads back, and the word that must
    never reach it from here is the one that sends a green cell back for an
    expensive spec repair."""
    for body, why in (p2(), p3(), p3(verdict="LEAKAGE",
                                    gates=gates(**{"G-LEAK": "relaxed"}))):
        assert body, why
        added = body.split(jn.JUDGMENT_LEAD, 1)[1]
        assert not re.search(r"BROKEN|WEAK|UNFAITHFUL", added, re.I)


def test_the_tail_ban_declines_rather_than_publishing_a_word_it_catches(monkeypatch):
    """Unreachable for the text this writes, and checked anyway because this is the
    field the repair router reads back. Pinned by widening the ban, since no input can
    steer the composer's own vocabulary into it."""
    monkeypatch.setitem(jn.JUDGMENT_TAIL_BAN, "G-PANEL-2",
                        re.compile(r"specification", re.IGNORECASE))
    body, why = p2()
    assert body is None and why == "composed text carries router vocabulary"


def test_a_note_that_opens_with_inconclusive_is_never_framed_as_a_verdict():
    body, why = p2(note="panel_2: INCONCLUSIVE — the reviewer did not submit")
    assert body is None and "INCONCLUSIVE" in why


def test_a_tail_outside_the_band_is_declined(monkeypatch):
    """The band bounds the ADDED text and not the note: the account it follows is
    a reviewer's essay of unbounded length, so a bound on the total would decline
    exactly the longest records."""
    long_note = ESSAY + " " + "x" * 12000
    body, why = p2(note=long_note)
    assert body, why
    monkeypatch.setattr(jn, "JUDGMENT_TAIL_BAND", (400, 500))
    body, why = p2()
    assert body is None and "outside 400..500" in why


def test_the_judgment_composition_is_idempotent():
    once, why = p2()
    assert once, why
    twice, why2 = p2(note=once)
    assert twice is None and why2 == "already composed"
    assert jn.already_composed(once)


def test_a_note_already_carrying_the_other_composers_table_is_left_alone():
    """Four compositions write one field. A note that already holds an outcome
    table must not also be told it has no table."""
    assert jn.already_composed("x\n\n" + an.TABLE_MARKER)
    assert jn.already_composed("x\n\n" + an.PROBE_TABLE_MARKER)
    body, why = p2(note=ESSAY + "\n\n" + an.TABLE_MARKER)
    assert body is None and why == "already composed"


# ---------------------------------------------------------------------------
# the ungraded fallback: a mechanized role whose round wrote no table
# ---------------------------------------------------------------------------

def test_the_count_is_restated_from_the_machine_sentence():
    body, why = jn.compose("G-EQ", COUNTER, record=ABSENT_RECORD)
    assert body, why
    assert body.startswith(COUNTER)
    assert "re-ran 7 candidate wrong implementations" in body
    assert "None of them verified without also resolving the instance" in body


def test_the_two_recorded_count_shapes_are_both_restated():
    """Both spellings occur: `7 attacks re-run`, and `N admissible attacks re-run
    of M submitted`. The second says what happened to the other M-N, because the
    sentence it comes from does."""
    body, why = jn.compose("G-EQ", OF_SUBMITTED, record=ABSENT_RECORD)
    assert body, why
    assert "submitted 12 candidate wrong implementations" in body
    assert "re-ran the 9 of them that changed only the implementation" in body
    assert "the other 3 did not, so they do not test this specification" in body


def test_a_count_the_sentence_contradicts_is_declined():
    """The two numbers come out of the same sentence, so disagreement means the
    sentence is not the shape it looks like -- and every clause reads it."""
    note = OF_SUBMITTED.replace("9 admissible attacks re-run of 12", "12 "
                                "admissible attacks re-run of 9")
    body, why = jn.compose("G-EQ", note, record=ABSENT_RECORD)
    assert body is None and "counts disagree" in why


def test_a_note_with_no_recorded_count_is_declined():
    body, why = jn.compose("G-EQ", "eq: the attacks were re-run and none broke "
                                   "the spec; positive control verifies",
                           record=ABSENT_RECORD)
    assert body is None and why == "no recorded attack count in the note"


def test_a_probe_suite_sentence_is_never_described_in_the_verifiers_terms():
    """On that backend nothing verifies and HOLDING is the good outcome, so every
    sentence of this shape is false of it. No `ears` record needs the fallback;
    this is the guard that keeps it from becoming the false framing
    `audit_note`'s whitelist prevented."""
    body, why = jn.compose("G-EQ", PROBE_COUNTER, record=ABSENT_RECORD)
    assert body is None and "probe-suite shape" in why


def test_the_control_sentence_is_written_only_when_the_record_asserts_it():
    without = COUNTER.replace("; positive control verifies", "")
    with_ctl, why = jn.compose("G-EQ", COUNTER, record=ABSENT_RECORD)
    plain, why2 = jn.compose("G-EQ", without, record=ABSENT_RECORD)
    assert with_ctl and "The positive control verifies, so the specification is " \
        "satisfiable" in with_ctl
    assert plain, why2
    assert "positive control" not in plain[len(without):]


def test_the_paragraph_names_the_gap_the_record_actually_has():
    """A reader of the card cannot otherwise tell a role whose evidence ships in
    the bundle from one whose evidence was never retained."""
    absent, why = jn.compose("G-EQ", COUNTER, record=ABSENT_RECORD)
    assert absent, why
    assert "The attack sources are not carried in this bundle" in absent
    assert "The audit record states the same limitation." in absent
    legacy, why = jn.compose("G-EQ", COUNTER, record=LEGACY_RECORD)
    assert legacy, why
    assert "in the format that audit round used" in legacy
    assert "summarising it would mean re-grading prose" in legacy


def test_a_record_that_states_no_limitation_is_not_said_to_state_one():
    body, why = jn.compose("G-EQ", COUNTER, record="## Role 1 — G-EQ: pass\n")
    assert body, why
    assert "The attack sources are not carried in this bundle" in body
    assert "states the same limitation" not in body


def test_the_whole_body_is_held_to_the_routers_vocabulary_here():
    """Both ends of this shape are composed, so there is no recorded sentence to
    hold harmless -- unlike the probe account next door, whose first line is the
    harness's own `weak-candidate(s)`."""
    body, why = jn.compose("G-EQ", COUNTER + " (spec looks weak)",
                           record=ABSENT_RECORD)
    assert body is None and why == "composed note carries router vocabulary"


def test_a_body_outside_the_mechanized_band_is_declined():
    lo, hi = jn.BODY_BAND
    body, _ = jn.compose("G-EQ", COUNTER, record=ABSENT_RECORD)
    assert body and lo <= len(body) <= hi
    over, why = jn.compose("G-EQ", COUNTER + " " + "x" * 2600,
                           record=ABSENT_RECORD)
    assert over is None and "outside" in why


def test_an_ungraded_note_that_opens_with_inconclusive_is_declined():
    body, why = jn.compose("G-EQ", "eq: INCONCLUSIVE — 7 attacks re-run",
                           record=ABSENT_RECORD)
    assert body is None and "INCONCLUSIVE" in why


def test_the_ungraded_composition_is_idempotent():
    once, why = jn.compose("G-EQ", COUNTER, record=ABSENT_RECORD)
    assert once, why
    twice, why2 = jn.compose("G-EQ", once, record=ABSENT_RECORD)
    assert twice is None and why2 == "already composed"


def test_the_fallback_is_licensed_by_one_decline_and_not_by_any():
    """An outcome outside `audit_note`'s whitelist on a passing role means the
    record's evidence and its status disagree. Falling back to a paragraph
    saying "none verified without resolving" would publish the status over the
    evidence, so only "it recorded no outcomes" licenses this shape."""
    _body, why = an.compose(COUNTER, [])
    assert why in jn.UNGRADED_REASONS
    _body, why = an.compose(COUNTER, [{"name": "a.py",
                                       "result": "inconclusive (timeout)"}])
    assert why not in jn.UNGRADED_REASONS


def test_the_gate_key_chooses_the_shape():
    judged, _ = p2()
    mech, _ = jn.compose("G-EQ", COUNTER, record=ABSENT_RECORD)
    assert judged and jn.JUDGMENT_LEAD in judged
    assert mech and jn.JUDGMENT_LEAD not in mech and jn.UNGRADED_MARKER in mech


def test_the_two_dispatch_sets_are_disjoint_and_each_role_is_fully_described():
    """A judged role reaches three tables -- its question, its vocabulary and its ban --
    and a key in one but not the others would raise instead of declining. Pinned here
    rather than asserted at import, since it is a property of the tables."""
    assert set(jn.JUDGMENT_QUESTION) == set(jn.JUDGMENT_PASS_VERDICT)
    assert set(jn.JUDGMENT_QUESTION) == set(jn.JUDGMENT_TAIL_BAN)
    assert set(jn.JUDGMENT_QUESTION) == set(jn.JUDGMENT_SIBLINGS)
    assert not set(jn.JUDGMENT_QUESTION) & set(jn.MECH_GATES)


@pytest.mark.parametrize("gate", ["G-PANEL", "G-VERIFY", "G-CONF", "g-eq", ""])
def test_a_gate_this_composes_for_neither_way_is_declined(gate):
    """Both sets are closed. The fallback's count regex would read `re-ran 7
    attacks` out of a reviewer's essay, so a mistyped key must not reach it and
    publish a wrong-implementation account for a role that graded nothing."""
    body, why = jn.compose(gate, COUNTER + " " + ESSAY, agent_verdict="FAITHFUL",
                           gates=gates(**{"G-CONF": "pass"}), shipped=SHIPPED,
                           record=ABSENT_RECORD)
    assert body is None and why == f"{gate} is not a role this composes for"


def test_the_first_line_is_preserved_byte_for_byte():
    """The defect router reads this field, so what it sees must not change."""
    for gate, note, kw in (("G-PANEL-2", ESSAY, {}),
                           ("G-EQ", COUNTER, {"record": ABSENT_RECORD})):
        body, why = jn.compose(gate, note, agent_verdict="FAITHFUL",
                               gates=gates(**{"G-CONF": "pass"}), **kw)
        assert body, why
        assert body.partition("\n")[0] == note.partition("\n")[0]


# ---------------------------------------------------------------------------
# the recorded corpus: the composer reproduces what it published
# ---------------------------------------------------------------------------

BENCH = ROOT / "benchmark-verified"
# `leakage_note`'s own marker and the two labels its block can open with, named
# here rather than imported because this test needs them as BYTES in a published
# record and not as that module's API. Where they appear inside a judgment note,
# the leakage account was grafted in at the `JUDGMENT_LEAD` seam after this
# composer had already run, so the note this composed from is the stub above it.
LEAK_MARKER = "**What this role measured.**"
LEAK_LEADS = ("\n\n**What the spec view discloses.**",
              "\n\n**What the record says about the disclosure.**")
# Sweeping every recorded note in the corpus takes seconds, so the default is
# every cell. `SBU_TEST_STRIDE=N` thins it for a fast pass, and the assertion
# below scales with the stride rather than being pinned to a count that any edit
# to the corpus would move.
STRIDE = 1
# Bundles whose audit record this release withholds (scripts/strip_copyleft.py): a
# note composed from `verdict.md` cannot be recomposed without it.
WITHHELD = ROOT / "docs" / "copyleft-withheld.tsv"


def _withheld_records() -> set[Path]:
    if not WITHHELD.is_file():
        return set()
    rows = WITHHELD.read_text(encoding="utf-8").splitlines()[1:]
    return {(ROOT / row.split("\t", 1)[0]).parent
            for row in rows if row.split("\t", 1)[0].endswith("/verdict.md")}


def _candidates(rec: str) -> list[tuple[str, str]]:
    """`(note this composed from, the note it must reproduce)`, per ordering.

    Usually one pair: the recorded note split at its own seam. A G-PANEL-3 note
    carrying a leakage account is two, because the corpus records both orderings
    -- some notes were composed from the stub and had the leakage block grafted in
    at the seam afterwards, some were composed after it, and the difference is
    visible only in which files the account named. Either is a faithful
    reproduction of this composer; neither is a licence to write a name the note
    did not carry.
    """
    at = rec.rfind("\n\n" + jn.JUDGMENT_LEAD)
    if at < 0:                                    # the ungraded shape
        at = rec.rfind("\n\n**What was measured.**")
        return [(rec[:at].strip(), rec)] if at > 0 else []
    head, tail = rec[:at], rec[at:]
    out = [(head.strip(), head.strip() + tail)]
    if LEAK_MARKER in head:
        cut = min([p for p in (head.find(m) for m in LEAK_LEADS) if p >= 0],
                  default=-1)
        if cut > 0:
            out.append((head[:cut].strip(), head[:cut].strip() + tail))
    return out


@pytest.mark.skipif(not BENCH.is_dir(), reason="corpus not present")
def test_the_composer_reproduces_the_notes_it_published(monkeypatch):
    """Byte-for-byte, over a deterministic sample of the published records.

    The strongest available check that this module is the composer the shipped
    corpus was written by: the inputs are read back out of the bundle -- the
    recorded note, the gate map's statuses, the files on disk, the audit record
    -- and the output is compared against the note in `meta.json`.

    One documented slack, and it is in the corpus rather than here: some
    published notes are this composer's output with its single trailing newline
    removed, by a later writer that has left no trace in the tree. Every other
    byte matches, so the recorded note is compared with that newline restored
    and the count is reported rather than hidden.
    """
    import os
    stride = int(os.environ.get("SBU_TEST_STRIDE") or STRIDE)
    exact = restored = leak_route = 0
    withheld = _withheld_records()
    for meta_p in sorted(BENCH.glob("*/*/meta.json"))[::stride]:
        bundle = meta_p.parent
        if bundle in withheld:
            continue
        meta = json.loads(meta_p.read_text())
        vp = bundle / "verdict.md"
        record = vp.read_text(errors="replace") if vp.is_file() else ""
        shipped = [p.name for p in bundle.iterdir()]
        for gate, entry in sorted((meta.get("gates") or {}).items()):
            if not isinstance(entry, dict):
                continue
            rec = str(entry.get("note") or "")
            if jn.UNGRADED_MARKER not in rec:
                continue
            cands = _candidates(rec)
            assert cands, f"{bundle}/{gate}: no seam in a composed note"
            hits = []
            for note, target in cands:
                want = target if target.endswith("\n") else target + "\n"
                body, why = jn.compose(
                    gate, note, agent_verdict=str(entry.get("agent_verdict") or ""),
                    gates=meta.get("gates") or {}, shipped=shipped, record=record)
                assert body, f"{bundle}/{gate}: declined: {why}"
                hits.append((body == want, target.endswith("\n")))
            assert any(ok for ok, _nl in hits), f"{bundle}/{gate}: not reproduced"
            had_nl = next(nl for ok, nl in hits if ok)
            exact += had_nl
            restored += not had_nl
            leak_route += len(cands) > 1
    total = exact + restored
    assert total * stride > 2500, f"only {total} composed notes in the sample"
    # Reported, not asserted to the byte: the stride is a knob and the corpus is
    # rewritten as it is built. What IS asserted is that every note in the
    # sample was reproduced.
    print(f"\nreproduced {total} notes ({exact} exact, {restored} with the "
          f"record's trailing newline restored, {leak_route} through the "
          f"leakage seam)")
