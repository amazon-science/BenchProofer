#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-17139 (nagini).

SHADOW: the impl region of model.py `transform_power`, copied verbatim below
with the contract calls (Requires/Ensures) stripped. The model has no
module-level @Pure helpers. The three @Pure @ContractOnly callees call the
REAL repo operations (per the contract, axiomatized callees are bridged to
the live library, never re-implemented):

  order_lt_zero(e)    -> the real ordering ``(e < 0) == True`` on the live
                         symbolic exponent (sympy.core.expr.Expr.__lt__)
  order_gt_max(e, m)  -> the real ordering ``(e > m) == True`` (Expr.__gt__)
  is_perfect_power(n) -> the real ``bool(sympy.perfect_power(n))``

ORACLE: the REAL patched repo function the model models per mapping.md — the
inner per-node transformer `_f` of `_TR56` in `sympy/simplify/fu.py`, driven
through its only entry point `_TR56(rv, f, g, h, max, pow)` on a single
eligible node (for a one-node input `bottom_up` applies `_f` exactly to that
node; none of its subterms is an eligible power, so the observed outcome is
`_f`'s outcome). The gate applies patch.diff to /testbed before this script
runs; PYTHONPATH=/testbed makes the patched code importable.

Type bridge (mapping.md §2): a model input (is_target, Expon{real, value},
max, pow) is materialised as a real node:

  * is_target True, real True  -> ``f(x) ** Integer(value)``; note sympy
    collapses exponents 0 and 1 at construction (``f(x)**1 == f(x)`` is not
    a Pow), so for those magnitudes the materialised node is simply not an
    eligible power — is_target is therefore always RE-DERIVED from the
    materialised node (``rv.is_Pow and rv.base.func == f``), exactly the
    binding mapping.md gives it, and both sides agree the node is unchanged.
  * is_target True, real False -> ``f(x) ** q`` for q drawn from a pool of
    non-real / unknown-realness exponents (imaginary literals, complex
    combinations, an unassumed symbol, an imaginary symbol) — the carrier's
    ``real`` is ``rv.exp.is_real is True``, so both False and None map to
    real=False.
  * is_target False            -> a power of a different base head, a plain
    symbol power, or a non-power node.

The oracle outcome is classified back onto the model's branch tags by
comparing the returned expression against the three possible shapes:
unchanged (== rv -> 0), the squared form ``h(g(arg)**2)`` for magnitude 2
(-> 1), or the general form ``h(g(arg)**2)**(value//2)`` (-> 2); any other
returned shape is reported as a disagreement. Real-but-non-integer symbolic
exponents are outside the model's integer carrier (mapping.md §2 scopes
``value`` to the integer magnitudes the dispatch reads) and are not
generated.

Oracle results are memoised per distinct materialised case (the transformer
is a pure function of the node and its keyword arguments); the shadow runs
on every case.

Input domain (the model's Requires): max >= 4; exp.real: bool,
exp.value: int. Boundary cases cover every dispatch arm (negative, zero,
first power, squared, fourth power, odd/even in-range, perfect and
non-perfect powers, at-max / over-max) for both pow modes, the full non-real
exponent pool, and non-target shapes; fuzz draws magnitudes in [-60, 60],
bounds in [4, 40], both pow modes, and all shape kinds.

>= 1e5 Requires-satisfying inputs: 100000 fuzz cases + boundary grid.
Pinned fuzz seed: 171390.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + sympy (the repo under test) only.
"""
import json
import random
import sys

from sympy import I, Integer, Symbol, cos, perfect_power, sin
from sympy.simplify.fu import _TR56

SEED = 171390
N_FUZZ = 100_000

X = Symbol('c_x')
F = sin
G = cos


def H(a):
    return 1 - a


# --- carrier shim --------------------------------------------------------------
class Expon(object):
    """Plain shim for the model's exponent carrier: the two modelled
    attributes plus the live symbolic exponent the real callees operate on."""

    def __init__(self, real, value, sym):
        self.real = real
        self.value = value
        self.sym = sym


# --- @ContractOnly callees: the REAL repo operations ---------------------------

def order_lt_zero(e):
    """Real callee: the live ordering ``(exp < 0) == True``. Raises on a
    non-real operand — the shadow's realness guard must fire first, exactly
    as the axiom's Requires demands."""
    return (e.sym < 0) == True          # noqa: E712


def order_gt_max(e, m):
    """Real callee: the live ordering ``(exp > m) == True``."""
    return (e.sym > m) == True          # noqa: E712


def is_perfect_power(n):
    """Real callee: the boolean the dispatch branches on."""
    return bool(perfect_power(n))


# --- the impl region of model.py, verbatim (contract calls stripped) -----------

def transform_power(is_target, exp, max, pow):
    if not is_target:
        return 0
    if not exp.real:
        return 0
    if order_lt_zero(exp) == True:
        return 0
    if order_gt_max(exp, max) == True:
        return 0
    if exp.value == 1:
        return 0
    if exp.value == 2:
        return 1
    else:
        if exp.value == 4:
            return 2
        elif not pow:
            if exp.value % 2 == 1:
                return 0
            return 2
        else:
            if not is_perfect_power(exp.value):
                return 0
            return 2
    # impl-end (verbatim copy above)


# --- oracle: the real patched transformer, classified onto the branch tags -----

# non-real / unknown-realness exponents (is_real is False or None); each pool
# entry is (label, expr)
Y = Symbol('c_y')                    # unassumed: is_real is None
Z = Symbol('c_z', imaginary=True)    # is_real is False
NONREAL_POOL = [
    ("I", I),
    ("2*I+1", 2 * I + 1),
    ("3*I", 3 * I),
    ("2+3*I", Integer(2) + 3 * I),
    ("1-I", 1 - I),
    ("-I", -I),
    ("I/2", I / 2),
    ("5*I-7", 5 * I - 7),
    ("unassumed symbol", Y),
    ("imaginary symbol", Z),
]

# non-target node shapes: (label, node builder over the integer magnitude)
NONTARGET_POOL = [
    ("other-head power", lambda v: G(X) ** Integer(v)),
    ("symbol power", lambda v: X ** Integer(v)),
    ("non-power sum", lambda v: F(X) + Integer(v)),
    ("non-power product", lambda v: Integer(2) * F(X)),
    ("bare symbol", lambda v: X),
]

_oracle_cache = {}


def real_outcome(rv, m, p):
    """Run the REAL patched transformer on node `rv` and classify the result
    onto the model's branch tags. Memoised: the transformer is a pure
    function of (rv, m, p)."""
    key = (rv, m, p)
    if key in _oracle_cache:
        return _oracle_cache[key]
    res = _TR56(rv, F, G, H, m, p)
    if res == rv:
        code = 0
    else:
        if not (rv.is_Pow and rv.base.func == F):
            code = ("ANOMALY", "non-eligible node was altered", res)
        else:
            arg = rv.base.args[0]
            squared = H(G(arg) ** 2)
            if rv.exp == 2 and res == squared:
                code = 1
            elif (rv.exp.is_real is True and int(rv.exp) >= 3
                  and res == squared ** (int(rv.exp) // 2)):
                code = 2
            else:
                code = ("ANOMALY", "unrecognised rewritten shape", res)
    _oracle_cache[key] = code
    return code


def check_case(label, rv, exp_shim, m, p):
    """Diff shadow vs oracle on one materialised case. Returns an error
    string on disagreement, else None."""
    is_target = bool(rv.is_Pow and rv.base.func == F)
    shadow = transform_power(is_target, exp_shim, m, p)
    real = real_outcome(rv, m, p)
    if shadow != real:
        return ("DISAGREEMENT [%s]\n"
                "  node=%r  max=%d  pow=%r  is_target=%r  "
                "carrier=(real=%r, value=%r)\n"
                "  shadow=%r\n  real=%r"
                % (label, rv, m, p, is_target,
                   exp_shim.real, exp_shim.value, shadow, real))
    return None


def target_int_case(v, m, p, label):
    """Materialise the target-power case for a real integer magnitude."""
    rv = F(X) ** Integer(v)
    if rv.is_Pow:
        exp_shim = Expon(rv.exp.is_real is True, int(rv.exp), rv.exp)
    else:
        # magnitudes 0 / 1 collapse at construction: not an eligible power
        exp_shim = Expon(True, v, Integer(v))
    return check_case(label, rv, exp_shim, m, p)


def target_nonreal_case(idx, m, p, label):
    q_label, q = NONREAL_POOL[idx]
    rv = F(X) ** q
    exp_shim = Expon(rv.exp.is_real is True, 0, rv.exp)
    return check_case("%s (%s)" % (label, q_label), rv, exp_shim, m, p)


def nontarget_case(idx, v, m, p, label):
    n_label, build = NONTARGET_POOL[idx]
    rv = build(v)
    if rv.is_Pow:
        real = rv.exp.is_real is True
        value = int(rv.exp) if real else 0
        exp_shim = Expon(real, value, rv.exp)
    else:
        exp_shim = Expon(True, 0, Integer(0))
    return check_case("%s (%s)" % (label, n_label), rv, exp_shim, m, p)


def main():
    rng = random.Random(SEED)
    checked = 0
    n_boundary = 0

    # --- boundary grid ----------------------------------------------------
    boundary_values = [-10, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
                       12, 16, 25, 27, 32, 36, 40, 41, 49, 64, 81, 100]
    boundary_maxes = [4, 5, 6, 10, 30]
    errs = []
    for v in boundary_values:
        for m in boundary_maxes:
            for p in (False, True):
                errs.append(target_int_case(v, m, p, "boundary target"))
                checked += 1
                n_boundary += 1
    for idx in range(len(NONREAL_POOL)):
        for m in (4, 10):
            for p in (False, True):
                errs.append(target_nonreal_case(idx, m, p,
                                                "boundary non-real"))
                checked += 1
                n_boundary += 1
    for idx in range(len(NONTARGET_POOL)):
        for v in (-3, 2, 5, 6):
            for p in (False, True):
                errs.append(nontarget_case(idx, v, 4, p,
                                           "boundary non-target"))
                checked += 1
                n_boundary += 1
    for e in errs:
        if e:
            print(e)
            return 1

    # --- fuzz -------------------------------------------------------------
    for trial in range(N_FUZZ):
        m = rng.randint(4, 40)
        p = rng.random() < 0.5
        kind = rng.random()
        if kind < 0.70:
            v = rng.randint(-60, 60)
            err = target_int_case(v, m, p, "fuzz#%d target" % trial)
        elif kind < 0.85:
            idx = rng.randrange(len(NONREAL_POOL))
            err = target_nonreal_case(idx, m, p, "fuzz#%d non-real" % trial)
        else:
            idx = rng.randrange(len(NONTARGET_POOL))
            v = rng.randint(-10, 10)
            err = nontarget_case(idx, v, m, p, "fuzz#%d non-target" % trial)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow transform_power == real patched transformer "
          "outcome on %d inputs (%d boundary + %d fuzz, seed %d); "
          "@ContractOnly callees bridged to the live ordering and "
          "perfect-power operations."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({
        "checked": checked, "disagreements": 0, "seed": SEED,
        "shadow": "direct (contract-stripped impl region; @ContractOnly "
                  "callees call the real repo operations)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
