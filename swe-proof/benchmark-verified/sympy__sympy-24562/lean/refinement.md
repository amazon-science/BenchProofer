# refinement.md — operation correspondence (sympy__sympy-24562)

Maps every op in `implementation_denominatorProduct` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

The patch replaces the denominator accumulation in the two-argument rational
constructor. Pre-patch the divisor argument variable `q` doubles as the
accumulator (`q *= p.q`), so the divisor's *textual* form is repeated when it
is a string. Post-patch a fresh integer accumulator collects every denominator
contribution numerically (`Q *= p.q`, `Q *= int(q)`), then hands the product to
the constructor (`q = Q`). We model the first operand's denominator
contribution as a positive whole-number factor (`pDen : Nat`), and the divisor
argument as its decimal digit string (`List Nat`) — because the digit string is
exactly the operand the bug repeats.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `pDen : Nat` (hyp `1 ≤ pDen`), `qdigits : List Nat` | the factor `p.q` from the first operand and the divisor argument `q` (a decimal int string) | R | `p.q` ↔ `Nat` ≥ 1 (produced by the unchanged callee `Rational(p).q` before this block); divisor string ↔ `List Nat` digit list (mapping.md bijection) |
| 2 | `let mut denAcc : Nat := 1` | `Q = 1` (the fresh integer accumulator the patch adds) | I | the new accumulator, initialised to 1 |
| 3 | `denAcc := denAcc * pDen` | `Q *= p.q` (patch line, was the buggy `q *= p.q`) | R | `p.q` ↔ `pDen`; numeric multiply into the accumulator |
| 4 | `for d in qdigits do c := c*10 + d` | `int(q)` — reading the divisor string into an integer | A-reference | decimal-digit read of the divisor; validated == Python integer parsing by G-AX. NOT axiomatized |
| 5 | `denAcc := denAcc * c` | `Q *= int(q)` (patch line, was the buggy `q = int(q)` overwrite) | I/R | fold the parsed divisor value into the same accumulator — unconditionally, so a zero-valued operand zeroes the product |
| 6 | `return denAcc` | `q = Q` (the combined denominator handed to the constructor) | R | `Nat` ↔ Python `int` denominator; both feed the same downstream sign/gcd/zero handling, unchanged by the patch |

No A-consumed rows: the proof discharges `decval` and the product directly; no
UNCHANGED callee property is assumed.

The discriminating clause is the combined denominator. Post-patch the divisor's
value is multiplied numerically: result `= pDen * decval qdigits`, including
the value 0 when the operand is zero-valued (the accumulation itself never
skips or filters a contribution — zero handling stays where it always was,
downstream of this block). The prepatch impl repeats the divisor *digit string*
`pDen` times before reading it (`q *= p.q` on a string), so for any factor
`pDen > 1` and nonzero operand the combined denominator is
`decval (qdigits ++ … ++ qdigits)` ≫ `pDen * decval qdigits`. Hence its
`correct_denominatorProduct` cannot close against the frozen
`problem_spec_denominatorProduct`. That is the G-DIFF signal, and it mirrors
the real bug: `Rational('0.5','100')` returned `1/100100` at `base_commit` and
`1/200` post-patch.

**Why the observable is the combined denominator (an integer), not a final
rational value.** The graded behavior is the value the fixed accumulation hands
to the rest of the constructor. Modeling only "numerator ÷ divisor value" would
under-pin the change: it would admit an accumulation that special-cases some
contributions (e.g. skips a zero-valued operand) yet agrees on all
nonzero-divisor quotients — an implementation whose transliteration back to the
repo diverges from the gold accumulation and fails the hidden tests around
zero-denominator handling. Pinning the product itself (`pDen * decval qdigits`,
total over the domain, zero included) leaves no such slack: any impl satisfying
the spec computes exactly the patched accumulation.
