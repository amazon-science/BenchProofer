# refinement.md — sympy__sympy-15345

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`renderNode` `do` block and the deep `render` model) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A-consumed** /
**A-reference** (axiom / deep-model of an outside callee — *none here*), or
**I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The dispatch site — render a node's argument text with the right delimiters

Gold hunks (`sympy/printing/mathematica.py`):
```
@@ known_functions @@
-
+    "Max": [(lambda *x: True, "Max")],
+    "Min": [(lambda *x: True, "Min")],
@@ MCodePrinter @@
     return expr.func.__name__ + "[%s]" % self.stringify(expr.args, ", ")
+    _print_MinMaxBase = _print_Function
```

| # | Solution.lean impl op (`renderNode`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `head : List Char` | `expr.func.__name__` (the head name `_print_Function` interpolates) | R | `str` ↔ `List Char` (mapping.md §2); an unchanged input. G-CONF reads the real head off the patched render and feeds the model the same. |
| A2 | param `args : List Char` | `self.stringify(expr.args, ", ")` (arguments rendered + comma-joined) | R + I | `str` ↔ `List Char`; the comma-join is the unchanged `stringify` helper. Held fixed on both G-CONF sides — the patch does not touch argument text or order. |
| A3 | param `kind : NodeKind` | the node's class, reduced to the rendering-relevant distinction (`MinMaxBase` ⇒ `.extremum`; dispatches to `_print_Function` ⇒ `.functionApp`; else ⇒ `.plainExpr`) | R | finite-domain abstraction of the dispatch key (mapping.md §2). |
| A4 | `match kind` choosing `head ++ ['['] ++ args ++ [']']` for `.functionApp` and `.extremum`, else `head ++ ['('] ++ args ++ [')']` | the `_print_MinMaxBase = _print_Function` alias (routes the extremum node class to the bracketed `"%s[%s]"` template) vs the inherited generic round-parenthesis fallback for un-dispatched nodes | I | concrete, transliterated by G-CONF. The extremum kind selecting the bracket form IS the alias; the function-app and plain-expr arms are the unchanged dispatch endpoints. |

Discriminating content of the change — the extremum kind moves from the
round-parenthesis branch to the square-bracket branch — lives in the
`.extremum => head ++ ['['] ++ args ++ [']']` arm (model) ⇔ the
`_print_MinMaxBase = _print_Function` alias (real). `Solution_prepatch.lean`
reproduces the pre-patch routing (`.extremum => head ++ ['('] ++ args ++ [')']`,
the generic-fallback delimiter) and **fails** the frozen clause
`kind = .extremum → out = head ++ ['['] ++ args ++ [']']` (G-DIFF, confirmed at
`Solution_prepatch.lean:85`).

## B. The `known_functions` "Max"/"Min" entries — behaviourally inert (I/no-op)

The gold patch also adds `"Max"`/`"Min"` to `known_functions`. Empirically
(mapping.md §3, verified in-container) this half is **behaviourally inert**:
`_print_Function` looks the head name up in `known_functions` and, on a hit,
emits `"<mfunc>[args]"` where `mfunc` is the mapped name — here `"Max"`/`"Min"`,
identical to the fallthrough `expr.func.__name__`. Applying the dict entries
WITHOUT the dispatch alias leaves `Max(x,y,z)` rendering `Max(x, y, z)`
(parens); applying the alias WITHOUT the dict entries already yields
`Max[x, y, z]`. So this hunk does not change any observable output and is
modeled as the identity (no node in the `do` block); the load-bearing op is A4.
No separate failing prepatch is owed for it (a prepatch must keep the spec
byte-identical, G-DIFF, and removing an inert hunk changes nothing observable).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the delimiter
pair chosen for an extremum node — is modeled **deeply** (the spelled-out
`match kind` dispatch in `render`, step A4), not hidden behind an axiom about
the function under change. There is **no consumed axiom and no A-reference deep
model of an outside callee**; the comma-joining helper (`stringify`) is unchanged
and consumed as the `args` input. G-AX is therefore skipped (mapping.md §3).

## D. verify(Solution) ⇒ resolved

`renderNode` verifies only if its output surrounds `args` with square brackets
for the extremum kind (A4) — `head[args]`, the valid function-application form —
and with the generic round parentheses only for un-dispatched nodes. By R
(`str ↔ List Char`, head/args as fixed inputs, `NodeKind` abstraction of the
dispatch key) the verified renderer equals the patched printer's per-node
behaviour on the tested nodes; by G-CONF the R/I transliteration of the dispatch
agrees with `patch.diff`'s behaviour on ≥10⁵ node renders (and DISAGREES with the
pre-patch printer exactly on the extremum nodes, confirming it tests the fix).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The sole
trust point is refinement fidelity (this doc + G-CONF); there are no axioms.
