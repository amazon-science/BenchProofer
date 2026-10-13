# refinement.md — sympy__sympy-20428

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`symbolicNonzero` `do` block and the deep `nonzeroSpec` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; state the
bijection), **A** (axiomatized callee — **A-consumed** / **A-reference**), or
**I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs + narrative by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The truth-value site — `Expression.__bool__` (`expressiondomain.py:122`)

Gold hunk:
```
         def __bool__(f):
-            return f.ex != 0
+            return not f.ex.is_zero
```

| # | Solution.lean impl op (`symbolicNonzero`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `e : SymExpr` | `f`, the `Expression` element of `__bool__` | R | `f` ↔ its two zero-observations `{identicallyZero, literalZero}` (mapping.md §2). The element is read by `__bool__` through exactly these observations; G-CONF bridges via `identicallyZero := (f.ex.is_zero is True)`, `literalZero := (f.ex == 0)`. |
| A2 | `return !e.identicallyZero` | `return not f.ex.is_zero` | I | identical concrete op under R: `e.identicallyZero` ↔ `f.ex.is_zero is True`, and Boolean `!`/`not` correspond. `is_zero`'s three-valued `None` (indeterminate) maps to `identicallyZero = false`, exactly matching `not None == True` (reported nonzero). G-CONF transliterates this verbatim. |

Discriminating content of the change — an element that **denotes** zero
(`identicallyZero = true`) but is **not the literal zero** (`literalZero =
false`) must be reported as zero, whereas the pre-patch `f.ex != 0` reports it
nonzero. This is pinned by `out = nonzeroSpec e` with `nonzeroSpec e =
!e.identicallyZero` (which ignores `literalZero`). The pre-patch body `f.ex !=
0` is the structural test `!e.literalZero`; `Solution_prepatch.lean` reproduces
exactly that and **fails** `out = nonzeroSpec e` (G-DIFF) precisely on the
`identicallyZero = true, literalZero = false` case — the issue's bad poly.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the truth
value of a symbolic element — is modeled **deeply and concretely**
(`nonzeroSpec = !identicallyZero`, step A2, an **I** under the type R of A1), not
hidden behind an axiom about the function under change. There is **no consumed
axiom** and **no A-reference** to an external callee: the two zero-tests
`Expr.is_zero` / `== 0` are primitive, unchanged observations of the element,
abstracted to the two `SymExpr` booleans and exercised structurally by G-CONF
(refinement.md follows the django__django-10554 deep-model precedent).

## C. G-AX is vacuous

No axioms (A-consumed) and no deep-model references to an external callee
(A-reference). `axiom_check.py` emits `status=skip` (mapping.md §3). The only
externally-checkable modeling claim — the `require` precondition `literalZero →
identicallyZero` (a literal-zero representation always denotes zero) — is
validated against real SymPy `EX(expr)` elements inside G-CONF (boundary + 10^5
fuzz, 0 violations), where the real patched `__bool__` is also the oracle.

## D. verify(Solution) ⇒ resolved

`symbolicNonzero` verifies only if its output equals `!e.identicallyZero` (A2) —
the mathematical zero test, ignoring the literal-zero representation. By R
(`f` ↔ `{identicallyZero, literalZero}`, mapping.md §2) the verified decision
equals `not f.ex.is_zero` on every element, which is the gold `__bool__`. By
G-CONF the R/I transliteration of `nonzeroSpec` agrees with the real patched
`__bool__` on ≥10⁵ inputs (0 disagreements; against base_commit it disagrees only
on the discriminating math-zero-not-literal element). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves the F2P test `test_issue_20427`
(`Poly(<a complicated constant that is mathematically 0>, x) == Poly(0, x,
domain='EX')`, which requires the zero element to test as zero). G-RESOLVE
confirms. Trust point is exactly refinement fidelity (this doc, G-EQ + G-CONF);
there is no axiom-soundness trust point (G-AX vacuous).
