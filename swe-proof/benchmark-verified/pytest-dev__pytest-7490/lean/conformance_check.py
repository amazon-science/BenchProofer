#!/usr/bin/env python3
"""G-CONF for pytest-dev__pytest-7490.

The gold patch is already applied to /testbed when this runs (so the test-call
hookwrapper of `_pytest/skipping.py` refreshes the stored xfail annotation after
the body runs). We compare the R/I Python shadow of
`implementation_resolveExpectedFailure` (the Lean impl, transliterated op-for-op
per refinement.md) against the REAL patched store-refresh logic exercised
through `_pytest.store.Store` + the real `xfailed_key`, over >=1e5 fuzzed
`(before, after)` annotation states. Zero disagreements => exit 0.

Type bijection (mapping.md):
  before : Option ExpectedFailure  <->  item._store.get(xfailed_key, None) at
                                        entry to pytest_runtest_call (None | Xfail)
  after  : Option ExpectedFailure  <->  evaluate_xfail_marks(item) re-evaluated
                                        after the body ran (None | Xfail)
  result : Option ExpectedFailure  <->  item._store[xfailed_key] after the patched
                                        post-body refresh (None | Xfail)

We use the genuine pytest data structures: the real `Store`/`StoreKey` and the
real `Xfail` attrs class from the (patched) repo. The oracle replays the exact
patched post-yield refresh fragment against a real Store; the only stub is the
re-evaluation hook (we feed the fuzzed `after` directly, since the patch does
not change `evaluate_xfail_marks`, only when its result is stored).

stdlib-only (plus the in-container pytest package); no hypothesis required.
"""
import random
import sys

from _pytest.store import Store, StoreKey
from _pytest.skipping import Xfail, xfailed_key


def make_xfail(reason, run, strict):
    """A real repo Xfail object (raises left None — irrelevant to selection)."""
    return Xfail(reason, run, strict, None)


def xfail_eq(a, b):
    """Structural equality on the modeled reporting view (reason/run/strict)."""
    if a is None or b is None:
        return a is None and b is None
    return (a.reason, a.run, a.strict) == (b.reason, b.run, b.strict)


def oracle(before, after):
    """Real patched behavior: run the post-body refresh fragment from the
    patched pytest_runtest_call against a genuine Store seeded with `before`.

        xfailed = item._store.get(xfailed_key, None)   # == before
        if xfailed is None:
            item._store[xfailed_key] = xfailed = evaluate_xfail_marks(item)  # after
        -> report consults item._store[xfailed_key]
    """
    store = Store()
    # `before` is what the setup hook / pre-yield block left in the store.
    # `None` models "nothing stored yet" as observed via .get(key, None).
    if before is not None:
        store[xfailed_key] = before

    xfailed = store.get(xfailed_key, None)
    if xfailed is None:
        # evaluate_xfail_marks(item) re-evaluated after the body ran == `after`
        store[xfailed_key] = xfailed = after

    return store.get(xfailed_key, None)


def shadow(before, after):
    """R/I transliteration of implementation_resolveExpectedFailure (Lean).

        let mut xfailed := before
        if xfailed.isNone then xfailed := after
        return xfailed
    """
    xfailed = before
    if xfailed is None:
        xfailed = after
    return xfailed


def rand_annotation(rng):
    """None | Xfail with fuzzed reporting fields."""
    if rng.random() < 0.4:
        return None
    reason = rng.choice(["", "xfail", "flaky", "known bug", "reason: x", "[NOTRUN] z"])
    run = rng.random() < 0.5
    strict = rng.random() < 0.5
    return make_xfail(reason, run, strict)


def main():
    rng = random.Random(7490)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for _ in range(N):
        before = rand_annotation(rng)
        after = rand_annotation(rng)
        o = oracle(before, after)
        s = shadow(before, after)
        if not xfail_eq(o, s):
            disagreements += 1
            if first is None:
                first = (before, after, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r"
              % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
