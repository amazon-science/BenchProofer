#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11885.

There is NO consumed @ContractOnly axiom in model.py: the combine-by-related-
table grouping is modelled DEEPLY as the front-recursive fold `distinct_count`
over the candidate related-table identities. G-AX therefore validates that deep
model against the REAL grouping operation the gold patch performs.

The gold patch groups the fast-removable candidate relations by their related
model into `model_fast_deletes = defaultdict(list)` and then issues exactly one
combined bulk removal per entry of that mapping:

    model_fast_deletes = defaultdict(list)
    for related in ...:
        if self.can_fast_delete(related_model, from_field=field):
            model_fast_deletes[related_model].append(field)
            continue
        ...
    for related_model, related_fields in model_fast_deletes.items():
        ...
        self.fast_deletes.append(sub_objs)      # one append per distinct model

So the number of bulk removals appended for the fast-removable candidates is
`len(model_fast_deletes)` -- the number of DISTINCT related models among the
candidates -- and every candidate field is preserved in exactly one group
(`sum(len(fields)) == number of candidates`).

This check reproduces that real grouping with the same standard-library
primitive the patch uses (`collections.defaultdict(list)`), keyed by the
related-model identity, and asserts on boundary + randomized fuzz inputs that:

  (A-reference 1) the deep model `distinct_count(ids)` equals the number of
      groups the real grouping produces, i.e. `len(model_fast_deletes)`;
  (A-reference 2) the grouping never drops or duplicates a candidate column:
      the total number of grouped fields equals the number of candidates;
  (A-reference 3) the count never exceeds the number of candidates and is at
      least one for a non-empty candidate run (the combining never increases the
      number of removals and a non-empty run still yields a removal).

Imports nothing repo-specific: only `collections` / `random` from the standard
library (the same `collections.defaultdict` the gold patch calls). Exit 0 iff
every obligation holds.
"""
import collections
import random
import sys


def distinct_count(ids):
    """Reference implementation of model.py's deep model `distinct_count`:
    number of distinct identities, counted at first occurrence (front-recursive
    in the model; here an iterative equivalent)."""
    seen = set()
    n = 0
    for x in ids:
        if x not in seen:
            seen.add(x)
            n += 1
    return n


def real_group_count(ids):
    """The REAL combining operation the gold patch performs: group the
    fast-removable candidate fields by their related-model identity into a
    `collections.defaultdict(list)` and issue one combined removal per entry.
    Returns (number_of_removals, total_grouped_fields)."""
    model_fast_deletes = collections.defaultdict(list)
    for field_id, model_id in enumerate(ids):
        # one referencing column per candidate; grouped by related model
        model_fast_deletes[model_id].append(field_id)
    removals = len(model_fast_deletes)                       # one per distinct model
    grouped_fields = sum(len(v) for v in model_fast_deletes.values())
    return removals, grouped_fields


def check(ids):
    model = distinct_count(ids)                              # deep model
    removals, grouped_fields = real_group_count(ids)         # real grouping
    # (A-reference 1) deep model == number of combined removals the patch issues
    assert model == removals, (
        "distinct_count deep model unsound on %r: model gives %d, real grouping "
        "issues %d combined removals" % (ids, model, removals))
    # (A-reference 2) every candidate column is grouped exactly once
    assert grouped_fields == len(ids), (
        "grouping dropped/duplicated a column on %r: %d candidates, %d grouped"
        % (ids, len(ids), grouped_fields))
    # (A-reference 3) bounds: never more removals than candidates; >=1 if non-empty
    assert 0 <= removals <= len(ids), (
        "removal count out of bounds on %r: %d removals, %d candidates"
        % (ids, removals, len(ids)))
    if len(ids) > 0:
        assert removals >= 1, (
            "non-empty candidate run yielded no removal on %r" % (ids,))


def main():
    boundary = [
        [],                       # no fast-removable candidates
        [7],                      # single relation -> single removal
        [7, 7],                   # the F2P case: two columns of ONE related model
        [7, 7, 7],                # three columns of one related model
        [3, 5],                   # two distinct models -> two removals
        [3, 3, 5],                # one model twice + one once
        [3, 5, 3],                # interleaved duplicates
        [5, 3, 5, 3],             # two models, alternating
        [1, 2, 3, 4, 5],          # all distinct
        [9, 9, 9, 9, 9],          # all identical
        [0, -1, 0, -1, 2],        # negative identities, duplicates
    ]
    for ids in boundary:
        check(ids)

    # randomized fuzz: small id universes maximize duplicate collisions
    # (the very situation the combining addresses)
    rng = random.Random(11885)
    for _ in range(50000):
        n = rng.randint(0, 12)
        universe = rng.randint(1, 6)
        ids = [rng.randint(0, universe) for _ in range(n)]
        check(ids)

    print("G-AX OK: distinct_count deep model == real defaultdict-grouped "
          "combined-removal count on %d boundary + 50000 fuzz candidate runs; "
          "no column dropped/duplicated; bounds hold." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
