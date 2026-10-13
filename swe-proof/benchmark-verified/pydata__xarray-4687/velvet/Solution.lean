import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The elementwise value-selection performed here is an
--  unchanged library primitive, modeled DEEPLY in the `pure` region as the
--  front-recursive `whereSelect` (an A-reference, validated == the real numeric
--  primitive by axiom_check.py / G-AX), NOT consumed as an axiom. The decision
--  that governs whether the source attribute mapping is carried onto the result
--  is a closed function of two booleans (the per-call choice and the ambient
--  default), modeled directly below; nothing is consumed as an axiom. The
--  ambient default is the result of an unchanged option query, modeled as the
--  boolean input `globalKeepDefault` (an R refinement; cross-language soundness
--  is checked by conformance_check.py / G-CONF).)
-- axioms-end

-- pure-start
/- The elementwise selection: at each cell, take the value from the first
   operand list where the condition holds, otherwise from the second. Defined
   front-recursively over the three aligned cell lists (one unfold per cell).
   This is the unchanged primitive the routine delegates value computation to. -/
def whereSelect : List Bool → List Int → List Int → List Int
  | [],      _,       _       => []
  | _,       [],      _       => []
  | _,       _,       []      => []
  | c :: cs, a :: xs, b :: ys => (if c then a else b) :: whereSelect cs xs ys

@[grind] lemma whereSelect_nil_l (x y : List Int) : whereSelect [] x y = [] := by
  simp [whereSelect]
@[grind] lemma whereSelect_cons (c : Bool) (cs : List Bool)
    (a : Int) (xs : List Int) (b : Int) (ys : List Int) :
    whereSelect (c :: cs) (a :: xs) (b :: ys)
      = (if c then a else b) :: whereSelect cs xs ys := by
  simp [whereSelect]

/- The result carrier: the selected cell values together with the attribute
   mapping the result exposes (an association list; an empty list means no
   attributes). Only the touched fields of the real result object are modeled
   (mapping.md §2). -/
structure WhereResult where
  values : List Int
  attrs  : List (String × String)
deriving Inhabited, DecidableEq

/- The resolved choice of whether the result keeps the source attribute mapping.
   When the call states an explicit choice, that choice stands; when it states
   none, the ambient default applies. -/
@[grind] def keepResolved (choice : Option Bool) (default : Bool) : Bool :=
  choice.getD default
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine two operands cell-by-cell under a boolean condition, returning, for
   each cell, the first operand's value where the condition holds and the second
   operand's value elsewhere, and choosing whether the result carries over the
   attribute mapping of the first selected-from operand.

   Whether the attribute mapping is carried over is decided by the resolved
   choice: an explicit per-call choice stands as given; absent one, an ambient
   default applies. When the resolved choice is to keep, the result exposes the
   attribute mapping of the first selected-from operand (`xAttrs`); otherwise the
   result exposes no attributes (the empty mapping). The cell values do not
   depend on that choice.

   Every input is read-only (none `mut`): the routine reads the condition, the
   two operands, the source attribute mapping and the two flags, and constructs a
   fresh result; it mutates none of them (directive 5). `cond`, `x`, `y` are
   aligned cell lists (equal length). -/
method selectByCondition
    (cond : List Bool) (x : List Int) (y : List Int)
    (xAttrs : List (String × String))
    (keepAttributes : Option Bool) (globalKeepDefault : Bool)
    return (out : WhereResult)
  require cond.length = x.length
  require x.length = y.length
  ensures out.values = whereSelect cond x y
  ensures out.attrs = (if keepResolved keepAttributes globalKeepDefault
                       then xAttrs else [])
  do
    -- impl-start
    -- Resolve the keep choice: an explicit per-call choice stands; absent one,
    -- the ambient default applies. Then keep the source attribute mapping iff
    -- the resolved choice is to keep, otherwise expose no attributes.
    let resolved : Bool := keepAttributes.getD globalKeepDefault
    let attrsOut : List (String × String) := if resolved then xAttrs else []
    return { values := whereSelect cond x y, attrs := attrsOut }
    -- impl-end

prove_correct selectByCondition by
  loom_solve
