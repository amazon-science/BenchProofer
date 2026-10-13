# Requirements — Namespace-aware cross-references for Python info fields

## Introduction

In Sphinx's Python domain, documentation *info fields* — `:type:`, `:rtype:`,
and the type portion of `:param <type> name:` — create *implicit* cross-references
to the named type. Users report that these implicit cross-references resolve
differently from an explicit role such as `:py:class:`. For an unqualified name
(e.g. `A`), the implicit lookup searches for the name in *every* (sub)module
rather than preferring the current module and its parents. This produces spurious
`more than one target found for cross-reference` ambiguity warnings and links an
unqualified type to the wrong object (for example, resolving `A` to `mod.A` when
the current module is `mod.submod` and `mod.submod.A` exists).

The root cause is that the reference node produced for an info-field type does not
carry the surrounding namespace context. An explicit role node records the current
module and enclosing class (via the `py:module` and `py:class` entries of the
domain's reference context); the resolver uses those to try scope-qualified lookups
first. The implicit info-field node omitted them, so the resolver fell back to a
fuzzy, all-modules search.

The affected code is the node-building step for inline type specifiers in
`PyXrefMixin.make_xref` (`sphinx/domains/python.py`), and the field-transformation
step that invokes cross-reference construction for info-field types in
`Field.transform` (`sphinx/util/docfields.py`). The goal: give an info-field type
cross-reference the same namespace context an explicit role node carries, so that
scope-aware resolution applies.

## Requirement 1: Info-field type cross-references record the current namespace

**User story:** As a documentation author, I want an implicit type cross-reference
created from an info field to know the module and class it appears in, so that an
unqualified type name resolves within the current scope like an explicit role,
without spurious ambiguity warnings.

**Acceptance criteria**

1. WHEN `PyXrefMixin.make_xref` builds a cross-reference node for an info-field
   type target, THEN the returned reference node SHALL carry a `py:module` entry
   whose value is the current module of the surrounding reference context (the
   value the reference context associates with `py:module`).
2. WHEN `PyXrefMixin.make_xref` builds a cross-reference node for an info-field
   type target, THEN the returned reference node SHALL carry a `py:class` entry
   whose value is the current class of the surrounding reference context (the
   value the reference context associates with `py:class`).
3. IF the surrounding reference context has no current module, THEN the returned
   node's `py:module` entry SHALL be a null/absent value (mirroring the missing
   context entry) rather than a fabricated name.
4. IF the surrounding reference context has no current class, THEN the returned
   node's `py:class` entry SHALL be a null/absent value rather than a fabricated
   name.
5. WHEN a type name is documented inside a class that is itself inside a module
   (e.g. a `:param <type> name:` or a `:param name:` paired with `:type name:`
   under a class in a module), THEN the produced type cross-reference node SHALL
   record both that enclosing module name and that enclosing class name.

## Requirement 2: Namespace context is available at the info-field type link site

**User story:** As a maintainer, I want the environment to be passed through to the
cross-reference construction for info-field types, so that the current namespace
context can actually be read when the node is built.

**Acceptance criteria**

1. WHEN `Field.transform` links the type of a field it otherwise treats as unknown
   but that carries a type (the branch that turns the single-text type body into a
   cross-reference), THEN it SHALL provide the build environment to the
   cross-reference construction call so that the surrounding namespace context is
   reachable.
2. The system SHALL ensure that reading the current module and current class in
   `make_xref` does not fail when a cross-reference is built for an info-field
   type, i.e. the environment SHALL be present (non-null) wherever info-field type
   cross-references are constructed during field transformation.

## Requirement 3: Preserve existing cross-reference resolution behavior

**User story:** As a maintainer, I want the pre-existing behavior of info-field
type cross-references to remain unchanged, so that the namespace fix does not
regress qualified names, prefix handling, or node shape.

**Acceptance criteria**

1. The reference node produced for an info-field type SHALL continue to request
   scope-specific resolution (its `refspecific` flag SHALL remain set).
2. WHEN the target begins with a `.` prefix, THEN `make_xref` SHALL strip the
   leading `.` from the resolved target and use the remaining name as the reference
   target.
3. WHEN the target begins with a `~` prefix, THEN `make_xref` SHALL strip the
   leading `~` from the reference target AND SHALL display only the final
   dotted component of the name as the visible link text.
4. WHEN a type target is the literal `None`, THEN the fields that special-case it
   SHALL build the reference as a generic object reference rather than a class
   reference.
5. The system SHALL emit the type cross-reference of a documented parameter or
   return type as a pending cross-reference in the Python domain with class-style
   reference type and with the reference target equal to the (prefix-stripped)
   type name.
6. WHEN a fully qualified type name is given (e.g. `mod.submod.A`), THEN the
   produced node SHALL keep that exact name as its reference target, so that
   already-correct qualified references are unaffected.
7. The system SHALL keep the overall parameter/type field rendering intact: a
   `:param <type> name:` (or a `:param name:` combined with a `:type name:`) SHALL
   render the parameter name, its parenthesized type as a cross-reference, and the
   description text together in the parameters list.
