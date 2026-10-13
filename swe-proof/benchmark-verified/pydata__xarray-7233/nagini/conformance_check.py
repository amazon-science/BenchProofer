#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-7233 (nagini).

SHADOW  — the impl region of `model.py` copied VERBATIM with the contract
          statement lines (Requires/Ensures/Invariant/Assert and the ToSeq
          ghost bookkeeping) stripped; the model IS Python, so no
          transliteration.  The @Pure helper `promoted` copies over as a
          plain function.  No PSeq appears in the impl region, so no
          sequence shim is needed.  There are no @ContractOnly callees.

ORACLE  — the REAL patched repo function the model models per mapping.md:
          `xarray.core.rolling.Coarsen.construct` (its whole rebuild tail),
          reached through the public
          `obj.coarsen(windows).construct(window_dim)` entry point on both
          Dataset and DataArray objects.  The gate applies the gold patch to
          /testbed before this script runs and sets PYTHONPATH=/testbed;
          this script never applies any diff itself.

BRIDGE  — mapping.md §2's type abstraction, realized concretely:
            member k             <-> the k-th name in the ordered variable
                                     collection of the input object (for a
                                     Dataset: `list(ds.variables)`; for a
                                     DataArray: its coordinate names plus the
                                     array member itself)
            was_label[k] == 1    <-> name_k in set(obj.coords)
            is_window[k] == 1    <-> name_k in set(window_dim)  (the name is
                                     one of the axes being windowed)
            is_axis_name[k] == 1 <-> the name member k is INSERTED under in
                                     the rebuilt container coincides with one
                                     of that container's axis names.  The
                                     rebuilt container's axis names are
                                     computed from the input alone: each input
                                     axis that is windowed contributes its
                                     replacement names, every other input axis
                                     contributes itself.  On the Dataset arm a
                                     member is inserted under its own name; on
                                     the DataArray arm the array member is
                                     inserted under the container's internal
                                     placeholder name instead of its own, so
                                     its bit is decided by that placeholder
                                     (which is never an axis name) -- the two
                                     arms genuinely differ here and the bridge
                                     follows each arm to the name it uses.
                                     `axis_bridge_ok` re-derives the axis-name
                                     set from the REALIZED output on every case
                                     and asserts it matches the input-derived
                                     one, so the bridge is checked, not assumed.
            Result()[k] == 1     <-> name_k in set(result.coords)
          The transform never adds, drops, or renames a member (asserted on
          every case), so the fixed name list makes the parallel-bit lists
          well defined on both sides.  The model's Requires hold by
          construction (equal lengths; membership bits are 0/1) and are
          asserted before each shadow call.

INPUTS  — >= 1e5 Requires-satisfying inputs: structured boundary cases
          covering every reachable (was_label, is_window, is_axis_name)
          combination — dimension coordinates on windowed axes, non-dimension
          and scalar coordinates, data members named like a windowed axis,
          plain data members, members whose name coincides with a REPLACEMENT
          axis name of the rebuilt container, members whose name coincides
          with a surviving (non-windowed) axis name, coordinate-only objects,
          objects whose windowed axis has no coordinate at all, and DataArray
          objects on both naming arms — plus fuzzed Datasets/DataArrays over
          1-2 windowed axes.  The fuzzer draws member names and replacement
          axis names from ONE SHARED alphabet, so name coincidences between a
          member and a rebuilt axis occur by construction rather than being
          impossible; `report["axis_name_cases"]` records how many checked
          inputs actually contained such a member, and the run FAILS if that
          count is zero (a generator that cannot express the sub-domain must
          not certify it).  Pinned fuzz seed: 72233.

Exit 0 iff zero disagreements; on a disagreement print the input object and
both per-member outputs, then exit 1.  stdlib + numpy + xarray (the repo
under test) only.
"""
import json
import random
import sys
import warnings

import numpy as np

warnings.simplefilter("ignore")

SEED = 72233
N_FUZZ = 100_000
MAX_DISAGREEMENTS = 5

# The internal placeholder name the container uses for the array member on the
# DataArray arm. Read from the repo under test rather than hard-coded, so a
# rename in the repo cannot silently desynchronize the bridge.
def _placeholder_name():
    from xarray.core.dataarray import _THIS_ARRAY
    return _THIS_ARRAY


# ---------------------------------------------------------------------------
# Shadow: model.py pure + impl regions, contract statements stripped.
# ---------------------------------------------------------------------------

def promoted(was_label, is_window, is_axis_name):
    sel = 0
    if was_label == 1 and is_window == 1:
        sel = 1
    if was_label == 1:
        sel = 1
    if is_axis_name == 1:
        sel = 1
    return sel


def rebuild_label_status(was_label, is_window, is_axis_name):
    result = []
    i = 0
    while i < len(was_label):
        wl = was_label[i]
        iw = is_window[i]
        ax = is_axis_name[i]
        sel = 0
        if wl == 1 and iw == 1:
            sel = 1
        if wl == 1:
            sel = 1
        if ax == 1:
            sel = 1
        result = result + [sel]
        i = i + 1
    return result


# ---------------------------------------------------------------------------
# Bridge: real xarray object <-> parallel 0/1 membership-bit lists.
# ---------------------------------------------------------------------------

def member_names(obj):
    """The ordered member-name list of a Dataset/DataArray (mapping.md §2).
    For a DataArray the members are its coordinates plus the array itself
    (modelled as one plain data member; its name may be None)."""
    import xarray as xr
    if isinstance(obj, xr.Dataset):
        return list(obj.variables)
    return list(obj.coords) + [obj.name]


def insertion_names(obj, names):
    """The name each member is INSERTED under in the rebuilt container.
    Dataset arm: the member's own name. DataArray arm: the coordinates keep
    their names but the array member goes in under the container's internal
    placeholder (mapping.md §2), which is not an axis name."""
    import xarray as xr
    if isinstance(obj, xr.Dataset):
        return list(names)
    return list(names[:-1]) + [_placeholder_name()]


def coord_bits(obj, names):
    coords = set(obj.coords)
    return [1 if n in coords else 0 for n in names]


def window_bits(window_dim, names):
    keys = set(window_dim)
    return [1 if n in keys else 0 for n in names]


def _replacements(value):
    return [value] if isinstance(value, str) else list(value)


def rebuilt_axis_names(obj, window_dim):
    """The axis names of the rebuilt container, from the INPUT alone: a windowed
    axis contributes its replacement names, any other axis contributes itself."""
    axes = set()
    for d in obj.dims:
        if d in window_dim:
            axes.update(_replacements(window_dim[d]))
        else:
            axes.add(d)
    return axes


def axis_name_bits(obj, window_dim, names):
    axes = rebuilt_axis_names(obj, window_dim)
    return [1 if ins in axes else 0 for ins in insertion_names(obj, names)]


def check_one(obj, windows, window_dim):
    """Run shadow and oracle on one input; return (error_or_None, had_axis_bit)."""
    names = member_names(obj)
    was_label = coord_bits(obj, names)
    is_window = window_bits(window_dim, names)
    is_axis_name = axis_name_bits(obj, window_dim, names)

    # the model's Requires, by construction:
    assert len(was_label) == len(is_window)
    assert len(was_label) == len(is_axis_name)
    assert all(b in (0, 1) for b in was_label)
    assert all(b in (0, 1) for b in is_axis_name)

    shadow = rebuild_label_status(was_label, is_window, is_axis_name)

    out = obj.coarsen(windows).construct(window_dim)
    # the transform keeps the member-name universe fixed (mapping.md §2)
    out_names = member_names(out)
    if set(n for n in out_names if n is not None) != \
            set(n for n in names if n is not None):
        return ("MEMBER-UNIVERSE CHANGED\n  input: %r\n  members before: %r\n"
                "  members after:  %r" % (obj, names, out_names)), False
    # the axis-name bridge is CHECKED against the realized output, not assumed:
    # the input-derived rebuilt-axis set must be the output's actual axis set.
    if rebuilt_axis_names(obj, window_dim) != set(out.dims):
        return ("AXIS-NAME BRIDGE MISMATCH\n  input: %r\n  derived: %r\n"
                "  actual:  %r" % (obj, sorted(map(str, rebuilt_axis_names(
                    obj, window_dim))), sorted(map(str, set(out.dims))))), False
    real = coord_bits(out, names)

    had_axis_bit = 1 in is_axis_name
    if real != shadow:
        return ("DISAGREEMENT\n"
                "  input object: %r\n"
                "  windows=%r window_dim=%r\n"
                "  member names: %r\n"
                "  was_label:    %r\n"
                "  is_window:    %r\n"
                "  is_axis_name: %r\n"
                "  shadow bits:  %r\n"
                "  real bits:    %r"
                % (obj, windows, window_dim, names,
                   was_label, is_window, is_axis_name, shadow, real)), had_axis_bit
    return None, had_axis_bit


# ---------------------------------------------------------------------------
# Input generation (all satisfy the Requires by construction).
# ---------------------------------------------------------------------------

def boundary_cases():
    import xarray as xr
    cases = []

    def ds_case(data_vars, coords, windows, window_dim):
        cases.append((xr.Dataset(data_vars, coords=coords),
                      windows, window_dim))

    # dim coordinate on the windowed axis + plain data member
    ds_case({"v": ("t", np.arange(6.0))}, {"t": np.arange(6)},
            {"t": 3}, {"t": ("a", "b")})
    # non-dimension coordinate on the windowed axis (the F2P shape)
    ds_case({"v": ("t", np.arange(6.0))},
            {"t": np.arange(6), "c": ("t", np.arange(6) * 2)},
            {"t": 3}, {"t": ("a", "b")})
    # windowed axis with NO coordinate at all; one non-dim coordinate
    ds_case({"v": ("t", np.arange(6.0))}, {"c": ("t", np.arange(6.0))},
            {"t": 3}, {"t": ("a", "b")})
    # scalar (0-d) coordinate: a prior label with no axis at all
    ds_case({"v": ("t", np.arange(4.0))}, {"s": 3.14},
            {"t": 2}, {"t": ("a", "b")})
    # a plain data member NAMED like the windowed axis, on another axis
    ds_case({"t": ("x", np.arange(2.0)),
             "v": (("t", "x"), np.zeros((4, 2)))}, {},
            {"t": 2}, {"t": ("a", "b")})
    # coordinate-only object (no data members)
    ds_case({}, {"t": np.arange(4)}, {"t": 2}, {"t": ("a", "b")})
    # several coordinates and data members, two windowed axes
    ds_case({"v": (("t", "u"), np.arange(24.0).reshape(6, 4)),
             "w": ("u", np.arange(4.0)),
             "k": ((), 7.0)},
            {"t": np.arange(6), "c": ("t", np.arange(6.0)),
             "d": ("u", np.arange(4.0)), "s": 1},
            {"t": 3, "u": 2}, {"t": ("a", "b"), "u": ("p", "q")})
    # 0-dim data member alongside an uncoordinated windowed axis
    ds_case({"v": ("t", np.arange(4.0)), "z": ((), 0.5)}, {},
            {"t": 2}, {"t": ("a", "b")})

    # --- the axis-name sub-domain: a member whose name coincides with one of
    # the rebuilt container's axis names. Both replacement names, both
    # declaration roles (data member and coordinate), and both singly and
    # together, plus a coincidence with a SURVIVING (non-windowed) axis name.
    ds_case({"v": ("t", np.arange(6.0)), "a": ("x", np.arange(2.0))}, {},
            {"t": 3}, {"t": ("a", "b")})
    ds_case({"v": ("t", np.arange(6.0)), "b": ("x", np.arange(2.0))}, {},
            {"t": 3}, {"t": ("a", "b")})
    ds_case({"v": ("t", np.arange(6.0)), "a": ("x", np.arange(2.0)),
             "b": ("x", np.arange(2.0))}, {},
            {"t": 3}, {"t": ("a", "b")})
    ds_case({"v": ("t", np.arange(6.0)), "a": ("x", np.arange(2.0))},
            {"c": ("t", np.arange(6.0))}, {"t": 3}, {"t": ("a", "b")})
    ds_case({"v": ("t", np.arange(6.0))}, {"a": ("x", np.arange(2.0))},
            {"t": 3}, {"t": ("a", "b")})
    ds_case({"v": (("t", "u"), np.arange(24.0).reshape(6, 4)),
             "q": ("x", np.arange(2.0))},
            {}, {"t": 3, "u": 2}, {"t": ("a", "b"), "u": ("q", "r")})
    # a data member named like a SURVIVING axis (not created by the windowing)
    cases.append((
        xr.Dataset({"anchor": (("t", "x"), np.zeros((6, 2))),
                    "x": ("t", np.arange(6.0))}).reset_coords("x"),
        {"t": 3}, {"t": ("a", "b")}))
    # a data member named like the COARSENED axis, which does NOT survive
    cases.append((
        xr.Dataset({"anchor": (("t", "x"), np.zeros((6, 2))),
                    "t": ("x", np.arange(2.0))}).reset_coords("t"),
        {"t": 3}, {"t": ("a", "b")}))

    # DataArray members: coordinates + the array itself
    cases.append((
        xr.DataArray(np.arange(6.0), dims="t",
                     coords={"t": np.arange(6), "c": ("t", np.arange(6.0))},
                     name="arr"),
        {"t": 3}, {"t": ("a", "b")}))
    # DataArray whose windowed axis is uncoordinated, non-dim coord present
    cases.append((
        xr.DataArray(np.arange(4.0), dims="t",
                     coords={"c": ("t", np.arange(4.0))}, name="arr"),
        {"t": 2}, {"t": ("a", "b")}))
    # unnamed DataArray, dim coordinate only
    cases.append((
        xr.DataArray(np.arange(4.0), dims="t",
                     coords={"t": np.arange(4)}),
        {"t": 2}, {"t": ("a", "b")}))
    # DataArray whose OWN NAME coincides with a replacement axis name: the
    # array member is inserted under the placeholder, so its bit is 0 -- the
    # arm where naming genuinely differs from the Dataset arm.
    cases.append((
        xr.DataArray(np.arange(6.0), dims="t",
                     coords={"c": ("t", np.arange(6.0))}, name="a"),
        {"t": 3}, {"t": ("a", "b")}))
    cases.append((
        xr.DataArray(np.arange(6.0), dims="t",
                     coords={"t": np.arange(6)}, name="b"),
        {"t": 3}, {"t": ("a", "b")}))
    # DataArray whose COORDINATE name coincides with a surviving axis name
    cases.append((
        xr.DataArray(np.zeros((6, 2)), dims=("t", "p"),
                     coords={"p": np.arange(2)}, name="arr"),
        {"t": 3}, {"t": ("a", "b")}))
    # DataArray named like the coarsened axis (which does not survive)
    cases.append((
        xr.DataArray(np.arange(6.0), dims="t",
                     coords={"c": ("t", np.arange(6.0))}, name="t"),
        {"t": 3}, {"t": ("a", "b")}))
    return cases


# One shared alphabet for member names AND replacement axis names, so a member
# name can coincide with a rebuilt axis name. The old disjoint-alphabet
# generator could not express that sub-domain at all.
_ALPHABET = ["a", "b", "p", "q", "r", "s", "m0", "m1", "x", "anchor"]


def fuzz_case(rng):
    """One random Requires-satisfying input: a small Dataset (or DataArray)
    whose members mix every reachable (was_label, is_window, is_axis_name)
    role. Returns None when the draw is not a constructible xarray object."""
    import xarray as xr
    n_dims = rng.randint(1, 2)
    w = rng.choice([2, 3])
    size = w * rng.choice([1, 2])
    dims = ["d%d" % i for i in range(n_dims)]
    windows = {d: w for d in dims}

    # replacement axis names drawn from the SHARED alphabet
    window_dim = {}
    used = set()
    for d in dims:
        pair = []
        for _ in range(2):
            for _attempt in range(20):
                nm = rng.choice(_ALPHABET)
                if nm not in used and nm not in pair and nm not in dims:
                    pair.append(nm)
                    break
            else:
                return None
        used.update(pair)
        window_dim[d] = tuple(pair)

    data_vars = {}
    coords = {}
    # an anchor member spanning every windowed axis keeps them all present
    data_vars["anchor"] = (tuple(dims),
                           np.arange(float(size ** n_dims)).reshape(
                               (size,) * n_dims))
    for d in dims:
        role = rng.choice(["dimcoord", "named_data", "none"])
        if role == "dimcoord":
            # coordinate named like the windowed axis
            coords[d] = np.arange(size)
        elif role == "named_data":
            # data member named like the windowed axis, on another axis
            data_vars[d] = ("x", np.arange(2.0))
        # "none": the windowed axis has no member of its own name
    for j in range(rng.randint(0, 3)):
        # member names come from the SAME alphabet as the replacement axis
        # names, so coincidences arise by construction
        nm = rng.choice(_ALPHABET + ["extra%d" % j])
        if nm in data_vars or nm in coords or nm in dims or nm == "anchor":
            continue
        host = rng.choice(dims)
        kind = rng.randrange(5)
        if kind == 0:
            coords[nm] = (host, np.arange(float(size)))
        elif kind == 1:
            coords[nm] = float(j)
        elif kind == 2:
            data_vars[nm] = (host, np.arange(float(size)))
        elif kind == 3:
            data_vars[nm] = ((), float(j))
        else:
            data_vars[nm] = ("x", np.arange(2.0))
    try:
        ds = xr.Dataset(data_vars, coords=coords)
    except Exception:
        return None

    if n_dims == 1 and rng.random() < 0.2:
        # DataArray path: promote the anchor, carrying the coords along. The
        # array member's own name is varied (including onto the shared
        # alphabet) to exercise the placeholder-insertion arm.
        try:
            da = ds["anchor"]
            roll = rng.random()
            if roll < 0.3:
                da = da.rename(None)
            elif roll < 0.7:
                da = da.rename(rng.choice(_ALPHABET))
            return da, windows, window_dim
        except Exception:
            return None
    return ds, windows, window_dim


def main():
    checked = 0
    axis_name_cases = 0
    generated = 0
    gen_rejected = 0
    oracle_rejected = 0
    failures = []

    for obj, windows, window_dim in boundary_cases():
        err, had_axis = check_one(obj, windows, window_dim)
        checked += 1
        axis_name_cases += 1 if had_axis else 0
        if err:
            failures.append(err)
            if len(failures) >= MAX_DISAGREEMENTS:
                break
    n_boundary = checked

    if not failures:
        rng = random.Random(SEED)
        attempts = 0
        # Draw until N_FUZZ inputs have actually been CHECKED. Many draws are
        # not constructible xarray objects, or are objects the transform itself
        # rejects (an ill-formed reshape); those are not conformance evidence,
        # so they are counted separately and do not inflate `checked`.
        while checked - n_boundary < N_FUZZ and attempts < N_FUZZ * 40:
            attempts += 1
            case = fuzz_case(rng)
            if case is None:
                gen_rejected += 1
                continue
            generated += 1
            obj, windows, window_dim = case
            try:
                err, had_axis = check_one(obj, windows, window_dim)
            except AssertionError:
                raise
            except Exception:
                # the real transform refuses this input; not a modelled case
                oracle_rejected += 1
                continue
            checked += 1
            axis_name_cases += 1 if had_axis else 0
            if err:
                failures.append(err)
                if len(failures) >= MAX_DISAGREEMENTS:
                    break

    n_fuzz = checked - n_boundary

    if failures:
        print("G-CONF FAIL: %d disagreement(s) in %d checked inputs "
              "(seed=%d)." % (len(failures), checked, SEED))
        for f in failures:
            print(f)
        return 1

    # A generator that cannot express the axis-name sub-domain must not certify
    # it: the pre-repair generator drew member names and replacement axis names
    # from disjoint alphabets, so it reported zero disagreements on a sub-domain
    # it never entered. Refuse to pass on that shape.
    if axis_name_cases == 0:
        print("G-CONF FAIL: 0 of %d checked inputs contained a member whose "
              "insertion name coincides with a rebuilt axis name; the "
              "generator cannot express that sub-domain, so a 0-disagreement "
              "result is not evidence about it." % checked)
        return 1

    print(json.dumps({"checked": checked, "boundary": n_boundary,
                      "fuzz": n_fuzz, "disagreements": 0,
                      "axis_name_cases": axis_name_cases,
                      "generator_rejected": gen_rejected,
                      "oracle_rejected": oracle_rejected,
                      "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    print("G-CONF OK: model.py impl shadow agrees with the real patched "
          "rebuild outcome on %d inputs (%d boundary + %d fuzz, seed %d), "
          "%d of them exercising the axis-name sub-domain, 0 disagreements."
          % (checked, n_boundary, n_fuzz, SEED, axis_name_cases))
    return 0


if __name__ == "__main__":
    sys.exit(main())
