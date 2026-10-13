# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A published role head must say what the stamp above it says.

`verdict_record._render_sections` composes the heading, the `status (recorded)`
bullet and the `machine verdict` bullet from the same fields it stamps, so the
head cannot disagree with the record at the moment it is written. `audit_recheck`
re-derives a stamp from the evidence retained in the file, which breaks that
invariant after the fact unless it re-renders the head too, and the shape it would
otherwise leave behind is a head publishing `fail` and `INCONCLUSIVE` above a
passing gate.

These tests pin the repair and, mostly, its limits. A stale head is sometimes the
only surviving evidence for the stamp it disagrees with: it is where the earlier
attempt's `status (recorded)` and machine verdict are still written down, so
rewriting it can be the step that destroys what a later re-derivation would have
to be proved from. The tests that matter are therefore the ones proving which
heads keep their text, and that no line of evidence moves.
"""
from __future__ import annotations

import audit_recheck as ar

BODY = "def f (n : Nat) : Nat := n + 1\n"
NOTE = ("G-EQ: 8 attacks re-verified from the retained audit evidence "
        "(verdict.md), none breaks the spec; positive control verifies. "
        "The original run's verifier timed out under host load.")
OLD = "eq: INCONCLUSIVE — 1 attack(s) inconclusive"


def _section(gate: str = "G-EQ", num: int = 1, status: str = "fail",
             note: str = OLD, label: str = "refinement fidelity",
             agent: str | None = "SOUND", nattacks: int = 3) -> str:
    """One role section in the shape the composer emits."""
    head = f"## Role {num} — {gate} ({label}): {status}"
    if agent:
        head += f" (agent: {agent})"
    out = [head, "", f"- **status (recorded):** `{status}`",
           f"- **machine verdict:** {note}", "",
           f"**Attacks re-run ({nattacks}):** each is a same-spec wrong impl.", ""]
    for i in range(1, nattacks + 1):
        out += [f"Attack {i} — `atk_{i}.lean` → rejected "
                "(same spec, does not verify — good)", "",
                f"```lean\n{BODY}```", ""]
    out += ["Prepatch bug re-encoded as an attack: `True`", "",
            "**Positive control** (a correct impl that MUST verify — "
            "non-vacuity): `atk_pos.lean`", "", f"```lean\n{BODY}```", ""]
    return "\n".join(out)


def _stamp(status: str = "pass", note: str = NOTE, recheck: bool = True) -> dict:
    e: dict = {"status": status, "note": note}
    if recheck:
        e["recheck"] = {"attacks": 8, "timeout_s": 1800, "reason": "timeout"}
    return e


# ---- the repair ----

def test_all_three_head_fields_move_to_the_stamp():
    new, changed, why = ar.align_role(_section(), "G-EQ", _stamp())
    assert changed == ["heading", "status (recorded)", "machine verdict"], why
    assert "## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)" in new
    assert "- **status (recorded):** `pass`" in new
    assert f"- **machine verdict:** {NOTE}" in new
    assert OLD not in new


def test_the_agent_verdict_survives_the_heading_rewrite():
    """It is a different claim from the machine's -- advisory context, and the
    file says so in its preamble -- so a status repair must not consume it."""
    new, _c, _w = ar.align_role(_section(agent="WEAK (verify⇏correct)"),
                                "G-EQ", _stamp())
    assert new.splitlines()[0] == (
        "## Role 1 — G-EQ (refinement fidelity): pass "
        "(agent: WEAK (verify⇏correct))")


def test_a_head_with_no_agent_verdict_is_handled():
    new, changed, why = ar.align_role(_section(agent=None), "G-EQ", _stamp())
    assert changed and not why
    assert new.splitlines()[0] == "## Role 1 — G-EQ (refinement fidelity): pass"


def test_only_the_wording_moves_when_the_status_already_agrees():
    """The 32-cell class: the head recorded the pass correctly and merely quotes
    the earlier, shorter sentence."""
    short = "eq: 10 attacks re-run, none breaks the spec; positive control verifies"
    new, changed, _w = ar.align_role(_section(status="pass", note=short),
                                     "G-EQ", _stamp())
    assert changed == ["machine verdict"]
    assert new.count("pass") >= 2 and short not in new


def test_an_already_aligned_head_is_a_no_op():
    md = _section(status="pass", note=NOTE)
    new, changed, why = ar.align_role(md, "G-EQ", _stamp())
    assert changed == [] and not why and new == md


def test_the_repair_is_idempotent():
    once, first, _w = ar.align_role(_section(), "G-EQ", _stamp())
    twice, second, _w2 = ar.align_role(once, "G-EQ", _stamp())
    assert first and second == [] and twice == once


# ---- the limits: heads that must KEEP their text ----

def test_a_stamp_without_a_recheck_payload_is_left_alone():
    """The licence. Without it there is no evidence that the head and the stamp
    describe one measurement, and the head may be the only record of the other."""
    md = _section()
    new, changed, why = ar.align_role(md, "G-EQ", _stamp(recheck=False))
    assert changed == [] and new == md
    assert "recheck" in why


def test_a_head_recording_a_demotion_is_left_alone():
    """A head that records a demotion is the record OF the demotion: `status
    (recorded)` and the machine verdict in it are the earlier attempt's answer,
    which is what any later restoration would have to be proved from. Rewriting it
    destroys that. Both wordings are refused.
    """
    for sentence in ("A later attempt did not reach a verdict for this role.",
                     "eq: this role reached no verdict on the latest attempt"):
        md = _section(note=sentence)
        new, changed, why = ar.align_role(md, "G-EQ", _stamp())
        assert changed == [] and new == md
        assert "demotion" in why, why


def test_a_failing_stamp_is_left_alone():
    """The dangerous direction: publishing `pass` over a gate the corpus records
    as failing would be a false claim about a specification."""
    md = _section(status="fail")
    new, changed, why = ar.align_role(md, "G-EQ", _stamp(status="fail"))
    assert changed == [] and new == md and "not a pass" in why


def test_an_unrecognised_heading_is_reported_not_guessed_at():
    md = _section().replace("## Role 1 — G-EQ (refinement fidelity): fail",
                            "## Role 1 — G-EQ (refinement fidelity) fail", 1)
    new, changed, why = ar.align_role(md, "G-EQ", _stamp())
    assert changed == [] and new == md and "unrecognised heading" in why


def test_a_missing_bullet_is_reported_and_nothing_is_inserted():
    for bullet in ("- **status (recorded):** `fail`\n",
                   f"- **machine verdict:** {OLD}\n"):
        md = _section().replace(bullet, "", 1)
        new, changed, why = ar.align_role(md, "G-EQ", _stamp())
        assert changed == [] and new == md, why
        assert why.startswith("no `"), why


def test_an_absent_role_section_is_declined():
    new, changed, why = ar.align_role(_section(gate="G-PANEL-2"), "G-EQ",
                                      _stamp())
    assert changed == [] and "no role section" in why


def test_another_role_is_not_touched():
    md = _section("G-EQ", 1) + "\n" + _section("G-PANEL-1", 2,
                                               label="spec-too-weak")
    new, changed, _w = ar.align_role(md, "G-EQ", _stamp())
    assert changed
    assert "## Role 2 — G-PANEL-1 (spec-too-weak): fail (agent: SOUND)" in new
    assert new.count("- **status (recorded):** `fail`") == 1


# ---- fidelity: the evidence does not move ----

def test_every_line_that_is_not_a_head_field_survives_byte_for_byte():
    md = _section()
    new, changed, _w = ar.align_role(md, "G-EQ", _stamp())
    before, after = md.split("\n"), new.split("\n")
    assert len(before) == len(after)
    diff = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert len(diff) == len(changed) == 3, [before[i] for i in diff]
    assert diff == [0, 2, 3], diff


def test_a_machine_bullet_quoted_inside_an_attack_body_is_not_the_role_bullet():
    """An attack may be a wrong impl whose comment quotes the record. The bullet
    scan stops at the first fence so the evidence cannot be mistaken for the
    head -- and cannot be edited by a head repair."""
    forged = ("Attack 1 — `atk_1.lean` → rejected (same spec, does not verify "
              "— good)\n\n```lean\n-- **status (recorded):** `fail`\n"
              f"- **machine verdict:** {OLD}\n{BODY}```\n")
    md = _section(nattacks=0).replace(
        "Prepatch bug re-encoded", forged + "\nPrepatch bug re-encoded", 1)
    new, changed, _w = ar.align_role(md, "G-EQ", _stamp())
    assert changed == ["heading", "status (recorded)", "machine verdict"]
    # the forged copies inside the fence are still there, untouched
    assert f"- **machine verdict:** {OLD}" in new
    assert "-- **status (recorded):** `fail`" in new


def test_a_role_heading_inside_a_fence_does_not_bound_the_span():
    """`role_span` is fence-aware: an attack body quoting `## Role 2 — ...` would
    otherwise cut the section short and hide its own bullets."""
    md = _section(nattacks=1).replace(
        f"```lean\n{BODY}```",
        f"```lean\n## Role 9 — G-PANEL-1 (spec-too-weak): fail\n{BODY}```", 1)
    _new, changed, why = ar.align_role(md, "G-EQ", _stamp())
    assert changed == ["heading", "status (recorded)", "machine verdict"], why


# ---- an enriched stamp is not a stale head ----

ACCOUNT = ("**What was measured.** The harness re-ran 8 candidate wrong "
           "implementations submitted against this specification, recorded "
           "each outcome, and re-verified the positive control.")


def _enriched(note: str = NOTE, account: str = ACCOUNT) -> tuple[str, str]:
    """`(md, note)` for a role whose account is already published as a block.

    The bullet keeps the tally and the account is published as its own block
    below it, which is what `_render_note` does with a multi-line note.
    """
    md = _section(status="pass", note=note).replace(
        f"- **machine verdict:** {note}\n",
        f"- **machine verdict:** {note}\n\n{account}\n", 1)
    return md, f"{note}\n\n{account}"


def test_a_published_account_is_not_a_disagreement():
    md, recorded = _enriched()
    _new, changed, why = ar.align_role(md, "G-EQ", _stamp(note=recorded))
    assert changed == [] and why == "", (changed, why)


def test_the_enriched_bullet_is_never_rewritten_into_a_broken_list():
    """The failure this guards: the whole multi-paragraph note inlined after the
    list marker, which ends the list at the first newline and republishes the
    account a second time."""
    md, recorded = _enriched()
    new, _c, _w = ar.align_role(md, "G-EQ", _stamp(note=recorded))
    assert new == md
    assert new.count(ACCOUNT) == 1


def test_a_rewrapped_account_still_counts_as_published():
    md, recorded = _enriched()
    md = md.replace(ACCOUNT, ACCOUNT.replace(", recorded", ",\nrecorded"), 1)
    _new, changed, why = ar.align_role(md, "G-EQ", _stamp(note=recorded))
    assert changed == [] and why == "", (changed, why)


def test_an_unpublished_account_is_declined_rather_than_inlined():
    md = _section(status="pass")                     # bullet carries OLD
    recorded = f"{NOTE}\n\n{ACCOUNT}"
    new, changed, why = ar.align_role(md, "G-EQ", _stamp(note=recorded))
    assert changed == [] and new == md
    assert "the composer's job" in why


def test_a_stale_head_under_an_enriched_stamp_is_still_declined_whole():
    """Not half-repaired: the heading and the recorded status must not move on a
    role whose bullet this tool has decided it cannot write."""
    md = _section(status="fail")
    new, changed, _why = ar.align_role(
        md, "G-EQ", _stamp(note=f"{NOTE}\n\n{ACCOUNT}"))
    assert changed == [] and new == md
    assert "`fail`" in new


def test_a_single_line_stamp_is_still_aligned_the_old_way():
    md = _section(status="pass")
    new, changed, _why = ar.align_role(md, "G-EQ", _stamp())
    assert changed == ["machine verdict"]
    assert f"- **machine verdict:** {NOTE}" in new


def test_the_enriched_no_op_is_idempotent_through_align_cell():
    md, recorded = _enriched()
    new, moved = ar.align_cell(md, {"G-EQ": _stamp(note=recorded)})
    assert moved == {} and new == md


def test_note_head_and_account_split_where_the_renderer_splits():
    recorded = f"{NOTE}\n\n{ACCOUNT}"
    assert ar.note_head(recorded) == NOTE
    assert ar.note_account(recorded) == ACCOUNT
    assert ar.note_head(NOTE) == NOTE and ar.note_account(NOTE) == ""


def test_align_cell_walks_every_role_and_reports_what_moved():
    md = _section("G-EQ", 1) + "\n" + _section("G-PANEL-1", 2,
                                               label="spec-too-weak")
    new, moved = ar.align_cell(md, {"G-EQ": _stamp(),
                                    "G-PANEL-1": _stamp(note="panel_1: ok"),
                                    "G-PANEL-2": _stamp()})
    assert set(moved) == {"G-EQ", "G-PANEL-1"}      # PANEL-2 has no section
    assert "- **machine verdict:** panel_1: ok" in new
    assert "`fail`" not in new
