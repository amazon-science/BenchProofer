# refinement.md — scikit-learn__scikit-learn-25102

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `projectColumns` `do` block and the deep `selectMasked` / `keptCol` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses the axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I; no kind-3.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The projection site — `SelectorMixin._transform` (`sklearn/feature_selection/_base.py:92`)

Gold hunk (the observable change):
```
-        if len(mask) != X.shape[1]:
-            raise ValueError("X has a different shape than during fitting.")
-        return X[:, safe_mask(X, mask)]                  # homogeneous ndarray path
+        return _safe_indexing(X, mask, axis=1)           # container-preserving projection
   ... and the empty-output DataFrame path:
+            if hasattr(X, "iloc"):
+                return X.iloc[:, :0]
```

| # | Solution.lean impl op (`projectColumns`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `cols : List (Int × Bool)` | the validated `X` (DataFrame) + its support `mask` | R | a 2D DataFrame with its mask ↔ `List (Int × Bool)`: `i`-th column ↔ `(dtypeCode_i, mask_i)` (mapping.md §2). G-CONF bridges DataFrame ↔ list of `(dtype, bit)`. |
| A2 | `keptCol c = if c.2 then [c.1] else []` (per-column contribution; kept column keeps its OWN type `c.1`) | the per-column action of `_safe_indexing(X, mask, axis=1)` (`X.iloc[:, mask]`): retained columns carried through with their own dtype, dropped columns omitted | A-reference + I | the changed projection is modeled **deeply**: `keptCol`/`selectMasked` (pure region) and the verified loop ARE the projection. No consumed projection axiom. The fold ops (`keptCol c`, `++`, the loop) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `_safe_indexing(X, mask, axis=1)` per-column dtypes is the **A-reference** G-AX validates. mapping.md §3.1. |
| A3 | result is `selectMasked cols`: the ordered concatenation of kept columns' own types, computed by the backward `while` fold | `_safe_indexing(X, mask, axis=1)` (empty path `X.iloc[:, :0]` when no column kept ⇒ `[]`) | A-reference + I | order + membership + per-column type preservation; the empty selection maps to `[]` = `selectMasked` of an all-`False` mask. |
| A4 | `result` returned (`List Int`) | the projected DataFrame, observed by the F2P tests via `output.dtypes` / `output.columns` | R | only the ordered per-column dtype identities are observable to the F2P `==` assertions (mapping.md §2); cell values / `shape[0]` / index are unchanged by selection and out of scope. |

Discriminating content of the change — a retained column keeps its **own**
element type `c.1`, not a single homogeneous default — lives in
`keptCol p = if p.2 then [p.1] else []` (model) ⇔ the container-preserving
`_safe_indexing(X, mask, axis=1)` (real). The pre-patch homogeneous ndarray path
emitted every kept column with one common type;
`Solution_prepatch.lean` reproduces that (`if c.2 then [0] else []`) and
**fails** `out = selectMasked cols` at the discriminating clause
`(if … then [0] else []) = keptCol …` (G-DIFF).

## B. The plumbing site — `cast_to_ndarray` (`sklearn/base.py:495`, `_base.py:68`)

Gold hunks: `BaseEstimator._validate_data` gains a `cast_to_ndarray=True`
parameter that, when `False`, skips the `check_array`/`check_X_y` coercion of
`X`/`y`; `SelectorMixin.transform` computes
`preserve_X = hasattr(X, "iloc") and output_config_dense == "pandas"` and passes
`cast_to_ndarray=not preserve_X`. A **flag-plumbing enabler**, not a separately
observable behavior.

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | (no separate node) — modeled as the precondition that `cols` reaches `projectColumns` with its per-column types intact (the DataFrame was NOT coerced to a homogeneous ndarray) | `cast_to_ndarray=not preserve_X` in `transform`; the `if cast_to_ndarray:` guards in `_validate_data` | R | the flag's only role is to deliver the un-coerced DataFrame to the projection site; under the pandas-output + DataFrame configuration the F2P tests use, this is the identity that makes `cols`'s `c.1` carry the original per-column types (mapping.md §1.1). It carries no observable behavior of its own beyond enabling site A. |

No separate failing prepatch for site B: the plumbing change is observable only
*through* the projection it enables. A prepatch must keep the spec byte-identical
(G-DIFF); site A's prepatch already exercises the end-to-end observable (dtype
collapse vs preservation), which is false unless BOTH edits are present — so the
single discriminating clause covers the cooperating change.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
column projection — is modeled **deeply** (the spelled-out fold `selectMasked`
with `keptCol`, step A2/A3, an A-reference + I), not hidden behind an axiom about
the function under change: there is no consumed projection axiom. There are no
consumed axioms at all (the `axioms` region is empty).

## D. verify(Solution) ⇒ resolved

`projectColumns` verifies only if its output equals the exact ordered
per-column projection that preserves each kept column's own type (A2/A3). By R
(DataFrame ↔ `List (Int × Bool)`; only ordered per-column dtypes observable)
the verified projector equals `_safe_indexing(X, mask, axis=1)` on the tested
DataFrame inputs; by G-AX the deep model `selectMasked` equals the real
per-column projection (A-reference) and the pre-patch ndarray path provably
collapses the dtypes (so the change is non-vacuous); by G-CONF the R/I
transliteration of the fold agrees with `patch.diff`'s behaviour on ≥10⁵ fuzzed
DataFrames. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement and the audited projection callee — and the
gold patch resolves (G-RESOLVE). Trust point: refinement fidelity (this doc,
G-EQ + G-CONF) and the single A-reference's soundness (G-AX); no consumed axioms.
