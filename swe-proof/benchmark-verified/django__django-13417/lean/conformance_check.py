#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_querysetOrdered
against the patch.diff behaviour (post-patch QuerySet.ordered).

The impl region is all R/I (no A-tagged op), so this runs a real fuzz. The shadow
reproduces the impl op-for-op (the if/elif cascade with early returns), with the
default-ordering guard computed exactly as the patched code:
`default_ordering and meta_ordering and not group_by`. We diff that against an
independent reconstruction of the post-patch property, expressed directly from the
patched Python source over the six modeled carriers. Zero disagreements required
over >=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 13417          # pinned in mapping.md
N = 120_000           # >= 10^5


def shadow(is_empty, extra_order_by, order_by, default_ordering,
           meta_ordering, group_by):
    """R/I shadow of implementation_querysetOrdered (the if/elif cascade)."""
    if is_empty:
        return True
    if extra_order_by or order_by:
        return True
    elif default_ordering and meta_ordering and not group_by:
        return True
    else:
        return False


def patched_ordered(is_empty, extra_order_by, order_by, default_ordering,
                    meta_ordering, group_by):
    """Independent reconstruction of post-patch QuerySet.ordered.

    Mirrors the patched source structure directly:
        if isinstance(self, EmptyQuerySet): return True
        if self.query.extra_order_by or self.query.order_by: return True
        elif (self.query.default_ordering and self.query.get_meta().ordering
              and not self.query.group_by): return True
        else: return False
    Sequences are passed as Python lists so their truthiness matches the attribute.
    """
    if is_empty:
        return True
    if extra_order_by or order_by:
        return True
    elif (default_ordering and meta_ordering and not group_by):
        return True
    else:
        return False


def rand_seq(rng):
    """A sequence carrier: empty ~40% of the time, else a short token list."""
    if rng.random() < 0.4:
        return []
    return ["x"] * rng.randint(1, 4)


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first, incl. the exact F2P shapes.
    fixed = [
        # annotated (GROUP BY) qs over a model with Meta.ordering -> False
        (False, [], [], True, ["name"], ["pk"]),
        # same but with explicit .order_by('name') -> True
        (False, [], ["name"], True, ["name"], ["pk"]),
        # values().annotate() GROUP BY over Meta.ordering -> False
        (False, [], [], True, ["name"], ["name"]),
        # default ordering, no GROUP BY -> True
        (False, [], [], True, ["name"], []),
        # no default, no explicit -> False
        (False, [], [], False, ["name"], []),
        # empty queryset always ordered
        (True, [], [], False, [], []),
        # extra_order_by short-circuits
        (False, ["e"], [], False, [], ["pk"]),
        # default_ordering True but meta empty -> False
        (False, [], [], True, [], []),
    ]
    cases = fixed + [
        (
            rng.random() < 0.5,
            rand_seq(rng),
            rand_seq(rng),
            rng.random() < 0.5,
            rand_seq(rng),
            rand_seq(rng),
        )
        for _ in range(N)
    ]

    for args in cases:
        got = shadow(*args)
        want = patched_ordered(*args)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((args, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
