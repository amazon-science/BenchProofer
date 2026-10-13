# refinement.md — pydata__xarray-3305

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the three `do` blocks and the deep `resolveGlobal` model) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — **A-consumed** where the proof uses an axiom's `ensures`, **A-reference**
where a deep model is validated == the real callee by G-AX), or **I** (identical
concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`, §4.1);
the A-reference and this narrative are audited by **G-AX** / **G-EQ**. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The element site — `Variable.quantile` (`xarray/core/variable.py:1595`)

Gold hunk:
```
- def quantile(self, q, dim=None, interpolation="linear"):
+ def quantile(self, q, dim=None, interpolation="linear", keep_attrs=None):
  ...
- return Variable(new_dims, qs)
+ if keep_attrs is None:
+     keep_attrs = _get_keep_attrs(default=False)
+ attrs = self._attrs if keep_attrs else None
+ return Variable(new_dims, qs, attrs)
```

| # | Solution.lean impl op (`reduceElementAttrs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `srcAttrs : List (String × String)` | `self._attrs` (the source variable's attrs) | R | `OrderedDict`/`None` ↔ `List (String × String)` (mapping.md §2). |
| A2 | param `choice : Option Bool` | `keep_attrs` arg (`bool`/`None`) | R | `True/False/None ↔ some true/some false/none` (mapping.md §2). |
| A3 | param `glob : GlobalPref` | `OPTIONS["keep_attrs"]` global read inside `_get_keep_attrs` | R | `"default"/True/False ↔ gDefault/gKeep/gDrop` (mapping.md §2). |
| A4 | `match choice with \| some b => b \| none => resolveGlobal glob false` | `if keep_attrs is None: keep_attrs = _get_keep_attrs(default=False)` | A-reference + I | the `none` branch is the deep model `resolveGlobal` (== `_get_keep_attrs`, A-reference, G-AX §3.1) with fallback `false` (matches `default=False`); the `some`/`if-not-None` selection is concrete (I). |
| A5 | `if effective then srcAttrs else []` then `return attrs` | `attrs = self._attrs if keep_attrs else None; return Variable(new_dims, qs, attrs)` | I + R | the conditional attach is identical (I); `[] ↔ None`-attrs result, `srcAttrs ↔ self._attrs` (R). The `Variable(new_dims, qs, …)` value/shape construction is unchanged data (mapping.md §2), elided. |

Discriminating content — the result carries `srcAttrs` exactly when `effective`
is true — lives in step A5. `Solution_prepatch.lean` reproduces the pre-patch
`return Variable(new_dims, qs)` (always empty attrs, `return []`) and **fails**
`out = keptAttrs srcAttrs choice glob` on the `effective = true ⇒ srcAttrs = []`
goal (G-DIFF).

## B. The container site — `Dataset.quantile` (`xarray/core/dataset.py:4694`, call site 4769)

Gold hunk:
```
  variables[name] = var.quantile(
-     q, dim=reduce_dims, interpolation=interpolation
+     q, dim=reduce_dims, interpolation=interpolation, keep_attrs=keep_attrs,
  )
```

| # | Solution.lean impl op (`reduceContainerAttrs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `let r ← reduceElementAttrs srcAttrs choice glob` | `var.quantile(q, dim=reduce_dims, interpolation=interpolation, keep_attrs=keep_attrs)` | I (callee-under-spec) | the container threads its OWN `choice`/`keep_attrs` to the member reduction unchanged. `prove_correct` applies `reduceElementAttrs_correct` directly (callee-under-spec, plan §3) — better than an axiom. The per-variable/`numeric_only`/coord logic around this call is unchanged (mapping.md §2). |
| B2 | `return r` | `variables[name] = …` and downstream Dataset assembly | R | the member's resulting attrs are the modeled view; assembly into the Dataset is unchanged structure (mapping.md §2). |

Discriminating content — the container passes its own `choice`, not `none`.
`Solution_prepatch_2.lean` reproduces the pre-patch call (omits `keep_attrs`,
i.e. `reduceElementAttrs srcAttrs none glob`) and **fails**
`keptAttrs srcAttrs none glob = keptAttrs srcAttrs choice glob` — they diverge at
`choice = some true`, `glob ∈ {gDefault, gDrop}` (an explicit keep lost to the
drop fallback), exactly the F2P scenario (`keep_attrs=True`, default global)
(G-DIFF).

## C. The wrapper site — `DataArray.quantile` (`xarray/core/dataarray.py:2827`)

| # | Solution.lean construct (`reduceLabeledAttrs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | `let r ← reduceContainerAttrs srcAttrs choice glob; return r` | `DataArray.quantile` already forwards `keep_attrs` to `_to_temp_dataset().quantile(...)` (unchanged by the patch) | I (callee-under-spec) | the F2P entry point; composes the two fixed sites end to end. `prove_correct` applies `reduceContainerAttrs_correct`. This wrapper is not itself patched, but is the function the F2P test calls (`DataArray(self.va).quantile(...)`), so it is modeled to make the end-to-end observable explicit. No separate prepatch (its body is unchanged; the two prepatches cover the two patched sites). |

## D. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The changed operations — attaching source
metadata under the keep decision (site A) and forwarding the per-call choice
(site B) — are both modeled **deeply and directly** (the `keptAttrs`/`effectiveKeep`
conditional and the threaded `choice`), not hidden behind an axiom about a
function under change. The only foreign callee, `_get_keep_attrs`, is **unchanged**
and modeled deeply as `resolveGlobal` (A-reference, G-AX). There is **no consumed
axiom**.

## E. verify(Solution) ⇒ resolved

`reduceElementAttrs` verifies only if its result carries `srcAttrs` exactly when
the effective keep decision is true (A5), `reduceContainerAttrs` only if it
threads the caller's own `choice` (B1), and `reduceLabeledAttrs` only if it
composes them end to end (C1). By R (`attrs ↔ List (String × String)`,
`keep_attrs ↔ Option Bool`, `OPTIONS ↔ GlobalPref`, unchanged value/shape) the
verified reductions equal the patched `Variable.quantile` / `Dataset.quantile` /
`DataArray.quantile` on the tested inputs; by G-AX the deep model `resolveGlobal`
equals the real `_get_keep_attrs` (A-reference); by G-CONF the R/I transliteration
agrees with `patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the one audited callee — and the gold patch resolves (G-RESOLVE). The single
trust point (plan §1.1) is the A-reference soundness (G-AX); refinement fidelity
is this doc (G-EQ + G-CONF).
