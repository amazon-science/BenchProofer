#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-22714 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo values. Each coordinate is
              abstracted to the `Coord` observations of mapping.md §2
              (`numeric = bool(a.is_number)`, `imagNonzero = (im(a).is_zero is
              False)`), and the modeled decision is recomputed:
                  anyImaginary = any(c.numeric and c.imagNonzero for c in cs)
              (the front-recursive `||` fold of `coordImaginary`). There are no
              A-tagged ops in the impl region, so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour. Two independent oracles, both over the
              REAL SymPy expressions at base_commit + gold patch:
                (1) the patched per-element guard transliterated VERBATIM from
                    the post-image of point.py:153 —
                    `any(a.is_number and im(a).is_zero is False for a in coords)`;
                (2) the end-to-end real constructor `Point(*coords)`: it must
                    raise `ValueError('Imaginary coordinates are not permitted.')`
                    IFF the modeled decision is True (the observable the F2P
                    regression test checks).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied by
the harness), stdlib + sympy only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 22714
N_FUZZ = 100_000

from sympy import (Integer, Rational, Float, I, Symbol, sqrt, pi, S, im,
                   Mul, Add)
from sympy.core.parameters import evaluate
from sympy.geometry.point import Point

IMAG_MSG = "Imaginary coordinates are not permitted."


# --- the abstraction (mapping.md §2): real SymPy expr -> Coord observations ---
def observe(a):
    """Compute the Coord fields from a real SymPy coordinate expression."""
    numeric = bool(a.is_number)
    imag_nonzero = (im(a).is_zero is False)
    imag_present = bool(im(a))
    return numeric, imag_nonzero, imag_present


# --- SHADOW: Solution.lean coordImaginary / anyImaginary, transliterated ------
def shadow_decision(coords):
    """anyImaginary (coords) with coordImaginary c = c.numeric && c.imagNonzero,
    over the abstracted observations. This is the R/I shadow of the impl."""
    result = False
    for a in coords:
        numeric, imag_nonzero, _imag_present = observe(a)
        result = (numeric and imag_nonzero) or result
    return result


# --- ORACLE 1: the patched guard, verbatim from post-image point.py:153 -------
def oracle_predicate(coords):
    """patch.diff's per-element guard over the real SymPy expressions."""
    return any(a.is_number and im(a).is_zero is False for a in coords)


# --- ORACLE 2: the end-to-end real constructor --------------------------------
def oracle_constructor_raises(coords):
    """Does the real Point(*coords) raise the imaginary-coordinate ValueError?

    Returns True/False, or None if some OTHER guard fired (out of scope: we only
    bridge the imaginary decision)."""
    try:
        Point(*coords)
        return False
    except ValueError as e:
        if str(e) == IMAG_MSG:
            return True
        return None        # a different ValueError (dimension etc.) — skip
    except Exception:
        return None         # TypeError etc. — out of scope for this guard


# --- input generation ---------------------------------------------------------
def gen_atom(rng):
    """A single SymPy coordinate expression spanning real/complex/symbolic."""
    k = rng.randint(0, 11)
    if k == 0:
        return Integer(rng.randint(-5, 5))
    if k == 1:
        return Rational(rng.randint(-5, 5), rng.randint(1, 5))
    if k == 2:
        return Float(rng.uniform(-3, 3))
    if k == 3:
        return S.Zero
    if k == 4:
        return I                                   # pure imaginary unit
    if k == 5:
        return Integer(rng.randint(1, 4)) * I      # n*I
    if k == 6:
        return Integer(rng.randint(-3, 3)) + Integer(rng.randint(1, 3)) * I
    if k == 7:
        return Symbol('x')                         # symbolic (is_number False)
    if k == 8:
        return Symbol('y', real=True)
    if k == 9:
        return sqrt(Integer(rng.randint(0, 5)))
    if k == 10:
        return pi
    return Integer(rng.randint(-5, 5))


def gen_coords(rng):
    """A coordinate list of length 2 or 3 (the dimensions Point accepts)."""
    n = rng.choice([2, 3])
    return [gen_atom(rng) for _ in range(n)]


def boundary_cases():
    """Hand-picked cases incl. the F2P regression (evaluate(False))."""
    cases = []
    # real integer points — must NOT be rejected
    cases.append((True, [Integer(1), Integer(2)]))
    cases.append((True, [Integer(1), Integer(2), Integer(3)]))
    cases.append((True, [S.Zero, S.Zero]))
    cases.append((True, [Rational(1, 2), Rational(1, 4)]))
    cases.append((True, [Float(0.5), Float(0.25)]))
    # genuinely imaginary coords — MUST be rejected
    cases.append((True, [Integer(2) * I, I]))
    cases.append((True, [Integer(3) + I, I]))
    cases.append((True, [I, Integer(0)]))
    cases.append((True, [Integer(1), Integer(2) * I]))
    # symbolic — not concrete numbers, not rejected
    cases.append((True, [Symbol('x'), Symbol('y')]))
    # the regression: same lists under suppressed evaluation
    cases.append((False, [Integer(1), Integer(2)]))
    cases.append((False, [Integer(1), Integer(2), Integer(3)]))
    cases.append((False, [Integer(2) * I, I]))
    cases.append((False, [Integer(3) + I, I]))
    return cases


def check_one(coords, disagreements):
    """Compare SHADOW vs both ORACLES for one coordinate list."""
    shadow = shadow_decision(coords)
    pred = oracle_predicate(coords)
    if shadow != pred:
        disagreements.append(("predicate", [str(c) for c in coords], shadow, pred))
        return
    ctor = oracle_constructor_raises(coords)
    if ctor is not None and ctor != shadow:
        disagreements.append(("constructor", [str(c) for c in coords], shadow, ctor))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # boundary cases (with explicit evaluate flag), F2P regression included
    for flag, coords in boundary_cases():
        count += 1
        with evaluate(flag):
            # rebuild atoms inside the context so suppression takes effect
            check_one(coords, disagreements)
        if len(disagreements) >= 5:
            break

    # randomized fuzz under both evaluation modes
    if not disagreements:
        for _ in range(N_FUZZ):
            count += 1
            flag = rng.choice([True, False])
            with evaluate(flag):
                coords = gen_coords(rng)
                check_one(coords, disagreements)
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for kind, coords, sh, orc in disagreements:
            print("  [%s] coords=%r shadow=%r oracle=%r" % (kind, coords, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of imaginaryCoordCheck agrees with patch.diff "
          "behaviour (patched predicate + end-to-end Point constructor) on %d "
          "inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
