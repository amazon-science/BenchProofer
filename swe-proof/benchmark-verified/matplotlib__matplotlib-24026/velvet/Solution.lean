import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The colour-selection rule under spec is modeled
--  DEEPLY in the `pure` region — `cyclicColors` IS the repetition of a finite
--  colour sequence, an A-reference validated == the standard-library finite
--  cyclic iterator by axiom_check.py (G-AX). No consumed axiom borrows
--  soundness from an outside contract; the shared-state frame is modeled
--  directly as a `mut` parameter pinned to its entry value. See refinement.md
--  §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The colour assigned to each of `layerCount` stacked areas, drawn in order
   from a finite, non-empty sequence of requested colours that is repeated as
   often as needed: area `i` takes colour `colors[i % colors.length]`. With
   exactly as many colours as areas this is the identity ordering; with fewer
   colours than areas the sequence wraps around from the beginning, and with
   more colours than areas the surplus is simply unused. The result has one
   colour per area, in area order. -/
def cyclicColors (colors : List String) (layerCount : Nat) : List String :=
  (List.range layerCount).map (fun (i : Nat) => colors[i % colors.length]!)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Choose the per-area fill colours for a stack of `layerCount` filled areas
   when an explicit, non-empty list of `colors` is supplied, and report the
   colour each area is filled with, in area order.

   The guarantees pin the two behaviours the request demands:

   - the colours are drawn solely from the supplied list, repeated cyclically:
     `out = cyclicColors colors layerCount` (exactly `layerCount` colours, area
     `i` taking `colors[i % colors.length]`). The choice is grounded entirely in
     the caller's own `colors`; it does not depend on, and is not drawn from,
     any colour source shared with other artists on the same axes.

   - the surrounding shared colour-cycle state is read-only: whatever colour
     sequence the axes would hand to its OTHER artists must be exactly the same
     after this operation as before it. `sharedCycle` carries that shared
     colour-cycle state; it is declared `mut` (the long-standing shape of this
     code reaches for the shared cycle as the place to record colours) but its
     post-state is pinned EXACTLY to its entry value
     (`ensures sharedCycle = sharedCycleOld`, directive 5). This is precisely the
     guarantee the use-case needs: colours stay synchronised across the other
     plot types drawn on the same axes, because filling these areas neither
     advances nor replaces the shared cycle.

   `colors` is read-only (not `mut`) and must be non-empty so the cyclic choice
   is well defined. A single colour specification is carried as a `String` (a
   named colour, hex string, or cycle reference such as `"C2"`); the operation
   only ever copies and reorders these tokens, never interpreting them, so an
   ordered `List String` carrier is faithful (mapping.md §2). -/
method selectLayerColors (mut sharedCycle : List String) (colors : List String)
    (layerCount : Nat) return (out : List String)
  require colors.length > 0
  ensures sharedCycle = sharedCycleOld
  ensures out = cyclicColors colors layerCount
  do
    -- impl-start
    -- Repeat the supplied colours over the areas using a private cyclic walk of
    -- `colors`; the shared colour-cycle state `sharedCycle` is never written, so
    -- it is handed back exactly as received.
    let assigned := (List.range layerCount).map
      (fun (i : Nat) => colors[i % colors.length]!)
    return assigned
    -- impl-end

prove_correct selectLayerColors by
  loom_solve
  simp [cyclicColors]
