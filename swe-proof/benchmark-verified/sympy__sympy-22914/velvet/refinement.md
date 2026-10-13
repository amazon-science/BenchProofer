# refinement.md — sympy__sympy-22914

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`printApp` `do` block and the `renderCall`/`joinComma` pure helpers) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — A-consumed / A-reference), or **I** (identical
concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); there are no A legs in this bundle (no axioms, no deep-model references).
Claim: any impl verifying against this frozen spec, refined per the map below,
is behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The application-printing site — `_print_Function` / `_known_functions`

Gold hunk (`sympy/printing/pycode.py`):
```
 _known_functions = {
     'Abs': 'abs',
+    'Min': 'min',
+    'Max': 'max',
 }
```

The hunk is data: it adds `Min→min`, `Max→max` to the builtin-equivalent table.
The behavior changes in `CodePrinter._print_Function` (`codeprinter.py:415-429`):
when `expr.func.__name__` is in `known_functions`, the node is emitted as
`func(*[self.parenthesize(item,0) for item in expr.args])`, i.e.
`"<builtin>(<comma-joined rendered operands>)"`. Pre-patch, `Min`/`Max` are not
in the table, so the node falls through to the `_rewriteable_functions` branch
(`codeprinter.py:433`), which rewrites `Min`/`Max` to a `Piecewise` and prints a
conditional expression — never `min(...)`/`max(...)`. For every head other than
`Min`/`Max`/`Abs`, the emission is byte-identical pre- and post-patch (the gold
hunk touches nothing else); that unchanged emission enters the model as the
read-only input `fallback`, and the spec's fourth post-condition pins the
routine to return it VERBATIM — the no-regression half of the contract.

| # | Solution.lean impl op (`printApp`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `head : List Char` | `expr.func.__name__` (the head name) | R | head name `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via the real `expr.func.__name__`. |
| A2 | param `args : List (List Char)` | `[self.parenthesize(item, 0) for item in expr.args]` | R | the operands ALREADY rendered to source text; the recursive rendering is unchanged infrastructure supplied as input (mapping.md §2). Each rendered operand `str` ↔ `List Char`; the list ↔ `List`. G-CONF feeds the real `parenthesize(arg,0)` outputs. |
| A3 | param `fallback : List Char` | the emission the UNCHANGED surrounding machinery produces for a head that is none of `Min`/`Max`/`Abs` (the `_print_<class>` / rewrite / `_print_not_supported` paths the gold hunk does not touch) | R | pre-existing, unchanged infrastructure whose OUTPUT is supplied to the modeled decision as a read-only input; `str` ↔ `List Char` (mapping.md §2). G-CONF feeds the real pristine-printer `doprint(expr)` as `fallback` on non-mapped heads and a poison sentinel on mapped heads. |
| A4 | `if head = "Min".toList then renderCall "min".toList args` | the `known_functions` branch resolving `'Min' → 'min'` then `func(*rendered_args)` | I | concrete dispatch + call assembly, transliterated by G-CONF. The added table entry IS this branch firing for `Min`. |
| A5 | `else if head = "Max".toList then renderCall "max".toList args` | the `known_functions` branch resolving `'Max' → 'max'` | I | as A4, for `Max`. The second added table entry. |
| A6 | `else if head = "Abs".toList then renderCall "abs".toList args` | the PRE-EXISTING `'Abs' → 'abs'` entry firing | I | unchanged behavior, modeled for fidelity/regression (the pre-patch keeps exactly this); ensures the spec does not over-claim on heads outside the change. |
| A7 | `else return fallback` | any other head emitted by the unchanged machinery — byte-identical pre/post patch | I | the no-change pass-through; the fourth post-condition (`head ∉ {Min,Max,Abs} → out = fallback`) PINS it, so an impl that alters any non-Min/Max/Abs emission fails to verify. |
| A8 | `renderCall name args = name ++ "(" ++ joinComma args ++ ")"`; `joinComma` = operands joined by `", "` | `"{name}({', '.join(rendered_args)})"` (`func(*rendered_args)`; `stringify(args, ", ")`) | I | concrete string assembly, transliterated verbatim by G-CONF (`render_call`/`join_comma`). |

Discriminating content of the change — a `Min`/`Max` node emitting
`min(...)`/`max(...)` rather than the Piecewise conditional — lives in the
post-conditions `head = "Min".toList → out = renderCall "min".toList args` and
`head = "Max".toList → out = renderCall "max".toList args`.
`Solution_prepatch.lean` reproduces the pre-patch table (only `Abs`), so for
`head = "Min"` it returns `fallback` (the unchanged machinery's emission — the
Piecewise conditional in the real repo) and **fails** the post-condition
`out = renderCall "min" args` (`fallback` is unconstrained, in the real repo the
Piecewise text ≠ `min(...)`); likewise for `Max` (G-DIFF). This is exactly the
F2P assertion `prntr.doprint(Min(x, y)) == "min(x, y)"`.

## B. Why the spec is TIGHT (total on the modeled domain)

The four `ensures` clauses cover EVERY head: the three mapped heads are pinned
to their builtin-call emissions, and every other head is pinned to `fallback` —
the unchanged machinery's output supplied as input. No output is left
unconstrained, so a verifying impl cannot smuggle in behavior the gold patch
does not have (e.g. mapping `sin` to some builtin, emitting `MIN(...)`, or
garbling non-mapped emissions): any such impl violates the fourth
post-condition. The only degrees of freedom a verifying impl has are
representational (branch order, how it assembles the pinned strings), which are
behaviorally invisible.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely changed — emitting a
`Min`/`Max` application as a builtin call — is modeled **deeply and directly**
(the `if head = … then renderCall …` ladder, all concrete I ops over R-refined
inputs). There is no axiom about the function under change, and no deep-model
reference: the external dependencies — the rendered operand texts and the
unchanged machinery's emission for non-mapped heads — are read-only INPUTS
(`args`, `fallback`), not callees (mapping.md §2). Hence no `axiom_check.py`
and G-AX `skip`.

## D. verify(Solution) ⇒ resolved

`printApp` verifies only if, for `head = "Min"`, `out = renderCall "min" args`;
for `head = "Max"`, `out = renderCall "max" args`; for `head = "Abs"`,
`out = renderCall "abs" args`; and for EVERY other head, `out = fallback` — the
unchanged machinery's emission, i.e. the node prints exactly as before the
patch. By R (head name, rendered operands, and fallback text `str ↔ List Char`;
mapping.md §2) and I (call assembly transliterated verbatim; pass-through
identity), the verified routine equals the patched `_print_Function`'s emission
on ALL nodes: builtin calls on `Min`/`Max`/`Abs`, byte-identical unchanged
output elsewhere; by G-CONF the R/I transliteration agrees with the patched
`PythonCodePrinter().doprint` on ≥10⁵ inputs spanning both mapped and
non-mapped heads (and disagrees with the pre-patch printer on `Min`/`Max` — the
differential is live). Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement, and the gold patch resolves
(G-RESOLVE). There are no axiom trust points (no A legs); the sole trust point
is refinement fidelity (this doc, G-EQ + G-CONF).
