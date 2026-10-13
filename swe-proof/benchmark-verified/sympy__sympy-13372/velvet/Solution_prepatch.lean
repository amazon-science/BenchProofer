import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts and no A-reference deep model. The classification
--  of each component — exact zero / concrete numeric quantity / still-symbolic —
--  and the converted numeric value of a numeric component are the observable
--  results of UNCHANGED callees consulted before this step; they are abstracted
--  as read-only inputs (a status tag and a value handle), not re-derived or
--  pinned to any value here. The operation under specification — assembling the
--  reported record, or signalling that no numeric result is available — is
--  modeled deeply below as the do block. Nothing is borrowed from an outside
--  contract, so there is no axiom to validate (meta.json G-AX skip).)
-- axioms-end

-- pure-start
/- The three mutually-exclusive situations a single component (real or
   imaginary) can be in when a numeric evaluation is attempted on it:

     * `exactZero`  — the component is an exact zero;
     * `numeric`    — the component is a concrete numeric quantity;
     * `nonNumeric` — the component is neither (it still carries unevaluated
                      structure), so it cannot be turned into a number.

   A first-class tag with decidable equality: the behavior under specification
   turns on WHICH situation each component is in. -/
inductive PartStatus where
  | exactZero
  | numeric
  | nonNumeric
  deriving DecidableEq, Inhabited

/- A component handed to the numeric-evaluation step: its situation tag together
   with the converted numeric value it would report (a value handle meaningful
   only when the situation is `numeric`; for the other situations it is unused). -/
structure Part where
  status : PartStatus
  value  : Int
  deriving Inhabited

/- The record a successful numeric-evaluation step reports: for each component,
   the reported value and the reported precision. An absent field is `none`. -/
structure EvalResult where
  realValue : Option Int
  imagValue : Option Int
  realPrec  : Option Int
  imagPrec  : Option Int
  deriving Inhabited

/- The desired result of the numeric-evaluation step, as a total function of the
   two components and the target precision — the deep model of the operation:

   - if EITHER component is non-numeric (neither an exact zero nor a concrete
     numeric quantity), no numeric result can be reported: the result is the
     absent marker `none` (signalling that numeric evaluation is unavailable, so
     a caller may fall back). No partial or fabricated record is reported;
   - otherwise both components are reportable, and the assembled record carries,
     per component, an absent value+precision when it is an exact zero, and its
     converted value + the target precision when it is numeric.

   Written with a term-level `if`/`else if` ladder (pure region; the impl do
   block mirrors it with nested `if`/`else`). -/
def evalSpec (realPart imagPart : Part) (prec : Int) : Option EvalResult :=
  if realPart.status = PartStatus.nonNumeric then none
  else if imagPart.status = PartStatus.nonNumeric then none
  else some {
    realValue := if realPart.status = PartStatus.exactZero then none else some realPart.value,
    imagValue := if imagPart.status = PartStatus.exactZero then none else some imagPart.value,
    realPrec  := if realPart.status = PartStatus.exactZero then none else some prec,
    imagPrec  := if imagPart.status = PartStatus.exactZero then none else some prec }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A numeric-evaluation step reports the numeric value of an expression that has
   been split into a real component and an imaginary component, each to be
   reported to a target precision. Each component is in exactly one of three
   situations: it is an exact zero, it is a concrete numeric quantity, or it is
   neither (it still carries unevaluated/symbolic structure).

   The reported record carries, per component, a reported value and a reported
   precision:
     * an exact-zero component contributes an absent value and an absent
       precision;
     * a numeric component contributes its converted numeric value and the
       target precision.

   When EITHER component is neither an exact zero nor a concrete numeric
   quantity, the step cannot report a numeric result at all: it yields the
   absent result `none`, signalling that numeric evaluation is unavailable for
   this expression (so a caller may fall back). It MUST NOT report a partial or
   fabricated record in that case.

   `realPart`, `imagPart`, and `prec` are read-only (not `mut`); the step builds
   a fresh result and mutates nothing (directive 5). -/
method numericComplexResult (realPart : Part) (imagPart : Part) (prec : Int)
    return (out : Option EvalResult)
  ensures out = evalSpec realPart imagPart prec
  ensures (realPart.status = PartStatus.nonNumeric ∨ imagPart.status = PartStatus.nonNumeric)
            → out = none
  ensures realPart.status ≠ PartStatus.nonNumeric → imagPart.status ≠ PartStatus.nonNumeric
            → ∃ r, out = some r
  do
    -- impl-start
    -- Pre-image skeleton: a component is treated as reportable UNLESS it is an
    -- exact zero — the non-numeric situation is never branched on, so a
    -- non-numeric component falls through and the record is assembled anyway,
    -- with a fabricated value+precision for it (the model of "reprec/imprec
    -- referenced when they were never set for a non-numeric part"). No `none`
    -- is ever signalled. This MUST fail the discriminating postcondition
    -- (non-numeric ⇒ none).
    return some {
      realValue := if realPart.status = PartStatus.exactZero then none else some realPart.value,
      imagValue := if imagPart.status = PartStatus.exactZero then none else some imagPart.value,
      realPrec  := if realPart.status = PartStatus.exactZero then none else some prec,
      imagPrec  := if imagPart.status = PartStatus.exactZero then none else some prec }
    -- impl-end

prove_correct numericComplexResult by
  loom_solve <;> simp_all [evalSpec]
