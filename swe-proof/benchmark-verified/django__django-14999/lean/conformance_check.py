#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_renameModel
against the patch.diff behaviour (post-patch RenameModel.database_forwards).

The impl region is NOT all-A-tagged (it is pure R/I control flow over reified
schema operations). We model the function's result as the ordered list of
emitted schema operations (see mapping.md): the main table rename is one
`("renameTable", old, new)` datum, and the UNCHANGED dependent follow-up
operations are the opaque input list `tail_ops`.

`shadow` is the op-for-op R/I reconstruction of implementation_renameModel.
`patched` is an independent reconstruction of the post-patch Python control flow.
We assert zero disagreements over >= 10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 14999          # pinned in mapping.md
N = 120_000           # >= 10^5


def shadow(allow_migrate, old_db_table, new_db_table, tail_ops):
    """R/I shadow of implementation_renameModel (Id.run do skeleton)."""
    if not allow_migrate:
        return []
    if old_db_table == new_db_table:
        return []
    acc = []
    acc = acc + [("renameTable", old_db_table, new_db_table)]
    acc = acc + list(tail_ops)
    return acc


def patched(allow_migrate, old_db_table, new_db_table, tail_ops):
    """Independent reconstruction of the post-patch database_forwards control
    flow, observing only the sequence of emitted schema operations.

        if allow_migrate_model(...):
            old_db_table = ...; new_db_table = ...
            if old_db_table == new_db_table:
                return            # emit nothing
            alter_db_table(new_model, old_db_table, new_db_table)   # main rename
            <dependent related-objects + m2m operations>            # = tail_ops
    """
    ops = []
    if allow_migrate:
        if old_db_table == new_db_table:
            return ops
        ops.append(("renameTable", old_db_table, new_db_table))
        ops.extend(tail_ops)
    return ops


def rand_table(rng):
    # Small alphabet of table names so the old==new collision is hit often.
    return rng.choice(["rider", "runner", "pony", "auth_user", "t", "rider"])


def rand_tail(rng):
    n = rng.randint(0, 4)
    out = []
    for _ in range(n):
        if rng.random() < 0.5:
            out.append(("renameTable", rand_table(rng), rand_table(rng)))
        else:
            out.append(("other", rng.randint(0, 9)))
    return out


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first.
    fixed = [
        (False, "rider", "runner", []),
        (False, "rider", "rider", [("other", 1)]),
        (True, "rider", "rider", []),                       # noop branch (the fix)
        (True, "rider", "rider", [("other", 1)]),           # noop, nonempty tail
        (True, "rider", "runner", []),                      # rename, empty tail
        (True, "rider", "runner", [("other", 1), ("renameTable", "a", "b")]),
        (True, "", "", []),
        (True, "", "x", [("other", 0)]),
    ]
    cases = fixed + [
        (rng.random() < 0.5, rand_table(rng), rand_table(rng), rand_tail(rng))
        for _ in range(N)
    ]

    for (am, old, new, tail) in cases:
        got = shadow(am, old, new, tail)
        want = patched(am, old, new, tail)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((am, old, new, tail), got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
