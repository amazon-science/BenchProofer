import Mathlib
-- imports-end

/-!
A neighborhood-size threshold may be supplied in two interchangeable forms: as an
absolute whole-number count of population members greater than one, or as a
fraction of the population (an amount at most one). The consumer that receives
the prepared threshold counts population members: it admits an integer count and
rejects a divisible amount, even one whose magnitude happens to be whole. Which
of the two forms a threshold is carried in is therefore itself observable, and
not merely the amount that threshold describes.

Preparing a threshold is a PARTIAL operation. Before a threshold is used it must
clear a range check, and a threshold that fails it is refused outright rather
than prepared: the routine delivers no prepared threshold at all. The check
admits a threshold whose amount is positive, is either a whole amount or at most
one, and does not exceed the population size.

The behavior modeled here is the reduction of an admitted threshold to an
absolute count. Scaling a fractional threshold by the population size is an
ordinary arithmetic step of the surrounding routine and is not part of the
behavior modeled here, so the already-scaled amount enters as an input, carried
exactly; every scaled amount the surrounding routine can produce is an exact
rational. What is modeled is the reduction of that scaled amount to an absolute
count: take the whole-number part of the scaled amount, with the count never
allowed to fall below two, and deliver the outcome in count form. A threshold
whose amount is already greater than one is used unchanged, in whichever form it
arrived in.

Two preparation routines are modeled. The first prepares a single threshold. The
second prepares a pair of thresholds, and the range check applies to each of them
in turn: the leading threshold is checked and then reduced as above; an unset
trailing threshold defaults to the (already reduced) leading one in whatever form
that carries; the trailing threshold — defaulted or supplied — is then itself
checked against the population size, and a trailing threshold whose amount is at
most one is reduced the same way from its own scaled amount. Because the default
supplies a value the routine has just computed, the trailing check can refuse a
pair whose leading threshold the same check admitted.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The range check
-- that guards these routines does not transform the value (in particular it does
-- not change which form carries it); it only decides whether the threshold is
-- prepared at all, and that decision is modeled deeply below rather than assumed
-- as a contract — it has to be, because in the pair routine the check is applied
-- to a value this specification itself computes. The scaling of a fractional
-- threshold by the population size is likewise not consumed as a contract: it
-- lies outside the modeled boundary and its result enters as the `scaled` input,
-- exactly. The reduction to an absolute count — the behavior under specification
-- — is modeled deeply below. Hence no `opaque`/`axiom`.
-- axioms-end

-- pure-start
/-- A neighborhood-size threshold as the surrounding routine carries it: either
an absolute whole-number `count` of population members, or a divisible `quantity`
that is not a count. The two are distinct even when they describe the same
amount, because the consumer that counts population members admits the former and
rejects the latter. -/
inductive Threshold where
  | count (k : ℤ)
  | quantity (q : ℚ)
  deriving DecidableEq

/-- The amount a threshold describes, disregarding which form carries it. -/
def Threshold.amount : Threshold → ℚ
  | .count k => (k : ℚ)
  | .quantity q => q

/-- The range check a threshold must clear before it is prepared: its amount is
positive, it is either a whole amount or an amount at most one, and it does not
exceed the population size. A threshold failing this is refused, and no prepared
threshold is delivered. -/
def Threshold.admits (t : Threshold) (populationSize : ℕ) : Prop :=
  0 < t.amount ∧ (t.amount.den = 1 ∨ t.amount ≤ 1) ∧
    t.amount ≤ (populationSize : ℚ)

instance (t : Threshold) (populationSize : ℕ) :
    Decidable (t.admits populationSize) := by
  unfold Threshold.admits; infer_instance

/-- Reduce a population-scaled amount `scaled` to an absolute count: take the
whole-number part of the amount, never letting the count fall below two, and
deliver it in count form — an absolute count of population members, not a
divisible quantity. -/
def normCount (scaled : ℚ) : Threshold := .count (max 2 ⌊scaled⌋)
-- pure-end

-- post-conditions-start
/-- Single-threshold preparation. A threshold that fails the range check is
refused and nothing is delivered. An admitted threshold whose amount is at most
one is a fraction, and the delivered result is the absolute count obtained from
its scaled amount via `normCount`; an admitted threshold whose amount is greater
than one is already an absolute count and is delivered exactly as it arrived, in
the same form. The result is pinned to the inputs on every branch, so nothing is
left free — in particular a fractional input must yield the count form, never a
divisible quantity of the same magnitude, and a refusal is pinned to exactly the
thresholds the check rejects. -/
def problem_spec_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ)
    (result : Option Threshold) : Prop :=
  (¬ minSamples.admits populationSize → result = none) ∧
  (minSamples.admits populationSize →
    (minSamples.amount ≤ 1 → result = some (normCount scaled)) ∧
    (1 < minSamples.amount → result = some minSamples))

/-- Pair-threshold preparation. The leading threshold faces the range check
first, and a leading threshold the check rejects refuses the whole pair. An
admitted leading threshold is reduced as in `resolveMinSamples`, from the leading
scaled amount. An unset trailing threshold (`none`) then defaults to that already
reduced leading threshold, carried in whatever form it has; a present trailing
threshold uses its own value. That trailing threshold — defaulted or supplied —
faces the range check in turn, and a rejection there refuses the pair as well,
even though the leading threshold was admitted. Otherwise the trailing threshold
is itself reduced: an amount at most one means a fraction, whose absolute count
comes from the trailing scaled amount; an amount greater than one is kept exactly
as it arrived. Both components of a delivered pair are pinned to the inputs, in
form as well as in amount, and each refusal is pinned to exactly the inputs the
check rejects. -/
def problem_spec_resolveThresholds
    (minSamples : Threshold) (trailingThreshold : Option Threshold)
    (populationSize : ℕ) (scaledLead : ℚ) (scaledTrail : ℚ)
    (result : Option (Threshold × Threshold)) : Prop :=
  let ms : Threshold :=
    if minSamples.amount ≤ 1 then normCount scaledLead else minSamples
  let mcs0 : Threshold := trailingThreshold.getD ms
  let mcs : Threshold :=
    if mcs0.amount ≤ 1 then normCount scaledTrail else mcs0
  (¬ minSamples.admits populationSize → result = none) ∧
  (minSamples.admits populationSize →
    (¬ mcs0.admits populationSize → result = none) ∧
    (mcs0.admits populationSize → result = some (ms, mcs)))
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy): the fractional branch clamps the scaled amount against the
-- floor of two but does NOT reduce it to a whole-number count. Whichever operand
-- of that clamp is the larger is what it delivers, so above the floor the result
-- stays the divisible scaled amount rather than an absolute count.
def implementation_resolveMinSamples
    (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ) :
    Option Threshold := Id.run do
  if minSamples.admits populationSize then
    let mut ms := minSamples
    if ms.amount ≤ 1 then
      ms := if scaled ≤ 2 then .count 2 else .quantity scaled
    return some ms
  else
    return none

def implementation_resolveThresholds
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
    return none
-- impl-end

-- proof-start
theorem correct_resolveMinSamples :
    ∀ (minSamples : Threshold) (populationSize : ℕ) (scaled : ℚ),
      problem_spec_resolveMinSamples minSamples populationSize scaled
        (implementation_resolveMinSamples minSamples populationSize scaled) := by
  intro minSamples populationSize scaled
  unfold problem_spec_resolveMinSamples implementation_resolveMinSamples
  simp only [Id.run, bind, pure]
  split_ifs with hA hle
  · exact ⟨fun h => absurd hA h, fun _ => ⟨fun _ => rfl, fun h => absurd hle (not_le.mpr h)⟩⟩
  · exact ⟨fun h => absurd hA h, fun _ => ⟨fun h => absurd h hle, fun _ => rfl⟩⟩
  · exact ⟨fun _ => rfl, fun h => absurd h hA⟩

theorem correct_resolveThresholds :
    ∀ (minSamples : Threshold) (trailingThreshold : Option Threshold)
      (populationSize : ℕ) (scaledLead : ℚ) (scaledTrail : ℚ),
      problem_spec_resolveThresholds minSamples trailingThreshold populationSize
        scaledLead scaledTrail
        (implementation_resolveThresholds minSamples trailingThreshold
          populationSize scaledLead scaledTrail) := by
  intro minSamples trailingThreshold populationSize scaledLead scaledTrail
  unfold problem_spec_resolveThresholds implementation_resolveThresholds
  simp only [Id.run, bind, pure]
  split_ifs <;>
    simp_all
-- proof-end
