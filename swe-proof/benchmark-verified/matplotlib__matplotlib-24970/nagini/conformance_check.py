#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-24970 (nagini).

SHADOW: the impl region of model.py `take_rows`, copied VERBATIM below with
the contract statement lines (Requires/Ensures/Invariant/Assert) stripped —
the model IS Python. The impl region uses plain List[int]/List[bool] only
(ToSeq/PSeq appear solely inside the stripped ghost lines), so no sequence
shim is needed. The one @ContractOnly callee, `assign_special_rows`, is
realized by the REAL repo operation it models per mapping.md section 1: the
three sequential conditional stores over the integer array followed by the
`mode='clip'` row gather, carried out on a container that admits every
special index written (the widened signed-int carrier that corresponds to
`modulus >= n + 3` per mapping.md section 2). The realization also checks
the callee's well-definedness effect: on an admitting container the stores
complete with no out-of-bound-integer DeprecationWarning.

ORACLE: the REAL patched repo function the model models per mapping.md —
`matplotlib.colors.Colormap.__call__` (the integer index-resolution stage).
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched module importable. Each element's
final lookup-table row is recovered from the returned RGBA values via a
colormap whose N + 3 lookup rows are pairwise distinct (asserted), so the
RGBA -> row-index map is a bijection.

TYPE BRIDGE (mapping.md section 2):
  values: List[int]   <-> the per-element integer values of the input array
                          (integer inputs; the modeled stage is the integer
                          index-resolution pipeline)
  bads:   List[bool]  <-> the input's bad/masked mask (driven via a masked
                          array on the oracle side)
  n: int              <-> Colormap.N (number of ordinary colour rows)
  modulus: int        <-> the range of values the INPUT integer container
                          admits (an m-bit unsigned dtype <-> 2**m); each
                          case picks a real input dtype that represents all
                          of its values and passes that dtype's range as
                          `modulus` — the shadow's result must be
                          independent of it (the impl widens internally)
  row result          <-> which of the N + 3 lookup rows each element's
                          RGBA was gathered from

EFFECT OBSERVABLE: the model requires the result to be produced by a
COMPLETING special-row assignment (one whose container admits every special
index it writes). On the oracle side that means the patched call emits no
out-of-bound-integer DeprecationWarning for ANY input integer dtype,
including narrow ones; a DeprecationWarning from the oracle is therefore
recorded as a disagreement.

Exit 0 iff zero disagreements over the boundary cases + 100000 fuzzed
Requires-satisfying inputs. Pinned seed: 24970001. stdlib + numpy +
matplotlib (the repo under test) only.
"""
import random
import sys
import warnings

import numpy as np

SEED = 24970001
N_FUZZ = 100_000


# ---------------------------------------------------------------------------
# @ContractOnly callee `assign_special_rows`, realized by the REAL repo
# operation it models (mapping.md section 1): the per-element special-row
# stores over the integer array, then the mode='clip' row gather. The carrier
# is the widened signed-int container (admits every special index written),
# which is the realization of `modulus >= n + 3`. The gather uses an index
# table of n + 3 rows, so the clip range is 0 .. n + 2 exactly as the
# real row gather over the (n + 3)-row lookup table.
# ---------------------------------------------------------------------------


def assign_special_rows(values, bads, n, modulus):
    assert modulus >= n + 3, "callee precondition (admitting container)"
    xa = np.array(values, dtype=int)          # widened carrier
    mask_bad = np.array(bads, dtype=bool)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        xa[xa > n - 1] = n + 1                # over-range row
        xa[xa < 0] = n                        # under-range row
        xa[mask_bad] = n + 2                  # bad/masked row (last, wins)
        rows = np.arange(n + 3).take(xa, mode='clip')
    dep = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    # Well-definedness effect: an admitting container completes the stores
    # with no out-of-bound-integer deprecation (the token-granting condition).
    assert not dep, "admitting container unexpectedly warned: %r" % dep
    return [int(r) for r in rows]


# ---------------------------------------------------------------------------
# model.py impl region (take_rows), VERBATIM with the contract statement
# lines (Requires/Ensures/Invariant/Assert) stripped.
# ---------------------------------------------------------------------------


def take_rows(values, bads, n, modulus):
    # Build the per-element special-row assignment input-by-input, mirroring the
    # element-wise array operation, then carry it out on a container that admits
    # every special index it writes. The special indices are the under-range row
    # (n), the over-range row (n + 1) and the bad/masked row (n + 2); the largest
    # is the bad row at n + 2, so a container admitting 0 .. n + 2 (range n + 3)
    # admits the whole assignment -- the input's own container may be narrower.
    sel_values = []  # type: list
    sel_bads = []  # type: list
    i = len(values)
    while i > 0:
        v = values[i - 1]
        bad = bads[i - 1]
        sel_values = [v] + sel_values
        sel_bads = [bad] + sel_bads
        i = i - 1
    carrier = n + 3
    result = assign_special_rows(sel_values, sel_bads, n, carrier)
    return result


# ---------------------------------------------------------------------------
# Oracle: the REAL patched Colormap.__call__, with per-element rows recovered
# from the RGBA output via a colormap whose n + 3 lookup rows are pairwise
# distinct.
# ---------------------------------------------------------------------------

_CMAP_CACHE = {}


def get_cmap_and_rowmap(n):
    got = _CMAP_CACHE.get(n)
    if got is not None:
        return got
    from matplotlib.colors import ListedColormap
    colors = [((i + 1) / (n + 4), 0.0, 0.25) for i in range(n)]
    cm = ListedColormap(colors)
    cm.set_under((0.0, 0.3, 0.6))
    cm.set_over((0.0, 0.55, 0.6))
    cm.set_bad((0.0, 0.8, 0.6))
    cm(np.array([0]))                         # force lookup-table init
    rowmap = {}
    for idx, row in enumerate(cm._lut):
        rowmap[tuple(float(x) for x in row)] = idx
    assert len(rowmap) == n + 3, "lookup rows not distinct for n=%d" % n
    _CMAP_CACHE[n] = (cm, rowmap)
    return cm, rowmap


def oracle_rows(values, bads, n, dtype, scalar=False):
    """Drive the real patched function; return (per-element rows, warned).
    `warned` is True iff an out-of-bound-integer DeprecationWarning was
    emitted — the effect the model forbids for a completing assignment."""
    cm, rowmap = get_cmap_and_rowmap(n)
    if scalar:
        X = dtype(values[0])
        if bads[0]:
            X = np.ma.array(X, mask=True)
    else:
        arr = np.array(values, dtype=dtype)
        if any(bads):
            X = np.ma.array(arr, mask=list(bads))
        else:
            X = arr
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        rgba = cm(X)
    warned = any(issubclass(w.category, DeprecationWarning) for w in caught)
    flat = np.asarray(rgba, dtype=float).reshape(-1, 4)
    rows = [rowmap[tuple(float(x) for x in r)] for r in flat]
    return rows, warned


# ---------------------------------------------------------------------------
# Input generation: Requires-satisfying (len(values)==len(bads), n>=1,
# modulus>=1) cases. Each case picks a REAL input integer dtype that
# represents every value; its range is the case's `modulus`.
# ---------------------------------------------------------------------------

DTYPES = [np.uint8, np.int8, np.uint16, np.int16, np.int32, np.int64]


def dtype_range(dtype):
    info = np.iinfo(dtype)
    return int(info.min), int(info.max)


def fitting_dtypes(values):
    out = []
    for dt in DTYPES:
        lo, hi = dtype_range(dt)
        if all(lo <= v <= hi for v in values):
            out.append(dt)
    return out


def gen_case(rng):
    n = rng.randint(1, 320)
    length = rng.randint(0, 8)
    values = []
    for _ in range(length):
        r = rng.random()
        if r < 0.05:
            values.append(rng.choice([-(2 ** 20), 2 ** 20, 2 ** 33, -(2 ** 33)]))
        else:
            values.append(rng.randint(-10, n + 15))
    bads = [rng.random() < 0.2 for _ in range(length)]
    dts = fitting_dtypes(values)
    dtype = rng.choice(dts)
    return values, bads, n, dtype, False


def boundary_cases():
    # the exact F2P shape: a scalar value-0 element of the narrowest unsigned
    # container at the default table size
    yield ([0], [False], 256, np.uint8, True)
    yield ([0], [False], 256, np.int64, True)
    yield ([0], [True], 256, np.uint8, True)      # masked scalar
    yield ([0], [False], 255, np.uint8, True)
    yield ([255], [False], 256, np.uint8, False)
    yield ([0, 5, 300, -2], [False, True, False, False], 256, np.int64, False)
    yield ([], [], 256, np.uint8, False)          # empty array
    yield ([0], [False], 1, np.uint8, False)      # smallest table
    yield ([-1, 0, 1, 2, 3], [False] * 5, 1, np.int8, False)
    yield ([126, 127], [False, True], 125, np.int8, False)
    yield ([0, 1], [True, True], 2, np.uint8, False)
    yield ([65535, 0], [False, False], 300, np.uint16, False)
    yield ([-(2 ** 33), 2 ** 33], [False, False], 256, np.int64, False)
    yield ([n_ % 7 for n_ in range(8)], [b % 2 == 0 for b in range(8)],
           5, np.uint8, False)


def main():
    rng = random.Random(SEED)
    disagreements = []
    checked = 0

    cases = list(boundary_cases())
    cases += [gen_case(rng) for _ in range(N_FUZZ)]

    for values, bads, n, dtype, scalar in cases:
        lo, hi = dtype_range(dtype)
        modulus = hi - lo + 1
        checked += 1
        shadow = take_rows(list(values), list(bads), n, modulus)
        oracle, warned = oracle_rows(values, bads, n, dtype, scalar=scalar)
        if shadow != oracle or warned:
            disagreements.append(
                (values, bads, n, np.dtype(dtype).name, scalar,
                 shadow, oracle, warned))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), checked, SEED))
        for vals, bads, n, dt, sc, sh, orc, wd in disagreements:
            print("  values=%r bads=%r n=%d dtype=%s scalar=%s\n"
                  "    shadow=%r\n    oracle=%r  deprecation_warned=%s"
                  % (vals, bads, n, dt, sc, sh, orc, wd))
        return 1
    print("G-CONF OK: model.py impl shadow (real-store callee on the "
          "admitting carrier) agrees with the patched Colormap.__call__ "
          "row selection on %d inputs (seed=%d), 0 disagreements, "
          "0 out-of-bound-integer deprecations." % (checked, SEED))
    import json
    print(json.dumps({
        "checked": checked, "disagreements": 0, "seed": SEED,
        "shadow": "contract-stripped take_rows impl region; @ContractOnly "
                  "assign_special_rows realized by the real store+clip-gather "
                  "operation on the admitting carrier"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
