# mapping.md — symbol binding & type bijection (sympy__sympy-24562)

## Modeled function
- **Lean** `implementation_denominatorProduct : Nat → List Nat → Nat`
- **Python** the denominator-accumulation block of the rational-number
  constructor — `sympy/core/numbers.py:1626-1641 @ b1cb676c`
  (`Rational.__new__`, the assignments that build the combined denominator from
  the two normalised operands).

At `base_commit` that block reuses the variable `q`, which still holds the
*original divisor argument*, as the accumulator for the denominator
(`q *= p.q`). When the divisor argument is a textual integer (a `str`), `str *
int` is Python string repetition, so the divisor's written form is duplicated
rather than its value multiplied — yielding e.g. `Rational('0.5','100') ==
1/100100` instead of `1/200`. The fix introduces a fresh integer accumulator
and folds every contribution into it numerically, so the raw operand is only
ever *parsed*, never arithmetically scaled. The accumulation is unconditional:
a zero-valued string operand contributes its value 0, zeroing the combined
denominator (which then feeds the constructor's unchanged zero-denominator
handling downstream).

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| the denominator factor `p.q` contributed by the first operand (a positive `int`) | `Nat` (`pDen`), with `1 ≤ pDen` | produced by the unchanged callee `Rational(p).q` *before* this block; a normalised denominator is positive |
| divisor argument `q`, given as a decimal integer string `"100"` | `List Nat` (`qdigits`) | the ordered decimal digits, most-significant first; this textual form is what the bug repeats |
| `int(q)` / value of the divisor string | `decval qdigits` (left-fold `acc*10+d`) | the integer the digit string denotes |
| the combined denominator the block produces | `Nat` result `pDen * decval qdigits` | the integer the patched block assigns to the constructor's denominator, including 0 for a zero-valued operand |

Why `List Nat` (decimal digits), not just `Nat`: the bug is non-homomorphic in
the value domain (string repeat ≠ integer multiply), so a value-only model
could not exhibit it. The carrier must expose the *digit sequence* so that
"repeat the operand" (the prepatch) is distinguishable from "multiply its
value" (the spec).

## Callee provenance
- **decval** (decimal digit string → integer): an **A-reference**. It models
  the real numeric read of the divisor string (`int(q)` /
  `fractions.Fraction`). Validated by G-AX against Python integer parsing of
  the same digit string. NOT axiomatized.
- **product accumulation** `pDen * decval qdigits`: exact natural-number
  arithmetic, modeled deeply (no opaque callee). Its post-patch value is
  validated by G-CONF against the real repo behaviour.
- No UNCHANGED callee is consumed as an axiom; the axioms region is empty.

## Flag dependency
None. The modeled block runs whenever both arguments are supplied; there is no
flag gating the per-digit read or the accumulator fold. G-AX / G-CONF fuzz the
single behavior.

## G-CONF / G-AX fuzz seed
Pinned seed: **24562**. G-CONF runs ≥10⁵ fuzzed `(pDen, qdigits)` inputs
(factors 1..1000, digit strings of length 0..8 INCLUDING zero-valued and
leading-zero operands, oversampling the issue's `pDen=2, '100'` family) and
diffs the R/I shadow `pDen * decval(qdigits)` against the real patched repo's
own parse-and-accumulate behaviour. G-AX validates `decval` against Python
integer parsing on boundary + fuzz digit strings.
