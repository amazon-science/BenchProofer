#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-6938 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `reifyIndependent` impl
              region transliterated to Python over an explicit dict-heap, via
              the mapping.md bijection (object identity ↔ integer Handle;
              `obj.dims` ↔ `store[handle]`). The deep allocation + slot copy:
                  r = next_fresh; store[r] = store[self]; next_fresh += 1; ret r
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `xarray.core.variable.IndexVariable.to_index_variable` applied to
              a real IndexVariable at base_commit-with-patch (the real
              correctness oracle, G-RESOLVE). Post-patch this is `self.copy()`.

For each fuzzed object both sides are reduced to the SAME observable signature
the F2P test cares about:
    (distinct_identity, dims_copied_at_call_time, source_unchanged_after_result_mutation)
They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + numpy +
the repo's own xarray. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

import numpy as np
from xarray.core.variable import IndexVariable

SEED = 6938
N_FUZZ = 100_000


def shadow_observable(dims_self):
    """R/I shadow of the `do` block over an explicit dict-heap.

    Returns the observable triple (distinct_identity, dims_copied,
    source_frame_preserved) the F2P test reads.
    """
    SELF = 0
    store = {SELF: tuple(dims_self)}
    next_fresh = 1

    # --- impl region, transliterated (I ops) ---
    r = next_fresh                       # let r := nextFresh   (fresh handle)
    store[r] = store[SELF]               # update store r (store self) (copy)
    next_fresh = next_fresh + 1          # bump frontier
    # return r

    distinct_identity = (r != SELF)
    dims_copied = (store[r] == tuple(dims_self))

    # mutate the RESULT's slot; the source slot must be untouched (disjoint).
    new_dims = tuple(str(d) + "_y" for d in store[r])
    store[r] = new_dims
    source_frame_preserved = (store[SELF] == tuple(dims_self))

    return (distinct_identity, dims_copied, source_frame_preserved)


def oracle_observable(dimname, values):
    """patch.diff behaviour: the real patched to_index_variable (== self.copy())."""
    iv = IndexVariable(dimname, list(values))
    dims_before = iv.dims

    out = iv.to_index_variable()         # patched callee

    distinct_identity = (out is not iv)
    dims_copied = (out.dims == dims_before)

    new_dims = tuple(str(d) + "_y" for d in out.dims)
    out.dims = new_dims
    source_frame_preserved = (iv.dims == dims_before)

    return (distinct_identity, dims_copied, source_frame_preserved)


def main():
    rng = random.Random(SEED)
    letters = list("abcdefghijklmnopqrstuvwxyz")

    # boundary first (incl. the exact F2P construction)
    boundary = [
        ("x", ["a"]),
        ("x", ["a", "b"]),
        ("x", []),
        ("time", [10, 20, 30]),
        ("z", list(np.arange(11) * 10)),
    ]

    n_checked = 0
    disagreements = 0

    def check(dimname, values):
        nonlocal n_checked, disagreements
        # The do-block's observable depends only on `dims_self` (the modeled
        # Payload); IndexVariable dims is the 1-tuple (dimname,).
        shadow = shadow_observable((dimname,))
        oracle = oracle_observable(dimname, values)
        n_checked += 1
        if shadow != oracle:
            disagreements += 1
            if disagreements <= 10:
                sys.stderr.write(
                    "DISAGREEMENT on dim=%r values=%r: shadow=%r oracle=%r\n"
                    % (dimname, values, shadow, oracle))

    for dimname, values in boundary:
        check(dimname, values)

    for _ in range(N_FUZZ):
        dimname = "".join(rng.choice(letters) for _ in range(rng.randint(1, 6)))
        n = rng.randint(0, 6)
        if rng.random() < 0.5:
            values = [rng.randint(-1000, 1000) for _ in range(n)]
        else:
            values = ["".join(rng.choice(letters)
                              for _ in range(rng.randint(1, 4)))
                      for _ in range(n)]
        check(dimname, values)

    if disagreements:
        sys.stderr.write(
            "G-CONF FAIL: %d/%d disagreements (seed=%d)\n"
            % (disagreements, n_checked, SEED))
        return 1

    print("G-CONF OK: R/I shadow of reifyIndependent agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (n_checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
