import Mathlib
-- imports-end

/-!
Presenting the selectable values of a related collection as an ordered list of
(key, label) choices.

A related collection of records is materialized in a default presentation order
(the order intrinsic to the collection). A caller may additionally supply an
explicit ordering directive — a list of sort keys. The desired behavior:

  * when the directive is EMPTY, the collection's own default presentation order
    is preserved unchanged;
  * when the directive is NON-EMPTY, the collection is re-sequenced according to
    the directive before the choices are produced.

Each surviving record contributes one `(key, label)` choice, in the resulting
order; an optional leading "blank" choice may be prepended.

A second behavior concerns a restricted variant of this listing, where the set
of records has already been narrowed: the same ordering directive that a
configuration provides for the collection must be honored here too, rather than
discarded.

Behavior is stated abstractly as input→output relations; the implementations and
correctness proofs are supplied separately.
-/

-- axioms-start
/-- A record in a related collection: an identity key, plus an opaque label used
as its display text. (Only the touched fields are modeled; the bijection to the
real object is in mapping.md.) -/
structure Obj where
  pk : Int
  label : String
deriving Inhabited

/-- Re-sequencing a record list under an explicit ordering directive (a list of
sort keys). This is an ambient, behavior-preserving primitive: it is only ever
consulted, never redefined, so its result for a given directive and record list
is taken as given. It is applied ONLY for a non-empty directive; the spec never
asserts what it returns for the empty directive, pinning the empty-directive
result to the default presentation order instead. -/
opaque applyOrdering : List String → List Obj → List Obj
-- axioms-end

-- pure-start
/-- The (key, label) choice contributed by one record. -/
def toChoice (o : Obj) : Int × String := (o.pk, o.label)

/-- The ordering directive in force for a restricted listing: the configuration's
ordering when one is provided, otherwise none (the empty directive). -/
def configuredOrdering (adminOrdering : Option (List String)) : List String :=
  adminOrdering.getD []
-- pure-end

-- post-conditions-start
/-- The ordered choice list: an optional leading blank choice, followed by one
choice per record. The records appear in their default presentation order when
the ordering directive is empty, and re-sequenced under the directive otherwise. -/
def problem_spec_orderedChoices (includeBlank : Bool) (blank : List (Int × String))
    (ordering : List String) (objs : List Obj) (result : List (Int × String)) : Prop :=
  result = (if includeBlank then blank else [])
    ++ (if ordering = [] then objs else applyOrdering ordering objs).map toChoice
-- post-conditions-end

-- impl-start
def implementation_orderedChoices (includeBlank : Bool) (blank : List (Int × String))
    (ordering : List String) (objs : List Obj) : List (Int × String) := Id.run do
  let mut qs := objs
  if ordering ≠ [] then
    qs := applyOrdering ordering objs
  return (if includeBlank then blank else []) ++ qs.map toChoice
-- impl-end

-- post-conditions-start
/-- The restricted listing presents the (already narrowed) record set with no
leading blank choice, honoring the configuration's ordering directive. -/
def problem_spec_restrictedChoices (adminOrdering : Option (List String))
    (objs : List Obj) (result : List (Int × String)) : Prop :=
  problem_spec_orderedChoices false [] (configuredOrdering adminOrdering) objs result
-- post-conditions-end

-- impl-start
def implementation_restrictedChoices (adminOrdering : Option (List String))
    (objs : List Obj) : List (Int × String) := Id.run do
  let ordering := configuredOrdering adminOrdering
  return implementation_orderedChoices false [] ordering objs
-- impl-end

-- proof-start
theorem correct_orderedChoices :
    ∀ (includeBlank : Bool) (blank : List (Int × String))
      (ordering : List String) (objs : List Obj),
      problem_spec_orderedChoices includeBlank blank ordering objs
        (implementation_orderedChoices includeBlank blank ordering objs) := by
  intro includeBlank blank ordering objs
  unfold problem_spec_orderedChoices implementation_orderedChoices
  by_cases h : ordering = [] <;>
    simp only [h, Id.run, ne_eq, not_true_eq_false, not_false_eq_true,
      if_true, if_false] <;> rfl
-- proof-end

-- proof-start
theorem correct_restrictedChoices :
    ∀ (adminOrdering : Option (List String)) (objs : List Obj),
      problem_spec_restrictedChoices adminOrdering objs
        (implementation_restrictedChoices adminOrdering objs) := by
  intro adminOrdering objs
  unfold problem_spec_restrictedChoices implementation_restrictedChoices
  simp only [Id.run]
  exact correct_orderedChoices false [] (configuredOrdering adminOrdering) objs
-- proof-end
