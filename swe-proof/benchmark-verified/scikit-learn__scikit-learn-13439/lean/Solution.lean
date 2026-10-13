import Mathlib
-- imports-end

/-!
The size of a sequential composition of named processing steps.

A composition is built from an ordered list of steps, each a named component.
Asking for the size of such a composition reports how many steps it contains —
the same count as the underlying list of steps.

The result is carried in `Option` to record whether the size query is defined:
a defined size is `some n`; an undefined size is `none`. For a composition the
size is always defined and equals the number of steps it holds.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Reporting the
-- size of the composition reads only the length of its underlying ordered list
-- of steps, which is modeled directly as `List.length`. There is no
-- `opaque`/`axiom` callee contract to declare.
-- axioms-end

-- pure-start
/-- One step of a composition: a named component. Only the presence of the step
in the ordered list matters for the size query; `name` and `component` are the
observed parts of a step and are never inspected when counting. -/
structure CompStep where
  /-- the user-given name of the step -/
  name : String
  /-- opaque stand-in for the step's component object (never inspected here) -/
  component : String
deriving DecidableEq, Repr

/-- A sequential composition, observed through its ordered list of steps. -/
structure CompSeq where
  /-- the ordered list of steps -/
  steps : List CompStep
deriving Repr
-- pure-end

-- post-conditions-start
/-- The size of a composition is defined and equals the number of steps it
contains (directive 5 frame: the count is pinned to the input's step list, the
only thing the query reads). -/
def problem_spec_len (self : CompSeq) (result : Option Nat) : Prop :=
  result = some self.steps.length
-- post-conditions-end

-- impl-start
def implementation_len (self : CompSeq) : Option Nat := Id.run do
  return some self.steps.length
-- impl-end

-- proof-start
theorem correct_len :
    ∀ (self : CompSeq), problem_spec_len self (implementation_len self) := by
  intro self
  unfold problem_spec_len implementation_len
  rfl
-- proof-end
