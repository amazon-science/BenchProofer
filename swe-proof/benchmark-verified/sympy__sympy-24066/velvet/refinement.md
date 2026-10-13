# refinement.md — sympy__sympy-24066

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`normalizeDimensions` `do` block, the deep `normSeq`/`normDim` model, and the
opaque `isDimensionless` / `dimOne` axioms) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee —
**A-consumed** where the proof uses the axiom, **A-reference** where a deep model
is validated == the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The applied-function branch — `_collect_factor_and_dimension` (`unitsystem.py:192-196`)

Gold hunk:
```
 elif isinstance(expr, Function):
-    fds = [self._collect_factor_and_dimension(
-        arg) for arg in expr.args]
-    return (expr.func(*(f[0] for f in fds)),
-            *(d[1] for d in fds))
+    fds = [self._collect_factor_and_dimension(arg) for arg in expr.args]
+    dims = [Dimension(1) if self.get_dimension_system().is_dimensionless(d[1]) else d[1] for d in fds]
+    return (expr.func(*(f[0] for f in fds)), *dims)
```

The only behavioural change is the new `dims` line: each operand's dimension
`d[1]` is replaced by the canonical `Dimension(1)` when it is dimensionless, and
kept otherwise. The recursion (`fds = [...]`) and the factor reconstruction
(`expr.func(*(f[0] for f in fds))`) are byte-unchanged. The modeled operation is
exactly the construction of `dims` from the operand-dimension list.

| # | Solution.lean impl op (`normalizeDimensions`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `dims : List Dimension` | the operand-dimension list `[d[1] for d in fds]` (`unitsystem.py:194`) | R | the sequence of operand `Dimension` objects ↔ `List Dimension`, by position (mapping.md §2). G-CONF builds it via `[self._collect_factor_and_dimension(a)[1] for a in expr.args]`. The unchanged recursion that produces `fds` is upstream of the modeled op and identity under refinement. |
| A2 | `result = normSeq dims`: the per-element map `normDim`, computed by the backward `while` fold | the comprehension `[Dimension(1) if ...is_dimensionless(d[1]) else d[1] for d in fds]` | A-reference + I | the changed operation is modeled **deeply**: `normSeq`/`normDim` (pure region) and the verified loop ARE the per-element canonicalization. No consumed equational axiom about the function under change. The fold ops (`normDim d`, `::`, the loop) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real comprehension is the **A-reference** G-AX validates (mapping.md §3.1). |
| A3 | `normDim d = if isDimensionless d then dimOne else d` | `Dimension(1) if self.get_dimension_system().is_dimensionless(d[1]) else d[1]` | A-consumed + I | the conditional select. `isDimensionless` is the OPAQUE axiom over the UNCHANGED predicate `get_dimension_system().is_dimensionless` (mapping.md §3.2); `dimOne` is the OPAQUE axiom over `Dimension(1)` (mapping.md §3.3). The `if … then … else` combination is **I** (concrete). The proof consumes the axioms only as the same total predicate / same canonical value per element; G-AX confirms `is_dimensionless` is total and `Dimension(1)` is dimensionless. |
| A4 | `out` returned (`List Dimension`) | `dims` spliced into the return tuple `(expr.func(...), *dims)` | R | the normalized list is the tail of the returned tuple; the leading factor term `expr.func(*(f[0] for f in fds))` is unchanged by the patch (mapping.md §2) and identity under refinement, so only the dimension list is modeled. |

Discriminating content of the change — a **dimensionless-but-non-canonical**
operand dimension (e.g. `Dimension(time/(capacitance*impedance))` from
`second/(ohm*farad)`) maps to `Dimension(1)`, NOT to itself — lives in `normDim
d = if isDimensionless d then dimOne else d` (model) ⇔ the `Dimension(1) if
is_dimensionless(d[1]) else d[1]` step (real). The pre-patch branch returned the
operand dimension verbatim; `Solution_prepatch.lean` reproduces that (`result :=
d :: result`) and **fails** `out = normSeq dims` precisely on the clause
`dims[i-1]! = normDim dims[i-1]!` (G-DIFF), which is false exactly when an
operand is dimensionless yet not the canonical value — the bug the F2P test
`test_issue_24062` exercises via `1 + exp(T/(R*C))`.

## B. No second site

The patch touches a single branch of a single function; there is no second
independently-fixed behaviour. The only failing prepatch is site A's.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
per-element dimensionless canonicalization — is modeled **deeply** (the
spelled-out fold `normSeq`/`normDim`, step A2, an A-reference + I), not hidden
behind an axiom about the function under change. The only consumed axioms,
`isDimensionless` and `dimOne` (step A3), cover an **unchanged** predicate and an
**unchanged** constant; they are opaque (weakest contract, directive 7).

## D. verify(Solution) ⇒ resolved

`normalizeDimensions` verifies only if its output equals the exact per-element
canonicalization `normSeq` (A2): every dimensionless operand reported as `dimOne`
and every other operand kept (A3). By R (`List Dimension` ↔ the operand-dimension
list; the factor term and recursion are unchanged identities) the verified
operation equals the patched `dims` line on real applied-`Function` expressions;
by G-AX the deep model `normSeq` equals the real comprehension (A-reference) and
`is_dimensionless` / `Dimension(1)` meet the opaque axioms' usage (A-consumed); by
G-CONF the R/I transliteration of the fold agrees with `patch.diff`'s behaviour on
3000+ real Function-branch inputs. Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement and audited callees —
and the gold patch resolves (G-RESOLVE). Trust points are exactly the two of plan
§1.1: axiom soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
