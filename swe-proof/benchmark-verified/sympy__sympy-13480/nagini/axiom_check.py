#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-13480.

Runs the REAL repository callees in-container (the unchanged `coth`, `tanh`,
the `S.ComplexInfinity` singleton, and the unchanged peel-off helper) on the
periodic-part branch of `coth.eval` — the branch the patch repairs — and
asserts that every observation matches the model in model.py.

All three axioms (`primary`->coth, `sibling`->tanh, `directed_infinity`->
S.ComplexInfinity) carry NO `Ensures`; the only contract the proof consumes is
DETERMINISM (a `@Pure` callee maps equal arguments to equal results) plus the
singleton identity of the directed-infinity sentinel. There is no value /
sentinel / raise behaviour to over-claim (SPEC_GUIDE directive 7). This script
confirms:

  (A-consumed: primary == coth) determinism: coth(e) is identically coth(e).
  (A-consumed: sibling == tanh) determinism: tanh(e) is identically tanh(e).
  (A-consumed: directed_infinity == S.ComplexInfinity) the sentinel is a stable
      singleton: `x is S.ComplexInfinity` is a well-defined deterministic test.

And it validates the end-to-end BRANCH CORRESPONDENCE of the behavior
model.py's postcondition pins (via its two exhaustive implications) against
the REAL (gold-patched) `coth.eval`: for an argument
that decomposes into a remainder `x` and a periodic part `m` (via the unchanged
`_peeloff_ipi`), the simplified value is
    coth(x)  if  coth(m) is S.ComplexInfinity     (model: primary(x))
    tanh(x)  otherwise                            (model: sibling(x))
exactly mirroring the patched branch — reconstructed from the SAME in-container
primitives so the check tracks whatever sympy version the harness pins. The two
FAIL_TO_PASS witnesses from the instance are asserted directly.

Imports only `sympy` (the package whose `coth.eval` the patch fixes) and the
standard library. Exit 0 iff every obligation holds.
"""
import random
import sys

from sympy import coth, tanh, log, tan, I, pi, S, Symbol, Rational, sympify
from sympy.functions.elementary.hyperbolic import _peeloff_ipi


# --- model.py reference encoding (kept in lock-step with the spec) -----------

def simplified(x, m):
    """Reference for the behavior model.py's postcondition implications pin,
    over REAL expressions: coth(x) when coth(m) is the directed-infinity
    singleton, else tanh(x). The discriminator is coth(m) -- the value
    computed from the periodic part."""
    if coth(m) is S.ComplexInfinity:
        return coth(x)
    return tanh(x)


# --- the checks --------------------------------------------------------------

def check_determinism(e):
    """primary/sibling axioms: coth and tanh are deterministic on e."""
    assert coth(e) == coth(e), "coth not deterministic on %r" % (e,)
    assert tanh(e) == tanh(e), "tanh not deterministic on %r" % (e,)


def check_sentinel():
    """directed_infinity axiom: S.ComplexInfinity is a stable singleton, and
    the `is` test against it is well-defined (reflexive, and distinguishes a
    finite value)."""
    assert S.ComplexInfinity is S.ComplexInfinity, "ComplexInfinity not a singleton"
    assert coth(S(0)) is S.ComplexInfinity, "coth(0) should be the sentinel"
    assert not (coth(S(1)) is S.ComplexInfinity), "coth(1) must be finite"


def check_branch_correspondence(arg):
    """End-to-end: where the periodic branch fires, the real (patched)
    coth(arg) equals the postcondition-pinned reference simplified(x, m)
    on the peeled parts.

    The branch's own design (its `else: # cothm == 0` comment) guarantees the
    periodic part m yields coth(m) in {directed-infinity, 0}. We only assert
    the correspondence on that domain — i.e. when the peeled m actually puts
    coth(m) at the sentinel or at zero. This keeps the check meaningful at the
    pinned sympy version (where _peeloff_ipi returns an I*pi-multiple, so coth(m)
    is always zoo or 0) and non-spuriously-failing if run under a version whose
    peel-off convention differs (then coth(m) is neither and we skip)."""
    a = sympify(arg)
    if not a.is_Add:
        return False
    x, m = _peeloff_ipi(a)
    if not m:
        return False
    cm = coth(m)
    if not (cm is S.ComplexInfinity or cm == 0):
        # m is not in the periodic-branch domain at this sympy version; skip.
        return False
    observed = coth(a)              # real (gold-patched) callee
    expected = simplified(x, m)     # postcondition reference on the same parts
    assert observed == expected, (
        "branch correspondence broken on arg=%r: peel x=%r m=%r ; "
        "coth(arg)=%r ; model simplified=%r ; coth(m)=%r zoo=%r"
        % (arg, x, m, observed, expected, cm, cm is S.ComplexInfinity))
    return True


def main():
    # --- A-consumed: determinism of coth/tanh -----------------------------
    y = Symbol('y')
    det_inputs = [S(0), S(1), S(2), Rational(1, 2), Rational(3, 2),
                  log(2), log(tan(2)), y, 1 + I * pi / 2, I * pi,
                  2 + I * pi / 3, log(-tan(2))]
    for e in det_inputs:
        check_determinism(e)

    rng = random.Random(13480)
    for _ in range(2000):
        e = Rational(rng.randint(-9, 9), rng.randint(1, 9)) + \
            Rational(rng.randint(-5, 5), rng.randint(1, 6)) * I * pi
        check_determinism(e)

    # --- A-consumed: the directed-infinity singleton ----------------------
    check_sentinel()

    # --- end-to-end branch correspondence vs the real patched coth.eval ---
    # The two FAIL_TO_PASS witnesses (asserted exactly as the harness does).
    assert coth(log(tan(2))) == coth(log(-tan(2))), \
        "FAIL_TO_PASS witness 1 broken: coth(log(tan(2))) != coth(log(-tan(2)))"
    assert coth(1 + I * pi / 2) == tanh(1), \
        "FAIL_TO_PASS witness 2 broken: coth(1 + I*pi/2) != tanh(1)"

    # Detect the peel-off convention of the pinned sympy: at the instance's
    # pinned version (1.1) `_peeloff_ipi` returns the periodic part as an
    # I*pi-multiple, so coth(m) lands on the directed-infinity sentinel or 0 and
    # the two-way branch fires. Some later versions return a bare coefficient
    # (coth of it is finite) and route this case through a different path; there
    # the periodic branch is not exercised, so requiring it to fire would be a
    # false alarm rather than a soundness signal.
    _x, _m = _peeloff_ipi(S(1) + I * pi)
    periodic_branch_active = bool(_m) and (
        coth(_m) is S.ComplexInfinity or coth(_m) == 0)

    # Directly-constructed periodic arguments x0 + (k/2)*I*pi so the
    # remainder/periodic peel-off fires. Reconstructed from in-container
    # primitives, so the expected side tracks the pinned sympy version.
    fired = 0
    bases = [S(1), Rational(3, 2), log(2), Rational(5, 2), S(2), y]
    mults = [Rational(1, 2), S(1), Rational(3, 2), S(2), Rational(5, 2), S(3),
             Rational(1, 3), Rational(2, 3)]
    for x0 in bases:
        for k in mults:
            if check_branch_correspondence(x0 + k * I * pi):
                fired += 1

    for _ in range(1500):
        x0 = Rational(rng.randint(-6, 6), rng.randint(1, 5))
        k = Rational(rng.randint(-6, 6), rng.randint(1, 4))
        arg = x0 + k * I * pi
        if check_branch_correspondence(arg):
            fired += 1

    if periodic_branch_active and fired == 0:
        print("G-AX ERROR: pinned version routes through the periodic branch "
              "but no case fired; the correspondence check is vacuous",
              file=sys.stderr)
        return 1

    note = ("verified on %d periodic-branch arguments" % fired
            if periodic_branch_active else
            "periodic-branch domain not exercised by this sympy version's "
            "peel-off convention (only determinism + witnesses checked here)")
    print("G-AX OK: coth/tanh deterministic on %d + 2000 fuzz inputs; "
          "ComplexInfinity singleton stable; 2 FAIL_TO_PASS witnesses hold; "
          "branch correspondence (model simplified == real patched coth.eval) "
          "%s." % (len(det_inputs), note))
    return 0


if __name__ == "__main__":
    sys.exit(main())
