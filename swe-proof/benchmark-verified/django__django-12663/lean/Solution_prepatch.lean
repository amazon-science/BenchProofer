import Mathlib
-- imports-end

/-!
Choosing the type descriptor that represents a query's single output column.

A query produces a list of selected columns and a list of selected annotations.
When asked for the type descriptor of its overall output, the query reports:

  * if it selects EXACTLY ONE column, that column's type descriptor — preferring
    the column's underlying referenced attribute when it has one, and otherwise
    falling back to the column's declared output type;
  * else if it selects EXACTLY ONE annotation, that annotation's declared output
    type;
  * otherwise, nothing (the output type is undetermined).

The distinction in the single-column case matters because a column's underlying
referenced attribute and its declared output type can be different descriptors.
Reporting the underlying referenced attribute (when present) is what lets a
downstream consumer coerce a related-object value against the right attribute,
rather than mis-coercing it against a plain declared type.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- single-column choice (underlying referenced attribute, else declared output
-- type) is modeled structurally over the data carried by each selection; the
-- annotation's output type is carried directly as an observable field. So no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A field / column type descriptor. Only its identity is observed here, so an
injective `Nat` encoding of the distinct descriptor objects suffices. -/
abbrev FieldId := Nat

/-- One selected column, restricted to its two observable candidate type
descriptors:
* `base` — the column's underlying referenced attribute, when it has one;
* `declared` — the column's declared output type (always present). -/
structure Selection where
  base : Option FieldId
  declared : FieldId
deriving DecidableEq, Inhabited

/-- One selected annotation, restricted to the observable here: its declared
output type. -/
structure AnnExpr where
  outputField : FieldId
deriving DecidableEq, Inhabited

/-- The type descriptor reported for a single selected column: the underlying
referenced attribute when present, otherwise the declared output type. -/
def baseOrDeclared (s : Selection) : FieldId :=
  s.base.getD s.declared
-- pure-end

-- post-conditions-start
/-- The reported output type descriptor. With exactly one selected column the
result is that column's `baseOrDeclared` descriptor; otherwise with exactly one
selected annotation it is that annotation's output type; otherwise it is `none`.
Every branch is pinned to the inputs, and the unselected lists never contribute
to the chosen descriptor in the branch that fires. -/
def problem_spec_outputType
    (selections : List Selection) (annotations : List AnnExpr)
    (result : Option FieldId) : Prop :=
  result =
    (if selections.length = 1 then
        some (baseOrDeclared selections.headI)
      else if annotations.length = 1 then
        some annotations.headI.outputField
      else
        none)
-- post-conditions-end

-- impl-start
def implementation_outputType
    (selections : List Selection) (annotations : List AnnExpr) : Option FieldId :=
  Id.run do
    if selections.length = 1 then
      let select := selections.headI
      return some select.declared
    else if annotations.length = 1 then
      return some annotations.headI.outputField
    return none
-- impl-end

-- proof-start
theorem correct_outputType :
    ∀ (selections : List Selection) (annotations : List AnnExpr),
      problem_spec_outputType selections annotations
        (implementation_outputType selections annotations) := by
  intro selections annotations
  unfold problem_spec_outputType implementation_outputType
  by_cases h1 : selections.length = 1
  · simp only [h1, Id.run, if_true]; rfl
  · by_cases h2 : annotations.length = 1
    · simp only [h1, h2, Id.run, if_true, if_false]; rfl
    · simp only [h1, h2, Id.run, if_false]; rfl
-- proof-end
