# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A record published as a diff, and what the two tools that read it may claim.

`build_one._attack_excerpt` publishes each attack as a unified diff against the
cell's spec file rather than one near-identical copy of that file per attack. It
is the right call -- twenty attacks would otherwise carry twenty copies of
model.py -- but it has two consequences, and this file pins both.

The first is a caption. "Identical to the baseline" is a defect in an ATTACK and
the defining property of a POSITIVE CONTROL, and one sentence was used for both,
so a cell published under a passing gate the claim that its own non-vacuity
control "cannot demonstrate anything" -- every such caption sits on a
positive-control line, never on an attack line.

The second is a re-derivation. `audit_recheck` writes each retained body to a file
and runs the verifier on it. A diff is not a program, so it does not verify and
carries no spec markers -- and `_verdict_of` turned that into a claim about the
SPECIFICATION: "spec may now reject a correct impl" for an echo, "bundle edited
since the audit" for a rejection. Neither is true of a cell that retains its
attacks this way. The tests below are mostly about that direction: a tool may
report that a record cannot be re-derived, and may not invent a spec weakness
from the format it was published in.
"""
from __future__ import annotations

from audit_recheck import (
    _verdict_of, is_diff_body, parse_verdict, reconstruct_from_diff)
from swebench_unified.construct.build_one import (
    CONTROL_IS_BASELINE, DIFF_CAPTION, DIFF_LEAD_IN, _attack_excerpt,
    _render_attack_block)

SPEC = ("# pre-conditions-start\n# pre-conditions-end\n"
        "def f(n):\n    return n + 1\n")
WRONG = SPEC.replace("n + 1", "n + 2")


# ---- the caption: the control is SUPPOSED to equal the baseline ----

def test_a_control_equal_to_the_baseline_is_captioned_as_a_control():
    _block, caption = _attack_excerpt(SPEC, SPEC, "python", role="control")
    assert caption == CONTROL_IS_BASELINE
    assert "cannot demonstrate anything" not in caption
    assert "non-vacuity control" in caption


def test_an_attack_equal_to_the_baseline_keeps_its_warning():
    """The other half of the same fact: an attack that changes nothing really
    does demonstrate nothing, and a reader has to be told."""
    _block, caption = _attack_excerpt(SPEC, SPEC, "python")
    assert "cannot demonstrate anything" in caption


def test_the_rendered_block_does_not_undermine_its_own_control():
    """End to end through the composer, which is where the caption comes from."""
    out = "\n".join(_render_attack_block(
        "nagini", [{"name": "atk_1.py", "src": WRONG, "result": "rejected"}],
        {"name": "pos_control.py", "src": SPEC}, True, baseline=SPEC))
    ctrl = [ln for ln in out.split("\n") if ln.startswith("**Positive control**")]
    assert len(ctrl) == 1, out
    assert "cannot demonstrate anything" not in ctrl[0]
    assert CONTROL_IS_BASELINE in ctrl[0]


def test_a_control_that_differs_from_the_baseline_is_still_shown_as_a_diff():
    """The caption is about equality, not about being a control: a control that is
    NOT the unmodified spec file is exactly the case a reader must see."""
    block, caption = _attack_excerpt(WRONG, SPEC, "python", role="control")
    assert "shown as a diff" in caption
    assert "```diff" in block and any(ln.startswith("+") for ln in block)


# ---- the hoist: why a block is a diff belongs to the battery, not the block ----

def test_the_diff_note_is_written_once_per_role_not_once_per_attack():
    """It is a fact about the whole battery -- every attack is the same spec file
    with a different implementation -- so saying it under each block repeats the
    same sentence once per attack. The lead-in carries it and the blocks stay
    bare."""
    atks = [{"name": f"atk_{i}.py", "src": WRONG.replace("n + 2", f"n + {i}"),
             "result": "rejected"} for i in (3, 4, 5)]
    out = "\n".join(_render_attack_block(
        "nagini", atks, {"name": "pos_control.py", "src": SPEC}, None,
        baseline=SPEC))
    assert out.count("```diff") == 3          # every attack diffed
    assert DIFF_CAPTION not in out
    assert out.count(DIFF_LEAD_IN) == 1
    # in the lead-in, so it is read before the blocks it describes
    lead = next(ln for ln in out.split("\n") if ln.startswith("**Attacks re-run"))
    assert DIFF_LEAD_IN in lead
    assert out.index(DIFF_LEAD_IN) < out.index("```diff")


def test_a_battery_with_nothing_to_diff_does_not_promise_a_diff():
    """No baseline to diff against, so every block is a whole program: a lead-in
    announcing a `diff` block would describe something that is not there."""
    out = "\n".join(_render_attack_block(
        "nagini", [{"name": "atk_1.py", "src": WRONG, "result": "rejected"}],
        None, None))
    assert DIFF_LEAD_IN not in out and DIFF_CAPTION not in out
    assert "```python" in out


def test_the_hoist_leaves_the_per_block_findings_where_they_are():
    """Only the boilerplate moves. The other captions are findings about ONE block
    -- this attack changes nothing, this control is the unmodified spec -- and a
    reader needs each next to the block it judges."""
    out = "\n".join(_render_attack_block(
        "nagini", [{"name": "atk_1.py", "src": WRONG, "result": "rejected"},
                   {"name": "atk_2.py", "src": SPEC, "result": "verified"}],
        {"name": "pos_control.py", "src": SPEC}, None, baseline=SPEC))
    assert DIFF_LEAD_IN in out                       # atk_1 did diff
    lines = out.split("\n")
    assert "cannot demonstrate anything" in next(
        ln for ln in lines if "`atk_2.py`" in ln)
    assert CONTROL_IS_BASELINE in next(
        ln for ln in lines if ln.startswith("**Positive control**"))


# ---- the re-derivation: a diff is not a program ----

def test_a_hunk_header_body_is_recognised_as_a_diff():
    assert is_diff_body("@@ -389,7 +389,11 @@\n     x = 1\n-    y = 2\n")
    assert is_diff_body("@@ -1 +1 @@\n-a\n+b\n")
    assert is_diff_body("\n@@ -1,2 +1,3 @@\n-a\n")     # leading blank line


def test_a_whole_program_is_not_a_diff():
    assert not is_diff_body(SPEC)
    assert not is_diff_body("")
    # a program whose own text mentions a hunk header, but not at the front
    assert not is_diff_body("# see @@ -1,2 +1,3 @@ below\ndef f(): pass\n")


def test_a_lean_decorator_at_the_top_is_not_a_diff():
    """`@[simp]` starts with `@` and is the first line of many Lean attacks."""
    assert not is_diff_body("@[simp] theorem t : 1 = 1 := rfl\n")


def test_a_diff_retained_echo_is_not_reported_as_a_spec_that_rejects_correctness():
    """The dangerous sentence. An adjudicated echo whose body is a diff cannot be
    re-verified, and calling that "the spec may now reject a correct impl" invents
    a soundness problem out of a publishing format."""
    roles = {"G-EQ": {"attacks": [], "control": None,
                      "prepatch_reproduced": True,
                      "diff_retained": ["atk_16.py"]}}
    out = _verdict_of(roles, 1)
    assert out["outcome"] == "inconclusive"
    assert "spec may now reject a correct impl" not in out["detail"]
    assert "bundle edited since" not in out["detail"]
    assert "published as a diff" in out["detail"]
    assert "atk_16.py" in out["detail"]


def test_the_diff_reason_is_stated_before_the_floor_it_explains():
    """`only 0 attacks` is a true consequence and a misleading headline: a reader
    (or a lane routing on this text) has to meet the cause first."""
    roles = {"G-EQ": {"attacks": [], "control": None,
                      "prepatch_reproduced": True,
                      "diff_retained": ["atk_1.py", "atk_2.py"]}}
    detail = _verdict_of(roles, 5)["detail"]
    assert detail.index("published as a diff") < detail.index("only 0 attacks")


def test_a_record_with_no_diffs_is_judged_exactly_as_before():
    """The guard must be inert on the full-source records this tool exists for."""
    ok = {"name": "atk_1.py", "old": "rejected (same spec, does not verify)",
          "old_class": "reject", "completed": True, "same_spec": True,
          "verifies": False, "summary": ""}
    roles = {"G-EQ": {"attacks": [ok], "control": {
        "name": "pos.py", "completed": True, "same_spec": True,
        "verifies": True, "summary": ""}, "prepatch_reproduced": True,
        "diff_retained": []}}
    out = _verdict_of(roles, 1)
    assert out["outcome"] == "pass", out["detail"]
    assert "published as a diff" not in out["detail"]


def test_a_verifying_attack_still_condemns_a_spec_alongside_a_diff_body():
    """The guard suppresses a diagnosis about attacks that were NEVER RUN. It must
    not suppress one about an attack that ran and verified, which is the only
    shape that can be a real verify-does-not-imply-correct hole."""
    hole = {"name": "atk_2.py", "old": "rejected (same spec, does not verify)",
            "old_class": "reject", "completed": True, "same_spec": True,
            "verifies": True, "summary": ""}
    roles = {"G-EQ": {"attacks": [hole], "control": None,
                      "prepatch_reproduced": True,
                      "diff_retained": ["atk_1.py"]}}
    out = _verdict_of(roles, 1)
    assert out["outcome"] == "candidate"
    assert "now VERIFY" in out["detail"] and "atk_2.py" in out["detail"]


# ---- the lossless claim: baseline + diff IS the attack ----

BIG = "\n".join(["# pre-conditions-start", "# pre-conditions-end"]
                + [f"def f{n}(x):" for n in range(6)]) + "\n"


def _diff_of(attack: str, baseline: str) -> str:
    """The retained body the composer would publish for `attack`."""
    block, _cap = _attack_excerpt(attack, baseline, "python")
    return "\n".join(block[2:-1])          # drop "", "```diff" and "```"


def test_a_retained_diff_round_trips_back_to_the_attack():
    """The claim `_attack_excerpt` rests on, measured rather than asserted."""
    body = _diff_of(WRONG, SPEC)
    assert is_diff_body(body)
    assert reconstruct_from_diff(SPEC, body) == WRONG


def test_multiple_separated_hunks_reconstruct():
    """One hunk is not the interesting case: a real attack edits two or three
    places far enough apart that difflib emits a hunk each."""
    attack = BIG.replace("def f0(x):", "def f0(y):").replace(
        "def f5(x):", "def f5(y):")
    body = _diff_of(attack, BIG)
    assert body.count("@@") >= 2, body
    assert reconstruct_from_diff(BIG, body) == attack


def test_a_blank_context_line_stripped_by_markdown_still_applies():
    """difflib writes a blank context line as a single space, and anything that
    normalises verdict.md strips it. Reconstruction has to survive that, since
    every spec file in the corpus has blank lines."""
    base = "a\n\nb\n\nc\n\nd\n\ne\n"
    attack = base.replace("c", "C")
    body = _diff_of(attack, base)
    stripped = "\n".join(ln.rstrip() if ln == " " else ln
                         for ln in body.split("\n"))
    assert stripped != body                       # the hazard is real
    assert reconstruct_from_diff(base, stripped) == attack


def test_a_hunk_whose_context_does_not_match_is_refused():
    """The whole point is to re-verify what the reviewer wrote. A hunk applied to
    a spec file that has since moved must not produce a plausible program."""
    body = _diff_of(WRONG, SPEC)
    assert reconstruct_from_diff(SPEC.replace("n + 1", "n + 7"), body) is None


def test_a_hunk_header_that_lies_about_its_length_is_refused():
    body = _diff_of(WRONG, SPEC).replace("@@ -1,4 +1,4 @@", "@@ -1,9 +1,4 @@")
    assert reconstruct_from_diff(SPEC, body) is None


def test_a_whole_program_body_is_not_run_through_the_applier():
    assert reconstruct_from_diff(SPEC, WRONG) is None      # not a diff at all


def test_reconstruction_emits_the_baseline_bytes_for_unchanged_lines():
    """The trailing-whitespace tolerance is for MATCHING only. If it leaked into
    the output, a reconstructed attack would differ from the reviewer's in
    whitespace, and `same_spec` compares text."""
    base = "def f():\n    x = 1   \n    return x\n"
    attack = base.replace("return x", "return 0")
    body = "\n".join(ln.rstrip() for ln in _diff_of(attack, base).split("\n"))
    assert reconstruct_from_diff(base, body) == attack
    assert "x = 1   " in (reconstruct_from_diff(base, body) or "")


# ---- the two ends meet: what the composer writes, the checker reads ----

def test_a_composed_diff_record_round_trips_to_the_diff_guard():
    """The regression that produced the two false sentences, measured end to end
    rather than asserted: render a real attack the way the corpus does, parse it
    back the way `audit_recheck` does, and the body must be recognised."""
    md = "\n".join(["## Role 1 — G-EQ (refinement fidelity): pass", ""]
                   + _render_attack_block(
        "nagini", [{"name": "atk_1.py", "src": WRONG,
                    "result": "correct echo (verifies AND its patch resolves)"}],
        {"name": "pos_control.py", "src": SPEC}, True, baseline=SPEC))
    sec = parse_verdict(md)["G-EQ"]
    assert len(sec["attacks"]) == 1
    _name, src, _old = sec["attacks"][0]
    assert is_diff_body(src), src
    # and the control, being equal to the baseline, has no body to re-verify
    assert sec["control"] is None
