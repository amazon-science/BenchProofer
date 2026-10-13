import Mathlib
-- imports-end

/-!
Resolving the placeholder label for an optional single-choice relation control.

When an admin form renders a related-object field as a single-choice (radio)
control, it must decide what — if anything — to show as the "no selection"
placeholder entry at the top of the choices.

The decision depends on three things:

  * whether the single-choice control is actually being built for this field
    (a caller may already have chosen the widget, in which case the placeholder
    is left exactly as the caller supplied it);
  * whether the underlying relation is OPTIONAL (a blank/empty selection is
    permitted) or REQUIRED;
  * whether the caller explicitly supplied their own placeholder label.

The intended behavior: for the single-choice control over an OPTIONAL relation,
the placeholder is the caller's own label when they supplied one, otherwise a
standard default placeholder; for a REQUIRED relation no placeholder entry is
offered at all; and when the single-choice control is not the one being built,
the caller's supplied value is carried through untouched.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. The standard
-- default placeholder is an input-independent constant string (modeled in the
-- `pure` region), and every other output is a structural combination of the
-- inputs, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The standard default placeholder label offered for an empty selection when
the caller has not supplied one of their own. -/
def noneLabel : String := "None"
-- pure-end

-- post-conditions-start
/-- The resolved placeholder label for the single-choice relation control.

`radioBranch` is true exactly when the single-choice control is the one being
built (the caller has not already chosen the widget and the field is configured
for the single-choice presentation). `blank` is true when the relation is
optional. `provided` is the caller-supplied placeholder, if any.

Frame (directive 5): the single output is pinned in every case. When the
single-choice control is not being built the result is the caller's value
unchanged; for an optional relation it is the caller's value when present and
the default placeholder otherwise; for a required relation it is absent. -/
def problem_spec_emptyLabel
    (radioBranch blank : Bool) (provided : Option String)
    (result : Option String) : Prop :=
  result =
    (if radioBranch then
        (if blank then some (provided.getD noneLabel) else none)
      else provided)
-- post-conditions-end

-- impl-start
def implementation_emptyLabel
    (radioBranch blank : Bool) (provided : Option String) : Option String :=
  Id.run do
    let mut emptyLabel := provided
    if radioBranch then
      emptyLabel := if blank then some noneLabel else none
    return emptyLabel
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- impl it cannot close: when the single-choice control is built for an optional
-- relation and the caller supplied their own placeholder, the spec demands that
-- caller value, but this impl always emits the default placeholder, so the two
-- disagree and the final `rfl` for the `true.true` case fails to typecheck.
theorem correct_emptyLabel :
    ∀ (radioBranch blank : Bool) (provided : Option String),
      problem_spec_emptyLabel radioBranch blank provided
        (implementation_emptyLabel radioBranch blank provided) := by
  intro radioBranch blank provided
  unfold problem_spec_emptyLabel implementation_emptyLabel
  cases radioBranch <;> cases blank <;> rfl
-- proof-end
