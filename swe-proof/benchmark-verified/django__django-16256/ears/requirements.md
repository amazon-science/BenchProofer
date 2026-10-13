# Requirements: Async creation helpers on related managers

## Introduction

Django's related managers — the manager objects returned when accessing a
relation from a model instance — expose synchronous `create()`,
`get_or_create()`, and `update_or_create()` helpers. Each of these helpers is
*scope-aware*: it forces the relation's binding into the operation so that a new
or matched object is automatically associated with the owning instance. For a
reverse many-to-one (foreign key) relation the helper sets the foreign-key
field to the owning instance; for a many-to-many relation it also creates the
intermediate ("through") association; for a generic (content-type) relation it
sets both the content-type and object-id fields to the owning instance.

An async-compatible interface was previously added at the queryset layer. As a
side effect, related managers inherited async helpers *from the queryset* rather
than owning their own — so awaiting an async create on a related manager ran the
plain queryset operation and did **not** apply the relation's scope binding. The
goal of this change is to give the affected related managers their own async
helpers `acreate()`, `aget_or_create()`, and `aupdate_or_create()` that mirror
their synchronous counterparts exactly, including the scope binding, while
preserving all existing synchronous behavior.

Affected code:
`django/db/models/fields/related_descriptors.py` (the reverse many-to-one
related manager built by `create_reverse_many_to_one_manager` and the
many-to-many related manager built by `create_forward_many_to_many_manager`,
which serves both the forward and reverse directions) and
`django/contrib/contenttypes/fields.py` (the generic related manager built by
`create_generic_related_manager`).

## Requirement 1: Async create on related managers

**User story:** As a developer using Django's async ORM interface, I want to
await creation of a related object through a related manager, so that the new
object is created and correctly associated with the owning instance without
blocking the event loop.

**Acceptance criteria**

1. The system SHALL provide an async `acreate` helper on the reverse
   many-to-one related manager, on the many-to-many related manager (in both
   the forward and reverse directions), and on the generic related manager.
2. WHEN `acreate` is awaited on a related manager with a set of keyword
   arguments, THEN the manager SHALL create and persist a new related object
   with those field values and SHALL return that newly created object.
3. WHEN `acreate` is awaited on a reverse many-to-one related manager, THEN the
   created object's foreign-key field SHALL reference the owning instance, and
   the object SHALL be retrievable through that same related manager.
4. WHEN `acreate` is awaited on a generic related manager, THEN the created
   object's content-type and object-id fields SHALL identify the owning
   instance, and the object SHALL be retrievable through that same related
   manager.
5. WHEN `acreate` is awaited on a many-to-many related manager, THEN the
   intermediate association between the owning instance and the created object
   SHALL be established so that the created object appears in the relation, and
   an optional `through_defaults` mapping SHALL be accepted and applied to the
   intermediate association.
6. The system SHALL produce, from awaiting `acreate`, exactly the object that
   the manager's synchronous create helper would produce and persist for the
   same arguments (same field values, same relation binding).
7. The async `acreate` helper SHALL be marked as altering data, consistent with
   its synchronous counterpart.

## Requirement 2: Async get-or-create on related managers

**User story:** As a developer using Django's async ORM interface, I want to
await get-or-create through a related manager, so that I either retrieve the
existing associated object or create a new correctly associated one.

**Acceptance criteria**

1. The system SHALL provide an async `aget_or_create` helper on the reverse
   many-to-one related manager, on the many-to-many related manager (in both
   the forward and reverse directions), and on the generic related manager.
2. WHEN `aget_or_create` is awaited with a set of lookup arguments, THEN the
   manager SHALL return a pair consisting of the object and a boolean
   indicating whether the object was newly created.
3. IF no matching related object exists within the relation's scope, THEN
   awaiting `aget_or_create` SHALL create and persist a new object associated
   with the owning instance and SHALL report it as newly created.
4. IF a matching related object already exists within the relation's scope,
   THEN awaiting `aget_or_create` SHALL return that existing object and SHALL
   report it as not newly created, without creating a duplicate.
5. WHEN `aget_or_create` is awaited, THEN the relation binding SHALL be applied
   the same way as for the manager's synchronous get-or-create helper: the
   owning instance's foreign key for a reverse many-to-one relation, the
   content-type and object-id for a generic relation, and the intermediate
   association (honoring an optional `through_defaults` mapping) for a
   many-to-many relation.
6. The system SHALL produce, from awaiting `aget_or_create`, exactly the
   object-and-created-flag result that the manager's synchronous get-or-create
   helper would produce for the same arguments.
7. The async `aget_or_create` helper SHALL be marked as altering data,
   consistent with its synchronous counterpart.

## Requirement 3: Async update-or-create on related managers

**User story:** As a developer using Django's async ORM interface, I want to
await update-or-create through a related manager, so that a matching associated
object is updated or a new correctly associated one is created.

**Acceptance criteria**

1. The system SHALL provide an async `aupdate_or_create` helper on the reverse
   many-to-one related manager, on the many-to-many related manager (in both
   the forward and reverse directions), and on the generic related manager.
2. WHEN `aupdate_or_create` is awaited with lookup arguments and defaults, THEN
   the manager SHALL return a pair consisting of the object and a boolean
   indicating whether the object was newly created.
3. IF no matching related object exists within the relation's scope, THEN
   awaiting `aupdate_or_create` SHALL create and persist a new object
   associated with the owning instance and SHALL report it as newly created.
4. IF a matching related object already exists within the relation's scope,
   THEN awaiting `aupdate_or_create` SHALL update that object with the supplied
   defaults, persist the change, and report it as not newly created.
5. WHEN `aupdate_or_create` is awaited, THEN the relation binding SHALL be
   applied the same way as for the manager's synchronous update-or-create
   helper: the owning instance's foreign key for a reverse many-to-one
   relation, the content-type and object-id for a generic relation, and the
   intermediate association (honoring an optional `through_defaults` mapping)
   for a many-to-many relation.
6. The system SHALL produce, from awaiting `aupdate_or_create`, exactly the
   object-and-created-flag result that the manager's synchronous
   update-or-create helper would produce for the same arguments.
7. The async `aupdate_or_create` helper SHALL be marked as altering data,
   consistent with its synchronous counterpart.

## Requirement 4: Async helpers route through the related manager, not the plain queryset

**User story:** As a developer, I want the async related-manager helpers to
behave like their synchronous related-manager counterparts, so that the
relation scope is always applied and awaiting an async helper never falls back
to an unscoped queryset operation.

**Acceptance criteria**

1. The system SHALL define `acreate`, `aget_or_create`, and `aupdate_or_create`
   directly on each affected related manager rather than allowing them to be
   inherited from the underlying queryset interface.
2. WHEN any of `acreate`, `aget_or_create`, or `aupdate_or_create` is awaited on
   a related manager, THEN the resulting object SHALL be scoped to the owning
   instance exactly as the manager's corresponding synchronous helper scopes it
   — never left unassociated or bound to a caller-chosen value that overrides
   the relation's own binding.
3. The system SHALL run the underlying synchronous work in a manner that does
   not block the running event loop, and each async helper SHALL be awaitable
   and SHALL yield its result upon completion.

## Requirement 5: Preserve existing synchronous and relation behavior

**User story:** As a maintainer, I want the existing synchronous helpers and all
other related-manager behavior to remain unchanged, so that adding async helpers
introduces no regressions.

**Acceptance criteria**

1. The system SHALL keep the existing synchronous `create`, `get_or_create`, and
   `update_or_create` helpers on all related managers with their current
   behavior, including their relation scoping and their data-altering marking.
2. The system SHALL keep all other related-manager operations — such as
   retrieving related objects, adding, removing, setting, clearing, and
   prefetching — behaving exactly as before.
3. WHEN a many-to-many synchronous helper is called with a `through_defaults`
   mapping, THEN that mapping SHALL continue to be applied to the intermediate
   association as before.
4. The system SHALL leave the queryset-level async interface unchanged; the new
   helpers SHALL be additions to the related managers and SHALL NOT remove or
   alter behavior available elsewhere.
