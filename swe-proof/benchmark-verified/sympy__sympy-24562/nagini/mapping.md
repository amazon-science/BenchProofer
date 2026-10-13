# mapping.md — sympy__sympy-24562

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b1cb676cf92dd1a48365b731979833375b188bf2`, states the type
abstraction, and gives the provenance of each axiom.

Repo file under change: `sympy/core/numbers.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `combine_ratio(p_num, p_den, q_digits, q_den)` | the integer-combination block of `Rational.__new__(cls, p, q=None, gcd=None)` — `sympy/core/numbers.py:1628-1641` (the changed accumulation; gold adds `Q = 1` / `q = Q`) | the modeled changed function: form the quotient of a dividend (resolved to `p_num/p_den`) and a divisor (numerator the textual `q_digits`, denominator `q_den`) into the constructed ratio's `(numerator, denominator)` before gcd reduction; single contracted+implemented function (markers are module-level singletons) |
| `read_int(digits)` *(axiom — A-consumed)* | `fractions.Fraction(str).numerator` for an all-digit string, reached via `q = Rational(q)` → `Q *= q.p` (`sympy/core/numbers.py:1636-1638` post-patch) | the unchanged textual-integer reader: parses a whole-number digit string to its integer value |
| `aux_value(digits, n)` *(axiom — A-reference)* | the value `fractions.Fraction(str * n).numerator` obtained from the longer string produced by Python `str` repetition `q * p.q` — the pre-patch line `q *= p.q` performed while `q` was still the textual divisor (`sympy/core/numbers.py:1630` pre-patch) | the value an alternative reading obtains from the SAME characters after repetition; **in the consumer spec view it is named neutrally (`aux_value`) and left fully unpinned (no relation to `read_int` is stated)** so the spec view reveals nothing about the bug mechanism; validated `== int(s*n)` and `!= n*int(s)` by axiom_check.py (G-AX). Used ONLY by `model_prepatch.py`'s impl (hidden), never by `model.py`'s proof or postconditions. |

The pre-patch repo behaviour the change removes (for the refinement audit, not
referenced from the consumer spec view): the in-place reuse of the variable `q`
as the denominator accumulator (`q *= p.q` at `numbers.py:1630`, `q = q.p` at
`numbers.py:1638`), which let the *textual* divisor `q` be combined with `p.q`
— i.e. string-repeated — before it was ever interpreted as a number.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the dividend operand `p` after `p = Rational(p)` — an exact ratio with numerator `p.p` and positive denominator `p.q` | two ints `p_num`, `p_den` (`p_den >= 1`) | `p_num ↔ p.p`, `p_den ↔ p.q` |
| the divisor operand `q` after `q = Rational(q)`: numerator `q.p` (spelled by the textual digit token) and denominator `q.q` | digit sequence `q_digits: List[int]` (numerator) + int `q_den` (denominator, `q_den >= 1`) | `q_digits[k] ↔ ord(digit_k of q's numerator text)`; `read_int(q_digits) ↔ q.p`; `q_den ↔ q.q`; specification carried by `PSeq[int]` via `ToSeq` |
| the constructed `(numerator, denominator)` pair (`p`, `Q`) just before gcd reduction (`numbers.py:1640-1657`) | `Tuple[int, int]` `(out_num, out_den)` | `Result()[0] ↔ p` (final numerator pre-reduction = `p.p * q.q`), `Result()[1] ↔ Q` (final denominator pre-reduction = `p.q * q.p`) |

**Modeled domain (the widened, F2P-covering scope).** The model covers **every
input shape the F2P/P2P tests exercise**: the dividend `p` is any exact rational
with `p_den >= 1` (integer when `p_den == 1`, fractional when `p_den > 1`); the
divisor `q` is any exact rational whose numerator is the all-digit token
`q_digits` and whose denominator is `q_den >= 1` (whole number when `q_den == 1`,
fractional when `q_den > 1`). In that domain the constructed pre-reduction pair
is `(p_num * q_den, p_den * read_int(q_digits))`, which is exactly what
`combine_ratio` pins (numerator AND denominator branches). Crucially this
includes:
- the input the F2P test fails on FIRST at base_commit, `Rational('1.5','1.5')`
  (`p_den = 2`, `q_den = 2`), and
- the headline `Rational('0.5','100')` (`p_den = 2`, `q_den = 1`).

The gcd reduction that follows (`numbers.py:1653-1657`) is unchanged and
preserves the ratio, so the pre-reduction equality the model pins transfers to
the reduced result the F2P test observes via `as_numer_denom` / `==`.

`str` indexing/iteration is banned in Nagini, so the divisor numerator carrier is
`List[int]` throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (checked by G-AX / axiom_check.py)

### 3.1 `read_int` axiom ↔ textual-integer reader (A-consumed)
**Callee:** the parse of a whole-number digit string to its integer value. In
`Rational.__new__`, a textual divisor reaches `q = Rational(q)`
(`numbers.py:1636`); `Rational(str)` with no second argument parses the string
through `fractions.Fraction(p)` (`numbers.py:1612-1620`) and returns an
`Integer`, whose `.p` is the spelled integer. For an all-digit string this is
exactly `int(str)` and `fractions.Fraction(str).numerator`. The axiom encodes
only the obligation the proof needs: a non-empty **all-digit** sequence reads to
a **non-negative** integer (`Result() >= 0`). The `Requires` is tightened to the
all-digit domain (`48 <= digits[k] <= 57`) so the `Ensures(Result() >= 0)` is
genuinely sound: a leading `'-'` (e.g. `'-5'` → `-5`) is excluded, and so the
non-negativity claim does not over-approximate the real reader on signed/non-digit
inputs.

**Soundness check (G-AX):** `axiom_check.py` runs the real reader
(`fractions.Fraction(s)`) on 12 boundary all-digit strings and 20 000 randomized
all-digit fuzz inputs, asserting `Result() >= 0` (the Ensures) and the exact
value `int(s)`. It ALSO fuzzes the Requires-EXCLUDED boundary (14 inputs: sign,
empty, decimal point, slash, non-digit, whitespace) and confirms that those are
exactly where the real reader returns negative or raises — justifying the tight
precondition. Exit 0 iff sound. Imports only `fractions` (the parser the
constructor uses for a textual operand).

### 3.2 `aux_value` axiom ↔ repeat-then-read value (A-reference)
**Operation:** Python string repetition followed by a single read,
`fractions.Fraction(s * n).numerator`. The pre-patch bug performed `q *= p.q`
while `q` was still the textual divisor — repeating the digit token `p.q` times
before any interpretation, then reading the longer token. The axiom encodes only
that a non-empty all-digit token (`n >= 1`) repeated then read yields a
**non-negative** integer (`Result() >= 0`); its value is deliberately **NOT
pinned** to `n * read_int(digits)`. This is what makes the denominator
postcondition discriminating: the verifier cannot prove an unpinned alternative
reading equals the read-then-scale value, so the prepatch and the wrong impls
fail.

**Leakage note (consumer spec view).** In `model.py`/`model_prepatch.py` this
axiom is named neutrally `aux_value` and its docstring states ONLY that it is an
unspecified non-negative integer-valued function unrelated to `read_int` — it
narrates nothing about repetition. The concrete "repeat-then-read" operation it
stands for is recorded only here (hidden) and in `axiom_check.py`, so the
consumer view leaks no bug→fix mechanism (closing the residual G-LEAK finding).
`model.py`'s proof and postconditions never reference `aux_value`; only
`model_prepatch.py`'s (hidden) impl does.

**Soundness check (G-AX):** `axiom_check.py` asserts `aux_value(s, n) >= 0`
(== `int(s*n)`) on 8 boundary + 5 000 fuzz `(s, n)` inputs, AND confirms the
discriminating arithmetic fact the spec relies on — reading a repeated digit
token differs from scaling the read value:

  `int('100' * 2) = int('100100') = 100100`  ≠  `int('100') * 2 = 200`.

This inequality is the entire bug (`Rational('0.5','100')` yielded `1/100100`
instead of `1/200`); 4530/5000 random witnesses with a non-zero leading digit and
`n >= 2` confirm the readings differ. The spec's denominator clause pins the
*correct* value `p_den * read_int(q_digits)`, against which the repeat-then-read
path provably cannot verify (G-DIFF).
