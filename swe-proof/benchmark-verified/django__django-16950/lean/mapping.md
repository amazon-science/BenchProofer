# mapping.md — django__django-16950

## Symbol binding (file:line @ base_commit f64fd47a7627ed6ffe2df2a32ded6ee528a784eb)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_clearParentKeyDefault` / `problem_spec_clearParentKeyDefault` | `django.forms.models.BaseInlineFormSet.add_fields` (the `_state.adding` block that conditionally resets the parent key attribute) | `django/forms/models.py:1173-1181` |

The modeled function is `BaseInlineFormSet.add_fields`. The whole method also
computes `name`/`kwargs` and installs an `InlineForeignKeyField`; those parts are
UNCHANGED by the patch and behavior-irrelevant to the fixed observable. The only
behavior the patch changes — and the only behavior the FAIL_TO_PASS test
observes — is the conditional reset of the parent instance's key attribute to
`None`.

### What the relevant block does (base_commit, PRE-FIX)

```python
def add_fields(self, form, index):
    ...
    # If we're adding a new object, ignore a parent's auto-generated key
    # as it will be regenerated on the save request.
    if self.instance._state.adding:
        if kwargs.get("to_field") is not None:
            to_field = self.instance._meta.get_field(kwargs["to_field"])
        else:
            to_field = self.instance._meta.pk
        if to_field.has_default():                      # <-- the changed guard (pre-fix)
            setattr(self.instance, to_field.attname, None)
    form.fields[name] = InlineForeignKeyField(self.instance, **kwargs)
```

POST-FIX the guard gains a second factor:

```python
        if to_field.has_default() and (
            # Don't ignore a parent's auto-generated key if it's not the
            # parent model's pk and form data is provided.
            to_field.attname == self.fk.remote_field.model._meta.pk.name
            or not form.data
        ):
            setattr(self.instance, to_field.attname, None)
```

So `self.instance.<to_field.attname>` is reset to `None` iff:

* PRE-FIX: `self.instance._state.adding` **and** `to_field.has_default()`.
* POST-FIX: `self.instance._state.adding` **and** `to_field.has_default()`
  **and** (`to_field.attname == self.fk.remote_field.model._meta.pk.name`
  **or** `not form.data`).

Otherwise the attribute keeps its current value.

### Input observable bijection

The fixed decision reads exactly four booleans plus the attribute's current
value. The modeled function takes those observables directly.

| Lean input | Python expression | notes |
|---|---|---|
| `adding : Bool` | `self.instance._state.adding` | whether the parent instance is being newly added (not yet saved). The reset block is entirely inside this guard. |
| `hasDefault : Bool` | `to_field.has_default()` | whether the resolved key field carries a default value. `to_field` is `self.instance._meta.get_field(kwargs["to_field"])` when a `to_field` kwarg was set (alternate key relation), else `self.instance._meta.pk`. Its `has_default()` is the observable. |
| `isParentPk : Bool` | `to_field.attname == self.fk.remote_field.model._meta.pk.name` | whether the resolved key field IS the parent model's primary key. `True` for the ordinary pk relation; `False` for an alternate-key (`to_field=`) relation. |
| `hasFormData : Bool` | `bool(form.data)` | whether the bound form carries submitted data. The patch uses `not form.data` (truthiness of the `QueryDict`); `hasFormData = bool(form.data)`. |
| `current : V` | `getattr(self.instance, to_field.attname)` (current value of the key attribute) | opaque carrier of the attribute's existing value; the reset logic never inspects it, only either clears it or leaves it. Modeled by a type variable `V`. |

The `to_field` resolution (`get_field` vs `_meta.pk`) and the `kwargs["to_field"]`
selection are UNCHANGED context: they only determine which field's
`has_default()`/`attname` feed the guard. Those are folded into the `hasDefault`
and `isParentPk` observables (just as the eligibility sub-conditions were folded
in django-11433), so the model does not re-derive them.

### Output bijection

| Python | Lean | bijection |
|---|---|---|
| value of `self.instance.<to_field.attname>` after the block | `Option V` | `none` ↔ the attribute was reset to `None`; `some current` ↔ the attribute kept its existing value `current`. Field names are distinct and only this one attribute is touched, so the resulting value of that attribute is a faithful, lossless model of the block's effect. |

The frame is pinned: when the reset does NOT fire, the result equals `some
current` (the input value carried through unchanged — directive 5).

### The fixed decision

`shouldReset = adding && hasDefault && (isParentPk || !hasFormData)` models the
POST-FIX guard exactly:

* `adding` ↔ `self.instance._state.adding`;
* `hasDefault` ↔ `to_field.has_default()`;
* `isParentPk || !hasFormData` ↔ `(to_field.attname == ...pk.name or not form.data)`.

The PRE-FIX guard drops the second factor entirely
(`shouldReset_pre = adding && hasDefault`), so it resets the attribute even for
an alternate key (`isParentPk = false`) when form data is present
(`hasFormData = true`) — the bug.

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| `self.instance._state.adding` (bool) | `adding : Bool` | identity |
| `to_field.has_default()` (bool) | `hasDefault : Bool` | identity |
| `to_field.attname == self.fk.remote_field.model._meta.pk.name` (bool) | `isParentPk : Bool` | identity |
| `bool(form.data)` | `hasFormData : Bool` | identity (`not form.data` ↔ `!hasFormData`) |
| `getattr(self.instance, to_field.attname)` | `current : V` | opaque value carrier |
| resulting `self.instance.<attname>` (`None` or value) | `Option V` | `none ↔ None`, `some current ↔ value` |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — the truth value
  of the reset guard — is modeled DEEPLY as the boolean
  `adding && hasDefault && (isParentPk || !hasFormData)` over the per-call
  observables (SPEC_GUIDE §3: a deeply-modeled changed decision is never
  axiomatized).
- **`has_default()`**, **`to_field.attname == ...pk.name`**, **`bool(form.data)`**,
  and **`_state.adding`** are each modeled as a `Bool` observable. The proof
  consumes no contract about them beyond their boolean value, which the inputs
  carry directly.
- **`setattr(self.instance, to_field.attname, None)`** is not a consumed callee:
  its effect is captured by the `Option V` result (`none`).
- **Flag dependency:** the fix's discriminator is the second factor
  `(isParentPk or not hasFormData)`. G-CONF fuzzes all 16 combinations of the
  four booleans so the new factor is exercised in both polarities, in particular
  the `adding ∧ hasDefault ∧ ¬isParentPk ∧ hasFormData` case the patch fixes.

## G-CONF fuzz seed

Pinned LCG seed: **16950** (see `conformance_check.py` `SEED`). Corpus: the full
exhaustive enumeration of the 16 boolean combinations (with a fixed opaque
`current`) plus ≥1e5 fuzzed inputs (four random booleans + a random `current`
int), diffed against an in-process replica of the POST-PATCH reset decision.
Hand-picked edge cases pin the discriminating alternate-key-with-data clause.
