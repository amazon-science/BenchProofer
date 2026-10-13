# refinement.md — pydata__xarray-3151

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`validateOrdering` `do` block plus the deep `isMonoInc`/`isMonoDec`/`dimOK`/
`allDimsOK` models) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete op). No consumed axioms (no **A-consumed**).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference leg + narrative are audited by **G-AX** and **G-EQ**.
Claim: any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The ordering-validation site — `combine_by_coords` (`xarray/core/combine.py:501-510`)

Gold hunk:
```
-        for dim in concatenated.dims:
-            if dim in concatenated:
-                indexes = concatenated.indexes.get(dim)
-                if not (indexes.is_monotonic_increasing
-                        or indexes.is_monotonic_decreasing):
-                    raise ValueError(... "monotonic global indexes" ...)
+        for dim in concat_dims:
+            indexes = concatenated.indexes.get(dim)
+            if not (indexes.is_monotonic_increasing
+                    or indexes.is_monotonic_decreasing):
+                raise ValueError(... "monotonic global indexes" ...)
```

The fix narrows the iteration set from **every coordinate axis**
(`concatenated.dims` filtered by `if dim in concatenated`) to **only the joined
axes** (`concat_dims`, the dims returned by `_infer_concat_order_from_coords`,
which are exactly the axes that vary across the inputs). An axis whose
coordinate is identical on every input is therefore no longer required to be
monotonic.

| # | Solution.lean impl op (`validateOrdering`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `dims : List Dimension` | the coordinate axes of `concatenated` paired with `concat_dims` membership | R | `List Dimension`, each axis carrying `varies` (∈ concat_dims) + `index` (its concatenated coord values as order-ranks). mapping.md §2. |
| A2 | `Dimension.varies` discriminates the iteration set | `for dim in concat_dims` (post) vs `for dim in concatenated.dims if dim in concatenated` (pre) | R + I | post-patch visits exactly the axes with `varies = true`; `dimOK d = !d.varies || …` makes a non-varying axis vacuously OK — the precise behavioural content of the fix. |
| A3 | `isMonotonic d.index = isMonoInc d.index || isMonoDec d.index` | `indexes.is_monotonic_increasing or indexes.is_monotonic_decreasing` | A-reference + I | the order test is modeled **deeply** (`isMonoInc`/`isMonoDec`, pure region); their equality to real pandas is the **A-reference** G-AX validates. The `||` and the per-axis decision are **I** (concrete, transliterated by G-CONF). mapping.md §3.1. |
| A4 | `ok = allDimsOK dims` (false ⇔ some joined axis non-monotonic) | the loop raises `ValueError` iff some visited axis is non-monotonic | R + I | `ok = false` ⇔ the real loop raises the monotonic-global-indexes error; `ok = true` ⇔ it returns normally. The backward `while` fold over `dimOK` is the conjunction the `for`/`raise` expresses. |

Discriminating content of the change — a **non-varying** (bystander) axis is
exempt from the monotonic requirement — lives in `dimOK d = !d.varies ||
isMonotonic d.index`. The pre-patch loop checked monotonicity on every
coordinate axis regardless of `varies`; `Solution_prepatch.lean` reproduces that
(`acc := isMonotonic d.index && acc`, ignoring `varies`) and **fails**
`ok = allDimsOK dims` on exactly the clause where a non-varying axis is
non-monotonic (G-DIFF — confirmed: unsolved goal `isMonotonic … = dimOK …`).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely *changed* — the
set of axes the monotonic check ranges over — is modeled **directly** via the
`varies` flag and `dimOK`'s `!d.varies` guard (steps A2/A4), not hidden behind an
axiom. The one library predicate the loop calls (`pandas` monotonicity) is
**unchanged** and modeled deeply (A-reference, G-AX-checked), not the function
under change. There is no consumed axiom.

## C. verify(Solution) ⇒ resolved

`validateOrdering` verifies only if its result equals `allDimsOK dims`, i.e. it
rejects exactly when some **joined** axis is non-monotonic and is silent on
non-varying axes (A2/A4). By R (`List Dimension` ↔ the coordinate axes;
`varies` ↔ `dim ∈ concat_dims`; `index` ↔ order-ranks of the concatenated
coordinate; `ok=false` ↔ raises) the verified decision equals the patched loop's
raise/return decision on the tested inputs; by G-AX the deep model
`isMonoInc`/`isMonoDec` equals real `pandas` monotonicity (A-reference); by
G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour over the
fuzzed multi-axis grid. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the audited callee — and
the gold patch resolves (G-RESOLVE). The single trust point is A-reference
soundness (G-AX); there is no consumed axiom.
