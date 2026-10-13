# Requirements: Unregistering a lookup must invalidate the memoized lookup cache

## Introduction

`django/db/models/query_utils.py` defines `RegisterLookupMixin`, the base that
gives fields, transforms, and related objects a per-class registry of named
lookups and transforms (`class_lookups`). To keep name resolution fast, the
mixin memoizes the merged lookup table: `get_lookups()` is cached (an
`lru_cache`), `_get_lookup()` reads that cache, and `get_lookup()` /
`get_transform()` build on `_get_lookup()`. The classmethod
`_clear_cached_lookups()` busts that memoized cache for the class and all of its
subclasses.

`register_lookup(cls, lookup, lookup_name=None)` adds an entry to
`class_lookups` and then calls `_clear_cached_lookups()` so that the newly
registered lookup is immediately visible. Its inverse,
`_unregister_lookup(cls, lookup, lookup_name=None)`, deletes the entry from
`class_lookups` but historically failed to invalidate the memoized cache. As a
result, after a lookup or transform was unregistered, `get_lookups()`,
`get_lookup()`, and `get_transform()` could keep returning the stale, removed
entry until something else happened to clear the cache — forcing callers (such
as tests that register a lookup temporarily) to manually clear the cache to see
a consistent state.

The goal is to make `_unregister_lookup` symmetric with `register_lookup`:
removing a named lookup must also invalidate the memoized cache so that
subsequent resolution immediately reflects the removal, without any extra manual
cache-clearing step, while preserving every existing registration and
resolution behavior.

## Requirement 1: Unregistering a lookup invalidates the memoized cache

**User story:** As a developer who registers a lookup and later removes it, I
want the registry's cached view to be refreshed automatically on removal, so
that name resolution never returns a lookup that is no longer registered.

**Acceptance criteria**

1. WHEN `RegisterLookupMixin._unregister_lookup(cls, lookup, lookup_name=None)`
   is called with `lookup_name` omitted or `None`, THEN the method SHALL resolve
   the name from `lookup.lookup_name` and remove that entry from
   `cls.class_lookups`.
2. WHEN `_unregister_lookup` is called with an explicit `lookup_name`, THEN the
   method SHALL remove the entry stored under that name from `cls.class_lookups`.
3. WHEN `_unregister_lookup` removes an entry, THEN it SHALL invalidate the
   memoized lookup cache for the class and its subclasses (the same cache-busting
   `register_lookup` performs) so that the removal is reflected on the next
   resolution.
4. IF a lookup is registered on a class and then unregistered via
   `_unregister_lookup`, THEN a subsequent call to that class's `get_lookups()`
   SHALL NOT include the unregistered lookup name, without any separate manual
   cache-clearing step being required.
5. IF a lookup is registered and then unregistered, THEN `get_lookup()` for that
   name SHALL resolve as though the lookup had never been registered (returning
   the inherited/fallback result or `None`, not the removed lookup).

## Requirement 2: Transform resolution reflects unregistration immediately

**User story:** As a developer using a custom transform on a field, I want
`get_transform` to stop returning a transform as soon as I unregister it, so
that I do not have to manually clear the cache to observe a consistent registry.

**Acceptance criteria**

1. WHEN a transform is registered on a field class and then removed with
   `_unregister_lookup`, THEN a subsequent `get_transform(name)` call SHALL NOT
   return the removed transform.
2. WHEN a transform that shadowed a built-in/inherited transform for a given
   name is unregistered, THEN `get_transform(name)` SHALL again resolve to the
   inherited/fallback transform that applied before the temporary registration.
3. The system SHALL make the post-unregistration transform resolution correct
   without requiring the caller to invoke the cache-clearing classmethod
   itself.

## Requirement 3: Preserve existing registration and resolution behavior

**User story:** As a maintainer, I want registration, cache priming, and all
existing lookup/transform resolution paths to keep behaving exactly as before,
so that the fix adds cache invalidation on removal without regressing anything
else.

**Acceptance criteria**

1. The system SHALL keep `register_lookup(cls, lookup, lookup_name=None)`
   behavior unchanged: it adds the entry to `cls.class_lookups` (creating a
   class-local `class_lookups` dict if the class does not already own one),
   invalidates the memoized cache, and returns the registered lookup.
2. WHEN a lookup name is registered, THEN `get_lookups()` SHALL include that
   name and `get_lookup(name)` SHALL resolve to the registered lookup.
3. WHEN `get_lookups()` is called repeatedly with no intervening
   registration or unregistration, THEN it SHALL return a consistent (memoized)
   result; and after a registration or unregistration invalidates the cache, the
   next `get_lookups()` call SHALL recompute and reflect the current
   `class_lookups`.
4. The system SHALL preserve the ordering/override semantics of merged lookups
   across a class and its parents (subclass registrations take precedence over
   inherited ones), so that overridden `get_lookup`/`get_transform` chains
   continue to resolve as before.
5. WHEN a lookup is registered on a class for the duration of an operation and
   then unregistered afterward, THEN operations performed while the lookup is
   registered (such as building constraint or index SQL that references the
   lookup) SHALL succeed, and the lookup SHALL no longer be resolvable once it
   has been unregistered.
6. IF `_unregister_lookup` is asked to remove a name that is not present in
   `cls.class_lookups`, THEN it SHALL raise `KeyError` as before (the removal
   targets the class-local registry entry).
