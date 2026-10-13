# refinement.md — astropy__astropy-14539

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`diffVLAColumn` `do` block, with the deep models `isVLA`/`rowResult`/`anyMulti`
and the `diffSpec` route) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A-consumed** (proof uses an
axiom's `ensures`), **A-reference** (deep model validated == the real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The route choice — `TableDataDiff._diff` per-column body (`astropy/io/fits/diff.py`)

Gold hunk:
```
-            elif "P" in col.format:
+            elif "P" in col.format or "Q" in col.format:
                 diffs = (
                     [ idx for idx in range(len(arra))
                       if not np.allclose(arra[idx], arrb[idx], rtol=..., atol=...) ],
                 )
             else:
                 diffs = np.where(arra != arrb)
```

| # | Solution.lean impl op (`diffVLAColumn`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `fmt : List Char` | `col.format` (str) | R | `str ↔ List Char` (mapping.md §2). G-CONF bridges via real `col.format`. |
| A2 | parameter `col : Column` (`varLength`, `numComparable`) | the column's intrinsic numpy dtype kind | R | `col.varLength ↔ (arra.dtype == object)` (intrinsically variable-length); `col.numComparable ↔` the elements are numeric-closeness-comparable (`np.allclose` does not raise) (mapping.md §2). These are the element-kind properties that determine whether a chosen route can complete; G-AX validates both bijections. |
| A3 | parameter `rows : List Row` (each `Row` = `differs`, `multiElem`) | the two aligned arrays `arra`, `arrb` of the column | R | each row ↔ `(not np.allclose(arra[i],arrb[i],…), len(arra[i])>1)` (mapping.md §2). The `rtol`/`atol`/`numdiffs` reporting params are unchanged and folded into `differs`. |
| A4 | `if isVLA fmt then …` — `isVLA fmt = fmt.contains 'P' \|\| fmt.contains 'Q'` | `elif "P" in col.format or "Q" in col.format:` | A-reference + I | the route-selecting test is modeled **deeply**: `isVLA` (pure region) transliterates the `or` of the two substring tests verbatim. The `if`/`else` branching is **I** (concrete control flow, transliterated by G-CONF); the equality of `isVLA` to the real format test, AND to the intrinsic kind `col.varLength` (object dtype), is the **A-reference** G-AX validates (mapping.md §3.1, fact 4). **This is the changed clause** — pre-patch was `"P" in col.format` only. |
| A5 | VLA branch result `rowWiseOutcome col rows` = `if col.numComparable then Except.ok (rowResult rows) else Except.error DiffErr.ambiguous` | the VLA branch `diffs = ([idx for idx in range(len(arra)) if not np.allclose(…)],)`; `self.diff_total += len(set(diffs[0]))` | A-reference + I | the row-wise route is modeled by its OBSERVED outcome: `np.allclose` **completes** with the per-row `differs` verdict iff the elements are numeric-closeness-comparable (`col.numComparable`), and otherwise **raises** (`DTypePromotionError` on a text column → `DiffErr.ambiguous`). The differing-index set `{i \| (rowResult rows)[i]}` ↔ `set(diffs[0])`. The equality `(row-wise raises) ↔ ¬col.numComparable` and `(completes) ⇒ rowResult` is the **A-reference** fact G-AX validates (mapping.md §3.2, fact 1). Because every VLA column is numComparable, the VLA branch always completes (`Except.ok`). The list-build is **I**. |
| A6 | generic branch `genericOutcome col rows` = `if col.varLength && anyMulti rows then Except.error DiffErr.ambiguous else Except.ok (rowResult rows)` | the `else:` branch `diffs = np.where(arra != arrb)` | A-reference + I | the generic element-wise route is modeled by its OBSERVED outcome: it **raises** (`DiffErr.ambiguous`) iff the column is intrinsically variable-length (object dtype, `col.varLength`) AND some row is multi-element (`anyMulti rows`); otherwise it completes with the same per-row verdict as A5. A *non-VLA* fixed-multidim column (e.g. `2J`) has multi-element rows but is a regular fixed-width block, so `np.where` completes — confirmed in-container; the guard is `col.varLength && anyMulti rows`, NOT `anyMulti rows` alone. The `error`/`ok` split is **I** control flow; the equality `(generic raises) ↔ (col.varLength ∧ anyMulti rows)` and `(generic completes) ⇒ same verdict` are the **A-reference** facts G-AX validates (mapping.md §3.2, fact 2). Because the post-patch classifier routes EVERY VLA column row-wise (A4) and `isVLA fmt = col.varLength`, the generic branch only ever runs with `col.varLength = false`, so it can never raise: the post-patch comparison provably always completes. |

Discriminating content of the change — a column whose format carries `Q` but not
`P` (e.g. `QJ`, `QD`) with multi-element rows — lives in
`isVLA fmt = fmt.contains 'P' || fmt.contains 'Q'`: the spec routes such a column
to the row-wise branch (`rowWiseOutcome col rows = Except.ok (rowResult rows)`,
since it is numComparable), whereas the pre-patch classifier `"P" in col.format`
routes it to the generic branch (`genericOutcome col rows = Except.error
DiffErr.ambiguous`, since it is `varLength` and multi-element).
`Solution_prepatch.lean` reproduces the P-only classifier and **fails**
`out = diffSpec fmt col rows` exactly on the `'P' ∈ fmt` vs `isVLA fmt` goal
(G-DIFF). Independently, the route choice is now load-bearing in BOTH directions:
an impl that ignores the format and routes every column **row-wise** produces
`Except.error` on a text column (`¬numComparable`) where the spec demands
`Except.ok` (the generic route), so it is rejected — the too-weak counterexample
the prior audit found can no longer verify.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
route-selecting format test — is modeled **deeply** (the spelled-out `isVLA`,
step A4, an A-reference + I), not hidden behind an axiom about the function under
change. There is **no consumed axiom**: the two routes' behaviors
(`rowWiseOutcome`/`genericOutcome`, built from `rowResult`/`anyMulti`/
`DiffErr.ambiguous` and the intrinsic `Column` kind) are deep models of UNCHANGED
numpy operations (`np.allclose` row-wise, `np.where` generic), validated == the
real callees by G-AX (A-reference).

## C. verify(Solution) ⇒ resolved

`diffVLAColumn` verifies only if its output equals `diffSpec fmt col rows`: a
variable-length column (`isVLA fmt`, i.e. `'P'` OR `'Q'` present) is compared
row-wise (`rowWiseOutcome`), which completes iff `col.numComparable` — and every
VLA column IS numComparable (A4+A5), so it always completes; a non-VLA column
takes the generic route (`genericOutcome`) whose `ValueError` failure is pinned to
`col.varLength && anyMulti rows` (A6) — which, on the non-VLA branch (`isVLA fmt =
col.varLength = false`), is unreachable, so the comparison always completes. The
route choice is load-bearing in both directions: a text column (`¬numComparable`)
MUST take the generic route (the row-wise numeric route would raise), and a VLA
multi-element column MUST take the row-wise route (the generic route would raise);
so neither "route everything row-wise" nor "route everything generic" satisfies
the spec. By R (`str ↔ List Char`, the `Column`/`Row` abstraction) the verified
dispatch equals the gold-patched `_diff` route choice on the tested columns; by
G-AX the deep models `isVLA`/`rowWiseOutcome`/`genericOutcome` equal the real
format test, the intrinsic dtype kind, and the real two routes (A-reference); by
G-CONF the R/I transliteration of the dispatch agrees with `patch.diff`'s
behaviour on ≥10⁵ inputs (incl. text columns routed generic). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited callees — and the gold patch resolves (G-RESOLVE). Trust
points are exactly the two of plan §1.1: deep-model soundness (G-AX) and
refinement fidelity (this doc, G-EQ + G-CONF).
