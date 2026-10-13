#!/usr/bin/env python3
"""G-AX for django__django-17029 — validates the single A-reference fact.

The bundle consumes NO axiom contract. Its one external soundness anchor
(refinement.md A2/A3, mapping.md §3) is the representation refinement

    method.cache_clear()  ==>  method.cache_info().currsize == 0

for a `functools._lru_cache_wrapper` (the wrapper produced by
`@functools.cache`, which is `functools.lru_cache(maxsize=None)`) — the two
caches `Apps.get_swappable_settings_name` and `Apps.get_models` are backed by.
`Solution.lean` refines `currsize` to a `Nat` and `cache_clear()` to assigning
`0`; this script exercises the REAL stdlib callee to confirm that, from ANY
starting occupancy, `cache_clear()` drives `currsize` to `0`.

stdlib-only. Exits 0 iff the A-reference holds on every boundary + fuzz case;
non-zero (with diagnostics) otherwise.
"""
import functools
import random
import sys


def run_case(distinct_keys, repeated_calls, seed):
    """Build a fresh @functools.cache-decorated function, prime it with
    `distinct_keys` distinct argument tuples (plus repeats), record the filled
    occupancy, then cache_clear() and assert currsize == 0."""
    rng = random.Random(seed)

    @functools.cache
    def f(a, b):
        return (a, b)

    keys = [(rng.randint(-10**6, 10**6), rng.randint(-10**6, 10**6))
            for _ in range(distinct_keys)]
    for k in keys:
        f(*k)
    # repeated calls must NOT change occupancy (distinct-tuple counting)
    for _ in range(repeated_calls):
        if keys:
            f(*rng.choice(keys))

    filled = f.cache_info().currsize
    expected_filled = len(set(keys))
    if filled != expected_filled:
        return (f"priming mismatch: currsize={filled} != distinct keys "
                f"{expected_filled} (distinct_keys={distinct_keys})")

    f.cache_clear()
    after = f.cache_info().currsize
    if after != 0:
        return (f"cache_clear did NOT empty cache: currsize={after} != 0 "
                f"(was {filled}; distinct_keys={distinct_keys})")
    return None


def main():
    failures = []

    # Boundary cases: empty cache, single entry, then clear.
    boundary = [(0, 0), (1, 0), (1, 5), (2, 3)]
    for i, (dk, rc) in enumerate(boundary):
        err = run_case(dk, rc, seed=1000 + i)
        if err:
            failures.append(f"[boundary {dk},{rc}] {err}")

    # Fuzz: many random occupancies and repeated-call counts.
    rng = random.Random(20240617)
    for i in range(2000):
        dk = rng.randint(0, 200)
        rc = rng.randint(0, 200)
        err = run_case(dk, rc, seed=rng.randint(0, 2**31))
        if err:
            failures.append(f"[fuzz {i}: dk={dk},rc={rc}] {err}")

    if failures:
        print("G-AX FAIL: functools.cache cache_clear() A-reference violated:",
              file=sys.stderr)
        for fmsg in failures[:20]:
            print("  " + fmsg, file=sys.stderr)
        return 1

    print("G-AX pass: functools.cache cache_clear() drives cache_info().currsize "
          "to 0 from every tested starting occupancy (boundary + 2000 fuzz). "
          "A-reference (refinement.md A2/A3) validated against the real stdlib "
          "callee.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
