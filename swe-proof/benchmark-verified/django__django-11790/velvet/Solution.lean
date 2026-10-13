import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no deep-model A-references. The behavior is pure
--  control/data flow: derive a length limit from the account model's configured
--  limit (a default applies when none is configured), then record that limit in
--  the field. Nothing about an unchanged callee's contract is assumed, so there
--  is nothing for G-AX to validate — see mapping.md §3 and axiom_check.py.)
-- axioms-end

-- pure-start
/- The effective maximum input length, derived from the account model's
   configured limit. When the model supplies a positive limit it is used
   directly; when the model configures no limit (or a vacuous zero one) a
   standard default applies. This mirrors the usual "configured value, otherwise a
   default" selection over a possibly-absent setting. -/
@[grind] def resolveLimit (modelLimit : Option Nat) : Nat :=
  match modelLimit with
  | some n => if n = 0 then 254 else n
  | none   => 254
-- pure-end

/- A text-entry form field, observed through exactly the two facets this routine
   must keep in agreement:
   * `maxLength`       — the maximum input length the field itself enforces.
   * `widgetMaxLength` — the same limit as exposed to the field's rendered
                         control (the attribute a browser reads to cap typing).
   `none` means the corresponding limit is unset. Other field attributes are
   untouched here and are not carried (mapping.md §2). -/
structure BoundedField where
  maxLength       : Option Nat
  widgetMaxLength : Option Nat
deriving Inhabited, DecidableEq

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Configure a form field's input-length limit from the account model.

   The desired behavior: the field must enforce the effective limit derived from
   the model's configured limit (defaulting when none is configured), AND that
   same limit must be exposed to the field's rendered control. The two facets
   must agree — a field whose enforced limit is set but whose rendered control
   does not advertise it is the defect this routine must avoid. Both facets end
   up holding the single derived limit.

   `field` is the field being configured; `modelLimit` is the account model's
   configured limit (read-only; not `mut`). The result is a fresh value built
   from `field` with both length facets set. -/
method configureFieldLimit (field : BoundedField) (modelLimit : Option Nat)
    return (result : BoundedField)
  ensures result.maxLength       = some (resolveLimit modelLimit)
  ensures result.widgetMaxLength = some (resolveLimit modelLimit)
  do
    -- impl-start
    -- Derive the effective limit: the model's configured limit, or the default
    -- when none is configured.
    let limit : Nat :=
      match modelLimit with
      | some n => if n = 0 then 254 else n
      | none   => 254
    -- Record the limit on the field, and expose the same limit to its rendered
    -- control.
    let mut result := field
    result := { result with maxLength := some limit }
    result := { result with widgetMaxLength := some limit }
    return result
    -- impl-end

prove_correct configureFieldLimit by
  loom_solve
