# Requirements — Python-domain variable info fields must not auto-cross-reference

## Introduction

When the Python domain (`sphinx.domains.python`) renders an object's
description, it turns "info field lists" — the `:param:`, `:type:`, `:var:`,
`:ivar:`, `:cvar:`, `:raises:`, `:returns:`, `:rtype:` fields — into doctree
nodes. This rendering is driven by the `doc_field_types` configuration on
`PyObject` in `sphinx/domains/python.py`, which delegates to the field classes
in `sphinx/util/docfields.py` (`Field.make_xref` / `Field.make_xrefs`,
`TypedField.make_field`).

Each configured field may carry a role name for its argument. When a role name
is present, the field's argument name is wrapped in a pending cross-reference
node so it becomes a hyperlink resolved against every object of that role in the
project. The documented-variable field group (`:var:`, `:ivar:`, `:cvar:`) was
configured to cross-reference its argument name as a general object. As a
result, a documented instance/class variable's name auto-linked to any
unrelated object sharing that name — e.g. a `limit` variable on one class
linking to an unrelated `limit` elsewhere. This is almost always wrong: two
identically named variables in different scopes are usually unrelated, and the
author never asked for the link.

The goal: the name of a documented variable field must be rendered as plain
inline text (no cross-reference), while the type annotation of that variable and
every other info-field behavior remain exactly as before.

The affected surface is `PyObject.doc_field_types` in
`sphinx/domains/python.py` (the entry configuring the `var`/`ivar`/`cvar`
field group) and the field-rendering helpers in `sphinx/util/docfields.py`.

## Requirement 1: Variable-name field renders without a cross-reference

**User story:** As an author documenting an instance or class variable, I want
the variable's name shown as plain styled text and not turned into a link, so
that it is not silently associated with unrelated same-named objects elsewhere
in the project.

**Acceptance criteria**

1. WHEN the Python domain renders a documented-variable info field (a field
   whose tag is `var`, `ivar`, or `cvar`), THEN the system SHALL emit the
   variable's name as a plain strong-inline text node and SHALL NOT wrap that
   name in a pending cross-reference node.
2. WHEN the variable field's name is rendered, THEN the system SHALL preserve
   the variable name text unchanged (the exact argument string) inside that
   strong-inline text node.
3. IF a documented-variable field is present, THEN the emitted name node SHALL
   carry no cross-reference target, reference role, or reference domain
   attribute for the variable name.

## Requirement 2: Variable type annotation stays a class cross-reference

**User story:** As an author, I want the type I give for a documented variable
to remain a resolvable link to that class, so that navigating from a variable
to its type keeps working.

**Acceptance criteria**

1. WHEN a documented-variable info field includes a type annotation whose value
   is a single simple name, THEN the system SHALL render that type as a pending
   cross-reference node that targets a class-role object, wrapping emphasized
   inline text holding the type name.
2. The system SHALL render the type portion with the same surrounding
   punctuation and separators as before (the type shown in parentheses,
   followed by the description separator), so only the variable-name linking
   behavior changes.
3. WHEN both a name and a type are present for one documented variable, THEN
   the system SHALL render the name as plain text (per Requirement 1) AND the
   type as a class cross-reference in the same rendered item.

## Requirement 3: Other info-field roles keep cross-referencing

**User story:** As a maintainer, I want the change scoped strictly to the
variable field group, so that parameters, exceptions, and return types keep
their existing links.

**Acceptance criteria**

1. The system SHALL keep rendering parameter info fields (`param`, `arg`,
   `keyword`, and their aliases) with their configured argument role, so a
   parameter name continues to render with the same node structure as before
   the change.
2. The system SHALL keep rendering exception fields (`raises` and its aliases)
   as cross-references to the exception role, unchanged.
3. The system SHALL keep rendering the parameter/variable type role
   (`type`, `vartype`, `paramtype`) as a class cross-reference, unchanged.
4. The system SHALL keep the field labels, field ordering, collapsing
   behavior, and the description text of every info field exactly as before;
   only the presence of a cross-reference on the documented-variable name
   changes.

## Requirement 4: Behavior independent of same-named objects

**User story:** As an author, I want a documented variable's name never to link
to an unrelated object, whether or not another object with that name exists, so
that rendering is predictable.

**Acceptance criteria**

1. IF another object anywhere in the project shares the documented variable's
   name, THEN the system SHALL still render the variable name as plain text and
   SHALL NOT create any link between the two.
2. WHEN the same variable name would previously have produced an auto-link,
   THEN the system SHALL now produce no cross-reference for that name under any
   referencing conditions.
