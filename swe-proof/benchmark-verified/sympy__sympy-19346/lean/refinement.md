# refinement.md — sympy__sympy-19346

Operation-by-operation correspondence between the Lean impls (Solution.lean, impl
regions) and the gold `patch.diff` (the two new printer methods in
`sympy/printing/repr.py`). Tags: **R** type refinement, **A-consumed** proof uses
an axiom, **A-reference** deep model validated == real callee by G-AX/G-CONF,
**I** identical concrete op. Every step is R, A, or I.

## Modeled function 1 — mapping (`_print_dict`)
Gold (post-patch):
```python
def _print_dict(self, expr):
    sep = ", "
    dict_kvs = ["%s: %s" % (self.doprint(key), self.doprint(value))
                for key, value in expr.items()]
    return "{%s}" % sep.join(dict_kvs)
```

| # | Lean impl op (`implementation_dictRepr`) | patch.diff counterpart | tag | note |
|---|---|---|---|---|
| 1 | input `entries : List (SymExpr × SymExpr)` | `expr.items()` (the dict, in iteration order) | **R** | dict ↔ ordered list of key/value pairs; bijection in mapping.md. |
| 2 | `let sep := ", "` | `sep = ", "` | **I** | identical separator literal. |
| 3 | `let mut parts : List String := []` | the list comprehension accumulator `dict_kvs` | **I** | accumulator for per-entry renderings. |
| 4 | `for p in entries do parts := parts ++ [elemRepr p.1 ++ ": " ++ elemRepr p.2]` | `["%s: %s" % (self.doprint(key), self.doprint(value)) for key, value in expr.items()]` | **A-reference** | each entry rendered as `doprint(key) ": " doprint(value)`; `elemRepr` models `self.doprint`/`srepr` on a sub-value (the canonical recursive renderer). Opaque carrier, no axiom; validated end-to-end by G-CONF against the real `srepr`. |
| 5 | `return "{" ++ String.intercalate sep parts ++ "}"` | `return "{%s}" % sep.join(dict_kvs)` | **I** | join by `sep`, wrap in braces. |

## Modeled function 2 — unordered collection (`_print_set`)
Gold (post-patch):
```python
def _print_set(self, expr):
    if not expr:
        return "set()"
    return "{%s}" % self.reprify(expr, ", ")
```

| # | Lean impl op (`implementation_setRepr`) | patch.diff counterpart | tag | note |
|---|---|---|---|---|
| 1 | input `elems : List SymExpr` | `expr` (the set, in iteration order) | **R** | set ↔ list of elements; bijection in mapping.md. |
| 2 | `if elems.isEmpty then return "set()"` | `if not expr: return "set()"` | **I** | identical empty-collection guard + dedicated literal. |
| 3 | `let mut parts : List String := []` | `reprify`'s internal list | **I** | accumulator. |
| 4 | `for e in elems do parts := parts ++ [elemRepr e]` | `self.reprify(expr, ", ")` = `", ".join([self.doprint(item) for item in expr])` | **A-reference** | each element rendered via `self.doprint`/`srepr`, modeled by `elemRepr` (same opaque canonical renderer as fn 1). Validated by G-CONF. |
| 5 | `return "{" ++ String.intercalate ", " parts ++ "}"` | `"{%s}" % self.reprify(expr, ", ")` | **I** | join by `", "`, wrap in braces. |

## Prepatch correspondence (Solution_prepatch.lean impl)
At base_commit there was NO `_print_dict`/`_print_set`; a dict/set fell through
`_print` to `emptyPrinter`'s final `str(expr)` clause, rendering each contained
element via its own non-canonical text form. The prepatch encodes this:
- dict: op 4 becomes `nativeRepr p.1 ++ ": " ++ nativeRepr p.2` (element's plain
  text instead of the recursive renderer);
- set: the empty guard (op 2) is removed and op 4 becomes `nativeRepr e`.

`nativeRepr` and `elemRepr` are distinct opaque carriers, so the spec's
discriminating clause (every element rendered by the canonical renderer, plus the
`"set()"` empty case) is false against the prepatch — `correct_*` is unclosable
(G-DIFF; confirmed: prepatch fails verification with unsolved goals comparing
`nativeRepr …` vs `elemRepr …` and the missing `set()` branch).

## Soundness notes
- No changed op is inexpressible: both new methods are modeled deeply as their
  exact string composition; the recursive element renderer is an opaque carrier
  identical in spec and impl (A-reference), NOT axiomatized → `axioms = []`.
- Two independently-fixed behaviors (dict rendering, set rendering) live in ONE
  `Solution_prepatch.lean`: a single prepatch breaks BOTH `correct_dictRepr` and
  `correct_setRepr`, each on its own discriminating clause, so one prepatch
  variant suffices for G-DIFF.
- `conf_skip = false` (the impl is mostly I/R with an A-reference renderer;
  G-CONF differential-tests it against real `srepr`).
