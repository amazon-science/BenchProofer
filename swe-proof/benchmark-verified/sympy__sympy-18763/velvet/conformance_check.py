#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-18763 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the I-tagged ops of Solution.lean's impl region (`renderSubsNotation`
              / `subsNotationLatex`) transliterated to Python over the real repo
              type (`str`), via the mapping.md bijection (`List Char` ↔ `str`,
              `++` ↔ `+`). The two free inputs `body`/`subsList` are the outputs
              of the UNCHANGED upstream renderers, so we recompute them with the
              real `LatexPrinter` (exactly the unchanged preamble of `_print_Subs`)
              — the abstracted-as-input legs run the real callee, not a model.
  * ORACLE  — `patch.diff`'s behaviour: the patched `LatexPrinter._print_Subs`
              applied at base_commit (the real correctness oracle, G-RESOLVE).
              The harness applies patch.diff before this runs.

They must agree on every `Subs` input. Exit 0 iff zero disagreements; any
disagreement is a mechanical I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + sympy only
(no hypothesis needed). The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import random
import sys

SEED = 18763
N_FUZZ = 100_000


def build_shadow_and_oracle():
    """Return (shadow_fn, oracle_fn, gen_fn) closed over a sympy environment."""
    from sympy import Subs, symbols, sin, cos, exp, log, sqrt, Integer, Rational
    from sympy.printing.latex import LatexPrinter

    syms = symbols('x y z a b t')

    def oracle(subs):
        """patch.diff's behaviour: the real patched _print_Subs."""
        p = LatexPrinter()
        return p._print_Subs(subs)

    def shadow(subs):
        """subsNotationLatex(body, subsList) transliterated to str (I ops),
        with body/subsList recomputed by the UNCHANGED preamble of _print_Subs
        using the real LatexPrinter (the abstracted-as-input legs)."""
        p = LatexPrinter()
        # --- unchanged preamble of _print_Subs (latex.py:700-705) ---
        expr, old, new = subs.args
        latex_expr = p._print(expr)
        latex_old = (p._print(e) for e in old)
        latex_new = (p._print(e) for e in new)
        latex_subs = r'\\ '.join(
            e[0] + '=' + e[1] for e in zip(latex_old, latex_new))
        # --- the I-tagged assembly (Solution.lean subsNotationLatex) ---
        body = latex_expr
        subs_list = latex_subs
        return (r'\left. \left(' + body + r'\right) \right|_{\substack{ '
                + subs_list + r' }}')

    def gen(n, rng):
        x, y, z, a, b, t = syms
        atoms = [x, y, z, a, b, t, Integer(1), Integer(2), Integer(-1),
                 Rational(1, 2), Integer(0)]
        unary = [lambda e: -e, lambda e: e + 1, lambda e: 2 * e,
                 sin, cos, exp, lambda e: log(e), lambda e: sqrt(abs(e) + 1)]
        binary = [lambda u, v: u + v, lambda u, v: u - v,
                  lambda u, v: u * v, lambda u, v: u + 2 * v]

        def rand_expr(depth):
            if depth <= 0 or rng.random() < 0.35:
                return rng.choice(atoms)
            if rng.random() < 0.5:
                return rng.choice(unary)(rand_expr(depth - 1))
            return rng.choice(binary)(rand_expr(depth - 1), rand_expr(depth - 1))

        # boundary cases first (plan §4.1 step 4): the issue's own examples.
        # `_print_Subs` only ever receives a Subs node; the issue's `3*Subs(...)`
        # is a Mul whose printer recurses into _print_Subs with this exact Subs.
        yield Subs(x * y, (x, y), (1, 2))
        yield Subs(-x + y, (x,), (1,))
        yield Subs(x, (x,), (0,))
        yield Subs(sin(x) + cos(y), (x, y), (0, 1))
        yield Subs(x + y + z, (x, y, z), (a, b, t))
        for _ in range(n):
            k = rng.randint(1, 3)
            var_syms = rng.sample([x, y, z, a, b, t], k)
            pts = [rng.choice(atoms) for _ in range(k)]
            e = rand_expr(rng.randint(0, 3))
            yield Subs(e, tuple(var_syms), tuple(pts))

    return shadow, oracle, gen


def main():
    rng = random.Random(SEED)
    shadow, oracle, gen = build_shadow_and_oracle()
    disagreements = []
    count = 0
    for subs in gen(N_FUZZ, rng):
        count += 1
        try:
            sh = shadow(subs)
            orc = oracle(subs)
        except Exception as ex:  # pragma: no cover - defensive
            disagreements.append((repr(subs), "EXC:%r" % ex, ""))
            if len(disagreements) >= 5:
                break
            continue
        if sh != orc:
            disagreements.append((repr(subs), sh, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d I-disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  subs=%s shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of renderSubsNotation agrees with patch.diff "
          "behaviour on %d Subs inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
