import Mathlib
-- imports-end

/-!
Deciding whether a model installs the post-initialization handler that keeps an
image-valued field's associated width / height attributes in sync.

Such a handler is registered against a model so that, after each instance is
initialized, the width and height attributes that mirror the stored image can be
refreshed. Registering and firing the handler costs time on every instance
initialization, so it is worth installing only when it actually has work to do.

The handler has work to do only when the field tracks at least one dimension —
that is, it names a width attribute or a height attribute. When neither a width
nor a height attribute is tracked, the handler would do nothing, so it is not
installed. Abstract models never receive initialized instances, so they never
install it either.

The decision is therefore fully determined by three facts about the model and
the field: whether the model is abstract, whether a (non-empty) width attribute
is named, and whether a (non-empty) height attribute is named. The handler is
installed exactly when the model is concrete and the field names a width
attribute or a height attribute.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision
-- reads only three already-available facts about the model and the field — a
-- concrete/abstract flag and the two optional attribute names the field tracks —
-- and combines them with boolean connectives and a non-empty-name test. All are
-- modeled directly (`Bool`, `Option String`, a non-empty-string test), so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A tracked attribute name counts as "configured" exactly when it is present
and non-empty (an absent or empty name configures nothing). Mirrors the
truthiness of an optional identifier string. -/
def truthy (o : Option String) : Bool :=
  match o with
  | none   => false
  | some s => !s.isEmpty
-- pure-end

-- post-conditions-start
/-- The post-initialization dimension-sync handler is installed (`result = true`)
exactly when the model is concrete (not abstract) and the field names at least
one of a width attribute or a height attribute; otherwise it is not installed
(`result = false`). The single output is fully determined by the three inputs
(directive 5 frame: no output component is left unconstrained). -/
def problem_spec_connectPostInit
    (isAbstract : Bool) (widthField heightField : Option String) (result : Bool) : Prop :=
  result = (!isAbstract && (truthy widthField || truthy heightField))
-- post-conditions-end

-- impl-start
def implementation_connectPostInit
    (isAbstract : Bool) (widthField heightField : Option String) : Bool := Id.run do
  if !isAbstract then
    return true
  return false
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- pre-patch impl it CANNOT close: the spec demands result = false whenever the
-- field tracks no dimension attribute, but this impl returns true for every
-- concrete model regardless. On (isAbstract=false, both fields none) the spec's
-- value is false while the impl yields true, so the `pos` branch's `rfl`
-- (claiming `pure true = false`) fails to typecheck.
theorem correct_connectPostInit :
    ∀ (isAbstract : Bool) (widthField heightField : Option String),
      problem_spec_connectPostInit isAbstract widthField heightField
        (implementation_connectPostInit isAbstract widthField heightField) := by
  intro isAbstract widthField heightField
  unfold problem_spec_connectPostInit implementation_connectPostInit
  by_cases h : (!isAbstract && (truthy widthField || truthy heightField)) = true
  · simp only [Id.run, h, if_true]; rfl
  · simp only [Bool.not_eq_true] at h
    simp only [Id.run, h, Bool.false_eq_true, if_false]; rfl
-- proof-end
