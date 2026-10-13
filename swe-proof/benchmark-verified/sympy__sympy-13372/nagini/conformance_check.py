#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13372 (nagini).

SHADOW: the impl region of model.py's `assemble_evalf_result`, copied VERBATIM
below with the contract calls (the two `Assert(...)` lines) stripped, together
with the `@Pure` helper `part_precision` (as a plain function), the
`EvalfResult` carrier (its `Ensures` stripped) and the user-defined
`EvalfDeferred` exception. No PSeq/ToSeq shim is needed (the carriers are ints
and Optional[int]); there are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo behaviour the model models per mapping.md — the
fallback block of `sympy.core.evalf.evalf(x, prec, options)` (the `except
KeyError:` body that splits the evaluated expression into real/imaginary parts,
classifies each part, and assembles `r = re, im, reprec, imprec`). The gate
applies patch.diff to /testbed before this script runs; PYTHONPATH=/testbed
makes the patched package importable. This script never applies any diff.

Driving the real block: `evalf` is entered through a minimal probe expression
whose class is absent from the numeric dispatch table (so the fallback path is
taken) and whose `_eval_evalf` returns a carrier exposing exactly the two parts
under test via `as_real_imag`. That injects an arbitrary (re_part, im_part)
pair straight into the modeled classification chains with the real module
untouched.

Type bridge (mapping.md section 2):
  * `re_kind` / `im_kind` are derived from each real part with the SAME
    predicates, in the same order, as the repo chain probes them:
    `part == 0` -> 0 (exact-zero), `elif part.is_number` -> 1 (numeric),
    else -> 2 (other).
  * the model's `prec` is the working-precision argument (a positive int by
    construction in every caller, so the fuzz domain is prec >= 1).
  * observable outcome: a normal return maps to the two assembled precision
    components (`r[2]`, `r[3]`) vs the shadow's `EvalfResult` fields (None for
    absent, the int precision otherwise); a `NotImplementedError` escaping the
    block maps to the shadow's `EvalfDeferred` (mapping.md section 2: the
    user-defined stand-in for the deferral signal).

Domain notes (both documented abstractions of mapping.md sections 2-3):
  * parts are real-valued expressions free of unevaluated real/imag-part
    extractors, so the pre-existing guard ABOVE the modeled block never fires
    and every probe reaches the classification chains;
  * numeric parts are finite real numbers, for which the (abstracted,
    unchanged) value conversion inside the numeric branch is total — the
    modeled delta is the precision components and the defer obligation, not
    the value computation.

>= 1e5 Requires-satisfying inputs: structured boundary cases covering all nine
(re_kind, im_kind) combinations (including the issue's OTHER-part shapes and
zero-valued floats/rationals that classify as exact-zero) plus 100000 fuzz
draws over a part pool spanning all three cases and varied precisions.
Pinned fuzz seed: 133720.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib only (random; hypothesis not needed).
"""
import json
import random
import sys
from typing import Optional

SEED = 133720
N_FUZZ = 100_000


# --- model.py exception + result carrier, contracts stripped ------------------

class EvalfDeferred(Exception):
    """Signals that a result cannot be assembled because some part is neither
    an exact zero nor a concrete number, so no precision component is defined
    for it."""


class EvalfResult:
    """The assembled result: the two touched precision components."""

    def __init__(self, reprec, imprec):
        self.reprec = reprec
        self.imprec = imprec


# --- @Pure helper from model.py, contracts stripped ---------------------------

def part_precision(kind, prec):
    """The precision component for one part: absent (None) for an exact-zero
    part (kind 0), the working precision for a numeric part (kind 1)."""
    if kind == 0:
        return None
    return prec


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def assemble_evalf_result(re_kind, im_kind, prec):
    # Classify the real part. The precision component is set only in the
    # exact-zero and numeric cases; the OTHER case defers before any result is
    # assembled (so no result is ever built around a missing component).
    reprec = None  # type: Optional[int]
    if re_kind == 0:
        reprec = None
    elif re_kind == 1:
        reprec = prec
    else:
        raise EvalfDeferred()
    # Classify the imaginary part identically.
    imprec = None  # type: Optional[int]
    if im_kind == 0:
        imprec = None
    elif im_kind == 1:
        imprec = prec
    else:
        raise EvalfDeferred()
    return EvalfResult(reprec, imprec)


# --- bridge ---------------------------------------------------------------


def part_kind(part):
    """The three-way case tag for one part, computed with the SAME predicates
    the repo classification chain uses, in the same order."""
    if part == 0:
        return 0
    elif part.is_number:
        return 1
    else:
        return 2


def shadow_outcome(re_kind, im_kind, prec):
    """Run the shadow; map its observable to a comparable tuple."""
    try:
        res = assemble_evalf_result(re_kind, im_kind, prec)
    except EvalfDeferred:
        return ("defer",)
    return ("ret", res.reprec, res.imprec)


def make_driver():
    """Build the probe machinery over the REAL patched module and return
    (drive, evalf_module). `drive(re_part, im_part, prec)` pushes the pair
    through the real fallback block and maps the observable outcome."""
    import sympy  # noqa: F401  (ensures the package + submodules are loaded)
    from sympy import Integer
    from sympy.core.expr import Expr
    EV = sys.modules.get("sympy.core.evalf")
    if EV is None:
        from sympy.core import evalf as EV  # pragma: no cover

    # Warm the numeric dispatch table so the probe's class misses it (the
    # fallback path is entered via that miss).
    Integer(2).evalf()

    class _Split(Expr):
        """Carrier returned by the probe's evaluation step: exposes exactly
        the two parts under test."""

        def __new__(cls, re_part, im_part):
            obj = Expr.__new__(cls)
            obj._re_part = re_part
            obj._im_part = im_part
            return obj

        def as_real_imag(self, deep=True, **hints):
            return (self._re_part, self._im_part)

    class _Probe(Expr):
        """Entry expression: absent from the dispatch table, so the numeric
        evaluator takes its fallback path; its evaluation step yields the
        carrier above."""

        def __new__(cls, carrier):
            obj = Expr.__new__(cls)
            obj._carrier = carrier
            return obj

        def _eval_evalf(self, prec):
            return self._carrier

    def drive(re_part, im_part, prec):
        probe = _Probe(_Split(re_part, im_part))
        try:
            r = EV.evalf(probe, prec, {})
        except NotImplementedError:
            return ("defer",)
        except BaseException as exc:  # any other escape is a disagreement
            return ("raise", type(exc).__name__, str(exc))
        reprec, imprec = r[2], r[3]
        return ("ret", reprec, imprec)

    return drive


def check_one(drive, re_part, im_part, prec):
    rk = part_kind(re_part)
    ik = part_kind(im_part)
    # Requires hold by construction: kinds are in {0,1,2}.
    assert 0 <= rk <= 2 and 0 <= ik <= 2
    shadow = shadow_outcome(rk, ik, prec)
    real = drive(re_part, im_part, prec)
    if real != shadow:
        return ("DISAGREEMENT\n  re_part=%r im_part=%r prec=%r\n"
                "  kinds=(%d, %d)\n  shadow=%r  real=%r"
                % (re_part, im_part, prec, rk, ik, shadow, real))
    return None


def build_part_pool():
    """Parts spanning all three cases: exact zeros (several spellings),
    finite real numerics (cheap and moderately rich), and symbolic OTHER
    parts (including the issue's shape)."""
    from sympy import (Integer, Rational, Float, sqrt, pi, E, sin, log,
                       symbols, Max, Min, Abs)
    x, y, z = symbols("x y z")
    zeros = [Integer(0), Rational(0, 1), Float(0), Float("-0.0")]
    numerics = [Integer(1), Integer(-5), Integer(3), Rational(7, 2),
                Rational(-1, 3), Float(2.5), Float("-1e10"), Float("1e-12"),
                sqrt(2), pi, E, sin(Integer(1)), log(Integer(2)),
                Rational(10**12, 7), Integer(2)**30]
    others = [x, y, x + 1, 2 * x, x * y, Max(0, y), Min(x, 3), Abs(z) + 1,
              sin(x), sqrt(x + 1), Max(0, y) + 1]
    return zeros, numerics, others


def boundary_cases(zeros, numerics, others):
    """All nine (re_kind, im_kind) combinations, several precisions, and the
    exact part shapes from the issue's failing input."""
    from sympy import symbols, Max
    x, y = symbols("x y")
    precs = [1, 2, 10, 53, 64, 128, 300]
    cases = []
    reps = {0: zeros[:2], 1: numerics[:3], 2: others[:3]}
    for rk in (0, 1, 2):
        for ik in (0, 1, 2):
            for rp in reps[rk]:
                for ip in reps[ik]:
                    for prec in precs:
                        cases.append((rp, ip, prec))
    # the issue's shape: an OTHER real part alongside an exact-zero imag part
    for prec in precs:
        cases.append((Max(0, y), zeros[0], prec))
        cases.append((x * Max(0, y), zeros[0], prec))
    # zero spellings that must classify as exact-zero, not numeric
    for zp in zeros:
        cases.append((zp, zp, 53))
        cases.append((zp, numerics[0], 53))
        cases.append((numerics[0], zp, 53))
        cases.append((zp, others[0], 53))
        cases.append((others[0], zp, 53))
    return cases


def main():
    drive = make_driver()
    zeros, numerics, others = build_part_pool()

    checked = 0
    n_boundary = 0
    for re_part, im_part, prec in boundary_cases(zeros, numerics, others):
        err = check_one(drive, re_part, im_part, prec)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    pool = zeros + numerics + others
    # weight precisions toward the values real callers pass (binary precision
    # derived from decimal digits), with boundary lows and occasional highs
    prec_choices = [1, 2, 4, 10, 30, 53, 57, 64, 100, 128, 200, 300]
    for _ in range(N_FUZZ):
        re_part = rng.choice(pool)
        im_part = rng.choice(pool)
        if rng.random() < 0.8:
            prec = rng.choice(prec_choices)
        else:
            prec = rng.randint(1, 300)
        err = check_one(drive, re_part, im_part, prec)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real evalf fallback (precision "
          "components / deferral) on %d inputs (%d boundary + %d fuzz, "
          "seed %d)." % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
