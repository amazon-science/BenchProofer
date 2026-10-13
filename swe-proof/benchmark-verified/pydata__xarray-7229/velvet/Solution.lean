import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

attribute [solverHint] Array.get_set_c

/- A labelled metadata level of a structured array value: a `name` (the level's
   identifier) and an opaque `attrs` token standing for that level's metadata
   mapping. Distinct tokens model distinct metadata mappings; `0` is the empty
   mapping. Provenance + the value bijection used by the executable checks:
   mapping.md (G-CONF / G-AX). -/
structure Lvl where
  name  : Nat
  attrs : Nat
deriving Inhabited, DecidableEq, Repr

/- A structured array value, reduced to the metadata that the operation touches:
   the global metadata token `gattrs`, the variable levels `vars`, and the
   coordinate levels `coords`. A plain (single-variable) value has `vars = #[]`. -/
structure Obj where
  gattrs : Nat
  vars   : Array Lvl
  coords : Array Lvl
deriving Inhabited

-- axioms-start
-- axioms-end

-- pure-start
/- The metadata token carried by the first level named `nm` in `lvls`, or the
   empty mapping `0` when no level carries that name. This is the by-name
   metadata selection from a designated source value: the metadata of the
   equally-named level, and the empty mapping when the source has no such level. -/
def lookupAttrs : List Lvl → Nat → Nat
  | [],      _  => 0
  | l :: ls, nm => if l.name = nm then l.attrs else lookupAttrs ls nm

/- The rebuilt coordinate level: keep its name, take its metadata from the
   equally-named coordinate level of the source `xCoords` (empty if absent). -/
def rebuiltCoord (xCoords : Array Lvl) (c : Lvl) : Lvl :=
  ⟨c.name, lookupAttrs xCoords.toList c.name⟩

/- The rebuilt variable level. In the ordinary case its metadata comes from the
   equally-named variable level of the source `xVars`. In the promotion case
   (the source is a single-variable value combined into a multi-variable result)
   only the source-named variable receives the source's global metadata; the
   other variables are left as the combination produced them. -/
def rebuiltVar (promote : Bool) (xName xGAttrs : Nat) (xVars : Array Lvl) (v : Lvl) : Lvl :=
  ⟨v.name,
    if promote then (if v.name = xName then xGAttrs else v.attrs)
    else lookupAttrs xVars.toList v.name⟩

/- The rebuilt global metadata: empty under promotion, otherwise the source's
   global metadata. -/
def rebuiltGlobal (promote : Bool) (xGAttrs : Nat) : Nat :=
  if promote then 0 else xGAttrs
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Rebuild the per-level metadata of a combined result `(resVars, resCoords)`
   from one designated source value described by `(xName, xGAttrs, xVars,
   xCoords)`, under the promotion flag `promote`.

   Coordinate levels ALWAYS take their metadata from the equally-named source
   coordinate (`rebuiltCoord`); variable levels take theirs per `rebuiltVar`;
   the global metadata per `rebuiltGlobal`. Names are preserved and the level
   counts are unchanged. -/
method rebuildAttrs
    (promote : Bool) (xName : Nat) (xGAttrs : Nat)
    (xVars : Array Lvl) (xCoords : Array Lvl)
    (resVars : Array Lvl) (resCoords : Array Lvl)
    return (out : Obj)
  ensures out.gattrs = rebuiltGlobal promote xGAttrs
  ensures out.vars.size = resVars.size
  ensures out.coords.size = resCoords.size
  ensures ∀ i, i < resVars.size → out.vars[i]! = rebuiltVar promote xName xGAttrs xVars (resVars[i]!)
  ensures ∀ i, i < resCoords.size → out.coords[i]! = rebuiltCoord xCoords (resCoords[i]!)
  do
    -- impl-start
    -- variable levels: each named level takes the source's equally-named metadata
    let mut outVars := resVars
    let mut i := 0
    while i < resVars.size
      invariant i ≤ resVars.size
      invariant outVars.size = resVars.size
      invariant ∀ j, j < i → outVars[j]! = rebuiltVar promote xName xGAttrs xVars (resVars[j]!)
      done_with i = resVars.size
      decreasing resVars.size - i
    do
      outVars[i] := rebuiltVar promote xName xGAttrs xVars (resVars[i]!)
      i := i + 1
    -- coordinate levels: ALWAYS take the source's equally-named coordinate metadata
    let mut outCoords := resCoords
    let mut k := 0
    while k < resCoords.size
      invariant k ≤ resCoords.size
      invariant outCoords.size = resCoords.size
      invariant ∀ j, j < k → outCoords[j]! = rebuiltCoord xCoords (resCoords[j]!)
      done_with k = resCoords.size
      decreasing resCoords.size - k
    do
      outCoords[k] := rebuiltCoord xCoords (resCoords[k]!)
      k := k + 1
    return { gattrs := rebuiltGlobal promote xGAttrs, vars := outVars, coords := outCoords }
    -- impl-end

prove_correct rebuildAttrs by
  loom_solve
