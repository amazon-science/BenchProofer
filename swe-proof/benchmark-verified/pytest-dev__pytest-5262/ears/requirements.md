# Requirements: EncodedFile should report a text (non-binary) mode

## Introduction

pytest's capture machinery wraps the captured output stream in an
`EncodedFile` object (defined in `src/_pytest/capture.py`). `EncodedFile`
accepts text (`str`) via its `write()` method, encodes it, and forwards the
bytes to an underlying binary buffer. Because `EncodedFile` delegates unknown
attribute lookups to that underlying buffer (via `__getattr__`), any code that
inspects the stream's `mode` sees the buffer's mode string — which contains the
binary indicator `b` (e.g. `"rb+"`).

Some third-party libraries inspect `stream.mode` to decide whether to write
`str` or `bytes`: a `b` in the mode is taken to mean the stream is binary, so
they write `bytes`. Since `EncodedFile.write()` rejects `bytes` on Python 3
(raising `TypeError`), this mismatch causes those libraries to crash when their
output is captured by pytest.

The goal is for `EncodedFile` to advertise a `mode` that reflects how it
actually behaves — a text stream — by removing the binary indicator from the
mode string it exposes, while leaving all other behavior of `EncodedFile`
unchanged.

## Requirement 1: EncodedFile advertises a non-binary (text) mode

**User story:** As a developer whose code inspects the captured output
stream's `mode` to choose between writing text and bytes, I want the captured
stream to report a text mode, so that my code writes `str` and does not crash
under pytest's output capture.

**Acceptance criteria**

1. WHEN the `mode` attribute of an `EncodedFile` instance is accessed, THEN
   `EncodedFile` SHALL return the underlying buffer's mode string with every
   binary-indicator character `b` removed and all remaining characters kept in
   their original order.
2. WHEN the underlying buffer's mode contains one or more `b` characters (for
   example `"rb+"`), THEN the `mode` reported by `EncodedFile` SHALL NOT
   contain any `b` character (for example, `"rb+"` SHALL be reported as `"r+"`).
3. IF the underlying buffer's mode contains no `b` character, THEN the `mode`
   reported by `EncodedFile` SHALL equal the underlying buffer's mode string
   unchanged.
4. The reported `mode` SHALL be derived from the underlying buffer's current
   mode each time it is accessed, rather than from a fixed literal.

## Requirement 2: Text writing and byte rejection are preserved

**User story:** As a maintainer, I want `EncodedFile`'s existing write
semantics to remain intact, so that the new mode reporting does not change how
data is written or validated.

**Acceptance criteria**

1. WHEN `write()` is called with a text (`str`) argument, THEN `EncodedFile`
   SHALL encode that text using its configured encoding and forward the
   resulting bytes to the underlying buffer.
2. IF `write()` is called with a `bytes` argument on Python 3, THEN
   `EncodedFile` SHALL raise a `TypeError` whose message indicates that the
   argument must be `str` and names the offending argument type.
3. The system SHALL continue to delegate attribute lookups other than the ones
   it defines explicitly (such as `mode` and `name`) to the underlying buffer.
4. The `name` attribute of an `EncodedFile` SHALL continue to be returned as a
   string.

## Requirement 3: Captured file-descriptor streams report a text mode

**User story:** As a developer relying on pytest's file-descriptor–level
capture, I want the captured `sys.stdout` (and equivalent captured streams) to
report a text mode, so that libraries inspecting the stream mode behave
correctly under capture.

**Acceptance criteria**

1. WHILE file-descriptor–level output capture is active, WHEN a captured
   standard output stream's `mode` is inspected, THEN the reported mode SHALL
   NOT contain the binary indicator `b`.
2. The captured stream SHALL remain writable with text (`str`) data while
   reporting this non-binary mode.
