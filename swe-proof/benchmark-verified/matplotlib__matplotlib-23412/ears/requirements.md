# Requirements: Honor dash offset when drawing patch edges

## Introduction

In `matplotlib.patches`, a `Patch` (e.g. `Rectangle`, `Ellipse`) can be given a
dashed edge linestyle expressed as an `(offset, onoffseq)` tuple, for example
`linestyle=(10, (10, 10))`. The linestyle setter (`Patch.set_linestyle`) stores
both the dash offset and the on/off sequence, and the getter
(`Patch.get_linestyle`) reports them back unchanged.

However, when the patch is rendered, `Patch.draw` discards the stored dash
offset before handing the dash pattern to the renderer's graphics context: it
draws with an offset forced to zero while keeping the on/off sequence. As a
result, two otherwise-identical patches that differ only in dash offset (e.g.
offsets `0` and `10`) draw with visually identical dashes — the offset has no
effect. This contradicts the behavior of line artists (`Line2D`), where the
offset shifts the dash phase.

The goal is to make `Patch.draw` respect the dash offset that was set via the
linestyle, so that the dash phase of a patch edge reflects the requested
offset, while leaving the stored linestyle, its accessors, and all other patch
drawing behavior unchanged.

## Requirement 1: Patch edge drawing honors the dash offset

**User story:** As a user styling a patch with a dashed edge, I want the dash
offset I supply in the linestyle to shift the dash phase of the drawn edge, so
that I can control where the dashes begin (e.g. to interleave two overlapping
outlines).

**Acceptance criteria**

1. WHEN a visible patch with a dashed edge linestyle is drawn, THEN
   `Patch.draw` SHALL apply the patch's stored dash offset (the first element
   of its scaled dash pattern) to the renderer, rather than substituting a
   fixed offset of zero.
2. WHEN a visible patch with a dashed edge linestyle is drawn, THEN
   `Patch.draw` SHALL apply the patch's stored on/off dash sequence (the second
   element of its scaled dash pattern) to the renderer unchanged.
3. WHEN two patches share the same geometry, linewidth, and on/off dash
   sequence but have different dash offsets, THEN the rendered edges SHALL
   differ in dash phase in accordance with those offsets (they SHALL NOT be
   forced to render identically).
4. WHEN a visible patch with a dashed edge is drawn with a non-zero dash
   offset, THEN the dash phase of the rendered edge SHALL be advanced by that
   offset in the same manner the dash offset shifts the dash phase for line
   artists (`Line2D`), so that the drawn dashes begin at the requested point in
   the on/off cycle rather than always at the start of the cycle.
5. IF the patch is not visible, THEN `Patch.draw` SHALL return without drawing,
   as before.

## Requirement 2: Preserve the stored linestyle, including its offset

**User story:** As a user, I want the linestyle I set on a patch — including a
non-zero dash offset — to be stored and reported back unchanged, so that
querying the patch reflects exactly what I requested.

**Acceptance criteria**

1. WHEN a patch's linestyle is set to a dash tuple `(offset, onoffseq)`, THEN
   `Patch.get_linestyle` SHALL return that same `(offset, onoffseq)` value,
   preserving a non-zero offset.
2. WHEN a patch's linestyle is set to a dash tuple with offset `0`, THEN
   `Patch.get_linestyle` SHALL return that value with offset `0` unchanged.
3. The system SHALL continue to scale the stored dash pattern by the patch's
   linewidth for rendering purposes without altering the offset that
   `Patch.draw` applies relative to that scaling.

## Requirement 3: Preserve all other patch drawing behavior

**User story:** As a maintainer, I want the offset fix to leave every other
aspect of patch construction, styling, and drawing intact, so that existing
behavior does not regress.

**Acceptance criteria**

1. The system SHALL keep the workaround in `Patch.draw` for the PDF and SVG
   renderers whereby a fully transparent facecolor is passed as `None` so that
   hatches are still drawn.
2. The system SHALL keep the existing behavior of default and named linestyles,
   custom on/off linestyles, and linestyle accent aliases as accepted by
   `Patch.set_linestyle`.
3. The system SHALL keep the default linestyle, default capstyle, default
   joinstyle, and default antialiasing of patches unchanged.
4. WHEN a patch is copied or its properties are updated, THEN the patch SHALL
   continue to carry both its unscaled and its scaled dash patterns
   (offset and on/off sequence) as before.
5. The system SHALL keep unchanged all non-linestyle patch behaviors —
   including edge/face color resolution and alpha handling, hatching,
   geometry and containment queries, and the string representation of a patch.
