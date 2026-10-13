# mapping.md — django__django-11551

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 7991111af12056ec9a856f35935d273526338c1f`, states the type
abstraction, and gives the provenance of each unchanged primitive the routine
consults.

Repo file under change: `django/contrib/admin/checks.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `check_display_item(...)` | `ModelAdmin checks `_check_list_display_item(self, obj, item, label)` — `django/contrib/admin/checks.py:718-749` | the modeled changed function (validator for one display entry) |
| `is_invokable` (param) | `callable(item)` — `checks.py:719` | observation of the unchanged builtin `callable`: is the entry itself directly invokable |
| `is_presenter_attr` (param) | `hasattr(obj, item)` — `checks.py:721` | observation of the unchanged builtin `hasattr` on the presenter object `obj` (the `ModelAdmin`) |
| `structural_absent` (param) | whether `obj.model._meta.get_field(item)` raises `FieldDoesNotExist` — `checks.py:725` (post-patch `724-726`) | observation of the unchanged metadata lookup `Options.get_field` (`django/db/models/options.py:560`) |
| `structural_is_relation` (param) | `isinstance(field, models.ManyToManyField)` applied to the field returned by `get_field` — `checks.py:729` | observation of the unchanged `isinstance`/`ManyToManyField` test on the structural field |
| `attribute_absent` (param) | whether `getattr(obj.model, item)` raises `AttributeError` (equivalently `not hasattr(obj.model, item)`) — `checks.py:723` (pre-patch) / the inner `getattr(obj.model, item)` in the `except FieldDoesNotExist:` block (post-patch) | observation of the unchanged builtin attribute lookup on the model class |
| `attribute_is_relation` (param) | `isinstance(field, models.ManyToManyField)` applied to the value returned by `getattr(obj.model, item)` — post-patch `checks.py` (the shared `isinstance` after the try/except) | observation of the unchanged `isinstance`/`ManyToManyField` test on the attribute value |
| return value (`int`) | the returned list of `checks.Error` (empty, or one `admin.E108`, or one `admin.E109`) | 0 ↔ `[]`; 108 ↔ `[Error(... id='admin.E108')]`; 109 ↔ `[Error(... id='admin.E109')]` |

The decision logic over these observations is the operation the patch changes;
it is modeled **deeply** (the spelled-out control flow in the `impl` region).
None of the consulted primitives is changed by the patch, so none is the
"function under spec"; each is reduced to the boolean observation it produces.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `callable(item)` (a `bool`) | `is_invokable: bool` | identical boolean |
| `hasattr(obj, item)` (a `bool`) | `is_presenter_attr: bool` | identical boolean |
| `try: get_field(item) except FieldDoesNotExist` (raise-or-return) | `structural_absent: bool` + `structural_is_relation: bool` | `structural_absent == True` ⇔ `get_field` raises `FieldDoesNotExist`; when it returns a field `f`, `structural_is_relation == isinstance(f, ManyToManyField)` |
| `try: getattr(obj.model, item) except AttributeError` (raise-or-return) | `attribute_absent: bool` + `attribute_is_relation: bool` | `attribute_absent == True` ⇔ `getattr` raises `AttributeError`; when it returns a value `v`, `attribute_is_relation == isinstance(v, ManyToManyField)` |
| `isinstance(field, models.ManyToManyField)` (a `bool`) | `*_is_relation: bool` | identical boolean, carried per resolution source |
| return `[]` / `[Error(id='admin.E108')]` / `[Error(id='admin.E109')]` | `int` ∈ {0, 108, 109} | the returned list is length 0, or a single error whose `id` is the corresponding code; the F2P/P2P tests observe exactly which (length + `id`) |

A `try/except` that may raise is the canonical Nagini refinement of a
raise-or-return callee to a pair (a "raised?" boolean plus the observation made
on the returned value when it did not raise). The changed function's *content*
is the control flow that decides, from these observations, which of the three
verdicts to emit; that content is expressible directly and is modeled deeply,
so there is no kind-A axiom to consume.

## 3. Callee provenance (the unchanged primitives reduced to observations)

These are NOT `@ContractOnly` axioms the proof consumes (the proof depends only
on the deeply-modeled decision logic); they are the unchanged callees whose
single observation each parameter encodes. `axiom_check.py` (G-AX) exercises the
real decision logic over every combination of these observations to confirm the
model's verdict matches the patched routine's verdict.

### 3.1 `callable` / `hasattr` — Python builtins
`callable(item)` is true iff `item` is callable; `hasattr(obj, item)` is true
iff `getattr(obj, item)` does not raise. Standard builtins, unchanged by the
patch. (`checks.py:719,721`.)

### 3.2 `Options.get_field` — `django/db/models/options.py:560`
```python
def get_field(self, field_name):
    try:
        return self._forward_fields_map[field_name]
    except KeyError:
        ...
        raise FieldDoesNotExist("%s has no field named '%s'" % (...))
    ...
    raise FieldDoesNotExist("%s has no field named '%s'" % (...))
```
Returns the field instance for a declared forward/reverse field, else raises
`django.core.exceptions.FieldDoesNotExist`. Unchanged by the patch. The patch
moves WHEN it is called (it is now attempted before, not gated by, the model
attribute test), not WHAT it does. Modeled by `structural_absent`
(= "raised `FieldDoesNotExist`") plus `structural_is_relation`.

### 3.3 `getattr(obj.model, item)` — Python builtin attribute access
Returns the attribute value, or raises `AttributeError` if the descriptor or
class does not provide it. A descriptor whose `__get__` raises `AttributeError`
when accessed on the class (e.g. the `PositionField` in the F2P test) makes
`getattr(obj.model, item)` raise — i.e. `attribute_absent == True` — even though
`get_field(item)` succeeds. Unchanged by the patch. Modeled by
`attribute_absent` plus `attribute_is_relation`.

### 3.4 `isinstance(field, models.ManyToManyField)` — `django/db/models/fields/related.py:1091`
`ManyToManyField` is the relation field that cannot be displayed in a single
column; the wrong-kind diagnostic (`admin.E109`) is produced exactly when the
resolved object is an instance of it. Unchanged by the patch; modeled by the
`*_is_relation` booleans. The patch's change is that this test is now applied to
the object obtained from EITHER lookup (structural or attribute), not only the
structural one.

## 4. The diagnostic codes
`admin.E108` ("refers to '%s', which is not a callable, an attribute of '%s', or
an attribute or method on '%s.%s'") and `admin.E109` ("must not be a
ManyToManyField") are the two error ids the routine can emit (`checks.py`,
unchanged strings). The model abstracts each emitted single-error list to its
integer code (108 / 109) and the empty (valid) list to 0 — the exact
length-and-`id` distinction the `CheckTestCase.assertIsValid` /
`assertIsInvalid` assertions observe.
