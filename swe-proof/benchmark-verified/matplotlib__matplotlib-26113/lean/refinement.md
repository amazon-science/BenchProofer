# refinement.md — matplotlib__matplotlib-26113

Operation-by-operation correspondence between `implementation_hexbinAccum`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `accum`
list-comprehension in `Axes.hexbin`, `C is not None` branch). Tags: **R** type
refinement, **A-consumed** proof uses an axiom, **A-reference** deep model
validated == real callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let mut accum := []` then `for acc in cells do …` | the list comprehension `[… for Cs_at_i in [Cs_at_i1, Cs_at_i2] for acc in Cs_at_i[1:]]` iterating the flattened per-cell lists | R |
| 2 | `if (acc.length : Int) ≥ mincnt then` | `if len(acc) >= mincnt` (the patched keep test) | R |
| 3 | `accum := accum ++ [some (reduceC acc)]` | `reduce_C_function(acc)` (the summarised cell) | A-reference¹ |
| 4 | `else accum := accum ++ [none]` | `else np.nan` (the dropped cell) | R |
| 5 | `return accum` | `np.array([...], float)` (the assembled grid) | R |

¹ `reduce_C_function` (`reduceC`) is applied **identically** in `problem_spec`
(`cellSummary`) and `implementation`, so it cancels in the correctness proof and
needs no asserted property — it is a reference op, not a consumed axiom. The
`axioms` region asserts nothing (only the `opaque` signature is declared so it can
appear in the executable impl). Tagged A-reference for bookkeeping; there is no
`_prop` axiom, so **G-AX skips** (no callee property to validate against the real
callee — `reduce_C_function` is an arbitrary user callable, not pinned by the
fix).

Notes:

- **The fix is op #2.** `mincnt`-vs-count comparison flips from strict `>` to
  `>=`. The pre-patch impl (`Solution_prepatch.lean`) re-introduces
  `if (acc.length : Int) > mincnt`, which drops a cell holding exactly `mincnt`
  points. With `mincnt = 1` (the F2P scenario), a cell holding exactly one point
  is dropped pre-patch and kept post-patch — the discriminating clause.
- The comparison and the kept/dropped decision are modeled DEEPLY in exact
  `Int`/`Nat` arithmetic; SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
  changed op. No opaque `Float` order is on the proof path.
- `Option Float` refines the `float`-or-`np.nan` cell value (`some v ↔ v`,
  `none ↔ np.nan`); downstream `~np.isnan(accum)` corresponds to "`some`" cells
  being drawn, so leaving a cell `none` is exactly the "not plotted" behavior the
  issue describes.
- **G-CONF** mechanically refutes the R legs (and the A-reference op, with
  `reduceC := sum`): the Python shadow of the impl is diffed against the post-patch
  comprehension over ≥1e5 fuzzed inputs. The `conf_skip` flag is **false** (the
  impl region is not all-A: ops 1,2,4,5 are R).
