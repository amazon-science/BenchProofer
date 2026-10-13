#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-6599 (nagini).

SHADOW: the impl region of model.py's ``coerce_values_to_float``, copied
VERBATIM below with only the contract calls (Requires / Ensures / Invariant /
Assert) stripped. The @Pure helpers ``well_defined_magnitudes`` /
``magnitude_read`` copy over as plain functions on a small immutable
tuple-backed PSeq shim (the Forall of ``well_defined_magnitudes`` folds into
the equivalent element loop); ``magnitude_read`` is kept as an internal
cross-check of the duration branch. The one @ContractOnly callee
(``elapsed_since``) delegates to the REAL repo-relied callee it is bound to
per mapping.md section 3.1 — ``xarray.core.duck_array_ops.datetime_to_numeric``
— lowering the magnitudes to a ``datetime64[ns]`` array and raising the float
result back to ints (the call site fixes ``reference == 0``, the ns magnitude
of the epoch offset).

ORACLE: the REAL patched repo function per mapping.md section 1 — the
per-variable coercion helper inside ``xarray.core.computation._ensure_numeric``.
It is a nested closure, so each probe reaches it exactly by calling
``_ensure_numeric`` on a one-variable DataArray (the non-Dataset arm of the
outer function applies the helper to its argument directly). The gate applies
patch.diff to /testbed and sets PYTHONPATH=/testbed before this script runs,
so the import resolves to the patched module.

TYPE BRIDGE (mapping.md section 2): the repo value is a numpy array of
``datetime64[ns]`` / ``timedelta64[ns]`` / numeric dtype; the model carrier is
``List[int]`` of base-resolution magnitudes plus an int kind tag
(OTHER/TIME_POINT/TIME_SPAN <-> dtype-kind category). Lowering: int64
magnitudes ``.view``-ed as the matching dtype. Raising: the oracle's numeric
output values, each required to be integer-valued, back to ints. The float
output is modeled as int on the exact-integer band, so generated magnitudes
stay within |m| <= 2**53 wherever a float conversion happens (plus
exactly-representable extremes such as +-2**62 and -2**63 on the duration
branch, whose magnitude read is the identity there); OTHER inputs are never
float-converted, so they range over the full int64 band.

INPUT PLAN (>= 1e5 Requires-satisfying inputs): boundary arrays per kind
(empty, singletons, the F2P duration magnitudes, the P2P timestamp
magnitudes, negatives, mixed signs, exact-band edges +-2**52/+-2**53,
duration-only exact extremes incl. the not-a-value sentinel magnitude,
full-int64 extremes on the passthrough kind) plus 100000 random fuzz arrays
over all three kinds (timestamp arrays never draw the sentinel, honouring the
precondition). Pinned fuzz seed: 6599. Exit 0 iff zero disagreements; on
disagreement prints the input and both outputs and exits 1. stdlib + the
in-container repo/numpy only.
"""
import json
import random
import sys

SEED = 6599
N_FUZZ = 100000

# value-category tags (model.py)
OTHER = 0       # already-numeric values: returned unchanged
TIME_POINT = 1  # absolute timestamps  (numpy datetime64; dtype.kind 'M')
TIME_SPAN = 2   # elapsed durations    (numpy timedelta64; dtype.kind 'm')

NAT_SENTINEL = -(2 ** 63)   # the not-a-value sentinel magnitude
EXACT_BAND = 2 ** 53        # |m| <= this: exact under float64


# --- PSeq shim: immutable sequence with the operations the model uses --------

class PSeq(object):
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

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure region of model.py, copied as plain functions ----------------------

def well_defined_magnitudes(values):
    """Every element is a well-defined magnitude: none is the not-a-value
    sentinel (the int64 extremum -2**63). (The model's Forall, folded into
    the equivalent element loop.)"""
    k = 0
    while k < len(values):
        if values[k] == NAT_SENTINEL:
            return False
        k = k + 1
    return True


def magnitude_read(values):
    """The duration's direct magnitude read, modelled deeply: the identity
    on magnitudes."""
    return values


# --- @ContractOnly callee: the REAL repo callee (mapping.md section 3.1) -----

def elapsed_since(kind, values, reference):
    """The axiomatized instant-relative measurement, delegated to the REAL
    repo callee ``datetime_to_numeric``: lower the magnitudes to a
    ``datetime64[ns]`` array, measure against the instant whose ns magnitude
    is ``reference`` (the call site under test fixes reference == 0, the
    epoch offset), and raise the float result back to ints."""
    import numpy as np
    from xarray.core.duck_array_ops import datetime_to_numeric
    arr = np.asarray(list(values._t), dtype="int64").view("datetime64[ns]")
    out = datetime_to_numeric(arr, offset=np.datetime64(reference, "ns"),
                              datetime_unit="ns")
    res = []
    for f in np.asarray(out).ravel().tolist():
        if float(f) != int(f):
            raise ValueError("real callee returned a non-integer value %r "
                             "for magnitudes %r" % (f, list(values._t)))
        res.append(int(f))
    return PSeq._wrap(res)


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def coerce_values_to_float(kind, values, reference):
    if kind == TIME_POINT:
        # numeric via the instant-relative measurement (the unchanged callee):
        # hold its result, the elapsed magnitudes since the reference instant
        measured = elapsed_since(kind, ToSeq(values), reference)
        result = []  # type: List[int]
        i = 0
        while i < len(values):
            result.append(measured[i])
            i = i + 1
        return result
    elif kind == TIME_SPAN:
        # read each duration's magnitude directly (the new branch): the float
        # magnitude equals the input magnitude in the base resolution
        out = []  # type: List[int]
        j = 0
        while j < len(values):
            out.append(values[j])
            j = j + 1
        return out
    else:
        # already numeric: passthrough
        passthrough = []  # type: List[int]
        m = 0
        while m < len(values):
            passthrough.append(values[m])
            m = m + 1
        return passthrough


# --- oracle: the real patched repo function -----------------------------------

def make_oracle():
    import numpy as np
    import xarray as xr
    from xarray.core.computation import _ensure_numeric

    def lower(kind, values, flavor):
        """Model input -> the repo's variable values (mapping.md section 2)."""
        base = np.asarray(list(values), dtype="int64")
        if kind == TIME_POINT:
            return base.view("datetime64[ns]")
        if kind == TIME_SPAN:
            return base.view("timedelta64[ns]")
        if flavor == "f":
            return base.astype("float64")   # integer-valued floats, kind 'f'
        return base                          # kind 'i'

    def oracle(kind, values, flavor):
        """Run the patched coercion; return (list-of-int, error-or-None)."""
        da = xr.DataArray(lower(kind, values, flavor), dims=["x"])
        out = _ensure_numeric(da)
        a = np.asarray(out.values)
        if a.dtype.kind in "mM":
            return None, ("output still carries a time dtype (%s): "
                          "not coerced to numbers" % a.dtype)
        res = []
        for v in a.ravel().tolist():
            if isinstance(v, int):      # passthrough kept an integer dtype
                res.append(v)
                continue
            f = float(v)
            if f != int(f):
                return None, "output value %r is not integer-valued" % (v,)
            res.append(int(f))
        return res, None

    return oracle


# --- differential driver -------------------------------------------------------

def describe(kind, values, flavor):
    tag = {OTHER: "OTHER", TIME_POINT: "TIME_POINT", TIME_SPAN: "TIME_SPAN"}[kind]
    fl = " (float64 carrier)" if (kind == OTHER and flavor == "f") else ""
    return "kind=%s%s values=%r" % (tag, fl, list(values))


def check(oracle, kind, values, flavor="i"):
    """Run shadow and oracle on one Requires-satisfying input; return an
    error string on disagreement, else None."""
    try:
        shadow = coerce_values_to_float(kind, list(values), 0)
    except Exception as exc:  # the shadow must be total on the domain
        return ("SHADOW ERROR on %s: %r" % (describe(kind, values, flavor), exc))
    real, err = oracle(kind, values, flavor)
    if err is not None:
        return ("DISAGREEMENT on %s:\n  shadow (impl region) = %r\n"
                "  real (patched repo)  = <%s>"
                % (describe(kind, values, flavor), shadow, err))
    if list(shadow) != real:
        return ("DISAGREEMENT on %s:\n  shadow (impl region) = %r\n"
                "  real (patched repo)  = %r"
                % (describe(kind, values, flavor), shadow, real))
    # internal cross-check: the duration branch agrees with the deep model
    if kind == TIME_SPAN and ToSeq(shadow) != magnitude_read(ToSeq(values)):
        return ("INTERNAL: impl region and magnitude_read disagree on %s"
                % describe(kind, values, flavor))
    return None


def boundary_cases():
    small = [
        [], [0], [1], [-1], [5], [1000],
        [1000, 2000, 3000],                 # duration magnitudes under test
        [0, 10 ** 9, 2 * 10 ** 9],          # timestamp magnitudes under test
        [-5, 7, -9],
        [-(10 ** 9), 10 ** 9],
        [123456789, -987654321],
        list(range(-6, 7)),
        [999999999, 1000000000, 1000000001],
        [2 ** 52], [-(2 ** 52)], [2 ** 53], [-(2 ** 53)],
        [2 ** 53 - 1, -(2 ** 53 - 1)],
        [2 ** 53, 0, -(2 ** 53)],
    ]
    cases = []
    for k in (OTHER, TIME_POINT, TIME_SPAN):
        for vs in small:
            cases.append((k, vs, "i"))
    # OTHER over an integer-valued float64 carrier (a second passthrough kind)
    for vs in ([], [0], [1000, 2000, 3000], [2 ** 52, -(2 ** 52)]):
        cases.append((OTHER, vs, "f"))
    # duration-only exactly-representable extremes, incl. the not-a-value
    # sentinel magnitude (the magnitude read is the identity there; only the
    # timestamp measurement excludes it)
    for vs in ([NAT_SENTINEL], [2 ** 62], [-(2 ** 62)],
               [NAT_SENTINEL, 0, 1000], [2 ** 62, -(2 ** 62)]):
        cases.append((TIME_SPAN, vs, "i"))
    # passthrough at the full int64 extremes (no float conversion happens)
    for vs in ([NAT_SENTINEL], [2 ** 63 - 1], [NAT_SENTINEL, 2 ** 63 - 1, 0]):
        cases.append((OTHER, vs, "i"))
    return cases


def fuzz_magnitude(rng, kind):
    r = rng.random()
    if r < 0.35:
        return rng.randint(-5000, 5000)
    if r < 0.55:
        return rng.choice([0, 1, -1, 1000, 2000, 3000,
                           10 ** 9, 2 * 10 ** 9, -(10 ** 9)])
    if r < 0.90:
        return rng.randint(-EXACT_BAND, EXACT_BAND)
    pool = [2 ** 52, -(2 ** 52), 2 ** 53, -(2 ** 53), 2 ** 53 - 1]
    if kind == TIME_SPAN:
        # exactly-representable extremes; the sentinel is in-domain here
        pool = pool + [NAT_SENTINEL, 2 ** 62, -(2 ** 62)]
    elif kind == OTHER:
        # passthrough: full int64 band, no float conversion
        pool = pool + [NAT_SENTINEL, 2 ** 63 - 1, -(2 ** 63) + 1, 2 ** 62]
    return rng.choice(pool)


def main():
    n_fuzz = N_FUZZ
    if len(sys.argv) > 1:            # optional local-smoke override only;
        n_fuzz = int(sys.argv[1])    # the gate passes no arguments
    oracle = make_oracle()

    checked = 0
    boundary = boundary_cases()
    for kind, vs, flavor in boundary:
        err = check(oracle, kind, vs, flavor)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(n_fuzz):
        kind = rng.choice((OTHER, TIME_POINT, TIME_SPAN))
        flavor = "f" if (kind == OTHER and rng.random() < 0.25) else "i"
        n = rng.randint(0, 8)
        if flavor == "f":
            vs = [rng.randint(-EXACT_BAND, EXACT_BAND) for _ in range(n)]
        else:
            vs = [fuzz_magnitude(rng, kind) for _ in range(n)]
        err = check(oracle, kind, vs, flavor)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched per-variable coercion on "
          "%d inputs (%d boundary + %d fuzz, seed %d); 0 disagreements."
          % (checked, len(boundary), n_fuzz, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
