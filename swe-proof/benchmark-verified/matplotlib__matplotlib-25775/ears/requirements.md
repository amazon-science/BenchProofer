# Requirements: Per-object antialiasing control for text artists

## Introduction

In `matplotlib`, most drawable artists expose a per-object antialiasing
setting that can be configured individually and read back. Text artists
(`matplotlib.text.Text` and its subclass `matplotlib.text.Annotation`) did not
offer this: they always derived their antialiasing behavior from the global
configuration value `rcParams["text.antialiased"]` at drawing time, so callers
could not turn antialiasing on or off for a single piece of text.

This change adds a per-object antialiasing state to text artists — a way to
read it, a way to set it, and a constructor keyword — and threads that state
through the drawing stage so that the raster/vector backends honor the
per-object value instead of consulting the global configuration directly. The
affected code is `matplotlib.text.Text` (constructor, visual-default reset,
state-copy, and drawing), the Agg backend text drawing
(`backends/backend_agg.py`, `RendererAgg.draw_text`), and the Cairo backend
(`backends/backend_cairo.py` — `RendererCairo.draw_text` and the Cairo graphics
context). The goal is that a text artist's antialiasing can be controlled per
object and that its rendered output reflects that per-object choice.

## Requirement 1: Reading and setting a text artist's antialiasing state

**User story:** As a user creating a plot, I want to set and read the
antialiasing state of an individual text artist, so that I can control text
rendering on a per-object basis instead of only globally.

**Acceptance criteria**

1. The system SHALL allow the current antialiasing state of a `Text` object to
   be queried and SHALL report it as a boolean value.
2. The system SHALL allow the antialiasing state of a `Text` object to be
   assigned to a supplied boolean value after the object exists.
3. WHEN a `Text` object's antialiasing state is assigned the value `True`, THEN
   querying that object's antialiasing state SHALL afterward return `True`.
4. WHEN a `Text` object's antialiasing state is assigned the value `False`,
   THEN querying that object's antialiasing state SHALL afterward return
   `False`.
5. WHEN the antialiasing state is assigned more than once, THEN querying it
   SHALL return exactly the value assigned most recently (a later assignment
   overrides any earlier value).
6. WHEN a `Text` object's antialiasing state is changed, THEN the object SHALL
   be marked as stale so it will be redrawn.

## Requirement 2: Default antialiasing state and creation-time value

**User story:** As a user, I want a text artist to fall back to the global
antialiasing configuration when I do not specify one, but to honor an explicit
choice given at creation time, so that existing behavior is preserved while new
control is available.

**Acceptance criteria**

1. WHEN a `Text` object is created without specifying an antialiasing value,
   THEN querying its antialiasing state SHALL return the current value of
   `rcParams["text.antialiased"]`.
2. The `Text` constructor SHALL accept a keyword argument that sets the initial
   antialiasing state, whose unspecified default means "use the global
   configuration value".
3. WHEN a `Text` object is created with its antialiasing keyword set to `True`,
   THEN querying its antialiasing state SHALL return `True` regardless of the
   global configuration value.
4. WHEN a `Text` object is created with its antialiasing keyword set to
   `False`, THEN querying its antialiasing state SHALL return `False`
   regardless of the global configuration value.
5. IF the antialiasing keyword is left unspecified at construction, THEN the
   artist's antialiasing state SHALL equal the global configuration value and
   SHALL NOT be forced to a fixed boolean.
6. WHEN a value is supplied at construction and later a different value is
   assigned, THEN querying the antialiasing state SHALL return the
   later-assigned value.

## Requirement 3: Annotation inherits per-object antialiasing

**User story:** As a user adding annotations, I want annotations to support the
same per-object antialiasing control as plain text, so that behavior is
consistent across text-like artists.

**Acceptance criteria**

1. The `Annotation` constructor SHALL accept the same antialiasing keyword
   argument and apply it with the same semantics as for `Text`.
2. WHEN an `Annotation` is created with its antialiasing keyword set to `True`,
   THEN querying its antialiasing state SHALL return `True`.
3. WHEN an `Annotation` is created with its antialiasing keyword set to
   `False`, THEN querying its antialiasing state SHALL return `False`.
4. WHEN an `Annotation` is created without specifying an antialiasing value,
   THEN querying its antialiasing state SHALL return the current value of
   `rcParams["text.antialiased"]`.
5. WHEN an `Annotation` created with its antialiasing keyword set to `False`
   later has its antialiasing state assigned `True`, THEN querying its
   antialiasing state SHALL afterward return `True`.

## Requirement 4: Drawing honors the per-object antialiasing state

**User story:** As a user, I want the rendered text to reflect the per-object
antialiasing state I selected, so that setting it explicitly has the same
visible effect as setting the corresponding global configuration value.

**Acceptance criteria**

1. WHEN a `Text` artist is drawn, THEN the drawing stage SHALL communicate the
   artist's current antialiasing state to the graphics context used for that
   text, rather than the backend consulting the global configuration value
   directly at glyph-rendering time.
2. WHEN a text artist with an explicit antialiasing state of `False` is
   rendered, THEN its output SHALL be identical to rendering the same text
   while the global configuration value is `False` and no per-object value is
   given.
3. WHEN a text artist with an explicit antialiasing state of `True` is
   rendered, THEN its output SHALL be identical to rendering the same text
   while the global configuration value is `True` and no per-object value is
   given.
4. The graphics context SHALL expose the antialiasing state it was given so
   that backend text-drawing code can read it back when rendering glyphs.
5. Requirement 4.2 and 4.3 SHALL hold for both raster (PNG/Agg) and vector
   (PDF) output.

## Requirement 5: Antialiasing state is preserved when copying artist state

**User story:** As a developer relying on artist copying, I want the per-object
antialiasing state to be carried over when one text artist's state is copied
from another, so that copied artists render consistently.

**Acceptance criteria**

1. WHEN one `Text` artist's visual state is updated from another `Text` artist,
   THEN the destination artist's antialiasing state SHALL be set to match the
   source artist's antialiasing state.

## Requirement 6: Preserve existing text and annotation behavior (regression protection)

**User story:** As an existing user, I want all previously working text and
annotation behavior to remain unchanged, so that adding per-object antialiasing
does not regress anything.

**Acceptance criteria**

1. The system SHALL continue to render text with the global antialiasing
   configuration when no per-object antialiasing value is in effect, preserving
   existing default rendering.
2. The system SHALL preserve existing text rendering behavior for font styles,
   multiline layout, alignment, titles, and existing global-configuration
   antialiasing behavior.
3. The system SHALL preserve existing `Annotation` construction and error
   behavior, including the existing validation of annotation coordinate
   arguments and the existing containment behavior.
4. The system SHALL preserve existing text positioning, window-extent, and
   character-index behavior.
