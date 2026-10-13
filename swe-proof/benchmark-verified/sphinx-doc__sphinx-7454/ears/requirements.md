# Requirements: Consistent cross-references for type-annotation tokens

## Introduction

When Sphinx renders a Python type annotation into documentation, the annotation
is parsed into a sequence of nodes by `_parse_annotation` in
`sphinx/domains/python.py`. Each bare name token of the annotation (for example
`int`, `List`, or `None`) is turned into a Python-domain cross-reference so that
it becomes a clickable link into the documentation set.

Historically every such token was emitted as a *class* cross-reference. This is
correct for class-like names such as `int` or `List`, but it is wrong for the
special token `None`: `None` is not a class but the unique `None` singleton
object, and it is documented as an object, not a class. As a result a `None`
return annotation rendered in signature mode failed to resolve to the `None`
documentation, while other tokens (and `None` rendered in description mode)
resolved correctly — an inconsistency reported by users.

The goal is that `_parse_annotation` produce a resolvable cross-reference for
*every* annotation token, and that the reference kind for the token `None`
select the object entity rather than the class entity, so that `None` links to
the documentation of the `None` singleton regardless of rendering mode. All
existing parsing and rendering behavior for other tokens and for compound
annotations must be preserved.

## Requirement 1: Every annotation token becomes a Python-domain cross-reference

**User story:** As a documentation author, I want each name in a type
annotation to become a clickable Python-domain reference, so that readers can
navigate from any annotated type to its documentation.

**Acceptance criteria**

1. WHEN `_parse_annotation` converts a bare name token of an annotation into a
   node, THEN it SHALL produce a pending cross-reference node for that token.
2. The system SHALL set the reference domain of every such cross-reference to
   the Python domain.
3. The system SHALL set the reference target of every such cross-reference to
   the exact text of the token.
4. The system SHALL use the exact text of the token as the visible label of the
   cross-reference.
5. WHEN an annotation cannot be parsed as a valid expression, THEN
   `_parse_annotation` SHALL still emit a single cross-reference for the whole
   annotation text, using the same domain, target, and label rules.

## Requirement 2: The `None` token uses an object reference; all other tokens use a class reference

**User story:** As a reader of API documentation, I want a `None` type
annotation to link to the documentation of the `None` singleton, so that its
behavior is consistent with every other type in the signature.

**Acceptance criteria**

1. WHEN the token being cross-referenced is exactly `None`, THEN the system
   SHALL set the reference kind to the object kind so that the reference
   resolves to the documented `None` object.
2. IF the token being cross-referenced is any name other than `None`, THEN the
   system SHALL set the reference kind to the class kind.
3. The system SHALL determine the reference kind solely from whether the token
   text equals `None`; the domain, target, and label SHALL NOT depend on that
   distinction.

## Requirement 3: Preserve existing parsing and rendering of compound annotations

**User story:** As a maintainer, I want the change to affect only the reference
kind of the `None` token, so that no other annotation-rendering behavior
regresses.

**Acceptance criteria**

1. The system SHALL continue to render a plain class name such as `int` as a
   single class-kind Python-domain cross-reference whose target and label are
   that name.
2. The system SHALL continue to parse subscripted annotations (for example a
   generic such as `List[int]`) into the name reference followed by the bracket
   punctuation, the inner token reference(s), and the closing bracket, keeping
   the class kind for every non-`None` token.
3. The system SHALL continue to parse comma-separated annotation elements and
   nested/qualified names into the same node structure as before, changing only
   the reference kind carried by the `None` token.
4. The system SHALL preserve the surrounding signature- and
   description-rendering behavior so that both rendering modes emit the same
   kind of cross-reference for a given token.
