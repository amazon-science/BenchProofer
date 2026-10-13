# Requirements: Binary request bodies must survive request preparation

## Introduction

`requests` prepares an outgoing HTTP request by turning the caller-supplied
`data` argument into a request body. This work happens in
`requests.models.PreparedRequest.prepare_body`, which for a plain (non-file,
non-stream) payload delegates to the static helper
`requests.models.RequestEncodingMixin._encode_params`. That helper handles four
shapes of `data`: a text/binary scalar (`str`/`bytes`), a file-like object, an
iterable (dict or list of 2-tuples), and anything else.

A regression made the scalar branch coerce its input to a native text string
before returning it. On Python 3 that coercion decodes `bytes` as ASCII, which
both changes the payload's type (binary becomes text) and raises a decode error
for any non-ASCII byte — for example a body produced by
`u"ööö".encode("utf-8")`. As a result, sending a binary body such as
`requests.put(url, data=u"ööö".encode("utf-8"))` fails, even though it worked in
earlier releases.

The same helper is also used, indirectly, to build the URL query string in
`requests.models.PreparedRequest.prepare_url`, where a `str`/`bytes` `params`
value must still be encoded into the query component. The goal is to make a
binary (or text) body pass through preparation unchanged while keeping URL
query-parameter encoding behaving exactly as before.

The affected module is `requests/models.py`.

## Requirement 1: Scalar body payloads are preserved unchanged

**User story:** As a developer sending a request, I want a `bytes` or `str`
body to be used exactly as I supplied it, so that binary payloads (including
UTF-8-encoded text) are transmitted intact.

**Acceptance criteria**

1. WHEN `_encode_params` receives a `bytes` value, THEN the system SHALL return
   that same `bytes` value, with its type and byte contents unchanged.
2. WHEN `_encode_params` receives a `str` value, THEN the system SHALL return
   that same `str` value, with its type and character contents unchanged.
3. The system SHALL NOT decode, encode, or otherwise convert a scalar `bytes`
   body payload to a text string during body preparation.
4. IF a scalar `bytes` body payload contains bytes that are not valid ASCII
   (such as the UTF-8 encoding of non-ASCII characters), THEN the system SHALL
   complete body preparation without raising a decoding error.

## Requirement 2: A prepared request preserves the body's binary type

**User story:** As a developer, I want the prepared request's body to remain
binary when I passed binary data, so that downstream transmission is byte-exact.

**Acceptance criteria**

1. WHEN a request is prepared with a `bytes` `data` argument, THEN the resulting
   prepared request's body SHALL be a `bytes` object.
2. WHEN a request is prepared with a `bytes` `data` argument, THEN the resulting
   prepared request's body SHALL contain the same bytes that were supplied.
3. WHEN a request is prepared with a `bytes` `data` argument, THEN preparing the
   request SHALL succeed without raising an exception, regardless of whether the
   bytes are ASCII-representable.

## Requirement 3: URL query parameters given as text or bytes are still encoded

**User story:** As a developer, I want `str` or `bytes` values passed as URL
`params` to be encoded into the query string as before, so that fixing binary
bodies does not break query-parameter handling.

**Acceptance criteria**

1. WHEN a request is prepared with a `bytes` `params` value, THEN the system
   SHALL incorporate that value into the URL's query component as native text,
   decoding the raw bytes into the equivalent textual query string so that the
   resulting query is identical to what an equivalent `str` value would produce.
2. WHEN a request is prepared with a `str` `params` value, THEN the system SHALL
   incorporate that value into the URL's query component unchanged in meaning.
3. The system SHALL keep encoding `params` supplied as a dict or a list of
   2-tuples into a URL-encoded query string, preserving the ordering guarantees
   of list-of-2-tuples input.
4. The system SHALL keep placing encoded query parameters before any URL
   fragment and SHALL NOT double-encode already-encoded path or query content.

## Requirement 4: Body-vs-URL parameter handling stay independent

**User story:** As a maintainer, I want the body path and the URL-parameter path
to be handled independently, so that neither coercion affects the other.

**Acceptance criteria**

1. The system SHALL apply text coercion to a `str`/`bytes` value only when that
   value is being encoded as URL query parameters, and SHALL NOT apply it when
   the value is being used as the request body.
2. WHEN `data` is a scalar `str`/`bytes` body, THEN the system SHALL continue to
   leave the request's `Content-Type` header unset by the body-encoding step.
3. The system SHALL keep its existing handling of the other body shapes
   (file-like objects, dicts, and lists of 2-tuples) unchanged.
