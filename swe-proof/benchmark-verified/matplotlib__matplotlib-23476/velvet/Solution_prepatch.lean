import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The step under spec touches only values already
--  present in the assembled snapshot; it calls no outside routine whose
--  behaviour would have to be assumed. The whole effect — choosing which
--  resolution value the snapshot carries — is modeled directly below.)
-- axioms-end

-- pure-start
/- A serialized snapshot of a drawing surface, abstracted to the fields this
   step touches or must preserve:

   - `resolution` — the dots-per-inch value the snapshot currently carries.
   - `baseline` — an optional, separately recorded reference resolution. It is
     present when a reference value was captured for this surface and absent
     otherwise.
   - `payload` — the remainder of the assembled snapshot (everything else the
     surface contributes to its serialized form). It is opaque here and is not
     affected by the step under spec.

   Only these touched/observed parts are carried; the bijection to the real
   serialized-state mapping is in mapping.md §2. -/
structure SurfaceSnapshot where
  resolution : Float
  baseline : Option Float
  payload : List Char
  deriving Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Finalize the resolution recorded in a serialized snapshot.

   A drawing surface's working resolution may differ from the reference
   resolution that was captured for it. The persisted snapshot must carry the
   reference value whenever one is available, so that reading the snapshot back
   reconstructs the surface at its reference resolution rather than at whatever
   transient working value happened to be in effect. When no reference value was
   captured, the current resolution is persisted unchanged.

   This step must disturb nothing else: the recorded reference value itself and
   the rest of the snapshot survive exactly as supplied (directive 5 frame —
   `snap` is read-only, not `mut`; the result is built freshly from it). The
   three guarantees together pin the behavior: the persisted resolution is the
   reference value when present and the current value otherwise, and every other
   part of the snapshot is preserved. -/
method finalizeSnapshot (snap : SurfaceSnapshot) return (out : SurfaceSnapshot)
  ensures out.resolution = snap.baseline.getD snap.resolution
  ensures out.baseline = snap.baseline
  ensures out.payload = snap.payload
  do
    -- impl-start
    -- Pre-patch skeleton: the finalize step persists the working resolution as
    -- it stands, never substituting the recorded reference value when one is
    -- present. The frozen spec requires the persisted resolution to be the
    -- reference value whenever `baseline` is `some _`, so prove_correct MUST
    -- fail on the `out.resolution = snap.baseline.getD snap.resolution` clause
    -- (the two differ exactly when a reference value was captured).
    return snap
    -- impl-end

prove_correct finalizeSnapshot by
  loom_solve
