#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-4966 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (`List Int` ↔ integer ndarray; `IntKind` ↔ dtype.kind; `attr`
              ↔ the `_Unsigned` attribute string). The dispatch `chooseMode`
              and the elementwise reinterpret `applyCast`/`castSeq` are pure R/I
              content; there is no A-tagged callee left in the computed result
              (the only A content, `np.asarray`, IS the integer reinterpret the
              shadow computes directly and G-AX validates separately).
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `xarray.coding.variables.UnsignedIntegerCoder.decode` applied at
              base_commit (the real correctness oracle, G-RESOLVE). Observes the
              decoded element values and the decoded dtype kind.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), numpy + xarray (the
repo under test). The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import random
import sys

import numpy as np

SEED = 4966
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean chooseMode/applyCast/castSeq -------------

def _choose_mode(kind, attr, bits):
    """Solution.lean `chooseMode` transliterated: (mode, resulting_kind)."""
    if attr is None:
        return ("keep", kind)
    if kind == "i":
        return (("toUnsigned", "u") if attr == "true" else ("keep", kind))
    if kind == "u":
        return (("toSigned", "i") if attr == "false" else ("keep", kind))
    return ("keep", kind)


def _apply_cast(mode, bits, x):
    if mode == "toUnsigned":
        return x if x >= 0 else x + (1 << bits)
    if mode == "toSigned":
        return x if x < (1 << (bits - 1)) else x - (1 << bits)
    return x


def shadow_decode(kind, bits, attr, values):
    """Solution.lean decodeModel: (resulting_kind, reinterpreted values)."""
    mode, rkind = _choose_mode(kind, attr, bits)
    return rkind, [_apply_cast(mode, bits, int(x)) for x in values]


# --- the oracle: the patched repo decode ------------------------------------

def oracle_decode(kind, bits, attr, values):
    """patch.diff's behaviour: run the patched UnsignedIntegerCoder.decode and
    observe (decoded.dtype.kind, decoded element values)."""
    import warnings

    import xarray as xr
    from xarray.coding import variables

    itemsize = bits // 8
    dtype = np.dtype("%s%d" % (kind, itemsize))
    arr = np.array(values, dtype=dtype)
    attrs = {} if attr is None else {"_Unsigned": attr}
    var = xr.Variable(("x",), arr, attrs=attrs)
    coder = variables.UnsignedIntegerCoder()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")           # the non-integer branch warns
        decoded = coder.decode(var)
    out_vals = [int(v) for v in np.asarray(decoded.values).reshape(-1)]
    return decoded.dtype.kind, out_vals


# --- fuzz inputs -------------------------------------------------------------

def fuzz_inputs(n, rng):
    widths = [8, 16, 32, 64]
    kinds = ["i", "u", "f"]
    attrs = [None, "true", "false", "True", "False", "1", ""]

    # boundary cases first (plan §4.1 step 4): the F2P configuration and its
    # extremes for every width and the relevant (kind, attr) pairs.
    for bits in widths:
        itemsize = bits // 8
        umax = (1 << bits) - 1
        smin, smax = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
        mid = 1 << (bits - 1)
        # the new branch: unsigned data + "_Unsigned":"false"
        yield ("u", bits, "false", [0, 1, mid - 1, mid, mid + 1, umax, umax // 2])
        yield ("u", bits, "false", [umax])              # the F2P -1 witness
        yield ("u", bits, None, [0, mid, umax])
        yield ("u", bits, "true", [0, mid, umax])       # non-matching value
        # the existing branch: signed data + "_Unsigned":"true"
        yield ("i", bits, "true", [0, 1, -1, smin, smax, -2])
        yield ("i", bits, None, [0, -1, smin, smax])
        yield ("i", bits, "false", [0, -1, smin])       # non-matching value
        yield ("u", bits, "false", [])                  # empty array
        yield ("i", bits, "true", [])

    for _ in range(n):
        kind = rng.choice(kinds)
        attr = rng.choice(attrs)
        if kind == "f":
            bits = rng.choice([16, 32, 64])   # numpy has no f1 (1-byte float)
            lo, hi = -8, 8                      # small ints, exactly float-representable
        elif kind == "u":
            bits = rng.choice(widths)
            lo, hi = 0, (1 << bits) - 1
        else:  # "i"
            bits = rng.choice(widths)
            lo, hi = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
        length = rng.randint(0, 6)
        vals = [rng.randint(lo, hi) for _ in range(length)]
        yield (kind, bits, attr, vals)


def _norm_values(kind, bits, values):
    """For a float ('f') kind there is no integer reinterpret; the shadow keeps
    values, and so does the oracle (the non-integer branch). Compare as floats
    to avoid int/float representation noise; for integer kinds compare as ints."""
    if kind == "f":
        return [float(v) for v in values]
    return [int(v) for v in values]


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for kind, bits, attr, vals in fuzz_inputs(N_FUZZ, rng):
        count += 1
        s_kind, s_vals = shadow_decode(kind, bits, attr, vals)
        o_kind, o_vals = oracle_decode(kind, bits, attr, vals)
        # for the float kind the dtype kind char stays "f"; the shadow's "f"
        # resulting kind matches. Compare kind char and the element values.
        if (s_kind != o_kind) or (_norm_values(s_kind, bits, s_vals)
                                  != _norm_values(o_kind, bits, o_vals)):
            disagreements.append((kind, bits, attr, vals, (s_kind, s_vals),
                                  (o_kind, o_vals)))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for k, b, a, v, sh, orc in disagreements:
            print("  kind=%r bits=%r attr=%r vals=%r shadow=%r oracle=%r"
                  % (k, b, a, v, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of decodeUnsigned agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
