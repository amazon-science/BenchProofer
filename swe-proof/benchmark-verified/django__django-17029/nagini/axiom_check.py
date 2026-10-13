#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-17029.

The bundle consumes NO `@ContractOnly` axiom: the cache-reset is modeled as a
direct state write to each memoizing method's observable cache occupancy
(`*_cache_occupancy = 0`). The single external fact the refinement leans on is
an A-reference about the UNCHANGED standard-library callee `functools.cache`
(== `functools.lru_cache(maxsize=None)`):

    for a `functools.cache`-wrapped method, after `m.cache_clear()` the
    observable occupancy `m.cache_info().currsize` is 0 — from ANY starting
    occupancy (empty, partially full, full, repeatedly filled).

This is exactly the representation refinement
`method.cache_clear()` ↔ `occupancy = 0` (refinement.md A2/A3, mapping.md §2/§3).
G-AX validates that A-reference by exercising the REAL `functools.cache` callee:
it builds wrappers, drives their `currsize` to a range of starting occupancies
(boundary + fuzz), calls `cache_clear()`, and asserts `currsize == 0` and that a
non-cleared sibling wrapper is unaffected (so the reset must clear EACH wrapper,
the discriminating property the patch fixes).

Imports nothing repo-specific: `functools` is the Python standard library — the
exact module `Apps.get_models` / `Apps.get_swappable_settings_name` are wrapped
with and that `clear_cache()` calls `cache_clear()` on. Exit 0 iff every
obligation holds.
"""
import functools
import random
import sys


def make_wrapper():
    """A `functools.cache`-wrapped function, mirroring how Django decorates
    `Apps.get_models` / `Apps.get_swappable_settings_name`."""
    @functools.cache
    def f(x):
        return x * x
    return f


def fill(wrapper, n):
    """Memoize `n` distinct argument tuples, driving currsize up to `n`."""
    for i in range(n):
        wrapper(i)


def check_clear_zeroes_from(occupancy):
    """A-reference: from a wrapper holding `occupancy` distinct results,
    cache_clear() must make currsize == 0 (the real functools callee)."""
    w = make_wrapper()
    fill(w, occupancy)
    assert w.cache_info().currsize == occupancy, (
        "precondition setup wrong: expected currsize %d, got %d"
        % (occupancy, w.cache_info().currsize))
    w.cache_clear()                               # real functools callee
    got = w.cache_info().currsize
    assert got == 0, (
        "functools.cache A-reference unsound: cache_clear() from occupancy %d "
        "left currsize == %d, expected 0" % (occupancy, got))


def check_repeated_fill_then_clear(occupancy, rounds):
    """cache_clear() returns currsize to 0 even after refilling/repeated use."""
    w = make_wrapper()
    for _ in range(rounds):
        fill(w, occupancy)
        for i in range(occupancy):                # re-access (lru ordering)
            w(i)
    w.cache_clear()
    got = w.cache_info().currsize
    assert got == 0, (
        "functools.cache A-reference unsound: cache_clear() after %d refill "
        "rounds of occupancy %d left currsize == %d" % (rounds, occupancy, got))


def check_each_wrapper_independent():
    """The discriminating property the patch fixes: clearing ONE wrapper does
    not clear another, so the reset must call cache_clear() on EVERY memoizing
    method. Here, modeling the two Apps caches: clearing only the 'models'
    wrapper leaves the 'swappable' wrapper's occupancy intact (the pre-patch
    bug); clearing BOTH zeroes BOTH (the fix)."""
    models = make_wrapper()           # ~ Apps.get_models
    swappable = make_wrapper()        # ~ Apps.get_swappable_settings_name
    fill(models, 7)
    fill(swappable, 5)
    # pre-patch behaviour: clear only the models wrapper
    models.cache_clear()
    assert models.cache_info().currsize == 0
    assert swappable.cache_info().currsize == 5, (
        "expected clearing one wrapper to leave the other untouched; the "
        "A-reference's independence assumption is wrong")
    # the fix: also clear the swappable wrapper
    swappable.cache_clear()
    assert swappable.cache_info().currsize == 0, (
        "functools.cache A-reference unsound: cache_clear() on the second "
        "wrapper did not zero its currsize")


def main():
    # boundary occupancies: empty, single, small, larger
    boundary = [0, 1, 2, 3, 5, 7, 16, 64, 256]
    for occ in boundary:
        check_clear_zeroes_from(occ)

    # repeated fill/refill then clear
    for occ in [0, 1, 4, 32]:
        for rounds in [1, 2, 5]:
            check_repeated_fill_then_clear(occ, rounds)

    # fuzz: random starting occupancies
    rng = random.Random(17029)
    for _ in range(2000):
        occ = rng.randint(0, 300)
        check_clear_zeroes_from(occ)

    # the per-wrapper independence (why ALL caches must be cleared)
    check_each_wrapper_independent()

    print("G-AX OK: functools.cache cache_clear() A-reference sound — "
          "currsize == 0 after clear from %d boundary + 2000 fuzz occupancies "
          "and repeated-refill cases; per-wrapper independence confirmed"
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
