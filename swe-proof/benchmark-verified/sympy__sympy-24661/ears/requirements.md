# Requirements: Honor `evaluate=False` for relational expressions in `parse_expr`

## Introduction

`sympy.parsing.sympy_parser.parse_expr(s, ..., evaluate=False)` parses a string
into a SymPy expression while suppressing SymPy's automatic evaluation, so that
the parsed result reflects the written structure rather than a simplified value.
Internally, when `evaluate=False` is requested, the parser rewrites the parsed
Python AST with `EvaluateFalseTransformer` (in
`sympy/parsing/sympy_parser.py`), which replaces operators with their SymPy
constructors and forces `evaluate=False` on them.

The defect: `EvaluateFalseTransformer` handled arithmetic operators but not
comparison (relational) operators. As a result, a comparison such as
`parse_expr('1 < 2', evaluate=False)` was still evaluated by Python/SymPy down
to a truth value (`True`) instead of being returned as the held, unevaluated
symbolic relation `Lt(1, 2, evaluate=False)` (which displays as `1 < 2`). The
same problem affected `<`, `<=`, `>`, `>=`, `==`, and `!=`.

The goal is that when `evaluate=False` is in effect, `parse_expr` turns a
comparison expression into the corresponding SymPy relational object held in
unevaluated form, mirroring the treatment already given to arithmetic
operators, while leaving all other parsing behavior unchanged. The affected
module is `sympy/parsing/sympy_parser.py`; the behavior is observed through the
public `parse_expr` function.

## Requirement 1: Relational expressions are held unevaluated under `evaluate=False`

**User story:** As a user parsing an expression string with `evaluate=False`, I
want a comparison to be returned as a symbolic relational object rather than a
computed truth value, so that the parsed result preserves the written relation.

**Acceptance criteria**

1. WHEN `parse_expr` is called with `evaluate=False` on a string whose top-level
   expression is a `<` comparison of two operands, THEN `parse_expr` SHALL
   return the SymPy `Lt` relational applied to the two parsed operands and held
   unevaluated (equal to `Lt(left, right, evaluate=False)`), not a truth value.
2. WHEN `parse_expr` is called with `evaluate=False` on a `<=` comparison, THEN
   `parse_expr` SHALL return the unevaluated `Le` relational of the two parsed
   operands (equal to `Le(left, right, evaluate=False)`).
3. WHEN `parse_expr` is called with `evaluate=False` on a `>` comparison, THEN
   `parse_expr` SHALL return the unevaluated `Gt` relational of the two parsed
   operands (equal to `Gt(left, right, evaluate=False)`).
4. WHEN `parse_expr` is called with `evaluate=False` on a `>=` comparison, THEN
   `parse_expr` SHALL return the unevaluated `Ge` relational of the two parsed
   operands (equal to `Ge(left, right, evaluate=False)`).
5. WHEN `parse_expr` is called with `evaluate=False` on an `==` comparison, THEN
   `parse_expr` SHALL return the unevaluated `Eq` relational of the two parsed
   operands (equal to `Eq(left, right, evaluate=False)`).
6. WHEN `parse_expr` is called with `evaluate=False` on a `!=` comparison, THEN
   `parse_expr` SHALL return the unevaluated `Ne` relational of the two parsed
   operands (equal to `Ne(left, right, evaluate=False)`).
7. WHEN a comparison is parsed under `evaluate=False`, THEN the produced
   relational SHALL remain a symbolic relational object (a `Rel` instance) and
   SHALL NOT be collapsed to a Boolean truth value even when both operands are
   concrete numbers whose relation is decidable.

## Requirement 2: Correct operator-to-relational mapping and operand order

**User story:** As a user, I want each comparison operator mapped to its
matching relational class with operands in the written order, so that the
parsed relation means what the source string says.

**Acceptance criteria**

1. The system SHALL map each supported comparison operator to its corresponding
   SymPy relational constructor: `<` to `Lt`, `<=` to `Le`, `>` to `Gt`, `>=`
   to `Ge`, `==` to `Eq`, and `!=` to `Ne`.
2. WHEN a comparison written as `A op B` is rewritten, THEN the system SHALL
   apply the relational constructor with the left-hand operand first and the
   right-hand operand second, preserving the written order.
3. WHEN either operand of a comparison is itself a compound sub-expression,
   THEN the system SHALL parse and rewrite that operand under the same
   `evaluate=False` regime before placing it into the relational, so that
   nested arithmetic within an operand is likewise held unevaluated.

## Requirement 3: Existing non-relational parsing behavior is preserved

**User story:** As an existing user, I want all previously working parsing
behavior to remain unchanged, so that adding relational handling does not
regress arithmetic parsing or default evaluation.

**Acceptance criteria**

1. The system SHALL keep parsing arithmetic expressions (for example addition,
   multiplication, and exponentiation) under `evaluate=False` as held,
   unevaluated SymPy expressions, exactly as before.
2. WHEN `parse_expr` is called with the default `evaluate=True` on a comparison
   of two concrete numbers, THEN the system SHALL continue to produce the
   evaluated result (the truth value / evaluated relational) as it did
   previously, so that only the `evaluate=False` path is changed.
3. WHEN `parse_expr` parses a string that contains no comparison operator, THEN
   the system SHALL return the same result as before this change for both
   `evaluate=True` and `evaluate=False`.
4. The system SHALL leave the parsing of non-comparison Python constructs
   (function calls, names, and numeric/other literals) unchanged when rewriting
   an expression under `evaluate=False`.
