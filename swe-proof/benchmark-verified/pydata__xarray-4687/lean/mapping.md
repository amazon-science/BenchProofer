# mapping.md — pydata__xarray-4687

## Symbol binding (file:line @ base_commit d3b6aa6d8b)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_condSelect` / `problem_spec_condSelect` / `correct_condSelect` | the top-level elementwise conditional-selection function that chooses between two operands per a boolean condition and (post-patch) accepts a 3-valued attribute-retention flag | `xarray/core/computation.py:1730` (`where(cond, x, y, keep_attrs=None)`) @ base_commit |
| `getKeepAttrsDefault` | the ambient default attribute-retention policy consulted when the caller passes no flag | `xarray/core/options.py:107` (`_get_keep_attrs(default=False)`) @ base_commit |
| `selVals` | the elementwise value selection performed downstream (`duck_array_ops.where(cond, x, y)` dispatched through `apply_ufunc`) | `xarray/core/duck_array_ops.py` (`where`) — modeled deeply, not axiomatized |
| `keptAttrs` / attribute propagation | the `keep_attrs=lambda attrs, context: attrs[1]` policy threaded into `apply_ufunc` when `keep_attrs is True` | `xarray/core/computation.py:1813-1830` (the added block) |

The modeled function is `where`. The gold patch adds a `keep_attrs` keyword and
threads it to `apply_ufunc`:

```python
def where(cond, x, y, keep_attrs=None):
    ...
    if keep_attrs is None:
        keep_attrs = _get_keep_attrs(default=False)
    if keep_attrs is True:
        # keep the attributes of x (the 2nd positional input to the ufunc)
        keep_attrs = lambda attrs, context: attrs[1]
    return apply_ufunc(duck_array_ops.where, cond, x, y,
                       join="exact", dataset_join="exact", dask="allowed",
                       keep_attrs=keep_attrs)
```

- PRE-PATCH `where` takes only `(cond, x, y)` and never passes `keep_attrs` to
  `apply_ufunc`; `apply_ufunc`'s default drops all attributes. Hence the result
  always loses metadata — the reported bug.
- POST-PATCH a `keep_attrs` flag is accepted. `None` ⇒ ambient
  `OPTIONS["keep_attrs"]` default (`_get_keep_attrs(default=False)`, normally
  `False`). `True` ⇒ a combiner that selects `attrs[1]` — the attrs of the 2nd
  ufunc operand, which is `x` (the value chosen where `cond` is true). Any other
  value ⇒ no retention (for the boolean observable: attributes dropped).

The two issues describe the same defect (`xr.where` dropping attributes); the
single F2P test `test_where_attrs` exercises `keep_attrs=True` and asserts the
result keeps `x`'s attrs.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| a 1-D `DataArray` of ints with `.attrs` dict | `DataArr` (`values : List Int`, `attrs : List (String × String)`) | array data ↦ `values` (row-major over the single dim); the `.attrs` ordered mapping ↦ association list of `(key, value)` string pairs |
| `cond : DataArray[bool]` (1-D, aligned) | `cond : List Bool` | elementwise boolean mask, same length/order |
| `keep_attrs` argument | `keepAttrs : Option Bool` | `None ↦ none`; `True ↦ some true`; `False ↦ some false`. (`str`/`callable` values are out of scope: F2P + issue exercise only the bool/None API; recorded as a flag restriction below.) |
| result `DataArray.values` | `result.values` | elementwise `np.where(cond, x, y)` ↦ `selVals cond x.values y.values` |
| result `DataArray.attrs` | `result.attrs` | `x.attrs` when retention in effect, else `{}` ↦ `[]` |
| `_get_keep_attrs(default=False)` | `getKeepAttrsDefault : Bool` | ambient `OPTIONS["keep_attrs"]` resolved against default `False`; `"default"`/`False ↦ false`, `True ↦ true` |

## Callee provenance + flag dependencies

- `getKeepAttrsDefault` (`opaque`) ↔ `_get_keep_attrs(default=False)`: an
  UNCHANGED callee the fix calls but does not modify. It is consulted ONLY on the
  `keepAttrs = none` branch. No `_prop` axiom about it is consumed by the proof
  (the spec's `keptAttrs` invokes it identically), so it is an **A-reference**
  (its value-relation is exercised by G-CONF), not a consumed axiom. G-AX is a
  skip stub.
- `selVals` ↔ `duck_array_ops.where`: the elementwise selection is UNCHANGED by
  the patch (only attribute handling changed). Modeled deeply as a zip/map; an
  A-reference validated by G-CONF against real `xr.where` values.
- Flag dependency: attribute retention happens **iff** the resolved
  `keep_attrs is True`. With the default options (`keep_attrs="default"` ⇒
  `False`), `keep_attrs=None` and `keep_attrs=False` both drop attributes; only
  `keep_attrs=True` retains. G-CONF fuzzes `None`, `True`, `False` under the
  default option state and asserts the value+attrs observable.

## G-CONF fuzz seed

`SEED = 20240626` (pinned in `conformance_check.py`).
