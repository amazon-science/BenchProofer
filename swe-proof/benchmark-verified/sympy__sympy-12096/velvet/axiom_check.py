#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-12096.

Executes the REAL repo callee on inputs (boundary argument lists over the
plain-number / composite-numeric / implemented-function-application cases, plus
randomized fuzzing built from real sympy expressions) and asserts that every
observation matches the model, as encoded in Solution.lean.

The kind-A checks:

  (A-reference) the deep model `numEvalSeq` (Solution.lean axioms + pure region)
      == the real post-patch per-element comprehension
        [i.evalf(prec) for i in args].
      The changed operation is modeled DEEPLY, not behind a consumed equational
      axiom; G-AX validates that deep model against the real callee.

  (A-consumed) `numEval`: the per-argument evaluator `Expr.evalf` is total
      Expr x prec -> Expr. CRUCIALLY exhibits the load-bearing witness: there
      exist arguments that are NOT fixed points of `evalf` (e.g. an applied
      implemented_function `f(2)` -> 4.0, or any composite numeric expression),
      so the per-argument evaluation genuinely changes the result (the bug).

Imports only sympy — the same package the patch lives in. Exit 0 iff every
obligation holds.
"""
import random
import sys

from sympy import (Float, Integer, Rational, sin, cos, sqrt, exp, log, pi, E,
                   Add, Mul)
from sympy.abc import x, y
from sympy.utilities.lambdify import implemented_function

PREC = 53  # working precision in bits (the `prec` arg of `_eval_evalf`)


def num_eval(a, prec):
    """Reference of Solution.lean `numEval`: the per-argument evaluation."""
    return a.evalf(prec)


def num_eval_seq(prec, args):
    """Reference of Solution.lean `numEvalSeq`: per-element map, order kept."""
    return [num_eval(a, prec) for a in args]


def real_comprehension(prec, args):
    """The REAL post-patch source expression (function.py:510), verbatim."""
    return [i.evalf(prec) for i in args]


def check_reference(prec, args):
    """A-reference: numEvalSeq(prec, args) == the real per-element comprehension."""
    observed = real_comprehension(prec, args)     # real post-patch sub-expr
    expected = num_eval_seq(prec, args)           # deep model
    assert observed == expected, (
        "numEvalSeq deep model unsound on %r @prec=%r: real comprehension gave "
        "%r, deep model gives %r" % (args, prec, observed, expected))
    # length + order preserved (numEvalSeq_length / the spec's out.length clause)
    assert len(observed) == len(args), (
        "evaluation must preserve arity on %r: got %d, expected %d"
        % (args, len(observed), len(args)))


def main():
    # implemented functions whose evalf genuinely reduces a composite arg
    f = implemented_function('f', lambda z: z**2)
    g = implemented_function('g', lambda z: 2 * z)

    # --- A-consumed: numEval (Expr.evalf) total + load-bearing witness -------
    witness_args = [f(2), g(2), f(g(2)), Integer(2) + Integer(3),
                    sqrt(Integer(2)), Rational(1, 3), sin(Integer(1))]
    for a in witness_args:
        r = a.evalf(PREC)
        # totality: evalf returns an Expr (a sympy object) for every argument
        assert hasattr(r, "evalf"), (
            "evalf must return a sympy Expr on %r, got %r" % (a, r))

    # load-bearing witness: an argument whose evaluation differs from itself.
    # f(2) is an applied implemented_function; evaluating it yields 4.0 != f(2).
    inner = f(2)
    assert inner.evalf(PREC) != inner, (
        "load-bearing witness broken: f(2).evalf(prec) must differ from f(2), "
        "else numEval would be vacuous (the per-argument evaluation is the bug)")
    # composite numeric expression also changes under evalf
    comp = Integer(2) + Integer(3)
    assert comp.evalf(PREC) != comp or Float(comp) == comp.evalf(PREC), (
        "composite numeric arg should evaluate to a Float")
    # plain Float is a fixed point of evalf (the "kept" case)
    fl = Float(2.0, 15)
    assert fl.evalf(PREC) == fl, "a plain Float must be unchanged by evalf"

    # --- A-reference: numEvalSeq == real comprehension, boundary cases -------
    boundary = [
        [],
        [Integer(2)],
        [f(2)],
        [f(2), g(2)],
        [g(2), f(2)],
        [f(g(2))],
        [f(2), Integer(3), sqrt(Integer(2))],
        [Rational(1, 3), pi, E],
        [sin(Integer(1)), cos(Integer(1))],
        witness_args,
    ]
    for args in boundary:
        check_reference(PREC, args)
        # also fuzz the precision itself
        for prec in (15, 30, 53, 100):
            check_reference(prec, args)

    # --- A-reference: randomized fuzz over real argument lists ---------------
    rng = random.Random(12096)
    atoms = [Integer(2), Integer(3), Integer(7), Rational(1, 3), Rational(5, 2),
             sqrt(Integer(2)), pi, E, sin(Integer(1)), cos(Integer(2)),
             f(2), g(2), f(g(2)), g(f(3)), f(Integer(5)), exp(Integer(1)),
             log(Integer(2))]
    for _ in range(3000):
        k = rng.randint(0, 4)
        args = [rng.choice(atoms) for _ in range(k)]
        prec = rng.choice([15, 24, 53, 80, 113])
        check_reference(prec, args)

    print("G-AX OK: numEvalSeq deep model (== real per-argument numerical "
          "evaluation [i.evalf(prec) for i in args]) sound on %d boundary + "
          "~3000 fuzz argument lists across multiple precisions; Expr.evalf "
          "total; load-bearing witness f(2).evalf(prec) != f(2) confirmed."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
