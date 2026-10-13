#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-24149 (nagini).

SHADOW: the impl regions of model.py's ``select_position_x0`` and
``select_position_xconv``, copied VERBATIM below with only the contract calls
(Requires / Ensures / MustTerminate) stripped. The @Pure helpers ``any_finite``
and ``first_finite_value`` copy over as plain functions on a small immutable
PSeq shim (tuple-backed; supports ``drop``, ``len``, indexing); the pure fold
``first_finite_value`` doubles as an internal cross-check of the executable
shadow. The two @ContractOnly callees delegate to the REAL repo functions they
are bound to (mapping.md section 3): ``first_finite`` calls
``matplotlib.cbook._safe_first_finite`` and ``first_unconditional`` calls
``matplotlib.cbook.safe_first_element``, each across the documented flag
carrier bridge (flags materialized to floats, the returned float lifted back
to its flag).

ORACLE: the REAL patched repo code the model models per mapping.md section 1 —
the two representative-selection blocks of
``matplotlib.axes._axes.Axes._convert_dx`` (the ``x0`` site, hunk 1, and the
``xconv`` site, hunk 2). The gate applies patch.diff to /testbed before this
script runs and sets PYTHONPATH so the import resolves to the patched module.
Each selection site is observed through ``_convert_dx`` itself: with
``dx = 0.0`` and an identity ``convert``, the helper returns exactly
``x0_sel + 0.0 - x_sel`` where ``x0_sel`` / ``x_sel`` are the two selected
representatives. Pinning ``xconv = np.array([0.0])`` makes the return value
``x0_sel`` (the x0-site representative verbatim); pinning ``x0 = [0.0]``
makes it ``-x_sel``, and negation is exact on floats, so ``x_sel`` is
recovered exactly (NaN stays NaN under negation). Both probes stay on the
float path, so none of the helper's non-selection fallbacks fire.

TYPE BRIDGE (mapping.md section 2): the repo value is a coordinate sequence of
floats (possibly containing non-finite entries); the model carrier is
``List[int]`` of per-element finiteness flags (0 == non-finite, non-zero ==
finite). Lowering: flag 0 materializes to a non-finite float (NaN by default;
some boundary cases use +/-inf on the oracle side), non-zero flag k
materializes to the finite float ``float(k)``; generated non-zero flags are
DISTINCT per position, so the selected element's identity — not merely its
finiteness — is observable. Lifting the oracle's returned float back: a
non-finite result lifts to flag 0; a finite result lifts to the flag of the
(unique) input position holding that float. Comparison is at the flag level:
shadow flag == lifted oracle flag, plus the finiteness-sanity direction
(shadow flag non-zero <-> oracle result finite).

INPUT PLAN (>= 1e5 Requires-satisfying inputs — the preconditions demand only
a non-empty flag list, so every non-empty pattern qualifies): every
finite/non-finite pattern of lengths 1..10 exhaustively (2046 patterns),
hand-picked boundary patterns (single elements, all-non-finite runs including
the length-1 case, long runs, duplicate flag values, +/-inf and mixed-sign
materializations), plus 60000 random fuzz patterns over mixed lengths with a
non-finite-heavy flag distribution. Every pattern is fed to BOTH modeled
functions (both selection sites), so the total is >= 2 * (2046 + boundary +
60000) > 124000 checks. Pinned fuzz seed: 24149.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the repo's own numpy/matplotlib only.
"""
import json
import math
import os
import random
import sys

os.environ.setdefault("MPLBACKEND", "Agg")

SEED = 24149
N_FUZZ = 60000


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

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

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


# --- pure region of model.py, contracts stripped ------------------------------

def any_finite(s):
    """Whether the sequence contains at least one finite element (a flag that
    is non-zero). The empty sequence contains none (`False`)."""
    if len(s) == 0:
        return False
    return (s[0] != 0) or any_finite(s.drop(1))


def first_finite_value(s):
    """The first finite element of the sequence — the leftmost element whose
    flag is non-zero — when one exists (requires any_finite(s))."""
    if s[0] != 0:
        return s[0]
    return first_finite_value(s.drop(1))


# --- flag <-> float materialization (the documented carrier bridge) -----------

def materialize(flags):
    """Lower a flag sequence to a concrete coordinate list: non-zero flag k ->
    the finite float float(k); zero flag -> NaN (the canonical non-finite)."""
    return [float(f) if f != 0 else float("nan") for f in flags]


def lift_result(r, flags, coords):
    """Lift the oracle's returned float back to a flag. Non-finite -> 0;
    finite -> the flag at the input position holding that float (positions
    carry distinct finite floats, so the lift pins identity). Returns None if
    the float matches no input position (itself a disagreement)."""
    if not math.isfinite(r):
        return 0
    for k in range(len(coords)):
        if math.isfinite(coords[k]) and coords[k] == r:
            return flags[k]
    return None


# --- @ContractOnly callees: the REAL repo selectors (mapping.md section 3) ----

def first_finite(s):
    """Axiomatized first-finite selector, delegated to the REAL repo callee
    ``cbook._safe_first_finite`` across the flag/float bridge. Only called
    under any_finite(s), i.e. inside the callee's normal-return domain."""
    import matplotlib.cbook as cbook
    r = cbook._safe_first_finite(materialize(list(s._t)))
    return int(r)


def first_unconditional(s):
    """Axiomatized first-element selector, delegated to the REAL repo callee
    ``cbook.safe_first_element`` across the flag/float bridge (a non-finite
    first element lifts to flag 0)."""
    import matplotlib.cbook as cbook
    r = cbook.safe_first_element(materialize(list(s._t)))
    return int(r) if math.isfinite(r) else 0


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def select_position_x0(seq):
    if any_finite(ToSeq(seq)):
        rep = first_finite(ToSeq(seq))
    else:
        rep = first_unconditional(ToSeq(seq))
    return rep


def select_position_xconv(seq):
    if any_finite(ToSeq(seq)):
        rep = first_finite(ToSeq(seq))
    else:
        rep = first_unconditional(ToSeq(seq))
    return rep


# --- oracle: the real patched selection sites of Axes._convert_dx -------------

def _identity(v):
    return v


def make_oracles():
    import numpy as np
    from matplotlib.axes._axes import Axes

    def real_x0_site(coords):
        # x0 varies; the xconv site is pinned to 0.0, so the return value is
        # convert(x0_sel + 0.0) - 0.0 == the x0-site representative itself.
        out = Axes._convert_dx(0.0, list(coords), np.array([0.0]), _identity)
        return float(out)

    def real_xconv_site(coords):
        # xconv varies; the x0 site is pinned to 0.0, so the return value is
        # 0.0 + 0.0 - x_sel == the negated xconv-site representative.
        out = Axes._convert_dx(0.0, [0.0],
                               np.asarray(coords, dtype=float), _identity)
        return float(-out)

    return real_x0_site, real_xconv_site


# --- differential driver -------------------------------------------------------

def check_site(name, shadow_fn, oracle_fn, flags, coords):
    """Run shadow and oracle on one flag pattern for one selection site;
    return an error string on disagreement, else None."""
    f = shadow_fn(list(flags))
    try:
        r = oracle_fn(coords)
    except Exception as e:  # the selection must be total on non-empty input
        return ("DISAGREEMENT on %s, flags %r (coords %r):\n"
                "  shadow (impl region) = %r\n"
                "  real (patched repo)  = raised %r"
                % (name, flags, coords, f, e))
    # finiteness direction of the bridge
    if (f != 0) != math.isfinite(r):
        return ("DISAGREEMENT on %s, flags %r (coords %r):\n"
                "  shadow (impl region) = flag %r (finite=%r)\n"
                "  real (patched repo)  = %r (finite=%r)"
                % (name, flags, coords, f, f != 0, r, math.isfinite(r)))
    # identity direction: the oracle's float lifts to exactly the shadow flag
    lifted = lift_result(r, flags, coords)
    if lifted != f:
        return ("DISAGREEMENT on %s, flags %r (coords %r):\n"
                "  shadow (impl region) = flag %r\n"
                "  real (patched repo)  = %r (lifts to flag %r)"
                % (name, flags, coords, f, r, lifted))
    # internal cross-check: the executable shadow agrees with the pure folds
    s = ToSeq(list(flags))
    expected = first_finite_value(s) if any_finite(s) else s[0]
    if f != expected:
        return ("INTERNAL: impl region and pure fold disagree on %r: "
                "shadow %r, fold %r" % (flags, f, expected))
    return None


def distinct_flags(rng, n, p_finite):
    """A random flag pattern of length n: each position non-finite (0) with
    probability 1 - p_finite, else a DISTINCT finite flag (position-bucketed
    so identity is observable; occasionally negative — any non-zero flag is
    a finite element)."""
    flags = []
    for k in range(n):
        if rng.random() < p_finite:
            v = (k + 1) * 1000 + rng.randint(0, 999)
            if rng.random() < 0.2:
                v = -v
            flags.append(v)
        else:
            flags.append(0)
    return flags


def boundary_patterns():
    """Hand-picked (flags, coords-override-or-None) boundary cases."""
    nan, inf = float("nan"), float("inf")
    pats = [
        # single elements: the all-non-finite length-1 pattern is exactly the
        # regression class (non-empty, no finite value)
        ([0], None),
        ([1], None),
        ([7], None),
        ([-3], None),
        # all-non-finite runs of growing length
        ([0, 0], None),
        ([0, 0, 0], None),
        ([0] * 10, None),
        ([0] * 200, None),
        # all-finite runs (distinct flags)
        ([1, 2], None),
        (list(range(1, 11)), None),
        (list(range(1, 201)), None),
        # leading non-finite prefix, finite tail
        ([0, 5], None),
        ([0, 0, 9], None),
        ([0] * 199 + [42], None),
        # finite head, non-finite tail
        ([5, 0], None),
        ([9, 0, 0], None),
        ([42] + [0] * 199, None),
        # alternating
        ([0, 1, 0, 2, 0, 3], None),
        ([1, 0, 2, 0, 3, 0], None),
        # duplicate flag values (indistinguishable elements in the carrier)
        ([1, 1], None),
        ([0, 4, 4, 0, 4], None),
        # negative and mixed-sign finite flags
        ([-1, 0, -2], None),
        ([0, -7], None),
        # non-finite materialized as +/-inf instead of NaN on the oracle side
        ([0], [inf]),
        ([0], [-inf]),
        ([0, 0], [inf, -inf]),
        ([0, 3], [inf, 3.0]),
        ([0, 0, 8], [-inf, nan, 8.0]),
        ([6, 0], [6.0, inf]),
        ([0, 0, 0, 0], [inf, nan, -inf, nan]),
    ]
    return pats


def main():
    real_x0_site, real_xconv_site = make_oracles()
    sites = (("select_position_x0 / x0 site", select_position_x0,
              real_x0_site),
             ("select_position_xconv / xconv site", select_position_xconv,
              real_xconv_site))

    checked = 0

    def run_pattern(flags, coords=None):
        nonlocal checked
        cs = coords if coords is not None else materialize(flags)
        for name, shadow_fn, oracle_fn in sites:
            err = check_site(name, shadow_fn, oracle_fn, flags, cs)
            if err:
                print(err)
                sys.exit(1)
            checked += 1

    # 1) hand-picked boundary patterns
    boundary = boundary_patterns()
    for flags, coords in boundary:
        run_pattern(flags, coords)

    # 2) exhaustive finite/non-finite patterns, lengths 1..10 (distinct
    #    position-indexed flags on the finite slots)
    n_exhaustive = 0
    for n in range(1, 11):
        for mask in range(1 << n):
            flags = [(k + 1) if (mask >> k) & 1 else 0 for k in range(n)]
            run_pattern(flags)
            n_exhaustive += 1

    # 3) randomized fuzz: mixed lengths, non-finite-heavy and finite-heavy
    #    mixtures (pinned seed)
    rng = random.Random(SEED)
    for i in range(N_FUZZ):
        if rng.random() < 0.02:
            n = rng.randint(13, 200)
        else:
            n = rng.randint(1, 12)
        p_finite = rng.choice((0.0, 0.05, 0.2, 0.5, 0.8, 1.0))
        flags = distinct_flags(rng, n, p_finite)
        run_pattern(flags)

    print("G-CONF OK: shadow impl == real patched selection sites of "
          "Axes._convert_dx on %d checks (%d boundary + %d exhaustive + %d "
          "fuzz patterns, x2 sites each, seed %d); 0 disagreements."
          % (checked, len(boundary), n_exhaustive, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl regions; "
                                "@ContractOnly callees delegated to the real "
                                "cbook selectors)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
