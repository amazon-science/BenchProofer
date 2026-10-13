# Requirements: Auto-created primary key advisory and inherited primary keys

## Introduction

Django's model system check framework emits an advisory (identifier
`models.W042`) when a model relies on an automatically created primary key and
the project has not opted into a configured default primary-key field type. The
decision is made by the `_check_default_pk` class method on the model base class
in `django/db/models/base.py`, which is invoked as part of a model's `check()`.

When a model inherits from a concrete ancestor model via multi-table
inheritance, Django gives the inheriting model a primary key that is actually a
one-to-one relation back to the ancestor (a link established by the inheritance
mechanism). This inheritance-link field is auto-created, but it does not
represent the inheriting model defining its own primary-key type — the primary
key genuinely belongs to the ancestor. In the affected behavior, the advisory
was being raised for such inheriting models even though the author had already
defined (or inherited) the primary key on the ancestor, producing spurious
`models.W042` warnings for every inheriting model.

The goal is to make the advisory correctly distinguish between a model that
actually leaves its own primary key unspecified and a model whose auto-created
primary key is merely an inheritance link derived from an ancestor, while
preserving all previously correct advisory behavior.

## Requirement 1: Suppress the advisory for inherited link primary keys

**User story:** As a developer using multi-table model inheritance, I want the
auto-created-primary-key advisory to not fire for inheriting models whose
primary key is an inheritance link back to an ancestor, so that I am not warned
repeatedly about a primary key that is already the responsibility of the
ancestor model.

**Acceptance criteria**

1. WHEN a model's primary key is auto-created AND that primary key is a to-one
   relation whose target is the ancestor model it extends via inheritance (an
   inheritance-link relation), THEN `_check_default_pk` SHALL NOT emit the
   `models.W042` advisory for that model, regardless of whether a default
   primary-key field type has been configured.
2. WHEN a model inherits from a concrete ancestor and defines no primary key of
   its own, so that its primary key is an automatically created inheritance-link
   relation, THEN the system SHALL treat the primary key as belonging to the
   ancestor and SHALL NOT report `models.W042` against the inheriting model.
3. WHEN a model inherits from a concrete ancestor and explicitly declares its
   own inheritance-link to-one field, THEN the system SHALL NOT report
   `models.W042` against that inheriting model.
4. IF a model's primary key is auto-created but is NOT an inheritance-link to-one
   relation, THEN the suppression above SHALL NOT apply and the ordinary
   advisory decision (Requirement 2) SHALL govern whether the advisory is
   emitted.

## Requirement 2: Preserve the advisory for genuinely unspecified primary keys

**User story:** As a Django maintainer, I want the advisory to keep firing for
models that truly leave their primary-key type unspecified, so that the original
purpose of the check — nudging projects toward a configured default primary-key
type — is retained.

**Acceptance criteria**

1. WHEN a model's primary key is auto-created AND is not an inheritance-link
   to-one relation AND no default primary-key field type has been opted into at
   either the project level or the owning application level, THEN
   `_check_default_pk` SHALL emit exactly one `models.W042` advisory concerning
   that model.
2. The emitted advisory SHALL carry the model it concerns as its subject and
   SHALL retain the same advisory identifier, message text, and hint text used
   before this change; the hint SHALL reference both the project-level default
   configuration setting and the owning application configuration's
   default-primary-key attribute.
3. WHEN a model explicitly declares its own primary key (so the primary key is
   not auto-created), THEN the system SHALL NOT emit the `models.W042` advisory
   for that model.
4. IF a default primary-key field type has been opted into at the project level,
   THEN the system SHALL NOT emit the `models.W042` advisory for any model on
   that basis.
5. IF a default primary-key field type has been opted into at the owning
   application level, THEN the system SHALL NOT emit the `models.W042` advisory
   for models of that application on that basis.

## Requirement 3: Correct per-model reporting across an inheritance chain

**User story:** As a developer with an inheritance hierarchy, I want the
advisory to be reported against exactly the model that actually leaves its
primary key unspecified, so that warnings are accurate and actionable.

**Acceptance criteria**

1. WHEN a concrete ancestor model leaves its primary key unspecified (its
   primary key is an auto-created field of its own) and an inheriting model
   extends it with an auto-created inheritance-link primary key, THEN the system
   SHALL emit `models.W042` for the ancestor model only and SHALL NOT emit it
   for the inheriting model.
2. WHEN a concrete ancestor model leaves its primary key unspecified and an
   inheriting model extends it while explicitly declaring its own
   inheritance-link to-one field, THEN the system SHALL emit `models.W042` for
   the ancestor model only and SHALL NOT emit it for the inheriting model.
3. WHEN an ancestor model explicitly declares its primary key and another model
   inherits from it, THEN the system SHALL emit no `models.W042` advisory for
   either the ancestor or the inheriting model.
4. The system SHALL evaluate the advisory independently per model, so that
   suppression of the advisory for one model in an inheritance chain SHALL NOT
   affect whether it is emitted for another model in the same chain.
