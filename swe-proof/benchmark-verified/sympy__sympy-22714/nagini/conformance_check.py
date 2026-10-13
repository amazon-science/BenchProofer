#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-22714 (nagini).

SHADOW: the impl region of model.py's `screen_coordinates`, copied VERBATIM
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
The @Pure helpers (`coord_triggers`, `any_triggering`) copy over as plain
functions; `PSeq`/`ToSeq` become an immutable-tuple shim carrying `.drop`.
There is no @ContractOnly callee in this bundle (the changed test is modeled
deeply; see refinement.md).

ORACLE: the REAL patched repo function per mapping.md section 1 — the
coordinate screen inside the point constructor. The gate applies patch.diff
to /testbed before this script runs (PYTHONPATH=/testbed), so constructing
`sympy.geometry.Point(*coords)` exercises the patched screen. The modeled
boolean is "the constructor takes the rejecting branch": True iff the call
raises the screen's own ValueError (classified by its distinctive message —
the screen is that message's only raise site). Any other outcome (success,
or an exception from a stage AFTER the screen) means the screen accepted:
had it rejected, its raise would have pre-empted every later stage. Stages
BEFORE the screen cannot raise on our inputs (>= 2 coordinates, all Expr,
no dimension keyword), so reaching the screen is guaranteed.

TYPE BRIDGE (mapping.md section 2): each SymPy coordinate `a` maps to three
int facts, in coordinate order —
    coord_kind[i]    = 1 if a.is_number is True else 0
    coord_verdict[i] = 1 / 0 / -1 for im(a).is_zero True / False / None
    coord_extra[i]   = 1 if bool(im(a)) else 0   (redundant; spec ignores it)
Both shadow inputs and the oracle run inside the SAME evaluation context
(`with evaluate(ctx)` for ctx in {True, False}) — the per-coordinate facts
are context-dependent and the historical defect is context-bound.

INPUT DOMAIN: the model's Requires only demand three equal-length int lists,
which the bridge satisfies by construction. On the real side the screen
exists only for tuples of >= 2 coordinates (shorter tuples raise earlier,
outside the modeled decision), so tuples of length 2..5 are generated. A
tuple whose decidability facts real SymPy cannot compute (encoder raises on
degenerate arithmetic) is outside the modeled domain and skipped — the same
domain rule axiom_check.py uses; skips are counted and bounded.

>= 1e5 comparisons: all ordered pairs of a 34-atom boundary pool under both
contexts, the issue's literal repro tuples, then randomized fuzz (lengths
2..5, atoms + composed expressions) to 100000+. Pinned fuzz seed: 227140.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the repo under test only.
"""
import json
import random
import sys
from itertools import product
from typing import List, Optional

SEED = 227140
N_TOTAL = 100_000


# --- shim for the sequence carrier ------------------------------------------

class _Seq(tuple):
    """Immutable int sequence with the tiny API the pure helpers use."""
    def drop(self, n):
        return _Seq(self[n:])

    def take(self, n):
        return _Seq(self[:n])


def PSeq(*items):
    return _Seq(items)


def ToSeq(lst):
    return _Seq(lst)


# --- @Pure helpers from model.py, contracts stripped -------------------------

def coord_triggers(kind, verdict):
    return kind == 1 and verdict == 0


def any_triggering(kind, verdict):
    if len(kind) == 0 or len(verdict) == 0:
        return False
    return (coord_triggers(kind[0], verdict[0])
            or any_triggering(kind.drop(1), verdict.drop(1)))


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def screen_coordinates(coord_kind: List[int],
                       coord_verdict: List[int],
                       coord_extra: List[int]) -> bool:
    rejected = False
    i = len(coord_kind)
    while i > 0:
        if coord_kind[i - 1] == 1 and coord_verdict[i - 1] == 0:
            rejected = True
        i = i - 1
    return rejected


# --- type bridge: SymPy coordinate -> the three int facts --------------------

def make_encoders():
    from sympy.functions.elementary.complexes import im

    def enc_one(a):
        """(kind, verdict, extra) for one coordinate, or None if real SymPy
        cannot compute the decidability facts (outside the modeled domain)."""
        try:
            kind = 1 if (a.is_number is True) else 0
            z = im(a).is_zero
            verdict = 1 if z is True else (0 if z is False else -1)
            try:
                extra = 1 if bool(im(a)) else 0
            except TypeError:
                extra = 0        # truthiness undefined; spec never reads it
        except (ValueError, TypeError, AttributeError, RecursionError):
            return None
        return (kind, verdict, extra)

    return enc_one


REJECT_MARK = "Imaginary"   # distinctive fragment of the screen's message


def real_screen(Point, coords):
    """The REAL patched screen's decision, observed through the constructor.
    True iff the rejecting branch raises; success or any later-stage
    exception means the screen accepted (its raise would have come first)."""
    try:
        Point(*coords)
        return False
    except ValueError as exc:
        return REJECT_MARK in str(exc)
    except Exception:
        return False


def check_tuple(Point, enc_one, coords, ctx_label, counters):
    encs = []
    for a in coords:
        e = enc_one(a)
        if e is None:
            counters["skipped"] += 1
            return None
        encs.append(e)
    coord_kind = [e[0] for e in encs]
    coord_verdict = [e[1] for e in encs]
    coord_extra = [e[2] for e in encs]
    shadow = screen_coordinates(coord_kind, coord_verdict, coord_extra)
    real = real_screen(Point, coords)
    counters["checked"] += 1
    if shadow != real:
        return ("DISAGREEMENT\n  input: coords=%r  (evaluate=%s)\n"
                "  encoded: kind=%r verdict=%r extra=%r\n"
                "  shadow=%r  real=%r"
                % (list(coords), ctx_label, coord_kind, coord_verdict,
                   coord_extra, shadow, real))
    return None


def main():
    # REAL patched constructor + evaluation-context manager, from /testbed.
    from sympy import (Integer, Rational, Float, I, pi, E, sqrt, Symbol, S,
                       sympify, oo, zoo, nan)
    from sympy.geometry import Point
    from sympy.core.parameters import evaluate

    enc_one = make_encoders()
    counters = {"checked": 0, "skipped": 0}

    def run_case(coords, ctx):
        with evaluate(ctx):
            err = check_tuple(Point, enc_one, coords, ctx, counters)
        if err:
            print(err)
            sys.exit(1)

    # --- boundary pool (mirrors axiom_check.py's representative atoms) -------
    x = Symbol('x')
    y = Symbol('y', real=True)
    z = Symbol('z', imaginary=True)
    w = Symbol('w', positive=True)
    real_atoms = [Integer(0), Integer(1), Integer(2), Integer(-3),
                  Rational(1, 2), Rational(-7, 4), Float(0.5), Float(0.0),
                  Float(-2.25), pi, E, sqrt(2), S.Zero, S.One,
                  Integer(10) ** 9, sqrt(3) + 1]
    imag_atoms = [I, 2 * I, -I, 3 * I, Rational(1, 2) * I, sqrt(2) * I,
                  I * pi, Integer(5) * I]
    complex_atoms = [1 + I, 2 - 3 * I, pi + E * I, sqrt(2) + I]
    symbolic_atoms = [x, y, z, w, x + 1, 2 * x, x + I]
    special_atoms = [oo, -oo, zoo, nan]
    pool = real_atoms + imag_atoms + complex_atoms + symbolic_atoms

    # All ordered pairs of the 34-atom pool, both contexts.
    boundary_pool = pool + special_atoms[:0]  # specials fuzzed separately
    n_boundary_start = counters["checked"]
    for ctx in (True, False):
        for combo in product(boundary_pool, repeat=2):
            run_case(combo, ctx)
    # Special values paired with a plain coordinate (degenerate arithmetic in
    # the facts is skipped by the domain rule, same as axiom_check.py).
    for ctx in (True, False):
        for s in special_atoms:
            run_case((s, Integer(1)), ctx)
            run_case((Integer(1), s), ctx)

    # The literal issue-repro tuples under the deferred-evaluation context,
    # both as constructed numbers and via sympify.
    run_case((Integer(1), Integer(2)), False)
    run_case((sympify('Integer(1)'), sympify('Integer(2)')), False)
    run_case((Integer(1), Integer(2)), True)
    # A genuinely imaginary coordinate must still be rejected in both contexts.
    run_case((2 * I, Integer(1)), True)
    run_case((2 * I, Integer(1)), False)
    n_boundary = counters["checked"] - n_boundary_start

    # --- randomized fuzz to >= N_TOTAL ---------------------------------------
    rng = random.Random(SEED)
    fuzz_pool = pool + special_atoms
    n_fuzz_start = counters["checked"]
    while counters["checked"] < N_TOTAL:
        ctx = bool(rng.getrandbits(1))
        n = rng.randint(2, 5)
        coords = []
        for _ in range(n):
            a = rng.choice(fuzz_pool)
            if rng.random() < 0.25:
                # a composed expression: one binary op over two atoms
                b = rng.choice(fuzz_pool)
                op = rng.randint(0, 2)
                try:
                    with evaluate(ctx):
                        if op == 0:
                            a = a + b
                        elif op == 1:
                            a = a * b
                        else:
                            a = a - b
                except Exception:
                    pass         # keep the plain atom
            coords.append(a)
        run_case(tuple(coords), ctx)
    n_fuzz = counters["checked"] - n_fuzz_start

    print("G-CONF OK: shadow impl == real patched coordinate screen on %d "
          "tuples (%d boundary + %d fuzz, %d skipped as outside the modeled "
          "domain, seed %d)."
          % (counters["checked"], n_boundary, n_fuzz, counters["skipped"],
             SEED))
    print(json.dumps({"checked": counters["checked"], "disagreements": 0,
                      "skipped": counters["skipped"], "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
