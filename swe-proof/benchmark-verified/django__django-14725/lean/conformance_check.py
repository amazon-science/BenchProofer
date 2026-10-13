#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_saveFormset
against the patch.diff behaviour (post-patch `BaseModelFormSet.save`).

The impl region is all R-tagged (no A-tagged callee left as a real repo callee):
`save` consumes only the two lists returned by its UNCHANGED collaborators
(`save_existing_objects` -> `existing`, `save_new_objects` -> `new`) and selects
how to combine them based on `self.edit_only`. We model those two lists directly
as inputs and reproduce the post-patch selection op-for-op, asserting zero
disagreements vs an independent reconstruction of the patched function over
>=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 14725          # pinned in mapping.md
N = 120_000           # >= 10^5


def shadow(edit_only: bool, existing: list, new: list) -> list:
    """R shadow of implementation_saveFormset.

    if edit_only: return existing
    return existing + new
    """
    if edit_only:
        return existing
    return existing + new


def patched_save(edit_only: bool, existing: list, new: list) -> list:
    """Independent reconstruction of the post-patch django save() selection:

        if self.edit_only:
            return self.save_existing_objects(commit)
        else:
            return self.save_existing_objects(commit) + self.save_new_objects(commit)

    where save_existing_objects() -> existing, save_new_objects() -> new.
    """
    if edit_only:
        return existing
    else:
        return existing + new


def rand_list(rng: random.Random) -> list:
    return [rng.randint(-50, 50) for _ in range(rng.randint(0, 8))]


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first: cover both flag values crossed with
    # empty / non-empty existing and new.
    fixed = [
        (True, [], []),
        (True, [1, 2], []),
        (True, [], [9]),
        (True, [1, 2], [9, 8]),      # the discriminating case: new must be dropped
        (False, [], []),
        (False, [1, 2], []),
        (False, [], [9]),
        (False, [1, 2], [9, 8]),
    ]
    cases = fixed + [
        (bool(rng.getrandbits(1)), rand_list(rng), rand_list(rng))
        for _ in range(N)
    ]

    for eo, ex, nw in cases:
        got = shadow(eo, ex, nw)
        want = patched_save(eo, ex, nw)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((eo, ex, nw, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for eo, ex, nw, g, w in examples:
            print(f"  edit_only={eo} existing={ex!r} new={nw!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
