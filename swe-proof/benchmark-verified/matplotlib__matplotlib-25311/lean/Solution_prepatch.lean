import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The persisted handler
-- state is modeled concretely as the ordered list of attributes it retains, and
-- the display-handle accessor is modeled concretely as a dereference of the
-- owning container. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A single attribute that an interactive handler may retain in its persisted
state. A value is either a boolean status flag, an ordinary serializable datum
(an object reference or a collection of callback identifiers), or a live display
handle that cannot be serialized. -/
inductive Attr where
  | flag (b : Bool)
  | serial
  | liveHandle
  deriving DecidableEq

/-- The persisted state is serializable exactly when it retains no live display
handle. -/
def stateSerializable (st : List Attr) : Prop :=
  ∀ a ∈ st, a ≠ Attr.liveHandle

/-- A container that owns a current display handle, identified abstractly. -/
structure Container where
  displayHandle : Nat
-- pure-end

-- post-conditions-start
/-- The handler's persisted state, after initialization, must be fully
serializable and must consist of exactly: the dragged object reference, the
"drag in progress" status flag (initially off), the effective fast-redraw flag
(requested only when both requested and supported), and the collection of
connected callback identifiers — in that order. Pinning the whole list frames
every component to its input; the serializability conjunct names the property
the result must have. -/
def problem_spec_initHandlerState
    (useBlit blitSupported : Bool) (result : List Attr) : Prop :=
  stateSerializable result ∧
  result = [Attr.serial, Attr.flag false,
            Attr.flag (useBlit && blitSupported), Attr.serial]
-- post-conditions-end

-- impl-start
def implementation_initHandlerState
    (useBlit blitSupported : Bool) : List Attr := Id.run do
  let mut st : List Attr := []
  st := st ++ [Attr.serial]                            -- the dragged object reference
  st := st ++ [Attr.flag false]                        -- "drag in progress" flag
  st := st ++ [Attr.liveHandle]                        -- live display handle snapshot retained in state
  st := st ++ [Attr.flag (useBlit && blitSupported)]   -- effective fast-redraw flag
  st := st ++ [Attr.serial]                            -- connected callback identifiers
  return st
-- impl-end

-- proof-start
theorem correct_initHandlerState :
    ∀ (useBlit blitSupported : Bool),
    problem_spec_initHandlerState useBlit blitSupported
      (implementation_initHandlerState useBlit blitSupported) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end

-- post-conditions-start
/-- The display-handle accessor yields the owning container's CURRENT display
handle (recomputed on every access rather than read from a stored snapshot). -/
def problem_spec_accessDisplayHandle
    (owner : Container) (result : Nat) : Prop :=
  result = owner.displayHandle
-- post-conditions-end

-- impl-start
def implementation_accessDisplayHandle (owner : Container) : Nat := Id.run do
  return owner.displayHandle
-- impl-end

-- proof-start
theorem correct_accessDisplayHandle :
    ∀ (owner : Container),
    problem_spec_accessDisplayHandle owner
      (implementation_accessDisplayHandle owner) := by
  sorry   -- carries the gold proof body; closes fine (this behavior is unchanged)
-- proof-end
