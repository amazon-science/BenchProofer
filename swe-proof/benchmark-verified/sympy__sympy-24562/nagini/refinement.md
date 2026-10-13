# refinement.md — sympy__sympy-24562

The operation-by-operation correspondence between `model.py`'s implementation
(the `combine_ratio` impl region and the two axioms `read_int` / `aux_value`)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses the axiom's
`Ensures`, **A-reference** where a value is validated against the real operation
by axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, computes the gold patch's pre-reduction `(numerator, denominator)` on
every input shape the F2P/P2P tests exercise, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The combination block — `Rational.__new__` (`sympy/core/numbers.py:1624-1641`)

Gold hunk (the changed integer accumulation; the new `Q` accumulator replaces
the in-place reuse of `q`):
```
+        Q = 1
         if not isinstance(p, SYMPY_INTS):
             p = Rational(p)
-            q *= p.q
+            Q *= p.q
             p = p.p
         else:
             p = int(p)
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

The block computes the quotient `p / q` of two operands. After parsing, the
dividend `p` is `p.p / p.q` and the divisor `q` is `q.p / q.q`; the constructed
pre-reduction ratio is `(p.p * q.q) / (p.q * q.p)`. The gold patch builds the
denominator in a **fresh accumulator `Q`** (initialized to 1, multiplied by each
denominator factor `p.q` then by the divisor numerator `q.p` / `int(q)`), then
assigns `q = Q`. The pre-patch instead reused the variable `q` itself as the
accumulator (`q *= p.q`, `q = q.p`), so when `q` was supplied as TEXT it was
combined with `p.q` — repeated `p.q` times — before it was ever read as a number.

### Modeled domain (what the spec covers)
The model covers **every input shape the F2P grid and headline exercise**:
- dividend `p` an exact rational `p_num / p_den` with `p_den >= 1` (covers the
  integer dividend `p_den == 1`, e.g. `p = 2`, and the fractional dividend
  `p_den > 1`, e.g. `p = '1.5'` → `3/2`, `p = '0.5'` → `1/2`);
- divisor `q` an exact rational whose numerator is the textual digit token
  `q_digits` (read by `read_int`) and whose denominator is `q_den >= 1` (covers
  the whole-number divisor `q_den == 1`, e.g. `q = '100'`, and the fractional
  divisor `q_den > 1`, e.g. `q = '1.5'` → `3/2`).

This is the widened domain: the input on which the F2P test fails FIRST at
base_commit — `Rational('1.5','1.5')` (fractional dividend AND fractional
divisor) — has shape `p_den = 2, q_den = 2`, which lies squarely inside the
modeled domain, and so does the headline `Rational('0.5','100')`
(`p_den = 2, q_den = 1`).

| # | model.py impl op (`combine_ratio`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `p_num, p_den` | `p.p`, `p.q` after `p = Rational(p)` | R | the dividend's numerator/denominator are ints: `p_num ↔ p.p`, `p_den ↔ p.q` (mapping.md §2). |
| A2 | param `q_digits: List[int]` | the textual divisor numerator (a digit `str`) read at `q = Rational(q)` | R | `str` of digits ↔ `List[int]` of digit code points (mapping.md §2). |
| A3 | param `q_den` | `q.q` after `q = Rational(q)` (the divisor's denominator) | R | `q_den ↔ q.q`; for a whole-number divisor `q_den == 1` (mapping.md §2). |
| A4 | `q_value = read_int(ToSeq(q_digits))` | `q.p` after `q = Rational(q)` (the integer the divisor's numerator spells) | A-consumed | `read_int` is the weakest contract on the unchanged textual-integer reader the proof needs (non-empty all-digit token ⇒ non-negative integer); its value stands for `q.p` (mapping.md §3.1). G-AX confirms it against the real `fractions.Fraction(s)`. |
| A5 | `out_num = p_num * q_den` | the final numerator: `p = p.p`, then `p *= q.q` (unchanged in both patches) | I + R | the numerator picks up the divisor's denominator `q.q` (`= q_den`); `p.p * q.q ↔ p_num * q_den`. |
| A6 | `out_den = p_den * q_value` | the final denominator `Q`: `Q = 1`, `Q *= p.q` (= `p_den`), `Q *= q.p` (= `read_int`); `q = Q` | I | the denominator accumulates `p.q * q.p == p_den * read_int(q_digits)` by ordinary integer multiplication, in a fresh accumulator. The model writes the product directly; the patch multiplies `Q` (initialized to 1) by each factor. Same integer arithmetic, same value. |
| A7 | return `(out_num, out_den)` | the `(p, q)` pair carried into gcd reduction (`numbers.py:1642+`) | R + I | the constructed pre-reduction `(numerator, denominator)`; the subsequent gcd reduction is unchanged and ratio-preserving, so the pinned pre-reduction equality transfers to the reduced result the F2P test reads via `as_numer_denom` / `==` (mapping.md §2). |

## B. The discriminating content — why every wrong impl is rejected

The single FAIL_TO_PASS `test_issue_24543` runs a 9-cell grid
`for p,q in ('1.5',1.5,2)²` THEN the headline `Rational('0.5','100') ==
Rational(1,200)`. At base_commit the bug manifests on exactly the **string
divisor** cells:
- `Rational('1.5','1.5')` and `Rational(1.5,'1.5')` **raise** `TypeError`
  (`'1.5'` repeated 2× = `'1.51.5'`, an invalid literal) — these are the cells
  that fail FIRST;
- the headline `Rational('0.5','100')` returns `1/100100` instead of `1/200`
  (`'100'` repeated 2× = `'100100'`).

Both share one root cause: the divisor's textual numerator is **read as a number
exactly once** vs. **first repeated and then read**. The spec pins the
denominator to `p_den * read_int(q_digits)` (read-then-scale, A6). The two readings
are modeled by two distinct axioms:
- `read_int(q_digits)` — read the token once (A-consumed, A4);
- `aux_value(q_digits, n)` — the value the alternative reading obtains from the
  longer token formed by repeating `q_digits` `n` times; its value is **left
  unpinned** (axiom Ensures only `>= 0`), and in general
  `aux_value(s, n) != n * read_int(s)`. In the consumer spec view this axiom is
  named neutrally and its docstring narrates none of the above mechanism (the
  repeat-then-read meaning lives only in mapping.md / axiom_check.py, hidden);
  `model.py` never references it, so the spec view leaks no bug→fix mechanism.

`model_prepatch.py` reproduces the pre-patch denominator
`aux_value(ToSeq(q_digits), p_den)` and **fails** the postcondition
`Result()[1] == p_den * read_int(ToSeq(q_digits))` (G-DIFF): the verifier cannot
prove an unpinned alternative reading equals the read-then-scale value.

The widened spec additionally pins the **numerator** to `p_num * q_den` (A5), so
an impl that drops the `q_den` factor for fractional divisors — the verdict's
counterexample, which the OLD narrow spec admitted — no longer verifies. Seven
same-spec wrong impls were checked with `adversary weakness`; NONE is a
candidate counterexample (each verification fails on the named clause):
- atk_1 (verdict counterexample): numerator omits `q_den` → fails A5
  (`Result()[0] == p_num * q_den`);
- atk_2 (the prepatch bug): denominator uses the unpinned `aux_value` → fails A6
  (`Result()[1] == p_den * read_int(...)`);
- atk_3: numerator/denominator factors swapped → fails A5;
- atk_4: denominator drops `p_den` → fails A6;
- atk_5: denominator ignores the divisor value (uses `q_den`) → fails A6;
- atk_6: numerator uses the read value instead of `q_den` → fails A5;
- atk_7: denominator uses `q_den` in place of the read value → fails A6.
A structurally-different CORRECT impl (denominator accumulated in the other
order, token read before the numerator is formed) still verifies — proving the
spec is non-vacuous.

## C. Scope and no kind-3 steps

Every step above is R, A, or I. The one operation that genuinely *changed* —
accumulating the denominator in a fresh variable instead of reusing the variable
holding the divisor's textual numerator — is captured by the contrast between
the verified direct product `p_den * read_int(q_digits)` (model, read-then-scale)
and the unpinned `aux_value(q_digits, p_den)` (prepatch, repeat-then-read);
no `@ContractOnly` axiom stands in for the changed accumulation. The numerator
operation `p *= q.q` is unchanged by the gold patch and is modeled identically
(A5) in both twins.

## D. verify(model) ⇒ resolved

`combine_ratio` verifies only if (i) the numerator is `p_num * q_den` (A5),
(ii) the denominator is `p_den * read_int(q_digits)` — the divisor's textual
numerator read exactly once and scaled by the dividend's denominator (A4, A6) —
and (iii) the call terminates: the precondition carries a
`MustTerminate(1)` obligation, so Nagini's obligation calculus rejects any
diverging body (a frozen loop, or an unconditional self-call, which would leak
the caller's unsatisfied obligation). This closes the partial-correctness hole
where a non-returning implementation discharges the value postconditions
vacuously; the real combination block is straight-line integer arithmetic and
trivially terminates.
By R (resolved-ratio ints ↔ `p.p`/`p.q`/`q.q`, digit `str` ↔ `List[int]`,
pre-reduction pair ↔ `(p, Q)`) and the ratio-preserving unchanged gcd reduction
(A7), the verified combination equals the gold patch's `Q`-accumulator
computation on EVERY F2P/P2P input shape, including the first-failing
`Rational('1.5','1.5')` and the headline `Rational('0.5','100')`. By G-AX the
`read_int` axiom (A-consumed) over-approximates the real reader on its tightened
all-digit domain and the `aux_value` axiom (A-reference) is sound and genuinely
distinct from read-then-scale. Therefore a model satisfying this spec, refined by
the map above, computes the gold patch's `(numerator, denominator)`; the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
