#!/usr/bin/env python3
"""G-CONF for django__django-11333.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_cachedLookup` (the Lean impl,
transliterated op-for-op per refinement.md) against the REAL patched
`django.urls.resolvers.get_resolver`, over >=1e5 fuzzed inputs.
Zero disagreements => exit 0.

Type bijection (mapping.md):
  config         <-> the `urlconf` argument (str | None);  None <-> none
  defaultConfig  <-> settings.ROOT_URLCONF (str)
  result         <-> the URLResolver object get_resolver(...) returns
  buildArtifact  <-> the lru_cache-memoized factory keyed on its argument

The modeled behavior is object IDENTITY, which for a memoized factory is exactly
equality of the (post-normalization) cache key. The observable predicate we
differential-test is therefore: for a pair of lookups (a, b), do they return the
SAME object?  The Lean impl computes `buildArtifact (some (config.getD
defaultConfig))`; two lookups are identical iff their normalized keys are equal.

Shadow identity(a, b)  := normKey(a) == normKey(b)        where
  normKey(config) = config if config is not None else defaultConfig
                    (then wrapped as the effective key)
Real   identity(a, b)  := get_resolver(a) IS get_resolver(b)   (CPython object id)

We assert shadow-identity == real-identity over fuzzed (defaultConfig, a, b)
triples. This captures the FAIL_TO_PASS assertions:
  get_resolver() IS get_resolver(ROOT_URLCONF)            (a=None, b=ROOT_URLCONF -> same)
  get_resolver() IS NOT get_resolver(other)               (different effective key)

stdlib-only; no hypothesis required. Pinned seed = 11333 (mapping.md).
"""
import random
import sys

import django
from django.conf import settings


def _ensure_settings():
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            ROOT_URLCONF=None,
            INSTALLED_APPS=[],
            DATABASES={},
        )
    django.setup()


SEED = 11333
N = 100_000


def norm_key(config, default_config):
    # R/I transliteration of implementation_cachedLookup's key selection:
    #   key := config ; if key is None: key := default_config ; present key.
    # The effective (normalized) cache key. `config is None` <-> Lean `config = none`.
    key = config
    if key is None:
        key = default_config
    return key  # the explicit-string key the factory is keyed on post-fix


def shadow_identity(a, b, default_config):
    # Two lookups return the same artifact iff their normalized keys are equal.
    return norm_key(a, default_config) == norm_key(b, default_config)


def real_identity(get_resolver, a, b):
    # Drive the REAL patched factory; compare CPython object identity.
    return get_resolver(a) is get_resolver(b)


def gen_configs(rng):
    # A small pool of distinct module-path-like configuration strings, plus None.
    pool = [
        "urlpatterns.path_urls",
        "urlpatterns.path_dynamic_urls",
        "urlpatterns.included_urls",
        "proj.urls",
        "proj.api.urls",
        "a.b.c",
        "x",
        "",                       # empty string is a distinct, valid key
    ]
    choices = [None] + pool
    return choices


def main() -> int:
    _ensure_settings()
    # Import after setup so the lru_cache wrapper is in place.
    from django.urls.base import set_urlconf  # noqa: F401
    from django.urls.resolvers import _get_cached_resolver, get_ns_resolver
    from django.urls import resolvers as R

    rng = random.Random(SEED)
    choices = gen_configs(rng)

    disagreements = 0
    examples = []
    checked = 0

    # Fixed boundary pairs mirroring the FAIL_TO_PASS assertions, evaluated under
    # several default configurations drawn from the pool.
    fixed_defaults = ["urlpatterns.path_urls", "proj.urls", "a.b.c", "x"]
    fixed_pairs = [(None, None), (None, "x"), ("x", "x")]

    def run_case(a, b, default_config):
        nonlocal disagreements, checked
        # Point settings at this run's default and clear caches so identity is
        # determined solely by the (normalized) keys of this pair.
        settings.ROOT_URLCONF = default_config
        _get_cached_resolver.cache_clear()
        get_ns_resolver.cache_clear()
        s = shadow_identity(a, b, default_config)
        r = real_identity(R.get_resolver, a, b)
        checked += 1
        if s != r:
            disagreements += 1
            if len(examples) < 10:
                examples.append((default_config, a, b, s, r))

    for dc in fixed_defaults:
        for (a, b) in fixed_pairs:
            run_case(a, b, dc)
            run_case(b, a, dc)

    # The default config must itself be a real string (settings.ROOT_URLCONF is
    # always a module path at runtime). Fuzz default + ordered pairs.
    string_pool = [c for c in choices if c is not None]
    while checked < N:
        dc = rng.choice(string_pool)
        a = rng.choice(choices)
        b = rng.choice(choices)
        run_case(a, b, dc)

    print(f"G-CONF django__django-11333: {checked} inputs, "
          f"{disagreements} disagreements")
    if disagreements:
        for dc, a, b, s, r in examples:
            print(f"  DISAGREE default={dc!r} a={a!r} b={b!r} "
                  f"shadow_same={s} real_same={r}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
