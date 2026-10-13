#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-14053
(plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`buildLabels`)
              transliterated to Python over the real container types, via the
              mapping.md bijection: `names : List Name` <-> the `feature_names`
              list (slot k carries the name at index k), `refs : List Int` <->
              the `tree_.feature` int list, `sentinel` <-> `_tree.TREE_UNDEFINED`,
              `out : List (Option Name)` <-> the `feature_names_` list (a name or
              None per slot). The fold `labelsOf`/`labelOne` is the in-order
              guarded resolution. There is NO A-tagged callee in the impl region,
              so the shadow is pure R/I and G-CONF carries full weight
              (conf_skip=false).
  * ORACLE  — `patch.diff`'s behaviour: the EXACT gold-added expression
              `[feature_names[i] if i != _tree.TREE_UNDEFINED else None
                for i in feature]`
              evaluated with real Python list indexing and the REAL
              `_tree.TREE_UNDEFINED` constant (imported from the patched repo).
              As an additional end-to-end witness we also drive the REAL patched
              `export_text` on the single-feature tree from the issue and confirm
              the report is produced (no IndexError) with the split node labelled.

They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied),
stdlib + sklearn only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import random
import sys

from sklearn.tree import _tree
from sklearn.tree import DecisionTreeClassifier
from sklearn.tree.export import export_text

SEED = 14053
N_FUZZ = 100_000

SENTINEL = _tree.TREE_UNDEFINED          # the REAL module constant (== -2)


# --- the R/I shadow: Solution.lean labelOne / labelsOf, transliterated --------
def label_one(n_names, sentinel, i):
    """labelOne (names) (sentinel) (i): none if i == sentinel else names[i]?.
    A name table of length n_names carries the name at slot k by the index k."""
    if i == sentinel:
        return None
    return i if 0 <= i < n_names else None


def shadow_labels(n_names, refs):
    """labelsOf names sentinel refs: the in-order per-reference resolution (the
    backward `while` fold of buildLabels), as a list of slot indices / None."""
    return [label_one(n_names, SENTINEL, i) for i in refs]


# --- the oracle: patch.diff's exact added expression --------------------------
def oracle_labels(n_names, refs):
    """patch.diff behaviour: the gold-added comprehension, run with real list
    indexing and the real TREE_UNDEFINED, then mapped back to slot indices for
    comparison (slot k <-> name 'fk', mapping.md §2)."""
    feature_names = ["f%d" % k for k in range(n_names)]
    feature_names_ = [feature_names[i] if i != _tree.TREE_UNDEFINED
                      else None for i in refs]
    return [None if v is None else int(v[1:]) for v in feature_names_]


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4): the single-feature / leaf shapes
    # the issue + F2P test exercise, sentinel at ends, no-sentinel, sentinel-only.
    boundary = [
        (1, [0, SENTINEL, SENTINEL]),       # the F2P shape: one split + 2 leaves
        (1, [SENTINEL]),                    # a stump (root is a leaf)
        (1, [0]),
        (1, [SENTINEL, 0, SENTINEL, 0, SENTINEL]),
        (2, [0, 1, SENTINEL, SENTINEL]),
        (3, [SENTINEL, 2, 0, SENTINEL, 1]),
        (5, [SENTINEL]),                    # short ref list, wide names
        (2, [0, 0, 1, 1, SENTINEL]),
        (4, []),                            # empty ref list
    ]
    for n_names, refs in boundary:
        yield n_names, refs
    for _ in range(n):
        n_names = rng.randint(1, 6)
        length = rng.randint(0, 12)
        refs = []
        for _ in range(length):
            # ~40% sentinel (a leaf node), else a VALID index — the precondition
            # a fitted tree's `feature` array satisfies against feature_names
            # (mapping.md §2.1). Out-of-range non-sentinel refs violate the
            # Requires and are out of scope.
            if rng.random() < 0.4:
                refs.append(SENTINEL)
            else:
                refs.append(rng.randint(0, n_names - 1))
        yield n_names, refs


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for n_names, refs in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_labels(n_names, refs)
        oracle = oracle_labels(n_names, refs)
        if shadow != oracle:
            disagreements.append((n_names, refs, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for n, refs, sh, orc in disagreements:
            print("  n_names=%r refs=%r shadow=%r oracle=%r" % (n, refs, sh, orc))
        return 1

    # end-to-end witness: the real patched export_text on the issue's tree.
    X_single = [[-2], [-1], [-1], [1], [1], [2]]
    y = [0, 0, 0, 1, 1, 1]
    clf = DecisionTreeClassifier(max_depth=2, random_state=0).fit(X_single, y)
    report = export_text(clf, feature_names=['only_feature'])  # must not raise
    if 'only_feature' not in report:
        print("G-CONF FAIL: end-to-end single-feature export_text did not label "
              "its split node:\n%s" % report)
        return 1

    print("G-CONF OK: R/I shadow of buildLabels agrees with patch.diff behaviour "
          "on %d inputs (seed=%d), 0 disagreements; real single-feature "
          "export_text labelled correctly." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
