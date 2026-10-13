# Requirements: Async-safe "method not allowed" handling in the base class-based view

## Introduction

Django's base class-based view `View` (in `django.views.generic.base`) can be
configured either synchronously or asynchronously depending on whether its HTTP
method handlers (`get`, `post`, etc.) are coroutine functions. When a view is
asynchronous, the dispatch machinery awaits the object returned by the selected
handler.

The fallback handler `View.http_method_not_allowed(request, *args, **kwargs)` —
invoked when a request uses an HTTP method the view does not implement — returned
a bare `HttpResponseNotAllowed` object unconditionally. For an asynchronous view,
the caller then attempted to `await` that plain response object, raising
`TypeError: object HttpResponseNotAllowed can't be used in 'await' expression`
and producing a 500 error instead of the intended 405 "Method Not Allowed".

The goal is to make `http_method_not_allowed` behave like the sibling `options`
handler already does: return an awaitable that resolves to the response when the
view operates asynchronously, and return the response directly when the view
operates synchronously — while preserving the response's identity (HTTP 405
"method not allowed", carrying the permitted method names) in both cases. The
async/sync mode is determined by the existing `View.view_is_async` property, whose
behavior must be preserved.

## Requirement 1: Method-not-allowed handler adapts to the view's async mode

**User story:** As a developer who defines a class-based view with only
asynchronous handlers, I want requests using unsupported HTTP methods to receive
a proper "method not allowed" response instead of crashing, so that my async view
behaves correctly under async dispatch.

**Acceptance criteria**
1. WHEN `http_method_not_allowed` is called on a view instance whose
   `view_is_async` is true, THEN the handler SHALL return an awaitable object
   (a coroutine) rather than a bare response.
2. WHEN the awaitable returned for an asynchronous view is resolved (awaited/run
   to completion), THEN it SHALL yield an `HttpResponseNotAllowed` instance.
3. WHEN `http_method_not_allowed` is called on a view instance whose
   `view_is_async` is false, THEN the handler SHALL return an
   `HttpResponseNotAllowed` instance directly, and that returned object SHALL NOT
   be a coroutine.
4. The system SHALL determine whether to return an awaitable wrapper versus the
   bare response solely from the view's `view_is_async` state, applying the same
   selection rule that `View.options` uses.

## Requirement 2: The method-not-allowed response identity is preserved in both modes

**User story:** As a client that sends a disallowed HTTP method, I want a
correct HTTP 405 response listing the methods the view permits, regardless of
whether the view is sync or async, so that error handling is consistent.

**Acceptance criteria**
1. The system SHALL produce, in both synchronous and asynchronous modes, a
   "method not allowed" response of type `HttpResponseNotAllowed` (HTTP status
   405).
2. The system SHALL populate that response with the list of request-method names
   the view permits, as computed by `View._allowed_methods()` (the upper-cased
   names of the HTTP methods the instance implements).
3. The permitted-method payload carried by the response SHALL be identical
   whether the view operates synchronously or asynchronously.
4. WHEN `http_method_not_allowed` runs, THEN the system SHALL continue to emit
   the existing "Method Not Allowed" warning log record for the request (with
   status code 405), unchanged from prior behavior.

## Requirement 3: The OPTIONS handler's async behavior is unchanged (regression protection)

**User story:** As a maintainer, I want the existing `options` handler to keep
its sync/async behavior, so that fixing the not-allowed handler does not alter
other handlers.

**Acceptance criteria**
1. WHEN `options` is called on a view instance whose `view_is_async` is true,
   THEN it SHALL return a coroutine that, when resolved, yields an `HttpResponse`.
2. WHEN `options` is called on a view instance whose `view_is_async` is false,
   THEN it SHALL return an `HttpResponse` instance directly and that object SHALL
   NOT be a coroutine.
3. The system SHALL keep providing the `Allow` header (listing permitted methods)
   and a `Content-Length` of `0` on the OPTIONS response.

## Requirement 4: Async-mode detection for views is preserved (regression protection)

**User story:** As a developer, I want Django to correctly classify a view as
sync or async and reject mixed handler sets, so that the not-allowed handler and
dispatch machinery choose the right behavior.

**Acceptance criteria**
1. The system SHALL report `View.view_is_async` as false for the base `View`
   class and for any subclass that defines no HTTP method handlers.
2. WHEN a view class defines only synchronous HTTP method handlers, THEN
   `view_is_async` SHALL be false; WHEN a view class defines only asynchronous
   HTTP method handlers, THEN `view_is_async` SHALL be true.
3. IF a view class defines a mix of synchronous and asynchronous HTTP method
   handlers, THEN accessing `view_is_async` SHALL raise `ImproperlyConfigured`
   with a message stating that the view's HTTP handlers must be either all sync
   or all async.
4. WHEN a view class is asynchronous, THEN the callable produced by `as_view()`
   SHALL be marked as a coroutine function; WHEN it is synchronous, THEN that
   callable SHALL NOT be a coroutine function.
