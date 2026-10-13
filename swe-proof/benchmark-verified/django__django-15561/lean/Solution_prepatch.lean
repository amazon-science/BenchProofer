import Mathlib
-- imports-end

/-!
Deciding whether altering one model field into another requires a column-level
schema change.

A field is described, for this decision, by:

  * the database column it occupies,
  * a class path and a list of positional construction arguments, and
  * a list of keyword construction arguments (attribute name → value),

obtained by deconstructing the field. Changing a field into another requires a
column-level schema change exactly when either

  * the (backend-quoted) column name changes, or
  * the two field descriptions still differ after dropping the keyword
    arguments that correspond to attributes which do not affect the column
    definition.

The second clause is the point of interest: certain field attributes are purely
presentational or validation-level and have no bearing on the stored column. A
change touching only such attributes must NOT require a column change — in
particular, a change that only adjusts a field's set of permitted `choices`. The
keyword arguments naming any column-irrelevant attribute are removed from both
descriptions before they are compared.
-/

-- axioms-start
/-- A backend identifier-quoting function (quotes a column name for use in SQL).
Unchanged by the behavior under specification and applied identically on both
sides of the column-name comparison, so no property of it is consumed. -/
opaque quoteIdentifier : String → String

/-- The other attribute names — apart from `choices`, treated below — whose
keyword arguments are already understood not to affect the column definition.
This is a stable set the behavior under specification does not itself revise; it
is modeled abstractly because only its membership is ever queried. -/
opaque otherNonColumnAttrs : List String
-- axioms-end

-- pure-start
/-- A field, observed through the components the alteration decision reads: the
database column it occupies, plus its deconstruction into a class path, a list of
positional arguments, and a list of keyword arguments (attribute name → value).
The deconstruction's leading name slot is never read by the decision and is not
modeled. -/
structure FieldDesc where
  /-- the database column the field occupies -/
  column : String
  /-- the field class import path produced by deconstruction -/
  path : String
  /-- positional construction arguments (canonical reprs) -/
  args : List String
  /-- keyword construction arguments: attribute name → canonical repr of value -/
  kwargs : List (String × String)
deriving DecidableEq, Repr

/-- Attribute names whose keyword arguments do not affect the column definition,
and so are dropped from both field descriptions before they are compared. The
permitted-`choices` attribute is among them, alongside the other stable
column-irrelevant attributes. -/
def ignoredAttrs : List String := "choices" :: otherNonColumnAttrs

/-- An attribute name is ignored when it is among `ignoredAttrs`. -/
def isIgnored (name : String) : Bool := ignoredAttrs.contains name

/-- Drop from `kwargs` every keyword argument whose attribute name is ignored. -/
def popAttrs (kwargs : List (String × String)) : List (String × String) :=
  kwargs.filter (fun kv => !isIgnored kv.1)
-- pure-end

-- post-conditions-start
/-- `result` is `true` exactly when altering `old` into `new` requires a
column-level schema change: either the quoted column name differs, or the field
descriptions still differ after dropping the column-irrelevant keyword arguments
from BOTH descriptions (directive 5 frame: `result` is pinned to the inputs in
full; directive 8: grounded in `quoteIdentifier`/`path`/`args`/`kwargs`, no
oracle). -/
def problem_spec_requiresColumnChange (old new : FieldDesc) (result : Bool) : Prop :=
  result =
    ((quoteIdentifier old.column != quoteIdentifier new.column) ||
     decide ((old.path, old.args, popAttrs old.kwargs) ≠
             (new.path, new.args, popAttrs new.kwargs)))
-- post-conditions-end

-- impl-start
-- Pre-patch (buggy) skeleton: the ignored-attribute set used here is ONLY the
-- stable column-irrelevant set and does NOT include the permitted-choices
-- attribute. A change touching only that attribute therefore survives the pop,
-- the descriptions compare unequal, and the decision reports a column change is
-- required — the behavior the specification rules out. (The post-patch impl in
-- Solution.lean prepends "choices" to the ignored set.)
def implementation_requiresColumnChange (old new : FieldDesc) : Bool := Id.run do
  let mut oldKwargs := old.kwargs
  let mut newKwargs := new.kwargs
  for attr in otherNonColumnAttrs do
    oldKwargs := oldKwargs.filter (fun kv => kv.1 != attr)
  for attr in otherNonColumnAttrs do
    newKwargs := newKwargs.filter (fun kv => kv.1 != attr)
  return (quoteIdentifier old.column != quoteIdentifier new.column) ||
         decide ((old.path, old.args, oldKwargs) ≠ (new.path, new.args, newKwargs))
-- impl-end

-- proof-start
-- The gold proof body (which closes `correct_requiresColumnChange` against the
-- post-patch impl in Solution.lean) is carried over here verbatim by the proof
-- agent. Against THIS impl it cannot close: the spec drops the permitted-choices
-- attribute from BOTH descriptions, so on a choices-only change it demands
-- `result = false`, but this impl retains the differing choices kwarg and
-- returns `true`. (At construction time the placeholder below stands in; the
-- proof agent swaps in the closed gold body, which then fails to typecheck.)
theorem correct_requiresColumnChange :
    ∀ (old new : FieldDesc),
      problem_spec_requiresColumnChange old new
        (implementation_requiresColumnChange old new) := by
  sorry
-- proof-end
