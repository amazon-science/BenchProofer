# properties.py — PBT falsification battery for scikit-learn__scikit-learn-14496 (lean).
#
# NOT a Lean module: a record of adversarially-reasoned cases the G-PBT runner
# executes and stamps with a recorded verdict. Each spec case is a full
# Solution.lean variant built by region-surgery — it edits ONLY the impl region
# (and, where a reshaped impl needs it, the proof body), so the frozen spec
# (axioms / pure / post-conditions) stays byte-identical, same_spec holds by
# construction, and each `theorem correct_<name>` STATEMENT is preserved
# verbatim. No case introduces sorry/admit/native_decide/axiom or any new
# theorem/lemma.
#
# CARRIER NOTE — the threshold's FORM is part of the carrier.
# A prepared threshold is modeled as a `Threshold`: either an absolute `count`
# (a whole number of population members) or a divisible `quantity`. This is not
# decoration. The consumer that receives the prepared threshold counts
# population members, and it discriminates on the FORM, not on the magnitude: it
# admits a count and rejects a divisible amount even when that amount's
# magnitude is whole. A carrier that recorded only the magnitude would model that
# distinction away, and the reduction's whole point — delivering a count rather
# than a divisible amount of the same size — would become invisible. That
# invisibility is a measured fact about the narrower carrier, not a conjecture:
# a rival delivering the right magnitude in divisible form satisfies every
# magnitude-level clause, INCLUDING an explicit "the result is integral"
# (`∃ k : ℤ, result = k`) clause, because the two are the same number. Hence the
# distinction lives in the carrier, where it is decidable, and the rival family
# R9–R11 / T6–T7 below attacks it directly.
#
# CARRIER NOTE — preparing a threshold is PARTIAL, and the partiality is part of
# the carrier too. Before a threshold is used it must clear a range check
# (`Threshold.admits`: the amount is positive, is either whole or at most one,
# and does not exceed the population size); a threshold the check refuses is not
# prepared at all, and the result is `none`. Both outcome shapes are therefore
# observable, and the R12–R15 / T8–T10 rivals attack them: a rival that prepares
# a refused threshold, one that applies only part of the check, one that refuses
# a threshold the check admits, and — the sharpest — one that checks only the
# LEADING threshold of a pair while the check applies to each in turn.
#
# The bundle models the SAME reduction as its nagini sibling, on the SAME model
# boundary (the population-scaling multiply is upstream of the boundary and its
# result enters as the `scaled` input), over TWO functions:
#   * `resolveMinSamples (minSamples : Threshold) (populationSize : ℕ)
#     (scaled : ℚ) : Option Threshold` — the single-threshold preparation. A
#     threshold the range check refuses yields `none`. An admitted threshold
#     whose amount is at most one is a fraction, and the count comes from its
#     scaled amount via `normCount scaled = .count (max 2 ⌊scaled⌋)`; a threshold
#     whose amount is greater than one is already an absolute count, kept EXACTLY
#     as it arrived (form included).
#   * `resolveThresholds (minSamples : Threshold)
#     (trailingThreshold : Option Threshold) (populationSize : ℕ)
#     (scaledLead : ℚ) (scaledTrail : ℚ) : Option (Threshold × Threshold)` — the
#     two-threshold preparation: the leading threshold checked and then reduced
#     as above from `scaledLead`; an UNSET trailing threshold (`none`) defaults to
#     the already-reduced leading one in whatever form that carries; the trailing
#     threshold — defaulted or supplied — checked in turn and then reduced from
#     `scaledTrail` on the same rule; both components pinned to the inputs in form
#     as well as amount, and each refusal pinned to exactly the inputs the check
#     rejects.
# `normCount` and `Threshold.admits` are FULLY computable and `Threshold` derives
# `DecidableEq`, so every rival is refutable at a concrete literal input — no
# conditioning on an opaque term is needed. `⌊·⌋` over `ℚ` does not reduce under
# `decide` (the `Decidable` instance gets stuck on `Rat.floor`), so the witnesses
# compute it with `norm_num` / `simp` after `simp only [Id.run, bind, pure]`
# reduces the `Id.run do` block.
#
# CARRIER NOTE — the scaled amount is an INPUT, not recomputed here. The
# surrounding routine forms the scaled amount with the ordinary arithmetic it
# already used before the modeled behavior existed, and that step is not part of
# the modeled behavior; the amount it yields is always an exact rational and is
# carried losslessly. Every witness below therefore states its scaled amount as
# the exact rational the surrounding routine actually hands over at that input
# (e.g. a half-population threshold on a population of seven hands over `7/2`),
# recomputed from the real routine rather than re-derived inside the model.
# On the keep-unchanged branch (a threshold whose amount is already greater than
# one) the real routine forms no scaled amount at all, and the specification
# constrains the result independently of it there; witnesses on that branch
# supply the amount the routine WOULD form, purely to saturate the binder. The
# same holds on a refusal, where the routine stops before forming any amount.
#
# The nagini floor rivals (un-floored echo / over-count / strict-undercount /
# floor-of-two-only / round-to-nearest) all port onto `resolveMinSamples`. The
# widened surface of `resolveThresholds` (the trailing normalization, the
# `none`-default step, the per-threshold range check and the two-component
# pinning) has NO nagini counterpart and is attacked here by fresh rivals
# (T1–T10).
#
# DEFENDED SURFACE (what every rival attacks):
#   resolveMinSamples:
#     (M0) ¬ minSamples.admits populationSize → result = none   (a threshold the
#          range check refuses is not prepared: the WHOLE check, not a part of
#          it, and the refusal is pinned to exactly those thresholds);
#     (M1) admitted ∧ minSamples.amount ≤ 1 → result = some (normCount scaled)
#          (fractional branch reduces the scaled amount to the whole-number,
#          clamped-to-2 count, DELIVERED IN COUNT FORM — NOT the unreduced
#          amount, NOT floor±1, NOT round-to-nearest, NOT a constant 2, and NOT
#          the right magnitude in divisible form);
#     (M2) admitted ∧ 1 < minSamples.amount → result = some minSamples
#          (a threshold that is already an absolute count is kept EXACTLY, form
#          included).
#   resolveThresholds — where
#     ms   = if minSamples.amount ≤ 1 then normCount scaledLead else minSamples
#     mcs0 = trailingThreshold.getD ms
#     mcs  = if mcs0.amount ≤ 1 then normCount scaledTrail else mcs0:
#     (T-r0)   ¬ minSamples.admits populationSize → result = none (the leading
#              threshold faces the check first, and its refusal refuses the pair);
#     (T-r1)   admitted leading ∧ ¬ mcs0.admits populationSize → result = none —
#              the trailing threshold faces the check IN TURN, and the subject of
#              that check is `mcs0`, the value this specification itself computes
#              (the defaulted-or-supplied trailing threshold), NOT the leading
#              input and NOT the raw optional argument;
#     (T-ms)   the leading component is the reduced leading threshold, on the
#              FRACTIONAL branch (minSamples.amount ≤ 1);
#     (T-msg)  the leading component is the leading threshold UNCHANGED on the
#              absolute-count branch (1 < minSamples.amount) — the guard is not
#              dropped;
#     (T-mcs)  the trailing component is the reduced trailing threshold;
#     (T-none) an unset trailing threshold defaults to the reduced leading one
#              (`getD ms`, not `getD 2` and not the raw leading input);
#     (T-guard)a present trailing threshold whose amount is greater than one is
#              kept unchanged (the guard is not dropped);
#     (T-form) both components are pinned in FORM: a fractional branch must
#              deliver a count, not a divisible quantity of equal magnitude.
#
# Input binders varied by the reject witnesses:
#   resolveMinSamples: `minSamples` at fractional points (1/2, 1/10), at the
#     branch BOUNDARY (exactly 1), at absolute-count points (5, 10), at a
#     non-integral point above one (5/2), at a point exceeding the population
#     (11) and at zero; `populationSize` at 5, 7, 10, 31; `scaled` at a
#     half-integral amount (7/2), at a sub-two amount (1/2), at a half-integral
#     amount straddling the rounding boundary (5/2), and at whole amounts (10,
#     25, 31, 110, 155). The FORM binder is varied too: a leading threshold
#     arriving as `.quantity` (a fraction, the ordinary case) and as `.count`
#     (an absolute count, the keep-unchanged case).
#   resolveThresholds: `minSamples` with amount ≤1, >1 and refused;
#     `trailingThreshold` at `some` (≤1, >1 and refused) AND at `none`;
#     `populationSize` at 1, 5, 7, 10, 31; `scaledLead` at 1/2, 7/2, 25, 30, 93,
#     155; `scaledTrail` at 1/2, 5/2, 30, 35, 110, 155, 217.
#
# AUDIT NOTE — SIXTH pass: PARTIALITY (faithfulness realignment).
#   A faithfulness review shadowed the modeled functions against the real
#   routines and found a divergence the previous carrier could not express: the
#   range check that guards a threshold was modeled only as a POSITIVITY
#   precondition on the proof binders, so on the inputs the real check refuses
#   the previous specification still predicted a prepared threshold. The witness
#   class is sharpest in the pair routine, where the trailing threshold defaults
#   to the value the routine has just computed: on a population of one with an
#   unset trailing threshold, the reduction clamps the leading threshold up to two
#   — which then EXCEEDS the population — and the real routine refuses the pair,
#   while the previous specification forced a delivered pair of two counts.
#   Reproduced against the real routine before repairing anything, and reproduced
#   at the base commit too, so it is not an artifact of the delta.
#   The repair models the check DEEPLY (`Threshold.admits`) and makes the result
#   an `Option`, so a refusal is a predicted outcome rather than an excluded
#   input. It has to be modeled deeply rather than assumed as a contract, because
#   in the pair routine the check's subject is a value the specification itself
#   computes. The proof-binder positivity preconditions are correspondingly GONE:
#   the modeled functions are now total, which WIDENS the attested domain instead
#   of narrowing it — no input that was admissible before is inadmissible now.
#   Every clause of the previous specification survives verbatim modulo `some`;
#   nothing was weakened, and NO reject case was dropped. Seven NEW rivals
#   (R12–R15, T8–T10) attack the partiality the previous carrier could not
#   express — including T8, which is exactly the previous specification's own
#   behavior (leading check only), and T9, which derives the trailing refusal
#   from the raw arguments instead of from the computed trailing threshold.
#   Every witness point below was RECOMPUTED from the real routine under the new
#   signature and confirmed to agree in form, magnitude AND refusal before
#   shipping.
#
# AUDIT NOTE — FOURTH pass: CARRIER WIDENING (spec-too-weak repair).
#   A prior audit found a rival that VERIFIED and whose faithful patch did NOT
#   resolve, which is a counterexample to `verify => correct`. Its reduction was
#   `normCount scaled / 1`. Division by one is an identity on the magnitude, so
#   on the previous ℚ-valued carrier the specification could not see it at all —
#   yet in the target language that division is a TRUE division whose result is a
#   divisible amount, and the consumer that counts population members rejects it.
#   Diagnosed structurally rather than patched: the defect was not a missing
#   clause but the CARRIER, which recorded only the magnitude of the prepared
#   threshold and so modeled its form away. Measured, not argued: with the old
#   carrier, `∃ k : ℤ, result = (k : ℚ)` — the strongest magnitude-level
#   integrality claim available — is SATISFIED by that rival (build exit 0),
#   because `3` and `3.0` are the same rational. No postcondition over that
#   carrier could have closed the hole.
#   The repair replaces the carrier with `Threshold` (`count` | `quantity`), so
#   the reduction's delivery of a COUNT is observable and the clauses above pin
#   it. The pre-patch twins were re-expressed on the new carrier accordingly: the
#   real pre-patch expression `max(2, scaled)` returns whichever operand is the
#   larger, so it yields the floor-of-two as a count when the scaled amount is at
#   most two and the divisible scaled amount itself otherwise — confirmed against
#   the real routine at every boundary (0.5, 1.5, 1.9999, 2.0, 2.0000001, 2.4,
#   3.0, 3.7, 30.0: form and magnitude match at all nine).
#   NO reject case was dropped or weakened by this pass; all thirteen prior
#   rivals are re-expressed on the new carrier, and five NEW rivals (R9–R11,
#   T6–T7) attack the form dimension the old carrier could not express — the
#   family the counterexample belonged to.
#
# AUDIT NOTE — THIRD pass: MODEL-BOUNDARY realignment (faithfulness).
#   An adversarial faithfulness review shadowed the modeled function against the
#   real routine and found the battery's carrier itself misaligned, not any one
#   case: the previous carrier recomputed the population-scaling INSIDE the model
#   as an exact-rational product `x * (n:ℚ)`, and took the floor of THAT. The
#   real routine forms the scaled amount with the ordinary arithmetic it already
#   used, whose result is the nearest representable amount rather than the exact
#   rational product, and reduces THAT. The two disagree exactly where the
#   representable amount lands on the far side of an integer from the exact
#   product: at a threshold of three fifths on a population of five the real
#   routine hands over exactly 3 and delivers a count of 3, while the exact
#   rational product is just under 3 and the old carrier predicted 2. Measured
#   against the real routine, not argued: also at 3/10 on ten, 7/10 on ten, 8/9
#   on nine, 3/7 on seven.
#   The repair moves that scaling OUTSIDE the model boundary — the scaled amount
#   enters as an input (`scaled`, `scaledLead`, `scaledTrail`), carried exactly,
#   which is the boundary the nagini sibling already used — so the modeled
#   behavior is exactly the reduction the patch changed. Every witness point
#   below was then RECOMPUTED from the real routine: each states the exact
#   rational amount that routine actually hands over at its input, and each was
#   confirmed to agree with the real routine's captured output before shipping.
#   No reject case was dropped or weakened; the rivals are the same eight + five,
#   re-expressed on the new carrier.
#
# AUDIT NOTE — SECOND, INDEPENDENT audit. Two defects found and
# repaired; the evidence is machine-checked exit codes, not argument.
#   (4) Clause (T-msg) — the LEADING component's keep-unchanged branch inside
#       resolveThresholds — had NO rival. All four resolveThresholds rivals
#       (T1–T4) leave the leading guard intact, so none of their witnesses
#       sits on the `1 < minSamples.amount` leading branch in a way that pins the
#       leading component there. Measured, not asserted: a WEAKENED copy of the
#       frozen spec whose master clause leaves the first component free exactly
#       on the leading branch left every T1–T4 case behaving as declared, so the
#       clause was unattested. Closed by T5 below, whose witness at minSamples
#       with amount 5 refutes a dropped leading guard.
#   (5) Clause (M2) — the keep-unchanged branch of resolveMinSamples — likewise
#       had every witness inside the fractional branch. Closed by R6 (drop the
#       leading guard, normalizing unconditionally), witness at an absolute count
#       of 5; and the `≤ 1` vs `< 1` boundary is probed by R8, witness at exactly
#       1.
#
# OMITTED nagini cases and why:
#   * The FRAME / permission-mutation class is VACUOUS on this backend: Lean is
#     referentially transparent — no aliasing, no fractional permission — so
#     there is nothing to overwrite to satisfy a postcondition vacuously and no
#     counterpart rival to author.
#   * The DIVERGENCE / non-termination class: NOTHING TO SHIP, but NOT because a
#     diverging impl is unwritable. It is writable (`partial def` clears
#     `variant_problems`), but it is rejected for the WRONG REASON — `partial
#     def` compiles to an opaque constant rather than to equations, so the frozen
#     obligation dies at an `unfold` failure, not at a semantic refutation — and
#     no witness can repair it, since conditioned witnesses on an opaque constant
#     elaborate against gold too (`witness-vacuous`) and an opaque constant has
#     no computable value for an unconditioned one. Recorded as a KNOWN HOLE
#     rather than as a vacuous class: a vacuous class would claim the battery is
#     complete, and it is not.
#   * AXIOM_TESTS are dropped: the axiom lane is G-AX's job and this bundle ships
#     no consumed axiom (the reduction and the range check are both modeled
#     deeply, not over an opaque callee).
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14496"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — whole impl `def` blocks and proof bodies, each unique in the
# frozen Solution.lean and lying strictly inside the impl / proof regions.
# ---------------------------------------------------------------------------

_MIN_IMPL = """def implementation_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ) :
    Option Threshold := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := normCount scaled
    return some ms
  else
    return none"""

_MIN_PROOF = """  intro minSamples populationSize scaled
  unfold problem_spec_resolveMinSamples implementation_resolveMinSamples
  simp only [Id.run, bind, pure]
  split_ifs with hA hle
  · exact ⟨fun h => absurd hA h, fun _ => ⟨fun _ => rfl, fun h => absurd hle (not_le.mpr h)⟩⟩
  · exact ⟨fun h => absurd hA h, fun _ => ⟨fun h => absurd h hle, fun _ => rfl⟩⟩
  · exact ⟨fun _ => rfl, fun h => absurd h hA⟩"""

_TH_IMPL = """def implementation_resolveThresholds
    (minSamples : Threshold) (trailingThreshold : Option Threshold)
    (populationSize : ℕ) (scaledLead : ℚ) (scaledTrail : ℚ) :
    Option (Threshold × Threshold) := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := normCount scaledLead
    let mcs0 := trailingThreshold.getD ms
    if mcs0.admits populationSize then
      let mut mcs := mcs0
      if mcs.amount ≤ 1 then
        mcs := normCount scaledTrail
      return some (ms, mcs)
    else
      return none
  else
    return none"""

_TH_PROOF = """  intro minSamples trailingThreshold populationSize scaledLead scaledTrail
  unfold problem_spec_resolveThresholds implementation_resolveThresholds
  simp only [Id.run, bind, pure]
  split_ifs <;>
    simp_all"""


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT.
# ===========================================================================

# S1 — resolveMinSamples as a pure functional `if` (no `Id.run do`, no mutable
# local). Same value on every branch, refusal included; a faithful author could
# write this.
_S1_IMPL = """def implementation_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ) :
    Option Threshold :=
  if minSamples.admits populationSize then
    some (if minSamples.amount ≤ 1 then normCount scaled else minSamples)
  else
    none"""

_S1_PROOF = """  intro minSamples populationSize scaled
  unfold problem_spec_resolveMinSamples implementation_resolveMinSamples
  split_ifs with hA hle
  · exact ⟨fun h => absurd hA h, fun _ => ⟨fun _ => rfl, fun h => absurd hle (not_le.mpr h)⟩⟩
  · exact ⟨fun h => absurd hA h, fun _ => ⟨fun h => absurd h hle, fun _ => rfl⟩⟩
  · exact ⟨fun _ => rfl, fun h => absurd h hA⟩"""

# S2 — resolveThresholds as a chain of pure `let`s, mirroring the spec's own
# `let` structure. Same outcome on every path; the reproof is `split_ifs`.
_S2_IMPL = """def implementation_resolveThresholds
    (minSamples : Threshold) (trailingThreshold : Option Threshold)
    (populationSize : ℕ) (scaledLead : ℚ) (scaledTrail : ℚ) :
    Option (Threshold × Threshold) :=
  if minSamples.admits populationSize then
    let ms := if minSamples.amount ≤ 1 then normCount scaledLead else minSamples
    let mcs0 := trailingThreshold.getD ms
    if mcs0.admits populationSize then
      some (ms, if mcs0.amount ≤ 1 then normCount scaledTrail else mcs0)
    else
      none
  else
    none"""

_S2_PROOF = """  intro minSamples trailingThreshold populationSize scaledLead scaledTrail
  unfold problem_spec_resolveThresholds implementation_resolveThresholds
  split_ifs <;>
    simp_all"""

# S3 (SOUNDNESS) — a CORRECT impl that reaches the same outcome by a different
# route: it destructures the incoming threshold and branches per form instead of
# consulting the amount through the accessor. Observationally equal to gold on
# every input, so it must verify; it exists to show the spec does not secretly
# demand gold's exact syntactic shape.
_S3_IMPL = """def implementation_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ) :
    Option Threshold :=
  if minSamples.admits populationSize then
    match minSamples with
    | .count k => if (k : ℚ) ≤ 1 then some (normCount scaled) else some (.count k)
    | .quantity q => if q ≤ 1 then some (normCount scaled) else some (.quantity q)
  else
    none"""

_S3_PROOF = """  intro minSamples populationSize scaled
  unfold problem_spec_resolveMinSamples implementation_resolveMinSamples
  split_ifs with hA
  · cases minSamples with
    | count k =>
      refine ⟨fun h => absurd hA h, fun _ => ⟨fun h => ?_, fun h => ?_⟩⟩
      · simp only [Threshold.amount] at h; simp only [h, if_true]
      · simp only [Threshold.amount] at h; simp only [not_le.mpr h, if_false]
    | quantity q =>
      refine ⟨fun h => absurd hA h, fun _ => ⟨fun h => ?_, fun h => ?_⟩⟩
      · simp only [Threshold.amount] at h; simp only [h, if_true]
      · simp only [Threshold.amount] at h; simp only [not_le.mpr h, if_false]
  · exact ⟨fun _ => rfl, fun h => absurd h hA⟩"""

# S4 (ADMISSIBILITY) — the frozen impls, unchanged, with anonymous `example`s
# appended INSIDE the impl region. They witness that the obligations are
# SATISFIABLE at concrete inputs of BOTH outcome shapes — a delivered pair and a
# refusal — computed rather than assumed. The modeled functions are total (there
# are no proof-binder preconditions left to admit an input past), so the
# admissibility question here is whether the postcondition can be satisfied at a
# normal input at all, and whether the refusal branch is REACHABLE rather than
# vacuous: an unreachable refusal clause would make (M0)/(T-r0)/(T-r1) idle.
# `example` declares no name, so this adds no `theorem`/`lemma` and stays inside
# `variant_scope`.
_S4_IMPL = _TH_IMPL + """

/-- A normal input: the two-threshold obligation is satisfiable there. -/
example : problem_spec_resolveThresholds (.quantity (1/2))
    (some (.quantity (1/2))) 7 (7/2) (7/2)
    (implementation_resolveThresholds (.quantity (1/2))
      (some (.quantity (1/2))) 7 (7/2) (7/2)) := by
  unfold problem_spec_resolveThresholds implementation_resolveThresholds
    normCount Threshold.admits
  simp only [Id.run, bind, pure, Threshold.amount]
  norm_num

/-- ...as is the single-threshold obligation. -/
example : problem_spec_resolveMinSamples (.quantity (1/2)) 7 (7/2)
    (implementation_resolveMinSamples (.quantity (1/2)) 7 (7/2)) := by
  unfold problem_spec_resolveMinSamples implementation_resolveMinSamples
    normCount Threshold.admits
  simp only [Id.run, bind, pure, Threshold.amount]
  norm_num

/-- The refusal branch is REACHABLE, not vacuous: the range check really does
refuse a threshold that is neither whole nor at most one, and the obligation is
satisfiable at that input too. -/
example : ¬ (Threshold.quantity (5/2)).admits 10 ∧
    problem_spec_resolveMinSamples (.quantity (5/2)) 10 25
      (implementation_resolveMinSamples (.quantity (5/2)) 10 25) := by
  refine ⟨?_, ?_⟩
  · unfold Threshold.admits
    simp only [Threshold.amount]
    norm_num
  · unfold problem_spec_resolveMinSamples implementation_resolveMinSamples
      normCount Threshold.admits
    simp only [Id.run, bind, pure, Threshold.amount]
    norm_num

/-- ...and it is reachable in the pair routine too, on the path where the
LEADING threshold is admitted and the trailing one is not. -/
example : (Threshold.count 3).admits 10 ∧ ¬ (Threshold.count 11).admits 10 ∧
    problem_spec_resolveThresholds (.count 3) (some (.count 11)) 10 30 110
      (implementation_resolveThresholds (.count 3) (some (.count 11)) 10 30 110) := by
  refine ⟨?_, ?_, ?_⟩
  · unfold Threshold.admits; simp only [Threshold.amount]; norm_num
  · unfold Threshold.admits; simp only [Threshold.amount]; norm_num
  · unfold problem_spec_resolveThresholds implementation_resolveThresholds
      normCount Threshold.admits
    simp only [Id.run, bind, pure, Threshold.amount]
    norm_num"""


# ===========================================================================
# UNIQUENESS rivals on resolveMinSamples.
# Each replaces ONLY the reduction inside the fractional branch (or the guard /
# the range check, for R6, R8, R12–R15) with a wrong one.
# ===========================================================================

# R1 — UNREDUCED ECHO (the pre-patch body). Clamps against the floor of two but
# does not reduce to a whole-number count, so above that floor it delivers the
# divisible scaled amount.
_R1_IMPL = """def implementation_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ) :
    Option Threshold := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := if scaled ≤ 2 then .count 2 else .quantity scaled
    return some ms
  else
    return none"""

# R2 — OVER-COUNT BY ONE (ceiling-like on non-integral scaled amounts).
_R2_IMPL = """def implementation_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ) :
    Option Threshold := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := .count (max 2 ⌊scaled⌋ + 1)
    return some ms
  else
    return none"""

# R3 — FLOOR-OF-TWO ONLY (partial-domain: correct only where the count is 2).
_R3_IMPL = """def implementation_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ) :
    Option Threshold := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := .count 2
    return some ms
  else
    return none"""

# R4 — DROP THE CLAMP-TO-TWO. Reduces the scaled amount but omits `max 2`, so a
# small fraction yields a count below two.
_R4_IMPL = """def implementation_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ) :
    Option Threshold := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := .count ⌊scaled⌋
    return some ms
  else
    return none"""

# R5 — ROUND-TO-NEAREST (the whole-number part of the amount plus one half).
# Rounds up at the half-way boundary.
_R5_IMPL = """def implementation_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ) :
    Option Threshold := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := .count (max 2 ⌊scaled + 1/2⌋)
    return some ms
  else
    return none"""

# R6 — DROPPED LEADING GUARD. Reduces the scaled amount UNCONDITIONALLY, so a
# threshold already given as an absolute count is replaced by the count derived
# from the scaled amount instead of kept unchanged. Attacks clause (M2).
_R6_IMPL = """def implementation_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ) :
    Option Threshold := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    ms := normCount scaled
    return some ms
  else
    return none"""

# R7 — STRICT-UNDERCOUNT (one below the whole-number part, clamped).
_R7_IMPL = """def implementation_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ) :
    Option Threshold := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := .count (max 2 (⌊scaled⌋ - 1))
    return some ms
  else
    return none"""

# R8 — BOUNDARY OFF-BY-ONE on the branch guard (`< 1` for `≤ 1`), so a threshold
# whose amount is exactly one takes the keep-unchanged branch instead of being
# reduced.
_R8_IMPL = """def implementation_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ) :
    Option Threshold := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount < 1 then
      ms := normCount scaled
    return some ms
  else
    return none"""

# ---------------------------------------------------------------------------
# FORM rivals (R9–R11) — the family a prior counterexample belonged to. Each
# computes the CORRECT MAGNITUDE and delivers it in the wrong form. On the
# previous magnitude-only carrier every one of these was invisible; here each is
# refuted at a literal input.
# ---------------------------------------------------------------------------

# R9 — RIGHT MAGNITUDE, DIVISIBLE FORM. The reduction reduces and clamps exactly
# as gold does, then hands the result over as a divisible quantity instead of as
# a count.
_R9_IMPL = """def implementation_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ) :
    Option Threshold := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := .quantity ((max 2 ⌊scaled⌋ : ℤ) : ℚ)
    return some ms
  else
    return none"""

# R10 — FORM ECHO OF THE INPUT (partial-domain form rival). Delivers a count
# only when the incoming threshold already arrived as a count, and otherwise
# keeps the fraction's divisible form while still computing the right magnitude.
_R10_IMPL = """def implementation_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ) :
    Option Threshold := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := match ms with
        | .count _ => normCount scaled
        | .quantity _ => .quantity ((max 2 ⌊scaled⌋ : ℤ) : ℚ)
    return some ms
  else
    return none"""

# R11 — FORM SPLIT ON MAGNITUDE (boundary form rival). Delivers a count only
# where the reduced magnitude is exactly the clamp floor of two, and a divisible
# quantity above it.
_R11_IMPL = """def implementation_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ) :
    Option Threshold := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := if ⌊scaled⌋ ≤ 2 then .count 2 else .quantity ((⌊scaled⌋ : ℤ) : ℚ)
    return some ms
  else
    return none"""

# ---------------------------------------------------------------------------
# PARTIALITY rivals (R12–R15) — the dimension the previous carrier could not
# express. Each computes the right prepared threshold wherever it delivers one;
# what it gets wrong is WHETHER a threshold is prepared at all.
# ---------------------------------------------------------------------------

# R12 — NO RANGE CHECK AT ALL. Prepares every threshold, so a threshold the
# check refuses is delivered instead of refused. Total-where-the-real-routine-is
# -partial: the crudest partiality defect, and correct on every admitted input.
_R12_IMPL = """def implementation_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ) :
    Option Threshold := Id.run do
  let mut ms := minSamples
  if ms.amount ≤ 1 then
    ms := normCount scaled
  return some ms"""

# R13 — PART OF THE CHECK ONLY (the folded-helper defect). Keeps the positivity
# and population-size legs and DROPS the whole-or-at-most-one leg, so a
# non-integral amount above one is prepared instead of refused. Correct on every
# other refusal shape and on every admitted input, so a witness taken at a
# non-positive or oversized threshold would not discriminate it.
_R13_IMPL = """def implementation_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ) :
    Option Threshold := Id.run do
  if 0 < minSamples.amount ∧ minSamples.amount ≤ (populationSize : ℚ) then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := normCount scaled
    return some ms
  else
    return none"""

# R14 — OVER-REFUSAL (the complementary direction). Demands a WHOLE amount
# unconditionally, dropping the at-most-one alternative, so a fraction — the
# very case the reduction exists for — is refused instead of prepared. Correct on
# every count-shaped input and on every refusal the real check performs; wrong
# exactly where the repaired clause now permits a delivered result.
_R14_IMPL = """def implementation_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ) :
    Option Threshold := Id.run do
  if 0 < minSamples.amount ∧ minSamples.amount.den = 1 ∧
      minSamples.amount ≤ (populationSize : ℚ) then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := normCount scaled
    return some ms
  else
    return none"""

# R15 — POPULATION-SIZE BOUNDARY OFF-BY-ONE (`<` for `≤`), so a threshold whose
# amount equals the population size exactly is refused instead of prepared.
# Partial-domain on a single boundary: it agrees with the frozen behaviour
# everywhere except at that one point, which no other partiality witness visits.
_R15_IMPL = """def implementation_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ) :
    Option Threshold := Id.run do
  if 0 < minSamples.amount ∧ (minSamples.amount.den = 1 ∨ minSamples.amount ≤ 1) ∧
      minSamples.amount < (populationSize : ℚ) then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := normCount scaled
    return some ms
  else
    return none"""


# ===========================================================================
# UNIQUENESS rivals on resolveThresholds (attack the widened surface).
# ===========================================================================

# T1 — leading component unreduced (pre-patch form); trailing left correct.
_T1_IMPL = """def implementation_resolveThresholds
    (minSamples : Threshold) (trailingThreshold : Option Threshold)
    (populationSize : ℕ) (scaledLead : ℚ) (scaledTrail : ℚ) :
    Option (Threshold × Threshold) := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := if scaledLead ≤ 2 then .count 2 else .quantity scaledLead
    let mcs0 := trailingThreshold.getD ms
    if mcs0.admits populationSize then
      let mut mcs := mcs0
      if mcs.amount ≤ 1 then
        mcs := normCount scaledTrail
      return some (ms, mcs)
    else
      return none
  else
    return none"""

# T2 — trailing component unreduced; leading left correct.
_T2_IMPL = """def implementation_resolveThresholds
    (minSamples : Threshold) (trailingThreshold : Option Threshold)
    (populationSize : ℕ) (scaledLead : ℚ) (scaledTrail : ℚ) :
    Option (Threshold × Threshold) := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := normCount scaledLead
    let mcs0 := trailingThreshold.getD ms
    if mcs0.admits populationSize then
      let mut mcs := mcs0
      if mcs.amount ≤ 1 then
        mcs := if scaledTrail ≤ 2 then .count 2 else .quantity scaledTrail
      return some (ms, mcs)
    else
      return none
  else
    return none"""

# T3 — WRONG UNSET-DEFAULT. An unset trailing threshold defaults to a constant
# count of two instead of the reduced leading threshold.
_T3_IMPL = """def implementation_resolveThresholds
    (minSamples : Threshold) (trailingThreshold : Option Threshold)
    (populationSize : ℕ) (scaledLead : ℚ) (scaledTrail : ℚ) :
    Option (Threshold × Threshold) := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := normCount scaledLead
    let mcs0 := trailingThreshold.getD (.count 2)
    if mcs0.admits populationSize then
      let mut mcs := mcs0
      if mcs.amount ≤ 1 then
        mcs := normCount scaledTrail
      return some (ms, mcs)
    else
      return none
  else
    return none"""

# T4 — DROPPED TRAILING GUARD. Reduces the trailing scaled amount
# UNCONDITIONALLY, so a present threshold whose amount exceeds one is replaced
# instead of kept.
_T4_IMPL = """def implementation_resolveThresholds
    (minSamples : Threshold) (trailingThreshold : Option Threshold)
    (populationSize : ℕ) (scaledLead : ℚ) (scaledTrail : ℚ) :
    Option (Threshold × Threshold) := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := normCount scaledLead
    let mcs0 := trailingThreshold.getD ms
    if mcs0.admits populationSize then
      let mut mcs := mcs0
      mcs := normCount scaledTrail
      return some (ms, mcs)
    else
      return none
  else
    return none"""

# T5 — DROPPED LEADING GUARD on resolveThresholds. Attacks (T-msg); NOT
# redundant with R6, since the two functions carry separate obligations.
_T5_IMPL = """def implementation_resolveThresholds
    (minSamples : Threshold) (trailingThreshold : Option Threshold)
    (populationSize : ℕ) (scaledLead : ℚ) (scaledTrail : ℚ) :
    Option (Threshold × Threshold) := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    ms := normCount scaledLead
    let mcs0 := trailingThreshold.getD ms
    if mcs0.admits populationSize then
      let mut mcs := mcs0
      if mcs.amount ≤ 1 then
        mcs := normCount scaledTrail
      return some (ms, mcs)
    else
      return none
  else
    return none"""

# T6 — FORM DEFECT ON THE LEADING COMPONENT ONLY. Right magnitudes throughout;
# the leading reduction delivers a divisible quantity while the trailing one is
# a correct count.
_T6_IMPL = """def implementation_resolveThresholds
    (minSamples : Threshold) (trailingThreshold : Option Threshold)
    (populationSize : ℕ) (scaledLead : ℚ) (scaledTrail : ℚ) :
    Option (Threshold × Threshold) := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := .quantity ((max 2 ⌊scaledLead⌋ : ℤ) : ℚ)
    let mcs0 := trailingThreshold.getD ms
    if mcs0.admits populationSize then
      let mut mcs := mcs0
      if mcs.amount ≤ 1 then
        mcs := normCount scaledTrail
      return some (ms, mcs)
    else
      return none
  else
    return none"""

# T7 — FORM DEFECT ON THE TRAILING COMPONENT ONLY. The complementary half.
_T7_IMPL = """def implementation_resolveThresholds
    (minSamples : Threshold) (trailingThreshold : Option Threshold)
    (populationSize : ℕ) (scaledLead : ℚ) (scaledTrail : ℚ) :
    Option (Threshold × Threshold) := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := normCount scaledLead
    let mcs0 := trailingThreshold.getD ms
    if mcs0.admits populationSize then
      let mut mcs := mcs0
      if mcs.amount ≤ 1 then
        mcs := .quantity ((max 2 ⌊scaledTrail⌋ : ℤ) : ℚ)
      return some (ms, mcs)
    else
      return none
  else
    return none"""

# ---------------------------------------------------------------------------
# PARTIALITY rivals on resolveThresholds (T8–T10) — the pair routine applies the
# range check to EACH threshold in turn, and the trailing one's subject is a
# value the routine has itself computed. These three attack exactly that.
# ---------------------------------------------------------------------------

# T8 — LEADING CHECK ONLY. Checks the leading threshold and never checks the
# trailing one, so a pair whose trailing threshold the check refuses is delivered
# instead of refused. This is the sharpest rival in the battery: it is correct on
# every input whose trailing threshold happens to be in range — which is most of
# them, and all of the ones a uniform fuzz visits — and it is wrong precisely on
# the class where the DEFAULTED trailing threshold, being the clamped-up leading
# one, can leave the range the leading input was inside. Attacks (T-r1).
_T8_IMPL = """def implementation_resolveThresholds
    (minSamples : Threshold) (trailingThreshold : Option Threshold)
    (populationSize : ℕ) (scaledLead : ℚ) (scaledTrail : ℚ) :
    Option (Threshold × Threshold) := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := normCount scaledLead
    let mut mcs := trailingThreshold.getD ms
    if mcs.amount ≤ 1 then
      mcs := normCount scaledTrail
    return some (ms, mcs)
  else
    return none"""

# T9 — UNGROUNDED TRAILING CHECK. Applies a check for the trailing threshold, but
# to the WRONG SUBJECT: it tests the trailing threshold defaulted from the
# UNREDUCED leading input rather than from the reduced one, i.e. it derives the
# refusal from the arguments it was handed instead of from the value the routine
# computed. Indistinguishable from correct whenever a trailing threshold is
# supplied, and whenever the raw and reduced leading thresholds agree on
# admissibility; wrong exactly where the reduction moves the defaulted value out
# of range. Attacks (T-r1) at the "did the check consult the computed value"
# level, which a rival that merely omits the check cannot probe.
_T9_IMPL = """def implementation_resolveThresholds
    (minSamples : Threshold) (trailingThreshold : Option Threshold)
    (populationSize : ℕ) (scaledLead : ℚ) (scaledTrail : ℚ) :
    Option (Threshold × Threshold) := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := normCount scaledLead
    if (trailingThreshold.getD minSamples).admits populationSize then
      let mut mcs := trailingThreshold.getD ms
      if mcs.amount ≤ 1 then
        mcs := normCount scaledTrail
      return some (ms, mcs)
    else
      return none
  else
    return none"""

# T10 — TRAILING CHECK ONLY. The complement of T8: the leading threshold is
# never checked, so a leading threshold the check refuses reaches the reduction
# and a pair is delivered. Correct on every input whose leading threshold is in
# range. Attacks (T-r0).
_T10_IMPL = """def implementation_resolveThresholds
    (minSamples : Threshold) (trailingThreshold : Option Threshold)
    (populationSize : ℕ) (scaledLead : ℚ) (scaledTrail : ℚ) :
    Option (Threshold × Threshold) := Id.run do
  let mut ms := minSamples
  if ms.amount ≤ 1 then
    ms := normCount scaledLead
  let mcs0 := trailingThreshold.getD ms
  if mcs0.admits populationSize then
    let mut mcs := mcs0
    if mcs.amount ≤ 1 then
      mcs := normCount scaledTrail
    return some (ms, mcs)
  else
    return none"""


# ---------------------------------------------------------------------------
# Witnesses. Each states the spec predicate directly at a concrete input; the
# `Id.run do` block is reduced by `simp only [Id.run, bind, pure]` and the
# whole-number part of a ℚ is computed by `norm_num`/`simp` (`decide` gets stuck
# on `Rat.floor`). `Threshold` derives `DecidableEq`, so a FORM mismatch is
# decided outright, and `Option` is decidable too, so a REFUSAL mismatch
# (`none` where a pair is required, or a pair where `none` is) is decided as
# well.
# The closer is two-step because a refutation lands in one of three shapes.
# When the rival's magnitude is wrong, `norm_num` finishes on the spot. When the
# magnitudes AGREE and only the form differs, `norm_num` computes both sides and
# leaves the residual constructor disequality (`¬ quantity 3 = count 3`), which
# the trailing `all_goals simp_all` discharges from the derived injectivity
# lemmas; the same closer handles the `some`/`none` disequalities on the
# partiality cases. Against the frozen solution every shape collapses to `¬ x = x`
# and the witness FAILS, which is what makes it a discriminator: each was built
# against the rival (must elaborate) and against the frozen solution (must fail),
# not a tautology.
# ---------------------------------------------------------------------------

def _w_min(args, pop, scaled):
    return (
        "example : ¬ problem_spec_resolveMinSamples (%s) (%s) (%s)\n"
        "    (implementation_resolveMinSamples (%s) (%s) (%s)) := by\n"
        "  unfold problem_spec_resolveMinSamples implementation_resolveMinSamples\n"
        "    normCount Threshold.admits\n"
        "  simp only [Id.run, bind, pure, Threshold.amount]\n"
        "  norm_num\n"
        "  all_goals simp_all" % (args, pop, scaled, args, pop, scaled))


def _w_th(ms, mcs, pop, lead, trail):
    return (
        "example : ¬ problem_spec_resolveThresholds (%s) (%s) (%s) (%s) (%s)\n"
        "    (implementation_resolveThresholds (%s) (%s) (%s) (%s) (%s)) := by\n"
        "  unfold problem_spec_resolveThresholds implementation_resolveThresholds\n"
        "    normCount Threshold.admits\n"
        "  simp only [Id.run, bind, pure, Threshold.amount]\n"
        "  norm_num\n"
        "  all_goals simp_all" % (ms, mcs, pop, lead, trail,
                                  ms, mcs, pop, lead, trail))


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = [

    # ---- POSITIVE CONTROLS (soundness; must verify) --------------------
    {
        "id": "pos-min-functional-if",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _MIN_IMPL, _S1_IMPL), _MIN_PROOF, _S1_PROOF),
        "rationale": (
            "A structurally-different but CORRECT single-threshold impl: a pure "
            "functional `if` with no `Id.run do` block and no mutable local, "
            "returning the same outcome on each branch, refusal included. It must "
            "verify against clauses (M0)/(M1)/(M2); if a faithful correct reshape "
            "cannot satisfy them the spec is SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-thresholds-let-chain",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _TH_IMPL, _S2_IMPL), _TH_PROOF, _S2_PROOF),
        "rationale": (
            "A structurally-different but CORRECT two-threshold impl: a chain of "
            "pure `let`s (no `Id.run do`, no mutable locals) mirroring the spec's "
            "own `let` structure, with the same two range checks in the same "
            "order. Same outcome on every input. Must verify against the master "
            "clause and both refusal clauses, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-min-match-on-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _MIN_IMPL, _S3_IMPL), _MIN_PROOF, _S3_PROOF),
        "rationale": (
            "A CORRECT impl that reaches the same answer by DESTRUCTURING the "
            "incoming threshold and branching per form, rather than by consulting "
            "its amount through the accessor. Observationally equal to the frozen "
            "impl on every input. This case exists because the spec observes form: "
            "it checks that the specification pins the OUTPUT's form without "
            "demanding any particular way of inspecting the INPUT's — a correct "
            "author who pattern-matches must still verify, else the carrier has "
            "over-fitted to gold's accessor style."
        ),
    },
    {
        "id": "admiss-normal-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _TH_IMPL, _S4_IMPL),
        "rationale": (
            "The frozen impls unchanged, plus anonymous `example`s inside the "
            "impl region witnessing that each obligation is SATISFIABLE at a "
            "normal input (a fractional leading threshold with a present "
            "fractional trailing threshold, with their scaled amounts) — the spec "
            "predicate is computed to hold of the impl's own output, not assumed. "
            "The modeled functions are TOTAL, so the admissibility question is "
            "not whether an input gets past a precondition but whether the "
            "postcondition is satisfiable at a normal input AND whether the "
            "refusal branch is REACHABLE: two further examples compute that the "
            "range check really does refuse a non-integral threshold above one, "
            "and that the pair routine's trailing refusal is reachable with the "
            "leading threshold admitted. Were the refusal clauses vacuous, (M0) / "
            "(T-r0) / (T-r1) would be idle and the partiality rivals below would "
            "attest nothing. `variant_scope` bans only a NAMED `theorem`/`lemma`; "
            "an `example` is admissible."
        ),
    },

    # ---- UNIQUENESS on resolveMinSamples -------------------------------
    {
        "id": "weak-min-unfloored-echo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_IMPL, _R1_IMPL),
        "refinement": (
            "This is the pre-patch behavior itself: clamp against the floor of "
            "two, delivering whichever operand is larger, with no reduction to a "
            "whole-number count. A faithful patch with this body leaves the "
            "fractional threshold as a divisible amount; the population-counting "
            "downstream neighbour search raises the very TypeError the issue "
            "reports, so the failing test does NOT pass. A verifying rival here is "
            "a true verify-does-not-resolve break."
        ),
        "rationale": (
            "Rejected by (M1): at a fractional threshold of 1/2 on a population of "
            "seven the scaled amount is 7/2, whose whole-number part exceeds the "
            "floor of two, so this delivers the divisible 7/2 where "
            "`normCount scaled` is the count 3 — wrong in both magnitude and form. "
            "Confirmed against the real routine at that input: it delivers the "
            "count 3."
        ),
        "witness": _w_min(".quantity (1/2)", "7", "7/2"),
    },
    {
        "id": "weak-min-overcount-ceiling",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_IMPL, _R2_IMPL),
        "refinement": (
            "Returning the whole-number count plus one is a ceiling on "
            "non-integral scaled amounts (7/2 → 4). A faithful patch using a "
            "ceiling of the scaled amount over-counts neighbours, so the "
            "fractional run no longer matches the integer-parameter run the "
            "failing test asserts equal → would not resolve."
        ),
        "rationale": (
            "Rejected by (M1): at 1/2 on a population of seven with scaled=7/2 the "
            "count must be 3 (the real routine's captured output), but the rival "
            "returns a count of 4."
        ),
        "witness": _w_min(".quantity (1/2)", "7", "7/2"),
    },
    {
        "id": "weak-min-floor-of-two-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_IMPL, _R3_IMPL),
        "refinement": (
            "Always returning a count of two on the fractional branch is correct "
            "only where the real count is two; on the failing test's fraction the "
            "count must exceed two, so collapsing it changes the neighbour count "
            "and the fractional run diverges from the integer-parameter run → does "
            "not resolve."
        ),
        "rationale": (
            "Rejected by (M1): at 1/2 on seven with scaled=7/2 the count must be 3, "
            "but the rival returns the constant 2."
        ),
        "witness": _w_min(".quantity (1/2)", "7", "7/2"),
    },
    {
        "id": "weak-min-drop-clamp-to-two",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_IMPL, _R4_IMPL),
        "refinement": (
            "Reducing the scaled amount but omitting the clamp-to-two lets a "
            "small fraction produce a count below two, which the guaranteed "
            "floor-of-two behaviour forbids → would not resolve. Partial-domain "
            "rival: correct wherever the whole-number part already exceeds two, "
            "wrong only on the small-fraction sub-domain."
        ),
        "rationale": (
            "Rejected by (M1): at a threshold of 1/10 on a population of five the "
            "scaled amount is 1/2, whose whole-number part is 0; normCount clamps "
            "to a count of 2 — which is what the real routine delivers there — but "
            "the rival returns 0. This is the ONLY point that exercises the clamp "
            "binder (a scaled amount below two)."
        ),
        "witness": _w_min(".quantity (1/10)", "5", "1/2"),
    },
    {
        "id": "weak-min-round-to-nearest",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_IMPL, _R5_IMPL),
        "refinement": (
            "Round-to-nearest agrees with the frozen reduction on amounts whose "
            "fractional part is below one half but diverges on any amount at least "
            "half above an integer (5/2 rounds to 3 vs the frozen 2). A faithful "
            "patch rounding the scaled amount would over-count on such inputs → "
            "would not resolve."
        ),
        "rationale": (
            "Rejected by (M1): at 1/2 on a population of five the scaled amount is "
            "5/2 and the frozen reduction gives the count 2 — confirmed as the real "
            "routine's captured output at that input — while the rival rounds to 3. "
            "This is the point sitting exactly on the half-way boundary the other "
            "rivals miss."
        ),
        "witness": _w_min(".quantity (1/2)", "5", "5/2"),
    },
    {
        "id": "weak-min-strict-undercount",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_IMPL, _R7_IMPL),
        "refinement": (
            "Subtracting one from the whole-number part (then clamping) undercounts "
            "the fractional threshold by one, passing too few neighbours "
            "downstream → would not resolve."
        ),
        "rationale": (
            "Rejected by (M1): at 1/2 on seven with scaled=7/2 the count must be 3, "
            "but the rival returns max(2, 3−1) = 2."
        ),
        "witness": _w_min(".quantity (1/2)", "7", "7/2"),
    },
    {
        "id": "weak-min-dropped-leading-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_IMPL, _R6_IMPL),
        "refinement": (
            "Reduces the scaled amount UNCONDITIONALLY, dropping the "
            "fraction-vs-count discrimination entirely, so a threshold already "
            "supplied as an absolute count is replaced by the count derived from "
            "the scaled amount instead of used as given. A faithful patch that "
            "reduced on every path would inflate an absolute count by a factor of "
            "the population size (a caller asking for 5 neighbours would get 155 "
            "on 31 samples), changing the neighbour count on the "
            "INTEGER-parameter runs the failing test compares against — so it "
            "would not resolve. Complement of the fractional-branch rivals, which "
            "all leave the keep-unchanged branch alone."
        ),
        "rationale": (
            "Rejected by (M2): at an absolute count of 5 on a population of 31 the "
            "threshold must be returned unchanged — the real routine delivers the "
            "count 5 there — but the rival reduces the scaled amount anyway and "
            "returns a count of 155. This is the only resolveMinSamples magnitude "
            "witness on the keep-unchanged branch, and hence the only one that pins "
            "(M2)."
        ),
        "witness": _w_min(".count 5", "31", "155"),
    },
    {
        "id": "weak-min-boundary-strict-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_IMPL, _R8_IMPL),
        "refinement": (
            "Tests the branch guard strictly (`< 1` for `≤ 1`), so a threshold of "
            "exactly one — the largest amount the spec still treats as a fraction "
            "— is misrouted to the keep-unchanged branch and returned as one "
            "instead of as the count derived from its scaled amount. A faithful "
            "patch with a strict comparison would pass a neighbour count of one "
            "downstream, below the guaranteed floor of two → would not resolve. "
            "Partial-domain rival: it agrees with the frozen behaviour everywhere "
            "EXCEPT the single boundary point."
        ),
        "rationale": (
            "Rejected by (M1): a threshold of exactly 1 satisfies the `≤ 1` guard, "
            "so on a population of 31 the result must be the count 31 — the real "
            "routine's captured output there — but the rival's strict guard skips "
            "the reduction and returns the threshold as it arrived. This is the "
            "exact value where `≤ 1` and `< 1` part company."
        ),
        "witness": _w_min(".quantity 1", "31", "31"),
    },

    # ---- UNIQUENESS on the FORM dimension --------------------------------
    {
        "id": "weak-min-right-magnitude-divisible-form",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_IMPL, _R9_IMPL),
        "refinement": (
            "Reduces and clamps EXACTLY as the frozen reduction does, then hands "
            "the result over as a divisible amount rather than as an absolute "
            "count. This is the family of the counterexample that forced this "
            "battery's carrier widening: a faithful patch whose reduction keeps "
            "the amount divisible (a true division by one being the cheapest way "
            "to do so) delivers a threshold whose magnitude is whole but whose "
            "form the population-counting consumer refuses, which is precisely the "
            "TypeError the issue reports — so the failing test does NOT pass even "
            "though every magnitude agrees with gold."
        ),
        "rationale": (
            "Rejected by (M1) read as an equality of THRESHOLDS: at 1/2 on seven "
            "with scaled=7/2 the magnitudes agree (both 3) and the refutation turns "
            "entirely on the form — the rival delivers a divisible amount where "
            "`normCount scaled` is a count. Decided by the carrier's derived "
            "equality. On the previous magnitude-only carrier this rival was NOT "
            "expressible as a defect at all: it satisfied every clause, including "
            "an explicit integrality claim, because a whole magnitude and a count "
            "were the same object there."
        ),
        "witness": _w_min(".quantity (1/2)", "7", "7/2"),
    },
    {
        "id": "weak-min-form-echoes-input",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_IMPL, _R10_IMPL),
        "refinement": (
            "Delivers a proper count only when the incoming threshold ALREADY "
            "arrived as a count, and otherwise computes the right magnitude but "
            "keeps the fraction's divisible form. A faithful patch of this shape "
            "fixes nothing on the reported input — a fraction is exactly the case "
            "the reduction exists for — so the failing test still raises → would "
            "not resolve. Partial-domain rival on the FORM axis: correct on "
            "count-shaped inputs, wrong on the fractional ones that matter."
        ),
        "rationale": (
            "Rejected by (M1): at the fractional threshold 1/2 on seven with "
            "scaled=7/2 the magnitude is right (3) but the form is divisible, where "
            "the spec demands a count. This rival exists to stop a form clause that "
            "is satisfied merely by PROPAGATING the input's form: it is correct "
            "wherever the input was already a count, so a witness taken only at a "
            "count-shaped input would not discriminate it."
        ),
        "witness": _w_min(".quantity (1/2)", "7", "7/2"),
    },
    {
        "id": "weak-min-form-splits-on-magnitude",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_IMPL, _R11_IMPL),
        "refinement": (
            "Delivers a count only where the reduced magnitude sits at the clamp "
            "floor of two, and a divisible amount above it (also dropping the "
            "clamp on that upper branch). A faithful patch of this shape is "
            "correct only on the small-fraction sub-domain and still raises the "
            "downstream TypeError on the reported input → would not resolve."
        ),
        "rationale": (
            "Rejected by (M1): at 1/2 on seven with scaled=7/2 the whole-number "
            "part is 3, above the clamp floor, so the rival delivers a divisible "
            "amount where the spec demands the count 3. Boundary/partial-domain "
            "form rival: it is correct at every point whose reduced magnitude is at "
            "most two, which is exactly where the clamp witness (1/10 on five, "
            "scaled=1/2) sits — so it also attests that the form obligation is "
            "pinned ABOVE the clamp boundary and not only at it."
        ),
        "witness": _w_min(".quantity (1/2)", "7", "7/2"),
    },

    # ---- UNIQUENESS on the PARTIALITY dimension -------------------------
    {
        "id": "weak-min-no-range-check",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_IMPL, _R12_IMPL),
        "refinement": (
            "Prepares EVERY threshold, so a threshold the range check refuses is "
            "used instead of refused. A faithful patch that dropped the check would "
            "let an out-of-range threshold reach the population-counting consumer, "
            "replacing a clear refusal with whatever that consumer does with a bad "
            "count — the callers relying on the refusal stop getting it. Correct on "
            "every admitted input, so only a witness on a refused one discriminates "
            "it."
        ),
        "rationale": (
            "Rejected by (M0): a threshold of 5/2 on a population of ten is "
            "neither whole nor at most one, so the check refuses it and the result "
            "must be `none` — confirmed against the real routine, which raises "
            "there rather than delivering a count — but the rival prepares it and "
            "delivers a threshold. Decided by `Option`'s derived equality."
        ),
        "witness": _w_min(".quantity (5/2)", "10", "25"),
    },
    {
        "id": "weak-min-partial-range-check",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_IMPL, _R13_IMPL),
        "refinement": (
            "Applies only PART of the range check: it keeps the positivity and "
            "population-size legs and drops the whole-or-at-most-one leg, so a "
            "non-integral amount above one is prepared instead of refused. This is "
            "the folded-helper defect — a check consulted for some of its "
            "conditions and not others — and it is invisible to any witness taken "
            "at a non-positive or oversized threshold, since those it still "
            "refuses correctly."
        ),
        "rationale": (
            "Rejected by (M0) on the leg the rival dropped: at 5/2 on a population "
            "of ten the amount is positive and below the population, so the rival "
            "prepares it, while the real routine refuses it (it is neither whole "
            "nor at most one) and the spec requires `none`. Deliberately the SAME "
            "witness point as the no-check rival, since what distinguishes the two "
            "is which conditions each retains, not where they fail."
        ),
        "witness": _w_min(".quantity (5/2)", "10", "25"),
    },
    {
        "id": "weak-min-over-refusal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_IMPL, _R14_IMPL),
        "refinement": (
            "The complementary direction: demands a WHOLE amount unconditionally, "
            "dropping the at-most-one alternative, so a fraction — the very case "
            "the reduction exists for — is refused instead of prepared. A faithful "
            "patch of this shape refuses every fractional threshold, so the "
            "fractional run in the failing test raises instead of clustering → "
            "would not resolve. Correct on every count-shaped input AND on every "
            "refusal the real check performs, which is what makes it the sharp test "
            "of whether the refusal clause is pinned to exactly the refused inputs "
            "rather than merely permitting a refusal somewhere."
        ),
        "rationale": (
            "Rejected by (M1): at the fractional threshold 1/2 on a population of "
            "seven the real routine prepares the count 3, and the spec requires "
            "`some (normCount scaled)`, but the rival refuses and returns `none`. "
            "This is the case that would catch a repair that had made the result an "
            "unconstrained option instead of pinning the delivered value."
        ),
        "witness": _w_min(".quantity (1/2)", "7", "7/2"),
    },
    {
        "id": "weak-min-population-boundary-strict",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_IMPL, _R15_IMPL),
        "refinement": (
            "Compares the amount against the population size strictly (`<` for "
            "`≤`), so a threshold that equals the population exactly is refused "
            "instead of prepared. A faithful patch with that comparison rejects the "
            "legitimate 'as many neighbours as there are samples' request the real "
            "routine accepts → callers of that boundary break. Partial-domain rival "
            "on a single boundary point, agreeing with the frozen behaviour "
            "everywhere else."
        ),
        "rationale": (
            "Rejected by (M2): a count of 10 on a population of 10 is admitted by "
            "the real routine, which delivers the count 10 unchanged, and the spec "
            "requires `some minSamples`; the rival's strict comparison refuses it. "
            "The exact value where `≤` and `<` part company on the population leg — "
            "a point no other partiality witness visits."
        ),
        "witness": _w_min(".count 10", "10", "100"),
    },

    # ---- UNIQUENESS on resolveThresholds -------------------------------
    {
        "id": "weak-th-leading-unfloored",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _TH_IMPL, _T1_IMPL),
        "refinement": (
            "Takes the LEADING scaled amount with the pre-patch unreduced form "
            "while the trailing reduction is left correct. A faithful patch with "
            "this body leaves the leading threshold divisible, raising the "
            "downstream TypeError → would not resolve. Partial-domain rival: "
            "correct on the trailing component, wrong on the leading one."
        ),
        "rationale": (
            "Rejected by (T-ms): at a leading 1/2 on a population of seven with "
            "scaledLead=7/2 and a trailing count of 5 the leading component must be "
            "the count 3, but the rival returns the divisible 7/2. The trailing "
            "threshold is a count above one and inside the population, so the pair "
            "is delivered and only the leading clause fires. The scaled amounts "
            "(7/2, 35) are the ones the real routine hands over at that input, and "
            "its captured output there is the pair (3, 5)."
        ),
        "witness": _w_th(".quantity (1/2)", "some (.count 5)", "7", "7/2", "35"),
    },
    {
        "id": "weak-th-trailing-unfloored",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _TH_IMPL, _T2_IMPL),
        "refinement": (
            "The complementary half: the leading reduction is correct, the "
            "TRAILING one uses the pre-patch unreduced form, leaving the trailing "
            "threshold divisible downstream → would not resolve. Partial-domain "
            "rival: correct on the leading component, wrong on the trailing one."
        ),
        "rationale": (
            "Rejected by (T-mcs): at a leading count of 5 (kept) on a population of "
            "five with a trailing 1/2 and scaledTrail=5/2 the trailing component "
            "must be the count 2 — the real routine's captured output is the pair "
            "(5, 2) — but the rival returns the divisible 5/2. The leading branch "
            "differs from the previous rival's."
        ),
        "witness": _w_th(".count 5", "some (.quantity (1/2))", "5", "25", "5/2"),
    },
    {
        "id": "weak-th-wrong-unset-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _TH_IMPL, _T3_IMPL),
        "refinement": (
            "An unset trailing threshold defaults to a constant count of two "
            "instead of the already-reduced leading threshold. A faithful patch "
            "defaulting the second threshold to a fixed two rather than to the "
            "resolved first would use the wrong minimum cluster size whenever the "
            "caller omits it and the first threshold resolves above two → the "
            "fractional run diverges from the integer-parameter run and does not "
            "resolve."
        ),
        "rationale": (
            "Rejected by (T-none): at a leading count of 3 (kept) on a population "
            "of 31 with an UNSET trailing threshold the trailing component must "
            "default to the leading value 3 — the real routine's captured output is "
            "the pair (3, 3) — but the rival defaults to 2. This is the only "
            "delivered-pair point with an unset trailing threshold, exercising the "
            "default binder. On that path the real routine forms no trailing scaled "
            "amount at all — the defaulted value already exceeds one, so the "
            "trailing guard is false and the amount is unconsumed on either side; "
            "it is supplied as 93 purely to saturate the binder."
        ),
        "witness": _w_th(".count 3", "none", "31", "93", "93"),
    },
    {
        "id": "weak-th-dropped-trailing-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _TH_IMPL, _T4_IMPL),
        "refinement": (
            "Reduces the trailing scaled amount UNCONDITIONALLY (dropping the "
            "guard), so a present threshold whose amount exceeds one is replaced "
            "by the count derived from that amount instead of kept unchanged. A "
            "faithful patch that did so to an already-absolute cluster size would "
            "inflate it far beyond the caller's intent → does not resolve."
        ),
        "rationale": (
            "Rejected by (T-guard): at a leading count of 5 (kept) on a population "
            "of 31 with a trailing count of 5 (which must be kept) the trailing "
            "component must stay 5 — the real routine's captured output is the pair "
            "(5, 5) — but the rival reduces the trailing amount anyway and returns "
            "155. This is the point that exercises the keep-unchanged guard on the "
            "trailing threshold."
        ),
        "witness": _w_th(".count 5", "some (.count 5)", "31", "155", "155"),
    },
    {
        "id": "weak-th-dropped-leading-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _TH_IMPL, _T5_IMPL),
        "refinement": (
            "Reduces the LEADING scaled amount UNCONDITIONALLY in the "
            "two-threshold preparation, so a leading threshold already supplied as "
            "an absolute count is replaced by the count derived from that amount. "
            "A faithful patch would inflate an absolute count by a factor of the "
            "population size and then also propagate that inflated value as the "
            "unset trailing default, changing the counts on the INTEGER-parameter "
            "runs the failing test compares against — so it would not resolve. "
            "Complement of T1–T4, which all leave the leading keep-unchanged "
            "branch alone."
        ),
        "rationale": (
            "Rejected by (T-msg): at a leading count of 5 (which must be returned "
            "unchanged) on a population of 31 with a trailing count of 7 (kept) and "
            "scaledLead=155, the rival's leading component is 155 where the real "
            "routine's captured output is the pair (5, 7). This is the only "
            "resolveThresholds witness that pins the leading component on the "
            "keep-unchanged branch, and hence the only one that attests (T-msg): "
            "against a copy of the spec with exactly that clause weakened away, "
            "this witness stops holding while all four T1–T4 witnesses are "
            "unaffected."
        ),
        "witness": _w_th(".count 5", "some (.count 7)", "31", "155", "217"),
    },
    {
        "id": "weak-th-leading-form-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _TH_IMPL, _T6_IMPL),
        "refinement": (
            "Every magnitude matches the frozen behaviour; the LEADING reduction "
            "delivers a divisible amount while the trailing one is a proper count. "
            "A faithful patch of this shape still hands the population-counting "
            "consumer a divisible leading threshold on the reported input → the "
            "failing test does not pass. Partial-domain on the component axis."
        ),
        "rationale": (
            "Rejected by (T-form) on the leading component: at a leading 1/2 on "
            "seven with scaledLead=7/2 and a trailing count of 5, the leading "
            "magnitude is right (3) and only the form is wrong. Together with T7 "
            "this pins the form obligation on BOTH components — a clause that "
            "constrained only one of them would leave the other free, and each of "
            "these two rivals is invisible to the witness of the other."
        ),
        "witness": _w_th(".quantity (1/2)", "some (.count 5)", "7", "7/2", "35"),
    },
    {
        "id": "weak-th-trailing-form-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _TH_IMPL, _T7_IMPL),
        "refinement": (
            "The complementary half of T6: the leading reduction is a proper "
            "count, and the TRAILING one delivers the right magnitude in divisible "
            "form. A faithful patch of this shape hands the clustering routine a "
            "divisible trailing threshold → would not resolve."
        ),
        "rationale": (
            "Rejected by (T-form) on the trailing component: at a leading count of "
            "5 (kept) on a population of five with a trailing 1/2 and "
            "scaledTrail=5/2 the trailing magnitude is right (2) and only the form "
            "is wrong. Complements T6 so neither component's form is left "
            "unattested."
        ),
        "witness": _w_th(".count 5", "some (.quantity (1/2))", "5", "25", "5/2"),
    },

    # ---- UNIQUENESS on the pair routine's PARTIALITY --------------------
    {
        "id": "weak-th-leading-check-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _TH_IMPL, _T8_IMPL),
        "refinement": (
            "Checks the leading threshold's range and never checks the trailing "
            "one, so a pair whose trailing threshold is out of range is delivered "
            "instead of refused. This is the sharpest rival in the battery, because "
            "it is correct on every input whose trailing threshold happens to be in "
            "range — which is nearly all of them, including everything a uniform "
            "fuzz over the two thresholds visits — and wrong precisely on the class "
            "where the DEFAULTED trailing threshold, being the clamped-up leading "
            "one, leaves the range the leading input was inside. A faithful patch "
            "of this shape silently accepts a trailing threshold larger than the "
            "population and hands it to the clustering routine, where the callers "
            "that depend on the refusal stop getting it."
        ),
        "rationale": (
            "Rejected by (T-r1): on a population of ONE with a fractional leading "
            "threshold of 1/2 and an UNSET trailing threshold, the leading "
            "threshold is admitted (positive, at most one, within the population) "
            "and reduces to the clamped count 2; the trailing threshold defaults to "
            "that 2, which EXCEEDS the population of one, so the check refuses it "
            "and the result must be `none`. Confirmed against the real routine at "
            "that input, which refuses rather than delivering a pair. The rival "
            "delivers the pair (2, 2). This is the point where the trailing check's "
            "subject is a value the routine itself computed, so no leading-side "
            "check can stand in for it."
        ),
        "witness": _w_th(".quantity (1/2)", "none", "1", "1/2", "1/2"),
    },
    {
        "id": "weak-th-ungrounded-trailing-check",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _TH_IMPL, _T9_IMPL),
        "refinement": (
            "Does apply a trailing range check, but to the WRONG SUBJECT: it tests "
            "the trailing threshold defaulted from the UNREDUCED leading input "
            "rather than from the reduced one — deriving the decision from the "
            "arguments it was handed instead of from the value the routine "
            "computed. Indistinguishable from correct whenever a trailing threshold "
            "is supplied, and whenever the raw and reduced leading thresholds agree "
            "on admissibility; wrong exactly where the reduction moves the "
            "defaulted value out of range. A faithful patch of this shape passes "
            "every test whose trailing threshold is explicit and still accepts the "
            "out-of-range defaulted one."
        ),
        "rationale": (
            "Rejected by (T-r1): at the same point as the leading-check-only rival "
            "— population one, leading 1/2, unset trailing — the raw leading input "
            "1/2 IS in range, so this rival's check passes and it delivers the pair "
            "(2, 2), while the subject the specification names is `mcs0` = the "
            "defaulted, already-reduced count 2, which exceeds the population, so "
            "the result must be `none` (the real routine refuses there). The two "
            "rivals share a witness point deliberately: what separates them is "
            "whether a check exists at all versus whether it consults the computed "
            "value, and the second is the one an echo-shaped implementation gets "
            "wrong."
        ),
        "witness": _w_th(".quantity (1/2)", "none", "1", "1/2", "1/2"),
    },
    {
        "id": "weak-th-trailing-check-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _TH_IMPL, _T10_IMPL),
        "refinement": (
            "The complement of the leading-check-only rival: the leading threshold "
            "is never checked, so a leading threshold the check refuses reaches the "
            "reduction and a pair is delivered. A faithful patch of this shape "
            "accepts a malformed leading threshold — the argument the routine "
            "validates FIRST — and the refusal callers rely on disappears. Correct "
            "on every input whose leading threshold is in range."
        ),
        "rationale": (
            "Rejected by (T-r0): a leading threshold of 5/2 on a population of ten "
            "is neither whole nor at most one, so the check refuses it and the whole "
            "pair must be `none` — confirmed against the real routine, which refuses "
            "there — but the rival skips the leading check, keeps 5/2 (its amount "
            "exceeds one), takes the supplied trailing count of 3 and delivers a "
            "pair. Pins that the leading refusal clause is not idle, which the "
            "trailing-side rivals leave unattested."
        ),
        "witness": _w_th(".quantity (5/2)", "some (.count 3)", "10", "25", "30"),
    },
]


# ===========================================================================
# AXIOM_TESTS
# ===========================================================================
# Dropped: the axiom lane is G-AX's job and this bundle ships no consumed axiom.
# Both the reduction (`normCount` spelled out as `.count (max 2 ⌊scaled⌋)`) and
# the range check (`Threshold.admits` spelled out as its three conditions) are
# modeled DEEPLY rather than over an opaque callee, so there is no `_prop` for
# the PBT axiom lane to probe. The range check HAS to be modeled deeply rather
# than assumed: in the pair routine its subject is a value the specification
# itself computes, so there is no incoming argument whose contract could stand in
# for it. The population-scaling step that produces `scaled` is not axiomatized
# either: it is outside the model boundary, and its result is an input rather
# than a consumed callee return.
AXIOM_TESTS = []
