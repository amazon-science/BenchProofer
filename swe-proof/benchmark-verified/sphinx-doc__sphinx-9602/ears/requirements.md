# Requirements: constant values in `Literal` type annotations must not be cross-referenced

## Introduction

Sphinx's Python domain renders textual type annotations into a sequence of
inline documentation nodes for display in signatures and descriptions. The
routine responsible is the annotation parser in `sphinx/domains/python.py`
(the `_parse_annotation` helper and its nested `unparse` walker), which turns a
parsed annotation into cross-reference nodes for type names, punctuation nodes
for brackets and separators, and text nodes for other content.

When an annotation contains a `Literal[...]` (or `typing.Literal[...]`)
parametrised type, its arguments are concrete constant *values* (for example
`True`, `False`, an integer, or a string), not type names. The current renderer
treats every leaf inside the annotation as a type name and emits a cross
reference for it. With nitpicky mode enabled (`-n -W`), those references resolve
against no such class (e.g. `True` is not a class), so the documentation build
fails with a missing-reference warning.

The goal is to render the arguments of a `Literal` annotation as plain display
text carrying each value's canonical source representation, so they are shown
verbatim and are never turned into cross references — while every other kind of
annotation continues to render exactly as before.

## Requirement 1: `Literal` argument values render as plain text, not cross references

**User story:** As a documentation author using `Literal[...]` in type
annotations with nitpicky mode, I want the literal values to appear as plain
text rather than as type cross references, so that my `-n -W` build does not
fail with spurious missing-class warnings.

**Acceptance criteria**

1. WHEN the annotation parser renders a parametrised type whose head name is
   exactly `Literal` or `typing.Literal`, THEN the annotation parser SHALL emit
   each constant argument as a plain inline text node and SHALL NOT emit a
   pending cross-reference node for that argument.
2. WHEN a `Literal`/`typing.Literal` argument is rendered as text, THEN the
   annotation parser SHALL use the value's canonical source representation as
   the text content: a boolean SHALL render as `True` or `False`, an integer
   SHALL render as its decimal digits, and a string SHALL render as its
   single-quoted form including the surrounding quote characters.
3. WHEN a `Literal`/`typing.Literal` type is rendered, THEN the annotation
   parser SHALL emit the head name as a cross-reference node, followed by an
   opening-bracket punctuation node, the argument nodes, and a closing-bracket
   punctuation node, in that order.
4. WHEN a `Literal`/`typing.Literal` type has more than one argument, THEN the
   annotation parser SHALL separate adjacent argument text nodes with a
   comma-and-space punctuation node.
5. IF nitpicky mode is enabled and an annotation contains `Literal` argument
   values, THEN building SHALL NOT report a missing-reference warning caused by
   those values.

## Requirement 2: non-`Literal` type names continue to be cross-referenced

**User story:** As a documentation author, I want ordinary type annotations to
keep rendering their type names as navigable cross references, so that existing
documentation and links are unaffected by the `Literal` handling.

**Acceptance criteria**

1. WHEN the annotation parser renders a bare type name (for example a class
   name such as `int`), THEN it SHALL emit a cross-reference node whose target
   is that type name with cross-reference type `class`.
2. WHEN the annotation parser renders the name `None`, THEN it SHALL emit a
   cross-reference node with cross-reference type `obj` (an object reference,
   not a class reference).
3. WHEN the annotation parser renders a parametrised type whose head is NOT
   `Literal`/`typing.Literal` (for example a generic container or callable
   type), THEN each type-name element inside it SHALL continue to be emitted as
   a cross-reference node, and brackets, commas, and ellipsis SHALL continue to
   be emitted as punctuation nodes.
4. The annotation parser SHALL continue to render an empty parenthesised group
   and an ellipsis inside a parametrised type as punctuation nodes exactly as
   before this change.
5. WHEN the annotation parser encounters syntactically unparseable annotation
   text, THEN it SHALL fall back to emitting a single cross-reference node for
   the whole annotation string, as before.

## Requirement 3: constant values in non-`Literal` positions keep displaying their source form

**User story:** As a documentation author who uses numeric or constant default
values and constants elsewhere in signatures, I want those constants to keep
displaying in their normal source form, so that this change does not alter
unrelated rendering.

**Acceptance criteria**

1. WHEN the annotation parser renders a constant value that appears outside a
   `Literal` argument list, THEN it SHALL display that value using its canonical
   source representation (for example a string constant shown with its
   surrounding quotes).
2. The system SHALL keep rendering function and data signatures that contain
   numeric literals, union-type expressions, optional types, and callable types
   with their existing node structure, unchanged by the `Literal` handling.
3. WHEN an annotation that does not contain a `Literal`/`typing.Literal` head
   is rendered, THEN the annotation parser SHALL preserve the previous
   rendering of its type names (as cross-reference nodes) and of its brackets,
   commas, and ellipsis (as punctuation nodes), in the same order as before;
   the only permitted difference from the previous behavior SHALL be that a
   constant value is displayed using its canonical source representation per
   Requirement 3.1 — so a string constant appearing outside a `Literal`
   argument list SHALL now be shown with its surrounding quotes, while a
   numeric constant (whose source representation is unchanged) SHALL render
   exactly as before.
