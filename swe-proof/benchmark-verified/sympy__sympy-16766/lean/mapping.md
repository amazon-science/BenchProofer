# mapping.md — sympy__sympy-16766

## Symbol binding (file:line @ base_commit b8fe457a02)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_indexedCode` / `problem_spec_indexedCode` / `correct_indexedCode` | `PythonCodePrinter._print_Indexed(self, expr)` — the renderer for an array element access | `sympy/printing/pycode.py:360-363` (post-patch); pre-patch: no `_print_Indexed` method, so an `Indexed` falls through to `_print_not_supported` (`sympy/printing/codeprinter.py:490-491`) |

The modeled function is the new `_print_Indexed` printer method. Its body is

```python
def _print_Indexed(self, expr):
    base = expr.args[0]
    index = expr.args[1:]
    return "{}[{}]".format(str(base), ", ".join([self._print(ind) for ind in index]))
```

`expr.args[0]` is the `IndexedBase` (its `str()` is the array name); `expr.args[1:]`
are the index expressions, each rendered recursively by `self._print`. The output
is the array name, then the rendered subscripts joined by `", "`, wrapped in one
pair of square brackets.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `str(expr.args[0])` — the printed base name | `base : String` | `str(base_obj)` ↦ `base` |
| `[self._print(ind) for ind in expr.args[1:]]` — the list of already-rendered subscript strings | `subscripts : List String` | each `self._print(ind)` string ↦ one `String` element, in order |
| the returned source string | `result : String` | identity (Python `str` ↦ Lean `String`) |
| `", ".join([...])` | `String.intercalate ", " subscripts` | comma-space join of the subscript strings |
| `"{}[{}]".format(b, j)` | `base ++ "[" ++ j ++ "]"` | literal-bracket concatenation |

The recursive sub-renderings (`str(base)` and `self._print(ind)`) are taken as
INPUTS — the strings the ambient printer already produces for the base and each
index. The fix introduces no new behavior in those callees; it only assembles
their outputs. So they are modeled as inputs, not axiomatized callees.

## Callee provenance + flag dependencies

- No callee axiom is consumed. The two callees the new method invokes
  (`str(...)` and `self._print(...)`) are UNCHANGED by the patch and their
  results enter the model as the inputs `base` / `subscripts`. The only changed
  operation is the string assembly itself, which is modeled DEEPLY (literal
  concatenation + `String.intercalate`).
- No flag dependency: `_print_Indexed` is dispatched unconditionally for any
  `Indexed` expression on `PythonCodePrinter` (and its subclasses NumPy/SciPy/
  Mpmath, which inherit it).
- F2P anchor: `test_PythonCodePrinter` asserts
  `prntr.doprint(p[0, 1]) == 'p[0, 1]'` for `p = IndexedBase("p")` — base `"p"`,
  subscripts `["0", "1"]`, result `"p[0, 1]"`.

## G-CONF fuzz seed

`SEED = 20240626` (pinned in `conformance_check.py`).
