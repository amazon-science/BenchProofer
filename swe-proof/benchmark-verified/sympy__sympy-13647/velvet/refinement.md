# refinement.md — sympy__sympy-13647

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `insertColumns` `do` block + the `spliceRow`/`spliceCols` deep model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** (proof uses an axiom's `ensures`),
**A-reference** (deep model validated == real callee by G-AX), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the modeled domain, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The changed function — `_eval_col_insert` (`sympy/matrices/common.py:81`)

Gold hunk (the one-line index fix inside the per-cell rule `entry(i, j)`):
```
              elif pos <= j < pos + other.cols:
                  return other[i, j - pos]
-             return self[i, j - pos - other.cols]
+             return self[i, j - other.cols]

          return self._new(self.rows, self.cols + other.cols,
                           lambda i, j: entry(i, j))
```

**Key structural fact (the heart of the model).** `entry(i, j)` is **independent
of the row index `i`** in its *column* logic: for every row, the three branches
partition the result columns identically as `j < pos` / `pos ≤ j < pos+oc` /
`j ≥ pos+oc`, and `i` is only ever passed straight through as the row of the
source read. So `_new(rows, cols+oc, entry)` is exactly the **row-wise** splice:
result row `i` = (the first `pos` entries of `self` row `i`) ++ (`other` row `i`)
++ (the entries of `self` row `i` selected by the third branch). This is why the
model is `List (List Int)` with a per-row `spliceRow` and no row-index reasoning.

| # | Solution.lean impl op (`insertColumns`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `srows orows : List (List Int)`, `pos : Nat` | `self`, `other` (matrices), `pos` (int) of `_eval_col_insert` | R | matrix ↔ `List (List Int)`, entry ↔ `Int`, position ↔ `Nat` (mapping.md §2). G-CONF bridges via `Matrix(rows)` / `R[i,j]`. |
| A2 | `require srows.length = orows.length` | the `self.rows == other.rows` guard in the wrapper `col_insert` (`common.py:214`) that must hold before `_eval_col_insert` runs | R | the modeled domain: equal row counts (mapping.md §2). The wrapper raises `ShapeError` otherwise, so `_eval_col_insert` never sees unequal counts. |
| A3 | the loop builds each result row as `spliceRow s o pos = s.take pos ++ o ++ s.drop pos` | `_new(rows, cols+oc, entry)` with the **fixed** `entry`: branch1 `self[i,j]` (j<pos), branch2 `other[i,j-pos]`, branch3 `self[i, j-other.cols]` (j≥pos+oc) | I | deep, concrete model. branch1 ↔ `s.take pos`; branch2 ↔ `o`; branch3, the FIXED read `self[i, j-oc]` over `j ∈ [pos+oc, c+oc)`, hits source columns `j-oc ∈ [pos, c)` = `s.drop pos`. The three concatenated = `spliceRow`. Validated == real `col_insert` by G-CONF over ≥10⁵ matrices. |
| A4 | `result` returned (`List (List Int)`) | `self._new(...)` (the constructed matrix) | R | `_new` materializes cell `(i,j)`=`entry(i,j)`; read back as rows it IS `spliceCols` (mapping.md §1). Modeled deeply, not axiomatized — see §C. |

Discriminating content of the change — the trailing segment of each row is the
**suffix** `self[i, j-other.cols]` (columns `pos..c-1`, i.e. `s.drop pos`), NOT
the pre-patch `self[i, j-pos-other.cols]` (columns `0..c-pos-1`, i.e.
`s.take (c-pos)`). This lives in `spliceRow`'s `++ srow.drop pos`. The pre-patch
read duplicates each row's PREFIX after the inserted block and discards its tail;
`Solution_prepatch.lean` reproduces exactly that (`s.take pos ++ o ++
s.take (s.length - pos)`) and **fails** `out = spliceCols pos srows orows`
(G-DIFF), at the third-segment clause.

## B. No second site

The gold patch touches a single line in one function. There is no second
independently-fixed behavior, hence one `Solution_prepatch.lean`.

## C. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. The operation that genuinely *changed* — the third-branch
column index of `entry` — is modeled **deeply** (the spelled-out `spliceRow`
suffix, step A3, an **I** op), not hidden behind an axiom about the function
under change. The matrix constructor `_new` is the only callee; it is modeled
deeply too (its grid-materialization IS `spliceCols`, step A4 — an **I** op
validated by G-CONF), not consumed as an axiom and not an A-reference. Hence
`axioms = []`, `deep_model_references = []`, and there is no `axiom_check.py`
(G-AX = skip). Both legs are pure R/I, so `conf_skip = false` and G-CONF
differential-tests the whole impl.

## D. verify(Solution) ⇒ resolved

`insertColumns` verifies only if its output equals the exact per-row splice with
the trailing segment being the original row's **suffix** from `pos` (A3). By R
(matrix ↔ `List (List Int)`, entry ↔ `Int`, equal-row-count domain) the verified
splice equals the patched `_eval_col_insert` / `col_insert` on the modeled
domain; by G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour on
≥10⁵ matrices including the issue's exact `eye(6)`/`2·ones(6,2)`/`pos=3` case.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The sole
trust point is refinement fidelity (this doc, G-EQ + G-CONF); there are no
axioms (G-AX is vacuous).
