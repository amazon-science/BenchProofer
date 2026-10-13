# refinement.md — sympy__sympy-17139

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`powerRewriteStep` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-consumed** (proof uses
an axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); there are no A legs (no axioms), and the narrative is audited by **G-EQ**.
Claim: any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The rewrite step — the nested `_f(rv)` inside `_TR56` (`sympy/simplify/fu.py:498`)

Gold hunk (inserted guard):
```
         if not (rv.is_Pow and rv.base.func == f):
             return rv
+        if not rv.exp.is_real:
+            return rv

         if (rv.exp < 0) == True:
             return rv
```

| # | Solution.lean impl op (`powerRewriteStep`) | patch.diff / `_f` op | tag | justification |
|---|---|---|---|---|
| A1 | param `rv : Expr` | the node `rv` handed to `_f` | R | sympy expression ↔ opaque `Expr` (identity-only); mapping.md §2. Only `out == rv` vs `out == transformed` is observed. |
| A2 | `if !matchesPow then return rv` | `if not (rv.is_Pow and rv.base.func == f): return rv` (`fu.py:499`) | R + I | the unchanged first guard. `matchesPow : Bool` is a FREE refinement of `rv.is_Pow and rv.base.func == f` (mapping.md §2); the control op (return-unchanged) is I. |
| A3 | `if !expIsReal exp then return rv` | `if not rv.exp.is_real: return rv` (`fu.py:502–503`, the **inserted** lines) | R + I | **the change under spec.** `expIsReal exp = (exp.im == 0)` refines `bool(rv.exp.is_real)`: a non-real exponent (nonzero imaginary part, `is_real ∈ {False, None}`) ⇒ return unchanged; mapping.md §2. The control op is I (a guarded `return rv`). |
| A4 | `else return transformed` | fall-through to the downstream rewrite ladder (`rv.exp < 0 / > max / == 2 / h(g**2)**e`, `fu.py:504–522`) | R | the unchanged downstream is a FREE `transformed : Expr` (directive 7): the spec admits every downstream value, so it can never be stronger than the real callee. G-CONF leaves `transformed` as the real `_TR56` downstream and checks only that the guard routes correctly. |

Discriminating content of the change — a targeted power with a NON-REAL exponent
must be returned unchanged (A3) — lives in `expIsReal exp = false ⇒ out = rv`.
Pre-patch, `_f` had no such screen: a non-real exponent fell straight to
`(rv.exp < 0) == True`, which raises `TypeError: Invalid comparison of complex`.
`Solution_prepatch.lean` reproduces the missing screen (a targeted power always
proceeds to `transformed`) and **fails** the `(matchesPow ∧ ¬ expIsReal exp) →
out = rv` clause (G-DIFF). `conformance_check.py` additionally confirms the real
pre-patch comparison `(rv.exp < 0) == True` raises on every non-real exponent and
the patched `_TR56` returns the power unchanged — the guard is load-bearing.

## B. No additional change sites

The patch is a single two-line guard insertion in one function. No callee
replacement, no second site, no independently-fixed behaviour ⇒ one prepatch.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — the reality screen
on the exponent — is modeled DIRECTLY in the method body (A3), decided
structurally by `expIsReal` from the exponent's imaginary component, not hidden
behind an axiom about the function under change. There are NO consumed axioms and
NO deep-model reference: the two unchanged sub-steps (`matchesPow`,
`transformed`) are free values (directive 7), strictly weaker than any contract,
so neither is owed one and G-AX is skipped.

## D. verify(Solution) ⇒ resolved

`powerRewriteStep` verifies only if (i) a non-targeted node is returned unchanged
(A2), (ii) a targeted power with a non-real exponent is returned unchanged (A3 —
the F2P behaviour: `T(sin(x)**I, …) == sin(x)**I`, `simplify(cos(x)**I) ==
cos(x)**I`), and (iii) a targeted power with a real exponent proceeds to the
downstream value (A4). By R (`Expr` identity, free `matchesPow`/`transformed`,
`expIsReal ↔ rv.exp.is_real`) the verified step equals the patched `_f` on the
modeled inputs; by G-CONF the R/I transliteration of the guard agrees with the
real patched `_TR56` over the fuzzed inputs (and the bug discriminator is
confirmed). Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement — and the gold patch resolves (G-RESOLVE).
The only trust point is refinement fidelity (this doc, G-EQ + G-CONF); there are
no axioms to trust (G-AX skipped).
