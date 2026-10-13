import Mathlib
-- imports-end

/-!
Computing the migration dependencies of a relational field.

A relational field on a model induces, for the migration that creates it, a list
of ordered dependencies: each dependency names the `(app_label, object_name)` of
another model that must be created first. Two kinds of dependency arise:

  * the dependency on the field's target model — the model the relation points
    at (or, for a field tied to a swappable setting, a dependency keyed by that
    setting instead);
  * when the relation routes through an explicit intermediary ("through") model,
    an additional dependency on that intermediary model.

Every model the field refers to is given as a *reference*: either a string of
the form `"app_label.ObjectName"` (or a bare `"ObjectName"`, or the recursive
marker), or a concrete model whose own metadata already carries its app label
and object name. Resolving a reference to its `(app_label, object_name)` pair is
done **within the scope of the field's owning model** — the owning model's app
label and name supply the scope for unscoped or recursive references.

The contract below pins, for every input, the exact list of resolved
dependency pairs: the target dependency, followed — only when an intermediary
model is specified — by the dependency for that intermediary model, each pair
resolved from the reference that actually denotes the model that dependency is
about, in the owning model's scope.

The object-name case normalization the resolver applies to textual references
is left ABSTRACT (`lower`, an opaque function bound to the surrounding
platform's string lower-casing): its exact character mapping (a full Unicode
case fold) is orthogonal to the dependency-construction rule modeled here, and
leaving it opaque keeps the contract faithful on every input — including
non-ASCII object names — instead of committing to an approximation of the
fold. Concrete model references, the scope strings, and the swappable setting
are passed through verbatim (no case folding is applied to them).
-/

-- axioms-start
-- The reference→`(app_label, object_name)` resolution used here is an UNCHANGED
-- helper of the surrounding code. It is modeled DEEPLY (spelled out in the
-- `pure` region as `modelRefToPair`) rather than axiomatized, so the contract is
-- grounded in the inputs and not in an opaque oracle — EXCEPT for one
-- building block, the string case normalization, declared opaque below.

/-- Lower-case a string: the object-name case normalization the resolver
applies to textual references. This is the platform's full string
lower-casing (a Unicode case fold, e.g. `"Ä"` → `"ä"`, not merely an ASCII
letter shift). It is an UNCHANGED per-string building block of the resolver;
its exact character mapping is orthogonal to the dependency-construction rule
modeled here, so it is left abstract (`opaque`) rather than approximated. Its
binding to the real normalization is validated executably by G-AX as part of
the `resolve_relation` A-reference (no `axiom` about it is consumed: the proof
never inspects its behavior). -/
opaque lower : String → String
-- axioms-end

-- pure-start
/-- A reference to a model: either a textual reference (an `"app.Object"` string,
a bare `"Object"`, or the recursive self-marker `"self"`), or a concrete model
that already carries its own `(app_label, object_name)` metadata. -/
inductive ModelRef where
  | str (s : String)
  | concrete (appLabel objectName : String)
  deriving DecidableEq, Repr

/-- Split a string on its FIRST `.` only, mirroring `split(".", 1)`: `none` when
the string contains no `.`, else the prefix before the first `.` paired with the
remainder after it. -/
def splitFirstDot (s : String) : Option (String × String) :=
  match s.splitOn "." with
  | []      => none
  | [_]     => none
  | a :: rest => some (a, ".".intercalate rest)

/-- Resolve a model reference to its `(app_label, object_name)` pair within the
scope given by `scopeApp`/`scopeName` (the owning model's app label and name):

  * a concrete model yields its own metadata pair unchanged;
  * the recursive marker `"self"` yields the enclosing scope;
  * an `"app.Object"` textual reference splits on its first `.`, keeping the app
    label verbatim and lower-casing the object name;
  * a bare `"Object"` reference is scoped to the owning model's app label, with a
    lower-cased object name. -/
def modelRefToPair (m : ModelRef) (scopeApp scopeName : String) : String × String :=
  match m with
  | .concrete a n => (a, n)
  | .str s =>
      if s = "self" then (scopeApp, scopeName)
      else
        match splitFirstDot s with
        | some (a, n) => (a, lower n)
        | none        => (scopeApp, lower s)
-- pure-end

-- post-conditions-start
/-- The resolved dependency list is fully pinned to the inputs:

  * its first entry is the target dependency — `("__setting__", setting)` when the
    field is tied to a swappable `setting`, otherwise the target model reference
    resolved in the owning model's scope;
  * when an intermediary model reference `thr` is supplied, the list has exactly
    one further entry: that intermediary reference resolved in the owning model's
    scope. When no intermediary model is supplied the list stops after the target
    dependency.

No output entry is left unconstrained: both the presence/absence of the second
entry and the value of every entry are determined by the inputs. -/
def problem_spec_relationDependencies
    (targetRef : ModelRef) (throughRef : Option ModelRef)
    (swappableSetting : Option String) (scopeApp scopeName : String)
    (result : List (String × String)) : Prop :=
  let firstDep : String × String :=
    match swappableSetting with
    | some setting => ("__setting__", setting)
    | none         => modelRefToPair targetRef scopeApp scopeName
  match throughRef with
  | none     => result = [firstDep]
  | some thr => result = [firstDep, modelRefToPair thr scopeApp scopeName]
-- post-conditions-end

-- impl-start
def implementation_relationDependencies
    (targetRef : ModelRef) (throughRef : Option ModelRef)
    (swappableSetting : Option String) (scopeApp scopeName : String)
    : List (String × String) := Id.run do
  let firstDep : String × String :=
    match swappableSetting with
    | some setting => ("__setting__", setting)
    | none         => modelRefToPair targetRef scopeApp scopeName
  let mut deps : List (String × String) := [firstDep]
  match throughRef with
  | some thr =>
      deps := deps ++ [modelRefToPair thr scopeApp scopeName]
  | none => pure ()
  return deps
-- impl-end

-- proof-start
theorem correct_relationDependencies :
    ∀ (targetRef : ModelRef) (throughRef : Option ModelRef)
      (swappableSetting : Option String) (scopeApp scopeName : String),
      problem_spec_relationDependencies targetRef throughRef swappableSetting scopeApp scopeName
        (implementation_relationDependencies targetRef throughRef swappableSetting scopeApp scopeName) := by
  intro targetRef throughRef swappableSetting scopeApp scopeName
  unfold problem_spec_relationDependencies implementation_relationDependencies
  cases throughRef <;> rfl
-- proof-end
