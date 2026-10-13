# Requirements: Faithful attribute-error reporting in `SkyCoord` attribute resolution

## Introduction

`astropy.coordinates.SkyCoord` (in `astropy/coordinates/sky_coordinate.py`)
defines a fallback attribute-resolution hook, `SkyCoord.__getattr__`, that
Python invokes only when ordinary attribute lookup on an instance fails. The
hook first attempts several domain-specific resolutions of the requested name
(recognizing frame name aliases, resolving frame attributes registered in the
frame transform graph, delegating to the embedded frame object, and
interpreting the name as another frame to transform to). If one of those
branches resolves the name, it returns the corresponding value.

When none of those branches applies, the previous behavior was to raise an
`AttributeError` whose message was fabricated from the *originally requested*
name and the instance's class name. This is misleading for subclasses that
define a `property` (or other descriptor) whose body accesses some *other*
attribute that does not exist: Python's descriptor protocol surfaces that
inner failure as an `AttributeError`, which causes Python to fall back to
`__getattr__` with the *property's* name — and the fabricated message then
blames the property rather than the genuinely missing inner attribute,
obscuring the real cause during debugging.

The goal is to make the fallback hook, on its non-resolving path, defer to the
object's ordinary attribute-access protocol for the same name so that the
resulting error faithfully reports the name that actually could not be
resolved, while preserving every existing successful resolution behavior.

## Requirement 1: Faithful error propagation on the non-resolving fallback path

**User story:** As a developer subclassing `SkyCoord` with custom properties,
I want an attribute-access failure inside a property body to report the name
that is actually missing, so that I can diagnose which attribute is absent
instead of being misdirected to the property's own name.

**Acceptance criteria**

1. WHEN `SkyCoord.__getattr__` is invoked for a name and none of its
   domain-specific resolution branches (frame-name alias match, frame-attribute
   resolution, embedded-frame delegation, or transform-target interpretation)
   resolves that name, THEN `SkyCoord.__getattr__` SHALL obtain the result by
   performing the object's ordinary attribute-access protocol for that same
   name rather than immediately raising a self-constructed error.

2. WHEN the fallback path defers to the ordinary attribute-access protocol and
   that protocol raises an `AttributeError`, THEN `SkyCoord.__getattr__` SHALL
   allow that `AttributeError` to propagate unchanged, so that the name and
   message it reports are exactly those produced by the ordinary protocol.

3. IF access of a name on a `SkyCoord` (or subclass) instance is served by a
   descriptor (such as a `property`) whose body accesses a further attribute
   that does not exist, THEN the `AttributeError` ultimately raised SHALL
   identify the further missing attribute's name (the name the ordinary
   protocol reports) and SHALL NOT substitute the name of the descriptor whose
   access was originally attempted.

4. The system SHALL NOT, on the non-resolving fallback path, raise an
   `AttributeError` whose reported missing-attribute name is fabricated from
   the originally requested name when the ordinary attribute-access protocol
   would report a different name as the cause.

## Requirement 2: Preserve failure behavior for genuinely absent attributes

**User story:** As a user of `SkyCoord`, I want accessing a plainly
non-existent attribute to still raise `AttributeError`, so that normal Python
attribute semantics and existing error-handling continue to work.

**Acceptance criteria**

1. WHEN a name that no resolution branch handles and that the object does not
   otherwise possess is accessed on a `SkyCoord` (or subclass) instance, THEN
   attribute access SHALL raise `AttributeError`.

2. WHEN such an `AttributeError` is raised for a genuinely absent name, THEN
   the error SHALL reference that requested name as the missing attribute.

3. The system SHALL continue to raise `AttributeError` (rather than any other
   exception type, or none) for attribute names that cannot be resolved,
   preserving compatibility with callers that rely on `hasattr` and on catching
   `AttributeError`.

## Requirement 3: Preserve all existing successful attribute-resolution behavior

**User story:** As a user of `SkyCoord`, I want frame aliases, frame
attributes, embedded-frame delegation, and frame transformations to keep
working exactly as before, so that the fix to error reporting introduces no
behavioral regression.

**Acceptance criteria**

1. WHILE a `SkyCoord` instance holds an initialized coordinate frame, WHEN a
   requested name matches one of the current frame's name aliases, THEN
   `SkyCoord.__getattr__` SHALL return the instance itself for that name as
   before.

2. WHEN a requested name is a frame attribute registered in the frame transform
   graph, THEN `SkyCoord.__getattr__` SHALL return that frame attribute's value
   (from the current frame when it belongs to it, otherwise from the
   instance's stored extra value), unchanged from prior behavior.

3. WHEN a requested public (non-underscore) name is available on the embedded
   frame object, THEN `SkyCoord.__getattr__` SHALL return the value obtained by
   delegating to that embedded frame object.

4. WHEN a requested name designates another coordinate frame to which the
   current frame can be transformed, THEN `SkyCoord.__getattr__` SHALL return
   the result of transforming the instance to that frame.

5. The system SHALL leave the behavior of setting and deleting attributes
   (including immutability of frame-alias and transformable-frame names, and
   validation of frame attributes) unchanged.
