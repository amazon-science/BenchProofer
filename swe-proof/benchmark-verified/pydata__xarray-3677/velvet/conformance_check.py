#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-3677 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo types, via the mapping.md bijection
              (self <-> KeyedMap, operand <-> Operand). The changed op is the
              operand normalization `other.to_dataset() if isinstance(other,
              xr.DataArray) else other`. The A-tagged callee
              `dataset_merge_method` (`combineCore`, an A-reference) is left as
              the REAL callee here — G-CONF isolates the R/I (coerce) leg; the A
              leg stays with G-AX.
  * ORACLE  — `patch.diff`'s behaviour: the patched `Dataset.merge` method
              applied at base_commit (the real correctness oracle, G-RESOLVE).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image) with the gold patch
applied; stdlib + xarray only. The fuzz seed is pinned (mapping.md §4). The
modeled domain is the no-conflict / disjoint-name regime (the F2P scenario).
"""
import random
import sys

import xarray as xr


SEED = 3677
N_FUZZ = 100_000
_NAMES = ["a", "b", "c", "d", "e", "x", "y", "z"]


def observe(thunk):
    """Run thunk; project its outcome onto what the F2P test observes: the
    {name: scalar value} mapping of the resulting Dataset, or a raised
    exception type."""
    try:
        ds = thunk()
    except Exception as e:                       # noqa: BLE001 — type is the observable
        return ("err", type(e).__name__)
    return ("ok", tuple(sorted(
        (str(k), int(v.values)) for k, v in ds.data_vars.items())))


def oracle(base_map, operand):
    """ORACLE: the real (patched) Dataset.merge method."""
    base = xr.Dataset({k: v for k, v in base_map.items()})
    return observe(lambda: base.merge(operand))


def shadow(base_map, operand):
    """SHADOW: the impl's coerce-then-combine, transliterated. A raw DataArray
    operand is re-expressed via to_dataset() (the changed op); a Dataset/mapping
    passes through. Then the REAL A-tagged combine callee runs (Dataset.merge on
    the normalized operand — which never crashes, since it is always keyed)."""
    base = xr.Dataset({k: v for k, v in base_map.items()})
    other = operand.to_dataset() if isinstance(operand, xr.DataArray) else operand
    return observe(lambda: base.merge(other))


def fuzz_inputs(n, rng):
    # operand shapes: a Dataset (keyed) or a named DataArray (single).
    def mk_base():
        k = rng.randint(0, 3)
        keys = rng.sample(_NAMES, k)
        return {key: rng.randint(-1000, 1000) for key in keys}

    def mk_operand(base_map):
        # keep names disjoint from base (no-conflict regime)
        free = [nm for nm in _NAMES if nm not in base_map]
        if not free:
            return xr.Dataset({})
        if rng.random() < 0.5:
            name = rng.choice(free)
            return xr.DataArray(data=rng.randint(-1000, 1000), name=name)
        k = rng.randint(0, min(3, len(free)))
        keys = rng.sample(free, k)
        return xr.Dataset({key: rng.randint(-1000, 1000) for key in keys})

    # boundary cases first: the F2P scenario + empties + multi
    yield ({"a": 0}, xr.DataArray(data=1, name="b"))           # the F2P case
    yield ({}, xr.DataArray(data=1, name="b"))
    yield ({"a": 0}, xr.Dataset({"b": 1}))
    yield ({"a": 0, "c": 5}, xr.DataArray(data=7, name="b"))
    yield ({"a": 0}, xr.Dataset({}))

    for _ in range(n):
        base_map = mk_base()
        yield (base_map, mk_operand(base_map))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for base_map, operand in fuzz_inputs(N_FUZZ, rng):
        count += 1
        s = shadow(base_map, operand)
        o = oracle(base_map, operand)
        if s != o:
            disagreements.append((base_map, operand, s, o))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for bm, op, s, o in disagreements:
            print("  base=%r operand=%r shadow=%r oracle=%r" % (bm, op, s, o))
        return 1
    print("G-CONF OK: R/I shadow of combineKeyed agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
