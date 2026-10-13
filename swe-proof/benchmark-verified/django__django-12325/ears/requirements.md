# Requirements: Correct parent-link selection for multi-table inheritance with multiple OneToOne relations

## Introduction

In Django's ORM, a model that uses multi-table inheritance (MTI) is linked to
its concrete parent model by a *parent link*: a `OneToOneField` whose database
column is promoted to become the subclass's primary key. A subclass may
legitimately declare **several** `OneToOneField` relations that point at the
same parent model — for example, one that is explicitly marked
`parent_link=True` and one or more ordinary one-to-one relations used for
unrelated purposes.

The affected code is the model-class assembly logic in
`django/db/models/base.py` (the `ModelBase.__new__` metaclass, where the
collection of parent links is built) and the primary-key preparation logic in
`Options._prepare` in `django/db/models/options.py` (where a parent link is
promoted to primary key).

Before the fix, the collection of parent links recorded **every**
`OneToOneField` that pointed at a parent model, keyed by the target model, using
last-write-wins semantics. When a subclass declared more than one one-to-one
relation to the same parent, an ordinary (non-parent-link) relation could
overwrite the genuine parent link in that mapping. The wrongly selected field
was then promoted to primary key, and a subsequent guard raised
`django.core.exceptions.ImproperlyConfigured` ("Add parent_link=True to ...").
This made the outcome depend on the textual order in which the one-to-one
fields were declared, and rejected perfectly valid models.

The goal is to make parent-link selection deterministic and independent of field
declaration order: only a `OneToOneField` explicitly designated as the parent
link should ever be treated as the parent link, and declaring extra one-to-one
relations to the parent must not cause the model to be misconfigured. Extra
relations that genuinely conflict (e.g. by producing clashing reverse accessor
or query names) must still be reported through the normal model-checking
framework, not by aborting class construction.

## Requirement 1: Only explicitly designated parent links are collected as parent links

**User story:** As a developer using multi-table inheritance, I want only the
one-to-one field I mark as the parent link to be treated as the parent link, so
that adding other one-to-one relations to the same parent does not break my
model.

**Acceptance criteria**

1. WHEN a model class is being assembled and its (and its bases') local fields
   are scanned to build the mapping of parent links, THEN the system SHALL
   record a `OneToOneField` into that mapping only if the field is a one-to-one
   relation AND its relation is designated as the parent link for its target
   model.
2. WHEN a candidate field is a `OneToOneField` that is NOT designated as the
   parent link for its target, THEN the system SHALL NOT record that field in
   the parent-link mapping and SHALL NOT let it displace any entry already
   recorded for the same target model.
3. IF a subclass declares both a one-to-one relation explicitly designated as
   the parent link to a given parent model and one or more additional one-to-one
   relations to that same parent model, THEN the system SHALL select the
   explicitly designated parent-link field as the parent link regardless of the
   order in which the fields are declared.
4. The system SHALL key the parent-link mapping by the identity of the related
   (parent) model, so that at most one parent link is retained per parent model.

## Requirement 2: Valid MTI models with extra one-to-one relations are accepted

**User story:** As a developer, I want a subclass that has a correct parent
link plus other one-to-one relations to the parent to be considered valid, so
that I am not forced into a specific field ordering or forced to remove useful
relations.

**Acceptance criteria**

1. WHEN a subclass of a concrete parent declares an additional
   `OneToOneField` to that parent (beyond the parent link) and relies on Django
   to create the parent link automatically, THEN the system SHALL construct the
   model successfully and the model's validation checks SHALL report no errors
   attributable to parent-link configuration.
2. WHEN a subclass declares an explicit `parent_link=True` one-to-one field
   to its parent together with an additional ordinary `OneToOneField` to the
   same parent, THEN the system SHALL construct the model successfully and its
   validation checks SHALL report no errors attributable to parent-link
   configuration.
3. The system SHALL determine model validity independently of the textual order
   in which the one-to-one fields are declared.

## Requirement 3: No misconfiguration error when promoting a parent link to primary key

**User story:** As a developer, I want the framework to stop rejecting valid
multi-table-inheritance models, so that legitimate models with multiple
one-to-one relations load without error.

**Acceptance criteria**

1. WHEN a subclass has no explicit primary key and one or more parent links,
   THEN the system SHALL promote a collected parent link to be the model's
   primary key.
2. WHEN promoting a parent link to primary key during primary-key preparation,
   THEN the system SHALL NOT raise `ImproperlyConfigured` on the grounds that the
   promoted field is not designated as a parent link.
3. The system SHALL NOT raise `ImproperlyConfigured` merely because a subclass
   declares one-to-one relations to its parent in addition to the parent link.

## Requirement 4: Genuine reverse-name clashes are still reported

**User story:** As a developer, I want conflicting relation names to still be
flagged by model checks, so that removing the old configuration error does not
hide real problems.

**Acceptance criteria**

1. WHEN a subclass declares an additional `OneToOneField` to its parent whose
   reverse accessor or reverse query name clashes with that of the automatically
   created parent link, THEN the system SHALL report the clash through the normal
   model-checking framework as reverse-accessor and reverse-query-name clash
   errors rather than aborting class construction.
2. WHEN reporting such a clash, THEN the system SHALL emit both a reverse
   accessor clash error and a reverse query name clash error for each conflicting
   direction between the two relations, each carrying a hint to add or change a
   `related_name` on one of the two fields.
3. The system SHALL continue to report all previously detected model-checking
   errors for relative fields (reverse accessor clashes, reverse query name
   clashes, ambiguous or invalid relationships, and related-name validation)
   exactly as before for cases unrelated to parent-link selection.

## Requirement 5: Automatically created parent link is marked as a parent link

**User story:** As a developer relying on migrations and model state, I want an
auto-created parent link to be recognizable as a parent link, so that model
state rendering and deconstruction remain accurate.

**Acceptance criteria**

1. WHEN the framework automatically creates the one-to-one field that serves as a
   subclass's parent link, THEN that field SHALL be designated as a parent
   link.
2. WHEN the state/serialized representation of such an auto-created parent-link
   field is produced, THEN its designation as a parent link SHALL be reflected in
   that representation alongside its primary-key designation.
3. The system SHALL keep the existing behavior for models that require an
   automatically added integer primary key when no parent link is present:
   such models SHALL continue to receive an auto-created primary-key field.
