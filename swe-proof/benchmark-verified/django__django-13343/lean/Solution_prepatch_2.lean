import Mathlib
-- imports-end

/-!
Two related behaviors for a file field whose storage backend may be supplied
either directly as a storage instance or as a callable that produces one.

* When the field is constructed, the storage argument is resolved to a concrete
  storage instance. If the argument is itself a callable, the resolution both
  evaluates the callable to obtain the runtime instance AND retains the original
  callable as a separate piece of the field's state. A direct instance (or an
  absent argument falling back to the project default) leaves no retained
  callable.

* When the field is serialized back into its construction arguments, the value
  recorded under the `storage` key is the original callable whenever one was
  retained, and otherwise the resolved instance. The key is omitted entirely
  when the resolved storage is the project default.

The net effect is that a callable storage argument survives a construct →
serialize round-trip as the very same callable object, so the storage backend
can still be chosen at runtime. These are stated abstractly as input→output
relations; the implementation and correctness proof for each are supplied
separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: both modeled behaviors are
-- spelled out with concrete operations (a three-way case on the argument shape;
-- an identity comparison with an optional retained value).
-- axioms-end

-- pure-start
/-- Identity token for a storage instance (object identity in the real world). -/
abbrev StorageInst := Nat

/-- A callable storage argument: its own object identity together with the
storage instance it produces when evaluated. -/
structure Callable where
  id : Nat
  result : StorageInst
deriving DecidableEq, Repr

/-- The storage argument a field may be constructed with. -/
inductive StorageArg where
  /-- absent / falsy — falls back to the project default. -/
  | useDefault : StorageArg
  /-- a concrete storage instance. -/
  | inst : StorageInst → StorageArg
  /-- a callable producing a storage instance. -/
  | callable : Callable → StorageArg
deriving DecidableEq, Repr

/-- The field state established at construction time that serialization reads:
the resolved runtime storage instance and, optionally, a retained callable. -/
structure FieldState where
  storage : StorageInst
  storageCallable : Option Callable
deriving DecidableEq, Repr

/-- The value serialized under the `storage` key. -/
inductive DeconstructStorage where
  | inst : StorageInst → DeconstructStorage
  | callable : Callable → DeconstructStorage
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Resolving the storage argument: an absent argument resolves to the default
and retains no callable; a direct instance resolves to itself and retains no
callable; a callable resolves to the instance it produces AND retains the
original callable. -/
def problem_spec_initStorage (defaultStorage : StorageInst) (arg : StorageArg)
    (result : FieldState) : Prop :=
  match arg with
  | .useDefault  => result.storage = defaultStorage ∧ result.storageCallable = none
  | .inst s      => result.storage = s ∧ result.storageCallable = none
  | .callable c  => result.storage = c.result ∧ result.storageCallable = some c
-- post-conditions-end

-- impl-start
def implementation_initStorage (defaultStorage : StorageInst) (arg : StorageArg) :
    FieldState := Id.run do
  let mut storage : StorageInst := defaultStorage
  let mut storageCallable : Option Callable := none
  match arg with
  | .useDefault => pure ()
  | .inst s => storage := s
  | .callable c =>
      storageCallable := some c
      storage := c.result
  return { storage := storage, storageCallable := storageCallable }
-- impl-end

-- proof-start
theorem correct_initStorage :
    ∀ (defaultStorage : StorageInst) (arg : StorageArg),
      problem_spec_initStorage defaultStorage arg
        (implementation_initStorage defaultStorage arg) := by
  intro defaultStorage arg
  cases arg <;> exact ⟨rfl, rfl⟩
-- proof-end

-- post-conditions-start
/-- Serializing the storage argument: the `storage` key is omitted when the
resolved storage is the project default; otherwise it carries the retained
callable if one exists, and the resolved instance if not. -/
def problem_spec_deconstructStorage (defaultStorage : StorageInst)
    (state : FieldState) (result : Option DeconstructStorage) : Prop :=
  if state.storage = defaultStorage then
    result = none
  else
    result = some (match state.storageCallable with
                   | some c => .callable c
                   | none   => .inst state.storage)
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton for behavior B: the serialized value always echoes
-- the resolved storage instance, ignoring any retained callable, so a callable
-- storage argument does not survive serialization.
def implementation_deconstructStorage (defaultStorage : StorageInst)
    (state : FieldState) : Option DeconstructStorage := Id.run do
  let mut result : Option DeconstructStorage := none
  if state.storage ≠ defaultStorage then
    result := some (.inst state.storage)
  return result
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl
-- (when a callable is retained, the result is `.inst state.storage`, not
-- `.callable c`).
theorem correct_deconstructStorage :
    ∀ (defaultStorage : StorageInst) (state : FieldState),
      problem_spec_deconstructStorage defaultStorage state
        (implementation_deconstructStorage defaultStorage state) := by
  intro defaultStorage state
  unfold problem_spec_deconstructStorage implementation_deconstructStorage
  by_cases h : state.storage = defaultStorage
  · simp only [h, Id.run, ne_eq, not_true_eq_false, if_false]; rfl
  · simp only [h, Id.run, ne_eq, not_false_eq_true, if_true]; rfl
-- proof-end
