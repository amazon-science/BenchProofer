## Introduction

Sphinx converts parsed Python abstract-syntax-tree (AST) expression nodes back
into human-readable source strings when it renders things like default argument
values and type annotations in generated documentation. This unparsing is
performed by the AST-to-source visitor in `sphinx/pycode/ast.py` (the
`unparse` entry point and its internal visitor), which has a dedicated handler
for tuple nodes (`visit_Tuple`).

The tuple handler currently distinguishes only two cases: an empty tuple, which
it renders as `()`, and a non-empty tuple, which it renders as its elements
joined by `", "` inside parentheses. This is incorrect for a tuple that has
exactly one element: Python requires a trailing comma to denote a
single-element tuple, so `(1,)` must not be rendered as `(1)` (which is instead
a parenthesized expression, not a tuple). The goal is to make the tuple
unparser produce syntactically faithful output for all three cardinalities —
zero, one, and many elements — while preserving the existing behavior for empty
and multi-element tuples.

## Requirement 1: Faithful rendering of a single-element tuple

**User story:** As a documentation author, I want a one-element tuple in a
default value or annotation to be rendered with its trailing comma, so that the
generated documentation shows valid Python that means a tuple rather than a
parenthesized value.

**Acceptance criteria**
1. WHEN the tuple unparser processes a tuple node that contains exactly one
   element, THEN the visitor SHALL return the rendered element enclosed in
   parentheses and followed by a comma before the closing parenthesis (for
   example, a tuple whose single element renders as `1` SHALL produce `(1,)`).
2. WHEN a single-element tuple is rendered, THEN the visitor SHALL render the
   contained element using the same unparsing it applies to any expression, and
   SHALL place exactly one comma immediately after that rendered element with no
   separating space, and SHALL NOT append a comma after any additional element
   (there being none).
3. The system SHALL NOT render a single-element tuple as its element wrapped in
   parentheses without a trailing comma.

## Requirement 2: Preserve empty and multi-element tuple rendering

**User story:** As a maintainer, I want the previously correct rendering of
empty and multi-element tuples to remain unchanged, so that fixing the
single-element case introduces no regression.

**Acceptance criteria**
1. WHEN the tuple unparser processes a tuple node that contains no elements,
   THEN the visitor SHALL return `()`.
2. WHEN the tuple unparser processes a tuple node that contains two or more
   elements, THEN the visitor SHALL return the rendered elements joined by a
   comma-and-space separator (`, `), enclosed in parentheses, with no trailing
   comma after the final element (for example, a three-element tuple whose
   elements render as `1`, `2`, `3` SHALL produce `(1, 2, 3)`).
3. The system SHALL keep rendering all other expression node kinds — including
   names, attribute access, numeric and string and bytes literals, unary
   operations, lists, sets, dictionaries, subscripts, lambdas, and ellipsis —
   exactly as before, so that only the single-element tuple case changes.
