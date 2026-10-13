# refinement.md — sympy__sympy-13878

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `arcsinCdfBuild` `do` block and the deep model `arcsinExprCdf`) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == real callee by G-AX/G-CONF), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE). The modeled site is the
single FAIL_TO_PASS-relevant change: the added `ArcsinDistribution._cdf`. The
other eleven `_cdf` additions and the cosmetic edits in the gold patch are not
modeled (none of their tests appear in FAIL_TO_PASS or PASS_TO_PASS — see
mapping.md §5); they ride along in `patch.diff` for G-RESOLVE but are outside
the modeled behaviour.

## A. The cumulative-distribution site — `ArcsinDistribution._cdf(self, x)`

Gold hunk (`sympy/stats/crv_types.py:157`, added):
```python
def _cdf(self, x):
    from sympy import asin
    a, b = self.a, self.b
    return Piecewise(
        (S.Zero, x < a),
        (2*asin(sqrt((x - a)/(b - a)))/pi, x <= b),
        (S.One, True))
```

| # | Solution.lean impl op (`arcsinCdfBuild`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `a b x : Expr` | `a, b = self.a, self.b` and the `x` argument | R | the two endpoint operands and the evaluation point ↔ free symbols; `Expr` leaves them abstract (mapping.md §2). G-CONF binds them to real `Symbol`s. |
| A2 | `onSupport := Expr.div (Expr.mul (Expr.natLit 2) (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a))))) Expr.pi` | `2*asin(sqrt((x - a)/(b - a)))/pi` | I (R on leaves) | constructor-for-constructor identical: `div/mul/sub/asin/sqrt/natLit/pi` ↔ `/ * - asin sqrt S(2) pi` (mapping.md §2). Transliterated and confirmed by G-CONF. |
| A3 | `return Expr.piecewise3 Expr.zero (Expr.lt x a) onSupport (Expr.le x b) Expr.one Expr.top` | `Piecewise((S.Zero, x < a), (<onSupport>, x <= b), (S.One, True))` | I (R on leaves) | three-clause case split, constructor-identical: `piecewise3` ↔ `Piecewise` of three `(value, cond)` pairs; `zero/one` ↔ `S.Zero/S.One`; `lt/le` ↔ `< / <=`; `top` ↔ `True`. The library canonicalises both this rebuild and the gold value identically (same builders), so they are the SAME object under `Basic.__eq__` (G-CONF, mapping.md §2). |

The whole modeled output is a deep model (`arcsinExprCdf`) of the value the
unchanged library term-builders produce: an **A-reference** validated == the
real `cdf(Arcsin(...))(...)` by G-CONF. There is **no consumed axiom** — the
builders are unchanged callees exercised end-to-end, not abstracted behind an
`ensures` the proof consumes.

**Termination semantics.** The bundle uses TOTAL correctness
(`loom.semantics.termination "total"`, `open TotalCorrectness`): the real
construction is a straight-line build of a fixed-shape expression object (a
bounded tree of constructor applications) and always terminates, so a
diverging implementation (one that never produces the closed-form object at
all) must NOT satisfy the spec. Under partial correctness such an
implementation would discharge the postcondition vacuously — a spec-too-weak
hole. The verified body is loop-free, so the totality obligation is
discharged directly.

Note on the postcondition shape (`ensures out = arcsinExprCdf a b x`):
`arcsinExprCdf` is a transparent, fully-unfolded function of the operands
(§A2–A3), not an answer-key oracle — an implementation that returns
`arcsinExprCdf a b x` IS the modeled computation (it builds the exact
closed-form tree from `a`, `b`, `x`), and its faithful refined patch is the
gold `_cdf` itself, which resolves (G-RESOLVE). Per SPEC_GUIDE directive 8,
a grounded oracle of this shape admits no *wrong* echo: every implementation
the spec admits produces the exact gold tree.

## B. The pre-change skeleton (G-DIFF)

At base, `ArcsinDistribution` has no `_cdf`; the default
`SingleContinuousDistribution._cdf` returns `None` and `cdf` falls through to
`compute_cdf` → an unevaluated definite integral. `Solution_prepatch.lean`
models this by returning `Expr.integralFallback x x` (the generic
integration-route object), which is **not** the closed-form case split the spec
demands, so `out = arcsinExprCdf a b x` is unsatisfiable and verification fails
on exactly the discriminating clause:

```
⊢ x.integralFallback x = arcsinExprCdf a b x   -- unsolved
```

This is the F2P discriminator: at base the cumulative function is the integral
object; post-patch it is the closed-form `Piecewise`.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, I, or A-reference. The operation that genuinely changed — the
construction of the closed-form cumulative-distribution object — is modeled
**deeply** (the spelled-out `arcsinExprCdf` over the operands, steps A2–A3), not
hidden behind an axiom about the function under change. There is **no consumed
`_cdf` axiom** and no answer-key oracle: `arcsinExprCdf` is a transparent
constructor expression over `a, b, x`, so its postcondition is dischargeable
only by building that exact tree from the operands (mapping.md §2 grounding).

A math-equal but structurally-different rebuild (e.g. the `acos` form, using
`asin(u) = π/2 - acos(u)`) does **not** satisfy `out = arcsinExprCdf a b x` and,
correspondingly, does **not** equal the F2P-asserted tree (confirmed
in-container: `acos`-form `== expected` is `False`). So the structural pin is
exactly the F2P criterion — the spec is strong enough (rejects the math-equal
counter-impl) and grounded (built from the operands), satisfying both prime
directives.

## D. verify(Solution) ⇒ resolved

`arcsinCdfBuild` verifies only if its output equals `arcsinExprCdf a b x` — the
exact three-clause closed form built from the operands (A2–A3). By R
(`Expr` constructor ↔ library term-builder, mapping.md §2) the verified output
transliterates to the real `Piecewise` the gold `_cdf` returns; by the A-reference
(G-CONF) that deep model equals the real `cdf(Arcsin(...))(...)` under structural
equality on 100 000 symbol/assumption configurations; that structural object is
exactly what the sole FAIL_TO_PASS `test_arcsin` asserts. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement, and the gold patch resolves (G-RESOLVE). The single trust point is
refinement fidelity (this doc + the constructor bijection, audited by G-EQ +
G-CONF); there are no consumed axioms to trust (G-AX is a no-op for this bundle).
