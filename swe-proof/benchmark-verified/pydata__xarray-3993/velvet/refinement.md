# refinement.md — pydata__xarray-3993

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`integrateDispatch` `do` block, which transliterates `resolve`) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; state the
bijection), **A-consumed** / **A-reference** (axiomatized / deeply-modeled
callee), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. This bundle has
**no A steps** (§C). Claim: any impl verifying against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The dispatch site — `DataArray.integrate` (`xarray/core/dataarray.py:3483`)

Gold hunk (behavioral core):
```
-    def integrate(self, dim, datetime_unit=None) -> "DataArray":
-        ds = self._to_temp_dataset().integrate(dim, datetime_unit)
+    def integrate(self, coord=None, datetime_unit=None, *, dim=None) -> "DataArray":
+        if dim is not None and coord is not None:
+            raise ValueError("Cannot pass both 'dim' and 'coord'. ...")
+        if dim is not None and coord is None:
+            coord = dim
+            warnings.warn(msg, FutureWarning, stacklevel=2)
+        ds = self._to_temp_dataset().integrate(coord, datetime_unit)
```

| # | Solution.lean impl op (`integrateDispatch`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `primary legacy : Selector` | the `coord` / `dim` keyword arguments | R | a selector ↔ `Option Nat`: absent-or-`None ↔ none`, supplied-with-name ↔ `some (id name)` (mapping.md §2). The head's only tests are `coord is not None` / `dim is not None`, which `Option`'s `some`/`none` model exactly. |
| A2 | `match … \| some _, some _ => Except.error .bothSupplied` | `if dim is not None and coord is not None: raise ValueError(...)` | I + R | the both-supplied branch. **I** in control flow (the same guard), **R** in carrier (`ValueError ↔ Except.error .bothSupplied`, mapping.md §2). |
| A3 | `\| none, some d => Except.ok (some { forwarded := d, advisory := true })` | `if dim is not None and coord is None: coord = dim; warnings.warn(..., FutureWarning)` then forward `coord` | I + R | the legacy-only branch: forward the legacy value (`coord = dim`) **and** emit the advisory. `advisory := true ↔` exactly one `FutureWarning` (mapping.md §2). The legacy selector is still honoured for its value. |
| A4 | `\| some c, none => Except.ok (some { forwarded := c, advisory := false })` | (neither guard fires) forward `coord`, no warning | I | the primary-only branch: forward the primary value, no advisory. |
| A5 | `\| none, none => Except.ok none` | (neither guard fires) forward `coord = None` to the integrator | R | no coordinate selected. Refines to forwarding `None` to the unchanged integrator, which raises `ValueError("Coordinate None does not exist.")` — both shadow and oracle observe an error (G-CONF: kind='err'). mapping.md §2. |
| A6 | `Dispatch.forwarded` then handed to the integrator | `self._to_temp_dataset().integrate(coord, datetime_unit)` | I | forwarding the single resolved coordinate to the **unchanged** integrator. G-CONF feeds `forwarded` to the real integrator on both sides, so this op cancels and only the *choice* is tested. The integrator is NOT a modeled callee (mapping.md §3.1). |

The discriminating content of the change — a legacy-only call
`da.integrate(dim="x")` must (i) still forward `"x"` and (ii) now emit a
`FutureWarning` — lives in row A3's `advisory := true`. The pre-patch head
forwarded the selector with **no** warning and rejected nothing;
`Solution_prepatch.lean` reproduces that (every supplied selector yields
`advisory := false`, no both-supplied rejection) and **fails** `out = resolve
primary legacy` precisely on the legacy-only branch (where the spec demands
`advisory := true`) — G-DIFF. This is exactly the behaviour the F2P
`test_integrate` asserts via `with pytest.warns(FutureWarning): da.integrate(dim="x")`.

## B. The `Dataset.integrate` hunk — non-behavioral

The gold patch's second file hunk edits only `Dataset.integrate`'s signature
type annotations and docstring (`xarray/core/dataset.py:5963`); its runtime body
is byte-identical (mapping.md §3.2). It is carried verbatim in `patch.diff` for
G-RESOLVE but models nothing and yields no separate prepatch: a docstring change
is unobservable to the frozen spec, so it cannot produce a discriminating
failing prepatch, and `same_spec` would be violated by inventing one.

## C. No A steps and no kind-3 (inexpressible-changed-op) steps

Every step is R or I. There are **no axiomatized callees** (A-consumed) and **no
deep-model references** (A-reference): the only downstream callee — the unchanged
trapezoidal integrator — is reached only through the forwarded selector and is
observed via that selector (the input carrier), so it is neither axiomatized nor
deeply modeled; it is left as the real callee on both legs of G-CONF (§A6,
mapping.md §3.1). The operation that genuinely changed — the argument-resolution
head (both-supplied rejection + legacy-only advisory + which value is forwarded)
— is modeled **directly and concretely** as `resolve`/the `match` (all R/I), not
hidden behind any axiom about the function under change.

## D. verify(Solution) ⇒ resolved

`integrateDispatch` verifies only if its output equals `resolve primary legacy`:
the both-supplied rejection (A2), the legacy-only forward-**with**-advisory (A3),
the primary-only forward-without-advisory (A4), and the no-selector empty result
(A5). By R (`Selector ↔ Option Nat`, `ValueError ↔ Except.error`, `FutureWarning
↔ advisory`) and I (the shared guards + the forward to the unchanged integrator),
the verified head equals the patched `DataArray.integrate`'s resolution on the
tested inputs; by G-CONF the R/I transliteration agrees with `patch.diff`'s
behaviour on ≥10⁵ inputs (including `da.integrate(dim="x")`); there are no A
trust points to validate (G-AX skip, §C). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE).
