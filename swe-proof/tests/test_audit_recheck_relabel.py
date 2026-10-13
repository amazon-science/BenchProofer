# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A re-derived attack has to say so in the record, not only in the stamp.

`audit_recheck` re-verifies the attacks retained in verdict.md at a caller-chosen
cap and re-derives the recorded verdict from them. `_verdict_of` returns `pass`
only when every attack whose ORIGINAL verifier ran out of clock completed this
time and failed to verify -- an incomplete one lands in `inc`, a completing-and-
verifying one in `oracle`, and both outrank a pass. So a written pass is itself
the proof that each such attack was measured and rejected.

What the write path used to leave behind is the published half. meta.json got the
cleared status and a note saying the cell was re-derived; verdict.md kept the
original `→ inconclusive (verifier timed out)` line. Anyone reading the artifact
then sees a PASSING gate whose retained evidence contains an undecided attack,
which is indistinguishable from a pass that rests on one. `audit_note.compose`
acts on exactly that reading: it declines to describe the record, and the release
surface keeps a 70-character counter. The attacks this happens to are the ones
whose timeout had already been re-derived.

These tests pin the rewrite and, more importantly, its limits -- the three shapes
that must KEEP their label, since a declined note is merely short and a wrongly
cleared one is a false claim about a specification.
"""
from __future__ import annotations

from swebench_unified.construct import audit_note
from audit_recheck import parse_verdict, relabel_settled_timeouts


def _composer_input(md: str, gate: str = "G-EQ") -> tuple[list[dict], str, bool | None]:
    """The composer's view of one role, read back out of the record."""
    sec = parse_verdict(md)[gate]
    attacks = [{"name": n, "result": o or ""} for n, _s, o in sec["attacks"]]
    control = (sec.get("control") or ("",))[0]
    return attacks, control, sec.get("prepatch_reproduced")

BODY = "def f (n : Nat) : Nat := n + 1\n"
TIMED_OUT = "inconclusive (verifier timed out (inconclusive))"
REJECTED = "rejected (same spec, does not verify — good)"
ECHO = "correct echo (verifies AND its patch resolves — not a weakness)"


def _role(gate: str, num: int, labels: list[str]) -> str:
    """One role section in the shape the composer emits."""
    out = [f"## Role {num} — {gate} (spec-too-weak)", "",
           "The spec was attacked as follows.", ""]
    for i, lab in enumerate(labels, 1):
        out += [f"Attack {i} — `atk_{i}.lean` → {lab}", "",
                f"```lean\n{BODY}```", ""]
    out += ["Prepatch bug re-encoded as an attack: `True`", "",
            "**Positive control** (a correct impl that MUST verify — "
            "non-vacuity): `atk_pos.lean`", "", f"```lean\n{BODY}```", ""]
    return "\n".join(out)


def _fresh(labels: list[str], over: dict[int, dict] | None = None) -> dict:
    """The re-verification results `recheck_cell` builds, in document order.

    Defaults describe the outcome that licenses a pass: every attack completed,
    still shares the bundle's spec, and only the adjudicated echo verifies.
    `over` overrides one attack by 1-based index, e.g. `{2: {"completed": False}}`.
    """
    from audit_recheck import classify_old
    atk = []
    for i, lab in enumerate(labels, 1):
        cls = classify_old(lab)
        a = {"name": f"atk_{i}.lean", "old": lab, "old_class": cls,
             "completed": True, "same_spec": True, "verifies": cls == "echo",
             "summary": ""}
        a.update((over or {}).get(i, {}))
        atk.append(a)
    return {"attacks": atk, "control": {"name": "atk_pos.lean", "completed": True,
                                        "same_spec": True, "verifies": True,
                                        "summary": ""},
            "prepatch_reproduced": True}


# ---- the rewrite ----

def test_a_settled_timeout_is_relabelled_as_rejected():
    labels = [REJECTED, TIMED_OUT, REJECTED, REJECTED, REJECTED]
    md = _role("G-EQ", 1, labels)
    new, changed = relabel_settled_timeouts(md, {"G-EQ": _fresh(labels)})
    assert changed == ["G-EQ/atk_2.lean"], changed
    assert "→ rejected (same spec, does not verify — re-derived at a higher" in new
    assert TIMED_OUT not in new


def test_the_new_label_reduces_to_one_the_composer_describes():
    """The whole point. `audit_note.outcome_label` cuts at the first " (" and
    matches the remainder against a closed whitelist, so the gloss may say
    anything but the label itself has to be a vocabulary word."""
    labels = [TIMED_OUT] + [REJECTED] * 4
    new, _ = relabel_settled_timeouts(_role("G-EQ", 1, labels),
                                      {"G-EQ": _fresh(labels)})
    attacks, _ctl, _pp = _composer_input(new)
    reduced = [audit_note.outcome_label(a["result"]) for a in attacks]
    assert reduced[0] == "rejected"
    assert all(lab in audit_note.OUTCOME_GLOSS for lab in reduced)


def test_the_gloss_keeps_the_original_timeout_on_the_record():
    """A reader is entitled to know the line is a SECOND measurement: a bare
    `rejected` would read as the original verifier's finding."""
    labels = [TIMED_OUT] + [REJECTED] * 4
    new, _ = relabel_settled_timeouts(_role("G-EQ", 1, labels),
                                      {"G-EQ": _fresh(labels)})
    line = [ln for ln in new.split("\n") if ln.startswith("Attack 1 ")][0]
    assert "re-derived at a higher verifier cap" in line
    assert "verifier timed out" in line


# ---- the limits: what must KEEP its label ----

def test_an_attack_still_inconclusive_at_the_higher_cap_is_untouched():
    """`_verdict_of` would call this cell `inconclusive` and write nothing, so the
    rewrite must not fire even if it is somehow reached: the attack was not
    measured, and saying it was rejected would invent a verdict."""
    labels = [TIMED_OUT] + [REJECTED] * 4
    new, changed = relabel_settled_timeouts(
        _role("G-EQ", 1, labels), {"G-EQ": _fresh(labels, {1: {"completed": False}})})
    assert changed == [] and TIMED_OUT in new


def test_an_attack_that_now_verifies_is_untouched():
    """The dangerous direction. A timed-out attack that VERIFIES at the bigger cap
    is an unadjudicated candidate bound for the resolve oracle -- the one shape
    that could be a real verify-does-not-imply-correct hole."""
    labels = [TIMED_OUT] + [REJECTED] * 4
    new, changed = relabel_settled_timeouts(
        _role("G-EQ", 1, labels), {"G-EQ": _fresh(labels, {1: {"verifies": True}})})
    assert changed == [] and TIMED_OUT in new
    assert "rejected (same spec, does not verify — re-derived" not in new


def test_an_attack_that_no_longer_shares_the_spec_is_untouched():
    """Evidence about a spec that no longer exists cannot settle anything."""
    labels = [TIMED_OUT] + [REJECTED] * 4
    _new, changed = relabel_settled_timeouts(
        _role("G-EQ", 1, labels), {"G-EQ": _fresh(labels, {1: {"same_spec": False}})})
    assert changed == []


def test_labels_that_were_never_timeouts_are_left_alone():
    labels = [REJECTED, ECHO, REJECTED, REJECTED, REJECTED]
    new, changed = relabel_settled_timeouts(md := _role("G-EQ", 1, labels),
                                            {"G-EQ": _fresh(labels)})
    assert changed == [] and new == md


# ---- fidelity ----

def test_only_the_caption_changes_and_every_body_survives():
    """The retained sources ARE the evidence, and
    `check_stamp_freshness._retained_control` compares the control body against the
    solution on disk byte for byte."""
    labels = [REJECTED, TIMED_OUT, REJECTED, REJECTED, REJECTED]
    md = _role("G-EQ", 1, labels)
    new, _ = relabel_settled_timeouts(md, {"G-EQ": _fresh(labels)})
    before, after = md.split("\n"), new.split("\n")
    assert len(before) == len(after)
    diff = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert len(diff) == 1, [before[i] for i in diff]
    assert before[diff[0]].startswith("Attack 2 ")
    old_sec, new_sec = parse_verdict(md)["G-EQ"], parse_verdict(new)["G-EQ"]
    assert [s for _n, s, _o in new_sec["attacks"]] == \
           [s for _n, s, _o in old_sec["attacks"]]
    assert new_sec["control"] == old_sec["control"]


def test_the_rewrite_is_idempotent():
    labels = [TIMED_OUT] + [REJECTED] * 4
    fresh = {"G-EQ": _fresh(labels)}
    once, first = relabel_settled_timeouts(_role("G-EQ", 1, labels), fresh)
    # the second pass re-reads the FILE, whose labels are now `rejected`, so the
    # timeout class is gone and there is nothing left to settle
    twice, second = relabel_settled_timeouts(once, fresh)
    assert first and second == [] and twice == once


def test_a_repeated_attack_name_is_matched_within_its_own_role():
    """Attack numbering restarts per role and `atk_1.lean` exists in both, so
    pairing by name alone would relabel the wrong role's line."""
    eq = [TIMED_OUT, REJECTED, REJECTED, REJECTED, REJECTED]
    p1 = [REJECTED] * 5
    md = _role("G-EQ", 1, eq) + "\n" + _role("G-PANEL-1", 2, p1)
    new, changed = relabel_settled_timeouts(
        md, {"G-EQ": _fresh(eq), "G-PANEL-1": _fresh(p1)})
    assert changed == ["G-EQ/atk_1.lean"], changed
    # the rewrite is visible in the raw caption, since `parse_sections` reduces
    # both roles' labels to the same word
    caps = [ln for ln in new.split("\n") if ln.startswith("Attack 1 ")]
    assert len(caps) == 2, caps
    assert "re-derived at a higher verifier cap" in caps[0]
    assert caps[1].endswith("→ " + REJECTED), caps[1]


# ---- end to end: the reason this exists ----

def test_the_relabelled_record_composes_a_release_note():
    """Before: `compose` meets a label outside its whitelist on a passing gate and
    declines, leaving the counter. After: a real table."""
    labels = [REJECTED, TIMED_OUT, REJECTED, REJECTED, ECHO]
    md = _role("G-EQ", 1, labels)
    note = ("G-EQ: 5 attacks re-verified from the retained audit evidence "
            "(verdict.md), none breaks the spec; positive control verifies.")

    attacks, control, prepatch = _composer_input(md)
    body, why = audit_note.compose(note, attacks, control=control,
                                   prepatch=prepatch)
    assert body is None, why

    new, _ = relabel_settled_timeouts(md, {"G-EQ": _fresh(labels)})
    attacks, control, prepatch = _composer_input(new)
    body, why = audit_note.compose(note, attacks, control=control,
                                   prepatch=prepatch)
    assert body, why
    assert audit_note.TABLE_MARKER in body
    assert not audit_note.FORBIDDEN.search(body), body
