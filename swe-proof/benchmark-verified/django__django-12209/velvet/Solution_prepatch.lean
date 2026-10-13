import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed boolean
--  decision over its inputs: given five read-only boolean observations about a
--  persistence request, it returns the boolean that controls whether the row is
--  written with an INSERT-only path. The underlying observations — whether the
--  request is a direct/unprocessed data load, whether an INSERT is already
--  being forced, whether the instance is being added for the first time, and
--  whether its primary key carries a usable default — are abstracted to the
--  boolean inputs (an R refinement, validated against the real persistence path
--  by conformance_check.py / G-CONF). Nothing is consumed as an axiom — see
--  refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- Whether the primary key carries a usable default value: it must both be set
   to something truthy AND be a genuinely provided default (not the sentinel
   that marks "no default at all"). Both observations are modeled as boolean
   inputs (mapping.md §2); the predicate holds iff both are true. -/
@[grind] def pkHasUsableDefault (pkDefaultTruthy pkDefaultProvided : Bool) : Bool :=
  pkDefaultTruthy && pkDefaultProvided

/- The decision that controls whether persisting a row skips the initial
   UPDATE probe and goes straight to an INSERT.

   The INSERT-only path is taken exactly when ALL of the following hold:
     * the request is an ordinary save, not a direct/unprocessed data load;
     * an INSERT is not already being forced by the caller;
     * the instance is being added for the first time;
     * its primary key carries a usable default value.
   Otherwise the incoming forcing flag is returned unchanged. In particular,
   for a direct/unprocessed data load the forcing is never introduced here, so
   an explicit primary key remains free to match an existing row through the
   ordinary UPDATE probe. -/
@[grind] def decidedForceInsert
    (raw forceInsert adding pkDefaultTruthy pkDefaultProvided : Bool) : Bool :=
  if !raw && !forceInsert && adding && pkHasUsableDefault pkDefaultTruthy pkDefaultProvided
  then true
  else forceInsert
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve the INSERT-forcing flag for a single-table persistence request.

   `raw` marks a direct/unprocessed data load (e.g. loading serialized
   fixtures); `forceInsert` is the caller-supplied request to force an INSERT;
   `adding` is whether the instance is being added for the first time;
   `pkDefaultTruthy` / `pkDefaultProvided` are the two observations about the
   primary key's default that together decide whether it carries a usable
   default value.

   All five inputs are read-only (none `mut`, directive 5): the routine inspects
   the five conditions and returns the resolved flag, mutating none of them. The
   resolved value is pinned exactly by `decidedForceInsert`: the INSERT-only path
   is forced only for an ordinary save of a freshly-added instance whose primary
   key has a usable default, and never for a direct/unprocessed data load. -/
method decideForceInsert
    (raw : Bool) (forceInsert : Bool) (adding : Bool)
    (pkDefaultTruthy : Bool) (pkDefaultProvided : Bool) return (out : Bool)
  ensures out = decidedForceInsert raw forceInsert adding pkDefaultTruthy pkDefaultProvided
  ensures pkHasUsableDefault pkDefaultTruthy pkDefaultProvided
            = (pkDefaultTruthy && pkDefaultProvided)
  do
    -- impl-start
    -- Pre-image skeleton: the INSERT-only path is forced for any freshly-added
    -- instance whose primary key has a usable default, WITHOUT excluding a
    -- direct/unprocessed data load. The frozen spec excludes such loads
    -- (`!raw`), so for a raw load with an explicit usable-default primary key
    -- this returns `true` where the spec returns `forceInsert` — prove_correct
    -- MUST fail.
    if (!forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided)) then
      return true
    else
      return forceInsert
    -- impl-end

prove_correct decideForceInsert by
  loom_solve
