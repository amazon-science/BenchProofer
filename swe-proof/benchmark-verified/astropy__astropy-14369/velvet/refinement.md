# refinement.md — astropy__astropy-14369

Operation-by-operation correspondence between `Solution.lean`'s `reduceDivisionChain`
impl region (with the deep `chainPower` / `expVec` model) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A-consumed** (proof
uses an axiom's `ensures`), **A-reference** (a deep model validated `==` the real
callee by `axiom_check.py` / G-AX), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs, so
it resolves.*

`patch.diff` is the gold patch **verbatim** (applies cleanly at `base_commit`,
the real correctness oracle, G-RESOLVE).

## A. What the patch changes

The gold patch edits the YACC grammar that the CDS unit-format parser is built
from (`astropy/units/format/cds.py`, with the regenerated LALR table in
`cds_parsetab.py`). The single behavioural hunk is the division rule:

```
 division_of_units : DIVISION unit_expression
-                  | unit_expression DIVISION combined_units
+                  | combined_units DIVISION unit_expression
```

The action body is textually unchanged (`p[0] = p[1] / p[3]`), but its meaning
flips: pre-patch the right-hand operand (`p[3] = combined_units`) is the
*recursively parsed remainder of the chain*, so division nests to the RIGHT and
each nesting level negates everything below it; post-patch the left-hand operand
(`p[1] = combined_units`) is the *accumulated left group* and the right operand
(`p[3] = unit_expression`) is a single unit, so division groups to the LEFT.

Observable consequence on a chain `u(0)/u(1)/.../u(n-1)`:

| grouping | exponent of operand at position i |
|---|---|
| post-patch (left)  | `+1` if `i==0`, else `-1` |
| pre-patch (right)  | `(-1)**i` (alternating: `+1,-1,+1,-1,...`) |

The two agree at i=0 and i=1 and first diverge at i=2 — exactly what the issue
reports ("the order of the division seems jumbled") and what the F2P tests
`km/s/Mpc`, `km/(s.Mpc)` observe.

## B. The model carrier

A division chain is modelled as a count `n : Nat` of operand positions in
textual order; the parse result is modelled as the `List Int` of resulting
integer exponents, one per operand position (`expVec n`). The full unit object
(scale, bases, dimensional algebra) is abstracted away: the tested defect is
purely the per-operand exponent the grouping assigns, so the exponent vector is
the complete observable.

## C. Operation correspondence

| # | Solution.lean op (`reduceDivisionChain`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | `n : Nat` — the number of operand positions of the chain in textual order | the operand sequence the parser reduces (`unit_expression` leaves of the `combined_units`/`division_of_units` tree) | R | rich `UnitBase` operands ↔ opaque positions `0..n-1`; only operand *position* matters for the exponent (mapping.md §2). |
| C2 | leading position seeded with exponent `+1` (`chainPower (i-1)` with `i-1==0`) | the leftmost `unit_expression` enters `combined_units` with power +1 (the `division_of_units : DIVISION unit_expression` / `product_of_units : unit_expression` base cases keep the head positive) | I/R | identical concrete fact (head exponent +1); R only in the carrier. |
| C3 | every later position gets exponent `-1` (`chainPower (i-1)` with `i-1>=1`) | post-patch rule `combined_units DIVISION unit_expression` with `p[0] = p[1] / p[3]`: the accumulated left group `p[1]` divided by the single new operand `p[3]` ⇒ that operand's power is negated exactly once | A-reference | the *changed* reduction is modelled **deeply** by `chainPower` (the +1/-1 rule), NOT behind a consumed axiom. The real (patched) callee — `astropy.units.Unit(<chain>, format='cds')` — is run by `axiom_check.py` (G-AX), which asserts the parsed exponent vector equals `chainPower` at **every operand position** on boundary + exhaustive + fuzz chains. |
| C4 | `(reduceDivisionChain n) = expVec n` and `out.length = n` postconditions | the parser emits one power per operand, with the left-grouped powers above | A-reference + I | one exponent per operand is structural; the values are the C3 A-reference. |

There is **no consumed axiom** and **no opaque unchanged callee** in the proof:
the only kind-A entry is the **A-reference** C3, the deep model validated against
the real patched parser by G-AX.

## D. The pre-patch differential witness

`Solution_prepatch.lean` keeps the spec byte-identical and implements the
right-grouped reduction: it assigns each operand position exponent `(-1)**i`
(parity) via `if (i-1) % 2 = 0 then 1 else -1`. Its loop body then **fails** to
re-establish the spec invariant `result = expVecFrom i (n-i)` — the prepended
parity value disagrees with `chainPower` at the first position `>= 2` (where
parity yields `+1` but left-grouping demands `-1`), so `prove_correct` cannot
close. This is exactly the clause that senses the grammar change (G-DIFF), and
the same divergence the F2P `km/s/Mpc` (`Mpc` at position 2) exhibits.

## E. No kind-3 (unexpressible-changed-op) steps

Every step is R, I, or A-reference. The one operation that genuinely *changed*
— the associativity/grouping of repeated division — is modelled **deeply**
(`chainPower` + the verified backward fold in `reduceDivisionChain`), not hidden
behind an axiom about the function under change. Its equality to the real patched
parser is the single trust point, discharged by G-AX (axiom_check.py).

## F. verify(Solution) ⇒ resolved

`reduceDivisionChain` verifies only if the leading position has exponent +1 and
every following position has exponent -1 (the left-grouped vector `expVec`,
C2–C4). By R (operand positions ↔ real `UnitBase` operands, exponent vector ↔ the
parsed composite unit's powers) the verified result equals the exponent vector
the post-patch CDS parser produces; G-AX confirms `chainPower == real parser` on
the F2P inputs, all length-≤5 distinct-operand chains, and 4000 fuzz chains
(0 mismatches). The shipped `patch.diff` is the gold patch verbatim, which makes
the official harness `resolved` (G-RESOLVE) — including the secondary grammar
effect that `km/s.Mpc-1` is now correctly *rejected* (the same single rule
change; carried entirely by patch.diff, beyond the exponent-vector view the model
pins). The two trust points are A-reference soundness (G-AX) and refinement
fidelity (this document, G-EQ).
