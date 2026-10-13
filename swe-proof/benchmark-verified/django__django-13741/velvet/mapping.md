# mapping.md — django__django-13741

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = d746f28949c009251a8741ba03d156964050717f`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each axiom.

Repo file under change: `django/contrib/auth/forms.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `readonlyDigestFieldLocked (userFlag : Option Bool)` | `ReadOnlyPasswordHashField.__init__` — `django/contrib/auth/forms.py:59` | the modeled changed function: the constructor whose default for the non-editability flag changes |
| `lockedDefault (userFlag : Option Bool)` | the `kwargs.setdefault('disabled', True)` step (post-patch `forms.py:62`) layered over base `Field.__init__(..., disabled=False)` (`django/forms/fields.py:57`) | pure spec: the non-editability flag a freshly built field ends with — caller value if given, else the locked default |
| `noEditChange` *(axiom — A-consumed)* | `Field.has_changed(self, initial, data)` — `django/forms/fields.py:175` (the `if self.disabled: return False` guard, line 179) | unchanged base callee: a non-editable field never reports a change |
| `noEditValue` *(axiom — A-consumed)* | `Field.bound_data(self, data, initial)` — `django/forms/fields.py:154` (the `if self.disabled: return initial` guard, line 163) | unchanged base callee: a non-editable field exposes its stored value when bound |

The pre-patch repo symbols the change removes (refinement audit only, not in the
consumer spec view): the bespoke `ReadOnlyPasswordHashField.bound_data`
(`forms.py:64-67`, `return initial`) and `ReadOnlyPasswordHashField.has_changed`
(`forms.py:69-70`, `return False`), and `UserChangeForm.clean_password`
(`forms.py:159-164`, `return self.initial.get('password')`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the constructor's optional `disabled` keyword: absent, or `True`/`False` | `Option Bool` | `kwargs` has no `'disabled'` key ↔ `none`; `disabled=b` ↔ `some b`. The carrier is three-valued because `setdefault` only fires when the key is ABSENT — `none` is the case the change governs. |
| `self.disabled : bool` after construction | Lean `Bool` | `True ↔ true`, `False ↔ false` |
| `initial` / `data` field values (the password-hash strings the hooks receive) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; the hooks' results are observed by character content. The value domain is irrelevant to the disabled-guard outcome (the guard returns before inspecting content), so any carrier the hooks accept is faithful; `List Char` is the natural one for the string values the field carries. |
| `has_changed(initial, data)` return | Lean `Bool` | `True ↔ true`, `False ↔ false` |
| `bound_data(data, initial)` return | Lean `List Char` | the returned value's character content |

`Option Bool` is exact for the three observable construction cases; `Bool` is
exact for the field's resulting `disabled` attribute and for `has_changed`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

The CHANGED operation (the default for the non-editability flag) is NOT
axiomatized — it is modeled directly by `lockedDefault` (an R/I op in the impl
region) and refuted by G-CONF (§4). The axioms cover only the two UNCHANGED base
`Field` callees the deletion-safety of the patch relies on.

### 3.1 `noEditChange` ↔ `Field.has_changed` (A-consumed)
**Callee:** `django.forms.fields.Field.has_changed(self, initial, data)`. Its
first action is `if self.disabled: return False` (`fields.py:179`). The axiom
encodes the WEAKEST contract the proof needs: when the field is non-editable
(`disabled is True`), `has_changed` returns `False` for ALL `initial`, `data`.
Nothing is claimed about the editable (`disabled is False`) path — irrelevant to
the desired behaviour.

### 3.2 `noEditValue` ↔ `Field.bound_data` (A-consumed)
**Callee:** `django.forms.fields.Field.bound_data(self, data, initial)`. Its
first action is `if self.disabled: return initial` (`fields.py:163`). The axiom
encodes: when the field is non-editable, `bound_data` returns the stored
`initial`, discarding `data`, for ALL `data`, `initial`.

**Soundness check (G-AX):** the two axioms are about the UNCHANGED base
`django.forms.fields.Field` class, so G-AX runs against the repo **as checked
out** (no patch applied — that is G-CONF's job for the changed default).
`axiom_check.py` constructs a real non-editable field by passing `disabled=True`
explicitly — both `ReadOnlyPasswordHashField(disabled=True)` and a generic
`forms.Field(disabled=True, required=False)`, which route through base
`Field.__init__` identically at base_commit and post-patch — and asserts, over
boundary + 20 000 fuzz `(initial, data)` pairs, that the real `has_changed`
returns `False` and the real `bound_data` returns `initial`. It also asserts an
editable field (`disabled=False`) is NOT constrained by these axioms (the axioms
only fire on `disabled is True`), guarding against over-claim. Imports django
only. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13741`**. The R/I
shadow it builds transliterates `lockedDefault` to Python
(`userFlag if userFlag is not None else True`) and diffs it against the gold
patch's behaviour: the `self.disabled` attribute of a real
`ReadOnlyPasswordHashField` constructed with the corresponding `disabled` kwarg
(absent ↔ `none`; `disabled=b` ↔ `some b`), over the three flag cases crossed
with randomized orthogonal kwargs (`required`, `label`, `initial`) for ≥10⁵
constructions. The impl region's computed `out` is pure R/I (the `noEdit*`
axioms appear only in postconditions, never in `out`), so `conf_skip=false`.
