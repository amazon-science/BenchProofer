# refinement.md — scikit-learn__scikit-learn-13328

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`validatedElementType` `do` block and the deep `resolveElemType` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses the axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The input-validation site — `HuberRegressor.fit` (`sklearn/linear_model/huber.py:253`)

Gold hunk:
```
  X, y = check_X_y(
-     X, y, copy=False, accept_sparse=['csr'], y_numeric=True)
+     X, y, copy=False, accept_sparse=['csr'], y_numeric=True,
+     dtype=[np.float64, np.float32])
```

| # | Solution.lean impl op (`validatedElementType`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `orig : DType` | the element type `X.dtype` of the matrix entering `check_X_y` | R | `np.dtype` ↔ `DType` (mapping.md §2). G-CONF bridges via the §2 category map. Shape/values dropped: the change observes only the element type. |
| A2 | `let accepted := orig.isAccepted` | the predicate `dtype_orig in [np.float64, np.float32]` evaluated inside `check_array` (`validation.py:460`) for the requested accept-list | R + I | the new `dtype=[np.float64, np.float32]` argument is the accept-list; membership is the concrete boolean test, transliterated identically by G-CONF. |
| A3 | `let out := if accepted then orig else DType.f64` | the resolution `dtype = None` (preserve) vs `dtype = dtype[0]` (convert to `float64`) followed by `np.asarray(array, dtype=dtype)` (`validation.py:461–466,496`) | A-reference + I | the unchanged callee `check_array`'s element-type resolution is modeled **deeply** by `resolveElemType` (pure region) and the `if accepted …` is its concrete transliteration (**I**, G-CONF-checked); the equality of that deep model to the real `check_array` resolution under the list request is the **A-reference** G-AX validates. mapping.md §3.1. No consumed axiom. |
| A4 | `return out` (the validated `DType`) | the validated `X` flowing on to `_huber_loss_and_gradient` | R | only the element type is observable to the modeled property; the matrix continues unchanged in shape/values (mapping.md §2). |

Discriminating content of the change — a **non-accepted** input element type
(notably `boolean`, the issue's truth-valued matrix; also `integer`, `f16`) is
**converted to `f64`** rather than passed through — lives in
`resolveElemType orig = f64` for non-accepted `orig` (model) ⇔ the `dtype =
dtype[0]` branch of `check_array` under the list request (real). The pre-patch
default `dtype="numeric"` preserved a non-`object` input element type
(`validation.py:452–457`), so a `bool` matrix reached `_huber_loss_and_gradient`
unconverted and the unary `-axis0_safe_slice(X, …)` (`huber.py:93`) raised
`TypeError` (numpy: "boolean negative `-` not supported").
`Solution_prepatch.lean` reproduces that `"numeric"` policy and **fails** both
`out = resolveElemType orig` and `out.isFloating = true` on `orig = boolean`
(and `integer`, `f16`) — G-DIFF.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely *changed* — the
argument tightening the element-type contract — is modeled **deeply** (the
spelled-out `resolveElemType`, step A3, an A-reference + I), not hidden behind an
axiom about the function under change: there is no consumed axiom at all. The
only A leg is the A-reference deep model of the **unchanged** callee
`check_array`, validated by G-AX.

## C. verify(Solution) ⇒ resolved

`validatedElementType` verifies only if its output equals the exact resolution
`if orig.isAccepted then orig else f64` (A3) AND is guaranteed floating
(`resolveElemType_isFloating`). By R (`np.dtype ↔ DType`, the accept-list
membership, the matrix carried on unchanged) the verified result equals the
element type the gold `check_X_y(..., dtype=[np.float64, np.float32])` produces
on the tested inputs; by G-AX the deep model `resolveElemType` equals the real
`check_array` resolution (A-reference); by G-CONF the R/I transliteration agrees
with `patch.diff`'s behaviour on the fuzzed element types. A non-floating input
therefore cannot survive validation unconverted, so `_huber_loss_and_gradient`'s
signed arithmetic is well-defined and `test_huber_bool` no longer crashes.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited callee — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: A-reference
soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
