# refinement.md — pydata__xarray-3993

The operation-by-operation correspondence between `model.py`'s implementation
(the `select_coordinate` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A-consumed** (proof uses an axiom's
`Ensures`), **A-reference** (a deep model validated == a real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

## A. The routing site — `DataArray.integrate` (`xarray/core/dataarray.py:3483`)

Gold hunk (body, post-patch), with the new signature
`integrate(self, coord=None, datetime_unit=None, *, dim=None)`:
```python
if dim is not None and coord is not None:
    raise ValueError(
        "Cannot pass both 'dim' and 'coord'. Please pass only 'coord' instead."
    )
if dim is not None and coord is None:
    coord = dim
    msg = ( … "`dim` will be removed in version 0.19.0." )
    warnings.warn(msg, FutureWarning, stacklevel=2)
ds = self._to_temp_dataset().integrate(coord, datetime_unit)
return self._from_temp_dataset(ds)
```

| # | model.py impl op (`select_coordinate`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `coord: Optional[int]`, `dim: Optional[int]` | the new signature's `coord=None` / keyword-only `dim=None` | R | a coordinate selector (Hashable) or its `None` default ↔ `Optional[int]`; `is None`/`is not None` are the only observations (mapping.md §2). |
| A2 | `if dim is not None and coord is not None: raise ConflictingSelection()` | `if dim is not None and coord is not None: raise ValueError("Cannot pass both 'dim' and 'coord'. …")` | I + R | identical guard condition (I); the raised type is `ConflictingSelection` ↔ `ValueError` (R, builtin-`Exsures` ban, mapping.md §2). Only the fact-of-raise on the both-supplied input is observed. |
| A3 | `if dim is not None and coord is None: coord = dim; deprecated = True` | `if dim is not None and coord is None: coord = dim; warnings.warn(msg, FutureWarning, stacklevel=2)` | I + R | identical guard and identical `coord = dim` reassignment (I); `deprecated = True` ↔ the `warnings.warn(FutureWarning)` side effect (R: the warning fact ↔ the boolean observable, mapping.md §2). `pytest.warns(FutureWarning)` in F2P observes exactly this. |
| A4 | `return Routed(coord, deprecated)` | `ds = self._to_temp_dataset().integrate(coord, datetime_unit); return self._from_temp_dataset(ds)` | R | the resolved `coord` carried into the (unchanged) downstream integration ↔ `Routed.coord`; the downstream numerics are unchanged, independent of the routing, and unobserved (mapping.md §2, §3.1) — modeled as the identity that simply carries the resolved coordinate out. |

The discriminating content of the change — that routing through the **legacy
selector alone** now both proceeds with `coord = dim` AND emits a deprecation
signal (previously it proceeded silently, since `dim` was the sole, undeprecated
argument) — lives in step A3: `Routed.deprecated == (dim is not None and coord
is None)` (model) ⇔ the conditional `warnings.warn(…, FutureWarning, …)` (real).
`model_prepatch.py` reproduces the pre-patch behaviour (route `dim` through but
**never** warn) and **fails** exactly the postcondition
`Result().deprecated == (dim is not None and coord is None)` — the spec sensing
the change (G-DIFF), and the very fact `pytest.warns(FutureWarning)` asserts.

## B. The co-changed second site — `Dataset.integrate` (`xarray/core/dataset.py:5966`)

Gold hunk: docstring rewrite + a return-type annotation `-> "Dataset"` and a
`coord: Union[Hashable, Sequence[Hashable]]` parameter annotation. **No body /
control-flow / data-flow line changes.** This site is behaviourally inert
(mapping.md §3.2): it introduces no independently-observable behaviour, needs no
modeled function and no separate `model_prepatch_<k>`. It is included in
`patch.diff` (gold verbatim) only because the gold patch touches it.

## C. No kind-3 (unexpressible-changed-op) steps; no axioms

Every step above is R or I. The one operation that genuinely *changed* — the
selector routing and its two signals — is modeled **deeply** (the spelled-out
`if` cascade in `select_coordinate`), not hidden behind an axiom. There is **no
consumed axiom** (`A-consumed`) and **no A-reference** deep model of a library
callee: the routing reads only its two selector arguments, and everything it
delegates to downstream is unchanged and unobserved (mapping.md §3.1).
`axiom_check.py` therefore audits not a library axiom but the *deep routing
model itself*, replaying the gold prologue's decision table to confirm the model
== the gold control flow (mapping.md §3.3).

## D. verify(model) ⇒ resolved

`select_coordinate` verifies only if (i) it refuses exactly the both-supplied
input (A2), (ii) it routes the single supplied selector to `Routed.coord` —
`dim` when only `dim` is given, `coord` otherwise (A1, A3, A4), (iii) it sets
`Routed.deprecated` to true on **exactly** the legacy-selector-only call (A3),
and (iv) it TERMINATES on every input (`Requires(MustTerminate(2))`): the
honoured call actually returns and the refused call actually raises, matching
the real prologue's straight-line evaluation. Clause (iv) closes the vacuity
hole the audit exhibited (a same-spec rival that diverged on the
primary-selector path — hanging the F2P/P2P suite — while satisfying every
`Ensures` vacuously; properties.py `w6-diverge` pins the rejection).
By R (selector ↔ `Optional[int]`, `ValueError` ↔ `ConflictingSelection`,
`FutureWarning` ↔ the boolean) the verified routing equals the gold prologue,
which then delegates the resolved `coord` to the unchanged trapezoidal
integration. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The single trust point is refinement fidelity (this document,
G-EQ); there is no axiom-soundness obligation because there is no consumed axiom.
