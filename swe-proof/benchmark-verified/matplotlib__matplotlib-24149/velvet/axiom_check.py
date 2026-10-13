#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-24149 (plan §4.1).

Runs the REAL, UNCHANGED repo callees that Solution.lean models DEEPLY (as
A-references, refinement.md ops 1-2) on boundary + fuzzed float sequences, and
asserts every observation matches the deep model. No consumed axioms exist; the
three obligations are all A-reference / predicate equivalences:

  (A-reference) firstFinite xs == cbook._safe_first_finite(xs)        [default
      skip_nonfinite=True]. Deep model `firstFinite xs = xs.find? isFiniteVal`:
        - `some v` (first element with isFiniteVal true)  ⇔ the real call
          RETURNS v;
        - `none`  (no element is finite)                  ⇔ the real call
          RAISES StopIteration.
      (The empty-sequence and iterator / np.flatiter branches are OUT of the
      modeled domain — mapping.md §2 — and are not asserted here.)

  (A-reference) firstElement xs == cbook.safe_first_element(xs)
      (= _safe_first_finite(xs, skip_nonfinite=False) = first element
      unconditionally). Deep model `firstElement xs = xs.headD 0`: on a
      non-empty sequence, the head.

  (predicate) isFiniteVal x == safe_isfinite(x) == np.isfinite(x) on a scalar
      float. NaN, +inf, -inf -> False; every other double -> True.

Runs in-container (prebuilt SWE-Bench image, Agg backend), matplotlib + numpy +
stdlib only — the same modules the gold patch calls. Fuzz seed pinned
(mapping.md §4). Exit 0 iff every obligation holds; else assertion -> exit 1.
"""
import math
import os
import random
import sys

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np
from matplotlib import cbook

SEED = 24149


# --- deep models (kept in lock-step with Solution.lean pure region) ----------

def isFiniteVal(x):
    """Lean `Float.isFinite`: not NaN and not +/-inf."""
    return math.isfinite(x)


def firstFinite(xs):
    """Deep model `xs.find? isFiniteVal`: first finite element, or None."""
    for v in xs:
        if isFiniteVal(v):
            return v
    return None


def firstElement(xs):
    """Deep model `xs.headD 0`: head of a non-empty sequence."""
    return xs[0]


# --- the checks --------------------------------------------------------------

def _bits_eq(a, b):
    """Float equality that treats NaN == NaN (we compare *which element* was
    selected, and a selected NaN must match a selected NaN)."""
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) and math.isnan(b):
            return True
    return a == b


def check_first_finite(xs):
    """A-reference op 1: firstFinite(xs) vs the real _safe_first_finite(xs)."""
    model = firstFinite(xs)                       # None | value
    try:
        observed = cbook._safe_first_finite(xs)   # real callee, default flag
    except StopIteration:
        assert model is None, (
            "_safe_first_finite raised StopIteration on %r but deep model "
            "firstFinite gave %r (expected None)" % (xs, model))
        return
    assert model is not None, (
        "_safe_first_finite returned %r on %r but deep model firstFinite gave "
        "None (expected a raise)" % (observed, xs))
    assert _bits_eq(observed, model), (
        "first-finite mismatch on %r: real callee %r, deep model %r"
        % (xs, observed, model))


def check_first_element(xs):
    """A-reference op 2: firstElement(xs) vs the real safe_first_element(xs)."""
    model = firstElement(xs)
    observed = cbook.safe_first_element(xs)       # real callee
    assert _bits_eq(observed, model), (
        "first-element mismatch on %r: real callee %r, deep model %r"
        % (xs, observed, model))


def check_predicate(x):
    """isFiniteVal(x) vs numpy scalar finiteness (== safe_isfinite for floats)."""
    model = isFiniteVal(x)
    observed = bool(np.isfinite(x))
    assert model == observed, (
        "isFiniteVal mismatch on %r: model %r, np.isfinite %r"
        % (x, model, observed))


SENTINELS = [float("nan"), float("inf"), float("-inf"), 0.0, -0.0,
             1.0, -1.0, 1e308, -1e308, 3.14, -2.5]


def main():
    # --- predicate equivalence on the sentinels + fuzz --------------------
    for x in SENTINELS:
        check_predicate(x)

    rng = random.Random(SEED)

    def rand_elt():
        return rng.choice(SENTINELS + [rng.uniform(-1e6, 1e6)])

    for _ in range(20000):
        check_predicate(rand_elt())

    # --- boundary float sequences (non-empty, in modeled domain) ----------
    boundary = [
        [float("nan")],                       # the F2P case: all-nan, len 1
        [float("nan"), float("nan")],         # all-nan, len 2
        [float("inf"), float("-inf")],        # all-non-finite (infs)
        [float("nan"), float("inf")],
        [0.0],                                # finite, len 1
        [1.0, 2.0, 3.0],                      # all finite
        [float("nan"), 5.0],                  # first non-finite, then finite
        [5.0, float("nan")],                  # first finite
        [float("nan"), float("nan"), 7.0],
        [float("inf"), 2.0, float("nan")],
    ]
    for xs in boundary:
        check_first_finite(xs)
        check_first_element(xs)

    # --- randomized fuzz over List Float (lengths 1..8) -------------------
    n_seq = 0
    for _ in range(100000):
        n = rng.randint(1, 8)
        # bias toward all-non-finite sequences (the discriminating case)
        if rng.random() < 0.25:
            pool = [float("nan"), float("inf"), float("-inf")]
        else:
            pool = SENTINELS + [rng.uniform(-1e6, 1e6)]
        xs = [rng.choice(pool) for _ in range(n)]
        check_first_finite(xs)
        check_first_element(xs)
        n_seq += 1

    print("G-AX OK: firstFinite (== cbook._safe_first_finite) + firstElement "
          "(== cbook.safe_first_element) deep models and isFiniteVal predicate "
          "(== np.isfinite) sound on %d boundary + %d fuzz sequences and "
          "20000+ scalar fuzz." % (len(boundary), n_seq))
    return 0


if __name__ == "__main__":
    sys.exit(main())
