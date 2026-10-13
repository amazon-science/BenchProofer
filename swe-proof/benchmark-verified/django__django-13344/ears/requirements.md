# Requirements: Middleware constructors must restore async-capability detection

## Introduction

Django's middleware classes derive from the shared base
`django.utils.deprecation.MiddlewareMixin`. That base constructor performs three
initialization steps for every middleware instance built from an (optional)
request-handler callable (`get_response`):

1. it emits a `RemovedInDjango40Warning` deprecation notice when no handler (or
   an explicit `None`) is supplied;
2. it stores the handler on the instance; and
3. it inspects the handler and, when the handler is an *asynchronous* (coroutine)
   callable, marks the constructed middleware instance as itself being an
   asynchronous callable — so that `asyncio.iscoroutinefunction(instance)`
   returns `True`.

Several middleware subclasses defined their own `__init__` that reproduced steps
(1) and (2) inline but omitted step (3). As a result, when such a middleware was
built from an asynchronous handler under an ASGI server, the instance was NOT
recognized as asynchronous. When it was the first middleware in the chain, the
handler layer below produced an unawaited coroutine and that coroutine — rather
than a resolved `HttpResponse` — was handed to the middleware's
`process_response`, breaking the response phase.

The affected constructors are:

- `django.contrib.sessions.middleware.SessionMiddleware.__init__`
- `django.middleware.cache.UpdateCacheMiddleware.__init__`
- `django.middleware.cache.FetchFromCacheMiddleware.__init__`
- `django.middleware.cache.CacheMiddleware.__init__`
- `django.middleware.security.SecurityMiddleware.__init__`

The goal: every one of these constructors must perform the shared base
initialization (deprecation notice, handler storage, AND async-capability
detection), while preserving each subclass's own configuration behavior
(settings reads, cache selection, timeout handling).

## Requirement 1: Async-capability detection for every middleware constructor

**User story:** As a developer running Django under an ASGI server, I want every
built-in middleware to correctly report whether it is asynchronous based on the
handler it wraps, so that the response phase receives a resolved response object
rather than an unawaited coroutine.

**Acceptance criteria**

1. WHEN any of the affected middleware classes (`SessionMiddleware`,
   `UpdateCacheMiddleware`, `FetchFromCacheMiddleware`, `CacheMiddleware`,
   `SecurityMiddleware`) is constructed with a handler that is an asynchronous
   (coroutine) callable, THEN the resulting instance SHALL be recognized as an
   asynchronous callable — i.e. `asyncio.iscoroutinefunction(instance)` SHALL
   return `True`.
2. WHEN any of those middleware classes is constructed with a handler that is an
   ordinary synchronous callable, THEN the resulting instance SHALL NOT be
   recognized as an asynchronous callable — i.e.
   `asyncio.iscoroutinefunction(instance)` SHALL return `False`.
3. The system SHALL apply the async-capability detection consistently across all
   built-in middleware that derive from the shared middleware base, so that no
   built-in middleware built from an asynchronous handler is misreported as
   synchronous.
4. The async-capability determination SHALL depend solely on whether the supplied
   handler is a coroutine callable, and SHALL NOT depend on the middleware's
   position in the configured middleware sequence.

## Requirement 2: Deprecation notice for a missing handler is preserved

**User story:** As a maintainer, I want the existing deprecation behavior for
omitting the handler argument to remain intact after the async-detection fix, so
that upgrade guidance is unchanged.

**Acceptance criteria**

1. WHEN any of the affected middleware classes is constructed with no handler
   argument, THEN the constructor SHALL raise/emit a `RemovedInDjango40Warning`
   whose message states that passing `None` for the middleware `get_response`
   argument is deprecated.
2. WHEN any of the affected middleware classes is constructed with an explicit
   `None` handler argument, THEN the constructor SHALL emit that same
   `RemovedInDjango40Warning` deprecation notice.
3. IF a non-`None` handler is supplied, THEN the constructor SHALL NOT emit the
   missing-handler deprecation notice.
4. The system SHALL store the supplied handler on the constructed instance so
   that the middleware's later request/response processing invokes that handler.

## Requirement 3: Cache middleware configuration attributes remain correct

**User story:** As a developer configuring caching middleware, I want each cache
middleware to be initialized with the correct timeout, key prefix, cache alias,
and resolved cache backend, so that behavior is unchanged while the async fix is
applied.

**Acceptance criteria**

1. WHEN `UpdateCacheMiddleware` is constructed with a handler and no keyword
   overrides, THEN the instance SHALL take its cache timeout from the
   `CACHE_MIDDLEWARE_SECONDS` setting, SHALL set its page timeout to `None`, SHALL
   take its key prefix from the `CACHE_MIDDLEWARE_KEY_PREFIX` setting, SHALL take
   its cache alias from the `CACHE_MIDDLEWARE_ALIAS` setting, and SHALL set its
   cache backend to the cache registered under that resolved alias.
2. WHEN `FetchFromCacheMiddleware` is constructed with a handler, THEN the
   instance SHALL take its key prefix from the `CACHE_MIDDLEWARE_KEY_PREFIX`
   setting, SHALL take its cache alias from the `CACHE_MIDDLEWARE_ALIAS` setting,
   and SHALL set its cache backend to the cache registered under that resolved
   alias.
3. WHEN `CacheMiddleware` is constructed without keyword overrides for key
   prefix or cache alias, THEN it SHALL resolve key prefix and cache alias from
   the same settings used by `UpdateCacheMiddleware`/`FetchFromCacheMiddleware`,
   and its cache backend SHALL be the cache registered under the resolved alias.
4. WHEN `CacheMiddleware` is constructed with keyword overrides for key prefix
   and/or cache alias, THEN it SHALL use the provided values (treating a provided
   `None` key prefix as the empty string and a provided `None` cache alias as the
   default cache alias), and its cache backend SHALL be the cache registered
   under the effective alias.
5. WHEN `CacheMiddleware` is constructed with an explicit cache timeout value,
   THEN it SHALL use that value; and WHEN no explicit cache timeout is provided
   it SHALL fall back to the default cache-timeout setting.
6. The system SHALL ensure that, for every cache middleware, the resolved cache
   backend attribute corresponds to the middleware's effective cache alias (they
   never refer to different caches).

## Requirement 4: Existing middleware processing behavior is preserved

**User story:** As a maintainer, I want the async fix to leave all other
middleware behavior unchanged, so that no regression is introduced.

**Acceptance criteria**

1. The system SHALL continue to route both synchronous and asynchronous request
   handling through the shared base initialization such that a middleware built
   from a synchronous handler operates in the base thread and shares the database
   connection as before.
2. WHILE processing a request, each affected middleware SHALL retain its existing
   request-phase and response-phase behavior (security headers, cache lookup and
   storage, session handling) unchanged by this fix.
3. The system SHALL keep each affected subclass's constructor-specific
   configuration (settings reads and, for the cache middleware, cache selection
   and timeout handling) intact after delegating the shared initialization steps.
