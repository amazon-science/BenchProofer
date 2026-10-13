#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-4966.

Executes the REAL library callee (`numpy.asarray(arr, dtype=target)` — the
elementwise transform the gold patch builds with
`partial(np.asarray, dtype=signed_dtype)`) on boundary inputs and randomized
fuzz across all four integer widths, and asserts that every observation matches
the model encoded in Solution.lean.

The single kind-A check (there are NO consumed axioms):

  (A-reference) the deep model `apply_cast` / `cast_seq` (Solution.lean pure
      region) == the real `np.asarray(arr, dtype=target)`, elementwise, for both
      reinterpret directions and all widths bits ∈ {8,16,32,64}:
        toUnsigned(bits): x -> x        if x >= 0
                               x+2^bits if x <  0      (i%d -> u%d)
        toSigned(bits):   x -> x        if x <  2^(bits-1)
                               x-2^bits if x >= 2^(bits-1)   (u%d -> i%d)

In addition, the full dispatch `choose_mode` (the patched `decode` branch logic)
is checked against a direct re-implementation of the patched control flow, so the
A2 (dispatch) and A4 (resulting kind) refinement legs are exercised here too.

Imports only `numpy` (the same library the gold patch calls) + stdlib. Exit 0
iff every obligation holds.
"""
import random
import sys

import numpy as np


# --- Solution.lean reference encodings (kept in lock-step with the spec) -----

def apply_cast(mode, bits, x):
    """Reference of Solution.lean `applyCast`: per-element reinterpret as a
    Python int."""
    if mode == "toUnsigned":
        return x if x >= 0 else x + (1 << bits)
    if mode == "toSigned":
        return x if x < (1 << (bits - 1)) else x - (1 << bits)
    if mode == "keep":
        return x
    raise AssertionError("unknown mode %r" % mode)


def cast_seq(mode, bits, values):
    return [apply_cast(mode, bits, x) for x in values]


def choose_mode(kind, attr, bits):
    """Reference of Solution.lean `chooseMode`: (mode, resulting_kind)."""
    if attr is None:
        return ("keep", kind)
    if kind == "i":
        if attr == "true":
            return ("toUnsigned", "u")
        return ("keep", kind)
    if kind == "u":
        if attr == "false":
            return ("toSigned", "i")
        return ("keep", kind)
    return ("keep", kind)


# --- the checks --------------------------------------------------------------

def check_reinterpret_reference(src_kind, dst_kind, bits, x):
    """Assert apply_cast(...) == the REAL np.asarray(dtype=dst) elementwise."""
    itemsize = bits // 8
    src_dtype = np.dtype("%s%d" % (src_kind, itemsize))
    dst_dtype = np.dtype("%s%d" % (dst_kind, itemsize))
    arr = np.array([x], dtype=src_dtype)              # the stored element
    real = int(np.asarray(arr, dtype=dst_dtype)[0])   # REAL callee
    mode = "toUnsigned" if dst_kind == "u" else "toSigned"
    # the model operates on the element value as carried by its current dtype
    model = apply_cast(mode, bits, int(arr[0]))
    assert real == model, (
        "apply_cast deep model unsound: %s%d->%s%d on stored %r: "
        "np.asarray gave %r, model gives %r"
        % (src_kind, itemsize, dst_kind, itemsize, int(arr[0]), real, model))


def main():
    widths = [8, 16, 32, 64]

    # --- apply_cast deep model (A-reference): boundary cases per width -------
    n_boundary = 0
    for bits in widths:
        umax = (1 << bits) - 1
        smin, smax = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
        mid = 1 << (bits - 1)
        # unsigned -> signed (the NEW branch): every interesting unsigned value
        u_boundary = sorted(set([0, 1, mid - 1, mid, mid + 1, umax,
                                 umax - 1, umax // 2]))
        for x in u_boundary:
            check_reinterpret_reference("u", "i", bits, x)
            n_boundary += 1
        # signed -> unsigned (the existing branch): every interesting signed value
        s_boundary = sorted(set([0, 1, -1, smin, smin + 1, smax, smax - 1, -2]))
        for x in s_boundary:
            check_reinterpret_reference("i", "u", bits, x)
            n_boundary += 1

    # --- apply_cast deep model (A-reference): randomized fuzz ----------------
    rng = random.Random(4966)
    n_fuzz = 0
    for bits in widths:
        umax = (1 << bits) - 1
        smin, smax = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
        for _ in range(5000):
            check_reinterpret_reference("u", "i", bits, rng.randint(0, umax))
            check_reinterpret_reference("i", "u", bits, rng.randint(smin, smax))
            n_fuzz += 2

    # --- choose_mode dispatch (A2/A4): exhaustive over the observed inputs ----
    # Mirror the patched decode control flow exactly.
    def patched_decode_branch(kind, attr):
        """(transform_target_kind_or_None, resulting_kind) per the gold patch."""
        if attr is None:                       # "_Unsigned" not in attrs
            return (None, kind)
        if kind == "i":
            return (("u" if attr == "true" else None), "u" if attr == "true" else kind)
        if kind == "u":                        # the ADDED elif branch
            return (("i" if attr == "false" else None), "i" if attr == "false" else kind)
        return (None, kind)                    # else: warn, unchanged

    n_dispatch = 0
    for kind in ["i", "u", "f"]:
        for attr in [None, "true", "false", "True", "False", "1", ""]:
            tgt, rkind = patched_decode_branch(kind, attr)
            mode, mkind = choose_mode(kind, attr, 8)
            exp_mode = "keep" if tgt is None else ("toUnsigned" if tgt == "u" else "toSigned")
            assert mode == exp_mode and mkind == rkind, (
                "choose_mode dispatch unsound for kind=%r attr=%r: model=(%r,%r) "
                "patched-decode=(%r,%r)" % (kind, attr, mode, mkind, exp_mode, rkind))
            n_dispatch += 1

    # --- F2P witness: the exact tested transform (unsigned max -> -1, etc.) ---
    for bits in widths:
        itemsize = bits // 8
        u = np.dtype("u%d" % itemsize)
        s = np.dtype("i%d" % itemsize)
        # test_decode_signed_from_unsigned: original signed -1 stored as unsigned,
        # decoded back to signed must be -1 again.
        original = np.array([-1], dtype=s)
        stored = original.astype(u)            # the unsigned representation
        decoded = np.asarray(stored, dtype=s)  # REAL transform the patch applies
        model = cast_seq("toSigned", bits, [int(stored[0])])
        assert int(decoded[0]) == model[0] == -1, (
            "F2P witness broken at bits=%d: stored=%r decoded=%r model=%r"
            % (bits, int(stored[0]), int(decoded[0]), model))

    print("G-AX OK: apply_cast deep model (== np.asarray reinterpret) sound on "
          "%d boundary + %d fuzz elements over 4 widths; choose_mode dispatch "
          "matches patched decode on %d configs; F2P witness holds."
          % (n_boundary, n_fuzz, n_dispatch))
    return 0


if __name__ == "__main__":
    sys.exit(main())
