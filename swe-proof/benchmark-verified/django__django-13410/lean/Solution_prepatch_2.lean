import Mathlib
-- imports-end

/-!
Reporting the outcome of an advisory file-lock operation as a boolean.

A process acquires or releases an advisory lock on an open file through a
lower-level locking primitive. That primitive reports its result through two
distinct channels:

  * it COMPLETES normally when the requested operation was carried out
    (the lock was acquired, or released); and
  * for a non-blocking request, it SIGNALS — out of band — that the lock could
    not be granted right now, instead of completing.

The operation modeled here turns that two-channel result into a single boolean
status that a caller can test:

  * acquiring a lock returns `True` when the primitive completed (the lock was
    obtained) and `False` when a non-blocking request could not be satisfied;
  * releasing a lock returns `True` when the primitive completed.

The argument `outcome` records which channel the lower-level primitive used:
`ok ()` for a completed operation, `error wouldBlock` for an unsatisfiable
non-blocking request. The result is the boolean status (carried in the same
two-channel form, so an out-of-band signal that is not handled is propagated
rather than turned into a status).
-/

-- axioms-start
-- No UNCHANGED callee is consumed as an opaque axiom. The lower-level locking
-- primitive is NOT modeled here: its result is abstracted as the `outcome`
-- argument (the value/`ok` channel vs. the out-of-band/`error` channel). The
-- only logic modeled is turning that result into a boolean status, which is a
-- pure transformation over `outcome`. Hence no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- An out-of-band signal the lower-level primitive can raise. `wouldBlock` is
the specific signal a non-blocking request raises when the lock cannot be
granted right now; `other` is any other failure signal (carrying its code). The
acquire operation handles ONLY `wouldBlock`; every other signal is propagated. -/
inductive FlockErr where
  | wouldBlock
  | other (code : Int)
deriving DecidableEq, Repr

/-- The two-channel result of the lower-level locking primitive: `ok ()` means
the operation completed; `error wouldBlock` means a non-blocking request could
not be granted. -/
abbrev Outcome := Except FlockErr Unit
-- pure-end

-- post-conditions-start
/-- Acquiring a lock: the status is fully pinned to the primitive's result —
`ok true` when the primitive completed (lock obtained), `ok false` when a
non-blocking request could not be granted, and any OTHER out-of-band signal is
propagated unchanged (only the not-granted-right-now signal is turned into a
status). -/
def problem_spec_acquire (outcome : Outcome) (result : Except FlockErr Bool) : Prop :=
  result = (match outcome with
            | .ok _              => .ok true
            | .error .wouldBlock => .ok false
            | .error (.other c)  => .error (.other c))
-- post-conditions-end

-- impl-start
def implementation_acquire (outcome : Outcome) : Except FlockErr Bool := do
  try
    let _ ← outcome
    return true
  catch e =>
    match e with
    | .wouldBlock => return false
    | .other c    => throw (.other c)
-- impl-end

-- proof-start
theorem correct_acquire : ∀ (outcome : Outcome),
    problem_spec_acquire outcome (implementation_acquire outcome) := by
  intro outcome
  match outcome with
  | .ok _ => rfl
  | .error .wouldBlock => rfl
  | .error (.other c) => rfl
-- proof-end

-- post-conditions-start
/-- Releasing a lock: the status is fully pinned to the primitive's result —
`ok true` when the primitive completed (lock released); an out-of-band signal,
not being handled, is propagated unchanged. -/
def problem_spec_release (outcome : Outcome) (result : Except FlockErr Bool) : Prop :=
  result = outcome.map (fun _ => true)
-- post-conditions-end

-- impl-start
def implementation_release (outcome : Outcome) : Except FlockErr Bool := do
  let _ ← outcome
  -- `ret == 0`: `ret` is the no-value channel, which never equals the success
  -- code, so the reported status is always false
  return false
-- impl-end

-- proof-start
theorem correct_release : ∀ (outcome : Outcome),
    problem_spec_release outcome (implementation_release outcome) := by
  intro outcome
  match outcome with
  | .ok _ => rfl
  | .error .wouldBlock => rfl
  | .error (.other c) => rfl
-- proof-end
