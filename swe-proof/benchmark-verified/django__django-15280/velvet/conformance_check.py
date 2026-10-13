#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15280 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python: `resolveOne`/`resolvedSeq` over the mapping.md bridge
              (a child row ↔ a `Child`; `is_cached` ↔ `existingParent : Option`;
              `instances_dict[key]` ↔ `lookup key`). There are NO A-tagged
              callees in this bundle (refinement.md §B), so the shadow is pure
              R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched reverse-relation linking
              loop of `get_prefetch_queryset`, run verbatim against stand-in
              objects that faithfully model the Django field cache semantics
              (`is_cached` = "the reverse relation is already populated on this
              child", `setattr(rel_obj, field.name, instance)` = "populate it",
              `instances_dict[rel_obj_attr(rel_obj)]` = the grouping-key lookup).
              The three loop-body lines are quoted from patch.diff verbatim; only
              the surrounding object model is a DB-free stand-in.

They must agree on the observable the F2P test checks — which parent each child
ends up associated with, in batch order — on every input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 15280
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean resolveOne / resolvedSeq, transliterated ---
# A `Child` is (key, existingParent) where existingParent is None (Lean `none`)
# or an int parent-id (Lean `some p`). `lookup` is a dict modelling the free
# function `lookup : Nat -> Nat`.
def shadow_resolve(children, lookup):
    """resolvedSeq lookup children, transliterated: a child carrying a parent
    keeps it; one carrying none is looked up by its key. (Solution.lean
    `resolveOne`: match existingParent with some p => p | none => lookup key.)"""
    out = []
    for key, existing_parent in children:
        if existing_parent is not None:        # Lean `some p => p`
            out.append(existing_parent)
        else:                                  # Lean `none => lookup key`
            out.append(lookup[key])
    return out


# --- the oracle: patch.diff's patched loop, run against stand-in objects ------
class _Field:
    """Stand-in for `self.field`. `is_cached(obj)` and `setattr`/read of the
    reverse relation model django.db.models.fields.mixins.FieldCacheMixin:
    is_cached <=> the relation name is present in the child's field cache."""
    name = "parent"

    @staticmethod
    def is_cached(rel_obj):
        return _Field.name in rel_obj.cache


class _RelObj:
    """Stand-in for a prefetched child row. `key` is rel_obj_attr(rel_obj); the
    cache dict holds the reverse relation once populated."""
    def __init__(self, key, existing_parent):
        self.key = key
        self.cache = {}
        if existing_parent is not None:
            # the nested prefetch already populated the reverse relation
            self.cache[_Field.name] = existing_parent


def oracle_resolve(children, lookup):
    """patch.diff behaviour: build the prefetch loop's inputs, run the PATCHED
    loop body verbatim, then read each child's resulting reverse relation."""
    field = _Field()
    queryset = [_RelObj(key, ep) for (key, ep) in children]
    instances_dict = dict(lookup)                      # {key: parent}

    def rel_obj_attr(rel_obj):                          # self.field.get_local_related_value
        return rel_obj.key

    # ---- patch.diff verbatim (related_descriptors.py:645-648, post-patch) ----
    for rel_obj in queryset:
        if not field.is_cached(rel_obj):
            instance = instances_dict[rel_obj_attr(rel_obj)]
            setattr_relation(rel_obj, field.name, instance)
    # --------------------------------------------------------------------------

    # observable: the reverse relation each child points at, in batch order
    return [rel_obj.cache[field.name] for rel_obj in queryset]


def setattr_relation(rel_obj, name, instance):
    """setattr(rel_obj, self.field.name, instance): populate the reverse relation
    into the child's field cache (FieldCacheMixin.set_cached_value semantics)."""
    rel_obj.cache[name] = instance


def fuzz_inputs(n, rng):
    """Yield (children, lookup) batches. `children` is a list of
    (key, existing_parent|None); `lookup` is a {key: parent} dict total over the
    keys that have no existing parent."""
    # boundary cases first (plan §4.1 step 4)
    yield ([], {})                                          # empty batch
    yield ([(0, None)], {0: 100})                           # single, uncached
    yield ([(0, 7)], {0: 100})                              # single, cached (the bug case)
    yield ([(0, 100)], {0: 100})                            # cached == lookup (must still keep)
    yield ([(0, None), (1, None)], {0: 10, 1: 11})          # all uncached
    yield ([(0, 5), (1, 6)], {0: 10, 1: 11})                # all cached, both differ from lookup
    yield ([(0, 5), (1, None), (2, 8)], {0: 10, 1: 11, 2: 12})  # mixed
    yield ([(0, None), (0, 9)], {0: 10})                    # same key, one cached one not
    yield ([(3, 0)], {3: 99})                               # cached parent id 0 (falsy but present)

    for _ in range(n):
        m = rng.randint(0, 8)
        keys = [rng.randint(0, 6) for _ in range(m)]
        lookup = {k: rng.randint(0, 1000) for k in keys}
        children = []
        for k in keys:
            if rng.random() < 0.5:
                # carries a pre-existing parent (sometimes equal to the lookup,
                # sometimes not, sometimes 0/falsy)
                children.append((k, rng.randint(0, 1000)))
            else:
                children.append((k, None))
        yield (children, lookup)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for children, lookup in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_resolve(children, lookup)
        oracle = oracle_resolve(children, lookup)
        if shadow != oracle:
            disagreements.append((children, lookup, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for ch, lk, sh, orc in disagreements:
            print("  children=%r lookup=%r shadow=%r oracle=%r" % (ch, lk, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of linkChildrenToParents agrees with patch.diff "
          "behaviour (the patched get_prefetch_queryset linking loop) on %d "
          "inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
