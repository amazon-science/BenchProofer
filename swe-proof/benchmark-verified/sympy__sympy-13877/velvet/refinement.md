# refinement.md — sympy__sympy-13877

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`selectPivot` `do` block) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A-consumed** (proof uses an
axiom's `ensures`), **A-reference** (a deep model validated == the real callee by
G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The pivot-selection site — inner `bareiss` (`sympy/matrices/matrices.py:165`, body :195)

Gold hunk (within `_eval_det_bareiss`):
```
-        # XXX included as a workaround for issue #12362.  Should use `_find_reasonable_pivot` instead
-        def _find_pivot(l):
-            for pos,val in enumerate(l):
-                if val:
-                    return (pos, val, None, None)
-            return (None, None, None, None)
...
-            # XXX should use `_find_reasonable_pivot`.  Blocked by issue #12362
-            pivot_pos, pivot_val, _, _ = _find_pivot(mat[:, 0])
+            pivot_pos, pivot_val, _, _ = _find_reasonable_pivot(mat[:, 0],
+                                         iszerofunc=_is_zero_after_expand_mul)
```
and the new module helper:
```
+def _is_zero_after_expand_mul(x):
+    """Tests by expand_mul only, suitable for polynomials and rational functions."""
+    return expand_mul(x) == 0
```

| # | Solution.lean impl op (`selectPivot`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `col : Array Entry` | `mat[:, 0]` — the first column passed to the pivot finder | R | a column of scalar `Expr` ↔ `Array Entry`; each entry `x` ↔ `⟨bool(x), expand_mul(x)≠0⟩` (mapping.md §2). G-CONF bridges column ↔ `Array Entry` index-for-index. |
| A2 | `require consistent col` (`mathNonzero j → litNonzero j`) | the standing sympy fact `expand_mul(x)≠0 ⟹ bool(x)` over the column | A-reference | the spec only assumes the WEAKER-implies-CHEAPER direction that always holds; G-AX (`check_consistent`) runs the real `expand_mul`/`bool` and confirms it on boundary + fuzz. NOT consumed in the loop body's flow; it is the frame the prepatch's wrong recogniser would need but the spec forbids relying on. |
| A3 | scan loop: `i` from `0`, stop at first `(col[i]!).mathNonzero = true`, recording `idx := i`, `found := true` | `_find_reasonable_pivot(col, iszerofunc=_is_zero_after_expand_mul)` on the modeled non-Float / decisive-`iszerofunc` branch (reduces to "first index whose entry is non-zero after `expand_mul`") | A-reference + I | the changed selection is modeled **deeply**: the decisive recogniser is `Entry.mathNonzero` (= `not _is_zero_after_expand_mul`), validated == the real callee by G-AX (`check_definition`, `check_pivot_branch`). The scan ops (`if`, index bump, the `while`) are **I** (concrete, transliterated by G-CONF); the equality of the deep recogniser to the real `_is_zero_after_expand_mul`/`expand_mul` is the **A-reference**. mapping.md §3.1. |
| A4 | result `⟨found, idx⟩ : PivotResult` | the observable part of the returned 4-tuple, `(pivot_offset is None?, pivot_offset)` | R | `pivot_offset is None` ↔ `found=false`; `pivot_offset=k` ↔ `⟨true,k⟩`. `pivot_val` and the two trailing `None`s are not observable for the fix (the determinant uses only which row is the pivot), so they are omitted (mapping.md §2). |

Discriminating content of the change — selection by the **decisive** recogniser
(`expand_mul(x)≠0`) rather than the **structural** one (`bool(x)`) — lives in the
loop guard `(col[i]!).mathNonzero = true` and the postcondition
`(col[res.idx]!).mathNonzero = true`. The pre-patch `_find_pivot` selected on
`if val:` (Python truthiness ⇒ `litNonzero`); `Solution_prepatch.lean` reproduces
that (loop tests `litNonzero`) and **fails** the clause
`res.found = true → (col[res.idx]!).mathNonzero = true` (G-DIFF): when an entry is
structurally non-zero but algebraically zero (`litNonzero = true`,
`mathNonzero = false`, allowed by `consistent`), the prepatch returns that index
yet the spec demands `mathNonzero = true` there.

Why this is the bug: choosing an algebraically-zero pivot makes the subsequent
division `entry = (pivot_val*… - …)/cumm` divide by an effectively-zero pivot,
producing `nan`; later `nan < 0` raises `Invalid NaN comparison` (the traceback in
the issue). Selecting only a decisively-non-zero pivot removes the bad division,
and the issue matrices then evaluate to `M(5..7).det() == 0` (FAIL_TO_PASS).

## B. Site B — `random_complex_number` (test-neutral, not modeled)

Gold also extends `sympy/utilities/randtest.py:16`: `random_complex_number` gains
an optional `tolerance=None` keyword forwarded to `nsimplify`. With the default
`tolerance=None`, `nsimplify(A, rational=True, tolerance=None)` is observationally
**identical** to the pre-patch `nsimplify(A, rational=True)` (nsimplify treats a
`None` tolerance as omitted — `simplify.py:1271`). No existing caller passes the
new keyword, so behaviour is byte-identical for every PASS_TO_PASS / FAIL_TO_PASS
test. This is a strictly-additive signature extension with no observable behaviour
change; it is carried in `patch.diff` (gold verbatim, for G-RESOLVE) but is not a
modeled behaviour and needs no separate failing prepatch (a prepatch must keep the
spec byte-identical, G-DIFF, and there is no behaviour here to discriminate). See
mapping.md §5.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
zero-test that decides pivot selection — is modeled **deeply** (the `mathNonzero`
field + the spelled-out scan, step A3, an A-reference + I), not hidden behind an
axiom about the function under change. There is **no consumed axiom**; the only
A rows are A-reference (`consistent`, the decisive recogniser), validated against
the real `expand_mul` / `_is_zero_after_expand_mul` by G-AX.

## D. verify(Solution) ⇒ resolved

`selectPivot` verifies only if it returns the first index that is decisively
non-zero (`mathNonzero`, A3) and reports `found=false` exactly when no such index
exists. By R (`column ↔ Array Entry`, `pivot_offset ↔ found/idx`) the verified
selection equals `_find_reasonable_pivot(mat[:,0],
iszerofunc=_is_zero_after_expand_mul)` on the modeled non-Float branch; by G-AX
the deep recogniser equals the real `_is_zero_after_expand_mul`/`expand_mul`
(A-reference) and `consistent` holds of every real scalar; by G-CONF the R/I
transliteration of the scan agrees with `patch.diff`'s behaviour on ≥10⁵ fuzzed
columns. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and the audited recogniser — and the gold patch
resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1: A-reference
soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
