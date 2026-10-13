import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a pure dispatch on the
--  incoming object's own observable shape: whether it is one of the recognized
--  container types, and what stored values it exposes. Both are read deeply from
--  the input carrier's fields (`isRecognized`, `valuesPayload`) — there is no
--  outside callee whose contract the proof consumes, and no claim is made about
--  any unchanged routine, so there is nothing to check against a real callee,
--  hence no G-AX. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- The identity of a data object (or of a stored values payload), modeled
   abstractly: the desired behaviour observes only WHICH object is forwarded —
   the object handed in, or the values it exposes — never the object's content.
   A single opaque carrier therefore suffices. -/
abbrev Obj := Nat

/- A data object as it arrives at the preparation step, described by exactly the
   three observables the dispatch consults:

   * `obj`           — the object's own identity (what "forward it unchanged"
                       yields);
   * `valuesPayload` — the stored values the object exposes, if it exposes any
                       (`some v`), or `none` if it exposes no such stored values;
   * `isRecognized`  — whether the object is one of the recognized container
                       types whose stored values are meant to be taken.

   Two incoming objects are the same exactly when all three observables agree. -/
structure Incoming where
  obj            : Obj
  valuesPayload  : Option Obj
  isRecognized   : Bool
  deriving DecidableEq

/- What the preparation step forwards.

   An object of one of the recognized container types is unwrapped to the stored
   values it exposes; EVERY other object is forwarded unchanged — even one that
   happens to expose a stored-values payload. In particular, exposing a values
   payload is NOT on its own grounds to unwrap: only the recognized container
   types are unwrapped. This is the behaviour an arbitrary user object with a
   values payload requires — it must be forwarded as itself, not silently
   replaced by its payload. -/
def forwarded (w : Incoming) : Obj :=
  if w.isRecognized then w.valuesPayload.getD w.obj else w.obj
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Prepare a data object for downstream wrapping.

   `w` carries the incoming object's three observables (above). The result is the
   object that should be handed downstream: an object of one of the recognized
   container types is replaced by the stored values it exposes; any other object
   — including one that merely exposes a values payload — is forwarded unchanged.

   `w` is read-only (not `mut`): the step inspects the incoming object's shape and
   returns the object to forward, mutating nothing it is handed (directive 5).

   `require`: an object of a recognized container type always exposes a stored
   values payload (`isRecognized → valuesPayload.isSome`), so unwrapping it
   genuinely yields that payload rather than falling back to the object itself. -/
method prepareData (w : Incoming) return (out : Obj)
  require w.isRecognized = true → w.valuesPayload.isSome = true
  ensures out = forwarded w
  do
    -- impl-start
    -- PRE-PATCH (buggy) skeleton: unwrap to the stored values whenever the
    -- object exposes ANY values payload, regardless of its type. Any object that
    -- exposes a values payload is silently replaced by that payload. The frozen
    -- spec requires `forwarded` (unwrap only the recognized container types), so
    -- on an UNrecognized object that exposes a payload this returns the payload
    -- where the spec demands the object itself — prove_correct MUST fail.
    let out :=
      match w.valuesPayload with
      | some v => v
      | none   => w.obj
    return out
    -- impl-end

prove_correct prepareData by
  loom_solve
  simp_all [forwarded]
