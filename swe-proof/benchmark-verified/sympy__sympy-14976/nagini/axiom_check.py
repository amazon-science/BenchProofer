#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-14976.

Executes the REAL SymPy callees on Requires-satisfying inputs (boundary cases
over numerator/denominator magnitude and sign, plus randomized fuzzing) and
asserts that every observation matches the deep model encoded in model.py.

The kind-A checks (both A-reference — there are NO consumed @ContractOnly
axioms in this bundle):

  (A-reference) the deep model `ctor` (model.py pure region) == the real
      unchanged helper `MpmathPrinter()._module_format('mpmath.mpf')`. Under the
      printer's default `fully_qualified_modules=True`, this returns the fixed
      token 'mpmath.mpf'.

  (A-reference) the deep model `rendered(p, q)` (model.py pure region) == the
      real patched renderer method `MpmathPrinter()._print_Rational(Rational(p, q))`:
          ctor '(' str(e.p) ')' '/' ctor '(' str(e.q) ')'
      where e.p / e.q are the REDUCED numerator / denominator SymPy stores.

      The oracle calls the modeled method `_print_Rational` DIRECTLY rather than
      the top-level dispatcher `doprint`. This is deliberate and required for
      soundness: SymPy's `Rational(p, q)` constructor auto-canonicalises, so any
      ratio that reduces to an integer (q == 1 after reduction — e.g.
      Rational(5, 1) -> Integer, Rational(0, 5) -> Zero) is re-typed away from
      `Rational`. `doprint` then dispatches such objects to `_print_Integer`,
      bypassing the modeled `_print_Rational` entirely, so a `doprint` oracle
      would compare the wrong method's output (`'5'`) against the modeled body
      (`mpmath.mpf(5)/mpmath.mpf(1)`) and spuriously fail. `_print_Rational` IS
      the function model.py models (meta.json modeled_functions[0].repo_symbol);
      it wraps both operands unconditionally for ALL p, q, so the A-reference
      holds across the whole fuzz domain including the q == 1 boundary cases.
      The exact F2P observation (which DOES go through `doprint`, since q == 2
      stays a Rational) is asserted separately at the end of main().

Imports nothing outside the repo under test: `sympy` is the package the gold
patch lives in. Exit 0 iff every obligation holds.

NOTE: this checker validates the *patched* renderer (`_print_Rational` is ADDED
by the gold patch — it does not exist pre-patch, where a Rational falls back to
the inherited StrPrinter bare `p/q`). It MUST therefore be run with the gold
patch applied in the official SWE-bench container for this instance (Python 3.6
image), i.e. `docker_exec.run_in_container(..., apply_gold=True)`. A guard in
main() fails loudly if the patched method is absent. It is NOT run on the
construction host (whose Python lacks distutils for this old sympy).
"""
import random
import sys

from sympy import Rational
from sympy.printing.pycode import MpmathPrinter

# model.py reference encoding of the constructor token, kept in lock-step
# with `ctor()` in model.py.
_CTOR = [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]  # 'mpmath.mpf'
_LPAREN, _RPAREN, _SLASH = 40, 41, 47


def rendered_model(p_int, q_int):
    """Reference implementation of model.py's deep model `rendered`, as a list
    of code points: ctor '(' str(p) ')' '/' ctor '(' str(q) ')'."""
    p_digits = [ord(ch) for ch in str(p_int)]
    q_digits = [ord(ch) for ch in str(q_int)]
    return (_CTOR + [_LPAREN] + p_digits + [_RPAREN] + [_SLASH]
            + _CTOR + [_LPAREN] + q_digits + [_RPAREN])


def check_ctor_reference(printer):
    """Assert ctor() == the REAL _module_format('mpmath.mpf') (default flag)."""
    observed = [ord(ch) for ch in printer._module_format('mpmath.mpf')]
    assert observed == _CTOR, (
        "ctor deep model unsound: _module_format('mpmath.mpf') gave %r, "
        "ctor() gives %r" % (observed, _CTOR))


def check_rendered_reference(printer, p, q):
    """Assert rendered(...) == the REAL MpmathPrinter._print_Rational output.

    The real method reads the REDUCED e.p / e.q, so the expected model uses the
    reduced numerator/denominator the constructed Rational stores. We call the
    modeled method `_print_Rational` DIRECTLY (not `doprint`): for ratios that
    canonicalise to an integer (q == 1 after reduction) `doprint` would dispatch
    to `_print_Integer` and bypass the modeled method (see module docstring)."""
    r = Rational(p, q)
    # the patched renderer method itself (the function model.py models); it
    # wraps both operands unconditionally for every reduced (e.p, e.q).
    observed = [ord(ch) for ch in printer._print_Rational(r)]
    expected = rendered_model(r.p, r.q)
    assert observed == expected, (
        "rendered deep model unsound on Rational(%r, %r) (reduced p=%r q=%r): "
        "real renderer gave %r, deep model gives %r"
        % (p, q, r.p, r.q, observed, expected))


def main():
    printer = MpmathPrinter()           # default settings, fully_qualified=True

    # Guard: this checker validates the PATCHED renderer; `_print_Rational` is
    # added by the gold patch. If it is absent we are running pre-patch (the
    # gold patch was not applied) and the A-reference is meaningless — fail loud
    # rather than silently validate the inherited StrPrinter fallback.
    assert 'MpmathPrinter' in type(printer)._print_Rational.__qualname__, (
        "MpmathPrinter._print_Rational not found on the printer class — run this "
        "checker with the gold patch applied (apply_gold=True); it validates the "
        "patched renderer, which does not exist pre-patch.")

    # --- ctor (A-reference): the unchanged module-formatter ---------------
    check_ctor_reference(printer)

    # --- rendered (A-reference): boundary (p, q) pairs --------------------
    boundary = [
        (1, 2),        # the F2P test input -> 'mpmath.mpf(1)/mpmath.mpf(2)'
        (232, 3),      # the issue's 77 + 1/3 numerator
        (1, 3),        # the P2P nsolve_rational input
        (2, 4),        # reduces to 1/2 (uses reduced e.p/e.q)
        (5, 1),        # integer-valued (reduces to Integer; _print_Rational still wraps)
        (-1, 2),       # negative numerator
        (1, 1),        # unit (reduces to One; _print_Rational still wraps)
        (0, 5),        # zero numerator -> reduces to Zero (e.p=0, e.q=1); still wraps
        (123456789, 987654321),
        (-7, 9),
        (100, 7),
    ]
    for p, q in boundary:
        check_rendered_reference(printer, p, q)

    # --- rendered (A-reference): randomized fuzz --------------------------
    rng = random.Random(14976)
    for _ in range(5000):
        p = rng.randint(-10 ** 6, 10 ** 6)
        q = rng.randint(1, 10 ** 6)
        if rng.random() < 0.5:
            q = -q
        check_rendered_reference(printer, p, q)

    # explicit F2P assertion (the exact hidden-test observation)
    assert printer.doprint(Rational(1, 2)) == 'mpmath.mpf(1)/mpmath.mpf(2)', (
        "F2P observation mismatch: %r" % printer.doprint(Rational(1, 2)))

    print("G-AX OK: ctor deep model (== _module_format('mpmath.mpf')) + "
          "rendered deep model (== MpmathPrinter._print_Rational, called "
          "directly) sound on %d boundary + 5000 fuzz Rationals; F2P "
          "doprint(Rational(1,2)) observation confirmed" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
