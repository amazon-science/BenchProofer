# Requirements: Honor axes visibility for 3D projections

## Introduction

In Matplotlib, calling `set_visible(False)` on an Axes is expected to hide the
Axes entirely: when the containing figure is rendered, a hidden Axes and all of
its contents must not appear in the output. For ordinary 2D Axes this works
because `matplotlib.axes._base._AxesBase.draw` checks the Axes' visibility flag
at the top of the draw routine and returns immediately when the flag is unset.

The 3D Axes class (`mpl_toolkits.mplot3d.axes3d.Axes3D`) overrides `draw` with
its own implementation and does **not** perform this visibility check. As a
result, a 3D subplot created with `projection='3d'` remains fully rendered even
after `set_visible(False)` is called, contradicting the documented behavior of
`Artist.set_visible` / `Artist.get_visible`.

The goal is to make `Axes3D.draw` respect the Axes visibility flag so that a
hidden 3D Axes produces the same rendered output as if it were absent, while
preserving all existing rendering behavior when the Axes is visible and
preserving the already-correct visibility handling of 2D Axes.

The affected code is the `draw` method of
`mpl_toolkits.mplot3d.axes3d.Axes3D`.

## Requirement 1: A hidden 3D Axes renders nothing

**User story:** As a user building 3D figures, I want `set_visible(False)` on a
3D subplot to actually hide it, so that toggling visibility behaves the same way
it does for 2D Axes.

**Acceptance criteria**

1. WHEN a figure containing an `Axes3D` is drawn AND that Axes' visibility flag
   (as reported by `get_visible()`) is `False`, THEN the `Axes3D.draw` method
   SHALL return without rendering any of that Axes' content.
2. WHILE an `Axes3D` has its visibility flag set to `False`, the rendered figure
   SHALL contain none of that Axes' visual elements — including its background
   patch, its axis panes/spines/ticks/labels, its grid lines, and every child
   artist (such as scatter points, lines, surfaces, and collections) that was
   added to it.
3. WHEN an otherwise-empty figure is drawn after adding a single `Axes3D` whose
   visibility flag is `False`, THEN the resulting rendered image SHALL be
   pixel-identical to the rendered image of a figure to which no Axes content was
   drawn.
4. IF the visibility check causes an early return, THEN `Axes3D.draw` SHALL NOT
   invoke any of its subsequent drawing side effects (such as recomputing/
   applying the aspect, updating the projection matrix, or clearing the stale
   state via view-limit refresh) that would otherwise occur during a normal draw.

## Requirement 2: A visible 3D Axes still renders fully

**User story:** As a user of 3D plots, I want the default (visible) behavior of
3D Axes to be completely unchanged, so that adding a visibility check does not
regress normal rendering.

**Acceptance criteria**

1. WHEN a figure containing an `Axes3D` is drawn AND that Axes' visibility flag
   is `True` (the default), THEN `Axes3D.draw` SHALL render the Axes exactly as
   before — its background patch, axes, grids, and all visible child artists.
2. The system SHALL continue to honor per-artist visibility within a visible
   `Axes3D`, drawing only those child artists whose own visibility flag is
   `True`.
3. WHEN a 3D scatter, line, surface, or other 3D artist is added to a visible
   `Axes3D` and the figure is drawn, THEN that artist SHALL appear in the
   rendered output as it did prior to this change.

## Requirement 3: 2D Axes visibility behavior is preserved

**User story:** As a maintainer, I want the existing 2D visibility behavior to
remain intact, so that the 3D fix does not disturb the general Axes contract.

**Acceptance criteria**

1. WHEN a figure containing an ordinary 2D Axes is drawn AND that Axes'
   visibility flag is `False`, THEN the Axes SHALL render nothing, producing
   output identical to a figure with no Axes content drawn.
2. The system SHALL keep the current behavior whereby a 2D Axes with its
   visibility flag set to `True` renders normally.
3. The system SHALL keep the current behavior whereby an Axes whose visibility
   flag is `False` does not respond to pointer/hit-testing (for example, a
   query for the Axes under a coordinate returns no such Axes while it is
   hidden), so that hidden-Axes handling remains consistent across event
   dispatch and rendering.
