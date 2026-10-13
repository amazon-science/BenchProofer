# refinement.md — astropy__astropy-14369

Operation-by-operation correspondence between `model.py`'s implementation (the
`reduce_division_chain` impl region + the deep `chain_power` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `Ensures`), **A-reference** (a deep model
validated `==` the real callee by `axiom_check.py` / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

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

Observable consequence on a chain `u(0)/u(1)/.../u(n-1)` whose operand at
position i carries its own intrinsic exponent `q(i)` (an operand may be written
with a numeric power of its own, `unit_with_power : UNIT numeric_power`, so
`kpc2` is ONE operand with `q = 2`), and with `lead` marking a chain that opens
with the division operator:

| grouping | exponent of operand at position i |
|---|---|
| post-patch (left)  | `+q(i)` if `i==0 and not lead`, else `-q(i)` |
| pre-patch (right)  | `(-1)**i · q(i)`, negated once more if `lead` (alternating) |

The two agree at i=0 and i=1 and first diverge at i=2 — exactly what the issue
reports ("the order of the division seems jumbled": `10+3J/m/s/kpc2` came out
with `s` and `kpc2` mis-signed) and what the F2P tests `km/s/Mpc`,
`km/(s.Mpc)`, `10+3J/m/s/kpc2` and `/s` observe. Both rules were validated
against the real parser in the instance image: post-patch on 6815 chains and
pre-patch on 2708 (the remainder of the same sweep being surfaces the pre-patch
grammar rejects outright), 0 mismatches each.

## B. The model carrier

A division chain is modelled as a `List[int]` of operand identifiers; the parse
result is modelled as the `List[int]` of resulting integer exponents, one per
operand position. The full unit object (scale, bases, dimensional algebra) is
abstracted away: the tested defect is purely the per-operand exponent the
grouping assigns, so the exponent vector is the complete observable.

## C. Operation correspondence

| # | model.py impl op (`reduce_division_chain`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | `powers: List[int]` — the intrinsic exponent of each chain operand, in textual order | the operand sequence the parser reduces (`unit_expression` leaves of the `combined_units`/`division_of_units` tree), each leaf's own numeric power from `unit_with_power : UNIT numeric_power` (`p[0] = p[1] ** p[2]`, `cds.py:230-236`) | R | rich `UnitBase` operands ↔ their integer intrinsic exponents; operand *identity* does not affect the exponent the grouping assigns, so it is abstracted away, but the operand's own exponent DOES and so is carried (mapping.md §2). |
| C2 | head keeps its own exponent, and only when `leading` is false (`result = [q] + result` when `i-1==0 and not leading`) | the leftmost `unit_expression` enters `combined_units` with its own power via `product_of_units : unit_expression` (`p[0] = p[1]`, `cds.py:179-180`). The OTHER production, `division_of_units : DIVISION unit_expression`, is the leading-`/` case and does the opposite — `p[0] = p[2] ** -1` (`cds.py:188-189`) NEGATES its operand — which is why the model gates the positive head on `not leading` rather than claiming a universally positive head. `CDS.parse('/s')` = `1 / s`, head exponent -1, confirmed in-container. | I/R | identical concrete fact per branch; R only in the carrier. |
| C3 | every later operand has its own exponent negated (`result = [-q] + result` otherwise) | post-patch rule `combined_units DIVISION unit_expression` with `p[0] = p[1] / p[3]`: the accumulated left group `p[1]` divided by the single new operand `p[3]` ⇒ that operand's power is negated exactly once, magnitude preserved | A-reference | the *changed* reduction is modelled **deeply** by `chain_power`, NOT behind a consumed axiom. The real (patched) callee — `astropy.units.Unit(<chain>, format='cds')` — is run by `axiom_check.py` (G-AX), which asserts the parsed exponent vector equals `chain_power` at **every operand position** on boundary + exhaustive + fuzz chains, across powered operands, repeated bases and both `leading` settings. |
| C4 | `len(Result()) == len(powers)` and the element-wise `Result()[k] == chain_power(k, powers[k], leading)` postcondition | the parser emits one power per operand, with the left-grouped powers above | A-reference + I | one exponent per operand is structural; the values are the C3 A-reference. Where two positions share a base the parser reports their sum, which this per-position vector determines (mapping.md §2 bridge). |

There is **no consumed axiom** and **no opaque unchanged callee** in the proof:
the only kind-A entry is the **A-reference** C3, the deep model validated
against the real patched parser by G-AX.

## D. The pre-patch differential witness

`model_prepatch.py` keeps the spec byte-identical and implements the
right-grouped reduction: it assigns the operand at position i its own exponent
times `(-1)**i` (negated once more when the chain opens with the division
operator). It verifies its own loop and then **fails** the spec's postcondition

```
Forall k. 0<=k<len(Result()) ==> Result()[k] == chain_power(k, powers[k], leading)
```

precisely at the first even position `>= 2` (where parity yields `+powers[k]`
but left-grouping demands `-powers[k]`) — i.e. exactly the clause that senses
the grammar change (G-DIFF). Recorded verifier output:

```
Verification failed
model_prepatch.py:80:13:82:54: error: Postcondition of reduce_division_chain
  might not hold. Assertion Forall(int, (lambda k: (Implies(((0 <= k) and
  (k < len(Result()))), (Result()[k] == chain_power(k, powers[k], leading))),
  [[Result()[k]]]))) might not hold.
```

This is the same divergence the F2P `km/s/Mpc` (`Mpc` at position 2) exhibits.

## E. No kind-3 (unexpressible-changed-op) steps

Every step is R, I, or A-reference. The one operation that genuinely *changed*
— the associativity/grouping of repeated division — is modelled **deeply**
(`chain_power` + the verified fold in `reduce_division_chain`), not hidden
behind an axiom about the function under change. Its equality to the real
patched parser is the single trust point, discharged by G-AX (axiom_check.py).

## F. verify(model) ⇒ resolved

`reduce_division_chain` verifies only if the head operand keeps its own exponent
when the chain does not open with the division operator and every other operand
has its own exponent negated exactly once (the left-grouped vector, C2–C4). By R
(per-position intrinsic exponents ↔ real `unit_expression` leaf powers, the
`leading` flag ↔ the leading-`/` production, exponent vector ↔ the parsed
composite unit's powers) the verified result equals the exponent vector the
post-patch CDS parser produces; G-AX confirms `chain_power == real parser` on
the F2P inputs (powered and leading-`/` forms included), all length-≤4
distinct-base chains of powered operands under both `leading` settings, all
length-≤4 repeated-base chains, and 4000 fuzz chains — 4663 total, 0 mismatches
— and G-CONF shadows the impl against the same callee on 100942 inputs with 0
disagreements. Both checks were confirmed to FAIL against the pre-patch parser
in the same image, so their passes discriminate. The shipped `patch.diff` is the gold patch verbatim, which makes
the official harness `resolved` (G-RESOLVE) — including the secondary grammar
effect that `km/s.Mpc-1` is now correctly *rejected* (the same single rule
change; carried entirely by patch.diff, beyond the exponent-vector view the
model pins). The two trust points are exactly PLAN §1.1: A-reference soundness
(G-AX) and refinement fidelity (this document, G-EQ).
