# Requirements: HttpResponse must handle memoryview content

## Introduction

`django.http.HttpResponse` accepts a response body from a variety of value
types and coerces it into a byte string for the output. The internal coercion
routine `HttpResponseBase.make_bytes(value)` (in `django/http/response.py`) is
responsible for turning each supported value into a bytestring encoded in the
response's output charset. Both `HttpResponse(content=...)` at construction and
assignment to the `HttpResponse.content` property route through this coercion.

Today the coercion recognises `bytes` values (returned unchanged as bytes) and
`str` values (encoded under the response charset), and falls back for everything
else to taking the object's textual representation (`str(value)`) and encoding
that. A `memoryview` object — for example a `BinaryField` value returned by some
database backends — is not recognised as byte-like, so it falls into the textual
fallback and the response body becomes the object's repr (e.g. the literal text
`<memory at 0x...>`) instead of the bytes it wraps.

The goal is to make `HttpResponse` treat a `memoryview` as byte-like: its
response content must be exactly the underlying bytes it exposes, while every
existing coercion behavior for other value types is preserved.

## Requirement 1: memoryview content is coerced to its underlying bytes

**User story:** As a developer setting binary data on an HTTP response, I want a
`memoryview` body to become the exact bytes it wraps, so that binary values
(such as database `BinaryField` results) are transmitted correctly rather than
as an object repr.

**Acceptance criteria**
1. WHEN an `HttpResponse` is constructed with a `memoryview` as its content,
   THEN the response's `content` SHALL equal the exact byte string exposed by
   that `memoryview` (the same bytes as `bytes(the_memoryview)`).
2. WHEN a value that is a `memoryview` is assigned to the `content` property of
   an `HttpResponse`, THEN the resulting `content` SHALL equal the exact byte
   string exposed by that `memoryview`.
3. The system SHALL NOT render a `memoryview` body via its textual
   representation; the response `content` for a `memoryview` SHALL NOT contain
   the object's repr text.
4. WHEN the byte-string coercion routine receives a `memoryview`, THEN it SHALL
   return a `bytes` instance (not a `memoryview` or other subclass) holding
   those underlying bytes.

## Requirement 2: existing content-coercion behavior is preserved

**User story:** As a Django user relying on current response behavior, I want
all previously supported content types to keep coercing exactly as before, so
that adding memoryview support introduces no regression.

**Acceptance criteria**
1. WHEN an `HttpResponse` is given a `bytes` value as content, THEN its
   `content` SHALL equal those same bytes, unchanged.
2. WHEN an `HttpResponse` is given a `str` value as content, THEN its `content`
   SHALL equal that string encoded under the response's output charset.
3. IF the response's output charset is not the default, THEN a `str` body SHALL
   be encoded using that configured charset.
4. WHEN an `HttpResponse` is given a non-string, non-bytes, non-memoryview value
   (for example an integer) as content, THEN its `content` SHALL equal that
   value's textual representation encoded under the output charset.
5. WHEN an `HttpResponse` is given an iterable of values as content, THEN its
   `content` SHALL equal the concatenation of each item coerced to bytes under
   the above rules, in iteration order.
6. The system SHALL continue to return the coerced `content` as a `bytes`
   instance for every supported content type.
