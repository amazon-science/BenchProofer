# mapping.md — sympy__sympy-15345

## Symbol binding (file:line @ base_commit 9ef28fba5b4d6d0168237c9c005a550e6dc27d81)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_printApplication` / `problem_spec_printApplication` | `MCodePrinter._print_Function` (square-bracket call template), reached for Max/Min via the new method binding `_print_MinMaxBase = _print_Function` | `sympy/printing/mathematica.py:96` (return line `102`); new binding at `:103` (post-patch) |
| `render : Expr → String` | the printer's own per-argument renderer; concretely `self.stringify((sub,), ", ")` over each argument | `sympy/printing/mathematica.py` `MCodePrinter`/`StrPrinter.stringify` |
| `funcName : String` | `expr.func.__name__` (and, for a known function, the mapped target name `mfunc` — here equal, `"Max"`/`"Min"`) | `mathematica.py:101`,`102` |
| `args : List Expr` | `expr.args` (the canonicalized argument tuple) | — |

## The fix, abstractly

A `Max`/`Min` expression is a `MinMaxBase` node, NOT a plain `Function`, so before
the patch the Mathematica printer had no method for it and the generic
`StrPrinter` fallback rendered it with PARENTHESIZED call syntax `Name(args)` —
which is not valid syntax in the target CAS. The gold patch (a) registers `Max`/
`Min` in the known-functions table and (b) binds `_print_MinMaxBase =
_print_Function`, so the node is now rendered by the function-application routine
into the target language's SQUARE-BRACKET call template `Name[args]`.

The single observable behavioral change is the call-delimiter syntax:
`Name(args)` (pre-patch, generic fallback) → `Name[args]` (post-patch, target CAS
call template). The argument list itself (order + per-argument rendering) is
identical pre/post — it comes from `expr.args` canonicalization and the unchanged
per-argument printer. The modeled routine pins exactly the post-patch template
shape `funcName ++ "[" ++ <args joined by ", "> ++ "]"`.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Lean | Python |
|---|---|
| `Expr : Type` (abstract) | a sympy `Expr` (one argument) |
| `render : Expr → String` | `lambda sub: p.stringify((sub,), ", ")` — the printer's per-argument renderer |
| `funcName : String` | `expr.func.__name__` ∈ {"Max","Min"} |
| `args : List Expr` | `list(expr.args)` |
| `renderArgs render args` | `self.stringify(expr.args, ", ")` — per-arg render, joined by `", "` |
| `result : String` | the rendered string |

`Expr` is an abstract Lean type variable; `render` is universally quantified, so
the spec/impl are parametric over EVERY per-argument renderer. The only modeled
behavior is the call template shape: square brackets `Name[args]` (post-patch) vs
the generic parenthesized `Name(args)` (pre-patch / prepatch impl).

## Callee provenance + flag deps

- `render` (the per-argument renderer, `self.stringify`/`self._print`) is the
  UNCHANGED printer machinery. It is NOT axiomatized: it is left universally
  quantified, so it is an A-reference recorded only to document the G-CONF binding
  to the real callee.
- No flag dependency: `Max`/`Min` are registered with the trivial condition
  `lambda *x: True`, so the function-application branch always fires for them; the
  bracket template is unconditional.

## Pinned G-CONF fuzz seed

`random.Random(15345)`, N = 100_000 (`conformance_check.py`).
