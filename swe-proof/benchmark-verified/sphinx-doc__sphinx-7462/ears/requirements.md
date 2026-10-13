# Requirements: Empty tuple type annotations must render without crashing

## Introduction

Sphinx renders Python type annotations in two independent places:

* `sphinx/domains/python.py` — the module-level `_parse_annotation(annotation)`
  helper contains an inner recursive `unparse(node)` that turns a parsed
  annotation AST into a list of inline documentation nodes (the display form
  used in signatures).
* `sphinx/pycode/ast.py` — the module-level `unparse(node)` function that turns
  a parsed AST back into its Python source-text string form.

Both functions handle tuple AST nodes by assembling the already-rendered pieces
of the tuple's elements. Neither one handled the *empty* tuple, which arises
from the valid annotation `Tuple[()]` (the empty-tuple type). In the
display-node renderer, the empty case dropped a non-existent trailing separator
and raised `IndexError: pop from empty list`, crashing the documentation build.
In the source-text renderer, the empty case produced an empty string instead of
the expected `()` literal.

The goal is that an empty tuple annotation is rendered as an explicit pair of
parentheses by both renderers, that documentation builds no longer crash on it,
and that all previously-supported annotation forms continue to render exactly
as before.

## Requirement 1: Display-node renderer handles the empty tuple

**User story:** As a user documenting a function annotated with the empty-tuple
type `Tuple[()]`, I want Sphinx to render the annotation instead of crashing, so
that my documentation build succeeds.

**Acceptance criteria**

1. WHEN the inner `unparse` in `sphinx/domains/python.py :: _parse_annotation`
   processes a tuple AST node that has no elements, THEN it SHALL return a
   sequence consisting of exactly an opening-parenthesis punctuation node
   followed by a closing-parenthesis punctuation node (rendering as `()`).
2. WHEN a tuple AST node with no elements is rendered, THEN the renderer SHALL
   NOT raise `IndexError` (or any other exception) and SHALL NOT attempt to
   remove a trailing separator that is not present.
3. WHEN `_parse_annotation` parses an annotation whose text is the empty-tuple
   form `Tuple[()]`, THEN the resulting node sequence SHALL contain the class
   reference `Tuple`, an opening square bracket, an opening parenthesis, a
   closing parenthesis, and a closing square bracket, in that order, so that the
   annotation renders as `Tuple[()]`.

## Requirement 2: Source-text renderer handles the empty tuple

**User story:** As a developer relying on Sphinx's AST-to-source renderer, I
want an empty tuple to be rendered as `()`, so that the produced source text is
valid and unambiguous.

**Acceptance criteria**

1. WHEN `sphinx/pycode/ast.py :: unparse` processes a tuple AST node that has no
   elements, THEN it SHALL return the literal string `()`.
2. The system SHALL NOT return an empty string for an empty tuple node.

## Requirement 3: Non-empty tuples and all other forms keep their behavior

**User story:** As an existing Sphinx user, I want every annotation form that
already worked to keep rendering identically, so that the empty-tuple fix
introduces no regression.

**Acceptance criteria**

1. WHEN the display-node `unparse` processes a tuple AST node with one or more
   elements, THEN it SHALL render each element in order, separated by a `, `
   separator, with no trailing separator after the final element.
2. WHEN the source-text `unparse` processes a tuple AST node with one or more
   elements, THEN it SHALL render the elements joined by `, ` (comma followed by
   a single space), unchanged from prior behavior — e.g. a two-element tuple of
   `int` and `int` renders as `int, int`.
3. The source-text `unparse` SHALL continue to render every other supported AST
   node form unchanged, including names, dotted attribute paths, subscripts
   (e.g. `Tuple[int, int]`), lists, sets, dicts, numeric and string and bytes
   literals, `...` (ellipsis), `None`, boolean/unary/binary operator
   expressions, lambda expressions, and call expressions.
4. The display-node `unparse` SHALL continue to render every other supported
   annotation form unchanged, including plain and dotted names as cross
   references, subscripted generics, and bracketed lists.
5. WHEN a tuple's elements are rendered by either renderer, THEN each element
   SHALL be produced by the existing per-element rendering recursion unchanged;
   only the assembly of the elements into the final tuple form is affected by
   this change.
