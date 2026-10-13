# mapping.md — django__django-15277

## Symbol binding (file:line @ base_commit `30613d6a748fce18919ff8b0da166d9fda2ed9bc`)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_buildFieldValidators` | `CharField.__init__` (the validator-attachment portion) | `django/db/models/fields/__init__.py:1010-1013` |
| `maxLength : Option Int` | `self.max_length` (the field's declared maximum length, default `None`) | set in `Field.__init__`, `django/db/models/fields/__init__.py:143` (`max_length=None` default) |
| `base : List Validator` | `self.validators` BEFORE the append — i.e. `[*default_validators, *_validators]` | `Field.validators` cached_property, `django/db/models/fields/__init__.py:610-615` |
| `Validator.lengthBound (limit : Option Int)` | `validators.MaxLengthValidator(self.max_length)` — a max-length-enforcing validator carrying its limit | `django/core/validators.py` `MaxLengthValidator`, instantiated at `fields/__init__.py:1013` |
| `Validator.basic (tag : Nat)` | any other validator object already present (e.g. a `default_validators` entry or a passed-in `validators=` entry) | `Field.default_validators` / `Field._validators` |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX

| Python | Lean | notes |
|---|---|---|
| `self.max_length` is `None` | `maxLength = none` | the field declares no maximum length |
| `self.max_length == n` (a positive int) | `maxLength = some n` | the declared maximum length |
| `self.validators` list (a Python `list`) | `List Validator` | ordered; the append adds at the END |
| `MaxLengthValidator(self.max_length)` | `Validator.lengthBound maxLength` | the validator's `limit_value` IS `self.max_length`. A `MaxLengthValidator(None)` (the value that raises in `.clean()`) ↔ `Validator.lengthBound none` |
| other validator object | `Validator.basic tag` | identity-only stand-in; `tag` distinguishes distinct other validators |

### Bridging note (the observable the fix governs)
The fixed behavior is entirely about *which validators end up in the list*. A
`MaxLengthValidator` whose `limit_value` is `None` is the validator that cannot
operate (`.clean()` → `compare` does `value > None` → `TypeError`). The function
either does or does not place that validator into the list, depending on whether
a maximum length was declared. We therefore model the list-construction exactly
(`base ++ conditional append`) and represent the attached validator by its
optional limit — `Validator.lengthBound none` is precisely the unusable
validator the post-patch code avoids creating.

## Callee provenance
No UNCHANGED outside callee is consumed. `MaxLengthValidator`'s *construction* is
the operation the fix gates, so it is modeled deeply (its presence/absence in the
list), NOT axiomatized (SPEC_GUIDE §3, §0.7). `list.append` and the
`max_length is not None` test are concrete ops. Hence: no `opaque`/`axiom`
declarations, `axiom_check.py` is a skip stub, G-AX skips.

## Flag dependencies
None. The append depends only on whether `self.max_length is None`.

## G-CONF fuzz seed
Pinned seed: **15277** (also in `conformance_check.py`).
