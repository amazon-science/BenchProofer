#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-15349 (nagini).

SHADOW: the impl regions of model.py `rotation_matrix` (3x3 block) and
`rotation_matrix_affine` (4x4 affine embedding). The shadow is not a
transcription of those regions -- it IS those regions, read out of model.py at
run time between the `# impl-start` / `# impl-end` markers and executed, so the
shadow cannot drift from the impl it shadows. The impl regions contain no
contract calls, so nothing needed stripping; the @Pure helpers appear only
inside contracts and are not part of the impl regions.

THE ONE BRIDGE APPLIED TO THAT TEXT (and the reason it is applied):

  The model's carrier is the EXPRESSIONS of this computation, presented as an
  opaque type with seven constructors and no assumed properties (model.py,
  CARRIER; meta.json axioms). Each constructor names one way the computation
  combines its inputs, and the bridge is the obvious one -- it binds each
  constructor to the SymPy operation it names:

        zero()  -> Integer(0)        add(u, v) -> u + v
        one()   -> Integer(1)        sub(u, v) -> u - v
        two()   -> Integer(2)        mul(u, v) -> u * v
        sq(u)   -> u ** 2

  Nothing else in the impl text is touched: the shadow below evaluates the
  model's own impl regions with exactly those seven bindings in scope. Under
  that binding a modelled term becomes the SymPy expression built by the same
  sequence of operations on the same operands, which is what the refinement
  claims it denotes (refinement.md A0, R-ops). model.py's clauses are written
  with `is` -- sameness of scalars, which on this carrier is congruence -- and
  the counterpart of that below is SymPy's own equality on the resulting
  expressions: structural, exact, with no tolerance and no simplification
  anywhere, and on symbolic inputs tightened to equality of expression TREES.

ORACLE: the REAL patched repo method the model models per mapping.md --
`sympy.algebras.quaternion.Quaternion.to_rotation_matrix`, both return
branches: no translation point -> the 3x3 rotation matrix (shadowed by
`rotation_matrix`), a translation point -> the 4x4 affine matrix (shadowed
by `rotation_matrix_affine`). The gate applies patch.diff to /testbed before
this script runs; PYTHONPATH=/testbed makes the patched package importable.

Type bridge (mapping.md section 2):
  - components a, b, c, d and the translation point x, y, z: the model's
    scalars are the repo's expressions; passed through unchanged (sympified, so
    that the shadow builds SymPy expressions rather than Python numbers).
  - the fifth parameter s: the COMMON SCALE ITSELF, which the real method
    realizes as s = q.norm()**-2, taken from that same call (`norm` applies
    `trigsimp` to the sum of squares, so the realized scale of a trigonometric
    quaternion is the exact scalar 1). It is an ordinary
    argument of the model -- an opaque scalar, with no property assumed of it --
    so the bridge instantiates the shadow's s at exactly the expression the real
    method computes, skipping the all-zero quaternion (where the real scale is
    undefined).
  - Matrix <-> flat row-major list: the model's entry k IS the real entry, so
    the bridge compares Result()[i*ncols + j] == Matrix[i, j] (ncols = 3 resp.
    4) with no factor in between. Matrix equality <-> element-wise list
    equality. The F2P test compares two Matrix objects for exact equality, i.e.
    every entry equal, which is exactly what is compared here.

Input domain (the model's Requires): the only precondition is the method-level
termination obligation; no argument is restricted, so every input below is
Requires-satisfying. Boundary cases cover the axis/unit quaternions, every sign
pattern, every zero-component pattern and large magnitudes; fuzz draws dense
small rationals and integers with occasional large outliers for both the
components and the translation point. SYMBOLIC quaternions are included too --
components that are indeterminates or trigonometric values of an angle -- which
is where the carrier earns its keep: there the comparison is between
expressions, and it is checked both with SymPy's equality and on the srepr
strings, i.e. as an identity of expression TREES rather than of values.

>= 1e5 Requires-satisfying inputs: boundary (both shapes) + 52000 fuzz
3x3 cases + 52000 fuzz 4x4 cases + the symbolic cases. Pinned fuzz seed: 15349.

Exit 0 iff zero disagreements; on disagreement print the input and both
outputs and exit 1. stdlib + sympy (the package under test) only.
"""
import json
import random
import re
import sys
from pathlib import Path

from sympy import (Integer, Rational, cos, simplify, sin, sqrt, srepr,
                   symbols, sympify)
from sympy.algebras.quaternion import Quaternion

SEED = 15349
N_FUZZ_3 = 52_000
N_FUZZ_4 = 52_000


# --- the bridge: one SymPy operation per constructor of the carrier -----------

def zero():
    return Integer(0)


def one():
    return Integer(1)


def two():
    return Integer(2)


def add(u, v):
    return u + v


def sub(u, v):
    return u - v


def mul(u, v):
    return u * v


def sq(u):
    return u ** 2


_BRIDGE = {"zero": zero, "one": one, "two": two,
           "add": add, "sub": sub, "mul": mul, "sq": sq}


# --- the shadow: model.py's impl regions, read out and executed ---------------

_MODEL_SRC = (Path(__file__).parent / "model.py").read_text()


def _impl_regions(src):
    """The text between each `# impl-start` / `# impl-end` marker pair, in
    source order. model.py has exactly two: the 3x3 block, then the affine."""
    regions = re.findall(r"# impl-start\n(.*?)\n\s*# impl-end", src, re.S)
    if len(regions) != 2:
        raise AssertionError(
            "expected exactly 2 impl regions in model.py, found %d" % len(regions))
    return regions


def _compile_shadow():
    """Build `rotation_matrix` / `rotation_matrix_affine` from model.py's own
    impl text, so the shadow is that text and cannot drift from it."""
    impl3, impl4 = _impl_regions(_MODEL_SRC)
    src = (
        "def rotation_matrix(a, b, c, d, s):\n"
        + impl3 + "\n\n"
        "def rotation_matrix_affine(a, b, c, d, s, x, y, z):\n"
        + impl4 + "\n"
    )
    ns = dict(_BRIDGE)
    exec(compile(src, "<model.py impl regions>", "exec"), ns)
    return src, ns["rotation_matrix"], ns["rotation_matrix_affine"]


SHADOW_SRC, rotation_matrix, rotation_matrix_affine = _compile_shadow()


# --- bridge + differential checks ---------------------------------------------

def scale_of(a, b, c, d):
    """The exact scale the real method realizes, s = q.norm()**-2, obtained from
    the SAME call the source makes. `norm` applies `trigsimp` to the sum of
    squares, so on a trigonometric quaternion the realized scale is the exact
    scalar 1 rather than an unsimplified quotient -- taking it from the real
    callee is what makes the fifth argument of the model the expression the
    behaviour is actually realised at. None for the degenerate all-zero
    quaternion, where the real scale is undefined."""
    n = Quaternion(a, b, c, d).norm()
    if n == 0:
        return None
    return n ** -2


def _sy(v):
    return sympify(v)


def check_3x3(a, b, c, d, structural=False):
    a, b, c, d = _sy(a), _sy(b), _sy(c), _sy(d)
    s = scale_of(a, b, c, d)
    if s is None:
        return None, 0
    shadow = rotation_matrix(a, b, c, d, s)
    M = Quaternion(a, b, c, d).to_rotation_matrix()
    if M.shape != (3, 3):
        return ("DISAGREEMENT (shape)\n  q=(%s,%s,%s,%s)\n  real shape=%r"
                % (a, b, c, d, (M.shape,))), 1
    for i in range(3):
        for j in range(3):
            got, want = shadow[i * 3 + j], M[i, j]
            if got != want or (structural and srepr(got) != srepr(want)):
                return ("DISAGREEMENT\n"
                        "  q=(%s,%s,%s,%s) s=%s entry=(%d,%d)\n"
                        "  shadow=%s\n  real=%s\n"
                        "  shadow_srepr=%s\n  real_srepr=%s"
                        % (a, b, c, d, s, i, j, got, want,
                           srepr(got), srepr(want))), 1
    return None, 1


def check_4x4(a, b, c, d, x, y, z, structural=False):
    a, b, c, d = _sy(a), _sy(b), _sy(c), _sy(d)
    x, y, z = _sy(x), _sy(y), _sy(z)
    s = scale_of(a, b, c, d)
    if s is None:
        return None, 0
    shadow = rotation_matrix_affine(a, b, c, d, s, x, y, z)
    M = Quaternion(a, b, c, d).to_rotation_matrix((x, y, z))
    if M.shape != (4, 4):
        return ("DISAGREEMENT (shape)\n  q=(%s,%s,%s,%s) v=(%s,%s,%s)\n"
                "  real shape=%r" % (a, b, c, d, x, y, z, (M.shape,))), 1
    for i in range(4):
        for j in range(4):
            got, want = shadow[i * 4 + j], M[i, j]
            if got != want or (structural and srepr(got) != srepr(want)):
                return ("DISAGREEMENT\n"
                        "  q=(%s,%s,%s,%s) s=%s v=(%s,%s,%s) entry=(%d,%d)\n"
                        "  shadow=%s\n  real=%s\n"
                        "  shadow_srepr=%s\n  real_srepr=%s"
                        % (a, b, c, d, s, x, y, z, i, j, got, want,
                           srepr(got), srepr(want))), 1
    return None, 1


def boundary_quaternions():
    quats = []
    # axis/unit quaternions and their negatives
    for k in range(4):
        for sign in (1, -1):
            q = [0, 0, 0, 0]
            q[k] = sign
            quats.append(tuple(q))
    # every sign pattern over (1,1,1,1) and over (2,3,5,7)
    for base in ((1, 1, 1, 1), (2, 3, 5, 7)):
        for mask in range(16):
            quats.append(tuple(v if not (mask >> k) & 1 else -v
                               for k, v in enumerate(base)))
    # every nonzero zero-component pattern (which components are nonzero)
    for mask in range(1, 16):
        quats.append(tuple((k + 2) if (mask >> k) & 1 else 0
                           for k in range(4)))
    # assorted exact shapes, non-integral scales and large magnitudes
    quats += [
        (1, 2, 3, 4), (3, 0, 4, 0), (1, -1, 1, -1), (5, 12, 0, 0),
        (10**9, -10**9, 1, 0), (2**40, 1, -1, 2**20),
        (-7, 11, -13, 17), (1, 10**6, -10**6, 1),
        (Rational(1, 2), Rational(1, 2), Rational(1, 2), Rational(1, 2)),
        (Rational(3, 5), Rational(4, 5), 0, 0),
        (Rational(-2, 7), Rational(1, 3), Rational(5, 6), Rational(-1, 4)),
    ]
    return quats


def boundary_points():
    return [(0, 0, 0), (1, 2, -3), (-1, -1, -1), (10**6, 0, -7), (0, 5, 0),
            (Rational(1, 3), Rational(-2, 5), Rational(7, 2))]


def symbolic_quaternions():
    """Quaternions whose components are EXPRESSIONS rather than numbers -- the
    case the carrier is chosen for. Here shadow and oracle are compared as
    expression trees (srepr), not merely as values."""
    sa, sb, sc, sd = symbols('sa sb sc sd')
    th = symbols('theta', real=True)
    return [
        (sa, sb, sc, sd),
        (cos(th / 2), sin(th / 2), Integer(0), Integer(0)),
        (cos(th / 2), Integer(0), Integer(0), sin(th / 2)),
        (Integer(1), sa, sa ** 3, sa ** 2),
        (sa + sb, sa - sb, sqrt(Integer(2)), Rational(1, 3)),
    ]


def rand_component(rng):
    r = rng.random()
    if r < 0.45:
        return rng.randint(-9, 9)
    if r < 0.85:
        return Rational(rng.randint(-9, 9), rng.randint(1, 9))
    if r < 0.97:
        return rng.randint(-10**4, 10**4)
    return rng.randint(-10**12, 10**12)


def rand_quat(rng):
    while True:
        q = tuple(rand_component(rng) for _ in range(4))
        if any(q):
            return q


def check_no_number_sort():
    """R-1sort, the repository half.

    The model computes with ONE sort of value, `Scalar` -- the constants are
    nullary and every other constructor takes scalars and returns a scalar, so
    no number is an argument, an operand or a result anywhere in it (model.py,
    CARRIER). Two facts about that boundary are worth measuring here rather than
    asserting in prose, because the refinement rule in mapping.md rests on them.

    FIRST: the impl regions this script executes contain no number-valued
    arithmetic at all, only constructor applications on the arguments. So the
    shadow above and the modelled operation agree about every value they
    compute, in both languages, for the trivial reason that neither computes
    with numbers.

    SECOND: the two languages do NOT agree about number-valued arithmetic in
    general, which is why the boundary matters. This language floors integer
    division and takes the sign of the divisor for the remainder, and its
    literal reals are binary approximations; the verifier's integers divide
    toward zero and its reals are exact. The values below are this language's,
    recorded so that the disagreement is a measurement in the bundle and not a
    claim about it. Nothing in the model or in either impl region depends on any
    of them -- that is the point: an expression of this kind lies outside the
    one sort the model has, so it has no counterpart under the map and a
    realisation writing one is computing outside the modelled behaviour."""
    obs = [("7 // -2", 7 // -2, -4), ("7 % -2", 7 % -2, -1),
           ("-7 // 2", -7 // 2, -4), ("-7 % 2", -7 % 2, 1),
           ("0.1 + 0.2 == 0.3", 0.1 + 0.2 == 0.3, False)]
    for text, got, want in obs:
        assert got == want and type(got) is type(want), (text, got, want)
    src = _MODEL_SRC
    for region in _impl_regions(src):
        for tok in ("//", " % ", "0.", "int(", "float("):
            assert tok not in region, (tok, "number-valued arithmetic in an impl region")
    print("  R-1sort: the impl regions compute in one sort (no //, no %%, no "
          "real literal, no int()/float()); this language reads 7 // -2 as %d "
          "and 7 %% -2 as %d and 0.1 + 0.2 != 0.3, where the verifier reads -3, "
          "1 and equality -- a disagreement the model stays clear of by having "
          "no number sort for it to arise in"
          % (7 // -2, 7 % -2))


def main():
    check_no_number_sort()
    checked = 0
    n_boundary = 0
    n_symbolic = 0

    for q in boundary_quaternions():
        err, n = check_3x3(*q)
        if err:
            print(err)
            return 1
        checked += n
        n_boundary += n
        for v in boundary_points():
            err, n = check_4x4(*(q + v))
            if err:
                print(err)
                return 1
            checked += n
            n_boundary += n

    # symbolic components: compared as expression TREES (structural=True)
    sym_pts = [(Integer(1), Integer(1), Integer(1)),
               (symbols('px'), symbols('py'), symbols('pz')),
               (Integer(0), Integer(0), Integer(0))]
    for q in symbolic_quaternions():
        err, n = check_3x3(*q, structural=True)
        if err:
            print(err)
            return 1
        checked += n
        n_symbolic += n
        for v in sym_pts:
            err, n = check_4x4(*(q + v), structural=True)
            if err:
                print(err)
                return 1
            checked += n
            n_symbolic += n

    rng = random.Random(SEED)
    for _ in range(N_FUZZ_3):
        err, n = check_3x3(*rand_quat(rng))
        if err:
            print(err)
            return 1
        checked += n
    for _ in range(N_FUZZ_4):
        q = rand_quat(rng)
        v = tuple(rand_component(rng) for _ in range(3))
        err, n = check_4x4(*(q + v))
        if err:
            print(err)
            return 1
        checked += n

    print("G-CONF OK: shadow rotation_matrix / rotation_matrix_affine == real "
          "to_rotation_matrix (3x3 and 4x4 branches) on %d inputs "
          "(%d boundary + %d symbolic + %d fuzz, seed %d); SymPy's own exact "
          "equality, and on the symbolic inputs equality of expression TREES "
          "(srepr), no tolerance and no simplification."
          % (checked, n_boundary, n_symbolic, N_FUZZ_3 + N_FUZZ_4, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (model.py's own impl regions, read "
                                "between the impl markers and executed; the "
                                "only bridge applied to that text binds each "
                                "of the seven carrier constructors to the SymPy "
                                "operation it names -- zero/one/two->Integer, add->+, "
                                "sub->-, mul->*, sq->**2); s bridged to the "
                                "exact scale q.norm()**-2 the real method "
                                "realizes, "
                                "and the entries compared directly with no "
                                "factor in between; symbolic inputs compared "
                                "as expression trees"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
