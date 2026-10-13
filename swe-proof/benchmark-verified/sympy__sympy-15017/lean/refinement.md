# refinement.md — sympy__sympy-15017

Operation correspondence between `implementation_arraySize` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

No axioms are declared or consumed. The only operation is integer
multiplication folded over the dimension list, modeled DEEPLY (a `for`-loop
multiply accumulator seeded at `1`, i.e. `List.prod`). Every row is **R** or
**I**. The R/I legs are differential-tested by G-CONF; G-AX is a skip stub (no
consumed callee axiom).

## `implementation_arraySize` ↔ the changed element-count statement

The gold patch changes

```python
self._loop_size = functools.reduce(lambda x,y: x*y, shape) if shape else 0
```

to

```python
self._loop_size = functools.reduce(lambda x,y: x*y, shape, 1)
```

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| input `shape : List Nat` | `shape` (tuple of integer dimension sizes) | R | tuple of non-negative ints ↦ `List Nat`, same values in order |
| `let mut acc := 1` | the explicit `reduce` initializer `1` | I | the fold seed; this is the one byte the patch adds — empty product `= 1` |
| `for d in shape do acc := acc * d` | `functools.reduce(lambda x,y: x*y, shape, 1)` | I | left fold of `*` over the dimensions, starting from the seed |
| `return acc` | `self._loop_size = …` | R | the resulting count; the value `__len__` returns ↦ `result : Nat` |

The result is the element count `len(arr)` returns; it is the observable
asserted by the F2P test `test_ndim_array_initiation` (`len(Array(x)) == 1` for a
scalar `x`; `len(Array([], shape=(0,))) == 0`).

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the buggy skeleton folds `*` over the dimensions but
  special-cases the *empty* shape to `0` (`reduce(mul, shape) if shape else 0`)
  instead of the empty product `1`. So a rank-0 (scalar) array reports `0`
  elements rather than `1`. The carried correctness proof cannot close because
  at `shape = []` the buggy impl yields `0` while `problem_spec_arraySize`
  requires `shape.prod = 1`. (FAIL_TO_PASS: `test_ndim_array_initiation`, the
  `len(rank_zero_array) == 1` assertion.)
