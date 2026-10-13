import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The inherited base-widget decision about whether a required-style marker is
   appropriate for this control, given whether the form already carries a value
   for the field. This is an UNCHANGED inherited routine the operation defers to;
   it is left OPAQUE (a free function) — the operation refines it, never replaces
   it, so no contract is claimed about its return value. Provenance: mapping.md.
   Because it is a free function with no asserted `ensures`, there is nothing to
   validate against the real callee (no axiom_check.py — meta.json G-AX skip). -/
opaque inheritedRequiredDecision : Bool → Bool
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A file-upload control decides whether to advertise a required-style marker on
   its rendered element. The desired behavior: the control advertises the marker
   only when the inherited base decision would allow it AND the form does not
   already carry an existing value for this field. When an existing value is
   present, the user may legitimately leave the control blank to keep that value,
   so the marker must be suppressed even if the base decision alone would permit
   it.

   `hasInitial` is the read-only flag for "an existing value is already present"
   (not `mut`); the routine computes a single boolean and mutates nothing
   (directive 5). The inherited base decision is deferred to as an opaque input
   (a free function of `hasInitial`); the result is its conjunction with the
   absence of an existing value. -/
method useRequiredAttribute (hasInitial : Bool) return (out : Bool)
  ensures out = (inheritedRequiredDecision hasInitial && !hasInitial)
  do
    -- impl-start
    -- Defer to the inherited base decision (an opaque inherited routine), then
    -- conjoin with the absence of an existing value.
    return (inheritedRequiredDecision hasInitial && !hasInitial)
    -- impl-end

prove_correct useRequiredAttribute by
  loom_solve
