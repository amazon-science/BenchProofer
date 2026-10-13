#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-4966 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert and the Acc/ToSeq framing) stripped.
The @Pure helpers (`reinterpret`, `reinterpret_seq`, `transform_to_signed`,
`transform_to_unsigned`, `is_transformed`, `fill_out`) copy over as plain
functions; PSeq is realized as an immutable tuple shim (only `reinterpret_seq`
uses it — it is exercised as an internal cross-check of the impl loops against
the pure fold). There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo method the model models per mapping.md —
`xarray.coding.variables.UnsignedIntegerCoder.decode`. The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched module importable. Each probe builds a `Variable` holding a fixed-width
integer array with the signedness-request attribute (and optionally a sentinel
fill attribute), decodes it, and materialises `.values`.

Type bridge (mapping.md section 2):
  * a fixed-width integer numpy array <-> List[int] of per-element values
    (kind "u": values in [0, modulus); kind "i": values in [-modulus/2,
    modulus/2)); element order preserved;
  * dtype kind "i"/"u" <-> kind code 0/1; itemsize 1/2/4/8 bytes <->
    modulus == 2**(8*itemsize);
  * the request attribute string "false"/"true"/anything-else <-> the
    unsigned code 0/1/2;
  * sentinel fill: presence <-> has_fill, its integer value <-> fill; the
    decoded fill read back from the decoded variable's attributes <->
    fill_out(kind, unsigned, modulus, fill).
The decoded array's element values (as Python ints) compare against the
shadow's List[int]; the lazy element-wise wrapper materialises on `.values`,
which is exactly the observation the mapping identifies.

Input domain: Requires demands kind in {0,1}, unsigned in {0,1,2},
modulus >= 2; the bridge further restricts element/fill values to the
storage width's range (the carrier bijection's domain). Arrays of length
0..6 across all four widths, both kinds, and request strings covering all
three codes (including a case-mismatched string for the "other" code).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz probes.
Pinned fuzz seed: 4966.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy only.
"""
import json
import random
import sys
import warnings

import numpy as np

SEED = 4966
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the pure helpers use ------

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


# --- pure region of model.py, contracts stripped ------------------------------

KIND_SIGNED = 0
KIND_UNSIGNED = 1
ATTR_FALSE = 0
ATTR_TRUE = 1
ATTR_OTHER = 2


def reinterpret(v, modulus, to_signed):
    if to_signed:
        if v >= modulus // 2:
            return v - modulus
        return v
    else:
        if v < 0:
            return v + modulus
        return v


def reinterpret_seq(s, modulus, to_signed):
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(reinterpret(s[0], modulus, to_signed)) + \
        reinterpret_seq(s.drop(1), modulus, to_signed)


def transform_to_signed(kind, unsigned):
    return kind == KIND_UNSIGNED and unsigned == ATTR_FALSE


def transform_to_unsigned(kind, unsigned):
    return kind == KIND_SIGNED and unsigned == ATTR_TRUE


def is_transformed(kind, unsigned):
    return transform_to_signed(kind, unsigned) or \
        transform_to_unsigned(kind, unsigned)


def fill_out(kind, unsigned, modulus, fill):
    if transform_to_signed(kind, unsigned):
        return reinterpret(fill, modulus, True)
    elif transform_to_unsigned(kind, unsigned):
        return reinterpret(fill, modulus, False)
    else:
        return fill


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def reconcile_signedness(data, kind, unsigned, modulus, has_fill, fill):
    result = []  # type: list
    if transform_to_signed(kind, unsigned):
        # unsigned-stored array, requested signed -> signed view of each element
        i = len(data)
        while i > 0:
            result = [reinterpret(data[i - 1], modulus, True)] + result
            i = i - 1
    elif transform_to_unsigned(kind, unsigned):
        # signed-stored array, requested unsigned -> unsigned view of each elem
        i = len(data)
        while i > 0:
            result = [reinterpret(data[i - 1], modulus, False)] + result
            i = i - 1
    else:
        # request matches storage or is absent/uninterpretable: pass through
        i = len(data)
        while i > 0:
            result = [data[i - 1]] + result
            i = i - 1
    return result


# --- bridge + oracle driver ----------------------------------------------------

# request attribute string -> the model's unsigned code
def attr_code(s):
    if s == "false":
        return ATTR_FALSE
    if s == "true":
        return ATTR_TRUE
    return ATTR_OTHER


def check_case(coder, Variable, itemsize, kind_char, unsigned_str, values,
               fill):
    """Run shadow and oracle on one probe; return an error string on
    disagreement, else None."""
    modulus = 1 << (8 * itemsize)
    kind = KIND_SIGNED if kind_char == "i" else KIND_UNSIGNED
    unsigned = attr_code(unsigned_str)
    has_fill = fill is not None

    # shadow (contract-stripped impl region)
    shadow_vals = reconcile_signedness(list(values), kind, unsigned, modulus,
                                       has_fill, fill if has_fill else 0)
    shadow_fill = fill_out(kind, unsigned, modulus, fill) if has_fill else None

    # internal cross-check: the impl loops agree with the pure fold
    if transform_to_signed(kind, unsigned):
        assert PSeq._wrap(shadow_vals) == \
            reinterpret_seq(PSeq._wrap(values), modulus, True)
    elif transform_to_unsigned(kind, unsigned):
        assert PSeq._wrap(shadow_vals) == \
            reinterpret_seq(PSeq._wrap(values), modulus, False)

    # oracle (real patched repo method)
    dtype = np.dtype("%s%d" % (kind_char, itemsize))
    arr = np.array(values, dtype=dtype)
    attrs = {"_Unsigned": unsigned_str}
    if has_fill:
        attrs["_FillValue"] = dtype.type(fill)
    var = Variable(("x",), arr, attrs)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        decoded = coder.decode(var)
        real_vals = [int(v) for v in np.asarray(decoded.values).ravel()]
        rf = decoded.attrs.get("_FillValue")
        real_fill = int(rf) if rf is not None else None

    if shadow_vals != real_vals or shadow_fill != real_fill:
        return ("DISAGREEMENT\n  itemsize=%d kind=%r attr=%r values=%r "
                "fill=%r\n  shadow: values=%r fill=%r\n  real:   values=%r "
                "fill=%r"
                % (itemsize, kind_char, unsigned_str, values, fill,
                   shadow_vals, shadow_fill, real_vals, real_fill))
    return None


WIDTHS = [1, 2, 4, 8]
ATTR_STRINGS = ["false", "true", "True", "neither"]  # codes 0, 1, 2, 2


def boundary_cases():
    """All widths x kinds x attribute strings x boundary arrays x fills."""
    cases = []
    for itemsize in WIDTHS:
        modulus = 1 << (8 * itemsize)
        half = modulus // 2
        for kind_char in ("i", "u"):
            if kind_char == "u":
                vals = [0, 1, half - 1, half, modulus - 1]
            else:
                vals = [-half, -half + 1, -1, 0, 1, half - 1]
            arrays = [[], [vals[0]], [vals[-1]], vals]
            fills = [None, vals[0], vals[-1]]
            for unsigned_str in ATTR_STRINGS:
                for arrv in arrays:
                    for fill in fills:
                        cases.append((itemsize, kind_char, unsigned_str,
                                      arrv, fill))
    return cases


def main():
    from xarray.coding.variables import UnsignedIntegerCoder  # REAL callee
    from xarray.core.variable import Variable

    coder = UnsignedIntegerCoder()
    checked = 0

    bcases = boundary_cases()
    for case in bcases:
        err = check_case(coder, Variable, *case)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        itemsize = rng.choice(WIDTHS)
        modulus = 1 << (8 * itemsize)
        half = modulus // 2
        kind_char = rng.choice(("i", "u"))
        lo, hi = (0, modulus) if kind_char == "u" else (-half, half)
        unsigned_str = rng.choice(ATTR_STRINGS)
        n = rng.randint(0, 6)
        values = [rng.randrange(lo, hi) for _ in range(n)]
        fill = rng.randrange(lo, hi) if rng.random() < 0.5 else None
        err = check_case(coder, Variable, itemsize, kind_char, unsigned_str,
                         values, fill)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real decode on %d probes "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, len(bcases), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
