#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-4695 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helpers
(RESERVED_NAME / DEFAULT_OPTION / option_after_namekeyed) copy over as plain
functions; PSeq.take(n) becomes a plain slice on lists. There are no
@ContractOnly callees in this bundle (the routing is modelled deeply).

ORACLE: the REAL patched repo function the model models per mapping.md --
`xarray.core.dataarray._LocIndexer.__getitem__`. The gate applies patch.diff
to /testbed before this script runs; PYTHONPATH=/testbed makes the patched
module importable. This script never applies any diff itself.

Observation point (mapping.md section 2): the model's two functions describe
what arrives at the underlying selector's boundary --
  * forward_axis_names  <-> the axis indexers the selector actually receives
    (after the repo's own positional/keyword dispatch helper,
    xarray.core.utils.either_dict_or_kwargs), and
  * bound_reserved_option <-> the value bound to the selector's reserved
    `method` parameter.
So the oracle drives the REAL `_LocIndexer.__getitem__` over a probe whose
`sel` has the exact reserved-parameter signature of `DataArray.sel` and
reports, via the repo's REAL dispatch helper, which indexers and option
values it received. A small end-to-end smoke on genuine DataArray objects
(including an axis named like the reserved option) additionally confirms the
facade performs the selection, with expectations computed independently by
raw array indexing.

Type bridge (mapping.md section 2):
  * mapping entry k  <->  (names[k], values[k]): axis-name id -> name string
    via a bijection sending RESERVED_NAME() == 7 to "method" and every other
    id i to "ax<i>" (never a reserved parameter name); label-selector id ->
    the int label itself (values are >= 0 per the Requires).
  * insertion order of the dict <-> list order of the parallel sequences.
  * bound option `None` <-> DEFAULT_OPTION() == -1 (the unset sentinel,
    distinct from every label id since labels are >= 0).
  * generated name ids are DISTINCT within a case: the List[int] carrier
    admits duplicates but a real dict cannot, so the conformance domain is
    the injective one.

>= 1e5 Requires-satisfying inputs: structured boundary mappings (empty, the
issue-shaped collision, collision at front/middle/back, collision-only,
label boundary values) plus 100000 fuzz mappings. Pinned fuzz seed: 46950.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy only (no hypothesis needed).
"""
import json
import random
import sys

SEED = 46950
N_FUZZ = 100_000


# --- pure helpers from model.py, contracts stripped ----------------------------

def RESERVED_NAME():
    # axis-name id that collides with a reserved option name of the
    # underlying selector
    return 7


def DEFAULT_OPTION():
    # default (unset sentinel) of the reserved option
    return -1


def option_after_namekeyed(names, values):
    # the value the reserved option would take under a NAME-KEYED routing
    # that diverts a colliding axis into the reserved slot (the routing the
    # correct facade must NOT perform); PSeq.take(n) -> slice
    if len(names) == 0:
        return DEFAULT_OPTION()
    if names[len(names) - 1] == RESERVED_NAME():
        return values[len(values) - 1]
    return option_after_namekeyed(names[:len(names) - 1],
                                  values[:len(values) - 1])


# --- the impl regions of model.py, verbatim, contract calls stripped -----------

def forward_axis_names(names, values):
    # Forward the mapping positionally: every entry, including one whose name
    # equals RESERVED_NAME, is kept as an axis selector.
    forwarded = []  # type: list
    i = 0
    while i < len(names):
        forwarded.append(names[i])
        i = i + 1
    return forwarded


def bound_reserved_option(names, values):
    # Positional forwarding: the reserved option is not fed from the mapping.
    option = DEFAULT_OPTION()
    return option


# --- bridge: int ids <-> real mapping names/labels ------------------------------

def name_of(nid):
    """Axis-name id -> dimension name. Only the colliding id maps to a name
    that is also a reserved parameter of the underlying selector."""
    return "method" if nid == RESERVED_NAME() else "ax%d" % nid


def id_of(name):
    return RESERVED_NAME() if name == "method" else int(name[2:])


def make_probe():
    """A stand-in data array whose `sel` has the exact reserved-parameter
    signature of the real selector and reports what it received, computed by
    the repo's REAL positional/keyword dispatch helper."""
    from xarray.core.utils import either_dict_or_kwargs

    class Probe(object):
        def sel(self, indexers=None, method=None, tolerance=None, drop=False,
                **indexers_kwargs):
            eff = either_dict_or_kwargs(indexers, indexers_kwargs, "sel")
            return (dict(eff), method, tolerance, drop)

    return Probe()


def check_case(loc_indexer_cls, probe, names, values):
    # Requires of the modeled functions, by construction of the generators:
    assert len(names) == len(values) and all(v >= 0 for v in values)
    shadow_fwd = forward_axis_names(list(names), list(values))
    shadow_opt = bound_reserved_option(list(names), list(values))

    mapping = dict(zip([name_of(n) for n in names], values))
    # REAL patched facade, observed at the selector boundary:
    eff, method, tolerance, drop = loc_indexer_cls(probe)[mapping]

    real_fwd = [id_of(k) for k in eff.keys()]
    real_opt = DEFAULT_OPTION() if method is None else method

    if (shadow_fwd != real_fwd or shadow_opt != real_opt
            or eff != mapping or tolerance is not None or drop is not False):
        return ("DISAGREEMENT\n  names=%r values=%r mapping=%r\n"
                "  shadow: forwarded=%r option=%r\n"
                "  real:   forwarded=%r option=%r (eff=%r, tolerance=%r, "
                "drop=%r)"
                % (names, values, mapping, shadow_fwd, shadow_opt,
                   real_fwd, real_opt, eff, tolerance, drop))
    return None


def boundary_cases():
    R = RESERVED_NAME()
    cases = [
        ([], []),                              # empty mapping
        ([0], [0]),                            # single ordinary axis
        ([R], [0]),                            # only the colliding axis
        ([R], [999]),
        ([0, 1], [5, 6]),                      # ordinary mapping
        ([0, R], [5, 6]),                      # collision at the back
        ([R, 0], [6, 5]),                      # collision at the front
        ([0, R, 1], [1, 2, 3]),                # collision in the middle
        ([2, 1, 0], [0, 0, 0]),                # order matters; zero labels
        ([0, 1, 2, 3, 4, 5], [9, 8, 7, 6, 5, 4]),
        ([R, 12], [1000000, 0]),               # large label id
        ([5, R, 3, 8], [4, 7, 0, 2]),
    ]
    return cases


def smoke_real_selection():
    """End-to-end: the facade on genuine data arrays selects the labelled
    element, including when an axis shares its name with the reserved option.
    Expectations computed independently by raw positional indexing."""
    import numpy as np
    import xarray as xr

    data = np.arange(4.0).reshape(2, 2)
    d_plain = xr.DataArray(data, dims=["dim1", "dim2"],
                           coords={"dim1": ["x", "y"], "dim2": ["a", "b"]})
    d_coll = xr.DataArray(data, dims=["dim1", "method"],
                          coords={"dim1": ["x", "y"], "method": ["a", "b"]})
    probes = [
        (d_plain, {"dim1": "x", "dim2": "a"}, data[0, 0]),
        (d_plain, {"dim1": "y", "dim2": "b"}, data[1, 1]),
        (d_coll, {"dim1": "x", "method": "a"}, data[0, 0]),
        (d_coll, {"dim1": "y", "method": "a"}, data[1, 0]),
        (d_coll, {"method": "b"}, None),  # partial mapping: one axis left
    ]
    for da, mapping, expect in probes:
        out = da.loc[mapping]
        if expect is None:
            got = [float(v) for v in np.asarray(out).ravel()]
            want = [float(data[0, 1]), float(data[1, 1])]
            if got != want:
                return ("SMOKE DISAGREEMENT\n  mapping=%r\n  got=%r want=%r"
                        % (mapping, got, want))
        else:
            if float(out) != float(expect):
                return ("SMOKE DISAGREEMENT\n  mapping=%r\n  got=%r want=%r"
                        % (mapping, float(out), float(expect)))
    return None


def main():
    # REAL repo symbol the model models (per mapping.md):
    from xarray.core.dataarray import _LocIndexer

    probe = make_probe()
    checked = 0

    n_boundary = 0
    for names, values in boundary_cases():
        err = check_case(_LocIndexer, probe, names, values)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    id_pool = list(range(14))  # includes RESERVED_NAME() == 7
    for _ in range(N_FUZZ):
        n = rng.randint(0, 6)
        names = rng.sample(id_pool, n)  # distinct ids: injective real mapping
        values = [rng.randint(0, 999) for _ in range(n)]
        err = check_case(_LocIndexer, probe, names, values)
        if err:
            print(err)
            return 1
        checked += 1

    err = smoke_real_selection()
    if err:
        print(err)
        return 1

    print("G-CONF OK: shadow impl == real patched label-selection facade on "
          "%d inputs (%d boundary + %d fuzz, seed %d) + 5 end-to-end smoke "
          "selections." % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
