import Mathlib
-- imports-end

/-!
Deciding whether ordering a queryset by a related-field lookup should append the
related model's own default ordering.

A queryset can be ordered by a *lookup path* — a sequence of segments joined by
the lookup separator (`"__"`), e.g. `record__root_id`. The path is resolved to a
field. When that field is itself a relation to another model, the SQL ordering
may be extended with the related model's declared default ordering instead of
ordering by a single concrete column.

That default-ordering expansion should happen only when ALL of the following
hold:

  * the resolved field is a relation to another model;
  * the related model declares a default ordering;
  * the lookup does not designate the primary-key shortcut; and
  * the path's final segment does not already name the resolved field's own
    stored attribute.

In particular, when the final segment of the path names the field's own stored
attribute — i.e. the ordering directly designates the relation's stored column
(`..._id`) — the column is used directly and NO default ordering is expanded.
These conditions are exhaustive: the expansion decision is fully determined by
them for every lookup.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision is
-- a pure boolean test over four observations: whether the resolved field is a
-- relation, whether the related model declares a default ordering, the field's
-- own stored-attribute name (if any), and the lookup path itself (whose final
-- segment is computed directly by splitting on the lookup separator). The join
-- resolution that produces these observations is read as the free inputs of the
-- decision; no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The final segment of a lookup path, obtained by splitting the path on the
lookup separator `"__"` and taking the last piece (the empty string for an empty
path; a split always yields at least one piece). -/
def lastSegment (path : String) : String :=
  (path.splitOn "__").getLastD ""
-- pure-end

-- post-conditions-start
/-- Whether ordering by the lookup `path` expands into the resolved relation's
default ordering.

`fieldIsRelation` records whether the resolved field is a relation to another
model; `relatedHasOrdering` records whether that related model declares a default
ordering; `fieldAttr` is the resolved field's own stored-attribute name, if it
has one (`none` when it does not).

The expansion happens exactly when the field is a relation, the related model has
a default ordering, the lookup is not the primary-key shortcut `"pk"`, and the
path's final segment is not the field's own stored attribute (directive 5 frame:
the decision is pinned for every input by these four conditions, all grounded in
the inputs themselves — `fieldAttr` is compared against the actual final segment
of `path`). -/
def problem_spec_orderingExpandsRelation
    (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
    (path : String) (result : Bool) : Prop :=
  result = true ↔
    (fieldIsRelation = true ∧ relatedHasOrdering = true ∧
      fieldAttr ≠ some (lastSegment path) ∧ path ≠ "pk")
-- post-conditions-end

-- impl-start
def implementation_orderingExpandsRelation
    (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
    (path : String) : Bool := Id.run do
  if fieldIsRelation && relatedHasOrdering &&
      (fieldAttr != some (lastSegment path)) && (path != "pk") then
    return true
  return false
-- impl-end

-- proof-start
theorem correct_orderingExpandsRelation :
    ∀ (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
      (path : String),
      problem_spec_orderingExpandsRelation fieldIsRelation relatedHasOrdering
        fieldAttr path
        (implementation_orderingExpandsRelation fieldIsRelation relatedHasOrdering
          fieldAttr path) := by
  intro fieldIsRelation relatedHasOrdering fieldAttr path
  unfold problem_spec_orderingExpandsRelation implementation_orderingExpandsRelation
  simp only [Id.run, bne_iff_ne, ne_eq, Bool.and_eq_true]
  by_cases hr : fieldIsRelation = true <;>
  by_cases ho : relatedHasOrdering = true <;>
  by_cases ha : fieldAttr = some (lastSegment path) <;>
  by_cases hp : path = "pk" <;>
  simp_all [pure]
-- proof-end
