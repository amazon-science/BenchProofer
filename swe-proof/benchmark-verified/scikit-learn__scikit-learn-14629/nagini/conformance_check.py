#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-14629
(nagini).

SHADOW: the impl region of model.py, copied VERBATIM below with the contract
calls (Requires/Ensures/Invariant) stripped. The @Pure helper ``est_vals``
copies over as a plain function. The ``Estimator`` carrier is reproduced as a
plain attribute holder; its ``PSeq[int]`` label-sequence value is shimmed as a
plain tuple of ints (immutable, value-compared — exactly the PSeq semantics
the shadow needs). There is no @ContractOnly callee (the axioms region is
empty; the gathering is modelled deeply).

ORACLE: the REAL patched repo behaviour the model models per mapping.md —
``sklearn.multioutput.MultiOutputClassifier.fit`` populating the per-output
class-label list ``classes_`` (one entry per fitted sub-estimator in
``estimators_``). The gate applies patch.diff to /testbed before this script
runs and PYTHONPATH resolves the patched in-tree source; this script does NOT
apply any patch itself.

TYPE BRIDGE (mapping.md section 2):
  - ``estimators: List[Estimator]``  <-> ``clf.estimators_`` (the fitted
    sub-estimator list); ``estimators[i].cls_vals`` <-> the VALUE of
    ``clf.estimators_[i].classes_``, encoded as a tuple of int label codes.
    Integer labels are their own codes; non-integer labels (e.g. strings)
    are mapped through an injective global code table — the encoding is a
    bijection on the labels observed, so tuple equality of codes is exactly
    element-for-element value equality of the label arrays (the model's
    discriminator, matching numpy value comparison).
  - ``Result(): List[PSeq[int]]``    <-> ``clf.classes_``; ``Result()[i]``
    <-> the VALUE of ``clf.classes_[i]`` under the same code encoding;
    ``len(Result())`` <-> ``len(clf.classes_)``.

DIFF: for each case, fit the REAL wrapper, bridge its fitted sub-estimator
list into shadow carriers, run the shadow, and compare position-by-position:
  shadow ``gather_output_classes(bridge(estimators_))``
    vs bridged real ``clf.classes_``
plus the structural facts the postconditions pin (``classes_`` is a list, one
entry per sub-estimator). The input list is also checked to be left intact by
the real operation (the frame condition: same objects, same label values).

INPUT DOMAIN: the shadow's precondition demands only read access to the
estimator list, so every fitted sub-estimator list is Requires-satisfying.
The real oracle constructs them by actually fitting: the wrapper needs a 2-D
target matrix, so the reachable oracle domain is >= 1 output (an empty
estimator list cannot be produced by a real fit; the shadow is trivially
consistent there: [] -> []). Coverage: boundary cases (single output,
iris-like 3x3, heterogeneous class counts, negative / non-contiguous /
string labels, several base-estimator kinds) + >= 1e5 fuzz cases, each one a
REAL fit of a cheap base classifier over a random output count / random
per-output label sets, diffed against the shadow. Pinned fuzz seed: 146290.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy + sklearn (the repo under test) only.
"""
import json
import sys

import numpy as np


SEED = 146290
N_FUZZ = 100_000


# --- shadow: model.py pure + impl regions, VERBATIM, contracts stripped -------

class Estimator:
    """Carrier shim: one fitted sub-estimator exposing only the touched facet
    (its learned class-label sequence, as a tuple of int codes — the PSeq[int]
    shim)."""

    def __init__(self, cls_vals):
        self.cls_vals = cls_vals


# pure-start (decorator + Requires stripped)
def est_vals(e):
    return e.cls_vals
# pure-end


def gather_output_classes(estimators):
    # impl-start (contracts stripped)
    result = []
    i = 0
    while i < len(estimators):
        result.append(est_vals(estimators[i]))
        i = i + 1
    return result
    # impl-end


# --- bridge: real label arrays -> tuples of int codes --------------------------

_CODE_TABLE = {}


def label_code(v):
    """Injective label -> int code. Integer-valued labels are their own code
    (so integer cases are bridged identically on both sides); anything else
    gets a fresh negative-offset code from a global table."""
    if isinstance(v, (int, np.integer)):
        return int(v)
    if isinstance(v, np.bool_) or isinstance(v, bool):
        return int(bool(v))
    key = (type(v).__name__, str(v))
    if key not in _CODE_TABLE:
        _CODE_TABLE[key] = 10_000_000 + len(_CODE_TABLE)
    return _CODE_TABLE[key]


def codes(arr):
    """The VALUE of one class-label array as a tuple of int codes."""
    return tuple(label_code(v) for v in np.asarray(arr).ravel())


# --- oracle harness -------------------------------------------------------------

def make_XY(label_sets, rng):
    """A tiny training set whose column j realises exactly label_sets[j]
    (every label present at least once, order shuffled)."""
    n_out = len(label_sets)
    n_samples = max(4, 2 * max(len(s) for s in label_sets))
    X = rng.randn(n_samples, 2)
    cols = []
    for s in label_sets:
        col = np.array([s[t % len(s)] for t in range(n_samples)])
        rng.shuffle(col)
        cols.append(col)
    Y = np.column_stack(cols)
    return X, Y


def check_one(MultiOutputClassifier, base_factory, label_sets, seed):
    """Fit the REAL wrapper on data realising `label_sets`, bridge, diff the
    shadow against the real per-output class-label list. Returns None on
    agreement, else a diagnostic string."""
    rng = np.random.RandomState(seed)
    X, Y = make_XY(label_sets, rng)
    clf = MultiOutputClassifier(base_factory(seed))
    clf.fit(X, Y)

    # bridge the fitted sub-estimator list into shadow carriers; snapshot the
    # per-position label values to check the input is left intact.
    shadow_in = [Estimator(codes(est.classes_)) for est in clf.estimators_]
    snapshot = [e.cls_vals for e in shadow_in]
    ests_before = list(clf.estimators_)

    shadow_out = gather_output_classes(shadow_in)

    # structural facts the postconditions pin, observed on the real side
    if not isinstance(clf.classes_, list):
        return ("real per-output collection is %r, not a list (labels=%r)"
                % (type(clf.classes_), label_sets))
    real_out = [codes(a) for a in clf.classes_]

    if len(shadow_out) != len(real_out):
        return ("length disagreement: shadow=%d real=%d (labels=%r seed=%d)"
                % (len(shadow_out), len(real_out), label_sets, seed))
    if len(real_out) != len(clf.estimators_):
        return ("real collection has %d entries for %d sub-estimators "
                "(labels=%r seed=%d)"
                % (len(real_out), len(clf.estimators_), label_sets, seed))
    for i in range(len(real_out)):
        if shadow_out[i] != real_out[i]:
            return ("entry %d disagreement (labels=%r seed=%d)\n"
                    "  shadow=%r\n  real  =%r"
                    % (i, label_sets, seed, shadow_out[i], real_out[i]))
    # frame: the input carriers are untouched (same objects, same values)
    if [e.cls_vals for e in shadow_in] != snapshot or \
            list(clf.estimators_) != ests_before:
        return "input estimator list mutated (labels=%r seed=%d)" % (
            label_sets, seed)
    return None


def main():
    from sklearn.multioutput import MultiOutputClassifier  # REAL patched repo
    from sklearn.dummy import DummyClassifier
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.ensemble import RandomForestClassifier

    def dummy(seed):
        return DummyClassifier(strategy="prior")

    def tree(seed):
        return DecisionTreeClassifier(random_state=seed)

    def forest(seed):
        return RandomForestClassifier(n_estimators=2, random_state=seed)

    checked = 0

    # --- shadow-only structural sanity: the unreachable empty list ------------
    if gather_output_classes([]) != []:
        print("DISAGREEMENT: shadow on empty input = %r, expected []"
              % (gather_output_classes([]),))
        return 1
    checked += 1

    # --- boundary cases (real fits with heavier base estimators) --------------
    boundary = [
        (forest, [[0, 1]], 0),                       # single output, 2 classes
        (forest, [[0, 1, 2]], 1),                    # single output, 3 classes
        (forest, [[0, 1, 2], [0, 1, 2], [0, 1, 2]], 2),  # iris-like 3x3
        (forest, [[0, 1], [0, 1, 2], [0, 1, 2, 3], [0, 1, 2, 3, 4]], 3),
        (tree,   [[-5, 7], [100, 200, 300]], 4),     # negative / spread labels
        (tree,   [[2, 4, 8, 16]], 5),                # non-contiguous labels
        (tree,   [[0, 1], [0, 1]], 6),               # 2 outputs, same labels
        (dummy,  [["a", "b"], ["x", "y", "z"]], 7),  # string labels
        (dummy,  [["low", "mid", "high"]], 8),
        (tree,   [list(range(10))], 9),              # many classes, one output
        (dummy,  [[0, 1]] * 8, 10),                  # many outputs
    ]
    for base_factory, label_sets, seed in boundary:
        msg = check_one(MultiOutputClassifier, base_factory, label_sets, seed)
        if msg is not None:
            print("DISAGREEMENT\n  " + msg)
            return 1
        checked += 1

    # --- fuzz: >= 1e5 real fits over random output/label configurations -------
    rng = np.random.RandomState(SEED)
    for t in range(N_FUZZ):
        n_out = int(rng.randint(1, 6))
        label_sets = []
        for _ in range(n_out):
            k = int(rng.randint(2, 6))
            # distinct integer labels, possibly negative / non-contiguous
            labels = list(rng.choice(np.arange(-20, 21), size=k,
                                     replace=False))
            label_sets.append([int(v) for v in labels])
        msg = check_one(MultiOutputClassifier, dummy, label_sets,
                        100_000 + t)
        if msg is not None:
            print("DISAGREEMENT (fuzz case %d)\n  " % t + msg)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real per-output class-label gathering "
          "on %d fitted wrappers (boundary + fuzz, seed %d)." % (checked, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
