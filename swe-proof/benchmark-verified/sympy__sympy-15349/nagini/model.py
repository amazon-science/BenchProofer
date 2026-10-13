"""Twin-artifact model for sympy__sympy-15349.

Behaviour under specification (stated as the desired result, abstractly):

  A quaternion (a, b, c, d) determines a rotation of 3-space, and the
  associated rotation matrix has, with the common scale factor s = 1/|q|^2,
  the closed-form entries

        | 1 - 2s(c^2+d^2)     2s(bc - da)        2s(bd + ca)    |
        | 2s(bc + da)        1 - 2s(b^2+d^2)     2s(cd - ba)    |
        | 2s(bd - ca)        2s(cd + ba)        1 - 2s(b^2+c^2) |

  The first row/column couples to a-rotations, etc.; the two off-diagonal
  entries that share the factor (cd) carry OPPOSITE signs on the (ba) term:
  the entry above the diagonal in the third column is 2s(cd - ba) and the
  entry below the diagonal in the second column is 2s(cd + ba). This is the
  property that makes the matrix a proper rotation (its action on a vector
  rotating only about the first axis leaves that axis invariant and rotates
  the other two through the same signed angle); a single rotation about that
  axis sends the lower entry to +sin and the upper entry to -sin of the same
  angle.

  When a translation point (x, y, z) is supplied, the 3x3 block is embedded as
  the upper-left of a 4x4 affine matrix; the extra column is
        m_i3 = p_i - (x*m_i0 + y*m_i1 + z*m_i2),   p = (x, y, z),
  the extra row is (0, 0, 0) and the corner is 1. The translation column
  therefore inherits the same signed off-diagonal entries (m13 depends on the
  third-column second-row entry 2s(cd - ba)).

CARRIER — the scalars this behaviour computes with are EXPRESSIONS, and they
are modelled as expressions. `Scalar` is an opaque type; its only inhabitants
are the ones the seven constructors below build, and those seven constructors
name everything this computation does with its inputs:

      zero()      the scalar denoted by nought
      one()       the scalar denoted by unity
      two()       the scalar denoted by twice unity
      add(u, v)   the sum of two scalars
      sub(u, v)   their difference
      mul(u, v)   their product
      sq(u)       the square of a scalar

  Nothing whatever is assumed about them. They carry no postcondition, no
  algebraic law, no ordering, and no interpretation as numbers: a scalar IS
  the term that builds it, and two scalars are the same one exactly when they
  are built the same way out of the same parts. Sameness on this carrier is
  therefore CONGRUENCE and nothing else -- the same constructor applied to the
  same arguments gives the same scalar, and no other identification between
  differently-built terms holds, nor is any such identification refutable.
  Each clause below accordingly says which scalar an entry IS, using `is`:
  sameness here is already the sameness of terms, so there is no coarser
  equality to appeal to and none is introduced.

  That is the faithful reading of this behaviour, and it is worth saying why,
  because it is the substance of the model rather than a technicality. The
  scalars here are symbolic: a component may be an indeterminate, or a
  trigonometric value of an angle, and what the surrounding library does with
  a computed entry is decided by the SHAPE of the expression it was built as.
  Two expressions that a numeric reading would identify -- a product of sums
  and the expanded sum of products, say, which agree at every number -- are
  not the same expression, and this behaviour keeps them apart. A carrier of
  numbers would merge them, and every claim below would then be a claim only
  up to algebraic rearrangement: a realisation could decide between the
  entries above on the basis of an equation between two such expressions,
  agree with every clause below because the equation holds of numbers, and
  compute something else entirely where the equation is a statement about
  shape. The carrier below cannot express that choice as a settled one: an
  equation between differently-built terms is undecided here, so a realisation
  that branches on one has to satisfy the clauses below on BOTH sides of it.

  The other direction is what makes the model sound rather than merely strict:
  every equality this carrier does prove is congruence, and congruence holds of
  expressions -- combining the same parts the same way twice yields the same
  expression. So a proof carried out here transfers, while no rearrangement
  the carrier does not know about can be smuggled through it.

  The seven constructors are the whole vocabulary, and `Scalar` is the whole
  carrier: this behaviour has exactly ONE sort of computed value. There is no
  division, no remainder, no comparison and no rounding on that sort -- an
  operation of that kind is not merely refutable here, it cannot be written
  down, and a realisation reaching for one does not translate. Neither is there
  a second, numeric sort alongside it. The three constants above are nullary
  and the other four take scalars and return a scalar, so no number is ever an
  argument, an operand or a result anywhere in this behaviour. Whole numbers
  occur below in one role only: as POSITIONS in the result and as its LENGTH,
  which is to say as the SHAPE of the matrix and not as a quantity the
  computation works with -- and that shape is always nine and sixteen, so no
  arithmetic is done on those either. A realisation that computes with numbers
  is therefore computing in a sort this behaviour does not have, and what it
  computes there has no counterpart in the modelled operation; mapping.md
  records what follows for its translation.

A matrix is modelled as a flat List[Scalar] in row-major order (length 9 for
the rotation block, 16 for the affine embedding), so the modelled result is
the matrix itself, entry for entry, with nothing in between.

Both operations are TOTAL: the whole matrix is produced by a finite
straight-line cascade of constructor applications on the arguments, so on
every argument tuple the call reaches its return and delivers the entries
below. Divergence is therefore ruled out by the specification itself, not
merely unmentioned by it: a realisation that never reaches the return
(unbounded self-delegation, or a loop with no decreasing measure) does NOT
meet this specification even though every entry equation below would then be
satisfied with nothing to check. The method-level `Requires(MustTerminate(...))`
is what carries that obligation.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List

from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
class Scalar:
    """One scalar of the modelled computation: an expression over the
    components, built by the constructors below and identified with the term
    that builds it. The type is opaque -- it has no field, no ordering and no
    numeric content, and the constructors assume nothing. It is also the ONLY
    sort of value this model computes with: the constants below are nullary and
    every other constructor takes scalars and returns a scalar, so no number is
    ever an argument, an operand or a result.

    A scalar also has a TRUTH VALUE, because the language this behaviour is
    written in gives every value one, and nothing is assumed about it either:
    it is declared below and carries no postcondition, so whether a given
    scalar counts as true or as false is UNDECIDED -- neither provable nor
    refutable -- exactly as an equation between differently-built scalars is."""

    @Pure
    @ContractOnly
    def __bool__(self) -> bool:
        """Whether this scalar counts as true. NOTHING is assumed: no scalar is
        known to be true and none is known to be false, so a realisation that
        decides an entry on the truth value of a scalar must deliver the entries
        below on BOTH sides of that decision."""


@Pure
@ContractOnly
def zero() -> Scalar:
    """The scalar denoted by nought."""


@Pure
@ContractOnly
def one() -> Scalar:
    """The scalar denoted by unity."""


@Pure
@ContractOnly
def two() -> Scalar:
    """The scalar denoted by twice unity."""


@Pure
@ContractOnly
def add(u: Scalar, v: Scalar) -> Scalar:
    """The sum of two scalars."""


@Pure
@ContractOnly
def sub(u: Scalar, v: Scalar) -> Scalar:
    """The difference of two scalars."""


@Pure
@ContractOnly
def mul(u: Scalar, v: Scalar) -> Scalar:
    """The product of two scalars."""


@Pure
@ContractOnly
def sq(u: Scalar) -> Scalar:
    """The square of a scalar."""
# axioms-end


# pure-start
@Pure
def two_s(s: Scalar) -> Scalar:
    # the common factor 2s shared by every off-diagonal entry
    return mul(two(), s)


@Pure
def diag0(b: Scalar, c: Scalar, d: Scalar, s: Scalar) -> Scalar:
    # 1 - 2s(c^2 + d^2)
    return sub(one(), mul(two_s(s), add(sq(c), sq(d))))


@Pure
def diag1(b: Scalar, c: Scalar, d: Scalar, s: Scalar) -> Scalar:
    # 1 - 2s(b^2 + d^2)
    return sub(one(), mul(two_s(s), add(sq(b), sq(d))))


@Pure
def diag2(b: Scalar, c: Scalar, d: Scalar, s: Scalar) -> Scalar:
    # 1 - 2s(b^2 + c^2)
    return sub(one(), mul(two_s(s), add(sq(b), sq(c))))


@Pure
def off_bc_minus(a: Scalar, b: Scalar, c: Scalar, d: Scalar,
                 s: Scalar) -> Scalar:
    # 2s(bc - da)
    return mul(two_s(s), sub(mul(b, c), mul(d, a)))


@Pure
def off_bc_plus(a: Scalar, b: Scalar, c: Scalar, d: Scalar,
                s: Scalar) -> Scalar:
    # 2s(bc + da)
    return mul(two_s(s), add(mul(b, c), mul(d, a)))


@Pure
def off_bd_plus(a: Scalar, b: Scalar, c: Scalar, d: Scalar,
                s: Scalar) -> Scalar:
    # 2s(bd + ca)
    return mul(two_s(s), add(mul(b, d), mul(c, a)))


@Pure
def off_bd_minus(a: Scalar, b: Scalar, c: Scalar, d: Scalar,
                 s: Scalar) -> Scalar:
    # 2s(bd - ca)
    return mul(two_s(s), sub(mul(b, d), mul(c, a)))


@Pure
def off_cd_minus(a: Scalar, b: Scalar, c: Scalar, d: Scalar,
                 s: Scalar) -> Scalar:
    # 2s(cd - ba) — the third-column second-row off-diagonal entry
    return mul(two_s(s), sub(mul(c, d), mul(b, a)))


@Pure
def off_cd_plus(a: Scalar, b: Scalar, c: Scalar, d: Scalar,
                s: Scalar) -> Scalar:
    # 2s(cd + ba) — the second-column third-row off-diagonal entry
    return mul(two_s(s), add(mul(c, d), mul(b, a)))


@Pure
def translation(p: Scalar, x: Scalar, y: Scalar, z: Scalar,
                r0: Scalar, r1: Scalar, r2: Scalar) -> Scalar:
    # p - x*r0 - y*r1 - z*r2, associated to the left as written
    return sub(sub(sub(p, mul(x, r0)), mul(y, r1)), mul(z, r2))
# pure-end


def rotation_matrix(a: Scalar, b: Scalar, c: Scalar, d: Scalar,
                    s: Scalar) -> List[Scalar]:
    # pre-conditions-start
    # TOTALITY. The nine entries are a finite straight-line cascade, so the call
    # always reaches its return; this is claimed as an obligation and not left
    # to whatever the realisation happens to do. Without it every Ensures below
    # would be a statement about runs that return, and a body that never
    # returns would discharge them all with nothing computed -- in particular
    # the entry at index 5, whose (ba) sign is the whole point of this model.
    # The level is 2 rather than 1 because the body allocates the result list,
    # and `list.__init__` needs a level strictly below its caller's.
    Requires(MustTerminate(2))
    # The components and the common scale are scalars of the computation (see
    # CARRIER): opaque values with no field to read, so no object permission is
    # needed and none is asked for. Being an argument, each ranges over every
    # scalar the behaviour can be realised at -- in particular over the scale
    # 1/|q|^2 itself, which is why the equations below are claims about the
    # arguments this behaviour actually has and not only about some of them.
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The result is the 3x3 rotation block in row-major order.
    Ensures(len(Result()) == 9)
    # Diagonal.
    Ensures(Result()[0] is diag0(b, c, d, s))
    Ensures(Result()[4] is diag1(b, c, d, s))
    Ensures(Result()[8] is diag2(b, c, d, s))
    # First-row / first-column off-diagonals.
    Ensures(Result()[1] is off_bc_minus(a, b, c, d, s))
    Ensures(Result()[2] is off_bd_plus(a, b, c, d, s))
    Ensures(Result()[3] is off_bc_plus(a, b, c, d, s))
    Ensures(Result()[6] is off_bd_minus(a, b, c, d, s))
    # The two (cd)-off-diagonals carry OPPOSITE signs on the (ba) term:
    #   row1,col2 (index 5) is 2s(cd - ba); row2,col1 (index 7) is 2s(cd + ba).
    Ensures(Result()[5] is off_cd_minus(a, b, c, d, s))
    Ensures(Result()[7] is off_cd_plus(a, b, c, d, s))
    # post-conditions-end
    # impl-start
    m00 = sub(one(), mul(mul(two(), s), add(sq(c), sq(d))))
    m01 = mul(mul(two(), s), sub(mul(b, c), mul(d, a)))
    m02 = mul(mul(two(), s), add(mul(b, d), mul(c, a)))

    m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
    m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
    m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))

    m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
    m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
    m22 = sub(one(), mul(mul(two(), s), add(sq(b), sq(c))))

    result = [m00, m01, m02, m10, m11, m12, m20, m21, m22]  # type: List[Scalar]
    return result
    # impl-end


def rotation_matrix_affine(a: Scalar, b: Scalar, c: Scalar, d: Scalar,
                           s: Scalar, x: Scalar, y: Scalar,
                           z: Scalar) -> List[Scalar]:
    # pre-conditions-start
    # TOTALITY, as above: the sixteen entries are a finite straight-line
    # cascade, so the call always reaches its return. The obligation is stated
    # at the method level, which is what rejects a diverging realisation; a
    # loop-free, non-self-delegating body pays nothing for it.
    # The level sits ABOVE the 3x3 method's so that a realisation which factors
    # the shared upper-left block out and DELEGATES to it stays admissible --
    # that is what the source does when it computes the nine block entries once
    # and then embeds them -- while self-delegation in either method, and
    # delegation the other way round, are not. The gap of four leaves room for a
    # realisation to insert helpers of its own in that chain.
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The result is the 4x4 affine matrix in row-major order.
    Ensures(len(Result()) == 16)
    # Upper-left 3x3 block equals the rotation block, row by row.
    Ensures(Result()[0] is diag0(b, c, d, s))
    Ensures(Result()[1] is off_bc_minus(a, b, c, d, s))
    Ensures(Result()[2] is off_bd_plus(a, b, c, d, s))
    Ensures(Result()[4] is off_bc_plus(a, b, c, d, s))
    Ensures(Result()[5] is diag1(b, c, d, s))
    Ensures(Result()[6] is off_cd_minus(a, b, c, d, s))
    Ensures(Result()[8] is off_bd_minus(a, b, c, d, s))
    Ensures(Result()[9] is off_cd_plus(a, b, c, d, s))
    Ensures(Result()[10] is diag2(b, c, d, s))
    # Translation column: p_i - x*m_i0 - y*m_i1 - z*m_i2.
    Ensures(Result()[3] is translation(x, x, y, z,
                                      diag0(b, c, d, s),
                                      off_bc_minus(a, b, c, d, s),
                                      off_bd_plus(a, b, c, d, s)))
    # The second-row translation entry inherits the signed (cd - ba) term.
    Ensures(Result()[7] is translation(y, x, y, z,
                                      off_bc_plus(a, b, c, d, s),
                                      diag1(b, c, d, s),
                                      off_cd_minus(a, b, c, d, s)))
    Ensures(Result()[11] is translation(z, x, y, z,
                                       off_bd_minus(a, b, c, d, s),
                                       off_cd_plus(a, b, c, d, s),
                                       diag2(b, c, d, s)))
    # Trailing row is (0, 0, 0, 1).
    Ensures(Result()[12] is zero())
    Ensures(Result()[13] is zero())
    Ensures(Result()[14] is zero())
    Ensures(Result()[15] is one())
    # post-conditions-end
    # impl-start
    m00 = sub(one(), mul(mul(two(), s), add(sq(c), sq(d))))
    m01 = mul(mul(two(), s), sub(mul(b, c), mul(d, a)))
    m02 = mul(mul(two(), s), add(mul(b, d), mul(c, a)))

    m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
    m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
    m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))

    m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
    m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
    m22 = sub(one(), mul(mul(two(), s), add(sq(b), sq(c))))

    m03 = sub(sub(sub(x, mul(x, m00)), mul(y, m01)), mul(z, m02))
    m13 = sub(sub(sub(y, mul(x, m10)), mul(y, m11)), mul(z, m12))
    m23 = sub(sub(sub(z, mul(x, m20)), mul(y, m21)), mul(z, m22))
    m30 = zero()
    m31 = zero()
    m32 = zero()
    m33 = one()

    result = [m00, m01, m02, m03,
              m10, m11, m12, m13,
              m20, m21, m22, m23,
              m30, m31, m32, m33]  # type: List[Scalar]
    return result
    # impl-end
