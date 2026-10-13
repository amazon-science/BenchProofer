# Requirements: Accept byte-string input when constructing FITS headers and cards from strings

## Introduction

In `astropy.io.fits`, a FITS header can be reconstructed from a raw in-memory
string via the class method `Header.fromstring`, and an individual header card
can be reconstructed via `Card.fromstring` (both in `astropy/io/fits/header.py`
and `astropy/io/fits/card.py`). Historically these methods accepted only a
text (`str`) input. However raw FITS header data read from a file opened in
binary mode arrives as a `bytes` object, and the companion loader
`Header.fromfile` already supports both text- and binary-mode files. The goal
of this change is to let `Header.fromstring` and `Card.fromstring` accept a
`bytes` input in addition to a text input, so that header data read as raw
bytes can be turned directly into a `Header`/`Card` without the caller having to
decode it first. FITS headers are defined over ASCII, but to preserve any
stray non-ASCII bytes that may appear in malformed files, byte input is
interpreted using the latin-1 encoding (every byte value 0–255 maps one-to-one
to a code point). All previously supported text-input behavior must remain
unchanged.

## Requirement 1: Card.fromstring accepts a byte string

**User story:** As a developer reading raw FITS data, I want to build a header
card from a `bytes` object, so that I do not have to decode raw binary card data
to text myself before parsing it.

**Acceptance criteria**
1. WHEN `Card.fromstring` is called with a `bytes` object, THEN the method SHALL
   interpret the bytes as text using the latin-1 encoding (each byte value
   mapped one-to-one to the code point of equal numeric value) and produce a
   card equivalent to the one that results from passing the corresponding
   decoded text.
2. WHEN `Card.fromstring` is called with a byte string encoding a standard
   keyword/value assignment card, THEN the resulting card's parsed keyword and
   parsed value SHALL equal, respectively, the keyword and value produced by
   parsing the equivalent latin-1-decoded text card.
3. WHEN `Card.fromstring` is given input shorter than a full 80-column card
   image, THEN the method SHALL still succeed, padding the image to the card
   width exactly as it does for equivalent text input.
4. The system SHALL continue to accept a text (`str`) input to
   `Card.fromstring` and produce the same card it produced before this change.

## Requirement 2: Header.fromstring accepts a byte string

**User story:** As a developer, I want to reconstruct a full FITS header from
the raw bytes read out of a binary-mode file, so that I can parse header data
without manually decoding it to text.

**Acceptance criteria**
1. WHEN `Header.fromstring` is called with a `bytes` object, THEN the method
   SHALL interpret the bytes as text using the latin-1 encoding before parsing
   the individual cards.
2. WHEN `Header.fromstring` is given the raw bytes of the complete header
   section of a FITS file, THEN the resulting header SHALL be equal to the
   header obtained from reading the same file through the normal header-loading
   path, and its individual keyword values SHALL match those of that header.
3. WHEN a header is constructed from raw bytes as in criterion 2, THEN its
   serialized text form SHALL be identical to the serialized text form of the
   header obtained through the normal header-loading path.
4. WHEN `Header.fromstring` parses byte input, THEN card-boundary,
   continuation-card, and END-of-header detection SHALL behave equivalently to
   the corresponding text-input parsing, including honoring an optional card
   separator argument.
5. The system SHALL continue to accept a text (`str`) input to
   `Header.fromstring`, with or without a card separator, and produce the same
   header it produced before this change.

## Requirement 3: Preserve existing string-based construction behavior

**User story:** As a maintainer, I want all existing ways of building and
manipulating headers and cards to keep working, so that adding byte-string
support introduces no regression.

**Acceptance criteria**
1. WHEN a card is constructed from a text card image, THEN the method SHALL parse
   its keyword and value exactly as it did before this change, for every value
   type that FITS cards support.
2. The system SHALL leave the behavior of constructing and initializing cards
   and headers by every previously supported means unchanged, so that each such
   construction produces the same contents as it did before this change.
3. The system SHALL introduce no observable change to any existing card or
   header operation other than the newly added acceptance of byte-string input
   to `Card.fromstring` and `Header.fromstring`; every behavior that held before
   this change SHALL continue to hold.
