#!/usr/bin/env python3
"""G-CONF differential conformance for scikit-learn__scikit-learn-13439.

Refutes the R/I refinement leg (A2: `return steps.length` ↔ `return
len(self.steps)`). SHADOW = `len(steps)` (the transliterated impl over the real
type); ORACLE = the patched `Pipeline.__len__` applied to a real Pipeline of the
same stage count. They must agree on every input. Exit 0 iff zero
disagreements. Runs in-container with the gold patch applied; stdlib only.
"""
import random
import sys

SEED = 13439
N_FUZZ = 100_000


def shadow_len(n_stages):
    """compositeSize transliterated: the cardinality of the stage collection."""
    return n_stages  # steps.length, where steps has n_stages elements


def make_pipeline_of_length(n):
    """Build a real sklearn Pipeline with n passthrough stages, then call the
    patched __len__ (the oracle)."""
    from sklearn.pipeline import Pipeline
    steps = [(f"s{i}", "passthrough") for i in range(n)]
    # Pipeline requires >=1 step and the last to be an estimator-or-passthrough;
    # 'passthrough' is accepted for all positions in this version.
    if n == 0:
        # len of an empty pipeline: Pipeline disallows 0 steps, so the
        # cardinality-0 case is vacuous for the real type; shadow handles it.
        return None
    return Pipeline(steps)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    # boundary + fuzz over plausible pipeline sizes
    sizes = [1, 2, 3, 5, 10] + [rng.randint(1, 40) for _ in range(N_FUZZ)]
    for n in sizes:
        count += 1
        pipe = make_pipeline_of_length(n)
        if pipe is None:
            continue
        oracle = len(pipe)            # patched Pipeline.__len__
        shadow = shadow_len(n)        # compositeSize R/I shadow
        if oracle != shadow:
            disagreements.append((n, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r" % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of compositeSize agrees with patched "
          "Pipeline.__len__ on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
