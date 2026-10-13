# refinement.md — sympy__sympy-13757

Operation-by-operation correspondence between `Solution.lean`'s `do` block
(`formExpressionTimesPolynomial`) and `patch.diff`. Every row is tagged
**R** (type refinement), **A-consumed**, **A-reference**, or **I** (identical
concrete op). No row is a *changed inexpressible op* (no kind-3).

The gold patch is a single class-attribute addition
(`Poly._op_priority = 10.001`); its entire observable effect is to cause the
`expr * Poly` product (ordinary expression on the left) to reach the polynomial's
own multiplication handler `Poly.__rmul__` instead of falling through to the
ordinary `Mul` machinery. That handler then carries the product out iff the two
factors combine into a single polynomial value (the left operand casts into the
polynomial's ring), and leaves it formal otherwise. The `do` block models exactly
that conditional outcome.

| # | Lean `do`-block op | patch.diff / repo counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `factorsCombineIntoPolynomial : Bool` (method input) | in `Poly.__rmul__(f, g)` (`sympy/polys/polytools.py:108-115`, reached post-gold for `expr * Poly`): whether `g = f.__class__(g, *f.gens)` succeeds (no `PolynomialError`) | **R** | Type refinement: the repo attempts to cast the left operand into the polynomial's ring; only WHETHER the cast succeeds (the factors combine) is observable to the carried-out/formal outcome, so it is refined to the single `Bool`. Bijection: `factorsCombineIntoPolynomial = (Poly(left_operand, *poly.gens) succeeds)`. Mechanically refuted by G-CONF (recomputes the cast on the real objects, diffs the Bool against observed carried-out/formal over both branches). |
| 2 | `let form := if factorsCombineIntoPolynomial then carriedOut else formalProduct` | `Poly.__rmul__`: `try: g = f.__class__(g, *f.gens)` then `return g.mul(f)` (carried out, a single `Poly`) `except PolynomialError: return g*f.as_expr()` (formal `Mul`) — `polytools.py:108-115` | **I** | Identical control flow: the same success/failure of the cast selects between "carry the product out into a single value" (carried out) and "return the standing formal product" (formal). The `do`-block's `if/else` mirrors the handler's `try/except` one-to-one. |
| 3 | `return { form := form, value := productValue }` | the carried-out branch returns the handler's evaluated product `g.mul(f)`; `productValue` is that handler's output | **R** | Type refinement: the rich `Poly`/`Mul` result object is refined to `ProductResult` carrying only the two touched observations (`form`, `value`). The value is supplied as a free input (combination machinery the patch does not change, mapping.md §3) and preserved unchanged into the result when carried out (directive 5: read-only `productValue`, `ensures factorsCombineIntoPolynomial = true → out.value = productValue`). |

## R/I legs checked by G-CONF
Rows 1 and 3 are **R**; row 2 is **I**. G-CONF (`conformance_check.py`) builds the
R/I shadow of the `do` block in Python over the real repo carrier — recomputing
the cast `Poly(left_operand, *poly.gens)` (row 1) and classifying the real
`e * Poly` result as carried-out/formal (row 2 consequence) — and diffs it
against `patch.diff` behaviour over ≥10⁵ fuzzed inputs spanning BOTH convertible
(carried-out) and non-convertible (formal) left operands. Zero disagreements ⇒
the R/I legs are faithful on both branches.

## Axiom legs
None. No A-consumed axioms and no A-reference deep models (see mapping.md §3 and
meta.json). The impl region contains R/I content, so `conf_skip = false` and
G-CONF runs (it is not the all-A-tagged skip case).
