import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The choose-one-of-two selection is modeled deeply; the
--  attribute / truthy-fallback semantics it stands on are validated against the
--  real behaviour out-of-band by axiom_check.py (G-AX) as an A-reference, not
--  consumed here.)
-- axioms-end

-- pure-start
-- (No auxiliary pure spec helpers are required for this behaviour.)
-- pure-end

/- A selected item carries two integer field identities: a *source* identity and
   a *resolved* identity.

   The resolved identity is always usable (nonzero). The source identity may be
   the sentinel `0`, meaning "no usable source identity present"; any nonzero
   source identity is a distinct, usable identity.

   The single field identity reported for the item is chosen as follows: when the
   source identity is usable (nonzero) it is reported; otherwise the resolved
   identity is reported. The discriminating inputs are those whose source
   identity is nonzero and differs from the resolved identity — there the result
   must be the source identity, never the resolved one.

   The item is read-only: neither identity is `mut`, and nothing is mutated
   (directive 5). Both identities and the result are modeled as `Int`, with a
   field identity carried by integer identity. -/

structure Selection where
  source : Int
  field : Int

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method outputFieldIdentity (sel : Selection) return (r : Int)
  require sel.field ≠ 0
  ensures (sel.source ≠ 0 → r = sel.source) ∧ (sel.source = 0 → r = sel.field)
  do
    -- impl-start
    let source := sel.source
    if source ≠ 0 then
      return source
    else
      return sel.field
    -- impl-end

prove_correct outputFieldIdentity by
  loom_solve
