# Requirements: Allow a legend to be attached to a sub-figure

## Introduction

In `matplotlib`, a `Legend` (`lib/matplotlib/legend.py`) is created against a
*parent* artist, and the `Figure.legend` / sub-figure `legend` method
(`lib/matplotlib/figure.py`) constructs a `Legend` with the figure-like object
as that parent. During construction the `Legend` constructor inspects the kind
of its parent to decide (a) whether the legend is an axes-level legend, (b)
which canvas object it records as its figure, and (c) whether the parent is
acceptable at all.

The figure hierarchy has a common base class `FigureBase` from which both the
top-level figure object (`Figure`) and a nested sub-figure object (`SubFigure`)
derive. A sub-figure is created by calling `subfigures()` on a figure; it is a
genuine drawing surface just like the top-level figure. Previously the
constructor's parent check only recognized the top-level `Figure` class, so
attaching a legend to a sub-figure — e.g. `subfig.legend()` after plotting a
labelled artist on `subfig.subplots()` — raised `TypeError` instead of
producing a legend.

The goal is to make any figure-like parent (top-level figure **or** nested
sub-figure) an accepted, first-class legend parent, while preserving all
existing behavior for axes parents, top-level figure parents, and invalid
parents.

## Requirement 1: Accept a sub-figure as a legend parent

**User story:** As a user building a figure out of sub-figures, I want to call
the `legend` method on a sub-figure and get a legend, so that each sub-figure
can carry its own legend.

**Acceptance criteria**
1. WHEN a `Legend` is constructed with a nested sub-figure object as its
   parent, THEN the constructor SHALL complete successfully without raising an
   error.
2. WHEN a `Legend` is constructed with a nested sub-figure object as its
   parent, THEN the legend SHALL be treated as a non-axes (figure-level) legend
   (its axes-legend flag SHALL be false).
3. WHEN a `Legend` is constructed with a nested sub-figure object as its
   parent, THEN the legend SHALL record that same sub-figure object as its
   associated figure, such that the legend's `figure` attribute is the
   sub-figure object it was attached to (identity equality).
4. WHEN the `legend` method is called on a sub-figure that has a labelled
   artist plotted on one of its axes, THEN it SHALL create a legend, register
   it on that sub-figure, and return the created legend object.

## Requirement 2: Preserve top-level figure legends

**User story:** As a user placing a legend on a whole figure, I want the
existing figure-legend behavior to be unchanged, so that current code keeps
working.

**Acceptance criteria**
1. WHEN a `Legend` is constructed with a top-level figure object as its parent,
   THEN the constructor SHALL complete successfully and treat the legend as a
   non-axes (figure-level) legend.
2. WHEN a `Legend` is constructed with a top-level figure object as its parent,
   THEN the legend SHALL record that same top-level figure object as its
   associated figure.
3. WHEN the `legend` method is called on a top-level figure, THEN it SHALL
   create a legend, register it on that figure, and return the created legend
   object, exactly as before.

## Requirement 3: Preserve axes legends

**User story:** As a user placing a legend on an axes, I want the existing
axes-legend behavior to be unchanged, so that per-axes legends keep working.

**Acceptance criteria**
1. WHEN a `Legend` is constructed with an axes object as its parent, THEN the
   legend SHALL be treated as an axes-level legend (its axes-legend flag SHALL
   be true).
2. WHEN a `Legend` is constructed with an axes object as its parent, THEN the
   legend SHALL record the figure that the axes belongs to as its associated
   figure (not the axes itself).
3. The system SHALL continue to support all existing axes-legend construction
   paths and options unchanged.

## Requirement 4: Reject non-figure, non-axes parents

**User story:** As a developer, I want an invalid legend parent to be rejected
clearly, so that misuse fails fast rather than producing a broken legend.

**Acceptance criteria**
1. IF a `Legend` is constructed with a parent that is neither an axes nor any
   figure-like object (neither a top-level figure nor a nested sub-figure),
   THEN the constructor SHALL raise a `TypeError`.
2. WHEN such a `TypeError` is raised, THEN its message SHALL state that a legend
   needs either an axes or a figure-like object as its parent.
3. The system SHALL make the accept/reject decision solely from the kind of the
   parent: axes and figure-like parents are accepted, everything else is
   rejected; no previously-accepted axes or top-level-figure parent SHALL become
   rejected as a result of this change.
