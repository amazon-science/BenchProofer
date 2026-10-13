#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-14559.

The bundle models ONE function: `QuerySet.bulk_update`. Its Lean implementation
(`implementation_bulkUpdate`) returns the number of rows matched by a batched
bulk modification:

    if keys empty:        return some 0
    batches := toChunks batchSize keys
    rowsUpdated := 0
    for batch in batches: rowsUpdated += batch.dedup.length
    return some rowsUpdated

This script transliterates that R/I impl into Python (`shadow_bulk_update`) and
differential-tests it against an ORACLE that reproduces the POST-PATCH behavior
of `QuerySet.bulk_update` (`django/db/models/query.py`) WITHOUT standing up a
database:

    if not objs:        return 0
    batches = [objs[i:i+batch_size] for i in range(0, len(objs), batch_size)]
    rows_updated = 0
    for batch in batches:
        # self.filter(pk__in=pks).update(**kwargs) matches each DISTINCT pk in
        # the batch once (SQL `WHERE pk IN (...)` dedups), and every modeled key
        # references an existing stored row, so the matched count for the batch
        # is the number of distinct pks in it.
        rows_updated += len(set(pk for pk in batch))
    return rows_updated

The differential's KEY observables (mapping.md):
  * the batching: Lean `toChunks batchSize` must equal Python's
    `objs[i:i+batch_size] for i in range(0, len(objs), batch_size)`;
  * the per-batch matched count: `batch.dedup.length` (order-preserving distinct)
    must equal the SQL-`IN` distinct-pk count `len(set(batch))`;
  * the empty case: `some 0` ↔ `0`;
  * the result presence: post-patch always returns an int (`some n`), never None.

We deliberately reproduce the patched accumulation arithmetically rather than
through the ORM (the modeled value is a pure count over the per-batch identifier
multiset; a live DB would only re-derive the same count more slowly). The
duplicate-across-batches subtlety the issue/F2P test pins
(`test_updated_rows_when_passing_duplicates`) is exercised directly by the
fuzzer, which injects duplicate keys at controlled batch sizes.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 14559 (mapping.md).
"""
import json
import random
import sys

SEED = 14559
N = 120_000


# --- batching helper: faithful replica of Lean `List.toChunks batchSize` ------
# For batchSize >= 1, Lean's `List.toChunks n xs` yields consecutive slices of
# length n (last possibly shorter) — identical to Python's
# `xs[i:i+n] for i in range(0, len(xs), n)`.
def chunks(batch_size, keys):
    return [keys[i:i + batch_size] for i in range(0, len(keys), batch_size)]


def order_preserving_dedup_len(batch):
    """Lean `List.dedup` length: count of distinct elements (order-preserving,
    but length is order-independent). Equals `len(set(batch))`."""
    seen = []
    for x in batch:
        if x not in seen:
            seen.append(x)
    return len(seen)


# --- ORACLE: post-patch bulk_update return value (faithful in-process replica) -
def oracle_bulk_update(keys, batch_size):
    if not keys:                      # `if not objs: return 0`
        return 0
    rows_updated = 0
    for batch in chunks(batch_size, keys):
        # self.filter(pk__in=batch).update(...) -> rows matched = distinct pks
        rows_updated += len(set(batch))
    return rows_updated


# --- SHADOW: transliteration of implementation_bulkUpdate (op-for-op) ----------
def shadow_bulk_update(keys, batch_size):
    if len(keys) == 0:                # keys.isEmpty -> return some 0
        return 0
    rows_updated = 0
    for batch in chunks(batch_size, keys):
        rows_updated += order_preserving_dedup_len(batch)  # batch.dedup.length
    return rows_updated


def gen_case(rng):
    """A fuzzed (keys, batch_size) drawn from the modeled domain: batch_size >= 1,
    keys a list of identifiers (with deliberate duplicates to exercise the
    within-batch vs across-batch distinction)."""
    kind = rng.random()
    if kind < 0.08:
        keys = []                                   # empty input
    else:
        n = rng.randint(1, 40)
        # small id pool so duplicates (within and across batches) are frequent
        pool = rng.randint(1, max(1, n // 2 + 1))
        keys = [rng.randint(0, pool) for _ in range(n)]
        if rng.random() < 0.3:                      # force an adjacent duplicate
            keys = keys + keys[:rng.randint(1, len(keys))]
            rng.shuffle(keys)
    batch_size = rng.randint(1, 12)
    return keys, batch_size


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    first = None
    # deterministic boundary cases incl. the F2P discriminator
    boundary = [
        ([], 5),
        ([7, 7], 5),     # duplicates, same batch  -> 1
        ([7, 7], 1),     # duplicates, split batch -> 2
        ([1], 1),
        (list(range(2000)), 1000),  # large batch -> 2000
        ([3, 3, 3], 2),  # [[3,3],[3]] -> 1 + 1 = 2
        ([3, 3, 3], 3),  # [[3,3,3]]   -> 1
    ]
    for keys, bs in boundary:
        if oracle_bulk_update(keys, bs) != shadow_bulk_update(keys, bs):
            disagreements += 1
            if first is None:
                first = (keys, bs, oracle_bulk_update(keys, bs),
                         shadow_bulk_update(keys, bs))
    for _ in range(N):
        keys, bs = gen_case(rng)
        o = oracle_bulk_update(keys, bs)
        s = shadow_bulk_update(keys, bs)
        if o != s:
            disagreements += 1
            if first is None:
                first = (keys, bs, o, s)
    status = "pass" if disagreements == 0 else "fail"
    print(json.dumps({
        "status": status,
        "instance": "django__django-14559",
        "seed": SEED,
        "cases": N + len(boundary),
        "disagreements": disagreements,
        "first_disagreement": first,
    }))
    return 0 if disagreements == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
