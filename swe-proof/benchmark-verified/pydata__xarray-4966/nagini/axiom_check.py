#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-4966.

Executes the REAL element-wise array conversion the patch performs
(`numpy.asarray(data, dtype=target_dtype)` for the array, and the scalar form
`np.dtype(target_dtype).type(fill)` for the fill value) and asserts that every
observation matches the model's DEEP model of the changed operation, as encoded
in model.py:

  (A-reference) the deep model `reinterpret(v, modulus, to_signed)` (model.py
      pure region) == the real fixed-width reinterpretation between the signed
      and unsigned views of one bit pattern, in BOTH directions:

        * to_signed   (unsigned-stored -> signed view):
              np.asarray([v], dtype="i%s" % itemsize)
              == v if v < modulus/2 else v - modulus      (e.g. max -> -1)
        * to_unsigned (signed-stored -> unsigned view):
              np.asarray([v], dtype="u%s" % itemsize)
              == v if v >= 0 else v + modulus              (e.g. -1 -> max)

      and `convert_fill` (the same rule applied to the scalar fill via
      `target_dtype.type(fill)`).

There are NO consumed (@ContractOnly) axioms in this bundle: the only opaque
callee is the *changed* element transform, modelled deeply and validated here.

Imports nothing repo-specific: `numpy` is the very module the gold patch calls.
Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np


# --- model.py reference encodings (kept in lock-step with the pure region) ---

def reinterpret(v, modulus, to_signed):
    """Reference implementation of model.py's deep model `reinterpret`."""
    assert modulus >= 2
    if to_signed:
        if v >= modulus // 2:
            return v - modulus
        return v
    else:
        if v < 0:
            return v + modulus
        return v


def convert_fill(v, modulus, to_signed):
    """model.py's `fill_out` reduces to `reinterpret` in the transformed cases."""
    return reinterpret(v, modulus, to_signed)


# --- the checks --------------------------------------------------------------

WIDTHS = [1, 2, 4, 8]  # itemsize in bytes -> 8/16/32/64 bits


def real_to_signed(v, itemsize):
    """REAL callee: reinterpret unsigned value v as the signed dtype of width."""
    signed_dtype = np.dtype("i%s" % itemsize)
    unsigned_dtype = np.dtype("u%s" % itemsize)
    arr = np.array([v], dtype=unsigned_dtype)            # store unsigned
    out = np.asarray(arr, dtype=signed_dtype)            # the patch's transform
    scalar = signed_dtype.type(unsigned_dtype.type(v))   # the fill transform
    return int(out[0]), int(scalar)


def real_to_unsigned(v, itemsize):
    """REAL callee: reinterpret signed value v as the unsigned dtype of width."""
    signed_dtype = np.dtype("i%s" % itemsize)
    unsigned_dtype = np.dtype("u%s" % itemsize)
    arr = np.array([v], dtype=signed_dtype)              # store signed
    out = np.asarray(arr, dtype=unsigned_dtype)          # the existing transform
    scalar = unsigned_dtype.type(signed_dtype.type(v))   # the fill transform
    return int(out[0]), int(scalar)


def check_to_signed(v, itemsize):
    modulus = 1 << (8 * itemsize)
    obs_arr, obs_scalar = real_to_signed(v, itemsize)
    exp = reinterpret(v % modulus, modulus, True)
    assert obs_arr == exp, (
        "reinterpret(to_signed) deep model unsound: width=%d v=%d "
        "real np.asarray gave %d, deep model gives %d"
        % (itemsize, v, obs_arr, exp))
    assert obs_scalar == convert_fill(v % modulus, modulus, True), (
        "convert_fill(to_signed) deep model unsound: width=%d v=%d "
        "real dtype.type gave %d, deep model gives %d"
        % (itemsize, v, obs_scalar, convert_fill(v % modulus, modulus, True)))


def check_to_unsigned(v, itemsize):
    modulus = 1 << (8 * itemsize)
    obs_arr, obs_scalar = real_to_unsigned(v, itemsize)
    # bring v into the signed range of this width (two's-complement view)
    signed_v = ((v + modulus // 2) % modulus) - modulus // 2
    exp = reinterpret(signed_v, modulus, False)
    assert obs_arr == exp, (
        "reinterpret(to_unsigned) deep model unsound: width=%d v=%d "
        "real np.asarray gave %d, deep model gives %d"
        % (itemsize, v, obs_arr, exp))
    assert obs_scalar == convert_fill(signed_v, modulus, False), (
        "convert_fill(to_unsigned) deep model unsound: width=%d v=%d "
        "real dtype.type gave %d, deep model gives %d"
        % (itemsize, v, obs_scalar, convert_fill(signed_v, modulus, False)))


def main():
    checked = 0

    # --- exhaustive domains for the two small widths (8 and 16 bits) ---------
    for itemsize in (1, 2):
        modulus = 1 << (8 * itemsize)
        for u in range(modulus):                 # every unsigned value
            check_to_signed(u, itemsize)
            checked += 1
        half = modulus // 2
        for s in range(-half, half):             # every signed value
            check_to_unsigned(s, itemsize)
            checked += 1

    # --- boundary values for every width, both directions --------------------
    for itemsize in WIDTHS:
        modulus = 1 << (8 * itemsize)
        half = modulus // 2
        unsigned_boundaries = [0, 1, half - 1, half, half + 1, modulus - 1]
        for u in unsigned_boundaries:
            check_to_signed(u, itemsize)
            checked += 1
        signed_boundaries = [-half, -half + 1, -1, 0, 1, half - 1]
        for s in signed_boundaries:
            check_to_unsigned(s, itemsize)
            checked += 1

    # --- randomized fuzz across all widths, both directions ------------------
    rng = random.Random(4966)
    for _ in range(40000):
        itemsize = rng.choice(WIDTHS)
        modulus = 1 << (8 * itemsize)
        half = modulus // 2
        check_to_signed(rng.randrange(0, modulus), itemsize)
        check_to_unsigned(rng.randrange(-half, half), itemsize)
        checked += 2

    # --- the specific F2P witnesses: max-unsigned decodes to -1 (signed) -----
    for itemsize in WIDTHS:
        modulus = 1 << (8 * itemsize)
        obs_arr, obs_scalar = real_to_signed(modulus - 1, itemsize)
        assert obs_arr == -1 and obs_scalar == -1, (
            "F2P witness broken: width=%d iinfo.max should decode to -1, got %d"
            % (itemsize, obs_arr))
        checked += 1

    print("G-AX OK: reinterpret/convert_fill deep model (== numpy.asarray / "
          "dtype.type) sound over %d checks (exhaustive 8+16 bit both "
          "directions + boundaries + 80000 fuzz + F2P max->-1 witnesses)"
          % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
