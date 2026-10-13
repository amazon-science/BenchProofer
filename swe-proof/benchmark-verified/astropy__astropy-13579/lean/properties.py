# properties.py — G-PBT falsification battery for astropy__astropy-13579 (lean lane).
#
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case
# is a FULL Solution.lean variant sharing the FROZEN spec byte-for-byte (only the
# impl region — and, for a positive that reproves, the proof body — is edited),
# checked by variant_scope + the Lean verifier. Every expect="reject" case carries
# a refutation `witness`: a self-contained snippet that ELABORATES against the
# rival and FAILS on the frozen solution, so the rejection is attributable to the
# spec rather than to a frozen tactic script that merely stopped matching a
# reshaped impl.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json)
# ---------------------------------------------------------------------------
# ONE obligation:
#
#   theorem correct_assemble :
#     ∀ (worldNDim : Nat) (worldKeep : List Nat) (inputs slicedOut : List Int),
#       worldKeep.Sorted (· < ·) → (∀ i ∈ worldKeep, i < worldNDim) →
#       inputs.length = worldKeep.length → slicedOut.length = worldNDim →
#       problem_spec_assemble worldNDim worldKeep inputs slicedOut
#         (implementation_assemble worldNDim worldKeep inputs slicedOut)
#
# `implementation_assemble` rebuilds a full-length coordinate vector for an
# underlying system of `worldNDim` axes from a reduced vector that supplies only
# the `worldKeep` axes. `problem_spec_assemble` has THREE independent top-level
# clauses, and every rival below is aimed at exactly one of them:
#
#   (C1) LENGTH / FRAME:   `result.length = worldNDim`
#        one entry per underlying axis, no more and no fewer.
#   (C2) OMITTED AXES:     `∀ iworld < worldNDim, iworld ∉ worldKeep →
#                            result.getD iworld 0 = slicedOut.getD iworld 0`
#        an axis absent from the reduced view carries the REFERENCE value for
#        THAT AXIS NUMBER. This is the DISCRIMINATING clause — it is the single
#        behaviour the fix establishes, and the pre-patch skeleton in
#        Solution_prepatch.lean fails precisely here (see refinement.md).
#   (C3) KEPT AXES:        `∀ c < worldKeep.length,
#                            result.getD (worldKeep.getD c 0) 0 = inputs.getD c 0`
#        the c-th kept axis carries the c-th supplied value — i.e. the supplied
#        values are consumed left-to-right, POSITIONALLY, and land at the axis
#        numbers `worldKeep` names.
#
# CARRIER CORRESPONDENCE vs nagini. The nagini sibling contracted TWO functions:
# an assembly step and a second function feeding the assembled vector to an
# opaque downstream transform, stated as
# `Result == full_world_to_pixel(ref_world_vector(..), dim)`. This bundle models
# ONLY the assembly (see mapping.md "Modeled scope": the downstream transform is
# unchanged and out of scope), so nagini's two `mask-recovered-*` rivals — which
# attack the ARGUMENT handed to that transform — have no second function to
# attack here. That is carrier narrowing, not a gap in coverage: the assembled
# vector IS the observable those rivals corrupted, and it is pinned outright by
# C1+C2+C3 rather than through an opaque callee. Independently confirmed by proof
# (see below): C1+C2+C3 determine `result` UNIQUELY, so nothing a mask rival
# could feed downstream is left unpinned by the three clauses.
#
# Everything on this carrier is TRANSPARENT (`Nat`, `List Int`, `List.getD`), so
# no witness needs to condition on an opaque term: every refutation is stated at
# concrete literal inputs and closed by `decide` after the do-loop is reduced.
# Consequently no witness binds anything and the gate's consistency probe is
# vacuously satisfied — there are no hypotheses that could be inconsistent.
#
# Each witness input point additionally lies INSIDE the obligation's precondition
# domain (`worldKeep` strictly sorted, every kept axis `< worldNDim`,
# `inputs.length = worldKeep.length`, `slicedOut.length = worldNDim`), so each
# rival is refuted at an input a legitimate caller can actually present — a rival
# refuted only out of domain would attribute nothing.
#
# ---------------------------------------------------------------------------
# LANES THAT DO NOT PORT
# ---------------------------------------------------------------------------
#   * FRAME/PERMISSION MUTATION. The nagini sibling marks this MANDATORY (two
#     cases: writing into a read-only supplied list, and writing into the
#     read-only kept-axis flag vector), because its three inputs were held at a
#     FRACTIONAL permission and the rivals made the fills "match" by side effect.
#     Lean is referentially transparent — no aliasing, no fractional permission,
#     no store into an input — so the class is genuinely VACUOUS on this carrier
#     and there is nothing to substitute. The frame OBLIGATION itself does port:
#     it lives in C1 (the result's length is pinned, so no axis may be added or
#     lost) and in the positional character of C2/C3 (every slot's value is
#     pinned to a named input entry, so no slot may carry an invented value),
#     and it is attacked by `weak-drop-last-axis` / `weak-extra-axis` (C1) and by
#     the seven value-placement rivals (C2/C3).
#   * DIVERGENCE / NON-TERMINATION. The nagini sibling carries NO `diverge-*` /
#     `nonterm-*` / `weak-diverge` case, so there is nothing to port; and on lean
#     the class is vacuous regardless, since `implementation_assemble` is a total
#     Lean `def` and a diverging implementation cannot be written at all. This is
#     the lean disposition, NOT the velvet `partial`-semantics known-spec-hole one
#     (the corpus-wide termination-semantics finding); no hole is being papered over here.
#   * VALUE-LEVEL MASK (nagini's two `mask-recovered-*`). Both attack the vector
#     handed to the opaque downstream transform, which this bundle does not model
#     (mapping.md "Modeled scope"), so there is no second function to corrupt.
#     What made them bite on nagini was that the transform was OPAQUE, so a rival
#     could feed it a different vector and not be provably equal to the required
#     value. Here the assembled vector is the modeled observable itself, and it is
#     pinned outright — see the uniqueness result below — so the class has no
#     residue: any impl the spec accepts produces the SAME vector gold does, hence
#     feeds any downstream transform the same argument.
#
# ---------------------------------------------------------------------------
# WHY SPEC-TOO-WEAK IS CLOSED BY PROOF, NOT ONLY BY SAMPLING
# ---------------------------------------------------------------------------
# The three clauses are jointly FUNCTIONAL: C2 pins every omitted position and C3
# every retained one, so `problem_spec_assemble` has at most one solution at every
# input — and it needs none of the four preconditions to do so. Proven during audit
# (Lean, elaborated clean, not shipped in the bundle):
#
#   theorem spec_unique (worldNDim) (worldKeep) (inputs slicedOut r1 r2)
#       (h1 : problem_spec_assemble worldNDim worldKeep inputs slicedOut r1)
#       (h2 : problem_spec_assemble worldNDim worldKeep inputs slicedOut r2) :
#       r1 = r2
#
# with the corollary (composed with `correct_assemble`) that any `r` the spec
# accepts on the precondition domain equals `implementation_assemble` there. So
# there is no wrong impl for a SPEC-TOO-WEAK probe to find: the rivals below are
# not a sample hoping to cover the space, they are witnesses that the pinning is
# reachable by the verifier at concrete inputs. Three further rivals not in this
# battery (whole result reversed; backwards accumulation by prepending; the wider
# arity tuning now landed as `weak-tuned-to-small-arities`) were built and each is
# refuted, consistent with that theorem.
#
# The opposite direction was probed too: a CORRECT reshape with a genuinely
# different shape — a non-monadic `(List.range worldNDim).map` with the kept-index
# computed as a `countP` rather than carried in a mutable cursor — verifies against
# the frozen spec with a pointwise proof, so the spec is not over-fit to the
# do-loop form either. Both `expect="verify"` positives below make the weaker
# version of that point with proofs that stay near the frozen argument.
#   * AXIOM_TESTS. The nagini sibling carries two (soundness + containment for
#     its one `@ContractOnly` downstream transform). The axiom lane is G-AX's job
#     and this gate ignores them. On this backend there is no consumed callee
#     axiom at all (refinement.md: "No axioms are declared or consumed"; the
#     reference vector is an INPUT, and axiom_check.py is a skip stub), so the
#     lane is empty here for a second, independent reason.
from pathlib import Path

INSTANCE = "astropy__astropy-13579"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Every anchor lies ENTIRELY inside the region it names and is
# unique in the frozen file, so the manifest breaks LOUDLY (AssertionError at
# import) if the frozen solution ever drifts.
# ---------------------------------------------------------------------------

# The whole executable body, strictly inside impl-start/impl-end. Every rival and
# both soundness positives swap THIS block (or a sub-slice of it).
_IMPL = (
    "  let mut result : List Int := []\n"
    "  let mut iworldCurr : Nat := 0\n"
    "  for iworld in [0:worldNDim] do\n"
    "    if iworld ∈ worldKeep then\n"
    "      result := result ++ [inputs.getD iworldCurr 0]\n"
    "      iworldCurr := iworldCurr + 1\n"
    "    else\n"
    "      result := result ++ [slicedOut.getD iworld 0]\n"
    "  return result"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted"

# The per-axis branch alone (a sub-slice of _IMPL): the value-selection decision.
_SELECT = (
    "    if iworld ∈ worldKeep then\n"
    "      result := result ++ [inputs.getD iworldCurr 0]\n"
    "      iworldCurr := iworldCurr + 1\n"
    "    else\n"
    "      result := result ++ [slicedOut.getD iworld 0]"
)
assert _BASE.count(_SELECT) == 1, "select anchor drifted"

# --- proof-region anchors (swapped ONLY by the two soundness positives, whose
# --- reshaped impls need an honest reproof of the byte-identical statement) ---

# The `forIn` normal form the frozen `impl_as_swapped_fold` bridge lemma states.
# It mirrors the impl's branch shape, so a positive that reshapes that branch must
# reshape this too.
_PROOF_FORIN = (
    "      (forIn L (⟨n, acc⟩ : MProd Nat (List Int)) fun iworld r =>\n"
    "        (if iworld ∈ worldKeep then pure (ForInStep.yield ⟨r.fst + 1, r.snd ++ [inputs.getD r.fst 0]⟩)\n"
    "         else pure (ForInStep.yield ⟨r.fst, r.snd ++ [slicedOut.getD iworld 0]⟩) : Id _)).run.snd"
)
assert _BASE.count(_PROOF_FORIN) == 1, "proof forIn anchor drifted"

# The bridge lemma's cons step, which discharges the two branches.
_PROOF_CASES = (
    "      by_cases h : a ∈ worldKeep\n"
    "      · simp only [h, if_true]\n"
    "        exact ih (n + 1) (acc ++ [inputs.getD n 0])\n"
    "      · simp only [h, if_false]\n"
    "        exact ih n (acc ++ [slicedOut.getD a 0])"
)
assert _BASE.count(_PROOF_CASES) == 1, "proof cases anchor drifted"

# The step that normalizes the impl's bounded-range loop into `List.range'`.
_PROOF_RANGE = (
    "  simp only [implementation_assemble, Id.run, Std.Range.forIn_eq_forIn_range', Std.Range.size,\n"
    "    Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]\n"
    "  exact key (List.range' 0 worldNDim) 0 []"
)
assert _BASE.count(_PROOF_RANGE) == 1, "proof range anchor drifted"

# The obligation's `intro` line — the admissibility case appends a satisfiability
# check after it and leaves the rest of the frozen proof untouched.
_PROOF_INTRO = "  intro worldNDim worldKeep inputs slicedOut hsorted hmem hinlen hsllen\n"
assert _BASE.count(_PROOF_INTRO) == 1, "proof intro anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-negated-guard: the per-axis decision is rewritten with the guard NEGATED and
# the two branches SWAPPED. Behaviourally identical at every input (same value at
# every slot, same left-to-right consumption of the supplied vector, same forward
# accumulation). The theorem STATEMENT is byte-identical; the proof is reproven
# honestly by reshaping the bridge lemma's `forIn` normal form and its two-branch
# `simp only` to match the new guard — the SAME argument, no new lemma, no new
# axiom, no `sorry`. This is the port of nagini's `pos-assemble-branch-reorder`.
_POS_NEGATED = _swap(
    _swap(
        _swap(
            _BASE, _SELECT,
            "    if iworld ∉ worldKeep then\n"
            "      result := result ++ [slicedOut.getD iworld 0]\n"
            "    else\n"
            "      result := result ++ [inputs.getD iworldCurr 0]\n"
            "      iworldCurr := iworldCurr + 1"),
        _PROOF_FORIN,
        "      (forIn L (⟨n, acc⟩ : MProd Nat (List Int)) fun iworld r =>\n"
        "        (if iworld ∉ worldKeep then pure (ForInStep.yield ⟨r.fst, r.snd ++ [slicedOut.getD iworld 0]⟩)\n"
        "         else pure (ForInStep.yield ⟨r.fst + 1, r.snd ++ [inputs.getD r.fst 0]⟩) : Id _)).run.snd"),
    _PROOF_CASES,
    "      by_cases h : a ∈ worldKeep\n"
    "      · simp only [h, not_true, if_false, if_true]\n"
    "        exact ih (n + 1) (acc ++ [inputs.getD n 0])\n"
    "      · simp only [h, not_false, if_true, if_false]\n"
    "        exact ih n (acc ++ [slicedOut.getD a 0])",
)

# pos-explicit-axis-list: the loop walks an explicitly materialized list of the
# underlying axis numbers instead of the bounded range. Same axes, same order,
# same body — identical output at every input. Reproven honestly: only the step
# that normalizes the loop's index source changes (the bounded-range normal form
# is replaced by the list one), and the rest of the frozen argument is reused
# verbatim. No new lemma / axiom / `sorry`. If either positive FAILS =>
# SPEC-TOO-STRONG (the postcondition would be over-fit to the frozen loop shape
# rather than pinning the behaviour). This is the port of nagini's
# `pos-recovered-inline` argument (a behaviour-preserving reshape must verify),
# re-aimed at the one function this bundle models.
_POS_RANGE_LIST = _swap(
    _swap(_BASE,
          "  for iworld in [0:worldNDim] do",
          "  for iworld in List.range worldNDim do"),
    _PROOF_RANGE,
    "  simp only [implementation_assemble, Id.run, List.range_eq_range']\n"
    "  exact key (List.range' 0 worldNDim) 0 []",
)

# admiss-precond-satisfiable: the frozen impl and the frozen proof argument, with
# TWO `have`s inserted, both at the SAME concrete input — the shape a legitimate
# caller of the modeled behaviour actually presents (3 underlying axes, the two
# LEADING axes retained and the trailing one omitted, two supplied values, a
# 3-entry reference vector):
#
#   (i)  `_precond_admissible` discharges all four precondition hypotheses there
#        BY EVALUATION. If the precondition set were contradictory — sortedness
#        against the axis bound, or the two length constraints against each other
#        — it could not close, which is exactly PRECOND-TOO-STRONG: an obligation
#        vacuously true because no caller can enter its domain.
#   (ii) `_obligation_at_that_input` discharges the OBLIGATION ITSELF at that same
#        input, again by evaluation, before the frozen argument closes the general
#        goal verbatim. This is the half that makes the lane bite on a total
#        carrier: a satisfiable precondition set is necessary but not sufficient,
#        because the obligation could still be UNSATISFIABLE at an admitted point
#        (no `result` meeting all three clauses), and then the frozen theorem
#        would be unprovable rather than vacuous. Discharging it concretely rules
#        that out at the one input the lane most needs to cover.
#
# That the precondition really is load-bearing (so the lane is not decorative) is
# independently the case: OUT of the domain — `worldKeep = [0, 0]`, which fails
# strict sortedness — C3 demands both `result.getD 0 0 = 5` and
# `result.getD 0 0 = 8`, so NO result satisfies the spec at all. Port of nagini's
# `admiss-recovered-precond`; the lean obligation really does carry four
# preconditions as binder hypotheses, so unlike most Lean-family bundles this
# lane is not vacuous here.
_ADMISS = _swap(
    _BASE, _PROOF_INTRO,
    "  intro worldNDim worldKeep inputs slicedOut hsorted hmem hinlen hsllen\n"
    "  have _precond_admissible :\n"
    "      ([0, 1] : List Nat).Sorted (· < ·) ∧\n"
    "      (∀ i ∈ ([0, 1] : List Nat), i < 3) ∧\n"
    "      ([5, 6] : List Int).length = ([0, 1] : List Nat).length ∧\n"
    "      ([3, 9, 4] : List Int).length = 3 := by\n"
    "    refine ⟨?_, ?_, rfl, rfl⟩\n"
    "    · decide\n"
    "    · decide\n"
    "  have _obligation_at_that_input :\n"
    "      problem_spec_assemble 3 [0, 1] [5, 6] [3, 9, 4]\n"
    "        (implementation_assemble 3 [0, 1] [5, 6] [3, 9, 4]) := by\n"
    "    unfold problem_spec_assemble implementation_assemble\n"
    "    simp [Id.run, bind, pure, List.range', List.forIn_cons, List.forIn_nil]\n"
    "    all_goals decide\n",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is
# left in place (it will not close for the reshaped impl, but the gate reads the
# WITNESS — checked in a file with the obligation removed — not the rival's own
# build).
# ===========================================================================

def _riv(new_impl):
    return _swap(_BASE, _IMPL, new_impl)


# --- C2 (omitted axes): the discriminating clause --------------------------

# weak-omitted-constant: every omitted axis is filled with a FIXED CONSTANT rather
# than its reference value. Correct on every KEPT axis; wrong on every omitted axis
# whose reference value is not that constant. This is the pre-patch behaviour
# (Solution_prepatch.lean, refinement.md "Independently-observable behavior").
_RIV_CONST = _riv(_IMPL.replace(
    "      result := result ++ [slicedOut.getD iworld 0]",
    "      result := result ++ [(1 : Int)]"))

# weak-omitted-uses-supplied: an omitted axis takes the NEXT SUPPLIED value
# instead of its reference value (a subtler wrong fill: it reads a real input, just
# the wrong one). Indistinguishable from gold on kept axes.
_RIV_USES_SUPPLIED = _riv(_IMPL.replace(
    "      result := result ++ [slicedOut.getD iworld 0]",
    "      result := result ++ [inputs.getD iworldCurr 0]"))

# weak-omitted-cursor-index: an omitted axis takes the reference value at the
# KEPT-COUNT cursor rather than at its own axis number. Reads the right vector at
# the wrong offset, so it AGREES with gold whenever the cursor happens to equal the
# axis number (e.g. every input whose omitted axes all precede the kept ones) — a
# near miss that the two rivals above do not cover.
_RIV_CURSOR_INDEX = _riv(_IMPL.replace(
    "      result := result ++ [slicedOut.getD iworld 0]",
    "      result := result ++ [slicedOut.getD iworldCurr 0]"))

# --- C3 (kept axes): positional consumption of the supplied vector --------

# weak-kept-axis-index: a kept axis takes the supplied value at its own AXIS
# NUMBER instead of at its position among the kept axes. Agrees with gold whenever
# the kept axes are exactly the leading ones (the cursor equals the axis number),
# wrong as soon as an omitted axis precedes a kept one.
_RIV_KEPT_AXIS_INDEX = _riv(_IMPL.replace(
    "[inputs.getD iworldCurr 0]", "[inputs.getD iworld 0]"))

# weak-kept-values-reversed: the supplied values are consumed RIGHT-TO-LEFT
# instead of left-to-right. Every kept axis still receives a supplied value and
# every omitted axis its reference value, and the result has the right length —
# only the ORDER of the positional correspondence in C3 is inverted, which the two
# index rivals above (both of which preserve left-to-right order on their agreeing
# sub-domains) do not attack.
_RIV_KEPT_REVERSED = _riv(_IMPL.replace(
    "[inputs.getD iworldCurr 0]", "[inputs.reverse.getD iworldCurr 0]"))

# weak-keep-test-positional: replaces the MEMBERSHIP test with a positional proxy
# ("this axis is retained iff its number is below the retained count"). Agrees with
# gold on every input whose retained axes are exactly the leading ones, and
# misclassifies both kinds of axis — omitted and kept — as soon as they are not.
# Attacks C2 and C3 jointly through the branch CONDITION rather than either
# branch's value, which no other rival here does.
_RIV_KEEP_POSITIONAL = _riv(_IMPL.replace(
    "if iworld ∈ worldKeep then", "if iworld < worldKeep.length then"))

# --- C1 (length / frame) --------------------------------------------------

# weak-first-axis-forced: correct at every axis except axis 0, which is forced to a
# fixed value regardless of whether it is retained. A PARTIAL-DOMAIN rival: the
# per-axis decision is right everywhere else, so it survives any refutation aimed
# only at a later axis. Port of nagini's `partial-first-slot-wrong`.
_RIV_FIRST_AXIS = _riv(
    "  let mut result : List Int := []\n"
    "  let mut iworldCurr : Nat := 0\n"
    "  for iworld in [0:worldNDim] do\n"
    "    if iworld = 0 then\n"
    "      result := result ++ [(0 : Int)]\n"
    "    else if iworld ∈ worldKeep then\n"
    "      result := result ++ [inputs.getD iworldCurr 0]\n"
    "      iworldCurr := iworldCurr + 1\n"
    "    else\n"
    "      result := result ++ [slicedOut.getD iworld 0]\n"
    "  return result")

# weak-drop-last-axis: an off-by-one over the underlying axes — every emitted entry
# is correct, but the LAST axis is never emitted, so the vector is one entry short.
_RIV_DROP_LAST = _riv(_IMPL.replace(
    "for iworld in [0:worldNDim] do", "for iworld in [0:worldNDim - 1] do"))

# weak-extra-axis: the mirror of the above — every underlying axis is emitted
# correctly, then one EXTRA entry is appended. C2 and C3 are both still satisfied
# (they constrain only positions below `worldNDim` and the retained axis numbers),
# so this rival is refutable ONLY by C1: it isolates the length clause in a way the
# drop-last rival, which also perturbs which values land where, does not.
_RIV_EXTRA = _riv(_IMPL.replace(
    "  return result", "  return result ++ [(0 : Int)]"))

# --- the arity-tuned rival (added by audit) --------------------------------

# weak-tuned-to-three-axes: the omitted-axis fill is correct ONLY when the
# underlying system happens to have exactly three axes, and reverts to the fixed
# constant for every other axis count. This is the OVERFIT shape none of the nine
# rivals above reach: each of those is wrong as a UNIFORM rule, so a spec that
# merely pinned behaviour at one arity would still reject them. This one is right
# at that arity by construction, so only the ∀-quantification over `worldNDim`
# refutes it — the binder the battery otherwise probes only by varying witness
# points, never by an impl that DISCRIMINATES on it. Aimed at the one thing an
# arity-tuned patch would exploit.
_RIV_TUNED_ARITY = _riv(_IMPL.replace(
    "      result := result ++ [slicedOut.getD iworld 0]",
    "      result := result ++ "
    "[if worldNDim = 3 then slicedOut.getD iworld 0 else (1 : Int)]"))

# weak-tuned-to-small-arities: the SAME overfit shape aimed at the battery itself
# rather than at the reproducer. The omitted-axis fill is the reference value for
# every underlying system of at most FOUR axes and the fixed pre-fix constant from
# five axes up. Machine-checked: this rival is EQUAL to the frozen impl at all ten
# of the witness points above (every one of which is at 1, 2, 3 or 4 axes), so no
# witness already in this battery refutes it — `weak-tuned-to-three-axes`, which is
# wrong at 1, 2 and 4 axes, is caught by several of them. Its own witness therefore
# has to leave the arity range the rest of the battery covers, which is precisely
# the residual hole an arity-tuned patch could hide in: a rival tuned not to the
# reproducer's dimensionality but to the DIMENSIONALITIES THE BATTERY SAMPLES.
_RIV_TUNED_SMALL = _riv(_IMPL.replace(
    "      result := result ++ [slicedOut.getD iworld 0]",
    "      result := result ++ "
    "[if worldNDim ≤ 4 then slicedOut.getD iworld 0 else (1 : Int)]"))


# --- witnesses -------------------------------------------------------------
# Each states `¬ problem_spec_assemble … (implementation_assemble …)` at ONE
# concrete input, unfolds the spec and the impl, reduces the do-loop over the
# materialized axis list, and closes the residue by `decide`. Every carrier here
# is transparent, so no witness needs a hypothesis: nothing is bound, hence
# nothing can be inconsistent. Each point lies inside the obligation's
# precondition domain (machine-checked: all four preconditions were discharged by
# evaluation at every one of the points below), and ELEVEN DISTINCT points are
# used — the rivals are refuted at different `worldNDim` (1, 2, 3, 4 and 5),
# different `worldKeep` (empty / leading / trailing / interior / contiguous /
# non-contiguous), and different `inputs` lengths (0 through 3), so no binder is
# held fixed across the battery.
#
# WHY THE GOLD-SIDE FAILURES ARE ADMISSIBLE EVIDENCE. Every witness's gold-side
# build fails with a PLAIN EVALUATION error — `Tactic decide proved that the
# proposition <the concrete claim> is false` — not a missing identifier, type
# error, unfolding failure or timeout. That was re-derived rather than read: for
# each of the eleven cases the claim was FLIPPED (the leading `¬` dropped) and
# rebuilt on both sides, and the exit codes INVERT (flipped-vs-gold elaborates,
# flipped-vs-rival fails with the mirrored evaluation error). So gold's exit code
# tracks what the witness CLAIMS, which is what makes it a discriminator rather
# than a tactic mismatch.
#
# On what a witness point does and does not attest to. A witness shows the rival
# violates the spec SOMEWHERE in the obligation's domain, which is all a
# uniqueness case needs. It does NOT follow that the rival misbehaves at the
# reported reproducer's own input shape, and for three rivals here it demonstrably
# does not: `weak-omitted-cursor-index`, `weak-kept-axis-index` and
# `weak-keep-test-positional` all coincide with the frozen behaviour when the
# retained axes are exactly the LEADING ones, which is that reproducer's shape.
# Their `refinement` entries say so rather than claiming otherwise; each is a
# genuinely wrong patch (it diverges on reduced views the surrounding suite does
# build), so its rejection attests to the spec, but it attests to a property
# STRONGER than the reproducer alone pins down.

_TAC = ("  unfold problem_spec_assemble implementation_assemble\n"
        "  simp [Id.run, bind, pure, List.range', List.forIn_cons, List.forIn_nil]\n"
        "  all_goals decide")


def _wit(nd, keep, inputs, sliced):
    return (f"example : ¬ problem_spec_assemble {nd} {keep} {inputs} {sliced}\n"
            f"    (implementation_assemble {nd} {keep} {inputs} {sliced}) := by\n"
            + _TAC)


# 2 axes, axis 0 retained, axis 1 omitted with reference value 9. gold puts 9 at
# axis 1; the constant-fill rival puts its constant there. (C2)
_WIT_CONST = _wit(2, "[0]", "[5]", "[3, 9]")

# 3 axes, only axis 1 retained. gold puts reference 3 at axis 0; the rival puts the
# supplied value 5 there. Distinct `worldKeep` shape (interior single axis). (C2)
_WIT_USES_SUPPLIED = _wit(3, "[1]", "[5]", "[3, 9, 4]")

# 3 axes, axis 0 retained, axes 1 and 2 omitted. The kept cursor is 1 for both
# omitted axes, so the rival reads reference index 1 twice: correct at axis 1,
# wrong at axis 2 (gold puts 4 there, the rival 9). Refuting this needs TWO omitted
# axes after a kept one — a shape no other witness here presents. (C2)
_WIT_CURSOR_INDEX = _wit(3, "[0]", "[5]", "[3, 9, 4]")

# 2 axes, only axis 1 retained. gold puts supplied[0] = 5 at axis 1; the rival
# reads supplied[1], which is absent. Refuting this REQUIRES a retained axis whose
# number exceeds its kept position, i.e. an omitted axis before it. (C3)
_WIT_KEPT_AXIS_INDEX = _wit(2, "[1]", "[5]", "[3, 9]")

# 2 axes, BOTH retained, two distinct supplied values. gold emits [5, 8]; the
# reversed-consumption rival emits [8, 5]. The only witness here with more than one
# retained axis and more than one supplied value — the sub-domain where consumption
# ORDER is observable at all. (C3)
_WIT_KEPT_REVERSED = _wit(2, "[0, 1]", "[5, 8]", "[3, 9]")

# 3 axes, only the LAST retained. The positional proxy retains axis 0 instead:
# gold puts reference 3 at axis 0 and supplied 5 at axis 2, the rival the reverse.
# A trailing-only `worldKeep` — the shape that maximally separates membership from
# position. (C2+C3, via the branch condition)
_WIT_KEEP_POSITIONAL = _wit(3, "[2]", "[5]", "[3, 9, 4]")

# 1 axis, retained. gold puts supplied 5 at axis 0; the rival forces its fixed
# value there. The minimal input (`worldNDim = 1`), which is where a
# first-axis-only defect is the whole behaviour. (C3 at axis 0)
_WIT_FIRST_AXIS = _wit(1, "[0]", "[5]", "[3]")

# 1 axis, NONE retained (empty `worldKeep`, empty supplied vector — the degenerate
# reduced view no other witness exercises). gold emits a 1-entry vector; the
# off-by-one rival emits none. (C1)
_WIT_DROP_LAST = _wit(1, "[]", "[]", "[7]")

# 3 axes, axes 0 and 2 retained, axis 1 omitted — the fully interleaved shape, and
# the SMALLEST non-contiguous `worldKeep` in the battery (the two arity-tuned
# witnesses below are non-contiguous too, at 4 and 5 axes). gold emits 3 entries;
# the rival emits 4, satisfying C2 and C3 while violating C1. (C1)
_WIT_EXTRA = _wit(3, "[0, 2]", "[5, 8]", "[2, 4, 6]")

# 4 axes — an axis count no witness ABOVE reaches, which is the whole point: the
# arity-tuned rival is correct at exactly three axes, so any witness at 1, 2 or 3
# axes either fails to refute it or refutes it for the wrong reason. (The
# small-arity witness below goes further out, to 5.) Axes 0, 1 and 3 retained,
# axis 2 omitted with reference value 4; the
# rival falls back to its constant there. (C2, via the `worldNDim` binder)
_WIT_TUNED_ARITY = _wit(4, "[0, 1, 3]", "[5, 6, 7]", "[3, 9, 4, 2]")

# 5 axes — beyond every arity the rest of the battery samples, which is the whole
# point of the case it serves: that rival is correct at 1 through 4 axes by
# construction, so it agrees with the frozen impl at all ten witness points above
# and only a FIFTH axis count separates them. Axes 0, 2 and 4 retained, axes 1 and
# 3 omitted with reference values 9 and 2; the rival falls back to its constant at
# both. Also the battery's largest `worldNDim` and its longest `slicedOut`.
# (C2, via the `worldNDim` binder)
_WIT_TUNED_SMALL = _wit(5, "[0, 2, 4]", "[5, 6, 7]", "[3, 9, 4, 2, 8]")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_NEGATED,
        "rationale": (
            "a structurally different but CORRECT impl: the per-axis decision is "
            "rewritten with the guard NEGATED and the two branches SWAPPED, which "
            "changes nothing about the value at any slot, the left-to-right "
            "consumption of the supplied vector, or the forward accumulation. The "
            "theorem STATEMENT is byte-identical and the proof is reproven honestly "
            "— the bridge lemma's `forIn` normal form and its two-branch `simp only` "
            "are reshaped to match the new guard, the SAME argument with no new "
            "lemma, axiom or `sorry`. Ports nagini's `pos-assemble-branch-reorder`. "
            "If it FAILS => SPEC-TOO-STRONG: clauses C1/C2/C3 would be pinned to the "
            "frozen branch shape rather than to the behaviour."
        ),
    },
    {
        "id": "pos-explicit-axis-list",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_RANGE_LIST,
        "rationale": (
            "a second structurally different CORRECT impl: the loop walks an "
            "explicitly materialized list of the underlying axis numbers instead of "
            "the bounded range. Same axes in the same order with the same body, so "
            "the output is identical at every input. Statement byte-identical; only "
            "the proof step that normalizes the loop's index source is replaced (the "
            "bounded-range normal form gives way to the list one) and the rest of the "
            "frozen argument is reused verbatim — no new lemma, axiom or `sorry`. "
            "Carries over nagini's `pos-recovered-inline` argument (a "
            "behaviour-preserving reshape must verify), re-aimed at the single "
            "function this bundle models. If it FAILS => SPEC-TOO-STRONG (the spec "
            "would be bound to the frozen loop's index source)."
        ),
    },
    {
        "id": "admiss-precond-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the frozen impl and the frozen proof argument, with TWO `have`s inserted "
            "at the SAME concrete in-domain input — 3 underlying axes, the two LEADING "
            "axes (0 and 1) retained and the trailing one omitted, two supplied values, "
            "a 3-entry reference vector, which is the shape a legitimate caller of the "
            "modeled behaviour presents. (i) `_precond_admissible` DISCHARGES all four "
            "precondition hypotheses there by evaluation: were the set contradictory — "
            "sortedness against the axis bound, or the two length constraints against "
            "each other — it could not close, and that is exactly PRECOND-TOO-STRONG, "
            "an obligation vacuously true because no caller can enter its domain. "
            "(ii) `_obligation_at_that_input` then discharges the OBLIGATION ITSELF "
            "there, again by evaluation, before the frozen argument closes the general "
            "goal verbatim — the half that makes this lane bite on a total carrier, "
            "since a satisfiable precondition set is necessary but not sufficient: the "
            "obligation could still be UNSATISFIABLE at an admitted point, and then the "
            "frozen theorem would be unprovable rather than vacuous. Both verify, so "
            "the domain is inhabited AND the obligation is discharged there. That the "
            "precondition is load-bearing rather than decorative is machine-checked "
            "separately: OUT of the domain, at `worldKeep = [0, 0]` (not strictly "
            "sorted), C3 demands two different values at the same position, so NO "
            "result satisfies the spec. Ports nagini's `admiss-recovered-precond`; "
            "unlike most Lean-family bundles this lane is NOT vacuous here, because the "
            "lean obligation really does carry four precondition hypotheses as binders."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-omitted-constant",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CONST,
        "refinement": (
            "fills every axis absent from the reduced view with a FIXED CONSTANT "
            "instead of the reference value for that axis. Its faithful real patch is "
            "the UNCHANGED pre-fix code path, so the F2P reproducer "
            "test_coupled_world_slicing behaves exactly as the reported issue "
            "describes: when the underlying system couples an omitted axis to a "
            "retained one, the wrong value on the omitted axis corrupts the inverse "
            "for the retained one and the recovered coordinate comes back off by "
            "eleven orders of magnitude instead of ~0. It would NOT resolve — this is "
            "the very behaviour the fix establishes (see refinement.md / "
            "Solution_prepatch.lean, whose carried proof fails on exactly this "
            "clause)."
        ),
        "rationale": (
            "REJECTED by clause C2 (omitted axes): the spec pins slot `iworld` of an "
            "omitted axis to `slicedOut.getD iworld 0`, and a constant is not that "
            "value whenever the reference vector differs from the constant there. "
            "Correct on every retained axis, so only C2 can see it. Witness: 2 axes "
            "with axis 0 retained and axis 1 omitted carrying reference 9. If it "
            "VERIFIES => SPEC-TOO-WEAK, and the single discriminating behaviour of "
            "this instance would be unpinned."
        ),
        "witness": _WIT_CONST,
    },
    {
        "id": "weak-omitted-uses-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_USES_SUPPLIED,
        "refinement": (
            "a subtler wrong fill: an omitted axis takes the NEXT SUPPLIED value "
            "rather than its reference value — it reads a real input, just the wrong "
            "one. Its faithful real patch feeds a caller-supplied coordinate into an "
            "axis the caller never supplied, so the reassembled vector still "
            "disagrees with the coordinate the reduced view was actually taken at; "
            "under the coupled system of the F2P reproducer the recovered retained "
            "coordinate is again not ~0 and test_coupled_world_slicing FAILS. It "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (omitted axes). Distinct from "
            "`weak-omitted-constant`: the wrong value is drawn from `inputs`, so a "
            "spec that merely required the omitted slot to hold SOME input-derived "
            "value would admit it — only the `= slicedOut.getD iworld 0` equation "
            "refutes it. Witness varies the `worldKeep` binder to an INTERIOR single "
            "axis (3 axes, only axis 1 retained), a shape no other witness presents. "
            "If it VERIFIES => SPEC-TOO-WEAK (the omitted-axis fill is pinned only to "
            "'some input', not to the reference value)."
        ),
        "witness": _WIT_USES_SUPPLIED,
    },
    {
        "id": "weak-omitted-cursor-index",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CURSOR_INDEX,
        "refinement": (
            "reads the RIGHT vector at the WRONG offset: an omitted axis takes the "
            "reference value at the running retained-axis count rather than at its own "
            "axis number. Its faithful real patch indexes the reference coordinates by "
            "the wrong counter, so an omitted axis receives another axis's reference "
            "value. HONEST SCOPE — this rival AGREES with the fixed behaviour on the "
            "F2P reproducer's own input shape (3 underlying axes, the two leading axes "
            "retained, the trailing one omitted: the cursor has reached 2 by the time "
            "the omitted axis is processed, which is that axis's own number), so it "
            "would RESOLVE that reproducer. Machine-checked: the two impls are equal "
            "at that point. It is nonetheless a genuinely WRONG patch — it diverges as "
            "soon as an omitted axis precedes a retained one, or as soon as two omitted "
            "axes follow a retained one — and the reduced views the surrounding suite "
            "builds do include non-contiguous retained sets, so it is not a "
            "behaviour-preserving reshape. Its rejection therefore attests to the "
            "spec's per-axis-number indexing, which is stronger than the single F2P "
            "point requires; it is NOT evidence about that reproducer."
        ),
        "rationale": (
            "REJECTED by clause C2 (omitted axes) — specifically by the fact that the "
            "index is the AXIS NUMBER. A NEAR MISS: it agrees with gold on every input "
            "whose omitted axes all precede its retained ones (there the cursor equals "
            "the axis number), so it survives the witnesses of both rivals above and "
            "needs its own, at an input with TWO omitted axes following a retained one "
            "(3 axes, axis 0 retained): the rival then reads reference index 1 twice, "
            "landing correctly at axis 1 and wrongly at axis 2. If it VERIFIES => "
            "SPEC-TOO-WEAK (the reference vector could be indexed by the wrong "
            "counter)."
        ),
        "witness": _WIT_CURSOR_INDEX,
    },
    {
        "id": "weak-kept-axis-index",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_KEPT_AXIS_INDEX,
        "refinement": (
            "a retained axis takes the supplied value at its own AXIS NUMBER instead "
            "of at its position among the retained axes. Its faithful real patch "
            "indexes the caller's reduced vector by the underlying axis number, which "
            "reads past the end of that (shorter) vector as soon as an omitted axis "
            "precedes a retained one. HONEST SCOPE — the F2P reproducer slices away "
            "the TRAILING axis, so its retained axes are exactly the leading ones and "
            "axis number equals retained position throughout; this rival therefore "
            "AGREES with the fixed behaviour there and would RESOLVE that reproducer. "
            "Machine-checked: the two impls are equal at that point. It is still a "
            "wrong patch — with an omitted axis before a retained one it reads the "
            "reduced vector out of bounds (in the real code an IndexError, here the "
            "`getD` default) — and the surrounding suite does slice away leading and "
            "interior axes, so it is not a behaviour-preserving reshape. Its rejection "
            "attests to the spec's POSITIONAL consumption, not to that reproducer."
        ),
        "rationale": (
            "REJECTED by clause C3 (retained axes): the spec pins the c-th retained "
            "axis to `inputs.getD c 0`, the position among the retained axes, not the "
            "axis number. A second NEAR MISS — it agrees with gold whenever the "
            "retained axes are exactly the leading ones — so its witness must place a "
            "retained axis whose number exceeds its retained position (2 axes, only "
            "axis 1 retained). Attacks a different clause from every rival above, all "
            "of which are correct on retained axes. If it VERIFIES => SPEC-TOO-WEAK "
            "(the supplied values need not be consumed positionally)."
        ),
        "witness": _WIT_KEPT_AXIS_INDEX,
    },
    {
        "id": "weak-kept-values-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_KEPT_REVERSED,
        "refinement": (
            "consumes the supplied values RIGHT-TO-LEFT instead of left-to-right. Its "
            "faithful real patch walks the caller's reduced vector backwards, so with "
            "two or more retained axes each receives another retained axis's "
            "coordinate. The F2P reproducer supplies two retained (spatial) "
            "coordinates and asserts both recovered pixels, so swapping them makes "
            "test_coupled_world_slicing FAIL. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C3 (retained axes) — by its ORDER content specifically. "
            "Every axis still receives a value of the right KIND and the length is "
            "right, so C1 and C2 are untouched; and both index rivals above preserve "
            "left-to-right order on their agreeing sub-domains, so neither probes this. "
            "The witness is at an input with two retained axes AND two distinct supplied "
            "values — the sub-domain where consumption order is observable at all (gold "
            "[5, 8] vs the rival's [8, 5]); it is the SMALLEST such point in the battery "
            "(worldNDim = 2, both axes retained), so order is the only thing it can be "
            "reading. If it VERIFIES => SPEC-TOO-WEAK "
            "(the positional correspondence in C3 would be unpinned up to permutation)."
        ),
        "witness": _WIT_KEPT_REVERSED,
    },
    {
        "id": "weak-keep-test-positional",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_KEEP_POSITIONAL,
        "refinement": (
            "replaces the retained-axis MEMBERSHIP test with a positional proxy — an "
            "axis counts as retained iff its number is below the retained COUNT. Its "
            "faithful real patch decides which axes the reduced view keeps by counting "
            "rather than by consulting the retained-axis set, so it treats the leading "
            "axes as retained whatever the actual slice was. HONEST SCOPE — the F2P "
            "reproducer's reduced view retains exactly the leading axes, where "
            "'number below the count' and 'in the retained set' coincide, so this "
            "rival AGREES with the fixed behaviour there and would RESOLVE that "
            "reproducer. Machine-checked: the two impls are equal at that point. It is "
            "a wrong patch all the same — for any reduced view that keeps a "
            "non-contiguous or non-leading set of axes it misclassifies BOTH kinds of "
            "axis, and the surrounding suite builds exactly such views — so it is not "
            "a behaviour-preserving reshape. Its rejection attests that the spec pins "
            "classification to the retained SET rather than to a count."
        ),
        "rationale": (
            "REJECTED by clauses C2 and C3 jointly, through the branch CONDITION "
            "rather than either branch's value — the only rival here that attacks the "
            "retained/omitted CLASSIFICATION rather than a fill. It agrees with gold "
            "on every input whose retained axes are exactly the leading ones, so its "
            "witness uses a trailing-only retained set (3 axes, only axis 2 retained): "
            "gold puts reference 3 at axis 0 and supplied 5 at axis 2, the rival the "
            "reverse. This varies the `worldKeep` binder to the shape that maximally "
            "separates membership from position, which no other witness reaches. If it "
            "VERIFIES => SPEC-TOO-WEAK (the retained-axis set could be replaced by a "
            "count)."
        ),
        "witness": _WIT_KEEP_POSITIONAL,
    },
    {
        "id": "weak-first-axis-forced",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FIRST_AXIS,
        "refinement": (
            "PARTIAL-DOMAIN: correct at every axis except the first, which is forced "
            "to a fixed value whether or not it is retained. Its faithful real patch "
            "is correct on all but the leading underlying axis; since the downstream "
            "inverse is a function of the WHOLE reassembled vector, one wrong entry "
            "still corrupts the recovered coordinates and the F2P reproducer "
            "test_coupled_world_slicing FAILS. It would NOT resolve. Ports nagini's "
            "`partial-first-slot-wrong`."
        ),
        "rationale": (
            "REJECTED at axis 0 — by C3 when axis 0 is retained (as in the witness) "
            "and by C2 when it is not. Distinct from every rival above because it is "
            "right EVERYWHERE ELSE: a rival wrong on a whole sub-domain is refuted by "
            "any witness in that sub-domain, whereas this one survives every "
            "refutation aimed at a later axis. Witness uses the minimal input "
            "(`worldNDim = 1`, axis 0 RETAINED), the point at which a first-axis-only "
            "defect is the entire behaviour; the only other witness at that size "
            "(`weak-drop-last-axis`) retains nothing, so this is the only point in the "
            "battery where C3 constrains axis 0 at the minimal arity. If it VERIFIES "
            "=> SPEC-TOO-WEAK (a single-slot defect would go unpinned)."
        ),
        "witness": _WIT_FIRST_AXIS,
    },
    {
        "id": "weak-drop-last-axis",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_LAST,
        "refinement": (
            "an off-by-one over the underlying axes: every emitted entry is correct, "
            "but the last axis is never emitted, so the reassembled vector is one entry "
            "short. Its faithful real patch hands the downstream inverse a vector of "
            "the wrong arity — it cannot be interpreted as coordinates for the "
            "underlying system at all, so the F2P reproducer "
            "test_coupled_world_slicing FAILS (and the P2P round-trips with it). It "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 (length): the spec pins `result.length = "
            "worldNDim`, and one entry per underlying axis is the frame guarantee — "
            "the analogue on this referentially-transparent carrier of nagini's "
            "read-only-input obligation, which cannot be attacked by mutation here. "
            "Witness uses the degenerate reduced view no other witness exercises: 1 "
            "axis, NONE retained, an empty supplied vector — so the `worldKeep` and "
            "`inputs` binders are probed at empty. At that point C3 is VACUOUS (there "
            "is no retained axis to constrain) and C1 fails outright; C2 fails too, "
            "because the rival emits nothing and `getD` past the end returns the "
            "default rather than the reference value — machine-checked, so this witness "
            "is NOT a C1-only refutation and `weak-extra-axis` remains the case that "
            "isolates the length clause. What this one adds is the empty-`worldKeep` "
            "corner. If it VERIFIES => SPEC-TOO-WEAK (axes could be silently dropped)."
        ),
        "witness": _WIT_DROP_LAST,
    },
    {
        "id": "weak-extra-axis",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EXTRA,
        "refinement": (
            "the mirror of the off-by-one: every underlying axis is emitted correctly, "
            "then one EXTRA entry is appended. Its faithful real patch hands the "
            "downstream inverse one coordinate too many — again the wrong arity for the "
            "underlying system — so the F2P reproducer test_coupled_world_slicing "
            "FAILS. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 (length) and ONLY by C1: C2 constrains positions "
            "below `worldNDim` and C3 the retained axis numbers, both of which this "
            "rival gets exactly right, so the appended entry is invisible to them. That "
            "isolates the length clause in a way `weak-drop-last-axis` cannot — "
            "dropping an axis also perturbs which positions exist, whereas this rival "
            "changes nothing but the count. Witness uses the fully interleaved shape (3 "
            "axes, axes 0 and 2 retained, axis 1 omitted) — a non-contiguous `worldKeep` "
            "with an omitted axis strictly between two retained ones, at the smallest "
            "arity where that shape exists; only the two arity-tuned witnesses (at 4 and "
            "5 axes) otherwise reach it. Machine-checked "
            "at that point: C2 and C3 both HOLD of the rival's [5, 4, 8, 0] and only the "
            "length clause fails, so the rejection is attributable to C1 alone. If it "
            "VERIFIES => "
            "SPEC-TOO-WEAK (the result's arity would be unpinned from above)."
        ),
        "witness": _WIT_EXTRA,
    },
    {
        "id": "weak-tuned-to-three-axes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TUNED_ARITY,
        "refinement": (
            "an OVERFIT patch: the omitted-axis fill is the reference value when the "
            "underlying system has exactly three axes, and the fixed pre-fix constant "
            "for every other axis count. Its faithful real patch is the one shape that "
            "would pass the reported reproducer while leaving the defect in place — the "
            "reproducer's underlying system has three axes, so this patch resolves it "
            "and nothing else. For any other underlying arity it is byte-for-byte the "
            "pre-fix behaviour, so a reduced view taken from a 2- or 4-axis system "
            "still gets a wrong coordinate on every omitted axis and still corrupts the "
            "inverse whenever that axis is coupled to a retained one. It would resolve "
            "the reproducer and NOT the issue, which is exactly the case a "
            "single-input battery cannot see and this rival exists to cover."
        ),
        "rationale": (
            "REJECTED by clause C2 (omitted axes) — but reachable only through the "
            "`worldNDim` binder, which is what distinguishes this case from every rival "
            "above. Each of those is wrong as a UNIFORM rule, so a spec pinning "
            "behaviour at one arity would reject them too; this one is correct at three "
            "axes by construction, so only the obligation's ∀-quantification over "
            "`worldNDim` refutes it. Witness is consequently the only one in the "
            "battery at FOUR axes (axes 0, 1 and 3 retained, axis 2 omitted): at 1, 2 "
            "or 3 axes it either does not refute or refutes for an unrelated reason. If "
            "it VERIFIES => SPEC-TOO-WEAK, and the spec would admit a patch tuned to "
            "the reproducer's own dimensionality."
        ),
        "witness": _WIT_TUNED_ARITY,
    },
    {
        "id": "weak-tuned-to-small-arities",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TUNED_SMALL,
        "refinement": (
            "the same OVERFIT shape as the rival above, but tuned WIDER: the "
            "omitted-axis fill is the reference value for every underlying system of at "
            "most four axes and the fixed pre-fix constant from five axes up. Its "
            "faithful real patch is correct for the small underlying systems a test "
            "suite is most likely to build and reverts to the pre-fix behaviour for the "
            "larger ones, so a reduced view taken from a 5-or-more-axis system still "
            "gets a wrong coordinate on every omitted axis and still corrupts the "
            "inverse whenever that axis is coupled to a retained one. It WOULD resolve "
            "the reported reproducer (whose underlying system has three axes) and would "
            "NOT resolve the issue."
        ),
        "rationale": (
            "REJECTED by clause C2 (omitted axes), through the `worldNDim` binder — and "
            "it exists because `weak-tuned-to-three-axes` does not close this class. "
            "That rival is wrong at 1, 2 and 4 axes, so several witnesses already in the "
            "battery refute it; this one is EQUAL to the frozen impl at ALL TEN of those "
            "witness points (machine-checked; every one of them is at 1, 2, 3 or 4 "
            "axes), so nothing already here can see it. Its witness is consequently the "
            "only one in the battery at FIVE axes — the arity range the rest of the "
            "battery never samples, which is exactly where a patch tuned to the "
            "BATTERY'S OWN sampled dimensionalities (rather than to the reproducer's) "
            "would hide. Axes 0, 2 and 4 retained, axes 1 and 3 omitted, so it also "
            "probes `worldKeep` at two non-adjacent omitted axes. If it VERIFIES => "
            "SPEC-TOO-WEAK, and the ∀-quantification over `worldNDim` would be pinned "
            "only over the arities the battery happens to instantiate."
        ),
        "witness": _WIT_TUNED_SMALL,
    },
]


# The axiom lane is G-AX's job and this gate ignores it. It is empty here for an
# independent reason too: no callee axiom is declared or consumed by this spec
# (refinement.md), the reference vector being an INPUT to the modeled behaviour.
AXIOM_TESTS = []
