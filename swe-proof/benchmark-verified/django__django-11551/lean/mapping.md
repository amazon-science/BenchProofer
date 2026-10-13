# mapping.md — django__django-11551

## Symbol binding (file:line @ base_commit 7991111af12056ec9a856f35935d273526338c1f)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_validateDisplayItem` / `problem_spec_validateDisplayItem` / `correct_validateDisplayItem` | `_check_list_display_item(self, obj, item, label)`: the per-entry validation of one display-configuration item — accept, or emit `admin.E108` / `admin.E109` | `django/contrib/admin/checks.py:718-749` @ base_commit |

## Modeled inputs (the observations available at the decision point)

The function under spec validates ONE listed display item. Its observable inputs
are the four independent checks the routine performs on the entry:

| Lean | Python reality | meaning |
|---|---|---|
| `itemCallable : Bool` | `callable(item)` | the entry is itself callable |
| `adminHasAttr : Bool` | `hasattr(obj, item)` | the entry is an attribute of the admin object `obj` |
| `modelField : Option Bool` | `obj.model._meta.get_field(item)` | `none` ⇔ the lookup raised `FieldDoesNotExist`; `some m` ⇔ a field was returned, with `m = isinstance(field, models.ManyToManyField)` |
| `modelAttr : Option Bool` | `getattr(obj.model, item)` | `none` ⇔ the access raised `AttributeError`; `some m` ⇔ a value was returned, with `m = isinstance(field, models.ManyToManyField)` |

`get_field` and `getattr` are UNCHANGED callees; their outcomes (raise vs. value,
and the many-to-many flag of any returned value) are taken as the model inputs.

## Output

| Lean | Python |
|---|---|
| `result : List String` | the list returned by `_check_list_display_item`: `[]` (acceptable), or a one-element list whose element is the `checks.Error` `id` — `"E108"` (unresolvable entry) or `"E109"` (many-to-many field) |

The error message strings, the `obj=`/`label` formatting, and the `checks.Error`
wrapper are unchanged by the patch and are abstracted to the error `id`, which is
the only behavior the FAIL_TO_PASS / PASS_TO_PASS tests assert on.

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| `callable(item)`, `hasattr(obj, item)` | `itemCallable`, `adminHasAttr : Bool` | identity |
| `get_field(item)` raises `FieldDoesNotExist` / returns `field` | `modelField : Option Bool` | raise ↦ `none`; return ↦ `some (isinstance(field, M2M))` |
| `getattr(model, item)` raises `AttributeError` / returns value | `modelAttr : Option Bool` | raise ↦ `none`; return ↦ `some (isinstance(value, M2M))` |
| returned `[]` / `[Error(id='E108')]` / `[Error(id='E109')]` | `result : List String` | `[]` / `["E108"]` / `["E109"]` |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** `callable`, `hasattr`, `_meta.get_field`, and
  `getattr` are all UNCHANGED; their outcomes are modeled as inputs. The
  acceptance/diagnostic control flow — which is exactly what the patch rewrites —
  is modeled DEEPLY (`problem_spec_validateDisplayItem` clauses + the imperative
  impl), so the rows are A-reference, validated by G-CONF, never axiomatized
  (§0.7). `axiom_check.py` is a skip stub.
- **No flag dependency.** The decision reads only the four observables above.
- **`get_field`-preferred ordering.** The patch resolves the field by trying
  `get_field` FIRST and falling back to `getattr` only on `FieldDoesNotExist`;
  the model reflects this (`modelField` is consulted before `modelAttr`). When
  both succeed, only `modelField`'s flag is observed — matching the patched code,
  which never reaches the `getattr` branch when `get_field` succeeds.

## G-CONF fuzz seed

`SEED = 20240709` (pinned in `conformance_check.py`). The observable space is
finite (2·2·3·3 = 36 points) and enumerated exhaustively in addition to the fuzz.
