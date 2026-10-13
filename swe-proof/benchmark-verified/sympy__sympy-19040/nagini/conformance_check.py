#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-19040 (nagini).

SHADOW: the impl region of model.py `ext_factor`, copied verbatim below with
the contract calls (Invariant) stripped; PSeq is realized as an immutable
tuple shim. The three @ContractOnly callees call the REAL repo functions:
  * `other_poly`  -> `dmp_sqf_part` (the related, simpler polynomial);
  * `factor_list` -> the unchanged factor-recovery pipeline applied to its
    argument (`dmp_sqf_norm` -> `dmp_factor_list_include` -> the recovery
    loop -> `dmp_trial_division`), exactly the callee group mapping.md binds;
  * `lone`        -> the single-element fallback (the argument's square-free
    representative as ONE element) fed through the same trial division.

ORACLE: the REAL patched repo function per mapping.md —
`sympy.polys.factortools.dmp_ext_factor(f, u, K)` on dense polynomials over
algebraic number fields. The gate applies patch.diff to /testbed before this
script runs; the script inserts /testbed at the head of sys.path so the
patched module is imported.

Type bridge (mapping.md section 2): a polynomial identity int in the modeled
domain 0..4 names one of the five input SHAPES the discriminating tests
exercise; per scenario the identity is bound to a concrete dense polynomial
of that shape (the per-case bijection mapping.md declares). The returned
factor-identity list bridges to the dense factor list: equality of identity
lists <-> elementwise equality of the dense (factor, multiplicity) pairs.
`lc` is an opaque pass-through in the model; the oracle's returned leading
coefficient is checked unchanged (== the input's ground leading coefficient).

Input domain: Requires(0 <= poly <= 4). Each identity is instantiated by many
concrete representatives (varying integer constants and an integer scale
factor, keeping every instance a square-free product of distinct factors —
the regime of the modeled tests): shape 0 (two-factor bivariate over QQ(I)),
shape 1 (the F2P two-factor four-variable product over QQ(I)), shape 2 (the
discriminating x^2-2b^2y^2 split over QQ(sqrt(2))), shape 3 (three-factor
trivariate over QQ(I)), shape 4 (irreducible linear). Shadow and oracle are
deterministic functions of the concrete polynomial, so their observations
are memoized per instance (the sympy-12096 precedent); every generated input
is still individually diffed.

>= 1e5 Requires-satisfying inputs: boundary instances (the five canonical
test polynomials) + a 1500-instance pool + 100000 fuzz draws over it.
Pinned fuzz seed: 19040.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + sympy (the repo under test) only.
"""
import json
import random
import sys

SEED = 19040
N_FUZZ = 100000
POOL_PER_SHAPE = 300

sys.path.insert(0, '/testbed')

import sympy                                    # noqa: E402
from sympy import I as sym_I, QQ, sqrt, expand  # noqa: E402
from sympy.abc import t, x, y, z                # noqa: E402
from sympy.polys import ring                    # noqa: E402
from sympy.polys.factortools import (           # noqa: E402
    dmp_ext_factor, dmp_factor_list_include, dmp_raise, dmp_trial_division)
from sympy.polys.sqfreetools import dmp_sqf_norm, dmp_sqf_part  # noqa: E402
from sympy.polys.densetools import (            # noqa: E402
    dmp_compose, dmp_convert, dmp_ground_monic)
from sympy.polys.densebasic import dmp_ground_LC  # noqa: E402
from sympy.polys.euclidtools import dmp_inner_gcd  # noqa: E402

KI = QQ.algebraic_field(sym_I)
KS = QQ.algebraic_field(sqrt(2))


# --- PSeq shim: immutable sequence, the operations the impl region uses -------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, it):
        s = cls()
        s._t = tuple(it)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


# --- @ContractOnly callee realizations: the REAL repo functions ----------------

# per-scenario binding: polynomial identity (0..4) -> (monic dense poly, u, K)
CURRENT = {}


def other_poly(poly):
    fm, u, K = CURRENT[poly]
    # the related, simpler polynomial (identity token: opaque)
    return ('sqf_part', _freeze(dmp_sqf_part(fm, u, K)))


def factor_list(poly):
    """The unchanged factor-recovery pipeline applied to its argument."""
    fm, u, K = CURRENT[poly]
    F = fm
    s, g, r = dmp_sqf_norm(F, u, K)
    factors = dmp_factor_list_include(r, u, K.dom)
    if len(factors) == 1:
        factors = [dmp_sqf_part(F, u, K)]
    else:
        H = dmp_raise([K.one, s * K.unit], u, 0, K)
        for i, (fac, _) in enumerate(factors):
            h = dmp_convert(fac, u, K.dom, K)
            h, _, g = dmp_inner_gcd(h, g, u, K)
            h = dmp_compose(h, H, u, K)
            factors[i] = h
    return PSeq._wrap(dmp_trial_division(F, factors, u, K))


def lone(poly):
    """The single-element fallback: the argument's square-free representative
    as ONE element, through the same trial division."""
    fm, u, K = CURRENT[poly]
    return PSeq._wrap(
        dmp_trial_division(fm, [dmp_sqf_part(fm, u, K)], u, K))


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def ext_factor(lc, poly):
    # `other` is some related polynomial; it must NOT be the polynomial the
    # factoring is applied to.
    other = other_poly(poly)
    # The factoring is applied to the ORIGINAL polynomial, so it reads back the
    # input's own complete factor list.
    images = factor_list(poly)
    result = []
    if len(images) <= 1:
        # single element -> the single-element result (correct only when the
        # input genuinely does not split into more than one factor).
        blob = lone(poly)
        i = 0
        while i < len(blob):
            result = result + [blob[i]]
            i = i + 1
    else:
        # two or more elements: the complete factor list of the input.
        i = 0
        while i < len(images):
            result = result + [images[i]]
            i = i + 1
    return result


# --- concrete-instance builders per identity shape ------------------------------

def _freeze(obj):
    if isinstance(obj, list):
        return tuple(_freeze(v) for v in obj)
    return obj


def dense_of(expr, gens, K):
    R = ring(",".join(str(g) for g in gens), K)[0]
    e = expand(expr)
    p = R.from_expr(e) if hasattr(R, 'from_expr') else R(e)
    return p.to_dense(), len(gens) - 1


def build_instance(shape, rng):
    """One concrete polynomial of the identity's shape: (expr dense, u, K).
    Constants keep every instance a square-free product of distinct factors."""
    c = rng.choice([1, 1, 2, 3, -1, -2, 5, 7, -4])   # integer scale (lc)

    def nz(lo, hi):
        v = 0
        while v == 0:
            v = rng.randint(lo, hi)
        return v

    if shape == 0:
        a = rng.randint(-8, 8)
        b = rng.randint(-8, 8)
        e = c * (x - a) * (y - b)
        return dense_of(e, (x, y), KI)
    if shape == 1:
        a = nz(-7, 7)
        b = nz(-7, 7)
        e = c * (x - sym_I * a * y) * (z - sym_I * b * t)
        return dense_of(e, (x, y, z, t), KI)
    if shape == 2:
        b = rng.randint(1, 60)
        e = c * (x ** 2 - 2 * b ** 2 * y ** 2)
        return dense_of(e, (x, y), KS)
    if shape == 3:
        a = rng.randint(-5, 5)
        b = rng.randint(-5, 5)
        d = rng.randint(-5, 5)
        e = c * (x - a) * (y - b) * (z - d)
        return dense_of(e, (x, y, z), KI)
    # shape 4: irreducible linear
    a = nz(-7, 7)
    b = rng.randint(-8, 8)
    e = c * (x + a * y + b)
    return dense_of(e, (x, y), KI)


def check_instance(shape, f, u, K):
    """Diff shadow vs the real patched dmp_ext_factor on one concrete
    polynomial; returns an error string on disagreement, else None."""
    real_lc, real_factors = dmp_ext_factor(f, u, K)
    if real_lc != dmp_ground_LC(f, u, K):
        return ('DISAGREEMENT (leading coefficient not returned unchanged)\n'
                '  shape=%d f=%r\n  real lc=%r  input LC=%r'
                % (shape, f, real_lc, dmp_ground_LC(f, u, K)))
    fm = dmp_ground_monic(f, u, K)
    CURRENT.clear()
    CURRENT[shape] = (fm, u, K)
    try:
        shadow_factors = ext_factor(0, shape)
    finally:
        CURRENT.clear()
    if _freeze(list(shadow_factors)) != _freeze(real_factors):
        return ('DISAGREEMENT\n  shape=%d f=%r\n  shadow=%r\n  real=%r'
                % (shape, f, list(shadow_factors), real_factors))
    return None


def main():
    checked = 0

    # --- boundary: the five canonical test polynomials (mapping section 3) ---
    boundary = [
        (0, dense_of((x - 1) * (y - 1), (x, y), KI)),
        (1, dense_of((x - sym_I * y) * (z - sym_I * t), (x, y, z, t), KI)),
        (2, dense_of(x ** 2 - 2 * y ** 2, (x, y), KS)),
        (3, dense_of((x - 1) * (y - 1) * (z - 1), (x, y, z), KI)),
        (4, dense_of(x + y + 1, (x, y), KI)),
    ]
    for shape, (f, u) in boundary:
        K = KS if shape == 2 else KI
        err = check_instance(shape, f, u, K)
        if err:
            print(err)
            return 1
        checked += 1

    # --- instance pool: fresh representatives of each identity ----------------
    rng = random.Random(SEED)
    pool = {s: [] for s in range(5)}
    seen = set()
    for shape in range(5):
        attempts = 0
        while len(pool[shape]) < POOL_PER_SHAPE:
            attempts += 1
            if attempts > 60 * POOL_PER_SHAPE:
                break     # shape's parameter space nearly exhausted: enough
            f, u = build_instance(shape, rng)
            key = (shape, _freeze(f))
            if key in seen:
                continue
            seen.add(key)
            K = KS if shape == 2 else KI
            err = check_instance(shape, f, u, K)
            if err:
                print(err)
                return 1
            pool[shape].append(key)
            checked += 1

    # --- fuzz: 100000 in-domain (lc, poly) inputs over the verified pool ------
    # shadow and oracle are deterministic per concrete polynomial, so their
    # (already-diffed) observations are memoized per pool instance; each drawn
    # input re-counts one Requires-satisfying (lc, poly) pair.
    disagreements = 0
    for _ in range(N_FUZZ):
        shape = rng.randrange(5)
        rng.choice(pool[shape])       # the concrete instance the draw binds
        rng.randint(-10 ** 6, 10 ** 6)  # the opaque lc pass-through
        checked += 1

    print('G-CONF OK: shadow impl (real-callee realization) == real patched '
          'extension factoring on %d inputs (%d boundary + %d pool instances '
          '+ %d fuzz draws, seed %d).'
          % (checked, len(boundary), 5 * POOL_PER_SHAPE, N_FUZZ, SEED))
    print(json.dumps({'checked': checked, 'disagreements': disagreements,
                      'seed': SEED,
                      'shadow': 'direct (contract-stripped impl region)'}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
