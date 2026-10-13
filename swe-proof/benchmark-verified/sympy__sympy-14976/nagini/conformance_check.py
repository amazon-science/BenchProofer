#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-14976 (nagini).

SHADOW: the impl region of model.py's `render_mpf_ratio`, copied VERBATIM
below with the contract calls (Requires/Ensures) stripped. The impl region
uses only plain Python lists (no PSeq/ToSeq snapshots inside the impl), so no
sequence shim is needed; the @Pure helpers (`ctor`, `rendered`) are spec-only
and are not called by the impl, so they do not appear in the shadow. There
are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo callee the model models per mapping.md /
meta.json — `sympy.printing.pycode.MpmathPrinter._print_Rational`, invoked on
a default-constructed printer. The gate applies patch.diff to /testbed before
this script runs; PYTHONPATH=/testbed makes the patched package importable.
The modeled method is called DIRECTLY (not via `doprint`): SymPy's
`Rational(p, q)` constructor canonicalises, so ratios that reduce to an
integer are re-typed and `doprint` would dispatch them to a different printer
method, bypassing the modeled one. The modeled method itself accepts every
reduced (e.p, e.q), so calling it directly covers the whole domain including
the q == 1 boundary. (axiom_check.py uses the identical oracle for the same
reason.)

Type bridge (mapping.md section 2): the model's two List[int] parameters are
the decimal digit strings of the REDUCED numerator and denominator as Unicode
code points — p_digits[k] == ord(str(r.p)[k]) and likewise for q_digits — and
the model's List[int] result maps to the returned str via the same
code-point encoding. So for each generated integer pair (p, q) the driver
builds `r = Rational(p, q)`, feeds the code points of str(r.p) / str(r.q) to
the shadow, and compares against the code points of the real method's output
string. Exact list equality; no numeric abstraction.

Input domain: the model's Requires only demand list access, and the bridge
restricts the inputs the repo ever produces to digit strings of a reduced
integer pair; the driver generates exactly those. Boundary cases (the
reported observation shapes, reductions to integer/zero/unit values, sign
placement, magnitude extremes) + fuzz to >= 1e5 pairs. Pinned fuzz seed:
1497614976 (recorded here and in the summary line).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys
from typing import List

SEED = 1497614976
N_TOTAL = 100_000


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def render_mpf_ratio(p_digits: List[int], q_digits: List[int]) -> List[int]:
    out = []  # type: List[int]
    # ctor '('
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    # numerator digits
    out = out + p_digits
    # ')' '/'
    out = out + [41]
    out = out + [47]
    # ctor '('
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    # denominator digits
    out = out + q_digits
    # ')'
    out = out + [41]
    return out


# --- differential driver -------------------------------------------------------

def check_case(printer, Rational, p, q):
    """Run shadow and oracle on one integer pair; return an error string on
    disagreement, else None. The bridge feeds the shadow the code points of
    the REDUCED numerator/denominator the constructed object stores."""
    r = Rational(p, q)
    p_digits = [ord(ch) for ch in str(r.p)]
    q_digits = [ord(ch) for ch in str(r.q)]
    shadow = render_mpf_ratio(p_digits, q_digits)
    try:
        real = [ord(ch) for ch in printer._print_Rational(r)]
    except Exception as exc:  # in-domain input must not raise
        return ("DISAGREEMENT (oracle raised)\n  input: p=%r q=%r "
                "(reduced p=%r q=%r)\n  shadow=%r ('%s')\n  real raised %s: %s"
                % (p, q, r.p, r.q, shadow, ''.join(map(chr, shadow)),
                   type(exc).__name__, exc))
    if shadow != real:
        return ("DISAGREEMENT\n  input: p=%r q=%r (reduced p=%r q=%r)"
                "\n  shadow=%r ('%s')\n  real=%r ('%s')"
                % (p, q, r.p, r.q, shadow, ''.join(map(chr, shadow)),
                   real, ''.join(map(chr, real))))
    return None


def boundary_cases():
    """Hand-picked pairs: the reported observation shapes, pairs that reduce
    (including to integer / zero / unit values, where the denominator becomes
    1), negative numerators and denominators (sign normalises onto the
    numerator), single-digit and many-digit magnitudes."""
    return [
        (1, 2),
        (232, 3),
        (1, 3),
        (2, 4),          # reduces to 1/2
        (5, 1),          # integer-valued
        (-1, 2),
        (1, -2),         # sign moves to the numerator on reduction
        (-1, -2),        # signs cancel
        (1, 1),          # unit
        (0, 5),          # zero -> reduced 0/1
        (-5, 1),
        (123456789, 987654321),
        (-7, 9),
        (100, 7),
        (10 ** 40, 3),   # many-digit numerator
        (3, 10 ** 40),   # many-digit denominator
        (10 ** 40 + 1, 10 ** 40),
        (-10 ** 40, 7),
        (6, 3),          # reduces to integer 2
        (-6, 4),         # reduces to -3/2
    ]


def main():
    # REAL patched callee (mapping.md section 1) — importable from /testbed.
    from sympy import Rational
    from sympy.printing.pycode import MpmathPrinter

    printer = MpmathPrinter()  # default settings

    # Guard: the modeled method must exist on the printer class itself (it is
    # introduced by the patch under test); fail loud if we are somehow running
    # against an unpatched tree, where the inherited fallback would be a
    # different method entirely.
    if 'MpmathPrinter' not in type(printer)._print_Rational.__qualname__:
        print("ERROR: modeled method not found on the printer class — this "
              "check must run with the patch applied.")
        return 1

    checked = 0

    for p, q in boundary_cases():
        err = check_case(printer, Rational, p, q)
        if err:
            print(err)
            return 1
        checked += 1

    # Fuzz to >= N_TOTAL pairs total, mixing magnitude bands so digit-string
    # lengths from 1 to ~40 are all exercised, with both signs and a steady
    # share of reducing pairs (common factors) and q == 1 / p == 0 shapes.
    rng = random.Random(SEED)
    n_fuzz = N_TOTAL - checked
    for k in range(n_fuzz):
        band = rng.random()
        if band < 0.4:
            hi = 10 ** 3
        elif band < 0.8:
            hi = 10 ** 9
        else:
            hi = 10 ** 40
        p = rng.randint(0, hi)
        q = rng.randint(1, hi)
        if rng.random() < 0.5:
            p = -p
        if rng.random() < 0.3:
            q = -q
        if k % 10 == 0:
            q = 1            # integer-valued shapes
        elif k % 10 == 1:
            p = 0            # zero shapes
        elif k % 10 == 2:
            g = rng.randint(2, 1000)
            p, q = p * g, q * g   # guaranteed common factor -> reduction
        err = check_case(printer, Rational, p, q)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real renderer output on %d pairs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary_cases()), n_fuzz, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
