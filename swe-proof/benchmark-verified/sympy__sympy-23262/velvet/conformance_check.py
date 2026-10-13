#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-23262 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`renderSequence`: the delimiter selection by kind, the
              comma-space join `joinComma`, and the open/body/close concat)
              transliterated to Python over the real repo types (`list`/`tuple`
              of rendered element texts), via the mapping.md bijection
              (`List Char` ↔ Python `str`, `isList` ↔ `isinstance(arg, list)`).
              There is NO A-tagged callee in the computed result — the element
              renderings are produced by the SAME unchanged recursive descent on
              both sides (an R identity bridge: leaves go through the real
              `doprint`), so this shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `sympy.utilities.lambdify._recursive_to_string` applied at
              base_commit (the real correctness oracle, G-RESOLVE).

The two recursions share the SAME leaf renderer (`doprint`) and the SAME
recursion structure; they can therefore differ ONLY in the join-and-wrap step
the impl models. They must agree on every input. Exit 0 iff zero disagreements;
any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + sympy only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 23262
N_FUZZ = 100_000

from sympy import symbols, Integer, Rational, sin, cos, Symbol
from sympy.core.basic import Basic
from sympy.matrices.common import MatrixOperations
from sympy.utilities.iterables import iterable
from sympy.utilities.lambdify import _recursive_to_string
from sympy.printing.pycode import PythonCodePrinter

doprint = PythonCodePrinter().doprint


# --- the R/I shadow: Solution.lean renderSequence, transliterated ------------

def join_comma(texts):
    """joinComma: comma-space between adjacent element texts (R/I)."""
    return ", ".join(texts)


def render_seq(is_list, elems):
    """renderSeq: wrap the joined body in the delimiter pair for the kind.
    Tuple closer carries a comma before ')'. (R/I)"""
    open_d = "[" if is_list else "("
    close_d = "]" if is_list else ",)"
    return open_d + join_comma(elems) + close_d


def shadow(arg):
    """The R/I shadow of _recursive_to_string: the UNCHANGED recursive-descent
    structure (leaves via the real `doprint`, str passthrough), with the
    iterable branch computed by renderSeq/joinComma (the modeled ops). The leaf
    behaviour is the R identity bridge — shared with the oracle by construction,
    so divergence can only come from the modeled join-and-wrap."""
    if isinstance(arg, (Basic, MatrixOperations)):
        return doprint(arg)
    elif iterable(arg):
        if isinstance(arg, list):
            is_list = True
        elif isinstance(arg, tuple):
            is_list = False
        else:
            raise NotImplementedError("unhandled type: %s, %s" % (type(arg), arg))
        return render_seq(is_list, [shadow(e) for e in arg])
    elif isinstance(arg, str):
        return arg
    else:
        return doprint(arg)


def oracle(arg):
    """patch.diff's behaviour: the patched real _recursive_to_string."""
    return _recursive_to_string(doprint, arg)


# --- fuzzing -----------------------------------------------------------------

def fuzz_inputs(n, rng, leaves):
    # boundary cases first (plan §4.1 step 4): the issue MWE and variants
    yield (Integer(1),)                       # one-element tuple -> '(1,)'
    yield (Integer(1), Integer(2))            # -> '(1, 2,)'
    yield (Integer(1), Integer(2), Integer(3))
    yield [Integer(1)]
    yield [Integer(1), Integer(2)]
    yield ()
    yield []
    yield ((Integer(1),),)
    yield ([Integer(1)], (Integer(2),))
    yield (Integer(1), (Integer(2), Integer(3)))
    yield [[Integer(1)], [Integer(2), Integer(3)]]
    yield (sin(symbols('x')), cos(symbols('x')))
    yield ("a", "b")
    yield ("solo",)

    def rand_struct(depth):
        if depth <= 0 or rng.random() < 0.45:
            return rng.choice(leaves)
        k = rng.randint(0, 4)
        children = [rand_struct(depth - 1) for _ in range(k)]
        if rng.random() < 0.5:
            return list(children)
        return tuple(children)

    for _ in range(n):
        arg = rand_struct(rng.randint(1, 4))
        if not isinstance(arg, (list, tuple)):
            arg = (arg,)
        yield arg


def main():
    rng = random.Random(SEED)
    x, y, z = symbols('x y z')
    leaves = [Integer(1), Integer(2), Integer(0), Integer(-3), Rational(1, 2),
              x, y, z, sin(x), cos(x) + 1, x * y, Symbol('w'), "abc", "", "x, y"]
    disagreements = []
    count = 0
    for arg in fuzz_inputs(N_FUZZ, rng, leaves):
        count += 1
        sh = shadow(arg)
        orc = oracle(arg)
        if sh != orc:
            disagreements.append((arg, sh, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for arg, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (arg, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of renderSequence agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
