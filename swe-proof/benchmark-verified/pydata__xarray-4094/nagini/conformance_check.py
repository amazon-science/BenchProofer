#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-4094 (nagini).

SHADOW: the impl region of model.py's `to_unstacked`, copied verbatim below
with the contract calls (Requires/Ensures/Invariant/Assert) stripped and the
proof-only ghost-lemma calls (lemma_carried_all_equal) removed. Lists stay
plain Python lists (the model IS Python). The one @ContractOnly callee the
impl region calls, `assemble`, is realized by the REAL repo callee it
axiomatizes per mapping.md section 3.2: the collection constructor/merge
(`xarray.Dataset(data_dict)`) over real per-member slices taken under the
same selection flag (`.sel({variable_dim: k}, drop=discard).squeeze(drop=True)`,
the callee pair of mapping.md section 3.1). The other @ContractOnly symbols
(`carried`, `shared_value`, the abstract `combined_collection` predicate) are
spec-only: the impl region never calls them, so they need no executable shim.

ORACLE: the REAL patched repo method the model models per mapping.md —
`xarray.core.dataarray.DataArray.to_unstacked_dataset`, invoked on a real
stacked DataArray. The gate applies patch.diff to /testbed before this script
runs; PYTHONPATH=/testbed makes the patched module importable.

TYPE BRIDGE (mapping.md section 2): the pinned shape is the single-sample-axis
stacked collection — n members along one shared stacked axis whose MultiIndex
ticks pair a member identifier with a position label. Member k of the model
maps to a variable name injectively derived from resid[k] ("m<resid[k]>"), so
the members' pairwise-distinct resid ints realize pairwise-distinct position
labels on the stacked axis (in this shape the residual position label of a
member's slice is determined by its own tick). data[k] (one int per member;
the per-member data width is incidental) realizes as member k's constant
value over a length-2 sample axis (length 2 so the size-one-axis collapse
touches only the stacked axis). The equivalence of this direct MultiIndex
construction with the repo's own stacking helper was verified in-container
(`.identical` on both sorted and unsorted member-name orders).

INPUT DOMAIN (the model's Requires): n >= 2, len(data) == len(resid) == n,
resid pairwise distinct. Generation enforces exactly this: n drawn from
2..6 (weighted toward the small shapes), data any ints (int64 range), resid
distinct ints. Boundary cases: minimal n, equal/zero/negative/extreme data
values, adjacent and far-apart resid values, unsorted member orders.

>= 1e5 Requires-satisfying inputs: 64 boundary + 100000 fuzz cases.
Pinned fuzz seed: 4094.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib + numpy + pandas (both shipped with the repo;
pandas only realizes the stacked axis' MultiIndex ticks).
"""
import json
import random
import sys

import numpy as np
import pandas as pd
import xarray as xr

SEED = 4094
N_FUZZ = 100_000

_STACK_DIM = "y"
_SAMPLE_DIM = "x"
_VARIABLE_DIM = "variable"


# --- bridge helpers ------------------------------------------------------------

def _name_of(resid_value):
    """Injective member-identifier encoding: distinct resid ints give distinct
    variable names, realizing the pairwise-distinct position labels."""
    return "m%d" % resid_value


def _build_stacked(values, names):
    """A real stacked DataArray in the pinned single-sample-axis shape:
    member k carries the constant value values[k] over a length-2 sample axis
    and sits at its own tick (names[k],) on the stacked MultiIndex axis."""
    midx = pd.MultiIndex.from_arrays([list(names)], names=[_VARIABLE_DIM])
    data = np.empty((2, len(values)), dtype=np.int64)
    for k, v in enumerate(values):
        data[:, k] = v
    return xr.DataArray(data, dims=(_SAMPLE_DIM, _STACK_DIM),
                        coords={_SAMPLE_DIM: [0, 1], _STACK_DIM: midx})


# --- @ContractOnly callee: realized by the REAL repo callees -------------------

def assemble(slices, resid, discard):
    """The combination callee. model.py axiomatizes it opaquely; the real
    callee it stands for (mapping.md section 3.2) is the Dataset constructor /
    coordinate merge over the per-member slices, each taken under the SAME
    selection flag (mapping.md section 3.1's callee pair). Returns the
    recovered per-member values in member order; a conflicting shared-name
    annotation propagates as the merge's rejection exception."""
    names = [_name_of(r) for r in resid]
    st = _build_stacked(slices, names)
    data_dict = {}
    for nm in names:
        data_dict[nm] = st.sel({_VARIABLE_DIM: nm},
                               drop=discard).squeeze(drop=True)
    merged = xr.Dataset(data_dict)  # rejected on a conflicting annotation
    return [int(merged[nm].values[0]) for nm in names]


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def to_unstacked(n, data, resid):
    discard = True
    data_dict = []  # type: list
    i = n
    while i > 0:
        # take member i-1's slice under `discard`, recovering its value verbatim.
        selected = data[i - 1]
        data_dict = [selected] + data_dict
        i = i - 1
    result = assemble(data_dict, resid, discard)
    return result


# --- oracle invocation on the real patched repo method -------------------------

def real_unstack(data, resid):
    """Build the real stacked collection for (data, resid) and call the REAL
    patched reconstruction method; observe (outcome, recovered values)."""
    names = [_name_of(r) for r in resid]
    st = _build_stacked(data, names)
    try:
        rec = st.to_unstacked_dataset(_STACK_DIM)
    except Exception as exc:
        return ("raised", repr(exc))
    if not isinstance(rec, xr.Dataset):
        return ("raised", "non-collection result %r" % type(rec))
    return ("ok", [int(rec[nm].values[0]) for nm in names])


def shadow_unstack(n, data, resid):
    try:
        out = to_unstacked(n, list(data), list(resid))
    except Exception as exc:
        return ("raised", repr(exc))
    return ("ok", list(out))


def check_case(n, data, resid):
    """Run shadow and oracle on one Requires-satisfying input; return an
    error string on disagreement, else None."""
    assert n >= 2 and len(data) == n and len(resid) == n
    assert len(set(resid)) == n  # Requires: pairwise-distinct positions

    s = shadow_unstack(n, data, resid)
    o = real_unstack(data, resid)
    if s[0] != o[0]:
        return ("DISAGREEMENT (outcome)\n  input: n=%d data=%r resid=%r\n"
                "  shadow=%r\n  real=%r" % (n, data, resid, s, o))
    if s[0] == "ok" and s[1] != o[1]:
        return ("DISAGREEMENT (values)\n  input: n=%d data=%r resid=%r\n"
                "  shadow=%r\n  real=%r" % (n, data, resid, s, o))
    return None


# --- input generation -----------------------------------------------------------

BIG = 2 ** 62


def boundary_cases():
    cases = []
    datas = [
        [0, 0], [0, 1], [1, 0], [-1, 1], [5, 5],
        [BIG, -BIG], [-BIG, BIG], [123456789, -987654321],
    ]
    resids = [
        [0, 1], [1, 0], [-1, 0], [7, -7], [1000000, -1000000], [2, 3],
    ]
    for d in datas:
        for r in resids:
            cases.append((2, d, r))
    for nn in (3, 4, 5, 6):
        base_d = [0, 1, -1, BIG, -BIG, 42][:nn]
        base_r = [5, -3, 0, 99, -99, 7][:nn]
        cases.append((nn, base_d, base_r))
        cases.append((nn, [7] * nn, list(range(nn))))
        cases.append((nn, list(range(nn)), list(range(nn - 1, -1, -1))))
        cases.append((nn, [-v for v in range(nn)], [10 * v - 17 for v in range(nn)]))
    return cases


def fuzz_case(rng):
    n = rng.choice([2] * 8 + [3] * 5 + [4, 5, 6])
    data = [rng.randint(-BIG, BIG) if rng.random() < 0.3
            else rng.randint(-1000, 1000) for _ in range(n)]
    resid = rng.sample(range(-10 ** 6, 10 ** 6), n)
    return n, data, resid


def main():
    checked = 0
    boundary = boundary_cases()
    for n, d, r in boundary:
        err = check_case(n, d, r)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        n, d, r = fuzz_case(rng)
        err = check_case(n, d, r)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl (contract-stripped impl region; assemble "
          "realized by the real collection constructor/merge over real "
          "per-member slices) == real patched reconstruction method on %d "
          "Requires-satisfying inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "assemble calls the real constructor/merge "
                                "over real slices)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
