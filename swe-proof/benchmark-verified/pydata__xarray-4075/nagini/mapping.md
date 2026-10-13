# mapping.md — pydata__xarray-4075

Model ↔ repo symbol binding, type abstraction, and callee provenance (file:line
at `base_commit` 19b088636eb7d3f65ab7a1046ac672e0689371d8).

## 1. Modeled function

| model.py symbol | repo symbol | repo location (base_commit) |
|---|---|---|
| `sum_of_weights_value` | `xarray.core.weighted.Weighted._sum_of_weights` (the `self._reduce(mask, self.weights, ...)` line it computes) | `xarray/core/weighted.py:137-150` (the changed statement is line 145; the patch rewrites it as a `dtype == bool` branch at lines 142-152 post-patch) |

`_sum_of_weights` masks the data (`mask = da.notnull()`, a boolean array), then
computes `sum_of_weights = self._reduce(mask, self.weights, dim=dim,
skipna=False)`, where `_reduce` (`xarray/core/weighted.py:112-135`) is
`return dot(da, weights, dims=dim)` — the weighted reduction is the **dot
product** of the (boolean) `mask` and the `weights`. The modeled function returns
that dot-product reduction value (the quantity the changed line computes); the
unchanged downstream `where(sum_of_weights != 0.0)` masking is the identity on the
non-zero results the tested inputs produce and is outside the changed statement.

## 2. Type abstraction

| repo reality | model |
|---|---|
| `mask = da.notnull()` — a boolean `DataArray` (1 element per data point: True where the datum is present, False where NaN) | `mask: List[int]` of `0`/`1` code values (`1` = present, `0` = NaN), specification carried by `PSeq[int]` via `ToSeq` |
| `self.weights` — a `DataArray` of numeric or boolean weights | `weights: List[int]` of non-negative integer weight values (the boolean case is exactly the values `0`/`1`); `PSeq[int]` |
| `self.weights.dtype == bool` — the predicate the patch branches on | `weights_are_bool: bool` — whether the weight array's element type is boolean |
| `dot(mask, weights, dims=dim)` — the array dot product / weighted reduction `sum_i mask[i]*weights[i]` along the reduced axis | the axiom `dot_reduce(mask, weights, boolean_dot)` over the two carriers; the modeled single reduced axis is the whole sequence (the issue's MCVE reduces a 1-D array fully, `dim=...`) |
| `self.weights.astype(int)` — the cast the patch inserts before the dot | passing `boolean_dot = False` to `dot_reduce` (an int operand makes the dot numeric, never boolean) |
| result of the reduction (a scalar `DataArray`) | `int` (the scalar value) |

The data values themselves (`da`) do not enter `sum_of_weights` except through
`da.notnull()` (the `mask`); only the mask matters here, so `da` is abstracted
to its presence mask.

## 3. Callee provenance

### 3.1 `dot_reduce` — A-consumed axiom for `xarray.core.computation.dot` (the array dot product)

- **Real callee:** `dot(da, weights, dims=dim)` in `_reduce`
  (`xarray/core/weighted.py:135`), i.e. `xarray.core.computation.dot`
  (`xarray/core/computation.py`), which dispatches to
  `numpy.einsum`/`tensordot`-style contraction. The reduction value is
  `sum over the reduced axis of (mask * weights)`.
- **Unchanged:** the patch does NOT change `dot`/`_reduce`; it changes only the
  *dtype of the operand* handed to the unchanged dot (a `bool`→`int` cast).
- **Encoded property (the weakest the proof needs), keyed on the operand dtype:**
  - `boolean_dot == False` (at least one numeric operand — the gold path always,
    after the cast): the dot is computed in **integer/numeric arithmetic**,
    `Result() == int_dot(mask, weights) == sum_i mask[i]*weights[i]`.
  - `boolean_dot == True` (BOTH operands boolean — the pre-patch path when
    `weights` is boolean, since `mask = da.notnull()` is always boolean): the dot
    is computed in **boolean arithmetic** and SATURATES,
    `Result() == bool_dot(mask, weights) == (1 if exists i: mask[i]==1 and
    weights[i]==1 else 0)`. This is the bug:
    `xr.dot([True,True],[True,True]) -> True` (1), not `2`.
- **Flag dependency:** the boolean-vs-numeric dispatch is a property of NumPy's
  reduction over `bool` arrays (logical contraction), inherited by `xr.dot`. The
  axiom is sound for the default `dot`/`einsum` configuration xarray uses. (G-AX
  fuzzes `np.dot`/`xr.dot` over bool and int operands.)
- **Deep models `int_dot`/`bool_dot`** (model.py `pure` region) are validated
  `== the real dot` by axiom_check.py / G-AX (A-reference): they spell out the
  two contraction semantics as front-recursive folds.

## 4. The change site and the discriminator

Gold hunk (`xarray/core/weighted.py`, the `_sum_of_weights` body):
```
- sum_of_weights = self._reduce(mask, self.weights, dim=dim, skipna=False)
+ # bool -> int, because ``xr.dot([True, True], [True, True])`` -> True
+ # (and not 2); GH4074
+ if self.weights.dtype == bool:
+     sum_of_weights = self._reduce(
+         mask, self.weights.astype(int), dim=dim, skipna=False
+     )
+ else:
+     sum_of_weights = self._reduce(mask, self.weights, dim=dim, skipna=False)
```

## 5. Conformance (G-CONF)

`conformance_check.py` runs the contract-stripped impl region (shadow, with
`dot_reduce` delegated to the real unchanged `xr.dot`) against the real
patched `Weighted._sum_of_weights` (oracle) over the section-2 bridge:
`mask` lifts to a data array that is missing exactly where the flag is 0 (so
`da.notnull()` reproduces it), `weights` to a bool- or int-typed array per
`weights_are_bool`, and a missing (zero-total, downstream-masked) oracle
result reads back as the reduction value 0. >= 1e5 inputs (boundary +
100000 fuzz). **Pinned fuzz seed: 4075** (the instance number).

The discriminator is the **operand dtype passed to the unchanged `dot`**: when
`weights` is boolean, the gold casts it to `int` so the dot is numeric
(`int_dot`, the true count); the pre-patch hands the boolean array straight to
`dot`, whose boolean contraction saturates (`bool_dot`, 0/1). The modeled
function returns the dot value; its postcondition pins it to `int_dot` (the true
weighted count). `model_prepatch.py` reproduces the pre-patch (passes
`boolean_dot = weights_are_bool`, no cast) and FAILS that postcondition on a
boolean-weights input whose true count is `>= 2` (`bool_dot == 1 != int_dot`).
