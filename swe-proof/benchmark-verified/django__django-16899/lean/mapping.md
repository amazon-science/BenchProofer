# mapping.md — symbol binding & type bijection (django__django-16899)

## Modeled function
- **Lean** `implementation_checkReadonlyFieldsItem :
  AdminObj → String → String → Bool → Bool → Bool → Bool → List String`
- **Python** `BaseModelAdminChecks._check_readonly_fields_item(self, obj, field_name, label)`
  — `django/contrib/admin/checks.py:761-787 @ d3d173425f` (base_commit).

The function validates one entry of an admin's `readonly_fields`. It returns an
empty list when the entry resolves (it is callable, an attribute of the admin
object, an attribute of the bound model, or a declared model field) and a
single `checks.Error(id="admin.E035")` otherwise. The patch changes ONLY the
text of that error message: post-patch it additionally cites the offending
value (`field_name`).

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `obj.__class__.__name__` | `AdminObj.className : String` | admin class name in the message |
| `obj.model._meta.label` | `AdminObj.modelLabel : String` | bound-model dotted label in the message |
| `field_name` (`str`) | `fieldName : String` | the configured value under test |
| `label` (`str`, e.g. `"readonly_fields[0]"`) | `label : String` | position label in the message |
| `callable(field_name)` | `isCallable : Bool` | UNCHANGED resolution check (R) |
| `hasattr(obj, field_name)` | `hasAttrObj : Bool` | UNCHANGED resolution check (R) |
| `hasattr(obj.model, field_name)` | `hasAttrModel : Bool` | UNCHANGED resolution check (R) |
| `obj.model._meta.get_field(field_name)` succeeds (no `FieldDoesNotExist`) | `fieldExists : Bool` | UNCHANGED resolution check (R) |
| `[]` / `[checks.Error(msg, …)]` | `List String` (`[]` / `[msg]`) | the error carries only the message text; `obj=` and `id=` are unchanged framing, not modeled |

`checks.Error(...)` is a framing wrapper: its `obj=obj.__class__` and
`id="admin.E035"` fields are unchanged by the patch and identical between the
empty/non-empty branches' surrounding code, so they are not modeled; the
observable, patched payload is the message string. Each error is represented by
its message `String`; the returned list has length 0 or 1.

## Callee provenance
- The four resolution predicates (`callable`, two `hasattr`, and
  `_meta.get_field`/`FieldDoesNotExist`) are UNCHANGED Python builtins / Django
  internals. The patch does not touch them and the fix's branch structure
  (four short-circuit acceptances, then the error) is identical pre/post. Their
  boolean OUTCOMES are taken as refined inputs (R) — they are NOT axiomatized
  (no `_prop`), so there is no A-consumed callee and `axiom_check.py` is a skip
  stub.
- The changed operation is the message text itself, a `%`-format. It is modeled
  DEEPLY as the literal `errorMessage` string concatenation (I-tagged) — it is
  the change spelled out concretely, delegating to no callee, so it is NOT an
  A-reference either.

## Flag dependency
None. The branch is reached only when all four checks fail; no configuration
flag gates the message.

## G-CONF fuzz seed
Pinned seed: **16899**. ≥10^5 fuzzed inputs over the four booleans and the four
strings (`label`, `fieldName`, `className`, `modelLabel`), oversampling the
all-false boolean combination so the changed message branch is hit hard.
