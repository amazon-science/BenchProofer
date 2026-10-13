# Requirements: AnnotationBbox group id must reach SVG output

## Introduction

When a figure contains an `AnnotationBbox` artist (from
`matplotlib.offsetbox`), a user can attach a group identifier to it with
`Artist.set_gid(...)`. For most artists this identifier is emitted into a
structured vector output such as SVG so the corresponding element can be
located afterwards. `AnnotationBbox`, however, does not wrap its drawing in a
grouping element, so its group id is lost: the saved SVG contains the image and
box but no element carrying the requested id.

The affected code is `AnnotationBbox.draw` in `lib/matplotlib/offsetbox.py`.
That method draws the artist's constituent parts (an optional connecting arrow,
the background patch, and the wrapped offset box) directly onto the renderer
without opening a grouping element. Renderers expose
`RendererBase.open_group(s, gid=None)` / `RendererBase.close_group(s)` for
exactly this purpose; the SVG renderer
(`lib/matplotlib/backends/backend_svg.py`) turns an opened group into a `<g>`
element whose `id` is the supplied gid.

The goal is to make `AnnotationBbox.draw` enclose the drawing of its parts
between a group-open marker that carries the artist's group id and a matching
group-close marker, so the group id survives into the SVG output — while
leaving unchanged both the drawing order of the parts and the grouping behavior
of every other artist and of the SVG renderer itself.

## Requirement 1: AnnotationBbox drawing is wrapped in a group carrying its gid

**User story:** As a user annotating a figure with an image via
`AnnotationBbox`, I want the group id I set with `set_gid` to appear in the
saved SVG, so that I can locate and post-process that annotation in the output
document.

**Acceptance criteria**

1. WHEN an `AnnotationBbox` artist is drawn onto a renderer and the artist is
   visible and its position can be resolved, THEN `AnnotationBbox.draw` SHALL
   open a grouping element on the renderer before drawing any of the artist's
   constituent parts.
2. WHEN `AnnotationBbox.draw` opens that grouping element, THEN it SHALL pass
   the artist's current group id (the value returned by `get_gid()`, which may
   be unset) as the group id argument of the renderer's group-open call.
3. WHEN `AnnotationBbox.draw` opens that grouping element, THEN it SHALL tag the
   group with the artist's class name as the group label.
4. WHEN an `AnnotationBbox` has finished drawing all of its constituent parts,
   THEN `AnnotationBbox.draw` SHALL close the grouping element with a
   group-close marker tagged with the same class-name label used to open it.
5. The system SHALL emit exactly one matching group-open / group-close pair per
   `AnnotationBbox.draw` invocation that produces drawing output, with the
   group-open preceding and the group-close following all part-draws.

## Requirement 2: The gid group encloses the whole annotation, preserving draw order

**User story:** As a user, I want the id-bearing group to contain the entire
annotation (arrow, box, and image), so that the id labels the annotation as a
whole and the annotation still renders identically.

**Acceptance criteria**

1. WHEN a visible, position-resolvable `AnnotationBbox` is drawn, THEN
   `AnnotationBbox.draw` SHALL draw its constituent parts in the order:
   the connecting arrow (when present), then the background patch, then the
   wrapped offset box.
2. IF the `AnnotationBbox` has a connecting arrow, THEN the arrow draw SHALL
   occur inside the opened group (after the group-open and before the
   group-close).
3. The system SHALL place both the background patch draw and the wrapped
   offset box draw inside the opened group.
4. WHEN the annotation is drawn, THEN resolving/updating the artist's positions
   SHALL NOT itself emit any grouping marker, and SHALL be treated as
   ordering-neutral relative to the group-open marker such that no constituent
   part is drawn outside the group.

## Requirement 3: Invisible or unresolvable annotations emit nothing

**User story:** As a user, I want an annotation that is hidden or cannot be
placed to produce no output at all, so that no stray group or empty element
appears in the SVG.

**Acceptance criteria**

1. IF an `AnnotationBbox` is not visible, THEN `AnnotationBbox.draw` SHALL
   return without opening a group, drawing any part, or emitting any marker.
2. IF an `AnnotationBbox`'s position cannot be resolved for the target
   renderer, THEN `AnnotationBbox.draw` SHALL return without opening a group,
   drawing any part, or emitting any marker.

## Requirement 4: SVG renders an opened gid group as a `<g>` element with that id

**User story:** As a user saving to SVG, I want the group id to become the `id`
attribute of the group element, so that the exact string I set is discoverable
in the SVG text.

**Acceptance criteria**

1. WHEN the SVG renderer opens a group and a non-empty group id is supplied,
   THEN it SHALL emit a group element whose `id` attribute is exactly that
   supplied group id string, unmodified.
2. WHEN the SVG renderer opens a group and no group id (or an empty one) is
   supplied, THEN it SHALL emit a group element whose `id` is derived from the
   group label instead, so that unlabeled groups remain distinguishable.
3. WHEN an `AnnotationBbox` carrying a user-set group id is saved to SVG, THEN
   the resulting SVG document SHALL contain a group element whose `id`
   attribute equals that user-set group id string.

## Requirement 5: Existing SVG grouping and drawing behavior is preserved

**User story:** As a maintainer, I want this change to affect only the missing
`AnnotationBbox` grouping, so that all other SVG output and artist behavior is
unchanged.

**Acceptance criteria**

1. The system SHALL keep the existing behavior in which artists that already
   emit group ids into SVG (for example via `set_gid`) continue to do so
   unchanged.
2. The system SHALL keep every existing group-open / group-close pairing
   balanced, so that grouping elements in the SVG output remain properly nested
   and closed.
3. The system SHALL keep unchanged the drawn appearance and position of an
   `AnnotationBbox` and its arrow, patch, and offset box; adding the grouping
   markers SHALL NOT alter what geometry or images are drawn.
4. The system SHALL keep unchanged the group-emission and drawing behavior of
   all other artists and renderer backends not involved in this fix.
