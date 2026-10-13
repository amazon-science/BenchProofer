#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
implementation_featureNamesByNode against the patch.diff behaviour (the
post-patch list comprehension in export_text).

The impl region is NOT all-A-tagged (it is pure R/I structure), so this runs a
real fuzz. The shadow reproduces the Lean impl op-for-op; we diff it against an
independent reconstruction of the post-patch comprehension over >=10^5 fuzzed
inputs.

Python `feature_names[i]` is total only because internal-node indices are in
range (the earlier len()==n_features ValueError guard) and leaf entries are -2.
The Lean R model uses the total `xs[i]?`. We therefore fuzz the realistic shape
(per mapping.md): index lists of in-range internal indices plus the leaf
sentinel -2, with feature_names lengths from 0 up. On that domain the total
lookup returns `some name` exactly where Python's lookup succeeds.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 14053          # pinned in mapping.md
N = 120_000           # >= 10^5
TREE_UNDEFINED = -2   # sklearn/tree/_tree.pyx:64


def get_opt(xs, i):
    """Lean `xs[i.toNat]?` — total positional lookup, None if out of range.
    i.toNat clamps negative i to 0 (mirrors Int.toNat in Lean)."""
    n = max(i, 0)
    return xs[n] if 0 <= n < len(xs) else None


def shadow(feature_names, features):
    """R/I shadow of implementation_featureNamesByNode.

    acc := []; for i in features:
       if i != sentinel: acc += [feature_names[i.toNat]?] else acc += [None]
    return acc.
    """
    acc = []
    for i in features:
        if i != TREE_UNDEFINED:
            acc.append(get_opt(feature_names, i))
        else:
            acc.append(None)
    return acc


def patched(feature_names, features):
    """Independent reconstruction of the post-patch comprehension:
    [feature_names[i] if i != _tree.TREE_UNDEFINED else None for i in features].
    All internal indices are in range by construction (see main), so the lookup
    never raises; we surface any out-of-range as None to match the total model
    (this branch is unreachable on the realistic domain)."""
    out = []
    for i in features:
        if i != TREE_UNDEFINED:
            out.append(feature_names[i] if 0 <= i < len(feature_names) else None)
        else:
            out.append(None)
    return out


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first.
    fixed = [
        ([], []),
        (["first"], [0, -2, -2]),                  # the F2P single-feature tree
        (["first"], [-2]),                         # single leaf (degenerate tree)
        (["a", "b", "c"], [0, 1, -2, 2, -2, -2]),
        (["x"], []),
        (["p", "q"], [-2, -2, -2]),                # all leaves
        (["p", "q"], [0, 1]),                      # all internal
    ]

    cases = list(fixed)
    for _ in range(N):
        nf = rng.randint(0, 8)
        feature_names = [f"f{k}" for k in range(nf)]
        m = rng.randint(0, 24)
        features = []
        for _ in range(m):
            # oversample the leaf sentinel; otherwise a valid in-range index
            if nf == 0 or rng.random() < 0.4:
                features.append(TREE_UNDEFINED)
            else:
                features.append(rng.randrange(nf))
        cases.append((feature_names, features))

    for feature_names, features in cases:
        got = shadow(feature_names, features)
        want = patched(feature_names, features)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((feature_names, features, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for fn, ft, g, w in examples:
            print(f"  names={fn!r} feat={ft!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
