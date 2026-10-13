# Requirements: Support pipe (`|`) as a union-type separator in Python domain type fields

## Introduction

In Sphinx's Python domain, info fields such as `:type:` and `:rtype:` accept a
type specification string and turn each referenced type name into a
cross-reference while leaving structural punctuation (brackets, commas, the word
`or`, ellipsis) as verbatim separator text. This behavior lives in the
type-splitting logic of `PyXrefMixin.make_xrefs` in `sphinx/domains/python.py`,
which splits the type-specification string into pieces, classifies each piece as
either a type name (to be cross-referenced) or a separator (to be kept as-is),
and returns the ordered list of resulting inline nodes.

Users increasingly write union types with the vertical bar / pipe syntax
(e.g. `bytes | str`), matching PEP 604 and common IDE conventions. Currently the
splitter does not recognize `|` as a separator, so a type spec like `int | str`
is not decomposed and its individual type names are not cross-referenced.

The goal is to make the type-field splitter treat `|` (optionally surrounded by
whitespace) as a type separator, on equal footing with the existing separators,
so each pipe-separated type name becomes its own cross-reference while the pipe
(with its surrounding spacing) is preserved verbatim between them — without
changing any of the existing separator behavior.

## Requirement 1: Recognize the pipe as a union-type separator

**User story:** As a documentation author, I want to write a parameter or
attribute type as `bytes | str`, so that each type is individually
cross-referenced just as it would be with the `or` keyword.

**Acceptance criteria**

1. WHEN `PyXrefMixin.make_xrefs` processes a type specification that contains a
   `|` character between two type names, THEN the splitter SHALL treat the `|`
   (together with any whitespace immediately surrounding it) as a separator and
   SHALL split the specification at that point.
2. WHEN a type specification of the form `A | B` (type name, pipe, type name) is
   processed, THEN the resulting sequence of inline nodes SHALL contain, in
   order: a cross-reference for `A`, a verbatim separator node, and a
   cross-reference for `B`.
3. WHEN a type name appears as one side of a pipe-separated specification, THEN
   that type name SHALL be emitted as a cross-reference node whose reference
   target is exactly that type name (with no surrounding whitespace or pipe
   characters included in the target).
4. WHEN the pipe separator is surrounded by single spaces (` | `), THEN the
   emitted separator node SHALL preserve that separator text verbatim, including
   its surrounding spaces, and SHALL NOT be turned into a cross-reference.
5. WHEN a type specification contains more than two pipe-separated type names
   (e.g. `A | B | C`), THEN each type name SHALL be emitted as its own
   cross-reference and each `|` SHALL be emitted as its own separator node, in
   left-to-right order.

## Requirement 2: Correct classification of type names versus separators

**User story:** As a Sphinx maintainer, I want the pipe-splitting to reuse the
same name-versus-separator classification as the existing separators, so that
pipe-separated type names are cross-referenced and pipes are not.

**Acceptance criteria**

1. The system SHALL classify each piece produced by splitting a type
   specification as either a type name or a separator, and SHALL emit a
   cross-reference for a type name and a verbatim inline node for a separator.
2. IF a piece consists solely of a pipe and its surrounding whitespace, THEN the
   system SHALL classify it as a separator and SHALL NOT emit a cross-reference
   for it.
3. IF a piece is a type name adjacent to a pipe separator, THEN the system SHALL
   classify it as a type name and SHALL emit a cross-reference whose target
   excludes the pipe and any adjacent whitespace.
4. The system SHALL preserve the left-to-right order of type names and
   separators exactly as they appear in the original type specification.

## Requirement 3: Preserve all existing type-separator behavior

**User story:** As an existing Sphinx user, I want my current type
specifications to keep rendering exactly as before, so that adding pipe support
introduces no regressions.

**Acceptance criteria**

1. WHEN a type specification uses the keyword `or` as a separator (e.g.
   `A or B`), THEN the splitter SHALL continue to treat `or` as a separator and
   SHALL emit each surrounding type name as a cross-reference, unchanged from
   prior behavior.
2. WHEN a type specification uses brackets, parentheses, or commas (e.g.
   `List[int, str]`), THEN the splitter SHALL continue to treat those
   punctuation characters as separators and SHALL continue to cross-reference
   the contained type names, unchanged from prior behavior.
3. WHEN a type specification contains an ellipsis (`...`), THEN the splitter
   SHALL continue to treat it as a separator, unchanged from prior behavior.
4. WHEN a type specification contains no recognized separator, THEN the splitter
   SHALL emit the whole specification as a single cross-reference, unchanged from
   prior behavior.
5. The system SHALL continue to produce the same node structure for a type field
   as before for any specification that does not contain a `|`, so that only
   pipe-containing specifications change in behavior.

## Requirement 4: End-to-end rendering of a piped type field

**User story:** As a documentation author, I want a `:type:` field written with a
pipe to render with each type linked and the pipe shown between them, so that
readers see correctly cross-referenced union types.

**Acceptance criteria**

1. WHEN a Python info field declares a parameter's type as `int | str`, THEN the
   rendered field body SHALL present `int` and `str` each as their own
   cross-reference and SHALL present ` | ` verbatim between them.
2. WHEN such a type is cross-referenced, THEN each generated reference SHALL
   carry the appropriate Python-domain class reference targeting the respective
   type name, so that resolvable type names become working links.
3. WHEN a `:param:` description accompanies a piped `:type:` field, THEN the
   parameter name, the parenthesized piped type, and the description text SHALL
   all be rendered together in the field body, with the piped type appearing in
   the same position it would for any other type specification.
