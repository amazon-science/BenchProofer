# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""pbt_witness: making a G-PBT rejection attributable to the spec.

The channel these tests pin is real, not hypothetical: a CORRECT commuted-`&&`
rival and a WRONG conjunct-dropping rival both exit 1 with `Tactic 'rfl' failed`,
on lean and velvet alike. Without a witness the gate reads both as "rejected as
expected" and reports SOUND, so every ported reject case would pass vacuously.

No verifier here: these cover the file surgery and the shape check. The
two-build discrimination itself is exercised by the gate.
"""
from __future__ import annotations

import pytest

from swebench_unified.backends import get_backend
from swebench_unified.backends.registry import GATED_BACKENDS
from swebench_unified.pbt_witness import (
    WITNESS_REQUIRED,
    all_witness_head_binders,
    consistency_probe,
    witness_file,
    witness_head_binders,
    witness_problems,
    witness_scope_problems,
)

LEAN = """\
import Mathlib
-- imports-end

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
  loom_solve <;> simp [bump]

method other (y : Nat) return (r : Nat)
  ensures r = y
  do
    -- impl-start
    return y
    -- impl-end

prove_correct other by
  loom_solve
"""

WITNESS = """\
example : ¬ problem_spec_count (implementation_count 3) 3 := by
  unfold problem_spec_count implementation_count
  decide
"""


@pytest.fixture()
def lean():
    return get_backend("lean").language


@pytest.fixture()
def velvet():
    return get_backend("velvet").language


# ---------------------------------------------------------------------------
# which backends require a witness
# ---------------------------------------------------------------------------

def test_nagini_is_exempt():
    """Viper discharges the postcondition itself, so on nagini "did not
    verify" really is a spec verdict, and its reject cases carry no witness."""
    assert "nagini" not in WITNESS_REQUIRED
    # Every OTHER gated backend needs one: a proof backend added to the registry
    # without a witness decision has to fail here, not be exempted by default.
    assert set(WITNESS_REQUIRED) == set(GATED_BACKENDS) - {"nagini"}


# ---------------------------------------------------------------------------
# lean: the proof region is emptied so no tactic script can mask the witness
# ---------------------------------------------------------------------------

def test_lean_witness_file_drops_the_obligation(lean):
    out = witness_file(LEAN, WITNESS, lean)
    assert "theorem correct_count" not in out
    assert "rfl" not in out
    # the spec and impl must survive — the witness is stated against them
    assert "def problem_spec_count" in out
    assert "def implementation_count" in out
    assert out.rstrip().endswith("decide")


def test_lean_witness_file_keeps_region_markers(lean):
    """Markers are kept so the result still parses as a bundle solution file
    (parse_regions runs on it downstream)."""
    from swebench_unified.markers import parse_regions
    out = witness_file(LEAN, WITNESS, lean)
    regions = parse_regions(out, lean)
    assert regions.ok, regions.errors
    assert regions.get("proof")


# ---------------------------------------------------------------------------
# velvet: prove_correct blocks are removed, headers and all
# ---------------------------------------------------------------------------

def test_velvet_witness_file_drops_every_prove_correct(velvet):
    out = witness_file(VELVET, "example : True := trivial", velvet)
    assert "prove_correct" not in out
    assert "loom_solve" not in out
    # both methods and their ensures clauses survive
    assert out.count("method ") == 2
    assert "ensures r = bump x" in out
    assert "ensures r = y" in out


def test_velvet_stripping_stops_at_the_next_command(velvet):
    """The tactic block is delimited by indentation; a greedy strip would eat
    the following `method` and silently shrink the file under test."""
    out = witness_file(VELVET, "example : True := trivial", velvet)
    assert "method other (y : Nat) return (r : Nat)" in out


# ---------------------------------------------------------------------------
# what else has to go with the obligations
# ---------------------------------------------------------------------------

def test_a_print_axioms_on_the_dropped_theorem_goes_too(lean):
    """A lean bundle may end with `#print axioms correct_<name>`. The theorem it
    names lives in the proof region, so keeping the command in a file where that
    region is emptied makes Lean report `Unknown constant` — the RIVAL build
    fails and the gate blames the witness (`witness-unproven`) for a file it
    never got to judge."""
    src = LEAN + "\n#print axioms correct_count\n"
    out = witness_file(src, WITNESS, lean)
    assert "#print axioms" not in out
    assert "correct_count" not in out
    assert "def problem_spec_count" in out


@pytest.mark.parametrize("cmd", ["#check implementation_count",
                                 "#eval implementation_count 3",
                                 "#print axioms correct_count"])
def test_every_hash_command_goes(cmd, lean):
    """They are all diagnostics — none contributes to what the witness asserts,
    and any of them can fail the build for reasons that have nothing to do with
    the witness."""
    out = witness_file(LEAN + f"\n{cmd}\n", WITNESS, lean)
    assert cmd not in out


def test_a_hash_inside_a_declaration_survives(lean):
    """Only TOP-LEVEL commands are diagnostics. `Nat.succ#foo`-style tokens and
    anything indented under a declaration are code, and dropping a line from the
    middle of a definition would break the file it is meant to repair."""
    src = LEAN.replace("def implementation_count (x : Nat) : Nat := x + 1",
                       "def implementation_count (x : Nat) : Nat :=\n"
                       "  -- #check is discussed here, not run\n"
                       "  x + 1")
    out = witness_file(src, WITNESS, lean)
    assert "x + 1" in out
    assert "#check is discussed here" in out


_VELVET_COL0 = """\
import Velvet.Std
-- imports-end

-- pure-start
def bump (x : Nat) : Nat := x + 1
-- pure-end

method countUp (x : Nat) return (r : Nat)
  ensures r = bump x
  do
    -- impl-start
    return x + 1
    -- impl-end
  termination_by x
  decreasing_by
    all_goals omega

prove_correct countUp
termination_by x
decreasing_by
  all_goals (try simp_wf)
  all_goals omega
by
  loom_solve <;> simp [bump]

def afterwards : Nat := 7
"""


def test_a_column_zero_prove_correct_clause_goes_with_its_block(velvet):
    """Lean lets a `prove_correct`'s own `termination_by`/`decreasing_by`/`by`
    clauses sit at column 0. Stopping the strip at the first column-0 line
    orphans them, and the witness file then fails to PARSE for both builds —
    recorded as `witness-unproven` for a witness never tried."""
    out = witness_file(_VELVET_COL0, "example : True := trivial", velvet)
    assert "prove_correct" not in out
    assert "loom_solve" not in out
    bare = [ln for ln in out.splitlines()
            if ln.startswith(("termination_by", "decreasing_by")) or ln == "by"]
    assert bare == [], f"orphaned clause(s): {bare}"


def test_the_methods_own_termination_clause_survives(velvet):
    """Same keywords, different owner. The METHOD's `termination_by` is indented
    under it and is part of the definition the witness is stated against;
    dropping it would leave a recursive method with no termination argument."""
    out = witness_file(_VELVET_COL0, "example : True := trivial", velvet)
    assert "  termination_by x" in out
    assert "  decreasing_by" in out


def test_stripping_resumes_after_the_column_zero_clauses(velvet):
    """The clauses are consumed, not treated as "skip until something indented":
    the next real declaration must come back."""
    out = witness_file(_VELVET_COL0, "example : True := trivial", velvet)
    assert "def afterwards : Nat := 7" in out


def test_witness_file_rejects_python_flavor():
    with pytest.raises(ValueError):
        witness_file("x = 1\n", "example : True := trivial",
                     get_backend("nagini").language)


# ---------------------------------------------------------------------------
# witness shape: it must assert something a build can actually refute
# ---------------------------------------------------------------------------

def test_accepts_a_real_witness():
    assert witness_problems(WITNESS) == []


@pytest.mark.parametrize("bad", [None, "", "   ", 42, ["example"]])
def test_rejects_missing_witness(bad):
    assert witness_problems(bad)


def test_rejects_witness_with_no_declaration():
    assert witness_problems("-- I promise the rival is wrong\n#check Nat")


@pytest.mark.parametrize("tok", ["sorry", "admit", "native_decide"])
def test_rejects_witness_that_assumes(tok):
    """`sorry` would let ANY statement elaborate, so it defeats both halves of
    the check at once: it would hold of the rival and of gold."""
    problems = witness_problems(f"example : False := by\n  {tok}\n")
    assert problems and tok in problems[0]


@pytest.mark.parametrize("decl", ["axiom", "opaque"])
def test_rejects_witness_that_postulates_its_own_conclusion(decl):
    """The forgery an adversarial audit found: state the refutation as an
    assumption, then discharge the `example` with it. It elaborates against
    gold too, so the gate would eventually record `witness-vacuous`, but the
    shape check is free and catches it before two builds are spent."""
    problems = witness_problems(
        f"{decl} cheat : rivalTester 1 = false\n"
        "example : rivalTester 1 = false := cheat\n")
    assert problems and decl in problems[0]


@pytest.mark.parametrize("tok", ["unsafe", "extern", "implemented_by"])
def test_rejects_witness_that_escapes_the_kernel(tok):
    assert witness_problems(f"example : False := by\n  exact {tok}Thing\n") or \
        witness_problems(f"{tok} foo : False := bar\nexample : False := foo\n")


@pytest.mark.parametrize("ident", ["admit_parser", "sorry_count",
                                   "native_decide_note", "axiomatic_note",
                                   "opaque_handle"])
def test_tokens_match_on_identifier_boundaries(ident):
    assert witness_problems(f"example : {ident} = {ident} := rfl\n") == []


def test_prose_may_name_the_banned_tokens():
    """A witness should be free to explain that it does NOT assume anything;
    the tokens are banned as code, not as words."""
    assert witness_problems(
        "-- No axiom, no sorry, no native_decide: this is decided outright.\n"
        "/- Not an `opaque` handle either. -/\n"
        "example : rivalTester 1 = false := by decide\n") == []


def test_deriving_an_instance_stays_legal():
    """velvet needs `deriving instance DecidableEq for Except` to reach a
    postcondition over a result carrier. That is an instance, not an
    assumption, and banning it would drop real cases."""
    assert witness_problems(
        "deriving instance DecidableEq for Except\n\n"
        "example : checkTester false (some 'a') = false := by decide\n") == []


# ---------------------------------------------------------------------------
# conditioning on the carrier: legitimate, and the one way it forges
#
# A spec stated over an `opaque` callee cannot be attacked at a literal input —
# `decide` gets stuck on the opaque term. The refutation must instead be stated
# at a point described by HYPOTHESIS, which is what made three cells reported as
# unportable ("no rival's violation is a theorem") refutable after all. The cost
# is that inconsistent hypotheses prove anything, so the assumptions themselves
# have to be checked.
# ---------------------------------------------------------------------------


def test_a_witness_at_literal_inputs_needs_no_probe():
    """The common case by a wide margin: nearly every reject witness in this
    corpus binds nothing, so there are no assumptions to be inconsistent and no
    build to spend."""
    assert witness_head_binders(
        "example : fTester (some 3) false = false := by decide\n") == ""
    assert consistency_probe(
        "example : fTester (some 3) false = false := by decide\n") is None


def test_the_probe_carries_the_witness_own_binders():
    """The probe asks whether the hypotheses can JOINTLY hold, so it must reuse
    them verbatim — including the value binders they mention, which would
    otherwise be unbound."""
    w = ("extract_program_for choiceValueHash\n\n"
         "example (v : Int) (h1 : valueHash v = 0) (h2 : valueHash v = 1) :\n"
         "    choiceValueHashExec v ≠ DivM.res (valueHash v) := by\n"
         "  omega\n")
    assert witness_head_binders(w) == (
        "(v : Int) (h1 : valueHash v = 0) (h2 : valueHash v = 1)")
    probe = consistency_probe(w)
    assert probe is not None
    assert probe.startswith(
        "example (v : Int) (h1 : valueHash v = 0) (h2 : valueHash v = 1) "
        ": False := by")


def test_the_probe_stops_at_the_statement_not_at_its_parentheses():
    """The statement itself is full of brackets (`DivM.res (valueHash 5)`), and
    swallowing them into the binders would build a probe that does not elaborate
    — reported as a timeout/inconclusive on an honest witness."""
    w = ("example (h : valueHash 5 ≠ 0) :\n"
         "    choiceValueHashExec 5 ≠ DivM.res (valueHash 5) := by\n"
         "  simp\n")
    assert witness_head_binders(w) == "(h : valueHash 5 ≠ 0)"


def test_a_directive_preamble_is_not_a_witness_head():
    """velvet witnesses open with `extract_program_for <name>` and friends. The
    head is the `example`, and reading the preamble as one would bind nothing
    while looking like it had."""
    w = ("extract_program_for m\nderive_tester_for m\n\n"
         "example (h : g 1 = 2) : mTester 1 = false := by simp [h]\n")
    assert witness_head_binders(w) == "(h : g 1 = 2)"


def test_an_implicit_or_instance_binder_still_makes_a_probe():
    """`{α : Type}` / `[Inhabited α]` are part of the head, so the probe has to
    reproduce them for the hypotheses that mention them to typecheck."""
    w = ("example {α : Type} [Inhabited α] (h : f (default : α) = 0) :\n"
         "    gTester (default : α) = false := by simp [h]\n")
    probe = consistency_probe(w)
    assert probe is not None and "{α : Type} [Inhabited α]" in probe


def test_a_harmless_leading_declaration_does_not_disable_the_probe():
    """The evasion the multi-head read exists to close: put anything that binds
    nothing in front of the refutation and a first-head-only probe reads "" and
    returns None, so the inconsistent hypotheses below it are never checked."""
    w = ("theorem harmless : (1:Nat) = 1 := rfl\n\n"
         "example (h1 : valueHash 5 = 0) (h2 : valueHash 5 = 1) :\n"
         "    gTester 5 = false := by simp_all\n")
    assert witness_head_binders(w) == ""          # the first head binds nothing
    probe = consistency_probe(w)
    assert probe is not None
    assert "(h1 : valueHash 5 = 0) (h2 : valueHash 5 = 1) : False" in probe


def test_every_binding_declaration_is_probed_in_one_file():
    """A refutation resting on a helper lemma proved from a contradiction is no
    better than one resting on the contradiction directly, so each binding head
    gets a probe — all in a single file, so the build cost does not scale."""
    w = ("theorem helper (h : f 1 = 0) : g 1 = 0 := by simp [h]\n\n"
         "example (h2 : f 1 = 1) : gTester 1 = false := by simp [helper, h2]\n")
    assert all_witness_head_binders(w) == ["(h : f 1 = 0)", "(h2 : f 1 = 1)"]
    probe = consistency_probe(w)
    assert probe is not None
    assert probe.count("example ") == 2
    assert "(h : f 1 = 0) : False" in probe and "(h2 : f 1 = 1) : False" in probe
    # and it is still a single legal witness file
    assert witness_problems(probe) == []


def test_the_probe_is_itself_a_legal_witness_shape():
    """It is appended to the same stripped file the witness builds in, so it must
    pass the same shape check — no `sorry`, no `native_decide`."""
    probe = consistency_probe(
        "example (h : valueHash 5 ≠ 0) : gTester 5 = false := by simp [h]\n")
    assert probe is not None and witness_problems(probe) == []


# ---------------------------------------------------------------------------
# the witness must be stated in the vocabulary both files SHARE
#
# "gold's build failed" only means "gold satisfies the spec here" if both builds
# asked the same question. A name that exists on one side and not the other makes
# them different questions, and one direction of that is a false refutation.
# ---------------------------------------------------------------------------

_RIVAL_HELPER = LEAN.replace(
    "-- impl-start", "-- impl-start\ndef rivalOnlyMarker : Nat := 0", 1)


def test_a_witness_over_a_variant_only_name_is_rejected():
    """The forgery this rejects: rival exit 0, gold exit 1 with
    `rfl ... but is expected to have type rivalOnlyMarker = 0`. Gold failed on an
    unknown name, not on a satisfied spec, and the witness is a tautology."""
    problems = witness_scope_problems(
        LEAN, _RIVAL_HELPER, "example : rivalOnlyMarker = 0 := rfl\n")
    assert problems and "rivalOnlyMarker" in problems[0]


def test_a_witness_over_the_shared_spec_and_impl_is_fine():
    """The normal case: everything a witness names is in both files."""
    assert witness_scope_problems(LEAN, _RIVAL_HELPER, WITNESS) == []


def test_a_variant_that_adds_nothing_constrains_nothing():
    assert witness_scope_problems(
        LEAN, LEAN, "example : rivalOnlyMarker = 0 := rfl\n") == []


def test_the_witness_own_declarations_are_its_own():
    """A witness may declare a helper of its own; it is appended to BOTH files,
    so it exists on both sides even if the variant coincidentally declares the
    same name."""
    assert witness_scope_problems(
        LEAN, _RIVAL_HELPER,
        "def rivalOnlyMarker : Nat := 0\n"
        "example : rivalOnlyMarker = 0 := rfl\n") == []


def test_the_velvet_tester_names_are_not_variant_only():
    """`extract_program_for m` / `derive_tester_for m` mint `mExec` / `mTester`
    from directives inside the witness, so a rule that read those names as
    variant-only would reject every witness that opens this way."""
    variant = VELVET.replace("return x + 1", "return x + 2", 1)
    assert witness_scope_problems(
        VELVET, variant,
        "extract_program_for countUp\nderive_tester_for countUp\n\n"
        "example : countUpTester 3 = false := by decide\n") == []


def test_a_substring_of_a_variant_only_name_is_not_a_hit():
    """Matched on identifier boundaries: a variant declaring `marker` must not
    flag a witness that only mentions `markerCount`."""
    variant = LEAN.replace("-- impl-start",
                           "-- impl-start\ndef marker : Nat := 0", 1)
    assert witness_scope_problems(
        LEAN, variant, "example : markerCount = markerCount := rfl\n") == []


def test_a_variant_only_name_mentioned_only_in_prose_is_not_a_hit():
    """Comments are stripped first, so a witness may explain the variant."""
    assert witness_scope_problems(
        LEAN, _RIVAL_HELPER,
        "-- The variant also introduces rivalOnlyMarker, which we do not use.\n"
        + WITNESS) == []
