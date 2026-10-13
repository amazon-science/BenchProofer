# mapping.md — django__django-12713

## Symbol binding (file:line @ base_commit 5b884d45ac5b76234eca614d90c83b347294c332)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_resolveWidget` / `problem_spec_resolveWidget` | the widget-selection block of `BaseModelAdmin.formfield_for_manytomany` | `django/contrib/admin/options.py:252-261` |
| `incoming : Option Widget` | `kwargs.get('widget')` — the widget the caller already put in `kwargs` (via `formfield_overrides`) | `options.py:250-261` |
| `defaultWidget` (pure helper) | the `if/elif/elif` cascade that picks `AutocompleteSelectMultiple` / `ManyToManyRawIdWidget` / `FilteredSelectMultiple` | `options.py:252-261` |
| `auto : List FieldName` | `self.get_autocomplete_fields(request)` (its returned list of field names) | `options.py:252-253` |
| `raw : List FieldName` | `self.raw_id_fields` | `options.py:255` |
| `vert : List FieldName` | `self.filter_vertical` | `options.py:257,260` |
| `horiz : List FieldName` | `self.filter_horizontal` | `options.py:257` |
| `name : FieldName` | `db_field.name` | `options.py:253,255,257,260` |
| `Widget` (inductive) | the form widget object eventually stored in `kwargs['widget']` | — |

The modeled function is the widget-selection block of `formfield_for_manytomany`.
It is the only behavior the patch changes and the only one observed by the
FAIL_TO_PASS test `test_formfield_overrides_m2m_filter_widget`.

### What the function does (base_commit)

```python
def formfield_for_manytomany(self, db_field, request, **kwargs):
    if not db_field.remote_field.through._meta.auto_created:
        return None
    db = kwargs.get('using')

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

    if 'queryset' not in kwargs:
        ...
    return db_field.formfield(**kwargs)
```

At base_commit the `if/elif/elif` cascade runs UNCONDITIONALLY: if the field name
matches one of the admin's classification lists, it assigns `kwargs['widget']`,
**overwriting** any widget the caller had already supplied in `kwargs` (e.g. via
`formfield_overrides = {ManyToManyField: {'widget': forms.CheckboxSelectMultiple}}`).
The post-patch code wraps the whole cascade in `if 'widget' not in kwargs:`, so a
caller-supplied widget is preserved and the classification cascade is skipped.

This is exactly the divergence from `formfield_for_foreignkey` noted in the issue:
that sibling already guards its widget assignment, so a `formfield_overrides`
widget survives there.

### Lean modeling

- `incoming : Option Widget` ↔ `kwargs.get('widget')`: `some w` when the caller
  pre-populated a widget, `none` when not. Only the presence and (for a supplied
  widget) the opaque object identity matter to the observable outcome, so a
  caller widget is `Widget.supplied id` with `id : Nat` an injective object-id
  stand-in.
  - **Presence vs value — domain invariant.** The patch guards on KEY presence
    (`'widget' not in kwargs`), which in general differs from value-is-`None`.
    Over the REACHABLE input domain these coincide: a widget supplied to this
    block comes from `formfield_overrides` (a `{FieldClass: {'widget': <widget>}}`
    mapping), whose `'widget'` value is always a real widget class/instance —
    never `None`. So `kwargs.get('widget') is None ⇔ 'widget' not in kwargs`, and
    `Option Widget` (`none ⇔ absent`, `some w ⇔ a real supplied widget`) is a
    faithful bijection on this domain. (A misconfigured explicit `widget=None`
    is not a Django use case and is not exercised by any F2P/P2P test; modeling
    it would need `Option (Option Widget)` for an unreachable input, so it is
    deliberately excluded. The guard is therefore correctly modeled as
    `incoming.isNone`.)
- `name : FieldName`, and the four classification lists `auto`, `raw`, `vert`,
  `horiz` are `List FieldName` (`Nat` field-name identities; only membership is
  observed). `get_autocomplete_fields(request)` is read AS its returned list
  `auto` — its body just returns `self.autocomplete_fields` and is unchanged by
  the patch (see callee provenance).
- `defaultWidget name auto raw vert horiz` models the cascade: autocomplete
  first, then raw-id, then filtered (carrying `name ∈ vert` as the vertical
  flag), else `none`. The `[*self.filter_vertical, *self.filter_horizontal]`
  membership test is `name ∈ (vert ++ horiz)`.
- `problem_spec_resolveWidget` pins the resulting widget exactly: a caller widget
  is kept (`some w`); otherwise `defaultWidget …` is used. The result is the
  final value of `kwargs.get('widget')` after the block.

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| `db_field.name` | `name : FieldName` (`Nat`) | each distinct field-name string ↔ a distinct `Nat`. |
| `kwargs.get('widget')` (before/after the block) | `Option Widget` | absent ↔ `none`; a caller widget ↔ `some (Widget.supplied id)`; a cascade-chosen widget ↔ `some .autocomplete` / `some .rawId` / `some (.filtered v)`. |
| `AutocompleteSelectMultiple(...)` | `Widget.autocomplete` | the autocomplete multi-select kind. |
| `widgets.ManyToManyRawIdWidget(...)` | `Widget.rawId` | the raw-id multi-select kind. |
| `widgets.FilteredSelectMultiple(verbose_name, name in filter_vertical)` | `Widget.filtered (name ∈ vert)` | the filtered multi-select; the boolean is the "is vertical" flag. |
| `get_autocomplete_fields(request)` | `auto : List FieldName` | the returned list of autocomplete-eligible names. |
| `self.raw_id_fields` | `raw : List FieldName` | the raw-id name list. |
| `self.filter_vertical` / `self.filter_horizontal` | `vert` / `horiz : List FieldName` | the two filtered-select subsets. |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — whether the
  classification cascade runs at all — is modeled DEEPLY by the `if widget.isNone`
  guard plus `defaultWidget` over the four configuration lists (SPEC_GUIDE §3: a
  deeply-modeled changed decision is never axiomatized). So the `axioms` region is
  empty and **G-AX skips**.
- `self.get_autocomplete_fields(request)` returns `self.autocomplete_fields`
  unchanged by the patch; it is read directly AS the input list `auto`. No
  property of it is consumed by the proof.
- The widget CONSTRUCTORS (`AutocompleteSelectMultiple`, `ManyToManyRawIdWidget`,
  `FilteredSelectMultiple`) are unchanged by the patch; only WHICH kind is
  selected (and whether selection happens at all) is observable here, captured by
  the `Widget` constructors. The F2P test asserts on widget KIND
  (`isinstance(field.widget.widget, CheckboxSelectMultiple)`).
- The surrounding context (`db_field.remote_field.through._meta.auto_created`
  early-return guard, the `'queryset' not in kwargs` block, the final
  `db_field.formfield(**kwargs)` and the help-text augmentation) is UNCHANGED by
  the patch and orthogonal to the widget-selection decision; not modeled. Its
  omission constrains no output component the spec leaves free — the spec pins the
  full resulting widget choice.

## G-CONF fuzz seed

Pinned LCG seed: **12713** (see `conformance_check.py` `SEED`). Corpus: a random
`name`, an `incoming` widget that is present (`supplied`) or absent with tuned
frequency, and four classification lists drawn from a small name pool so the
membership tests actually bite (the name lands in autocomplete / raw-id /
filtered-vertical / filtered-horizontal / none with meaningful frequency), over
≥1e5 fuzzed inputs. The R/I shadow of `implementation_resolveWidget` (guard the
cascade behind "no caller widget") is diffed against an in-process replica of the
POST-PATCH selection block (`if 'widget' not in kwargs:` wrapping the cascade).
Hand-picked edge cases pin the discriminating clause: a caller widget present AND
`name` matching one of the classification lists (pre-fix the cascade would have
overwritten the caller widget; post-fix it is preserved).
