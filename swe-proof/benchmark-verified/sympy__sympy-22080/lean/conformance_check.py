#!/usr/bin/env python3
"""G-CONF for sympy__sympy-22080.

Differential test: the R/I shadow of `implementation_renderProduct` (the Lean
impl, transcribed in Python) vs an in-process replica of the POST-PATCH
`_print_Mul` tail. Both consume the leading sign, the product's own precedence
`prec`, the numerator factor list (each factor carries its binding strength
`precedence(item)` and its already-rendered text `self._print(item)`), and the
denominator as a list of FULLY RENDERED texts (`b_str` after the unchanged
`self.parenthesize(x, prec)` rendering AND the unchanged `pow_paren`
group-wrapping post-processing — see mapping.md; the fix does not touch the
denominator pipeline, so its output texts are R-abstracted inputs). We fuzz
those inputs and assert byte-identical output over >=1e5 samples.

stdlib-only; exit 0 iff zero disagreements.
"""
import json
import random
import sys
from fractions import Fraction

SEED = 22080
N = 100_000

NEG_SINGLE_LEVEL = Fraction(55)  # 0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"]) = 0.5*(60+50)

# Real precedence weights that occur for the modeled inputs (mapping.md):
#  40 = Add (a negative product's own precedence), 49.5 = pow-expanded power
#  product, 50 = Mul (post-patch Mod strength), 55 = the threshold itself,
#  60 = Pow, 70 = Func (pre-patch Mod strength), 1000 = Atom.
WEIGHTS = [Fraction(40), Fraction(99, 2), Fraction(50), Fraction(55),
           Fraction(60), Fraction(70), Fraction(1000)]


def paren_factor(level, strength, text):
    """parenFactor: wrap iff strength <= level (parenthesize default strict=False)."""
    return ("(" + text + ")") if strength <= level else text


def lean_shadow(sign, prec, num, den):
    """Transcription of implementation_renderProduct (the R/I legs).

    `num` is a list of (strength, text) numerator factors; `den` is a list of
    fully rendered denominator texts (strings).
    """
    if len(num) == 1 and sign == "-":
        num_str = [paren_factor(NEG_SINGLE_LEVEL, s, t) for (s, t) in num]
    else:
        num_str = [paren_factor(prec, s, t) for (s, t) in num]
    body = "*".join(num_str)
    if not den:
        return sign + body
    elif len(den) == 1:
        return sign + body + "/" + den[0]
    else:
        return sign + body + "/(" + "*".join(den) + ")"


def patched_replica(sign, prec, num, den):
    r"""In-process replica of the post-patch `_print_Mul` tail.

    Mirrors the repo source exactly:
        if len(a) == 1 and sign == "-":
            a_str = [self.parenthesize(a[0], 0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"]))]
        else:
            a_str = [self.parenthesize(x, prec) for x in a]
        b_str = [self.parenthesize(x, prec) for x in b]
        # pow_paren post-processing may further wrap b_str entries (#14160)
        if not b:        return sign + '*'.join(a_str)
        elif len(b)==1:  return sign + '*'.join(a_str) + "/" + b_str[0]
        else:            return sign + '*'.join(a_str) + "/(%s)" % '*'.join(b_str)

    where self.parenthesize(item, level) (default strict=False) wraps iff
    precedence(item) <= level; precedence(item) is the factor's `strength`.
    The denominator pipeline (parenthesize against prec, then the pow_paren
    group-wrapping loop) is UNCHANGED by the patch; its resulting texts b_str
    are consumed here as the input `den` (len(b) == len(b_str)).
    """
    def parenthesize(strength, text, level):
        return ("(%s)" % text) if strength <= level else text

    if len(num) == 1 and sign == "-":
        a_str = [parenthesize(num[0][0], num[0][1], NEG_SINGLE_LEVEL)]
    else:
        a_str = [parenthesize(s, t, prec) for (s, t) in num]
    b_str = list(den)  # fully rendered denominator texts (input)
    if not den:
        return sign + "*".join(a_str)
    elif len(den) == 1:
        return sign + "*".join(a_str) + "/" + b_str[0]
    else:
        return sign + "*".join(a_str) + "/(%s)" % "*".join(b_str)


def rand_text(rng):
    alphabet = "xyz01 *+-/()%"
    n = rng.randint(0, 8)
    return "".join(rng.choice(alphabet) for _ in range(n))


def rand_factor(rng):
    if rng.random() < 0.7:
        s = rng.choice(WEIGHTS)
    else:
        s = Fraction(rng.randint(0, 2000), rng.choice([1, 2]))
    return (s, rand_text(rng))


def rand_factor_list(rng, min_len=0, max_len=4):
    n = rng.randint(min_len, max_len)
    return [rand_factor(rng) for _ in range(n)]


def rand_text_list(rng, min_len=0, max_len=4):
    n = rng.randint(min_len, max_len)
    return [rand_text(rng) for _ in range(n)]


def main() -> int:
    rng = random.Random(SEED)
    # hand-picked edge cases first (mirroring the issue's expressions plus the
    # denominator branches, incl. pow_paren-wrapped denominator texts)
    edge = [
        # -Mod(x, y): single Mod factor (post-patch strength 50) under leading "-"
        ("-", Fraction(40), [(Fraction(50), "x % y")], []),
        # Mod(-x, y): no leading sign, single factor of strength 50
        ("", Fraction(70), [(Fraction(50), "(-x) % y")], []),
        # -x**4 expanded: single power-product factor of strength 49.5
        ("-", Fraction(40), [(Fraction(99, 2), "x*x*x*x")], []),
        # x**4 - x**2 expanded: numerator is the whole Add, sign "" (>1 factor not)
        ("", Fraction(40), [(Fraction(40), "-x*x + x*x*x*x")], []),
        # general multi-factor numerator under "-": NOT the special case
        ("-", Fraction(50), [(Fraction(50), "a"), (Fraction(50), "b")], []),
        # denominator branches (fully rendered denominator texts as inputs)
        ("", Fraction(50), [(Fraction(50), "a")], ["c"]),
        ("-", Fraction(40), [(Fraction(50), "x % y")], ["d", "e"]),
        # pow_paren-wrapped denominator text (2*x/(y*y): b_str[0] == "(y*y)")
        ("-", Fraction(40), [(Fraction(1000), "2"), (Fraction(1000), "x")],
         ["(y*y)"]),
        # empty-text / boundary-strength
        ("-", Fraction(40), [(Fraction(55), "")], []),
        ("-", Fraction(40), [(Fraction(56), "z")], []),  # strength just above level -> no wrap
    ]
    disagreements = 0
    first_fail = None
    for (sign, prec, num, den) in edge:
        if lean_shadow(sign, prec, num, den) != patched_replica(sign, prec, num, den):
            disagreements += 1
            if first_fail is None:
                first_fail = (sign, str(prec), num, den)
    for _ in range(N):
        sign = rng.choice(["", "-"])
        prec = rng.choice(WEIGHTS) if rng.random() < 0.7 else Fraction(rng.randint(0, 2000), rng.choice([1, 2]))
        num = rand_factor_list(rng, min_len=1, max_len=4)  # a = a or [S.One] -> never empty
        den = rand_text_list(rng, min_len=0, max_len=4)
        if lean_shadow(sign, prec, num, den) != patched_replica(sign, prec, num, den):
            disagreements += 1
            if first_fail is None:
                first_fail = (sign, str(prec), num, den)

    status = "pass" if disagreements == 0 else "fail"
    print(json.dumps({
        "status": status,
        "instance": "sympy__sympy-22080",
        "samples": N + len(edge),
        "seed": SEED,
        "disagreements": disagreements,
        "first_fail": first_fail,
    }))
    return 0 if disagreements == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
