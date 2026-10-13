#!/usr/bin/env python3
"""G-CONF for sympy__sympy-20154.

Differential test: the R/I Python shadow of `implementation_partitions`
(Solution.lean) vs. the REAL patched generator `partitions` in
`sympy/utilities/iterables.py`. The orchestrator applies the gold patch before
running this, so the imported `partitions` is the fixed (copy-on-yield) version.

Model (mapping.md): the partition-generation algorithm is UNCHANGED by the
patch, so its produced sequence of partition *values* is the abstract input
carrier `states`. We capture that ground-truth sequence independently of the
patch by snapshotting each yielded dict ourselves at consume time:

    states = [dict(p) for p in partitions(*args)]   # per-step true values

The shadow of `implementation_partitions` is the identity materialization
`result = states` (each step emits its own current value). The patched repo's
plain materialization `list(partitions(*args))` must equal that — i.e. the
fixed generator hands out one independent snapshot per yield, in order.

(The pre-patch generator yields the *same* object every step, so
`list(partitions(...))` would collapse to N references to the final partition —
unequal to `states`. That is the bug; this check confirms the patched repo no
longer exhibits it, and that the shadow models the fixed behavior.)

Type bridge (mapping.md): one partition dict ↔ `List (Nat × Nat)`; the produced
sequence ↔ `states : List PartMap`; `list(partitions(...))` ↔ `result`.

Exit 0 iff zero disagreements over >=1e5 fuzzed (n, m, k) cases. stdlib + sympy.
"""
import random
import sys

from sympy.utilities.iterables import partitions

SEED = 20154
N_CASES = 100_000


def shadow(states):
    """R/I transliteration of implementation_partitions (Solution.lean):
    identity materialization — emit each produced state as its own entry."""
    out = []
    for s in states:
        out.append(s)
    return out


def gen_args(rng):
    n = rng.randint(1, 40)
    m = rng.choice([None] + list(range(1, n + 1)))
    k = rng.choice([None] + list(range(1, n + 1)))
    return n, m, k


def main():
    rng = random.Random(SEED)
    mismatches = 0
    first = None
    for _ in range(N_CASES):
        n, m, k = gen_args(rng)
        # ground-truth produced-value sequence: snapshot each yield ourselves
        states = [dict(p) for p in partitions(n, m=m, k=k)]
        model_result = shadow(states)
        # the real patched materialization
        real_result = [p for p in partitions(n, m=m, k=k)]
        if model_result != real_result:
            mismatches += 1
            if first is None:
                first = {"n": n, "m": m, "k": k,
                         "model": model_result, "real": real_result}
    if mismatches:
        print(f"G-CONF FAIL: {mismatches}/{N_CASES} disagreements; first={first}")
        sys.exit(1)
    print(f"G-CONF PASS: 0/{N_CASES} disagreements (seed {SEED})")
    sys.exit(0)


if __name__ == "__main__":
    main()
