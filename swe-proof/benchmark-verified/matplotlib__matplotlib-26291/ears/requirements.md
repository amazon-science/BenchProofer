# Requirements: Robust renderer resolution for inset-axes locators

## Introduction

`mpl_toolkits.axes_grid1.inset_locator` provides helpers for creating and
placing *inset axes* inside a host Axes. Inset axes are positioned by an
*axes locator* — a callable installed on the inset Axes that, given the host
Axes and a renderer, computes the inset's bounding box. The relevant locator
callables live in `AnchoredLocatorBase` (base class) and its subclasses
`AnchoredSizeLocator` / `AnchoredZoomLocator` in
`lib/mpl_toolkits/axes_grid1/inset_locator.py`. The user-facing entry point is
the `inset_axes(...)` function in that same module.

An axes locator is invoked in two distinct situations:

1. During normal drawing, where the framework passes a concrete renderer.
2. During bounding-box computation for tight-layout / tight-bbox operations
   (for example, saving a figure with `bbox_inches="tight"`), where the
   framework invokes the locator with **no renderer** (i.e. `renderer` is
   `None`).

In the second situation, `AnchoredLocatorBase.__call__` unconditionally used
the supplied renderer to measure the inset's window extent. Because the caller
passed `None`, the measurement path attempted to reach a renderer through an
object that was not populated, raising `AttributeError: 'NoneType' object has
no attribute '_get_renderer'`. As a result, creating an inset axes and then
saving the figure with `bbox_inches="tight"` failed.

The goal is that an inset-axes locator resolve a usable renderer on its own
when the caller supplies none, so that measuring and positioning the inset
succeeds in both situations — while leaving normal (renderer-supplied) behavior
unchanged.

## Requirement 1: Resolve a renderer when the locator is called without one

**User story:** As a user positioning inset axes, I want the inset locator to
work even when it is invoked without a renderer, so that operations that omit
the renderer (such as tight bounding-box computation) do not crash.

**Acceptance criteria**

1. WHEN an inset-axes locator (`AnchoredLocatorBase.__call__` and its
   subclasses) is invoked with a renderer argument of `None`, THEN the locator
   SHALL obtain a concrete renderer from the host Axes' parent figure before
   computing any extent, rather than attempting to measure with the absent
   renderer.
2. WHEN an inset-axes locator is invoked with a renderer argument of `None`,
   THEN the locator SHALL NOT raise `AttributeError` (nor any other exception)
   arising from the missing renderer, and SHALL return the inset's computed
   bounding box.
3. WHEN an inset-axes locator is invoked with a non-`None` renderer, THEN the
   locator SHALL use that supplied renderer unchanged and SHALL NOT substitute
   a different renderer.
4. The system SHALL derive the fallback renderer from the same figure that owns
   the host Axes passed to the locator, so that the extent is measured against
   the correct figure.

## Requirement 2: Saving a figure with a tight bounding box succeeds for inset axes

**User story:** As a user who added inset axes to a figure, I want to save that
figure with a tight bounding box, so that I get the expected output without an
error.

**Acceptance criteria**

1. WHEN a figure that contains an inset axes created via `inset_axes(...)` is
   saved with the tight bounding-box option (`bbox_inches="tight"`), THEN the
   save SHALL complete successfully without raising an exception.
2. WHEN the tight bounding-box machinery invokes an inset axes' locator without
   a renderer as part of computing the figure's tight extent, THEN that
   invocation SHALL succeed and yield a valid bounding box for the inset.
3. WHEN `inset_axes(...)` is used with only a width and height specified (no
   explicit anchor bounding box), THEN the resulting inset axes SHALL still be
   positionable during tight bounding-box computation without error.

## Requirement 3: Preserve existing inset-axes creation and rendering behavior

**User story:** As an existing user of the inset-axes API, I want all current
inset-axes creation and drawing behavior to keep working, so that this fix
introduces no regressions.

**Acceptance criteria**

1. The system SHALL continue to let `inset_axes(...)` create inset axes for the
   full range of supported argument forms (explicit width/height, sizes given
   relative to the parent, an explicit anchor bounding box and transform, and
   the zoom-based inset variant) without behavioral change.
2. WHEN an inset-axes locator is invoked during normal drawing with a valid
   renderer, THEN it SHALL compute and return the same inset bounding box it did
   before, so that rendered figures containing inset axes are unchanged.
3. The system SHALL keep the direct-call behavior of the locator base class:
   calling the locator with a host Axes and a valid renderer SHALL return the
   inset's transformed bounding box, and the `draw` method SHALL remain
   unsupported (raising a runtime error), unchanged by this fix.
4. The system SHALL preserve all other inset-related behaviors — including inset
   colorbars, marking/zoom indicators between parent and inset, and inset
   positioning helpers — so that figures using these features continue to build
   and render as before.
