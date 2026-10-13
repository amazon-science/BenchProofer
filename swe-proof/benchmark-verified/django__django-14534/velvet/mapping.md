# mapping.md — django__django-14534

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 910ecd1b8df7678f45c3d507dde6bcb1faafa243`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `django/forms/boundfield.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `labelIdentifier (name : String) (index : String) (attrs : Attrs)` | `BoundWidget.id_for_label` — `django/forms/boundfield.py:278-280` (the `@property` body) | the modeled changed function: the identifier used when rendering a label that points at one rendered widget |
| `name : String` | `self.data['name']` — the widget's field name | recorded datum of one widget (read only) |
| `index : String` | `self.data['index']` — the widget's position among sibling widgets | recorded datum of one widget (read only) |
| `attrs : Attrs` (`List (String × String)`) | `self.data['attrs']` — the widget's recorded HTML attributes mapping | recorded datum of one widget; the only datum the desired behavior reads |
| `recordedId (attrs : Attrs)` *(deep model)* | the post-patch lookup `self.data['attrs'].get('id')` — `boundfield.py:280` post-patch | pure spec: the recorded `"id"` attribute (present ⇒ its value, absent ⇒ `None`); modeled deeply, NOT an axiom |
| `out : Option String` | the return value of `id_for_label` (`str` or `None`) | the label identifier, or absent |

The pre-patch repo behaviour the change fixes (refinement audit only, not in the
consumer spec view): `id_for_label` returned
`'id_%s_%s' % (self.data['name'], self.data['index'])` (`boundfield.py:280`
pre-patch) — an identifier SYNTHESIZED from the widget's name and position,
ignoring the identifier the surrounding rendering already recorded in
`self.data['attrs']['id']`. That synthesized string disagrees with the recorded
id whenever a non-default `auto_id` prefix was used (e.g. `prefix_field_0`
vs. the synthesized `id_field_0`), and is a non-`None` string even when no id was
recorded (e.g. it returned `id_name_0` where the recorded attrs had no `'id'`,
so the correct result is `None`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.data['attrs']`, the widget's recorded HTML attributes mapping (`dict[str, str]`) | `Attrs = List (String × String)` | a `dict` of attribute name → value ↔ an ordered list of key/value pairs; a name occurs at most once; `attrs.get(k)` ↔ `List.lookup k attrs` (`some v` when present, `none` when absent). Attribute values are HTML-attribute strings (the `'id'` value is the only one read). |
| `self.data['name']` (`str`) | `name : String` | identity on the field-name string. Read but not consulted by the desired behavior. |
| `self.data['index']` (`str`/`int` rendered to `str`) | `index : String` | identity on the position rendered as text. Read but not consulted by the desired behavior. |
| the return value `str` or `None` | `out : Option String` | `None` ↔ `none`; a `str` id ↔ `some s`. `dict.get('id')` returns `None` for a missing key ↔ `List.lookup "id"` returns `none`. |

`self.data['attrs']` is built by `BoundField.subwidgets` from
`id_ = self.field.widget.attrs.get('id') or self.auto_id` and threaded through
`widget.subwidgets(...)`, which records the per-subwidget `'id'` (the resolved
`auto_id`, with any caller prefix and the subwidget index already applied). The
modeled function reads that recorded `'id'` back; how it was computed upstream is
UNCHANGED by the patch and outside the modeled function (it is an input here).

## 3. Callee provenance

No consumed axioms; no deep-model reference to a concrete external callee.

- **`recordedId` (the recorded-id lookup).** The post-patch body is a single
  total mapping lookup, `self.data['attrs'].get('id')`. It is modeled DEEPLY by
  `recordedId attrs = attrs.lookup "id"` (the `pure` region), NOT behind an axiom
  about the function under change (directive 7). Its fidelity to the gold patch
  is audited mechanically by G-CONF (`conformance_check.py`). `.get('id')` is a
  stdlib `dict` method, not a repo callee, and is exercised directly by G-CONF;
  there is nothing to over-approximate, so no `axiom` is owed.

There is therefore no `axiom_check.py` for this bundle (`meta.json gates.G-AX =
skip`, like django__django-14752 / django__django-11149).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14534`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `labelIdentifier`/`recordedId` (the deep lookup model) to Python
and runs it against the gold-patched `BoundWidget.id_for_label` body
(`self.data['attrs'].get('id')`, transliterated verbatim) over many widget-data
points: attrs with an `'id'` (including caller-prefixed ids and the index in the
id), attrs without an `'id'` (the `None` case), and varying `name`/`index` that
the desired behavior must NOT consult. The whole impl region is R/I (no A-tagged
callee in the computed `out`), so `conf_skip = false`.
