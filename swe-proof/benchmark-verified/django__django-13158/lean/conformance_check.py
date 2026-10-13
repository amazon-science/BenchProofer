#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-13158.

The bundle models ONE function: `Query.set_empty`
(`django/db/models/sql/query.py:1778`). Its Lean implementation
(`implementation_makeEmpty`) forces a query tree to return an empty result set:
mark this node's own where to match nothing, AND recurse into every combined
sub-query so the empty-result guarantee holds of the WHOLE tree:

    make_empty(mk(_, combined)) = mk(True, [make_empty(sub) for sub in combined])

A query is modeled by its single touched per-node fact (`self_empty`: has its own
where been forced to match nothing?) plus the ordered list of sub-queries combined
into its result (`combined`), nested to any depth. A leaf has `combined == []`.

This script transliterates that R/I impl into Python (`shadow_make_empty`) and
differential-tests it against an ORACLE: a faithful in-process replica of the
POST-PATCH semantics of `Query.set_empty` at the same abstraction — i.e.
`set_empty` appends a NothingNode to this query's where (self_empty := True) and,
per the fix, calls `set_empty()` on every query in `self.combined_queries`.

We do NOT stand up Django/ORM (heavy; the modeled value is the recursion of the
"force empty" through the combined-query tree). Both legs receive the SAME input:
a random query tree.

Two observations are compared for every input:
  * `yields_nothing(tree)` — does the WHOLE tree now return no rows? (own where
    empty AND every combined sub-query yields nothing, recursively). This is the
    F2P discriminator: pre-fix, only the top node was emptied, so a combined
    sub-query still yielded its rows.
  * `to_shape(tree)` — the bare nesting structure (frame): the operation must not
    add or drop any sub-query at any level.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 13158 (also in
mapping.md).
"""
import sys

SEED = 13158
N = 120_000


# --- query-tree model --------------------------------------------------------
# A query is a dict {"self_empty": bool, "combined": [query, ...]}.
def leaf(self_empty=False):
    return {"self_empty": self_empty, "combined": []}


def node(self_empty, combined):
    return {"self_empty": self_empty, "combined": combined}


# --- observations ------------------------------------------------------------
def yields_nothing(q):
    """Whole-tree empty-result guarantee: own where forced empty AND every
    combined sub-query yields nothing, recursively."""
    if not q["self_empty"]:
        return False
    return all(yields_nothing(sub) for sub in q["combined"])


def to_shape(q):
    """Bare nesting structure with self_empty markers erased."""
    return [to_shape(sub) for sub in q["combined"]]


# --- ORACLE: post-patch set_empty semantics, faithful replica ----------------
def oracle_set_empty(q):
    """Rebuild the tree as post-patch `set_empty` would leave it: this node's own
    where forced empty, and `set_empty` recursed into every combined sub-query."""
    return {
        "self_empty": True,
        "combined": [oracle_set_empty(sub) for sub in q["combined"]],
    }


# --- shadow of implementation_makeEmpty (the R/I leg) ------------------------
def shadow_make_empty(q):
    self_empty = True
    subs = []
    for sub in q["combined"]:
        subs.append(shadow_make_empty(sub))
    return {"self_empty": self_empty, "combined": subs}


def disagree(q):
    o = oracle_set_empty(q)
    s = shadow_make_empty(q)
    # compare both observations, not raw dicts (defensive)
    if yields_nothing(o) != yields_nothing(s):
        return ("yields_nothing", q, yields_nothing(o), yields_nothing(s))
    if to_shape(o) != to_shape(s):
        return ("to_shape", q, to_shape(o), to_shape(s))
    # also the full rebuilt tree must match
    if o != s:
        return ("tree", q, o, s)
    # sanity: post-op the whole tree MUST yield nothing (the fix's point)
    if not yields_nothing(s):
        return ("post_not_empty", q, True, yields_nothing(s))
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _rand_tree(rnd, depth=0):
    self_empty = (next(rnd) % 2 == 0)
    # limit fan-out and depth to keep trees finite
    n_children = 0 if depth >= 4 else (next(rnd) % 4)
    combined = [_rand_tree(rnd, depth + 1) for _ in range(n_children)]
    return {"self_empty": self_empty, "combined": combined}


def _edge_cases():
    return [
        leaf(False),                                   # single leaf, not empty
        leaf(True),                                    # single leaf, already empty
        # THE fix: a union node with two leaf sub-queries (test_union_none shape)
        node(False, [leaf(False), leaf(False)]),
        node(True, [leaf(False), leaf(False)]),        # top marked but children not
        node(False, [leaf(True), leaf(True)]),
        # nested combination
        node(False, [node(False, [leaf(False)]), leaf(False)]),
        node(False, [leaf(False), leaf(False), leaf(False)]),
        # deep chain
        node(False, [node(False, [node(False, [leaf(False)])])]),
    ]


def main() -> int:
    checked = 0

    for q in _edge_cases():
        d = disagree(q)
        if d:
            print(f"DISAGREE edge [{d[0]}] {d[1]!r}: oracle={d[2]} shadow={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        q = _rand_tree(rnd)
        d = disagree(q)
        if d:
            print(f"DISAGREE fuzz [{d[0]}] {d[1]!r}: oracle={d[2]} shadow={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
