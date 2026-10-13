# properties.py — G-PBT falsification battery for django__django-15280 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case
# is a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only
# the impl region — and, where a positive reproves or a ground instance is added,
# the proof body — is edited), checked by variant_scope + the Lean verifier. Every
# expect="reject" case carries a refutation `witness`: a self-contained snippet
# that ELABORATES against the rival and FAILS on the frozen solution, so the
# rejection is attributable to the spec and not to a tactic script that merely
# stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json):
#   assignParents : (Int → Int) → List Child → List Child
#     where Child = { key : Int, parent : Option Int }.
#   The single postcondition clause pins the whole result:
#       result = children.map (assignOne lookup)
#   with assignOne c = c when c.parent is `some _` (a value is ALREADY assigned —
#   keep it, and every other component of c, unchanged), and assignOne c =
#   { c with parent := some (lookup c.key) } when c.parent is `none` (no value yet
#   — assign the default parent looked up by the child's own key). Batch ORDER and
#   LENGTH are preserved (it is a `map`). So the load-bearing decision is, per
#   child: WHETHER a value is already assigned (`some`/`none`), and if not, WHICH
#   default to assign (`lookup c.key`, keyed by THIS child's key).
#
# CARRIER NOTE: nagini modeled three parallel lists (slot_full / slot_value /
# supplied) with a per-index oracle; this backend folds the same behavior into a
# single `List Child`, where each child carries both its occupancy (`parent`
# is `some`/`none`) and its key. The per-child guarantee is identical; the rivals
# below attack the same decisions over the folded carrier.
#
# LANES THAT DO NOT PORT (see 'assessment' in the submission):
#   * FRAME / PERMISSION MUTATION (nagini's MANDATORY class: slot_full and supplied
#     were held at Acc(..., 1/2), so a rival that STORED into a read-only input was
#     rejected for insufficient permission — _FRAME_SUPPLIED, _FRAME_SLOTFULL).
#     Lean is referentially transparent: `lookup` and `children` are immutable
#     values, there is no fractional permission to violate and no aliasing to
#     exploit, so this entire class is VACUOUS here. No substitute is fabricated.
#   * ADMISSIBILITY (nagini's precondition-admission probe defended the 0/1
#     occupancy + parallel-length Requires). The lean obligation is
#     `∀ lookup children, problem_spec … (implementation …)` with NO precondition
#     hypothesis, so nothing could be PRECOND-TOO-STRONG; the honest analogue is a
#     ground instance discharged at the F2P-shaped input (see admiss case below).
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them, and this
#     bundle declares no opaque callee / axiom anyway (the "is a value already
#     assigned?" test is modeled directly by the Option parent slot).
from pathlib import Path

INSTANCE = "django__django-15280"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- region anchors (each lies ENTIRELY inside a single region and is unique) ---

# The FULL frozen impl body (verbatim). Every impl reshape swaps this out, so the
# spec and the `theorem correct_assignParents` STATEMENT stay byte-identical.
_IMPL_GOLD = """def implementation_assignParents
    (lookup : Int → Int) (children : List Child) : List Child := Id.run do
  let mut acc : List Child := []
  for c in children do
    if c.parent.isNone then
      let p := lookup c.key
      acc := acc ++ [{ c with parent := some p }]
    else
      acc := acc ++ [c]
  return acc"""
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"

# The FULL frozen tactic body of `correct_assignParents` (verbatim). The positive
# control reproves it for its new impl shape; it is otherwise untouched.
_CORRECT_PROOF = """  intro lookup children
  unfold problem_spec_assignParents implementation_assignParents
  -- Bridge the desugared loop body to the cleaned body of `assignParents_forIn`.
  have h2 : (Id.run do
      let mut acc : List Child := []
      for c in children do
        if c.parent.isNone then
          let p := lookup c.key
          acc := acc ++ [{ c with parent := some p }]
        else
          acc := acc ++ [c]
      return acc) = Id.run (forIn children ([] : List Child) (fun c r =>
        (if c.parent.isNone = true then
          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
        else
          pure (ForInStep.yield (r ++ [c]))))) := rfl
  rw [h2, assignParents_forIn]
  simp"""
assert _BASE.count(_CORRECT_PROOF) == 1, "proof region drifted; update _CORRECT_PROOF"

# Anchor for inserting a ground instance into the proof (admissibility).
_INTRO = "  intro lookup children\n"
assert _BASE.count(_INTRO) == 1, "intro anchor drifted"


def _impl(body):
    """Full Solution.lean variant with only the impl body replaced (proof frozen)."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — must VERIFY.
# ---------------------------------------------------------------------------
# Structurally DIFFERENT but behaviourally identical: drop the imperative
# `Id.run do` / `let mut` accumulator loop entirely and express the per-child
# decision as a single functional `map` with a `match` on the occupancy slot. It
# produces the identical result on every input; the frozen proof (which bridges
# the desugared `for`-loop to a `forIn` helper) no longer applies to the new
# shape, so the obligation is RE-PROVED for it. The `theorem correct_assignParents`
# STATEMENT is byte-identical, and no new lemma/axiom/assumption token is added
# (the frozen helper stays present and unused; the reproof closes by `rfl` after
# unfolding both sides to the same `map`). If a faithful correct impl in this
# shape could not verify => SPEC-TOO-STRONG.
_POS_IMPL = """def implementation_assignParents
    (lookup : Int → Int) (children : List Child) : List Child :=
  children.map (fun c =>
    match c.parent with
    | some _ => c
    | none => { c with parent := some (lookup c.key) })"""

_POS_PROOF = """  intro lookup children
  unfold problem_spec_assignParents implementation_assignParents assignOne
  rfl"""


# ---------------------------------------------------------------------------
# ADMISSIBILITY — must VERIFY. A ground instance discharged at the F2P-shaped
# input (one child already assigned a parent = the nested-prefetch case, one child
# with no parent yet = the ordinary case) confirms the obligation is SATISFIABLE
# at the normal input rather than only provable in the abstract. Inserted as a
# `have _ground := by … decide` after `intro`, ahead of the frozen proof, which is
# then carried verbatim. Nothing is assumed: the theorem STATEMENT is byte-
# identical and no new declaration/axiom/sorry appears.
_ADMIT_GROUND = (
    "  intro lookup children\n"
    "  have _ground : problem_spec_assignParents (fun _ => 99)\n"
    "      [⟨1, some 7⟩, ⟨2, none⟩]\n"
    "      (implementation_assignParents (fun _ => 99) [⟨1, some 7⟩, ⟨2, none⟩]) := by\n"
    "    unfold problem_spec_assignParents implementation_assignParents\n"
    "    decide\n"
)


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly (only the impl body changes) and carries a `decide`-able
# witness pinning the divergence at one concrete input.
# ---------------------------------------------------------------------------

# uncond-overwrite (= the pre-patch bug): drop the occupancy guard and assign the
# looked-up default to EVERY child, overwriting one that already has a parent.
_UNCOND = """def implementation_assignParents
    (lookup : Int → Int) (children : List Child) : List Child := Id.run do
  let mut acc : List Child := []
  for c in children do
    let p := lookup c.key
    acc := acc ++ [{ c with parent := some p }]
  return acc"""

# invert-guard: assign to the ALREADY-populated children and leave the empty ones
# untouched — the mirror of the correct guard.
_INVERT = """def implementation_assignParents
    (lookup : Int → Int) (children : List Child) : List Child := Id.run do
  let mut acc : List Child := []
  for c in children do
    if c.parent.isSome then
      let p := lookup c.key
      acc := acc ++ [{ c with parent := some p }]
    else
      acc := acc ++ [c]
  return acc"""

# skip-last: correct on every child EXCEPT the final one, which is never assigned
# a parent even when empty (index-position bug in the traversal).
_SKIP_LAST = """def implementation_assignParents
    (lookup : Int → Int) (children : List Child) : List Child := Id.run do
  let n := children.length
  let mut acc : List Child := []
  let mut i : Nat := 0
  for c in children do
    if c.parent.isNone && i + 1 != n then
      let p := lookup c.key
      acc := acc ++ [{ c with parent := some p }]
    else
      acc := acc ++ [c]
    i := i + 1
  return acc"""

# wrong-key: fill empty slots (correct occupancy decision) but look up the default
# using a FIXED key (0) instead of the child's own key — the recorded default is
# unrelated to which child receives it.
_WRONG_KEY = """def implementation_assignParents
    (lookup : Int → Int) (children : List Child) : List Child := Id.run do
  let mut acc : List Child := []
  for c in children do
    if c.parent.isNone then
      let p := lookup 0
      acc := acc ++ [{ c with parent := some p }]
    else
      acc := acc ++ [c]
  return acc"""


def _wit(lookup, children):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    input, closed by `decide`. Elaborates against a rival that diverges from the
    frozen result there and fails on gold (which satisfies the spec everywhere)."""
    return (
        f"example : ¬ problem_spec_assignParents ({lookup}) {children}\n"
        f"    (implementation_assignParents ({lookup}) {children}) := by\n"
        f"  unfold problem_spec_assignParents implementation_assignParents\n"
        f"  decide"
    )


SPEC_TESTS = [
    {
        "id": "pos-functional-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_IMPL), _CORRECT_PROOF, _POS_PROOF),
        "rationale": (
            "structurally-different but CORRECT impl: the imperative accumulator "
            "loop is replaced by a single functional `children.map` with a `match` "
            "on the occupancy slot, producing the identical result on every input. "
            "It must satisfy `result = children.map (assignOne lookup)`; after "
            "`unfold` both sides are the same `map` and the goal closes by `rfl`. "
            "The `theorem correct_assignParents` statement is byte-identical and no "
            "new lemma/axiom/assumption token is introduced. If it FAILS => "
            "SPEC-TOO-STRONG (a faithful correct impl in a different shape rejected)."
        ),
    },
    {
        "id": "admiss-mixed-batch-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _INTRO, _ADMIT_GROUND),
        "rationale": (
            "the obligation is additionally discharged at the F2P-shaped ground "
            "input — a batch with one child ALREADY carrying a parent (`some 7`, "
            "the nested-prefetch case) and one child with none yet (the ordinary "
            "case) — by `decide`, ahead of the frozen proof carried verbatim. "
            "Confirms the modeled behavior is satisfiable at exactly the input the "
            "F2P exercises (the analogue of PRECOND-TOO-STRONG). Nothing is assumed: "
            "the theorem STATEMENT is byte-identical, the ground instance is a "
            "`have` inside the existing tactic body, no new declaration/axiom/sorry."
        ),
    },
    {
        "id": "weak-uncond-overwrite-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_UNCOND),
        "refinement": (
            "this IS the pre-patch behaviour: the per-child assignment is applied "
            "unconditionally, so a child that ALREADY has a parent (assigned by an "
            "inner nested prefetch) is overwritten by the outer default. Its "
            "faithful real counterpart is the unchanged repo, which fails the "
            "FAIL_TO_PASS observable — after the outer pass, following the child "
            "back to its parent fires a DB query (assertNumQueries(0) -> 1 != 0) "
            "because the more-specific prefetched parent was clobbered. It does NOT "
            "resolve, so a verifying rival here is a true verify-not-resolve break."
        ),
        "rationale": (
            "REJECT from the clause `result = children.map (assignOne lookup)`: on a "
            "child with `parent = some v` where the default differs (`lookup key ≠ "
            "v`), `assignOne` keeps `some v` but the rival overwrites it with the "
            "default. Attacks the occupancy-guard (`some _` keep) decision from the "
            "over-write side. Witness at a POPULATED child."
        ),
        # populated child ⟨0, some 1⟩, constant lookup = 5: gold keeps some 1,
        # rival overwrites to some 5.
        "witness": _wit("fun _ => (5 : Int)", "[⟨0, some 1⟩]"),
    },
    {
        "id": "weak-invert-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_INVERT),
        "refinement": (
            "inverting the guard — assign to already-populated children and skip "
            "the empty ones — corresponds to a patch that both clobbers the nested "
            "prefetched parent AND never links the ordinary children, so following "
            "an unassigned child to its parent still fires a query. It fails the "
            "FAIL_TO_PASS observable (and any reverse-relation test that expects "
            "every unassigned child linked). It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = children.map (assignOne lookup)`: on a "
            "child with `parent = none`, `assignOne` assigns `some (lookup key)` but "
            "the rival leaves `none`. Attacks the occupancy-guard decision from the "
            "under-write (empty-slot) side. Witness at an EMPTY child (varying the "
            "`parent` field off the `some _` value the over-write rival uses)."
        ),
        # empty child ⟨0, none⟩, constant lookup = 5: gold assigns some 5,
        # rival leaves none.
        "witness": _wit("fun _ => (5 : Int)", "[⟨0, none⟩]"),
    },
    {
        "id": "weak-skip-last-child",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SKIP_LAST),
        "refinement": (
            "skipping the final child in the traversal corresponds to a patch that "
            "leaves the last prefetched row's parent unassigned; following that "
            "child back to its parent then fires a DB query, so the FAIL_TO_PASS "
            "assertNumQueries(0) fails for the un-linked last child. It does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = children.map (assignOne lookup)`, "
            "which pins EVERY position of the ordered result (a `map` over the whole "
            "batch): on a multi-child batch whose LAST child is empty, the spec "
            "assigns `some (lookup key)` at the final position but the rival leaves "
            "it `none`. Attacks the batch-completeness / ordering aspect over a "
            "multi-element batch — varying the batch LENGTH, which the single-child "
            "witnesses hold fixed."
        ),
        # two-child batch, last one empty, lookup = 5: gold => [⟨0,some 1⟩,⟨2,some 5⟩],
        # rival leaves the last as ⟨2, none⟩.
        "witness": _wit("fun _ => (5 : Int)", "[⟨0, some 1⟩, ⟨2, none⟩]"),
    },
    {
        "id": "weak-wrong-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WRONG_KEY),
        "refinement": (
            "looking up the default with a fixed key instead of the child's own key "
            "corresponds to assigning every unassigned child the SAME parent "
            "regardless of which related value it carries; the reverse relation "
            "would be populated with the wrong parent, so following a child to its "
            "parent yields the wrong object (and a mismatch the prefetch tests "
            "detect). It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = children.map (assignOne lookup)`: for "
            "an empty child the spec assigns `some (lookup c.key)` keyed by THIS "
            "child's key, but the rival assigns `some (lookup 0)`. Exercised with a "
            "NON-CONSTANT lookup and a child key ≠ 0 — the only configuration that "
            "distinguishes the two, so this is the case that varies the `lookup` "
            "binder and the child `key` field (every other witness uses a constant "
            "lookup where the key is irrelevant)."
        ),
        # empty child key 5, lookup = identity: gold assigns some 5 (lookup 5),
        # rival assigns some 0 (lookup 0).
        "witness": _wit("fun x => x", "[⟨5, none⟩]"),
    },
]


# No consumed axioms and no deep-model references: the occupancy test is modeled
# directly by the Option parent slot and the default table is a plain total
# function argument, so there is no in-model axiom obligation for a PBT axiom lane
# to re-discharge (and that lane belongs to G-AX regardless).
AXIOM_TESTS = []
