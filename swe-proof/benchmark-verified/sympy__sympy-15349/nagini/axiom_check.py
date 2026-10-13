#!/usr/bin/env python3
"""G-AX executable reference check for sympy__sympy-15349.

The seven @ContractOnly functions of this bundle assert NOTHING: `zero`, `one`,
`two`, `add`, `sub`, `mul` and `sq` are the constructors of the carrier -- the
three constants nullary, so that no number is ever an argument or a result
anywhere in the model -- they carry no
postcondition, and no algebraic law about them is available to a proof (model.py,
CARRIER; meta.json axioms). There is therefore no axiom obligation of the usual
kind to fuzz -- an axiom with no content cannot be unsound. What the refinement
relies on instead are REFERENCE facts about the real code and about the
constructors' counterparts in it (refinement.md tags R), and this script
validates them in-container against the REAL SymPy callee:

  (R-ops) each constructor names one operation of the repository, under the
      bridge zero() -> Integer(0), one() -> Integer(1), two() -> Integer(2),
      add(u,v) -> u + v, sub(u,v) -> u - v, mul(u,v) -> u * v, sq(u) -> u ** 2 --
      the three literals being exactly the three the source writes. Checked below
      on symbolic operands, by
      building each counterpart and exhibiting the expression it produces.

  (R-layout) the `Matrix(...)` constructor is value-preserving and row-major:
      `Quaternion(a,b,c,d).to_rotation_matrix()[i, j]` equals the supplied
      entry m_{ij}; i.e. `Matrix[i, j] == Result()[i*ncols + j]` in the model.

  (R-formula) every entry produced by the REAL `to_rotation_matrix` is the
      expression the corresponding model term denotes under the bridge
      (diag0..diag2, off_bc_minus/plus, off_bd_plus/minus, off_cd_minus/plus,
      translation) at the scale the real method realizes, s = q.norm()**-2. On
      symbolic components this is checked as an identity of expression TREES
      (srepr), which is the strongest form of the claim: the real method does
      not merely compute something equal to the modelled term, it builds that
      term. In particular the third-column second-row entry is the CORRECTED
      `2*s*(c*d - b*a)` (off_cd_minus), NOT `2*s*(c*d + b*a)` -- and the issue's
      witness Quaternion(cos(x/2), sin(x/2), 0, 0) yields the textbook
      X-rotation matrix [[1,0,0],[0,cos x,-sin x],[0,sin x,cos x]].

  (R-cong) the only identification the carrier proves is congruence -- the same
      constructor applied to the same operands -- which is why model.py's clauses
      are written with `is`, sameness of scalars, rather than with a separate
      equality predicate. Congruence holds of the repository's expressions:
      building the same term twice out of the same parts yields the same object.
      Checked below, symbolically, so that every identification a proof over this
      carrier can use is known to be a real one.

  (R-finer) the converse direction is exhibited rather than assumed: the
      repository's equality identifies MORE expressions than the carrier does
      (it flattens and orders sums and products and collapses a repeated factor
      to a power), so the carrier distinguishes some expressions the repository
      calls equal, and the model is correspondingly STRICTER than the source --
      never laxer. And the fact that forces the carrier to be expressions at all
      is exhibited too: two differently-built expressions that agree at every
      number are NOT equal in the repository, so a carrier of numbers would
      settle an equation the repository leaves standing.

Imports nothing beyond `sympy` (the very package the change edits, present in the
instance image) and the stdlib. Exit 0 iff every observation matches the model.
"""
import random
import sys

from sympy import (Integer, Matrix, Rational, cos, expand, simplify, sin,
                   sqrt, srepr, symbols, sympify, trigsimp)
from sympy.algebras.quaternion import Quaternion


# --- the bridge: one repository operation per constructor of the carrier ------

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


# --- model.py reference terms (kept in lock-step with model.py's pure region) --

def two_s(s):                    return mul(two(), s)
def diag0(b, c, d, s):           return sub(one(), mul(two_s(s), add(sq(c), sq(d))))
def diag1(b, c, d, s):           return sub(one(), mul(two_s(s), add(sq(b), sq(d))))
def diag2(b, c, d, s):           return sub(one(), mul(two_s(s), add(sq(b), sq(c))))
def off_bc_minus(a, b, c, d, s): return mul(two_s(s), sub(mul(b, c), mul(d, a)))
def off_bc_plus(a, b, c, d, s):  return mul(two_s(s), add(mul(b, c), mul(d, a)))
def off_bd_plus(a, b, c, d, s):  return mul(two_s(s), add(mul(b, d), mul(c, a)))
def off_bd_minus(a, b, c, d, s): return mul(two_s(s), sub(mul(b, d), mul(c, a)))
def off_cd_minus(a, b, c, d, s): return mul(two_s(s), sub(mul(c, d), mul(b, a)))  # CORRECTED
def off_cd_plus(a, b, c, d, s):  return mul(two_s(s), add(mul(c, d), mul(b, a)))


def translation(p, x, y, z, r0, r1, r2):
    return sub(sub(sub(p, mul(x, r0)), mul(y, r1)), mul(z, r2))


def model_entries_3x3(a, b, c, d, s):
    """The nine model terms: the matrix entries themselves, row-major."""
    return [
        diag0(b, c, d, s),          off_bc_minus(a, b, c, d, s),
        off_bd_plus(a, b, c, d, s),
        off_bc_plus(a, b, c, d, s), diag1(b, c, d, s),
        off_cd_minus(a, b, c, d, s),
        off_bd_minus(a, b, c, d, s), off_cd_plus(a, b, c, d, s),
        diag2(b, c, d, s),
    ]


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


def check_quaternion(a, b, c, d, structural=False):
    """Run the REAL to_rotation_matrix and assert it matches the model under
    R-layout (row-major) and R-formula (each entry IS the modelled term)."""
    a, b, c, d = (sympify(v) for v in (a, b, c, d))
    s = scale_of(a, b, c, d)
    if s is None:
        return  # s = norm**-2 undefined; skip the degenerate quaternion
    q = Quaternion(a, b, c, d)

    M = q.to_rotation_matrix()                 # REAL callee, 3x3
    assert M.shape == (3, 3)

    expected = model_entries_3x3(a, b, c, d, s)
    # R-layout: Matrix[i, j] == Result()[i*3 + j]; R-formula: the real entry is
    # the model's term, with no factor in between.
    for i in range(3):
        for j in range(3):
            obs = M[i, j]
            exp = expected[i * 3 + j]
            assert obs == exp, (
                "entry mismatch at (%d,%d) for q=(%s,%s,%s,%s): real=%s model=%s"
                % (i, j, a, b, c, d, obs, exp))
            if structural:
                assert srepr(obs) == srepr(exp), (
                    "entry (%d,%d) equal but not the same expression tree:\n"
                    "  real =%s\n  model=%s" % (i, j, srepr(obs), srepr(exp)))

    # The discriminating entry must be the CORRECTED sign and differ from the
    # `+ b*a` form whenever s*b*a != 0.
    assert M[1, 2] == off_cd_minus(a, b, c, d, s)
    if b * a != 0:
        assert M[1, 2] != off_cd_plus(a, b, c, d, s), (
            "the two (cd) off-diagonal forms are indistinguishable for "
            "q=(%s,%s,%s,%s) with b*a != 0" % (a, b, c, d))

    # 4x4 affine embedding: same upper-left block, row-major value-preserving.
    v = (Rational(1), Rational(2), Rational(-3))
    M4 = q.to_rotation_matrix(v)
    assert M4.shape == (4, 4)
    for i in range(3):
        for j in range(3):
            assert M4[i, j] == expected[i * 3 + j]
    # translation column m_i3 = p_i - x*m_i0 - y*m_i1 - z*m_i2 -- exactly the
    # model's translation term, built from the same block entries.
    x, y, z = v
    p = (x, y, z)
    for i in range(3):
        col = translation(p[i], x, y, z, expected[i * 3 + 0],
                          expected[i * 3 + 1], expected[i * 3 + 2])
        assert M4[i, 3] == col, (
            "translation mismatch at row %d for q=(%s,%s,%s,%s)"
            % (i, a, b, c, d))
        if structural:
            assert srepr(M4[i, 3]) == srepr(col), (
                "translation row %d equal but not the same expression tree:\n"
                "  real =%s\n  model=%s" % (i, srepr(M4[i, 3]), srepr(col)))
    assert (M4[3, 0], M4[3, 1], M4[3, 2], M4[3, 3]) == (0, 0, 0, 1)


def check_symbolic_components():
    """R-layout / R-formula at FULLY SYMBOLIC quaternions, as an identity of
    expression TREES.

    The strongest form of the two reference facts: no concrete component, so the
    observation is the entry expressions themselves rather than a sample of
    their values, and srepr equality says the real method builds the very term
    the model pins rather than something that happens to be equal to it.
    """
    sa, sb, sc, sd = symbols('sa sb sc sd')
    th = symbols('theta', real=True)
    cases = [
        (sa, sb, sc, sd),
        (cos(th / 2), sin(th / 2), Integer(0), Integer(0)),
        (Integer(1), sa, sa ** 3, sa ** 2),
        (sa + sb, sa - sb, sqrt(Integer(2)), Rational(1, 3)),
    ]
    for q in cases:
        check_quaternion(*q, structural=True)
    # the corrected sign, symbolically, and its difference from the other form
    s = scale_of(sa, sb, sc, sd)
    M = Quaternion(sa, sb, sc, sd).to_rotation_matrix()
    assert M[1, 2] == off_cd_minus(sa, sb, sc, sd, s)
    assert M[1, 2] != off_cd_plus(sa, sb, sc, sd, s)
    print("  R-formula (symbolic, structural): M[1,2] is the term %s"
          % srepr(M[1, 2])[:120])


def check_constructor_bridge():
    """R-ops: exhibit each constructor's counterpart on symbolic operands."""
    u, v = symbols('u v')
    obs = [("two()", two()), ("add(u, v)", add(u, v)), ("sub(u, v)", sub(u, v)),
           ("mul(u, v)", mul(u, v)), ("sq(u)", sq(u))]
    for name, e in obs:
        print("  R-ops: %-10s -> %s" % (name, srepr(e)))
    assert two() == Integer(2) and zero() == Integer(0) and one() == Integer(1)
    assert add(u, v) - (u + v) == 0
    assert sub(u, v) - (u - v) == 0
    assert mul(u, v) - u * v == 0
    assert sq(u) - u ** 2 == 0


def check_congruence_and_strictness():
    """R-cong and R-finer.

    R-cong: every identification this carrier proves is congruence, and congruence
    is real -- combining the same parts the same way twice yields the same object.

    R-finer: the repository's equality identifies MORE than the carrier does, so
    the carrier can only distinguish where the repository does not: the model is
    stricter than the source, never laxer.

    And the fact that forces the carrier to be expressions rather than numbers:
    two differently-built expressions that agree at every number are NOT equal
    here, so on a carrier of numbers a realisation could settle an equation the
    repository leaves standing and take a decision on it.
    """
    a, b, c, d, s = symbols('a b c d s')

    # R-cong: same constructors, same operands, twice -> the same expression.
    t1 = off_cd_minus(a, b, c, d, s)
    t2 = off_cd_minus(a, b, c, d, s)
    assert t1 == t2 and srepr(t1) == srepr(t2)
    t3 = mul(two_s(s), sub(mul(c, d), mul(b, a)))     # spelled out inline
    assert srepr(t3) == srepr(t1), (
        "congruence failed: the same term built twice differs\n  %s\n  %s"
        % (srepr(t3), srepr(t1)))

    # R-finer: places where the repository is COARSER than the carrier. Each of
    # these pairs is two DISTINCT terms of the carrier which the repository
    # identifies; the carrier therefore only ever refuses what the repository
    # accepts, and the model is the stricter of the two.
    coarser = [
        ("mul(u,u) / sq(u)", mul(c, c), sq(c)),
        ("mul(b,c) / mul(c,b)", mul(b, c), mul(c, b)),
        ("add(u,v) / add(v,u)", add(b, c), add(c, b)),
        ("mul(mul(2,s),X) / mul(2,mul(s,X))",
         mul(mul(two(), s), mul(c, d)), mul(two(), mul(s, mul(c, d)))),
        # a DEGREE-1 rearrangement: Add collects like terms, so the repository
        # identifies these two even though they are built differently. Recorded
        # here rather than among the distinct pairs below, which is where a
        # numeric reading would put it -- the repository's coarseness is a fact
        # to be measured, not guessed.
        ("mul(2, add(a,d)) / add(add(add(a,d),a),d)",
         mul(two(), add(a, d)), add(add(add(a, d), a), d)),
    ]
    for name, u, v in coarser:
        assert u == v, "expected the repository to identify %s" % name
        print("  R-finer: repository identifies %-34s (%s)" % (name, u))

    # The carrier-forcing fact: mathematically equal, NOT equal here.
    pairs = [
        ("(a+d)*(a+d) vs a**2 + 2*a*d + d**2",
         mul(add(a, d), add(a, d)),
         add(add(sq(a), mul(two(), mul(a, d))), sq(d))),
        ("(a-d)*(a+d) vs a**2 - d**2",
         mul(sub(a, d), add(a, d)), sub(sq(a), sq(d))),
        ("(a*a + d*d)**2 vs a**4 + 2*a**2*d**2 + d**4",
         sq(add(sq(a), sq(d))),
         add(add(sq(sq(a)), mul(two(), mul(sq(a), sq(d)))), sq(sq(d)))),
    ]
    for name, u, v in pairs:
        assert simplify(u - v) == 0, "%s: not mathematically equal" % name
        assert expand(u) == expand(v)
        assert u != v, (
            "%s: the repository unexpectedly identifies these two expressions, "
            "so the carrier's distinction would be idle" % name)
        assert (u == v) is False and (u != v) is True
        print("  R-distinct: %-38s equal at every number, distinct here"
              % name)

    # And the consequence, stated at the value the entry decision is made on:
    # a condition that a numeric reading settles is left standing here.
    cond = mul(add(a, d), add(a, d)) != add(add(sq(a), mul(two(), mul(a, d))),
                                           sq(d))
    assert cond is True, (
        "the polynomial-identity condition is not live in the repository; "
        "the carrier choice would then be unmotivated")


def main():
    # --- boundary quaternions ------------------------------------------------
    boundary = [
        (1, 0, 0, 0),
        (1, 1, 0, 0), (1, 0, 1, 0), (1, 0, 0, 1),
        (1, 1, 1, 1), (1, -1, 1, -1), (2, 3, 5, 7),
        (1, 2, 3, 4), (0, 1, 1, 1), (3, 0, 4, 0),
        (Rational(1, 2), Rational(1, 2), Rational(1, 2), Rational(1, 2)),
        (Rational(3, 5), Rational(4, 5), 0, 0),
        (Rational(-2, 7), Rational(1, 3), Rational(5, 6), Rational(-1, 4)),
    ]
    for a, b, c, d in boundary:
        check_quaternion(a, b, c, d)

    # --- randomized fuzz (small integers + rationals) ------------------------
    rng = random.Random(15349)
    for _ in range(400):
        vals = []
        for _k in range(4):
            if rng.random() < 0.5:
                vals.append(rng.randint(-6, 6))
            else:
                vals.append(Rational(rng.randint(-6, 6), rng.randint(1, 6)))
        a, b, c, d = vals
        check_quaternion(a, b, c, d)

    # --- the issue's symbolic witness: textbook X-rotation -------------------
    x = symbols('x')
    q = Quaternion(cos(x / 2), sin(x / 2), 0, 0)
    got = trigsimp(q.to_rotation_matrix())
    want = Matrix([[1, 0, 0],
                   [0, cos(x), -sin(x)],
                   [0, sin(x),  cos(x)]])
    assert got == want, (
        "issue witness mismatch: to_rotation_matrix gave %s, expected %s"
        % (got, want))

    # --- the reference facts the carrier choice rests on ----------------------
    check_constructor_bridge()
    check_symbolic_components()
    check_congruence_and_strictness()

    print("G-AX OK: real to_rotation_matrix builds the modelled terms "
          "(row-major, value-preserving, compared directly at the realised "
          "scale s = q.norm()**-2) on %d boundary + 400 fuzz quaternions "
          "(3x3 + "
          "4x4), and on FULLY SYMBOLIC quaternions as an identity of "
          "expression trees; m12 == 2*s*(cd - ba); the seven constructors' "
          "counterparts are exhibited; congruence holds of the repository's "
          "expressions, the repository's equality is coarser than the "
          "carrier's (so the model is the stricter of the two), and "
          "differently-built expressions that agree at every number are "
          "exhibited as distinct there -- which is what the carrier is for; and "
          "no order is defined on the carrier at all, matching the fact that the "
          "repository has no decidable order on these scalars."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
