# refinement.md — sympy__sympy-23262

Maps every operation in `implementation_renderArg` to its `patch.diff`
counterpart in `_recursive_to_string`. Tags: **R** type refinement, **A-consumed**
proof-consumed axiom, **A-reference** deep-modeled callee (G-AX validated), **I**
identical concrete op.

| # | Lean impl op | patch.diff / source op | tag | note |
|---|---|---|---|---|
| 1 | `Arg` carrier (`leaf`/`list`/`tuple`) | the runtime arg object passed to `_recursive_to_string` (leaf vs python `list` vs python `tuple`) | R | bijection in mapping.md. `iterable`+`isinstance` dispatch ↔ the inductive constructor. |
| 2 | `.leaf s => s` | the `isinstance(arg,(Basic,MatrixOperations))→doprint(arg)`, `isinstance(arg,str)→arg`, and final `else→doprint(arg)` leaf branches | R | every leaf path produces the printed string; we refine the leaf to that string `s`. `doprint` is refined away (not called) — fix does not touch leaf rendering. |
| 3 | `.list xs` → `xs.map implementation_renderArg` | `', '.join(_recursive_to_string(doprint, e) for e in arg)` under the `isinstance(arg,list)` branch | I | recursive render of each element; `String.intercalate ", "` ↔ `', '.join`. |
| 4 | list wrap `"[" ++ … ++ "]"` | `left, right = "[", "]"; return left + … + right` | I | unchanged by the fix (list branch already correct pre-patch). |
| 5 | `.tuple xs` → `xs.map implementation_renderArg` | `', '.join(_recursive_to_string(doprint, e) for e in arg)` under the `isinstance(arg,tuple)` branch | I | same join as list. |
| 6 | tuple wrap `"(" ++ … ++ ",)"` | `left, right = "(", ",)"; return left + … + right` | I | **THE FIX.** trailing comma before `)`. Pre-patch impl uses `")"` (= buggy `left,right="()"`). |

No changed op is inexpressible; the whole function is modeled deeply and
concretely. No callee is consumed as an axiom and none is deep-model-referenced
(`doprint` is refined away per row 2). axiom_check.py is therefore a skip stub.

The R/I legs (all rows) are mechanically refuted by G-CONF, which builds the
Python shadow of `implementation_renderArg` and differential-tests it against the
patched `_recursive_to_string` over fuzzed nested trees.
