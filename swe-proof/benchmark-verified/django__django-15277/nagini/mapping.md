# mapping.md — django__django-15277

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 30613d6a748fce18919ff8b0da166d9fda2ed9bc`, states the type
abstraction, and gives the provenance of each kind-A reference (the deep model
is validated against these real callees by axiom_check.py / G-AX; no axiom is
consumed).

Repo file under change: `django/db/models/fields/__init__.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_char_validators(max_length)` | the validator-assembly statement of `CharField.__init__` — `django/db/models/fields/__init__.py:1010-1013` (the assembly line is `:1013`) | the modeled changed function: the constructor decision whether to assemble a length validator |
| `compare_length(value_length, limit)` *(deep model — A-reference)* | `MaxLengthValidator.compare(a, b)` (`a > b`) and the comparison performed in `BaseValidator.__call__` — `django/core/validators.py:390-391, 326-331` | pure spec: the numeric "exceeds the limit" test one length validator performs, undefined on an absent limit |
| `clean_charfield(max_length, value_length)` | the observable cleaning path: `Field.clean` → `Field.run_validators` → `BaseValidator.__call__` → `MaxLengthValidator.compare` — `django/db/models/fields/__init__.py:664-673, 617-631`; `django/core/validators.py:326-331` | end-to-end consequence: cleaning a freshly constructed field never fails on an absent limit |
| `LimitComparisonError` | the `TypeError` raised by `len(value) > None` inside `MaxLengthValidator.compare` when `limit_value is None` (`django/core/validators.py:391`) | user-defined exception standing in for that `TypeError` (see §2) |
| `max_length` (`Optional[int]`) | `Field.max_length` / `CharField`'s `max_length` kwarg — set in `Field.__init__` (`django/db/models/fields/__init__.py:143`) | the optional maximum-length attribute |
| element of the assembled list (`Optional[int]`) | the `limit_value` of one `MaxLengthValidator` (`BaseValidator.__init__`, `django/core/validators.py:321-322`) | the limit of one assembled length validator |

The pre-patch repo behaviour the change fixes (for the refinement audit, not
referenced from the consumer spec view): `CharField.__init__` at `:1013`
unconditionally executes
`self.validators.append(validators.MaxLengthValidator(self.max_length))`, so
when `max_length is None` the assembled list contains a `MaxLengthValidator`
whose `limit_value is None`; a later `clean()` then evaluates
`len(value) > None` in `MaxLengthValidator.compare` and raises `TypeError`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `CharField.max_length` (`int` or `None`) | `max_length: Optional[int]` | identity: a positive `int` ↔ that `int`; `None` ↔ `None` |
| `self.validators` list — specifically its `MaxLengthValidator` element(s) | `List[Optional[int]]` of limits | a `MaxLengthValidator` with `limit_value = L` ↔ the list element `L`; the model abstracts each length validator to its sole behaviour-relevant datum, its limit. Only the length-validator slot is modeled (the other validators a `CharField` carries — `default_validators` — are unchanged by the patch, independent of `max_length`, and do not raise on `clean`, so they are unobserved). |
| `MaxLengthValidator(self.max_length)` construction (`validators.py:321-322`) | `validators.append(max_length)` | constructing the validator with limit `max_length` ↔ appending `max_length` to the list of limits |
| length of a candidate value `len(value)` (the `clean`/`cleaned` value, `validators.py:327,393`) | `value_length: int` | identity on the integer length |
| `MaxLengthValidator.compare(a, b) == a > b` (`validators.py:390-391`) | `value_length > limit` | identity numeric comparison |
| `TypeError` from `len(value) > None` | `LimitComparisonError` via `Exsures` | a builtin exception in an `Exsures` crashes the Nagini translator (SPEC_GUIDE §2 / banned constructs), so the undefined-comparison failure is carried by a user-defined exception class with the same trigger condition (`limit is None`) |
| `Field.clean` / `run_validators` control flow (`fields/__init__.py:664-673, 617-631`) | the loop in `clean_charfield` over the assembled limits | running each validator ↔ iterating the limits and performing each comparison; `run_validators` swallows only `ValidationError` (`fields/__init__.py:625`), NOT the `TypeError`, so the `TypeError` propagates out of `clean` exactly as the model's un-caught `LimitComparisonError` does |

## 3. Callee provenance (kind-A references — checked by G-AX / axiom_check.py)

This bundle consumes **no `@ContractOnly` axiom**: the changed operation (the
guarded assembly + the length comparison) is modeled **deeply** in `model.py`.
The deep model is validated **== the real callees** out-of-band by
axiom_check.py (G-AX). The references:

### 3.1 `compare_length` deep model ↔ `MaxLengthValidator.compare` (A-reference)
**Callee:** `django/core/validators.py:383-394`.
```python
class MaxLengthValidator(BaseValidator):
    code = 'max_length'
    def compare(self, a, b):
        return a > b
    def clean(self, x):
        return len(x)
```
and the harness in `BaseValidator.__call__` (`validators.py:326-331`):
```python
def __call__(self, value):
    cleaned = self.clean(value)                       # = len(value)
    limit_value = self.limit_value() if callable(self.limit_value) else self.limit_value
    ...
    if self.compare(cleaned, limit_value):            # = len(value) > limit_value
        raise ValidationError(...)
```
So a `MaxLengthValidator` with limit `L`, run on a value of length `n`, computes
`n > L`. When `L is None` (the only way `limit_value` is absent for a
`CharField`, set from `max_length=None`), `n > None` raises `TypeError`. This is
exactly `compare_length`'s `Ensures(Result() == (value_length > limit))` and
`Exsures(LimitComparisonError, limit is None)`. G-AX asserts `v.compare(a, b) ==
(a > b)` over fuzz and that `MaxLengthValidator(None)` cannot compare without a
`TypeError`. (`limit_value` callable case is irrelevant here: a `CharField`'s
`max_length` is a plain `int`/`None`, never a callable — Django's docs and
`fields/__init__.py:143`.)

### 3.2 `build_char_validators` deep model ↔ gold-patched `CharField.__init__` (A-reference)
**Site:** `django/db/models/fields/__init__.py:1010-1013`. The gold patch is:
```python
-        self.validators.append(validators.MaxLengthValidator(self.max_length))
+        if self.max_length is not None:
+            self.validators.append(validators.MaxLengthValidator(self.max_length))
```
Hence the assembled `validators` list (for its `MaxLengthValidator` element):
empty when `max_length is None`; a single `MaxLengthValidator(max_length)`
otherwise. This is `build_char_validators`'s posts. G-AX inspects the real
`CharField().validators` (no `MaxLengthValidator` when `max_length=None`) and
`CharField(max_length=n).validators` (exactly one with `limit_value == n`).
(Precedent for the empty-slot behaviour: `BinaryField.__init__` already guards
its `MaxLengthValidator` append on `max_length is not None` — see the problem
statement.)

### 3.3 `clean_charfield` ↔ `Field.clean` end-to-end (A-reference)
**Path:** `Field.clean` (`fields/__init__.py:664-673`) → `run_validators`
(`:617-631`) → each `validator(value)` → `MaxLengthValidator.__call__`. The
observable the F2P test (`test_output_field_does_not_create_broken_validators`)
exercises is that `CharField()._resolve-derived field` with `max_length=None`
can be `.clean(value, model_instance=None)`-ed without raising. G-AX calls the
real `CharField().clean("...", model_instance=None)` and asserts it returns
normally; pre-patch this raises `TypeError`. Note `run_validators` catches only
`exceptions.ValidationError` (`:625`), so a `TypeError` from the broken
comparison is NOT swallowed — it propagates out of `clean`, matching the model's
un-caught `LimitComparisonError`.

**Soundness check (G-AX):** `axiom_check.py` runs (1) a self-contained
faithfulness check of the comparison model (numeric `>` + None-raise) over 64
boundary + 20000 fuzz pairs with no Django, then (2)-(4) the Django-backed
checks above against the real `MaxLengthValidator` / `CharField`. It imports
only `django` (the repo under test) plus stdlib; Django needs a minimal
in-process settings configuration (no DB — constructing a field and calling
`.clean()` never opens a connection). Exit 0 iff every obligation holds; outside
the container it runs the self-contained half and SKIPs the Django half.
