# Requirements: `ProjectState` initializer treats its application-registry argument as a set

## Introduction

`ProjectState` (in `django/db/migrations/state.py`) represents the entire
project's migration state. Its initializer accepts an optional argument naming
the applications to include from the main application registry (the parameter
that carries the unmigrated/"real" apps). Historically the initializer was
defensive: it accepted any iterable for this argument and coerced it into a set,
or substituted an empty set when nothing was supplied.

Since every caller in Django's internal API now supplies this argument as a set
(or omits it), the coercion is no longer warranted. The goal of this change is
to make the initializer treat a supplied value as an invariant that must already
be a set: the initializer should stop silently converting other collection types
and should instead reject any supplied value that is not a set. When no value is
supplied, the initializer must still default to an empty set, and the stored
collection must continue to behave exactly as before for all downstream state
operations (rendering, equality, relation resolution).

The affected code is the constructor of `ProjectState` and the attribute it
assigns for the real-application labels; no public behavior of the surrounding
`ProjectState`/`StateApps` machinery changes for the supported (set-or-absent)
inputs.

## Requirement 1: Reject a supplied non-set application-registry argument

**User story:** As a Django maintainer relying on the internal migration-state
API, I want the `ProjectState` initializer to enforce that a supplied
real-application argument is already a set, so that accidental passing of a
different collection type is surfaced immediately rather than being silently
tolerated.

**Acceptance criteria**

1. WHEN a `ProjectState` is constructed with a real-application argument whose
   value is a collection that is not a `set` (for example a list, tuple, or
   other iterable), THEN the initializer SHALL raise an `AssertionError`.
2. WHEN the supplied real-application argument is not a `set`, THEN the
   initializer SHALL raise the `AssertionError` before storing any
   real-application collection on the instance (construction does not complete
   successfully).
3. The system SHALL apply this rejection only to values that were actually
   supplied and are non-`None`; a not-supplied argument is governed by
   Requirement 2.

## Requirement 2: Default to an empty set when no argument is supplied

**User story:** As a caller who constructs a `ProjectState` without naming any
real applications, I want the initializer to behave exactly as before, so that
existing default construction keeps working.

**Acceptance criteria**

1. WHEN a `ProjectState` is constructed without a real-application argument (the
   argument is omitted or its value is `None`), THEN the initializer SHALL set
   the stored real-application collection to an empty `set`.
2. IF the real-application argument is `None`, THEN the initializer SHALL NOT
   raise an `AssertionError`.
3. WHEN construction with no supplied argument completes, THEN the stored
   real-application collection SHALL be a `set` instance.

## Requirement 3: Store a supplied set unchanged

**User story:** As a caller that already passes a set of real-application
labels, I want the initializer to keep my set as the stored collection, so that
migration state resolves the intended applications.

**Acceptance criteria**

1. WHEN a `ProjectState` is constructed with a real-application argument that is
   a `set` (including an empty set), THEN construction SHALL complete without
   raising, and the stored real-application collection SHALL be a `set`
   containing exactly the supplied labels.
2. The system SHALL NOT reject a supplied set regardless of whether it is empty
   or non-empty.

## Requirement 4: Preserve all existing project-state behavior for supported inputs

**User story:** As a user of Django migrations, I want every existing behavior
of migration state construction, rendering, comparison, and relation resolution
to remain unchanged, so that this refactor introduces no regressions.

**Acceptance criteria**

1. The system SHALL continue to build a `ProjectState` from an application
   registry, including registries that contain swappable models, unused models
   with custom managers, and mixed-case application labels, with the same
   resulting state as before.
2. The system SHALL continue to render a `ProjectState` into a working
   application set (resolving cross-application foreign keys, many-to-many
   relations, model inheritance, and proxy/abstract bases) without altering the
   state's internal model definitions during rendering.
3. WHEN two `ProjectState` instances are compared, THEN equality SHALL hold if
   and only if their model definitions and their real-application collections
   are equal, and inequality SHALL be reported otherwise.
4. The system SHALL continue to use the stored real-application collection to
   decide which model relations are exempt from dangling-reference errors, so
   that including real applications resolves foreign keys that would otherwise
   be reported as dangling.
5. The system SHALL keep every other `ProjectState` capability unchanged for
   supported inputs, including reloading models on relation changes, updating
   related models, and non-destructive construction from an application
   registry.
