# mapping.md — django__django-14534

## Symbol binding (file:line @ base_commit 910ecd1b8df7678f45c3d507dde6bcb1faafa243)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_idForLabel` / `problem_spec_idForLabel` | `BoundWidget.id_for_label` (property) | `django/forms/boundfield.py:277-278` |
| `WidgetData` (pure structure) | `self.data` — the per-subwidget presentation dict produced by `ChoiceWidget.options` / `…subwidgets(...)` and handed to `BoundWidget.__init__` | `django/forms/boundfield.py` (`BoundField.subwidgets` builds it; `BoundWidget.__init__` stores it as `self.data`) |
| `WidgetData.attrs` | `self.data['attrs']` — the HTML attribute dict of the subwidget's input element | the `attrs` key of the subwidget dict |
| `WidgetData.name` | `self.data['name']` | the `name` key of the subwidget dict |
| `WidgetData.index` | `self.data['index']` | the `index` key of the subwidget dict |
| `WidgetData.attrs.lookup "id"` | `self.data['attrs'].get('id')` | the post-patch body |

The modeled function is `BoundWidget.id_for_label`. It is the only function whose
behavior changes and the only one observed by the FAIL_TO_PASS tests
(`test_boundfield_subwidget_id_for_label`, `test_iterable_boundfield_select`).

### What the function does (base_commit vs post-patch)

```python
# base_commit (django/forms/boundfield.py:277-278)
@property
def id_for_label(self):
    return 'id_%s_%s' % (self.data['name'], self.data['index'])

# post-patch
@property
def id_for_label(self):
    return self.data['attrs'].get('id')
```

At base_commit the property *synthesizes* an identifier from two unrelated fields
of the subwidget dict (`name` and `index`) using a fixed `'id_%s_%s'` format
string. This ignores the `id` that `ChoiceWidget.options` actually placed in
`self.data['attrs']` — so when the form is initialized with a custom `auto_id`
format (e.g. `auto_id='prefix_%s'`), the rendered input carries
`attrs['id'] == 'prefix_field_0'` while `id_for_label` returns the unrelated
`'id_field_0'`. The post-patch body reads the identifier straight from the
attribute dict (`self.data['attrs'].get('id')`), so the reported label target
always matches the identifier the element is rendered with. When `'id'` is absent
from `attrs`, `dict.get('id')` returns `None`.

### Lean modeling

- `self.data` (a dict with keys `name`, `index`, `value`, `attrs`, `template_name`,
  `wrap_label`, …) is modeled as `WidgetData`, restricted to the three keys the
  base/post code reads: `attrs`, `name`, `index`.
- `self.data['attrs']` is an HTML attribute dict; modeled as an association list
  `List (String × String)` with distinct keys (HTML attribute dicts are built by
  `Widget.build_attrs`/`dict` updates, so each attribute name occurs at most once).
  Only the `"id"` key is read here; key order and the other attributes are
  irrelevant to the result. `List.lookup "id"` returns the first matching value,
  which — keys being distinct — is the unique value or `none`.
- `self.data['attrs'].get('id')` (a Python `dict.get` returning `str | None`) is
  modeled as `attrs.lookup "id" : Option String`: `some v` ↔ the dict maps `'id'`
  to `v`; `none` ↔ `'id'` not in the dict (Python `None`).
- `self.data['name']`, `self.data['index']` are subwidget dict strings; modeled
  as `String` fields. They are read by the *pre*-patch synthesis only and do not
  constrain the post-patch result.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| the subwidget presentation dict `self.data` | `WidgetData` | restricted to keys `attrs`, `name`, `index`; other keys are not read by the modeled property. |
| `self.data['attrs']` (`dict[str, Any]`, here string-valued for the `id` slot) | `WidgetData.attrs : List (String × String)` | each `(attribute-name, attribute-value)` ↔ one pair; keys distinct; order irrelevant to the `id` lookup. |
| `self.data['attrs'].get('id')` | `attrs.lookup "id" : Option String` | `str → some str`; missing key / `None` → `none`. |
| `self.data['name']` | `WidgetData.name : String` | identity on strings. |
| `self.data['index']` | `WidgetData.index : String` | the option index, rendered as a decimal string (`'%s' % index`); identity on strings. |
| return of `id_for_label` | `Option String` | the label `for=` target (`str` or `None`). |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — *which* value the
  property returns — is modeled DEEPLY by `attrs.lookup "id"` over the option's
  attribute table (SPEC_GUIDE §3: a deeply-modeled changed op is never
  axiomatized). No property of an external callee is consumed by the proof, so the
  `axioms` region is empty and **G-AX skips**.
- `self.data['attrs'].get('id')` — `dict.get` is a builtin total lookup returning
  the value or `None`; modeled directly by `List.lookup`. Not axiomatized (it is
  the changed op itself).
- The construction of `self.data` (in `BoundField.subwidgets` via
  `self.field.widget.subwidgets(...)`/`ChoiceWidget.options`) is UPSTREAM of the
  modeled property and UNCHANGED by the patch. The patch reads `self.data`; it
  does not change how `self.data` is built. The F2P test
  (`test_boundfield_subwidget_id_for_label`) sets `auto_id='prefix_%s'`, which
  makes `ChoiceWidget.options` place `attrs['id'] = 'prefix_field_0'`; the value
  in `attrs['id']` is therefore the input to the modeled property and is taken as
  given (a free input in `WidgetData.attrs`). No flag in the modeled function.

## G-CONF fuzz seed

Pinned LCG seed: **14534** (see `conformance_check.py` `SEED`). Corpus: randomized
subwidget dicts — `attrs` an association list with 0–5 distinct keys (the key set
drawn so `'id'` is present in roughly half the cases, with id-values drawn from
both default-style `'id_<name>_<index>'` strings and custom-prefix strings like
`'prefix_<name>_<index>'`, so the synthesized and read identifiers both coincide
and diverge), `name` and `index` drawn from small string ranges. The R/I shadow
of `implementation_idForLabel` (`attrs.get('id')`) is diffed against an in-process
replica of the POST-PATCH `id_for_label` (`self.data['attrs'].get('id')`) over
≥1e5 fuzzed inputs. Hand-picked edge cases pin the discriminating clause: a
custom `auto_id` prefix where `attrs['id'] != 'id_%s_%s' % (name, index)`, and an
`attrs` dict with no `'id'` key (result `None`).
