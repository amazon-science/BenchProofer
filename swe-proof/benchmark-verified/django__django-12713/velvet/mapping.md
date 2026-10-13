# mapping.md — django__django-12713

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 5b884d45ac5b76234eca614d90c83b347294c332`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each modeled construct.

Repo file under change: `django/contrib/admin/options.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolveWidget (provided computedDefault : Option Widget)` | `ModelAdmin.formfield_for_manytomany` — `django/contrib/admin/options.py:242` (the widget-selection block, lines 252–261 pre-patch / 252–270 post-patch) | the modeled changed function: how the widget that ends up in `kwargs` is chosen |
| `Widget` (structure with `id : Nat`) | a form widget instance (`AutocompleteSelectMultiple` / `ManyToManyRawIdWidget` / `FilteredSelectMultiple`, or a caller-supplied widget such as `forms.CheckboxSelectMultiple`) | opaque widget identity; only widget identity/kind is observable to the caller |
| `provided : Option Widget` | `kwargs.get('widget')` — present iff `'widget' in kwargs` | the caller-supplied widget (e.g. via `formfield_overrides`), or absent |
| `computedDefault : Option Widget` | the widget the UNCHANGED autocomplete/raw_id/filter selection chain (lines 252–261) would assign for this field | the field-derived default widget, or `none` when no branch fires |

The pre-patch behaviour the change corrects (refinement audit only, not in the
consumer spec view): the selection chain at lines 252–261 runs
**unconditionally**, so any `kwargs['widget']` the caller passed is overwritten
whenever a branch fires.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `kwargs.get('widget')` (a widget instance or absent) | `Option Widget` | a widget present in `kwargs` ↔ `some w`; `'widget' not in kwargs` ↔ `none`. The guard `'widget' not in kwargs` ↔ `provided.isNone`. |
| a form widget instance | `Widget` (tagged `id : Nat`) | distinct widget objects/kinds ↔ distinct `id`s; the caller only observes *which* widget was used (object identity / `isinstance`), so an opaque tagged id is faithful. The F2P test compares `field.widget.widget` to the supplied `CheckboxSelectMultiple`. |
| the autocomplete/raw_id/filter selection chain's net assignment | `computedDefault : Option Widget` | the widget the unchanged `if/elif/elif` would set (`AutocompleteSelectMultiple` / `ManyToManyRawIdWidget` / `FilteredSelectMultiple`) ↔ `some w`; no branch fires ↔ `none`. This abstracts the unchanged membership tests (`db_field.name in autocomplete_fields` / `raw_id_fields` / `[*filter_vertical, *filter_horizontal]`) and the unchanged widget constructors as a single free input (the django__django-11095 ORACLE-choice precedent: unchanged callees folded into a free value). |

The queryset block (lines 263–266 post-patch) and the help-text wrapping
(269–273) are widget-irrelevant and identical pre/post patch; they do not affect
which widget is resolved, so they are outside the modeled carrier.

## 3. Callee provenance (kind-A)

**None.** There are no axiomatized callees and no deep-model references in this
bundle (`meta.json axioms = []`, `deep_model_references = []`; G-AX skipped). The
only modeled behaviour is the *precedence* between a caller-supplied widget and a
field-computed default — a closed `Option`-precedence function of two free
inputs. The widget constructors and the membership tests inside the selection
chain are UNCHANGED by the patch and are abstracted to the free input
`computedDefault` (§2), not consumed as contracts. The guard `'widget' not in
kwargs` (the one thing the patch adds) is modeled deeply as `provided.isNone`,
validated against the patched control flow by G-CONF (§4), not axiomatized.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12713`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`resolveWidget` to Python; the ORACLE transliterates the patched
`formfield_for_manytomany` widget-resolution flow VERBATIM (the unchanged
selection chain folded into `computed_default`, per the django__django-11095
ORACLE-choice precedent — running the real admin method needs the full migrated
admin harness and would not isolate the modeled change). Boundary cases cover
the F2P scenario (caller supplies a widget for a `filter_vertical` field, whose
unchanged chain would otherwise pick `FilteredSelectMultiple`) and the full
(provided ∈ {none, caller}) × (default ∈ {none, auto, raw_id, filter}) matrix.
