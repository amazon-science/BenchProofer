# refinement.md — sympy__sympy-24562

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `denominatorProduct` `do` block and the `digitsValue` deep model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** / **A-reference** (axiomatized / deeply-modeled callee — none
here), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The denominator-accumulation block — `Rational.__new__` (`sympy/core/numbers.py:1626-1641`)

Gold hunk (the relevant lines):
```
         q = 1
         gcd = 1
+        Q = 1
         if not isinstance(p, SYMPY_INTS):
             p = Rational(p)
-            q *= p.q
+            Q *= p.q
             p = p.p
         ...
         if not isinstance(q, SYMPY_INTS):
             q = Rational(q)
             p *= q.q
-            q = q.p
+            Q *= q.p
         else:
-            q = int(q)
+            Q *= int(q)
+        q = Q
```

| # | Solution.lean impl op (`denominatorProduct`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `pDen : Nat` (require `pDen ≥ 1`) | the denominator factor `p.q` of the first operand | R | `Nat` ↔ Python `int p.q`, both ≥ 1 (normalised denominator is positive). Produced by the unchanged callee `Rational(p).q` *before* this block (mapping.md §3). |
| A2 | parameter `qDigits : List Nat` (require each `< 10`) | the second operand `q`, a non-negative integer in decimal notation (the `str` case) | R | decimal digit string ↔ `List Nat`, most-significant-first (mapping.md §3). G-CONF bridges via `int("".join …)`. |
| A3 | `let v := digitsValue qDigits` | parsing the operand to its integer value: post-patch `Q *= int(q)` / `Q *= Rational(q).p` | I | `digitsValue` (the `foldl acc*10+d` model) is the concrete positional-decimal parse, transliterated 1:1 by G-CONF (`digits_value`). Equality to sympy's own parse (`Rational(qstr).p`) is fuzzed by G-CONF over ≥10⁵ inputs. |
| A4 | `acc := 1; acc := acc * pDen; acc := acc * v` | the patched accumulation `Q = 1; Q *= p.q; Q *= int(q)` | I | the fresh-accumulator multiply chain, transliterated 1:1 (`pDen * digitsValue(qDigits)`). The combined denominator is the arithmetic **product** of the factor and the operand's value. |
| A5 | `return acc` (`Nat`) | `q = Q` (the combined denominator) | R | `Nat` ↔ Python `int` denominator; both feed the same downstream sign/gcd normalisation, unchanged by the patch. |

Discriminating content of the change — the operand is combined by its numeric
**value**, not by repeating its digit sequence — lives in
`ensures out = pDen * digitsValue qDigits`. The pre-patch block ran
`q *= p.q` while `q` was still the **raw textual operand**, so `str * int`
**repeated** it (`'100' * 2 = '100100'`); `Solution_prepatch.lean` reproduces
that as `digitsValue ((List.replicate pDen qDigits).flatten)` and **fails** the
value-product postcondition (G-DIFF), e.g. for `pDen=2, qDigits=[1,0,0]`:
`100100 ≠ 200`.

**Termination semantics.** The file uses `loom.semantics.termination "total"`
(total correctness). The real accumulation block is a straight-line multiply
chain (`Q = 1; Q *= p.q; Q *= int(q)`) that always terminates and returns, and
the F2P test observes its returned denominator, so total correctness is the
faithful semantics. Partial correctness would admit a same-spec implementation
that diverges (an infinite loop vacuously satisfies every `ensures`) — a wrong
impl the tests would fail — so it would leave the spec too weak.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — how the second
operand contributes to the denominator (multiply its value, never scale the raw
operand) — is modeled **deeply** (the spelled-out `digitsValue` parse + the
value-product, steps A3–A4), not hidden behind an axiom. There are **no axioms**
in this bundle (A-consumed = ∅, A-reference = ∅): the factor and the decimal
operand are read-only abstractions of values produced by UNCHANGED callees
(`Rational(p).q`, `int(q)` / `Rational(q)`) that run *before* the changed block.

## C. verify(Solution) ⇒ resolved

`denominatorProduct` verifies only if its output equals `pDen * digitsValue
qDigits` (A3–A4) — the value-product, never the digit-repeat. By R
(`Nat ↔ int`, decimal-digit ↔ `List Nat`) the verified block equals the patched
`Q`-accumulation on the string-operand inputs the F2P test exercises
(`Rational('0.5','100') == Rational(1,200)`, and the 3×3 matrix
`Rational(p,q).as_numer_denom() == Rational('%s/%s'%(p,q)).as_numer_denom()`).
By G-CONF the R/I transliteration of `digitsValue` + the value-product agrees
with `patch.diff`'s behaviour on ≥10⁵ inputs (the shadow's `digitsValue` equals
sympy's own decimal parse). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The sole trust point is refinement fidelity (this doc,
G-EQ + G-CONF); there are no axioms (G-AX skip).
