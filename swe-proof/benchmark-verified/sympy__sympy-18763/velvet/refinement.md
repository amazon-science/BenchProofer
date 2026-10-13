# refinement.md — sympy__sympy-18763

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `renderSubsNotation` `do` block plus the deep `subsNotationLatex` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
bijection in mapping.md §2), **A-consumed** / **A-reference** (none here), or
**I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The assembly site — `_print_Subs()` (`sympy/printing/latex.py:706`)

Gold hunk:
```
- return r'\left. %s \right|_{\substack{ %s }}' % (latex_expr, latex_subs)
+ return r'\left. \left(%s\right) \right|_{\substack{ %s }}' % (latex_expr, latex_subs)
```
The unchanged preamble (lines 700-705: unpack `subs.args`; `latex_expr =
self._print(expr)`; the `latex_subs = r'\\ '.join(...)` of the rendered
assignments) computes the two fragments that enter the model as the free inputs
`body` (`latex_expr`) and `subsList` (`latex_subs`).

| # | Solution.lean impl op (`renderSubsNotation`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `body : List Char` | `latex_expr` (the `%s` for the inner expression) | R | `str` ↔ `List Char` (mapping.md §2). G-CONF computes `body` with the real `LatexPrinter._print(expr)` (unchanged callee, run as itself), bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | parameter `subsList : List Char` | `latex_subs` (the second `%s`) | R | `str` ↔ `List Char`. G-CONF computes `subsList` with the real unchanged `r'\\ '.join(...)`. |
| A3 | `"\\left. \\left(".toList ++ body` | the `%`-format emitting `\left. \left(` then `latex_expr` | I | identical concrete prefix + concatenation; the literal template piece ↔ the same `String.toList`. This is the **discriminating** op: the body is enclosed in its own `\left( ... \right)` pair. |
| A4 | `++ "\\right) \\right|_{\\substack{ ".toList ++ subsList` | the format emitting `\right) \right|_{\substack{ ` then `latex_subs` | I | identical concrete middle segment + concatenation; closes the enclosing delimiter pair before the evaluation bar and the stacking group. |
| A5 | `++ " }}".toList`, returned (`List Char`) | the trailing ` }}` of the format, the `return` | I + R | identical concrete suffix; `str` ↔ `List Char` on the returned value. `_print_Subs`'s `str` return ↔ `out`. |

Discriminating content of the change — the body is wrapped in a matched
`\left( ... \right)` delimiter pair (A3+A4) rather than emitted bare — lives in
`subsNotationLatex`'s `"\\left. \\left(" ++ body ++ "\\right) \\right|..."`
(model) ⇔ the post-patch `\left. \left(%s\right) \right|...` format (real). The
pre-patch template emitted the body bare (`\left. %s \right|...`);
`Solution_prepatch.lean` reproduces that and **fails** `out = subsNotationLatex
body subsList` exactly on the missing `\left(`/`\right)` (G-DIFF).

## B. No axioms, no deep-model references

No `axiom` and no A-reference. The single changed operation — the return-template
string assembly — is modeled **deeply and concretely** (`subsNotationLatex`, the
spelled-out `++` chain), and the `do` block is the identical concatenation (all
**I**). The unchanged upstream renderers (`self._print`, the `\\ `.join) are not
axiomatized; their outputs are the free inputs `body` / `subsList` (no asserted
contract ⇒ nothing for G-AX to validate ⇒ no `axiom_check.py`, G-AX skips).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — wrapping the body
in `\left( ... \right)` — is fully expressible (literal concatenation), so it is
modeled concretely (I), not hidden behind an axiom about the function under
change.

## D. verify(Solution) ⇒ resolved

`renderSubsNotation` verifies only if its output equals the exact
delimiter-enclosing assembly (A3-A5), i.e. the body wrapped in `\left( ...
\right)`. By R (`str ↔ List Char`; the unchanged renderers `_print` / `\\ `.join
compute `body` / `subsList`) the verified assembly equals the post-patch
`r'\left. \left(%s\right) \right|_{\substack{ %s }}' % (latex_expr, latex_subs)`
on every `Subs` input; by G-CONF the I-transliteration of the assembly agrees
with `patch.diff`'s behaviour on ≥10⁵ fuzzed `Subs` objects. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The only trust point is
refinement fidelity (this doc, G-EQ + G-CONF); there are no axioms.
