#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-19954 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`keepByMask`
              applied to all three parallel lists) transliterated to Python over
              the *real* repo types, via the mapping.md bijection (each list
              element ↔ an opaque int identifier; the per-position removal
              decision ↔ a list[bool]). `keepByMask` is transliterated
              front-recursively, exactly as the Lean fold consumes flag+entry
              together from the front. There is NO A-tagged callee to leave real
              (mapping.md §3): the slice axiomatizes nothing.
  * ORACLE  — `patch.diff`'s behaviour: the three list-comprehensions the gold
              patch installs at sympy/combinatorics/perm_groups.py:2207-2209,
              run verbatim on the same (blocks, num_blocks, rep_blocks, mask):
                  blocks     = [b for i,b in enumerate(blocks)     if not mask[i]]
                  num_blocks = [n for i,n in enumerate(num_blocks) if not mask[i]]
                  rep_blocks = [r for i,r in enumerate(rep_blocks) if not mask[i]]

They must agree, element for element, on all three returned lists for every
input — AND the oracle's three lists must stay equal-length (the index-alignment
the IndexError bug destroyed). Exit 0 iff zero disagreements; any disagreement is
a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image); stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 19954
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean keepByMask, transliterated ---------------
def keep_by_mask(xs, mask):
    """keepByMask (xs : List Int) (mask : List Bool), front-recursive: consume
    one entry and one flag from the front together; a True flag drops the entry,
    a False flag keeps it; a shorter mask truncates (matches the Lean clauses
    keepByMask_nil_left / keepByMask_nil_right)."""
    out = []
    n = min(len(xs), len(mask))
    for k in range(n):
        if not mask[k]:
            out.append(xs[k])
    return out


def shadow_prune(blocks, num_blocks, rep_blocks, mask):
    """The impl region of pruneParallelSystems: all three lists filtered by the
    SAME mask."""
    return (
        keep_by_mask(blocks, mask),
        keep_by_mask(num_blocks, mask),
        keep_by_mask(rep_blocks, mask),
    )


# --- the oracle: patch.diff's three list-comprehensions, verbatim -----------
def oracle_prune(blocks, num_blocks, rep_blocks, mask):
    """The gold patch behaviour (perm_groups.py:2207-2209). Inputs are
    index-aligned and the mask has one flag per position (the require clauses)."""
    new_blocks = [b for i, b in enumerate(blocks) if not mask[i]]
    new_num_blocks = [n for i, n in enumerate(num_blocks) if not mask[i]]
    new_rep_blocks = [r for i, r in enumerate(rep_blocks) if not mask[i]]
    return new_blocks, new_num_blocks, new_rep_blocks


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4) -- (length, mask) shapes that
    # exercise the IndexError trigger: a flagged position BEFORE the list end.
    boundary = [
        (0, []),
        (1, [False]),
        (1, [True]),
        (2, [True, False]),    # del-by-index here shifted indices -> IndexError
        (2, [False, True]),
        (3, [True, False, False]),
        (3, [False, True, True]),
        (3, [True, True, True]),
        (4, [True, False, True, False]),
        (5, [True, True, False, True, False]),
    ]
    for length, mask in boundary:
        blocks = list(range(100, 100 + length))
        num_blocks = list(range(200, 200 + length))
        rep_blocks = list(range(300, 300 + length))
        yield blocks, num_blocks, rep_blocks, mask
    for _ in range(n):
        length = rng.randint(0, 16)
        mask = [rng.random() < 0.4 for _ in range(length)]
        # distinct identifier ranges per list so a cross-list mix-up is visible
        blocks = [rng.randint(0, 10_000) for _ in range(length)]
        num_blocks = [rng.randint(20_000, 30_000) for _ in range(length)]
        rep_blocks = [rng.randint(40_000, 50_000) for _ in range(length)]
        yield blocks, num_blocks, rep_blocks, mask


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for blocks, num_blocks, rep_blocks, mask in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_prune(blocks, num_blocks, rep_blocks, mask)
        oracle = oracle_prune(blocks, num_blocks, rep_blocks, mask)
        # alignment invariant the bug violated: all three oracle lists equal-length
        aligned = len(oracle[0]) == len(oracle[1]) == len(oracle[2])
        if shadow != oracle or not aligned:
            disagreements.append((blocks, num_blocks, rep_blocks, mask, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for b, n, r, m, sh, orc in disagreements:
            print("  blocks=%r num=%r rep=%r mask=%r shadow=%r oracle=%r"
                  % (b, n, r, m, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of pruneParallelSystems agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements; all three lists "
          "stay index-aligned." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
