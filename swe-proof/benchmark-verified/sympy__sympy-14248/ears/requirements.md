# Requirements — Printing differences of matrix expressions

## Introduction

SymPy represents a subtraction `a - b` internally as an addition `a + (-1)*b`.
For ordinary (scalar) expressions the printers already recombine such internal
representations so that the output reads as a subtraction. For matrix
expressions (`MatrixSymbol`, `MatAdd`, `MatMul`, `MatrixElement`) this
recombination was missing, so a matrix difference was rendered with explicit
`(-1)*` / `-1 ` coefficients and stray leading `+` signs. For example
`A - A*B - B` printed as `(-1)*B + (-1)*A*B + A` (string form),
`-B + -A⋅B + A` (pretty form) and `-1 B + -1 A B + A` (LaTeX form) instead of a
clean difference.

This requirement set governs how matrix additions and matrix products carrying a
negative leading coefficient are rendered by the printers in
`sympy/printing/str.py` (`StrPrinter`), `sympy/printing/latex.py`
(`LatexPrinter`) and `sympy/printing/pretty/pretty.py` (`PrettyPrinter`), and —
because the code-generation printers (C, Fortran, JavaScript, Julia, Octave, R)
reuse the string printer's matrix-rendering routines — how those printers render
matrix differences inside a `MatrixElement`. The goal is that a matrix
difference prints as a subtraction, exactly as a scalar difference does, while
every already-correct rendering is preserved.

The affected routines are the ones that render matrix sums and matrix products
in each of these printers.

## Requirement 1: String printer renders matrix sums as differences

**User story:** As a user printing matrix expressions with `str`/`print`, I want
a matrix difference to display with minus signs, so that the output matches the
mathematical intent instead of exposing internal `(-1)` coefficients.

**Acceptance criteria**

1. WHEN the string printer renders a matrix addition whose rendered terms
   include one or more terms that begin with a leading minus sign, THEN the
   printer SHALL join the terms so that each such negative term is written as a
   subtraction (its leading minus retained, joined to the preceding term by
   " - " with single spaces) rather than as an addition of a negated term.
2. WHEN the string printer renders a matrix addition, THEN it SHALL join each
   non-negative term other than the first to the preceding output with " + "
   (a plus surrounded by single spaces).
3. IF the first term of a rendered matrix addition is non-negative, THEN the
   printer SHALL emit it without any leading sign; IF the first term is
   negative, THEN the printer SHALL retain its leading minus sign and emit no
   separate leading plus.
4. WHEN the string printer renders a matrix product whose leading factor is a
   negative number, THEN the printer SHALL factor that sign out and prefix the
   product with a single "-", printing the remaining product with its magnitude
   coefficient, so that a coefficient of exactly -1 disappears entirely (e.g. an
   internally negated matrix symbol renders as just "-" followed by the symbol,
   with no "(-1)*" or "-1*" text).
5. WHEN the string printer renders the problem-statement example `A - A*B - B`
   for matrix symbols `A`, `B`, THEN the result SHALL read as a subtraction with
   the internal `(-1)` coefficients removed — its terms joined per criteria 1–4
   with no `(-1)*` or `-1*` text — rather than the old form
   `(-1)*B + (-1)*A*B + A`.
6. WHEN the string printer renders a matrix addition one of whose terms is a
   parenthesized matrix sum carrying a negative leading coefficient (a
   subtracted grouped sum), THEN that term SHALL be emitted with a single
   leading minus applied to the parenthesized group per criteria 1 and 4, not as
   an added `(-1)*(...)` factor.
7. WHEN the string printer renders a matrix element whose underlying matrix is a
   difference of matrix symbols, THEN the inner matrix expression SHALL be
   rendered as a subtraction per criteria 1–4 (with no `(-1)*` coefficient) and
   the element's index appended in the printer's element-indexing syntax.

## Requirement 2: LaTeX printer renders matrix sums as differences

**User story:** As a user producing LaTeX for matrix expressions, I want matrix
differences to typeset with minus signs, so that formulas read naturally.

**Acceptance criteria**

1. WHEN the LaTeX printer renders a matrix addition whose rendered terms include
   terms beginning with a leading minus, THEN it SHALL emit each such term as a
   subtraction (joined by " - ") and each non-negative subsequent term as an
   addition (joined by " + "), with no leading sign before a non-negative first
   term.
2. WHEN the LaTeX printer renders a matrix product whose leading factor is a
   negative number, THEN it SHALL move that sign to a single leading "-" and
   print the remaining product with its magnitude, so that a leading coefficient
   of -1 produces no visible coefficient.
3. WHEN the LaTeX printer renders a single negated matrix symbol, THEN the
   output SHALL be the symbol name prefixed with exactly one leading `-` and no
   coefficient (i.e. no `-1 ` before the symbol).
4. WHEN the LaTeX printer renders the problem-statement example `A - A*B - B`,
   THEN the output SHALL read as a subtraction whose terms are joined per
   criteria 1–2 with the `(-1)` coefficients removed, rather than the old form
   `-1 B + -1 A B + A`.
5. WHEN the LaTeX printer renders a matrix addition that contains several matrix
   products each carrying a negative leading coefficient, THEN each such product
   SHALL be joined as a subtraction per criteria 1–2 and printed with its sign
   factored to a single leading `-` per criterion 2 (no `-1 ` coefficient on any
   term).
6. WHEN the LaTeX printer renders a matrix element whose underlying matrix is a
   difference of matrix symbols, THEN the inner matrix expression SHALL be
   rendered as a subtraction per criteria 1–2 (with no `-1 ` coefficient),
   wrapped in the printer's parentheses macro and followed by the element's
   subscripted index.

## Requirement 3: Pretty printer renders matrix sums as differences

**User story:** As a user pretty-printing matrix expressions, I want matrix
differences shown with minus signs and no doubled sign artifacts.

**Acceptance criteria**

1. WHEN the pretty printer renders a matrix addition and a subsequent term is
   negative, THEN it SHALL append that term after a single blank-space separator
   while preserving the term's own leading minus, rather than inserting " + "
   before a negated term.
2. WHEN the pretty printer renders a matrix addition and a subsequent term is
   non-negative, THEN it SHALL append that term after a " + " separator.
3. WHEN the pretty printer renders a matrix product with a negative leading
   coefficient of -1, THEN the output SHALL be the product's factors joined in
   order, prefixed with a single leading `-` and no `-1` coefficient.
4. WHEN the pretty printer renders the difference of two matrix symbols, THEN the
   output SHALL show the subtracted term with its own leading minus and the
   remaining term added per criteria 1–2 (no doubled or added `-1` sign).
5. WHEN the pretty printer renders a matrix addition that mixes subtracted matrix
   products with an added matrix product, THEN each subtracted term SHALL be
   appended per criterion 1 (a blank-space separator, the term keeping its own
   leading minus) and each non-negative term per criterion 2 (a " + "
   separator), with no `(-1)` coefficients appearing.

## Requirement 4: Code-generation printers inherit matrix-difference rendering

**User story:** As a user generating code (C, Fortran, JavaScript, Julia,
Octave, R) that references a matrix-expression element, I want a matrix
difference embedded in an element to render without `(-1)` coefficients.

**Acceptance criteria**

1. WHEN any code-generation printer renders a matrix element whose underlying
   matrix is a difference of matrix symbols, THEN the inner matrix expression
   SHALL be rendered as a subtraction per Requirement 1 (with no `(-1)*`
   coefficient), with only the language-specific element-indexing syntax
   differing between printers.
2. The system SHALL keep the matrix-sum and matrix-product rendering of the
   code-generation printers consistent with the string printer's behavior for
   these expressions.

## Requirement 5: Preserve existing correct renderings (regression protection)

**User story:** As a maintainer, I want all matrix and scalar renderings that
were already correct to stay unchanged, so that fixing the difference case
introduces no regressions.

**Acceptance criteria**

1. WHEN any printer renders a matrix product whose leading factor is not a
   negative number (including a positive scalar coefficient times a matrix
   element, such as a positive integer times an element of `A`), THEN the output
   SHALL be byte-for-byte identical to the rendering produced before this change
   — the positive coefficient retained in front of the element and no leading
   minus introduced, in each printer's own coefficient/indexing syntax.
2. WHEN any printer renders a matrix addition all of whose terms are
   non-negative, THEN the terms SHALL be joined with " + " (or the printer's
   established additive separator) and no term SHALL be turned into a
   subtraction.
3. The system SHALL preserve the ordering of terms in a matrix addition and the
   ordering of factors in a matrix product exactly as produced by the
   expression, changing only the sign/joining presentation.
4. The system SHALL leave the rendering of Hadamard products, matrix
   transposes/adjoints, matrix slices, block matrices, and non-matrix (scalar)
   additions and products unchanged.
5. IF a matrix product has a negative leading coefficient other than -1, THEN
   the printer SHALL retain the magnitude of that coefficient after moving the
   sign to the front (the coefficient's absolute value is not dropped).
