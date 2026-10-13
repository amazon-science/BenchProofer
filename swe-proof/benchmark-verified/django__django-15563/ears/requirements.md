# Requirements: Correct row targeting for queryset updates under multiple inheritance

## Introduction

When a Django model uses multi-table multiple inheritance (a model inheriting
from more than one concrete parent model), a single `QuerySet.update(...)` call
that changes fields owned by an ancestor model is split into one auxiliary
UPDATE per affected ancestor ("related updates"). Each ancestor lives in its own
database table with its own primary key column.

The affected code is the update-SQL compilation path:
`SQLUpdateCompiler.pre_sql_setup` in `django/db/models/sql/compiler.py`, together
with `UpdateQuery.get_related_updates` and the `Query.related_ids` /
`Query.related_updates` state in `django/db/models/sql/subqueries.py`.

The defect: the pre-update step pre-selected only the updated model's own
primary key and reused that single list of identifiers to filter *every*
ancestor's UPDATE. That is correct only when an ancestor is reachable from the
model through a chain of primary-key-to-primary-key links (so the ancestor
shares the model's primary key values). For an ancestor whose primary key is
independent of the model's primary key (a second/other parent in a diamond or
plain multiple-inheritance tree), the model's primary key values do not identify
that ancestor's rows. The old behavior therefore filtered the ancestor's UPDATE
on foreign identifiers, so the intended rows were left unchanged while unrelated
rows (rows of that ancestor table whose keys happened to coincide numerically)
were modified.

The goal: gather, for each ancestor, the identifiers that actually target *that
ancestor's* rows, and use them to drive that ancestor's UPDATE — while leaving
the common single-inheritance / shared-primary-key case unchanged.

## Requirement 1: Determine per-ancestor identifier source during update setup

**User story:** As a developer updating a queryset for a model with multiple
inheritance, I want each ancestor's UPDATE to be driven by identifiers that
belong to that ancestor, so that the correct rows are changed.

**Acceptance criteria**

1. WHEN an update is compiled that requires one or more related updates to
   ancestor models, THEN the update-setup step SHALL always pre-select the
   updated model's own primary key value for the matched rows.
2. WHEN determining how to target a given ancestor's rows, THEN the system SHALL
   inspect the path from the model to that ancestor and classify the ancestor as
   *primary-key-shared* if and only if every join field along that path is a
   primary key.
3. IF an ancestor is primary-key-shared, THEN the system SHALL target that
   ancestor's rows using the model's own primary key values (the values already
   pre-selected for the model), without pre-selecting any additional key column
   for that ancestor.
4. IF an ancestor is NOT primary-key-shared, THEN the system SHALL additionally
   pre-select that ancestor's own primary key value for each matched row, so
   that ancestor is targeted by its own identifiers rather than the model's.
5. WHEN more than one ancestor is not primary-key-shared, THEN the system SHALL
   allocate a distinct pre-selected key column to each such ancestor, so that no
   two ancestors read their identifiers from the same additional column.
6. The system SHALL preserve the original ordering of the related updates when
   associating each ancestor with the identifiers gathered for it.

## Requirement 2: Materialize and route per-ancestor identifiers before progressive updates

**User story:** As a developer, I want the identifiers used for each ancestor's
UPDATE to be captured up front, so that the sequence of dependent UPDATE queries
targets a stable, correct set of rows.

**Acceptance criteria**

1. WHEN the matched rows are read from the pre-selection query, THEN for each
   ancestor the system SHALL collect the identifier values from the column
   assigned to that ancestor (the model's own key column for a
   primary-key-shared ancestor, or that ancestor's dedicated column otherwise).
2. WHEN identifiers have been collected, THEN the system SHALL retain them keyed
   per ancestor model, so that each ancestor model can later be matched to its
   own list of identifiers.
3. The system SHALL continue to constrain the model's own UPDATE to the matched
   rows using the model's pre-selected primary key values.
4. WHILE producing the auxiliary UPDATE query for a given ancestor model, the
   system SHALL restrict that query to rows whose primary key is among the
   identifiers collected for that same ancestor model, and SHALL NOT reuse
   another model's identifiers.
5. IF no pre-selected identifiers were captured (identifier collection was not
   performed for this update), THEN the auxiliary UPDATE queries SHALL be built
   without an identifier-based restriction, preserving the prior behavior for
   that case.

## Requirement 3: Correct end-to-end behavior for multiple-inheritance updates

**User story:** As a user, I want `update()` on a multiply-inheriting model to
change exactly the intended rows of the intended ancestor, so that neither my
target rows are missed nor unrelated rows are corrupted.

**Acceptance criteria**

1. WHEN a field owned by a second (non-primary-key-shared) parent is updated
   through a child queryset, THEN the child's own rows SHALL receive the new
   value for that field.
2. WHEN such an update completes, THEN rows of the ancestor table that do not
   belong to the updated child instances SHALL remain unchanged.
3. WHEN a field owned by an indirect ancestor (an ancestor reached through
   another parent, e.g. a grandparent through a child) is updated through a
   child queryset, THEN the correct ancestor rows corresponding to the child
   instances SHALL receive the new value.
4. WHEN an updated instance is subsequently re-read, THEN the value observed for
   the updated ancestor field SHALL equal the value that was written.

## Requirement 4: Preserve existing single-inheritance and shared-key behavior

**User story:** As a maintainer, I want the common inheritance cases to keep
working exactly as before, so that this fix introduces no regression.

**Acceptance criteria**

1. WHEN an update targets a model with no related ancestor updates, THEN the
   update-setup behavior SHALL be unchanged from before this fix.
2. WHEN a field owned by an ancestor that is primary-key-shared with the model
   is updated, THEN the ancestor's rows SHALL continue to be targeted by the
   model's own primary key values and SHALL be updated correctly.
3. The system SHALL keep returning the number of rows affected by the primary
   update query, unchanged by the per-ancestor identifier routing.
4. WHEN an operation does not trigger a related update to a
   non-primary-key-shared ancestor (for example any read/query operation, or an
   update whose changed fields are all owned by the model itself or by
   primary-key-shared ancestors), THEN its observable behavior SHALL be identical
   to the behavior before this fix, because the per-ancestor identifier routing
   changes only how non-primary-key-shared ancestor UPDATEs are targeted.
