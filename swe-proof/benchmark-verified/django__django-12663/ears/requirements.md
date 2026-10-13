## Introduction

Django's ORM lets a query expose an "output field" — the field/type descriptor
that describes the query's single result column. This descriptor is computed by
the `output_field` property of `Query` in
`django/db/models/sql/query.py`. Downstream lookup machinery
(`django/db/models/lookups.py`) uses this descriptor to prepare (coerce) the
right-hand side of a comparison before building SQL: it calls
`output_field.get_prep_value(rhs)` (and, for related fields, the field's
`get_prep_lookup` conversion).

When a query selects exactly one column, that column is represented by a
column-reference expression (a `Col`). Such an expression carries two distinct
type descriptors:

* its **declared output type** (exposed as the expression's `field` attribute),
  and
* its **underlying referenced model attribute** (exposed as the expression's
  `target` attribute) — the concrete model field the column points at.

For a plain scalar column these can coincide, but for a column that references a
related object (a foreign key), the `target` is the related field that knows how
to convert a related-object value (including a lazy proxy such as
`SimpleLazyObject`) into the stored key value, whereas the plain declared type
does not.

Prior to the change that introduced this regression, filtering an annotated
queryset (where the annotation is a `Subquery` — possibly nested over another
`Subquery`/`OuterRef` — that ultimately selects a single related column) by a
`SimpleLazyObject` worked. Afterwards the outermost `Query.output_field`
returned the column's declared type (`field`) instead of its referenced
attribute (`target`), so the lazy proxy was never converted to its underlying
model instance / key and lookup preparation raised
`TypeError: int() argument must be ... not 'SimpleLazyObject'`.

The goal is to make `Query.output_field` report the referenced attribute of a
single selected column when one exists, so related-field value coercion (and
therefore lazy-object filtering through nested subquery annotations) works
again, while leaving the annotation-based and empty cases unchanged.

## Requirement 1: Report a single selected column's referenced attribute

**User story:** As a developer building a queryset whose result is a single
column, I want the query's output field to describe the actual referenced model
attribute, so that value coercion for that column (including related-field
conversions) uses the correct field.

**Acceptance criteria**

1. WHEN a query's set of selected columns contains exactly one selected column,
   THEN `Query.output_field` SHALL return that column's referenced underlying
   model attribute (the expression's `target`) whenever that attribute is
   present (not `None`).
2. IF the single selected column has no referenced underlying attribute (its
   `target` is absent/`None`), THEN `Query.output_field` SHALL fall back to and
   return that column's declared output type (the expression's `field`).
3. The system SHALL treat "exactly one selected column" as strictly one entry in
   the selected-columns collection; the referenced-attribute selection SHALL NOT
   be applied when zero or more-than-one columns are selected.
4. WHEN the single-selected-column branch determines the descriptor, THEN it
   SHALL derive the descriptor solely from that one selected column and SHALL
   NOT consult the selected-annotations collection.

## Requirement 2: Preserve the single-annotation and undetermined behavior

**User story:** As a maintainer, I want the existing output-field behavior for
annotation-only queries and for queries with no single output column to remain
unchanged, so that no other queryset behavior regresses.

**Acceptance criteria**

1. IF a query selects no single column but its selected annotations contain
   exactly one annotation, THEN `Query.output_field` SHALL return that
   annotation's declared output type.
2. IF a query neither selects exactly one column nor has exactly one selected
   annotation, THEN `Query.output_field` SHALL return nothing (a `None`/absent
   result).
3. The system SHALL keep evaluating the single-column case before the
   single-annotation case, so that a query with exactly one selected column
   reports the column-derived descriptor regardless of its annotations.

## Requirement 3: Coerce related values through a single-column subquery annotation

**User story:** As a developer, I want to filter an annotated queryset by a
value that resolves to a related model instance (including a lazy proxy), so
that comparisons against a subquery-annotated related column succeed instead of
crashing.

**Acceptance criteria**

1. WHEN a queryset is annotated with a `Subquery` (including a `Subquery` nested
   over another `Subquery`/`OuterRef`) whose innermost selection is a single
   related-object column, and that annotation is used as the left-hand side of a
   filter, THEN the query SHALL prepare the right-hand value using the referenced
   related field's conversion (the field that maps a related object to its key
   value).
2. WHEN the right-hand side of such a filter is a `SimpleLazyObject` (or other
   lazy proxy) that wraps a model instance, THEN evaluating the filter SHALL
   convert it to the corresponding related-object key and SHALL NOT raise a
   `TypeError` about the value's type being unusable for coercion.
3. WHEN such a filtered queryset is executed, THEN it SHALL return the rows whose
   annotated related column equals the resolved value, matching the result that
   the same filter produces when given the concrete (non-lazy) related instance.
