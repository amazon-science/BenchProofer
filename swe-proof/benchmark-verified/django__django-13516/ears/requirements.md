# Requirements: Make `flush()` work on management-command output streams

## Introduction

Django management commands write user-facing output through a thin wrapper,
`OutputWrapper` (in `django.core.management.base`), which sits in front of the
real `stdout`/`stderr` stream and relays operations to it. The wrapper delegates
unknown attributes to the underlying stream via `__getattr__`, but because it
subclasses `io.TextIOBase`, the base class already provides a no-op `flush()`
method. As a result, `__getattr__` is never consulted for `flush`, and a call to
`wrapper.flush()` does nothing: buffered output is not pushed to the underlying
stream.

This is visible during long-running commands such as `migrate`, where
progress lines (for example, "Applying <migration>...") are meant to appear
immediately but instead stay buffered until the command finishes. The goal is
for a `flush()` request on the wrapper to reach the underlying stream so that
buffered output is emitted right away, while leaving all other wrapper behavior
(writing, styling, attribute delegation, tty detection) unchanged.

## Requirement 1: A flush request on the wrapper reaches the underlying stream

**User story:** As a user running a long management command, I want progress
output to appear as soon as the command flushes it, so that I can see work
happening instead of waiting until the command ends.

**Acceptance criteria**

1. WHEN a caller invokes `flush()` on an `OutputWrapper` instance and the
   underlying stream provides a `flush` operation, THEN the wrapper SHALL invoke
   the underlying stream's `flush` operation exactly once.
2. WHEN a caller invokes `flush()` on an `OutputWrapper` instance whose
   underlying stream provides a `flush` operation, THEN the wrapper's own
   `flush` SHALL NOT be a no-op — the effect SHALL be observable on the
   underlying stream (its `flush` is called), rather than the request being
   silently discarded.
3. IF the underlying stream does not provide a `flush` operation, THEN invoking
   `flush()` on the `OutputWrapper` SHALL complete without error and SHALL NOT
   attempt to call a `flush` operation on that stream.
4. The system SHALL determine whether the underlying stream supports flushing
   before attempting to flush it, so that streams lacking a `flush` operation
   are handled safely.
5. WHEN `flush()` on the wrapper returns, THEN the underlying stream's own
   identity and its support for flushing SHALL be unchanged (the wrapper only
   relays the flush; it does not replace or reconfigure the stream).

## Requirement 2: Preserve existing output-writing behavior

**User story:** As a maintainer, I want the flush fix to leave text writing and
styling behavior intact, so that no existing command output is altered.

**Acceptance criteria**

1. WHEN a caller invokes `write(msg)` on an `OutputWrapper`, THEN the wrapper
   SHALL forward the (styled) text to the underlying stream's `write`
   operation.
2. WHEN `write` is called and the message does not already end with the
   wrapper's configured line ending, THEN the wrapper SHALL append that ending
   before writing.
3. WHEN `write` is called and the message already ends with the configured line
   ending, THEN the wrapper SHALL NOT append a second ending.
4. WHEN a style function is active for the wrapper, THEN `write` SHALL apply it
   to the message before forwarding to the underlying stream.

## Requirement 3: Preserve attribute delegation and stream introspection

**User story:** As a maintainer, I want attribute delegation and tty detection
to keep working, so that code relying on the wrapper as a stand-in for the real
stream is unaffected.

**Acceptance criteria**

1. WHEN code accesses an attribute on the `OutputWrapper` that the wrapper does
   not define itself, THEN the wrapper SHALL return the corresponding attribute
   from the underlying stream.
2. WHEN `isatty()` is invoked on the wrapper, THEN it SHALL report whether the
   underlying stream is a tty (returning a falsey result when the underlying
   stream provides no `isatty` operation).
3. The system SHALL keep the wrapper's line-ending configuration and style
   function accessible and behaving as before this change.
