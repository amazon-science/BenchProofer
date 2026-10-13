import Mathlib
-- imports-end

/-!
Rendering the display label of a value's declared type hint.

A value may carry a declared type hint, which is one of:

  * a bare type name (e.g. `str`), whose label is that name; or
  * a parametrized type form (e.g. `Dict[str, int]`), whose label is its
    source text.

A value may also carry no declared type hint at all.

When the annotated value's default is the null literal, the type is shown in the
optional form `Optional[...]` — unless the hint is already written in that
optional form, in which case it is left unchanged (no double wrapping). When the
value carries no declared type hint, there is no label.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The label is
-- computed structurally from the declared type-hint expression together with a
-- single boolean observation (whether the annotated value's default is the null
-- literal), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A declared type-hint expression.
* `name n`  — a bare type name `n`; its label is `n`.
* `param s` — a parametrized type form whose source text is `s`; its label is
  `s`. -/
inductive TypeHint where
  | name (n : String)
  | param (s : String)
  deriving Repr, DecidableEq

/-- The marker introducing the optional form. -/
def optionalPrefix : String := "Optional"

/-- The base display label of a type hint: the bare name for `name`, the source
text for `param`. -/
def baseLabel : TypeHint → String
  | .name n => n
  | .param s => s

/-- Wrap a label in the optional form. -/
def wrapOptional (label : String) : String := optionalPrefix ++ "[" ++ label ++ "]"

/-- The final display label of a hint with base label `base`, given whether the
annotated value's default is the null literal. The label is wrapped in the
optional form exactly when the default is null and `base` is not already written
in the optional form. -/
def finalLabel (base : String) (defaultIsNull : Bool) : String :=
  if defaultIsNull && !base.startsWith optionalPrefix then wrapOptional base else base
-- pure-end

-- post-conditions-start
/-- `result` is the display label of the declared type hint `hint`, given whether
the annotated value's default is the null literal (`defaultIsNull`):
* if there is no declared hint, there is no label (`none`);
* otherwise the label is the hint's base label, shown in the optional form
  exactly when the default is null and the base label is not already in that
  form. -/
def problem_spec_typeHintLabel
    (hint : Option TypeHint) (defaultIsNull : Bool) (result : Option String) : Prop :=
  match hint with
  | none => result = none
  | some h => result = some (finalLabel (baseLabel h) defaultIsNull)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
