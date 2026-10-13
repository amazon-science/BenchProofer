# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""variant_scope: what a G-PBT case may change — no verifier, no docker.

These are soundness regression tests. Each `test_rejects_*` encodes a variant
that passes `markers.same_spec` yet neuters the obligation it claims to test;
before variant_scope existed, every one of them elaborated cleanly and would
have recorded a G-PBT pass on an `expect="verify"` case. The `test_accepts_*`
tests pin the other side: the rules must not reject a legitimate reprove, or
they would block the port they exist to protect.
"""
from __future__ import annotations

import dataclasses

import pytest

from swebench_unified.backends import get_backend
from swebench_unified.markers import same_spec
from swebench_unified.variant_scope import (
    _KNOWN_FLAVORS,
    _axiom_names,
    _decl_names,
    frozen_self_check,
    impl_region_only,
    is_admissible_variant,
    lean_obligations,
    unsound_evasions,
    variant_problems,
)

LEAN = """\
import Mathlib
-- imports-end

-- pure-start
def zeroRow (n : Nat) : List Nat := List.replicate n 0
-- pure-end

-- post-conditions-start
def problem_spec_count (r : Nat) (x : Nat) : Prop := r = x + 1
-- post-conditions-end

-- impl-start
def implementation_count (x : Nat) : Nat := x + 1
-- impl-end

-- proof-start
theorem correct_count (x : Nat) :
    problem_spec_count (implementation_count x) x := by
  rfl
-- proof-end
"""

VELVET = """\
import Velvet.Std
-- imports-end

-- pure-start
def bump (x : Nat) : Nat := x + 1
-- pure-end

-- pre-conditions-start
-- pre-conditions-end
-- post-conditions-start
-- post-conditions-end

method countUp (x : Nat) return (r : Nat)
  ensures r = bump x
  do
    -- impl-start
    return x + 1
    -- impl-end

prove_correct countUp by
  loom_solve
"""

NAGINI = """\
from nagini_contracts.contracts import *


# post-conditions-start
@Pure
def expected(x: int) -> int:
    return x + 1
# post-conditions-end


def impl(x: int) -> int:
    # pre-conditions-start
    Requires(x >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() == expected(x))
    # post-conditions-end
    # impl-start
    return 1 + x
    # impl-end
"""

# The unique impl-region anchor (the spec helper says `return x + 1`, so an
# impl edit must not reuse that text or it would rewrite the spec too).
NAGINI_IMPL = "    return 1 + x"


@pytest.fixture()
def lean():
    return get_backend("lean").language


@pytest.fixture()
def velvet():
    return get_backend("velvet").language


@pytest.fixture()
def nagini():
    return get_backend("nagini").language


def swap_region(src: str, start: str, end: str, body: str) -> str:
    """Replace the text between two markers (markers themselves kept)."""
    i, j = src.index(start), src.index(end)
    return src[:i] + start + "\n" + body + src[j:]


# ---------------------------------------------------------------------------
# the frozen source is always admissible against itself
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("src,fixture", [(LEAN, "lean"), (VELVET, "velvet"),
                                        (NAGINI, "nagini")])
def test_frozen_self_check_is_clean(src, fixture, request):
    tables = request.getfixturevalue(fixture)
    assert frozen_self_check(src, tables) == []


# ---------------------------------------------------------------------------
# lean: the obligation statement must survive
# ---------------------------------------------------------------------------

def test_rejects_gutted_obligation(lean):
    """`theorem correct_count : True := trivial` passes same_spec (the proof
    region is elided) and elaborates — the original false-SOUND channel."""
    bad = swap_region(LEAN, "-- proof-start", "-- proof-end",
                      "theorem correct_count : True := trivial\n")
    assert same_spec(LEAN, bad, lean), "precondition: same_spec is fooled"
    problems = variant_problems(LEAN, bad, lean)
    assert problems and "statement was rewritten" in problems[0]


def test_rejects_deleted_obligation(lean):
    bad = swap_region(LEAN, "-- proof-start", "-- proof-end", "")
    assert same_spec(LEAN, bad, lean)
    assert any("is missing" in p for p in variant_problems(LEAN, bad, lean))


def test_rejects_retyped_obligation(lean):
    bad = swap_region(LEAN, "-- proof-start", "-- proof-end",
                      "theorem correct_count : 1 = 1 := rfl\n")
    assert any("statement was rewritten" in p
               for p in variant_problems(LEAN, bad, lean))


def test_rejects_weakened_obligation_binder(lean):
    """Dropping a hypothesis/binder from the statement is a rewrite, even
    though the theorem name and shape look right."""
    bad = LEAN.replace("theorem correct_count (x : Nat) :",
                       "theorem correct_count (x : Nat) (h : x = 0) :")
    assert any("statement was rewritten" in p
               for p in variant_problems(LEAN, bad, lean))


def test_rejects_new_axiom(lean):
    bad = LEAN.replace("-- proof-start", "-- proof-start\naxiom cheat : False", 1)
    assert any("new axiom" in p for p in variant_problems(LEAN, bad, lean))


def test_rejects_sorry_in_proof(lean):
    bad = LEAN.replace("  rfl", "  sorry")
    assert any("sorry" in p for p in variant_problems(LEAN, bad, lean))


def test_rejects_new_theorem_hidden_in_impl_region(lean):
    """The impl region is elided too, so a trivializing declaration can hide
    there just as well as in the proof region."""
    bad = LEAN.replace("-- impl-end",
                       "theorem sneaky : True := trivial\n-- impl-end")
    assert any("new theorem/lemma" in p for p in variant_problems(LEAN, bad, lean))


def test_helper_lemma_is_scope_creep_for_a_variant_but_not_unsound(lean):
    """The one rule the two callers must differ on.

    A battery variant reproves the SAME obligations, so a fresh declaration is
    scope creep and `variant_problems` rejects it. An audit attack is an
    independent rival implementation and may legitimately need a helper lemma to
    prove itself, so `unsound_evasions` must not reject it: doing so would retire
    a real counterexample and record a weakness search that never happened.
    """
    helper = LEAN.replace("-- impl-end",
                          "lemma helper (n : Nat) : n + 0 = n := by simp\n-- impl-end")
    assert any("new theorem/lemma" in p for p in variant_problems(LEAN, helper, lean))
    assert unsound_evasions(LEAN, helper, lean) == []


def test_unsound_evasions_still_catches_assuming(lean):
    """What the attack path does keep: an exit code that was assumed, not earned."""
    assert any("sorry" in p
               for p in unsound_evasions(LEAN, LEAN.replace("  rfl", "  sorry"), lean))
    dropped = LEAN.replace("theorem correct_count", "theorem renamed_count")
    assert any("is missing" in p for p in unsound_evasions(LEAN, dropped, lean))


def test_rejects_native_decide(lean):
    bad = LEAN.replace("  rfl", "  native_decide")
    assert any("native_decide" in p for p in variant_problems(LEAN, bad, lean))


# ---------------------------------------------------------------------------
# lean: legitimate reproves stay admissible
# ---------------------------------------------------------------------------

def test_accepts_different_impl_same_proof(lean):
    ok = LEAN.replace("def implementation_count (x : Nat) : Nat := x + 1",
                      "def implementation_count (x : Nat) : Nat := 1 + x")
    assert is_admissible_variant(LEAN, ok, lean)


def test_accepts_reproved_obligation_with_different_tactics(lean):
    """A soundness positive with a structurally different impl legitimately
    needs a different proof BODY. Only the statement is pinned."""
    ok = LEAN.replace("def implementation_count (x : Nat) : Nat := x + 1",
                      "def implementation_count (x : Nat) : Nat := 1 + x")
    ok = ok.replace("  rfl", "  unfold problem_spec_count implementation_count\n  omega")
    assert is_admissible_variant(LEAN, ok, lean)


def test_accepts_recommented_proof(lean):
    ok = LEAN.replace("  rfl", "  -- reprove after the reshape\n  rfl")
    assert is_admissible_variant(LEAN, ok, lean)


def test_accepts_reindented_obligation(lean):
    """Whitespace in the statement is normalized: a reflow is not a rewrite."""
    ok = LEAN.replace("theorem correct_count (x : Nat) :\n"
                      "    problem_spec_count (implementation_count x) x := by",
                      "theorem correct_count (x : Nat)\n"
                      "    : problem_spec_count (implementation_count x) x := by")
    assert is_admissible_variant(LEAN, ok, lean)


def test_obligation_extraction(lean):
    obl = lean_obligations(LEAN)
    assert list(obl) == ["correct_count"]
    assert "problem_spec_count" in obl["correct_count"]
    assert ":=" not in obl["correct_count"]


# ---------------------------------------------------------------------------
# velvet: the obligation lives in the spec view, but must still be present
# ---------------------------------------------------------------------------

def test_velvet_rejects_missing_prove_correct(velvet):
    bad = VELVET[:VELVET.index("prove_correct")]
    assert any("prove_correct" in p for p in variant_problems(VELVET, bad, velvet))


def test_velvet_rejects_sorry_body(velvet):
    bad = VELVET.replace("  loom_solve", "  sorry")
    assert any("sorry" in p for p in variant_problems(VELVET, bad, velvet))


def test_velvet_accepts_different_impl(velvet):
    ok = VELVET.replace("    return x + 1", "    let y := x + 1\n    return y")
    assert is_admissible_variant(VELVET, ok, velvet)


def test_velvet_ensures_tampering_still_caught_by_same_spec(velvet):
    """Sanity: velvet's obligation is in the spec view, so same_spec already
    catches this. The scope check must agree, not contradict."""
    bad = VELVET.replace("  ensures r = bump x", "  ensures True")
    assert not same_spec(VELVET, bad, velvet)
    assert any("same_spec" in p for p in variant_problems(VELVET, bad, velvet))


# ---------------------------------------------------------------------------
# nagini: an injected @ContractOnly assumes rather than proves
# ---------------------------------------------------------------------------

def test_nagini_rejects_injected_contract_only(nagini):
    bad = NAGINI.replace(
        "    # impl-start\n",
        "    # impl-start\n"
        "    @ContractOnly\n"
        "    def _oracle(a):\n"
        "        # type: (int) -> int\n"
        "        Ensures(Result() == 999)\n"
        "        pass\n")
    assert same_spec(NAGINI, bad, nagini), "precondition: same_spec is fooled"
    assert any("@ContractOnly" in p for p in variant_problems(NAGINI, bad, nagini))


def test_nagini_rejects_assume(nagini):
    bad = NAGINI.replace(NAGINI_IMPL, "    Assume(False)\n" + NAGINI_IMPL)
    assert any("Assume" in p for p in variant_problems(NAGINI, bad, nagini))


def test_nagini_accepts_reshaped_impl(nagini):
    ok = NAGINI.replace(NAGINI_IMPL, "    y = 1 + x\n    return y")
    assert is_admissible_variant(NAGINI, ok, nagini)


# ---------------------------------------------------------------------------
# identifier-boundary matching: real bundles contain `admit_parser` and
# `instance_admits_namespace`; a substring scan rejected both.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ident", ["admit_parser", "instance_admits_namespace",
                                   "sorry_count", "admitted_rows"])
def test_tokens_match_on_identifier_boundaries(nagini, ident):
    ok = NAGINI.replace(NAGINI_IMPL,
                        f"    {ident} = 1 + x\n    return {ident}")
    assert is_admissible_variant(NAGINI, ok, nagini), \
        f"{ident} must not read as an assumption token"


def test_frozen_usage_of_a_token_is_not_a_delta(lean):
    """If the frozen bundle legitimately uses a token, a variant may too —
    the rule bans INTRODUCING one, so it never rejects what G-HYGIENE
    already accepted."""
    frozen = LEAN.replace("  rfl", "  native_decide")
    variant = frozen.replace("def implementation_count (x : Nat) : Nat := x + 1",
                             "def implementation_count (x : Nat) : Nat := 1 + x")
    assert is_admissible_variant(frozen, variant, lean)


# ---------------------------------------------------------------------------
# impl_region_only — reported, not required
# ---------------------------------------------------------------------------

def test_impl_region_only_true_for_impl_edit(lean):
    ok = LEAN.replace("def implementation_count (x : Nat) : Nat := x + 1",
                      "def implementation_count (x : Nat) : Nat := 1 + x")
    assert impl_region_only(LEAN, ok, lean)


def test_impl_region_only_false_when_proof_also_changes(lean):
    ok = LEAN.replace("  rfl", "  omega")
    assert not impl_region_only(LEAN, ok, lean)


# ---------------------------------------------------------------------------
# the flavor dispatch, and the certification argument that rests on it
# ---------------------------------------------------------------------------

def test_every_registered_backend_has_rules_here():
    """An empty return from this module means ADMISSIBLE, so a flavor with no
    branch would report every same-spec rival of its bundles sound with no rule
    having run. The dispatch raises instead -- which makes this list the promise
    that each flavor's way of discharging an obligation is covered, and makes a
    backend added without a branch fail here rather than in a green verdict.

    `pbt_certify._RELAXATIONS["120317cd9"]` also stands on it: that commit's
    exemption is unconditional because the guard it added can only fire on a
    flavor outside this list, so the premise has to be checked and not assumed.
    """
    for name in ("nagini", "velvet", "lean", "ears"):
        flavor = get_backend(name).language.flavor
        assert flavor in _KNOWN_FLAVORS, f"{name}: {flavor} has no rules"


def test_an_unregistered_flavor_raises_rather_than_passing_everything(lean):
    """The failure mode the dispatch exists to prevent, at all three points."""
    unknown = dataclasses.replace(lean, flavor="coq")
    for call in (lambda: _decl_names("", unknown),
                 lambda: _axiom_names("", unknown),
                 lambda: unsound_evasions(LEAN, LEAN, unknown)):
        with pytest.raises(ValueError, match="unknown language flavor"):
            call()
