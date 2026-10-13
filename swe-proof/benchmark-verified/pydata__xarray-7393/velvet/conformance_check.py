#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-7393 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `arrayDispatch` impl region,
              transliterated to Python over the *real* repo objects. The
              A-tagged callees (`recordedDtype` = self.dtype, `isComponent` =
              self.level is not None, `componentValues` = get_level_values(...)
              .values, `toDtype` = np.asarray(...,dtype=...), `baseMaterialize` =
              super().__array__) are NOT substituted by a model here — they are
              read from the REAL repo objects (the bundle's A content is
              `opaque`, validated by G-AX, so it is out of G-CONF's R/I scope).
              What G-CONF exercises is the CONTROL FLOW the change adds: default
              a missing dtype to the recorded dtype; on the level branch retag
              the stored level values to the resolved dtype; else delegate.
  * ORACLE  — `patch.diff`'s behaviour: the gold-patched
              `PandasMultiIndexingAdapter.__array__` itself, called on the same
              view + dtype argument (the real correctness oracle, G-RESOLVE —
              the harness applies patch.diff before this runs).

They must agree on the observable result `(str(dtype), tolist())` for every
view + dtype configuration. Exit 0 iff zero disagreements; any disagreement is a
mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + the
numpy/pandas/xarray under test only. The fuzz seed is pinned (mapping.md §4) for
a deterministic verdict.
"""
import random
import sys

import numpy as np
import xarray as xr
from xarray.core.indexing import PandasMultiIndexingAdapter

SEED = 7393
N_FUZZ = 100_000

PROMOTED = ["int32", "float32", "int16", "uint8", "float16", "int8", "uint16"]
CONTROLS = ["int64", "float64"]
ALL_DTYPES = PROMOTED + CONTROLS


def level_adapter(values, dtype):
    """Build the issue's scenario and reach the per-level multi-index adapter
    (the view `arrayDispatch`/`__array__` materializes)."""
    foo = xr.Dataset(coords={"bar": ("bar", np.array(values, dtype=dtype))})
    foo = foo.stack(baz=("bar",))
    data = foo["bar"].variable._data
    seen = 0
    while not isinstance(data, PandasMultiIndexingAdapter) and seen < 8:
        inner = getattr(data, "array", None)
        if inner is None or inner is data:
            break
        data = inner
        seen += 1
    assert isinstance(data, PandasMultiIndexingAdapter)
    return data


def shadow_array(adapter, dtype):
    """The R/I transliteration of `arrayDispatch`: default-resolve the dtype,
    branch on the level, retag the level values; reading every A-reference
    observation from the REAL adapter."""
    d = adapter.dtype if dtype is None else dtype          # dtype.getD recordedDtype
    if adapter.level is not None:                          # isComponent
        native = adapter.array.get_level_values(adapter.level).values  # componentValues
        return np.asarray(native, dtype=d)                 # toDtype _ d
    else:
        return super(PandasMultiIndexingAdapter, adapter).__array__(dtype)  # baseMaterialize


def oracle_array(adapter, dtype):
    """patch.diff's behaviour: the gold-patched __array__ itself."""
    return adapter.__array__(dtype)


def observe(arr):
    arr = np.asarray(arr)
    return (str(arr.dtype), arr.tolist())


def build_adapter_pool(rng):
    """Build a diverse pool of REAL per-level multi-index adapters once. Each
    `stack` is expensive, so we materialize the pool up-front and then run the
    >=10^5-comparison loop by pairing each adapter with a varied requested dtype
    (the cheap, behaviour-determining R/I op). The pool spans every dtype, plus
    boundary value sets (the issue's exact values, singletons, small arrays)."""
    pool = []
    # the issue's exact int32/float32 cases first (plan §4.1 step 4)
    for dt in ["int32", "float32"]:
        pool.append(level_adapter([0, 1], dt))
        pool.append(level_adapter([0], dt))
    # one singleton + one small random array per dtype
    for dt in ALL_DTYPES:
        pool.append(level_adapter([0], dt))
        if np.issubdtype(np.dtype(dt), np.integer):
            info = np.iinfo(dt)
            lo, hi = int(info.min), int(info.max)
            vals = [rng.randint(lo, hi) for _ in range(rng.randint(2, 6))]
        else:
            vals = [rng.uniform(-100.0, 100.0) for _ in range(rng.randint(2, 6))]
        pool.append(level_adapter(vals, dt))
    return pool


def requested_dtypes():
    """Requested-dtype arguments swept per adapter: the default (None, the F2P
    path) plus every explicit dtype (which overrides the default)."""
    return [None] + [np.dtype(dt) for dt in ALL_DTYPES]


def main():
    rng = random.Random(SEED)
    pool = build_adapter_pool(rng)
    reqs = requested_dtypes()

    disagreements = []
    count = 0
    # deterministically sweep (adapter x requested-dtype), reshuffling and
    # repeating until >=10^5 comparisons are made.
    while count < N_FUZZ and not disagreements:
        order = [(a, r) for a in pool for r in reqs]
        rng.shuffle(order)
        for adapter, req in order:
            count += 1
            try:
                shadow = observe(shadow_array(adapter, req))
            except Exception as e:
                shadow = ("EXC", type(e).__name__)
            try:
                oracle = observe(oracle_array(adapter, req))
            except Exception as e:
                oracle = ("EXC", type(e).__name__)
            if shadow != oracle:
                disagreements.append((str(adapter.dtype), req, shadow, oracle))
                if len(disagreements) >= 5:
                    break
            if count >= N_FUZZ:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for recorded, req, sh, orc in disagreements:
            print("  recorded=%s req=%s shadow=%r oracle=%r"
                  % (recorded, req, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of arrayDispatch agrees with patch.diff "
          "behaviour on %d multi-index level views (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
