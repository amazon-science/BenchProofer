# Requirements: Serialize m2m relations whose related manager uses select_related

## Introduction

Django's serialization framework (`django.core.serializers`) can emit a
model instance's many-to-many relations. For each auto-created m2m through
relation, the serializer iterates the related objects and records their
primary keys. The related set is obtained from the related manager
(`getattr(obj, field.name)`), and — in the common, non–natural-key case — the
serializer restricts the query to load only the primary key column before
iterating.

A defect appears when the related model's default manager configures its base
queryset with `select_related(...)` (for example, a custom `Manager.get_queryset`
that calls `select_related("master")` so a foreign key is followed by default).
In that situation the related manager's queryset already carries a
field-restricted `select_related` state, and the serializer's additional
primary-key-only restriction defers the foreign key that `select_related` wants
to traverse. At SQL-compile time this contradiction makes
`django.db.models.sql.compiler` (via
`django.db.models.query_utils.select_related_descend`) raise
`FieldError: Field <Model>.<field> cannot be both deferred and traversed using
select_related at the same time.`, so serialization fails even though the user
never asked to follow any relation while serializing.

The fix lives in the m2m handling of both serializer backends —
`Serializer.handle_m2m_field` in `django/core/serializers/python.py` (which
underlies the json, jsonl, and yaml formats) and `handle_m2m` in
`django/core/serializers/xml_serializer.py` (the xml format). The related-object
query built for emitting m2m primary keys must neutralize any inherited
field-restricted `select_related` configuration before the primary-key-only
restriction is applied, so that no field is simultaneously deferred and
traversed. The goal is that serializing an m2m relation succeeds regardless of
whether the related manager applies `select_related`, while still loading and
emitting only the related objects' primary keys.

## Requirement 1: Serialize m2m relations when the related manager uses select_related

**User story:** As a developer serializing model instances, I want m2m
relations to serialize successfully even when the related model's manager
follows a foreign key with `select_related` by default, so that I do not have
to add a plain default manager as a workaround.

**Acceptance criteria**

1. WHEN a model instance is serialized and one of its many-to-many relations
   points at a model whose related manager's base queryset was configured with
   a field-restricted `select_related` (e.g. `select_related("master")`), THEN
   the serializer SHALL complete without raising `FieldError`.
2. WHEN building the query used to read an m2m relation's related objects for
   primary-key emission, THEN the serializer SHALL neutralize any inherited
   field-restricted `select_related` state so that no field is left both
   deferred and traversed via `select_related` at SQL-compile time.
3. IF the related manager's queryset carries no `select_related` configuration,
   THEN the serializer SHALL still produce the same serialized output it
   produced before, having introduced no observable change for that case.
4. The system SHALL apply this behavior to every many-to-many field whose
   through relation is auto-created, for each object being serialized.

## Requirement 2: Emit only the related objects' primary keys

**User story:** As a developer, I want m2m serialization to remain efficient
and to record only related primary keys, so that the fix does not load extra
columns or change the serialized representation of m2m fields.

**Acceptance criteria**

1. WHEN serializing an auto-created m2m relation in the non–natural-key case,
   THEN the serializer SHALL restrict the related-object query to load only the
   primary key column, so that the executed SQL does not select any other field
   (including the foreign key that a custom manager's `select_related` would
   otherwise follow).
2. The serializer SHALL emit, for each auto-created m2m field, the list of the
   related objects' primary key values (and for xml, one `object` element per
   related primary key), unchanged in content and order from the pre-fix
   representation for cases that already worked.
3. WHILE loading only the primary key, the serializer SHALL still iterate the
   full set of related objects for that m2m field, emitting one entry per
   related object.

## Requirement 3: Preserve the natural-foreign-key path

**User story:** As a developer using natural keys, I want m2m serialization
with `use_natural_foreign_keys` to keep emitting natural keys, so that the
primary-key-only optimization does not strip data the natural key needs.

**Acceptance criteria**

1. WHEN a serialization is requested with natural foreign keys and the related
   model defines a natural key, THEN the serializer SHALL emit each related
   object's natural key rather than its primary key.
2. WHEN the natural-foreign-key path is taken, THEN the serializer SHALL NOT
   restrict the related-object query to only the primary key, so that all
   fields the natural key computation depends on remain loaded.

## Requirement 4: Honor prefetched related objects

**User story:** As a developer who prefetches m2m relations, I want the
serializer to use the already-prefetched related objects, so that prefetching
continues to avoid extra queries.

**Acceptance criteria**

1. WHEN the object being serialized has a prefetched cache entry for the m2m
   field, THEN the serializer SHALL iterate that prefetched related set instead
   of issuing the primary-key-only query.
2. WHEN no prefetched cache entry exists for the m2m field, THEN the serializer
   SHALL fall back to building and iterating the related-object query described
   in Requirements 1 and 2.

## Requirement 5: Apply the fix uniformly across serialization formats

**User story:** As a developer, I want the corrected m2m behavior in every
built-in serialization format, so that the choice of format does not reintroduce
the failure.

**Acceptance criteria**

1. WHEN serializing to the python-based formats (json, jsonl, and yaml), THEN
   the m2m handling SHALL exhibit the behavior of Requirements 1–4.
2. WHEN serializing to xml, THEN the m2m handling SHALL exhibit the same
   behavior of Requirements 1–4, so that both serializer backends stay
   consistent.

## Requirement 6: Regression protection for existing serialization behavior

**User story:** As a maintainer, I want every serialization behavior that is
unrelated to the m2m `select_related` change to keep working exactly as before,
so that the fix introduces no regressions.

**Acceptance criteria**

1. The system SHALL keep serializing a model instance's regular (non-m2m)
   fields and its foreign keys exactly as before, so that basic serialization
   and its round-trip deserialization continue to produce equivalent instances.
2. WHEN previously-serializable content is deserialized, THEN the system SHALL
   keep allowing the resulting objects to be saved back to the database as
   before.
3. IF a serialization does not involve an m2m relation whose related manager
   applies a field-restricted `select_related`, THEN the system SHALL produce
   output that is identical to the pre-fix behavior for that same input,
   introducing no other observable change to serialized content, format-specific
   encoding rules, or reporting behavior.
