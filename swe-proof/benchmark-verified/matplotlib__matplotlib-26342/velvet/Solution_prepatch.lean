import Velvet.Std
-- imports-end

-- Total-correctness semantics: the desired behavior is that a path-replacement
-- request COMPLETES (see the method docstring), so the spec must also rule out
-- implementations that diverge (under partial correctness a non-terminating
-- body would vacuously satisfy every postcondition).
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axiomatized callees: the operation under specification is a leaf state
-- mutation modeled DIRECTLY over the observable carrier (see the `pure` region).
-- There is no unchanged callee whose internal behavior the proof must assume.
-- axioms-end

-- pure-start
/- The observable state of a drawable path container, restricted to the two
   aspects a path-replacement request can touch:

   * `paths` — the ordered collection of drawable paths the container currently
     holds (what a paths query returns); modeled as a list of opaque path
     identities (`Int`), since the operation neither inspects nor reshapes any
     individual path, it only stores the supplied collection wholesale;
   * `stale` — whether the container is marked as needing a redraw before it can
     next be rendered.

   All other container state (offsets, transforms, sizes, styling) is untouched
   by a path-replacement request and is therefore not part of this carrier
   (mapping.md §2). -/
structure PathContainer where
  paths : List Int
  stale : Bool
  deriving Inhabited, DecidableEq

/- A paths query reports the collection the container currently holds. -/
def getPaths (c : PathContainer) : List Int := c.paths
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Replace the drawable paths held by a container with a supplied collection.

   Desired behavior: the request must SUCCEED (it completes normally rather than
   refusing the operation), the container thereafter holds exactly the supplied
   collection of paths — so a subsequent paths query returns precisely what was
   stored — and the container is marked as needing a redraw. The success/refusal
   outcome is reported in `out`: `Except.ok ()` for a completed replacement,
   `Except.error ()` for a refusal that leaves the request unfulfilled.

   `newPaths` is the read-only supplied collection (not `mut`): it is stored, not
   altered. The container `coll` is mutated to reflect the replacement; both
   touched aspects (`paths`, `stale`) are pinned exactly, so no fragment of the
   post-state is left unconstrained (directive 5). -/
method setPaths (mut coll : PathContainer) (newPaths : List Int)
    return (out : Except Unit Unit)
  ensures out = Except.ok ()
  ensures coll.paths = newPaths
  ensures getPaths coll = newPaths
  ensures coll.stale = true
  do
    -- impl-start
    -- Pre-image skeleton: the path-replacement request resolves to the generic
    -- base-class handler, which refuses the operation outright — it reports a
    -- refusal and leaves the container's stored paths and redraw flag untouched.
    -- The frozen spec demands a completed replacement that stores the supplied
    -- collection and marks a redraw, so prove_correct MUST fail.
    return Except.error ()
    -- impl-end

prove_correct setPaths by
  loom_solve
