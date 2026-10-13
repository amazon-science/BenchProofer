# Requirements: Preserve field-projection when a pickled query is installed into a QuerySet

## Introduction

Django's `QuerySet` (in `django/db/models/query.py`) separates two concerns.
The `Query` object (`self._query`, exposed through the `query` property and its
setter) holds the SQL-level description of what will be run, including the set of
fields a `.values()`/`.values_list()` call selected (`Query.values_select`). The
`QuerySet` itself holds `self._iterable_class`, the strategy that turns each raw
database row into a Python result: `ModelIterable` builds full model instances,
while `ValuesIterable` builds a `dict` mapping each projected field name to its
value (and `ValuesListIterable`/`FlatValuesListIterable`/`NamedValuesListIterable`
build tuple / single-value / named-tuple rows).

`Query` objects are documented as picklable and re-usable: a caller may pickle
`some_qs.query`, then install it into a freshly created queryset via the
`query` setter (`qs = Model.objects.all(); qs.query = pickle.loads(...)`) to
re-run the query later. However, `_iterable_class` lives on the `QuerySet`, not
on the `Query`, so it is not carried by the pickled query. A queryset created
with `Model.objects.all()` starts with `_iterable_class = ModelIterable`. When a
pickled query that had projected specific fields (via `.values()` or
`.values_list()`, typically combined with `.annotate()` for GROUP BY) was
installed through the setter, the queryset kept `ModelIterable`. Iterating it
then tried to build model instances out of field/aggregate rows, producing wrong
result types and crashing (e.g. `AttributeError: 'NoneType' object has no
attribute 'attname'`) instead of returning the expected dict rows.

The goal is to make the `query` setter reconcile the row-building strategy with
the query being installed: when the installed query projects a specific set of
fields, the queryset must produce field-value dictionaries; otherwise the
existing strategy must be left untouched.

## Requirement 1: Installing a field-projecting query yields dict rows

**User story:** As a developer who pickles `queryset.query` from a
`.values(...).annotate(...)` (or `.values_list(...)`) queryset and installs it
into a plain queryset for later re-evaluation, I want re-running that query to
return the field-value dictionaries the query projects, so that the result type
matches an un-pickled `.values()` queryset and does not crash.

**Acceptance criteria**

1. WHEN a query is assigned through the `QuerySet.query` setter and that query
   projects a specific set of selected fields (its `values_select` is
   non-empty), THEN the queryset SHALL set its row-building strategy
   (`_iterable_class`) to the field-value-mapping strategy (`ValuesIterable`).
2. WHEN such a queryset (one into which a field-projecting query was installed)
   is subsequently evaluated, THEN each result row SHALL be a `dict` mapping the
   projected field name(s) — including any annotated aggregate — to their
   values, and SHALL NOT be a model instance.
3. WHEN a query originally produced by `.values('name').annotate(<aggregate>)`
   is pickled, unpickled, and installed via the setter, THEN evaluating the
   queryset SHALL yield the same field-value dictionaries (the selected field
   plus the annotated value) that the original queryset would have yielded,
   and accessing/printing the result SHALL NOT raise.
4. WHEN the installed field-projecting query was originally produced by any
   `.values_list(...)` variant (positional, `flat=True`, or `named=True`),
   THEN the queryset SHALL still adopt the field-value-mapping (`dict`) strategy
   — i.e. such a re-installed query SHALL be evaluated as though it were a
   `.values(...)` query, producing dict rows rather than tuples, flat values, or
   named tuples.

## Requirement 2: Installing a non-projecting query preserves the current strategy

**User story:** As a developer installing an ordinary (non-`.values`) query into
a queryset, I want the queryset's existing row-building strategy to be left
alone, so that normal querysets keep returning model instances.

**Acceptance criteria**

1. WHEN a query is assigned through the `QuerySet.query` setter and that query
   projects no specific fields (its `values_select` is empty), THEN the setter
   SHALL leave the queryset's row-building strategy (`_iterable_class`)
   unchanged from whatever it was before the assignment.
2. WHEN a plain queryset (default `ModelIterable` strategy) has an ordinary
   pickled query installed and is then evaluated, THEN each result row SHALL be
   a model instance, exactly as before this change.
3. IF the queryset already carried a non-model row-building strategy before the
   assignment and the installed query projects no specific fields, THEN the
   setter SHALL NOT reset that strategy back to the model-instance strategy.

## Requirement 3: The assigned query is always stored, and other behavior is preserved (regression protection)

**User story:** As a maintainer, I want the `query` setter to keep doing
everything it did before — storing the assigned query — and I want all other
pickling/unpickling behavior of querysets, queries, and related objects to be
unaffected, so that this fix adds the strategy reconciliation without regressing
anything else.

**Acceptance criteria**

1. WHEN any value is assigned through the `QuerySet.query` setter, THEN the
   queryset's stored query (`_query`) SHALL become exactly that assigned value,
   in every case (whether or not the row-building strategy is changed).
2. The row-building strategy SHALL be adjusted by the setter based solely on
   whether the installed query projects a specific set of fields; the setter
   SHALL NOT otherwise mutate the queryset's result cache, prefetch state, or
   other attributes as a side effect of the assignment.
3. WHEN a `QuerySet` (including specialized, deferred, prefetch-related, or
   `values`/`values_list` querysets) is pickled and unpickled as a whole object,
   THEN it SHALL continue to round-trip and evaluate to the same results as
   before this change.
4. WHEN a `Query` object is pickled and unpickled, THEN it SHALL continue to
   round-trip unchanged; installing it via the setter SHALL preserve its
   selected fields, annotations, filters, and ordering so the re-run query
   returns the same rows as the original.
5. WHEN a queryset built with defaults (no explicit field projection) is
   pickled/unpickled or has its query re-installed, THEN it SHALL still yield
   model instances whose primary key and other attributes are accessible without
   error.
6. The model-related pickling behaviors that already worked — model instances,
   many-to-many relations, related-field and reverse-relation querysets,
   `DoesNotExist`/`MultipleObjectsReturned` exception classes, deferred loading,
   `Exists`/subquery/prefetch querysets remaining lazily unevaluated, and
   unpickling guards for missing or mismatched Django versions — SHALL all
   continue to behave exactly as before.
