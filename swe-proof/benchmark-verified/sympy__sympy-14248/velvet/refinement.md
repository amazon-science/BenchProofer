# refinement.md — sympy__sympy-14248

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `joinSignedMatrixTerms` `do` block and the deep `joinSignedTerms` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** / **A-reference**), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs are audited by **G-AX**. This bundle has **no A legs** (no
axioms, no A-references — see mapping.md §3): every row below is R or I.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The modeled site — `StrPrinter._print_MatAdd` (`sympy/printing/str.py:313`)

Gold hunk (str.py):
```
-        return ' + '.join([self.parenthesize(arg, precedence(expr))
-            for arg in expr.args])
+        terms = [self.parenthesize(arg, precedence(expr))
+             for arg in expr.args]
+        l = []
+        for t in terms:
+            if t.startswith('-'):
+                sign = "-"
+                t = t[1:]
+            else:
+                sign = "+"
+            l.extend([sign, t])
+        sign = l.pop(0)
+        if sign == '+':
+            sign = ""
+        return sign + ' '.join(l)
```

| # | Solution.lean impl op (`joinSignedMatrixTerms` / pure model) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `terms : List (List Char)` | `terms = [self.parenthesize(arg, precedence(expr)) for arg in expr.args]` | R | each `str` term ↔ `List Char` (mapping.md §2). The `parenthesize`/`precedence` calls are the **unchanged** R-bridge input — G-CONF feeds the SAME real `parenthesize` strings to both sides, so they are shared input, not a modeled op. |
| A2 | `require terms ≠ []` | (implicit) sympy builds `MatAdd` only with `≥ 2` args | R | the precondition mirrors the structural guarantee that `expr.args` is non-empty (mapping.md §2); `l.pop(0)` in the gold relies on it. |
| A3 | leading term `terms[0]!` emitted verbatim (`joinSignedTerms_head`) | `sign = l.pop(0); if sign == '+': sign = ""; return sign + …` — the first `[sign, t]` pair: the leading body `t` keeps its own `-` (its sign is folded back as the `sign` prefix when it was `-`, dropped when `+`) | I | the gold pops the *first* `[sign, body]`; if that sign is `-` it is re-prefixed, if `+` it is dropped — net effect is the first term **verbatim** (its leading `-` preserved, no `+`). `joinSignedTerms (t :: ts) = t ++ joinTail ts` encodes exactly this. |
| A4 | each non-leading term → `tailPiece t = ' ' :: termSign t :: ' ' :: termBody t` | the loop body `if t.startswith('-'): sign='-'; t=t[1:] else: sign='+'` then `l.extend([sign,t])`, joined by `' '.join` | I | `termSign`/`termBody` are the `startswith('-')` split; `' '.join([…, sign, body, …])` puts a space on each side of `sign`, i.e. `" sign body"` per non-leading term. Transliterated 1:1 by G-CONF's `shadow_join`. |
| A5 | result returned as `List Char` | the returned `str` | R | `List Char` ↔ `str` (mapping.md §2); the F2P tests compare the rendered string. |

The backward `while` fold (`result := tailPiece t ++ result`, `i := i-1`, then
`return terms[0]! ++ result`) is the **I** transliteration of the left-to-right
`' '.join` over `l`: it accumulates `joinTail (terms.drop i)` and finally
prepends the verbatim head, equal to `joinSignedTerms terms` (the loop invariant
`result = joinTail (terms.drop i)`, proven via `joinTail_drop_step`).

## B. No axioms / no A-references

The single changed operation (the sign-folding join) is modeled **deeply** in
the `pure` region; there is no consumed axiom and no A-reference. The only
callee, `StrPrinter.parenthesize`, is **unchanged** and shared as input by both
legs of G-CONF (mapping.md §3) — it is an R-bridge, not an axiom. `axiom_check.py`
re-confirms the deep model equals the real patched `_print_MatAdd` over boundary
+ fuzz as a non-vacuous witness for the "no axioms" claim.

## C. No kind-3 (inexpressible-changed-op) steps in the modeled site

Every step of the modeled `_print_MatAdd` is R or I. The operation that genuinely
changed — folding a leading-negative term into a subtraction — is modeled deeply
(`termSign`/`termBody`/`tailPiece`/`joinTail`), not hidden behind an axiom about
the function under change.

The patch's **other** hunks (str/latex `_print_MatMul`; latex/pretty
`_print_MatAdd`) are out of `Solution.lean` scope by the §0 scoping decision in
mapping.md — latex MatAdd is the byte-identical algorithm (covered up to its
per-term renderer R-bridge), MatMul is an independent behaviour, and pretty
renders onto a 2-D canvas Velvet's value fragment cannot express (kind-3 for
*that* site only). They ship in `patch.diff` (gold verbatim) so G-RESOLVE
exercises them; they are NOT mislabeled as modeled. The modeled MatAdd site
already discriminates the headline bug and every code-printer F2P (which inherit
`str.py._print_MatAdd` via `CodePrinter(StrPrinter)`).

## D. verify(Solution) ⇒ resolved (on the modeled site)

`joinSignedMatrixTerms` verifies only if its output equals `joinSignedTerms terms`
— the per-term sign-folding join with a leading-`-` term rendered as `" - body"`
(A4) and the head verbatim (A3). The pre-patch `_print_MatAdd` (`' + '.join`)
renders a leading-`-` term as `" + -body"`; `Solution_prepatch.lean` reproduces
that and **fails** `out = joinSignedTerms terms` at the loop invariant (G-DIFF),
which is exactly the F2P-observed bug (`str(A - A*B - B)` was `-B + -A*B + A`,
now `-B - A*B + A`). By R (`str ↔ List Char`, shared `parenthesize` input) the
verified join equals the patched `str.py._print_MatAdd` on the tested inputs; by
G-CONF the R/I transliteration agrees with `patch.diff` over ≥10⁵ fuzzed matrix
sums; by G-AX the deep model equals the real patched callee. The gold patch
(which also fixes the unmodeled sibling sites identically) resolves (G-RESOLVE).
Trust points: refinement fidelity (this doc, G-CONF) — there are no axioms to
trust (G-AX is a redundant witness here).
