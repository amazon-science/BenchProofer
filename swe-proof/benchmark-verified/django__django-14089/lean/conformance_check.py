#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_reversed
against the patch.diff behaviour (post-patch OrderedSet reverse enumeration).

The impl region is all R/I (no A-tagged op), so this runs a real fuzz. The shadow
reproduces the impl op-for-op: starting from an empty accumulator, walk the
carrier's ordered members and prepend each, producing the reverse of the member
order (== List.reverse). We diff that against an independent reconstruction of the
post-patch behaviour: build the carrier exactly as the real code does
(`dict.fromkeys(iterable)`, which is what `OrderedSet.__init__` uses) and
materialize `reversed(self.dict)` — the added `__reversed__` method's return —
into a list. Zero disagreements required over >=10^5 fuzzed inputs.

The carrier dedups its input to the distinct members in first-seen order (the
dict keys); the modeled `xs` is that ordered-key list, so the shadow reverses the
deduped sequence, exactly matching `reversed(self.dict)`.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 14089          # pinned in mapping.md
N = 120_000           # >= 10^5


def ordered_keys(raw):
    """Carrier semantics: OrderedSet(iterable) stores dict.fromkeys(iterable),
    i.e. the distinct members in first-seen order."""
    return list(dict.fromkeys(raw))


def shadow(xs):
    """R/I shadow of implementation_reversed: prepend-fold over the ordered
    members == reverse of the member order."""
    acc = []
    for x in xs:
        acc = [x] + acc
    return acc


def patched_reversed(raw):
    """Independent reconstruction of the post-patch behaviour: build the carrier
    dict as the real code does and materialize reversed(self.dict)."""
    d = dict.fromkeys(raw)            # exactly OrderedSet.__init__
    return list(reversed(d))          # exactly reversed(self.dict)


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first, incl. the exact F2P shape.
    fixed = [
        [1, 2, 3],            # F2P: reversed -> [3, 2, 1]
        [],                   # empty
        [7],                  # singleton
        [5, 5, 5],            # all duplicates -> dedups to [5]
        [1, 2, 2, 3, 1],      # interior + wrap duplicates
        [3, 2, 1],            # already-descending
        [-4, 0, 4, -4],       # negatives + dup
    ]

    cases = list(fixed)
    for _ in range(N):
        length = rng.randint(0, 20)
        # small value range to force frequent duplicates (exercise dedup)
        raw = [rng.randint(-6, 6) for _ in range(length)]
        cases.append(raw)

    for raw in cases:
        xs = ordered_keys(raw)        # what the model's `xs` is
        got = shadow(xs)
        want = patched_reversed(raw)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((raw, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
