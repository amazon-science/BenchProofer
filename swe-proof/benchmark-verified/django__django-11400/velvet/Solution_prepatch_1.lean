import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a pure decision over
--  two ordering specifications — the one the caller explicitly requests and the
--  one the collection carries intrinsically — yielding the ordering specification
--  the collection is finally materialized under. The downstream materialization
--  that turns an ordering specification into an ordered sequence is an UNCHANGED
--  shared continuation reached identically on both branches, so nothing about it
--  is assumed: it is not consumed as a contract and not deep-modeled. There is no
--  `axiom` declaration and no A-reference. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The ordering specification a collection is finally materialized under, given
   the collection's intrinsic default ordering and an explicitly requested
   ordering. An ordering specification is a sequence of ordering keys (empty = no
   explicit request).

   When the caller requests an explicit ordering (a non-empty sequence of keys),
   that request governs and is used verbatim. When the caller requests nothing
   (the empty sequence), the collection's intrinsic default ordering is preserved
   — an empty request must NOT override the default with "no ordering at all".

   The governing distinction: an empty explicit request asks to *adopt the
   default*, not to *discard* it. Grounded entirely in the two input sequences
   (directive 8): the result is one of them, selected by whether the requested
   sequence is empty. -/
def effectiveOrdering (defaultOrdering requested : List String) : List String :=
  if requested.isEmpty then defaultOrdering else requested
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Determine the ordering specification a related collection's choices are
   materialized under. `defaultOrdering` is the collection's intrinsic default
   ordering — the ordering it carries unless told otherwise; it is read-only
   (not `mut`) and is never altered. `requested` is the ordering explicitly asked
   for at this call site; also read-only.

   Desired behaviour: an explicit non-empty request governs and is used as given;
   an empty request falls back to — and therefore preserves — the collection's
   intrinsic default ordering, rather than collapsing it to no ordering. The
   result is the ordering specification the (unchanged) materialization then
   reads, so it fully determines the order of the produced choices. -/
method orderedChoices (defaultOrdering : List String) (requested : List String)
    return (out : List String)
  ensures out = effectiveOrdering defaultOrdering requested
  do
    -- impl-start
    -- Pre-patch skeleton (buggy): the requested ordering drives the
    -- materialization unconditionally. When `requested` is empty this collapses
    -- the collection's intrinsic default ordering to "no ordering" instead of
    -- falling back to it. The frozen spec requires the fallback
    -- (effectiveOrdering), so prove_correct MUST fail on the empty-request clause.
    let ordering := requested
    return ordering
    -- impl-end

prove_correct orderedChoices by
  loom_solve
  simp_all [effectiveOrdering]

/- Determine the ordering specification a value-restricted related collection's
   choices are materialized under. This call site narrows the related collection
   to the values actually in use, and then materializes the choices through the
   SAME ordering kernel (`orderedChoices`): an administrator-configured ordering
   for the related collection MUST be supplied to that kernel, so that the
   restricted choices honor the configured ordering exactly as the unrestricted
   choices do.

   `defaultOrdering` is the related collection's intrinsic default ordering;
   `adminOrdering` is the administrator-configured ordering for that collection
   (empty when none is configured). Both are read-only (not `mut`). Desired
   behaviour: the configured ordering plays the role of the explicit request to
   the shared kernel — when configured it governs, and when absent the kernel's
   fallback preserves the intrinsic default ordering. The configured ordering
   must reach the kernel; discarding it would lose that guarantee. -/
method restrictedChoices (defaultOrdering : List String) (adminOrdering : List String)
    return (out : List String)
  ensures out = effectiveOrdering defaultOrdering adminOrdering
  do
    -- impl-start
    -- Route the administrator-configured ordering through the shared ordering
    -- kernel; it is treated exactly as an explicit request, so a configured
    -- ordering governs and an absent one falls back to the default.
    let out ← orderedChoices defaultOrdering adminOrdering
    return out
    -- impl-end

prove_correct restrictedChoices by
  loom_solve
