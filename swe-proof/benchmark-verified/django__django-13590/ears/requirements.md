# Requirements: Preserve named-tuple arguments when resolving lookup values

## Introduction

When a queryset filter is built (for example a `__range` lookup), Django's ORM
resolves the right-hand side value before turning it into SQL. This resolution
is performed by `resolve_lookup_value` on `django.db.models.sql.query.Query`.
For a value that is a list or tuple, the method resolves each element
independently (an element may itself be a query expression) and then rebuilds a
container **of the same type** from the resolved elements.

The affected behavior concerns *subtypes* of `tuple` — in particular named
tuples produced by `collections.namedtuple`. A named tuple's constructor
requires each field to be supplied as a separate positional argument; it does
**not** accept a single iterable of the field values the way `list` and plain
`tuple` do. When the rebuilt container is constructed by handing its
constructor one iterable, a named tuple raises a `TypeError` complaining about
missing positional arguments. The goal is to rebuild any list or tuple value —
including named-tuple subtypes — without error, preserving the container type,
length, order, and per-element resolution, so that filters that pass a named
2-tuple as the value of a `__range` lookup work again.

## Requirement 1: Rebuild list and tuple lookup values with resolved elements

**User story:** As a developer filtering a queryset with a list or tuple value,
I want each element resolved and the container rebuilt faithfully, so that the
resulting query reflects my elements in the right order and type.

**Acceptance criteria**
1. WHEN `Query.resolve_lookup_value` receives a value that is a `list` or a
   `tuple`, THEN it SHALL resolve each element of the value independently, in
   iteration order, applying the same value-resolution logic recursively to
   each element.
2. WHEN a list or tuple value is resolved, THEN the returned container SHALL
   have the same number of elements as the input, in the same order, where each
   returned element is the resolution of the element at the corresponding
   position of the input.
3. WHEN a list or tuple value is resolved, THEN the returned container's type
   SHALL be the same type as the input value (a `list` input yields a `list`,
   and a `tuple` input yields a value of that same tuple type).
4. IF an element of a list or tuple value is itself a resolvable query
   expression, THEN `resolve_lookup_value` SHALL replace that element with its
   resolved form in the rebuilt container.

## Requirement 2: Support named-tuple lookup values without error

**User story:** As a developer, I want to pass a named tuple as the argument to
a lookup (such as `__range`), so that upgrading Django does not break filters
that were previously working.

**Acceptance criteria**
1. WHEN `Query.resolve_lookup_value` receives a value whose type is a named
   tuple (a `tuple` subtype whose constructor takes the fields as individual
   positional arguments rather than a single iterable), THEN it SHALL rebuild
   the value by supplying the resolved elements as separate positional
   arguments to that type's constructor.
2. WHEN a named-tuple value is resolved, THEN `resolve_lookup_value` SHALL NOT
   raise a `TypeError` about missing positional arguments, and SHALL return a
   value of the same named-tuple type with each field set to the resolution of
   the corresponding input field.
3. WHEN a queryset is filtered with a `__range` lookup whose value is a named
   tuple of two elements (the range bounds), THEN the filter SHALL execute
   successfully and SHALL return exactly the rows whose field value falls within
   the inclusive range described by the two named-tuple elements.
4. The system SHALL distinguish named-tuple types from ordinary `list` and
   `tuple` values by a property of the type that indicates its elements must be
   passed individually (the presence of the named-tuple factory method used to
   build an instance from an iterable), rather than by hard-coding specific
   named-tuple classes.

## Requirement 3: Preserve existing resolution behavior for other values

**User story:** As a maintainer, I want the previously correct behavior for
non-container and expression values to be unchanged, so that the fix introduces
no regressions.

**Acceptance criteria**
1. WHEN `Query.resolve_lookup_value` receives a value that exposes an expression
   resolution capability (a resolvable query expression), THEN it SHALL replace
   the value with its resolved expression and SHALL NOT treat it as a list or
   tuple.
2. WHEN `Query.resolve_lookup_value` receives a value that is neither a
   resolvable expression nor a `list` nor a `tuple`, THEN it SHALL return the
   value unchanged.
3. The system SHALL keep the existing behavior for plain `list` and plain
   `tuple` values: such a value continues to be rebuilt into the same container
   type from its resolved elements, exactly as before, so that lookups using
   ordinary lists and tuples (including range and `__in` lookups with plain
   sequences and with expression elements) continue to work.
