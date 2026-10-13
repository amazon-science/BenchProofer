import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The decision modeled here is a closed boolean
--  function of its inputs, and the field set it returns is one of two input
--  lists. The predicate that observes whether change-notification subscribers
--  are registered for a model is itself an added helper, modeled DEEPLY in the
--  `pure` region as the disjunction of its two boolean observations; its
--  callees (the per-kind subscriber-presence queries) are abstracted to the two
--  boolean inputs `preDelete`/`postDelete` (an R refinement, validated against
--  the real registry by conformance_check.py / G-CONF). Nothing is consumed as
--  an axiom — see refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- Whether any change-notification subscriber that would expose the about-to-be
   removed rows to user code is registered for a model. Two kinds matter: a
   subscriber notified just before removal, and one notified just after. The
   predicate holds iff at least one of the two is present. (Subscribers for the
   set-membership-changed notification are deliberately NOT consulted here: such
   a subscriber never receives the rows under consideration, so it places no
   requirement on which columns are fetched.) -/
@[grind] def hasExposingSubscriber (preDelete postDelete : Bool) : Bool :=
  preDelete || postDelete

/- Whether the column set fetched for the dependent rows may be narrowed to the
   referenced columns only. Narrowing is permitted exactly when the fetch was
   NOT widened to also pull in further related rows (which would make the
   interaction between the two narrowings hard to get right) AND no exposing
   subscriber is registered (which could hand the rows to user code, where any
   column might be read). -/
@[grind] def mayNarrow (widenedFetch preDelete postDelete : Bool) : Bool :=
  !(widenedFetch || hasExposingSubscriber preDelete postDelete)

/- The set of columns actually fetched for the dependent rows. When narrowing is
   permitted, only the referenced columns are fetched; otherwise the full set of
   columns is fetched. `allColumns` and `referencedColumns` model the two column
   sets as identifier lists (mapping.md §2); `referencedColumns ⊆ allColumns` in
   the repo, but the desired behaviour pins the exact set returned, so the model
   needs no subset hypothesis. -/
@[grind] def columnsFetched (allColumns referencedColumns : List Nat)
    (widenedFetch preDelete postDelete : Bool) : List Nat :=
  if mayNarrow widenedFetch preDelete postDelete then referencedColumns
  else allColumns
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Choosing which columns to fetch for a batch of dependent rows that must be
   visited to remove them. The desired behaviour: fetch only the columns that
   are actually referenced (a strict optimisation that avoids decoding columns
   the visit never needs) UNLESS either the fetch was widened to also pull in
   further related rows, or a change-notification subscriber that could expose
   the rows to user code is registered for the dependent model — in either of
   those cases the full column set must be fetched.

   All five inputs are read-only (none `mut`): the routine inspects the two
   candidate column lists and the three boolean conditions and decides; it
   mutates none of them (directive 5). The two boolean subscriber observations
   are combined exactly as `hasExposingSubscriber` (the added predicate), and the
   narrowing decision and resulting column set are pinned exactly by `mayNarrow`
   / `columnsFetched`. -/
method columnsToFetch (allColumns : List Nat) (referencedColumns : List Nat)
    (widenedFetch : Bool) (preDelete : Bool) (postDelete : Bool) return (out : List Nat)
  ensures out = columnsFetched allColumns referencedColumns widenedFetch preDelete postDelete
  ensures hasExposingSubscriber preDelete postDelete = (preDelete || postDelete)
  do
    -- impl-start
    -- Narrow to the referenced columns only when the fetch was not widened and
    -- no exposing subscriber is registered; otherwise keep the full column set.
    let narrow : Bool := !(widenedFetch || (preDelete || postDelete))
    if narrow then
      return referencedColumns
    else
      return allColumns
    -- impl-end

prove_correct columnsToFetch by
  loom_solve
