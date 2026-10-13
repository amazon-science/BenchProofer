# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Refutation witnesses: the screens that run before the two builds.

Each forgery here would hold of the rival and fail of the solution file, clearing both
builds, so only a screen stops it.
"""

from __future__ import annotations

from benchproofer.core import witness
from benchproofer.registries import BACKENDS

LEAN = BACKENDS.get("lean4")
COMMENT = "--"

ACCEPTED = """\
-- benchproofer:begin spec
def Spec (n : Nat) (r : Nat) : Prop :=
  r = n + n
-- benchproofer:end spec

-- benchproofer:begin impl
def impl (n : Nat) : Nat :=
  2 * n
-- benchproofer:end impl

-- benchproofer:begin proof
theorem impl_meets_spec (n : Nat) : Spec n (impl n) := by
  unfold Spec impl
  omega
-- benchproofer:end proof
"""
#: The rival, which adds a helper of its own -- something a variant may legitimately do,
#: since the spec view elides the implementation region.
RIVAL = ACCEPTED.replace(
    "def impl (n : Nat) : Nat :=\n  2 * n",
    "def bump (n : Nat) : Nat := n + 1\n\ndef impl (n : Nat) : Nat :=\n  bump (2 * n)",
)
#: A real witness: it names the specification, and it is false of the solution file.
HONEST = "example : ¬ Spec 3 (impl 3) := by\n  unfold Spec impl\n  decide"


def test_a_case_with_no_witness_is_reported_as_having_none() -> None:
    assert witness.problems(None, COMMENT) == ["the case ships no witness"]
    assert witness.problems("   ", COMMENT) == ["the case ships no witness"]


def test_an_honest_witness_clears_every_screen() -> None:
    assert witness.problems(HONEST, COMMENT) == []
    assert witness.scope_problems(ACCEPTED, RIVAL, HONEST, LEAN) == []
    assert witness.anchor_problems(ACCEPTED, HONEST, LEAN) == []


def test_a_witness_that_assumes_its_own_conclusion_is_refused() -> None:
    """It would hold of the rival, which is the half the two builds ask for first."""
    forged = "axiom cheat : ¬ Spec 3 (impl 3)\nexample : ¬ Spec 3 (impl 3) := cheat"

    assert witness.problems(forged, COMMENT) == [
        "the witness uses 'axiom', so it would hold of anything"
    ]


def test_a_witness_that_decides_nothing_is_refused() -> None:
    assert witness.problems("-- the rival is wrong at 3\n", COMMENT) == [
        "the witness declares no `example`, `theorem` or `lemma` to decide"
    ]


def test_prose_may_discuss_a_banned_construct() -> None:
    """The screens read what the checker reads, as everywhere else in the tool."""
    explained = f"-- proved without sorry or any axiom\n{HONEST}"

    assert witness.problems(explained, COMMENT) == []


def test_a_witness_stated_over_a_name_only_the_rival_has_is_refused() -> None:
    """It fails of the solution file as an unknown name, establishing nothing."""
    tautology = "example : bump 0 = 1 := by decide"

    problems = witness.scope_problems(ACCEPTED, RIVAL, tautology, LEAN)

    assert len(problems) == 1
    assert "the witness names bump" in problems[0]


def test_a_name_the_witness_brings_with_it_is_its_own() -> None:
    """The witness is appended to both files, so what it declares exists on both sides."""
    own = f"def bump (n : Nat) : Nat := n + 1\n\n{HONEST}"

    assert witness.scope_problems(ACCEPTED, RIVAL, own, LEAN) == []


def test_a_witness_that_only_tells_the_two_implementations_apart_is_refused() -> None:
    """A difference is not a violation, and this is the inference the rule replaces."""
    difference = "example : impl 3 = 7 := by decide"

    problems = witness.anchor_problems(ACCEPTED, difference, LEAN)

    assert len(problems) == 1
    assert "mentions none of Spec" in problems[0]


def test_the_specification_has_to_be_named_in_the_statement_not_the_proof() -> None:
    """`unfold Spec` in a tactic block is routine and says nothing about the claim."""
    padded = "example : impl 3 = 7 := by\n  unfold Spec impl\n  decide"

    assert witness.anchor_problems(ACCEPTED, padded, LEAN) != []


def test_a_file_whose_spec_region_declares_nothing_is_not_held_to_an_anchor() -> None:
    """A shape this does not model, where silence beats refusing every witness."""
    bare = ACCEPTED.replace("def Spec (n : Nat) (r : Nat) : Prop :=\n  r = n + n", "-- TODO")

    assert witness.anchor_problems(bare, "example : True := trivial", LEAN) == []


#: A specification whose clause is an equation against a helper, as a Velvet `ensures`
#: must be and a Lean one often is: it says what it says through `doubled`, and
#: `carried` in turn.
THROUGH_A_HELPER = """\
-- benchproofer:begin helpers
def carried (n : Nat) : Nat :=
  n + n

def doubled (n : Nat) : Nat :=
  carried n

def unrelated (n : Nat) : Nat :=
  n * n
-- benchproofer:end helpers

-- benchproofer:begin spec
def Spec (n : Nat) (r : Nat) : Prop :=
  r = doubled n
-- benchproofer:end spec

-- benchproofer:begin impl
def impl (n : Nat) : Nat :=
  2 * n
-- benchproofer:end impl

-- benchproofer:begin proof
theorem impl_meets_spec (n : Nat) : Spec n (impl n) := by
  unfold Spec impl doubled carried
  omega
-- benchproofer:end proof
"""


def test_a_claim_about_what_the_specification_is_written_in_terms_of_is_about_it() -> None:
    """A witness stated over the helper the clause uses is about the specification."""
    reachable = witness.anchors(THROUGH_A_HELPER, LEAN)

    assert {"Spec", "doubled", "carried"} <= reachable
    assert "unrelated" not in reachable
    assert "impl" not in reachable
    assert (
        witness.anchor_problems(
            THROUGH_A_HELPER, "example : ¬ doubled 3 = 6 := by decide", LEAN
        )
        == []
    )


def test_a_helper_the_specification_never_mentions_is_not_an_anchor() -> None:
    """Then a claim about it tells the two implementations apart and nothing more."""
    problems = witness.anchor_problems(
        THROUGH_A_HELPER, "example : unrelated 3 = 9 := by decide", LEAN
    )

    assert len(problems) == 1
    assert "mentions none of" in problems[0]


def test_the_probe_puts_the_witness_where_the_shipped_proof_was() -> None:
    """Otherwise the shipped tactic, which fails for any reshaped rival, fails first."""
    probed = witness.probe(RIVAL, HONEST, LEAN)

    assert "theorem impl_meets_spec" not in probed
    assert probed.endswith(HONEST + "\n")
    assert "def Spec" in probed and "def bump" in probed


def test_a_diagnostic_command_goes_with_the_proof_it_reports_on() -> None:
    """Left in, it fails on the emptied proof's name, as if the witness did not hold."""
    reporting = ACCEPTED + "\n#print axioms impl_meets_spec\n"

    probed = witness.probe(reporting, HONEST, LEAN)

    assert "#print axioms" not in probed


def test_a_witness_binds_nothing() -> None:
    """A claim at one input assumes nothing: a hypothesis could assume its conclusion."""
    claim = (
        "example (h₀ : impl 3 = 6) (h₁ : (impl 1) = 2) :\n"
        "    ¬ Spec 3 (impl 3) := by\n  unfold Spec impl\n  decide"
    )

    assert witness.binders(claim, COMMENT) == ["(h₀ : impl 3 = 6)", "(h₁ : (impl 1) = 2)"]
    assert witness.hypothesis_problems(HONEST, LEAN) == []
    for binder in ("(n : Nat)", "{T : Type}", "(h : False)", "[inst : Inhabited Nat]"):
        claim = f"theorem w {binder} : ¬ Spec 3 (impl 3) := by\n  decide"

        (problem,) = witness.hypothesis_problems(claim, LEAN)
        assert binder in problem and "binds no hypothesis and no value" in problem


def test_drafting_and_the_gates_refuse_a_witness_by_the_same_screens() -> None:
    """A screen drafting skipped is a proof session spent on a witness the gate refuses."""
    tactic = BACKENDS.get("lean4")
    accepted = (
        "-- benchproofer:begin axioms\n-- benchproofer:axiom pkg.fetch\n"
        "opaque fetch : Nat → Nat\n-- benchproofer:models pkg.double\n"
        "def double (n : Nat) : Nat := n + n\n-- benchproofer:end axioms\n"
        "-- benchproofer:begin spec\ndef spec (n : Nat) : Prop := fetch n = n\n"
        "-- benchproofer:end spec\n-- benchproofer:begin impl\ndef f (n : Nat) := n\n"
        "-- benchproofer:end impl\n"
    )
    assuming = "example (h : fetch 3 = 4) : ¬ spec 3 := by simp [spec, h]"

    assert witness.objections(accepted, accepted, assuming, tactic) == (
        witness.hypothesis_problems(assuming, tactic)
    )
    assert witness.objections(accepted, accepted, assuming, tactic)
    assert witness.unassumable(accepted, tactic) == ("fetch",)
