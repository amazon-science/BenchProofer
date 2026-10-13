# Requirements: Faithful round-trip of FITS string card values containing consecutive single quotes

## Introduction

In `astropy.io.fits`, a header card holds a keyword and a value. String values
are stored in the 80-column card *image* using the FITS quoting convention: the
value is delimited by single quotes and any literal single-quote character
inside the value is written as two consecutive single quotes. When a string
value is too long to fit in a single 80-column card, it is serialized across
several physical cards using the CONTINUE convention, and reassembled on parse.

The value/comment portion of a (sub)card is matched with a regular expression
and the captured string is post-processed before the pieces are joined back
together. This reassembly path (in `Card._split`, `astropy/io/fits/card.py`) is
where the defect lives.

Symptom (reported by users): constructing a `Card` with a long string value
that contains a pair of single quotes (`''`), serializing it to its card image
(`str(card)` / `card.image`), and parsing it back with `Card.fromstring`
sometimes yields a *different* value — one of the doubled single quotes is
dropped, so `...''` becomes `...'`. Whether the corruption occurs depends on the
length of the value and where the `''` falls relative to the card boundaries, so
it is intermittent. The goal is to make the create → serialize → parse round
trip preserve the value exactly for every string, in particular for values that
contain consecutive single-quote characters.

The affected component is the string-value handling of `astropy.io.fits.Card`,
specifically the code path that splits/reassembles long (CONTINUE-convention)
string card values and the regular expression that isolates the quoted string
from an optional trailing comment.

## Requirement 1: Exact round-trip of long string values containing consecutive single quotes

**User story:** As a user writing FITS headers, I want long string values that
contain double single quotes to survive a serialize-and-reparse cycle unchanged,
so that my metadata is never silently corrupted.

**Acceptance criteria**

1. WHEN a `Card` is created with a keyword and a string value, and that card's
   image is parsed back with `Card.fromstring`, THEN the parsed card's `value`
   SHALL be equal to the original string value.
2. WHEN the original string value is long enough to require the CONTINUE
   convention (i.e. its serialized image spans more than one physical 80-column
   card), THEN criterion 1 SHALL still hold.
3. WHEN the original string value contains one or more pairs of consecutive
   single-quote characters (`''`) at any position within the value, THEN the
   reparsed value SHALL be equal to the original value exactly, for every string
   regardless of what precedes or surrounds such a pair, retaining both
   single-quote characters of every such pair together with all other characters
   of the value; the reparser SHALL NOT collapse a `''` pair into a single `'`,
   and it SHALL NOT drop any of the value's characters.
4. The system SHALL preserve this round-trip fidelity regardless of the byte
   offset at which the doubled single quotes fall relative to card boundaries;
   i.e. correctness SHALL NOT depend on the length of the value.

## Requirement 2: General consistency between escaping on write and unescaping on read

**User story:** As a maintainer, I want a single, consistent quoting convention
applied on serialization and reversed on parsing, so that no doubling or
un-doubling of quotes is applied more than once.

**Acceptance criteria**

1. The system SHALL represent each literal single-quote character within a
   string card value as two consecutive single quotes in the card image, and
   SHALL reverse exactly that transformation when parsing the image back into a
   value.
2. WHEN a serialized long string card is reassembled from its continuation
   segments, THEN the value contributed by each segment SHALL be taken as the
   content matched between its delimiting quotes, with only trailing padding
   whitespace removed, and SHALL NOT have an additional `''`→`'` reduction
   applied to it.
3. WHEN the regular expression that separates the quoted string from an optional
   trailing comment is applied to a segment's value/comment text, THEN it SHALL
   match the segment's field in its entirety (up to the end of that text) so
   that the closing quote of the value is identified correctly and no valid
   value is truncated at an interior quote pair.
4. IF a segment's value/comment text does not match the expected quoted-string
   pattern, THEN the reassembly SHALL fall back to treating the text verbatim
   (as it did before), so that malformed cards are not newly rejected.

## Requirement 3: Preserve existing string, comment, and header behavior (regression protection)

**User story:** As an existing user, I want all previously correct card and
header behavior to keep working, so that fixing the doubled-quote bug introduces
no regressions.

**Acceptance criteria**

1. WHEN a short string value (one that fits in a single 80-column card) is
   created and reparsed, THEN its reparsed `value` SHALL equal the original,
   including values that contain single or doubled quote characters.
2. WHEN a long string value carries a trailing comment, THEN parsing the
   serialized card back SHALL recover both the full value and the comment text
   unchanged.
3. The system SHALL continue to strip only trailing padding whitespace from a
   reassembled value and SHALL continue to drop the single trailing
   continuation marker used to indicate that another segment follows.
4. The system SHALL keep the existing behavior for non-string card values
   (boolean, integer, floating-point, complex, and undefined values) and for
   commentary keywords, so that their construction, serialization, and parsing
   are unaffected.
5. The system SHALL keep the existing behavior for record-valued keyword cards
   and HIERARCH cards, so that their keyword/value handling is unaffected.
