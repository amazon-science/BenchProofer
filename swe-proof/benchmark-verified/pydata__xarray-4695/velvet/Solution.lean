import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no deep-model references. The label-based
--  selection routine is, for a given source array, a deterministic function of
--  the indexer mapping it is asked to apply (one (dimension-name, label-values)
--  pair per entry). We model the routine's observable result as exactly that
--  applied mapping (an R type-refinement of the returned array — see
--  refinement.md / mapping.md §2). Nothing about the downstream selection
--  engine is consumed as an axiom; the behaviour under specification is the
--  routing of the supplied mapping, modeled deeply as the identity carry-through
--  below. G-AX is therefore skipped; G-CONF differential-tests the R/I leg.)
-- axioms-end

-- pure-start
/- The value supplied for one dimension: a list of tick labels (a scalar label
   is the singleton list). The selection routine carries these through unchanged;
   only which dimension each list is bound to is behaviourally significant. -/
abbrev Label := List String
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Label-based selection from a source array given an explicit mapping of
   dimension name to the labels requested along that dimension.

   `key` is read-only (not `mut`): the routine inspects the mapping and performs
   the selection; it does not alter the request (directive 5).

   The desired behaviour: EVERY entry of the mapping is honoured as a
   dimension/label request — the result is the selection driven by the whole
   mapping, in order, with no entry omitted, re-purposed, or rejected, REGARDLESS
   of the textual dimension names involved. Selection succeeds (`Except.ok`)
   carrying exactly the mapping that was applied; a dimension whose name happens
   to coincide with an option of the selection routine must NOT cause that entry
   to be diverted away from the dimension request (which would drop it from the
   applied mapping, or be rejected as a malformed option).

   The result is modeled as the applied (dimension, labels) mapping: for a given
   source array the selected array is a deterministic function of exactly this
   mapping (R refinement, mapping.md §2), so pinning the applied mapping pins the
   selected array. -/
method labelSelect (key : List (String × Label))
    return (out : Except String (List (String × Label)))
  ensures out = Except.ok key
  do
    -- impl-start
    -- Apply the whole mapping as the dimension/label request, as a unit.
    return Except.ok key
    -- impl-end

prove_correct labelSelect by
  loom_solve
