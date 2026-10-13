## Introduction

Matplotlib lets users register a colormap in the colormap registry under a
lookup name that may differ from the colormap object's own display name
(the `name` attribute). This happens, for example, when a user takes a builtin
colormap such as `viridis`, adjusts its extremes with `with_extremes(...)`,
and registers the resulting object under a new name without updating the
object's `name` attribute.

Two problems arise from the historical behavior:

1. `matplotlib.colors.Colormap.__eq__` treats two colormaps as unequal whenever
   their `name` attributes differ, even when they produce identical colors.
   This makes a relabelled-but-otherwise-identical colormap compare unequal to
   its source and interferes with round-tripping a colormap through the
   registry.
2. `matplotlib.cm.ColormapRegistry.register` stores a copy of the colormap
   under the requested lookup name, but leaves that copy's `name` attribute set
   to whatever the original object carried. A later lookup by the registered
   name therefore returns an object whose reported `name` disagrees with the
   name it was fetched under, which breaks downstream lookups that use the
   object's own `name` (e.g. the `pyplot` set-cmap / imshow path).

The goal is to make colormap equality depend only on color-producing content
(not on the display name), and to make registration stamp the stored copy's
`name` with the registration name, so that a colormap looked up by its
registered name both reports that name and compares equal to the colormap that
was registered. The affected modules are `lib/matplotlib/colors.py`
(`Colormap.__eq__`) and `lib/matplotlib/cm.py`
(`ColormapRegistry.register`).

## Requirement 1: Colormap equality ignores the display name

**User story:** As a user who relabels a colormap, I want two colormaps that
produce identical colors to compare equal regardless of their display names, so
that renaming a colormap does not change what it is considered to be.

**Acceptance criteria**

1. WHEN two `Colormap` instances are compared for equality and they differ only
   in their `name` attribute (their out-of-range/extend behavior and their fully
   initialized lookup tables are otherwise identical), THEN the equality
   comparison SHALL report them as equal.
2. WHEN two `Colormap` instances have equal `name` attributes but their fully
   initialized lookup tables differ, THEN the equality comparison SHALL report
   them as not equal.
3. IF the two `Colormap` instances have initialized lookup tables of different
   sizes, THEN the equality comparison SHALL report them as not equal.
4. WHEN two `Colormap` instances differ in the attribute controlling colorbar
   extension behavior, THEN the equality comparison SHALL report them as not
   equal, regardless of their names.
5. IF the object being compared against is not a `Colormap` instance, THEN the
   equality comparison SHALL report them as not equal.
6. The equality comparison SHALL initialize each colormap's lookup table as
   needed before comparing lookup tables, and SHALL decide equality by
   element-for-element comparison of those tables together with the colorbar
   extension attribute, and SHALL NOT consider the `name` attribute.

## Requirement 2: Registration stamps the stored colormap with the registered name

**User story:** As a user registering a colormap under a chosen name, I want the
registered colormap to report that name, so that later lookups which rely on the
colormap object's own name work correctly.

**Acceptance criteria**

1. WHEN a colormap whose display name differs from the requested registration
   name is registered in the registry, THEN the registry SHALL store a copy
   whose `name` attribute equals the registration name.
2. WHEN a colormap is subsequently looked up by the name it was registered
   under, THEN the returned colormap SHALL report that registration name as its
   `name` attribute.
3. WHEN a colormap is registered under a name and then looked up by that name,
   THEN the returned colormap SHALL compare equal to the colormap that was
   registered (its color-producing content being preserved by registration).
4. WHILE stamping the stored copy's name, the registry SHALL preserve all
   color-producing content of the registered colormap (its out-of-range/extend
   behavior and its lookup table), changing only the display name.
5. IF the registered colormap's display name already equals the registration
   name, THEN the registry SHALL leave the stored copy's color-producing content
   and name unchanged.

## Requirement 3: Preserve existing registration and lookup behavior

**User story:** As a maintainer, I want the existing registry safeguards and
snapshot semantics to remain intact, so that the name-handling fix does not
regress unrelated behavior.

**Acceptance criteria**

1. The registry SHALL continue to store an independent copy of the colormap at
   registration time, so that later mutations of the original colormap object do
   not alter the registered colormap.
2. IF a colormap is registered under a name that is already present in the
   registry and overwriting is not explicitly forced, THEN the registry SHALL
   raise a `ValueError` and SHALL NOT replace the existing entry.
3. IF registration is requested under a name that would overwrite a builtin
   colormap and such overriding is not permitted, THEN the registry SHALL raise
   a `ValueError`.
4. WHEN no registration name is supplied, THEN the registry SHALL use the
   colormap object's own display name as the registration name.
5. WHEN a name that is not present in the registry is requested for lookup, THEN
   the registry SHALL raise an error identifying the unrecognized name.
