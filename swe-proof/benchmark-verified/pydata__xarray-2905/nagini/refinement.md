# refinement.md — pydata__xarray-2905

The operation-by-operation correspondence between `model.py`'s implementation
(the `normalize_self_describing` impl region) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, where the proof uses the axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The normalization step — `as_compatible_data` (`xarray/core/variable.py:220-221`)

Gold hunk:
```
     # we don't want nested self-described arrays
-    data = getattr(data, "values", data)
+    if isinstance(data, (pd.Series, pd.Index, pd.DataFrame)):
+        data = data.values
```

| # | model.py impl op (`normalize_self_describing`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `data: Incoming` with bool fields + identity tags | the local `data` value reaching the step | R | the arbitrary Python value ↔ a record of the facts the step inspects (`is_recognized_container`, `exposes_values`) plus identity tags (`identity`, `values_identity`). Object identity (`is`) ↔ tag equality (`==`). mapping.md §1–2. |
| A2 | `if data.is_recognized_container:` | `if isinstance(data, (pd.Series, pd.Index, pd.DataFrame)):` | A-reference | the **changed** decision predicate is modelled **deeply** as the bool `is_recognized_container`; there is no consumed axiom standing in for it. The deep model is validated **== the real predicate's effect** by G-AX: `axiom_check.py` runs the real `as_compatible_data` and shows it unwraps exactly the three recognized pandas containers and nothing else (mapping.md §3). |
| A3 | `result = data.values_identity` (recognized branch) | `data = data.values` | R | rebinding the local `data` to its `.values` object ↔ the surviving identity becoming `values_identity`. Identity-tag refinement of `data.values`. |
| A4 | `result = data.identity` (else branch) | (no rebinding — `data` keeps its value; the gold `if` has no `else`) | I | when the predicate is false the gold leaves `data` untouched, i.e. the surviving value is the input itself; the model returns `data.identity`. The two are the identical control outcome "pass the value through unchanged". |
| A5 | `return result` | the local `data` flows on to the rest of `as_compatible_data` | R | the function's result tag ↔ the value bound to `data` after the step. |

The discriminating content of the change — an object that **exposes `.values`
but is not a recognized container** must NOT be unwrapped — lives in step A2/A4:
when `not is_recognized_container` the model returns `data.identity`. The
pre-patch step (`getattr(data, "values", data)`) unwrapped on
`exposes_values`; `model_prepatch.py` reproduces that (`if data.exposes_values`)
and **fails** the postcondition
`Implies(not data.is_recognized_container, Result() == data.identity)` on the
witness `is_recognized_container=False, exposes_values=True` — exactly the
issue's `HasValues` / the F2P `CustomWithValuesAttr` case (G-DIFF).

## B. Read-only input, fractional permission

`data` is never mutated by this step (the gold only rebinds a *local* name; the
incoming object's recognized-ness / values-exposure / identities are unchanged).
Accordingly every field is Required AND Ensured at `Acc(..., 1/2)`, and the four
`Ensures(field == Old(field))` clauses pin the input as unchanged. A
full-permission, free-to-overwrite input would let a wrong impl satisfy the
postcondition vacuously by rewriting `is_recognized_container`; the fractional
read-only permission plus the `Old`-equality clauses block that (directive 5).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the unwrap **decision predicate** — is modelled **deeply** (the bool
`is_recognized_container` + the verified branch), not hidden behind an axiom
about an unchanged callee. There is **no consumed `@ContractOnly` axiom**: the
only kind-A item is the **A-reference** of step A2, where G-AX validates the
deep predicate against the real `as_compatible_data` behaviour.

## D. verify(model) ⇒ resolved

`normalize_self_describing` verifies only if its surviving value is `data.values`
exactly when the input is a recognized container and is the input itself
otherwise (A2/A3/A4). By R (identity tags ↔ object identity, the bool fields ↔
the real `isinstance`/`hasattr` predicates) the verified step equals the gold
`if isinstance(data, (pd.Series, pd.Index, pd.DataFrame)): data = data.values`
on every input: recognized containers unwrap to `.values`, all other values
(including `.values`-bearing user objects) pass through. By G-AX the deep
predicate `is_recognized_container` is faithful to the real decision
(A-reference), and the model invariant (recognized ⟹ exposes `.values`) holds
on the real pandas types. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The single trust point is refinement fidelity (this document, G-EQ)
plus the A-reference faithfulness check (G-AX); there is no consumed axiom.
