# mapping.md — django__django-14034

Binds every `model.py` symbol to its repository counterpart at
`base_commit = db1fc5cd3c5d36cdb5d0fe4404efd6623dd3e8fb`, states the type
abstraction, and gives the provenance of each deep-model reference (the
unchanged Django callees the deep model is validated against by G-AX).

Repo file under change: `django/forms/boundfield.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_required_attrs(out, ...)` | `BoundField.build_widget_attrs(self, attrs, widget=None)` — `django/forms/boundfield.py:232` (body `:235`) | the modeled changed function (assembles the input rendering attributes) |
| `out: Result2` | the local `attrs` dict the method returns (`boundfield.py:234,236,238`) | the aggregate attribute set produced by the method |
| `out.required_attr` | `attrs['required']` key (`boundfield.py:236`) | the aggregate mandatory marker (tri-state: -1 unset / 0 absent / 1 present) |
| `out.disabled_attr` | `attrs['disabled']` key (`boundfield.py:238`) | the aggregate disabled marker |
| `widget_mark` | `widget.use_required_attribute(self.initial)` (`boundfield.py:235`) — `Widget.use_required_attribute`, `django/forms/widgets.py:280` | the field-level widget's mandatory report for the current initial value (a bool) |
| `field_required` | `self.field.required` (`boundfield.py:235`) | the field's own mandatory flag |
| `form_marks` | `self.form.use_required_attribute` (`boundfield.py:235`) | the form-level mandatory switch |
| `is_partial_multi` | `hasattr(self.field, 'require_all_fields') and not self.field.require_all_fields and isinstance(self.field.widget, MultiWidget)` (post-patch `boundfield.py:238-242`) | the per-constituent regime guard |
| `field_disabled` | `self.field.disabled` (`boundfield.py:237`) | the field's disabled flag |
| `subs: List[Constituent]` | `zip(self.field.fields, widget.widgets)` (post-patch `boundfield.py:243`) — `MultiValueField.fields` (`django/forms/fields.py:1001`) paired with `MultiWidget.widgets` (`django/forms/widgets.py:813`) | the constituent (subfield, subwidget) pairs |
| `subs[k].widget_mark` | `subwidget.use_required_attribute(self.initial)` (post-patch `boundfield.py:244`) | constituent subwidget's mandatory report (a bool) |
| `subs[k].field_required` | `subfield.required` (post-patch `boundfield.py:244`) | constituent subfield's own mandatory flag |
| `subs[k].marker` | `subwidget.attrs['required']` (post-patch `boundfield.py:244`) | per-constituent mandatory marker slot (set on each subwidget's attrs) |
| `constituent_marker(wm, fr)` *(deep model — A-reference)* | the assigned value `subwidget.use_required_attribute(self.initial) and subfield.required` (post-patch `boundfield.py:244`) | pure spec: the marker a constituent receives in the per-constituent regime |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the `attrs` dict (`boundfield.py:234`) and its `'required'`/`'disabled'` keys | `Result2` object with two `int` tri-state slots | `attrs['required'] is True` ↔ `required_attr == 1`; key absent ↔ `required_attr == -1`. The method only ever assigns `True` to `attrs['required']`, so the `0` (explicit False) state never arises at the aggregate level (it only arises per-constituent, where the patch assigns a boolean). `attrs['disabled']` similarly. |
| `widget.use_required_attribute(initial)` (any `Widget`) — returns a Python truthy/falsey value | `bool` `widget_mark` | the boolean used in the `and` chain; coerced via `bool(...)` in axiom_check (Django uses it in a boolean `and`, so only truthiness matters) |
| `self.field.required`, `self.form.use_required_attribute`, `subfield.required`, `self.field.disabled` | `bool` | direct |
| `hasattr(field,'require_all_fields') and not field.require_all_fields and isinstance(field.widget, MultiWidget)` | `bool` `is_partial_multi` | the three-way conjunction is opaque to the modeled behavior; its truth value is all the operation consumes, so it is a single bool input. `hasattr(...)` is False for non-`MultiValueField` fields ⇒ `is_partial_multi` is False ⇒ regime B, faithfully. |
| `zip(self.field.fields, widget.widgets)` | `List[Constituent]` | the i-th `Constituent` carries the i-th pair's `(subwidget.use_required_attribute(initial), subfield.required, subwidget.attrs['required'])`. `zip` truncates to the shorter; in Django the two lists are equal length by construction (`MultiWidget` is built from the same fields), so the list length is the common count. |
| `subwidget.attrs['required'] = (bool)` | `subs[k].marker = 1` if the boolean is True else `0` | `True` ↔ `1`, `False` ↔ `0`; untouched (regime B / guard fails) ↔ `-1`. The rendering rule (§3.2) maps `1`→`required` token present, `0`/`-1`→absent. |

`dict` keys are modeled as object fields (tri-state ints) rather than a Nagini
`Dict` because the observable is exactly *which* marker is present, and the
method only assigns a small fixed set of keys.

## 3. Deep-model references (kind A-reference — checked by G-AX / axiom_check.py)

The changed operation is modeled **deeply** (boolean guards + a per-constituent
assignment). There is **no consumed `@ContractOnly` axiom**: nothing opaque is
referenced inside an `Ensures`. The model relies on two facts about the
**unchanged** Django callees, validated by `axiom_check.py` (G-AX) against the
real code in-container.

### 3.1 `constituent_marker` deep model ↔ the per-constituent assignment (A-reference)
**Callee:** `Widget.use_required_attribute(self, initial)` (`django/forms/widgets.py:280`,
base `return not self.is_hidden`; overridden by `CheckboxInput`/`Select`/etc.).
The patch assigns, per constituent,

```python
subwidget.attrs['required'] = subwidget.use_required_attribute(self.initial) and subfield.required
```

model.py encodes this as `constituent_marker(widget_mark, field_required)`,
where `widget_mark := bool(subwidget.use_required_attribute(initial))` and
`field_required := subfield.required`, and

  `constituent_marker(wm, fr) == 1  iff  (wm and fr)  else 0`.

This is the boolean product of the two callee results. `use_required_attribute`
is **unchanged** by the patch. G-AX executes the real callee for every
(subwidget kind ∈ {TextInput, NumberInput, EmailInput, URLInput, PasswordInput,
HiddenInput, Textarea}, initial ∈ {None, '', 'x', '0', 0, [], ['a'], 'Hello'})
combination and asserts the boolean product equals `constituent_marker`.

### 3.2 The rendering rule ↔ the widget `attrs.html` template (A-reference)
**Callee:** the widget rendering, `django/forms/templates/django/forms/widgets/attrs.html`:
`{% if value is not False %} {{ name }}{% if value is not True %}="..."{% endif %}{% endif %}`.
A `required` attr whose value is `True` renders the bare token `required`; a
value of `False` (or an absent key) renders nothing. model.py encodes the
observable as `marker == 1` (present) vs `marker ∈ {0, -1}` (absent). G-AX
renders the real `TextInput` with `attrs={'required': True}`, `{'required':
False}`, and `{}` and asserts the `required` token appears iff the value was
`True`.

**Soundness check (G-AX):** `axiom_check.py` (a) checks §3.1 over all
7×8×2 = 112 (widget, initial, required) combinations plus 20 000 random boolean
pairs; (b) checks §3.2 on the real rendering; (c) reproduces the F2P scenario
end-to-end against the **real patched** `BoundField.build_widget_attrs` +
`form.as_p()` — the required subinput carries `required`, the optional one does
not, and the aggregate `required` is NOT set (regime A) — and (d) confirms an
ordinary required field still gets the aggregate `required` (regime B). It
imports only Django (the package under test) + the standard library. Exit 0 iff
sound.

## 4. Pre-patch repo symbol (for the refinement audit)

The pre-patch body (`boundfield.py:235-236`) is the unconditional
`attrs['required'] = True` inside the guard — no per-constituent branch. This is
reproduced by `model_prepatch.py` (the impl sets `out.required_attr = 1`
whenever the guard holds, even in regime A), which fails the regime-A
postcondition `out.required_attr == -1`.
