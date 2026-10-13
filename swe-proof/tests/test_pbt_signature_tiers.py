# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""pbt_signature_tiers: reading the gold-side evidence a passing reject rests on.

Every one of the four `_STUCK_*` screens in gates/pbt.py was written after an
audit agent read ONE build log and found a shape the previous screen missed --
and each time the corpus-wide question ("which other passing cells rest on this?")
had to be answered by grepping manifests for witness shapes, which is a proxy.
`gold_signature` made it measurable; this reporter is what reads it, so the
classification has to be trustworthy in both directions.

The signatures below are real build bytes, not invented shapes. The one that
matters most is `has type True`: it is a strong refutation wearing a tactic
error's clothes (`simp` PROVED the equation the witness assumed violated), and
filing it under "the script broke" would hide real refutations behind a tier that
reads as suspicious.
"""
from __future__ import annotations

from pbt_signature_tiers import TIERS, classify


def test_a_decided_claim_is_the_strongest_tier():
    """`decide` reporting the proposition false is exactly the evidence the gold
    half wants: the kernel evaluated the claim and rejected it."""
    assert classify("Tactic `decide` proved that the proposition "
                    'buildCheckStatementsTester ["group".toList] = false '
                    "is false") == "decided"
    assert classify("tactic `decide` proved that the proposition "
                    "countTester [1] = 3 is false") == "decided"


def test_a_hypothesis_reduced_to_True_is_a_refutation_not_a_broken_script():
    """The measured trap. `simp` reduced the witness's assumed-violated equation
    to `True` against gold, i.e. PROVED it, and the failure then surfaces as
    whatever step choked on the `True`. Reading the tactic name instead of the
    reduct files the strongest evidence in the corpus as noise."""
    assert classify("Application type mismatch: The argument hcon.left has type "
                    "True but is expected to have type fwdX (bwdX vx vy vz) = "
                    "fwdX vx vy vz") == "reduced"
    assert classify("Invalid field `symm`: The environment does not contain "
                    "`True.symm` h2 has type True") == "reduced"
    assert classify("unsolved goals call : ℤ h1 : coreUfunc call = Except.ok 0 "
                    "⊢ False") == "reduced"


def test_two_concrete_terms_shown_to_differ_is_its_own_tier():
    """Weaker than a decision but still evaluated: gold's actual value is on the
    page, so the claim was not merely unprovable, it was false of gold."""
    assert classify("Tactic `rfl` failed: The left-hand side pure [[0, 0, 0]] "
                    "is not definitionally equal to the right-hand side"
                    ) == "disagreed"
    assert classify("omega could not prove the goal: a possible counterexample "
                    "may satisfy the constraints a ≤ b") == "disagreed"


def test_a_structural_break_is_the_tier_that_needs_an_agent():
    """The script never reached gold's values, which is also what a hollow
    rejection looks like. Only builds can tell those apart, so this tier is a
    worklist, not a verdict."""
    assert classify("Tactic `introN` failed: There are no additional binders or "
                    "`let` bindings in the goal to introduce") == "shape"
    assert classify("Tactic `rewrite` failed: Did not find an occurrence of the "
                    'pattern if "b" = "a" then ?m.26') == "shape"


def test_a_stuck_screen_text_on_a_PASSING_case_is_flagged_not_absorbed():
    """This tier should be empty: those cases are failed by the gate. A hit means
    the whole-log `_stuck_screen` scan and the first-diagnostic signature
    disagreed on the same build, which is the asymmetry worth surfacing rather
    than filing under 'other'."""
    assert classify("Tactic `decide` failed ... its `Decidable` instance did not "
                    "reduce to `isTrue` or `isFalse`.") == "stuck"
    assert classify("failed to synthesize Decidable ¬{True}do let r ← forIn "
                    "Lean.Loop.mk") == "stuck"


def test_an_unrecorded_signature_is_not_silently_counted_as_evidence():
    """Records predating `gold_signature` carry no evidence at all. Folding them
    into any tier would report coverage the artifact does not have."""
    assert classify("") == "unrecorded"
    assert classify(None or "") == "unrecorded"


def test_an_unknown_shape_falls_through_rather_than_being_forced():
    """The tiers were written against real bytes and are extended the same way,
    so an unmatched signature has to be visible instead of absorbed into the
    nearest rule.

    This used "`simp` made no progress" until that shape was measured and given
    the `inert` tier of its own. Keeping it here would have pinned the example
    rather than the property, and would have failed the day the rule it asked for
    arrived.
    """
    assert classify("the elaborator emitted something nobody has read yet") == \
        "other"
    # and `inert` is a tier now, not a fall-through
    assert classify("`simp` made no progress") == "inert"


def test_the_tiers_are_ordered_strongest_first():
    """First match wins, so a signature that is BOTH a decision and a mismatch
    (Lean prints both often enough) must classify as the decision."""
    assert [t for t, _ in TIERS][:2] == ["decided", "reduced"]
    both = ("Application type mismatch ... `decide` proved that the proposition "
            "fTester 3 = false is false")
    assert classify(both) == "decided"
