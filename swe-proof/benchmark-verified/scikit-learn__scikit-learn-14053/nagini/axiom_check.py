#!/usr/bin/env python3
"""G-AX executable cross-check for scikit-learn__scikit-learn-14053.

This instance axiomatizes NO callee: the changed operation (per-node feature
name resolution) is modeled DEEPLY by the verified `built_seq` fold in
model.py. There is therefore no axiom-soundness trust point. This script is a
lightweight executable demonstration that:

  (1) the deep model `built_seq` (reproduced here) equals the PATCHED list
      comprehension
        [names[i] if i != -2 else None for i in feat]
      on boundary + randomized fuzz over the genuine domain of `tree_.feature`
      (each per-node selector is a valid name index or the leaf marker -2); and

  (2) the PRE-PATCH comprehension
        [names[i] for i in feat]
      raises exactly the reported `IndexError` when a leaf marker (-2) is read
      against a short name table (a single feature) — and silently produces a
      wrong-but-non-crashing value for a longer table — so the defect the spec
      senses is real.

`_tree.TREE_UNDEFINED == -2` (sklearn/tree/_tree.pyx:64). Imports only the
standard library. Exit 0 iff every obligation holds.
"""
import random
import sys

LEAF = -2  # _tree.TREE_UNDEFINED


def built_seq(names, feat):
    """Reference for model.py's deep model `built_seq`: per-node resolution,
    leaf marker (and any non-position selector) -> None, valid index -> name."""
    out = []
    for s in feat:
        if s != LEAF and 0 <= s < len(names):
            out.append(names[s])
        else:
            out.append(None)
    return out


def patched_comprehension(names, feat):
    """The PATCHED line, executed verbatim over the abstracted carriers."""
    return [names[i] if i != LEAF else None for i in feat]


def prepatch_comprehension(names, feat):
    """The PRE-PATCH line, executed verbatim over the abstracted carriers."""
    return [names[i] for i in feat]


def in_domain(names, feat):
    return all(s == LEAF or (0 <= s < len(names)) for s in feat)


def check_model_eq_patch(names, feat):
    """(1) deep model == patched comprehension on a well-formed input."""
    assert in_domain(names, feat)
    expected = patched_comprehension(names, feat)
    observed = built_seq(names, feat)
    assert observed == expected, (
        "deep model built_seq disagrees with patched comprehension on "
        "names=%r feat=%r: model=%r patch=%r"
        % (names, feat, observed, expected))


def main():
    # --- boundary cases ----------------------------------------------------
    # Single feature with leaf markers: the exact reported crash shape.
    single_feat_tree = [0, 0, LEAF, 0, LEAF, LEAF]   # internal/leaf mix
    names1 = [100]                                    # one feature ('first')
    boundary = [
        ([], []),                                     # empty tree
        (names1, single_feat_tree),
        (names1, [LEAF]),                             # a single leaf (stump)
        (names1, [0]),                                # a single internal node
        ([10, 11], [0, 1, LEAF, 1, LEAF]),            # two features
        ([10, 11, 12], [2, LEAF, 0, 1, LEAF, LEAF]),  # three features
    ]
    for names, feat in boundary:
        check_model_eq_patch(names, feat)

    # --- randomized fuzz over the genuine domain ---------------------------
    rng = random.Random(14053)
    for _ in range(20000):
        n = rng.randint(1, 6)                         # >= 1 feature
        names = [rng.randint(0, 9999) for _ in range(n)]
        m = rng.randint(0, 20)                        # node count
        feat = [LEAF if rng.random() < 0.5 else rng.randrange(n)
                for _ in range(m)]
        check_model_eq_patch(names, feat)

    # --- (2) the pre-patch defect is real ----------------------------------
    # Single feature + a leaf marker -> IndexError (the reported bug).
    raised = False
    try:
        prepatch_comprehension(names1, single_feat_tree)
    except IndexError:
        raised = True
    assert raised, ("pre-patch comprehension did NOT raise IndexError on a "
                    "single-feature tree with a leaf marker — the modeled bug "
                    "must be reproducible")

    # With >= 2 features the pre-patch does not crash but resolves the leaf
    # marker to the WRONG (second-to-last) name; the patched/model value is
    # None there. This confirms the spec's leaf clause is load-bearing.
    names2 = [10, 11]
    feat2 = [0, LEAF]
    pre = prepatch_comprehension(names2, feat2)        # [10, 11]  (11 is wrong)
    post = built_seq(names2, feat2)                     # [10, None]
    assert pre != post and pre[1] == names2[LEAF] and post[1] is None, (
        "expected pre-patch to mis-resolve the leaf marker to names[-2] while "
        "the model/patch yields None; got pre=%r post=%r" % (pre, post))

    print("G-AX OK: deep model built_seq == patched comprehension on %d "
          "boundary + 20000 fuzz inputs; pre-patch IndexError reproduced on a "
          "single-feature tree (no consumed axioms)." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
