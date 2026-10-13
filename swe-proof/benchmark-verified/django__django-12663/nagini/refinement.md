# refinement.md — django__django-12663

The operation-by-operation correspondence between `model.py`'s implementation
(the `output_field_identity` impl region) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, where the proof uses an axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real semantics by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The single-selection output-field site — `Query.output_field`

Gold hunk (`django/db/models/sql/query.py`, the `len(self.select) == 1` branch):
```
     def output_field(self):
         if len(self.select) == 1:
-            return self.select[0].field
+            select = self.select[0]
+            return getattr(select, 'target', None) or select.field
         elif len(self.annotation_select) == 1:
             return next(iter(self.annotation_select.values())).output_field
```

| # | model.py impl op (`output_field_identity`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `sel: Selection` (the single selected item) | `select = self.select[0]` (under `len(self.select) == 1`) | R | the selected item `self.select[0]` (a `Col`) ↔ the minimal `Selection` object exposing only its two touched field notions (mapping.md §1, §2). The `len(self.select) == 1` guard is the calling context; only this branch is modeled. |
| A2 | `source = sel.source` | `getattr(select, 'target', None)` | R | `Col.target` ↔ `sel.source`, with the sentinel `0` ≡ "no usable source field" (attribute absent OR falsy) and any nonzero ≡ a usable, distinct source field (mapping.md §2). `getattr(..., 'target', None)` reads `Col.target`; `None`/falsy ↔ `0`. |
| A3 | `if source != 0: return source` | the truthy left operand of `getattr(select, 'target', None) or select.field` is returned | R + I | the truthiness test `source != 0` ↔ Python's truthiness of `getattr(select, 'target', None)`; the integer-identity refinement maps "truthy field object" to "nonzero identity". When truthy, the source field is returned. The `or` short-circuit is the identical control structure. |
| A4 | `return sel.field` (the fall-through when `source == 0`) | `... or select.field` (the right operand, taken when the left is falsy/`None`) | R + I | `select.field` (= `Expression.field` → `output_field`) ↔ `sel.field`; reached exactly when the source field is absent or falsy. Identical fallback control. |

The discriminating content of the change — preferring the relation-aware
SOURCE field (`Col.target`) over the resolved field (`Col.field`) for a single
selection whose two notions differ — lives in clause A3 (model) ⇔ the
`getattr(select, 'target', None) or` prefix added by the gold (real). The
pre-patch code was `return self.select[0].field`, i.e. always the resolved
field; `model_prepatch.py` reproduces that (`return sel.field`) and **fails**
the postcondition `Implies(sel.source != 0, Result() == sel.source)`, which is
exactly the spec sensing the change (G-DIFF, confirmed: the prepatch fails on
that clause).

## B. Consumed axioms

None. The single-selection output-field choice is pure choose-one-of-two logic,
modeled **deeply** (the `if source != 0: return source; return sel.field`
skeleton). There is no `@ContractOnly` the proof consumes — no dead axiom.

## C. Deep-model reference (A-reference)

The real attribute / truthy-fallback semantics the deep model stands on — that
`getattr(select, 'target', None) or select.field` returns `Col.target` when it
is present and truthy and `Col.field` otherwise, and that for a single-selection
`Query` this is the relation-aware field whenever the column carries one — are
the **A-reference**: validated equal to the real Python / Django behaviour by
`axiom_check.py` (G-AX), NOT consumed as an axiom. See mapping.md §3.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I (the changed op is modeled deeply, validated as an
A-reference by G-AX). There is no consumed axiom about the function under change
and no hand-waved step. The one operation that genuinely *changed* — choosing
`Col.target` over `Col.field` — is the spelled-out `if source != 0` selection
(A3/A4), not hidden behind an axiom.

## E. verify(model) ⇒ resolved

`output_field_identity` verifies only if its result is the source field whenever
a usable one is present (A3, the postcondition `Implies(sel.source != 0,
Result() == sel.source)`) and the resolved field otherwise (A4). By R (the
`Col` ↔ `Selection` field-identity refinement and the `getattr/or` truthy
correspondence) the verified function equals
`getattr(self.select[0], 'target', None) or self.select[0].field` on the single
selection the F2P test exercises; by G-AX the deep model's choose-one semantics
equal the real `getattr/or` and the real `Query.output_field`. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the G-AX-validated reference — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: reference
soundness (G-AX) and refinement fidelity (this document, G-EQ); there is no
consumed-axiom trust point.
