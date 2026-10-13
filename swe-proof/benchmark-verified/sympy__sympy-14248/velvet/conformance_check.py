#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-14248 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`joinSignedMatrixTerms` / the pure `joinSignedTerms` fold)
              transliterated to Python, fed the *real* repo term-strings via
              the mapping.md bijection (`List Char` ↔ `str`, a list element ↔
              one rendered term). There are NO A-tagged callees in the impl
              region: the changed string-join operation is modeled DEEPLY, so
              the whole shadow is pure R/I. The unchanged callee `parenthesize`
              that produces the input term-strings is the R-bridge INPUT shared
              by both sides — it is not under test (mapping.md §2).
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `sympy.printing.str.StrPrinter._print_MatAdd` applied at
              base_commit (the real correctness oracle, G-RESOLVE).

For each fuzzed `MatAdd` expression we feed BOTH sides the identical list of
rendered term-strings (obtained from the real, unchanged `parenthesize`), then
compare the shadow's join against the real `_print_MatAdd`. They must agree on
every input. Exit 0 iff zero disagreements; any disagreement is a mechanical
R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + the repo's
own sympy only. The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import itertools
import random
import sys

SEED = 14248
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean joinSignedTerms, transliterated -----------
def shadow_join(terms):
    """joinSignedTerms (the pure region), transliterated to str over the real
    repo carrier. `terms` is the non-empty list of rendered term-strings (one
    `str` per `List Char` element). Mirrors, op for op:
        joinSignedTerms (t :: ts) = t ++ joinTail ts
        joinTail (t :: ts)        = tailPiece t ++ joinTail ts
        tailPiece t               = ' ' :: termSign t :: ' ' :: termBody t
        termSign t = '-' if t.head? = some '-' else '+'
        termBody t = t.drop 1     if t.head? = some '-' else t
    The leading term is emitted verbatim; each later term contributes
    " <sign> <body>", folding a leading '-' marker into a subtraction."""
    out = list(terms[0])              # leading term verbatim
    for t in terms[1:]:
        if t.startswith('-'):         # termSign / termBody: fold a leading '-'
            sign = '-'
            body = t[1:]
        else:
            sign = '+'
            body = t
        out = out + [' ', sign, ' '] + list(body)
    return "".join(out)


def fuzz_exprs(n, rng):
    """Yield MatAdd expressions over square MatrixSymbols. Square (same dim)
    so every product/sum of the symbols is shape-valid. We build sums of
    signed matrix products via Python arithmetic and keep only genuine MatAdds.
    Boundary cases (the issue + F2P examples) come first."""
    from sympy import MatrixSymbol, MatAdd, S

    syms = [MatrixSymbol(name, 3, 3) for name in ("A", "B", "C", "D")]
    A, B, C, D = syms

    # boundary: the issue example and the F2P str.py cases
    boundary = [
        A - A * B - B,
        A * B - (A + B),
        A - B,
        A * B * C - A * B - B * C,
        -A * B * C,
        A + B,
        A + B + C,
        -A - B,
        B - A,
        A * B + C * D - B,
    ]
    for e in boundary:
        yield e

    def rand_term():
        k = rng.randint(1, 3)
        prod = None
        for _ in range(k):
            s = rng.choice(syms)
            prod = s if prod is None else prod * s
        if rng.random() < 0.5:
            prod = -prod
        return prod

    produced = 0
    while produced < n:
        k = rng.randint(2, 5)
        terms = [rand_term() for _ in range(k)]
        expr = terms[0]
        for t in terms[1:]:
            expr = expr + t
        produced += 1
        yield expr


def main():
    from sympy import MatAdd
    from sympy.printing.str import StrPrinter
    from sympy.printing.precedence import precedence

    rng = random.Random(SEED)
    printer = StrPrinter()
    disagreements = []
    count = 0
    skipped = 0

    # extra layer: the exact F2P literals from sympy/printing/tests/test_str.py
    from sympy import MatrixSymbol
    A = MatrixSymbol("A", 3, 3)
    B = MatrixSymbol("B", 3, 3)
    f2p = [
        (A - A * B - B, "-B - A*B + A"),
        (A * B - (A + B), "-(A + B) + A*B"),
    ]
    for expr, want in f2p:
        got = printer.doprint(expr)
        if got != want:
            disagreements.append((repr(expr), got, want + " (F2P literal)"))

    for expr in fuzz_exprs(N_FUZZ, rng):
        if not isinstance(expr, MatAdd):
            skipped += 1
            continue
        count += 1
        terms = [printer.parenthesize(arg, precedence(expr)) for arg in expr.args]
        if not terms:
            continue
        shadow = shadow_join(terms)            # R/I shadow of the impl region
        oracle = printer._print_MatAdd(expr)   # patch.diff behaviour
        if shadow != oracle:
            disagreements.append((repr(expr), shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d MatAdd inputs:"
              % (len(disagreements), count))
        for e, sh, orc in disagreements:
            print("  expr=%s shadow=%r oracle=%r" % (e, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of joinSignedMatrixTerms agrees with patch.diff "
          "behaviour on %d MatAdd inputs (seed=%d; %d non-MatAdd skipped), "
          "0 disagreements." % (count, SEED, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
