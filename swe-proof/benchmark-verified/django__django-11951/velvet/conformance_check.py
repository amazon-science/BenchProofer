#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-11951.

Refutes the R/I refinement leg (A3-A4: the modeled chunk-size derivation
`maxBatchSize if batchSize == 0 else min(batchSize, maxBatchSize)` over `Nat`
inputs).

ORACLE CHOICE — why we transliterate the source line instead of running
`_batched_insert`:
  The patched assignment lives inside `QuerySet._batched_insert`, which requires
  a live database connection, a `QuerySet`, real model objects, and the backend's
  `ops.bulk_batch_size(...)` round-trip. The behavior under test is the pure
  arithmetic that combines the caller's requested `batch_size` with the
  database-compatible `max_batch_size`. So, per the worker prompt, the ORACLE is
  the patched source line transliterated VERBATIM:
      batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size
  (from the gold-patched django/db/models/query.py, `_batched_insert`). The
  SHADOW is the modeled formula from Solution.lean's `effectiveBatchSize`
  post-image. We differential-test SHADOW vs ORACLE over fuzzed
  (batch_size, max_batch_size) pairs with max_batch_size >= 1 plus boundary
  cases. Exit 0 iff zero disagreements. stdlib only.

  CALLEE ABSTRACTION: the database callee `ops.bulk_batch_size(fields, objs)`
  (floored at 1 via `max(..., 1)`) is UNCHANGED by the patch and identical on
  both sides of the fix. It is therefore abstracted as the `max_batch_size`
  input here (mapping.md §3) and fuzzed directly over max_batch_size >= 1 — there
  is no axiom and no axiom_check.py.
"""
import random
import sys

SEED = 11951
N_FUZZ = 200_000
MAX_VAL = 4096


def shadow(batch_size, max_batch_size):
    """effectiveBatchSize transliterated: the modeled chunk-size derivation.
    Mirrors `if batchSize = 0 then maxBatchSize else min batchSize maxBatchSize`
    exactly. (`Nat` truthiness: 0 is the unspecified branch.)"""
    if batch_size == 0:
        return max_batch_size
    return min(batch_size, max_batch_size)


def oracle(batch_size, max_batch_size):
    """The patched source line, transliterated verbatim from
    django/db/models/query.py (gold-patched _batched_insert):
        batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size
    `batch_size` is a non-negative count, so `if batch_size:` is truthy iff != 0
    (None maps to the unspecified branch, modeled as 0)."""
    return min(batch_size, max_batch_size) if batch_size else max_batch_size


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    cases = []
    # Boundary cases: unspecified (0), exactly at cap, just over cap, just under.
    for m in (1, 2, 3, 10, MAX_VAL):
        for b in (0, 1, m - 1, m, m + 1, m + 1000, 2 * m):
            if b < 0:
                continue
            cases.append((b, m))
    # Fuzz: max_batch_size >= 1 (the require), batch_size >= 0 (0 = unspecified).
    for _ in range(N_FUZZ):
        m = rng.randint(1, MAX_VAL)
        b = rng.randint(0, MAX_VAL)
        cases.append((b, m))

    for batch_size, max_batch_size in cases:
        count += 1
        s = shadow(batch_size, max_batch_size)
        o = oracle(batch_size, max_batch_size)
        if s != o:
            disagreements.append((batch_size, max_batch_size, s, o))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of effectiveBatchSize agrees with the patched "
          "source line on %d (batch_size, max_batch_size) pairs "
          "(boundary + fuzz, seed=%d, max_batch_size>=1), 0 disagreements. "
          "DB callee bulk_batch_size abstracted as the max_batch_size input."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
