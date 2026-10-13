# refinement.md — sympy__sympy-15345

Every operation in `implementation_printApplication` mapped to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX/G-CONF),
**I** (identical concrete op).

## `implementation_printApplication` ↔ `_print_Function` (square-bracket template, mathematica.py:102), reached for Max/Min via `_print_MinMaxBase = _print_Function`

Gold (post-patch) effect — a `Max`/`Min` node now dispatches to `_print_Function`,
whose return line is:
```python
return "%s[%s]" % (mfunc, self.stringify(expr.args, ", "))   # known-function branch
# (or, equivalently for the func-name fallback within the same method)
return expr.func.__name__ + "[%s]" % self.stringify(expr.args, ", ")
```
Pre-patch effect — no `_print_MinMaxBase`, so a `Max`/`Min` node fell through to
the generic `StrPrinter` rendering, producing the PARENTHESIZED call form
`Name(args)`.

| Lean op | patch.diff op | tag |
|---|---|---|
| `renderArgs render args` = `String.intercalate ", " (args.map render)` | `self.stringify(expr.args, ", ")` — per-argument render joined by `", "` | **A-reference** (per-argument renderer universally quantified; binding to real `self.stringify`/`self._print` checked by G-CONF) |
| `funcName ++ "[" ++ … ++ "]"` | `"%s[%s]" % (mfunc, …)` / `func.__name__ + "[%s]" % …` — square-bracket call template splice | **I** |

The prepatch's `funcName ++ "(" ++ renderArgs render args ++ ")"` corresponds to
the pre-patch generic fallback `Name(args)` (parenthesized call syntax) — the
exact bug the issue reports (`'Max(2, x)'` instead of `'Max[2, x]'`).

## Notes
- No op is changed-inexpressible. The single behavioral change — render the
  `Max`/`Min` application with the target language's square-bracket call template
  instead of the generic parenthesized fallback — is modeled directly as the
  bracket delimiters in the constant template.
- The argument list (order + per-argument rendering) is unchanged by the patch;
  it is captured by the universally-quantified `render` applied to each element of
  `args`, joined by the fixed separator.
- No consumed axiom: `render` is universally quantified, so the proof uses no
  property of it (the spec holds for every per-argument renderer).
  `axiom_check.py` is a skip stub. The R/I content (template splice with the fixed
  bracket delimiters and separators) is differential-tested by
  `conformance_check.py` (G-CONF, `conf_skip=false`).
