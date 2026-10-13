# refinement.md — django__django-12713

Maps every operation in `implementation_resolveWidget` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `resolveWidget` (widget-selection block of `formfield_for_manytomany`)

Post-patch repo code (`patch.diff`, `options.py:252-261`):
```python
if 'widget' not in kwargs:
    autocomplete_fields = self.get_autocomplete_fields(request)
    if db_field.name in autocomplete_fields:
        kwargs['widget'] = AutocompleteSelectMultiple(db_field.remote_field, self.admin_site, using=db)
    elif db_field.name in self.raw_id_fields:
        kwargs['widget'] = widgets.ManyToManyRawIdWidget(db_field.remote_field, self.admin_site, using=db)
    elif db_field.name in [*self.filter_vertical, *self.filter_horizontal]:
        kwargs['widget'] = widgets.FilteredSelectMultiple(
            db_field.verbose_name,
            db_field.name in self.filter_vertical
        )
```

Lean impl (`implementation_resolveWidget`):
```lean
def implementation_resolveWidget
    (name : FieldName) (incoming : Option Widget)
    (auto raw vert horiz : List FieldName) : Option Widget := Id.run do
  let mut widget := incoming
  if widget.isNone then
    if name ∈ auto then
      widget := some .autocomplete
    else if name ∈ raw then
      widget := some .rawId
    else if name ∈ (vert ++ horiz) then
      widget := some (.filtered (name ∈ vert))
  return widget
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut widget := incoming` | `widget = kwargs.get('widget')` (the option bag seen on entry) | **R** | `incoming` ↔ `kwargs.get('widget')`: `some (Widget.supplied id)` when the caller pre-populated a widget (e.g. via `formfield_overrides`), `none` when not. Object identity is the only caller-widget observable, modeled by `id : Nat`. See mapping.md. |
| 2 | `if widget.isNone then …` | `if 'widget' not in kwargs:` | **I** (deep model of the changed op) | **the fixed operation.** `widget.isNone` ↔ `'widget' not in kwargs`. This is the guard the patch adds: the classification cascade runs ONLY when the caller chose nothing. Pre-patch the cascade ran unconditionally. |
| 3 | `if name ∈ auto then widget := some .autocomplete` | `if db_field.name in autocomplete_fields: kwargs['widget'] = AutocompleteSelectMultiple(...)` | **R** | `auto` ↔ `get_autocomplete_fields(request)`'s returned list (read AS the list — unchanged callee); `name ∈ auto` ↔ membership; `Widget.autocomplete` ↔ the autocomplete multi-select kind (only the kind is observed). |
| 4 | `else if name ∈ raw then widget := some .rawId` | `elif db_field.name in self.raw_id_fields: kwargs['widget'] = widgets.ManyToManyRawIdWidget(...)` | **R** | `raw` ↔ `self.raw_id_fields`; `Widget.rawId` ↔ the raw-id multi-select kind. |
| 5 | `else if name ∈ (vert ++ horiz) then widget := some (.filtered (name ∈ vert))` | `elif db_field.name in [*self.filter_vertical, *self.filter_horizontal]: kwargs['widget'] = widgets.FilteredSelectMultiple(db_field.verbose_name, db_field.name in self.filter_vertical)` | **R** | `vert ++ horiz` ↔ the splatted concatenation `[*filter_vertical, *filter_horizontal]`; `Widget.filtered (name ∈ vert)` ↔ the filtered multi-select carrying the `db_field.name in self.filter_vertical` boolean. `verbose_name` is presentation-only and not observed. |
| 6 | (implicit `else` — no branch) | no `elif` matches ⇒ `kwargs['widget']` stays absent | **I** | when the caller chose nothing and no list matches, no widget is configuration-selected (`widget` stays `none`). |
| 7 | `return widget` | the value of `kwargs.get('widget')` after the block | **R** | the resulting widget option ↔ the post-block `kwargs['widget']` (consumed downstream by `db_field.formfield(**kwargs)`). |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the patched selection block.

## Callee provenance (no consumed axiom)

- `self.get_autocomplete_fields(request)` (`options.py:252`) returns
  `self.autocomplete_fields` UNCHANGED by the patch; read directly AS the input
  list `auto`. No property consumed.
- The widget constructors (`AutocompleteSelectMultiple`, `ManyToManyRawIdWidget`,
  `FilteredSelectMultiple`) are UNCHANGED by the patch; only the SELECTED KIND
  (and whether selection happens) is observable, captured by `Widget`'s
  constructors. The F2P test asserts on widget kind.
- The early-return `auto_created` guard, the `'queryset' not in kwargs` block, the
  final `db_field.formfield(**kwargs)` call, and the help-text augmentation are
  UNCHANGED and orthogonal to the widget-selection decision; not modeled. The spec
  pins the full resulting widget choice, so omitting them leaves no free output
  component.

## Soundness check (verify ⟹ correct)

- `problem_spec_resolveWidget` pins the result EXACTLY (`result = match incoming
  …`) — directive 5 (frame): the output is fully determined by `incoming`, `name`,
  and the four configuration lists. No output component is left unconstrained. No
  ungrounded oracle (directive 8) — the postcondition is dischargeable only by
  actually checking `incoming` then running the classification cascade.
- The prepatch impl reproduces the PRE-FIX behavior: it runs the cascade
  UNCONDITIONALLY (no `if widget.isNone` guard), so when `incoming = some w` and
  `name` is in one of the classification lists it OVERWRITES the caller widget. It
  violates the spec on the discriminating clause `incoming = some w ∧ (name ∈ auto
  ∨ name ∈ raw ∨ name ∈ vert ++ horiz)`: the spec requires `result = some w`, but
  the prepatch returns the cascade-chosen widget. Its carried gold proof cannot
  close (G-DIFF/G-PANEL).
- This discriminating case is precisely the FAIL_TO_PASS assertion added by the
  test patch (`test_formfield_overrides_m2m_filter_widget`): an admin sets
  `filter_vertical = ['members']` (so `name = 'members' ∈ vert`) AND supplies a
  widget via `formfield_overrides`; the test asserts the field's widget is the
  caller-supplied `CheckboxSelectMultiple`. Pre-fix the cascade overwrote it with
  the filtered widget; post-fix the guard preserves it.
- G-CONF confirms the R/I shadow == an in-process replica of the patched
  selection block over hand-picked edge cases (including caller widget present
  with `name` matching each list, caller widget present with no match, no caller
  widget with each match, and no caller widget with no match) plus ≥1e5 fuzzed
  inputs.
