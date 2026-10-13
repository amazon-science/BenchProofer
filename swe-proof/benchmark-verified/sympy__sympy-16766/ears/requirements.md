# Requirements: Python code printing for indexed array-access expressions

## Introduction

SymPy's Python code printer (`PythonCodePrinter` / `AbstractPythonCodePrinter`
in `sympy/printing/pycode.py`, exercised through the `pycode()` helper and by
`lambdify`) converts symbolic expressions into strings of runnable Python
source. Symbolic array element access — an `IndexedBase` subscripted with one
or more indices, producing an `Indexed` expression (from `sympy.tensor`) — has
no dedicated print method on the printer. As a result the printer falls back to
its "unsupported node" path and emits a commented warning block
(`# Not supported in Python:` / `# Indexed`) ahead of the printed text.

The goal is to make the Python code printer render indexed array access as
idiomatic Python subscription (e.g. `p[0]`, `p[0, 1]`) with no unsupported
warning, so that code generated for such expressions is clean and directly
usable. Existing behavior of the printer for all other expression types must be
preserved.

## Requirement 1: Print indexed array access as Python subscription

**User story:** As a user generating Python source from symbolic expressions
(directly via `pycode()`/`PythonCodePrinter` or through `lambdify`), I want
indexed array-access expressions to be rendered as ordinary Python subscript
syntax, so that the generated code is valid, readable, and free of "unsupported"
warnings.

**Acceptance criteria**

1. WHEN the Python code printer is asked to print an indexed array-access
   expression (an `IndexedBase` object subscripted to yield an `Indexed`
   expression), THEN the printer SHALL return a string of the form
   `<base>[<indices>]`, where `<base>` is the string form of the indexed base
   and `<indices>` is the comma-and-space–separated list of the printed indices.
2. WHEN an indexed expression has a single index, THEN the printer SHALL render
   it as the base followed by that one index in square brackets (for example, a
   base `p` indexed by `0` SHALL be printed as `p[0]`).
3. WHEN an indexed expression has two or more indices, THEN the printer SHALL
   render every index, in their given order, separated by a comma followed by a
   single space, inside one pair of square brackets (for example, a base `p`
   indexed by `0` and `1` SHALL be printed as `p[0, 1]`).
4. The printer SHALL print each index by applying its normal per-expression
   printing to that index, so that non-trivial index expressions are rendered
   exactly as they would be when printed on their own.
5. WHEN an indexed array-access expression is printed, THEN the printer SHALL
   NOT emit any "not supported" comment or warning text for that expression.

## Requirement 2: Add indexed-access support without regressing other expressions

**User story:** As a maintainer relying on the Python code printers, I want the
addition of indexed-access printing to leave the output for every other kind of
expression exactly as it was, so that no previously supported behavior
regresses.

**Acceptance criteria**

1. WHEN the base Python code printer, or any of its specialized variants, is
   asked to print an expression that is not an indexed array-access expression,
   THEN it SHALL return exactly the same string it returned before
   indexed-access printing was added.
2. The change SHALL consist solely of adding support for printing indexed
   array-access expressions; it SHALL NOT alter the printed output of any other
   expression type, operator, printer variant, or code construct that the
   printers already handled.
