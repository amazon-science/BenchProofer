#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11333.

This bundle has NO `@ContractOnly` axiom and NO A-reference deep model that
stands in for a real stdlib/library callee: the only deep modeling is

  (i) the omitted-means-default substitution (`resolve_selector`), and
  (ii) the `functools.lru_cache(maxsize=None)` memo, modeled as a `Dict`
       lookup-or-insert keyed on the RESOLVED selector.

There is therefore nothing for G-AX to falsify against a real callee's observed
behaviour; soundness rests on refinement fidelity (refinement.md, G-EQ) and the
real-harness oracle (G-RESOLVE). To make that explicit and machine-checkable,
this script validates the TWO modeling assumptions the refinement leans on,
against the REAL `functools.lru_cache` (the exact stdlib facility the gold
patch uses) -- not a hand-rolled stand-in:

  1. `lru_cache(maxsize=None)` is a faithful memo: keyed by call arguments,
     a repeated key returns the *same object* (identity), a new key constructs
     and stores; no eviction (the cache only grows). This is what the model's
     `Dict` lookup-or-insert + "cache only grows" postcondition abstracts.

  2. Resolve-THEN-memoize (the gold ordering) makes the omitted selector and the
     explicit default selector share ONE cached object, while a distinct
     selector gets a distinct object -- and memoize-THEN-resolve (the pre-patch
     ordering) does NOT (the F2P discriminator). We reconstruct both orderings
     faithfully on top of the real `lru_cache` and assert the identity outcomes
     the F2P test (`assertIs` / `assertIsNot`) demands.

stdlib-only imports (`functools`, the same module the gold patch calls). Exit 0
iff every obligation holds.
"""
import functools
import random
import sys


# A stand-in for the expensive constructed object: each call yields a NEW object
# with a distinct identity, exactly like `URLResolver(RegexPattern(r'^/'), urlconf)`.
class _Resolver:
    __slots__ = ("urlconf",)

    def __init__(self, urlconf):
        self.urlconf = urlconf


def _build_resolve_then_cache(root):
    """Faithful reconstruction of the GOLD ordering: resolve the omitted
    selector to `root` FIRST, then memoize on the resolved value."""
    @functools.lru_cache(maxsize=None)
    def _get_cached_resolver(urlconf=None):
        return _Resolver(urlconf)

    def get_resolver(urlconf=None):
        if urlconf is None:
            urlconf = root
        return _get_cached_resolver(urlconf)

    return get_resolver


def _build_cache_then_resolve(root):
    """Faithful reconstruction of the PRE-PATCH ordering: memoize on the RAW
    argument, resolve the omitted selector to `root` only INSIDE the cached
    body (so `None` and `root` are distinct cache keys)."""
    @functools.lru_cache(maxsize=None)
    def get_resolver(urlconf=None):
        if urlconf is None:
            urlconf = root
        return _Resolver(urlconf)

    return get_resolver


def check_lru_cache_is_a_memo():
    """Assumption 1: lru_cache(maxsize=None) returns the SAME object for a
    repeated key, a NEW object for a new key, and never evicts."""
    calls = []

    @functools.lru_cache(maxsize=None)
    def f(k):
        obj = _Resolver(k)
        calls.append(k)
        return obj

    a1 = f(10)
    a2 = f(10)
    assert a1 is a2, "lru_cache did not return the same object for a repeated key"
    b = f(20)
    assert b is not a1, "lru_cache returned the same object for distinct keys"
    # no eviction: the first key is still cached (constructor not re-invoked)
    a3 = f(10)
    assert a3 is a1, "lru_cache evicted a key under maxsize=None"
    assert calls == [10, 20], (
        "lru_cache re-invoked the constructor for a cached key: %r" % (calls,))


def check_gold_identity(root, other):
    """Assumption 2 (gold ordering): omitted selector and explicit default
    share one object; a distinct selector gets a distinct object."""
    get_resolver = _build_resolve_then_cache(root)
    # F2P assertIs: omitted == explicit default -> SAME object
    assert get_resolver() is get_resolver(root), (
        "gold ordering: get_resolver() is not get_resolver(default) for "
        "root=%r" % (root,))
    # F2P assertIsNot: a different selector -> DISTINCT object
    assert get_resolver() is not get_resolver(other), (
        "gold ordering: get_resolver() collided with a different selector "
        "%r" % (other,))


def check_prepatch_breaks_identity(root, other):
    """The pre-patch ordering FAILS the assertIs half (the bug we sense): the
    omitted selector and the explicit default end up as DISTINCT objects."""
    get_resolver = _build_cache_then_resolve(root)
    assert get_resolver() is not get_resolver(root), (
        "pre-patch ordering unexpectedly shared an object -- the F2P "
        "discriminator would not distinguish the fix (root=%r)" % (root,))
    # the assertIsNot half still holds pre-patch (distinct selectors differ)
    assert get_resolver() is not get_resolver(other)


def main():
    check_lru_cache_is_a_memo()

    # boundary roots/others incl. the literal F2P configuration
    cases = [
        ("urlpatterns.path_urls", "urlpatterns.path_dynamic_urls"),
        ("a", "b"),
        ("", "x"),
        ("django.conf.urls", "myapp.urls"),
    ]
    for root, other in cases:
        assert root != other
        check_gold_identity(root, other)
        check_prepatch_breaks_identity(root, other)

    # randomized fuzz over distinct (root, other) string pairs
    rng = random.Random(11333)
    alphabet = "abcdefghijklmnopqrstuvwxyz._0123456789"
    n_fuzz = 5000
    for _ in range(n_fuzz):
        root = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 12)))
        other = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 12)))
        if root == other:
            other = other + "x"
        check_gold_identity(root, other)
        check_prepatch_breaks_identity(root, other)

    print("G-AX OK: no axioms/A-references to falsify; the two modeling "
          "assumptions validated against the REAL functools.lru_cache "
          "(memo identity + no eviction) and the resolve-then-memoize vs "
          "memoize-then-resolve identity outcomes (gold shares one object, "
          "pre-patch does not) over %d boundary + %d fuzz selector pairs."
          % (len(cases), n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
