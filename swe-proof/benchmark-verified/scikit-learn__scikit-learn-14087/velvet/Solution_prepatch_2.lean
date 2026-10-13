import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two decisions modeled here are pure control-flow
--  choices over values that have ALREADY been produced by surrounding routines:
--  the two candidate coefficient vectors (one per coefficient-array layout), the
--  averaged auxiliary mixing value, and the two strategy/mode flags are all
--  taken as FREE INPUTS. The routine itself calls no further repo function whose
--  contract must be assumed, so there is no unchanged callee to axiomatize and
--  nothing for G-AX to falsify. See mapping.md §3 and refinement.md, all rows
--  R or I.)
-- axioms-end

-- pure-start
/- A fitted coefficient vector, identified abstractly. Only WHICH candidate
   vector is selected is observed here, never the concrete numbers it contains,
   so an exact-rational list is a faithful, decidable carrier (DECISIONS float
   note: model order-only or selection-only quantities with `Rat`, not
   `Float`). -/
abbrev Coef := List Rat

/- The selected coefficient vector for one class, given the effective strategy.
   The surrounding routine has prepared two candidates from the stored
   cross-validation coefficients — one read out under the per-class layout
   (`coefByPerClass`) and one under the joint layout (`coefByJoint`). The vector
   that is meaningful is the one matching the strategy actually in effect: the
   per-class candidate when the effective strategy is the per-class one, the
   joint candidate otherwise. The decision MUST consult the effective strategy,
   not whatever was originally requested (`perClassEffective`, not
   `perClassRequested`) — the two can disagree, and only the effective one names
   the layout the stored coefficients actually have. -/
def chooseCoef (perClassEffective : Bool) (coefByPerClass coefByJoint : Coef) : Coef :=
  if perClassEffective then coefByPerClass else coefByJoint

/- The recorded auxiliary mixing value for one class. An auxiliary mixing value
   exists only when the auxiliary regularization mode is in effect; in that mode
   the surrounding routine has already averaged it (`auxValue`). When the mode is
   not in effect there is no auxiliary value to record and the slot is left empty
   (`none`) — it must NOT be synthesized from data that does not apply. -/
def chooseAux (auxActive : Bool) (auxValue : Rat) : Option Rat :=
  if auxActive then some auxValue else none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Record one class's results in the no-refit aggregation branch.

   The cross-validation aggregation has already produced, for this class, two
   candidate coefficient vectors (`coefByPerClass`, `coefByJoint`) and — when the
   auxiliary regularization mode applies — an averaged auxiliary mixing value
   (`auxValue`). This routine commits the two outputs the branch records:

     • the coefficient vector, chosen according to the strategy actually IN
       EFFECT for this fit (`perClassEffective`); the strategy as originally
       requested (`perClassRequested`) does not determine the layout of the
       stored coefficients and must not drive the choice;
     • the auxiliary mixing value, recorded only when the auxiliary mode is in
       effect (`auxActive`), and left empty (`none`) otherwise.

   All inputs are read-only (none `mut`): the routine reads the prepared values
   and flags and returns the pair it records, mutating nothing handed to it
   (directive 5). -/
method recordClassResult
    (perClassEffective : Bool) (perClassRequested : Bool)
    (coefByPerClass : Coef) (coefByJoint : Coef)
    (auxActive : Bool) (auxValue : Rat)
    return (out : Coef × Option Rat)
  ensures out.1 = chooseCoef perClassEffective coefByPerClass coefByJoint
  ensures out.2 = chooseAux auxActive auxValue
  do
    -- impl-start
    -- Pre-image skeleton (behavior 2): the auxiliary mixing value is recorded
    -- UNCONDITIONALLY, even when the auxiliary mode is not in effect — exactly
    -- the case in which no auxiliary value applies and the surrounding table it
    -- would be read from is degenerate. The frozen spec requires the slot be
    -- left empty (`none`) when the mode is off, so prove_correct MUST fail.
    let coef : Coef := if perClassEffective then coefByPerClass else coefByJoint
    let aux : Option Rat := some auxValue
    return (coef, aux)
    -- impl-end

prove_correct recordClassResult by
  loom_solve <;> simp only [chooseCoef, chooseAux]
