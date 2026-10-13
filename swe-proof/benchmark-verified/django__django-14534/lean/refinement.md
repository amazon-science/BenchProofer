# refinement.md — django__django-14534

Maps every operation in `implementation_idForLabel` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `idForLabel` (`BoundWidget.id_for_label`)

Post-patch repo code (`patch.diff`, `boundfield.py:277-278`):
```python
@property
def id_for_label(self):
    return self.data['attrs'].get('id')
```

Lean impl (`implementation_idForLabel`):
```lean
def implementation_idForLabel (data : WidgetData) : Option String := Id.run do
  return data.attrs.lookup "id"
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `data : WidgetData` (input carrier) | `self.data` — the subwidget presentation dict | **R** | `self.data` ↔ `WidgetData` restricted to the keys the modeled property reads (`attrs`, `name`, `index`); see mapping.md. The other dict keys are not read by `id_for_label`. |
| 2 | `data.attrs` | `self.data['attrs']` | **R** | the option's HTML-attribute dict ↔ `List (String × String)` with distinct keys (mapping.md). |
| 3 | `data.attrs.lookup "id"` | `self.data['attrs'].get('id')` | **I** (deep model of the changed op) | **the fixed operation.** `dict.get('id')` ↔ `List.lookup "id"`: returns the value mapped to the `'id'` key, or `none`/`None` when absent. Keys distinct ⇒ `lookup` yields the unique value. This is the entire post-patch body. |
| 4 | `return …` | `return self.data['attrs'].get('id')` | **R** | the property's return value ↔ the impl's returned `Option String`. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the patched `id_for_label`.

## Callee provenance (no consumed axiom)

- `dict.get('id')` — a builtin total lookup; it IS the changed op, modeled deeply
  by `List.lookup` (never axiomatized).
- The construction of `self.data['attrs']['id']` happens UPSTREAM, in
  `BoundField.subwidgets` / `ChoiceWidget.options`, and is UNCHANGED by the patch.
  The patch only changes which field of the already-built `self.data` the
  property returns. The contents of `attrs` are therefore a free input to the
  modeled function (`WidgetData.attrs`); the spec constrains the result purely as
  a function of that input.
- `self.data['name']`, `self.data['index']` — read by the PRE-patch synthesis
  only. Post-patch they do not bear on the result; they remain in `WidgetData`
  so the prepatch impl can reproduce the pre-fix synthesis verbatim.

## Soundness check (verify ⟹ correct)

- `problem_spec_idForLabel` pins the result to `data.attrs.lookup "id"` — full
  equality to an input-grounded expression (directive 5/8): the result is
  determined entirely by the option's attribute table, and is NOT pinned to an
  ungrounded oracle. `name`/`index` never appear on the spec's RHS, so an impl
  cannot satisfy the spec by synthesizing from them. No output component is left
  unconstrained.
- The prepatch impl reproduces the PRE-FIX synthesis: it returns
  `some ("id_" ++ name ++ "_" ++ index)`, modeling `'id_%s_%s' % (name, index)`.
  It violates the spec on the discriminating clause: any `WidgetData` whose
  `attrs.lookup "id" ≠ some ("id_" ++ name ++ "_" ++ index)` — e.g. a custom
  `auto_id='prefix_%s'` giving `attrs['id'] = "prefix_field_0"` while the
  synthesis yields `"id_field_0"`, or `attrs` lacking `'id'` so the spec demands
  `none` but the synthesis returns `some …`. Its carried gold proof cannot close
  (G-DIFF/G-PANEL).
- This discriminating case is precisely the FAIL_TO_PASS assertions added by the
  test patch: `test_boundfield_subwidget_id_for_label` sets `auto_id='prefix_%s'`
  and asserts `subwidgets[0].id_for_label == 'prefix_field_0'` (the value in
  `attrs['id']`), which the pre-fix synthesis `'id_field_0'` fails; and
  `test_iterable_boundfield_select` asserts `fields[0].id_for_label is None` for a
  form with `auto_id=False` (no `'id'` in `attrs`), which the pre-fix synthesis
  `'id_name_0'` fails.
- G-CONF confirms the R/I shadow == an in-process replica of the patched
  `id_for_label` (`self.data['attrs'].get('id')`) over hand-picked edge cases
  (custom-prefix id present, no `'id'` key ⇒ `None`, default-style id present)
  plus ≥1e5 fuzzed subwidget dicts.
