# mapping.md — pydata__xarray-4075

## Modeled function

| Lean | Python | file:line @ base_commit `19b088636e` |
|---|---|---|
| `implementation_sumOfWeights` / `problem_spec_sumOfWeights` / `correct_sumOfWeights` | `Weighted._sum_of_weights(self, da, dim)` — aggregate weight over the not-null entries | `xarray/core/weighted.py:137-150` (post-patch: boolean weights are reduced in integer arithmetic) |

The modeled domain is the boolean-weights case the issue is about: a 1-D
`DataArray` of data, boolean `weights`, full reduction (`dim=None`). `mask =
da.notnull()` is the boolean not-null mask; the function returns the sum of the
weights at the kept positions, with a total of `0` reported as missing (the
`.where(sum != 0)` step turns a zero aggregate into NaN).

## Type bijection (Lean ↔ Python) — used by G-CONF + G-AX

| Python | Lean | notes |
|---|---|---|
| `mask = da.notnull()` (bool array, 1-D) | `mask : List Bool` | one flag per data entry; `True` = entry retained |
| `self.weights` (bool array, 1-D) | `weights : List Bool` | boolean weights, aligned position-wise with `mask` |
| the array contraction `dot(mask, weights_int)` over the reduced dim | `zipDot : List (Bool × Bool) → Int` | integer multiply-and-accumulate: each aligned pair contributes `1` iff both flags set, summed in order |
| `sum_of_weights.where(sum_of_weights != 0.0)` | `Option Int` | scalar result; `0`-total ↦ `none` (NaN), positive total ↦ `some` |

Precondition `mask.length = weights.length` (binder of `correct_sumOfWeights`)
mirrors that `notnull()` has the same shape as `weights` after alignment; the
modeled case is the equal-length 1-D contraction the F2P tests exercise.

## Callee provenance / flag deps

- **Unchanged callee — `_reduce` / `xr.dot` (A-reference).** The aggregation is
  performed by the array contraction routine `_reduce(mask, weights, …)`, which
  delegates to `xarray.core.computation.dot` (`weighted.py:135`). This callee is
  **not changed** by the patch. It is modeled DEEPLY as `zipDot` (an integer
  multiply-and-accumulate) — an A-reference, validated `== ` the real callee by
  G-AX (axiom_check.py runs the real `xr.dot` on the integer-cast inputs).
- **Changed op — the `bool → int` cast (R, deeply modeled).** The fix is: when
  the weights are of boolean dtype, cast them to integer before the contraction
  (`self.weights.astype(int)`). Boolean `xr.dot` uses boolean algebra (`*` = AND,
  `sum` = OR), so it saturates at `True` (= 1); the integer contraction returns
  the true count. This changed op is modeled deeply (the `if m && w then acc+1`
  accumulation in integer arithmetic), NOT axiomatized. **Flag dependency:** the
  cast fires only on `weights.dtype == bool`; the modeled domain fixes that
  configuration (weights are `List Bool`), and G-AX exercises `xr.dot` in exactly
  that integer-cast configuration.
- The `.where(sum_of_weights != 0.0)` masking is an identical concrete op (I),
  modeled as the `if acc = 0 then none` branch.

## G-CONF fuzz seed

`conf_seed = 4075` (pinned; see conformance_check.py / axiom_check.py and meta.json).
