"""PBT falsification manifest for sympy__sympy-16597.

NOT a Nagini module: a record of adversarial cases the runner
(swebench_nagini.pbt) executes and stamps RESULT onto. Spec cases are full
model.py variants that share the FROZEN spec (only `impl` regions differ,
guaranteed by region-surgery via `_swap`) and are checked by Nagini verify +
markers.same_spec. There are no @ContractOnly axioms (meta.axioms == []) and no
A-consumed deep models, so AXIOM_TESTS == [].

Defended surface (reasoned, not mechanical)
--------------------------------------------
THIRTY-ONE no-input deducers each return a fresh `KB` record of trits
(Optional[bool]), one per independent starting assumption. The load-bearing
postconditions are `consistent_theory(Result())` plus, in every deducer, an
explicit pin of EVERY trit of the record to the status that seed's closure
resolves (all 22 in each of the thirty-one; see SIGN NEUTRALITY below for the
four sign trits, which the unbounded seed formerly left free, and NON-ZERO
STATUS below for the trit that only one seed used to carry).

`consistent_theory` is a GROUNDED @Pure predicate over the record's OWN fields
(a spelled-out conjunction of Implies(...) containment clauses) — there is no
opaque answer-key oracle to echo, so the ungrounded-oracle-echo class is N/A
(an "echo" here is just a correct record). The functions take NO inputs and
hold NO read-only Acc(x,1/2) parameter, so the frame-mutation class is also N/A
(there is no caller input to overwrite).

PER-SEED CLOSURE (2026-08-15). `consistent_theory` is a predicate on ONE
record, so a clause like `rational=T -> finite=T` is VACUOUS on any seed where
boundedness is already resolved for some other reason: on an `even` record
`rational` and `finite` are both True whichever relation forced them. A spec
that instantiates the closure at only one or two convenient seeds therefore
cannot see WHICH memberships force boundedness, and admits a knowledge base
that resolves boundedness for the parity seed alone while leaving it Unknown
for `integer`, `odd` and `rational` (machine-witnessed 2026-08-15: such a rival
verified, and its faithful patch was harness-run to resolved=FALSE, failing the
`is_finite is True` assertions on exactly those seeds). The obligation is now
instantiated SEED BY SEED — five bounded seeds (`even`, `odd`, `integer`,
`rational`, `irrational`), one unbounded seed, and four non-membership frontier
seeds — so each boundedness antecedent is observed on its own record with the
others Unknown. The `nm-*-drop-finite` cases are the reject lane for the
too-weak direction of this class.

FRONTIER (the too-strong direction of the same class). The four non-membership
seeds pin boundedness to None. A knowledge base that settles the seed-by-seed
obligation by resolving boundedness everywhere — propagating non-membership
backwards, e.g. deciding a non-rational quantity is unbounded — contradicts the
real behaviour, in which a bounded irrational and an unbounded quantity are
both non-rational. The `over-frontier-*` cases are that reject lane.

NOT PINNED, deliberately (over-fitting guard). Boundedness for the seeds
`algebraic=True` and `transcendental=True` is NOT constrained. Both statuses
were measured to differ across independently-verified correct alternatives:
one resolving variant leaves `algebraic=True -> finite` Unknown, another leaves
`transcendental=True -> finite` Unknown, and both pass every hidden test. Any
clause pinning them would reject a correct implementation.

The closure theory also carries real=T -> complex=T, the !odd direction
even=T -> odd=F (of even==integer&!odd), the reverse exclusion integer=T ->
noninteger=F (of noninteger==real&!integer), the parity exclusion in both
directions, and the algebraic/transcendental exclusion in both directions.
These are all facts the real engine deduces for every reachable seed (G-AX
validated), so records contradicting them are rejected by
consistent_theory(Result()).

SIGN NEUTRALITY (2026-08-15, third correction). The unbounded seed used to
pin its membership cascade and leave the four sign statuses free, on the reading
that unboundedness simply says nothing about them. Saying nothing is not the
same as pinning Unknown: a record was free to read a strict sign, or a
one-sided bound by zero, off unboundedness alone, and three such rivals were
machine-witnessed to verify against the earlier spec. They are wrong, because
growing beyond every bound is available in EITHER direction: the two opposite
unbounded quantities agree on every membership and disagree on sign, so a
relation that derived a sign from unboundedness would make one of them
contradict itself (measured: the corresponding rule sets leave the
oppositely-unbounded quantity's assumption set inconsistent). The four
`Ensures(... is None)` clauses on the unbounded seed state that, and the
`over-sign-*` cases are its reject lane.

CLAUSE-LEVEL INSTANTIATION (2026-08-16). The same vacuity that hid the
per-seed boundedness class hides EVERY clause no pinned record exercises. A
clause is a statement about one record, so `algebraic=T -> complex=T` says
nothing on a record where realness already forced complexity, and
`real=T & positive=F -> nonpositive=T` says nothing on a record that never
refuses a strict sign. With the closure instantiated at the fifteen membership
seeds alone, nine clause groups of the theory were never observed on a record
that could witness them: the algebraic containment, the two weak sign regions
and their defining conditions, the origin (both bounds by zero at once), the
mutual exclusion of the two distinguished whole-number classes above zero, the
recognition of the smaller one from its defining conditions, and the punctured
real line. Machine-witnessed 2026-08-16 over a survey of 107 rival rule sets:
29 of them verified against the fifteen-seed spec and 13 of those 29 were
resolved=FALSE under the harness (e.g. dropping the realness conjunct of the
non-zero equivalence, or the exclusion between the two whole-number classes).
The closure is now instantiated at nine further seeds chosen so that each of
those clause groups is observed on a record whose OTHER statuses leave it
free to fail; the same survey re-run admits 16 rivals, every one of them
resolved=TRUE, and every trit of the nine new records was measured invariant
across those 16, so no new pin rejects a correct alternative. The `rev-*`
cases on the new seeds are the reject lane for this class, and the
`pos-prime-reorder` / `pos-nonzero-reorder` cases are its over-fitting guard.

NON-ZERO STATUS (2026-08-16). A record field is only constrained where some
postcondition mentions it. The status "definitely away from the origin" was
mentioned by ONE of the thirty-one deducers -- the seed that takes it as its
hypothesis -- and `consistent_theory` held no permission to it at all, so no
clause of the closure theory could speak about it either. On the other
thirty seeds it was therefore a FREE cell of the record: an
implementation could hand back any of the three trits for it and still verify,
including reading a strict-sign consequence off parity or denying distance from
the origin for a strictly positive whole number. Machine-witnessed: four rival
rule sets differing from gold ONLY in that cell verified against the earlier
spec. The field is now pinned in all thirty-one postconditions at the status
the real engine resolves for that seed (measured at the modelled reference and
re-measured identically at the unmodelled base, so the pins cannot turn on
anything the reference theory does not already hold), and `consistent_theory`
takes a fractional permission to it and carries the thirteen clauses of the
punctured real line: its realness conjunct in both directions, the two strict
signs and the two one-sided bounds that force or deny it, the origin, odd
parity, irrationality, and unboundedness on the real line. The `nz-*` cases are
the reject lane for this class in all four shapes (claim where the closure
abstains, claim where it denies, deny where it asserts, abstain where it
asserts), and `pos-real-transcendental-nonzero-first` /
`pos-origin-nonzero-first` are its over-fitting guard.

A further falsification class is COMPLETION (2026-08-14). Every clause above is
a statement about the VALUES of a record that was handed back; none of them
says a record is handed back at all. A deducer that re-enters itself instead of
delivering the closure leaves every queried status pending forever, and the
value clauses hold of it with no work done. The deducers therefore demand
`MustTerminate` in their pre-conditions: the deduction is a TOTAL operation
(the real forward-chaining closure drains a finite fact queue and returns, so
`Symbol('x', even=True).is_finite` and `S.Infinity.is_rational` are always
answered). The `diverge-*` cases below are the reject lane for this class.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-16597"
FLOAT_ENCODING = None  # meta.json float_encoding is null


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- exact gold impl blocks (each is unique in model.py) ---------------------
_A_DEDUCE_EVEN = """    # impl-start
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
    # impl-end"""

_A_DEDUCE_ODD = """    # impl-start
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
    # impl-end"""

_A_DEDUCE_INTEGER = """    # impl-start
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
    # impl-end"""

_A_DEDUCE_RATIONAL = """    # impl-start
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
    # impl-end"""

_A_DEDUCE_IRRATIONAL = """    # impl-start
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
    # impl-end"""

_A_DEDUCE_INFINITE = """    # impl-start
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
    # impl-end"""

# --- SIGN NEUTRALITY rivals (expect reject): deduce_infinite records that read
#     a sign, or a one-sided bound, off unboundedness alone. Derived from the
#     gold block so they cannot drift from it.
_SIGN_INF_POSITIVE = _A_DEDUCE_INFINITE.replace(
    "    return k\n",
    "    # WRONG vs the real engine: a quantity known only to be unbounded and\n"
    "    # real has no sign region resolved; growing beyond every bound is\n"
    "    # available in either direction.\n"
    "    k.positive = True\n"
    "    k.nonnegative = True\n"
    "    k.negative = False\n"
    "    k.nonpositive = False\n"
    "    return k\n")

_SIGN_INF_NONNEG = _A_DEDUCE_INFINITE.replace(
    "    return k\n",
    "    # WRONG vs the real engine: not even a one-sided bound by zero follows\n"
    "    # from unboundedness.\n"
    "    k.nonnegative = True\n"
    "    k.negative = False\n"
    "    return k\n")

_A_DEDUCE_NOT_RATIONAL = """    # impl-start
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
    # impl-end"""

_A_DEDUCE_NOT_EVEN = """    # impl-start
    k = KB()
    # the seed; a denied parity propagates to nothing
    k.even = False
    return k
    # impl-end"""

_A_DEDUCE_NOT_ODD = """    # impl-start
    k = KB()
    # the seed; a denied parity propagates to nothing
    k.odd = False
    return k
    # impl-end"""


_A_DEDUCE_NOT_IRRATIONAL = """    # impl-start
    k = KB()
    # the seed; nothing else follows from it
    k.irrational = False
    return k
    # impl-end"""

# === SPEC LANE ===============================================================

# --- POSITIVE CONTROL (soundness): a structurally-different but CORRECT
#     deduce_even. The gold impl assigns in containment order; this variant
#     assigns in REVERSE containment order. No loops/invariants exist, so
#     reordering keeps every proof obligation (the postcondition is a pure
#     predicate over the final record). MUST verify, else SPEC-TOO-STRONG.
_POS_EVEN = """    # impl-start
    k = KB()
    # assign in reverse containment order through the same final record
    k.complex = True
    k.algebraic = True
    k.finite = True
    k.real = True
    k.imaginary = False
    k.hermitian = True
    k.rational = True
    k.integer = True
    k.even = True
    # the excluded memberships, assigned before the parity facts this time
    k.transcendental = False
    k.irrational = False
    k.infinite = False
    k.odd = False
    k.noninteger = False
    # prime / composite stay Unknown (the seed does not decide primality)
    return k
    # impl-end"""

# --- POSITIVE CONTROL (soundness) for deduce_infinite: reorder the cascade and
#     bind the seed last; the closure is order-insensitive. MUST verify.
_POS_INF = """    # impl-start
    k = KB()
    # distance from the origin resolved before anything else, seed last
    k.nonzero = True
    # establish the negative-set facts first, seed afterwards (order-insensitive)
    k.noninteger = True
    k.composite = False
    k.prime = False
    k.odd = False
    k.even = False
    k.integer = False
    k.transcendental = False
    k.irrational = False
    k.algebraic = False
    k.rational = False
    k.finite = False
    k.complex = True
    k.real = True
    k.imaginary = False
    k.hermitian = True
    k.infinite = True
    return k
    # impl-end"""

# --- POSITIVE CONTROL (soundness) for a BOUNDED SEED OTHER than the parity one:
#     deduce_rational reaches boundedness FIRST and derives the rest afterwards,
#     i.e. by a different route through the same relations. The per-seed
#     obligation must be satisfiable by any order of propagation, not only the
#     containment order. MUST verify, else the seed-by-seed clause over-fits a
#     propagation sequence.
_POS_RATIONAL = """    # impl-start
    k = KB()
    # boundedness first, membership afterwards: a different route to the same
    # closed record
    k.finite = True
    k.infinite = False
    k.complex = True
    k.algebraic = True
    k.transcendental = False
    k.real = True
    k.imaginary = False
    k.hermitian = True
    k.irrational = False
    k.rational = True
    return k
    # impl-end"""

# --- POSITIVE CONTROL (soundness) for a FRONTIER seed: deduce_not_rational
#     reaches the same closed record with the parity denials before the
#     wholeness denial. MUST verify.
_POS_NOT_RATIONAL = """    # impl-start
    k = KB()
    # the denials in the reverse of the licensed propagation order
    k.composite = False
    k.prime = False
    k.odd = False
    k.even = False
    k.integer = False
    k.rational = False
    return k
    # impl-end"""

# --- ADMISSIBILITY: assert (inside the impl region) that consistent_theory is
#     establishable on a normal F2P-shaped result and the witnessed trit holds.
#     The deducers take no inputs, so the precondition is the empty domain; this
#     confirms the postcondition's @Pure predicate ADMITS the realised record
#     (else PRECOND/usage-TOO-STRONG). Keeps the gold body, adds Asserts only.
_ADMISS_EVEN = _A_DEDUCE_EVEN.replace(
    "    return k\n    # impl-end",
    """    # admissibility: the realised record satisfies the closure theory and the
    # witnessed trit, on a normal in-domain (no-input) call.
    Assert(consistent_theory(k))
    Assert(k.finite is True)
    Assert(k.even is True)
    return k
    # impl-end""")

# --- ADMISSIBILITY on a frontier seed: the Unknown pins are jointly
#     establishable too (a record may leave boundedness Unknown here).
_ADMISS_NOT_EVEN = _A_DEDUCE_NOT_EVEN.replace(
    "    return k\n    # impl-end",
    """    Assert(consistent_theory(k))
    Assert(k.finite is None)
    Assert(k.even is False)
    return k
    # impl-end""")

# --- UNIQUENESS PRIMARY (expect reject): deduce_even rival that ALSO sets
#     odd=True. consistent_theory carries the !odd direction of
#     'even == integer & !odd' (even=T -> odd=F), so a record with even=True AND
#     odd=True is INCONSISTENT with the theory and consistent_theory(Result())
#     REJECTS it.
#     REFINEMENT: the real engine deduces is_odd=False for an even quantity; the
#     hidden suite asserts Symbol('x', even=True).is_odd is False. A faithful
#     patch whose engine derived odd=True for an even seed would fail it.
_WEAK_EVEN_ODD = """    # impl-start
    k = KB()
    k.even = True
    k.integer = True
    k.rational = True
    k.real = True
    k.imaginary = False
    k.hermitian = True
    k.algebraic = True
    k.finite = True
    k.complex = True
    k.noninteger = False
    k.irrational = False
    k.transcendental = False
    k.infinite = False
    # WRONG: an even quantity is not odd; the real engine deduces odd=False.
    k.odd = True
    return k
    # impl-end"""

# --- UNIQUENESS (expect reject): deduce_even rival that sets noninteger=True.
#     An even quantity IS an integer, so the real engine gives
#     is_noninteger=False; consistent_theory carries integer=T -> noninteger=F.
_WEAK_EVEN_NONINT = """    # impl-start
    k = KB()
    k.even = True
    k.integer = True
    k.rational = True
    k.real = True
    k.imaginary = False
    k.hermitian = True
    k.algebraic = True
    k.finite = True
    k.complex = True
    k.odd = False
    k.irrational = False
    k.transcendental = False
    k.infinite = False
    # WRONG: an integer is NOT a noninteger; engine gives is_noninteger=False.
    k.noninteger = True
    return k
    # impl-end"""

# --- UNIQUENESS (expect reject) for deduce_infinite: rival that sets
#     complex=False on a real quantity. consistent_theory carries real ->
#     complex, so an unbounded real with complex=False is INCONSISTENT.
_WEAK_INF_COMPLEX = """    # impl-start
    k = KB()
    k.infinite = True
    k.real = True
    k.imaginary = False
    k.hermitian = True
    k.finite = False
    k.rational = False
    k.algebraic = False
    k.irrational = False
    k.transcendental = False
    k.integer = False
    k.even = False
    k.odd = False
    k.prime = False
    k.composite = False
    k.noninteger = True
    # WRONG vs the real engine (an unbounded real IS complex).
    k.complex = False
    return k
    # impl-end"""

# --- SOUNDNESS near-miss (expect reject): deduce_infinite rival that DROPS the
#     noninteger=True assignment (leaves it None). The postcondition pins
#     Result().noninteger is True.
_NM_INF_DROP_NONINT = """    # impl-start
    k = KB()
    k.infinite = True
    k.real = True
    k.imaginary = False
    k.hermitian = True
    k.complex = True
    k.finite = False
    k.rational = False
    k.algebraic = False
    k.irrational = False
    k.transcendental = False
    k.integer = False
    k.even = False
    k.odd = False
    k.prime = False
    k.composite = False
    # DROP: noninteger left None -> violates Ensures(Result().noninteger is True)
    return k
    # impl-end"""


def _drop_finite(anchor_text):
    """Delete the boundedness assignment (and the !infinite fact that depends on
    it) from a bounded-seed impl, leaving both Unknown: the PRE-PATCH reading of
    that one seed, with every other seed still fully resolved."""
    out = []
    for line in anchor_text.splitlines():
        st = line.strip()
        if st in ("k.finite = True", "k.infinite = False"):
            continue
        if st.startswith("#") and ("finite (bounded)" in st or st == "# finite -> !infinite"):
            continue
        out.append(line)
    res = "\n".join(out)
    assert "k.finite" not in res and "k.infinite" not in res
    return res


# --- PARTIAL DOMAIN (expect reject), one case per bounded seed. Each leaves
#     boundedness Unknown for exactly ONE membership assumption while every
#     other seed still resolves it. This is the family the 2026-08-15
#     counterexample belongs to: a knowledge base in which boundedness is
#     forced by one favoured assumption only. Under the pre-repair spec, which
#     instantiated the closure at the parity seed alone, such a rival verified;
#     each of these must now REJECT.
_NM_EVEN_DROP_FINITE = _drop_finite(_A_DEDUCE_EVEN)
_NM_ODD_DROP_FINITE = _drop_finite(_A_DEDUCE_ODD)
_NM_INTEGER_DROP_FINITE = _drop_finite(_A_DEDUCE_INTEGER)
_NM_RATIONAL_DROP_FINITE = _drop_finite(_A_DEDUCE_RATIONAL)
_NM_IRRATIONAL_DROP_FINITE = _drop_finite(_A_DEDUCE_IRRATIONAL)

# --- FRONTIER OVERREACH (expect reject): the too-strong direction. A knowledge
#     base that propagates NON-membership backwards to boundedness. Each of
#     these resolves boundedness on a seed whose real closure leaves it
#     Unknown.
#     REFINEMENT: the hidden suite asserts is_finite is None for a quantity
#     known only to be non-rational / non-irrational / non-even / non-odd, so a
#     patch resolving it either way fails. Two of the three directions also make
#     the real rule set inconsistent (measured 2026-08-15: adding
#     !rational -> !finite, !irrational -> !finite or !even -> !finite each
#     raises a contradiction during deduction on unrelated seeds).
_OVER_NOT_RATIONAL_UNBOUNDED = _A_DEDUCE_NOT_RATIONAL.replace(
    "    return k\n    # impl-end",
    """    # WRONG: non-membership in the rationals does not decide boundedness -- a
    # bounded irrational is also not rational.
    k.finite = False
    k.infinite = True
    return k
    # impl-end""")

_OVER_NOT_IRRATIONAL_BOUNDED = """    # impl-start
    k = KB()
    k.irrational = False
    # WRONG: failing to be irrational places a quantity in no set at all; it may
    # be unbounded. Boundedness must stay Unknown here.
    k.finite = True
    k.infinite = False
    return k
    # impl-end"""

_OVER_NOT_EVEN_BOUNDED = """    # impl-start
    k = KB()
    k.even = False
    # WRONG: a non-even quantity need not be a whole number at all, so nothing
    # bounds it. Boundedness must stay Unknown.
    k.finite = True
    k.infinite = False
    return k
    # impl-end"""

_OVER_NOT_ODD_WHOLENESS = """    # impl-start
    k = KB()
    k.odd = False
    # WRONG: the parity exclusion runs from a POSITIVE parity to the denial of
    # the other, never from a denial outwards, and it never decides wholeness.
    k.even = True
    k.integer = True
    k.rational = True
    k.real = True
    k.imaginary = False
    k.hermitian = True
    k.algebraic = True
    k.finite = True
    k.complex = True
    k.noninteger = False
    k.irrational = False
    k.transcendental = False
    k.infinite = False
    return k
    # impl-end"""

# --- COMPLETION (expect reject): a deducer that never delivers a record — it
#     re-enters itself instead of propagating. Every VALUE clause (the closure
#     theory and all 14 pinned trits) is satisfied with nothing computed, so
#     only the completion demand can reject it.
_DIVERGE_EVEN = """    # impl-start
    return deduce_even()
    # impl-end"""

_DIVERGE_INF = """    # impl-start
    return deduce_infinite()
    # impl-end"""

_DIVERGE_RATIONAL = """    # impl-start
    return deduce_rational()
    # impl-end"""

_DIVERGE_NOT_EVEN = """    # impl-start
    return deduce_not_even()
    # impl-end"""

# --- COMPLETION (expect reject): divergence via an unbounded loop rather than
#     self-re-entry. The loop's guard never changes, so the record is never
#     delivered.
_DIVERGE_LOOP_EVEN = """    # impl-start
    k = KB()
    while k.even is None:
        k.odd = None
    k.even = True
    k.integer = True
    k.rational = True
    k.real = True
    k.imaginary = False
    k.hermitian = True
    k.algebraic = True
    k.finite = True
    k.complex = True
    k.odd = False
    k.noninteger = False
    k.irrational = False
    k.transcendental = False
    k.infinite = False
    return k
    # impl-end"""



# --- anchors for the DEFINING-CONDITION seeds (quoted verbatim from model.py;
#     region surgery via _swap keeps them in sync or fails loudly).
_A_DEDUCE_REAL_NONRATIONAL_BOUNDED = """    # impl-start
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
    # impl-end"""

_A_DEDUCE_REAL_TRANSCENDENTAL = """    # impl-start
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
    # impl-end"""

_A_DEDUCE_INTEGER_NONODD = """    # impl-start
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
    # impl-end"""


def _blank_membership(anchor_text, assign, keep_comment):
    """Delete ONE membership resolution from a defining-condition impl, leaving
    that membership Unknown. The record still satisfies every one-way
    containment and every contrapositive; only the REVERSE direction of the
    equivalence -- the fact that meeting a set's defining conditions makes a
    quantity a member -- is left unpropagated."""
    out = []
    for line in anchor_text.splitlines():
        st = line.strip()
        if st == assign:
            continue
        if st.startswith("#") and keep_comment in st:
            continue
        out.append(line)
    res = "\n".join(out)
    assert assign not in res
    return res


# Leave irrationality Unknown on the seed whose statuses define it.
_REV_RNB_DROP_IRRATIONAL = _blank_membership(
    _A_DEDUCE_REAL_NONRATIONAL_BOUNDED,
    "k.irrational = True",
    "defining condition of irrationality is met",
)
# Same omission on the transcendental seed: boundedness IS resolved here, so the
# irrationality condition is fully met, yet the membership is left Unknown.
_REV_RT_DROP_IRRATIONAL = _blank_membership(
    _A_DEDUCE_REAL_TRANSCENDENTAL,
    "k.irrational = True",
    "real & !rational & finite -> irrational",
)
# Leave evenness Unknown on the whole-number-not-odd seed.
_REV_INO_DROP_EVEN = _blank_membership(
    _A_DEDUCE_INTEGER_NONODD,
    "k.even = True",
    "defining condition of evenness is met",
)
# Positive control: a correct defining-condition impl written in a different
# order (memberships established before the containments they license).
_POS_INO_REORDER = """    # impl-start
    k = KB()
    # the seed, with the defined membership recognised first
    k.integer = True
    k.odd = False
    k.even = True
    # everything wholeness licenses, assigned afterwards
    k.noninteger = False
    k.rational = True
    k.irrational = False
    k.algebraic = True
    k.transcendental = False
    k.real = True
    k.imaginary = False
    k.hermitian = True
    k.complex = True
    k.finite = True
    k.infinite = False
    return k
    # impl-end"""

# --- the nine seeds that instantiate the clause groups the fifteen membership
#     seeds never witnessed (CLAUSE-LEVEL INSTANTIATION above). Exact gold impl
#     blocks; each is unique in model.py.

_A_DEDUCE_ALGEBRAIC_BOUNDED = """    # impl-start
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
    # impl-end"""

_A_DEDUCE_NOT_NONNEGATIVE = """    # impl-start
    k = KB()
    # the seed
    k.nonnegative = False
    # positive -> nonnegative, so !nonnegative -> !positive
    k.positive = False
    # a prime or composite quantity is positive, so !positive denies both
    k.prime = False
    k.composite = False
    return k
    # impl-end"""

_A_DEDUCE_REAL_NOT_NONNEGATIVE = """    # impl-start
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
    # impl-end"""

_A_DEDUCE_REAL_NOT_POSITIVE = """    # impl-start
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
    # impl-end"""

_A_DEDUCE_REAL_NOT_NEGATIVE = """    # impl-start
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
    # impl-end"""

_A_DEDUCE_ORIGIN = """    # impl-start
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
    # impl-end"""

_A_DEDUCE_PRIME = """    # impl-start
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
    # impl-end"""

_A_DEDUCE_NONCOMPOSITE_POSITIVE_EVEN = """    # impl-start
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
    # impl-end"""

_A_DEDUCE_NONZERO = """    # impl-start
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
    # impl-end"""


# --- reject lane: drop exactly the ONE resolution the new pin needs, leaving it
#     Unknown. Every one-way containment and every contrapositive still holds in
#     the mutilated record, so a spec whose pinned records never witness the
#     clause admits these; each corresponds to a surveyed rival rule set that
#     was harness-run to resolved=FALSE.

_REV_AB_DROP_COMPLEX = _blank_membership(
    _A_DEDUCE_ALGEBRAIC_BOUNDED,
    "k.complex = True",
    "algebraic -> complex",
)

_REV_NN_DROP_POSITIVE = _blank_membership(
    _A_DEDUCE_NOT_NONNEGATIVE,
    "k.positive = False",
    "!nonnegative -> !positive",
)

_REV_RNN_DROP_NEGATIVE = _blank_membership(
    _A_DEDUCE_REAL_NOT_NONNEGATIVE,
    "k.negative = True",
    "real & !nonnegative -> negative",
)

_REV_RNP_DROP_NONPOSITIVE = _blank_membership(
    _A_DEDUCE_REAL_NOT_POSITIVE,
    "k.nonpositive = True",
    "nonpositive == real & !positive",
)

_REV_RNG_DROP_NONNEGATIVE = _blank_membership(
    _A_DEDUCE_REAL_NOT_NEGATIVE,
    "k.nonnegative = True",
    "nonnegative == real & !negative",
)

_REV_ORIGIN_DROP_EVEN = _blank_membership(
    _A_DEDUCE_ORIGIN,
    "k.even = True",
    "the only quantity with both bounds is zero",
)

_REV_PRIME_DROP_NONCOMPOSITE = _blank_membership(
    _A_DEDUCE_PRIME,
    "k.composite = False",
    "is not composite",
)

_REV_NPE_DROP_PRIME = _blank_membership(
    _A_DEDUCE_NONCOMPOSITE_POSITIVE_EVEN,
    "k.prime = True",
    "that is not composite is prime",
)

_REV_NZ_DROP_REAL = _blank_membership(
    _A_DEDUCE_NONZERO,
    "k.real = True",
    "lies on the real line",
)


# Positive controls for the new seeds: correct impls written in a different
# order (every licensed status established before the seed that licenses it).
_POS_PRIME_REORDER = """    # impl-start
    k = KB()
    # the licensed statuses first, the seed recognised last
    k.nonzero = True
    k.infinite = False
    k.transcendental = False
    k.irrational = False
    k.noninteger = False
    k.hermitian = True
    k.imaginary = False
    k.complex = True
    k.finite = True
    k.algebraic = True
    k.real = True
    k.rational = True
    k.nonnegative = True
    k.nonpositive = False
    k.negative = False
    k.composite = False
    k.positive = True
    k.integer = True
    k.prime = True
    return k
    # impl-end"""

_POS_NONZERO_REORDER = """    # impl-start
    k = KB()
    # self-adjointness and orientation first
    k.hermitian = True
    k.imaginary = False
    k.complex = True
    # the real line, then the seed that placed the quantity on it
    k.real = True
    k.nonzero = True
    return k
    # impl-end"""


# --- exact gold impl blocks for the seeds that leave the real line and the
#     seed of unbounded absolute value (each is unique in model.py) ---------
_A_DEDUCE_IMAGINARY = """    # impl-start
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
    # impl-end"""

_A_DEDUCE_IMAGINARY_TRANSCENDENTAL = """    # impl-start
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
    # impl-end"""

_A_DEDUCE_UNBOUNDED = """    # impl-start
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
    # impl-end"""

_A_DEDUCE_NONREAL_AT_ORIGIN = """    # impl-start
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
    # impl-end"""

_A_DEDUCE_NOT_ANTIHERMITIAN = """    # impl-start
    k = KB()
    # the seed
    k.antihermitian = False
    # !antihermitian -> !imaginary
    k.imaginary = False
    return k
    # impl-end"""


# --- exact gold impl blocks for the two order-of-multiplication seeds (each
#     is unique in model.py) ------------------------------------------------
_A_DEDUCE_COMMUTING = """    # impl-start
    k = KB()
    # The seed forces nothing at all, so the freshly-built all-Unknown record IS
    # the closed one: no membership, no sign region and neither adjointness
    # status may be read off order-independence.
    return k
    # impl-end"""

_A_DEDUCE_NONCOMMUTING = """    # impl-start
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
    # impl-end"""


# --- non-zero status lane -----------------------------------------------------
# The status "definitely away from the origin" is a field of the record like any
# other, and it is now pinned in EVERY seed's postcondition, so the reject lane
# below covers all four shapes a rule theory can take on it: reading it off a
# seed whose closure leaves it Unknown, asserting it on the one record that
# denies it, denying it on a record that asserts it, and abstaining where the
# closure asserts it.


def _claim_status(anchor_text, comment, assign):
    """Add ONE status resolution just before the record is handed back."""
    if assign in anchor_text:
        raise AssertionError(f"already present: {assign!r}")
    out = anchor_text.replace(
        "    return k",
        f"    # {comment}\n    {assign}\n    return k",
        1,
    )
    assert out != anchor_text
    return out


def _flip_status(anchor_text, old, new):
    """Turn ONE status resolution into the opposite trit."""
    if anchor_text.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return anchor_text.replace(old, new, 1)


# Parity alone does not move a quantity away from the origin -- the origin is
# itself an even whole number -- so the parity seed's closure leaves this status
# Unknown. This rival reads it off parity.
_NZ_EVEN_CLAIM = _claim_status(
    _A_DEDUCE_EVEN, "even -> nonzero", "k.nonzero = True")
# Both bounds by zero at once is the ONE record whose non-zero status is denied;
# this rival asserts it there instead.
_NZ_ORIGIN_CLAIM = _flip_status(
    _A_DEDUCE_ORIGIN, "k.nonzero = False", "k.nonzero = True")
# A strictly positive quantity is away from the origin; this rival denies it.
_NZ_PRIME_DENY = _flip_status(
    _A_DEDUCE_PRIME, "k.nonzero = True", "k.nonzero = False")
# The too-weak direction on two seeds whose closure DOES resolve the status: a
# whole number of odd parity (so not the even origin), and a real transcendental
# (so not the rational origin).
_NZ_ODD_DROP = _blank_membership(
    _A_DEDUCE_ODD, "k.nonzero = True", "distinct from the (even) origin")
_NZ_RT_DROP = _blank_membership(
    _A_DEDUCE_REAL_TRANSCENDENTAL, "k.nonzero = True",
    "distinct from the (rational) origin")

# Over-fitting guards for the new pins: the same records, with the non-zero
# status established FIRST rather than read off the closure last.
_POS_RT_NONZERO_FIRST = """    # impl-start
    k = KB()
    # away from the origin and on the real line, before anything that shows it
    k.nonzero = True
    k.real = True
    k.imaginary = False
    k.hermitian = True
    k.complex = True
    # the seed and its cascade afterwards
    k.transcendental = True
    k.algebraic = False
    k.finite = True
    k.infinite = False
    k.rational = False
    k.irrational = True
    k.integer = False
    k.noninteger = True
    k.even = False
    k.odd = False
    k.prime = False
    k.composite = False
    return k
    # impl-end"""

_POS_ORIGIN_NONZERO_FIRST = """    # impl-start
    k = KB()
    # the denial first, then the two bounds that force it
    k.nonzero = False
    k.nonnegative = True
    k.nonpositive = True
    k.positive = False
    k.negative = False
    # the rest of the origin's table
    k.even = True
    k.odd = False
    k.integer = True
    k.noninteger = False
    k.rational = True
    k.irrational = False
    k.algebraic = True
    k.transcendental = False
    k.real = True
    k.imaginary = False
    k.hermitian = True
    k.complex = True
    k.finite = True
    k.infinite = False
    k.prime = False
    k.composite = False
    return k
    # impl-end"""

# --- OFF-THE-REAL-LINE lane -----------------------------------------------------
# Until this correction every record the spec observed placed the quantity ON the
# real line or left its realness Unknown; realness was resolved False on NO
# observed record. So every relation this theory holds about NOT lying on that
# line -- and every relation that reads a status off unboundedness -- was
# vacuous on the whole observable, and a rule theory free to get them wrong
# verified. The rivals below are that class, in each of the shapes it takes:
# reading boundedness off a seed whose closure leaves it Unknown, resolving a
# membership off the real line that the line's own containments deny, dropping
# the ONE resolution the off-line records force, and reading a numeric status
# off order-of-multiplication alone.

# The too-strong direction off the real line: a multiple of the imaginary unit,
# with boundedness read off a seed that does not decide it.
_OFF_IMAG_CLAIM_FINITE = _claim_status(
    _A_DEDUCE_IMAGINARY, "!real -> finite", "k.finite = True")
# The same shape on the algebraic/transcendental divide, which the bare
# imaginary seed likewise leaves open.
_OFF_IMAG_CLAIM_TRANSC = _claim_status(
    _A_DEDUCE_IMAGINARY, "!real -> !transcendental", "k.transcendental = False")
# And on unboundedness, whose status the seed does not reach either.
_OFF_IMAG_CLAIM_INFINITE = _claim_status(
    _A_DEDUCE_IMAGINARY, "!real -> !infinite", "k.infinite = False")
# Self-adjointness read off the imaginary axis, where the closure abstains.
_OFF_IMAG_CLAIM_HERM = _claim_status(
    _A_DEDUCE_IMAGINARY, "!real -> hermitian", "k.hermitian = True")
# The too-weak direction: the bounded record OFF the real line, with the one
# status the boundedness relation resolves there dropped. This is the record on
# which that relation is observable away from the line, so the omission is
# exactly the pre-repair reading of it.
_OFF_IMAGTR_DROP_FINITE = _drop_finite(_A_DEDUCE_IMAGINARY_TRANSCENDENTAL)
# Self-adjointness claimed on the bounded off-line record.
_OFF_IMAGTR_CLAIM_HERM = _claim_status(
    _A_DEDUCE_IMAGINARY_TRANSCENDENTAL, "transcendental -> hermitian",
    "k.hermitian = True")
# Unboundedness: the record that assumes only unbounded absolute value, with the
# unbounded status itself read as resolved where the closure leaves it Unknown.
_OFF_UNB_CLAIM_INFINITE = _claim_status(
    _A_DEDUCE_UNBOUNDED, "!finite -> infinite", "k.infinite = True")
# ... and with a membership the unboundedness denies left Unknown instead.
_OFF_UNB_DROP_INTEGER = _blank_membership(
    _A_DEDUCE_UNBOUNDED, "k.integer = False", "!rational -> !integer")
# Realness read off unboundedness, which does not say WHERE the quantity fails
# to be bounded.
_OFF_UNB_CLAIM_REAL = _claim_status(
    _A_DEDUCE_UNBOUNDED, "!finite -> real", "k.real = True")
# The punctured line read backwards: the record at no distance from the origin
# and not a whole number, with the realness it forces left Unknown.
_OFF_ORIGIN_DROP_REAL = _blank_membership(
    _A_DEDUCE_NONREAL_AT_ORIGIN, "k.real = False",
    "at no distance from the origin AND not a whole number")
# Denying one adjointness orientation is read as denying a membership too.
_OFF_NAH_CLAIM_COMPOSITE = _claim_status(
    _A_DEDUCE_NOT_ANTIHERMITIAN, "!antihermitian -> !composite",
    "k.composite = False")
# Order-of-multiplication alone read as placing the quantity in a set: the
# containment from complexity to order-independence run BACKWARDS.
_OFF_COMM_CLAIM_COMPLEX = _claim_status(
    _A_DEDUCE_COMMUTING, "commutative -> complex", "k.complex = True")
# The contrapositive of that containment dropped where it is the only route to
# the record's memberships.
_OFF_NONCOMM_DROP_COMPLEX = _blank_membership(
    _A_DEDUCE_NONCOMMUTING, "k.complex = False",
    "!commutative -> !complex")

# Over-fitting guards for the new lane: the SAME off-line and unbounded records,
# with the propagation done in a different order. Closure is order-insensitive,
# so each must VERIFY, else the new pins state a propagation order rather than
# the theory.
_POS_IMAG_REAL_FIRST = """    # impl-start
    k = KB()
    # off the real line first, then the orientation that puts it there
    k.real = False
    k.rational = False
    k.integer = False
    k.even = False
    k.odd = False
    k.prime = False
    k.composite = False
    k.irrational = False
    k.noninteger = False
    k.nonzero = False
    k.positive = False
    k.negative = False
    k.nonpositive = False
    k.nonnegative = False
    k.imaginary = True
    k.complex = True
    k.antihermitian = True
    return k
    # impl-end"""
_POS_IMAGTR_FINITE_FIRST = """    # impl-start
    k = KB()
    # boundedness established BEFORE the membership that forces it
    k.finite = True
    k.infinite = False
    k.transcendental = True
    k.algebraic = False
    k.imaginary = True
    k.complex = True
    k.antihermitian = True
    k.real = False
    k.rational = False
    k.integer = False
    k.even = False
    k.odd = False
    k.prime = False
    k.composite = False
    k.irrational = False
    k.noninteger = False
    k.nonzero = False
    k.positive = False
    k.negative = False
    k.nonpositive = False
    k.nonnegative = False
    return k
    # impl-end"""

SPEC_TESTS = [
    # ---- positive controls (must verify) ----
    # ---- DEFINING CONDITIONS, reverse direction (expect reject). Each leaves a
    #      membership Unknown that the statuses already in the record define. All
    #      one-way containments and contrapositives still hold, so a spec that
    #      only ever propagates memberships forward admits these.
    {
        "id": "rev-real-nonrational-bounded-drop-irrational",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_REAL_NONRATIONAL_BOUNDED,
                        _REV_RNB_DROP_IRRATIONAL),
        "refinement": "Refines to a rule theory that states irrationality as a "
                      "one-way containment instead of an equivalence, so a real, "
                      "bounded, non-rational quantity is never recognised as "
                      "irrational. The hidden suite asserts that recognition.",
        "rationale": "A real, bounded, non-rational quantity MEETS the defining "
                     "condition of irrationality, so irrationality must resolve "
                     "True; this rival leaves it Unknown while every forward "
                     "containment still holds. Must reject.",
    },
    {
        "id": "rev-real-transcendental-drop-irrational",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_REAL_TRANSCENDENTAL,
                        _REV_RT_DROP_IRRATIONAL),
        "refinement": "Refines to a theory that bounds the transcendentals but "
                      "still propagates irrationality one way only, so a real "
                      "transcendental's irrationality stays Unknown. The hidden "
                      "suite asserts it resolves.",
        "rationale": "This rival resolves boundedness for the transcendental "
                     "seed yet still leaves irrationality Unknown, i.e. it "
                     "propagates the boundedness relation without the "
                     "equivalence that depends on it. Must reject.",
    },
    {
        "id": "rev-integer-nonodd-drop-even",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_INTEGER_NONODD, _REV_INO_DROP_EVEN),
        "refinement": "Refines to a theory stating evenness as a one-way "
                      "containment, so a whole number that is not odd is never "
                      "recognised as even. The hidden suite asserts that "
                      "recognition.",
        "rationale": "A whole number that is not odd MEETS the defining "
                     "condition of evenness, so evenness must resolve True; "
                     "this rival abstains. Must reject.",
    },
    {
        "id": "pos-integer-nonodd-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _A_DEDUCE_INTEGER_NONODD, _POS_INO_REORDER),
        "rationale": "Structurally-different but CORRECT defining-condition "
                     "impl: the defined membership is recognised before the "
                     "containments it licenses. Closure is order-insensitive, "
                     "so this must verify else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-even-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _A_DEDUCE_EVEN, _POS_EVEN),
        "rationale": "Structurally-different (reverse containment order) but "
                     "CORRECT deduce_even. Straight-line, no invariants, so "
                     "reordering keeps every proof obligation. Must verify else "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-infinite-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _A_DEDUCE_INFINITE, _POS_INF),
        "rationale": "deduce_infinite with the cascade assigned in reverse and "
                     "the seed bound last; closure is order-insensitive. Must "
                     "verify else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-rational-boundedness-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _A_DEDUCE_RATIONAL, _POS_RATIONAL),
        "rationale": "The per-seed boundedness obligation must not pin a "
                     "propagation ROUTE. This variant resolves boundedness "
                     "before membership and reaches the same closed record. Must "
                     "verify else the seed-by-seed clause over-fits an order.",
    },
    {
        "id": "pos-not-rational-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _A_DEDUCE_NOT_RATIONAL, _POS_NOT_RATIONAL),
        "rationale": "A frontier seed's licensed denials, established in the "
                     "reverse order. Must verify else the frontier pins over-fit.",
    },
    # ---- admissibility (must verify) ----
    {
        "id": "admiss-even",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _A_DEDUCE_EVEN, _ADMISS_EVEN),
        "rationale": "Gold body plus Assert(consistent_theory(k)) and the "
                     "witnessed trit asserts inside the impl region. Confirms the "
                     "@Pure closure predicate ADMITS the realised in-domain "
                     "record (no-input precondition). Must verify else "
                     "usage-TOO-STRONG.",
    },
    {
        "id": "admiss-not-even",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _A_DEDUCE_NOT_EVEN, _ADMISS_NOT_EVEN),
        "rationale": "The frontier seed's Unknown pins are jointly establishable "
                     "with the closure theory: a record may leave boundedness "
                     "Unknown. Confirms the Unknown-pinning clauses are "
                     "satisfiable, not contradictory.",
    },
    # ---- uniqueness (expect reject; a verify here would be the defect) ----
    {
        "id": "weak-even-odd",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_EVEN, _WEAK_EVEN_ODD),
        "refinement": "Real _assume_rules has 'even == integer & !odd', so an "
                      "even quantity deduces is_odd=False; the hidden suite "
                      "asserts Symbol('x', even=True).is_odd is False. A faithful "
                      "patch whose engine produced odd=True for an even seed would "
                      "FAIL that assertion, so this rival cannot resolve.",
        "rationale": "REJECT from the consistent_theory clause even=T -> odd=F.",
    },
    {
        "id": "weak-even-noninteger",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_EVEN, _WEAK_EVEN_NONINT),
        "refinement": "An even quantity is an integer, so the real engine gives "
                      "is_noninteger=False. An engine deducing noninteger=True "
                      "for an integer breaks the assumptions consistency the "
                      "suite relies on, so such a patch cannot resolve.",
        "rationale": "REJECT from the consistent_theory clause "
                     "integer=T -> noninteger=F.",
    },
    {
        "id": "weak-infinite-complex",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_INFINITE, _WEAK_INF_COMPLEX),
        "refinement": "Real engine: an unbounded real quantity IS complex; every "
                      "real seed deduces is_complex=True. A patch whose engine "
                      "derived complex=False for a real quantity would contradict "
                      "the real engine on every real seed.",
        "rationale": "REJECT from the consistent_theory clause real=T -> "
                     "complex=T. (validated == the real engine by G-AX.)",
    },
    # ---- sign-neutrality lane: a sign read off unboundedness (expect reject)
    {
        "id": "over-sign-infinite-positive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_INFINITE, _SIGN_INF_POSITIVE),
        "refinement": "Real engine: a quantity known only to be unbounded and "
                      "real leaves is_positive / is_negative / is_nonpositive / "
                      "is_nonnegative all Unknown. An engine that derived a "
                      "strict sign from unboundedness would contradict the "
                      "quantity unbounded in the opposite direction, whose sign "
                      "is the other one; measured, such a rule set makes that "
                      "quantity's assumption set inconsistent, so its patch "
                      "cannot resolve.",
        "rationale": "REJECT from Ensures(Result().positive is None) and "
                     "Ensures(Result().nonnegative is None) on deduce_infinite.",
    },
    {
        "id": "over-sign-infinite-nonnegative",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_INFINITE, _SIGN_INF_NONNEG),
        "refinement": "The weaker form of the same over-reach: only a bound by "
                      "zero on one side is claimed. The real engine leaves that "
                      "Unknown too, and an engine deriving it would again "
                      "contradict the oppositely-unbounded quantity.",
        "rationale": "REJECT from Ensures(Result().nonnegative is None) on "
                     "deduce_infinite (a one-sided bound is no more licensed by "
                     "unboundedness than a strict sign).",
    },
    # ---- partial-domain lane: boundedness resolved for one seed only --------
    {
        "id": "nm-even-drop-finite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_EVEN, _NM_EVEN_DROP_FINITE),
        "refinement": "Leaving boundedness Unknown for an even quantity is the "
                      "PRE-PATCH behaviour; the hidden suite asserts "
                      "Symbol('x', even=True).is_finite is True.",
        "rationale": "REJECT from Ensures(Result().finite is True) AND the theory "
                     "clause rational=T -> finite=T. Must reject (prepatch "
                     "parity).",
    },
    {
        "id": "nm-odd-drop-finite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_ODD, _NM_ODD_DROP_FINITE),
        "refinement": "The hidden suite asserts Symbol('x', odd=True).is_finite "
                      "is True. A knowledge base that bounds only the EVEN seed "
                      "fails it — this is the shape of the 2026-08-15 "
                      "counterexample, whose faithful patch was harness-run to "
                      "resolved=FALSE.",
        "rationale": "REJECT from the per-seed obligation on deduce_odd. Under a "
                     "spec instantiated at the even seed alone this variant "
                     "verified; a verify here is SPEC-TOO-WEAK by partial "
                     "domain.",
    },
    {
        "id": "nm-integer-drop-finite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_INTEGER, _NM_INTEGER_DROP_FINITE),
        "refinement": "The hidden suite asserts is_finite is True for a quantity "
                      "known only to be a whole number (and for the "
                      "nonnegative/nonpositive refinements of it), which a "
                      "parity-only boundedness edge leaves Unknown.",
        "rationale": "REJECT from the per-seed obligation on deduce_integer.",
    },
    {
        "id": "nm-rational-drop-finite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_RATIONAL, _NM_RATIONAL_DROP_FINITE),
        "refinement": "The hidden suite asserts is_finite is True for a quantity "
                      "known only to be rational. This is the weakest bounded "
                      "seed — nothing places it among the whole numbers — so it "
                      "is the sharpest witness that boundedness must follow from "
                      "membership in the rationals itself.",
        "rationale": "REJECT from the per-seed obligation on deduce_rational.",
    },
    {
        "id": "nm-irrational-drop-finite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_IRRATIONAL, _NM_IRRATIONAL_DROP_FINITE),
        "refinement": "The hidden suite asserts is_finite is True for a quantity "
                      "known only to be irrational. Boundedness cannot reach this "
                      "seed through the rationals (the exclusion puts it "
                      "outside them), so it is an independent antecedent.",
        "rationale": "REJECT from the per-seed obligation on deduce_irrational.",
    },
    # ---- frontier overreach lane: boundedness resolved where it must not be --
    {
        "id": "over-frontier-not-rational-unbounded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_NOT_RATIONAL,
                        _OVER_NOT_RATIONAL_UNBOUNDED),
        "refinement": "The hidden suite asserts is_finite is None for a quantity "
                      "known only to be non-rational. Measured 2026-08-15: a rule "
                      "set propagating non-membership backwards to unboundedness "
                      "also makes the real engine raise a contradiction on "
                      "unrelated seeds.",
        "rationale": "REJECT from Ensures(Result().finite is None) on "
                     "deduce_not_rational. Guards the too-strong direction of the "
                     "per-seed class: a spec that only demanded boundedness "
                     "resolve for more seeds would admit resolving it everywhere.",
    },
    {
        "id": "over-frontier-not-irrational-bounded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_NOT_IRRATIONAL,
                        _OVER_NOT_IRRATIONAL_BOUNDED),
        "refinement": "The hidden suite asserts is_finite is None for a quantity "
                      "known only to be non-irrational; a patch resolving it to "
                      "True fails.",
        "rationale": "REJECT from Ensures(Result().finite is None) on "
                     "deduce_not_irrational.",
    },
    {
        "id": "over-frontier-not-even-bounded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_NOT_EVEN, _OVER_NOT_EVEN_BOUNDED),
        "refinement": "The hidden suite asserts is_finite is None for a quantity "
                      "known only to be non-even.",
        "rationale": "REJECT from Ensures(Result().finite is None) on "
                     "deduce_not_even.",
    },
    {
        "id": "over-frontier-not-odd-wholeness",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_NOT_ODD, _OVER_NOT_ODD_WHOLENESS),
        "refinement": "The hidden suite asserts is_even is None and is_integer is "
                      "None for a quantity known only to be non-odd. Reading the "
                      "parity exclusion backwards (not odd => even) contradicts "
                      "it, and would bound a quantity nothing places among the "
                      "whole numbers.",
        "rationale": "REJECT from the Unknown pins on deduce_not_odd. Confirms "
                     "the exclusions are directional in the spec, not biconditional.",
    },
    # ---- completion lane (expect reject): a deduction that never delivers ----
    {
        "id": "diverge-even-selfcall",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_EVEN, _DIVERGE_EVEN),
        "refinement": "The real forward-chaining closure drains a finite fact "
                      "queue and returns, so Symbol('x', even=True).is_finite is "
                      "always answered. A deduction that re-enters itself never "
                      "answers — the query raises — so such a patch cannot "
                      "resolve.",
        "rationale": "REJECT from the deducers' completion demand (MustTerminate "
                     "in the pre-conditions). Every VALUE clause is vacuously "
                     "satisfied by a body that never returns, so this case is the "
                     "only lane that senses the completion property.",
    },
    {
        "id": "diverge-infinite-selfcall",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_INFINITE, _DIVERGE_INF),
        "refinement": "The unbounded-real queries are likewise always answered by "
                      "the real closure. A self-re-entering deduction makes them "
                      "raise instead, so the patch cannot resolve.",
        "rationale": "REJECT from the completion demand on deduce_infinite.",
    },
    {
        "id": "diverge-rational-selfcall",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_RATIONAL, _DIVERGE_RATIONAL),
        "refinement": "Same class on a seed added by the per-seed obligation: the "
                      "rational-seed query is answered by the real closure too.",
        "rationale": "REJECT from the completion demand on deduce_rational. "
                     "Confirms the new deducers carry the obligation as well, "
                     "rather than being value-only clauses a diverging body "
                     "satisfies vacuously.",
    },
    {
        "id": "diverge-not-even-selfcall",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_NOT_EVEN, _DIVERGE_NOT_EVEN),
        "refinement": "A frontier seed whose closed record is almost entirely "
                      "Unknown is the cheapest place for a vacuity escape: a body "
                      "that never returns satisfies thirteen `is None` pins with "
                      "no work done. The real closure answers this query too.",
        "rationale": "REJECT from the completion demand on deduce_not_even.",
    },
    {
        "id": "diverge-even-loop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_EVEN, _DIVERGE_LOOP_EVEN),
        "refinement": "A propagation loop whose guard never changes never drains, "
                      "so no assumption query the suite makes is ever answered; "
                      "the real closure always terminates.",
        "rationale": "REJECT from the completion demand, reached through an "
                     "unbounded LOOP rather than self-re-entry — confirms the "
                     "obligation covers both routes to non-delivery.",
    },
    # ---- clause-level instantiation lane (expect reject): each rival leaves
    #      Unknown the ONE status a clause group of the theory resolves on this
    #      seed and only on this seed. Machine-surveyed: the corresponding rule
    #      sets verified against the fifteen-seed spec and were harness-run to
    #      resolved=FALSE.
    {
        "id": "rev-algebraic-bounded-drop-complex",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_ALGEBRAIC_BOUNDED, _REV_AB_DROP_COMPLEX),
        "refinement": "Refines to a rule theory in which membership of the "
                      "algebraic numbers does not place a quantity among the "
                      "complex ones. The hidden suite asserts that containment "
                      "(test_symbol_noncommutative).",
        "rationale": "On the fifteen membership seeds every algebraic record is "
                     "also real, which forces complexity for an unrelated "
                     "reason, so the containment clause is vacuous there. This "
                     "seed hands boundedness over instead of realness, leaving "
                     "the clause the only route to complexity. Must reject.",
    },
    {
        "id": "rev-not-nonnegative-drop-positive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_NOT_NONNEGATIVE, _REV_NN_DROP_POSITIVE),
        "refinement": "Refines to a theory in which strict positivity is not "
                      "contained in the weak upper region, so refusing that "
                      "region leaves strict positivity Unknown. The hidden "
                      "suite asserts the refusal propagates.",
        "rationale": "REJECT from Ensures(Result().positive is False) on the "
                     "refused-upper-region seed. The surveyed rival that "
                     "deletes the strict-positivity equivalence fails "
                     "test_symbol_falsenonnegative.",
    },
    {
        "id": "rev-real-not-nonnegative-drop-negative",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_REAL_NOT_NONNEGATIVE, _REV_RNN_DROP_NEGATIVE),
        "refinement": "Refines to a theory that never recognises strict "
                      "negativity from a real quantity refused the weak upper "
                      "region, i.e. it drops the equivalence tying the two. The "
                      "hidden suite asserts the recognition.",
        "rationale": "A real quantity that is NOT bounded below by zero is "
                     "strictly below zero; this rival abstains while every "
                     "one-way containment still holds. Must reject.",
    },
    {
        "id": "rev-real-not-positive-drop-nonpositive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_REAL_NOT_POSITIVE, _REV_RNP_DROP_NONPOSITIVE),
        "refinement": "Refines to a theory stating the weak lower region as a "
                      "one-way containment instead of `real & !positive`, so a "
                      "real quantity denied strict positivity is never bounded "
                      "above by zero. The hidden suite asserts it is.",
        "rationale": "REJECT from the defining-condition pin on this seed. The "
                     "surveyed rival weakening that equivalence fails "
                     "test_symbol_falsepositive_real.",
    },
    {
        "id": "rev-real-not-negative-drop-nonnegative",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_REAL_NOT_NEGATIVE, _REV_RNG_DROP_NONNEGATIVE),
        "refinement": "The mirror-image omission: a real quantity denied strict "
                      "negativity is never bounded below by zero. The hidden "
                      "suite asserts it is (test_neg_symbol_nonpositive).",
        "rationale": "REJECT from the defining-condition pin on the "
                     "refused-strict-negativity seed. Both weak regions are "
                     "pinned, so a rival must state both equivalences.",
    },
    {
        "id": "rev-origin-drop-even",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_ORIGIN, _REV_ORIGIN_DROP_EVEN),
        "refinement": "Refines to a theory in which a quantity bounded above "
                      "AND below by zero is not recognised as the origin, so "
                      "its parity, wholeness and boundedness stay Unknown. The "
                      "hidden suite asserts them (test_symbol_zero, "
                      "test_Mul_is_algebraic).",
        "rationale": "Both bounds at once leave exactly one quantity, whose "
                     "whole table is settled; this rival abstains on it. The "
                     "surveyed rule sets that delete the origin's defining "
                     "condition or its parity consequence are resolved=FALSE.",
    },
    {
        "id": "rev-prime-drop-noncomposite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_PRIME, _REV_PRIME_DROP_NONCOMPOSITE),
        "refinement": "Refines to a theory in which the two distinguished "
                      "whole-number classes above zero do not exclude each "
                      "other. The hidden suite asserts the exclusion "
                      "(test_Mul_is_prime_composite).",
        "rationale": "REJECT from Ensures(Result().composite is False) on the "
                     "prime seed. No membership seed is pinned at a prime "
                     "quantity, so the exclusion was unobserved before.",
    },
    {
        "id": "rev-noncomposite-positive-even-drop-prime",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_NONCOMPOSITE_POSITIVE_EVEN,
                        _REV_NPE_DROP_PRIME),
        "refinement": "Refines to a theory that never recognises the smaller "
                      "class from its defining conditions: a strictly positive "
                      "even whole number that is not composite stays Unknown "
                      "instead of resolving. The hidden suite asserts the "
                      "recognition (test_composite).",
        "rationale": "The reverse direction of the same exclusion, on the seed "
                     "that meets its defining conditions. Must reject.",
    },
    {
        "id": "rev-nonzero-drop-real",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_NONZERO, _REV_NZ_DROP_REAL),
        "refinement": "Refines to a theory whose non-zero status drops its "
                      "realness conjunct, so a definitely-non-zero quantity is "
                      "no longer placed on the real line. The hidden suite "
                      "asserts it is (test_symbol_imaginary, "
                      "test_symbol_falsenonnegative).",
        "rationale": "REJECT from Ensures(Result().real is True) on the "
                     "punctured-real-line seed. Two surveyed rule sets take "
                     "exactly this shape and both are resolved=FALSE; neither "
                     "was caught by any membership seed.",
    },
    {
        "id": "pos-prime-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _A_DEDUCE_PRIME, _POS_PRIME_REORDER),
        "rationale": "Structurally-different but CORRECT prime-seed impl: every "
                     "licensed status is established before the seed that "
                     "licenses it. Closure is order-insensitive, so this must "
                     "verify else the new pins over-fit a propagation order.",
    },
    {
        "id": "pos-nonzero-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _A_DEDUCE_NONZERO, _POS_NONZERO_REORDER),
        "rationale": "The same guard on the seed carrying the new record field: "
                     "self-adjointness and orientation first, the seed last. "
                     "Must verify else SPEC-TOO-STRONG.",
    },
    # ---- non-zero status lane (expect reject). The status is pinned per seed in
    #      all thirty-one postconditions, so each of these rivals contradicts a
    #      pin, and the two `claim` cases additionally contradict a clause of the
    #      closure theory. Every value they contradict was read off the real
    #      engine at the modelled reference and re-read identically at the
    #      unmodelled base, so no pin here can turn on a rule the reference
    #      theory does not already hold.
    {
        "id": "nz-even-claim-nonzero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_EVEN, _NZ_EVEN_CLAIM),
        "refinement": "Refines to a rule theory carrying `even -> nonzero`, i.e. "
                      "one that reads distance from the origin off parity alone. "
                      "The hidden suite asserts an even symbol's non-zero status "
                      "stays Unknown (test_symbol_even, test_Mul_is_even_odd).",
        "rationale": "The origin IS an even whole number, so parity cannot place "
                     "a quantity away from it; the closure leaves the status "
                     "Unknown on this seed. REJECT from "
                     "Ensures(Result().nonzero is None) on deduce_even.",
    },
    {
        "id": "nz-origin-claim-nonzero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_ORIGIN, _NZ_ORIGIN_CLAIM),
        "refinement": "Refines to a theory in which a quantity bounded above AND "
                      "below by zero is still away from the origin -- an "
                      "inconsistent assumption set the hidden suite rejects "
                      "(test_symbol_zero).",
        "rationale": "Doubly-bounded by zero is exactly the origin, whose "
                     "non-zero status is denied. REJECT twice over: from "
                     "Ensures(Result().nonzero is False) and from the closure "
                     "clause nonpositive & nonnegative -> !nonzero.",
    },
    {
        "id": "nz-prime-deny-nonzero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_PRIME, _NZ_PRIME_DENY),
        "refinement": "Refines to a theory that denies a strictly positive whole "
                      "number distance from the origin, i.e. drops the "
                      "`positive == nonnegative & nonzero` direction. The hidden "
                      "suite asserts it (test_symbol_positive, test_prime).",
        "rationale": "A strict sign entails distance from the origin. REJECT from "
                     "Ensures(Result().nonzero is True) on the prime seed and "
                     "from the closure clause positive -> nonzero.",
    },
    {
        "id": "nz-odd-drop-nonzero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_ODD, _NZ_ODD_DROP),
        "refinement": "Refines to a theory that never settles the non-zero "
                      "status of a whole number of odd parity, leaving "
                      "`Symbol('x', odd=True).is_nonzero` Unknown where the "
                      "hidden suite asserts True (test_symbol_odd).",
        "rationale": "The too-weak direction of the same class: the record is "
                     "otherwise gold and every clause of the closure still "
                     "holds of it, so only the per-seed pin can catch it. "
                     "REJECT from Ensures(Result().nonzero is True).",
    },
    {
        "id": "nz-real-transcendental-drop-nonzero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_REAL_TRANSCENDENTAL, _NZ_RT_DROP),
        "refinement": "Refines to a theory that abstains on the non-zero status "
                      "of a real transcendental, where the hidden suite asserts "
                      "it resolves (test_symbol_real_false, test_other_symbol).",
        "rationale": "This is the seed the recorded attack lane used: an "
                     "implementation free to differ from gold on this ONE status "
                     "was admitted while the field was carried by a single "
                     "deducer. It is now pinned here, so both directions are "
                     "rejected. REJECT from Ensures(Result().nonzero is True).",
    },
    {
        "id": "pos-real-transcendental-nonzero-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _A_DEDUCE_REAL_TRANSCENDENTAL,
                        _POS_RT_NONZERO_FIRST),
        "rationale": "Over-fitting guard on the attacked seed: the SAME record, "
                     "with the non-zero status and the real line established "
                     "before the seed. Closure is order-insensitive, so this "
                     "must verify else the new pins over-fit a propagation "
                     "order rather than stating the theory.",
    },
    {
        "id": "pos-origin-nonzero-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _A_DEDUCE_ORIGIN, _POS_ORIGIN_NONZERO_FIRST),
        "rationale": "The mirror guard on the one seed that DENIES the status: "
                     "denial first, the two bounds that force it afterwards. "
                     "Must verify else SPEC-TOO-STRONG.",
    },
    # ---- OFF-THE-REAL-LINE lane (expect reject). Each rival is a rule theory
    #      that gets a relation wrong only where the quantity does NOT lie on
    #      the real line, or reads a status off unboundedness or off
    #      order-of-multiplication. Every such relation was vacuous on the
    #      pre-repair observable, so each of these verified before.
    {
        "id": "off-imaginary-claim-finite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_IMAGINARY, _OFF_IMAG_CLAIM_FINITE),
        "refinement": "Refines to a theory that bounds every quantity off the "
                      "real line, so `Symbol('x', imaginary=True).is_finite` "
                      "comes back True where the hidden suite needs Unknown.",
        "rationale": "Failing to lie on the real line says nothing about the "
                     "size of a quantity: a bounded and an unbounded multiple "
                     "of the imaginary unit both satisfy the seed. REJECT from "
                     "Ensures(Result().finite is None).",
    },
    {
        "id": "off-imaginary-claim-transcendental",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_IMAGINARY, _OFF_IMAG_CLAIM_TRANSC),
        "refinement": "Refines to a theory in which nothing off the real line is "
                      "transcendental, so a transcendental multiple of the "
                      "imaginary unit becomes contradictory instead of a record.",
        "rationale": "The imaginary axis carries transcendental and algebraic "
                     "quantities alike, so the divide is not decided by the seed. "
                     "REJECT from Ensures(Result().transcendental is None).",
    },
    {
        "id": "off-imaginary-claim-infinite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_IMAGINARY, _OFF_IMAG_CLAIM_INFINITE),
        "refinement": "Refines to a theory that resolves the unbounded status "
                      "off the real line, where the hidden suite leaves it open.",
        "rationale": "Same class, on the status of being unbounded rather than "
                     "bounded. REJECT from Ensures(Result().infinite is None).",
    },
    {
        "id": "off-imaginary-claim-hermitian",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_IMAGINARY, _OFF_IMAG_CLAIM_HERM),
        "refinement": "Refines to a theory reading self-adjointness off the "
                      "imaginary axis, where the closure abstains.",
        "rationale": "Anti-self-adjointness is forced by the seed; "
                     "self-adjointness is not. REJECT from "
                     "Ensures(Result().hermitian is None).",
    },
    {
        "id": "off-imaginary-transcendental-drop-finite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_IMAGINARY_TRANSCENDENTAL,
                        _OFF_IMAGTR_DROP_FINITE),
        "refinement": "Refines to a theory that bounds the transcendentals only "
                      "where the quantity ALSO lies on the real line, so "
                      "`Symbol('x', transcendental=True, imaginary=True)"
                      ".is_finite` stays Unknown. This is the pre-patch reading "
                      "of the relation, surviving off the line.",
        "rationale": "Transcendence bounds a quantity irrespective of the real "
                     "line; a theory that bounds it only on the line is the "
                     "defect under specification, still present off the line. "
                     "REJECT from Ensures(Result().finite is True) (prepatch "
                     "reading of this record).",
    },
    {
        "id": "off-imaginary-transcendental-claim-hermitian",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_IMAGINARY_TRANSCENDENTAL,
                        _OFF_IMAGTR_CLAIM_HERM),
        "refinement": "Refines to a theory reading self-adjointness off "
                      "transcendence, which does not decide it.",
        "rationale": "REJECT from Ensures(Result().hermitian is None) on the "
                     "bounded off-line record.",
    },
    {
        "id": "off-unbounded-claim-infinite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_UNBOUNDED, _OFF_UNB_CLAIM_INFINITE),
        "refinement": "Refines to a theory in which failing to be bounded and "
                      "being unbounded in the recorded sense are the same "
                      "status, resolving one from the other.",
        "rationale": "The containment between them runs one way only: the "
                     "record's unbounded status is not forced by the denial of "
                     "boundedness. REJECT from Ensures(Result().infinite is "
                     "None).",
    },
    {
        "id": "off-unbounded-drop-integer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_UNBOUNDED, _OFF_UNB_DROP_INTEGER),
        "refinement": "Refines to a theory that does not carry the boundedness "
                      "relation contrapositively, so an unbounded quantity is "
                      "never ruled out of the whole numbers.",
        "rationale": "Every whole number is bounded, so an unbounded quantity is "
                     "none; this rival abstains. REJECT from "
                     "Ensures(Result().integer is False).",
    },
    {
        "id": "off-unbounded-claim-real",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_UNBOUNDED, _OFF_UNB_CLAIM_REAL),
        "refinement": "Refines to a theory placing every unbounded quantity on "
                      "the real line, so an unbounded quantity off that line "
                      "becomes contradictory.",
        "rationale": "Unboundedness does not say WHERE a quantity fails to be "
                     "bounded. REJECT from Ensures(Result().real is None).",
    },
    {
        "id": "off-nonreal-at-origin-drop-real",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_NONREAL_AT_ORIGIN,
                        _OFF_ORIGIN_DROP_REAL),
        "refinement": "Refines to a theory that never concludes non-realness "
                      "from the punctured line, leaving realness Unknown where "
                      "the closure denies it.",
        "rationale": "On the real line the one quantity at no distance from the "
                     "origin IS a whole number, so denying both places the "
                     "quantity off the line. This rival leaves it open while "
                     "every forward containment still holds. REJECT from "
                     "Ensures(Result().real is False).",
    },
    {
        "id": "off-not-antihermitian-claim-composite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_NOT_ANTIHERMITIAN,
                        _OFF_NAH_CLAIM_COMPOSITE),
        "refinement": "Refines to a theory relating one adjointness orientation "
                      "to a membership among the whole numbers, which no "
                      "containment of this theory supports.",
        "rationale": "Denying anti-self-adjointness denies being a non-zero "
                     "multiple of the imaginary unit and nothing else. REJECT "
                     "from Ensures(Result().composite is None).",
    },
    {
        "id": "off-commuting-claim-complex",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_COMMUTING, _OFF_COMM_CLAIM_COMPLEX),
        "refinement": "Refines to a theory reading complexity off "
                      "order-independence under multiplication -- the "
                      "containment run backwards -- so quantities outside every "
                      "numeric set become complex.",
        "rationale": "Complexity entails order-independence, not conversely; "
                     "order-independence alone places a quantity in no set at "
                     "all. REJECT from Ensures(Result().complex is None).",
    },
    {
        "id": "off-noncommuting-drop-complex",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DEDUCE_NONCOMMUTING,
                        _OFF_NONCOMM_DROP_COMPLEX),
        "refinement": "Refines to a theory that drops the contrapositive of "
                      "that containment, so a quantity that does not multiply "
                      "order-independently is never ruled out of the complex "
                      "numbers.",
        "rationale": "Every complex quantity multiplies order-independently, so "
                     "one that does not is not complex. REJECT from "
                     "Ensures(Result().complex is False).",
    },
    {
        "id": "pos-imaginary-real-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _A_DEDUCE_IMAGINARY, _POS_IMAG_REAL_FIRST),
        "rationale": "Over-fitting guard on the off-line record: the SAME "
                     "record, with non-realness established before the "
                     "orientation that forces it. Closure is order-insensitive, "
                     "so this must verify else the new pins over-fit a "
                     "propagation order rather than stating the theory.",
    },
    {
        "id": "pos-imaginary-transcendental-finite-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _A_DEDUCE_IMAGINARY_TRANSCENDENTAL,
                        _POS_IMAGTR_FINITE_FIRST),
        "rationale": "The mirror guard on the record that carries the "
                     "boundedness relation off the real line: boundedness first, "
                     "the membership that forces it afterwards. Must verify else "
                     "SPEC-TOO-STRONG.",
    },
]


# No @ContractOnly axioms (meta.axioms == []) and no A-consumed deep models;
# the deep theory `consistent_theory` is an A-reference validated out-of-band by
# axiom_check.py (G-AX), which the PBT axiom lane does not re-run.
AXIOM_TESTS = []
