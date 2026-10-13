import Mathlib
-- imports-end

/-!
Selecting the form widget for a multi-valued relation field on an admin form.

The setting: an admin form is being built for a field that relates one record to
MANY others. The form-builder receives a bag of keyword options that the CALLER
may have already populated, plus the admin configuration that classifies field
names into three groups:

  * names that should use an autocomplete-style multi-select;
  * names that should use a raw-id multi-select;
  * names that should use a two-box filtered multi-select (further split into a
    "vertical" subset and a "horizontal" subset).

The builder must decide which widget the field ends up with. The intended
behavior:

  * a widget the CALLER has already chosen takes precedence — it is kept as-is
    and the configuration-driven classification is not consulted at all;
  * otherwise the widget is chosen from the configuration: an autocomplete name
    wins first, then a raw-id name, then a filtered-select name (carrying whether
    that name is in the vertical subset);
  * if the caller chose nothing and the name matches none of the groups, the
    field is left without a configuration-chosen widget.

`Widget` records only the touched distinction: which KIND of widget is selected
(and, for a caller-chosen one, its opaque object identity).
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The field-name
-- classification is supplied directly as the three configuration lists (the
-- accessor that returns the autocomplete-eligible names is read as its result
-- list), and the widget-selection decision is modeled structurally over those
-- lists and the caller-supplied option. No `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- A field-name identity. Modeled as a `Nat` (an injective encoding of the
distinct field-name strings; only equality / list-membership is observed). -/
abbrev FieldName := Nat

/-- The kind of widget selected for the relation field, restricted to the
touched distinctions:
* `autocomplete` — an autocomplete-style multi-select;
* `rawId` — a raw-id multi-select;
* `filtered vertical` — a two-box filtered multi-select; `vertical = true` iff
  the field name belongs to the "vertical" subset;
* `supplied id` — a widget the caller chose, identified only by its opaque
  object identity `id`. -/
inductive Widget where
  | autocomplete
  | rawId
  | filtered (vertical : Bool)
  | supplied (id : Nat)
deriving DecidableEq

/-- The configuration-driven widget choice for a field name, absent any
caller-supplied widget: an autocomplete name wins first, then a raw-id name,
then a filtered-select name (carrying membership in the vertical subset); a name
in none of the groups gets no configuration-chosen widget. -/
def defaultWidget (name : FieldName) (auto raw vert horiz : List FieldName) :
    Option Widget :=
  if name ∈ auto then some .autocomplete
  else if name ∈ raw then some .rawId
  else if name ∈ (vert ++ horiz) then some (.filtered (name ∈ vert))
  else none
-- pure-end

-- post-conditions-start
/-- The widget the field ends up with. A caller-supplied widget (`incoming =
some w`) is kept exactly; otherwise the configuration-driven choice is used. The
result is fully pinned by the inputs. -/
def problem_spec_resolveWidget
    (name : FieldName) (incoming : Option Widget)
    (auto raw vert horiz : List FieldName) (result : Option Widget) : Prop :=
  result =
    (match incoming with
     | some w => some w
     | none   => defaultWidget name auto raw vert horiz)
-- post-conditions-end

-- impl-start
def implementation_resolveWidget
    (name : FieldName) (incoming : Option Widget)
    (auto raw vert horiz : List FieldName) : Option Widget := Id.run do
  let mut widget := incoming
  -- The configuration is consulted unconditionally; a matching classification
  -- overwrites whatever the caller may already have chosen.
  if name ∈ auto then
    widget := some .autocomplete
  else if name ∈ raw then
    widget := some .rawId
  else if name ∈ (vert ++ horiz) then
    widget := some (.filtered (name ∈ vert))
  return widget
-- impl-end

-- proof-start
theorem correct_resolveWidget :
    ∀ (name : FieldName) (incoming : Option Widget)
      (auto raw vert horiz : List FieldName),
      problem_spec_resolveWidget name incoming auto raw vert horiz
        (implementation_resolveWidget name incoming auto raw vert horiz) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
