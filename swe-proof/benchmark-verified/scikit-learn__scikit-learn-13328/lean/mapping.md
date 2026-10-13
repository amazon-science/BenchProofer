# mapping.md — scikit-learn__scikit-learn-13328

## Instance
- repo: `scikit-learn/scikit-learn`
- base_commit: `37b0e66c871e8fb032a9c7086b2a1d5419838154`
- modeled file: `sklearn/linear_model/huber.py` (the changed call site), whose
  observable dtype effect is produced by the unchanged validation callee in
  `sklearn/utils/validation.py`.
- F2P test: `sklearn/linear_model/tests/test_huber.py::test_huber_bool`
- pinned G-CONF fuzz seed: **13328** (G-CONF is a skip stub — see below)

## What the fix does (issue + gold patch)
A regressor's `fit` validates its input feature matrix `X` before numerical
processing. Pre-patch it requested the generic dtype `"numeric"`; for a boolean
input array `"numeric"` performs **no conversion** (the array keeps its boolean
element type), and the downstream numerical kernel then applies unary negation
`-X`, which numpy rejects for a boolean array → `TypeError`. The gold patch
changes the requested dtype to the explicit accepted set `[np.float64,
np.float32]`, so any input whose element type is not already one of those is
converted to `np.float64`.

```python
# huber.py:251-254  (HuberRegressor.fit)
X, y = check_X_y(
    X, y, copy=False, accept_sparse=['csr'], y_numeric=True)            # PRE
X, y = check_X_y(
    X, y, copy=False, accept_sparse=['csr'], y_numeric=True,
    dtype=[np.float64, np.float32])                                     # POST
```

### Where the observable behavior lives (the deep-modeled callee)
`check_X_y` forwards `X` and `dtype` to `check_array`
(`sklearn/utils/validation.py`). The dtype-resolution branch
(`validation.py:439-466`) decides the array's final element type:

```python
dtype_numeric = isinstance(dtype, str) and dtype == "numeric"   # 439
dtype_orig = getattr(array, "dtype", None) ...                  # 441
if dtype_numeric:                                               # 452
    if dtype_orig is not None and dtype_orig.kind == "O":       #   object -> float64
        dtype = np.float64
    else:
        dtype = None                                            #   else: keep (NO conversion)
if isinstance(dtype, (list, tuple)):                            # 459  (the POST case)
    if dtype_orig is not None and dtype_orig in dtype:          #   orig already accepted
        dtype = None                                            #   keep (no conversion)
    else:
        dtype = dtype[0]                                        #   convert to first accepted = float64
...
array = np.asarray(array, dtype=dtype, order=order)             # 496  (dtype=None -> keep orig)
```

So the resolved final element type, as a function of the original element type
`orig` and the requested spec:

| requested spec | orig ∈ {float64, float32} | orig = object | orig = bool / int / other |
|---|---|---|---|
| `"numeric"` (PRE)            | keep `orig`  | → float64 | **keep `orig`** (the bug: bool stays bool) |
| `[float64, float32]` (POST) | keep `orig`  | → float64 | **→ float64** (converted; the fix)        |

The discriminating input is a **boolean** `X`: POST yields a floating element
type (so `-X` is well-defined downstream); PRE leaves it boolean (crash).

## Symbol binding
| Lean symbol | Python | provenance (file:line @ base) |
|---|---|---|
| `implementation_prepareInput` | the dtype effect of `check_X_y(..., dtype=[float64,float32])` on `X` in `HuberRegressor.fit` | huber.py:251-254 |
| deep model of the list-dtype branch | `check_array` dtype resolution | validation.py:439-466, 496 |
| `NpKind` | numpy array element dtype (`array.dtype`) | — |
| `NpKind.float64`/`float32`/`bool`/`int64`/`object` | `np.float64`/`np.float32`/`np.bool_`/`np.int64`/`object` | — |
| accepted set `[float64, float32]` | the gold `dtype=[np.float64, np.float32]` argument | huber.py:253 (post) |

## Lean ↔ Python type bijection (used by G-AX)
- A numpy array's `array.dtype` is modeled by `NpKind`. The bijection covers the
  representative element types reached by `fit`'s public input contract:
  `np.bool_ ↔ NpKind.bool`, `np.int64 ↔ NpKind.int64`, `np.float32 ↔
  NpKind.float32`, `np.float64 ↔ NpKind.float64`, `object ↔ NpKind.object`.
  (Any other non-floating, non-object numeric kind — `int8/16/32`, `float16`,
  `uint*` — resolves identically to `int64` under `[float64,float32]`: it is not
  in the accepted set, hence → `float64`. The model's `else → float64` branch is
  faithful to all of them; the enumerated kinds are the representatives G-AX
  drives.)
- The result `NpKind` is the modeled array's final `array.dtype` after
  `check_array` returns.

## Callee provenance + flag deps
- Deep-modeled callee: `check_array` dtype resolution (**A-reference**), validated
  by `axiom_check.py` (G-AX) which drives the REAL `check_X_y`/`check_array` with
  `dtype=[np.float64, np.float32]` over inputs of each `NpKind` and asserts the
  returned `array.dtype` matches `implementation_prepareInput`.
- Flag dependency: the resolution branch taken depends only on whether the
  requested dtype is the string `"numeric"` vs a list/tuple. The fix selects the
  list form; the model is the list-form resolution. The `dtype_numeric` /
  flexible / object-coercion sub-branches (validation.py:524, 535) do **not** fire
  for a list dtype, so they are correctly absent from the model.

## G-CONF fuzz seed
Seed **13328**. G-CONF is a **skip stub** (`conf_skip=true`): the impl's
substantive operation is the deep model of the unchanged `check_array` callee
(A-reference), which is validated by G-AX against the real callee; there is no
independent R/I arithmetic leg to differential-test.
