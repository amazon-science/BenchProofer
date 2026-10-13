#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-7229 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `rebuildAttrs` impl region
              transliterated to Python over the *real* xarray types, via the
              mapping.md bijection (Obj/Lvl ↔ result object/level,
              getattr(...,"attrs",{}) ↔ lookupAttrs, {} ↔ 0). The result
              SKELETON (level names + output type + the promotion flag) is the
              unchanged `apply_ufunc` callee's output (A1/R input); the shadow
              obtains it from `xr.where(..., keep_attrs=False)` — the same call
              with metadata dropped — and then rebuilds each level's metadata by
              the deep model (rebuiltGlobal / rebuiltVar / rebuiltCoord). There
              are NO A-tagged callees inside the computed metadata, so the
              shadow is pure R/I (conf_skip=false).
  * ORACLE  — `patch.diff`'s behaviour: the patched `xr.where(..., keep_attrs=
              True)` applied at base_commit (the real correctness oracle,
              G-RESOLVE).

They must agree on the per-level `.attrs` of every output level for every input.
Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample. Runs in-container (the prebuilt SWE-Bench instance image);
imports only the repo package `xarray` (+ numpy). Fuzz seed pinned (mapping.md
§4) for a deterministic verdict.
"""
import random
import sys

import numpy as np
import xarray as xr
from xarray import DataArray, Dataset

SEED = 7229
N_FUZZ = 100_000


# --- the R/I shadow: rebuildAttrs transliterated -----------------------------

def _is_ds(o):
    return isinstance(o, Dataset)


def shadow_level_attrs(cond, x, y):
    """Predict {('global'|'var'|'coord', name) -> attrs dict} for the output,
    using the result skeleton (names/type) from apply_ufunc (keep_attrs=False)
    and the deep by-name rebuild model. This is the R/I shadow of rebuildAttrs."""
    skeleton = xr.where(cond, x, y, keep_attrs=False)        # apply_ufunc skeleton
    promote = _is_ds(y) and not _is_ds(x)
    x_name = getattr(x, "name", None)

    out = {}
    # rebuiltGlobal
    out[("global", None)] = {} if promote else dict(getattr(x, "attrs", {}) or {})
    # rebuiltVar over the skeleton's data_vars
    for v in list(getattr(skeleton, "data_vars", [])):
        if promote:
            out[("var", v)] = (dict(getattr(x, "attrs", {}) or {})
                               if v == x_name else dict(skeleton[v].attrs))
        else:
            out[("var", v)] = dict(getattr(getattr(x, v, None), "attrs", {}) or {})
    # rebuiltCoord over the skeleton's coords (ALWAYS by-name)
    for c in list(getattr(skeleton, "coords", [])):
        out[("coord", c)] = dict(getattr(getattr(x, c, None), "attrs", {}) or {})
    return out


def oracle_level_attrs(cond, x, y):
    """patch.diff's behaviour: the patched xr.where(keep_attrs=True)."""
    result = xr.where(cond, x, y, keep_attrs=True)
    out = {("global", None): dict(result.attrs)}
    for v in list(getattr(result, "data_vars", [])):
        out[("var", v)] = dict(result[v].attrs)
    for c in list(getattr(result, "coords", [])):
        out[("coord", c)] = dict(result[c].attrs)
    return out


# --- input construction (mirrors the F2P matrix + randomized fuzz) -----------

_KEYS = ["attr", "long_name", "units", "standard_name", "k1", "k2"]
_VALS = ["a", "b", "cond_da", "x_da", "y_da", "x_coord", "y_coord", "deg", 1, 2, 7]


def rattrs(rng, n_max=3):
    n = rng.randint(0, n_max)
    keys = rng.sample(_KEYS, min(n, len(_KEYS)))
    return {k: rng.choice(_VALS) for k in keys}


def da(rng, vals, name=None):
    # coord "a" is the (single) dimension coordinate — mirrors boundary_inputs
    # (which omit `dims`, so the coord defines the dim). Passing dims="x" with a
    # coord named "a" is rejected by DataArray (coord not a subset of dims).
    d = DataArray(vals, coords={"a": [0, 1]}, attrs=rattrs(rng), name=name)
    d["a"].attrs = rattrs(rng)
    return d


def boundary_inputs():
    cond = DataArray([True, False], coords={"a": [0, 1]}, attrs={"attr": "cond_da"})
    cond["a"].attrs = {"attr": "cond_coord"}
    x = DataArray([1, 1], coords={"a": [0, 1]}, attrs={"attr": "x_da"})
    x["a"].attrs = {"attr": "x_coord"}
    y = DataArray([0, 0], coords={"a": [0, 1]}, attrs={"attr": "y_da"})
    y["a"].attrs = {"attr": "y_coord"}
    yield cond, x, y, "3 DataArrays"
    yield cond, 0, y, "x scalar"
    yield cond, x, 0, "y scalar"
    yield cond, 1, 0, "x and y scalar"
    yield True, x, y, "cond scalar"
    ds_x = Dataset(data_vars={"x": x}, attrs={"attr": "x_ds"})
    ds_y = Dataset(data_vars={"x": y}, attrs={"attr": "y_ds"})
    yield cond, ds_x, ds_y, "DataArray + 2 Datasets"
    yield cond, x.rename("x"), ds_y, "2 DataArrays + 1 Dataset (promotion)"


def fuzz_inputs(rng, n):
    for _ in range(n):
        shape = rng.randint(0, 6)
        cond = da(rng, [True, False])
        x = da(rng, [1, 1])
        y = da(rng, [0, 0])
        if shape == 0:
            yield cond, x, y, "fuzz:3da"
        elif shape == 1:
            yield cond, rng.choice([0, 1, 5]), y, "fuzz:xscalar"
        elif shape == 2:
            yield cond, x, rng.choice([0, 1, 5]), "fuzz:yscalar"
        elif shape == 3:
            yield cond, rng.choice([0, 1]), rng.choice([0, 1]), "fuzz:bothscalar"
        elif shape == 4:
            yield True, x, y, "fuzz:condscalar"
        elif shape == 5:
            ds_x = Dataset(data_vars={"x": x}, attrs=rattrs(rng))
            ds_y = Dataset(data_vars={"x": y}, attrs=rattrs(rng))
            yield cond, ds_x, ds_y, "fuzz:da+2ds"
        else:
            ds_y = Dataset(data_vars={"x": y}, attrs=rattrs(rng))
            yield cond, x.rename("x"), ds_y, "fuzz:promotion"


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    def compare(cond, x, y, label):
        nonlocal count
        count += 1
        shadow = shadow_level_attrs(cond, x, y)
        oracle = oracle_level_attrs(cond, x, y)
        if shadow != oracle:
            disagreements.append((label, shadow, oracle))

    for cond, x, y, label in boundary_inputs():
        compare(cond, x, y, label)
    for cond, x, y, label in fuzz_inputs(rng, N_FUZZ):
        compare(cond, x, y, label)
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for label, sh, orc in disagreements:
            print("  case=%s shadow=%r oracle=%r" % (label, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of rebuildAttrs agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
