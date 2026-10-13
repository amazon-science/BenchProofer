import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The one unchanged callee this slice relies on — the
   shared reduction over a common dimension — is modeled DEEPLY in the `pure`
   region (`reduceDot`, with its two carrier-dependent legs) and validated ==
   the real callee by G-AX (an A-reference, mapping.md §3), so it carries no
   module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The non-null mask of a data array: at each position, whether the datum is
   present. Modeled element-wise; a present datum is `some _`, a missing one is
   `none`, so only the presence pattern is observed. -/
def maskOf (da : List (Option Int)) : List Bool := da.map Option.isSome

/- The arithmetic reduction of a mask against weights over the shared position
   axis: the sum of the weights at the positions whose datum is present. This is
   the numeric contraction. Front-recursive over the aligned position lists. -/
def arithDot : List Bool → List Int → Int
  | (m :: ms), (w :: ws) => (if m then w else 0) + arithDot ms ws
  | _, _ => 0

/- The logical reduction of a mask against weights over the shared position
   axis: whether ANY present position carries a nonzero weight, as `1`/`0`. This
   is the carrier collapsing to a truth value rather than a count. -/
def anyMasked : List Bool → List Int → Int
  | (m :: ms), (w :: ws) => if m && decide (w ≠ 0) then 1 else anyMasked ms ws
  | _, _ => 0

/- The shared reduction callee, modeled deeply (A-reference, mapping.md §3.1).
   It is carrier-polymorphic: handed a logical-carrier operand it collapses to
   the truth-valued reduction (`anyMasked`); otherwise it computes the numeric
   contraction (`arithDot`). The flag records which carrier the weights present.
   Validated `reduceDot == the real reduction` (both legs) by G-AX. -/
def reduceDot (mask : List Bool) (weights : List Int) : Bool → Int
  | true  => anyMasked mask weights
  | false => arithDot mask weights

@[grind] lemma reduceDot_false (m : List Bool) (w : List Int) :
    reduceDot m w false = arithDot m w := rfl
@[grind] lemma reduceDot_true (m : List Bool) (w : List Int) :
    reduceDot m w true = anyMasked m w := rfl

/- The desired sum of weights: the arithmetic total of the weights at the
   present data positions, with a zero total reported as absent (a zero total
   carries no usable information and must not propagate as a valid weight). The
   total is the NUMERIC contraction regardless of how the weights are carried —
   the result counts the contributing weights, it does not merely detect them. -/
def sumOfWeightsSpec (da : List (Option Int)) (weights : List Int) : Option Int :=
  if arithDot (maskOf da) weights = 0 then none
  else some (arithDot (maskOf da) weights)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Sum the weights, accounting for missing data values. `da` is the data array
   (present/absent per position); `weights` the aligned weights; the flag records
   whether the weights are carried as a logical array. The result is the
   arithmetic total of the weights at present positions, with a zero total
   reported as absent. -/
method sumOfWeights (da : List (Option Int)) (weights : List Int)
    (weightsAreLogical : Bool) return (out : Option Int)
  ensures out = sumOfWeightsSpec da weights
  do
    -- impl-start
    -- Pre-image skeleton: the weights are reduced through their native carrier
    -- with no special handling, so logical-carrier weights collapse to a
    -- truth-valued reduction (anyMasked) rather than the numeric total. The
    -- frozen spec requires the arithmetic total, so prove_correct MUST fail.
    let mask := maskOf da
    let s : Int := reduceDot mask weights weightsAreLogical
    let out := if s = 0 then none else some s
    return out
    -- impl-end

prove_correct sumOfWeights by
  loom_solve
  cases weightsAreLogical <;> simp_all [reduceDot, sumOfWeightsSpec]
