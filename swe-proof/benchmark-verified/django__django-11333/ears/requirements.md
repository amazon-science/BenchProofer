# Requirements: `get_resolver` cache keying on the effective URLconf

## Introduction

`django.urls.resolvers.get_resolver(urlconf=None)` returns a `URLResolver` built
for a given URLconf. Because constructing a `URLResolver` (and populating its
route caches via `URLResolver._populate`) is expensive, the result is memoized
so that repeated calls for the same configuration reuse one object.

The function accepts an optional `urlconf` argument. When it is `None`, the
function falls back to the active default configuration, `settings.ROOT_URLCONF`.
Callers such as `django.urls.base.reverse` and `django.urls.base.resolve` reach
`get_resolver` through `django.urls.get_urlconf`, which yields `None` until the
first request is handled (at which point `set_urlconf` records
`settings.ROOT_URLCONF`) and the explicit configuration string thereafter.

The defect being corrected: the memoization was keyed on the *raw* argument, so
a call with no argument (key `None`) and a call with the explicit
`settings.ROOT_URLCONF` value (key = that string) were treated as different
cache entries even though both denote the identical effective configuration.
This produced two distinct `URLResolver` objects and ran the expensive
population twice. The goal is to resolve the argument to its effective value
*before* the memoized lookup, so that a `None` argument and an explicit
`settings.ROOT_URLCONF` argument collapse to one shared cached object, while all
other behavior — including cache clearing and the distinctness of genuinely
different configurations — is preserved.

## Requirement 1: A `None` argument and the explicit default collapse to one cached object

**User story:** As a caller who reaches `get_resolver` sometimes with no
argument and sometimes with the active default configuration, I want both to
return the very same resolver, so that the expensive resolver construction and
population happen only once.

**Acceptance criteria**

1. WHEN `get_resolver` is called with `urlconf` absent or `None`, THEN the
   function SHALL behave as though it were called with the current value of
   `settings.ROOT_URLCONF`.
2. WHEN `get_resolver` is called once with `urlconf` absent or `None` and once
   with a string equal to the current `settings.ROOT_URLCONF`, THEN the two
   calls SHALL return the identical (same-identity) `URLResolver` object.
3. The system SHALL resolve a `None` argument to `settings.ROOT_URLCONF` before
   the memoized lookup is performed, so that the memoization key reflects the
   effective configuration rather than the raw argument.
4. The system SHALL construct and populate the `URLResolver` for a given
   effective configuration at most once, reusing the cached object on
   subsequent calls that denote that same effective configuration.

## Requirement 2: Distinct configurations still yield distinct resolvers

**User story:** As a caller who requests resolvers for genuinely different
URLconf modules, I want a separate resolver for each, so that each configuration
resolves against its own route set.

**Acceptance criteria**

1. WHEN `get_resolver` is called with two different URLconf values that do not
   denote the same effective configuration, THEN the function SHALL return two
   distinct (different-identity) `URLResolver` objects.
2. The system SHALL continue to key the memoization such that unequal effective
   configurations map to different cached resolvers.

## Requirement 3: Each returned resolver targets the requested configuration

**User story:** As a caller, I want the returned resolver to be built for the
configuration I asked for, so that URL resolution and reversal operate against
the correct route set.

**Acceptance criteria**

1. WHEN `get_resolver` returns a resolver for a given effective configuration,
   THEN that resolver SHALL be a `URLResolver` constructed against that
   configuration rooted at the top-level path prefix `^/`.
2. The system SHALL keep the returned object's type and construction identical
   to the prior behavior for any single call; only the sharing of the cache
   entry between a `None` argument and the explicit default is changed.

## Requirement 4: Cache clearing continues to reset the resolver cache

**User story:** As a caller of `django.urls.base.clear_url_caches`, I want the
resolver cache fully cleared, so that resolvers are rebuilt after I invalidate
caches (for example after changing URL configuration in tests).

**Acceptance criteria**

1. WHEN `clear_url_caches` is called, THEN the system SHALL discard every cached
   `URLResolver` so that a subsequent `get_resolver` call rebuilds and returns a
   freshly constructed object.
2. WHEN `clear_url_caches` is called, THEN the system SHALL also clear the
   callable cache used by `get_callable` and the namespaced-resolver cache used
   by `get_ns_resolver`, exactly as before.
3. The system SHALL keep `clear_url_caches` clearing the resolver memoization
   even though that memoization now lives behind the effective-configuration
   normalization; clearing SHALL empty the actual cache that stores constructed
   resolvers.

## Requirement 5: Signature and unrelated behavior are preserved

**User story:** As a maintainer, I want `get_resolver` to keep its public
contract, so that existing call-sites and imports keep working unchanged.

**Acceptance criteria**

1. The system SHALL keep `get_resolver` callable with no argument, with `None`,
   or with a URLconf value, returning a `URLResolver` in every case.
2. The system SHALL keep the behavior of `reverse`, `resolve`, and other
   `get_resolver` call-sites unchanged apart from the reduced duplication of
   resolver construction.
3. The system SHALL NOT alter the construction, population, or public interface
   of `URLResolver` itself.
