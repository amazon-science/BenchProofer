# refinement.md — django__django-11551

The operation-by-operation correspondence between `model.py`'s implementation
(the `check_display_item` impl region) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated == a real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change

The gold patch rewrites the body of `_check_list_display_item`
(`django/contrib/admin/checks.py:718-749`). Pre-patch (buggy):
```python
if callable(item):
    return []
elif hasattr(obj, item):
    return []
elif hasattr(obj.model, item):            # <-- gate that breaks the fix
    try:
        field = obj.model._meta.get_field(item)
    except FieldDoesNotExist:
        return []
    else:
        if isinstance(field, models.ManyToManyField):
            return [Error(... id='admin.E109')]
        return []
else:
    return [Error(... id='admin.E108')]
```
Post-patch (gold):
```python
if callable(item):
    return []
elif hasattr(obj, item):
    return []
try:
    field = obj.model._meta.get_field(item)
except FieldDoesNotExist:
    try:
        field = getattr(obj.model, item)
    except AttributeError:
        return [Error(... id='admin.E108')]
if isinstance(field, models.ManyToManyField):
    return [Error(... id='admin.E109')]
return []
```
The fix removes the `elif hasattr(obj.model, item):` gate so that the
structural `get_field` lookup is always attempted; the not-resolvable
diagnostic (`admin.E108`) is emitted only when BOTH the structural lookup and
the attribute lookup fail; and the `ManyToManyField` test is hoisted so it
applies to the object obtained from EITHER lookup.

## Operation correspondence

| # | model.py impl op (`check_display_item`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| 1 | `if is_invokable: return 0` | `if callable(item): return []` | R + I | `callable(item)` (a `bool`) ↔ `is_invokable` (mapping.md §2,§3.1); identical control flow; `[]` ↔ `0`. |
| 2 | `if is_presenter_attr: return 0` | `elif hasattr(obj, item): return []` | R + I | `hasattr(obj, item)` ↔ `is_presenter_attr` (mapping.md §3.1); identical control flow; `[]` ↔ `0`. |
| 3 | `if not structural_absent: relation = structural_is_relation` | `try: field = obj.model._meta.get_field(item) except FieldDoesNotExist: ...` — the no-raise branch binds `field` to the structural field | R + I | the raise-or-return `get_field` call ↔ the pair (`structural_absent`, `structural_is_relation`) (mapping.md §2,§3.2): "did not raise `FieldDoesNotExist`" ⇔ `not structural_absent`, and the field's `isinstance(..., ManyToManyField)` ⇔ `structural_is_relation`. Binding `field` from the structural lookup is identical control flow. |
| 4 | `else: if attribute_absent: return 108` | inside `except FieldDoesNotExist:` → `try: field = getattr(obj.model, item) except AttributeError: return [Error(... id='admin.E108')]` | R + I | reached only when the structural lookup raised (`structural_absent`); the inner `getattr` raise-or-return ↔ (`attribute_absent`, `attribute_is_relation`) (mapping.md §2,§3.3): "raised `AttributeError`" ⇔ `attribute_absent` ⇒ emit the not-resolvable code; `[Error(id='admin.E108')]` ↔ `108`. Identical control flow. |
| 5 | `else: ... relation = attribute_is_relation` | the `getattr` no-raise branch binds `field` to the attribute value | R + I | when `getattr` does not raise (`not attribute_absent`), `field` is the attribute value; its `isinstance(..., ManyToManyField)` ⇔ `attribute_is_relation` (mapping.md §3.3,§3.4). Identical control flow (falls through to the shared `isinstance`). |
| 6 | `if relation: return 109` | `if isinstance(field, models.ManyToManyField): return [Error(... id='admin.E109')]` | R + I | the hoisted `isinstance` test applied to `field` (from whichever lookup bound it) ↔ the `relation` flag carried from step 3 or 5 (mapping.md §3.4); `[Error(id='admin.E109')]` ↔ `109`. Identical control flow. |
| 7 | `return 0` | `return []` | R + I | the fall-through accept; `[]` ↔ `0`. |

The discriminating content of the change — that the structural lookup is no
longer gated by the model-attribute test — lives in step 4's `else` branch: the
model reaches the structural verdict (steps 3, 6) whenever `not
structural_absent`, **regardless of** `attribute_absent`. The pre-patch gates
the whole structural attempt behind `not attribute_absent`
(`elif hasattr(obj.model, item)`), so when `attribute_absent` is true it jumps
straight to `108`. `model_prepatch.py` reproduces that gate and **fails** the
postcondition clause (C) (`not structural_absent ⇒ Result == 0/109`), which is
exactly the F2P observation (`test_valid_field_accessible_via_instance`: a
field reachable only via the structural lookup, with the attribute unreachable,
must be accepted) (G-DIFF).

## No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The operation that genuinely *changed* — the
decision logic (which verdict to emit from the four resolution observations) —
is expressible directly and is modeled **deeply** (the spelled-out control flow
in the impl region), NOT hidden behind an axiom. None of the consulted
primitives (`callable`, `hasattr`, `get_field`, `getattr`,
`isinstance`/`ManyToManyField`) is changed by the patch; each is reduced to the
boolean observation it produces via the standard raise-or-return refinement
(mapping.md §2). Hence there is **no consumed axiom (A-consumed) and no deep-
model reference (A-reference)** in this bundle: `axiom_check.py` instead
exhaustively confirms the model's verdict matches the patched routine's verdict
over every combination of observations (the decision-logic equivalence check).

## verify(model) ⇒ resolved

`check_display_item` verifies only if: it accepts when the entry is invokable or
a presenter attribute (clause A, steps 1-2); it emits the not-resolvable code
IFF neither early acceptance holds and BOTH lookups report absent (clause B,
step 4 reached only after step 3's `else` and the structural raise); when the
structural lookup yields a field the verdict is decided by that field alone
(clause C, steps 3+6); and when the structural lookup reports absent but the
attribute lookup yields a value, the verdict is decided by that value equally
(clause D, steps 5+6). By R (each builtin/`get_field`/`getattr`/`isinstance`
observation ↔ its boolean; `[]`/`E108`/`E109` ↔ `0`/`108`/`109`) the verified
decision equals the gold patch's decision on every reachable observation
combination — confirmed exhaustively by axiom_check.py (G-AX, 64 combinations +
the real-callee end-to-end PositionField witness). Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement,
and the gold patch resolves (G-RESOLVE). The only trust point is refinement
fidelity (this document, G-EQ); there is no axiom-soundness trust point because
no axiom is consumed.
