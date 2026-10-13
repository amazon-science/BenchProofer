# refinement.md — sympy__sympy-16766

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `renderAccess` `do` block, the deep `joinComma`/`accessRender` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** / **A-reference**), or **I**
(identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. This bundle has
**no A legs** (mapping.md §3): every step is R or I.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change — add `PythonCodePrinter._print_Indexed`

Gold hunk (`sympy/printing/pycode.py`, after `_print_Not`):
```
+    def _print_Indexed(self, expr):
+        base = expr.args[0]
+        index = expr.args[1:]
+        return "{}[{}]".format(str(base), ", ".join([self._print(ind) for ind in index]))
```

| # | Solution.lean impl op (`renderAccess`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `base : List Char` | `str(base)` where `base = expr.args[0]` (the carrier) | R | rendered-fragment `str` ↔ `List Char` (mapping.md §2). `str(base)` is an **unchanged** helper output; its value is the input carrier. G-CONF feeds the shadow the real `str(base)`. |
| A2 | param `indices : List (List Char)` | `[self._print(ind) for ind in expr.args[1:]]` (the rendered subscripts) | R | list of rendered-fragment strings ↔ `List (List Char)`, length + order preserved (mapping.md §2). `self._print` is **unchanged** by the patch; each fragment is input carrier. G-CONF feeds the shadow the real `self._print(ind)`. |
| A3 | the `while` loop building `joined = joinComma indices` (backward fold, prepending `piece` then `", "` except for the last fragment) | `", ".join([... ])` | I | the comma-join is modeled **deeply** and concretely: `joinComma` interleaves `", "` between consecutive fragments with no leading/trailing separator — exactly `str.join`. Transliterated and differential-tested by G-CONF. |
| A4 | `return base ++ "[".toList ++ joined ++ "]".toList` | `"{}[{}]".format(str(base), <joined>)` | I | the fixed template `"{}[{}]"` is exactly base, `"["`, joined, `"]"` concatenated (mapping.md §2). Concrete; G-CONF-tested. |
| A5 | the result carries **no** "unsupported"-annotation prefix (it is `accessRender`, nothing prepended) | the post-patch handler returns the access string directly, so `Indexed` is no longer added to `self._not_supported` and `doprint` prepends no `# Not supported` comment | I | the OBSERVABLE the F2P test checks is `doprint(p[0,1]) == 'p[0, 1]'` — i.e. the rendered access with **no** warning comment. The deep model emits exactly that string and nothing else. |

Discriminating content of the change — the access is rendered as *supported*
code (`base[i0, i1, …]` with no annotation) instead of falling through to the
generic "unsupported construct" handler that prepends a `# Not supported in
Python:` / `# Indexed` comment block. `Solution_prepatch.lean` reproduces the
pre-patch behaviour (prefixing that annotation) and **fails** `out =
accessRender base indices` (G-DIFF): its returned `out` begins with the
annotation bytes, so it is provably `≠ accessRender base indices`.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — adding a
dedicated rendering for element access so it is emitted as supported code — is
modeled **deeply** (the spelled-out `joinComma`/`accessRender` and the verified
backward fold). There is **no consumed axiom** and **no A-reference**: the only
callees the patch invokes (`str(base)`, `self._print(ind)`) are unchanged and
their outputs are the input carrier (R), not oracles (mapping.md §3). The result
is grounded entirely in the inputs (SPEC_GUIDE §0 directive 8): `out` is a pure
structural function of `base` and `indices`, never an opaque answer key.

## C. verify(Solution) ⇒ resolved

`renderAccess` verifies only if its output equals `accessRender base indices` —
the carrier text, then the subscript fragments joined by `", "` inside square
brackets, with no annotation prefix (A3–A5). By R (`str ↔ List Char`, the
`"{}[{}]"` template ↔ bracket concatenation, `str.join ↔ joinComma`) the verified
result equals `"{}[{}]".format(str(base), ", ".join(self._print(ind) …))` on the
real rendered components — exactly the gold patch's `_print_Indexed`. The F2P
test `prntr.doprint(p[0, 1]) == 'p[0, 1]'` observes precisely this string (and
its absence of the pre-patch warning comment); the seven PASS_TO_PASS cases
(`x**y`, `Mod`, `And`, `Or`, `pi`, `acos`, `Piecewise`, `sign`, …) are untouched
because the change is purely additive (a new `_print_Indexed` method; no existing
dispatch altered). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). There are no axiom trust points; the residual trust is the type
bijection (mapping.md §2), falsifiable by G-CONF.
