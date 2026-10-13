# Requirements: Correct MIME type guessing for `br` and `compress` file encodings in `FileResponse`

## Introduction

`django.http.response.FileResponse` sets response headers for a file-like
object in its `set_headers` method. When the caller does not supply an explicit
content type, `set_headers` derives the `Content-Type` header from the file
name using `mimetypes.guess_type`, which returns a `(content_type, encoding)`
pair. For files whose name ends in a compression-related extension,
`guess_type` reports the *decoded* content type together with a compression
`encoding` (for example `test.html.Z` yields the HTML content type plus a
compression encoding). To stop browsers from silently decompressing such
files, `set_headers` translates the reported compression `encoding` into a
compression-specific `Content-Type` instead of using the decoded type.

The defect: the translation table only covered a subset of compression
encodings. Files whose extension corresponds to the Brotli (`.br`) or Unix
compress (`.Z`) encodings were not translated, so their responses were served
with the decoded content type (e.g. `text/html`) rather than a
compression-specific type. The goal is to make `FileResponse` map every
compression encoding that `mimetypes` recognizes — including Brotli and Unix
compress — to a compression-specific `Content-Type`, while preserving the
existing mappings and all other header behavior.

## Requirement 1: Map compression encodings to compression-specific content types

**User story:** As a developer serving compressed files through
`FileResponse`, I want the response `Content-Type` to reflect the compression
format rather than the decoded payload type, so that browsers do not
automatically decompress the file and clients receive an accurate type.

**Acceptance criteria**

1. WHEN a `FileResponse` is constructed with no explicitly supplied content
   type and the file name's extension indicates the Brotli compression
   encoding (a `.br` final extension), THEN `set_headers` SHALL set the
   `Content-Type` header to `application/x-brotli`.
2. WHEN a `FileResponse` is constructed with no explicitly supplied content
   type and the file name's extension indicates the Unix compress encoding (a
   `.Z` final extension), THEN `set_headers` SHALL set the `Content-Type`
   header to `application/x-compress`.
3. WHEN the resolved compression encoding is one of Brotli or Unix compress,
   THEN the chosen `Content-Type` SHALL be the compression-specific type and
   SHALL NOT be the decoded content type that `mimetypes` reports for the file
   name (for example, a `.html.br` or `.html.Z` file SHALL NOT be served as
   `text/html`).
4. The system SHALL leave the `Content-Encoding` header unset for these files,
   so that browsers do not automatically decompress the served content.

## Requirement 2: Preserve existing compression-encoding mappings

**User story:** As a developer relying on the current behavior for gzip, bzip2,
and xz files, I want those mappings to remain unchanged, so that adding new
encodings does not regress existing responses.

**Acceptance criteria**

1. WHEN a `FileResponse` is constructed with no explicit content type and the
   file name indicates the gzip encoding (a `.gz` final extension), THEN
   `set_headers` SHALL set the `Content-Type` header to `application/gzip`.
2. WHEN a `FileResponse` is constructed with no explicit content type and the
   file name indicates the bzip2 encoding (a `.bz2` final extension), THEN
   `set_headers` SHALL set the `Content-Type` header to `application/x-bzip`.
3. WHEN a `FileResponse` is constructed with no explicit content type and the
   file name indicates the xz encoding (a `.xz` final extension), THEN
   `set_headers` SHALL set the `Content-Type` header to `application/x-xz`.

## Requirement 3: Preserve default content-type behavior for non-compressed and untyped files

**User story:** As a developer serving ordinary files, I want the existing
content-type resolution to continue working, so that only compressed-file
handling changes.

**Acceptance criteria**

1. WHEN a `FileResponse` is constructed with no explicit content type and the
   file name maps to a known content type with no compression encoding, THEN
   `set_headers` SHALL set the `Content-Type` header to that guessed content
   type.
2. IF the file name is empty or `mimetypes` cannot determine a content type,
   THEN `set_headers` SHALL set the `Content-Type` header to
   `application/octet-stream`.
3. WHEN the caller supplies an explicit content type, THEN `set_headers` SHALL
   NOT override it with a guessed or compression-derived type.

## Requirement 4: Preserve unrelated header behavior

**User story:** As a maintainer, I want the content-length, content-disposition,
and other header behaviors of `FileResponse` to be unaffected by this change,
so that only MIME-type guessing is altered.

**Acceptance criteria**

1. The system SHALL continue to compute and set the `Content-Length` header for
   seekable files, buffers, and named files exactly as before this change.
2. The system SHALL continue to set the `Content-Disposition` header (including
   attachment handling and filename escaping) exactly as before this change.
3. The system SHALL continue to support responses built from buffers, named
   files, and non-seekable sources without altering their existing header
   values other than the compression `Content-Type` mapping described above.
