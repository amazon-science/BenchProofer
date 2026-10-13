# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The determinism lemma's generated statement, and the demand that asks the checker for it.

The statement is the tool's, not the bundle's, which does not state the lemma at all: one
named `spec_is_deterministic` proving `True` would be worth nothing. A shape this cannot
read has no statement rather than a guessed one.
"""

from __future__ import annotations

import pytest

from benchproofer.core import determinism
from benchproofer.registries import BACKENDS

LEAN = BACKENDS.get("lean4")

FUNCTIONAL = """\
-- benchproofer:begin helpers
def carried (n : Nat) : Nat :=
  n + n
-- benchproofer:end helpers

-- benchproofer:begin spec
def Spec (n : Nat) (flag : Bool) (result : Option Nat) : Prop :=
  result = (if flag then some (carried n) else none)
-- benchproofer:end spec

-- benchproofer:begin impl
def impl (n : Nat) (flag : Bool) : Option Nat :=
  if flag then some (2 * n) else none
-- benchproofer:end impl

-- benchproofer:begin proof
theorem impl_meets_spec (n : Nat) (flag : Bool) : Spec n flag (impl n flag) := by
  unfold Spec impl carried
  cases flag <;> simp <;> omega
-- benchproofer:end proof
"""


STATED = "∀ x1 x2 r1 r2, Spec x1 x2 r1 → Spec x1 x2 r2 → r1 = r2"


@pytest.mark.parametrize(
    ("old", "new", "stated"),
    [
        ("", "", STATED),
        ("(result : Option Nat) : Prop", "(result : Option (List Nat)) : Prop", STATED),
        (
            "def Spec (n : Nat) (flag : Bool) (result",
            "def Spec (result",
            "∀ r1 r2, Spec r1 → Spec r2 → r1 = r2",
        ),
        (
            "(n : Nat) (flag : Bool) (result",
            "{n : Nat} (flag : Bool) (result",
            "∀ x1 r1 r2, Spec x1 r1 → Spec x1 r2 → r1 = r2",
        ),
        (
            "-- benchproofer:begin spec\n",
            "-- benchproofer:begin spec\n"
            "def Acceptable (n : Nat) (ok : Prop) : Prop :=\n  ok\n\n",
            STATED,
        ),
        ("def Spec", "noncomputable def Spec", STATED),
    ],
    ids=[
        "as shipped",
        "a parenthesized type",
        "no input",
        "an implicit binder",
        "a helper",
        "a noncomputable predicate",
    ],
)
def test_the_statement_binds_one_fresh_name_per_explicit_input(
    old: str, new: str, stated: str
) -> None:
    """The predicate applied to each input and to two results, which are equal.

    A binder whose type has parentheses is one binder, an implicit one is the checker's to
    fill in, and of several predicates the one stated is the one the proof region's claim
    is about.
    """
    assert determinism.statement(FUNCTIONAL.replace(old, new), LEAN) == stated


#: A precondition over the inputs, a predicate of its own beside the specification.
PRECONDITIONED = FUNCTIONAL.replace(
    "-- benchproofer:begin spec\n",
    "-- benchproofer:begin spec\ndef Valid (n : Nat) : Prop :=\n  n < 100\n\n",
)


@pytest.mark.parametrize(
    "claim",
    [
        "(n : Nat) (flag : Bool) (h : Valid n) :\n    Spec n flag (impl n flag)",
        "(flag : Bool) : ∀ n, Valid n → Spec n flag (impl n flag)",
        "(flag : Bool) : ∀ n : Nat, Valid n -> Spec n flag (impl n flag)",
    ],
    ids=["a hypothesis binder", "an implication", "an ASCII arrow"],
)
def test_a_precondition_a_claim_takes_as_a_hypothesis_is_not_a_specification(
    claim: str,
) -> None:
    """The specification is the predicate the claim concludes, not one it assumes.

    A precondition has no result, so a lemma over it would demand that any two inputs it
    admits are equal.
    """
    solution = PRECONDITIONED.replace(
        "(n : Nat) (flag : Bool) : Spec n flag (impl n flag)", claim
    )

    assert f"theorem impl_meets_spec {claim} := by" in solution
    assert determinism.statement(solution, LEAN) == STATED


METHOD = FUNCTIONAL.replace(
    "def Spec (n : Nat) (flag : Bool) (result : Option Nat) : Prop :=\n"
    "  result = (if flag then some (carried n) else none)",
    "method spec (n : Nat) return (out : Option Nat)\n  ensures out = some (carried n)",
)
CONTRACT = (
    "# benchproofer:begin spec\n"
    "def impl(cents: int) -> int:\n"
    "    Requires(cents >= 0)\n"
    "    Ensures(Result() == cents)\n"
    "# benchproofer:end spec\n"
    "# benchproofer:begin impl\n    return cents\n# benchproofer:end impl\n"
)
TWO_CLAIMED = FUNCTIONAL.replace(
    "-- benchproofer:begin spec\n",
    "-- benchproofer:begin spec\ndef Other (n : Nat) (result : Nat) : Prop :=\n"
    "  result = n\n\n",
).replace("Spec n flag (impl n flag)", "Spec n flag (impl n flag) ∧ Other n n")


#: Two predicates no claim of the proof region names, so neither is the specification.
UNCLAIMED = TWO_CLAIMED.replace(
    "theorem impl_meets_spec (n : Nat) (flag : Bool) : Spec n flag (impl n flag) ∧ Other n n",
    "theorem impl_meets_spec (n : Nat) (flag : Bool) : impl n flag = impl n flag",
)


@pytest.mark.parametrize(
    ("solution", "backend"),
    [
        (METHOD, "lean4"),
        (FUNCTIONAL, "falsifier"),
        (CONTRACT, "nagini"),
        (UNCLAIMED, "lean4"),
        (
            TWO_CLAIMED.replace("def Other (n : Nat) (result : Nat)", "def Other {n : Nat}"),
            "lean4",
        ),
    ],
    ids=[
        "a method contract",
        "no proof",
        "a Nagini contract",
        "two predicates no claim names",
        "a claimed predicate with no explicit binder",
    ],
)
def test_a_shape_with_no_predicate_to_state_it_over_has_no_statement(
    solution: str, backend: str
) -> None:
    """A contract names no postcondition constant, and a falsifier has no lemma to check.

    Of two predicates no claim names, either may be a helper, and a lemma about a helper
    would answer a question nobody asked; a predicate with no explicit binder has no result.
    """
    assert determinism.statement(solution, BACKENDS.get(backend)) == ""


def test_each_predicate_a_claim_is_stated_over_gets_a_conjunct_of_its_own() -> None:
    """A specification of two functions pins both results, each over its own inputs.

    The demand is one example per conjunct, so the file is accepted only where every
    predicate admits one result per input, and each is offered the bundle's claims.
    """
    other = "∀ x1 r1 r2, Other x1 r1 → Other x1 r2 → r1 = r2"

    asked = determinism.derived(TWO_CLAIMED, LEAN)

    assert determinism.statement(TWO_CLAIMED, LEAN) == f"({other}) ∧ ({STATED})"
    assert f"example :\n    {other} := by\n  intro x1 r1 r2 h1 h2" in asked
    assert f"example :\n    {STATED} := by\n  intro x1 x2 r1 r2 h1 h2" in asked
    assert "(exact impl_meets_spec x1 r1 r2 h1 h2; done)" in asked
    assert "(simp only [Other] at h1 h2; subst_vars; rfl)" in asked


def test_the_demand_offers_every_claim_the_proof_region_states_and_then_tactics() -> None:
    """Which of them proves it is the checker's to say, so no naming convention is needed.

    The bundle does not state the lemma, so the demand does not rest on one being there: a
    claim the file happens to prove is tried first because it is cheap, and a fixed list of
    tactics after it.
    """
    two = FUNCTIONAL.replace(
        "-- benchproofer:end proof",
        "\nlemma pinned (n : Nat) (flag : Bool) (r : Option Nat) :\n"
        "    Spec n flag r → r = impl n flag := by\n  unfold Spec impl carried; cases flag "
        "<;> simp <;> omega\n-- benchproofer:end proof",
    )

    asked = determinism.derived(two, LEAN)

    assert determinism.claimants(two, LEAN) == ("impl_meets_spec", "pinned")
    assert "(exact pinned x1 x2 r1 r2 h1 h2; done)" in asked
    assert "((rw [pinned x1 x2 r1 h1, pinned x1 x2 r2 h2]); done)" in asked
    assert "simp only [Spec] at h1 h2" in asked
    # The file is asked for a term of the generated type, with everything it wrote kept.
    assert f"{STATED} := by" in asked
    assert asked.startswith(two.rstrip()[:200])


def test_a_proof_region_that_assumes_its_claim_is_offered_nothing() -> None:
    """A determinism lemma resting on an assumption says every implementation is refused."""
    stubbed = FUNCTIONAL.replace("cases flag <;> simp <;> omega", "sorry")

    assert determinism.derived(stubbed, LEAN) == ""


def test_a_proof_region_stating_no_claim_is_still_asked_by_tactic() -> None:
    """The lemma is the gate's to prove, so a bundle that states none is still asked."""
    bare = FUNCTIONAL.replace("theorem impl_meets_spec", "def impl_meets_spec")

    assert determinism.statement(bare, LEAN) != ""
    assert determinism.claimants(bare, LEAN) == ()
    assert f"{STATED} := by" in determinism.derived(bare, LEAN)
