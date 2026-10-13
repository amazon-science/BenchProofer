# Requirements: Clearing all memoized registry caches

## Introduction

The application registry in `django/apps/registry.py` (the `Apps` class) memoizes
the answers of two independent query methods, each decorated with
`functools.cache`:

- `Apps.get_models(include_auto_created=False, include_swapped=False)` — returns
  the list of installed models, and
- `Apps.get_swappable_settings_name(to_string)` — returns the settings name for a
  swappable model reference, or `None`.

`Apps.clear_cache()` is documented as clearing *all* internal caches, for methods
that alter the app registry; it is invoked whenever the registry contents may
have changed (for example from `set_available_apps`, `unset_available_apps`,
`set_installed_apps`, and `unset_installed_apps`). However, `clear_cache()`
discards only the `get_models` memoized results and leaves the
`get_swappable_settings_name` memoized results in place, so a stale swappable
settings answer can survive a call that is supposed to reset the registry state.

The goal is to make `clear_cache()` honor its contract: after it runs, every
memoized result of both cached query methods must be gone, so that the next call
recomputes from the current registry contents, while all other behavior of the
registry is preserved.

## Requirement 1: clear_cache discards the swappable-settings-name cache

**User story:** As a developer resetting the app registry between runs, I want
`Apps.clear_cache()` to drop the memoized `get_swappable_settings_name` answers,
so that a previously cached swappable-settings result cannot be served after the
registry state has been reset.

**Acceptance criteria**
1. WHEN `Apps.clear_cache()` is called, THEN the registry SHALL discard every
   memoized result of `get_swappable_settings_name`.
2. IF `get_swappable_settings_name` had been called before `clear_cache()` so
   that its cache held one or more memoized entries, THEN after `clear_cache()`
   returns, `Apps.get_swappable_settings_name.cache_info().currsize` SHALL be `0`.
3. WHEN `get_swappable_settings_name` is called after a `clear_cache()`, THEN it
   SHALL recompute its answer from the current registry contents rather than
   return a value memoized before the `clear_cache()` call.

## Requirement 2: clear_cache continues to discard the models cache

**User story:** As a developer resetting the app registry, I want
`Apps.clear_cache()` to keep clearing the memoized `get_models` answers, so that
the existing cache-reset behavior is not regressed by the fix.

**Acceptance criteria**
1. WHEN `Apps.clear_cache()` is called, THEN the registry SHALL discard every
   memoized result of `get_models`.
2. IF `get_models` had been called before `clear_cache()` so that its cache held
   one or more memoized entries, THEN after `clear_cache()` returns,
   `Apps.get_models.cache_info().currsize` SHALL be `0`.

## Requirement 3: clear_cache preserves unrelated registry state and refresh

**User story:** As a maintainer of the app registry, I want `clear_cache()` to
leave the rest of the registry untouched, so that clearing the caches does not
change readiness or corrupt per-model metadata.

**Acceptance criteria**
1. WHEN `Apps.clear_cache()` is called, THEN it SHALL leave the registry's
   readiness flag (`self.ready`) unchanged.
2. WHILE `self.ready` is true, WHEN `clear_cache()` runs, THEN it SHALL still
   expire the per-model `_meta` metadata caches of every installed model without
   refilling the `get_models` result cache.
3. The system SHALL NOT require `get_swappable_settings_name` or `get_models` to
   be repopulated by `clear_cache()` itself; both caches SHALL be left empty
   until the next corresponding query recomputes an answer.

## Requirement 4: cached query methods keep their existing semantics

**User story:** As a consumer of the app registry, I want `get_models` and
`get_swappable_settings_name` to keep returning correct values, so that adding
the cache clearing does not alter their observable results.

**Acceptance criteria**
1. The system SHALL keep `Apps.get_models(include_auto_created, include_swapped)`
   returning the list of installed models honoring both inclusion flags, exactly
   as before the change.
2. The system SHALL keep `Apps.get_swappable_settings_name(to_string)` returning
   the swappable settings name for a swappable model reference and `None` when the
   reference is not swappable, exactly as before the change.
3. WHEN `set_available_apps`, `unset_available_apps`, `set_installed_apps`, or
   `unset_installed_apps` is called, THEN the registry SHALL end with both cached
   query methods cleared, so that subsequent queries reflect the changed set of
   installed apps.
