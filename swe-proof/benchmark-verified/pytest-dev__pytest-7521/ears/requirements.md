# Requirements: File-descriptor capture must preserve carriage returns verbatim

## Introduction

pytest provides output-capturing fixtures. The file-descriptor-based capture
path (the `capfd` / `capfdbinary` fixtures, implemented in
`src/_pytest/capture.py`) redirects a target file descriptor into a temporary
file and later reads the accumulated bytes back out as text through a text
wrapper (the `EncodedFile` / `io.TextIOWrapper` layer built in
`FDCaptureBinary`).

A regression was introduced whereby this readback applied *universal newline
translation*: a carriage return (`\r`, U+000D) written to the captured stream —
whether standalone or as the first half of a CR+LF pair — was silently rewritten
to a line feed (`\n`, U+000A) when read back via `readouterr()`. Code that
writes progress indicators or other `\r`-terminated output (e.g. reprinting on
the same terminal line) therefore saw its output corrupted when captured, so
tests asserting on the exact captured bytes failed.

The goal is to make the file-descriptor capture readback reproduce the written
character stream **verbatim** — every code point unchanged and in order, with no
newline normalization — while leaving all other capture behavior intact.

## Requirement 1: Carriage returns survive file-descriptor capture unchanged

**User story:** As a test author using the `capfd` fixture, I want captured
output to be returned exactly as it was written, so that assertions on
`\r`-terminated output (such as same-line progress indicators) behave the same
as the program's real output.

**Acceptance criteria**

1. WHEN text ending in a carriage return (`\r`) is written to a captured file
   descriptor and then retrieved with `readouterr()`, THEN the capture layer
   SHALL return a string that ends with that same carriage return and does not
   replace it with a line feed.
2. WHEN text ending in a carriage-return/line-feed pair (`\r\n`) is written to a
   captured file descriptor and then retrieved with `readouterr()`, THEN the
   capture layer SHALL return a string that ends with that exact two-character
   `\r\n` sequence, preserving both characters in order.
3. WHEN any string is written to a captured file descriptor and retrieved with
   `readouterr()`, THEN the returned text SHALL contain the same code points, in
   the same order, as were written — no code point is dropped, inserted, merged,
   or rewritten during readback.
4. The system SHALL NOT perform universal-newline (line-ending normalization)
   translation when decoding file-descriptor-captured output back into text.

## Requirement 2: Existing capture behavior is preserved

**User story:** As a pytest user, I want the newline fix to leave every other
aspect of output capturing working, so that no previously-passing capture
behavior regresses.

**Acceptance criteria**

1. WHEN text ending in a bare line feed (`\n`) is written to a captured file
   descriptor and retrieved with `readouterr()`, THEN the capture layer SHALL
   return a string that ends with that line feed unchanged.
2. The system SHALL continue to decode captured file-descriptor output as UTF-8
   text, replacing any bytes that are not valid UTF-8 rather than raising.
3. The system SHALL keep the `capfd`, `capfdbinary`, `capsys`, and `capsysbinary`
   fixtures functioning for their existing separation of standard-output and
   standard-error streams, including their binary variants returning bytes.
4. The system SHALL keep supporting suspend/resume of capturing and repeated
   `readouterr()` calls without loss or corruption of captured content.
5. The system SHALL preserve the mode/name reporting and the write-through
   behavior of the file-descriptor capture's text wrapper, so that writes are
   flushed to the underlying buffer immediately.
