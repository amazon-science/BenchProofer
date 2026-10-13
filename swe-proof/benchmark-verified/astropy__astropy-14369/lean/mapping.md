# mapping.md — symbol binding & type bijection (astropy__astropy-14369)

## Modeled function
- **Lean** `implementation_divChain : G → List G → G` (with `[CommGroup G]`)
- **Python** the division-chain reduction of the CDS unit grammar, i.e. the
  `division_of_units` production handler `p_division_of_units` together with the
  `combined_units` / `product_of_units` / `unit_expression` reductions that feed
  it — `astropy/units/format/cds.py:182-190 @ fa4e8d1` (the changed function).

The CDS parser turns a unit string into a unit value by reducing the YACC
grammar. The patch changes how a *chain of divisions* associates. A unit string
such as `A/B/C/D` is a leading term `A` followed by an ordered list of further
terms `[B, C, D]` each introduced by the quotient operator. The patched grammar
reduces this chain left-associatively: `(((A / B) / C) / D)`, which equals the
leading term divided by the product of all the following terms,
`A / (B · C · D)`. (The pre-patch grammar reduced it right-associatively,
`A / (B / (C / D))`, jumbling the trailing terms' signs.)

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| a parsed unit value (`UnitBase` / `CompositeUnit`) | an element of an arbitrary `CommGroup G` | units form a commutative group under multiplication: `*` is associative & commutative with identity the dimensionless unit, every unit is invertible, and `a / b = a * b⁻¹`. Concretely the free abelian group on the base units — an *exponent vector* (G-CONF/G-AX use that concrete carrier). |
| `p[1]` (leading `combined_units`) | `head : G` | the first term of the chain. |
| the remaining `unit_expression` terms, in source order | `rest : List G` | each subsequent term introduced by `/`. `[]` ↔ a single-term chain (no division). |
| `a * b` (unit multiplication) | `a * b` (group `*`) | base-exponent addition. |
| `a / b` (unit division, `p[1] / p[3]`) | `a / b` (group `/`) | base-exponent subtraction; `a / b = a * b⁻¹`. |
| `b ** -1` (`p[2] ** -1`, the single-term `/x` case) | `b⁻¹` (group inverse) | base-exponent negation. Recovered as `1 / b` = `head / [b].prod` with `head = 1`. |
| the reduced chain value | `result : G` | `head / rest.prod`. |

## Operations modeled deeply (A-reference)
The unit algebra is modeled DEEPLY as an arbitrary `CommGroup` — the impl and
spec use only `*`, `⁻¹`, `/`, `1` and `List.prod`. This is NOT axiomatized as a
bespoke `_prop`; it is Mathlib's `CommGroup` typeclass, whose laws the proof
consumes. G-AX validates that the real unit algebra (the free abelian group on
base units, represented as exponent vectors) satisfies exactly those laws used:
associativity and commutativity of `*`, `a / b = a * b⁻¹`, `1` neutral, and
equality decided by combined base exponents. Hence A-reference, not A-consumed.

## What the model deliberately abstracts
Lexing (token recognition for `UNIT`, `UINT`, `SIGN`, `X`, …), the numeric
`factor` prefix, bracket/parenthesis grouping, and per-unit powers are all
*unchanged* by the patch and orthogonal to the associativity fix. They are not
modeled: the bug and its fix are entirely in how a flat division chain
associates, which is exactly `head / rest.prod`. Parenthesised sub-chains reduce
to a single `G` element before entering the chain, so they are already captured
by a term of `rest` (or of `head`).

## Callee provenance
- No UNCHANGED callee is consumed as an axiom; the axioms region is empty. The
  multiplication / division / inverse operators are the unit algebra's own
  group operations (`core.CompositeUnit.__mul__` / `__truediv__` / `__pow__`),
  deep-modeled as `CommGroup` and G-AX-validated, not axiomatized.

## Flag dependency
None. The chain reduction reads no boolean flags.

## G-CONF fuzz seed
Pinned seed: **14369**. ≥10^5 fuzzed inputs: random division chains of length
0–8 over random base-unit exponent vectors, spanning single-term chains
(`head` only), the single-`/x` inverse case, and long chains — the inputs that
exercise the associativity reduction the patch changes.
