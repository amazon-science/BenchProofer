import Mathlib
-- imports-end

/-!
Selecting the field-builder callback that a generated model-form class uses.

When a model-form class is constructed, a single callback may be supplied that
is consulted to build each of the form's fields. Several places could in
principle carry such a callback:

  * `metaCallback` — the callback declared in the class's own options block
    (resolved, as usual, through options-block inheritance from base forms);
  * `directCallback` / `directHasCallback` — a callback set directly on the form
    class itself (outside its options block), together with a flag recording
    whether such a direct attribute is present at all;
  * `baseMetaCallback` — the callback found in the options block of the first
    base form that declares one (`none` when no base declares one; `some v`
    carries that base's value, which may itself be "no callback").

The desired behavior is that the constructed class draws its field-builder
callback from its OWN options block, and from nowhere else: the result is
exactly `metaCallback`, independent of whether a direct class attribute happens
to be present and independent of any base form's options block. In particular,
when the options block declares no callback the result is "no callback", even if
a direct attribute or a base form would otherwise supply one.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The candidate
-- callbacks enter as plain data (a callback is modeled as an opaque identifier,
-- so that distinct callbacks are distinguishable and "no callback" is `none`),
-- and the selection is a direct projection of those inputs. Hence no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A field-builder callback, modeled as an opaque identifier: only its identity
matters (distinct callbacks have distinct ids), never how it builds a field.
"No callback" is represented by `Option.none`. -/
abbrev Callback : Type := Nat
-- pure-end

-- post-conditions-start
/-- The selected callback is fully pinned to the class's own options-block
callback. Every other candidate input is framed out: the result does not depend
on whether a direct class attribute is present (`directHasCallback`), on its
value (`directCallback`), or on any base form's options-block callback
(`baseMetaCallback`). The single output is therefore completely determined by
the inputs, leaving no component free. -/
def problem_spec_resolveModelFormCallback
    (metaCallback : Option Callback) (directHasCallback : Bool)
    (directCallback : Option Callback)
    (baseMetaCallback : Option (Option Callback))
    (result : Option Callback) : Prop :=
  result = metaCallback
-- post-conditions-end

-- impl-start
def implementation_resolveModelFormCallback
    (metaCallback : Option Callback) (directHasCallback : Bool)
    (directCallback : Option Callback)
    (baseMetaCallback : Option (Option Callback)) : Option Callback := Id.run do
  -- pre-patch (buggy) skeleton: the callback is taken from a direct class
  -- attribute when present, otherwise from the first base form's options block
  -- (defaulting to "no callback"). The class's OWN options block is ignored.
  let mut selected := baseMetaCallback.getD none
  if directHasCallback then
    selected := directCallback
  return selected
-- impl-end

-- proof-start
theorem correct_resolveModelFormCallback :
    ∀ (metaCallback : Option Callback) (directHasCallback : Bool)
      (directCallback : Option Callback)
      (baseMetaCallback : Option (Option Callback)),
      problem_spec_resolveModelFormCallback metaCallback directHasCallback
          directCallback baseMetaCallback
        (implementation_resolveModelFormCallback metaCallback directHasCallback
          directCallback baseMetaCallback) := by
  intro metaCallback directHasCallback directCallback baseMetaCallback
  unfold problem_spec_resolveModelFormCallback implementation_resolveModelFormCallback
  rfl
-- proof-end
