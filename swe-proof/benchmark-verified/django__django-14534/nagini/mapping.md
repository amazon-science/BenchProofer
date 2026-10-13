# mapping.md — django__django-14534

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 910ecd1b8df7678f45c3d507dde6bcb1faafa243`, states the type
abstraction, and gives the provenance of the one out-of-band reference.

Repo file under change: `django/forms/boundfield.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `label_target_id(ctx)` | `BoundWidget.id_for_label` (property) — `django/forms/boundfield.py:278-280` (body line 280) | the modeled changed function: the label-target identifier a per-choice subwidget container reports |
| `ChoiceContext` | the per-option context dict stored on `BoundWidget.data` — produced by `ChoiceWidget.create_option` (`django/forms/widgets.py:621-638`) and assigned at `BoundWidget.__init__` (`boundfield.py:260-263`) | minimal carrier of the touched fields of `self.data` |
| `ctx.attrs` | `self.data['attrs']` — the per-option `option_attrs` dict (`widgets.py:634`) | the attribute mapping the resolved identifier is recorded in |
| `ctx.name` | `self.data['name']` (`widgets.py:629`) | the option's name token (consumed only by the buggy fabrication) |
| `ctx.index` | `self.data['index']` (`widgets.py:633`) | the option's position (consumed only by the buggy fabrication) |
| `id_key()` | the literal dict key `'id'` (`self.data['attrs'].get('id')`, post-patch body; `widgets.py:626-627` sets `option_attrs['id']`) | the attribute-mapping key under which the resolved identifier is recorded |

The pre-patch repo expression the change removes (for the refinement audit, not
referenced from the consumer spec view): `'id_%s_%s' % (self.data['name'],
self.data['index'])` (`boundfield.py:280` @ base_commit) — the name/position
fabrication.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.data` (a `dict`) — the per-option rendering context | `ChoiceContext` class exposing only the three touched fields (`attrs`, `name`, `index`) | `self.data['attrs']` ↔ `ctx.attrs`; `self.data['name']` ↔ `ctx.name`; `self.data['index']` ↔ `ctx.index`. The other keys (`value`, `label`, `selected`, `type`, `template_name`, `wrap_label`) are untouched by `id_for_label` and omitted. |
| `self.data['attrs']` (a `dict` of HTML attributes), key `'id'` → an id `str` | `Dict[int, int]` keyed by `id_key()` (the `'id'` token), value an `int` id token | `'id' in attrs` ↔ `id_key() in ctx.attrs`; `attrs.get('id')` returns the id `str` when present, else `None` ↔ `ctx.attrs[id_key()]` when `id_key() in ctx.attrs`, else `None`. |
| an id `str` (e.g. `'prefix_field_0'`, `'id_name_0'`) | an opaque `int` token | the tested behaviour only observes WHICH id is reported and whether one exists; the id `str` and the absence (`None`) are faithfully carried by an `int` token and the carrier `None`. The id `str` is **already fully resolved** in `option_attrs['id']` (prefix applied + index appended by `ChoiceWidget.id_for_label`, `widgets.py:626-627,645-651`); the property only reads it back. |
| `str(idx)` index / `'%s_%s'`-formatted name (in the removed fabrication) | `ctx.name`, `ctx.index` int tokens combined arithmetically (prepatch only) | the fabrication consumes only `name`/`index`; modeled as `ctx.name * 1000 + ctx.index` — a deterministic value independent of `attrs`, never `None`. |

`str` indexing is banned in Nagini, so all id/name values are `int` tokens; the
absence of an id is the genuine `None`.

## 3. Out-of-band reference (kind A-reference — checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom**. The behaviour under
specification — "report the identifier recorded in the attribute mapping, or
None if none is recorded" — is modeled **deeply**: `label_target_id` is the
direct membership test + lookup `attrs.get('id')`, spelled out in the impl. The
only thing validated out-of-band is that the model's dict membership/lookup
matches real Python `dict.get` / `in` semantics on the actual data layout.

### 3.1 `label_target_id` deep model ↔ `BoundWidget.id_for_label` (A-reference)
**Callee context:** `dict.get('id')` on `self.data['attrs']` (CPython builtin
`dict`), plus the upstream guarantee (`ChoiceWidget.create_option`,
`widgets.py:621-638`) that `option_attrs['id']`, when present, already holds the
fully-resolved id (prefix + per-option index, set at `widgets.py:626-627` via
`ChoiceWidget.id_for_label`, `widgets.py:645-651`). The deep model is validated
== the real property out-of-band by `axiom_check.py` (G-AX): it constructs the
real `BoundField.subwidgets` / `BoundWidget` data path for the three observed
form configurations and asserts the real `BoundWidget.id_for_label` equals
`attrs.get('id')` — i.e. that `label_target_id`'s `Result()` (= recorded id, or
None) matches the real post-patch property.

The three configurations the F2P / P2P tests pin (and that `axiom_check.py`
reproduces):

| form config | widget | `data['attrs']` id | real `id_for_label` (post-patch) | model `Result()` |
|---|---|---|---|---|
| `auto_id='prefix_%s'` (a configured prefix) | `CheckboxSelectMultiple` | `'prefix_field_0'`, `'prefix_field_1'` | `'prefix_field_0'`, `'prefix_field_1'` | recorded id (id present) |
| default `auto_id='id_%s'` | `RadioSelect` | `'id_name_0'`, `'id_name_1'` | `'id_name_0'`, `'id_name_1'` | recorded id (id present) |
| `auto_id=False` (no id generation) | `Select` | (no `'id'` key) | `None` | `None` (id absent) |

The pre-patch property returned `'id_%s_%s' % (name, index)` =
`'id_field_0'` / `'id_name_0'` regardless: it honoured neither the configured
prefix (config 1 → wrong `'id_field_0'`) nor the absence (config 3 → wrong
`'id_name_0'` instead of `None`). That divergence is exactly what
`model_prepatch.py` reproduces and the spec's clauses (1)+(2) reject. Docs /
source: CPython `dict.get`; Django `django/forms/widgets.py` `ChoiceWidget`.

**Soundness check (G-AX):** `axiom_check.py` builds real Django forms for the
three configurations above (and fuzzes the choice count / prefix / a
widget-level `attrs['id']`), drives `form[field].subwidgets`, and for every
subwidget asserts the (post-patch) `BoundWidget.id_for_label` equals
`subwidget.data['attrs'].get('id')` — confirming the deep model is the real
property. It imports only Django itself (configured minimally) and the standard
library. Exit 0 iff sound.
