# mapping.md — sympy__sympy-15017

## Symbol binding (file:line @ base_commit 6810dee426943c1a2fe85b5002dd0d4cf2246a05)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_arraySize` / `problem_spec_arraySize` / `correct_arraySize` | computation of the element count of an N-dimensional dense array from its shape, inside `ImmutableDenseNDimArray._new` | `sympy/tensor/array/dense_ndim_array.py:152` |

The modeled computation is the single statement that derives the array's element
count (the value subsequently returned by `__len__`) from the array's `shape`
tuple. At `base_commit` it reads

```python
self._loop_size = functools.reduce(lambda x,y: x*y, shape) if shape else 0
```

and the gold patch changes it to

```python
self._loop_size = functools.reduce(lambda x,y: x*y, shape, 1)
```

`shape` is a tuple of non-negative integer dimension sizes (each `_sympify`d to a
SymPy `Integer`). The element count is the product of these dimensions; the
patched form uses an explicit fold seed of `1`, so the **empty product** of a
rank-0 array (`shape == ()`, a scalar) is `1` rather than `0`.

### Consumer of the modeled value (why the F2P test observes it)

`NDimArray.__len__` (`sympy/tensor/array/ndim_array.py:178`) returns `self._loop_size`
verbatim. Hence `len(arr)` equals the modeled element count. The F2P test
`test_ndim_array_initiation` asserts:

- `len(ImmutableDenseNDimArray([], shape=(0,))) == 0` — shape `(0,)`, product `0`.
- `len(ImmutableDenseNDimArray(x)) == 1` for a scalar `x` — shape `()`, product `1`
  (the rank-0 case; `0` at `base_commit`, `1` after the fix).
- `len(arr_with_one_element) == 1`, etc. — non-empty shapes, product unchanged.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `shape` — tuple of non-negative integer dimension sizes | `shape : List Nat` | the tuple of dimensions in order ↦ a `List Nat` of the same values |
| the computed element count (`self._loop_size`, returned by `len(arr)`) | `result : Nat` | identity (a non-negative Python int ↦ a `Nat`) |
| `functools.reduce(lambda x,y: x*y, shape, 1)` | `shape.prod` (fold of multiplication with seed `1`) | the fold of `*` over the dimensions with identity seed `1`; empty product `= 1` |

## Callee provenance + flag dependencies

- **No callee axiom is consumed.** The only operation involved is integer
  multiplication folded over the dimension list, which is modeled DEEPLY
  (`List.prod` / a `for`-loop accumulator seeded at `1`). There is no unchanged
  repo callee whose contract the proof must assume — the integers are the inputs.
- No flag dependency: the computation runs unconditionally in `_new` for every
  constructed dense array.
- `shape` always contains non-negative integers at this point: it has already
  passed `_handle_ndarray_creation_inputs`, which raises `TypeError` unless every
  dimension is an integer, and dimension sizes are sizes (≥ 0). Modeling as
  `List Nat` is faithful.

## G-CONF fuzz seed

`SEED = 20240627` (pinned in `conformance_check.py`).
