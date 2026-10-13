# Requirements: correct denominator bracketing when string-printing products with reciprocal factors

## Introduction

When SymPy renders a multiplication (`Mul`) to its plain-text string form, the
string printer splits the product into a numerator part and a denominator part
and joins them with `/`. Denominator factors arise from commutative power
factors with a negative exponent (a reciprocal such as `1/base`). For a bare
reciprocal factor (exponent exactly `-1`), the printer emits the base's own
rendered fragment on the right-hand side of the division; when that base is
itself a compound expression, the fragment must be wrapped in an extra pair of
parentheses so the division binds correctly.

The affected code is the `Mul` printing path of the plain string printer —
`StrPrinter._print_Mul` in `sympy/printing/str.py`. Before the fix, the extra
parentheses were added only when the reciprocal factor's base was itself a
product (a `Mul`). A base that is itself a compound power — for example the
reciprocal of a single symbol, which is represented as a `Pow` — was left
unbracketed, so a product of a factor with such a reciprocal-of-a-reciprocal
printed as a chain of two divisions (which reassociates as
`(numerator / 1) / base`) instead of grouping the reciprocated base in its own
parentheses. This is the publicly reported symptom in which a fraction placed
over another fraction rendered as chained `/` operators, dropping the
denominator's parentheses and thereby changing the meaning of the expression.
The goal is to place the surrounding parentheses whenever the base of such a
denominator factor is a multi-component compound expression — whether a product
**or** a power — while leaving all previously correct output unchanged.

The observable surface is the string produced by `str(...)` / `sstr(...)` for
`Mul` expressions (including unevaluated `Mul`/`Pow` built with
`evaluate=False`).

## Requirement 1: Bracket a reciprocal denominator factor whose base is a compound power

**User story:** As a user printing an unevaluated product that contains a
reciprocal of a fraction, I want the reciprocated sub-expression to be wrapped
in parentheses in the string output, so that the printed expression preserves
the intended grouping of the division.

**Acceptance criteria**

1. WHEN `str(...)` is applied to a `Mul` that contains a commutative reciprocal
   factor (a `Pow` with exponent exactly `-1`) whose base is itself a
   multi-component power expression (a `Pow` having more than one argument, such
   as a reciprocal of a symbol), THEN the string printer SHALL surround that
   base's rendered fragment with a single pair of parentheses in the denominator
   position of the output.
2. WHEN a reciprocal denominator factor's base is itself a reciprocal (a nested
   "one over a compound") such that its fragment would otherwise be spliced
   directly after the division operator, THEN the printer SHALL enclose that
   base fragment in exactly one pair of parentheses — so the nested division is
   grouped explicitly rather than collapsing into two chained `/` operators that
   reassociate and change the meaning.
3. IF a reciprocal denominator factor's base is a compound expression that would
   otherwise render as several `/`- or `*`-joined terms spliced directly after
   the division operator, THEN the printer SHALL parenthesize that base's
   fragment so the printed division does not silently reassociate.

## Requirement 2: Preserve bracketing for reciprocal factors whose base is a product

**User story:** As a user relying on existing correct output, I want products in
the denominator to keep their parentheses, so that previously correct printing
is not regressed by the new behavior.

**Acceptance criteria**

1. WHEN `str(...)` is applied to a `Mul` containing a commutative reciprocal
   factor (a `Pow` with exponent exactly `-1`) whose base is a multi-component
   product (a `Mul` with more than one argument), THEN the printer SHALL
   surround that base's rendered fragment with a single pair of parentheses.
2. WHEN such a reciprocal-of-a-product denominator factor appears in a product
   that also carries a leading numeric coefficient or overall sign, THEN the
   printer SHALL render the sign and coefficient as a prefix, join with a single
   `/`, and still enclose the multi-component product base in exactly one pair of
   parentheses (rather than leaving those factors to reassociate outside the
   division) — the coefficient and sign do not affect the base's bracketing.

## Requirement 3: Do not add parentheses to simple (single-component) reciprocal bases

**User story:** As a user printing ordinary fractions, I want simple
denominators to stay unparenthesized, so that everyday output remains clean and
unchanged.

**Acceptance criteria**

1. IF a reciprocal denominator factor's base is an atom or otherwise has only a
   single component (its argument count is one, e.g. a lone symbol), THEN the
   printer SHALL emit that base's fragment WITHOUT adding an extra surrounding
   pair of parentheses.
2. WHEN `str(...)` is applied to a simple quotient such as one symbol divided by
   another (a reciprocal whose base is a single symbol), THEN the printer SHALL
   render it as the two fragments joined by a single `/` with no added
   parentheses (for example, `x` over `y` prints as `x/y`).
3. The system SHALL restrict the extra-bracketing decision to reciprocal factors
   whose base is a compound product or compound power, and SHALL NOT wrap the
   fragments of denominator factors of any other kind solely on account of this
   rule.

## Requirement 4: Preserve all other Mul string-printing behavior

**User story:** As a user of the string printer across many expression kinds, I
want unrelated `Mul` printing to be unchanged, so that only the compound-power
denominator case is affected.

**Acceptance criteria**

1. The system SHALL keep the existing numerator/denominator split of a product:
   factors with negative exponents SHALL be rendered in the denominator and the
   remaining factors in the numerator.
2. WHEN a product has exactly one denominator factor, THEN the printer SHALL
   join the numerator and that single factor with one `/` (adding the extra
   parentheses only when required by Requirements 1–2).
3. WHEN a product has more than one denominator factor, THEN the printer SHALL
   render the denominator as those factors joined by `*` and enclosed in one
   surrounding pair of parentheses.
4. WHEN a product has an overall negative leading coefficient, THEN the printer
   SHALL prefix the output with a single `-` sign and render the remaining
   magnitude as above.
5. WHEN a reciprocal factor has an exponent that is negative but not exactly
   `-1`, THEN the printer SHALL render it as a power with the corresponding
   positive exponent in the denominator, unaffected by the extra-bracketing rule
   of Requirements 1–3.
