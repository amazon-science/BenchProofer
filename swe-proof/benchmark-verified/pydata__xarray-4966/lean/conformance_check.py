#!/usr/bin/env python3
"""G-CONF for pydata__xarray-4966.

The gold patch is already applied to /testbed when this runs. We compare the
R / I / A-reference Python shadow of `implementation_unsignedDecode` (the Lean
impl, transliterated op-for-op per refinement.md) against the REAL patched
`xarray.coding.variables.UnsignedIntegerCoder.decode`, over >=1e5 fuzzed inputs.
Zero disagreements on the modeled output components (values, dtype-kind,
itemsize, fill) => exit 0.

Type bijection (mapping.md):
  data        <-> np integer array values        (List Int <-> ndarray)
  kind        <-> data.dtype.kind ("i"/"u"/else) (.signed/.unsigned/.other)
  itemsize    <-> data.dtype.itemsize (bytes)
  fill        <-> attrs["_FillValue"] (Option Int: some present / none absent)
  unsignedAttr<-> attrs["_Unsigned"]  (Option String: present value / absent)
The oracle reinterpretation `reinterpAsUnsigned/reinterpAsSigned (8*itemsize)`
binds to the REAL `np.asarray(dtype="uN"/"iN")` width-preserving cast.
stdlib + numpy + xarray (the repo under test); no hypothesis required.
"""
import random
import sys

import numpy as np
import xarray as xr
from xarray.coding import variables

SEED = 4966  # pinned (mapping.md)

# Byte widths the routine supports: u1/i1 .. u8/i8 (numpy integer itemsizes).
BITSIZES = [1, 2, 4, 8]


# ---------------------------------------------------------------------------
# Oracle: drive the REAL patched UnsignedIntegerCoder.decode and read back the
# modeled output components.
# ---------------------------------------------------------------------------
def oracle(values, kind_char, itemsize, unsigned_attr, fill):
    """Behavior of the patched repo function, projected onto the modeled
    components. `kind_char` in {"i","u","f"}; `unsigned_attr` is None or a str;
    `fill` is None or a python int."""
    dtype = np.dtype("%s%d" % (kind_char, itemsize))
    arr = np.array(values, dtype=dtype)
    attrs = {}
    if unsigned_attr is not None:
        attrs["_Unsigned"] = unsigned_attr
    if fill is not None:
        # store the fill value in the array's own dtype, as the tests do
        attrs["_FillValue"] = dtype.type(fill)
    var = xr.Variable(("x",), arr, attrs=dict(attrs))
    coder = variables.UnsignedIntegerCoder()
    decoded = coder.decode(var)
    out_vals = np.asarray(decoded.values)  # materialize lazy transform
    out_kind = out_vals.dtype.kind
    out_itemsize = out_vals.dtype.itemsize
    out_fill = decoded.attrs.get("_FillValue", None)
    return (
        [int(v) for v in out_vals.tolist()],
        out_kind,
        out_itemsize,
        None if out_fill is None else int(out_fill),
    )


# ---------------------------------------------------------------------------
# Shadow: op-for-op transliteration of implementation_unsignedDecode (Lean).
# ---------------------------------------------------------------------------
def reinterp_as_unsigned(bits, x):
    return x % (2 ** bits)


def reinterp_as_signed(bits, x):
    m = 2 ** bits
    r = x % m
    return r - m if 2 * r >= m else r


def shadow(values, kind_char, itemsize, unsigned_attr, fill):
    """R/I/A-reference shadow. Returns (data, out_kind_char, out_itemsize, fill)."""
    kind = {"i": "signed", "u": "unsigned"}.get(kind_char, "other")
    data = list(values)
    out_kind = kind
    out_fill = fill
    if unsigned_attr is None:
        out_kind_char = {"signed": "i", "unsigned": "u"}.get(out_kind, kind_char)
        return data, out_kind_char, itemsize, out_fill
    u = unsigned_attr
    if kind == "signed":
        if u == "true":
            bits = 8 * itemsize
            data = [reinterp_as_unsigned(bits, x) for x in data]
            out_kind = "unsigned"
            out_fill = None if fill is None else reinterp_as_unsigned(bits, fill)
    elif kind == "unsigned":
        if u == "false":
            bits = 8 * itemsize
            data = [reinterp_as_signed(bits, x) for x in data]
            out_kind = "signed"
            out_fill = None if fill is None else reinterp_as_signed(bits, fill)
    out_kind_char = {"signed": "i", "unsigned": "u"}.get(out_kind, kind_char)
    return data, out_kind_char, itemsize, out_fill


UNSIGNED_POOL = [None, "true", "false", "True", "False", "1", "0", "yes"]


def rand_values(rng, kind_char, itemsize):
    info = np.iinfo(np.dtype("%s%d" % (kind_char, itemsize)))
    n = rng.randint(1, 5)
    out = []
    for _ in range(n):
        # bias toward boundaries (0, min, max, -1->wrap) plus uniform noise
        pick = rng.random()
        if pick < 0.25:
            out.append(int(info.max))
        elif pick < 0.45:
            out.append(int(info.min))
        elif pick < 0.55:
            out.append(0)
        else:
            out.append(rng.randint(int(info.min), int(info.max)))
    return out


def main():
    rng = random.Random(SEED)
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        kind_char = rng.choice(["i", "u", "f"])
        itemsize = rng.choice(BITSIZES)
        unsigned_attr = rng.choice(UNSIGNED_POOL)
        if kind_char == "f":
            # non-integer kind: the routine ignores the attribute (pass-through).
            # Use an integer-valued float array so values compare cleanly.
            itemsize = rng.choice([2, 4, 8])
            vals = [float(rng.randint(-100, 100)) for _ in range(rng.randint(1, 4))]
            dtype = np.dtype("f%d" % itemsize)
            arr = np.array(vals, dtype=dtype)
            attrs = {}
            if unsigned_attr is not None:
                attrs["_Unsigned"] = unsigned_attr
            var = xr.Variable(("x",), arr, attrs=dict(attrs))
            decoded = variables.UnsignedIntegerCoder().decode(var)
            o_vals = np.asarray(decoded.values)
            o = ([float(v) for v in o_vals.tolist()], o_vals.dtype.kind, o_vals.dtype.itemsize)
            s_vals = list(vals)
            s = (s_vals, "f", itemsize)
            if o != s:
                disagreements += 1
                if first is None:
                    first = (kind_char, itemsize, unsigned_attr, vals, o, s)
            continue

        values = rand_values(rng, kind_char, itemsize)
        # optionally include a fill value
        if rng.random() < 0.5:
            info = np.iinfo(np.dtype("%s%d" % (kind_char, itemsize)))
            fill = rng.choice([int(info.max), int(info.min), 0,
                               rng.randint(int(info.min), int(info.max))])
        else:
            fill = None

        o = oracle(values, kind_char, itemsize, unsigned_attr, fill)
        s = shadow(values, kind_char, itemsize, unsigned_attr, fill)
        if o != s:
            disagreements += 1
            if first is None:
                first = (kind_char, itemsize, unsigned_attr, values, fill, o, s)

    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
