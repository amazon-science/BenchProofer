# refinement.md — django__django-11551

Operation correspondence between `implementation_validateDisplayItem` and the
gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real behavior by
G-CONF), **I** (identical concrete op).

No axioms are declared or consumed. The four external operations the changed code
calls — `callable`, `hasattr(obj, …)`, `obj.model._meta.get_field`, and
`getattr(obj.model, …)` (all UNCHANGED) — have their outcomes supplied as the
model inputs (`itemCallable`, `adminHasAttr`, `modelField`, `modelAttr`); the
acceptance/diagnostic control flow that the patch rewrites is modeled DEEPLY.
Every row is **R**, **A-reference**, or **I**. The legs are differential-tested
by G-CONF; G-AX is a skip stub.

## What the gold patch changes (`django/contrib/admin/checks.py`, `_check_list_display_item`)

Pre-patch control flow (the bug):

```python
if callable(item):            return []
elif hasattr(obj, item):      return []
elif hasattr(obj.model, item):           # <-- GATE on attribute access
    try:    field = obj.model._meta.get_field(item)
    except FieldDoesNotExist: return []   # silently accepts
    else:   ... E109 if M2M else []
else:                                     # attribute access failed
    return [E108]                         # never tries get_field
```

The `elif hasattr(obj.model, item)` gate means an entry is only checked for a
field when attribute access on the model class succeeds. A field that exists in
the metadata but is unreachable via attribute access on the class (e.g. a
descriptor that raises `AttributeError` when accessed on the class rather than an
instance) falls into the `else` branch and is wrongly rejected with `E108`.

Post-patch control flow (the fix):

```python
try:    field = obj.model._meta.get_field(item)   # try metadata FIRST
except FieldDoesNotExist:
    try:    field = getattr(obj.model, item)      # fall back to attribute access
    except AttributeError: return [E108]          # only here is it unresolvable
if isinstance(field, models.ManyToManyField): return [E109]
return []
```

A field resolved by EITHER route is accepted (unless M2M); `E108` only when both
routes fail.

## `implementation_validateDisplayItem` ↔ the patched function

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| inputs `itemCallable adminHasAttr : Bool`, `modelField modelAttr : Option Bool` | `callable(item)`, `hasattr(obj, item)`, `get_field(item)` (raise/field), `getattr(model, item)` (raise/value) | R | observables at the decision point; the four UNCHANGED callees' outcomes are the model inputs (mapping.md bijection) |
| `if itemCallable then return []` | `if callable(item): return []` | I | callable entry accepted |
| `if adminHasAttr then return []` | `elif hasattr(obj, item): return []` | I | admin-object attribute accepted |
| `match modelField with \| some m => fieldIsM2M := m` | `try: field = obj.model._meta.get_field(item)` (succeeds) | A-reference | metadata lookup tried FIRST; field's M2M flag captured |
| `\| none => match modelAttr with \| some m => fieldIsM2M := m` | `except FieldDoesNotExist: try: field = getattr(obj.model, item)` (succeeds) | A-reference | fallback to attribute access on `FieldDoesNotExist`; field's M2M flag captured |
| `\| none => return ["E108"]` | `except AttributeError: return [Error(id='E108')]` | A-reference | BOTH routes failed ⇒ unresolvable entry |
| `if fieldIsM2M then return ["E109"]` | `if isinstance(field, models.ManyToManyField): return [Error(id='E109')]` | A-reference | a resolved many-to-many field is rejected |
| `return []` | trailing `return []` | I | a resolved non-M2M field is accepted |

The `checks.Error` wrapper, message strings, and `obj=`/`label` arguments are
unchanged and abstracted to the error `id` (the only behavior the tests assert).

## Independently-observable behaviors (G-DIFF)

One prepatch variant (`Solution_prepatch.lean`) — the actual bug. It reinstates
the attribute-access GATE: field resolution is attempted only when `modelAttr` is
`some _`; if `modelAttr = none` the entry is rejected `["E108"]` without consulting
`modelField`. It carries the gold proof body (which fails to close).

Fails `correct_validateDisplayItem` on the third spec clause
(`itemCallable=false → adminHasAttr=false → ∀ m, modelField = some m → result = …`)
whenever `modelField = some m` and `modelAttr = none`: the prepatch returns
`["E108"]`, but the spec demands `[]` (for `m=false`) or `["E109"]` (for `m=true`).

This is exactly the FAIL_TO_PASS behavior
(`test_valid_field_accessible_via_instance`): a custom field whose descriptor
raises `AttributeError` when accessed on the class (so `getattr(model, item)`
fails ⇒ `modelAttr = none`) but which IS present in the model metadata (so
`get_field` succeeds ⇒ `modelField = some false`) must be ACCEPTED, not flagged
`admin.E108`.

The prepatch keeps the spec view byte-identical to `Solution.lean`.
