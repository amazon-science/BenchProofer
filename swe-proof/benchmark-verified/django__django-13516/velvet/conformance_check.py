#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13516 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `propagateFlush` impl region
              transliterated to Python over the *real* repo state (an
              `OutputWrapper` restricted to its flush-relevant carrier), via the
              mapping.md bijection (`OutputSink ↔ ⟨hasattr(w._out,'flush'), k⟩`,
              one forwarded flush ↔ `+1`). The branch is pure R/I; there is no
              consumed axiom in the computed state, so the shadow is exact.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.core.management.base.OutputWrapper.flush` applied at
              base_commit (the real correctness oracle, G-RESOLVE), driven on a
              wrapped underlying stream that records how many times its own
              `flush` is reached.

An "input" is a (flushable, n_requests) pair: whether the wrapped underlying
stream exposes `flush`, and how many flush requests are issued on the wrapper.
The observable compared is the resulting forwarded-flush count (and that the
non-flushable configuration never raises). They must agree on every input.
Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The
fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys
from io import StringIO
from unittest import mock

SEED = 13516
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean propagateFlush, transliterated ------------
def shadow_flush_count(flushable, n_requests):
    """`propagateFlush` run `n_requests` times on a sink with the given
    `flushable`, returning the final `flushes` count.

    Transliteration of the impl `do` block:
        if sink.flushable then sink := {sink with flushes := flushes + 1}
        else return
    `flushable` is read-only (the `ensures sink.flushable = sinkOld.flushable`
    frame), so it never changes across requests."""
    flushes = 0
    for _ in range(n_requests):
        if flushable:               # if sink.flushable then
            flushes = flushes + 1   #   flushes := flushes + 1
        # else: no-op (return), state unchanged
    return flushes


# --- the oracle: patch.diff's behaviour --------------------------------------
class _NoFlushStream:
    """An underlying stream WITHOUT a `flush` attribute (non-flushable). Defines
    only `write`; `hasattr(self, 'flush')` is False."""
    def __init__(self):
        self.buf = []

    def write(self, s):
        self.buf.append(s)


def oracle_flush_count(flushable, n_requests):
    """patch.diff's behaviour: the patched OutputWrapper.flush() reached
    `n_requests` times, counting how many forwarded flushes hit the underlying
    stream. The harness applies patch.diff before this runs, so the imported
    OutputWrapper has the new `flush` method."""
    from django.core.management.base import OutputWrapper

    if flushable:
        out = StringIO()  # StringIO exposes flush -> hasattr(out,'flush') True
        with mock.patch.object(out, 'flush') as mocked:
            w = OutputWrapper(out)
            assert hasattr(w._out, 'flush'), "fixture flushable mismatch"
            for _ in range(n_requests):
                w.flush()
            return mocked.call_count
    else:
        out = _NoFlushStream()
        w = OutputWrapper(out)
        assert not hasattr(w._out, 'flush'), "fixture non-flushable mismatch"
        for _ in range(n_requests):
            w.flush()  # must not raise
        return 0


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield (True, 0)
    yield (True, 1)
    yield (True, 2)
    yield (False, 0)
    yield (False, 1)
    yield (False, 5)
    yield (True, 10)
    for _ in range(n):
        flushable = rng.random() < 0.5
        k = rng.randint(0, 12)
        yield (flushable, k)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for flushable, n_req in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_flush_count(flushable, n_req)
        try:
            oracle = oracle_flush_count(flushable, n_req)
        except Exception as e:  # a raise on the non-flushable path is a failure
            disagreements.append(((flushable, n_req), shadow,
                                  "RAISED:%s" % type(e).__name__))
            if len(disagreements) >= 5:
                break
            continue
        if shadow != oracle:
            disagreements.append(((flushable, n_req), shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for inp, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of propagateFlush agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
