# Requirements: `select_related()` + `only()` across a relation to a proxy model

## Introduction

When a Django `QuerySet` restricts which columns it loads to a subset reached
through related models — combining `select_related()` (join and populate related
objects in the same query) with `only()`/`defer()` (load only some fields) — the
ORM must decide exactly which columns to fetch for each model involved. That plan
is computed by `Query.deferred_to_data` in `django/db/models/sql/query.py`.

`deferred_to_data` walks each restricted field path one relation at a time. For
every relation step it resolves the model reached by that step (`cur_model`), then
records — in the `must_include` mapping, keyed by that model — that the model's
primary-key column must be loaded, so that rows for that model can be assembled.
The resulting per-model field sets are consumed downstream by `RelatedPopulator`
(also in `query.py`), which builds each related object; `RelatedPopulator`
locates a model's primary-key column by searching for the *concrete* model's pk
`attname` in the list of fields planned for that model.

A **proxy model** shares the database table and primary-key column of its
concrete base model while remaining a distinct model class. The bug: when a
relation (e.g. a `ForeignKey`) targets a proxy model, `deferred_to_data` keyed
the field-load plan under the *proxy* model object rather than under its concrete
base. Because `RelatedPopulator` later looks the plan up under the concrete model
and searches for the concrete model's pk `attname`, the primary-key column is
absent from the plan registered under the proxy, and building the related object
fails with `ValueError: 'id' is not in list`.

The goal is that the field-load plan produced while walking relation paths is
always keyed under the **concrete** model that owns the shared table and pk
column, never under a proxy, so that `select_related()` followed by `only()`
(or `defer()`) works when a relation points at a proxy model — while leaving the
behavior for ordinary (non-proxy) models exactly as it was.

## Requirement 1: `select_related().only()` over a relation to a proxy model must succeed

**User story:** As a developer whose model has a `ForeignKey` (or one-to-one)
pointing at a proxy model, I want to optimize a query with
`select_related("<rel>").only("<rel>__<field>")`, so that the query executes and
returns the correct objects instead of crashing.

**Acceptance criteria**

1. WHEN a `QuerySet` applies `select_related()` across a relation whose target is
   a proxy model and restricts loaded fields with `only()` (or `defer()`) so that
   the relation is traversed by `Query.deferred_to_data`, THEN evaluating the
   `QuerySet` SHALL complete without raising, and SHALL NOT raise
   `ValueError: 'id' is not in list` (or any comparable "primary key column not
   found" error) while building the related objects.
2. WHEN such a `QuerySet` is evaluated, THEN it SHALL return the same result rows
   as the equivalent query issued without the `only()`/`defer()` restriction — in
   particular a single matching row SHALL be retrieved and SHALL compare equal to
   the object that was stored.
3. WHEN the related object reached through the proxy relation is populated from a
   `select_related()` join, THEN its primary key SHALL be loaded and populated,
   and the explicitly requested related field SHALL be available, so the related
   instance is usable without triggering an additional query for its identity.

## Requirement 2: Key the field-load plan under the concrete model at every relation step

**User story:** As a maintainer of the query planner, I want each traversed
relation's column requirements recorded under the concrete model that owns the
table, so that any consumer keying on the concrete model finds the plan.

**Acceptance criteria**

1. WHEN `Query.deferred_to_data` resolves the model reached by a relation step and
   that model is a proxy, THEN it SHALL record that step's primary-key requirement
   under the resolved model's **concrete** model, and SHALL NOT record it under
   the proxy model itself.
2. WHEN the model reached by a relation step is already a concrete (non-proxy)
   model, THEN the model used as the key SHALL be that same model, so that the
   recorded key is unchanged from the previous behavior for non-proxy targets.
3. The mapping of models to the field sets that must be loaded SHALL, for every
   relation step traversed, use the concrete model as the key; consequently the
   field options (`_meta`) consulted for the remainder of that step SHALL be those
   of the concrete model, whose primary key is the shared pk column.
4. WHEN more than one relation step is traversed in a single field path, THEN each
   step SHALL be keyed under its own resolved model's concrete model, in the order
   the steps are traversed, so that chains of relations passing through proxy
   models are all keyed correctly.

## Requirement 3: Preserve existing deferred/immediate loading behavior (regression protection)

**User story:** As a maintainer, I want every other case of `only()`/`defer()`
across relations to behave exactly as before, so that non-proxy queries,
`select_related()` without field restriction, and proxy-model queries that never
took this path are unaffected.

**Acceptance criteria**

1. The system SHALL keep computing correct column-load plans for `only()`/`defer()`
   over relations whose targets are ordinary (non-proxy) models, producing the
   same selected columns and results as before this change.
2. WHEN a `QuerySet` uses `select_related()` to include related models without any
   `only()`/`defer()` restriction, THEN it SHALL continue to load and populate
   those related objects fully, exactly as before.
3. The system SHALL continue to support querying, creating, updating, deleting,
   and filtering through proxy models — including proxy-to-proxy hierarchies,
   reverse relations to proxies, and manager/`select_related` usage on proxies —
   with the same results as before this change.
4. WHEN resolving a proxy model to its concrete base for the purpose of keying the
   load plan, THEN the operation SHALL be a no-op for a model that is already
   concrete (a concrete model's concrete model is itself), so no existing
   non-proxy query plan changes.
5. The identity and equality semantics of proxy and concrete model instances
   (a proxy instance and the concrete instance with the same primary key compare
   equal) SHALL remain unchanged.
