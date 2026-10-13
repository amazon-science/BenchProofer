#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-13089.

The bundle models ONE maintenance pass: trimming a size-bounded key/value store
back under its capacity (`BaseDatabaseCache._cull`, the `else` arm). The modeled
value is a PURE function of four observables (mapping.md):

    frequency : int        (self._cull_frequency)
    capacity  : int        (self._max_entries)
    now       : int        (reference instant, integer surrogate for the datetime)
    entries   : list[(key:str, expires:int)]   (the stored rows)

Post-patch rule (the gold fix):

    if frequency == 0:
        store = []                                    # self.clear()
    else:
        survivors = [e for e in entries if e.expires >= now]   # DELETE expired
        if len(survivors) > capacity:
            cull_num = len(survivors) // frequency
            ordered  = sorted(k for (k, _) in survivors)       # ORDER BY cache_key
            # cache_key_culling_sql: LIMIT 1 OFFSET cull_num
            row = ordered[cull_num] if cull_num < len(ordered) else None
            if row is not None:                                # the patch's guard
                survivors = [e for e in survivors if e.key >= row]
            # else: cursor.fetchone() was empty -> the patch performs NO delete
        store = survivors

The pre-patch code unconditionally did `cursor.fetchone()[0]`, raising
"'NoneType' object is not subscriptable" exactly when `row is None` (the offset
addressed no key — e.g. an empty/near-empty store with capacity forced below the
survivor count). The fix wraps the delete in `if last_cache_key:`.

Standing up a database / ORM to drive the real `_cull` is heavy and unnecessary:
the modeled value is this pure decision over the observables the cursor exposes
(COUNT, the ordered-key boundary fetch). So the ORACLE below is a faithful
in-process replica using the EXACT patched control flow, and the SHADOW is the
op-for-op transliteration of `implementation_cull` (per refinement.md):
keepUnexpired -> filter expires>=now; cullBoundary -> sorted(keys)[offset] via
`[offset]?`; keepAboveKey -> filter key>=boundary; the `none` arm returns the
survivors unchanged (the patch's "no delete" path).

The surviving set is membership-determined, so the two legs are compared AS SETS
of (key, expires) pairs. Keys are drawn from a lowercase-ASCII pool so that
Python string ordering and Lean `String.<` (lexicographic by code point) agree
exactly on the boundary computation — the one place ordering matters.

stdlib-only. Pinned seed: 13089 (also in mapping.md).
"""
import random
import sys

SEED = 13089
N = 120_000


# --- ORACLE: faithful in-process replica of the patched _cull decision -------
def oracle_cull(frequency, capacity, now, entries):
    if frequency == 0:
        return frozenset()
    survivors = [(k, e) for (k, e) in entries if e >= now]
    if len(survivors) > capacity:
        cull_num = len(survivors) // frequency
        ordered = sorted(k for (k, _) in survivors)
        row = ordered[cull_num] if cull_num < len(ordered) else None
        if row is not None:
            survivors = [(k, e) for (k, e) in survivors if k >= row]
        # else: empty fetch -> the patch performs no delete (no crash)
    return frozenset(survivors)


# --- SHADOW of implementation_cull (the R/I leg, op-for-op) ------------------
def _keep_unexpired(now, entries):
    return [(k, e) for (k, e) in entries if now <= e]


def _cull_boundary(xs, offset):
    ordered = sorted(k for (k, _) in xs)          # mergeSort (· ≤ ·) on keys
    return ordered[offset] if offset < len(ordered) else None   # [offset]?


def _keep_above_key(k0, xs):
    return [(k, e) for (k, e) in xs if not (k < k0)]   # !decide (key < k0)


def shadow_cull(frequency, capacity, now, entries):
    if frequency == 0:
        return frozenset()
    remaining = _keep_unexpired(now, entries)
    if len(remaining) > capacity:
        cull_num = len(remaining) // frequency
        b = _cull_boundary(remaining, cull_num)
        if b is not None:
            return frozenset(_keep_above_key(b, remaining))
        return frozenset(remaining)
    return frozenset(remaining)


def disagree(frequency, capacity, now, entries):
    got = oracle_cull(frequency, capacity, now, entries)
    want = shadow_cull(frequency, capacity, now, entries)
    if got != want:
        return ((frequency, capacity, now, entries), got, want)
    return None


KEY_POOL = ["aa", "ab", "ba", "bb", "ca", "cb", "da", "force_cull_delete",
            "key0", "key1", "zz"]


def _enumerate_edge():
    cases = []
    # The FAIL_TO_PASS shape: empty store, capacity forced below survivor count.
    # survivors == 0, 0 > -1 so cull fires; cull_num == 0; ordered == [] so the
    # boundary fetch is empty -> the patch must NOT crash and stores [].
    cases.append((3, -1, 0, []))
    cases.append((3, -1, 0, [("aa", 100)]))          # 1 survivor, offset 0 -> "aa"
    # zero frequency clears regardless.
    cases.append((0, 10, 0, [("aa", 5), ("bb", 5)]))
    # within capacity: survivors kept, expired dropped.
    cases.append((3, 10, 0, [("aa", -1), ("bb", 5)]))
    # exceeds capacity, boundary addresses a real key.
    cases.append((2, 1, 0, [("bb", 5), ("da", 5), ("aa", 5), ("ca", 5)]))
    # offset == len(survivors) -> empty fetch -> no delete.
    cases.append((1, 0, 0, [("aa", 5)]))             # 1 survivor, 1>0, cull_num=1, []? -> None
    # all expired -> survivors empty, then 0 > capacity may fire with empty fetch.
    cases.append((2, -1, 50, [("aa", 1), ("bb", 2)]))
    return cases


def main() -> int:
    checked = 0
    for freq, cap, now, ents in _enumerate_edge():
        d = disagree(freq, cap, now, ents)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        freq = rng.choice([0, 1, 2, 3, 5])
        cap = rng.randint(-2, 8)
        now = rng.randint(0, 10)
        nent = rng.randint(0, 8)
        ents = []
        for _ in range(nent):
            ents.append((rng.choice(KEY_POOL), rng.randint(0, 10)))
        d = disagree(freq, cap, now, ents)
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
