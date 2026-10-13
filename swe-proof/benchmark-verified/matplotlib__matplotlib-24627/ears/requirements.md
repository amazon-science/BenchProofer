# Requirements: Clearing an Axes deparents its former child artists

## Introduction

In Matplotlib, every artist that is added to an Axes (a line, a patch, text,
a collection, an image, and so on) carries two back-references to its owner:
`artist.axes` (the owning `Axes`)
and `artist.figure` (the owning `Figure`). When an artist is removed
individually via `Artist.remove()`, these back-references are unset (both
become `None`), reflecting that the artist is no longer parented.

Clearing an Axes is expected to be equivalent, for the artists it drops, to
removing each of them: after the Axes is cleared it no longer holds any of its
previous children, so those former children should likewise no longer point
back at the Axes or its Figure. However, clearing the Axes only replaced the
Axes' internal child list with a fresh empty list and left the dropped
artists' `.axes` and `.figure` attributes pointing at the now-cleared Axes and
its Figure. Consequently a caller holding a reference to a plotted artist would
still observe `artist.axes` as the (already cleared) Axes and `artist.figure`
as its Figure, which is inconsistent with the behavior of individual removal.

The affected code is the shared clearing routine of `Axes` in
`lib/matplotlib/axes/_base.py` (the internal `__clear` method that backs both
`Axes.cla()` and `Axes.clear()`). The goal is that clearing an Axes deparents
every former child artist — unsetting its `.axes` and `.figure` — while leaving
all other established clearing behavior unchanged.

## Requirement 1: Clearing an Axes deparents each former child artist

**User story:** As a user who keeps a reference to an artist I plotted, I want
clearing that artist's Axes to detach the artist from its Axes and Figure, so
that a cleared artist's ownership references honestly report that it is no
longer parented.

**Acceptance criteria**

1. WHEN an `Axes` is cleared via `Axes.cla()` or `Axes.clear()`, THEN every
   artist that was a child of that Axes immediately before the clear SHALL have
   its `.axes` attribute set to `None`.
2. WHEN an `Axes` is cleared via `Axes.cla()` or `Axes.clear()`, THEN every
   artist that was a child of that Axes immediately before the clear SHALL have
   its `.figure` attribute set to `None`.
3. The deparenting in criteria 1 and 2 SHALL apply uniformly to every child
   artist the Axes held, regardless of the artist's type, and SHALL NOT be
   limited to only a subset of the artist types present.
4. WHILE an artist remains a child of an Axes that has not been cleared or from
   which it has not been removed, the artist's `.axes` SHALL refer to that
   Axes and its `.figure` SHALL refer to that Axes' Figure.

## Requirement 2: Clearing empties the Axes and detaches its former children

**User story:** As a user, I want clearing an Axes to leave it holding none of
its previous artists, so that the Axes starts fresh and its old contents are
fully detached.

**Acceptance criteria**

1. WHEN an `Axes` is cleared, THEN the Axes SHALL no longer retain any of the
   child artists it held before the clear.
2. WHEN an `Axes` is cleared, THEN the detachment of each former child (its
   `.axes` and `.figure` becoming `None`) SHALL be consistent with the state
   produced by removing that artist individually with `Artist.remove()`.

## Requirement 3: Existing clear/cla behavior is preserved

**User story:** As a maintainer, I want the deparenting change to leave all
other established clearing behavior intact, so that adding artist detachment
does not regress unrelated functionality.

**Acceptance criteria**

1. The system SHALL keep `Axes.cla()` and `Axes.clear()` producing equivalent
   clearing behavior on a standard Axes.
2. IF an `Axes` subclass overrides the clearing routine, THEN the system SHALL
   continue to dispatch clearing through that subclass's override so that the
   subclass's own clearing behavior is honored.
3. The system SHALL continue to reset the cleared Axes' own state (such as
   axis scales, limits, and grid configuration) as it did before this change.
4. WHEN shared or twinned Axes are cleared, THEN the system SHALL continue to
   clear each such Axes correctly, preserving their established shared-axis
   behavior.
5. The system SHALL continue to deparent an artist (unset its `.axes`) when the
   artist is removed individually via `Artist.remove()`.
