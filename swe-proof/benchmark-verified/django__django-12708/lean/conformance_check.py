#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
implementation_dropComposedIndex against the patch.diff behaviour (the
index-removal selection in `_delete_composed_index`, post-patch kwargs
`{'index': True, 'unique': False}`).

The impl region is R/I (rows 1,2,4,5) plus a deeply-modeled, executable
A-reference (row 3, the `_constraint_names` keyword filter). conf_skip=false:
this runs a real fuzz.

  shadow (op-for-op transliteration of implementation_dropComposedIndex):
    names = []                                              # I
    for c in constraints:                                   # R: dict iteration
        if c.columns == cols and c.is_index and (not c.is_unique) \
           and (not c.excluded):                            # A-ref: post-patch filter
            names.append(c.name)
    if len(names) != 1: return ('error', len(names))        # R: count check / raise
    return ('ok', names[0])                                 # R: the dropped name

We diff against an INDEPENDENT reconstruction of the patched Python selection
(`patched_selection`) that follows `_constraint_names`'s loop and
`_delete_composed_index`'s exactly-one check directly. exit 0 iff zero
disagreements over >=10^5 fuzzed inputs.

stdlib-only.
"""
import random
import sys

SEED = 12708          # pinned in mapping.md
N = 120_000           # >= 10^5

COLNAMES = ["pink", "weight", "name", "height", "age"]


def shadow(constraints, cols):
    """R/I shadow of implementation_dropComposedIndex.

    `constraints` is a list of dicts with keys
    name/columns/is_index/is_unique/excluded; `cols` is a list[str].
    Returns ('ok', name) or ('error', n)."""
    names = []
    for c in constraints:
        if (c["columns"] == cols and c["is_index"] and (not c["is_unique"])
                and (not c["excluded"])):
            names.append(c["name"])
    if len(names) != 1:
        return ("error", len(names))
    return ("ok", names[0])


def patched_selection(constraints, cols):
    """Independent reconstruction of the post-patch selection performed by
    `_delete_composed_index` at the index-removal call site, following
    `_constraint_names` with kwargs index=True, unique=False and the `exclude`
    set (modeled per-constraint as `excluded`), then the exactly-one count
    check.

    Note this is written from the Python semantics directly, NOT by reusing
    `shadow`, so a divergence would surface."""
    constraint_names = []
    for c in constraints:
        # _constraint_names keyword filter (only the active flags at this site):
        if c["columns"] != cols:
            continue
        if c["is_index"] is not True:          # index=True
            continue
        if c["is_unique"] is not False:        # unique=False  (the patch)
            continue
        if c["excluded"]:                      # name in exclude set
            continue
        constraint_names.append(c["name"])
    # _delete_composed_index exactly-one check
    if len(constraint_names) != 1:
        return ("error", len(constraint_names))   # ValueError(len) payload
    return ("ok", constraint_names[0])            # constraint_names[0] is dropped


def random_case(rng):
    cols = rng.sample(COLNAMES, rng.randint(1, 3))
    # half the time, also generate constraints over a DIFFERENT column set
    other = rng.sample(COLNAMES, rng.randint(1, 3))
    k = rng.randint(0, 5)
    constraints = []
    for i in range(k):
        use_target = rng.random() < 0.6
        ccols = list(cols) if use_target else list(other)
        constraints.append({
            "name": f"c{i}",
            "columns": ccols,
            "is_index": rng.random() < 0.7,
            "is_unique": rng.random() < 0.4,
            "excluded": rng.random() < 0.25,
        })
    return constraints, cols


def fixed_cases():
    """Boundary cases, incl. the F2P scenario: a unique + an ordinary index over
    the same columns."""
    cols = ["pink", "weight"]
    return [
        # F2P: unique_together + index_together over the same columns.
        ([{"name": "uniq", "columns": cols, "is_index": True, "is_unique": True,
           "excluded": False},
          {"name": "idx", "columns": cols, "is_index": True, "is_unique": False,
           "excluded": False}], cols),
        # only the index present -> ok
        ([{"name": "idx", "columns": cols, "is_index": True, "is_unique": False,
           "excluded": False}], cols),
        # only a unique present -> 0 candidates -> error 0
        ([{"name": "uniq", "columns": cols, "is_index": True, "is_unique": True,
           "excluded": False}], cols),
        # nothing -> error 0
        ([], cols),
        # index but excluded (declared via Meta.indexes) -> error 0
        ([{"name": "idx", "columns": cols, "is_index": True, "is_unique": False,
           "excluded": True}], cols),
        # two ordinary indexes over same cols -> error 2
        ([{"name": "i1", "columns": cols, "is_index": True, "is_unique": False,
           "excluded": False},
          {"name": "i2", "columns": cols, "is_index": True, "is_unique": False,
           "excluded": False}], cols),
        # index over different cols -> error 0
        ([{"name": "idx", "columns": ["name"], "is_index": True,
           "is_unique": False, "excluded": False}], cols),
    ]


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []
    cases = fixed_cases() + [random_case(rng) for _ in range(N)]
    for constraints, cols in cases:
        got = shadow(constraints, cols)
        want = patched_selection(constraints, cols)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((constraints, cols, got, want))
    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for c, cols, g, w in examples:
            print(f"  cols={cols!r} constraints={c!r} shadow={g!r} patched={w!r}")
        return 1
    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
