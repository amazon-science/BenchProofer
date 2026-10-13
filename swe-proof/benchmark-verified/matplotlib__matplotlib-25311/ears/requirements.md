# Requirements: Picklable figures with interactive draggable artists

## Introduction

Matplotlib lets users make a legend or an annotation draggable (for example via
a legend's `set_draggable(True)`, the `draggable=True` option when creating a
legend, or by enabling dragging on an annotation). Internally this behavior is
implemented by the draggable-handler machinery in
`lib/matplotlib/offsetbox.py` — the base class `DraggableBase` and its
subclasses `DraggableLegend` and `DraggableAnnotation`.

When a draggable handler is attached, the resulting figure could no longer be
serialized: attempting to pickle the figure raised a `TypeError` reporting that
a GUI canvas object (e.g. the backend's figure-canvas) could not be pickled.
The root cause is that the handler retained a direct, persistent reference to
the figure's backend canvas in its instance state; that live canvas object is
not serializable, so it poisoned the whole figure's pickle stream.

The goal is that a figure carrying a draggable legend or a draggable annotation
serializes successfully, that the serialized form never embeds a reference to
the figure's backend canvas object, and that the draggable interaction behavior
and general figure serialization continue to work exactly as before.

## Requirement 1: Figures with draggable interactive artists are serializable

**User story:** As a user who has made a legend or an annotation draggable, I
want to pickle (serialize) my figure, so that I can save and later restore my
plot without hitting an error about a non-serializable canvas object.

**Acceptance criteria**
1. WHEN a figure that contains a draggable legend is serialized with the
   pickle protocol, THEN the operation SHALL complete successfully without
   raising an error.
2. WHEN a figure that contains a draggable annotation is serialized with the
   pickle protocol, THEN the operation SHALL complete successfully without
   raising an error.
3. IF a draggable handler is attached to an artist in the figure, THEN
   serializing the figure SHALL NOT raise a `TypeError` (or any error)
   attributable to a backend figure-canvas object being non-serializable.
4. WHEN a figure that has been serialized while carrying a draggable artist is
   later deserialized, THEN the restored figure SHALL be usable, including
   being able to trigger a redraw through its canvas.

## Requirement 2: No backend canvas reference is embedded in the serialized stream

**User story:** As a maintainer, I want the serialized form of a figure to be
independent of the (possibly GUI) backend canvas, so that figures stay portable
across backends and no live canvas object leaks into saved data.

**Acceptance criteria**
1. WHEN a figure carrying a draggable artist is serialized, THEN the resulting
   serialized stream SHALL contain no reference to the figure's backend
   canvas object, regardless of which backend produced the figure.
2. The draggable handler SHALL NOT retain the figure's backend canvas as part
   of its own persisted (serializable) instance state.
3. IF the figure's canvas object is of a type that is itself serializable,
   THEN the serialized stream of the figure SHALL still contain no reference to
   that canvas object introduced by the draggable handler.

## Requirement 3: Canvas access is resolved dynamically from the owning figure

**User story:** As a developer of the draggable machinery, I want the handler
to obtain the canvas on demand from its artist's owning figure, so that the
handler never holds a stale or non-serializable canvas reference yet always
operates on the correct, current canvas.

**Acceptance criteria**
1. WHEN code reads the `canvas` of a draggable handler, THEN the handler SHALL
   return the current canvas of the figure that owns the handler's reference
   artist (i.e. the canvas reached through the reference artist's figure).
2. WHEN the owning figure's canvas changes (for example after the figure is
   deserialized onto a new canvas), THEN a subsequent read of the handler's
   `canvas` SHALL reflect the current canvas rather than any previously seen
   value.
3. The handler's `canvas` SHALL be exposed as a derived/computed accessor whose
   value is recomputed on each access, rather than a value snapshotted once and
   stored on the instance.

## Requirement 4: Draggable interaction behavior is preserved

**User story:** As a user, I want dragging a legend or annotation to keep
working exactly as before, so that fixing the serialization problem does not
regress interactivity.

**Acceptance criteria**
1. WHEN a draggable handler is created, THEN it SHALL determine whether to use
   fast blitting redraws from the combination of the caller's blit request and
   whether the current canvas supports blitting, and SHALL use fast blitting
   only when both hold.
2. WHEN a draggable handler is created, THEN it SHALL register its pick and
   button-release callbacks on the current canvas so that the artist can be
   dragged.
3. WHILE a drag is in progress, the handler SHALL use the current canvas to
   perform motion updates and redraws (including blit-based restore/blit when
   fast blitting is in effect).
4. WHEN a drag ends, THEN the handler SHALL finalize the artist's offset and
   disconnect its motion callback from the current canvas.
5. IF the reference artist is not already pickable when the handler is created,
   THEN the handler SHALL make that artist pickable.

## Requirement 5: General figure serialization remains intact

**User story:** As a user, I want ordinary figures (with the full range of
plot elements) to keep serializing and round-tripping correctly, so that this
fix introduces no regression to existing serialization behavior.

**Acceptance criteria**
1. The system SHALL keep the ability to serialize and deserialize figures that
   do not use any draggable artist, preserving their content across the
   round trip.
2. WHEN a figure is deserialized, THEN the restored figure's canvas SHALL be
   able to perform a draw without error.
3. The system SHALL keep serialization working for figures composed of the
   ordinary range of plot elements and axes configurations, without embedding
   any live backend canvas reference, so that the fix introduces no regression
   for figures that do not use a draggable artist.
