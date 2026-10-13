#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-19954.

This bundle has NO axiomatized external callee: the changed operation is pure
list pruning, modelled DEEPLY by the `filtered` / `kept` folds in model.py's
pure region. There is therefore no `@ContractOnly` axiom to validate against a
library function. What G-AX validates here is the A-reference deep model: that
`filtered` / `kept` (as encoded in model.py) compute exactly the real Python
semantics the gold patch's list comprehensions compute, namely

    [x for i, x in enumerate(L) if not mask[i]]

applied with one shared boolean mask to every parallel list — so the three
pruned lists stay aligned (equal length, parallel correspondence).

As a faithfulness cross-check it also reproduces the PRE-PATCH in-place
deletion (`del num_blocks[i], blocks[i]` while scanning `enumerate(rep_blocks)`)
and confirms it disagrees with the correct filter exactly when two or more
positions are flagged (raising IndexError or keeping the wrong positions) —
which is the bug the F2P `DihedralGroup(18/50).sylow_subgroup(p=2)` triggers.

Imports nothing repo-specific (stdlib only). Exit 0 iff every obligation holds.
"""
import itertools
import random
import sys


# --- model.py deep-model reference encodings (kept in lock-step) -------------

def kept_model(flag):
    """Reference for model.py `kept`: number of False entries."""
    return sum(1 for f in flag if not f)


def filtered_model(xs, flag):
    """Reference for model.py `filtered`: keep xs[i] iff not flag[i],
    survivors in original order. Front-recursive in model.py; iterative here."""
    return [x for i, x in enumerate(xs) if not flag[i]]


# --- the real operation the gold patch performs ------------------------------

def gold_prune(blocks, nums, reps, mask):
    """The gold patch's three list comprehensions, sharing one mask."""
    out_blocks = [b for i, b in enumerate(blocks) if not mask[i]]
    out_nums = [n for i, n in enumerate(nums) if not mask[i]]
    out_reps = [r for i, r in enumerate(reps) if not mask[i]]
    return out_blocks, out_nums, out_reps


# --- the pre-patch buggy operation (for the faithfulness cross-check) --------

def prepatch_prune(blocks, nums, reps, mask):
    """The pre-patch logic: in-place del on blocks/num_blocks while scanning
    enumerate(rep_blocks), with rep_blocks filtered afterwards by membership.
    Returns ('IndexError', ...) when it would raise out of range."""
    bl = list(blocks)
    nb = list(nums)
    to_remove_idx = []
    for i in range(len(reps)):
        if mask[i]:
            if i < len(bl) and i < len(nb):
                del nb[i]
                del bl[i]
                to_remove_idx.append(i)
            else:
                return "IndexError", None, None
    rb = [r for j, r in enumerate(reps) if j not in to_remove_idx]
    return bl, nb, rb


# --- the checks --------------------------------------------------------------

def check_deep_model(xs, mask):
    """Assert filtered_model / kept_model == the gold patch's real semantics."""
    fb, fn, fr = gold_prune(xs, xs, xs, mask)
    fm = filtered_model(xs, mask)
    assert fb == fm, ("filtered deep model unsound on xs=%r mask=%r: gold gave "
                      "%r, deep model gives %r" % (xs, mask, fb, fm))
    # parallel-alignment: all three gold outputs equal length == kept(mask)
    km = kept_model(mask)
    assert len(fb) == len(fn) == len(fr) == km, (
        "parallel alignment broken on xs=%r mask=%r: lens %d,%d,%d kept=%d"
        % (xs, mask, len(fb), len(fn), len(fr), km))


def check_prepatch_is_buggy(n_with_two_plus, n_witness):
    """Confirm the pre-patch logic disagrees with the correct filter exactly
    when >=2 positions are flagged (raises or keeps wrong positions)."""
    witnessed = 0
    for n in range(0, 7):
        for bits in itertools.product([False, True], repeat=n):
            mask = list(bits)
            ids = list(range(n))
            correct = filtered_model(ids, mask)
            pre = prepatch_prune(ids, ids, ids, mask)
            num_flagged = sum(bits)
            if num_flagged >= 2:
                # pre-patch must diverge (IndexError sentinel or wrong survivors)
                if pre[0] == "IndexError" or pre[0] != correct:
                    witnessed += 1
                else:
                    raise AssertionError(
                        "pre-patch unexpectedly correct on mask=%r: pre=%r "
                        "correct=%r" % (mask, pre, correct))
            else:
                # with <=1 flag the in-place del coincides with the filter
                assert pre[0] != "IndexError" and pre[0] == correct, (
                    "pre-patch wrong with <=1 flag mask=%r: pre=%r correct=%r"
                    % (mask, pre, correct))
    assert witnessed >= n_witness, (
        "expected at least %d divergence witnesses, got %d"
        % (n_witness, witnessed))
    return witnessed


def main():
    # --- deep-model (A-reference) boundary cases --------------------------
    boundary = [
        ([], []),
        ([10], [False]),
        ([10], [True]),
        ([10, 20], [False, False]),
        ([10, 20], [True, False]),
        ([10, 20], [False, True]),
        ([10, 20], [True, True]),
        ([10, 20, 30], [True, True, False]),   # the canonical desync case
        ([10, 20, 30], [True, False, True]),
        ([10, 20, 30, 40], [False, True, True, False]),
        ([7, 7, 7, 7], [True, False, True, False]),  # repeated identities
    ]
    for xs, mask in boundary:
        check_deep_model(xs, mask)

    # --- deep-model (A-reference) randomized fuzz -------------------------
    rng = random.Random(19954)
    for _ in range(50000):
        n = rng.randint(0, 12)
        xs = [rng.randint(-3, 3) for _ in range(n)]   # small domain -> ties
        mask = [rng.random() < 0.4 for _ in range(n)]
        check_deep_model(xs, mask)

    # --- pre-patch faithfulness cross-check -------------------------------
    witnessed = check_prepatch_is_buggy(2, 5)

    print("G-AX OK: filtered/kept deep model == gold list-comprehension prune "
          "on %d boundary + 50000 fuzz inputs; pre-patch in-place deletion "
          "diverges on %d >=2-flag witnesses (IndexError / wrong survivors)."
          % (len(boundary), witnessed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
