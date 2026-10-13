#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
implementation_requiresSubqueryWrap against the patch.diff behaviour
(post-patch subquery-wrapping decision in Query.get_aggregation).

The impl region is all R/I (no A-tagged op), so this runs a real fuzz. The shadow
reproduces the impl op-for-op: OR-accumulate `refs_subquery` and `refs_window`
over every requested aggregate's referenced annotations, then OR both into the
pre-existing-conditions disjunct. We diff that against an independent
reconstruction of the post-patch decision built directly from the patched source
lines (`refs_subquery |= any(... "subquery", False ...)`,
`refs_window |= any(... "contains_over_clause", True ...)`, and the final
`if (... or refs_subquery or refs_window or ...)`).

Zero disagreements required over >=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 17084          # pinned in mapping.md
N = 120_000           # >= 10^5


def shadow(aggregates, other_conditions):
    """R/I shadow of implementation_requiresSubqueryWrap.

    aggregates: list of aggregates, each a list of references; a reference is a
    dict {"subquery": bool, "over": bool} mirroring the two attribute reads.
    """
    refs_subquery = False
    refs_window = False
    for refs in aggregates:
        refs_subquery = refs_subquery or any(r["subquery"] for r in refs)
        refs_window = refs_window or any(r["over"] for r in refs)
    return other_conditions or refs_subquery or refs_window


def patched_decision(aggregates, other_conditions):
    """Independent reconstruction of the post-patch get_aggregation decision,
    transcribed from the patched source. Each reference is modeled as a tiny
    annotation object; the attribute reads use getattr with the source defaults
    (`subquery` -> False, `contains_over_clause` -> True)."""

    class Ann:
        def __init__(self, ref):
            # only set attributes when present, to exercise getattr defaults
            if ref["subquery_present"]:
                self.subquery = ref["subquery"]
            if ref["over_present"]:
                self.contains_over_clause = ref["over"]

    refs_subquery = False
    refs_window = False
    for refs in aggregates:
        anns = [Ann(r) for r in refs]
        refs_subquery |= any(getattr(a, "subquery", False) for a in anns)
        refs_window |= any(getattr(a, "contains_over_clause", True) for a in anns)
    return bool(
        other_conditions
        or refs_subquery
        or refs_window
    )


def _norm(aggregates):
    """Project the richer (presence-aware) reference form down to the resolved
    booleans the shadow consumes, applying the same getattr defaults."""
    out = []
    for refs in aggregates:
        out.append([
            {
                "subquery": r["subquery"] if r["subquery_present"] else False,
                "over": r["over"] if r["over_present"] else True,
            }
            for r in refs
        ])
    return out


def rand_ref(rng):
    return {
        "subquery_present": rng.random() < 0.7,
        "subquery": rng.random() < 0.5,
        "over_present": rng.random() < 0.7,   # 30% absent -> getattr default True
        "over": rng.random() < 0.5,
    }


def rand_case(rng):
    n_aggs = rng.randint(0, 4)
    aggregates = [
        [rand_ref(rng) for _ in range(rng.randint(0, 4))]
        for _ in range(n_aggs)
    ]
    other = rng.random() < 0.5
    return aggregates, other


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first.
    fixed = [
        # empty: no aggregates, no other conditions -> no wrap
        ([], False),
        ([], True),
        # the F2P shape: a single aggregate referencing one window annotation,
        # no other conditions, not a subquery -> must wrap (True).
        ([[{"subquery_present": True, "subquery": False,
            "over_present": True, "over": True}]], False),
        # same but a non-window, non-subquery reference -> no wrap (False).
        ([[{"subquery_present": True, "subquery": False,
            "over_present": True, "over": False}]], False),
        # subquery reference alone -> wrap.
        ([[{"subquery_present": True, "subquery": True,
            "over_present": True, "over": False}]], False),
        # reference missing the over attribute -> getattr default True -> wrap.
        ([[{"subquery_present": True, "subquery": False,
            "over_present": False, "over": False}]], False),
    ]

    cases = fixed + [rand_case(rng) for _ in range(N)]

    for aggregates, other in cases:
        got = shadow(_norm(aggregates), other)
        want = patched_decision(aggregates, other)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((aggregates, other), got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
