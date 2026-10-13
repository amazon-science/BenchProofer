"""Twin-artifact model for sympy__sympy-16597.

Behaviour under specification (stated as desired behaviour, not as an edit):

A numeric-property knowledge base assigns each property of a quantity a
three-valued status (True / False / Unknown). The knowledge base must be CLOSED
under the intended mathematical relations between the number sets it names:

  * CONTAINMENT. Every integer is rational; every rational is real and is
    algebraic; every irrational is real; every algebraic quantity is complex;
    every transcendental quantity is complex; every real quantity is complex;
    every even, odd, prime or composite quantity is an integer.

  * BOUNDEDNESS. The rationals, the algebraic numbers, the irrationals and the
    transcendentals are sets of quantities of finite absolute value, so
    membership in any of them makes a quantity bounded; an unbounded quantity
    is not bounded.

  * EXCLUSION. Nothing is both rational and irrational, nothing is both
    algebraic and transcendental, nothing is both even and odd, no prime
    quantity is composite, and a real quantity is a non-integer exactly when it
    is not an integer (so no integer is a non-integer).

  * DEFINING CONDITIONS. Several of these relations are equivalences, not
    one-way containments, so they also constrain in the REVERSE direction: a
    quantity that meets a set's defining conditions IS a member of it. A real
    quantity that is bounded and is not rational is irrational; a whole number
    that is not odd is even; a real quantity that is not positive is bounded
    above by zero, and one that is not negative is bounded below by zero; a
    strictly positive even whole number that is not composite is prime; and a
    quantity bounded above AND below by zero at once is the origin, a bounded
    even whole number. A
    record that only ever propagates memberships forward, and never recognises a
    membership that the statuses it has already resolved are enough to
    establish, is NOT closed.

  * ORIENTATION AND SIGN. Lying on the real line and being a non-zero multiple
    of the imaginary unit are mutually exclusive. Being of any definite sign, or
    bounded on either side by zero, places a quantity on the real line, so a
    quantity off that line is in none of those regions. A definite sign excludes
    the opposite strict sign and the opposite weak bound and entails its own weak
    bound, and a prime or composite quantity is positive. A quantity on the real
    line equals its own conjugate and so is self-adjoint, while a non-zero
    multiple of the imaginary unit is anti-self-adjoint. The knowledge base also
    carries a NON-ZERO status, which records the punctured real line, and that
    status is tied to the rest of the record in BOTH directions. A quantity
    known to be non-zero lies on the real line and is distinct from zero, and so
    is complex, is not a non-zero multiple of the imaginary unit, and is
    self-adjoint; a quantity that is NOT on the real line is not on the
    punctured line either. Every definite sign entails it, and combining it with
    either weak bound by zero gives the corresponding strict sign back. Being
    bounded above AND below by zero at once is the origin, which denies it;
    conversely denying it OF A REAL quantity says the quantity is the origin,
    hence an even whole number bounded on both sides by zero. Odd parity,
    irrationality, and unboundedness on the real line each entail it, since none
    of those quantities is the origin, while parity alone does not -- the origin
    is itself even. These statuses are part
    of the same knowledge base and must be resolved by the same closure: a record
    that answers the membership questions but abstains on orientation, sign or
    self-adjointness where the relations decide them is likewise NOT closed.

Closure is two-directional: every relation propagates its contrapositive as
well, so learning that a quantity is NOT in one set constrains which sets it
can belong to.

Closure is required SEED BY SEED, not merely at one convenient starting point.
A knowledge base that resolves boundedness for one membership assumption while
leaving it Unknown for another that the containments place inside the same
bounded set is not closed; and the same holds of every other relation above,
because a relation says nothing on a record whose statuses were already
resolved for some other reason. The obligation below therefore states the
resolved status of every property for each of thirty-one independent starting
assumptions, chosen so that each relation is observed on at least one record
where nothing else settles the status it decides: between them they witness
both directions of the boundedness relations, the frontier where boundedness
must stay Unknown, the reverse direction of every defining condition, and the
containment, exclusion, sign, orientation and self-adjointness relations:

  BOUNDED SEEDS. Each of the assumptions `even`, `odd`, `integer`, `rational`
  and `irrational` places a quantity inside one of the bounded sets — directly,
  or through the containments even/odd -> integer -> rational -> {real,
  algebraic} and irrational -> real. So each of the five resolves boundedness
  to True, and each resolves the remaining properties to the status its own
  containments and exclusions force (for instance an `integer` seed cannot
  decide parity or primality, and a `rational` seed cannot decide whether the
  quantity is a whole number, so those stay Unknown).

  UNBOUNDED SEED. An unbounded real quantity belongs to none of the sets whose
  membership makes a quantity bounded, hence is not an integer, hence is
  neither even nor odd nor prime nor composite, and its non-integer status
  resolves to True. Unboundedness decides no DIRECTION, though: growing beyond
  every bound is possible on either side of zero, so a quantity known only to be
  unbounded and real has none of the sign regions resolved -- neither strict
  sign, nor either bound by zero, follows from it. Leaving those Unknown is part
  of the closure and not an abstention: a record that reads a sign, or even a
  one-sided bound, off unboundedness alone would make the two opposite unbounded
  directions indistinguishable, and the quantity unbounded the other way
  contradicts it.

  UNKNOWN-FRONTIER SEEDS. Merely learning that a quantity is NOT in one of
  these sets must NOT resolve boundedness: knowing a quantity is not rational,
  not irrational, not even, or not odd leaves its boundedness Unknown, because
  an unbounded quantity and a bounded one both satisfy each of those four
  non-memberships. Non-membership propagates only along the contrapositives the
  containments actually license — a non-rational quantity is not an integer and
  so is neither even, odd, prime nor composite — and along no others; in
  particular it decides neither realness nor boundedness.

  DEFINING-CONDITION SEEDS. Three further assumptions each hand the record
  exactly the statuses that one of the equivalences needs on its right-hand
  side, so that the membership it defines must come out resolved rather than
  Unknown. Assuming a quantity is real, bounded and not rational must make it
  irrational. Assuming a quantity is real and transcendental must ALSO make it
  irrational — transcendence places it among the bounded sets and rules out
  rationality, and those statuses together meet the irrationality condition, so
  a record that resolves boundedness but still leaves irrationality Unknown here
  has propagated the boundedness relation without propagating the equivalence
  that depends on it. Assuming a quantity is a whole number that is not odd must
  make it even. In each case the queried membership is forced by statuses the
  record already holds, so leaving it Unknown is a failure of closure and not a
  permissible abstention.

  ONE-SIDED SEEDS. Two further assumptions each place a whole number on one side
  of zero only. A whole number bounded below by zero is bounded, is not negative
  and is bounded below by zero, yet whether it is strictly positive stays Unknown
  because zero satisfies the assumption too; a whole number bounded above by zero
  is likewise bounded, is not strictly positive, and — since being prime or
  composite would require strict positivity — is neither prime nor composite,
  while whether it is strictly negative stays Unknown. These two make the sign
  regions observable in the same record as the memberships, and they resolve
  boundedness through wholeness exactly as the containments require.

  BOUNDED ALGEBRAIC SEED. One assumption places a quantity among the algebraic
  numbers and, separately, states that it is bounded. Membership of the
  algebraic numbers places it among the complex quantities and rules out
  transcendence; boundedness rules out unboundedness; nothing here decides
  realness, rationality or wholeness, so those stay Unknown. Handing
  boundedness over as an assumption rather than deriving it is deliberate: the
  point of this seed is that the containment of the algebraic numbers in the
  complex quantities is observed on a record where realness -- which would place
  the quantity among the complex quantities for an unrelated reason -- is
  Unknown.

  SIGN-FRONTIER SEEDS. Four assumptions each state that a quantity is NOT in one
  of the sign regions. Refusing the region bounded below by zero denies strict
  positivity, and with it primality and compositeness, and settles nothing else:
  realness itself stays Unknown, because a quantity off the real line is in no
  sign region at all. Adding realness to that same refusal settles the sign
  completely -- such a quantity is strictly negative, hence bounded above by
  zero, hence self-adjoint, complex, and not a multiple of the imaginary unit.
  A real quantity refused strict positivity is bounded above by zero, and a real
  quantity refused strict negativity is bounded below by zero, each by the
  equivalence that defines the weak region; their remaining sign statuses stay
  Unknown, because zero satisfies either refusal.

  ORIGIN SEED. One assumption bounds a quantity above AND below by zero. Only
  the origin satisfies both, so neither strict sign is possible and the whole
  record is settled: a bounded even whole number, rational, real, algebraic,
  complex, self-adjoint, neither prime nor composite, and neither irrational nor
  transcendental nor a non-integer.

  WHOLE-NUMBER-CLASS SEEDS. Two assumptions concern the two distinguished
  classes of whole numbers above zero, each of which excludes the other. A prime
  quantity is a whole number and is strictly positive, hence rational, real,
  algebraic, bounded, complex, self-adjoint, bounded below by zero, and neither
  negative nor bounded above by zero; it is not composite; and its parity stays
  Unknown, since both parities occur among the primes. Conversely a strictly
  positive even whole number that is NOT composite meets the defining condition
  of the smaller class, so primality must come out resolved rather than Unknown.

  PUNCTURED-LINE SEED. One assumption states that a quantity is definitely
  non-zero. That status is the punctured real line, so the quantity lies on the
  real line and is therefore complex, is not a non-zero multiple of the
  imaginary unit, and is self-adjoint; which side of zero it lies on stays
  Unknown, and so does every membership question. This status is not the
  private concern of that one seed: like every other property of the record it
  is resolved, or left Unknown, by the same closure on ALL thirty-one seeds,
  and the obligation below states its value on each of them. Nine of the seeds
  resolve it True, for four independent reasons -- a strict sign, odd parity,
  irrationality, and unboundedness on the real line -- the origin seed resolves
  it False, and the remaining fourteen leave it Unknown, so no single relation
  can account for the whole column.

Together the thirty-one seeds make the boundedness relations observable ONE
ANTECEDENT AT A TIME, and make the equivalences observable in BOTH directions: a
knowledge base cannot satisfy them by resolving boundedness for a
single favoured assumption, because every membership assumption the
containments place inside a bounded set is queried separately, and it cannot
satisfy them by resolving boundedness everywhere either, because the
non-membership seeds pin it to Unknown. The same one-antecedent-at-a-time
discipline applies to the containment, sign, orientation, self-adjointness and
exclusion relations: each of them decides a status on at least one seed whose
other assumptions leave that status free, so a knowledge base that drops the
relation is visible there.

The knowledge base is modelled as a small record of three-valued properties
(True / False / None == Unknown). `consistent_theory` is the pure predicate
that the record is closed under the relations above; each deducer
forward-chains one seed assumption to a closed record. The relations are
modelled DEEPLY (spelled out as the closure predicate plus the per-seed
resolved statuses); they are the behaviour under specification, validated
against the real rule engine by axiom_check.py (G-AX), not consumed as an
axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No @ContractOnly axioms are consumed. The theory of the number sets is the
#  behaviour under specification and is modelled deeply by `consistent_theory`
#  and the per-seed resolved statuses below; its agreement with the real
#  fact-deduction engine is validated out-of-band by axiom_check.py / G-AX, not
#  relied on as an axiom.)
# axioms-end


# pure-start
class KB:
    """Three-valued status of each relevant numeric property.

    Each field is True (the property holds), False (it does not), or None
    (unknown). Only the properties touched by the witnessed queries are carried.
    """

    def __init__(self) -> None:
        # Building a fresh all-Unknown record completes.
        Requires(MustTerminate(1))
        Ensures(Acc(self.integer) and self.integer is None)     # type: ignore
        Ensures(Acc(self.rational) and self.rational is None)   # type: ignore
        Ensures(Acc(self.real) and self.real is None)           # type: ignore
        Ensures(Acc(self.finite) and self.finite is None)       # type: ignore
        Ensures(Acc(self.even) and self.even is None)           # type: ignore
        Ensures(Acc(self.odd) and self.odd is None)             # type: ignore
        Ensures(Acc(self.algebraic) and self.algebraic is None) # type: ignore
        Ensures(Acc(self.transcendental) and self.transcendental is None) # type: ignore
        Ensures(Acc(self.irrational) and self.irrational is None) # type: ignore
        Ensures(Acc(self.infinite) and self.infinite is None)   # type: ignore
        Ensures(Acc(self.complex) and self.complex is None)     # type: ignore
        Ensures(Acc(self.noninteger) and self.noninteger is None) # type: ignore
        Ensures(Acc(self.prime) and self.prime is None)         # type: ignore
        Ensures(Acc(self.composite) and self.composite is None) # type: ignore
        Ensures(Acc(self.imaginary) and self.imaginary is None) # type: ignore
        Ensures(Acc(self.positive) and self.positive is None)   # type: ignore
        Ensures(Acc(self.negative) and self.negative is None)   # type: ignore
        Ensures(Acc(self.nonpositive) and self.nonpositive is None) # type: ignore
        Ensures(Acc(self.nonnegative) and self.nonnegative is None) # type: ignore
        Ensures(Acc(self.hermitian) and self.hermitian is None) # type: ignore
        Ensures(Acc(self.antihermitian) and self.antihermitian is None) # type: ignore
        Ensures(Acc(self.nonzero) and self.nonzero is None) # type: ignore
        self.integer = None        # type: Optional[bool]
        self.rational = None       # type: Optional[bool]
        self.real = None           # type: Optional[bool]
        self.finite = None         # type: Optional[bool]
        self.even = None           # type: Optional[bool]
        self.odd = None            # type: Optional[bool]
        self.algebraic = None      # type: Optional[bool]
        self.transcendental = None # type: Optional[bool]
        self.irrational = None     # type: Optional[bool]
        self.infinite = None       # type: Optional[bool]
        self.complex = None        # type: Optional[bool]
        self.noninteger = None     # type: Optional[bool]
        self.prime = None          # type: Optional[bool]
        self.composite = None      # type: Optional[bool]
        self.imaginary = None      # type: Optional[bool]
        self.positive = None       # type: Optional[bool]
        self.negative = None       # type: Optional[bool]
        self.nonpositive = None    # type: Optional[bool]
        self.nonnegative = None    # type: Optional[bool]
        self.hermitian = None      # type: Optional[bool]
        self.antihermitian = None  # type: Optional[bool]
        self.nonzero = None        # type: Optional[bool]


@Pure
def consistent_theory(k: KB) -> bool:
    """The record is closed under the intended relations between number sets.

    Each `A is True ==> B is True` clause is a containment or an exclusion;
    each `A is False ==> B is False` clause is a contrapositive. `finite` is
    the boundedness property (the quantity has finite absolute value).
    """
    Requires(Acc(k.integer, 1 / 8) and Acc(k.rational, 1 / 8) and Acc(k.real, 1 / 8))
    Requires(Acc(k.finite, 1 / 8) and Acc(k.even, 1 / 8) and Acc(k.odd, 1 / 8))
    Requires(Acc(k.algebraic, 1 / 8) and Acc(k.transcendental, 1 / 8))
    Requires(Acc(k.irrational, 1 / 8) and Acc(k.infinite, 1 / 8))
    Requires(Acc(k.complex, 1 / 8) and Acc(k.noninteger, 1 / 8))
    Requires(Acc(k.prime, 1 / 8) and Acc(k.composite, 1 / 8))
    Requires(Acc(k.imaginary, 1 / 8) and Acc(k.positive, 1 / 8))
    Requires(Acc(k.negative, 1 / 8) and Acc(k.nonpositive, 1 / 8))
    Requires(Acc(k.nonnegative, 1 / 8))
    Requires(Acc(k.hermitian, 1 / 8) and Acc(k.antihermitian, 1 / 8))
    Requires(Acc(k.nonzero, 1 / 8))
    return (
        # integer -> rational ; !rational -> !integer
        Implies(k.integer is True, k.rational is True)
        and Implies(k.rational is False, k.integer is False)
        # rational -> real ; rational -> algebraic ; rational -> finite
        and Implies(k.rational is True, k.real is True)
        and Implies(k.rational is True, k.algebraic is True)
        and Implies(k.rational is True, k.finite is True)
        # real -> complex (a real quantity is complex)
        and Implies(k.real is True, k.complex is True)
        # algebraic -> complex ; algebraic -> finite
        and Implies(k.algebraic is True, k.complex is True)
        and Implies(k.algebraic is True, k.finite is True)
        # even -> integer ; odd -> integer ; !integer -> !even ; !integer -> !odd
        and Implies(k.even is True, k.integer is True)
        and Implies(k.odd is True, k.integer is True)
        and Implies(k.integer is False, k.even is False)
        and Implies(k.integer is False, k.odd is False)
        # even == integer & !odd ; odd == integer & !even (the exclusion, both ways)
        and Implies(k.even is True, k.odd is False)
        and Implies(k.odd is True, k.even is False)
        # prime -> integer ; composite -> integer ; !integer -> !prime ; -> !composite
        and Implies(k.prime is True, k.integer is True)
        and Implies(k.composite is True, k.integer is True)
        and Implies(k.integer is False, k.prime is False)
        and Implies(k.integer is False, k.composite is False)
        # irrational -> real ; irrational -> !rational ; irrational -> finite
        and Implies(k.irrational is True, k.real is True)
        and Implies(k.irrational is True, k.rational is False)
        and Implies(k.irrational is True, k.finite is True)
        # transcendental -> complex ; -> !algebraic ; -> finite
        and Implies(k.transcendental is True, k.complex is True)
        and Implies(k.transcendental is True, k.algebraic is False)
        and Implies(k.transcendental is True, k.finite is True)
        # algebraic -> !transcendental (the same exclusion, other direction)
        and Implies(k.algebraic is True, k.transcendental is False)
        # infinite -> !finite ; finite -> !infinite
        and Implies(k.infinite is True, k.finite is False)
        and Implies(k.finite is True, k.infinite is False)
        # contrapositive: an unbounded quantity is in none of the sets whose
        # membership makes a quantity bounded
        and Implies(k.finite is False, k.rational is False)
        and Implies(k.finite is False, k.algebraic is False)
        and Implies(k.finite is False, k.irrational is False)
        and Implies(k.finite is False, k.transcendental is False)
        # noninteger == real & !integer : the True direction we witness, plus
        # the reverse-direction exclusion (an integer is NOT a noninteger)
        and Implies(k.real is True and k.integer is False, k.noninteger is True)
        and Implies(k.integer is True, k.noninteger is False)
        # DEFINING CONDITIONS, reverse direction. Irrationality and evenness are
        # not merely implied BY their supersets, they are DEFINED by conditions
        # the record can already have resolved, so meeting those conditions
        # forces the membership rather than leaving it Unknown.
        # irrational == real & !rational & finite (the <- direction)
        and Implies(
            k.real is True and k.rational is False and k.finite is True,
            k.irrational is True,
        )
        # even == integer & !odd (the <- direction)
        and Implies(k.integer is True and k.odd is False, k.even is True)
        # ORIENTATION. A quantity that lies on the real line is not a non-zero
        # multiple of the imaginary unit, and a quantity that is such a multiple
        # does not lie on the real line: the two are mutually exclusive.
        and Implies(k.real is True, k.imaginary is False)
        and Implies(k.imaginary is True, k.real is False)
        # SIGN REGIONS. Being of any definite sign, or bounded on either side by
        # zero, places a quantity on the real line; so a quantity that is NOT on
        # the real line is in none of those regions.
        and Implies(k.positive is True, k.real is True)
        and Implies(k.negative is True, k.real is True)
        and Implies(k.nonpositive is True, k.real is True)
        and Implies(k.nonnegative is True, k.real is True)
        and Implies(k.real is False, k.positive is False)
        and Implies(k.real is False, k.negative is False)
        and Implies(k.real is False, k.nonpositive is False)
        and Implies(k.real is False, k.nonnegative is False)
        # SIGN REGIONS, defining conditions. `not greater than zero` and `not
        # less than zero` are DEFINED on the real line by the denial of the
        # opposite strict sign, so these too constrain in the reverse direction:
        # a real quantity that is not positive is bounded above by zero, and a
        # real quantity that is not negative is bounded below by zero.
        and Implies(k.real is True and k.positive is False, k.nonpositive is True)
        and Implies(k.real is True and k.negative is False, k.nonnegative is True)
        # SIGN EXCLUSION. A definite sign excludes the opposite strict sign and
        # the opposite weak bound, and entails its own weak bound; a quantity
        # bounded above AND below by zero is not strictly positive.
        and Implies(k.positive is True, k.negative is False)
        and Implies(k.negative is True, k.positive is False)
        and Implies(k.positive is True, k.nonpositive is False)
        and Implies(k.negative is True, k.nonnegative is False)
        and Implies(k.positive is True, k.nonnegative is True)
        and Implies(k.negative is True, k.nonpositive is True)
        and Implies(k.nonpositive is True and k.nonnegative is True,
                    k.positive is False)
        # A prime or composite quantity is a positive whole number, so its sign
        # is resolved rather than left open.
        and Implies(k.prime is True, k.positive is True)
        and Implies(k.composite is True, k.positive is True)
        # SELF-ADJOINTNESS. A quantity on the real line equals its own conjugate,
        # so it is self-adjoint; a non-zero multiple of the imaginary unit is
        # anti-self-adjoint. Each relation also propagates its contrapositive, so
        # failing to be self-adjoint places a quantity off the real line.
        and Implies(k.real is True, k.hermitian is True)
        and Implies(k.imaginary is True, k.antihermitian is True)
        and Implies(k.hermitian is False, k.real is False)
        and Implies(k.antihermitian is False, k.imaginary is False)
        # THE PUNCTURED REAL LINE. The NON-ZERO status records distance from the
        # origin, which only a quantity on the real line has, so it places the
        # quantity there -- and a quantity off that line is in none of the
        # regions the status describes.
        and Implies(k.nonzero is True, k.real is True)
        and Implies(k.real is False, k.nonzero is False)
        # Any definite sign is a definite distance from the origin.
        and Implies(k.positive is True, k.nonzero is True)
        and Implies(k.negative is True, k.nonzero is True)
        # Being bounded above AND below by zero at once is being AT the origin,
        # so the non-zero status is settled there rather than left open.
        and Implies(k.nonpositive is True and k.nonnegative is True,
                    k.nonzero is False)
        # ... and the two readings agree: a quantity at no distance from the
        # origin that lies on the real line IS the origin, an even whole number
        # bounded by zero on both sides.
        and Implies(k.nonzero is False and k.real is True, k.even is True)
        and Implies(k.nonzero is False and k.real is True, k.nonnegative is True)
        and Implies(k.nonzero is False and k.real is True, k.nonpositive is True)
        # DEFINING CONDITIONS, the sign direction: a non-zero quantity bounded
        # on one side by zero has the corresponding STRICT sign, since the only
        # quantity the weak bound adds to the strict region is the origin.
        and Implies(k.nonzero is True and k.nonpositive is True,
                    k.negative is True)
        and Implies(k.nonzero is True and k.nonnegative is True,
                    k.positive is True)
        # The memberships that exclude the origin therefore settle the status
        # too: the origin is an even, rational, bounded quantity, so anything
        # not even, not rational, or not bounded -- while on the real line --
        # is at a definite distance from it.
        and Implies(k.odd is True, k.nonzero is True)
        and Implies(k.irrational is True, k.nonzero is True)
        and Implies(k.real is True and k.finite is False, k.nonzero is True)
        # OFF THE REAL LINE. A quantity that does not lie on the real line is in
        # none of the sets the line contains: it is not a whole number, not a
        # ratio of whole numbers, and not a bounded non-rational point OF that
        # line, so each of those memberships is denied rather than left open.
        # Its non-integer status is a status ON the line too, so it is denied as
        # well, and having no position on the line it is at no definite distance
        # from the origin.
        and Implies(k.real is False, k.integer is False)
        and Implies(k.real is False, k.rational is False)
        and Implies(k.real is False, k.irrational is False)
        and Implies(k.real is False, k.noninteger is False)
        and Implies(k.real is False, k.nonzero is False)
        # A non-zero multiple of the imaginary unit lies off the real line, so
        # everything above applies to it; in particular it is at no definite
        # distance from the origin, and it is not a bounded non-rational point
        # of the line.
        and Implies(k.imaginary is True, k.nonzero is False)
        and Implies(k.imaginary is True, k.irrational is False)
        and Implies(k.imaginary is True, k.rational is False)
        and Implies(k.imaginary is True, k.integer is False)
        and Implies(k.imaginary is True, k.noninteger is False)
        # Being at no definite distance from the origin while NOT being a whole
        # number places a quantity off the real line: on the line the only such
        # quantity is the origin itself, which IS a whole number.
        and Implies(k.nonzero is False and k.integer is False, k.real is False)
        # UNBOUNDEDNESS, the memberships it denies. A quantity of unbounded
        # absolute value belongs to none of the sets whose membership bounds it,
        # hence is not a whole number, hence is neither even nor odd nor prime
        # nor composite.
        and Implies(k.finite is False, k.integer is False)
        and Implies(k.finite is False, k.even is False)
        and Implies(k.finite is False, k.odd is False)
        and Implies(k.finite is False, k.prime is False)
        and Implies(k.finite is False, k.composite is False)
        # OUTSIDE THE COMPLEX NUMBERS. Every quantity of every set this theory
        # speaks about is a complex quantity, so failing to be one places the
        # quantity outside all of them: it is not on the real line, not a
        # non-zero multiple of the imaginary unit, and on neither side of the
        # algebraic/transcendental divide.
        and Implies(k.complex is False, k.real is False)
        and Implies(k.complex is False, k.imaginary is False)
        and Implies(k.complex is False, k.algebraic is False)
        and Implies(k.complex is False, k.transcendental is False)
    )
# pure-end


def deduce_even() -> KB:
    """Forward-chain the seed assumption `even = True` to a closed record."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # the seed assumption is preserved, and every status the closure of this
    # seed resolves is pinned: an even quantity is a whole number, hence
    # rational, hence bounded; it is not odd, not a non-integer, and lies in
    # none of the sets the exclusions rule out. Parity does not decide
    # primality, so those two statuses stay Unknown.
    Ensures(Result().integer is True)
    Ensures(Result().rational is True)
    Ensures(Result().real is True)
    Ensures(Result().finite is True)
    Ensures(Result().even is True)
    Ensures(Result().odd is False)
    Ensures(Result().algebraic is True)
    Ensures(Result().transcendental is False)
    Ensures(Result().irrational is False)
    Ensures(Result().infinite is False)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is False)
    Ensures(Result().prime is None)
    Ensures(Result().composite is None)
    # lying on the real line, the quantity is not a non-zero multiple of the
    # imaginary unit; nothing in this seed decides its sign, so each sign region
    # stays Unknown.
    Ensures(Result().imaginary is False)
    Ensures(Result().positive is None)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is None)
    # lying on the real line, the quantity is its own conjugate, hence
    # self-adjoint; nothing here places it off that line, so whether it is
    # anti-self-adjoint stays Unknown.
    Ensures(Result().hermitian is True)
    Ensures(Result().antihermitian is None)
    # the origin is an even whole number, so parity alone does not put the
    # quantity at a distance from zero: the non-zero status stays Unknown.
    Ensures(Result().nonzero is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.even = True
    # even -> integer
    k.integer = True
    # integer -> rational
    k.rational = True
    # rational -> real
    k.real = True
    # real -> !imaginary
    k.imaginary = False
    # real -> hermitian (self-adjoint)
    k.hermitian = True
    # rational -> algebraic
    k.algebraic = True
    # rational / algebraic -> finite (bounded)
    k.finite = True
    # real / algebraic -> complex
    k.complex = True
    # even -> !odd
    k.odd = False
    # integer -> !noninteger
    k.noninteger = False
    # rational -> !irrational
    k.irrational = False
    # algebraic -> !transcendental
    k.transcendental = False
    # finite -> !infinite
    k.infinite = False
    return k
    # impl-end


def deduce_odd() -> KB:
    """Forward-chain the seed assumption `odd = True` to a closed record."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # the mirror-image seed: an odd quantity is likewise a whole number, hence
    # rational, hence bounded, and is not even. Boundedness must resolve here
    # too, for the same containment reason and not because of the parity of the
    # seed.
    Ensures(Result().integer is True)
    Ensures(Result().rational is True)
    Ensures(Result().real is True)
    Ensures(Result().finite is True)
    Ensures(Result().even is False)
    Ensures(Result().odd is True)
    Ensures(Result().algebraic is True)
    Ensures(Result().transcendental is False)
    Ensures(Result().irrational is False)
    Ensures(Result().infinite is False)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is False)
    Ensures(Result().prime is None)
    Ensures(Result().composite is None)
    # lying on the real line, the quantity is not a non-zero multiple of the
    # imaginary unit; nothing in this seed decides its sign, so each sign region
    # stays Unknown.
    Ensures(Result().imaginary is False)
    Ensures(Result().positive is None)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is None)
    # lying on the real line, the quantity is its own conjugate, hence
    # self-adjoint; nothing here places it off that line, so whether it is
    # anti-self-adjoint stays Unknown.
    Ensures(Result().hermitian is True)
    Ensures(Result().antihermitian is None)
    # an odd whole number is not even, and the origin IS even, so the quantity
    # is distinct from zero; on the real line that is the non-zero status.
    Ensures(Result().nonzero is True)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.odd = True
    # odd -> integer
    k.integer = True
    # integer -> rational
    k.rational = True
    # rational -> real
    k.real = True
    # real -> !imaginary
    k.imaginary = False
    # real -> hermitian (self-adjoint)
    k.hermitian = True
    # rational -> algebraic
    k.algebraic = True
    # rational / algebraic -> finite (bounded)
    k.finite = True
    # real / algebraic -> complex
    k.complex = True
    # odd -> !even
    k.even = False
    # integer -> !noninteger
    k.noninteger = False
    # rational -> !irrational
    k.irrational = False
    # algebraic -> !transcendental
    k.transcendental = False
    # finite -> !infinite
    k.infinite = False
    # !even -> distinct from the (even) origin ; real & != 0 -> nonzero
    k.nonzero = True
    return k
    # impl-end


def deduce_integer() -> KB:
    """Forward-chain the seed assumption `integer = True` to a closed record."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # a whole number is rational, hence bounded, hence not a non-integer. Its
    # parity is undetermined (the seed says nothing about it), and so is its
    # primality; both stay Unknown, which is what distinguishes this seed's
    # closure from the parity seeds' while boundedness still resolves.
    Ensures(Result().integer is True)
    Ensures(Result().rational is True)
    Ensures(Result().real is True)
    Ensures(Result().finite is True)
    Ensures(Result().even is None)
    Ensures(Result().odd is None)
    Ensures(Result().algebraic is True)
    Ensures(Result().transcendental is False)
    Ensures(Result().irrational is False)
    Ensures(Result().infinite is False)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is False)
    Ensures(Result().prime is None)
    Ensures(Result().composite is None)
    # lying on the real line, the quantity is not a non-zero multiple of the
    # imaginary unit; nothing in this seed decides its sign, so each sign region
    # stays Unknown.
    Ensures(Result().imaginary is False)
    Ensures(Result().positive is None)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is None)
    # lying on the real line, the quantity is its own conjugate, hence
    # self-adjoint; nothing here places it off that line, so whether it is
    # anti-self-adjoint stays Unknown.
    Ensures(Result().hermitian is True)
    Ensures(Result().antihermitian is None)
    # the origin is a whole number, so wholeness alone leaves the non-zero
    # status Unknown.
    Ensures(Result().nonzero is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.integer = True
    # integer -> rational
    k.rational = True
    # rational -> real
    k.real = True
    # real -> !imaginary
    k.imaginary = False
    # real -> hermitian (self-adjoint)
    k.hermitian = True
    # rational -> algebraic
    k.algebraic = True
    # rational / algebraic -> finite (bounded)
    k.finite = True
    # real / algebraic -> complex
    k.complex = True
    # integer -> !noninteger
    k.noninteger = False
    # rational -> !irrational
    k.irrational = False
    # algebraic -> !transcendental
    k.transcendental = False
    # finite -> !infinite
    k.infinite = False
    return k
    # impl-end


def deduce_rational() -> KB:
    """Forward-chain the seed assumption `rational = True` to a closed record."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # membership in the rationals resolves boundedness directly, and carries
    # realness and algebraicity with it. Whether the quantity is a WHOLE number
    # is undetermined, so `integer` and the properties that depend on it stay
    # Unknown -- boundedness must resolve even though nothing here places the
    # quantity among the whole numbers.
    Ensures(Result().integer is None)
    Ensures(Result().rational is True)
    Ensures(Result().real is True)
    Ensures(Result().finite is True)
    Ensures(Result().even is None)
    Ensures(Result().odd is None)
    Ensures(Result().algebraic is True)
    Ensures(Result().transcendental is False)
    Ensures(Result().irrational is False)
    Ensures(Result().infinite is False)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is None)
    Ensures(Result().prime is None)
    Ensures(Result().composite is None)
    # lying on the real line, the quantity is not a non-zero multiple of the
    # imaginary unit; nothing in this seed decides its sign, so each sign region
    # stays Unknown.
    Ensures(Result().imaginary is False)
    Ensures(Result().positive is None)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is None)
    # lying on the real line, the quantity is its own conjugate, hence
    # self-adjoint; nothing here places it off that line, so whether it is
    # anti-self-adjoint stays Unknown.
    Ensures(Result().hermitian is True)
    Ensures(Result().antihermitian is None)
    # the origin is rational, so this membership leaves the non-zero status
    # Unknown.
    Ensures(Result().nonzero is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.rational = True
    # rational -> real
    k.real = True
    # real -> !imaginary
    k.imaginary = False
    # real -> hermitian (self-adjoint)
    k.hermitian = True
    # rational -> algebraic
    k.algebraic = True
    # rational / algebraic -> finite (bounded)
    k.finite = True
    # real / algebraic -> complex
    k.complex = True
    # rational -> !irrational
    k.irrational = False
    # algebraic -> !transcendental
    k.transcendental = False
    # finite -> !infinite
    k.infinite = False
    return k
    # impl-end


def deduce_irrational() -> KB:
    """Forward-chain the seed assumption `irrational = True` to a closed record."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # an irrational quantity is real and bounded, and is not rational, hence
    # not a whole number, hence neither even nor odd nor prime nor composite,
    # and its non-integer status resolves to True. Boundedness here comes from
    # the irrationals being a bounded set, not through the rationals -- the
    # exclusion puts this seed outside them. Whether the quantity is algebraic
    # is undetermined.
    Ensures(Result().integer is False)
    Ensures(Result().rational is False)
    Ensures(Result().real is True)
    Ensures(Result().finite is True)
    Ensures(Result().even is False)
    Ensures(Result().odd is False)
    Ensures(Result().algebraic is None)
    Ensures(Result().transcendental is None)
    Ensures(Result().irrational is True)
    Ensures(Result().infinite is False)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is True)
    Ensures(Result().prime is False)
    Ensures(Result().composite is False)
    # lying on the real line, the quantity is not a non-zero multiple of the
    # imaginary unit; nothing in this seed decides its sign, so each sign region
    # stays Unknown.
    Ensures(Result().imaginary is False)
    Ensures(Result().positive is None)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is None)
    # lying on the real line, the quantity is its own conjugate, hence
    # self-adjoint; nothing here places it off that line, so whether it is
    # anti-self-adjoint stays Unknown.
    Ensures(Result().hermitian is True)
    Ensures(Result().antihermitian is None)
    # an irrational quantity is not rational and the origin IS rational, so it
    # is distinct from zero; being real too, its non-zero status is True.
    Ensures(Result().nonzero is True)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.irrational = True
    # irrational -> real
    k.real = True
    # real -> !imaginary
    k.imaginary = False
    # real -> hermitian (self-adjoint)
    k.hermitian = True
    # irrational -> finite (bounded)
    k.finite = True
    # real -> complex
    k.complex = True
    # irrational -> !rational
    k.rational = False
    # !rational -> !integer
    k.integer = False
    # !integer -> !even
    k.even = False
    # !integer -> !odd
    k.odd = False
    # !integer -> !prime
    k.prime = False
    # !integer -> !composite
    k.composite = False
    # real & !integer -> noninteger
    k.noninteger = True
    # finite -> !infinite
    k.infinite = False
    # !rational -> distinct from the (rational) origin ; real & != 0 -> nonzero
    k.nonzero = True
    return k
    # impl-end


def deduce_integer_nonnegative() -> KB:
    """Forward-chain the seed assumption `integer = True`, `nonnegative = True`
    to a closed record: a whole number bounded below by zero."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # a whole number is rational, hence bounded, algebraic, real and complex,
    # and is not a non-integer. Being bounded below by zero it is not negative,
    # while whether it is strictly positive is left open, since zero meets this
    # seed too. Wholeness alone still does not decide parity or primality.
    Ensures(Result().integer is True)
    Ensures(Result().rational is True)
    Ensures(Result().real is True)
    Ensures(Result().finite is True)
    Ensures(Result().even is None)
    Ensures(Result().odd is None)
    Ensures(Result().algebraic is True)
    Ensures(Result().transcendental is False)
    Ensures(Result().irrational is False)
    Ensures(Result().infinite is False)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is False)
    Ensures(Result().prime is None)
    Ensures(Result().composite is None)
    Ensures(Result().imaginary is False)
    Ensures(Result().positive is None)
    Ensures(Result().negative is False)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is True)
    # lying on the real line, the quantity is its own conjugate, hence
    # self-adjoint; nothing here places it off that line, so whether it is
    # anti-self-adjoint stays Unknown.
    Ensures(Result().hermitian is True)
    Ensures(Result().antihermitian is None)
    # the origin is a whole number bounded below by zero, so the non-zero
    # status stays Unknown -- exactly as the strict sign does.
    Ensures(Result().nonzero is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.integer = True
    k.nonnegative = True
    # integer -> rational
    k.rational = True
    # rational -> real
    k.real = True
    # real -> !imaginary
    k.imaginary = False
    # real -> hermitian (self-adjoint)
    k.hermitian = True
    # rational -> algebraic
    k.algebraic = True
    # rational / algebraic -> finite (bounded)
    k.finite = True
    # real / algebraic -> complex
    k.complex = True
    # nonnegative -> !negative
    k.negative = False
    # integer -> !noninteger
    k.noninteger = False
    # rational -> !irrational
    k.irrational = False
    # algebraic -> !transcendental
    k.transcendental = False
    # finite -> !infinite
    k.infinite = False
    return k
    # impl-end


def deduce_integer_nonpositive() -> KB:
    """Forward-chain the seed assumption `integer = True`, `nonpositive = True`
    to a closed record: a whole number bounded above by zero."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # a whole number is rational, hence bounded, algebraic, real and complex,
    # and is not a non-integer. Being bounded above by zero it is not strictly
    # positive, and since a prime or composite quantity would have to be
    # strictly positive, both of those resolve False. Whether it is strictly
    # negative is left open, since zero meets this seed too.
    Ensures(Result().integer is True)
    Ensures(Result().rational is True)
    Ensures(Result().real is True)
    Ensures(Result().finite is True)
    Ensures(Result().even is None)
    Ensures(Result().odd is None)
    Ensures(Result().algebraic is True)
    Ensures(Result().transcendental is False)
    Ensures(Result().irrational is False)
    Ensures(Result().infinite is False)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is False)
    Ensures(Result().prime is False)
    Ensures(Result().composite is False)
    Ensures(Result().imaginary is False)
    Ensures(Result().positive is False)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is True)
    Ensures(Result().nonnegative is None)
    # lying on the real line, the quantity is its own conjugate, hence
    # self-adjoint; nothing here places it off that line, so whether it is
    # anti-self-adjoint stays Unknown.
    Ensures(Result().hermitian is True)
    Ensures(Result().antihermitian is None)
    # the origin is a whole number bounded above by zero, so the non-zero
    # status stays Unknown -- exactly as the strict sign does.
    Ensures(Result().nonzero is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.integer = True
    k.nonpositive = True
    # integer -> rational
    k.rational = True
    # rational -> real
    k.real = True
    # real -> !imaginary
    k.imaginary = False
    # real -> hermitian (self-adjoint)
    k.hermitian = True
    # rational -> algebraic
    k.algebraic = True
    # rational / algebraic -> finite (bounded)
    k.finite = True
    # real / algebraic -> complex
    k.complex = True
    # nonpositive -> !positive
    k.positive = False
    # !positive -> !prime ; !composite
    k.prime = False
    k.composite = False
    # integer -> !noninteger
    k.noninteger = False
    # rational -> !irrational
    k.irrational = False
    # algebraic -> !transcendental
    k.transcendental = False
    # finite -> !infinite
    k.infinite = False
    return k
    # impl-end


def deduce_infinite() -> KB:
    """Forward-chain the seed assumption `infinite = True` (with a real,
    finite-negating quantity) to a closed record, resolving the set-membership
    statuses to False."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # the unbounded direction: an unbounded real quantity belongs to none of
    # the sets whose membership makes a quantity bounded, hence is not a whole
    # number, hence is neither even nor odd nor prime nor composite, and its
    # non-integer status resolves to True. This is the contrapositive traffic
    # of the same boundedness relations the bounded seeds exercise forwards.
    Ensures(Result().integer is False)
    Ensures(Result().rational is False)
    Ensures(Result().real is True)
    Ensures(Result().finite is False)
    Ensures(Result().even is False)
    Ensures(Result().odd is False)
    Ensures(Result().algebraic is False)
    Ensures(Result().transcendental is False)
    Ensures(Result().irrational is False)
    Ensures(Result().infinite is True)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is True)
    Ensures(Result().prime is False)
    Ensures(Result().composite is False)
    # lying on the real line, the quantity is not a non-zero multiple of the
    # imaginary unit. Which side of zero an unbounded real quantity lies on is
    # NOT determined by unboundedness: this seed says only that the quantity
    # grows beyond every bound, which either direction permits, so every sign
    # region stays Unknown -- no strict sign, and neither bound by zero, is
    # resolved. Those Unknowns are an obligation and not an abstention: a record
    # that reads a sign, or even a one-sided bound, off unboundedness alone would
    # make the two opposite unbounded directions indistinguishable, and the
    # quantity unbounded the other way contradicts it.
    Ensures(Result().imaginary is False)
    Ensures(Result().positive is None)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is None)
    # lying on the real line, the quantity is its own conjugate, hence
    # self-adjoint; nothing here places it off that line, so whether it is
    # anti-self-adjoint stays Unknown.
    Ensures(Result().hermitian is True)
    Ensures(Result().antihermitian is None)
    # growing beyond every bound is being at no finite distance from the
    # origin, so the quantity is distinct from it: the non-zero status is True
    # even though WHICH side of zero it lies on stays Unknown.
    Ensures(Result().nonzero is True)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.infinite = True
    # the seed
    k.real = True
    # real -> !imaginary
    k.imaginary = False
    # real -> hermitian (self-adjoint)
    k.hermitian = True
    # real -> complex
    k.complex = True
    # infinite -> !finite
    k.finite = False
    # !finite -> !rational
    k.rational = False
    # !finite -> !algebraic
    k.algebraic = False
    # !finite -> !irrational
    k.irrational = False
    # !finite -> !transcendental
    k.transcendental = False
    # !rational -> !integer
    k.integer = False
    # !integer -> !even
    k.even = False
    # !integer -> !odd
    k.odd = False
    # !integer -> !prime
    k.prime = False
    # !integer -> !composite
    k.composite = False
    # real & !integer -> noninteger
    k.noninteger = True
    # !finite -> at no finite distance from the origin ; real & != 0 -> nonzero
    k.nonzero = True
    return k
    # impl-end


def deduce_not_rational() -> KB:
    """Forward-chain the seed assumption `rational = False` to a closed
    record: non-membership propagates only along the contrapositives the
    containments license."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # the Unknown frontier. Knowing a quantity is NOT rational rules out its
    # being a whole number and so its being even, odd, prime or composite -- and
    # nothing more. In particular it must leave BOUNDEDNESS Unknown: a bounded
    # irrational and an unbounded quantity are both non-rational, so the
    # relations give no verdict. Realness is likewise undetermined.
    Ensures(Result().integer is False)
    Ensures(Result().rational is False)
    Ensures(Result().real is None)
    Ensures(Result().finite is None)
    Ensures(Result().even is False)
    Ensures(Result().odd is False)
    Ensures(Result().algebraic is None)
    Ensures(Result().transcendental is None)
    Ensures(Result().irrational is None)
    Ensures(Result().infinite is None)
    Ensures(Result().complex is None)
    Ensures(Result().noninteger is None)
    Ensures(Result().prime is False)
    Ensures(Result().composite is False)
    # this seed does not place the quantity on the real line, so neither its
    # orientation nor any sign region is decided.
    Ensures(Result().imaginary is None)
    Ensures(Result().positive is None)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is None)
    # this seed does not place the quantity on the real line, so neither
    # self-adjointness nor anti-self-adjointness is decided.
    Ensures(Result().hermitian is None)
    Ensures(Result().antihermitian is None)
    # a non-rational quantity need not lie on the real line at all, and the
    # non-zero status is a status ON that line, so it stays Unknown.
    Ensures(Result().nonzero is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.rational = False
    # !rational -> !integer
    k.integer = False
    # !integer -> !even
    k.even = False
    # !integer -> !odd
    k.odd = False
    # !integer -> !prime
    k.prime = False
    # !integer -> !composite
    k.composite = False
    return k
    # impl-end


def deduce_not_irrational() -> KB:
    """Forward-chain the seed assumption `irrational = False` to a closed
    record: the non-membership decides nothing else."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # the weakest frontier seed. Failing to be irrational places a quantity in
    # no set at all -- it may be rational, or unbounded, or not real -- so every
    # other status, boundedness included, stays Unknown.
    Ensures(Result().integer is None)
    Ensures(Result().rational is None)
    Ensures(Result().real is None)
    Ensures(Result().finite is None)
    Ensures(Result().even is None)
    Ensures(Result().odd is None)
    Ensures(Result().algebraic is None)
    Ensures(Result().transcendental is None)
    Ensures(Result().irrational is False)
    Ensures(Result().infinite is None)
    Ensures(Result().complex is None)
    Ensures(Result().noninteger is None)
    Ensures(Result().prime is None)
    Ensures(Result().composite is None)
    # this seed does not place the quantity on the real line, so neither its
    # orientation nor any sign region is decided.
    Ensures(Result().imaginary is None)
    Ensures(Result().positive is None)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is None)
    # this seed does not place the quantity on the real line, so neither
    # self-adjointness nor anti-self-adjointness is decided.
    Ensures(Result().hermitian is None)
    Ensures(Result().antihermitian is None)
    # refusing irrationality settles nothing about the real line, so the
    # non-zero status stays Unknown.
    Ensures(Result().nonzero is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed; nothing else follows from it
    k.irrational = False
    return k
    # impl-end


def deduce_not_even() -> KB:
    """Forward-chain the seed assumption `even = False` to a closed record:
    failing to have one parity decides neither the other nor boundedness."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # a non-even quantity need not be a whole number at all, so its
    # wholeness, its parity in the other direction, and its boundedness all
    # stay Unknown. The parity exclusion runs from a POSITIVE parity to the
    # denial of the other, never from a denial outwards.
    Ensures(Result().integer is None)
    Ensures(Result().rational is None)
    Ensures(Result().real is None)
    Ensures(Result().finite is None)
    Ensures(Result().even is False)
    Ensures(Result().odd is None)
    Ensures(Result().algebraic is None)
    Ensures(Result().transcendental is None)
    Ensures(Result().irrational is None)
    Ensures(Result().infinite is None)
    Ensures(Result().complex is None)
    Ensures(Result().noninteger is None)
    Ensures(Result().prime is None)
    Ensures(Result().composite is None)
    # this seed does not place the quantity on the real line, so neither its
    # orientation nor any sign region is decided.
    Ensures(Result().imaginary is None)
    Ensures(Result().positive is None)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is None)
    # this seed does not place the quantity on the real line, so neither
    # self-adjointness nor anti-self-adjointness is decided.
    Ensures(Result().hermitian is None)
    Ensures(Result().antihermitian is None)
    # refusing evenness settles nothing about the real line, so the non-zero
    # status stays Unknown.
    Ensures(Result().nonzero is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed; a denied parity propagates to nothing
    k.even = False
    return k
    # impl-end


def deduce_not_odd() -> KB:
    """Forward-chain the seed assumption `odd = False` to a closed record:
    the mirror frontier seed, which likewise decides nothing else."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # the mirror of the previous seed. Denying one parity leaves wholeness, the
    # other parity and boundedness all Unknown; boundedness must NOT become
    # resolved here just because it is resolved for every seed that positively
    # places the quantity inside one of the bounded sets.
    Ensures(Result().integer is None)
    Ensures(Result().rational is None)
    Ensures(Result().real is None)
    Ensures(Result().finite is None)
    Ensures(Result().even is None)
    Ensures(Result().odd is False)
    Ensures(Result().algebraic is None)
    Ensures(Result().transcendental is None)
    Ensures(Result().irrational is None)
    Ensures(Result().infinite is None)
    Ensures(Result().complex is None)
    Ensures(Result().noninteger is None)
    Ensures(Result().prime is None)
    Ensures(Result().composite is None)
    # this seed does not place the quantity on the real line, so neither its
    # orientation nor any sign region is decided.
    Ensures(Result().imaginary is None)
    Ensures(Result().positive is None)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is None)
    # this seed does not place the quantity on the real line, so neither
    # self-adjointness nor anti-self-adjointness is decided.
    Ensures(Result().hermitian is None)
    Ensures(Result().antihermitian is None)
    # refusing oddness settles nothing about the real line, so the non-zero
    # status stays Unknown.
    Ensures(Result().nonzero is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed; a denied parity propagates to nothing
    k.odd = False
    return k
    # impl-end


def deduce_real_nonrational_bounded() -> KB:
    """Forward-chain the seed assumption `real = True`, `rational = False`,
    `finite = True` to a closed record: the defining conditions of
    irrationality are all present, so irrationality must be resolved True."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # a real, bounded, non-rational quantity MEETS the defining condition of
    # irrationality, so irrationality is resolved True and not left Unknown.
    # Not being rational makes it not a whole number, hence neither even, odd,
    # prime nor composite, and a real non-integer is a non-integer. Which of
    # the algebraic / transcendental sets it lies in is not decided.
    Ensures(Result().integer is False)
    Ensures(Result().rational is False)
    Ensures(Result().real is True)
    Ensures(Result().finite is True)
    Ensures(Result().even is False)
    Ensures(Result().odd is False)
    Ensures(Result().algebraic is None)
    Ensures(Result().transcendental is None)
    Ensures(Result().irrational is True)
    Ensures(Result().infinite is False)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is True)
    Ensures(Result().prime is False)
    Ensures(Result().composite is False)
    # lying on the real line, the quantity is not a non-zero multiple of the
    # imaginary unit; nothing in this seed decides its sign, so each sign region
    # stays Unknown.
    Ensures(Result().imaginary is False)
    Ensures(Result().positive is None)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is None)
    # lying on the real line, the quantity is its own conjugate, hence
    # self-adjoint; nothing here places it off that line, so whether it is
    # anti-self-adjoint stays Unknown.
    Ensures(Result().hermitian is True)
    Ensures(Result().antihermitian is None)
    # the quantity is not rational and the origin IS rational, so it is
    # distinct from zero; being real, its non-zero status is True.
    Ensures(Result().nonzero is True)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.real = True
    # real -> !imaginary
    k.imaginary = False
    # real -> hermitian (self-adjoint)
    k.hermitian = True
    k.rational = False
    k.finite = True
    # the defining condition of irrationality is met
    k.irrational = True
    # !rational -> !integer
    k.integer = False
    # !integer -> !even ; !odd ; !prime ; !composite
    k.even = False
    k.odd = False
    k.prime = False
    k.composite = False
    # real & !integer -> noninteger
    k.noninteger = True
    # real -> complex
    k.complex = True
    # finite -> !infinite
    k.infinite = False
    # !rational -> distinct from the (rational) origin ; real & != 0 -> nonzero
    k.nonzero = True
    return k
    # impl-end


def deduce_real_transcendental() -> KB:
    """Forward-chain the seed assumption `real = True`, `transcendental = True`
    to a closed record: transcendence bounds the quantity and denies it
    rationality, which together force irrationality."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # transcendence places the quantity among the bounded sets and excludes it
    # from the algebraic ones, hence from the rationals; a real, bounded,
    # non-rational quantity then MEETS the defining condition of irrationality,
    # so irrationality is resolved True. This seed therefore witnesses the
    # boundedness relation and the equivalence that depends on it TOGETHER.
    Ensures(Result().integer is False)
    Ensures(Result().rational is False)
    Ensures(Result().real is True)
    Ensures(Result().finite is True)
    Ensures(Result().even is False)
    Ensures(Result().odd is False)
    Ensures(Result().algebraic is False)
    Ensures(Result().transcendental is True)
    Ensures(Result().irrational is True)
    Ensures(Result().infinite is False)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is True)
    Ensures(Result().prime is False)
    Ensures(Result().composite is False)
    # lying on the real line, the quantity is not a non-zero multiple of the
    # imaginary unit; nothing in this seed decides its sign, so each sign region
    # stays Unknown.
    Ensures(Result().imaginary is False)
    Ensures(Result().positive is None)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is None)
    # lying on the real line, the quantity is its own conjugate, hence
    # self-adjoint; nothing here places it off that line, so whether it is
    # anti-self-adjoint stays Unknown.
    Ensures(Result().hermitian is True)
    Ensures(Result().antihermitian is None)
    # transcendence rules out algebraicity and so rationality, and the origin
    # is rational, so the quantity is distinct from zero; being real, its
    # non-zero status is True.
    Ensures(Result().nonzero is True)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.real = True
    # real -> !imaginary
    k.imaginary = False
    # real -> hermitian (self-adjoint)
    k.hermitian = True
    k.transcendental = True
    # transcendental -> !algebraic
    k.algebraic = False
    # transcendental -> finite (bounded)
    k.finite = True
    # !algebraic -> !rational
    k.rational = False
    # !rational -> !integer
    k.integer = False
    # !integer -> !even ; !odd ; !prime ; !composite
    k.even = False
    k.odd = False
    k.prime = False
    k.composite = False
    # real & !rational & finite -> irrational
    k.irrational = True
    # real & !integer -> noninteger
    k.noninteger = True
    # real / transcendental -> complex
    k.complex = True
    # finite -> !infinite
    k.infinite = False
    # !rational -> distinct from the (rational) origin ; real & != 0 -> nonzero
    k.nonzero = True
    return k
    # impl-end


def deduce_integer_nonodd() -> KB:
    """Forward-chain the seed assumption `integer = True`, `odd = False` to a
    closed record: the defining conditions of evenness are both present, so
    evenness must be resolved True."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # a whole number that is not odd MEETS the defining condition of evenness,
    # so evenness is resolved True and not left Unknown. Being a whole number
    # also makes it rational, hence bounded, algebraic, real and complex, and
    # not a non-integer. Wholeness alone still does not decide primality.
    Ensures(Result().integer is True)
    Ensures(Result().rational is True)
    Ensures(Result().real is True)
    Ensures(Result().finite is True)
    Ensures(Result().even is True)
    Ensures(Result().odd is False)
    Ensures(Result().algebraic is True)
    Ensures(Result().transcendental is False)
    Ensures(Result().irrational is False)
    Ensures(Result().infinite is False)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is False)
    Ensures(Result().prime is None)
    Ensures(Result().composite is None)
    # lying on the real line, the quantity is not a non-zero multiple of the
    # imaginary unit; nothing in this seed decides its sign, so each sign region
    # stays Unknown.
    Ensures(Result().imaginary is False)
    Ensures(Result().positive is None)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is None)
    # lying on the real line, the quantity is its own conjugate, hence
    # self-adjoint; nothing here places it off that line, so whether it is
    # anti-self-adjoint stays Unknown.
    Ensures(Result().hermitian is True)
    Ensures(Result().antihermitian is None)
    # the origin is a whole number that is not odd, so the non-zero status
    # stays Unknown.
    Ensures(Result().nonzero is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.integer = True
    k.odd = False
    # the defining condition of evenness is met
    k.even = True
    # integer -> rational
    k.rational = True
    # rational -> real
    k.real = True
    # real -> !imaginary
    k.imaginary = False
    # real -> hermitian (self-adjoint)
    k.hermitian = True
    # rational -> algebraic
    k.algebraic = True
    # rational / algebraic -> finite (bounded)
    k.finite = True
    # real / algebraic -> complex
    k.complex = True
    # integer -> !noninteger
    k.noninteger = False
    # rational -> !irrational
    k.irrational = False
    # algebraic -> !transcendental
    k.transcendental = False
    # finite -> !infinite
    k.infinite = False
    return k
    # impl-end


def deduce_algebraic_bounded() -> KB:
    """Forward-chain the seed assumption `algebraic = True`, `finite = True` to a
    closed record: a bounded algebraic quantity."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # an algebraic quantity is complex -- the containment holds for EVERY
    # algebraic quantity, not only for the rational ones, so it must be
    # resolved here even though this seed decides no membership below
    # algebraic (whether the quantity is rational, real or a whole number
    # all stay Unknown). Boundedness comes from the seed itself, so this
    # record claims nothing about which sets make a quantity bounded.
    Ensures(Result().integer is None)
    Ensures(Result().rational is None)
    Ensures(Result().real is None)
    Ensures(Result().finite is True)
    Ensures(Result().even is None)
    Ensures(Result().odd is None)
    Ensures(Result().algebraic is True)
    Ensures(Result().transcendental is False)
    Ensures(Result().irrational is None)
    Ensures(Result().infinite is False)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is None)
    Ensures(Result().prime is None)
    Ensures(Result().composite is None)
    Ensures(Result().imaginary is None)
    Ensures(Result().positive is None)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is None)
    Ensures(Result().hermitian is None)
    Ensures(Result().antihermitian is None)
    # realness is Unknown here, and the non-zero status is a status on the real
    # line, so it stays Unknown too.
    Ensures(Result().nonzero is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.algebraic = True
    k.finite = True
    # algebraic -> complex
    k.complex = True
    # algebraic -> !transcendental
    k.transcendental = False
    # finite -> !infinite
    k.infinite = False
    return k
    # impl-end


def deduce_not_nonnegative() -> KB:
    """Forward-chain the seed assumption `nonnegative = False` to a closed
    record: a quantity NOT bounded below by zero."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # being strictly positive entails being bounded below by zero, so the
    # denial of that bound denies strict positivity; and since a prime or a
    # composite quantity is strictly positive, both of those go with it.
    # Nothing else follows: the denial of a bound places the quantity
    # nowhere, so realness, boundedness and every membership stay Unknown.
    Ensures(Result().integer is None)
    Ensures(Result().rational is None)
    Ensures(Result().real is None)
    Ensures(Result().finite is None)
    Ensures(Result().even is None)
    Ensures(Result().odd is None)
    Ensures(Result().algebraic is None)
    Ensures(Result().transcendental is None)
    Ensures(Result().irrational is None)
    Ensures(Result().infinite is None)
    Ensures(Result().complex is None)
    Ensures(Result().noninteger is None)
    Ensures(Result().prime is False)
    Ensures(Result().composite is False)
    Ensures(Result().imaginary is None)
    Ensures(Result().positive is False)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is False)
    Ensures(Result().hermitian is None)
    Ensures(Result().antihermitian is None)
    # a quantity in no sign region at all satisfies this refusal, so realness
    # and with it the non-zero status stay Unknown.
    Ensures(Result().nonzero is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.nonnegative = False
    # positive -> nonnegative, so !nonnegative -> !positive
    k.positive = False
    # a prime or composite quantity is positive, so !positive denies both
    k.prime = False
    k.composite = False
    return k
    # impl-end


def deduce_real_not_nonnegative() -> KB:
    """Forward-chain the seed assumption `real = True`, `nonnegative = False` to
    a closed record: a quantity on the real line that is NOT bounded below by
    zero."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # on the real line the two weak bounds are the denials of the opposite
    # strict signs, so denying the lower bound while asserting realness
    # forces STRICT negativity -- and with it the upper bound -- rather than
    # leaving the direction open. Strict positivity, primality and
    # compositeness are excluded; no membership and no boundedness follows.
    Ensures(Result().integer is None)
    Ensures(Result().rational is None)
    Ensures(Result().real is True)
    Ensures(Result().finite is None)
    Ensures(Result().even is None)
    Ensures(Result().odd is None)
    Ensures(Result().algebraic is None)
    Ensures(Result().transcendental is None)
    Ensures(Result().irrational is None)
    Ensures(Result().infinite is None)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is None)
    Ensures(Result().prime is False)
    Ensures(Result().composite is False)
    Ensures(Result().imaginary is False)
    Ensures(Result().positive is False)
    Ensures(Result().negative is True)
    Ensures(Result().nonpositive is True)
    Ensures(Result().nonnegative is False)
    # lying on the real line, the quantity is its own conjugate, hence
    # self-adjoint; nothing here places it off that line, so whether it is
    # anti-self-adjoint stays Unknown.
    Ensures(Result().hermitian is True)
    Ensures(Result().antihermitian is None)
    # the quantity is strictly below zero, hence distinct from it: the
    # non-zero status is True.
    Ensures(Result().nonzero is True)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.real = True
    k.nonnegative = False
    # real -> complex ; real -> !imaginary ; real -> hermitian
    k.complex = True
    k.imaginary = False
    k.hermitian = True
    # positive -> nonnegative, so !nonnegative -> !positive
    k.positive = False
    # real & !positive -> nonpositive (bounded above by zero)
    k.nonpositive = True
    # nonnegative == real & !negative, so real & !nonnegative -> negative
    k.negative = True
    # !positive -> !prime ; !composite
    k.prime = False
    k.composite = False
    # negative -> nonzero (strictly below zero)
    k.nonzero = True
    return k
    # impl-end


def deduce_real_not_positive() -> KB:
    """Forward-chain the seed assumption `real = True`, `positive = False` to a
    closed record: a quantity on the real line that is NOT strictly positive."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # the upper bound by zero is DEFINED on the real line as the denial of
    # strict positivity, so it must come back resolved rather than Unknown.
    # Whether the quantity is strictly negative stays Unknown, since zero
    # meets this seed too, and so does the lower bound.
    Ensures(Result().integer is None)
    Ensures(Result().rational is None)
    Ensures(Result().real is True)
    Ensures(Result().finite is None)
    Ensures(Result().even is None)
    Ensures(Result().odd is None)
    Ensures(Result().algebraic is None)
    Ensures(Result().transcendental is None)
    Ensures(Result().irrational is None)
    Ensures(Result().infinite is None)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is None)
    Ensures(Result().prime is False)
    Ensures(Result().composite is False)
    Ensures(Result().imaginary is False)
    Ensures(Result().positive is False)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is True)
    Ensures(Result().nonnegative is None)
    # lying on the real line, the quantity is its own conjugate, hence
    # self-adjoint; nothing here places it off that line, so whether it is
    # anti-self-adjoint stays Unknown.
    Ensures(Result().hermitian is True)
    Ensures(Result().antihermitian is None)
    # the origin is bounded above by zero, so refusing strict positivity on the
    # real line leaves the non-zero status Unknown.
    Ensures(Result().nonzero is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.real = True
    k.positive = False
    # real -> complex ; real -> !imaginary ; real -> hermitian
    k.complex = True
    k.imaginary = False
    k.hermitian = True
    # nonpositive == real & !positive (the <- direction)
    k.nonpositive = True
    # !positive -> !prime ; !composite
    k.prime = False
    k.composite = False
    return k
    # impl-end


def deduce_real_not_negative() -> KB:
    """Forward-chain the seed assumption `real = True`, `negative = False` to a
    closed record: a quantity on the real line that is NOT strictly negative."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # symmetrically, the lower bound by zero is DEFINED on the real line as
    # the denial of strict negativity, so it too must come back resolved.
    # Strict positivity stays Unknown (zero meets this seed), and so does
    # the upper bound, primality and compositeness.
    Ensures(Result().integer is None)
    Ensures(Result().rational is None)
    Ensures(Result().real is True)
    Ensures(Result().finite is None)
    Ensures(Result().even is None)
    Ensures(Result().odd is None)
    Ensures(Result().algebraic is None)
    Ensures(Result().transcendental is None)
    Ensures(Result().irrational is None)
    Ensures(Result().infinite is None)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is None)
    Ensures(Result().prime is None)
    Ensures(Result().composite is None)
    Ensures(Result().imaginary is False)
    Ensures(Result().positive is None)
    Ensures(Result().negative is False)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is True)
    # lying on the real line, the quantity is its own conjugate, hence
    # self-adjoint; nothing here places it off that line, so whether it is
    # anti-self-adjoint stays Unknown.
    Ensures(Result().hermitian is True)
    Ensures(Result().antihermitian is None)
    # the origin is bounded below by zero, so refusing strict negativity on the
    # real line leaves the non-zero status Unknown.
    Ensures(Result().nonzero is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.real = True
    k.negative = False
    # real -> complex ; real -> !imaginary ; real -> hermitian
    k.complex = True
    k.imaginary = False
    k.hermitian = True
    # nonnegative == real & !negative (the <- direction)
    k.nonnegative = True
    return k
    # impl-end


def deduce_nonnegative_nonpositive() -> KB:
    """Forward-chain the seed assumption `nonnegative = True`, `nonpositive =
    True` to a closed record: a quantity bounded below AND above by zero."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # a quantity bounded on both sides by zero IS zero: neither strict sign
    # survives, and the additive identity is an even whole number, so the
    # whole membership chain resolves -- rational, real, algebraic, bounded,
    # complex -- rather than staying Unknown behind the two bounds. It is
    # neither prime nor composite, since both require strict positivity.
    Ensures(Result().integer is True)
    Ensures(Result().rational is True)
    Ensures(Result().real is True)
    Ensures(Result().finite is True)
    Ensures(Result().even is True)
    Ensures(Result().odd is False)
    Ensures(Result().algebraic is True)
    Ensures(Result().transcendental is False)
    Ensures(Result().irrational is False)
    Ensures(Result().infinite is False)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is False)
    Ensures(Result().prime is False)
    Ensures(Result().composite is False)
    Ensures(Result().imaginary is False)
    Ensures(Result().positive is False)
    Ensures(Result().negative is False)
    Ensures(Result().nonpositive is True)
    Ensures(Result().nonnegative is True)
    # lying on the real line, the quantity is its own conjugate, hence
    # self-adjoint; nothing here places it off that line, so whether it is
    # anti-self-adjoint stays Unknown.
    Ensures(Result().hermitian is True)
    Ensures(Result().antihermitian is None)
    # bounded above AND below by zero, the quantity IS the origin, so it is at
    # no distance from zero at all: the non-zero status resolves to False.
    Ensures(Result().nonzero is False)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.nonnegative = True
    k.nonpositive = True
    # bounded above AND below by zero: neither strict sign is possible
    k.positive = False
    k.negative = False
    # the only quantity with both bounds is zero: an even whole number
    k.even = True
    k.integer = True
    # even -> !odd
    k.odd = False
    # integer -> rational
    k.rational = True
    # rational -> real ; rational -> algebraic
    k.real = True
    k.algebraic = True
    # rational / algebraic -> finite (bounded)
    k.finite = True
    # real / algebraic -> complex
    k.complex = True
    # real -> !imaginary ; real -> hermitian (self-adjoint)
    k.imaginary = False
    k.hermitian = True
    # integer -> !noninteger
    k.noninteger = False
    # rational -> !irrational
    k.irrational = False
    # algebraic -> !transcendental
    k.transcendental = False
    # finite -> !infinite
    k.infinite = False
    # !positive -> !prime ; !composite
    k.prime = False
    k.composite = False
    # nonnegative & nonpositive -> the origin -> !nonzero
    k.nonzero = False
    return k
    # impl-end


def deduce_prime() -> KB:
    """Forward-chain the seed assumption `prime = True` to a closed record: a
    prime quantity."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # a prime is a strictly positive whole number and is NOT composite --
    # the two are mutually exclusive, so compositeness must come back
    # resolved rather than Unknown. Wholeness carries the membership chain
    # (rational, real, algebraic, bounded, complex) and strict positivity
    # carries the sign region; parity stays Unknown, since primes come both
    # ways.
    Ensures(Result().integer is True)
    Ensures(Result().rational is True)
    Ensures(Result().real is True)
    Ensures(Result().finite is True)
    Ensures(Result().even is None)
    Ensures(Result().odd is None)
    Ensures(Result().algebraic is True)
    Ensures(Result().transcendental is False)
    Ensures(Result().irrational is False)
    Ensures(Result().infinite is False)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is False)
    Ensures(Result().prime is True)
    Ensures(Result().composite is False)
    Ensures(Result().imaginary is False)
    Ensures(Result().positive is True)
    Ensures(Result().negative is False)
    Ensures(Result().nonpositive is False)
    Ensures(Result().nonnegative is True)
    # lying on the real line, the quantity is its own conjugate, hence
    # self-adjoint; nothing here places it off that line, so whether it is
    # anti-self-adjoint stays Unknown.
    Ensures(Result().hermitian is True)
    Ensures(Result().antihermitian is None)
    # a prime quantity is strictly above zero, hence distinct from it.
    Ensures(Result().nonzero is True)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.prime = True
    # prime -> integer ; prime -> positive
    k.integer = True
    k.positive = True
    # a prime quantity is not composite
    k.composite = False
    # integer -> rational
    k.rational = True
    # rational -> real ; rational -> algebraic
    k.real = True
    k.algebraic = True
    # rational / algebraic -> finite (bounded)
    k.finite = True
    # real / algebraic -> complex
    k.complex = True
    # real -> !imaginary ; real -> hermitian (self-adjoint)
    k.imaginary = False
    k.hermitian = True
    # integer -> !noninteger
    k.noninteger = False
    # rational -> !irrational
    k.irrational = False
    # algebraic -> !transcendental
    k.transcendental = False
    # finite -> !infinite
    k.infinite = False
    # positive -> !negative ; !nonpositive ; nonnegative
    k.negative = False
    k.nonpositive = False
    k.nonnegative = True
    # positive -> nonzero (strictly above zero)
    k.nonzero = True
    return k
    # impl-end


def deduce_noncomposite_positive_even() -> KB:
    """Forward-chain the seed assumption `composite = False`, `positive = True`,
    `even = True` to a closed record: a strictly positive even whole number
    that is not composite."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # compositeness is the OTHER defining condition on the whole numbers: a
    # strictly positive even quantity that is not composite has no proper
    # divisors left, so it is prime, and primality must come back resolved
    # rather than Unknown. Evenness carries wholeness and the membership
    # chain; strict positivity carries the sign region.
    Ensures(Result().integer is True)
    Ensures(Result().rational is True)
    Ensures(Result().real is True)
    Ensures(Result().finite is True)
    Ensures(Result().even is True)
    Ensures(Result().odd is False)
    Ensures(Result().algebraic is True)
    Ensures(Result().transcendental is False)
    Ensures(Result().irrational is False)
    Ensures(Result().infinite is False)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is False)
    Ensures(Result().prime is True)
    Ensures(Result().composite is False)
    Ensures(Result().imaginary is False)
    Ensures(Result().positive is True)
    Ensures(Result().negative is False)
    Ensures(Result().nonpositive is False)
    Ensures(Result().nonnegative is True)
    # lying on the real line, the quantity is its own conjugate, hence
    # self-adjoint; nothing here places it off that line, so whether it is
    # anti-self-adjoint stays Unknown.
    Ensures(Result().hermitian is True)
    Ensures(Result().antihermitian is None)
    # the quantity is strictly above zero, hence distinct from it.
    Ensures(Result().nonzero is True)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.composite = False
    k.positive = True
    k.even = True
    # a strictly positive even whole number that is not composite is prime
    k.prime = True
    # even -> integer ; even -> !odd
    k.integer = True
    k.odd = False
    # integer -> rational
    k.rational = True
    # rational -> real ; rational -> algebraic
    k.real = True
    k.algebraic = True
    # rational / algebraic -> finite (bounded)
    k.finite = True
    # real / algebraic -> complex
    k.complex = True
    # real -> !imaginary ; real -> hermitian (self-adjoint)
    k.imaginary = False
    k.hermitian = True
    # integer -> !noninteger
    k.noninteger = False
    # rational -> !irrational
    k.irrational = False
    # algebraic -> !transcendental
    k.transcendental = False
    # finite -> !infinite
    k.infinite = False
    # positive -> !negative ; !nonpositive ; nonnegative
    k.negative = False
    k.nonpositive = False
    k.nonnegative = True
    # positive -> nonzero (strictly above zero)
    k.nonzero = True
    return k
    # impl-end


def deduce_imaginary() -> KB:
    """Forward-chain the seed assumption `imaginary = True` to a closed record:
    a non-zero multiple of the imaginary unit lies OFF the real line, so every
    status that is a status on that line is denied rather than left open."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # A non-zero multiple of the imaginary unit is a complex quantity that does
    # NOT lie on the real line. Every membership the line contains is therefore
    # denied: it is not a whole number, not a ratio of whole numbers, and not a
    # bounded non-rational point of the line; hence neither even nor odd nor
    # prime nor composite, and its non-integer status -- itself a status ON the
    # line -- is denied too.
    Ensures(Result().integer is False)
    Ensures(Result().rational is False)
    Ensures(Result().real is False)
    Ensures(Result().even is False)
    Ensures(Result().odd is False)
    Ensures(Result().irrational is False)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is False)
    Ensures(Result().prime is False)
    Ensures(Result().composite is False)
    Ensures(Result().imaginary is True)
    # Having no position on the real line, the quantity is at no definite
    # distance from the origin and lies in none of the sign regions.
    Ensures(Result().nonzero is False)
    Ensures(Result().positive is False)
    Ensures(Result().negative is False)
    Ensures(Result().nonpositive is False)
    Ensures(Result().nonnegative is False)
    # It is anti-self-adjoint. Whether it is ALSO self-adjoint is not decided
    # by this seed alone, so that status stays Unknown.
    Ensures(Result().antihermitian is True)
    Ensures(Result().hermitian is None)
    # This seed says nothing about which side of the algebraic/transcendental
    # divide the quantity falls on, and so nothing about its boundedness: a
    # bounded and an unbounded multiple of the imaginary unit both satisfy it.
    Ensures(Result().algebraic is None)
    Ensures(Result().transcendental is None)
    Ensures(Result().finite is None)
    Ensures(Result().infinite is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.imaginary = True
    # imaginary -> complex
    k.complex = True
    # imaginary -> antihermitian (anti-self-adjoint)
    k.antihermitian = True
    # imaginary -> !real (off the real line)
    k.real = False
    # !real -> !rational
    k.rational = False
    # !rational -> !integer
    k.integer = False
    # !integer -> !even ; !odd ; !prime ; !composite
    k.even = False
    k.odd = False
    k.prime = False
    k.composite = False
    # !real -> !irrational (irrationality is a property OF the real line)
    k.irrational = False
    # !real -> !noninteger
    k.noninteger = False
    # !real -> !nonzero (no position on the line, no distance from the origin)
    k.nonzero = False
    # !real -> no sign region
    k.positive = False
    k.negative = False
    k.nonpositive = False
    k.nonnegative = False
    return k
    # impl-end


def deduce_imaginary_transcendental() -> KB:
    """Forward-chain the seed assumption `imaginary = True`,
    `transcendental = True` to a closed record: transcendence bounds the
    quantity even though it lies OFF the real line."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # Transcendence places the quantity among the bounded sets -- and it does so
    # WITHOUT reference to the real line, so boundedness is resolved True here
    # exactly as it is for a real transcendental quantity. This seed therefore
    # witnesses the boundedness relation on a record whose realness is DENIED.
    Ensures(Result().finite is True)
    Ensures(Result().infinite is False)
    Ensures(Result().transcendental is True)
    Ensures(Result().algebraic is False)
    # Off the real line, every membership the line contains is denied, as is
    # the non-integer status; irrationality in particular is a property OF the
    # real line, so a bounded non-real quantity is not irrational.
    Ensures(Result().integer is False)
    Ensures(Result().rational is False)
    Ensures(Result().real is False)
    Ensures(Result().even is False)
    Ensures(Result().odd is False)
    Ensures(Result().irrational is False)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is False)
    Ensures(Result().prime is False)
    Ensures(Result().composite is False)
    Ensures(Result().imaginary is True)
    # At no definite distance from the origin, in no sign region, and
    # anti-self-adjoint; self-adjointness is not decided.
    Ensures(Result().nonzero is False)
    Ensures(Result().positive is False)
    Ensures(Result().negative is False)
    Ensures(Result().nonpositive is False)
    Ensures(Result().nonnegative is False)
    Ensures(Result().antihermitian is True)
    Ensures(Result().hermitian is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.imaginary = True
    k.transcendental = True
    # transcendental -> finite (bounded), independently of the real line
    k.finite = True
    # finite -> !infinite
    k.infinite = False
    # transcendental -> !algebraic
    k.algebraic = False
    # imaginary / transcendental -> complex
    k.complex = True
    # imaginary -> antihermitian (anti-self-adjoint)
    k.antihermitian = True
    # imaginary -> !real (off the real line)
    k.real = False
    # !algebraic / !real -> !rational
    k.rational = False
    # !rational -> !integer
    k.integer = False
    # !integer -> !even ; !odd ; !prime ; !composite
    k.even = False
    k.odd = False
    k.prime = False
    k.composite = False
    # !real -> !irrational
    k.irrational = False
    # !real -> !noninteger
    k.noninteger = False
    # !real -> !nonzero
    k.nonzero = False
    # !real -> no sign region
    k.positive = False
    k.negative = False
    k.nonpositive = False
    k.nonnegative = False
    return k
    # impl-end


def deduce_unbounded() -> KB:
    """Forward-chain the seed assumption `finite = False` to a closed record:
    unbounded absolute value alone -- with no position on the real line assumed
    -- denies every membership whose containment bounds a quantity."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # A quantity of unbounded absolute value belongs to none of the sets whose
    # membership makes a quantity bounded, so all four are denied; and being no
    # whole number it is neither even nor odd nor prime nor composite. This is
    # the boundedness relation observed CONTRAPOSITIVELY, on a record that
    # assumes nothing but unboundedness.
    Ensures(Result().finite is False)
    Ensures(Result().rational is False)
    Ensures(Result().algebraic is False)
    Ensures(Result().irrational is False)
    Ensures(Result().transcendental is False)
    Ensures(Result().integer is False)
    Ensures(Result().even is False)
    Ensures(Result().odd is False)
    Ensures(Result().prime is False)
    Ensures(Result().composite is False)
    # Unboundedness does not say WHERE the quantity fails to be bounded: it may
    # or may not lie on the real line. So realness, orientation, complexity, the
    # non-integer status, the distance from the origin, every sign region and
    # both adjointness statuses stay Unknown -- as does whether the quantity is
    # unbounded in the sense the record's own unbounded status records.
    Ensures(Result().real is None)
    Ensures(Result().complex is None)
    Ensures(Result().noninteger is None)
    Ensures(Result().imaginary is None)
    Ensures(Result().positive is None)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is None)
    Ensures(Result().hermitian is None)
    Ensures(Result().antihermitian is None)
    Ensures(Result().nonzero is None)
    Ensures(Result().infinite is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.finite = False
    # !finite -> !rational ; !algebraic ; !irrational ; !transcendental
    k.rational = False
    k.algebraic = False
    k.irrational = False
    k.transcendental = False
    # !rational -> !integer
    k.integer = False
    # !integer -> !even ; !odd ; !prime ; !composite
    k.even = False
    k.odd = False
    k.prime = False
    k.composite = False
    return k
    # impl-end


def deduce_nonreal_at_origin() -> KB:
    """Forward-chain the seed assumption `integer = False`, `nonzero = False`
    to a closed record: on the real line the only quantity at no distance from
    the origin IS a whole number, so denying both places it OFF that line."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # Being at no definite distance from the origin, while NOT being a whole
    # number, forces the quantity off the real line: the origin is the one point
    # of the line at no distance from itself, and it IS a whole number. So
    # realness is resolved False rather than left open, and with it every
    # membership and status the line carries.
    Ensures(Result().nonzero is False)
    Ensures(Result().integer is False)
    Ensures(Result().real is False)
    Ensures(Result().rational is False)
    Ensures(Result().irrational is False)
    Ensures(Result().noninteger is False)
    Ensures(Result().even is False)
    Ensures(Result().odd is False)
    Ensures(Result().prime is False)
    Ensures(Result().composite is False)
    # In no sign region, since each of them is a region OF the real line.
    Ensures(Result().positive is False)
    Ensures(Result().negative is False)
    Ensures(Result().nonpositive is False)
    Ensures(Result().nonnegative is False)
    # Nothing here decides the algebraic/transcendental divide, boundedness,
    # complexity, orientation or either adjointness status.
    Ensures(Result().algebraic is None)
    Ensures(Result().transcendental is None)
    Ensures(Result().finite is None)
    Ensures(Result().infinite is None)
    Ensures(Result().complex is None)
    Ensures(Result().imaginary is None)
    Ensures(Result().hermitian is None)
    Ensures(Result().antihermitian is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.integer = False
    k.nonzero = False
    # at no distance from the origin AND not a whole number -> off the real line
    k.real = False
    # !real -> !rational
    k.rational = False
    # !real -> !irrational
    k.irrational = False
    # !real -> !noninteger
    k.noninteger = False
    # !integer -> !even ; !odd ; !prime ; !composite
    k.even = False
    k.odd = False
    k.prime = False
    k.composite = False
    # !real -> no sign region
    k.positive = False
    k.negative = False
    k.nonpositive = False
    k.nonnegative = False
    return k
    # impl-end


def deduce_not_antihermitian() -> KB:
    """Forward-chain the seed assumption `antihermitian = False` to a closed
    record: failing to be anti-self-adjoint denies being a non-zero multiple of
    the imaginary unit, and nothing else."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # A non-zero multiple of the imaginary unit is anti-self-adjoint, so failing
    # to be anti-self-adjoint denies that orientation. That is the whole of what
    # this seed decides.
    Ensures(Result().antihermitian is False)
    Ensures(Result().imaginary is False)
    # The Unknown frontier. Denying that one orientation places the quantity in
    # no set and on no side of the real line: a real quantity and a quantity of
    # neither orientation both satisfy the seed, so realness, complexity, every
    # membership, boundedness, the non-integer status, self-adjointness, the
    # distance from the origin and every sign region all stay Unknown.
    Ensures(Result().integer is None)
    Ensures(Result().rational is None)
    Ensures(Result().real is None)
    Ensures(Result().finite is None)
    Ensures(Result().even is None)
    Ensures(Result().odd is None)
    Ensures(Result().algebraic is None)
    Ensures(Result().transcendental is None)
    Ensures(Result().irrational is None)
    Ensures(Result().infinite is None)
    Ensures(Result().complex is None)
    Ensures(Result().noninteger is None)
    Ensures(Result().prime is None)
    Ensures(Result().composite is None)
    Ensures(Result().positive is None)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is None)
    Ensures(Result().hermitian is None)
    Ensures(Result().nonzero is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.antihermitian = False
    # !antihermitian -> !imaginary
    k.imaginary = False
    return k
    # impl-end


def deduce_commuting() -> KB:
    """Forward-chain the seed assumption `commutative = True` to a closed record:
    order-independence under multiplication places the quantity in no numeric set
    at all, so every membership and every status stays Unknown."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # Order-independence under multiplication is a property of how the quantity
    # MULTIPLIES, not of which numeric set contains it. Every quantity of the
    # sets this theory speaks about multiplies in that order-independent way, so
    # assuming it excludes nothing: a whole number, a point off the real line,
    # and an unbounded quantity all satisfy this seed. The record it closes to
    # is therefore the wholly Unknown one -- which is the obligation that the
    # containment from complexity to order-independence runs in ONE direction
    # only, and that nothing in this theory may be read backwards out of it.
    Ensures(Result().integer is None)
    Ensures(Result().rational is None)
    Ensures(Result().real is None)
    Ensures(Result().finite is None)
    Ensures(Result().even is None)
    Ensures(Result().odd is None)
    Ensures(Result().algebraic is None)
    Ensures(Result().transcendental is None)
    Ensures(Result().irrational is None)
    Ensures(Result().infinite is None)
    Ensures(Result().complex is None)
    Ensures(Result().noninteger is None)
    Ensures(Result().prime is None)
    Ensures(Result().composite is None)
    Ensures(Result().imaginary is None)
    Ensures(Result().positive is None)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is None)
    Ensures(Result().hermitian is None)
    Ensures(Result().antihermitian is None)
    Ensures(Result().nonzero is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # The seed forces nothing at all, so the freshly-built all-Unknown record IS
    # the closed one: no membership, no sign region and neither adjointness
    # status may be read off order-independence.
    return k
    # impl-end


def deduce_noncommuting() -> KB:
    """Forward-chain the seed assumption `commutative = False` to a closed record:
    a quantity that does NOT multiply order-independently is outside every
    numeric set this theory speaks about."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # Every complex quantity multiplies order-independently, so a quantity that
    # does NOT is not complex -- the containment read contrapositively. Nothing
    # complexity contains can hold of it either: it is not on the real line, not
    # a multiple of the imaginary unit, no whole number, no ratio of whole
    # numbers, no bounded non-rational point of the line, and neither algebraic
    # nor transcendental; hence neither even nor odd nor prime nor composite,
    # with the non-integer status and every sign region denied along with the
    # line itself, and at no definite distance from the origin.
    Ensures(Result().complex is False)
    Ensures(Result().real is False)
    Ensures(Result().imaginary is False)
    Ensures(Result().integer is False)
    Ensures(Result().rational is False)
    Ensures(Result().irrational is False)
    Ensures(Result().algebraic is False)
    Ensures(Result().transcendental is False)
    Ensures(Result().even is False)
    Ensures(Result().odd is False)
    Ensures(Result().prime is False)
    Ensures(Result().composite is False)
    Ensures(Result().noninteger is False)
    Ensures(Result().nonzero is False)
    Ensures(Result().positive is False)
    Ensures(Result().negative is False)
    Ensures(Result().nonpositive is False)
    Ensures(Result().nonnegative is False)
    # Boundedness is NOT decided. Order-independence bears on how a quantity
    # multiplies, not on the size of it, so both statuses about being bounded
    # stay Unknown -- as do both adjointness statuses, which this seed likewise
    # does not reach.
    Ensures(Result().finite is None)
    Ensures(Result().infinite is None)
    Ensures(Result().hermitian is None)
    Ensures(Result().antihermitian is None)
    # post-conditions-end
    # impl-start
    k = KB()
    # !commutative -> !complex (the containment read contrapositively)
    k.complex = False
    # !complex -> !real ; !imaginary
    k.real = False
    k.imaginary = False
    # !complex -> !algebraic ; !transcendental
    k.algebraic = False
    k.transcendental = False
    # !real -> !rational -> !integer
    k.rational = False
    k.integer = False
    # !integer -> !even ; !odd ; !prime ; !composite
    k.even = False
    k.odd = False
    k.prime = False
    k.composite = False
    # !real -> !irrational ; !noninteger ; !nonzero ; no sign region
    k.irrational = False
    k.noninteger = False
    k.nonzero = False
    k.positive = False
    k.negative = False
    k.nonpositive = False
    k.nonnegative = False
    return k
    # impl-end


def deduce_nonzero() -> KB:
    """Forward-chain the seed assumption `nonzero = True` to a closed record: a
    quantity that is definitely non-zero."""
    # pre-conditions-start
    # (no inputs)
    # The deduction is a TOTAL operation: forward-chaining a seed under the
    # containment relations reaches the closed record in finitely many
    # propagation steps and hands it back, for every seed. It never re-enters
    # itself or chains without end, so the queried statuses are always
    # available to the caller rather than pending forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().integer) and Acc(Result().rational) and Acc(Result().real))
    Ensures(Acc(Result().finite) and Acc(Result().even) and Acc(Result().odd))
    Ensures(Acc(Result().algebraic) and Acc(Result().transcendental))
    Ensures(Acc(Result().irrational) and Acc(Result().infinite))
    Ensures(Acc(Result().complex) and Acc(Result().noninteger))
    Ensures(Acc(Result().prime) and Acc(Result().composite))
    Ensures(Acc(Result().imaginary) and Acc(Result().positive))
    Ensures(Acc(Result().negative) and Acc(Result().nonpositive))
    Ensures(Acc(Result().nonnegative))
    Ensures(Acc(Result().hermitian) and Acc(Result().antihermitian))
    Ensures(Acc(Result().nonzero))
    # the result is closed under the containment theory
    Ensures(consistent_theory(Result()))
    # being definitely non-zero is a status about a quantity's DISTANCE from
    # zero, which only a quantity on the real line has, so it places the
    # quantity on that line -- hence complex, self-adjoint and not a
    # non-zero multiple of the imaginary unit. It decides no membership and
    # no bound: a non-zero real quantity can be of either sign, of any set
    # membership, and unbounded.
    Ensures(Result().integer is None)
    Ensures(Result().rational is None)
    Ensures(Result().real is True)
    Ensures(Result().finite is None)
    Ensures(Result().even is None)
    Ensures(Result().odd is None)
    Ensures(Result().algebraic is None)
    Ensures(Result().transcendental is None)
    Ensures(Result().irrational is None)
    Ensures(Result().infinite is None)
    Ensures(Result().complex is True)
    Ensures(Result().noninteger is None)
    Ensures(Result().prime is None)
    Ensures(Result().composite is None)
    Ensures(Result().imaginary is False)
    Ensures(Result().positive is None)
    Ensures(Result().negative is None)
    Ensures(Result().nonpositive is None)
    Ensures(Result().nonnegative is None)
    # lying on the real line, the quantity is its own conjugate, hence
    # self-adjoint; nothing here places it off that line, so whether it is
    # anti-self-adjoint stays Unknown.
    Ensures(Result().hermitian is True)
    Ensures(Result().antihermitian is None)
    Ensures(Result().nonzero is True)
    # post-conditions-end
    # impl-start
    k = KB()
    # the seed
    k.nonzero = True
    # a definitely non-zero quantity lies on the real line
    k.real = True
    # real -> complex
    k.complex = True
    # real -> !imaginary
    k.imaginary = False
    # real -> hermitian (self-adjoint)
    k.hermitian = True
    return k
    # impl-end
