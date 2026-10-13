# Requirements — corrected rendering of tuple expressions in unparsed signatures

## Introduction

Sphinx's `autodoc` extension renders Python signatures (default argument
values, type annotations) by turning parsed expression syntax trees back into
source-like text. This "unparsing" is performed by the cut-down visitor
`_UnparseVisitor` in the module `sphinx/pycode/ast.py` (exposed through the
module-level `unparse` helper).

A tuple used as a default argument value is rendered incorrectly: a class
method declared as

    def add_lines(self, lines, color=(1, 1, 1), width=5, label=None, name=None):

is rendered with the parentheses stripped from the tuple —
`add_lines(lines, color=1, 1, 1, width=5, ...)` — which is misleading and, for
a multi-element default, syntactically ambiguous. The expected rendering keeps
the parentheses: `color=(1, 1, 1)`.

The goal is to make the unparser reproduce a non-empty tuple expression with
its surrounding parentheses, while preserving the existing (parenthesis-free)
rendering of a comma-separated index inside a subscription such as
`Tuple[int, int]`, and without changing how any other expression form is
rendered. The affected behavior lives in the tuple-rendering and
subscription-rendering methods of `_UnparseVisitor`.

## Requirement 1: Parenthesized rendering of tuple expressions

**User story:** As a developer reading generated API documentation, I want a
tuple-valued default argument or annotation to be rendered with its
parentheses, so that the displayed signature is unambiguous and matches the
source.

**Acceptance criteria**
1. WHEN `unparse` renders a tuple expression that has one or more elements,
   THEN the module SHALL produce the elements joined by `", "` and enclosed in
   a leading `(` and a trailing `)` (for example the expression `(1, 2, 3)`
   SHALL render as the text `(1, 2, 3)`).
2. WHEN `unparse` renders a tuple expression that has exactly one element,
   THEN the module SHALL still enclose that single element in parentheses.
3. WHEN `unparse` renders an empty tuple expression, THEN the module SHALL
   produce the text `()`.
4. The system SHALL preserve `", "` (comma followed by a single space) as the
   separator between the rendered elements of a tuple.
5. WHEN a tuple expression appears as a default argument value in a rendered
   function or method signature, THEN the rendered default SHALL show the tuple
   with its enclosing parentheses (for example `color=(1, 1, 1)`).

## Requirement 2: Comma-separated subscription index stays unparenthesized

**User story:** As a developer relying on rendered type annotations, I want a
subscription whose index is a comma-separated group (such as `Tuple[int, int]`)
to keep rendering its members directly inside the square brackets, so that the
parenthesizing of standalone tuples does not corrupt subscription rendering.

**Acceptance criteria**
1. WHEN `unparse` renders a subscription whose index is a non-empty
   comma-separated group that contains no unpacking (starred) member, THEN the
   module SHALL render the index members joined by `", "` placed directly
   between the `[` and `]` of the subscription, WITHOUT any parentheses around
   the group (for example `Tuple[int, int]` SHALL render as the text
   `Tuple[int, int]`, not `Tuple[(int, int)]`).
2. WHILE the parenthesized tuple rendering of Requirement 1 is in effect, the
   system SHALL still produce the unparenthesized subscription-index form
   described in criterion 1 for such subscriptions.
3. IF a subscription index is any form other than a non-empty comma-separated
   group without unpacking (for example a single value, a slice, an empty
   group, or a group containing an unpacking member), THEN the module SHALL
   render the index by its own ordinary rendering placed between the `[` and
   `]` (for example `a[b]` SHALL render as `a[b]`).
4. The system SHALL produce the identical subscription rendering regardless of
   whether the interpreter represents the index directly or wraps it in an
   index-node container, so that behavior does not differ across supported
   Python versions.

## Requirement 3: All other expression renderings are preserved

**User story:** As a maintainer, I want every expression form other than the
tuple and comma-group-subscription cases addressed above to render exactly as
it did before this change, so that fixing the tuple rendering does not regress
any other rendered signature.

**Acceptance criteria**
1. WHEN `unparse` renders an expression that is neither a non-empty tuple
   expression (Requirement 1) nor a subscription of the forms addressed in
   Requirement 2, THEN the module SHALL produce exactly the same text as the
   pre-change implementation produced for that expression — the rendering of
   every such form SHALL be left unchanged.
2. The system SHALL leave unchanged the rendering of atomic expression forms —
   names, attribute accesses, numeric/string/bytes/ellipsis literals, and the
   boolean and none singleton constants — producing the same output as the
   pre-change implementation.
3. The system SHALL leave unchanged the rendering of the container display
   forms (list, set, and dictionary displays) and of call expressions,
   producing the same output as the pre-change implementation.
4. The system SHALL leave unchanged the rendering of unary operations and of
   lambda expressions, producing the same output as the pre-change
   implementation.
5. WHEN `unparse` is given no node (a null input), THEN the module SHALL
   return no rendering (a null result) rather than a string, exactly as the
   pre-change implementation did.
6. The system SHALL produce these unchanged renderings identically on every
   supported Python version, regardless of internal syntax-tree
   representation differences between versions.
