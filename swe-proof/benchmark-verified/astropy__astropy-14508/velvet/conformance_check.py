#!/usr/bin/env python3
"""G-CONF differential conformance for astropy__astropy-14508.

The modeled `do` block (`formatFloatField`) has ONE A-reference op -- the float
renderer `shortestField` == `str(value).replace("e","E")`, whose soundness is
covered by G-AX (axiom_check.py) -- and the rest is the R/I 20-character trim:

    vs  = shortestField value                      # A-reference
    n   = len(vs)                                   # R (len over List Char)
    if n <= 20: return vs                           # I (control-flow guard)
    idx = eIndex vs                                 # R (find("E"), len sentinel)
    if idx >= n: return vs[:20]                     # R+I (slice [:20])
    else: return vs[:20-(n-idx)] + vs[idx:]         # R+I (slice + concat)

This file transliterates that R/I skeleton back to a concrete Python function
`shadow(value)` (with the renderer supplied by the real stdlib callee, since
that op is the audited A-reference) and differential-tests it against the GOLD
post-patch `_format_float` (patch.diff) over a large finite-float fuzz corpus.
Agreement on every input demonstrates the R/I transliteration of the trim is
faithful to the gold patch. Exit 0 iff 0 disagreements; stdlib-only.

Domain: finite floats (inf/nan rejected upstream by io.fits; see mapping.md §4).
"""
import math
import random
import sys


# --- GOLD post-patch _format_float (verbatim from patch.diff) ----------------

def gold_format_float(value):
    """Format a floating number to make sure it is at most 20 characters."""
    value_str = str(value).replace("e", "E")
    if (str_len := len(value_str)) > 20:
        idx = value_str.find("E")
        if idx < 0:
            value_str = value_str[:20]
        else:
            value_str = value_str[: 20 - (str_len - idx)] + value_str[idx:]
    return value_str


# --- R/I shadow: transliteration of the Lean `formatFloatField` do block -----
# The A-reference renderer op is the real audited callee (G-AX); everything else
# is the R/I trim, transliterated character-for-character from the Lean impl.

def shortest_field(value):                       # A-reference (audited by G-AX)
    return str(value).replace("e", "E")


def e_index(field):                              # R: eIndex / find("E"), len sentinel
    i = field.find("E")
    return len(field) if i < 0 else i


def shadow(value):
    vs = shortest_field(value)                   # A-reference
    n = len(vs)                                  # R
    if n <= 20:                                  # I
        return vs
    idx = e_index(vs)                            # R
    if idx >= n:                                 # R+I  (idx == len  <=>  find == -1)
        return vs[:20]                           # R+I  vs.take 20
    else:
        return vs[: 20 - (n - idx)] + vs[idx:]   # R+I  vs.take(20-(n-idx)) ++ vs.drop idx


def main():
    disagreements = 0
    n_checked = 0

    boundary = [
        0.009125, 8.95, -99.9, 1.0, -1.0, 0.0, 100.0, 0.1, 0.5,
        -467374636747637647347374734737437.0,
        1.2345377437887837487e88, 6324767364763746367e-33,
        1e-10, 1e10, 1e100, 1e-100, 1e308, 5e-324, 2.2250738585072014e-308,
        394633776111243.0,
        2.0 ** -24, 2.0 ** -44, 2.0 ** 122, 2.0 ** 0, 2.0 ** -1000,
        (1 - 2 ** -53) * 2.0 ** -60, (1 - 2 ** -53) * 2.0 ** 60,
        1.0 / 3.0, math.pi, math.e,
    ]
    for v in boundary:
        n_checked += 1
        if shadow(v) != gold_format_float(v):
            disagreements += 1
            print(f"DISAGREE on {v!r}: shadow={shadow(v)!r} gold={gold_format_float(v)!r}")

    rng = random.Random(14508)
    N = 120000
    for _ in range(N):
        mant = rng.uniform(-10.0, 10.0)
        exp = rng.randint(-308, 308)
        v = mant * (10.0 ** exp)
        if not math.isfinite(v):
            continue
        n_checked += 1
        if shadow(v) != gold_format_float(v):
            disagreements += 1
            if disagreements <= 10:
                print(f"DISAGREE on {v!r}: shadow={shadow(v)!r} gold={gold_format_float(v)!r}")

    # exact powers of two (the over-cap scientific path is exercised by large/small ones)
    for k in range(-1074, 1024):
        v = 2.0 ** k
        if not math.isfinite(v) or v == 0.0:
            continue
        n_checked += 1
        if shadow(v) != gold_format_float(v):
            disagreements += 1

    if disagreements == 0:
        print(f"G-CONF OK: R/I shadow of formatFloatField agrees with patch.diff "
              f"(gold _format_float) on {n_checked} finite-float inputs "
              f"(seed=14508, incl. powers of two), 0 disagreements.")
        return 0
    print(f"G-CONF FAIL: {disagreements} disagreements over {n_checked} inputs.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
