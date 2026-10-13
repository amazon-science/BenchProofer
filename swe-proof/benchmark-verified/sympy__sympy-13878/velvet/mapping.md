# mapping.md — sympy__sympy-13878

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 7b127bdf71a65d230c1c5128b34521acc84e3290`, states the type
abstraction (the bijection G-CONF uses to bridge the Lean carrier ↔ the library
objects), and records callee provenance and the pinned fuzz seed.

Repo file under change: `sympy/stats/crv_types.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `arcsinCdfBuild (a b x : Expr)` | `ArcsinDistribution._cdf(self, x)` — **added** by the gold patch at `sympy/stats/crv_types.py:157` (in the class `ArcsinDistribution`, `crv_types.py:150`); `a, b` are `self.a, self.b` (`_argnames = ('a','b')`, `crv_types.py:151`) | the modeled changed function: it builds the closed-form cumulative distribution object |
| `Expr` (`pure`) | the fragment of `sympy` symbolic term-builders the closed form uses: `Piecewise`, `S.Zero`/`S.One`/`S(2)`, `pi`, `/`, `*`, `-`, `asin`, `sqrt`, the relationals `<`/`<=`, and the `True` guard | the honest expression data carrier |
| `arcsinExprCdf (a b x : Expr)` (`pure`, deep model — **A-reference**) | the exact `Piecewise(...)` the patch's `_cdf` returns (`crv_types.py:157-163` post-patch) | pure spec: the per-operand expansion of the desired result object; its equality to the real library value is validated by `conformance_check.py` (G-CONF) |

The unchanged dispatch that makes `_cdf` observable is
`SingleContinuousDistribution.cdf` (`sympy/stats/crv.py:214-220`): with no kwargs
it returns `self._cdf(x)` when that is not `None`, else falls through to
`self.compute_cdf(**kwargs)(x)` (definite integration). The patch does **not**
touch this dispatch — it only supplies the `_cdf` data. At base,
`ArcsinDistribution` has `pdf` only (no `_cdf`, `crv_types.py:150-154`), so the
base default `SingleContinuousDistribution._cdf` returns `None`
(`crv.py:211-212`) and `cdf(Arcsin('x',a,b))(x)` returns the unevaluated
definite integral `Integral(1/sqrt(-_x**2+_x*a+_x*b-a*b), (_x, -oo, x))/pi` —
modeled by `Expr.integralFallback` in the pre-change skeleton.

## 2. Type abstraction (R-refinement) — the Lean↔library bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean
carrier and the library objects. The carrier is a finite expression inductive
because the modeled operation is *symbolic-object construction*; each
constructor maps 1:1 to a library term-builder. The library applies the same
canonicalisation (relational flip `x < a` → `a > x`; additive-argument ordering
`x - a` → `-a + x`) on BOTH sides of the differential — the SHADOW builds with
the same builders, so it lands on the same canonical object. G-CONF compares
under `Basic.__eq__` (structural equality), the exact relation `test_arcsin`
asserts on. The bijection therefore reproduces the canonical object; it does not
re-implement the canonicaliser.

| Lean `Expr` constructor | library term-builder | note |
|---|---|---|
| `Expr.zero` | `S.Zero` | rational `0` |
| `Expr.one` | `S.One` | rational `1` |
| `Expr.natLit n` | `S(n)` | exact integer literal (here `n = 2`) |
| `Expr.pi` | `pi` | circle constant |
| `Expr.div p q` | `p / q` | field division |
| `Expr.mul p q` | `p * q` | multiplication |
| `Expr.sub p q` | `p - q` | subtraction |
| `Expr.asin e` | `asin(e)` | inverse sine |
| `Expr.sqrt e` | `sqrt(e)` | square root |
| `Expr.lt p q` | `p < q` (`StrictLessThan`) | strict order relation |
| `Expr.le p q` | `p <= q` (`LessThan`) | non-strict order relation |
| `Expr.top` | `True` | the always-true final guard |
| `Expr.piecewise3 v1 c1 v2 c2 v3 c3` | `Piecewise((v1,c1),(v2,c2),(v3,c3))` | three-clause case split |
| `Expr.integralFallback lo hi` | the generic `Integral(...)` value from the default integration route | pre-change skeleton only; never produced by the patched function |

The operands `a, b, x` are free `Symbol`s (the distribution's two endpoints and
the evaluation point); `Expr` leaves them abstract, so the constructed tree is
*parameterised by the actual operands* — there is an input data carrier (the
operands appear in the result's order and arithmetic relations), and the result
is forced to be produced by them. This is the §0.8 grounding: the postcondition
is not an opaque oracle echo, because `arcsinExprCdf` is a transparent
constructor expression over `a, b, x`, not an axiom or hardcoded lookup.

## 3. Callee provenance

### 3.1 `arcsinExprCdf` deep model ↔ `ArcsinDistribution._cdf` value (A-reference)
The changed operation — constructing the closed-form cumulative distribution
object — is modeled **deeply** by `arcsinExprCdf` in the `pure` region; there is
**no consumed axiom**. The library term-builders it composes (`Piecewise`,
`asin`, `sqrt`, the relationals, the field operations) are **unchanged** by the
patch; the patch supplies only the *arrangement* of these builders. G-CONF
(`conformance_check.py`) validates that the deep model, transliterated through
the §2 bijection, equals the real library value `cdf(Arcsin(name,a,b))(x)`
(post-patch) under structural equality — the A-reference check.

No `axiom_check.py`: there is **no consumed axiom and no unchanged imperative
callee** to validate in isolation. The unchanged callees are pure symbolic
term-builders; their behaviour is exercised end-to-end by G-CONF, which builds
real `Piecewise`/`asin`/`sqrt`/relational objects via the bijection and compares
the assembled object to the real `cdf`. Axiomatising `_cdf` itself is forbidden
(§0.7, it is the function under change); axiomatising the term-builders
separately would be a dead axiom subsumed by G-CONF.

## 4. Fuzz seed (G-CONF)

`conformance_check.py` pins `SEED = 13878`, `N_FUZZ = 100_000`. The input degrees
of freedom are the symbol names and assumption sets of the three operands (there
are no numeric input values: the function maps symbols → a symbolic object). The
fuzzer's first cases reproduce `test_arcsin` exactly (`a, b` real; `x` plain),
then vary names and assumption sets (`plain`/`real`/`positive`) to confirm the
constructor bijection is robust rather than an artefact of one symbol choice.
Comparison is `Basic.__eq__` — the relation the sole FAIL_TO_PASS uses.

## 5. F2P discriminator

`FAIL_TO_PASS = ["test_arcsin"]` (len 1; `PASS_TO_PASS` len 19, none of the other
modified-distribution `cdf` tests appear in either list — confirmed
programmatically). The new fail→pass assertion is
`cdf(X)(x) == Piecewise((0, a > x), (2*asin(sqrt((-a + x)/(-a + b)))/pi, b >= x),
(1, True))`. At base this returns an unevaluated `Integral` (≠ the `Piecewise`),
so `test_arcsin` fails; post-patch the `_cdf` short-circuit returns the
`Piecewise`, which equals the asserted tree (the library canonicalises the raw
`x < a`/`x - a` forms to `a > x`/`-a + x` on construction). Confirmed
in-container: the constructor-bijection rebuild `== expected` is `True`; a
math-equal `acos`-form rebuild `== expected` is `False` (a structurally
different tree fails the assert) — so the structural pin is exactly the F2P
criterion, and the spec is neither too weak (the `acos` counter-impl is rejected)
nor an echo (the tree is built from the operands).
