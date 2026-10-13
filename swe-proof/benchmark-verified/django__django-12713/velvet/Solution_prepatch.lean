import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The only behaviour modeled here is the precedence
--  between a caller-supplied widget and a default widget computed from the input
--  field's characteristics. The computation of that default is UNCHANGED and is
--  taken as a FREE INPUT `computedDefault`, so the spec makes no behavioural
--  claim about how the default is derived and holds for every value of it (an R
--  abstraction, validated against the real default-selection chain by
--  conformance_check.py / G-CONF). Nothing is consumed as an axiom, hence no
--  G-AX. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- An opaque widget identity. Only whether two widgets are the same object/kind
   is observable to the caller (the consumer compares the resolved widget to the
   one it supplied), so a tagged id is the faithful carrier. -/
structure Widget where
  id : Nat
deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve which widget to use for an input field.

   The caller may supply a widget explicitly (`provided` is `some`); when it
   does, that widget must be the one used. When the caller supplies none
   (`provided` is `none`), the widget is the default computed from the field's
   characteristics (`computedDefault`), which may itself be absent (`none`) when
   the field has no special default.

   Both inputs are read-only (neither `mut`): the routine inspects the supplied
   widget and the computed default and decides; it mutates neither (directive 5). -/
method resolveWidget (provided : Option Widget) (computedDefault : Option Widget)
    return (out : Option Widget)
  ensures out = (if provided.isNone then computedDefault else provided)
  do
    -- impl-start
    -- Pre-image skeleton: the field's computed default is applied
    -- unconditionally, so whenever a default exists it OVERWRITES whatever the
    -- caller supplied. The frozen spec requires the caller's widget to win when
    -- supplied, so prove_correct MUST fail.
    let mut widget := provided
    if computedDefault.isSome then
      widget := computedDefault
    return widget
    -- impl-end

prove_correct resolveWidget by
  loom_solve
