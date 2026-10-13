import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees. A size-validation guard runs before the conditioning
   step and only restricts the input domain; its guarantee is captured as a
   `require` precondition rather than an axiom, so there is no dead/over-claimed
   axiom (SPEC_GUIDE §0 directive 7). -/
-- axioms-end

-- pure-start
/- A sizing parameter may be given in two forms: as an absolute count (a value
   strictly greater than one) or as a fraction of the population (a value in the
   half-open interval (0, 1]).  When it is given as a fraction it must be turned
   into a concrete absolute count: take the value it scales to against the
   population, reduce that to a whole number by discarding any fractional part,
   and never let the result fall below two.  When the parameter is already an
   absolute count it is used as-is.

   The scaling is performed in the ambient inexact numeric type, so the scaled
   value the conditioning step actually receives is only guaranteed to agree with
   the ideal product to within that type's relative precision — one part in
   2^53.  It is therefore an INPUT to the routines below (`scaled`) rather than
   something recomputed here, and the contracts pin the reduction to a whole
   count *of the value that was actually produced*.  `scaledFromPopulation`
   states exactly that admissible relationship; a routine may not invent a
   different scaled value.

   Modeled with `Rat`: once the scaled value is in hand the remaining behavior is
   an exact order/integer relation (discard the fractional part, clamp), and on a
   non-negative value discarding the fractional part coincides with the floor, so
   `Rat.floor` models it exactly (mapping.md §2). -/
def scaledFromPopulation (scaled value : Rat) (population : Nat) : Prop :=
  value * (population : Rat) - value * (population : Rat) / 9007199254740992 ≤ scaled ∧
    scaled ≤ value * (population : Rat) + value * (population : Rat) / 9007199254740992

def asAbsoluteCount (value scaled : Rat) : Rat :=
  if value ≤ 1 then
    (((max 2 (Rat.floor scaled)) : Int) : Rat)
  else
    value

structure SizePair where
  primary   : Rat
  secondary : Rat
deriving DecidableEq

/- The secondary parameter is optional: when it is not supplied it defaults to
   the already-conditioned primary value. -/
def pairedSecondarySource
    (value scaledPrimary secondaryValue : Rat) (secondaryGiven : Bool) : Rat :=
  if secondaryGiven then secondaryValue else asAbsoluteCount value scaledPrimary

/- The conditioned pair: condition the primary; the secondary is the supplied
   value if present, otherwise the conditioned primary, and is then conditioned
   in turn. -/
def resolvedPairedSizes
    (value secondaryValue scaledPrimary scaledSecondary : Rat)
    (secondaryGiven : Bool) : SizePair :=
  { primary := asAbsoluteCount value scaledPrimary,
    secondary :=
      asAbsoluteCount
        (pairedSecondarySource value scaledPrimary secondaryValue secondaryGiven)
        scaledSecondary }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- First routine: a single sizing parameter is conditioned against the
   population before it is consumed downstream.  The output must be the absolute
   count `asAbsoluteCount` describes — in particular, when the input was a
   fraction the output is a *whole* count (the scaled value with its fractional
   part discarded, floored at two), never a leftover fractional value. -/
method conditionSizeParameter
    (value : Rat) (scaled : Rat) (population : Nat) return (out : Rat)
  require 0 < value
  require 1 ≤ population
  require scaledFromPopulation scaled value population
  ensures out = asAbsoluteCount value scaled
  do
    -- impl-start
    -- Pre-image skeleton: the scaled value is clamped at two but its fractional
    -- part is NEVER discarded, so a fractional input leaves a non-integral
    -- residue. The frozen spec demands the whole count `asAbsoluteCount`, so
    -- prove_correct MUST fail.
    let mut size : Rat := value
    if value ≤ 1 then
      size := max 2 scaled
    return size
    -- impl-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Second routine: two sizing parameters are conditioned.  The primary one is
   conditioned first.  The secondary one is optional: when it is not supplied it
   defaults to the (already conditioned) primary value, and either way it is
   then conditioned against the population in the same manner.  Both outputs must
   be the absolute counts `asAbsoluteCount` describes. -/
method resolvePairedSizes
    (value : Rat) (secondaryValue : Rat) (scaledPrimary : Rat) (scaledSecondary : Rat)
    (secondaryGiven : Bool) (population : Nat) return (out : SizePair)
  require 0 < value
  require 0 < secondaryValue
  require 1 ≤ population
  require scaledFromPopulation scaledPrimary value population
  require scaledFromPopulation scaledSecondary
    (pairedSecondarySource value scaledPrimary secondaryValue secondaryGiven) population
  ensures out =
    resolvedPairedSizes value secondaryValue scaledPrimary scaledSecondary secondaryGiven
  do
    -- impl-start
    let mut primary : Rat := value
    if value ≤ 1 then
      primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
    let mut secondary : Rat := primary
    if secondaryGiven then
      secondary := secondaryValue
    if secondary ≤ 1 then
      secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
    return { primary := primary, secondary := secondary }
    -- impl-end

prove_correct conditionSizeParameter by
  loom_solve <;> simp_all [asAbsoluteCount]

prove_correct resolvePairedSizes by
  loom_solve <;> simp_all [resolvedPairedSizes, pairedSecondarySource, asAbsoluteCount]
