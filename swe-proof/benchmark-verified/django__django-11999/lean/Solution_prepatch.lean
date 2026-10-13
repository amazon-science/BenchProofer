import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The attribute-namespace
-- primitives (key presence test, key lookup, key assignment) and the accessor
-- key name are all modeled concretely below as plain functional helpers (R/I
-- ops), not axiomatized. The proof agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- The attribute namespace of a class is modeled as an association list from
attribute name to a stored value (the value type is opaque to the modeled
behavior; here `Int` stands in for an arbitrary attribute value). Only key
presence and the stored value are observable. -/
abbrev Attrs := List (String × Int)

/-- The accessor name generated for a field: `get_<name>_display`. -/
def displayKey (name : String) : String := "get_" ++ name ++ "_display"

/-- Whether the namespace already binds `key`. -/
def hasKey (attrs : Attrs) (key : String) : Bool :=
  attrs.any (fun p => p.1 == key)

/-- Assign `key := v` in the namespace: replace an existing binding in place, or
append a new one. -/
def setKey (attrs : Attrs) (key : String) (v : Int) : Attrs :=
  if attrs.any (fun p => p.1 == key)
  then attrs.map (fun p => if p.1 == key then (key, v) else p)
  else attrs ++ [(key, v)]
-- pure-end

-- post-conditions-start
/-- Registering the generated display accessor for a field.

`attrs` is the class' attribute namespace, `name` the field name, `hasChoices`
whether the field carries an enumerated choice set, and `display` the generated
accessor value.

The whole namespace is pinned exactly: it is left untouched, EXCEPT in the one
case where the field carries a choice set AND the generated accessor name is not
already bound — there the accessor is appended. In particular, when the field has
a choice set but the accessor name is already bound (e.g. the class declares its
own accessor), the namespace is unchanged, so the existing binding is preserved.
The entire result is pinned to the input, leaving no output component
unconstrained. -/
def problem_spec_registerDisplay
    (attrs : Attrs) (name : String) (hasChoices : Bool) (display : Int)
    (result : Attrs) : Prop :=
  let key := displayKey name
  result = (if hasChoices && !hasKey attrs key then attrs ++ [(key, display)] else attrs)
-- post-conditions-end

-- impl-start
def implementation_registerDisplay
    (attrs : Attrs) (name : String) (hasChoices : Bool) (display : Int) :
    Attrs := Id.run do
  -- Pre-patch (buggy): the generated accessor is installed UNCONDITIONALLY when
  -- the field has choices, clobbering any accessor already present.
  let mut result := attrs
  if hasChoices then
    let key := displayKey name
    result := setKey result key display
  return result
-- impl-end

-- proof-start
theorem correct_registerDisplay :
    ∀ (attrs : Attrs) (name : String) (hasChoices : Bool) (display : Int),
    problem_spec_registerDisplay attrs name hasChoices display
      (implementation_registerDisplay attrs name hasChoices display) := by
  intro attrs name hasChoices display
  unfold problem_spec_registerDisplay implementation_registerDisplay
  sorry   -- carries the gold proof shape; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
