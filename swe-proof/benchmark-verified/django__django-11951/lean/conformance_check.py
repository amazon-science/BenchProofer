#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-11951.

The bundle models the part of the bulk-insert helper that decides batch
boundaries (mapping.md): from a caller-requested batch size and the backend's
compatible maximum, it computes the effective per-batch size and slices the
object list into the consecutive batches the helper then inserts one at a time.

The decision is a PURE function of three observables the helper has in hand:

    batch_size : int   (the `batch_size` parameter; None/0 == unset/falsy)
    raw_max    : int   (ops.bulk_batch_size(fields, objs); >= 0)
    objs       : list  (the objects to insert; only positions matter)

Standing up a database backend + connection + a real `QuerySet._batched_insert`
to drive batching is heavy and unnecessary: the modeled value is exactly this
pure decision over the observables the real routine reads. So the ORACLE below is
a faithful in-process replica using the EXACT patched expressions:

    max_batch_size = max(raw_max, 1)
    batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size
    batches = [objs[i:i + batch_size] for i in range(0, len(objs), batch_size)]

The SHADOW is the op-for-op transliteration of `implementation_splitBatches` /
`effectiveBatchSize` / `chunkBatches` (per refinement.md):

    max_batch_size = max(raw_max, 1)
    eff = max_batch_size if batch_size == 0 else min(batch_size, max_batch_size)
    n = (len(objs) + eff - 1) // eff
    batches = [objs[k*eff : k*eff + eff] for k in range(n)]

Batches are compared as ordered lists of ordered lists (the bijection is
positional identity — mapping.md). This genuinely tests:
  * the F2P behavior: an explicit batch_size LARGER than max_batch_size is capped
    to max_batch_size (more, smaller batches than the buggy override would give);
  * an explicit batch_size SMALLER than max_batch_size is honored;
  * the unset (0/falsy) request falls back to max_batch_size;
  * raw_max == 0 normalized up to 1;
  * empty objs -> no batches; exact-multiple and remainder splits.

stdlib-only. Pinned seed: 20240627 (also in mapping.md).
"""
import random
import sys

SEED = 20240627
N = 120_000


# --- ORACLE: faithful in-process replica of the patched batching -------------
def oracle(batch_size, raw_max, objs):
    max_batch_size = max(raw_max, 1)
    bs = min(batch_size, max_batch_size) if batch_size else max_batch_size
    return [objs[i:i + bs] for i in range(0, len(objs), bs)]


# --- SHADOW of implementation_splitBatches (the R / I / A-reference leg) ------
# Mirrors Solution.lean:
#   effectiveBatchSize bs rm = let m = max rm 1
#                              if bs = 0 then m else min bs m
#   batchCount eff n         = (n + eff - 1) / eff
#   chunkBatches eff objs    = [ (objs.drop (k*eff)).take eff | k in range cnt ]
def shadow(batch_size, raw_max, objs):
    max_batch_size = max(raw_max, 1)
    eff = max_batch_size if batch_size == 0 else min(batch_size, max_batch_size)
    n = (len(objs) + eff - 1) // eff
    return [objs[k * eff: k * eff + eff] for k in range(n)]


def disagree(bs, rm, objs):
    o = oracle(bs, rm, objs)
    s = shadow(bs, rm, objs)
    if o != s:
        return ((bs, rm, objs), o, s)
    return None


def _enumerate_edge():
    cases = []
    pools = [[], [0], list(range(7)), list(range(10)), list(range(1000))]
    for objs in pools:
        # unset request -> use max(raw_max,1)
        cases.append((0, 3, objs))
        cases.append((0, 0, objs))     # raw_max 0 -> normalized to 1
        cases.append((0, 1, objs))
        # explicit request larger than max -> capped (the F2P fix)
        cases.append((5, 3, objs))
        cases.append((len(objs) + 1 if objs else 1, 3, objs))
        # explicit request smaller than max -> honored
        cases.append((2, 5, objs))
        cases.append((1, 100, objs))
        # explicit request equal to max
        cases.append((4, 4, objs))
        # explicit request equals len (exact single batch when <= max)
        cases.append((len(objs) or 1, 10_000, objs))
    return cases


def main() -> int:
    checked = 0
    for bs, rm, objs in _enumerate_edge():
        d = disagree(bs, rm, objs)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        bs = rng.randint(0, 30)        # 0 models the unset/falsy request
        rm = rng.randint(0, 30)
        nobj = rng.randint(0, 40)
        objs = list(range(nobj))
        d = disagree(bs, rm, objs)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
