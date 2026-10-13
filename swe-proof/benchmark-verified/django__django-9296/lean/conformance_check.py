#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-9296.

The bundle models ONE behavior: walking a paginated collection page by page, in
order, surfacing each page's slice of items. Its Lean implementation
(`implementation_paginatorPages`) builds, for every 1-based page number, the
contiguous slice of items shown on that page:

    pages = []
    for n in page_numbers(count, per_page, orphans, allow_empty):   # [1..num_pages]
        pages.append(page_slice(object_list, per_page, orphans, n))
    return pages

This script transliterates that R/I impl into Python (`shadow_pages`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH paginator. The patch adds

    def __iter__(self):
        for page_number in self.page_range:
            yield self.page(page_number)

so the observed sequence is `[paginator.page(n).object_list for n in
paginator.page_range]`. The oracle reproduces the real (unchanged) `num_pages`,
`page_range`, and `page(n)` callees over plain Python lists — exactly the
behavior `test_paginator_iteration` observes via `list(next(page_iterator))`.

We do NOT stand up Django: the modeled value is a pure function of
`(object_list, per_page, orphans, allow_empty_first_page)`, and the only field
the F2P test reads off a yielded `Page` is its `object_list` slice. So the
oracle reimplements the paginator arithmetic directly (mapping.md).

The differential genuinely tests the Lean modeling: the shadow uses the Lean
`pageCount` / `pageNumbers` / `pageSlice` helpers (Nat truncated subtraction,
`(h + p - 1) // p` ceiling, `drop`/`take` slice), whereas the oracle reproduces
the real `num_pages` (`ceil(max(1, count-orphans)/per_page)`), `page_range`
(`range(1, num_pages+1)`), and `page(n)` (`object_list[bottom:top]` with the
orphan extension) callees.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 9296 (also recorded in
mapping.md). per_page >= 1 (the real `num_pages` divides by it); orphans >= 0.
"""
import sys
from math import ceil

SEED = 9296
N = 120_000


# --- ORACLE: the post-patch paginator, faithful in-process replica -----------
# Reproduces the real (unchanged) num_pages / page_range / page(n) callees that
# the added __iter__ drives, over a plain Python list `object_list`.
def oracle_num_pages(count, per_page, orphans, allow_empty):
    if count == 0 and not allow_empty:
        return 0
    hits = max(1, count - orphans)
    return ceil(hits / per_page)


def oracle_page_slice(object_list, per_page, orphans, n):
    count = len(object_list)
    bottom = (n - 1) * per_page
    top = bottom + per_page
    if top + orphans >= count:
        top = count
    return object_list[bottom:top]


def oracle_pages(object_list, per_page, orphans, allow_empty):
    count = len(object_list)
    num_pages = oracle_num_pages(count, per_page, orphans, allow_empty)
    page_range = range(1, num_pages + 1)                 # paginator.page_range
    return [oracle_page_slice(object_list, per_page, orphans, n)
            for n in page_range]


# --- shadow of implementation_paginatorPages (the R/I leg) --------------------
# Mirrors Solution.lean's pageCount / pageNumbers / pageSlice exactly, using
# Nat-style truncated subtraction and the floor-division ceiling.
def shadow_page_count(count, per_page, orphans, allow_empty):
    if count == 0 and not allow_empty:
        return 0
    h = max(1, count - orphans)                          # max 1 (count - orphans)
    return (h + per_page - 1) // per_page                # ceil for per_page >= 1


def shadow_page_slice(object_list, per_page, orphans, n):
    count = len(object_list)
    bottom = (n - 1) * per_page
    top = bottom + per_page
    if top + orphans >= count:
        top = count
    width = top - bottom if top >= bottom else 0         # Nat truncated subtraction
    return object_list[bottom:bottom + width]            # (drop bottom).take width


def shadow_pages(object_list, per_page, orphans, allow_empty):
    count = len(object_list)
    pages = []
    for n in range(1, shadow_page_count(count, per_page, orphans, allow_empty) + 1):
        pages.append(shadow_page_slice(object_list, per_page, orphans, n))
    return pages


def disagree(object_list, per_page, orphans, allow_empty):
    got = oracle_pages(object_list, per_page, orphans, allow_empty)
    want = shadow_pages(object_list, per_page, orphans, allow_empty)
    if got != want:
        return ((object_list, per_page, orphans, allow_empty), got, want)
    return None


# --- input corpus -------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked edge cases pinning page-count / orphan / slice boundaries."""
    cases = [
        # the F2P test itself: [1,2,3] per_page=2 -> [[1,2],[3]]
        ([1, 2, 3], 2, 0, True),
        # empty list, allow_empty True -> one empty page
        ([], 2, 0, True),
        # empty list, allow_empty False -> zero pages
        ([], 2, 0, False),
        # exact multiple -> no partial last page
        ([1, 2, 3, 4], 2, 0, True),
        # orphans absorbs the trailing partial page into the last full page
        ([1, 2, 3, 4, 5], 2, 1, True),     # 5 items, orphans=1 -> last page absorbs
        ([1, 2, 3, 4, 5], 2, 3, True),     # orphans >= remainder
        # single item
        ([7], 1, 0, True),
        # per_page larger than the collection -> single page
        ([1, 2], 10, 0, True),
        # orphans larger than per_page
        ([1, 2, 3, 4, 5, 6, 7], 3, 5, True),
        # count - orphans negative-clamped (orphans > count) -> max(1, .)
        ([1, 2], 2, 10, True),
        ([1, 2], 2, 10, False),
    ]
    return cases


def _rand_list(rnd):
    k = next(rnd) % 12                       # length 0..11
    return [next(rnd) % 100 for _ in range(k)]


def main() -> int:
    checked = 0

    for ol, pp, orph, ae in _enumerate_edge():
        d = disagree(ol, pp, orph, ae)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        ol = _rand_list(rnd)
        per_page = (next(rnd) % 6) + 1       # 1..6 (>= 1)
        orphans = next(rnd) % 6              # 0..5 (biased near per_page boundary)
        allow_empty = (next(rnd) % 2 == 0)
        d = disagree(ol, per_page, orphans, allow_empty)
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
