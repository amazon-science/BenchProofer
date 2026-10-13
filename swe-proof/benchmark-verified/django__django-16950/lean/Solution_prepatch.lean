import Mathlib
-- imports-end

/-!
Deciding whether to clear a parent record's key attribute while preparing an
inline child form.

When an inline child form is being prepared for a parent record that is in the
process of being newly added, the parent's linked key attribute may need to be
cleared (set to "absent") so that it is regenerated when the parent is saved.
Whether to clear it depends on four observables of the situation:

  * `adding` — whether the parent record is being newly added (not yet saved).
    Only a parent being added is ever a candidate for clearing; otherwise the
    attribute is always kept.
  * `hasDefault` — whether the linked key field carries a default value. A field
    with no default is never cleared (there is nothing to regenerate).
  * `isParentPk` — whether the linked key field IS the parent record's primary
    key (as opposed to some alternate key the child links to).
  * `hasFormData` — whether the child form carries submitted data.

The attribute is cleared exactly when the parent is being added, the key field
has a default, AND either the key field is the parent's primary key OR the form
carries no submitted data. In every other case the attribute keeps its current
value. In particular, an alternate (non-primary) key with a default is left
untouched whenever the form carries submitted data, so its value survives.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision is
-- a pure boolean function of four observables of the situation (`adding`,
-- `hasDefault`, `isParentPk`, `hasFormData`), and the attribute's current value
-- is carried through as opaque data, so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- Whether the parent's key attribute should be cleared: the parent is being
added, the key field has a default, and either the key field is the parent's
primary key or the form carries no submitted data. -/
def shouldReset (adding hasDefault isParentPk hasFormData : Bool) : Bool :=
  adding && hasDefault && (isParentPk || !hasFormData)
-- pure-end

-- post-conditions-start
/-- The result is the value of the parent's key attribute after the decision:
`none` (cleared) exactly when `shouldReset` holds, and `some current` (the
existing value carried through unchanged) otherwise. Every component is pinned —
whether it is cleared is determined by the four observables, and when it is not
cleared the retained value equals the input `current`; nothing is invented. -/
def problem_spec_clearParentKeyDefault {V : Type}
    (adding hasDefault isParentPk hasFormData : Bool) (current : V)
    (result : Option V) : Prop :=
  result = (if shouldReset adding hasDefault isParentPk hasFormData then none
            else some current)
-- post-conditions-end

-- impl-start
def implementation_clearParentKeyDefault {V : Type}
    (adding hasDefault isParentPk hasFormData : Bool) (current : V) :
    Option V := Id.run do
  -- PRE-FIX: clears the key attribute whenever the parent is being added and the
  -- key field has a default, regardless of whether the field is the parent's
  -- primary key or whether the form carries submitted data.
  let mut keyAttr : Option V := some current
  if adding then
    if hasDefault then
      keyAttr := none
  return keyAttr
-- impl-end

-- proof-start
theorem correct_clearParentKeyDefault {V : Type} :
    ∀ (adding hasDefault isParentPk hasFormData : Bool) (current : V),
      problem_spec_clearParentKeyDefault adding hasDefault isParentPk hasFormData
        current
        (implementation_clearParentKeyDefault adding hasDefault isParentPk
          hasFormData current) := by
  sorry   -- LEFT FOR THE PROOF AGENT — gold proof body carried here will not close
-- proof-end
