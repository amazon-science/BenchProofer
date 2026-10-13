import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the cache-reset is a pure state operation on the
--  registry's own observable cache occupancies, modeled directly as state
--  writes. The unchanged stdlib memoization wrapper whose emptied-cache effect
--  these writes refine is an A-reference validated out-of-band, not a consumed
--  contract.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- An application registry keeps several memoizing lookup methods, each backed
   by its own bounded result cache whose occupancy — the number of distinct
   argument tuples whose result is currently retained — can be observed as a
   non-negative count.

   The registry exposes a single cache-reset operation whose promise is to
   discard ALL of those retained results: every memoizing method's cache. So
   immediately afterwards each cache's occupancy must be zero, regardless of how
   full any of them was beforehand. A reset that leaves any one method's
   retained results in place would violate that promise — a later observer would
   still see stale memoized values for that method.

   Here two memoizing methods are modeled (the all-models lookup and the
   swappable-settings-name lookup), carrying only the touched state: one
   non-negative occupancy counter each. Both counters are genuinely mutated
   (declared `mut`) and their post-states are pinned exactly to zero (directive
   5: every changed frame is pinned to its exact post-state). -/
method clearAllCaches (mut modelsOccupancy : Nat) (mut swappableOccupancy : Nat)
    return (unit : Unit)
  ensures modelsOccupancy = 0
  ensures swappableOccupancy = 0
  do
    -- impl-start
    -- Pre-image (buggy) skeleton: the reset empties only the all-models lookup
    -- cache and NEVER clears the swappable-settings-name lookup cache, so its
    -- occupancy is left exactly as it came in (a stale, possibly-positive count).
    -- The frozen spec requires `swappableOccupancy = 0` on return, so
    -- prove_correct MUST fail on that clause.
    modelsOccupancy := 0
    return ()
    -- impl-end

prove_correct clearAllCaches by
  loom_solve
