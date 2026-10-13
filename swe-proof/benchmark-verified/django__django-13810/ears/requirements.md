# Requirements: MiddlewareNotUsed must not poison the middleware handler chain

## Introduction

`BaseHandler.load_middleware` (in `django/core/handlers/base.py`) builds the
request-processing chain by iterating over `settings.MIDDLEWARE` in reverse. For
each configured middleware it first calls `self.adapt_method_mode(...)` to coerce
the current running handler into the execution mode (synchronous or
asynchronous) that the next middleware will run under, and then instantiates the
middleware with that handler. A middleware may decline to install itself by
raising `MiddlewareNotUsed` from its constructor, in which case the loop logs the
event (in debug mode) and moves on to the next middleware.

The defect: the mode-coerced handler was committed to the running-handler
variable *before* the middleware was instantiated. When the middleware then
raised `MiddlewareNotUsed` and was skipped, the running handler had already been
replaced by the coerced version. The next middleware therefore received a handler
whose execution mode had been adapted for a middleware that was never installed,
disregarding the async/sync capability checks performed for the surviving
middleware. In an ASGI (asynchronous) context this "poisons" the chain: a later
stage ends up wired to run synchronously and returns a plain response object
where an awaitable coroutine is expected, surfacing to the caller as an error
about a response object not being awaitable.

The goal is to ensure that when a middleware is skipped via `MiddlewareNotUsed`,
the running handler passed on to subsequent middleware is exactly the handler
that existed before that middleware's mode adaptation — the adaptation performed
for a skipped middleware must have no lasting effect — while preserving normal
chain assembly, the mode adaptation for installed middleware, and all existing
debug logging.

The behavior is localized to the middleware-construction step inside the
`load_middleware` loop and its interaction with `adapt_method_mode` and the
`MiddlewareNotUsed` skip path.

## Requirement 1: A skipped middleware must not alter the running handler

**User story:** As a developer running Django under ASGI with a middleware that
declines to install itself, I want the middleware chain to remain correctly wired
for the remaining middleware, so that asynchronous request handling keeps working
as documented.

**Acceptance criteria**
1. WHEN a middleware's construction raises `MiddlewareNotUsed` during
   `load_middleware`, THEN the running handler used for the next middleware in the
   iteration SHALL be the same handler that was in effect before that middleware's
   mode adaptation was computed.
2. WHEN a middleware is skipped via `MiddlewareNotUsed`, THEN the running
   handler's recorded execution mode carried into the next iteration SHALL remain
   the execution mode it had before the skipped middleware, unaffected by any mode
   coercion performed for the skipped middleware.
3. The system SHALL NOT allow a mode-adapted handler produced for a middleware
   that raised `MiddlewareNotUsed` to be passed to any subsequently constructed
   middleware.

## Requirement 2: Asynchronous chains remain async after a skipped middleware

**User story:** As a user of an ASGI-served site whose middleware list includes a
non-async-capable middleware that opts out via `MiddlewareNotUsed`, I want async
requests to still resolve correctly, so that I do not get errors about a response
that cannot be awaited.

**Acceptance criteria**
1. WHEN `load_middleware` is invoked in asynchronous mode and a middleware
   positioned inner to (constructed before, i.e. reversed-order earlier) another
   middleware raises `MiddlewareNotUsed`, THEN the surviving outer middleware
   SHALL still be wired against a handler in the correct (asynchronous) execution
   mode for that middleware.
2. WHEN an asynchronous request is processed through a chain assembled with such a
   skipped middleware, THEN the assembled chain SHALL yield an awaitable
   response that resolves to the expected successful response (status code 200 and
   the expected response body).
3. The system SHALL preserve the async/sync mode negotiation for every installed
   middleware exactly as if the skipped middleware had never appeared in
   `settings.MIDDLEWARE`.

## Requirement 3: Normal middleware installation still adapts the handler

**User story:** As a maintainer, I want middleware that installs successfully to
continue receiving and propagating the mode-adapted handler, so that the fix does
not regress ordinary chain assembly.

**Acceptance criteria**
1. WHEN a middleware is constructed successfully (no `MiddlewareNotUsed` raised),
   THEN it SHALL be instantiated with the handler coerced to that middleware's
   execution mode by `adapt_method_mode`.
2. WHEN a middleware installs successfully, THEN the running handler carried into
   the next iteration SHALL reflect that successful installation, so that mode
   adaptation continues to compose across the chain as before.
3. The system SHALL continue to raise `ImproperlyConfigured` WHEN a middleware
   factory returns `None`, and SHALL continue to raise a `RuntimeError` WHEN a
   configured middleware advertises neither synchronous nor asynchronous
   capability.

## Requirement 4: Preserve MiddlewareNotUsed logging and adaptation logging

**User story:** As an operator diagnosing middleware behavior with debug logging
enabled, I want the existing log output about skipped middleware and adapted
handlers to be unchanged, so that debugging remains reliable.

**Acceptance criteria**
1. WHILE `DEBUG` is enabled, WHEN a middleware raises `MiddlewareNotUsed`, THEN
   the system SHALL emit a debug log record on the `django.request` logger
   identifying that the middleware was not used, including the middleware's dotted
   path (and any explanatory message provided by the exception).
2. WHILE `DEBUG` is disabled, WHEN a middleware raises `MiddlewareNotUsed`, THEN
   the system SHALL NOT emit that debug log record.
3. WHILE `DEBUG` is enabled, WHEN `adapt_method_mode` coerces a handler or method
   between synchronous and asynchronous modes, THEN the system SHALL emit a debug
   log record on the `django.request` logger indicating that the named handler was
   adapted, and the relative ordering of the adaptation record(s) and any
   subsequent `MiddlewareNotUsed` record SHALL reflect the actual order in which
   the events occurred during chain assembly.
4. The system SHALL keep the assignment of `process_view`,
   `process_template_response`, and `process_exception` middleware hooks, and the
   final adaptation of the top of the chain, behaving exactly as before for all
   installed middleware.
