# properties.py — G-PBT falsification battery for matplotlib__matplotlib-24970 (lean).
#
# NOT a Lean module: a manifest of adversarially-reasoned cases the G-PBT runner
# executes and stamps with a recorded verdict. Every case is a full Solution.lean
# variant built by region surgery (`_swap`) that edits ONLY the impl region and,
# where a reshaped impl needs it, the proof body. The frozen spec regions
# (`axioms` / `pure` / `post-conditions`) stay byte-identical, so
# `markers.same_spec` holds by construction, the `theorem correct_index`
# STATEMENT is preserved verbatim, and no case introduces
# `sorry`/`admit`/`native_decide`/`axiom` or any new theorem/lemma. A rejection
# is therefore attributable to the postcondition, never to a tampered spec.
#
# ---------------------------------------------------------------------------
# PORT NOTE — carrier narrowing against the nagini sibling
# ---------------------------------------------------------------------------
# The nagini battery contracts a four-argument routine over two READ-ONLY input
# sequences held at a fractional permission, and its whole discriminator is a
# capability token granted only by a separately-contracted callee: on that
# carrier the modeled quantity is a SIDE EFFECT with no value-level footprint, so
# the token is what a value pin cannot express.
#
# This Lean bundle models the same behavior on a purely functional carrier, and
# that changes where the discriminator lives:
#
#   * the modeled function is `implementation_index (N M : Nat) (xs : List Int)`
#     returning `Except Unit (List Nat)`;
#   * the "assignment is not well-defined on this container" outcome — which
#     nagini could only express as a withheld token — is here a FIRST-CLASS
#     VALUE, `Except.error ()`. The spec's `∃ out, result = Except.ok out`
#     conjunct pins it directly;
#   * `M` (the input value type's capacity) is a plain `Nat` binder, so the
#     nagini "carrier" rivals become rivals over which bound the container
#     enforces;
#   * there is no answer-key callee to route through: `desiredIndex` is a `pure`
#     region fold spelled out over the actual input, so the value pin is grounded
#     and there is nothing to echo.
#
# DEFENDED SURFACE — the independent top-level clauses of `problem_spec_index`,
# each of which some rival below attacks:
#   C1  `∃ out, result = Except.ok out` — the conversion ALWAYS succeeds,
#       whatever the input value type's capacity `M` is. This is the clause the
#       nagini token stood in for, and it is the one the discriminating behavior
#       turns on.
#   C2  `out.length = xs.length` — one index per input value; nothing is dropped
#       or added.
#   C3  `∀ i < xs.length, out.getD i 0 = desiredIndex N (xs.getD i 0)` — the
#       POSITIONAL, per-element value pin: index `i` of the result is the exact
#       slot input `i` maps to. This carries three sub-behaviors a rival can
#       attack independently — the in-range identity, the `under` slot `N` for
#       `x < 0`, the `over` slot `N + 1` for `x ≥ N` — plus the ORDER in which
#       the results correspond to the inputs.
#
# INPUT BINDERS of the spec predicate and of the obligation: `N` (palette size),
# `M` (the input value type's capacity — present in the obligation and in the
# impl, deliberately ABSENT from the spec, which is exactly the claim "the answer
# must not depend on it"), and `xs` (the value list). The reject witnesses below
# vary all three: `N ∈ {1, 2, 3, 5}`, `M ∈ {3, 100}`, and `xs` over length 1 and
# 2 with negative / in-range / above-range / boundary contents. `M` matters most:
# a rival whose answer depends on `M` is refuted only at a small `M`, while a
# rival that is wrong regardless of `M` is refuted at a generous one — so the two
# capacity rivals are pinned at DIFFERENT `M` on purpose.
#
# OMITTED nagini cases, and why (repeated in the `assessment` payload):
#   * the two FRAME-MUTATION rivals (nagini rejects a write into either
#     half-permission input sequence for INSUFFICIENT PERMISSION) are VACUOUS on
#     this backend. Lean is referentially transparent: there is no aliasing and
#     no fractional permission, an input `List Int` cannot be written to, so
#     there is no counterpart rival to author. This is a collapsed class, not a
#     gap.
#   * the DIVERGENCE class is a KNOWN HOLE, not a collapsed class, and the
#     distinction matters (a collapsed class says this battery is complete; a hole
#     says the spec is not). A diverging rival IS expressible: `partial def
#     implementation_index N M xs := implementation_index N M xs` type-checks and
#     stays inside the variant scope. What cannot be built is a WITNESS against it.
#     Measured: a `partial def` is opaque to reduction, so `unfold
#     implementation_index` fails outright on the rival, and the conditioned form
#     (assume the diverging call returns some concrete value, refute from there)
#     also holds of the FROZEN solution — it is vacuous, not discriminating. So the
#     class cannot be shipped as a reject case here; it is recorded as a hole
#     against the spec rather than as an absent class.
#   * the ADMISSIBILITY positive DOES have a counterpart on this carrier and is
#     carried as `admiss-obligation-satisfiable-at-narrow-capacity`. It is true
#     that `correct_index` is an unconditional `∀ (N M : Nat) (xs : List Int)` with
#     no precondition hypothesis, but that is not a reason for the lane to be
#     vacuous: the analogue of PRECOND-TOO-STRONG on a total carrier is the
#     obligation being UNSATISFIABLE at a representative input, which a positive
#     that discharges the obligation at that concrete input by EVALUATION tests
#     directly. See that case's rationale.
#   * AXIOM_TESTS are dropped: the axiom lane is G-AX's job, and this bundle
#     consumes no callee axiom (the slot assignment is spelled out concretely).
#   * nagini's "fabricate the result without routing through the token-granting
#     callee" rival has no counterpart either: with no answer-key callee there is
#     nothing to bypass. Its ARGUMENT — that a value-correct result is not enough
#     — survives instead as `rival-container-one-short`, whose per-element values
#     are gold's on the whole sub-domain where it succeeds at all, and which C1
#     alone catches.
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24970"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — each lies ENTIRELY inside the impl or the proof region and is
# unique in the frozen file, so surgery cannot reach the spec.
# ---------------------------------------------------------------------------

# The two reserved-slot stores of the loop body (impl region).
_STORES = ("    if idx > (N : Int) - 1 then\n"
           "      idx := (N : Int) + 1\n"
           "    if idx < 0 then\n"
           "      idx := (N : Int)\n")
# The above-range guard alone.
_OVER_GUARD = "    if idx > (N : Int) - 1 then\n"
# The above-range store alone.
_OVER_STORE = "      idx := (N : Int) + 1\n"
# The per-element emit at the loop body tail.
_EMIT = "    out := out ++ [idx.toNat]\n"
# The whole loop body (stores + emit), for the structurally-different positive.
_LOOP_BODY = ("  for x in xs do\n"
              "    let mut idx : Int := x\n"
              "    -- send values above the valid range to the `over` slot first, "
              "then values\n"
              "    -- below it to the `under` slot\n"
              "    if idx > (N : Int) - 1 then\n"
              "      idx := (N : Int) + 1\n"
              "    if idx < 0 then\n"
              "      idx := (N : Int)\n"
              "    out := out ++ [idx.toNat]\n")

# --- proof-region anchors ---------------------------------------------------
# The frozen per-element body lemma, restated by the positive that reshapes the
# stores. Sliced by landmark so the whole lemma + obligation can be re-emitted.
_PROOF_FROM = "-- The desugared loop body equals a clean body that appends"
_PROOF_TO = "-- proof-end"
_CORRECT_FROM = "theorem correct_index :"

for _anchor in (_STORES, _OVER_GUARD, _OVER_STORE, _EMIT, _LOOP_BODY,
                _PROOF_FROM, _PROOF_TO, _CORRECT_FROM):
    if _BASE.count(_anchor) != 1:
        raise AssertionError(f"anchor not unique in frozen source: {_anchor!r}")

_HEAD = _BASE[:_BASE.index(_PROOF_FROM)]
_TAIL = _BASE[_BASE.index(_PROOF_TO):]

# The frozen accumulator lemma, carried verbatim by the positive that restates
# only the body lemma (identical name, identical statement — not a new lemma).
_HELPER = """theorem helper_index (N : Nat) (xs : List Int) (init : List Nat) :
    (Id.run (forIn xs init (fun x r =>
        ForInStep.yield (r ++ [desiredIndex N x]))) : List Nat)
      = init ++ xs.map (desiredIndex N) := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp [List.map_cons, List.append_assoc]
"""

# The frozen length + positional closing steps of `correct_index`.
_CLOSE = """  · simp
  · intro i hi
    rw [List.getD_eq_getElem?_getD, List.getD_eq_getElem?_getD]
    simp only [List.getElem?_map]
    rw [List.getElem?_eq_getElem hi]
    simp
"""


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (P1) STRUCTURALLY DIFFERENT, CORRECT — both guards read the ORIGINAL value and
# the `under` store is applied FIRST. The frozen impl applies the above-range
# store first and then re-tests the ALREADY-UPDATED local, which is what makes
# its order load-bearing; testing the untouched input value instead makes the two
# guards disjoint, so the order becomes free and the `under` store may go first.
# Observationally identical to gold, materially different control flow. The proof
# restates the SAME body lemma (`body_eq_index`, same name, new shape) and reuses
# the frozen accumulator lemma and closing steps unchanged.
_POS_GUARD_SOURCE = _HEAD + """-- The desugared loop body equals a clean body that appends `desiredIndex N x`.
theorem body_eq_index (N : Nat) (x : Int) (r : List Nat) :
    (if x < 0 then
        (if x > (N:Int) - 1 then ForInStep.yield (r ++ [((N:Int) + 1).toNat])
         else ForInStep.yield (r ++ [((N:Int)).toNat]))
      else
        (if x > (N:Int) - 1 then ForInStep.yield (r ++ [((N:Int) + 1).toNat])
         else ForInStep.yield (r ++ [x.toNat])))
      = ForInStep.yield (r ++ [desiredIndex N x]) := by
  have hidx : desiredIndex N x =
      (if x < 0 then
        (if x > (N:Int) - 1 then ((N:Int) + 1).toNat else ((N:Int)).toNat)
       else
        (if x > (N:Int) - 1 then ((N:Int) + 1).toNat else x.toNat)) := by
    unfold desiredIndex
    by_cases h1 : x < 0
    · have h2 : ¬ (x > (N:Int) - 1) := by omega
      simp only [h1, h2, if_true, if_false]
      omega
    · by_cases h2 : x > (N:Int) - 1
      · have h3 : (N:Int) ≤ x := by omega
        simp only [h1, h2, h3, if_true, if_false]
        omega
      · have h3 : ¬ ((N:Int) ≤ x) := by omega
        simp only [h1, h2, h3, if_false]
  rw [hidx]
  by_cases h1 : x < 0 <;> by_cases h2 : x > (N:Int) - 1 <;>
    simp only [h1, h2, if_true, if_false]

""" + _HELPER + """
theorem correct_index :
    ∀ (N M : Nat) (xs : List Int),
      problem_spec_index N xs (implementation_index N M xs) := by
  intro N M xs
  refine ⟨xs.map (desiredIndex N), ?_, ?_, ?_⟩
  · unfold implementation_index
    simp only [Id.run]
    have hbody : (forIn xs ([]:List Nat) (fun x r =>
        if x < 0 then do
          pure PUnit.unit
          if x > (N:Int) - 1 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)+1).toNat]))
            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
        else do
          pure PUnit.unit
          if x > (N:Int) - 1 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)+1).toNat]))
            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [x.toNat]))) : Id (List Nat))
      = (forIn xs ([]:List Nat) (fun x r =>
        ForInStep.yield (r ++ [desiredIndex N x])) : Id (List Nat)) := by
      congr 1
      funext x r
      simp only [bind, pure]
      exact body_eq_index N x r
    rw [hbody]
    have := helper_index N xs []
    simp only [Id.run] at this
    rw [this]; rfl
""" + _CLOSE + _TAIL
_POS_GUARD_SOURCE = _swap(
    _POS_GUARD_SOURCE, _STORES,
    "    if x < 0 then\n"
    "      idx := (N : Int)\n"
    "    if x > (N : Int) - 1 then\n"
    "      idx := (N : Int) + 1\n",
)

# (P2) CORRECT, LOCAL-VARIABLE RESHAPE of the range bound. The above-range guard
# compares against a named local rather than the inline expression, so the
# verifier must still see the same bound through the binding. Same values, same
# order, different code shape; the frozen proof body is kept verbatim (the
# `let` elaborates away). If this failed, the proof would be over-fit to the
# literal spelling of the bound rather than to its value.
_POS_LOCAL_BOUND = _swap(
    _BASE, _OVER_GUARD,
    "    let top : Int := (N : Int) - 1\n    if idx > top then\n",
)

# (P3) STRUCTURALLY DIFFERENT, CORRECT — the loop emits the shared `pure`-region
# slot map directly instead of reconstructing it with a mutable local and two
# conditional stores. This is the most distant admissible shape: the entire
# branching structure of the impl is gone. The proof drops the per-element body
# lemma (nothing left to normalize) and applies the frozen accumulator lemma to
# the loop directly; `body_eq_index` stays DECLARED and unchanged, so no
# obligation and no frozen lemma is removed. A spec that rejected this would be
# pinning the impl's branch structure rather than its input→output relation.
_ADMISS_INTRO = ("      problem_spec_index N xs (implementation_index N M xs) := by\n"
                 "  intro N M xs\n")

# (P4) ADMISSIBILITY. The frozen obligation carries no precondition hypothesis, so
# the nagini-shaped "the precondition admits a normal input" case has no literal
# counterpart — but the analogue on a TOTAL carrier does exist and is not vacuous:
# the obligation being UNSATISFIABLE at exactly the input the real-world regression
# exercises. That is a live risk here rather than a formality, because the whole
# discriminating behavior of this cell is that the conversion must SUCCEED
# (`Except.ok`) at a value type whose capacity cannot hold a reserved slot number,
# and `M` is a free binder the spec deliberately never mentions. A spec whose
# `∃ out, result = Except.ok out` conjunct were unreachable at that shape of input
# would be PRECOND-TOO-STRONG in the only sense this carrier has, and no positive
# above would notice: all three of them close the GENERAL obligation and never
# evaluate it anywhere.
#
# So this case discharges the obligation at that concrete point BY EVALUATION —
# palette size 256, an input value type of capacity exactly 256 (so neither
# reserved slot `256` nor `257` fits in `0 … 255`), and the single in-range value
# `0` whose own answer is slot `0` either way — as a `have` in front of the frozen
# proof, which then closes the frozen obligation VERBATIM. The `have` is discharged
# by `simp` after unfolding, so it is a real evaluation and not a restatement, and
# it is `clear`ed before the general proof begins so it cannot contribute to it:
# if the concrete instance were unsatisfiable the `have` would not close, and the
# case would fail while every other positive still passed.
_POS_ADMISS = _swap(
    _BASE, _ADMISS_INTRO,
    "      problem_spec_index N xs (implementation_index N M xs) := by\n"
    "  have hadm : problem_spec_index 256 [(0 : Int)]\n"
    "      (implementation_index 256 256 [(0 : Int)]) := by\n"
    "    unfold problem_spec_index implementation_index desiredIndex\n"
    "    simp\n"
    "  clear hadm\n"
    "  intro N M xs\n",
)

_POS_DIRECT_MAP = _swap(_BASE, _LOOP_BODY,
                        "  for x in xs do\n"
                        "    out := out ++ [desiredIndex N x]\n")
_POS_DIRECT_MAP = (_POS_DIRECT_MAP[:_POS_DIRECT_MAP.index(_CORRECT_FROM)]
                   + """theorem correct_index :
    ∀ (N M : Nat) (xs : List Int),
      problem_spec_index N xs (implementation_index N M xs) := by
  intro N M xs
  refine ⟨xs.map (desiredIndex N), ?_, ?_, ?_⟩
  · unfold implementation_index
    simp only [Id.run]
    have hbody : (forIn xs ([]:List Nat) (fun x r =>
        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [desiredIndex N x]))
          : Id (ForInStep (List Nat)))) : Id (List Nat))
      = (forIn xs ([]:List Nat) (fun x r =>
        ForInStep.yield (r ++ [desiredIndex N x])) : Id (List Nat)) := by
      congr 1
    rw [hbody]
    have := helper_index N xs []
    simp only [Id.run] at this
    rw [this]; rfl
""" + _CLOSE
                   + _POS_DIRECT_MAP[_POS_DIRECT_MAP.index(_PROOF_TO):])


# ===========================================================================
# UNIQUENESS RIVALS — expect "reject", each with a witness SEEN to discriminate
# ===========================================================================

# (U1) THE CANONICAL RIVAL — record the indices in a container that keeps the
# INPUT VALUE TYPE's capacity `M`, so a reserved slot number that does not fit in
# `0 … M - 1` cannot be recorded and the conversion FAILS. Attacks C1 directly.
_RIVAL_NARROW = _swap(
    _BASE, _EMIT,
    "    if idx ≥ (M : Int) then\n      return Except.error ()\n" + _EMIT,
)
# N = 2, M = 3: the `over` slot is 3, which does not fit in `0 … 2`. Gold widens
# and answers `[3]`; the rival cannot record it. `M` MUST be small here — at a
# generous `M` this rival agrees with gold everywhere, which is precisely the
# sub-domain claim its rationale makes.
#
# The `desiredIndex` unfold and the trailing `all_goals decide` are load-bearing,
# NOT decoration. Without them `simp` leaves the residual slot equation
# `¬3 = desiredIndex 2 5` unevaluated, and the gold-side build then fails with
# `unsolved goals` — the SAME error, byte for byte, that the OPPOSITE claim
# (`3 = desiredIndex 2 5`, i.e. "gold is wrong here") produces. Measured: both
# built at exit 1 with the goal differing only by the `¬` neither side discharged,
# so the gold exit code carried no information about the claim. Unfolding the slot
# map exposes an arithmetic goal and `decide` evaluates it, which makes the two
# outcomes split: the refutation gets `decide proved that the proposition False is
# false` (exit 1) while the flipped claim ELABORATES (exit 0). `all_goals` is used
# because `simp` already closes the goal outright against the rival, leaving
# `decide` nothing to do there.
_W_NARROW = """example : ¬ problem_spec_index 2 [(5 : Int)]
    (implementation_index 2 3 [(5 : Int)]) := by
  unfold problem_spec_index implementation_index desiredIndex
  simp
  all_goals decide
"""

# (U2) NEAR-MISS of U1 — the container is widened, but only far enough for the
# `under` slot `N`, not for the `over` slot `N + 1`. Agrees with gold on every
# in-range and every below-range value (verified: it satisfies the spec at
# `N = 2, xs = [-4]`), and fails only above the range. Attacks C1 on a strictly
# smaller sub-domain than U1, at a GENEROUS `M` — so the rejection cannot be
# blamed on a stingy capacity.
_RIVAL_ONE_SHORT = _swap(
    _BASE, _EMIT,
    "    if idx ≥ (N : Int) + 1 then\n      return Except.error ()\n" + _EMIT,
)
# Same evaluation requirement as `_W_NARROW`, for the same measured reason: with
# the slot map left folded, the gold-side failure is `unsolved goals
# ⊢ ¬3 = desiredIndex 2 5`, indistinguishable from the failure the flipped claim
# produces. Unfolding `desiredIndex` and deciding is what makes gold's exit code
# track what the witness actually asserts.
_W_ONE_SHORT = """example : ¬ problem_spec_index 2 [(5 : Int)]
    (implementation_index 2 100 [(5 : Int)]) := by
  unfold problem_spec_index implementation_index desiredIndex
  simp
  all_goals decide
"""

# (U3) RESERVED-SLOT STORE ORDER REVERSED. The frozen impl re-tests the local
# AFTER the above-range store, so applying the below-range store first makes the
# above-range test see a value the first store just wrote: a below-range value is
# sent to `N`, and `N > N - 1` then re-sends it to `N + 1`. Every above-range and
# in-range value is unaffected, so this is wrong ONLY on the below-range
# sub-domain. Attacks the `under`-slot arm of C3.
_RIVAL_STORE_ORDER = _swap(
    _BASE, _STORES,
    "    if idx < 0 then\n"
    "      idx := (N : Int)\n"
    "    if idx > (N : Int) - 1 then\n"
    "      idx := (N : Int) + 1\n",
)
_W_STORE_ORDER = """example : ¬ problem_spec_index 1 [(-1 : Int)]
    (implementation_index 1 100 [(-1 : Int)]) := by
  unfold problem_spec_index implementation_index desiredIndex
  simp
"""

# (U4) RANGE BOUNDARY OFF BY ONE — the above-range test admits the value `N`
# itself as an in-range index instead of sending it to the `over` slot. Wrong at
# exactly one value per palette size, correct everywhere else. Attacks the
# `over`-slot arm of C3 at its boundary.
_RIVAL_BOUNDARY = _swap(_BASE, _OVER_GUARD, "    if idx > (N : Int) then\n")
_W_BOUNDARY = """example : ¬ problem_spec_index 1 [(1 : Int)]
    (implementation_index 1 100 [(1 : Int)]) := by
  unfold problem_spec_index implementation_index desiredIndex
  simp
"""

# (U5) THE TWO RESERVED SLOTS COLLAPSED — above-range values are sent to the
# `under` slot `N` rather than to their own `over` slot `N + 1`. Both arms of the
# out-of-range behavior still produce a RESERVED slot of the right shape (and the
# result still has the right length and always succeeds), so only the per-element
# identity of the slot catches it. Attacks the `over`-slot arm of C3.
_RIVAL_SLOTS_COLLAPSED = _swap(_BASE, _OVER_STORE, "      idx := (N : Int)\n")
_W_SLOTS_COLLAPSED = """example : ¬ problem_spec_index 3 [(7 : Int)]
    (implementation_index 3 100 [(7 : Int)]) := by
  unfold problem_spec_index implementation_index desiredIndex
  simp
"""

# (U6) OUT-OF-RANGE VALUES DROPPED instead of mapped to a reserved slot — the
# emit happens only for values already inside the palette range. Every surviving
# element carries gold's value, so C3 is satisfied nowhere it is asked about the
# dropped ones; what breaks is the one-index-per-input pairing. Attacks C2 (and,
# through the positional shift, C3). The witness needs a MIXED list: with a
# single dropped element the result is empty and only the length clause speaks.
_RIVAL_DROP = _swap(
    _BASE, _STORES + _EMIT,
    "    if 0 ≤ idx ∧ idx ≤ (N : Int) - 1 then\n"
    "      out := out ++ [idx.toNat]\n",
)
# Same evaluation requirement as the two capacity witnesses. Left folded, the
# gold-side failure is the un-evaluated positional goal `∃ x < 2, ¬[0, 3][x]?.getD
# 0 = desiredIndex 2 ([0, 7][x]?.getD 0)`, and the flipped claim fails with the
# same shape carrying `∀` in place of `∃ ... ¬` — neither discharged, so gold's
# exit code said nothing about the claim. With the slot map unfolded and decided,
# the refutation gets `decide proved that the proposition ... is false` (exit 1)
# and the flipped claim elaborates (exit 0).
_W_DROP = """example : ¬ problem_spec_index 2 [(0 : Int), (7 : Int)]
    (implementation_index 2 100 [(0 : Int), (7 : Int)]) := by
  unfold problem_spec_index implementation_index desiredIndex
  simp
  all_goals decide
"""

# (U7) POSITIONAL CORRESPONDENCE BROKEN — each index is prepended rather than
# appended, so the result is the correct MULTISET of slot indices in reversed
# order. Length is right, every element is a legitimate slot index, the
# conversion succeeds; only the `∀ i, out.getD i 0 = desiredIndex N (xs.getD i 0)`
# pairing of C3 catches it. Invisible on any single-element or palindromic input,
# which is why the witness uses two distinct in-range values.
_RIVAL_REVERSED = _swap(_BASE, _EMIT, "    out := [idx.toNat] ++ out\n")
_W_REVERSED = """example : ¬ problem_spec_index 5 [(0 : Int), (1 : Int)]
    (implementation_index 5 100 [(0 : Int), (1 : Int)]) := by
  unfold problem_spec_index implementation_index desiredIndex
  simp
  decide
"""


SPEC_TESTS = [
    # ---------------- positive controls (must VERIFY) ----------------
    {"id": "pos-control-guard-source-order",
     "kind": "soundness", "expect": "verify",
     "module": _POS_GUARD_SOURCE,
     "rationale":
        "A CORRECT impl whose two reserved-slot guards both test the ORIGINAL "
        "input value (rather than the frozen impl's already-updated local) and "
        "which therefore applies the below-range store FIRST. Making the guards "
        "read the untouched value makes them disjoint, so the store order is "
        "free — observationally identical to gold on every binder, materially "
        "different control flow. The proof restates the per-element body lemma "
        "for the new shape (same lemma NAME and role; the frozen accumulator "
        "lemma and the length/positional closing steps are carried verbatim) and "
        "leaves the `theorem correct_index` statement byte-identical. Defends "
        "C1+C2+C3 together, over all of `N`, `M` and `xs`. If it were rejected, "
        "the proof would be over-fit to the frozen store ORDER rather than to "
        "the input→output relation => SPEC-TOO-STRONG."},
    {"id": "pos-control-local-bound",
     "kind": "soundness", "expect": "verify",
     "module": _POS_LOCAL_BOUND,
     "rationale":
        "A CORRECT impl that reaches the range bound through a named local "
        "instead of the inline expression. Same values, same order, different "
        "code shape; the frozen proof body is kept verbatim. Defends C3's "
        "in-range/above-range split. If it were rejected, the proof would be "
        "over-fit to the literal SPELLING of the bound rather than to its value "
        "=> SPEC-TOO-STRONG. This is the counterpart of the nagini "
        "local-variable-reshape positive."},
    {"id": "pos-control-direct-slot-map",
     "kind": "soundness", "expect": "verify",
     "module": _POS_DIRECT_MAP,
     "rationale":
        "The most distant admissible CORRECT shape: the loop emits the shared "
        "slot map for each value directly, so the mutable local and BOTH "
        "conditional stores are gone — the impl's entire branching structure "
        "differs from gold's while the input→output relation is identical. The "
        "proof applies the frozen accumulator lemma to the loop directly; every "
        "frozen lemma stays declared and the obligation statement is unchanged. "
        "Defends C1+C2+C3. If it were rejected, the spec (or the proof it "
        "admits) would be pinning the impl's branch STRUCTURE rather than its "
        "behavior => SPEC-TOO-STRONG. This is the nagini statement-reorder "
        "positive's argument, taken as far as this carrier allows."},
    {"id": "admiss-obligation-satisfiable-at-narrow-capacity",
     "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale":
        "PRECOND-TOO-STRONG probe. The frozen obligation is an unconditional "
        "`∀ (N M : Nat) (xs : List Int)` with no precondition hypothesis, so the "
        "nagini precondition-admits-a-normal-input case has no literal "
        "counterpart; the analogue on a TOTAL carrier is the obligation being "
        "UNSATISFIABLE at a representative input, which this case tests directly. "
        "It discharges `problem_spec_index` BY EVALUATION at the concrete point "
        "the real-world regression exercises — palette size 256, an input value "
        "type of capacity exactly 256 (so neither reserved slot `256` nor `257` "
        "fits in `0 … 255`), a single in-range value `0` — as a `have` before the "
        "frozen obligation is closed verbatim, then `clear`s it so it cannot "
        "contribute to the general proof. This is the one case that EVALUATES the "
        "spec rather than closing it generically: the other three positives would "
        "all still pass if C1 (`∃ out, result = Except.ok out`) were unreachable "
        "at exactly that shape of input. If the `have` failed to close => "
        "PRECOND-TOO-STRONG (the obligation rejects the very input the "
        "discriminating behavior turns on)."},

    # ---------------- uniqueness rivals (must be REJECTED) ----------------
    {"id": "rival-container-keeps-input-capacity",
     "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NARROW,
     "refinement":
        "This is the pre-patch shape: the indices are recorded in a container "
        "that keeps the INPUT value type's capacity `M`, so a reserved slot "
        "number outside `0 … M - 1` cannot be stored and the conversion is "
        "rejected. A faithful real patch of this shape leaves the narrow "
        "container in place, so the reserved-slot store is still out of range "
        "and the F2P test — which asks that a value of the narrow type give the "
        "same answer as the same value of the default type, under a "
        "configuration that escalates the resulting diagnostic — would NOT "
        "resolve. Note the F2P input's own ANSWER is unchanged by this rival "
        "(value 0 maps to slot 0 either way): the discriminating behavior is "
        "whether the reserved-slot store succeeds at all, which is exactly what "
        "C1 pins. So a verifying rival here would be a true "
        "verify-does-not-imply-resolve break.",
     "rationale":
        "Rejection source: C1, `∃ out, result = Except.ok out`. Witness at "
        "`N = 2, M = 3, xs = [5]`: the `over` slot is `3`, which does not fit in "
        "`0 … 2`, so the rival answers `Except.error ()` while the spec demands "
        "`Except.ok [3]`. `M` is pinned SMALL on purpose — at a generous `M` "
        "this rival agrees with gold everywhere, so the witness is placed exactly "
        "in the sub-domain the rival is wrong on, and it varies the `M` binder "
        "that no other witness stresses. If it verified => SPEC-TOO-WEAK (the "
        "spec would admit a conversion that fails on a narrow input type).",
     "witness": _W_NARROW},
    {"id": "rival-container-one-slot-short",
     "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ONE_SHORT,
     "refinement":
        "Widen the container, but only far enough for the `under` slot `N` — one "
        "short of the `over` slot `N + 1`. A faithful real patch of this shape "
        "still cannot record the above-range reserved slot, so the out-of-range "
        "store still fails and the F2P would NOT resolve; and in ordinary use "
        "any value above the palette range would be rejected rather than shown "
        "in its reserved color, breaking the sibling dtype cases the P2P list "
        "carries. This is the off-by-one widening, the nagini "
        "carrier-one-short rival's counterpart.",
     "rationale":
        "Rejection source: C1 again, but on a strictly SMALLER sub-domain than "
        "`rival-container-keeps-input-capacity`, so it gets its own witness "
        "rather than sharing one: this rival SATISFIES the spec at `N = 2, "
        "xs = [-4]` (below-range values need only the `under` slot `N`, which does "
        "fit) and at every in-range value. Note the sub-domain comparison is "
        "SMALLER-in-M, not smaller-overall: measured by evaluation, this rival "
        "diverges from gold at 7 of 9 probe points while the capacity rival "
        "diverges at only 2, because this one's bound is enforced at every `M` "
        "whereas that one's bites only where `M` is small. Witness at "
        "`N = 2, M = 100, xs = [5]`: refuted at a GENEROUS `M`, so the rejection "
        "is attributable to the bound the impl itself enforces and not to a "
        "stingy input capacity. If it verified => SPEC-TOO-WEAK.",
     "witness": _W_ONE_SHORT},
    {"id": "rival-reserved-store-order-reversed",
     "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_STORE_ORDER,
     "refinement":
        "Apply the below-range store BEFORE the above-range one. Because the "
        "second guard re-tests the value the first store just wrote, a "
        "below-range value is first sent to the `under` slot `N` and then, since "
        "`N` is itself above the last palette index, re-sent to the `over` slot "
        "`N + 1`. A faithful real patch of this shape resolves nothing: the "
        "conversion still succeeds and still has the right length, so the F2P "
        "value (0, in range) is unaffected and the test would pass, while every "
        "below-range value would silently get the WRONG reserved color — "
        "breaking the below-range behavior the P2P suite covers. Correct on a "
        "sub-domain only, exactly the nagini partial-domain rival's argument.",
     "rationale":
        "Rejection source: the `under`-slot arm of C3. Witness at "
        "`N = 1, M = 100, xs = [-1]`: the spec demands slot `1` (the `under` "
        "slot) and the rival yields `2`. Distinct binder point from every other "
        "witness — it is the only one that probes a NEGATIVE input value, so "
        "without it a rival that mishandled only the below-range arm would go "
        "unnoticed. If it verified => SPEC-TOO-WEAK.",
     "witness": _W_STORE_ORDER},
    {"id": "rival-range-boundary-off-by-one",
     "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BOUNDARY,
     "refinement":
        "Shift the above-range test by one, so the first value PAST the palette "
        "range is treated as an ordinary in-range index instead of being sent to "
        "the `over` slot. A faithful real patch of this shape leaves the widening "
        "in place, so the F2P's diagnostic-free requirement is met and that test "
        "would pass — but the value at the boundary would index one past the "
        "last palette entry, giving the wrong color for it and breaking ordinary "
        "above-range use covered by the P2P suite. So it would NOT resolve the "
        "full suite even though the F2P alone cannot see it.",
     "rationale":
        "Rejection source: the `over`-slot arm of C3, at its boundary. Witness "
        "at `N = 1, M = 100, xs = [1]`: value `1` is the first value past a "
        "one-color palette, so the spec demands the `over` slot `2` and the rival "
        "yields `1`. This is the only witness pinned at the exact boundary "
        "`x = N`, a point every other rival gets right. If it verified => "
        "SPEC-TOO-WEAK.",
     "witness": _W_BOUNDARY},
    {"id": "rival-reserved-slots-collapsed",
     "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SLOTS_COLLAPSED,
     "refinement":
        "Send above-range values to the below-range reserved slot instead of to "
        "their own. A faithful real patch of this shape widens the container "
        "correctly (so the F2P's diagnostic never fires and that test passes) "
        "and still produces one legitimate reserved slot number per out-of-range "
        "value — but the two reserved slots are configured independently, so "
        "above-range values would be shown in the below-range color, breaking "
        "the P2P cases that assert the two are distinguishable. NOT a resolve.",
     "rationale":
        "Rejection source: the per-element IDENTITY of the reserved slot in C3. "
        "C1 and C2 are both satisfied (the conversion succeeds with the right "
        "length) and every emitted value is a real reserved slot, so only the "
        "value pin catches it — the analogue of nagini's point that a "
        "shape-correct result is not a correct one. Witness at "
        "`N = 3, M = 100, xs = [7]`: the spec demands the `over` slot `4`, the "
        "rival yields `3`. A distinct `N` from every other witness, and the only "
        "one that separates the two reserved slots from each other. If it "
        "verified => SPEC-TOO-WEAK.",
     "witness": _W_SLOTS_COLLAPSED},
    {"id": "rival-out-of-range-values-dropped",
     "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP,
     "refinement":
        "Emit an index only for values already inside the palette range, "
        "dropping the rest rather than mapping them to a reserved slot. A "
        "faithful real patch of this shape produces a SHORTER result than its "
        "input, so downstream lookup receives the wrong number of entries and "
        "the positions after the first out-of-range value are misaligned. The "
        "F2P input is a single in-range value, so nothing is dropped and that "
        "test would pass; every P2P case involving an out-of-range value breaks. "
        "NOT a resolve.",
     "rationale":
        "Rejection source: C2, `out.length = xs.length` (and, through the "
        "positional shift, C3) — the only rival that attacks the length clause, "
        "so without it a rival that returned a shorter list would never be "
        "caught. Witness at `N = 2, M = 100, xs = [0, 7]`: the spec demands two "
        "indices `[0, 3]`, the rival yields one. The witness needs a MIXED list "
        "(one in-range value, one above it) — with a single dropped element the "
        "result is empty and the failure would not exhibit the misalignment. It "
        "is also the only witness at a length-2 list with values from different "
        "arms. If it verified => SPEC-TOO-WEAK.",
     "witness": _W_DROP},
    {"id": "rival-positional-order-reversed",
     "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_REVERSED,
     "refinement":
        "Prepend each index instead of appending it, so the result is the right "
        "multiset of slot indices in the wrong ORDER. A faithful real patch of "
        "this shape returns the correct number of correct slot numbers, the "
        "conversion always succeeds, and it is invisible on the single-element "
        "F2P input — that test would pass. But every multi-element use would get "
        "its colors in reverse, so it would NOT resolve the suite. This is the "
        "sharpest form of the nagini value-proxy argument on this carrier: "
        "getting the right VALUES is not getting the right ANSWER.",
     "rationale":
        "Rejection source: the POSITIONAL quantifier of C3, "
        "`∀ i < xs.length, out.getD i 0 = desiredIndex N (xs.getD i 0)`. C1 and "
        "C2 hold and every element is a legitimate slot index, so the "
        "input↔output PAIRING is the only clause that refutes it — the one "
        "structural property a multiset-level spec would have missed. Witness at "
        "`N = 5, M = 100, xs = [0, 1]`: two DISTINCT in-range values are needed "
        "(any single-element or palindromic input satisfies the rival), and the "
        "spec demands `[0, 1]` where the rival gives `[1, 0]`. If it verified => "
        "SPEC-TOO-WEAK.",
     "witness": _W_REVERSED},
]
