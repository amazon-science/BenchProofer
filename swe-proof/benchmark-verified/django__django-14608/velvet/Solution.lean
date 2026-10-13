import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- An error-message collection paired with the CSS class string under which it
   renders. Only the two fields the modeled behavior observes are kept: the
   ordered messages and the rendered class string. -/
structure ErrorBox where
  data : List (List Char)
  cssClass : List Char
  deriving Inhabited

/- The CSS class string an error collection carries, given an optional modifier
   label. With no modifier the base class stands alone; with a modifier the base
   class is followed by a single space and the modifier. This is a deep model of
   the unchanged collection constructor's class-string computation, validated
   equal to it by axiom_check.py (G-AX). -/
def cssClassFor (modifier : Option (List Char)) : List Char :=
  match modifier with
  | none   => "errorlist".toList
  | some m => "errorlist ".toList ++ m
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method buildNonFormErrors (errors : List (List Char)) return (out : ErrorBox)
  ensures out.data = errors
  ensures out.cssClass = cssClassFor (some "nonform".toList)
  do
    -- impl-start
    let cls := cssClassFor (some "nonform".toList)
    return { data := errors, cssClass := cls }
    -- impl-end

prove_correct buildNonFormErrors by
  loom_solve
