# Requirements: A public path-replacement operation on collection artists

## Introduction

In `matplotlib.collections`, the base `Collection` artist holds its geometry as
an ordered list of paths, exposed read-only through `get_paths()`. There is no
supported public way to install a *new* list of paths onto an arbitrary
collection: the base class defines `set_paths(paths)` only as a stub that raises
`NotImplementedError`, while the `PathCollection` subclass carries its own
working override. Consumers of other collection subclasses — notably contour
artists (`ContourSet`, a `Collection` subclass) — are therefore forced to mutate
the list returned by `get_paths()` in place (e.g. `cs.get_paths()[:] = ...`) to
swap in transformed paths.

The goal is to make wholesale path replacement a first-class, uniformly
available operation: any collection artist SHALL support `set_paths(paths)` that
replaces its stored path list with the supplied one and marks the artist as
needing a redraw, so that a subsequently rendered figure reflects the new paths.
This must not regress the pre-existing behavior of `PathCollection`, of
`get_paths()`, or of the contour machinery.

## Requirement 1: Base collection supports wholesale path replacement

**User story:** As a developer working with any collection artist, I want a
supported `set_paths` method on the base collection type, so that I can replace
its geometry without reaching into and mutating the list returned by
`get_paths()`.

**Acceptance criteria**

1. WHEN `set_paths(paths)` is called on a `Collection` (base-class) instance with
   a list of paths, THEN the collection SHALL store that supplied list as its
   path collection so that a subsequent call to `get_paths()` returns exactly the
   paths that were supplied.
2. WHEN `set_paths(paths)` is called on a `Collection` instance, THEN the
   collection SHALL mark itself as stale (its staleness flag set to `True`) so
   that the artist is scheduled for re-rendering.
3. The base `Collection.set_paths` operation SHALL be total: it SHALL accept any
   supplied list of paths and complete successfully, and SHALL NOT raise
   `NotImplementedError` (or otherwise reject the request) for a valid list
   argument.
4. WHEN `set_paths` replaces the path list, THEN the collection SHALL leave all
   of its other state (offsets, transforms, colors, and any other attributes)
   unchanged — only the stored path list and the staleness flag are affected.

## Requirement 2: Replacement is available to collection subclasses, including contour artists

**User story:** As a user of contour artists, I want to replace all paths on a
contour set through a single `set_paths` call, so that transformed geometry can
be installed without in-place mutation of the path list.

**Acceptance criteria**

1. WHEN `set_paths(paths)` is called on a contour artist (a `Collection`
   subclass, e.g. `ContourSet`), THEN the artist SHALL adopt the supplied list of
   paths as its geometry, so that its `get_paths()` returns exactly those paths.
2. IF a contour artist has its path list replaced via `set_paths` with the paths
   taken from another contour artist, THEN rendering the receiving artist SHALL
   produce output equivalent to rendering the artist those paths came from
   (i.e. the visible geometry is fully determined by the installed paths).
3. WHEN `set_paths` is used to install a replacement list, THEN the resulting
   behavior SHALL be equivalent to assigning the replacement list wholesale
   (as with `get_paths()[:] = replacement`), replacing the previous paths
   entirely rather than appending to or partially editing them.

## Requirement 3: Preserve existing path-collection and accessor behavior

**User story:** As a maintainer, I want the existing behavior of the specialized
path collection and the path accessors to remain intact, so that adding the
base-class operation introduces no regression.

**Acceptance criteria**

1. The system SHALL continue to support `set_paths(paths)` on `PathCollection`
   with the same observable behavior as before: the supplied paths become the
   collection's stored paths and the collection is marked stale.
2. WHEN `get_paths()` is called on any collection, THEN it SHALL return the
   currently stored list of paths (the same object previously installed by
   construction or by `set_paths`).
3. The system SHALL preserve all existing contour construction, labeling,
   shape-validation, error-reporting, and rendering behavior unchanged; adding
   the path-replacement operation SHALL NOT alter how contours are created,
   validated, drawn, labeled, or removed.
