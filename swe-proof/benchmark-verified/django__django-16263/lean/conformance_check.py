#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-16263.

The bundle models ONE decision: the count/aggregate query-planning logic inside
`Query.get_aggregation` (`django/db/models/sql/query.py`). Its Lean
implementation (`implementation_countPlan`) decides, from the named clauses a
query already carries:

  * `useSubquery`  — whether the count must be wrapped in a subquery, and
  * `keptExisting` — which already-present clause aliases survive into the
    emitted query.

This script transliterates that R/I implementation into Python (`shadow_plan`)
and differential-tests it against the ORACLE: a faithful in-process replica of
the POST-PATCH behavior of `get_aggregation`'s decision:

    existing = [ a for a in anns if (not a.added) and a.selected ]
    has_existing_aggregation =
        any(a.contains_aggregate or a.contains_over_clause for a in existing)
        or post_group_filter
    use_subquery = group_by_tuple or is_sliced or has_existing_aggregation
                   or distinct or combinator
    if use_subquery:
        if distinct:
            # the ref-based re-masking lives inside `if not inner_query.distinct:`
            # and is SKIPPED: the inner mask stays at annotation_select, so every
            # materialised existing clause survives.
            kept = [ a.alias for a in existing ]
        else:
            added_mask = ⋃ { name } ∪ refs   over the added aggregates
            kept = [ a.alias for a in anns if (not a.added) and a.alias in added_mask ]
    else:
        kept = []

We do NOT stand up Django's ORM/SQL compiler (heavy; the modeled value is a pure
decision over the per-clause flags, the added aggregates' reference sets, and a
handful of query-level booleans). Both legs are total functions over the modeled
abstraction, so the edge set EXHAUSTIVELY enumerates a small structured space
(presence/absence of each flag combination across 0-3 carried clauses with a
small alias alphabet and reference choices); the fuzz loop then samples >=1e5
random points. The three FAIL_TO_PASS scenarios are covered exhaustively:

  - aliased Count (selected=False, aggregate)        -> use_subquery=False, kept=[]
  - selected non-aggregate (Lower)                   -> use_subquery=False, kept=[]
  - selected unreferenced aggregate (Count)          -> use_subquery=True,  kept=[]
  - selected aggregate referenced by added Avg       -> use_subquery=True,  kept=[that alias]

stdlib-only. Pinned seed: 16263 (also recorded in mapping.md).
"""
import itertools
import random
import sys

SEED = 16263
N = 120_000

ALIASES = ("a", "b", "c", "__count", "avg")


# ---------------------------------------------------------------------------
# ORACLE: faithful in-process replica of the POST-PATCH get_aggregation decision
# ---------------------------------------------------------------------------
def oracle_plan(st):
    anns = st["anns"]
    existing = [a for a in anns if (not a["added"]) and a["selected"]]
    has_existing_aggregation = any(
        a["containsAggregate"] or a["containsOverClause"] for a in existing
    ) or st["postGroupFilter"]
    use_subquery = (
        st["groupByTuple"]
        or st["isSliced"]
        or has_existing_aggregation
        or st["distinct"]
        or st["combinator"]
    )
    if use_subquery:
        if st["distinct"]:
            # The ref-based re-masking block lives inside
            # `if not inner_query.distinct:` and is SKIPPED for distinct
            # queries: the inner mask stays at annotation_select, so every
            # materialised existing clause survives (verified against the
            # patched worktree: LOWER(...) AS "name_lower" stays in the inner
            # SELECT of a .distinct().count()).
            kept = [a["aliasName"] for a in anns
                    if (not a["added"]) and a["selected"]]
            return {"useSubquery": True, "keptExisting": kept}
        # set_annotation_mask(added names | their get_refs()): the surviving mask
        # is rebuilt purely from the summary aggregates' references, so a
        # referenced carried clause is kept whether or not it was materialised.
        mask = set()
        for a in anns:
            if a["added"]:
                mask.add(a["aliasName"])
                mask.update(a["refs"])
        kept = [a["aliasName"] for a in anns
                if (not a["added"]) and a["aliasName"] in mask]
        return {"useSubquery": True, "keptExisting": kept}
    return {"useSubquery": False, "keptExisting": []}


# ---------------------------------------------------------------------------
# SHADOW of implementation_countPlan (the R/I leg) — line-for-line skeleton.
# ---------------------------------------------------------------------------
def shadow_plan(st):
    anns = st["anns"]
    existing = [a for a in anns if (not a["added"]) and a["selected"]]
    has_agg = False
    for a in existing:
        if a["containsAggregate"] or a["containsOverClause"]:
            has_agg = True
    needs_sub = (
        st["groupByTuple"]
        or st["isSliced"]
        or (has_agg or st["postGroupFilter"])
        or st["distinct"]
        or st["combinator"]
    )
    if needs_sub:
        mask = []  # List String, built by append (mirrors the `for` loop)
        for a in anns:
            if a["added"]:
                mask = mask + [a["aliasName"]] + list(a["refs"])
        if st["distinct"]:
            kept = [a["aliasName"] for a in existing]
        else:
            kept = [a["aliasName"] for a in anns
                    if (not a["added"]) and a["aliasName"] in mask]
        return {"useSubquery": True, "keptExisting": kept}
    return {"useSubquery": False, "keptExisting": []}


def compare(st):
    o = oracle_plan(st)
    s = shadow_plan(st)
    # keptExisting order: both legs iterate `existing` in list order, so equal.
    return o == s


# ---------------------------------------------------------------------------
# input generators
# ---------------------------------------------------------------------------
def make_ann(alias, selected, agg, over, added, refs):
    return {
        "aliasName": alias,
        "selected": selected,
        "containsAggregate": agg,
        "containsOverClause": over,
        "added": added,
        "refs": list(refs),
    }


def exhaustive_states():
    """Small but exhaustive structured enumeration: 0-2 carried clauses + 1
    added aggregate, over the boolean flag combinations and a tiny alias/ref
    alphabet. Covers all FAIL_TO_PASS scenarios."""
    bools = (False, True)
    qflags = list(itertools.product(bools, repeat=5))  # group/sliced/distinct/comb/postFilter
    clause_alias = ("a", "b")
    ref_choices = ([], ["a"], ["b"], ["a", "b"])
    # carried clauses: 0, 1, or 2 with varying (selected, agg, over)
    clause_variants = list(itertools.product(bools, bools, bools))
    carried_sets = [[]]
    for v in clause_variants:
        carried_sets.append([("a",) + v])
    for v1 in clause_variants:
        for v2 in clause_variants:
            carried_sets.append([("a",) + v1, ("b",) + v2])

    for gf, isl, dist, comb, pgf in qflags:
        for carried in carried_sets:
            for added_refs in ref_choices:
                anns = [
                    make_ann(al, sel, agg, ov, False, [])
                    for (al, sel, agg, ov) in carried
                ]
                anns.append(make_ann("__count", True, True, False, True, added_refs))
                yield {
                    "anns": anns,
                    "groupByTuple": gf,
                    "isSliced": isl,
                    "distinct": dist,
                    "combinator": comb,
                    "postGroupFilter": pgf,
                }


def random_state(rng):
    k = rng.randint(0, 3)
    anns = []
    used = set()
    for _ in range(k):
        al = rng.choice(ALIASES)
        anns.append(
            make_ann(
                al,
                rng.random() < 0.6,
                rng.random() < 0.5,
                rng.random() < 0.3,
                False,
                rng.sample(ALIASES, rng.randint(0, 2)),
            )
        )
        used.add(al)
    # 1-2 added aggregates
    for _ in range(rng.randint(1, 2)):
        anns.append(
            make_ann(
                rng.choice(("__count", "avg")),
                True,
                rng.random() < 0.8,
                rng.random() < 0.2,
                True,
                rng.sample(ALIASES, rng.randint(0, 3)),
            )
        )
    return {
        "anns": anns,
        "groupByTuple": rng.random() < 0.3,
        "isSliced": rng.random() < 0.3,
        "distinct": rng.random() < 0.3,
        "combinator": rng.random() < 0.2,
        "postGroupFilter": rng.random() < 0.3,
    }


def f2p_scenarios():
    """The three FAIL_TO_PASS observations + one referenced-kept control."""
    base = dict(groupByTuple=False, isSliced=False, distinct=False,
                combinator=False, postGroupFilter=False)
    yield ("unused_aliased_aggregate_pruned",
           {"anns": [make_ann("authors_count", False, True, False, False, []),
                     make_ann("__count", True, True, False, True, [])], **base},
           {"useSubquery": False, "keptExisting": []})
    yield ("non_aggregate_annotation_pruned",
           {"anns": [make_ann("name_lower", True, False, False, False, []),
                     make_ann("__count", True, True, False, True, [])], **base},
           {"useSubquery": False, "keptExisting": []})
    yield ("unreferenced_aggregate_annotation_pruned",
           {"anns": [make_ann("authors_count", True, True, False, False, []),
                     make_ann("__count", True, True, False, True, [])], **base},
           {"useSubquery": True, "keptExisting": []})
    yield ("referenced_aggregate_annotation_kept",
           {"anns": [make_ann("authors_count", True, True, False, False, []),
                     make_ann("avg", True, True, False, True, ["authors_count"])], **base},
           {"useSubquery": True, "keptExisting": ["authors_count"]})
    # G-PANEL-2 divergence witness (2026-08): distinct=True skips the ref-based
    # re-masking (`if not inner_query.distinct:`), so a selected non-aggregate
    # annotation SURVIVES in the inner query even though nothing references it.
    yield ("distinct_selected_nonagg_kept",
           {"anns": [make_ann("name_lower", True, False, False, False, []),
                     make_ann("total", True, True, False, True, [])],
            **{**base, "distinct": True}},
           {"useSubquery": True, "keptExisting": ["name_lower"]})


def main():
    checks = 0
    # 1) pin the F2P scenarios against the spec's expected values
    for name, st, expected in f2p_scenarios():
        got = oracle_plan(st)
        if got != expected:
            print(f"status=fail F2P oracle mismatch [{name}]: {got} != {expected}")
            sys.exit(1)
        if not compare(st):
            print(f"status=fail shadow!=oracle on F2P [{name}]")
            sys.exit(1)
        checks += 1

    # 2) exhaustive structured enumeration
    for st in exhaustive_states():
        if not compare(st):
            print(f"status=fail disagreement (exhaustive): {st}")
            sys.exit(1)
        checks += 1

    # 3) fuzz
    rng = random.Random(SEED)
    while checks < N:
        st = random_state(rng)
        if not compare(st):
            print(f"status=fail disagreement (fuzz): {st}")
            sys.exit(1)
        checks += 1

    print(f"status=pass conformance OK ({checks} checks, 0 disagreements)")
    sys.exit(0)


if __name__ == "__main__":
    main()
