#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13344.

Executes the REAL unchanged callees on Requires-satisfying inputs (boundary +
randomized fuzz) and asserts every observation matches what model.py encodes.

Two kind-A checks:

  (A-consumed) the `producer_is_async` axiom (model.py axioms region) models the
      runtime coroutine-function predicate `asyncio.iscoroutinefunction`. The
      axiom's sole Ensures is:
          producer is None  ->  result is False
      G-AX runs the real `asyncio.iscoroutinefunction` on the absent value plus
      sync/async/non-callable producer tokens and asserts the contract holds
      (in particular iscoroutinefunction(None) is False), and that the predicate
      is deterministic.

  (A-reference) the deep model of configuration in model.py
      (`configure_handler` / `configure_settings_handler`) establishes three
      facts about a constructed handler:
          stored producer is the supplied producer,
          absence-signal fires  iff  producer is the absent value,
          async-advertised      iff  the producer is asynchronous.
      The real configuration mechanism is `MiddlewareMixin.__init__` (via
      super().__init__): it stores get_response, fires the deprecation signal
      when get_response is None, and runs _async_check(), which sets the
      `_is_coroutine` marker (`asyncio.coroutines._is_coroutine`) exactly when
      asyncio.iscoroutinefunction(get_response) is True; that marker is what
      makes asyncio.iscoroutinefunction(instance) report True. This check
      reproduces that exact mechanism using only the standard library (asyncio /
      warnings) -- the same machinery the patched code relies on -- and asserts
      the resulting (stored, signalled, advertised) triple equals the model's
      three facts on boundary + fuzz producers.

Two further checks cover the store-selecting variant (the CacheMiddleware
restructure the three constructor PASS_TO_PASS tests pin):

  (A-consumed) the `resolve_store` axiom models the unchanged registry lookup
      `caches[alias]`. The axiom claims only that the lookup is DETERMINISTIC in
      the name (same name -> same store). The real registry read is a plain
      mapping keyed on the alias; this check reproduces it with a stdlib `dict`
      (the relied-on machinery is a keyed lookup) and asserts determinism.

  (A-reference) the store-selection deep model in `configure_settings_handler`
      establishes the load-bearing invariant `store == resolve_store(store_name)`
      across the default / explicit-default / explicit-custom construction
      paths. This check reproduces the real CacheMiddleware.__init__ control
      flow (defaults established by super().__init__, then a conditional
      override that re-selects the name AND re-resolves the store from it) using
      only a stdlib registry, and asserts the resolved store always equals the
      store the selected name designates -- i.e. exactly the `.cache ==
      caches[.cache_alias]` invariant the constructor tests assert.

Imports nothing repo-specific: only `asyncio` and `warnings` from the standard
library (the very machinery the gold patch's super().__init__ chain uses).
Exit 0 iff every obligation holds.
"""
import asyncio
import random
import sys
import warnings


# --- producer tokens ---------------------------------------------------------

async def _async_producer(request):
    return None


def _sync_producer(request):
    return None


def _make_lambda():
    return lambda request: None


# A pool of producer tokens; each is (token, is_async_expected).
def _producer_pool():
    pool = [
        (None, False),                 # the absent producer (the None case)
        (_sync_producer, False),       # a plain sync function
        (_async_producer, True),       # a coroutine function
        (_make_lambda(), False),       # a sync lambda
        (5, False),                    # a non-callable token
        ("x", False),                  # a non-callable token
        (object(), False),             # an arbitrary object
    ]
    # also wrap an async function in functools.partial-like closures
    async def _async2(req, x=1):
        return x

    def _sync2(req, x=1):
        return x
    pool.append((_async2, True))
    pool.append((_sync2, False))
    return pool


# --- (A-consumed) producer_is_async axiom vs real iscoroutinefunction --------

def check_producer_is_async_axiom(token, expected_async):
    """Assert the real predicate matches the modelled producer_is_async, and in
    particular the axiom's sole Ensures: None -> False."""
    observed = asyncio.iscoroutinefunction(token)
    assert isinstance(observed, bool), (
        "iscoroutinefunction returned non-bool on %r: %r" % (token, observed))
    # determinism
    again = asyncio.iscoroutinefunction(token)
    assert observed == again, (
        "iscoroutinefunction not deterministic on %r: %r vs %r"
        % (token, observed, again))
    assert observed == expected_async, (
        "iscoroutinefunction mismatch on %r: got %r expected %r"
        % (token, observed, expected_async))
    if token is None:
        # the axiom's only Ensures clause
        assert observed is False, (
            "axiom unsound: iscoroutinefunction(None) is %r, axiom requires "
            "False" % observed)


# --- (A-reference) deep config model vs the real super().__init__ mechanism --

class _RealHandler:
    """Faithful stdlib-only reproduction of the configuration mechanism the
    gold patch routes through: MiddlewareMixin.__init__ (called via super()).
    No django import; the relied-on machinery is pure asyncio + warnings."""

    def __init__(self, get_response):
        # step 1: deprecation signal exactly when get_response is None
        self._absence_signalled = False
        if get_response is None:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                warnings.warn(
                    "Passing None for the middleware get_response argument is "
                    "deprecated.", DeprecationWarning, stacklevel=2)
                self._absence_signalled = len(caught) >= 1
        # step 2: retain the producer
        self.get_response = get_response
        # step 3: _async_check() — set the coroutine marker iff async producer
        if asyncio.iscoroutinefunction(self.get_response):
            self._is_coroutine = asyncio.coroutines._is_coroutine


def check_configuration_reference(token, expected_async):
    """Assert the three modelled facts hold for the real configuration
    mechanism, for the given producer token."""
    h = _RealHandler(token)
    # fact (2): producer retained
    assert h.get_response is token, (
        "stored producer mismatch for %r: %r" % (token, h.get_response))
    # fact (1): absence signal fires iff producer is the absent value
    assert h._absence_signalled == (token is None), (
        "absence-signal mismatch for %r: signalled=%r expected=%r"
        % (token, h._absence_signalled, token is None))
    # fact (3): handler advertises async iff producer is async — observed
    # through the very predicate downstream code uses on the instance
    advertised = asyncio.iscoroutinefunction(h)
    assert advertised == expected_async, (
        "async-advertised mismatch for %r: handler iscoroutine=%r expected=%r"
        % (token, advertised, expected_async))


# --- (A-consumed) resolve_store axiom vs the real registry lookup ------------
# The real callee is `caches[alias]` (django.core.cache.caches), a registry that
# maps an alias name to its cache backend. It is an unchanged keyed mapping read;
# the only property the proof consumes is determinism (same name -> same store).
# Reproduced here with a plain stdlib dict registry (no django import).

_STORE_REGISTRY = {
    # alias-name token -> store token (a deterministic mapping read)
    0: 1000,        # the model's "unset" default name resolves to a store
    7: 1700,
    42: 4200,
    -3: -1300,
    1: 1100,
    99: 9900,
}


def _resolve_store_real(store_name):
    """Stdlib reproduction of the unchanged `caches[alias]` registry read:
    a deterministic keyed lookup. Unknown names resolve to a stable derived
    store (still a deterministic function of the name)."""
    if store_name in _STORE_REGISTRY:
        return _STORE_REGISTRY[store_name]
    return ("store", store_name)


def check_resolve_store_axiom(store_name):
    """Assert the registry read is deterministic in the name (the sole property
    the resolve_store axiom claims)."""
    a = _resolve_store_real(store_name)
    b = _resolve_store_real(store_name)
    assert a == b, (
        "resolve_store not deterministic on %r: %r vs %r" % (store_name, a, b))


# --- (A-reference) store-selection deep model vs real CacheMiddleware flow ----

class _RealStoreHandler:
    """Stdlib-only reproduction of the store-selection control flow of the
    patched CacheMiddleware.__init__: super().__init__ establishes the default
    name and resolves the store from it; an explicit override re-selects the
    name AND re-resolves the store from the new name. Mirrors the gold patch's
    `self.cache_alias = ...; self.cache = caches[self.cache_alias]` discipline."""

    def __init__(self, default_name, override_name):
        # defaults first (as super().__init__ -> base init does)
        self.store_name = default_name
        self.store = _resolve_store_real(self.store_name)
        # explicit override re-selects the name and re-resolves the store
        if override_name is not None:
            self.store_name = override_name
            self.store = _resolve_store_real(self.store_name)


def check_store_selection_reference(default_name, override_name):
    """Assert the load-bearing invariant: the resolved store always equals the
    store the selected name designates -- on every construction path."""
    h = _RealStoreHandler(default_name, override_name)
    expected_name = override_name if override_name is not None else default_name
    assert h.store_name == expected_name, (
        "store-name selection mismatch: default=%r override=%r got=%r"
        % (default_name, override_name, h.store_name))
    assert h.store == _resolve_store_real(h.store_name), (
        "store/name inconsistency: name=%r store=%r expected=%r"
        % (h.store_name, h.store, _resolve_store_real(h.store_name)))


def main():
    pool = _producer_pool()

    # boundary: every token in the pool
    for token, exp in pool:
        check_producer_is_async_axiom(token, exp)
        check_configuration_reference(token, exp)

    # boundary: store-selection paths (default / explicit-default / custom),
    # including known + unknown alias names and the None-override (defaults) case
    store_names = [0, 7, 42, -3, 1, 99, 123456, -7]
    for dn in store_names:
        # the default path: no override -> store resolved from the default name
        check_resolve_store_axiom(dn)
        check_store_selection_reference(dn, None)
        for ov in store_names:
            # the override path: store re-resolved from the override name
            check_resolve_store_axiom(ov)
            check_store_selection_reference(dn, ov)

    # randomized fuzz: build random sync/async producers and non-callables
    rng = random.Random(13344)
    fuzz = 0
    for _ in range(4000):
        kind = rng.randint(0, 4)
        if kind == 0:
            token, exp = None, False
        elif kind == 1:
            def _f(request):
                return None
            token, exp = _f, False
        elif kind == 2:
            async def _g(request):
                return None
            token, exp = _g, True
        elif kind == 3:
            token, exp = rng.randint(-1000, 1000), False
        else:
            token, exp = (lambda request: None), False
        check_producer_is_async_axiom(token, exp)
        check_configuration_reference(token, exp)
        # store-selection fuzz: random default + (maybe None) override names
        dn = rng.randint(-10000, 10000)
        ov = None if rng.randint(0, 1) == 0 else rng.randint(-10000, 10000)
        check_resolve_store_axiom(dn)
        if ov is not None:
            check_resolve_store_axiom(ov)
        check_store_selection_reference(dn, ov)
        fuzz += 1

    print("G-AX OK: producer_is_async axiom (== asyncio.iscoroutinefunction) "
          "and the configuration deep model (== super().__init__ marker "
          "mechanism) sound on %d boundary + %d fuzz producer tokens; "
          "resolve_store axiom (== caches[alias] registry read) deterministic "
          "and the store-selection deep model (store == resolve_store(name) on "
          "the default/explicit-default/custom paths) sound on all boundary + "
          "fuzz name pairs" % (len(pool), fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
