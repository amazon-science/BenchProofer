#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-3993 (nagini).

SHADOW: the impl region of model.py's `select_coordinate`, copied verbatim
below with the contract calls (Requires/Ensures/Exsures) stripped. The model
uses no PSeq and no @Pure module helpers, so no shims are needed; the two
support classes (the user-defined exception and the small outcome object) are
carried over with their contract lines removed. There are no @ContractOnly
callees in this bundle.

ORACLE: the REAL patched repo method the model models per mapping.md —
`xarray.core.dataarray.DataArray.integrate` (the gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed resolves the patched
source). Its three observables, exactly as bound in mapping.md section 1:
  * Routed.coord      <-> the coordinate value handed to the delegation
                          boundary `self._to_temp_dataset().integrate(...)`,
                          captured here by installing a recording stand-in at
                          that boundary (the downstream numerics are unchanged
                          and unobserved by the specification);
  * Routed.deprecated <-> whether a FutureWarning was emitted during the call,
                          captured with warnings.catch_warnings(record=True);
  * ConflictingSelection <-> the ValueError the method raises when both
                          selectors are supplied at once (with the delegation
                          boundary replaced, no other ValueError source exists
                          inside the call).

TYPE BRIDGE (mapping.md section 2): the model abstracts a selector (any
hashable coordinate identifier, or None for "not supplied") as Optional[int]
with an arbitrary injective encoding, since only is-None-ness and identity of
the chosen selector are observed. The bridge maps each int identifier to a
concrete hashable coordinate name (several injective encodings are exercised:
strings, raw ints, tuples) and maps None to the argument's default / an
explicit None (the real guards test `is not None`, so omitting the argument
and passing None explicitly are the same point of the input domain; both
calling conventions are exercised).

INPUT DOMAIN: Requires is just MustTerminate — every (Optional[int],
Optional[int]) pair is admissible. Coverage: the full supplied/omitted
enumeration crossed with all calling-convention/encoding styles as boundary
cases, plus 100000 fuzz pairs. Pinned fuzz seed: 3993.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib only (xarray/numpy come from the instance image).
"""
import random
import json
import sys
import warnings

SEED = 3993
N_FUZZ = 100_000


# --- support classes from model.py, contract lines stripped -------------------

class ConflictingSelection(Exception):
    pass


class Routed:
    def __init__(self, coord, deprecated):
        self.coord = coord            # type: ignore
        self.deprecated = deprecated  # type: ignore


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def select_coordinate(coord, dim):
    if dim is not None and coord is not None:
        raise ConflictingSelection()

    deprecated = False
    if dim is not None and coord is None:
        coord = dim
        deprecated = True

    return Routed(coord, deprecated)


# --- oracle plumbing -----------------------------------------------------------

_UNSET = object()


class _DelegationRecorder:
    """Stand-in installed at the delegation boundary: records the coordinate
    value the routing prologue hands onward and returns a sentinel (the
    downstream computation is unchanged by the patch and unobserved by the
    specification, so it is not exercised here)."""

    def __init__(self):
        self.coord = _UNSET

    def reset(self):
        self.coord = _UNSET

    def integrate(self, coord, datetime_unit=None):
        self.coord = coord
        return self  # sentinel; passed through the (also replaced) unwrapper


# Injective encodings of the model's int identifier into a concrete hashable
# coordinate name; only is-None-ness and identity are observed, so any
# injective map is a faithful bridge.
ENCODINGS = [
    lambda i: "sel_%d" % i,
    lambda i: i,
    lambda i: ("sel", i),
]


def real_route(da, coord_id, dim_id, encode, style, recorder):
    """Call the REAL patched method with the encoded selectors and observe
    (refused?, routed coordinate, deprecation-signal emitted?)."""
    coord_arg = None if coord_id is None else encode(coord_id)
    dim_arg = None if dim_id is None else encode(dim_id)
    recorder.reset()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            if style == 0:
                # omit unsupplied arguments entirely (the defaults)
                kwargs = {}
                if coord_arg is not None:
                    kwargs["coord"] = coord_arg
                if dim_arg is not None:
                    kwargs["dim"] = dim_arg
                da.integrate(**kwargs)
            elif style == 1:
                # pass both keywords explicitly (None == not supplied)
                da.integrate(coord=coord_arg, dim=dim_arg)
            else:
                # primary selector positionally, legacy keyword-only
                da.integrate(coord_arg, dim=dim_arg)
        except ValueError:
            emitted = any(issubclass(w.category, FutureWarning) for w in caught)
            return ("raised", None, emitted)
        emitted = any(issubclass(w.category, FutureWarning) for w in caught)
    routed = recorder.coord
    return ("ok", routed, emitted)


def shadow_route(coord_id, dim_id, encode):
    """Run the contract-stripped shadow and express its outcome in oracle
    terms through the same injective encoding."""
    try:
        r = select_coordinate(coord_id, dim_id)
    except ConflictingSelection:
        return ("raised", None, False)
    routed = None if r.coord is None else encode(r.coord)
    return ("ok", routed, r.deprecated)


def check_one(da, coord_id, dim_id, encode, style, recorder):
    s = shadow_route(coord_id, dim_id, encode)
    o = real_route(da, coord_id, dim_id, encode, style, recorder)
    if s[0] != o[0]:
        return ("refusal disagreement on coord=%r dim=%r style=%d: "
                "shadow=%r real=%r" % (coord_id, dim_id, style, s, o))
    if s[0] == "raised":
        # fact-of-refusal agrees; nothing further is observed on this path
        return None
    if s[1] != o[1]:
        return ("routed-coordinate disagreement on coord=%r dim=%r style=%d: "
                "shadow=%r real=%r" % (coord_id, dim_id, style, s, o))
    if bool(s[2]) != bool(o[2]):
        return ("deprecation-signal disagreement on coord=%r dim=%r style=%d: "
                "shadow=%r real=%r" % (coord_id, dim_id, style, s, o))
    return None


def main():
    from xarray.core.dataarray import DataArray  # REAL patched class

    da = DataArray([1.0, 2.0, 3.0], dims="x", coords={"x": [0.0, 0.5, 1.5]})

    recorder = _DelegationRecorder()
    orig_to_temp = DataArray._to_temp_dataset
    orig_from_temp = DataArray._from_temp_dataset
    DataArray._to_temp_dataset = lambda self: recorder
    DataArray._from_temp_dataset = lambda self, ds: ds
    checked = 0
    boundary = 0
    try:
        # --- boundary: full supplied/omitted enumeration x encodings x styles
        values = [None, 0, 1, 7, -3, 100]
        for coord_id in values:
            for dim_id in values:
                for encode in ENCODINGS:
                    for style in (0, 1, 2):
                        err = check_one(da, coord_id, dim_id, encode, style,
                                        recorder)
                        if err:
                            print("DISAGREEMENT\n  " + err)
                            return 1
                        checked += 1
                        boundary += 1

        # --- fuzz: pinned seed --------------------------------------------
        rng = random.Random(SEED)
        pool = [None] + list(range(-50, 50))
        for _ in range(N_FUZZ):
            coord_id = rng.choice(pool)
            dim_id = rng.choice(pool)
            encode = ENCODINGS[rng.randrange(len(ENCODINGS))]
            style = rng.randrange(3)
            err = check_one(da, coord_id, dim_id, encode, style, recorder)
            if err:
                print("DISAGREEMENT\n  " + err)
                return 1
            checked += 1
    finally:
        DataArray._to_temp_dataset = orig_to_temp
        DataArray._from_temp_dataset = orig_from_temp

    print("G-CONF OK: shadow routing == real patched entry point on %d inputs "
          "(%d boundary + %d fuzz, seed %d); refusal, routed coordinate, and "
          "deprecation signal all agree." % (checked, boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
