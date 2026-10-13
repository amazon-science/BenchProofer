import Mathlib
-- imports-end

/-!
Reporting the DOM identifier to associate with the label of one rendered choice
inside an iterable, multi-option form widget.

When such a widget is rendered, each individual option is described by a small
record of presentation data. Among that data is an attribute table — the set of
HTML attributes that will be emitted on the option's input element — together
with the option's symbolic name and its positional index within the group.

The identifier a caller should point a `<label for=…>` at is exactly the `id`
attribute that the option's input element will actually carry. That value lives
in the option's attribute table under the key `"id"`. If the attribute table
holds no such key, there is no associated identifier and the answer is "none".

The desired behavior is therefore: look the `"id"` key up in the option's
attribute table and report whatever is found there (or its absence), so that the
reported identifier always agrees with the identifier the element is rendered
with — including any caller-supplied identifier scheme.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The reported
-- identifier is the value stored under the `"id"` key of the option's attribute
-- table; that lookup is modeled structurally over the table itself, so no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The presentation data describing one option of an iterable choice widget,
restricted to the touched fields:
* `attrs` — the option's attribute table: an association list of
  `(attribute-name, attribute-value)` pairs with distinct keys (see mapping.md),
  modeling the HTML attributes the option's input element carries;
* `name` — the option group's symbolic name;
* `index` — the option's positional index within the group, as a string. -/
structure WidgetData where
  attrs : List (String × String)
  name : String
  index : String
-- pure-end

-- post-conditions-start
/-- The reported label identifier is exactly the value stored under the `"id"`
key of the option's attribute table: `some v` when the table maps `"id"` to `v`,
and `none` when the table has no `"id"` entry. The option's `name` and `index`
do not constrain the result. -/
def problem_spec_idForLabel (data : WidgetData) (result : Option String) : Prop :=
  result = data.attrs.lookup "id"
-- post-conditions-end

-- impl-start
def implementation_idForLabel (data : WidgetData) : Option String := Id.run do
  return data.attrs.lookup "id"
-- impl-end

-- proof-start
theorem correct_idForLabel :
    ∀ (data : WidgetData),
      problem_spec_idForLabel data (implementation_idForLabel data) := by
  intro data
  unfold problem_spec_idForLabel implementation_idForLabel
  rfl
-- proof-end
