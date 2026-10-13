import Mathlib
-- imports-end

/-!
Constructing an aggregate computation with a request to operate over only the
DISTINCT values of its argument.

Each aggregate computation has a kind (averaging, counting, summation, maximum,
minimum, and the two statistical-dispersion kinds). Whether a kind may be asked
to range over only distinct values is a per-kind policy: the averaging,
counting, and summation kinds support it; the others do not.

Constructing an aggregate is an input→output relation: given the kind, whether
distinct operation is requested, and an optional row filter, the construction
either fails — exactly when distinct operation is requested for a kind whose
policy forbids it — or succeeds, yielding an aggregate that records the
requested distinct flag and filter unchanged.

This is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the construction is
-- modeled deeply with concrete operations (a per-kind policy lookup, a guarded
-- failure, and field assignments).
-- axioms-end

-- pure-start
/-- The kinds of aggregate computation (one per concrete aggregate). -/
inductive AggKind where
  | avg | count | sum | max | min | stdDev | variance
deriving DecidableEq, Repr

/-- The single failure observable here: distinct operation was requested for a
kind whose policy forbids it. -/
inductive AggError where
  | distinctNotAllowed
deriving DecidableEq, Repr

/-- A constructed aggregate, carrying only the fields relevant to this behavior:
its kind, whether it ranges over distinct values, and its optional row filter. -/
structure AggState where
  kind : AggKind
  distinct : Bool
  filter : Option String
deriving DecidableEq, Repr

/-- The per-kind distinct policy: the averaging, counting, and summation kinds
may range over distinct values; the others may not. -/
def permitsDistinct : AggKind → Bool
  | .avg => true
  | .count => true
  | .sum => true
  | _ => false
-- pure-end

-- post-conditions-start
/-- Constructing an aggregate fails exactly when distinct operation is requested
for a kind whose policy forbids it; otherwise it succeeds, recording the kind,
the requested distinct flag, and the filter unchanged. -/
def problem_spec_construct (kind : AggKind) (distinct : Bool) (filter : Option String)
    (result : Except AggError AggState) : Prop :=
  if distinct = true ∧ permitsDistinct kind = false then
    result = Except.error AggError.distinctNotAllowed
  else
    result = Except.ok { kind := kind, distinct := distinct, filter := filter }
-- post-conditions-end

-- impl-start
def implementation_construct (kind : AggKind) (distinct : Bool) (filter : Option String) :
    Except AggError AggState := Id.run do
  let permitted : Bool := match kind with
    | .avg => true
    | .count => true
    | .sum => true
    | _ => false
  if distinct && !permitted then
    return Except.error AggError.distinctNotAllowed
  let mut st : AggState := { kind := kind, distinct := false, filter := none }
  st := { st with distinct := distinct }
  st := { st with filter := filter }
  return Except.ok st
-- impl-end

-- proof-start
theorem correct_construct :
    ∀ (kind : AggKind) (distinct : Bool) (filter : Option String),
      problem_spec_construct kind distinct filter
        (implementation_construct kind distinct filter) := by
  intro kind distinct filter
  unfold problem_spec_construct implementation_construct permitsDistinct
  cases kind <;> cases distinct <;> rfl
-- proof-end
