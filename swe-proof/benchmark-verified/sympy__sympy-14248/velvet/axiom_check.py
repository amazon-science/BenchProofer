#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-14248.

This bundle declares NO axioms and NO deep-model references (A-reference):
the modeled change is the sign-folding join of a matrix sum's rendered term
strings (the issue: ``a - b`` must print ``a - b``, not ``a + (-1)*b``). The
impl region computes the rendering entirely with concrete list arithmetic
(inspect each term's leading character, emit a separating ``' + '`` or
``' - '`` accordingly, splice the bodies). The only callee it consumes is the
*unchanged* `StrPrinter.parenthesize`, which produces the per-term strings;
that callee is the R-bridge INPUT shared by both sides of the differential
(mapping.md §2), not a contract the proof axiomatizes. See refinement.md (all
rows R or I).

Consequently G-AX has nothing to falsify: the `axioms` region of Solution.lean
is empty and there is no unchanged callee whose `ensures` the proof relies on.
As a non-vacuous soundness witness we additionally confirm, against the REAL
patched callee, that the deep model the spec pins (`joinSignedTerms`, here the
`shadow_join` transliteration) agrees with the patched
`StrPrinter._print_MatAdd` on boundary + fuzzed matrix sums — the same
agreement G-CONF exercises, re-checked here independently so the "no axioms"
claim is backed by execution, not assertion.

Imports only stdlib + the repo's own (patched) sympy; exit 0 iff sound.
"""
import random
import sys


def shadow_join(terms):
    """The spec's deep model `joinSignedTerms`, transliterated to str.
    `terms` is the non-empty list of rendered term-strings."""
    out = list(terms[0])
    for t in terms[1:]:
        if t.startswith('-'):
            sign = '-'
            body = t[1:]
        else:
            sign = '+'
            body = t
        out = out + [' ', sign, ' '] + list(body)
    return "".join(out)


def main():
    from sympy import MatrixSymbol, MatAdd
    from sympy.printing.str import StrPrinter
    from sympy.printing.precedence import precedence

    printer = StrPrinter()
    syms = [MatrixSymbol(n, 3, 3) for n in ("A", "B", "C", "D")]
    A, B, C, D = syms

    boundary = [
        A - A * B - B,
        A * B - (A + B),
        A - B,
        B - A,
        A * B * C - A * B - B * C,
        -A * B * C,
        A + B,
        A + B + C,
        -A - B,
        A * B + C * D - B,
    ]

    rng = random.Random(14248)

    def rand_term():
        prod = None
        for _ in range(rng.randint(1, 3)):
            s = rng.choice(syms)
            prod = s if prod is None else prod * s
        if rng.random() < 0.5:
            prod = -prod
        return prod

    checked = 0
    for _ in range(20000):
        k = rng.randint(2, 5)
        expr = rand_term()
        for _ in range(k - 1):
            expr = expr + rand_term()
        boundary.append(expr)

    for expr in boundary:
        if not isinstance(expr, MatAdd):
            continue
        terms = [printer.parenthesize(arg, precedence(expr)) for arg in expr.args]
        observed = printer._print_MatAdd(expr)        # REAL patched callee
        modeled = shadow_join(terms)                  # deep model
        assert observed == modeled, (
            "joinSignedTerms deep model unsound on %r: _print_MatAdd gave %r, "
            "deep model gives %r" % (expr, observed, modeled))
        checked += 1

    print("G-AX OK: no axioms / no A-references; joinSignedTerms deep model "
          "(== patched StrPrinter._print_MatAdd) sound on %d boundary + fuzz "
          "matrix-sum inputs." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
