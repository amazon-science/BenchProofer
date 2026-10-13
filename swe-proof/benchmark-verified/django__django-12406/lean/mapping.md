# mapping.md — django__django-12406

Cold construction. Spec derived solely from `problem_statement`, the gold
`patch`, and the repo source at `base_commit`
(`335c9c94acf263901fb023404408880245b0c4b4`).

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_emptyOption` / `problem_spec_emptyOption` / `correct_emptyOption` | `ModelChoiceField.__init__` empty-label decision | `django/forms/models.py:1184-1191` |
| `implementation_formKwargs` / `problem_spec_formKwargs` / `correct_formKwargs` | `ForeignKey.formfield` form-field kwargs assembly | `django/db/models/fields/related.py:973-983` |

Both functions are CHANGED by the gold patch and are modeled deeply (no callee is
axiomatized). The two are independently observable (see G-DIFF: one prepatch per
behavior).

## Behavior 1 — `ModelChoiceField.__init__` (forms/models.py)

At base_commit the empty-label decision is:

```python
if required and (initial is not None):
    self.empty_label = None
else:
    self.empty_label = empty_label
```

The gold patch adds a keyword-only parameter `blank=False` and widens the
condition to:

```python
if (
    (required and initial is not None) or
    (isinstance(self.widget, RadioSelect) and not blank)
):
    self.empty_label = None
else:
    self.empty_label = empty_label
```

`self.empty_label` is the single mutated field. When it is `None`, the
`ModelChoiceIterator.__iter__` (forms/models.py:1148-1150) does NOT yield the
leading `("", empty_label)` blank choice; when it is the label string, it does.
So the empty-label value is exactly the observable that the F2P tests
(`test_choices_radio_blank`, `test_*_foreign_key_with_radio`) assert on through
`list(field.choices)`.

### Lean ↔ Python type bijection (behavior 1)

| Python | Lean | bijection |
|---|---|---|
| `required: bool` | `required : Bool` | identity |
| `initial is not None` | `initialPresent : Bool` | `True ↔ initial is not None` |
| `isinstance(self.widget, RadioSelect)` | `radioWidget : Bool` | `True ↔ widget is a RadioSelect (incl. subclasses)` |
| `blank: bool` | `blankAllowed : Bool` | identity |
| `empty_label: str` keyword (default `"---------"`) | `defaultLabel : String` | identity (value-level string) |
| `self.empty_label` result (`str | None`) | `result : Option String` | `None ↔ None`, `some s ↔ s` |

The four-row truth-table over `(required, initialPresent, radioWidget,
blankAllowed)` was confirmed against the patched real callee in-container
(see G-AX `axiom_check.py`): `empty_label is None` iff
`(required ∧ initialPresent) ∨ (radioWidget ∧ ¬blankAllowed)`.

## Behavior 2 — `ForeignKey.formfield` (related.py)

At base_commit `formfield` builds the kwargs dict passed to the super
`formfield` (which constructs the `ModelChoiceField`):

```python
return super().formfield(**{
    'form_class': forms.ModelChoiceField,
    'queryset': ...,
    'to_field_name': ...,
    **kwargs,
})
```

The gold patch appends one entry:

```python
    **kwargs,
    'blank': self.blank,
```

i.e. it plumbs the model field's `blank` attribute into the form-field kwargs so
behavior 1 can consume it. The dict is built then has `'blank'` set last (after
the caller-supplied `**kwargs`), so `'blank'` is unconditionally `self.blank`,
overriding any incoming `blank` in `kwargs`. Every OTHER key is unchanged from
the pre-patch dict.

### Lean ↔ Python type bijection (behavior 2)

| Python | Lean | bijection |
|---|---|---|
| the kwargs dict BEFORE the added `'blank'` entry (`form_class`/`queryset`/`to_field_name`/`**kwargs`) | `base : Std.HashMap String KwargVal` | key→value map; key = Python dict key (`String`) |
| dict value (a class / queryset / name / flag) | `KwargVal` (`obj | name (Option String) | flag Bool`) | tagged-union abstraction of the heterogeneous values; only the `blank` flag's value matters for the fix |
| `self.blank: bool` | `blankAllowed : Bool` | identity |
| resulting kwargs dict | `result : Std.HashMap String KwargVal` | key→value map |

`base` models the dict as assembled up to and excluding the new `'blank'` key
(after `**kwargs` merge). Modeling it as the pre-patch dict makes the frame
obligation precise: `result["blank"]? = blank` AND every other key equals its
`base` value. Confirmed in-container: `kwargs['blank'] == self.blank` for both
`blank=False` and `blank=True` ForeignKeys, all other keys identical.

## Callee provenance / flag deps

- No UNCHANGED callee needs an axiom. Both changed functions are modeled deeply
  with concrete Lean operations (a Boolean conditional; a `HashMap.insert`).
  → `axioms` region is EMPTY; `axiom_check.py` is a skip stub.
- `RadioSelect` membership is captured as the abstract `radioWidget : Bool`
  (the `isinstance` test, which is `True` for `RadioSelect` and its subclasses).
  The flag dependency is: the radio branch only forces `empty_label = None` when
  `not blank`.

## G-CONF fuzz seed

Pinned seed: **20240612**. `conformance_check.py` enumerates the full
`(required, initial, widget∈{None,RadioSelect,Select}, blank)` matrix for
behavior 1 against the patched real `ModelChoiceField.__init__`, and the
`blank ∈ {False, True}` cases for behavior 2 against the patched real
`ForeignKey.formfield`, plus ≥10⁵ randomized draws over those discrete domains.
