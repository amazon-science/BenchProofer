#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15554 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`eligibleEntries`
              / `entryEligible`) transliterated to Python over the *real* repo
              shapes, via the mapping.md §2 bijection (alias dict -> ordered list,
              opaque identities -> Nats, `reuse` -> Option list, the flag ->
              bool). There are NO A-tagged callees in the impl, so the shadow is
              pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the POST-PATCH `reuse_aliases`
              comprehension of `Query.join`, transcribed VERBATIM and evaluated
              over REAL `Join` objects, so the `j.equals(join)` / `j == join`
              comparisons are the genuine repository methods (not the model).

They must agree on every input. The output compared is the ordered list of
eligible aliases — exactly what `reuse_aliases` is before the unchanged
downstream `[-1]`/`table_alias` selection (refinement.md §B, tagged I) consumes
it. Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), django + stdlib only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import itertools
import random
import sys

from django.db.models.sql.datastructures import Join
from django.db.models.query_utils import FilteredRelation, Q

SEED = 15554
N_FUZZ = 100_000


# --- a minimal join_field (identity-compared), as in axiom_check.py ----------
class FakeField:
    def __init__(self, tag):
        self.tag = tag

    def get_joining_columns(self):
        return ()


def make_join(table_name, parent_alias, field, fr):
    return Join(
        table_name=table_name,
        parent_alias=parent_alias,
        table_alias="ta",
        join_type=None,
        join_field=field,
        nullable=False,
        filtered_relation=fr,
    )


# --- ORACLE: post-patch reuse_aliases comprehension, verbatim ----------------
def oracle_reuse_aliases(alias_map, join, reuse, reuse_with_filtered_relation):
    """Transcribed VERBATIM from the gold-patched Query.join (query.py:1027):

        if reuse_with_filtered_relation and reuse:
            reuse_aliases = [
                a for a, j in self.alias_map.items()
                if a in reuse and j.equals(join)
            ]
        else:
            reuse_aliases = [
                a for a, j in self.alias_map.items()
                if (reuse is None or a in reuse) and j == join
            ]

    `alias_map` is an ordered dict {alias: Join}; comparisons are the real
    Join.equals / Join.__eq__."""
    if reuse_with_filtered_relation and reuse:
        return [a for a, j in alias_map.items() if a in reuse and j.equals(join)]
    else:
        return [
            a for a, j in alias_map.items()
            if (reuse is None or a in reuse) and j == join
        ]


# --- SHADOW: Solution.lean eligibleEntries / entryEligible, transliterated ---
def model_struct_exact_keys(j, struct_ids, fr_reps):
    """Map a real Join to its (structKey, refineTag) Nats per mapping.md §2."""
    skey = (j.table_name, j.parent_alias, id(j.join_field))
    sk = struct_ids.setdefault(skey, len(struct_ids) + 1)
    fr = j.filtered_relation
    if fr is None:
        rt = 0
    else:
        rt = None
        for rep, rid in fr_reps:
            if rep == fr:
                rt = rid
                break
        if rt is None:
            rt = len(fr_reps) + 1
            fr_reps.append((fr, rt))
    return sk, rt


def shadow_eligible(registry, req, allowed, restricted):
    """eligibleEntries req allowed restricted registry, transliterated.

    registry : list[(alias, (structKey, refineTag))]; req : (structKey, refineTag)
    allowed  : None | list[alias]; restricted : bool."""
    req_sk, req_rt = req

    def restricted_mode():
        return restricted and (allowed is not None and len(allowed) > 0)

    def allowed_member(a):
        return allowed is not None and a in allowed

    def entry_eligible(a, ident):
        sk, rt = ident
        if restricted_mode():
            return allowed_member(a) and (sk == req_sk)              # matchesStructural
        else:
            return (allowed is None or allowed_member(a)) and (sk == req_sk and rt == req_rt)  # matchesExact

    return [a for a, ident in registry if entry_eligible(a, ident)]


def fuzz_cases(n, rng):
    table_names = ["t_book", "t_author", "t_publisher"]
    parents = ["A", "B", "C"]
    fields = [FakeField(i) for i in range(3)]
    frs = [
        None,
        FilteredRelation("book", condition=Q(book__title__contains="Alice")),
        FilteredRelation("book", condition=Q(book__title__icontains="Jane")),
        FilteredRelation("book", condition=Q(book__title__contains="Alice")),  # == frs[1]
        FilteredRelation("author", condition=Q(author__name="x")),
    ]
    components = list(itertools.product(table_names, parents, fields, frs))

    # The motivating boundary case (the issue / F2P test_multiple): two entries
    # that are structurally identical (same table/parent/field) but carry
    # different filtered_relations. The bug shared the first for both; the fix
    # keeps them distinct.
    fld = fields[0]
    fr_alice, fr_jane = frs[1], frs[2]
    yield (
        [("a0", make_join("t_book", "A", fld, fr_alice)),
         ("a1", make_join("t_book", "A", fld, fr_jane))],
        make_join("t_book", "A", fld, fr_jane),   # request the Jane-tagged one
        {"a0", "a1"}, True,
    )
    yield (
        [("a0", make_join("t_book", "A", fld, fr_alice)),
         ("a1", make_join("t_book", "A", fld, fr_jane))],
        make_join("t_book", "A", fld, fr_jane),
        None, False,
    )

    aliases = ["a0", "a1", "a2", "a3", "a4"]
    for _ in range(n):
        size = rng.randint(0, 5)
        registry = []
        used = aliases[:size]
        for a in used:
            comp = rng.choice(components)
            registry.append((a, make_join(*comp)))
        req = make_join(*rng.choice(components))
        # reuse: None, empty set, or a random subset of the used aliases
        choice = rng.randint(0, 2)
        if choice == 0:
            reuse = None
        elif choice == 1:
            reuse = set()
        else:
            reuse = set(a for a in used if rng.random() < 0.5)
        restricted = rng.random() < 0.5
        yield registry, req, reuse, restricted


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for registry, req_join, reuse, restricted in fuzz_cases(N_FUZZ, rng):
        count += 1
        alias_map = dict(registry)

        # ORACLE over real Join objects
        oracle = oracle_reuse_aliases(alias_map, req_join, reuse, restricted)

        # SHADOW: map the same real objects through the §2 bijection, then run
        # the transliterated model. Shared struct/refine id tables so identical
        # identities map to identical Nats across the registry and the request.
        struct_ids, fr_reps = {}, []
        model_registry = [
            (a, model_struct_exact_keys(j, struct_ids, fr_reps))
            for a, j in registry
        ]
        req_id = model_struct_exact_keys(req_join, struct_ids, fr_reps)
        allowed = None if reuse is None else list(reuse)
        shadow = shadow_eligible(model_registry, req_id, allowed, restricted)

        if shadow != oracle:
            disagreements.append((registry, reuse, restricted, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for reg, reuse, restr, sh, orc in disagreements:
            print("  registry=%r reuse=%r restricted=%r shadow=%r oracle=%r"
                  % ([(a, (j.table_name, j.parent_alias, j.filtered_relation))
                      for a, j in reg], reuse, restr, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of computeEligible agrees with patch.diff "
          "behaviour (post-patch reuse_aliases over real Join objects) on %d "
          "inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
