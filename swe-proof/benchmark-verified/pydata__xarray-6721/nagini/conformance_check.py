#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-6721 (nagini).

SHADOW: the impl region of model.py's `block_lengths_by_axis`, copied verbatim
below with the contract calls (Requires/Ensures/Invariant) stripped. Lists stay
plain Python lists (the model IS Python). The single @ContractOnly callee the
impl region calls, `inspect_underlying`, is realized by the REAL repo operation
it axiomatizes per mapping.md: probing the entry's UNDERLYING store for a block
structure (`hasattr(v._data, "chunks")` on a real in-container `Variable`),
with the forced-load count observed through a recording sentinel store. The
other @ContractOnly symbols (`inspect_materialised`, the abstract
`payload_intact` predicate) are never called by the impl region — the token is
a proof-only construct with no runtime footprint — so they need no executable
shim; the runtime face of the no-materialisation obligation IS the oracle run
itself (see below).

ORACLE: the REAL patched repo function the model models per mapping.md —
`xarray.core.common.get_chunksizes(variables)` — invoked on real `Variable`
objects. The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched module importable. Every case includes
the option of a lazily-backed entry whose inner store RAISES on any item
access (the same recording/raising sentinel shape as axiom_check.py), so an
oracle that materialised any entry would raise and be reported as a
disagreement — the runtime witness of the intactness clause.

TYPE BRIDGE (mapping.md "Type abstraction"): one Entry <-> one Variable, order
preserved. Entry fields realize as:
  * block_backed=False, forces_load=False -> in-memory numpy-backed Variable;
  * block_backed=False, forces_load=True  -> Variable over a
    LazilyIndexedArray wrapping an inaccessible (raising) inner store — the
    exact FAIL_TO_PASS regime;
  * block_backed=True,  forces_load=False -> dask-backed Variable, one dim,
    one chunk of the entry's length (so the single value in `chunksizes` is
    the tuple `(length,)`, bridged to the model's int `length`).
  (block_backed AND forces_load has no repo realization: a store advertising
  a block structure is a duck array, so obtaining the payload forces no load.)
Axis labels: the model's int axis maps injectively to a dim name string
("ax_<n>" / "ax_n<n>"); distinct ints give distinct dims. The result mapping:
the shadow's flat (axis, length) pair list, dropping the (-1,-1) skip markers
and keying by the bridged dim name, must equal `dict()` of the oracle's frozen
mapping with each value being the one-chunk tuple (length,). The trailing
loads slot must be 0 and the sentinel must record zero item accesses across
the oracle call. Duplicate axes are drawn only with consistent lengths among
block-structured entries (the cross-entry inconsistency raise is orthogonal
to the modeled behaviour per refinement.md and outside the bridged domain);
non-block-structured entries may collide with anything.

INPUT DOMAIN (the model's Requires): any finite list of valid entries (all
four fields readable, every entry initially intact — realized by constructing
each Variable fresh, payload never touched). Lengths are drawn from a pooled
set of positive ints (dask arrays are lazily allocated, so lengths up to 1e9
cost nothing); axes span negative/zero/huge ints.

>= 1e5 Requires-satisfying inputs: boundary battery (empty list, every single
regime, all 3^3 regime triples, duplicate-axis and extreme-value shapes) +
100000 fuzz cases. Pinned fuzz seed: 6721.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib + numpy (+ dask, shipped in the evaluation
image, needed only to realize the block-structured regime; if unavailable
that regime is dropped and the run reports it).
"""
import json
import random
import sys

SEED = 6721
N_FUZZ = 100_000


# --- the impl region of model.py, verbatim, contract calls stripped -----------

class Entry:
    def __init__(self, block_backed, forces_load, axis, length, variable):
        self.block_backed = block_backed
        self.forces_load = forces_load
        self.axis = axis
        self.length = length
        self.variable = variable  # bridge only: the real Variable realizing it


def block_lengths_by_axis(entries):
    result = []
    loads = 0
    i = 0
    while i < len(entries):
        e = entries[i]
        probe = inspect_underlying(e)
        loads = loads + probe[1]
        if probe[0]:
            result = result + [e.axis, e.length]
        else:
            result = result + [-1, -1]
        i = i + 1
    result = result + [loads]
    return result


# --- @ContractOnly callee: realized by the REAL repo operation ----------------

_RECORD = []  # item-access sentinel, shared with the inaccessible inner store


def inspect_underlying(e):
    """The underlying-store block probe the model axiomatizes: read the real
    Variable's raw store in place for a block structure, counting the loads
    this forces (always zero — the raw store is never materialised)."""
    before = len(_RECORD)
    status = hasattr(e.variable._data, "chunks")
    return (status, len(_RECORD) - before)


# --- bridge: realize each Entry regime as a real in-container Variable --------

class _LoadTrip(Exception):
    pass


def _setup():
    import numpy as np
    from xarray import Variable
    from xarray.core import indexing, utils
    from xarray.core.common import get_chunksizes

    class InaccessibleArray(utils.NDArrayMixin, indexing.ExplicitlyIndexed):
        # inner store whose item access is a materialisation attempt: it is
        # recorded and refused, so any payload pull is loudly observable.
        def __init__(self, array):
            self.array = array

        def __getitem__(self, key):
            _RECORD.append("load")
            raise _LoadTrip("payload materialised")

    lazy_store = indexing.LazilyIndexedArray(InaccessibleArray(np.arange(2)))
    mem_store = np.arange(2)

    dask_cache = {}
    try:
        import dask.array as da

        def dask_store(length):
            st = dask_cache.get(length)
            if st is None:
                st = da.zeros(length, chunks=length)  # one chunk of `length`
                dask_cache[length] = st
            return st
    except Exception:
        dask_store = None

    return np, Variable, get_chunksizes, lazy_store, mem_store, dask_store


def _dim_of(axis):
    """Injective int-axis -> dim-name bridge."""
    return "ax_%d" % axis if axis >= 0 else "ax_n%d" % (-axis)


def _make_entry(Variable, lazy_store, mem_store, dask_store, bb, fl, axis, length):
    dim = _dim_of(axis)
    if bb:
        v = Variable((dim,), dask_store(length))
    elif fl:
        v = Variable((dim,), lazy_store)
    else:
        v = Variable((dim,), mem_store)
    return Entry(bb, fl, axis, length, v)


# --- one differential case -----------------------------------------------------

def check_case(ctx, regimes):
    """regimes: list of (block_backed, forces_load, axis, length). Returns an
    error string on disagreement, else None."""
    np, Variable, get_chunksizes, lazy_store, mem_store, dask_store = ctx
    entries = []
    variables = []
    for bb, fl, ax, ln in regimes:
        e = _make_entry(Variable, lazy_store, mem_store, dask_store,
                        bb, fl, ax, ln)
        entries.append(e)
        variables.append(e.variable)

    # shadow run
    _RECORD.clear()
    try:
        out = block_lengths_by_axis(entries)
    except Exception as exc:
        return "DISAGREEMENT (shadow raised)\n  input: %r\n  shadow=%r" % (
            regimes, exc)

    # oracle run on the real patched function; a forced materialisation
    # trips the sentinel (and raises), surfacing as a disagreement
    _RECORD.clear()
    try:
        real = get_chunksizes(variables)
    except Exception as exc:
        return ("DISAGREEMENT (oracle raised / forced a load)\n"
                "  input: %r\n  shadow=%r\n  real raised %r" % (
                    regimes, out, exc))
    if _RECORD:
        return ("DISAGREEMENT (oracle materialised a payload)\n"
                "  input: %r\n  shadow=%r\n  accesses=%d" % (
                    regimes, out, len(_RECORD)))
    real_d = dict(real)

    # shadow shape + per-entry contributions per the bridge
    if len(out) != 2 * len(regimes) + 1:
        return "DISAGREEMENT (shadow shape)\n  input: %r\n  shadow=%r" % (
            regimes, out)
    if out[-1] != 0:
        return ("DISAGREEMENT (shadow loads slot)\n  input: %r\n  shadow=%r" %
                (regimes, out))
    expected = {}
    for k, (bb, fl, ax, ln) in enumerate(regimes):
        pair = (out[2 * k], out[2 * k + 1])
        if bb:
            if pair != (ax, ln):
                return ("DISAGREEMENT (entry %d contribution)\n"
                        "  input: %r\n  shadow pair=%r expected=%r" % (
                            k, regimes, pair, (ax, ln)))
            expected[_dim_of(ax)] = (ln,)
        else:
            if pair != (-1, -1):
                return ("DISAGREEMENT (entry %d skip marker)\n"
                        "  input: %r\n  shadow pair=%r expected=(-1, -1)" % (
                            k, regimes, pair))
    if real_d != expected:
        return ("DISAGREEMENT (mapping content)\n  input: %r\n  shadow=%r\n"
                "  shadow-as-mapping=%r\n  real=%r" % (
                    regimes, out, expected, real_d))
    return None


# --- input generation ------------------------------------------------------------

LEN_POOL = [1, 2, 3, 5, 7, 8, 64, 100, 1000, 10 ** 6, 10 ** 9]
AXIS_EXTREMES = [0, 1, -1, 2 ** 31, -(2 ** 31), 999999937]


def boundary_cases(have_dask):
    kinds = [(False, False), (False, True)] + ([(True, False)] if have_dask else [])
    cases = [[]]  # empty collection
    # every single regime, with extreme axes and lengths
    for bb, fl in kinds:
        for ax in AXIS_EXTREMES:
            cases.append([(bb, fl, ax, 1)])
        cases.append([(bb, fl, 3, 10 ** 9)])
    # all regime triples, distinct axes
    for a in kinds:
        for b in kinds:
            for c in kinds:
                cases.append([a + (0, 2), b + (1, 5), c + (-7, 3)])
    # duplicate axes: block/block same length; block vs non-block; non/non
    if have_dask:
        cases.append([(True, False, 4, 7), (True, False, 4, 7)])
        cases.append([(True, False, 4, 7), (False, True, 4, 9)])
        cases.append([(False, False, 4, 1), (True, False, 4, 7)])
    cases.append([(False, True, 5, 1), (False, True, 5, 2)])
    cases.append([(False, False, 5, 1), (False, True, 5, 2)])
    # longer mixed collection
    long = []
    for i in range(8):
        bb, fl = kinds[i % len(kinds)]
        long.append((bb, fl, 100 + i, LEN_POOL[i % len(LEN_POOL)]))
    cases.append(long)
    return cases


def fuzz_case(rng, have_dask):
    n = rng.choice([0] + [1] * 3 + [2] * 5 + [3] * 5 + [4] * 3 + [5, 6, 8])
    regimes = []
    chunked_axis_len = {}
    for _ in range(n):
        r = rng.random()
        if have_dask and r < 0.45:
            bb, fl = True, False
        elif r < 0.75:
            bb, fl = False, True
        else:
            bb, fl = False, False
        if rng.random() < 0.15 and regimes:
            axis = rng.choice(regimes)[2]  # deliberate axis collision
        elif rng.random() < 0.1:
            axis = rng.choice(AXIS_EXTREMES)
        else:
            axis = rng.randint(-10 ** 6, 10 ** 6)
        length = rng.choice(LEN_POOL)
        if bb:
            # keep block-structured entries on one axis length-consistent
            # (the cross-entry inconsistency raise is outside the bridged
            # domain — see the module docstring)
            length = chunked_axis_len.setdefault(axis, length)
        regimes.append((bb, fl, axis, length))
    return regimes


def main():
    ctx = _setup()
    dask_store = ctx[5]
    have_dask = dask_store is not None

    checked = 0
    boundary = boundary_cases(have_dask)
    for regimes in boundary:
        err = check_case(ctx, regimes)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        regimes = fuzz_case(rng, have_dask)
        err = check_case(ctx, regimes)
        if err:
            print(err)
            return 1
        checked += 1

    note = "" if have_dask else " [dask unavailable: block-structured regime dropped]"
    print("G-CONF OK: shadow impl (contract-stripped impl region; "
          "inspect_underlying realized by the real underlying-store block "
          "probe) == real patched inspection function on %d Requires-"
          "satisfying inputs (%d boundary + %d fuzz, seed %d); zero payload "
          "materialisations observed.%s" % (checked, len(boundary), N_FUZZ,
                                            SEED, note))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "inspect_underlying probes the real "
                                "underlying store in place)",
                      "dask_regime": have_dask}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
