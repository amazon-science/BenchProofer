#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sympy__sympy-19954.

The bundle models ONE routine: the per-candidate update of the three parallel
accumulator collections (`blocks`, `num_blocks`, `rep_blocks`) inside
`PermutationGroup.minimal_blocks` (mapping.md). Its observable outcome is the new
triple of collections after comparing a fresh candidate against the retained
representative cells, pruning superseded systems from all three collections in
alignment, and conditionally appending the candidate.

Standing up a transitive permutation group to drive the real method is heavy and
unnecessary: the modeled value is a PURE function of the observables the inner
block reads (`blocks`, `num_blocks`, `rep_blocks`, and the candidate triple
`block`, `num_block`, `rep`). So the ORACLE below is a faithful in-process
replica of the POST-PATCH inner block (the gold `blocks_remove_mask` rewrite),
and the SHADOW is the op-for-op transliteration of
`implementation_pruneSystems` (Solution.lean impl region), per refinement.md.

This genuinely tests the soundness-critical clause: when TWO OR MORE retained
systems are superseded by one candidate, the three collections must be pruned by
the SAME aligned index set (the gold mask) rather than by a running index into a
shrinking list — the divergence that produced the original IndexError / silent
misalignment. The single-supersession and no-supersession cases are also covered.

stdlib-only. Pinned seed: 19954 (also in mapping.md).
"""
import random
import sys

SEED = 19954
N = 150_000


# --- ORACLE: faithful in-process replica of the POST-PATCH inner block --------
# rep / r are sets; blocks entries are lists; num entries are tuples.
def oracle(blocks, num_blocks, rep_blocks, block, num_block, rep):
    blocks = list(blocks)
    num_blocks = list(num_blocks)
    rep_blocks = list(rep_blocks)
    minimal = True
    blocks_remove_mask = [False] * len(blocks)
    for i, r in enumerate(rep_blocks):
        if len(r) > len(rep) and rep.issubset(r):
            blocks_remove_mask[i] = True
        elif len(r) < len(rep) and r.issubset(rep):
            minimal = False
            break
    blocks = [b for i, b in enumerate(blocks) if not blocks_remove_mask[i]]
    num_blocks = [n for i, n in enumerate(num_blocks) if not blocks_remove_mask[i]]
    rep_blocks = [r for i, r in enumerate(rep_blocks) if not blocks_remove_mask[i]]
    if minimal and num_block not in num_blocks:
        blocks = blocks + [block]
        num_blocks = num_blocks + [num_block]
        rep_blocks = rep_blocks + [rep]
    return (blocks, num_blocks, rep_blocks)


# --- SHADOW of implementation_pruneSystems (the R/I legs) ----------------------
# Mirrors Solution.lean impl region exactly: build a removal mask while scanning
# (true=superseded), stop and pad on a dominating cell, then dropFlagged all
# three collections by that single mask, then conditionally append.
def superseded_by(rep, r):
    return len(r) > len(rep) and rep.issubset(r)


def dominates(rep, r):
    return len(r) < len(rep) and r.issubset(rep)


def drop_flagged(xs, mask):
    # dropFlagged: drop xs[i] where mask[i]; if mask runs out, keep the rest.
    out = []
    for i, a in enumerate(xs):
        if i < len(mask) and mask[i]:
            continue
        out.append(a)
    return out


def shadow(blocks, num_blocks, rep_blocks, block, num_block, rep):
    minimal = True
    mask = []
    for r in rep_blocks:
        if superseded_by(rep, r):
            mask = mask + [True]
        elif dominates(rep, r):
            minimal = False
            break
        else:
            mask = mask + [False]
    mask = mask + [False] * (len(rep_blocks) - len(mask))
    blocks2 = drop_flagged(blocks, mask)
    num2 = drop_flagged(num_blocks, mask)
    rep2 = drop_flagged(rep_blocks, mask)
    if minimal and (num_block not in num2):
        return (blocks2 + [block], num2 + [num_block], rep2 + [rep])
    else:
        return (blocks2, num2, rep2)


def disagree(args):
    got = oracle(*args)
    want = shadow(*args)
    if got != want:
        return (args, got, want)
    return None


# rep cells modeled as frozensets of small ints; the only behavior that matters
# is cardinality and subset relations among rep cells.
def _rand_set(rng):
    pts = list(range(rng.randint(0, 7)))
    return frozenset(p for p in range(8) if rng.random() < 0.55) or frozenset(pts[:1])


def _make_case(rng):
    n = rng.randint(0, 6)
    rep_blocks = [_rand_set(rng) for _ in range(n)]
    # blocks / num entries are carried opaquely; tag by index so misalignment shows
    blocks = [[i, i + 100] for i in range(n)]
    num_blocks = [(i, i + 1) for i in range(n)]
    rep = _rand_set(rng)
    block = [999, 1000]
    # num_block sometimes collides with an existing one to exercise the dedup
    if n > 0 and rng.random() < 0.3:
        num_block = num_blocks[rng.randrange(n)]
    else:
        num_block = (777, 778)
    return (blocks, num_blocks, rep_blocks, block, num_block, rep)


def _edge_cases():
    cases = []
    # no retained systems -> candidate appended
    cases.append(([], [], [], [9, 9], (7, 7), frozenset({0, 1})))
    # ONE superseded (rep ⊂ r): r0 removed from all three
    cases.append(([[0, 1]], [(0, 0)], [frozenset({0, 1, 2, 3})],
                  [9, 9], (7, 7), frozenset({0, 1})))
    # TWO superseded by one candidate -> aligned mask removes both rows 0 and 1
    # (the soundness-critical case: a running index would mis-delete here).
    cases.append(([[0, 1], [2, 3]], [(0, 0), (1, 1)],
                  [frozenset({0, 1, 2, 3}), frozenset({0, 1, 4, 5})],
                  [9, 9], (7, 7), frozenset({0, 1})))
    # dominating cell -> candidate rejected, no pruning of remaining indices
    cases.append(([[0, 1], [2, 3]], [(0, 0), (1, 1)],
                  [frozenset({0}), frozenset({0, 1, 2, 3})],
                  [9, 9], (7, 7), frozenset({0, 1})))
    # superseded THEN dominating: break stops before pruning later rows
    cases.append(([[0, 1], [2, 3], [4, 5]], [(0, 0), (1, 1), (2, 2)],
                  [frozenset({0, 1, 2, 3}), frozenset({0}), frozenset({0, 1, 2, 3, 4})],
                  [9, 9], (7, 7), frozenset({0, 1})))
    # num_block already present -> not appended even though minimal
    cases.append(([[0, 1]], [(0, 0)], [frozenset({2})],
                  [9, 9], (0, 0), frozenset({0, 1})))
    return cases


def main() -> int:
    checked = 0
    for c in _edge_cases():
        d = disagree(c)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        c = _make_case(rng)
        d = disagree(c)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
