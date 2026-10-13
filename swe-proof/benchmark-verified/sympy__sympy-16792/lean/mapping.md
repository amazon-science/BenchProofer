# mapping.md — sympy__sympy-16792

## Symbol binding (file:line @ base_commit 09786a173e)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_arrayArgBounds` / `problem_spec_arrayArgBounds` / `correct_arrayArgBounds` | the index-bound metadata chosen for a *redundant* argument in `CodeGen.routine` (the `argument_sequence` `KeyError` branch) | `sympy/utilities/codegen.py:741-748` @ base_commit |
| `boundsOf shape` | `dimensions(s) = [(S.Zero, dim - 1) for dim in s.shape]` | gold patch helper, `codegen.py:698-700` (post-patch); pre-patch: bound metadata simply absent on this path |

The modeled function is `CodeGen.routine`. The behavior the fix changes lives in
the redundant-argument reconstruction loop that runs only when the caller pins
`argument_sequence`:

```python
for symbol in argument_sequence:
    try:
        new_args.append(name_arg_dict[symbol])
    except KeyError:
        # PRE-PATCH:  new_args.append(InputArgument(symbol))            # no dimensions
        # POST-PATCH: dimensions metadata iff symbol is array-like
        if isinstance(symbol, (IndexedBase, MatrixSymbol)):
            metadata = {'dimensions': dimensions(symbol)}
        else:
            metadata = {}
        new_args.append(InputArgument(symbol, **metadata))
```

`InputArgument(symbol, **metadata)` stores `metadata['dimensions']` in
`Variable.dimensions` (`codegen.py:330`). That attribute is exactly the
observable: when set, the C/Fortran printer emits the argument as a
pointer/array (`double *x`); when `None`/absent, as a scalar (`double x`).

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `symbol` is `MatrixSymbol`/`IndexedBase` (array-like) vs a plain `Symbol` | `isArrayLike : Bool` | `isinstance(symbol, (IndexedBase, MatrixSymbol))` ↦ `true`; otherwise `false` |
| `symbol.shape` = tuple of dimension sizes | `shape : List Int` | `tuple(int(d) for d in symbol.shape)` ↦ `shape`; a scalar has no shape (the branch never reads it → `shape` irrelevant when `isArrayLike = false`) |
| `metadata.get('dimensions')` stored as `InputArgument.dimensions` (`None` ⇒ scalar) | `result : List (Int × Int)` | `None` ↦ `[]`; `[(S.Zero, d-1), …]` ↦ `[(0, d-1), …]` via `int()` on each bound |
| `(S.Zero, dim - 1)` | `((0 : Int), d - 1)` | `S.Zero` ↦ `0`; `dim - 1` ↦ `d - 1` |

## Callee provenance + flag dependencies

- No callee axiom is consumed. `dimensions(s)` is the operation the patch
  introduces, so it is modeled DEEPLY as `boundsOf` (an A-reference validated by
  G-CONF against the real per-dimension bound list), never axiomatized (§0.7).
- Flag dependency: the branch is reached only when the caller supplies
  `argument_sequence` AND the symbol is redundant (does not occur in `expr`, so
  it is absent from `name_arg_dict`). G-CONF fuzzes exactly this configuration
  (constant `expr`, the symbol supplied only via `argument_sequence`).
- `IndexedBase` is named in the `isinstance` guard but, on the
  `argument_sequence` path, an `IndexedBase` arg is first replaced by its
  `.label` (a plain `Symbol`) in the `new_sequence` loop (`codegen.py:728-734`),
  so by the time it reaches the `KeyError` branch it is no longer an
  `IndexedBase` and is treated as a scalar. The observable array-like case on
  this path is therefore `MatrixSymbol`; G-CONF fuzzes `MatrixSymbol`
  (array-like ⇒ bounds) and plain `Symbol` (scalar ⇒ none), matching the F2P
  test `test_ccode_unused_array_arg` (a `MatrixSymbol('x', 2, 1)`).

## G-CONF fuzz seed

`SEED = 20240625` (pinned in `conformance_check.py`).
