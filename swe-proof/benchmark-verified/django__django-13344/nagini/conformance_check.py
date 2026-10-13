#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13344 (nagini).

SHADOW: the impl regions of model.py (`configure_handler`,
`configure_settings_handler`) copied verbatim below with the contract calls
(Requires/Ensures) stripped, plus the model's minimal `Handler` class. The two
@ContractOnly callees are realised by calling the REAL repo machinery through
the type bridge:

  * ``producer_is_async(token)``  -> ``asyncio.iscoroutinefunction`` on the
    bridged producer object (mapping.md section 3.1);
  * ``resolve_store(name_token)`` -> ``django.core.cache.caches[alias]`` on
    the bridged alias name (mapping.md section 3.3).

ORACLE: the REAL patched constructors the model models per mapping.md /
refinement.md. `configure_handler` is diffed against the plain-subclass
inits — SecurityMiddleware, SessionMiddleware, UpdateCacheMiddleware,
FetchFromCacheMiddleware — and `configure_settings_handler` against
CacheMiddleware.__init__. The gate applies the patch to /testbed before this
script runs; the script only imports and drives the patched code.

Type bridge (mapping.md section 2):
  * producer token Optional[int]: ``None`` <-> the absent value; each non-None
    token maps to one fixed object from a pool mixing plain functions,
    coroutine functions, lambdas, bound/partial callables and non-callables
    (identity-stable, so ``is`` retention lowers exactly).
  * observable facets of the constructed middleware: retained producer =
    ``mw.get_response`` (identity); absence signal = a RemovedInDjango40Warning
    captured during construction; async advertised =
    ``asyncio.iscoroutinefunction(mw)`` on the instance.
  * store-name token int -> a cache alias from a fixed registry of configured
    aliases (the concrete domain of the abstraction: the registry read is
    only defined on configured aliases); store token -> the backend object
    ``caches[alias]`` (per-thread identity-stable, so ``is`` compares exact).
  * ``default_name`` -> settings.CACHE_MIDDLEWARE_ALIAS (set per input);
    ``override_name`` None <-> no ``cache_alias`` kwarg supplied; token k <->
    ``cache_alias=alias_k``. The explicit ``cache_alias=None`` kwarg lowers a
    supplied override designating the registry's default alias.

Input domain: the model's preconditions only demand field access, so any
(producer token, default name, override-or-None) triple over the bridged
domains is Requires-satisfying. Boundary cases cover the absent producer on
every subclass, each producer kind, and the default / explicit-default /
explicit-custom / explicit-None store-selection paths.

>= 1e5 Requires-satisfying inputs: boundary + 100000 fuzz triples, each
driving BOTH modelled operations (one plain subclass rotating + the
settings-carrying one). Pinned fuzz seed: 133440.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (no f-strings: older container Pythons).
"""
import asyncio
import functools
import json
import random
import sys
import warnings

SEED = 133440
N_FUZZ = 100000


# --- the model's minimal view class (contract calls stripped) -----------------

class Handler(object):
    def __init__(self):
        self.producer = None
        self.async_advertised = False
        self.absence_signalled = False
        self.store_name = 0
        self.store = 0


# --- @ContractOnly callees: bridged calls into the REAL repo machinery --------

PRODUCERS = {}   # producer token -> the bridged producer object (None -> None)
ALIASES = []     # store-name token (index) -> configured cache alias


def producer_is_async(producer):
    """The real unchanged predicate on the bridged producer object."""
    return asyncio.iscoroutinefunction(PRODUCERS[producer])


def resolve_store(store_name):
    """The real unchanged registry read on the bridged alias name."""
    from django.core.cache import caches
    return caches[ALIASES[store_name]]


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def configure_handler(handler, producer):
    if producer is None:
        handler.absence_signalled = True
    else:
        handler.absence_signalled = False
    handler.producer = producer
    handler.async_advertised = producer_is_async(producer)


def configure_settings_handler(handler, producer, default_name, override_name):
    if producer is None:
        handler.absence_signalled = True
    else:
        handler.absence_signalled = False
    handler.producer = producer
    handler.async_advertised = producer_is_async(producer)
    # Defaults established first (as super().__init__ -> base init does):
    handler.store_name = default_name
    handler.store = resolve_store(handler.store_name)
    # An explicit override re-selects the name AND re-resolves the store from it:
    if override_name is not None:
        handler.store_name = override_name
        handler.store = resolve_store(handler.store_name)
    return handler.store
    # impl-end (verbatim copy ends)


# --- oracle plumbing -----------------------------------------------------------

def build_oracle():
    """Configure minimal settings (several locmem cache aliases, a model-free
    session engine), build the producer pool, return the middleware classes."""
    from django.conf import settings
    aliases = ["default", "alpha", "beta", "gamma", "delta", "omega"]
    if not settings.configured:
        settings.configure(
            CACHES=dict(
                (a, {"BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                     "LOCATION": "loc-" + a})
                for a in aliases),
            CACHE_MIDDLEWARE_ALIAS="default",
            # a session backend with no ORM models, so no app registry needed
            SESSION_ENGINE="django.contrib.sessions.backends.cache",
        )
    import django
    django.setup()

    from django.contrib.sessions.middleware import SessionMiddleware
    from django.middleware.cache import (
        CacheMiddleware, FetchFromCacheMiddleware, UpdateCacheMiddleware)
    from django.middleware.security import SecurityMiddleware

    global ALIASES
    ALIASES = aliases

    # producer pool: one fixed object per non-None token (identity-stable)
    async def _async_producer(request):
        return None

    async def _async_with_default(request, x=1):
        return x

    def _sync_producer(request):
        return None

    class _CallableObj(object):
        def __call__(self, request):
            return None

    PRODUCERS.update({
        None: None,                                   # the absent producer
        1: _sync_producer,                            # plain function
        2: _async_producer,                           # coroutine function
        3: (lambda request: None),                    # lambda
        4: object(),                                  # non-callable object
        5: functools.partial(_sync_producer),         # partial of a function
        6: _async_with_default,                       # coroutine fn w/ default
        7: _CallableObj(),                            # callable instance
        8: 5,                                         # non-callable int
        9: functools.partial(_async_producer),        # partial of a coroutine fn
    })

    plain_classes = [SecurityMiddleware, SessionMiddleware,
                     UpdateCacheMiddleware, FetchFromCacheMiddleware]
    return plain_classes, CacheMiddleware


def construct_observed(cls, get_response, kwargs=None):
    """Construct the real middleware capturing the deprecation signal; return
    (instance, absence_signalled, async_advertised)."""
    from django.utils.deprecation import RemovedInDjango40Warning
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        mw = cls(get_response, **(kwargs or {}))
    signalled = any(issubclass(w.category, RemovedInDjango40Warning)
                    for w in caught)
    return mw, signalled, asyncio.iscoroutinefunction(mw)


# --- differential drivers --------------------------------------------------------

def check_plain(cls, ptok):
    """Shadow configure_handler vs the real plain-subclass constructor."""
    mw, signalled, advertised = construct_observed(cls, PRODUCERS[ptok])
    h = Handler()
    configure_handler(h, ptok)
    if not (h.producer is ptok and PRODUCERS[h.producer] is mw.get_response):
        return ("DISAGREEMENT (producer retention) cls=%s ptok=%r:\n"
                "  shadow producer token = %r\n"
                "  real get_response     = %r"
                % (cls.__name__, ptok, h.producer, mw.get_response))
    if h.absence_signalled != signalled:
        return ("DISAGREEMENT (absence signal) cls=%s ptok=%r:\n"
                "  shadow = %r\n  real   = %r"
                % (cls.__name__, ptok, h.absence_signalled, signalled))
    if h.async_advertised != advertised:
        return ("DISAGREEMENT (async advertised) cls=%s ptok=%r:\n"
                "  shadow = %r\n  real   = %r"
                % (cls.__name__, ptok, h.async_advertised, advertised))
    return None


def check_settings(cache_cls, ptok, default_tok, override_tok, explicit_none):
    """Shadow configure_settings_handler vs the real CacheMiddleware
    constructor. explicit_none lowers a supplied override that designates the
    registry's default alias (token 0) via the None-valued kwarg spelling."""
    from django.conf import settings
    settings.CACHE_MIDDLEWARE_ALIAS = ALIASES[default_tok]
    if explicit_none:
        kwargs = {"cache_alias": None}
        model_override = 0            # the registry's default alias token
    elif override_tok is None:
        kwargs = {}
        model_override = None
    else:
        kwargs = {"cache_alias": ALIASES[override_tok]}
        model_override = override_tok
    mw, signalled, advertised = construct_observed(
        cache_cls, PRODUCERS[ptok], kwargs)
    h = Handler()
    ret = configure_settings_handler(h, ptok, default_tok, model_override)
    tag = ("ptok=%r default=%r override=%r explicit_none=%r"
           % (ptok, default_tok, override_tok, explicit_none))
    if not (h.producer is ptok and PRODUCERS[h.producer] is mw.get_response):
        return ("DISAGREEMENT (producer retention, settings) %s:\n"
                "  shadow producer token = %r\n  real get_response = %r"
                % (tag, h.producer, mw.get_response))
    if h.absence_signalled != signalled:
        return ("DISAGREEMENT (absence signal, settings) %s:\n"
                "  shadow = %r\n  real   = %r"
                % (tag, h.absence_signalled, signalled))
    if h.async_advertised != advertised:
        return ("DISAGREEMENT (async advertised, settings) %s:\n"
                "  shadow = %r\n  real   = %r"
                % (tag, h.async_advertised, advertised))
    if ALIASES[h.store_name] != mw.cache_alias:
        return ("DISAGREEMENT (selected store name) %s:\n"
                "  shadow alias = %r\n  real cache_alias = %r"
                % (tag, ALIASES[h.store_name], mw.cache_alias))
    if h.store is not mw.cache:
        return ("DISAGREEMENT (resolved store) %s:\n"
                "  shadow store = %r\n  real cache = %r"
                % (tag, h.store, mw.cache))
    if ret is not mw.cache:
        return ("DISAGREEMENT (reported store) %s:\n"
                "  shadow result = %r\n  real cache = %r"
                % (tag, ret, mw.cache))
    return None


def main():
    try:
        plain_classes, cache_cls = build_oracle()
    except Exception as exc:
        print("G-CONF ERROR: oracle setup failed: %r" % (exc,))
        return 1

    ptoks = sorted(PRODUCERS, key=lambda t: -1 if t is None else t)
    n_names = len(ALIASES)
    checked = 0
    n_boundary = 0

    # boundary: every producer token on every plain subclass, and the
    # default / explicit-default / explicit-custom / explicit-None
    # store-selection paths on every producer token
    for ptok in ptoks:
        for cls in plain_classes:
            err = check_plain(cls, ptok)
            if err:
                print(err)
                return 1
            checked += 1
            n_boundary += 1
        for (d, o, en) in [(0, None, False),   # pure default path
                           (0, 0, False),      # explicit == default
                           (0, 1, False),      # explicit custom
                           (2, None, False),   # non-default default
                           (2, 2, False),
                           (2, 5, False),
                           (3, None, True),    # explicit None-valued override
                           (0, None, True)]:
            err = check_settings(cache_cls, ptok, d, o, en)
            if err:
                print(err)
                return 1
            checked += 1
            n_boundary += 1

    # fuzz: pinned seed; each iteration drives both modelled operations
    rng = random.Random(SEED)
    nn_ptoks = [t for t in ptoks if t is not None]
    for i in range(N_FUZZ):
        ptok = None if rng.random() < 0.15 else rng.choice(nn_ptoks)
        cls = plain_classes[i % len(plain_classes)]
        err = check_plain(cls, ptok)
        if err:
            print(err)
            return 1
        d = rng.randrange(n_names)
        roll = rng.random()
        if roll < 0.35:
            o, en = None, False           # default path
        elif roll < 0.45:
            o, en = None, True            # explicit None-valued override
        else:
            o, en = rng.randrange(n_names), False
        err = check_settings(cache_cls, ptok, d, o, en)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched constructors "
          "(4 plain subclasses + the settings-carrying one) on %d inputs "
          "(%d boundary + %d fuzz, seed %d); 0 disagreements."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
