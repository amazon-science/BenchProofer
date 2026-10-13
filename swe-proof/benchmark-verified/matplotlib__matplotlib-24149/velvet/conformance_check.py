#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-24149 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's `selectReference` impl region, transliterated to
              Python over the real repo domain (a non-empty sequence of scalar
              floats, mapping.md §2). The A-reference ops (refinement.md ops 1-2)
              are left as the REAL repo callees:
                found  = cbook._safe_first_finite(xs)   (None if it raises
                         StopIteration — the `firstFinite -> none` leg)
                result = found  if found is not None
                         else cbook.safe_first_element(xs)   (the `getD` fallback)
              and the R op (op 3) wraps the result as a non-error outcome
              ('ok', result). This is the impl skeleton with A-callees real.

  * ORACLE  — patch.diff's behaviour, transliterated VERBATIM from the patched
              `_convert_dx` extraction block (gold lines):
                try:
                    val = cbook._safe_first_finite(xs)
                except (TypeError, IndexError, KeyError):
                    pass                      # (out of modeled domain here)
                except StopIteration:
                    val = cbook.safe_first_element(xs)
              The bound `val` and the fact that no exception escapes is the
              ('ok', val) the patch produces.

They must agree on every input: same outcome tag ('ok') and same selected float
(NaN-aware bit comparison). Exit 0 iff zero disagreements; any disagreement is a
mechanical R/I-fidelity counterexample.

Runs in-container (prebuilt SWE-Bench image, Agg backend), stdlib + matplotlib +
numpy only. Fuzz seed pinned (mapping.md §4) for a deterministic verdict.
"""
import math
import os
import random
import sys

os.environ.setdefault("MPLBACKEND", "Agg")

from matplotlib import cbook

SEED = 24149
N_FUZZ = 100_000

SENTINELS = [float("nan"), float("inf"), float("-inf"), 0.0, -0.0,
             1.0, -1.0, 1e308, -1e308, 3.14, -2.5]


# --- the R/I shadow: Solution.lean selectReference, A-ops left as real -------

def shadow_select(xs):
    """selectReference impl transliterated. A-reference callees (ops 1-2) are
    the REAL cbook routines; op 3 wraps the chosen value as ('ok', value)."""
    try:
        found = cbook._safe_first_finite(xs)   # firstFinite (A-ref); None if raises
    except StopIteration:
        found = None
    if found is not None:
        result = found
    else:
        result = cbook.safe_first_element(xs)  # firstElement (A-ref) — the getD leg
    return ("ok", result)


# --- the oracle: patch.diff's patched extraction block, verbatim -------------

def oracle_select(xs):
    """The gold-patched _convert_dx extraction block for one site, transliterated
    verbatim. Returns ('ok', bound_value) when no exception escapes."""
    val = xs                                   # placeholder (unused on this path)
    try:
        val = cbook._safe_first_finite(xs)
    except (TypeError, IndexError, KeyError):
        # out of modeled domain (non-empty float sequence never triggers these)
        pass
    except StopIteration:
        # the arm the patch adds: fall back to the first element unconditionally
        val = cbook.safe_first_element(xs)
    return ("ok", val)


def _outcome_eq(a, b):
    """Compare ('ok', float) outcomes with NaN-aware float equality."""
    if a[0] != b[0]:
        return False
    x, y = a[1], b[1]
    if isinstance(x, float) and isinstance(y, float):
        if math.isnan(x) and math.isnan(y):
            return True
    return x == y


def main():
    rng = random.Random(SEED)
    disagreements = 0
    first_cex = None

    # deterministic boundary battery first
    boundary = [
        [float("nan")],
        [float("nan"), float("nan")],
        [float("inf"), float("-inf")],
        [0.0],
        [1.0, 2.0, 3.0],
        [float("nan"), 5.0],
        [5.0, float("nan")],
        [float("nan"), float("nan"), 7.0],
    ]
    inputs = list(boundary)

    for _ in range(N_FUZZ):
        n = rng.randint(1, 8)
        if rng.random() < 0.25:
            pool = [float("nan"), float("inf"), float("-inf")]   # all-non-finite
        else:
            pool = SENTINELS + [rng.uniform(-1e6, 1e6)]
        inputs.append([rng.choice(pool) for _ in range(n)])

    for xs in inputs:
        s = shadow_select(list(xs))
        o = oracle_select(list(xs))
        if not _outcome_eq(s, o):
            disagreements += 1
            if first_cex is None:
                first_cex = (xs, s, o)

    if disagreements:
        print("G-CONF FAIL: %d disagreements; first counterexample: "
              "xs=%r shadow=%r oracle=%r" % (disagreements, *first_cex))
        return 1

    print("G-CONF OK: shadow(selectReference) == oracle(patch.diff) on %d "
          "inputs (%d boundary + %d fuzz), zero disagreements."
          % (len(inputs), len(boundary), N_FUZZ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
