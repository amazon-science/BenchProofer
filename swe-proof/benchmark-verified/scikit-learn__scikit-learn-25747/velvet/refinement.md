# refinement.md — scikit-learn__scikit-learn-25747

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`wrapContainer` `do` block, plus the `sizeFits`/`resolvedCols`/`frameAfter`/
`wrapResult` pure model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A-consumed** (proof uses an
axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); there are no A legs in this bundle (no axioms). Claim: any impl verifying
against the frozen spec, refined per the map below, is behaviourally equal to the
gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The wrapping site — `_wrap_in_pandas_container`, DataFrame branch

Gold hunk (`sklearn/utils/_set_output.py`, the `isinstance(data_to_wrap, pd.DataFrame)` branch):
```
  if isinstance(data_to_wrap, pd.DataFrame):
      if columns is not None:
          data_to_wrap.columns = columns
-     if index is not None:
-         data_to_wrap.index = index
      return data_to_wrap
```

| # | Solution.lean impl op (`wrapContainer`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `mut frame : Frame` | `data_to_wrap` (the `pd.DataFrame` adjusted in place and returned) | R | `pd.DataFrame` ↔ `Frame {colLabels, rowLabels}` (mapping.md §2); the in-place mutation is the `mut` parameter. |
| A2 | `colSupplied : Option (List Lbl)` | `columns` (after callable-resolution prologue, lines 47-51) | R | `None` ↔ `none`, label seq ↔ `some`; the callable is resolved before the bijection exactly as the unchanged prologue does (mapping.md §2). |
| A3 | `rowSupplied : Option (List Lbl)` | `index` keyword argument | R | `None` ↔ `none`, label seq ↔ `some`. Present in the signature because the real function takes it; the post-patch branch never reads it — its absence of effect is the fix (A6). |
| A4 | `if sizeFits colSupplied frame.colLabels then … else return Except.error WrapErr.sizeMismatch` | the length validation pandas performs inside `data_to_wrap.columns = columns` (line 56-57): a set not holding one label per existing column raises `ValueError: Length mismatch` out of the branch, BEFORE any label is written | R | `sizeFits supplied current` ↔ `supplied is None or len(supplied) == len(current)`; the escaping `ValueError` ↔ `Except.error WrapErr.sizeMismatch`; pandas validates before mutating, so the failing path leaves `frame` untouched (`frameAfter` = identity) — G-CONF fuzzes ill-fitting sets and checks both the failure and the untouched axes. |
| A5 | `frame := { frame with colLabels := resolvedCols colSupplied frame.colLabels }` (fitting path) | `if columns is not None: data_to_wrap.columns = columns` (successful assignment) | R + I | `resolvedCols supplied current = supplied.getD current` IS "take the supplied column labels when provided, else keep the current ones" — the concrete transliteration of the (unchanged) column-setting conditional on the path where the assignment succeeds. The row axis is untouched by this assignment (struct update keeps `rowLabels`). G-CONF transliterates it. |
| A6 | (no row-axis assignment) — `ensures frame.rowLabels = frameOld.rowLabels` | the **deleted** `if index is not None: data_to_wrap.index = index` | I (deletion) | the behavioural change: the post-patch branch leaves the row axis exactly as the container had it — whatever `rowSupplied` holds and whatever its size (pre-patch, an ill-fitting `index` ALSO raised; post-patch it is ignored entirely). Modeled as the *absence* of any `rowLabels` write plus the explicit directive-5 frame clause pinning it to `frameOld.rowLabels`. |
| A7 | `return Except.ok frame` | `return data_to_wrap` | R | the same container, adjusted, handed back; success ↔ `Except.ok`. |

Discriminating content of the change — an already-labelled container **keeps its
own row labels**, the offered row-label set having no effect — lives in
`ensures frame.rowLabels = frameOld.rowLabels` (model) ⇔ the deletion of
`data_to_wrap.index = index` (real). The pre-patch code overwrote the row axis
with `index` (when it fit; and raised when it did not);
`Solution_prepatch.lean` reproduces that
(`frame := { frame with rowLabels := rowSupplied.getD frame.rowLabels }` on the
fitting path, error otherwise) and **fails** `ensures frame.rowLabels =
frameOld.rowLabels` (G-DIFF) — the exact clause the F2P test
`test_set_output_pandas_keep_index` asserts.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — the suppression
of the row-axis overwrite — is modeled **deeply** (the absence of the write,
pinned by the directive-5 frame clause A6), not hidden behind an axiom. The
pandas length check guarding the column-axis assignment (A4) is likewise modeled
deeply as `sizeFits` in the pure region and mechanically cross-checked by
G-CONF's ill-fitting fuzz cases. There is **no consumed axiom** and **no
deep-model reference**: the branch calls nothing whose behaviour the proof must
assume, so G-AX is skipped.

## C. verify(Solution) ⇒ resolved

`wrapContainer` verifies only if (A4) an ill-fitting column-label set makes the
request fail with the size-mismatch error, leaving the container untouched, AND
(A5) on the fitting path the column axis takes the supplied labels when provided
and is otherwise unchanged, AND (A6) the row axis equals its prior value
`frameOld.rowLabels` — i.e. the offered `rowSupplied` has no effect. By R
(`pd.DataFrame ↔ Frame`, `columns/index ↔ Option (List Lbl)`, `ValueError ↔
Except.error`) the verified adjustment equals the gold branch: set columns when
supplied and fitting (raise when ill-fitting), return the container with its
original row labels intact. By G-CONF the R/I transliteration of the branch —
including the failure outcome and the untouched-on-failure axes — agrees with
`patch.diff`'s `(columns, index)` behaviour on ≥10⁵ inputs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The single trust point is
refinement fidelity (this doc, G-EQ + G-CONF); there are no axioms, so axiom
soundness (G-AX) is vacuous.
