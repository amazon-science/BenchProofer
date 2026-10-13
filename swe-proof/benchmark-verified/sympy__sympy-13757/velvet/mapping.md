# mapping.md — sympy__sympy-13757

Symbol binding, type bijection, callee provenance, and the pinned G-CONF fuzz
seed. All file:line references are at `base_commit`
`a5e6a101869e027e7930e694f8b1cfb082603453`.

## 1. Symbol binding (what the spec models)

| Lean symbol | Repo reality (file:line @ base_commit) |
|---|---|
| `method formExpressionTimesPolynomial` | the product `expr * Poly` (ordinary expression on the left, polynomial on the right) — the gold-patched dispatch now reaches the polynomial's own multiplication handler `Poly.__rmul__` (`sympy/polys/polytools.py:108-115`). |
| `factorsCombineIntoPolynomial : Bool` | whether the two factors combine into a single polynomial value — i.e. whether the left operand can be cast into the polynomial's ring: in `Poly.__rmul__(f, g)`, `g = f.__class__(g, *f.gens)` succeeds (no `PolynomialError`). This is the unchanged combination machinery, NOT the patched datum. |
| `out.form = carriedOut` | `Poly.__rmul__` casts the left operand and returns `g.mul(f)` → a single evaluated `Poly` result (`is_Poly is True`). |
| `out.form = formalProduct` | the cast raises `PolynomialError`, so `Poly.__rmul__` returns `g*f.as_expr()` → an ordinary `Mul` standing, unevaluated product of the two factors (e.g. `sin(x)*Poly(x)` → `x*sin(x)`). |
| `productValue : List Int` | the coefficient vector of the evaluated product the polynomial handler returns when the product IS carried out (e.g. `x*Poly(x) == Poly(x**2)`); supplied as a free input — see §3. |

## 2. The type bijection (used by G-CONF)

The modeled observable is **whether the two factors combine into a single
polynomial value**, modeled as the single boolean the result depends on:

- **Repo:** `Poly.__rmul__(f, g)` (reached for `expr * Poly`) attempts to cast the
  left operand into the polynomial's ring: `g = f.__class__(g, *f.gens)`. If the
  cast SUCCEEDS the factors combine and the product is carried out
  (`g.mul(f)`, a single `Poly`); if it raises `PolynomialError` the factors do
  NOT combine and the product is left formal (`g*f.as_expr()`, an `sympy.Mul`).
  This convertibility test is the SAME combination machinery whether the
  polynomial is the left or the right operand — the gold patch does not change
  it; the gold patch only causes the `expr * Poly` form to reach this handler at
  all (see §3).
- **Lean:** `factorsCombineIntoPolynomial : Bool` = the truth value of that
  convertibility. Post-patch, when the two factors combine the product is carried
  out (`carriedOut`); when they do not, it is left formal (`formalProduct`). The
  spec pins BOTH branches.

Why the boolean is NOT the precedence comparison the patch flips: post-gold the
precedence comparison `Poly._op_priority(10.001) > Expr._op_priority(10.0)` is
**True for EVERY** `expr * Poly` regardless of the left operand, so it cannot
distinguish the carried-out cases (`x*Poly(x)`) from the genuinely-formal ones
(`sin(x)*Poly(x)`). The real carried-out/formal verdict is decided by the
convertibility of the left factor, which is what the spec observes.

`ProductForm` ↔ Python:
- `carriedOut`  ↔ the real `e * p` is a single evaluated value with
  `is_Poly is True` (the polynomial handler cast both factors and ran the mul).
- `formalProduct` ↔ the real `e * p` is still an `sympy.Mul` of the two factors.

`ProductResult.value : List Int` ↔ the coefficient list of the carried-out
product. Pinned by the spec to equal the supplied `productValue` (the unchanged
combination machinery's output) when carried out, not recomputed — see §3 and
directive 5.

## 3. Callee provenance + flag deps (no axioms)

There are **no** axiomatized callees and **no** deep-model references in this
bundle.

- The **gold patch** (`Poly._op_priority = 10.001`, `sympy/polys/polytools.py:109`,
  added) makes the binary-op dispatch for `expr * Poly` reach the polynomial's own
  handler `Poly.__rmul__` instead of falling through to the ordinary `Mul`
  machinery. Its observable consequence is exactly the carried-out / formal verdict
  this spec pins; it is not axiomatized (directive 7: never axiomatize the changed
  op — here it is modeled as the consequence the F2P observes).
- The **convertibility** of the left factor (`Poly(g, *gens)` succeeds vs. raises
  `PolynomialError`) is combination machinery the patch does NOT touch; it is the
  determinant of carried-out vs. formal and is observed directly as the boolean
  `factorsCombineIntoPolynomial`, NOT axiomatized.
- The **product value** the polynomial handler computes when the product is
  carried out (`g.mul(f)` → `dmp_mul` etc.) is likewise combination machinery the
  patch does NOT touch. Its result is supplied to the operation as the free input
  `productValue`; the spec's `ensures … out.value = productValue` holds for EVERY
  such value, strictly weaker than pinning any concrete product. Hence no contract
  is owed for it (directive 7; SPEC_GUIDE §3 "no dead axioms").

No flag-dependent callees.

## 4. G-CONF fuzz seed

Pinned seed: **13757**. `conformance_check.py` computes the boolean shadow verdict
on the REAL repo carrier — `Poly(left_operand, *poly.gens)` succeeds vs. raises
`PolynomialError` — and diffs it against the observed `e * Poly(x,x)`
classification over the F2P boundary rows (convertible ⇒ carried out) PLUS
non-convertible transcendental operands (`sin(x)`, `exp(x)`, … ⇒ FORMAL) plus
100,000 fuzzed left operands of both kinds (numbers, symbols, powers, linear
forms, and transcendentals). Both branches of the modeled boolean are exercised.
