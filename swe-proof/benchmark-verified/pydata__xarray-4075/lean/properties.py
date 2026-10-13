# properties.py — PBT falsification battery for pydata__xarray-4075 (lean backend).
# PORT of the nagini sibling's spec lane onto this bundle's carrier. NOT a Lean
# source file; a record of adversarially-reasoned cases the G-PBT gate executes and
# stamps a verdict onto. Each spec case is a FULL Solution.lean variant that shares
# the FROZEN spec byte-for-byte (region surgery: only the `impl` body and the `proof`
# body are edited; the spec view — imports, axioms, pure helpers, post-conditions,
# and the `theorem correct_<name>` STATEMENT — is never touched). Every case is
# checked by variant_scope (same_spec + obligation preserved + no new assumptions)
# and, for reject cases, a discriminating `witness` the gate builds twice.
#
# ---------------------------------------------------------------------------
# Carrier narrowing vs the nagini sibling (recorded so the omissions are auditable)
# ---------------------------------------------------------------------------
# The nagini model contracts `sum_of_weights_value(mask, weights, weights_are_bool)`
# over half-permission list carriers and routes the reduction through a consumed
# `dot_reduce` axiom keyed on a `boolean_dot` flag. This bundle models ONLY the
# purely-functional core the issue is about: `sumOfWeights (mask weights : List Bool)
# : Option Int`, where the boolean weights are ALWAYS reduced in integer arithmetic
# (`zipDot`), a zero total is reported as absence (`none`), and every positive total
# as `some`. The frozen obligation is
#
#     result = sowSpec mask weights
#       where sowSpec = let s := zipDot (mask.zip weights); if s = 0 then none else some s
#
# Consequences for the port:
#   * The `weights_are_bool` binder does NOT exist here — the modeled domain fixes
#     boolean weights and integer reduction. So the nagini `weak-prepatch`
#     (boolean_dot = weights_are_bool) and `weak-bool-dot` (boolean_dot = True)
#     rivals COLLAPSE into a single carrier-native rival: the saturating boolean
#     contraction that reports presence (one unit) instead of the count. That rival
#     is `weak-saturating` below; it is exactly this bundle's Solution_prepatch.
#   * The FRAME-MUTATION lane (frame-mut-mask / frame-mut-weights) is VACUOUS on
#     lean: the carrier is referentially transparent, there is no aliasing and no
#     fractional permission, so a "write into a read-only input" rival cannot be
#     expressed. Not fabricated a substitute (see `assessment`). DEMONSTRATED, not
#     asserted: `mask`/`weights` are immutable `List Bool` VALUES, so the nearest
#     expressible analogue — rebind a local copy and clobber it
#     (`let mut m2 := mask; m2 := m2.map (fun _ => false)`) before computing the
#     aggregate from the untouched binder — leaves the returned value unchanged.
#     There is no store to the caller's carrier for a spec to forbid, so such a
#     rival is not WRONG and would be a vacuous reject case.
#   * The ADMISSIBILITY lane, by contrast, IS expressible and is NOT dropped: the
#     nagini `admiss-reads` control (a normal length-matched pair is in-domain) has
#     a carrier-native analogue — instantiate the obligation's binder hypothesis at
#     concrete in-domain points and pin the value the frozen impl actually produces
#     there. That is `admiss-instantiate` below.
#   * The DIVERGENCE lane is genuinely vacuous here: `implementation_sumOfWeights`
#     is a total Lean `def`, so a non-terminating implementation cannot be written.
#   * The AXIOM lane (dot_reduce soundness/containment) is DROPPED: the callee is
#     modeled DEEPLY as `zipDot` (an A-reference, not a consumed axiom), there is no
#     `opaque`/`axiom` in the frozen bundle, and the axiom lane is G-AX's job.
#
# What replaces case-count parity is COVERAGE of the surface this bundle models:
#   * the obligation is DEFENDED by two structurally-different correct impls
#     (pos-direct, pos-reshape) and ATTACKED by six rivals;
#   * every independent clause of the postcondition is attacked — the per-position
#     `m && w` conjunction (both the mask conjunct and the weight conjunct), the
#     integer COUNT (vs a saturating presence indicator), the POSITIONAL PAIRING of
#     the two sequences, and the zero-total ↦ none masking;
#   * both INPUT BINDERS (mask, weights) are varied by the reject witnesses across
#     six distinct input points, and each binder is abused by a dedicated rival;
#   * the obligation is shown NON-VACUOUS at in-domain points (admiss-instantiate).
from pathlib import Path

INSTANCE = "pydata__xarray-4075"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen `impl` region body (everything strictly BETWEEN the def header line
# and the `-- impl-end` marker). Every imperative rival _swap()s ONLY this block,
# so the edit never touches the spec view. same_spec holds by construction.
_IMPL_BODY = """\
  let mut acc : Int := 0
  for (m, w) in mask.zip weights do
    if m && w then
      acc := acc + 1
  if acc = 0 then
    return none
  return some acc"""

assert _BASE.count(_IMPL_BODY) == 1, "impl region body drifted from expected text"

# The frozen `impl` def in full (header + body), for the functional positive that
# replaces the whole definition rather than just the loop.
_IMPL_FULL = (
    "def implementation_sumOfWeights (mask weights : List Bool) : Option Int := Id.run do\n"
    + _IMPL_BODY
)
assert _BASE.count(_IMPL_FULL) == 1, "impl def drifted"

# The frozen proof body (interior of the `proof` region's `correct_sumOfWeights`
# tactic block — everything after the `:= by`). Only the tactic body may change;
# the theorem STATEMENT is byte-identical across every variant.
_PROOF_BODY = """\
  intro mask weights _
  unfold problem_spec_sumOfWeights implementation_sumOfWeights sowSpec
  have hf := fold_helper (mask.zip weights) 0
  simp only [Id.run, zero_add, bind, pure] at hf ⊢
  rw [hf]"""
assert _BASE.count(_PROOF_BODY) == 1, "proof body drifted"

# The frozen `fold_helper` helper theorem (a proof-region lemma), swapped only by
# the imperative-reshape positive so its induction matches the reshaped loop. Its
# NAME is preserved (variant_scope introduces no new decl); `correct_sumOfWeights`
# is untouched.
_FOLD_HELPER = """\
theorem fold_helper (xs : List (Bool × Bool)) (init : Int) :
    Id.run (forIn xs init (fun x r =>
      if (x.1 && x.2) = true then pure (ForInStep.yield (r + 1))
      else pure (ForInStep.yield r))) = init + zipDot xs := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, zipDot, add_zero]; rfl
  | cons a as ih =>
    obtain ⟨m, w⟩ := a
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (m && w) = true
    · simp only [h, if_true, ih, zipDot]; ring
    · simp only [Bool.not_eq_true] at h
      simp only [h, Bool.false_eq_true, if_false, ih, zipDot]; ring"""
assert _BASE.count(_FOLD_HELPER) == 1, "fold_helper drifted"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl-region loop body replaced."""
    return _swap(_BASE, _IMPL_BODY, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# Each carries a proof that actually closes for the reshaped impl; the
# `correct_sumOfWeights` STATEMENT is byte-identical, no helper lemma added, no
# obligation weakened.
# ---------------------------------------------------------------------------

# pos-direct: a structurally DIFFERENT but behaviourally CORRECT impl. Instead of
# the imperative accumulation loop, it evaluates the grounded fold directly and
# performs the zero ↦ none masking inline — i.e. it IS `sowSpec` spelled out. Since
# the obligation is `result = sowSpec mask weights`, the definitionally-equal impl
# closes by `rfl`. If it FAILS => SPEC-TOO-STRONG (a faithful correct impl producing
# the pinned aggregate is rejected).
def _mk_pos_direct():
    s = _swap(
        _BASE,
        _IMPL_FULL,
        "def implementation_sumOfWeights (mask weights : List Bool) : Option Int :=\n"
        "  let s := zipDot (mask.zip weights)\n"
        "  if s = 0 then none else some s",
    )
    return _swap(s, _PROOF_BODY, "  intro mask weights _\n  rfl")


# pos-reshape: the imperative shape kept, but the per-position update is written as
# the additive `acc := acc + (if m && w then 1 else 0)` (a single unconditional
# accumulate) instead of the guarded increment. Semantically identical; the proof
# reproves with a `fold_helper` whose loop matches the reshaped body. If it FAILS =>
# SPEC-TOO-STRONG on a trivial arithmetic reshape.
def _mk_pos_reshape():
    s = _impl(
        "  let mut acc : Int := 0\n"
        "  for (m, w) in mask.zip weights do\n"
        "    acc := acc + (if m && w then 1 else 0)\n"
        "  if acc = 0 then\n"
        "    return none\n"
        "  return some acc"
    )
    return _swap(
        s,
        _FOLD_HELPER,
        "theorem fold_helper (xs : List (Bool × Bool)) (init : Int) :\n"
        "    Id.run (forIn xs init (fun x r =>\n"
        "      pure (ForInStep.yield (r + (if x.1 && x.2 then 1 else 0))))) = init + zipDot xs := by\n"
        "  induction xs generalizing init with\n"
        "  | nil => simp only [List.forIn_nil, Id.run, zipDot, add_zero]; rfl\n"
        "  | cons a as ih =>\n"
        "    obtain ⟨m, w⟩ := a\n"
        "    rw [List.forIn_cons]\n"
        "    simp only [Id.run, bind] at ih ⊢\n"
        "    simp only [ih, zipDot]; ring",
    )


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly (only the impl body changes) and carries a witness the gate builds
# against BOTH the rival (must elaborate) and the frozen solution (must fail).
# ---------------------------------------------------------------------------

# weak-saturating: the pre-patch behaviour — the boolean contraction that saturates.
# Any kept-and-set position flips a boolean flag; the result is `some 1` on presence,
# `none` on absence, never the true count. This is the port of nagini's collapsed
# `weak-prepatch`/`weak-bool-dot` pair. Attacks the COUNT clause.
_WEAK_SATURATING = (
    "  let mut acc : Bool := false\n"
    "  for (m, w) in mask.zip weights do\n"
    "    if m && w then\n"
    "      acc := true\n"
    "  if acc = false then\n"
    "    return none\n"
    "  return some 1"
)

# weak-ignore-mask: drops the mask conjunct, counting every set-weight position
# regardless of whether the entry is retained. Correct only when the mask retains
# every set-weight position; wrong as soon as a dropped entry carries a set weight.
# Attacks the mask conjunct of the per-position `m && w` combination.
_WEAK_IGNORE_MASK = (
    "  let mut acc : Int := 0\n"
    "  for (m, w) in mask.zip weights do\n"
    "    if w then\n"
    "      acc := acc + 1\n"
    "  if acc = 0 then\n"
    "    return none\n"
    "  return some acc"
)

# weak-ignore-weight: the dual — drops the weight conjunct, counting every retained
# position regardless of its weight. Attacks the weight conjunct of `m && w`.
_WEAK_IGNORE_WEIGHT = (
    "  let mut acc : Int := 0\n"
    "  for (m, w) in mask.zip weights do\n"
    "    if m then\n"
    "      acc := acc + 1\n"
    "  if acc = 0 then\n"
    "    return none\n"
    "  return some acc"
)

# weak-drop-zero: the count is computed correctly but the zero-total ↦ none masking
# is dropped — a zero aggregate is reported as `some 0` instead of `none`. Attacks
# the absence/masking clause. Correct on every positive-total input; wrong exactly on
# the zero-total sub-domain.
_WEAK_DROP_ZERO = (
    "  let mut acc : Int := 0\n"
    "  for (m, w) in mask.zip weights do\n"
    "    if m && w then\n"
    "      acc := acc + 1\n"
    "  return some acc"
)

# weak-const-none: returns the constant `none` — correct only on the empty-aggregate
# sub-domain, wrong on any input with a retained set-weight position. A cheap
# supporting near-miss; attacks the `some`-of-positive-total clause.
_WEAK_CONST_NONE = "  return none"

# weak-misalign: the per-position combination and the count are both right, and so is
# the zero ↦ none masking — what is wrong is WHICH mask flag each weight is paired
# with. It contracts the REVERSED mask against the weights, i.e. position i of the
# weights meets position n-1-i of the retention mask. This is the one clause the
# other five rivals leave standing: each of them changes WHAT is accumulated, none
# of them changes the ALIGNMENT of the two sequences, so a spec that pinned only the
# multiset of contributions rather than their positional pairing would admit this
# one. Note it agrees with the spec on every palindromic mask (and hence on the
# all-true F2P shape), so it is a genuine partial-domain near-miss rather than a
# blunt wrong answer.
_WEAK_MISALIGN = (
    "  let mut acc : Int := 0\n"
    "  for (m, w) in mask.reverse.zip weights do\n"
    "    if m && w then\n"
    "      acc := acc + 1\n"
    "  if acc = 0 then\n"
    "    return none\n"
    "  return some acc"
)

# admiss-instantiate: the ADMISSIBILITY control (the carrier-native analogue of the
# nagini `admiss-reads` case). The frozen impl and proof are kept VERBATIM; the case
# only ADDS `example`s that instantiate `correct_sumOfWeights` at concrete in-domain
# points and pin the value the frozen impl produces there. It is what rules out a
# vacuously-satisfiable binder: if `mask.length = weights.length` could not be
# discharged at a real pair, or if the obligation held only where the impl returns
# nothing, `correct_sumOfWeights [true,true] [true,true] rfl` would not typecheck.
# Both branches of the masking are instantiated (a positive aggregate and an absent
# one). Adds no theorem/lemma name and no assumption token — only anonymous
# `example`s inside the proof region.
_ADMISS_EXAMPLES = """

-- Admissibility: the binder hypothesis `mask.length = weights.length` is
-- SATISFIABLE, and the obligation instantiates non-vacuously at concrete
-- in-domain points -- a non-empty aggregate and an absent one.
example : problem_spec_sumOfWeights [true, true] [true, true]
    (implementation_sumOfWeights [true, true] [true, true]) :=
  correct_sumOfWeights [true, true] [true, true] rfl

example : implementation_sumOfWeights [true, true] [true, true] = some 2 := by
  decide

example : problem_spec_sumOfWeights [false] [true]
    (implementation_sumOfWeights [false] [true]) :=
  correct_sumOfWeights [false] [true] rfl

example : implementation_sumOfWeights [false] [true] = none := by
  decide"""


def _mk_admiss():
    """Frozen impl AND proof verbatim, plus in-domain instantiation examples."""
    return _swap(_BASE, _PROOF_BODY, _PROOF_BODY + _ADMISS_EXAMPLES)


SPEC_TESTS = [
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _mk_pos_direct(),
        "rationale": (
            "structurally-different but CORRECT impl: evaluates the grounded fold "
            "directly and performs the zero ↦ none masking inline, i.e. it is the "
            "spec's own `sowSpec` spelled out as the implementation. The obligation "
            "is `result = sowSpec mask weights`, so the definitionally-equal impl "
            "closes by `rfl` — no helper lemma, no weakened statement. If it FAILS "
            "=> SPEC-TOO-STRONG (a faithful correct impl producing the pinned "
            "aggregate is rejected)."
        ),
    },
    {
        "id": "pos-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _mk_pos_reshape(),
        "rationale": (
            "the imperative shape kept, but the per-position update is the additive "
            "`acc := acc + (if m && w then 1 else 0)` (one unconditional accumulate) "
            "instead of the guarded increment — semantically identical. The proof "
            "reproves via a `fold_helper` whose loop matches the reshaped body; the "
            "`correct_sumOfWeights` STATEMENT is byte-identical and no new theorem "
            "name is introduced. If it FAILS => SPEC-TOO-STRONG on a trivial "
            "arithmetic reshape."
        ),
    },
    {
        "id": "weak-saturating",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SATURATING),
        "refinement": (
            "this IS the pre-patch behaviour: the aggregate is formed by the boolean "
            "contraction that saturates (presence ↦ one unit) rather than the "
            "integer count. Its faithful real patch is the unchanged repo, which on "
            "boolean weights computes the dot product of two boolean arrays and "
            "returns the presence indicator, not the count — exactly the reported "
            "bug. It fails the F2P tests (which expect the retained-weight COUNT of "
            "2, not 1) and does NOT resolve; a verifying saturating rival would be a "
            "true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by `result = sowSpec mask weights`: on mask=[true,true], "
            "weights=[true,true] the aggregate is 2 (`some 2`), but the saturating "
            "rival returns `some 1`. Attacks the COUNT clause. If it VERIFIES => "
            "SPEC-TOO-WEAK (the presence/count collapse is not forbidden)."
        ),
        "witness": (
            "example : ¬ problem_spec_sumOfWeights [true, true] [true, true]\n"
            "    (implementation_sumOfWeights [true, true] [true, true]) := by\n"
            "  unfold problem_spec_sumOfWeights implementation_sumOfWeights sowSpec\n"
            "  decide"
        ),
    },
    {
        "id": "weak-ignore-mask",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_IGNORE_MASK),
        "refinement": (
            "drops the not-null mask from the contraction, aggregating every "
            "set-weight position regardless of whether the entry is retained. A real "
            "patch that omitted the notnull mask would count weights at dropped "
            "(missing-data) entries, so it would not resolve the reductions that "
            "exercise a non-trivial mask; verifying it would be a real break."
        ),
        "rationale": (
            "REJECTED by `result = sowSpec mask weights`: on mask=[false], "
            "weights=[true] the retained aggregate is 0 (`none`), but ignoring the "
            "mask yields `some 1`. Attacks the MASK conjunct of the per-position "
            "`m && w` combination. If it VERIFIES => SPEC-TOO-WEAK (the mask input "
            "is not load-bearing in the spec)."
        ),
        "witness": (
            "example : ¬ problem_spec_sumOfWeights [false] [true]\n"
            "    (implementation_sumOfWeights [false] [true]) := by\n"
            "  unfold problem_spec_sumOfWeights implementation_sumOfWeights sowSpec\n"
            "  decide"
        ),
    },
    {
        "id": "weak-ignore-weight",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_IGNORE_WEIGHT),
        "refinement": (
            "the dual: drops the weight from the contraction, counting every "
            "retained position regardless of its weight. A real patch that ignored "
            "the weights would report the retained-entry count rather than the "
            "weighted aggregate, failing every reduction with a non-uniform weight "
            "array; verifying it would be a real break."
        ),
        "rationale": (
            "REJECTED by `result = sowSpec mask weights`: on mask=[true], "
            "weights=[false] the aggregate is 0 (`none`), but ignoring the weight "
            "yields `some 1`. Attacks the WEIGHT conjunct of the per-position "
            "`m && w` combination. If it VERIFIES => SPEC-TOO-WEAK (the weight input "
            "is not load-bearing in the spec)."
        ),
        "witness": (
            "example : ¬ problem_spec_sumOfWeights [true] [false]\n"
            "    (implementation_sumOfWeights [true] [false]) := by\n"
            "  unfold problem_spec_sumOfWeights implementation_sumOfWeights sowSpec\n"
            "  decide"
        ),
    },
    {
        "id": "weak-drop-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_ZERO),
        "refinement": (
            "computes the count correctly but omits the zero-total ↦ absence "
            "masking, reporting `some 0` where a valid aggregate is absent. A real "
            "patch that dropped the `.where(sum != 0)` step would emit a zero "
            "aggregate instead of the missing marker, changing the downstream "
            "normalization (a zero denominator instead of a NaN); it would not "
            "resolve the reductions over an all-absent slice."
        ),
        "rationale": (
            "REJECTED by `result = sowSpec mask weights`: on mask=[false], "
            "weights=[false] the aggregate total is 0, which the spec reports as "
            "`none`, but dropping the masking yields `some 0`. Attacks the "
            "zero-total ↦ none clause. If it VERIFIES => SPEC-TOO-WEAK (the absence "
            "masking is not enforced)."
        ),
        "witness": (
            "example : ¬ problem_spec_sumOfWeights [false] [false]\n"
            "    (implementation_sumOfWeights [false] [false]) := by\n"
            "  unfold problem_spec_sumOfWeights implementation_sumOfWeights sowSpec\n"
            "  decide"
        ),
    },
    {
        "id": "admiss-instantiate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _mk_admiss(),
        "rationale": (
            "the obligation's binder hypothesis `mask.length = weights.length` must "
            "be SATISFIABLE and the conclusion non-vacuous at real in-domain points. "
            "The frozen impl and proof are kept VERBATIM; the case only adds "
            "anonymous `example`s that apply `correct_sumOfWeights` at concrete "
            "length-matched pairs (discharging the hypothesis by `rfl`) and pin the "
            "value the impl produces there — `some 2` on mask=[true,true], "
            "weights=[true,true] and `none` on mask=[false], weights=[true], i.e. "
            "both branches of the zero-total masking. If it FAILS => "
            "PRECOND-TOO-STRONG (the precondition admits no normal input, or the "
            "obligation is vacuous where the aggregate is actually produced)."
        ),
    },
    {
        "id": "weak-misalign",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_MISALIGN),
        "refinement": (
            "the aggregate is formed over a MISALIGNED pairing: each weight is "
            "combined with the retention flag of the mirrored position instead of "
            "its own. A real patch that reduced the two arrays without honouring "
            "their shared index — pairing them in opposite order along the reduced "
            "dimension — would count weights against the wrong entries' presence, so "
            "it would report the right total only on symmetric inputs and would not "
            "resolve reductions over an asymmetric mask. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by `result = sowSpec mask weights`: on mask=[true,false], "
            "weights=[true,false] the aligned aggregate is 1 (position 0 is retained "
            "and set, so `some 1`), but pairing the reversed mask against the weights "
            "leaves no position with both flags set, yielding `none`. Attacks the "
            "POSITIONAL PAIRING clause — the one clause the other rivals leave "
            "standing, since each of them changes WHAT is accumulated rather than "
            "WHICH mask flag meets which weight. If it VERIFIES => SPEC-TOO-WEAK "
            "(the spec pins only the multiset of contributions, not their alignment)."
        ),
        "witness": (
            "example : ¬ problem_spec_sumOfWeights [true, false] [true, false]\n"
            "    (implementation_sumOfWeights [true, false] [true, false]) := by\n"
            "  unfold problem_spec_sumOfWeights implementation_sumOfWeights sowSpec\n"
            "  decide"
        ),
    },
    {
        "id": "weak-const-none",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_CONST_NONE),
        "refinement": (
            "returns the constant absence marker — what a real patch that "
            "short-circuited or dropped the reduction entirely would do. Correct only "
            "on the empty-aggregate sub-domain; on any input with a retained "
            "set-weight position it emits absence where a positive aggregate is "
            "required, failing the F2P reductions and the downstream mean. Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by `result = sowSpec mask weights`: on mask=[true,false], "
            "weights=[true,true] the aggregate is 1 (`some 1`), but the constant "
            "rival returns `none`. Attacks the `some`-of-positive-total clause. If "
            "it VERIFIES => SPEC-TOO-WEAK (a positive aggregate is not pinned)."
        ),
        "witness": (
            "example : ¬ problem_spec_sumOfWeights [true, false] [true, true]\n"
            "    (implementation_sumOfWeights [true, false] [true, true]) := by\n"
            "  unfold problem_spec_sumOfWeights implementation_sumOfWeights sowSpec\n"
            "  decide"
        ),
    },
]
