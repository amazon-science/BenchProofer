#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-14508 (nagini).

SHADOW: the impl region of model.py `format_float_field`, copied verbatim below
with the contract calls (Requires/Ensures/Invariant/Assert) stripped and PSeq
realized as an immutable tuple shim (ToSeq wraps a list into it). The @Pure
helpers `e_index` / `e_index_from` copy over as plain functions. The one
@ContractOnly callee the impl invokes, `shortest_field`, is realized by its
REAL callee per mapping.md section 3.1: the stdlib shortest round-tripping
float rendering (`str(value)`) with the exponent marker upper-cased, returned
as a fresh list of code points. (`shortest_seq` / `parse_dec` / `sig_count` /
`min_sig` / `shortest_field_len` / `padded_field` appear only inside contracts,
so they have no executable role here.)

ORACLE: the REAL patched repo function the model models per mapping.md —
`astropy.io.fits.card._format_float`. The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched module
importable.

Type bridge (mapping.md section 2): the rendered field is a `str` in the repo
and a `List[int]` of code points in the model; the bijection is
`field[k] == ord(s[k])`. The shadow's output list is joined back to a `str`
via `chr` and compared to the oracle's return value for exact equality.

The INPUT bridge is the pair refinement: a finite double `d` refines to
`(value, neg) = (d + 0.0, signbit(d))`. `d + 0.0` is bit-identical to `d` for
every finite nonzero `d` and maps -0.0 to +0.0, so the pair is a complete
invariant of `d` -- for nonzero `d` the value determines it, at zero the flag
does. The oracle is called on `d`; the shadow on the pair `d` refines to. That is
what lets the differential witness the two zeros, which an interpreted real
identifies but the real renderer distinguishes ("0.0" vs "-0.0").

Input domain: the precondition region restricts the renderer to finite real
numbers (non-finite values are rejected upstream of the callee and never reach
it), so generation draws only finite doubles: boundary values covering both
the fits-within-cap and over-cap branches (fixed-notation and scientific-
notation trims), plus randomized fuzz over raw 64-bit patterns, mantissa x
10^exp products, small integers, and subnormals.

>= 1e5 Requires-satisfying inputs: boundary cases + >=100000 fuzz values.
Pinned fuzz seed: 14508.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import math
import random
import struct
import sys

SEED = 14508
N_FUZZ_BITS = 60_000
N_FUZZ_EXP = 40_000
N_FUZZ_SUB = 10_000


# --- PSeq shim: immutable sequence, the operations the impl region uses ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    """Materialize a list as a pure sequence (the Nagini ToSeq bridge)."""
    return PSeq._wrap(lst)


# --- the @ContractOnly callee, realized by its REAL callee (mapping.md 3.1) ---

def _as_double(value, neg):
    """The finite double the pair `(value, neg)` denotes."""
    return math.copysign(value, -1.0 if neg else 1.0)


def canon(d):
    """The pair a finite double refines to: (magnitude representative, sign)."""
    return (d + 0.0, math.copysign(1.0, d) < 0.0)


def shortest_field(value, neg):
    """Minimal-significant-digit exact rendering of the number the pair denotes,
    with an upper-case exponent marker, as a fresh list of code points."""
    return [ord(ch) for ch in str(_as_double(value, neg)).replace("e", "E")]


# --- pure helpers from model.py, contracts stripped ---------------------------

def e_index(field):
    """Index of the first exponent marker `E` (code point 69) in `field`, or -1
    if there is none."""
    return e_index_from(field, 0)


def e_index_from(field, i):
    """First index >= i of the exponent marker `E` in `field`, or -1."""
    if i == len(field):
        return -1
    if field[i] == 69:
        return i
    return e_index_from(field, i + 1)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def format_float_field(value, neg):
    vs = shortest_field(value, neg)
    n = len(vs)
    if n <= 20:
        return vs
    # Over the cap: trim to 20 characters, preserving any exponent suffix. The
    # carrier `vs` IS the exact rendering (ToSeq(vs) == shortest_seq(value)), so
    # the trim is stated structurally against it via take/drop/concat.
    idx = e_index(ToSeq(vs))
    result = []  # type: list
    old_seq = ToSeq(result)  # type carrier for the per-append step (see below)
    if idx < 0:
        j = 0
        while j < 20:
            old_seq = ToSeq(result)
            result.append(vs[j])
            j = j + 1
    else:
        keep = 20 - (n - idx)
        j = 0
        while j < keep:
            old_seq = ToSeq(result)
            result.append(vs[j])
            j = j + 1
        k = idx
        while k < n:
            old_seq = ToSeq(result)
            result.append(vs[k])
            k = k + 1
    return result
    # (impl region ends)


# --- differential driver -------------------------------------------------------

def check_value(real_fn, value):
    """Run shadow and oracle on one finite float; return an error string on
    disagreement, else None."""
    shadow = format_float_field(*canon(value))
    shadow_str = "".join(chr(c) for c in shadow)
    real_str = real_fn(value)
    if shadow_str != real_str:
        return ("DISAGREEMENT\n  value=%r (bits=0x%016x)\n  shadow=%r\n  real=%r"
                % (value, struct.unpack("<Q", struct.pack("<d", value))[0],
                   shadow_str, real_str))
    return None


def boundary_values():
    vals = [
        0.0, -0.0, 1.0, -1.0, 0.5, -0.5, 100.0, -100.0,
        0.009125, 8.95, -99.9, 0.1, 0.2, 0.3, 8.7,
        # over-cap, scientific notation (exponent suffix preserved by the trim)
        -467374636747637647347374734737437.0,
        1.2345377437887837487e88,
        6324767364763746367e-33,
        # over-cap candidates in fixed notation
        1.0 / 3.0, 2.0 / 3.0, math.pi, math.e,
        0.1 + 0.2,
        # exponent-range extremes and subnormals
        1e-10, 1e10, 1e100, 1e-100, 1e308, -1e308, 5e-324, -5e-324,
        2.2250738585072014e-308,
        (1 - 2 ** -53) * 2 ** -60,
        (1 - 2 ** -53) * 2 ** 0,
        (1 - 2 ** -53) * 2 ** 60,
        2 ** -24,
        1e16, 1e17, -1e16,     # around the fixed/scientific rendering switch
        9999999999999998.0,
        123456789012345678901.0,
    ]
    return vals


def main():
    from astropy.io.fits.card import _format_float  # REAL patched callee

    checked = 0
    for v in boundary_values():
        assert math.isfinite(v)
        err = check_value(_format_float, v)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)

    # raw 64-bit patterns -> doubles (skip non-finite: outside the domain)
    for _ in range(N_FUZZ_BITS):
        bits = rng.getrandbits(64)
        v = struct.unpack("<d", struct.pack("<Q", bits))[0]
        if not math.isfinite(v):
            continue
        err = check_value(_format_float, v)
        if err:
            print(err)
            return 1
        checked += 1

    # mantissa x 10^exp products (dense around human-scale magnitudes)
    for _ in range(N_FUZZ_EXP):
        mant = rng.uniform(-10.0, 10.0)
        exp = rng.randint(-308, 308)
        v = mant * (10.0 ** exp)
        if not math.isfinite(v):
            continue
        err = check_value(_format_float, v)
        if err:
            print(err)
            return 1
        checked += 1

    # small integers-as-floats and subnormal-range draws
    for i in range(-2000, 2001):
        err = check_value(_format_float, float(i))
        if err:
            print(err)
            return 1
        checked += 1
    for _ in range(N_FUZZ_SUB):
        v = rng.uniform(-1e-300, 1e-300)
        if not math.isfinite(v):
            continue
        err = check_value(_format_float, v)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real renderer on %d finite-float inputs "
          "(%d boundary + fuzz, seed %d)."
          % (checked, len(boundary_values()), SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
