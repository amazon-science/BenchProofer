#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-14053
(nagini).

SHADOW: the impl region of model.py's `resolve_node_names`, copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
The model IS Python: the backward per-node loop runs directly over plain
lists. There is NO @ContractOnly callee (mapping.md section 4): the modeled
operation uses only list indexing and a conditional, so the shadow is fully
self-contained.

ORACLE: the REAL patched repo computation the model models per mapping.md
section 1 — the per-node display-name resolution that `export_text`
(sklearn/tree/export.py) performs from the caller-supplied name table and the
fitted tree's per-node feature-selector array. The gate applies the gold
patch to /testbed before this script runs and sets PYTHONPATH so the patched
package is what imports here; this script does NOT apply any patch itself.

The resolved-name sequence is an intermediate local of the real function
(consumed in place by the report recursion), so the oracle value is captured
from the REAL function's own frame with sys.settrace: the trace fires on the
first line event after the local is bound, snapshotting exactly the value the
genuine patched lines computed. Nothing in the traced function is replaced or
re-executed — the resolution lines that run are the repo's own.

Type bridge (mapping.md section 3):
  * `names: List[int]` (identifier table) <-> the caller's list of distinct
    feature-name strings; the bridge instantiates identifier k for the table
    entry at position k, so `names[k]` <-> `feature_names[k]`;
  * `feat: List[int]` <-> the fitted tree's per-node selector array (numpy
    int array; entries are valid table positions or the reserved out-of-band
    value -2), bridged entrywise via int();
  * result `List[Optional[int]]` <-> the resolved per-node list (a name
    string for a node that selects a feature, None otherwise); a resolved
    string maps back to its table position, None maps to None; compared
    elementwise with exact equality.

Two oracle lanes:

  Lane A (input-domain fuzz, the >=1e5 lane): drive the REAL function with a
  minimal fitted-tree stand-in whose selector array is a chosen in-domain
  vector, tracing the frame and aborting right after the resolution lines
  bind their result — this steers the genuine repo lines over exactly the
  model's Requires-satisfying input domain (every selector -2 or a valid
  table position). Only the surrounding carrier is synthetic; the resolution
  itself is the real repo code.

  Lane B (end-to-end, nothing synthetic): fit REAL DecisionTreeRegressor /
  DecisionTreeClassifier estimators on random data, run the REAL function to
  completion, and capture the same local at frame return. The shadow's
  inputs derive from the raw fitted tree (tree_.feature), never from the
  oracle's output.

Input domain: the model's Requires admit any table (even empty) with every
selector -2 or a valid position. The real resolution modeled here is the
branch taken for a caller-SUPPLIED name table, which the real function only
enters for a non-empty table validated to have exactly one entry per tree
feature — so generation uses len(names) >= 1 (the reachable oracle domain);
the degenerate empty-table point admitted by the (weaker) model precondition
has no oracle-side counterpart.

>= 1e5 Requires-satisfying inputs: 100000 synthetic-selector fuzz cases +
boundary cases (single-entry table with the reported node-mix shape, single
leaf, single internal node, all-leaf and all-internal vectors, empty node
vector, wider tables) + 300 end-to-end fitted trees. Pinned seed: 14053.

Exit 0 iff zero disagreements; on disagreement prints the input and both
sides' resolved sequences and exits 1. stdlib + numpy only.
"""
import json
import random
import sys

import numpy as np

SEED = 14053
N_SYNTH_FUZZ = 100_000
N_FIT_FUZZ = 300
LEAF = -2   # the reserved out-of-band selector value (see mapping.md sec. 2)


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def resolve_node_names(names, feat):
    # impl-start (contracts stripped)
    result = []  # type: List[Optional[int]]
    i = len(feat)
    while i > 0:
        fi = feat[i - 1]
        if fi != -2:
            nm = names[fi]  # type: Optional[int]
            result = [nm] + result
        else:
            none_val = None  # type: Optional[int]
            result = [none_val] + result
        i = i - 1
    return result
    # impl-end


# --- oracle plumbing ----------------------------------------------------------

class _Abort(Exception):
    """Raised from the trace to stop the traced call right after the
    resolution lines bind their result (Lane A only)."""


def capture_resolved(export_text_fn, abort, args, kwargs):
    """Call the REAL function under sys.settrace and snapshot its local
    `feature_names_` (the resolved per-node list) the moment it is bound.
    With abort=True the call is stopped right there (Lane A: the synthetic
    carrier need not support the rest of the function); with abort=False the
    call runs to completion (Lane B)."""
    code_obj = export_text_fn.__code__
    captured = {}

    def local_tr(frame, event, arg):
        if 'feature_names_' in frame.f_locals and 'v' not in captured:
            captured['v'] = list(frame.f_locals['feature_names_'])
            if abort:
                raise _Abort()
        return local_tr

    def global_tr(frame, event, arg):
        if frame.f_code is code_obj:
            return local_tr
        return None

    sys.settrace(global_tr)
    try:
        export_text_fn(*args, **kwargs)
    except _Abort:
        pass
    finally:
        sys.settrace(None)
    if 'v' not in captured:
        raise RuntimeError("oracle capture failed: the resolved per-node "
                           "list was never bound in the traced frame")
    return captured['v']


class _StubTree(object):
    """Minimal fitted-tree stand-in for Lane A: carries a chosen per-node
    selector array and a matching feature count. Only the attributes the
    real function reads BEFORE the resolution lines are provided; the traced
    call is aborted immediately after those lines run."""

    def __init__(self, feat, n_features):
        self.feature = np.asarray(feat, dtype=np.int64)
        self.n_features = n_features


class _StubEstimator(object):
    """Minimal estimator stand-in for Lane A (fitted-check requires a `fit`
    attribute and the fitted-tree attribute)."""

    def __init__(self, feat, n_features):
        self.tree_ = _StubTree(feat, n_features)
        self.classes_ = np.array([0])

    def fit(self, X, y):        # pragma: no cover - presence only
        return self


def make_names(n):
    """Distinct name strings for the real call; identifier k of the model's
    table maps to position k (mapping.md sec. 3 bridge)."""
    return ["nm_%d" % k for k in range(n)]


def real_to_ids(resolved, feature_names):
    """Bridge the oracle's resolved list back to the model's carriers: a
    resolved table entry -> its position identifier, the placeholder -> None."""
    pos = {}
    for k, s in enumerate(feature_names):
        pos[s] = k
    out = []
    for v in resolved:
        if v is None:
            out.append(None)
        else:
            if v not in pos:
                return None     # not a table entry at all: certain mismatch
            out.append(pos[v])
    return out


def diff_case(names_ids, feat_list, real_resolved, feature_names, label):
    shadow = resolve_node_names(names_ids, feat_list)
    real_ids = real_to_ids(real_resolved, feature_names)
    if real_ids != shadow:
        return ("DISAGREEMENT (%s)\n  names=%r feat=%r\n  shadow=%r\n"
                "  real (raw)=%r\n  real (bridged)=%r"
                % (label, names_ids, feat_list, shadow,
                   real_resolved, real_ids))
    return None


# --- input generation -----------------------------------------------------------

def boundary_cases():
    """Hand-picked Requires-satisfying (n_names, feat) configurations,
    all with a non-empty table (the reachable oracle domain)."""
    return [
        # (number of table entries, per-node selector vector)
        (1, [0, 0, LEAF, 0, LEAF, LEAF]),      # single entry, node mix
        (1, [LEAF]),                           # a single leaf (stump)
        (1, [0]),                              # a single internal node
        (1, []),                               # empty node vector
        (1, [LEAF, LEAF, LEAF]),               # all leaves
        (1, [0, 0, 0]),                        # all internal
        (2, [0, 1, LEAF, 1, LEAF]),            # two entries
        (2, [1, 1, 1]),                        # only the last entry used
        (3, [2, LEAF, 0, 1, LEAF, LEAF]),      # three entries
        (6, [5, 0, LEAF, 3, 3, LEAF, 1]),      # wider table, repeats
    ]


def fuzz_case(rng):
    n = rng.randint(1, 6)                      # >= 1 table entry
    m = rng.randint(0, 20)                     # node count
    feat = []
    for _ in range(m):
        if rng.random() < 0.5:
            feat.append(LEAF)
        else:
            feat.append(rng.randrange(n))
    return n, feat


def main():
    # REAL patched repo symbols (PYTHONPATH=/testbed, gold patch applied by
    # the gate before this script runs)
    from sklearn.tree.export import export_text
    from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

    checked = 0
    failures = 0
    rng = random.Random(SEED)
    nprng = np.random.RandomState(SEED)

    # --- lane A: synthetic in-domain selector vectors -----------------------
    lane_a_inputs = boundary_cases()
    for _ in range(N_SYNTH_FUZZ):
        lane_a_inputs.append(fuzz_case(rng))

    for n, feat in lane_a_inputs:
        feature_names = make_names(n)
        est = _StubEstimator(feat, n)
        real_resolved = capture_resolved(
            export_text, True, (est,), {"feature_names": feature_names})
        err = diff_case(list(range(n)), list(feat), real_resolved,
                        feature_names, "synthetic selectors")
        if err:
            print(err)
            return 1
        checked += 1

    # --- lane B: end-to-end fitted estimators, nothing synthetic ------------
    n_fit = 0
    for k in range(N_FIT_FUZZ):
        n_features = int(nprng.randint(1, 7))
        n_samples = int(nprng.randint(4, 30))
        X = nprng.uniform(-10.0, 10.0, size=(n_samples, n_features))
        if k % 3 == 0:
            y = nprng.randint(0, 3, size=n_samples)
            est = DecisionTreeClassifier(
                max_depth=int(nprng.randint(1, 5)), random_state=k)
        else:
            y = nprng.uniform(-1.0, 1.0, size=n_samples)
            est = DecisionTreeRegressor(
                max_depth=int(nprng.randint(1, 5)), random_state=k)
        est.fit(X, y)
        feature_names = make_names(n_features)

        real_resolved = capture_resolved(
            export_text, False, (est,), {"feature_names": feature_names})

        feat_list = [int(v) for v in est.tree_.feature]
        err = diff_case(list(range(n_features)), feat_list, real_resolved,
                        feature_names, "end-to-end fit")
        if err:
            print(err)
            return 1
        checked += 1
        n_fit += 1

    print("G-CONF OK: shadow impl == real patched per-node name resolution "
          "on %d inputs (%d synthetic-selector + %d end-to-end fitted cases, "
          "seed %d)." % (checked, checked - n_fit, n_fit, SEED))
    print(json.dumps({"checked": checked, "disagreements": failures,
                      "seed": SEED, "fit_cases": n_fit,
                      "shadow": "direct (contract-stripped impl region; "
                                "no @ContractOnly callees; oracle local "
                                "captured from the real frame via settrace)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
