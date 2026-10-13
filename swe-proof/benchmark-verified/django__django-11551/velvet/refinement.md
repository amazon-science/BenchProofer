# refinement.md — django__django-11551

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `listDisplayItemCheck` `do` block and the deep `listDisplayItemOutcome`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement; state the bijection), **A-consumed** (proof uses an axiom's
`ensures`), **A-reference** (deep model validated == real callee by G-AX), or
**I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); there are no A legs (no axioms). Claim: any impl verifying against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The changed function — `_check_list_display_item` (`checks.py:718`)

The gold patch restructures the body so that the field registry is consulted
before condemning the entry, and `E108` is produced only when both the registry
lookup AND the model-class attribute access fail. Post-patch control flow:

```
if callable(item):                         return []                       # ok
elif hasattr(obj, item):                   return []                       # ok
try:    field = obj.model._meta.get_field(item)        # getFieldRaises?
except FieldDoesNotExist:
    try:    field = getattr(obj.model, item)           # modelAttrRaises?
    except AttributeError:                 return [E108]                   # e108
if isinstance(field, models.ManyToManyField): return [E109]               # e109
return []                                                                  # ok
```

| # | Solution.lean impl op (`listDisplayItemCheck`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | input `isCallable : Bool`; `if isCallable then ok` | `if callable(item): return []` | R + I | `callable(item)` ↔ `isCallable` (mapping.md §2). The `if … then ok` is the identical guard. |
| A2 | input `hasAttrObj : Bool`; `else if hasAttrObj then ok` | `elif hasattr(obj, item): return []` | R + I | `hasattr(obj, item)` ↔ `hasAttrObj`. Identical guard. |
| A3 | input `getFieldRaises : Bool`; `else if getFieldRaises then (…)` | `try: field = obj.model._meta.get_field(item) except FieldDoesNotExist:` | R + I | the registry lookup outcome ↔ `getFieldRaises` (raises ↔ `true`). The `else if getFieldRaises then <fallback> else <m2m-test>` branch IS the try/except: the `except` body is the `then`, the success path (field obtained from `get_field`) is the `else` that proceeds to the M2M test. |
| A4 | input `modelAttrRaises : Bool`; inner `if modelAttrRaises then e108` | inner `try: field = getattr(obj.model, item) except AttributeError: return [E108]` | R + I | `getattr` failure ↔ `modelAttrRaises` (raises ↔ `true`). On the registry-miss path, `e108` exactly when `getattr` also raises. |
| A5 | input `fieldIsM2M : Bool`; `… else if fieldIsM2M then e109 else ok` (on both field-resolved paths) | `if isinstance(field, models.ManyToManyField): return [E109]  …  return []` | R + I | the single shared M2M test ↔ `fieldIsM2M`, applied to whichever field was resolved (registry hit OR `getattr` success). Maps to `e109`, else `ok`. |
| A6 | result `CheckResult` returned | the returned `[]` / `[Error(id='admin.E108')]` / `[Error(id='admin.E109')]` | R | the report's only changed-by-this-patch observable is its error id (mapping.md §2): `ok ↔ []`, `e108 ↔ E108`, `e109 ↔ E109`. The `checks.Error(...)` message/obj args are unchanged concrete constructions on each branch. |

Discriminating content of the change — a registry-known field whose class-level
attribute access fails (`getFieldRaises = false`, `modelAttrRaises = true`) must
be `ok` (or `e109` if M2M), NOT `e108` — lives in the `else if getFieldRaises then …`
structure: the M2M/ok decision is reached whenever `getFieldRaises = false`,
regardless of `modelAttrRaises`. The pre-patch code gated the whole resolution on
`hasattr(obj.model, item)` (= `not modelAttrRaises`), so it returned `e108`
whenever `modelAttrRaises = true`. `Solution_prepatch.lean` reproduces that gate
and **fails** `out = listDisplayItemOutcome …` (G-DIFF) precisely on the
`getFieldRaises = false ∧ modelAttrRaises = true` rows — the PositionField case
of the F2P test `test_valid_field_accessible_via_instance`.

## B. No kind-A steps

There are no axiomatized callees and no deep-model references to an unchanged
callee. `callable`, `hasattr`, `get_field`, `getattr`, `isinstance` are all
**unchanged** observation primitives whose results are abstracted to the five
boolean inputs (R-refinements, A1–A5), validated against the real objects by
G-CONF — not consumed as axioms. The function under specification is the changed
function itself, which is modeled deeply (`listDisplayItemOutcome`), never
axiomatized (directive 7).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — the control flow
deciding when `E108` is produced — is modeled **deeply** (the spelled-out nested
`if` ladder `listDisplayItemOutcome`, steps A1–A5), not hidden behind an axiom.
There is no consumed axiom and no `else if` (the Lean uses nested
`if … then … else if …`, the permitted ladder form, §2).

## D. verify(Solution) ⇒ resolved

`listDisplayItemCheck` verifies only if its output equals
`listDisplayItemOutcome` on every combination of the five observations — in
particular `ok`/`e109` (not `e108`) whenever `getFieldRaises = false`,
independent of `modelAttrRaises` (A3–A5). By R (the five observation bijections
and the error-id observable, mapping.md §2) the verified decision equals the
patched `_check_list_display_item`'s reported error id on every input; by G-CONF
the R/I transliteration agrees with `patch.diff`'s behaviour on ≥10⁵ inputs
(including the PositionField path the F2P test exercises). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). There are no axioms, so the
only trust point is refinement fidelity (this doc, G-EQ + G-CONF); G-AX is empty.
