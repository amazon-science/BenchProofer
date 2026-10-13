import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Both modeled functions are changed functions whose
--  new logic is a pure boolean combination of their inputs, modeled deeply.
--  The widget-kind test and the initial-value-present test are observed only
--  through their boolean results, which are the inputs here.)
-- axioms-end

-- pure-start
-- (No pure helpers needed: each decision is a closed boolean expression.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- When a model relation builds the choice field used to pick a related object,
   it must hand that field the model's own "a blank selection is permitted"
   flag, so the field can decide downstream whether to present an unfilled
   option. The forwarded flag is exactly the model's declared blank-allowed
   flag — nothing more, nothing less. The model's flag is read-only (not
   `mut`); this query computes a single boolean and mutates nothing
   (directive 5). Input and result are modeled as `Bool`. -/
method relationBlankFlag (modelAllowsBlank : Bool) return (out : Bool)
  ensures out = modelAllowsBlank
  do
    -- impl-start
    -- Pre-image (site B): the relation did NOT forward the model's blank-allowed
    -- flag when building the choice field, so the field always behaved as though
    -- a blank selection were not permitted, regardless of the model's actual
    -- declaration. This skeleton drops the flag (constant non-permitted) and
    -- MUST fail the frozen spec whenever the model does permit a blank.
    return false
    -- impl-end

prove_correct relationBlankFlag by
  loom_solve

/- A choice field for picking one related object decides whether to present a
   leading, unfilled "blank" option. That option is presented unless the field
   determines it would be misleading. It is withheld in either of two
   situations:

     * the field is required AND already carries an initial value (a blank
       option would invite clearing a value that must be supplied); or
     * the field renders with a radio widget AND a blank selection is not
       permitted (a radio widget has an inherent unfilled state, so an extra
       blank radio would look like a valid choice when it is not).

   Otherwise the blank option is presented. The result is `true` exactly when
   the blank option is offered.

   Four boolean inputs are observed: whether the field is required, whether an
   initial value is present, whether the widget is a radio widget, and whether a
   blank selection is permitted. All are read-only (not `mut`); the decision
   mutates nothing (directive 5). The radio-widget kind and the
   blank-permitted flag are observed as DISTINCT inputs because the second
   withholding rule must DISCRIMINATE between a radio field that permits blank
   (option kept) and one that does not (option withheld). All inputs and the
   result are `Bool`. -/
method blankChoiceOffered (required : Bool) (initialPresent : Bool) (widgetIsRadio : Bool) (blank : Bool) return (out : Bool)
  ensures out = !((required && initialPresent) || (widgetIsRadio && !blank))
  do
    -- impl-start
    return !((required && initialPresent) || (widgetIsRadio && !blank))
    -- impl-end

prove_correct blankChoiceOffered by
  loom_solve
