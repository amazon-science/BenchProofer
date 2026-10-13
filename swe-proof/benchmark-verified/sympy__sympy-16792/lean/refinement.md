# refinement.md — sympy__sympy-16792

Operation correspondence between `implementation_arrayArgBounds` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

No axioms are declared or consumed: the changed operation (`dimensions(s)`) is
modeled DEEPLY as `boundsOf`. Every row is **R**, **A-reference**, or **I**. The
R/I/A-reference legs are differential-tested by G-CONF; G-AX is a skip stub (no
consumed callee axiom).

## `implementation_arrayArgBounds` ↔ the `argument_sequence` `KeyError` branch

The gold patch turns

```python
except KeyError:
    new_args.append(InputArgument(symbol))
```

into

```python
except KeyError:
    if isinstance(symbol, (IndexedBase, MatrixSymbol)):
        metadata = {'dimensions': dimensions(symbol)}
    else:
        metadata = {}
    new_args.append(InputArgument(symbol, **metadata))
```

where `dimensions(s) = [(S.Zero, dim - 1) for dim in s.shape]` (the first hunk
merely extracts this list-comprehension into a named helper — a behavior-neutral
refactor of the SAME computation already present at `codegen.py:709-712`; not an
independently-observable behavior).

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `let mut metadata : List (Int × Int) := []` | `metadata = {}` (the no-dimensions default) | I | accumulator init; scalar/no-bound case |
| condition `if isArrayLike` | `if isinstance(symbol, (IndexedBase, MatrixSymbol))` | R | `isinstance(symbol, (IndexedBase, MatrixSymbol))` ↦ `isArrayLike : Bool` (see mapping.md: on this path the array-like case is `MatrixSymbol`). Boolean bijection. |
| `metadata := boundsOf shape` (then-branch) | `metadata = {'dimensions': dimensions(symbol)}` | A-reference | `dimensions(symbol) = [(S.Zero, dim-1) for dim in symbol.shape]` modeled deeply by `boundsOf shape = shape.map (fun d => (0, d-1))`; validated == real `dimensions` by G-CONF. The `'dimensions'` dict key is the observable `InputArgument.dimensions` carrier. |
| `metadata := []` (else-branch) | `metadata = {}` | R | empty dimension metadata (`None`/absent on `InputArgument`) ↦ `[]` |
| `return metadata` | `InputArgument(symbol, **metadata).dimensions` | R | the stored `dimensions` attribute ↦ `List (Int × Int)` |

The result is the precise observable: `InputArgument.dimensions` (`codegen.py:330`)
non-empty ⇒ the printer emits the argument as a pointer/array (`double *x`),
empty/`None` ⇒ as a scalar (`double x`). The F2P test
`test_ccode_unused_array_arg` asserts `double *x` in the generated source for an
unused `MatrixSymbol` argument.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the redundant-argument path always attaches empty
  bound metadata (`metadata := []` unconditionally — the pre-patch
  `InputArgument(symbol)` with no `dimensions`), so an array-valued argument is
  emitted as a scalar. The carried gold proof of `correct_arrayArgBounds` fails
  to close on the `isArrayLike = true` case (`pure [] = boundsOf shape`).
  (FAIL_TO_PASS: `test_ccode_unused_array_arg`.)
