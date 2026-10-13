import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no A-reference deep model. The operation under
--  specification — constructing the handler's persisted object state — is
--  modeled deeply as the do block below. The only environment fact relied on is
--  structural and is encoded in the type model: a stored reference handle is
--  serializable on its own, whereas the live rendering surface is not (the
--  distinguished `Attr.surface` token). Nothing is borrowed from an outside
--  contract, so there is no axiom to validate — meta.json G-AX skip.)
-- axioms-end

-- pure-start
/- The kinds of value a freshly constructed drag-interaction handler can place
   into its persisted object state:

     * `surface`      — the live rendering surface the handler talks to. It is
                        NOT serializable: if it is placed into the persisted
                        state it is dragged into the serialized stream and makes
                        the whole object impossible to persist.
     * `refHandle`    — a reference to the object being dragged. It IS
                        serializable on its own, and the surface can be obtained
                        through it on demand.
     * `flag b`       — a boolean status/mode bit (serializable).
     * `registration` — a record of installed event registrations (serializable).

   The behavior under specification turns on WHICH of these the handler retains,
   so a first-class tag with decidable equality. -/
inductive Attr where
  | surface
  | refHandle
  | flag (b : Bool)
  | registration
  deriving DecidableEq, Inhabited

/- A constructed handler, abstracted to exactly what the observed behavior
   depends on:

     * `attrs`          — the values retained in its persisted object state (the
                          content that would be written to a serialized stream);
     * `surfaceFromRef` — whether the handler can produce the rendering surface
                          on demand from its stored reference handle, WITHOUT
                          retaining the surface in its persisted state. -/
structure Handler where
  attrs : List Attr
  surfaceFromRef : Bool
  deriving Inhabited

/- Serializability: the persisted state must contain no non-serializable
   rendering surface, so that the object can be persisted as a whole. -/
def persistable (h : Handler) : Prop :=
  Attr.surface ∉ h.attrs

/- Reachability: the rendering surface must remain obtainable. Either the
   handler can derive it on demand from a retained reference handle, or it still
   retains the surface directly. Grounded in the actual retained values: the
   first disjunct requires the reference handle to be present. -/
def surfaceReachable (h : Handler) : Prop :=
  (h.surfaceFromRef = true ∧ Attr.refHandle ∈ h.attrs) ∨ Attr.surface ∈ h.attrs

/- Status-bit inventory closure: the only boolean status/mode bits the
   constructed handler retains are the two it is built with — the cleared
   drag-status bit and the given effective mode bit. A handler carrying any
   other status bit is a different object than the one this constructor
   builds. -/
def flagsExact (h : Handler) (effective : Bool) : Prop :=
  ∀ b : Bool, Attr.flag b ∈ h.attrs → (b = false ∨ b = effective)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Constructing a drag-interaction handler. The handler watches an object being
   dragged across a rendering surface; it records a reference to that object,
   the mode/status bits it needs, and the event registrations it installs.

   Two behaviors are required of the constructed handler:

     * its persisted object state must be serializable — it must NOT retain the
       (non-serializable) rendering surface in that state, or the whole object
       becomes impossible to persist;
     * the rendering surface must nevertheless remain reachable — the handler
       must be able to obtain it on demand from the reference it retains.

   `useBlit` and `supportsBlit` are read-only inputs (a requested mode bit and a
   capability bit of the surface); the constructor builds a fresh handler and
   mutates neither (directive 5). The effective mode bit retained is their
   conjunction. The persisted state must carry the full working inventory: the
   reference to the dragged object, the (initially cleared) drag-status bit, the
   effective mode bit, and the installed event registrations — a handler
   constructed without its event registrations or its cleared status bit is not
   the required object, and neither is one that smuggles in status bits beyond
   those two (`flagsExact`). -/
method initHandler (useBlit : Bool) (supportsBlit : Bool) return (out : Handler)
  ensures persistable out
  ensures surfaceReachable out
  ensures Attr.refHandle ∈ out.attrs
  ensures Attr.flag (useBlit && supportsBlit) ∈ out.attrs
  ensures Attr.flag false ∈ out.attrs
  ensures Attr.registration ∈ out.attrs
  ensures flagsExact out (useBlit && supportsBlit)
  do
    -- impl-start
    -- Pre-image skeleton: the handler retains the rendering surface DIRECTLY in
    -- its persisted state (and provides no on-demand derivation —
    -- `surfaceFromRef := false`). Reachability is satisfied via the directly
    -- retained surface, but the persisted state now embeds the non-serializable
    -- surface, so the `persistable` clause is violated and prove_correct MUST
    -- fail.
    let mut attrs : List Attr := []
    attrs := Attr.refHandle :: attrs
    attrs := Attr.surface :: attrs
    attrs := Attr.flag false :: attrs
    attrs := Attr.flag (useBlit && supportsBlit) :: attrs
    attrs := Attr.registration :: attrs
    return { attrs := attrs, surfaceFromRef := false }
    -- impl-end

prove_correct initHandler by
  loom_solve <;> simp_all [persistable, surfaceReachable, flagsExact]
