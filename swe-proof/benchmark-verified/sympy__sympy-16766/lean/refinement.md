# refinement.md — sympy__sympy-16766

Operation correspondence between `implementation_indexedCode` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

No axioms are declared or consumed. The only changed operation is the string
assembly, modeled DEEPLY (literal concatenation + comma-join). The two callees
the new method invokes (`str(base)`, `self._print(ind)`) are UNCHANGED by the
patch; their outputs enter the model as the inputs `base` / `subscripts`, so no
callee contract is needed. Every row is **R** or **I**. The R/I legs are
differential-tested by G-CONF; G-AX is a skip stub (no consumed callee axiom).

## `implementation_indexedCode` ↔ the new `_print_Indexed` method

The gold patch adds

```python
def _print_Indexed(self, expr):
    base = expr.args[0]
    index = expr.args[1:]
    return "{}[{}]".format(str(base), ", ".join([self._print(ind) for ind in index]))
```

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| input `base : String` | `str(expr.args[0])` | R | the printed array name; `str(base_obj)` ↦ `base` (unchanged callee result modeled as input) |
| input `subscripts : List String` | `[self._print(ind) for ind in expr.args[1:]]` | R | each index rendered by the unchanged recursive printer; the list of result strings ↦ `subscripts` |
| `let joined := String.intercalate ", " subscripts` | `", ".join([...])` | I | comma-space join of the rendered subscripts |
| `return base ++ "[" ++ joined ++ "]"` | `"{}[{}]".format(str(base), ...)` | I | format string `"{}[{}]"` ↦ `base ++ "[" ++ joined ++ "]"`; the literal `[` / `]` are identical bytes |

The result is the exact source string the method returns; it is the observable
asserted by the F2P test `test_PythonCodePrinter`
(`prntr.doprint(p[0, 1]) == 'p[0, 1]'`).

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: with no `_print_Indexed` method, an `Indexed`
  expression dispatches to the generic `_print_not_supported` path, which adds
  the expression to `_not_supported` and emits a placeholder marker instead of
  the bracketed subscript form. The buggy skeleton therefore returns a fixed
  marker independent of `base`/`subscripts`; the carried gold proof (`rfl`)
  fails to close (`pure "# Not supported" ≠ base ++ "[" ++ … ++ "]"`).
  (FAIL_TO_PASS: `test_PythonCodePrinter`.)
