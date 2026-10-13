#!/usr/bin/env python3
"""G-CONF for django__django-15957.

The modeled function (`restrictPrefetch`) is the prefetch-query restriction that
the gold patch adds (`_filter_prefetch_queryset` in
`django/db/models/fields/related_descriptors.py`). Its impl region is composed of
concrete data-construction ops (R/I tagged in refinement.md): build the
membership predicate; if the query is sliced, append a per-group lower bound from
the offset and (when a limit is set) an upper bound, then drop the offset/limit
bounds.

This check builds the R/I Python shadow of `implementation_restrictPrefetch`
(mirroring Solution.lean's data construction) AND an independent Python shadow of
the GOLD-PATCH behaviour (`_filter_prefetch_queryset`'s predicate/limit
construction, abstracted over the query state), then diffs the two over >=10^5
fuzzed inputs. Exit 0 iff zero disagreements.

stdlib-only. Pinned seed: 15957.
"""
import json
import random
import sys

SEED = 15957
N = 200_000


# ---- Lean R/I shadow (mirrors implementation_restrictPrefetch exactly) -------
def is_sliced(offset, limit):
    # isSliced query = q.offset != 0 || q.limit.isSome
    return offset != 0 or limit is not None


def lean_shadow(ordering, offset, limit, field_name, instances):
    predicate = [("memberOf", field_name, tuple(instances))]
    out_off, out_lim = offset, limit
    if is_sliced(offset, limit):
        r = (field_name, tuple(ordering))
        predicate = predicate + [("positionAbove", r, offset)]
        if limit is not None:
            predicate = predicate + [("positionAtMost", r, limit)]
        out_off, out_lim = 0, None
    return {"predicate": predicate, "offset": out_off, "limit": out_lim}


# ---- Gold-patch behaviour shadow --------------------------------------------
# Mirrors `_filter_prefetch_queryset`:
#   predicate = Q(field__in=instances)
#   if query.is_sliced:
#       low, high = low_mark, high_mark
#       order_by = [...]                      # the group ordering
#       window = Window(RowNumber(), partition_by=field, order_by=order_by)
#       predicate &= GreaterThan(window, low_mark)
#       if high_mark is not None:
#           predicate &= LessThanOrEqual(window, high_mark)
#       query.clear_limits()                  # low_mark, high_mark = 0, None
#   return queryset.filter(predicate)
#
# Bridging (mapping.md):
#   low_mark  <-> query.offset            (rows skipped)
#   high_mark <-> query.limit             (final position; None == no upper bound)
#   is_sliced <-> low_mark != 0 or high_mark is not None
#   Window(RowNumber(), partition_by=field, order_by=order_by)  <-> Ranking(field, ordering)
#   GreaterThan(window, low_mark)         <-> positionAbove(r, offset)
#   LessThanOrEqual(window, high_mark)    <-> positionAtMost(r, high)
def gold_shadow(ordering, low_mark, high_mark, field_name, instances):
    predicate = [("memberOf", field_name, tuple(instances))]
    out_low, out_high = low_mark, high_mark
    sliced = (low_mark != 0) or (high_mark is not None)
    if sliced:
        window = (field_name, tuple(ordering))   # partition_by=field, order_by=ordering
        predicate = predicate + [("positionAbove", window, low_mark)]
        if high_mark is not None:
            predicate = predicate + [("positionAtMost", window, high_mark)]
        out_low, out_high = 0, None               # clear_limits()
    return {"predicate": predicate, "offset": out_low, "limit": out_high}


def gen(rng):
    nord = rng.randint(0, 3)
    ordering = [rng.choice(["pk", "-name", "title", "-published"]) for _ in range(nord)]
    offset = rng.choice([0, 0, 1, 2, 3, 5, 10, rng.randint(0, 1000)])
    limit = rng.choice([None, None, 1, 2, 3, offset + 1, rng.randint(0, 1000)])
    field = rng.choice(["author", "book", "category", "first_time_authors"])
    k = rng.randint(0, 4)
    instances = [rng.randint(1, 50) for _ in range(k)]
    return ordering, offset, limit, field, instances


def edge_cases():
    cases = []
    for ordering in ([], ["pk"], ["-name", "title"]):
        for offset, limit in [(0, None), (0, 3), (1, None), (1, 2), (5, 5), (2, 0)]:
            cases.append((ordering, offset, limit, "author", [1, 2, 3]))
    return cases


def main():
    rng = random.Random(SEED)
    checked = 0
    cases = edge_cases() + [gen(rng) for _ in range(N)]
    for ordering, offset, limit, field, instances in cases:
        a = lean_shadow(ordering, offset, limit, field, instances)
        b = gold_shadow(ordering, offset, limit, field, instances)
        if a != b:
            print(json.dumps({
                "status": "fail",
                "input": {"ordering": ordering, "offset": offset, "limit": limit,
                          "field": field, "instances": instances},
                "lean": str(a), "gold": str(b),
            }))
            return 1
        checked += 1
    print(json.dumps({"status": "pass", "checked": checked, "mismatches": 0,
                      "seed": SEED}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
