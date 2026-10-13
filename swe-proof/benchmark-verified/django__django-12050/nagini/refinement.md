# refinement.md — django__django-12050

The operation-by-operation correspondence between `model.py`'s implementation
(the `resolve_iterable_value` impl region) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, where the proof uses the axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The iterable-normalisation branch — `Query.resolve_lookup_value`
(`django/db/models/sql/query.py:1053`, the `elif isinstance(value, (list, tuple))`
branch, body lines 1062–1076 pre-patch)

Gold hunk (the whole branch body is replaced):
```
- resolved_values = []
- for sub_value in value:
-     if hasattr(sub_value, 'resolve_expression'):
-         if isinstance(sub_value, F):
-             resolved_values.append(sub_value.resolve_expression(
-                 self, reuse=can_reuse, allow_joins=allow_joins, simple_col=simple_col,))
-         else:
-             resolved_values.append(sub_value.resolve_expression(
-                 self, reuse=can_reuse, allow_joins=allow_joins,))
-     else:
-         resolved_values.append(sub_value)
- value = tuple(resolved_values)
+ return type(value)(
+     self.resolve_lookup_value(sub_value, can_reuse, allow_joins, simple_col)
+     for sub_value in value
+ )
```

| # | model.py impl op (`resolve_iterable_value`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `value: Iterable` with fields `kind: int` (0=list, 1=tuple) and `items: List[int]` | the `value` argument in the `list`/`tuple` branch | R | the concrete iterable carrier (`list` vs `tuple`) ↔ the `kind` tag; the ordered items ↔ `items: List[int]` of opaque identities (mapping.md §2). `kind == 0 ⇔ value is a list`, `kind == 1 ⇔ value is a tuple`. |
| A2 | `out = Iterable(value.kind)` — a fresh container whose `kind` equals the input's | `type(value)(...)` — construct a NEW container of the input's concrete type | R + I | `type(value)(gen)` builds a fresh `list` (if `value` was a list) or `tuple` (if it was a tuple). The model's `Iterable(value.kind)` is that construction: `out.kind == value.kind` is the verified counterpart of "the result type is `type(value)`" (mapping.md §2). This is the single line carrying the FIX. |
| A3 | the loop `out.items.append(normalise_item(value.items[i]))` over `i = 0..len-1` | the generator `self.resolve_lookup_value(sub_value, can_reuse, allow_joins, simple_col) for sub_value in value` | A-consumed | each item is normalised independently by the unchanged per-item rule. `normalise_item` (the axiom) stands for `self.resolve_lookup_value(sub_value, …)` applied to a single sub-value: for a scalar sub-value it is the identity (the recursive call hits neither branch), for an expression sub-value it is `sub.resolve_expression(…)`. This per-item rule is UNCHANGED by the patch (pre-patch applied the same rule via the inlined `F`/non-`F` branching; the result of resolving each element is identical) — see §3. The proof consumes only that `out.items[k] == normalise_item(value.items[k])`. |
| A4 | `return out` (the fresh `Iterable`) | `return type(value)(...)` | I | both return the freshly built container. |

The discriminating content of the change — the result keeps the input's
concrete iterable type instead of being coerced to `tuple` — lives in
`Result().kind == value.kind` (model) ⇔ `type(value)(...)` vs the pre-patch
`value = tuple(resolved_values)` (real). `model_prepatch.py` reproduces the bug
(`out = Iterable(1)`, i.e. always a tuple) and **fails** the postcondition
`Result().kind == value.kind`, which is exactly the spec sensing the change
(G-DIFF). It fails precisely when `value.kind == 0` (a list input) — the F2P
scenario `Q(name=['a', 'b'])`.

## B. The per-item normalisation `normalise_item` (A-consumed axiom)

`normalise_item(item)` is the weakest contract (`Ensures(True)`) the proof
needs: the spec requires only that the result's i-th item equals
`normalise_item(input_i)`, a deterministic function of the item alone. The
single behavioural fact the refinement rests on — beyond determinism — is that
this per-item rule is **container-independent**: resolving a sub-value does not
depend on whether its parent was a list or a tuple. This is what makes the only
difference between the two container kinds the container TYPE itself (clause A2).
G-AX (axiom_check.py) validates this against the REAL Django
`resolve_lookup_value`: the per-item result is identical between a list and a
tuple container, and equals resolving the item standalone. Because the patch
does NOT change how an individual item is resolved (it only changes the
surrounding container construction), `normalise_item` faithfully abstracts both
the pre- and post-patch per-item behaviour.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* —
constructing the result as `type(value)(...)` rather than `tuple(...)` — is
modeled **deeply** as `Iterable(value.kind)` with the verified postcondition
`Result().kind == value.kind` (step A2), not hidden behind an axiom. The only
consumed axiom, `normalise_item` (**A-consumed**, §B), covers the **unchanged**
per-item resolution the branch still performs; it is not the operation the patch
changed.

## D. verify(model) ⇒ resolved

`resolve_iterable_value` verifies only if its result carries the input's `kind`
(A2: `Result().kind == value.kind`) and only if every result item equals the
per-item normalisation of the corresponding input item (A3:
`Result().items[k] == normalise_item(value.items[k])`, same length). By R
(`kind` ↔ concrete `list`/`tuple` type, `items` ↔ the ordered sub-values) the
verified result equals `type(value)(self.resolve_lookup_value(sub, …) for sub in
value)` on the tested inputs; by G-AX the per-item rule is the container-
independent unchanged callee `normalise_item` abstracts. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited callee — and the gold patch resolves (G-RESOLVE).
The trust points are exactly the two of PLAN §1.1: axiom soundness (G-AX) and
refinement fidelity (this document, G-EQ).
