#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-26194.

The model axiomatizes two UNCHANGED numeric primitives the routine relies on:

  (A-consumed) `pos_inf()`  -- the positive-infinity sentinel that the routine
      prepends as the anchoring threshold. It models NumPy's `np.inf`.

  (A-consumed) `is_pos_inf(x)` -- the test "is `x` the positive-infinity
      sentinel". It models NumPy's `np.isinf` (restricted to the positive
      sentinel; `np.inf` is positive).

  Proof obligation the model consumes: `is_pos_inf(pos_inf())` is true. The
  executable check therefore asserts the axiom's `Ensures` against the real
  callees: `np.isinf(np.inf)` is True, `np.inf` is positive, and a finite nudge
  of any score (`finite + 1.0`, the rejected pre-patch value) is NOT infinite.

These are the ONLY axiom callees the proof consumes, and they are
*version-independent* IEEE-754 / NumPy primitives -- so the axiom-soundness
check (`check_infinity_primitives`) is UNCONDITIONAL and patch-state-independent:
it determines the exit code and validates exactly what the two @ContractOnly
axioms claim, in any container.

Separately, as a faithfulness corroboration (NOT an axiom obligation), we also
exercise the REAL `roc_curve` end-to-end and confirm it prepends an infinite
leading threshold with a finite tail -- i.e. the gold transformation the F2P
test pins (`np.isinf(thresholds[0])`). But `roc_curve` is the FUNCTION UNDER
SPECIFICATION, not an axiom callee, so its observed behaviour is patch-state
dependent: the eval image ships PRE-PATCH sklearn (where the leading threshold
is the finite `max(y_score) + 1`), and the gold-applied state yields `np.inf`.
This end-to-end leg is therefore GATED on detected patch presence -- run in full
when the in-container sklearn is the post-patch (gold) build, skipped with an
explicit notice otherwise. It NEVER fails the axiom check in a pre-patch
container; the function-under-spec end-to-end correctness is G-RESOLVE's job,
not G-AX's.

Imports nothing repo-private: `numpy` and `sklearn.metrics.roc_curve` are the
very modules/symbols the patched code uses. Exit 0 iff the (unconditional)
axiom obligations hold.
"""
import random
import sys

import numpy as np
from sklearn.metrics import roc_curve


# --- (A-consumed) pos_inf / is_pos_inf primitives ----------------------------
# These ARE the axiom callees. Patch-state-independent; determine the exit code.

def check_infinity_primitives():
    """is_pos_inf(pos_inf()) -- the axiom's Ensures -- holds on the real NumPy
    primitives: np.inf is infinite, and it is the positive sentinel.

    This is the load-bearing axiom-soundness obligation, validated against the
    real callees the model abstracts (np.inf / np.isinf). It is independent of
    whether the in-container sklearn is patched -- np.inf and np.isinf are
    unchanged by the patch."""
    assert np.isinf(np.inf), "np.isinf(np.inf) must be True (pos_inf axiom)"
    assert np.inf > 0, "np.inf must be the POSITIVE infinity sentinel"
    # a finite nudge of any score is NOT infinite (this is the pre-patch value
    # that the spec rejects; it must observably differ from the sentinel)
    for v in [-1e308, -1.0, 0.0, 0.5, 1.0, 1e308]:
        assert not np.isinf(v + 1.0), "finite + 1.0 must NOT be infinite"
    # is_pos_inf must NOT accept ordinary finite reals (so the pre-patch finite
    # anchoring value cannot masquerade as the sentinel)
    for v in [-1e308, -1.0, 0.0, 0.5, 1.0, 2.0, 1e9, 1e308]:
        assert not np.isinf(v), "finite real must NOT satisfy is_pos_inf"


# --- patch-state probe -------------------------------------------------------

def roc_curve_is_patched():
    """Return True iff the in-container roc_curve already prepends the infinite
    leading threshold (i.e. the gold/post-patch build). On the pre-patch build
    the leading threshold is the finite `max(y_score) + 1`, so this returns
    False. Used only to GATE the end-to-end faithfulness leg below -- never to
    relax the axiom obligations, which are checked unconditionally above."""
    try:
        _, _, thresholds = roc_curve([0, 1], [0.1, 0.9])
        return bool(np.isinf(thresholds[0]))
    except Exception:
        return False


# --- the real roc_curve: leading threshold is infinite, the rest finite ------
# Faithfulness corroboration of the function UNDER SPEC -- gated on gold being
# applied; this is NOT an axiom obligation (roc_curve is not an axiom callee).

def check_roc_curve_leading_infinite(y_true, y_score):
    """Assert the REAL (post-patch) roc_curve prepends an INFINITE leading
    threshold and that every remaining threshold is finite (the unchanged
    scores)."""
    fpr, tpr, thresholds = roc_curve(y_true, y_score)
    assert len(thresholds) >= 1, "roc_curve returned no thresholds"
    # the load-bearing F2P observation: the anchoring (first) threshold is +inf
    assert np.isinf(thresholds[0]), (
        "roc_curve leading threshold is not infinite for "
        "y_true=%r y_score=%r: thresholds=%r" % (y_true, y_score, thresholds))
    assert thresholds[0] > 0, "leading threshold must be POSITIVE infinity"
    # every remaining threshold is one of the finite input scores (the tail is
    # the unchanged descending distinct scores)
    for t in thresholds[1:]:
        assert np.isfinite(t), (
            "non-leading threshold unexpectedly infinite for "
            "y_true=%r y_score=%r: thresholds=%r" % (y_true, y_score, thresholds))


def run_roc_curve_endtoend_leg():
    """Exercise the real post-patch roc_curve over boundary + the F2P fixture +
    fuzz. Caller guarantees gold is applied (roc_curve_is_patched())."""
    # --- boundary cases over score scale ---------------------------------
    boundary = [
        # probability estimates (the reported regression): all scores in [0, 1]
        ([0, 1], [0.1, 0.9]),
        ([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]),
        ([0, 1, 1, 0], [0.2, 0.2, 0.8, 0.8]),     # ties
        ([0, 1], [1.0, 0.0]),                      # extreme probabilities
        ([0, 1], [0.5, 0.5]),                      # all-equal scores
        # the F2P drop_intermediate fixtures
        ([0, 0, 0, 0, 1, 1], [0.0, 0.2, 0.5, 0.6, 0.7, 1.0]),
        ([0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
         [0.0, 0.1, 0.6, 0.6, 0.7, 0.8, 0.9, 0.6, 0.7, 0.8, 0.9, 0.9, 1.0]),
        # confidence scores that can exceed 1 (the old code "happened" to work)
        ([0, 1, 0, 1], [-2.0, 5.0, 0.3, 3.0]),
        # large-magnitude scores (max + 1 would still be finite here too)
        ([0, 1], [1e9, -1e9]),
    ]
    for y_true, y_score in boundary:
        check_roc_curve_leading_infinite(y_true, y_score)

    # --- the exact F2P non-regression fixture (seed 42) -------------------
    rng = np.random.RandomState(42)
    y_true = rng.randint(0, 2, size=10)
    y_score = rng.rand(10)
    check_roc_curve_leading_infinite(y_true, y_score)

    # --- randomized fuzz: probability estimates and arbitrary scores ------
    rng = random.Random(26194)
    n_fuzz = 5000
    for _ in range(n_fuzz):
        n = rng.randint(2, 30)
        # ensure both classes present so roc_curve is non-degenerate
        y_true = [0, 1] + [rng.randint(0, 1) for _ in range(n - 2)]
        rng.shuffle(y_true)
        mode = rng.randint(0, 2)
        if mode == 0:        # probability estimates in [0, 1]
            y_score = [rng.random() for _ in range(len(y_true))]
        elif mode == 1:      # confidence scores possibly > 1 or < 0
            y_score = [rng.uniform(-10.0, 10.0) for _ in range(len(y_true))]
        else:                # large magnitudes
            y_score = [rng.uniform(-1e6, 1e6) for _ in range(len(y_true))]
        check_roc_curve_leading_infinite(np.array(y_true), np.array(y_score))
    return len(boundary), n_fuzz


def main():
    # UNCONDITIONAL axiom obligation: validates pos_inf / is_pos_inf against the
    # real, version-independent NumPy primitives. Determines the exit code in
    # any container, pre- or post-patch.
    check_infinity_primitives()
    print("G-AX OK (axioms): pos_inf/is_pos_inf sound on real numpy "
          "(np.isinf(np.inf) True, np.inf>0, finite/finite+1.0 not infinite).")

    # Faithfulness corroboration of the function under spec (roc_curve) -- gated
    # on the in-container sklearn already being the gold/post-patch build, since
    # roc_curve is the function UNDER SPECIFICATION, not an axiom callee, and the
    # eval image ships pre-patch.
    if roc_curve_is_patched():
        n_boundary, n_fuzz = run_roc_curve_endtoend_leg()
        print("G-AX OK (faithfulness leg): real (post-patch) roc_curve leading "
              "threshold is +inf on %d boundary + 1 F2P fixture + %d fuzz "
              "inputs; all remaining thresholds finite."
              % (n_boundary, n_fuzz))
    else:
        print("G-AX NOTICE: in-container roc_curve is PRE-PATCH (leading "
              "threshold finite max+1); end-to-end faithfulness leg skipped. "
              "This is expected on the default (apply_gold=False) container; the "
              "axiom obligations above are patch-state-independent and passed. "
              "End-to-end post-patch correctness is verified by G-RESOLVE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
