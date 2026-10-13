#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-14711 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outcomes:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`vectorAdd`)
              transliterated to Python, with the A-reference callees left as the
              real repo callees (`_check_vector` and the `Vector(args+args)`
              construction). Concretely:
                  if other == 0:            return self            # I-op (step 3)
                  v   = _check_vector(other)                       # A-ref (step 4)
                  return Vector(self.args + v.args)                # A-ref (step 5)
              This is built independently here — it does NOT call Vector.__add__.
  * ORACLE  — `patch.diff`'s behaviour: the patched `Vector.__add__` constructed
              at base_commit (the real correctness oracle; G-RESOLVE applies the
              gold patch before this runs).

Observable of an add, per the mapping.md §2 bijection:
  - whether it returns a vector or raises `TypeError`
    (↔ `Except.ok _` vs `Except.error .notAVector`);
  - on success, the resulting vector compared by SymPy value equality `==`
    (↔ the `VecVal` payload; internal `args` are never inspected).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. The fuzz seed is pinned
(mapping.md §4) for a deterministic verdict.

Runs in-container, stdlib + sympy only.
"""
import random
import sys

SEED = 14711
N_FUZZ = 100_000


def build_inputs():
    from sympy.physics.vector import ReferenceFrame
    from sympy import symbols, Integer, Rational
    N = ReferenceFrame('N')
    A = N.orientnew('A', 'Axis', [symbols('q1'), N.x])
    x, y, z = symbols('x y z')

    # Genuine, non-zero vectors (the `vec` operand class + the `self` pool).
    vecs = [
        N.x, N.y, N.z, A.x, A.y, A.z,
        x * N.x, x * N.x + y * N.y, x * N.x + y * N.y + z * N.z,
        x ** 2 * N.x + y ** 2 * N.y, 2 * N.x + 3 * N.y, x * A.x + y * A.z,
    ]
    # The additive identity (the `zero` operand class).
    zeros = [0]
    # Foreign non-vector, non-zero values (the `foreign` operand class).
    foreigns = [1, 2, -5, 3.5, "x", x, Integer(7), Rational(3, 2), (1, 2), [1]]
    return vecs, zeros, foreigns


def shadow(self_v, other):
    """R/I shadow of vectorAdd: the guard (I) in front of the two A-reference
    callees, reconstructed independently from the patched __add__."""
    from sympy.physics.vector import Vector
    from sympy.physics.vector.vector import _check_vector
    if other == 0:                       # step 3 (I): isZeroOperand guard
        return ("ok", self_v)
    try:
        v = _check_vector(other)         # step 4 (A-ref): asVector
    except TypeError:
        return ("err",)
    return ("ok", Vector(self_v.args + v.args))   # step 5 (A-ref): combine


def oracle(self_v, other):
    """patch.diff behaviour: the patched Vector.__add__ applied directly."""
    try:
        return ("ok", self_v.__add__(other))
    except TypeError:
        return ("err",)


def same(a, b):
    if a[0] != b[0]:
        return False
    if a[0] == "err":
        return True
    # success: compare resulting vectors by SymPy value equality.
    try:
        return bool(a[1] == b[1])
    except Exception:
        return False


def main():
    try:
        import sympy.physics.vector  # noqa: F401
    except Exception as e:  # pragma: no cover
        print("G-CONF FAIL: cannot import sympy:", type(e).__name__, e)
        return 1

    vecs, zeros, foreigns = build_inputs()
    others = [("zero", o) for o in zeros] + \
             [("vec", o) for o in vecs] + \
             [("foreign", o) for o in foreigns]

    disagreements = []
    n = 0

    # Full cross product: every self × every operand class.
    for s in vecs:
        for _cls, o in others:
            sh = shadow(s, o)
            orc = oracle(s, o)
            if not same(sh, orc):
                disagreements.append((repr(s), repr(o), sh[0], orc[0]))
            n += 1

    # Fuzz to exceed the §4.1 floor deterministically.
    rng = random.Random(SEED)
    while n < N_FUZZ:
        s = rng.choice(vecs)
        _cls, o = rng.choice(others)
        sh = shadow(s, o)
        orc = oracle(s, o)
        if not same(sh, orc):
            disagreements.append((repr(s), repr(o), sh[0], orc[0]))
        n += 1

    if disagreements:
        print("G-CONF FAIL:", len(disagreements), "disagreement(s) over", n,
              "inputs (seed=%d). First few:" % SEED)
        for d in disagreements[:10]:
            print("   ", d)
        return 1

    print("G-CONF OK: R/I shadow of vectorAdd agrees with patch.diff behaviour "
          "on %d adds (seed=%d), 0 disagreements." % (n, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
