# Requirements: Cross-reference type annotations in documented property signatures

## Introduction

Sphinx's Python domain (`sphinx/domains/python.py`) renders the signatures of
documented Python objects. Each object directive builds a signature node by
adding child inline nodes for the name, any prefix, and any declared type
annotation. The object of interest here is the *property* directive, handled by
`PyProperty.handle_signature`.

When a documented property declares a type (via its `type` option), that type
was previously emitted as a single inert run of plain text of the form
`": " + type`. As a result, the type name shown after the `":"` separator was
displayed but was not navigable: a documented type appearing in a property's
type annotation did not become a cross-reference to that type's documentation.

The goal is to render a documented property's declared type the same way other
Python-domain constructs (such as data/attribute annotations and function
return/parameter annotations) render types: the type string is parsed into a
sequence of inline nodes in which type names become cross-reference-aware nodes,
so a documented type in a property's annotation becomes a navigable
cross-reference. The shared annotation-parsing helper `_parse_annotation(typ,
env)` performs this parsing. This change is localized to
`PyProperty.handle_signature`; the parsing helper and all other directives'
behavior remain as they are.

## Requirement 1: Parse a documented property's type annotation into cross-referenceable nodes

**User story:** As an author documenting a Python API, I want the type declared
on a property to be cross-referenced in the rendered signature, so that a reader
can navigate from the property's annotation to the documentation of that type.

**Acceptance criteria**
1. WHEN a property directive is rendered and a non-empty `type` option is
   present, THEN `PyProperty.handle_signature` SHALL append to the signature a
   single type-annotation node whose children begin with a plain-text node
   holding the separator `": "` followed, in order, by the inline nodes obtained
   by parsing the declared type string with the shared annotation parser
   `_parse_annotation`.
2. WHEN the declared type names a type (for example a class name), THEN the
   parsed annotation SHALL include a cross-reference node for that type name
   rather than emitting the type name only as inert plain text, so that the type
   can resolve to its documentation.
3. The separator between the property name and its type SHALL be the two
   characters colon-then-space (`": "`), represented as its own plain-text node
   distinct from the parsed type nodes.
4. IF the property directive has no `type` option (or an empty one), THEN
   `PyProperty.handle_signature` SHALL NOT append any type-annotation node to the
   signature.

## Requirement 2: Preserve the property signature prefix and identity

**User story:** As a documentation reader, I want a property to still be clearly
labeled and named after this change, so that only the type rendering improves.

**Acceptance criteria**
1. The system SHALL continue to prefix a property signature with `"property "`,
   with `"abstract "` prepended when the `abstractmethod` option is set and
   `"class "` prepended when the `classmethod` option is set.
2. The system SHALL continue to emit the property's name node in the signature
   and to return the property's fully-qualified name and prefix unchanged from
   prior behavior.
3. WHEN both a prefix and a type are present, THEN the signature SHALL contain
   the prefix annotation, the name, and the type annotation together, with the
   type annotation rendered per Requirement 1.

## Requirement 3: Preserve type-annotation rendering for other directives

**User story:** As a maintainer, I want data and attribute annotations to keep
being cross-referenced exactly as before, so that this fix does not change or
regress the constructs that already parsed their type annotations.

**Acceptance criteria**
1. The system SHALL continue to render a data object's declared type annotation
   as a `": "` separator followed by the parsed, cross-reference-aware inline
   nodes of the type string.
2. The system SHALL continue to render an attribute object's declared type
   annotation as a `": "` separator followed by the parsed, cross-reference-aware
   inline nodes of the type string, and to render its `value` option unchanged.
3. The behavior of the shared annotation parser `_parse_annotation` — including
   its handling of plain names, dotted names, unions written with the `|`
   operator, subscripted generics, literals, and `...` — SHALL remain unchanged.

## Requirement 4: Preserve cross-reference resolution for property types

**User story:** As an author, I want a property whose type refers to a documented
class to resolve to that class, so that the new cross-reference actually links to
the target when it exists.

**Acceptance criteria**
1. WHEN a property's declared type names a class that is documented in the same
   project, THEN the cross-reference produced for that type in the property's
   annotation SHALL resolve to that class's target.
2. The system SHALL keep resolving type cross-references appearing in property
   annotations under the same resolution rules already used for other Python
   domain type cross-references (including the configured behavior for
   unqualified type names).
