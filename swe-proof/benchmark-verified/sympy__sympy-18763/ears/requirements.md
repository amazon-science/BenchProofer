# Requirements: LaTeX rendering of substitution (`Subs`) expressions

## Introduction

SymPy's LaTeX printer renders a `Subs` object — an unevaluated substitution of
one or more symbols by values into a body expression — as a "restriction" form:
the body expression displayed with a vertical bar carrying the assignments as a
stacked subscript. This behavior lives in the `Subs` handler of the LaTeX
printer (`_print_Subs` in `sympy/printing/latex.py`), reached via
`sympy.printing.latex.latex(...)` and the `latex` string form of a `Subs`
object.

The current rendering emits the body expression bare, with no delimiters around
it. When the `Subs` object is itself a subterm of a larger expression (for
example a coefficient multiplying it), the un-delimited body visually merges
with the surrounding operators, producing an ambiguous and mathematically
misleading result (e.g. `3` multiplied by a substitution of `-x + y` reads as
though only part of the sum is inside the restriction). The goal is to always
present the body as a self-contained parenthesized group so the restricted
quantity reads as a single unit regardless of its surrounding context, while
preserving every other aspect of the existing rendering.

## Requirement 1: Parenthesize the body of a substitution rendering

**User story:** As a user printing a `Subs` expression to LaTeX, I want the
substituted body to be wrapped in visible parentheses, so that the restricted
quantity is unambiguous even when the substitution is embedded in a larger
expression.

**Acceptance criteria**

1. WHEN the LaTeX printer renders a `Subs` object, THEN the printer SHALL emit
   the rendered body expression enclosed in a LaTeX-sized parenthesis group,
   i.e. delimited on the left by `\left(` and on the right by `\right)`.
2. WHEN the LaTeX printer renders a `Subs` object, THEN the printer SHALL place
   that parenthesized body as the quantity to the left of the restriction bar,
   inside the overall `\left. ... \right|_{\substack{ ... }}` layout, so that
   the complete output has the shape
   `\left. \left(<body>\right) \right|_{\substack{ <assignments> }}`.
3. The body group SHALL be inserted whether the body is an atomic term or a
   compound expression (such as a sum), so the delimiters are always present
   regardless of the body's structure.
4. WHEN a `Subs` object appears as a factor within a larger product (for
   example a numeric coefficient times the substitution), THEN the resulting
   LaTeX SHALL keep the parentheses around the substituted body so that the
   coefficient applies to the whole restricted quantity rather than merging
   with part of the body.

## Requirement 2: Preserve the existing restriction layout and assignment list

**User story:** As a user who relies on the established LaTeX form of `Subs`, I
want everything other than the new body parentheses to remain exactly as before,
so that existing output and downstream rendering are not disturbed.

**Acceptance criteria**

1. The printer SHALL continue to render the outer restriction using the
   left-dot / right-bar construction with a stacked subscript, i.e.
   `\left. ... \right|_{\substack{ ... }}`.
2. WHEN a `Subs` object has one or more `(old, new)` assignment pairs, THEN the
   printer SHALL render each pair as the LaTeX of the old symbol, followed by an
   equals sign, followed by the LaTeX of the new value, pairing old symbols with
   new values in order.
3. WHEN there are two or more assignment pairs, THEN the printer SHALL separate
   consecutive rendered pairs with the existing stacked line-break separator
   (two backslashes followed by a space) inside the subscript.
4. The printer SHALL render the body expression, each old symbol, and each new
   value using the printer's normal recursive LaTeX rendering, applying no
   additional wrapping to them beyond the body parentheses required by
   Requirement 1.
5. The single space characters surrounding the parenthesized body and the
   assignment list within the layout SHALL be preserved exactly as in the
   established output, so that a substitution with a single assignment renders
   with the body group between the left-dot and right-bar and the lone
   assignment shown in the subscript.
