"""properties.py — G-PBT falsification battery for sympy__sympy-21596 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct restrictToRealValues`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

Every reject case below is given the STRONGEST tactic body found for it while
authoring (``loom_solve <;> cases imaginaryPart <;> simp [reported, keptToReal,
realIndices, anyVanishes, vanishingSet, Set.ext_iff, Set.diff_eq,
Set.union_diff_distrib, NonDetT.run, NonDetT.pure, pure, bind, NonDetT.bind] <;>
tauto``), not the frozen solution's narrower body. It splits on the shape of the
imaginary part first, so no rival is ever refuted merely because a ``match`` was
left unreduced; it unfolds membership, has set extensionality, the
difference/union laws and the monad's own ``pure``/``bind`` equations available,
and closes with propositional reasoning. What is left over is a residual goal
that is genuinely FALSE.

DEFENDED SURFACE (one contracted method over integer-indexed sets):

  restrictToRealValues (domain, imaginaryPart, denominators, valueOf)
      : IndexReport
      ensures out = .apart (keptToReal imaginaryPart) (.zerosOfAny denominators)
      ensures reported domain valueOf out
            = realIndices domain valueOf imaginaryPart
                \\ anyVanishes valueOf denominators

The four INPUT binders and their observation:
  * ``domain``        — the index set the family ranges over, modeled as
                        ``Set Int``. It enters the answer as the nullary ATOM
                        ``given``, i.e. as ITSELF and not as a set of indices,
                        which is what makes a re-description of the same indices
                        in its place a DIFFERENT answer (see LEAF IDENTITY).
  * ``imaginaryPart`` — WHAT THE ROUTINE HAS BEEN TOLD about the imaginary part,
                        in the two shapes that reach an index assembly at all
                        (see SHAPE FIDELITY): ``zeroThroughout``, the imaginary
                        part settled to be zero at every index at once, so no
                        factor of it is resolved and no list of its factors is
                        even formed; or ``factors gs``, the imaginary part handed
                        over as the LIST of factors its numerator splits into,
                        the value being real at ``n`` iff one of them vanishes
                        there (``anyVanishes valueOf gs``). A factor is carried
                        as ITSELF — an identity-bearing ``Factor`` handle — and
                        NOT as the values it takes, which is what makes another
                        factor of equal value everywhere a DIFFERENT factor (see
                        FACTOR IDENTITY).
  * ``denominators``  — the LIST of denominator factors whose vanishing makes the
                        value undefined (``anyVanishes valueOf denominators``),
                        same carrier. This leg is applied under BOTH shapes.
  * ``valueOf``       — the reading that gives the value a factor takes at an
                        index: ``some q`` where it takes the rational value
                        ``q``, ``none`` where it takes no rational value at all.
                        That reading is TOTAL and EXACT on values — a factor
                        ``n + 1/2`` really does take ``1/2`` at index ``0`` (a
                        value that is neither ``0`` nor an integer), and
                        ``1/n - 1`` really does take no value there — and it is a
                        function OF a factor, so it never determines one.

TWO load-bearing post-images, and the FIRST is the one that carries the
observable this instance is judged on:

  (1) the ASSEMBLY clause — the answer is the description
      ``keptToReal imaginaryPart`` taken apart-from the per-factor zero
      collection of ``denominators``, where the keep leg follows the SHAPE the
      imaginary part arrived in: the index domain ITSELF (``given``) where it is
      settled zero throughout, and that domain kept-down-to the per-factor zero
      collection of the listed factors where it arrived as factors. It fixes
      WHICH pieces are combined, in WHICH roles, in WHICH order, WHICH SHAPE
      calls for a keep node at all, it fixes each collection's FACTOR LIST — its
      length, its order, and each member as the FACTOR HANDED IN rather than as
      whatever values that member takes — because resolving the listed factors
      ONE AT A TIME is what turns a factored imaginary part into named indices
      instead of an unresolved condition, and where a factor is what a
      description names, the factor itself is what the description carries; and
      — since ``given`` is an atom and not a payload — it fixes that NOTHING
      stands between the domain and the keep.
  (2) the INDEX clause — reading the description back over the domain it was
      assembled against, and over the value reading its factors were handed
      with, gives
      ``realIndices domain valueOf imaginaryPart
          \\ anyVanishes valueOf denominators``,
      i.e. ``domain \\ anyVanishes valueOf denominators`` where the imaginary
      part is settled zero throughout and
      ``(domain ∩ anyVanishes valueOf gs) \\ anyVanishes valueOf denominators``
      where it arrived as ``factors gs``.
      This is the membership-level consequence of (1) (and, being a consequence,
      is not an independent constraint); it is the leg ``conformance_check.py``
      probes point-by-point.

Why (1) at all — an EXACT set equality on indices is not enough. The answer is
handed back to the caller as an index-set DESCRIPTION, and the caller reports it:
for the issue's own family the answer asked for is the two-element enumeration
``{-1, 1}``, while "the integers at which ``(n-1)(n+1)`` vanishes" describes the
same two indices and names neither. Both descriptions have identical membership,
so an index-only post-image cannot tell them apart, and a rival that assembles
the second one satisfies clause (2) exactly. That is not hypothetical: with the
factor list collapsed to one product factor the real callees answer
``ConditionSet(n, Eq((n-1)*(n+1), 0), Integers)`` where the desired behaviour
answers ``FiniteSet(-1, 1)``, and the failing test compares descriptions, so it
still fails. Clause (1) is what makes that difference observable; every reject
case below is measured against the real callees (see REFINEMENT EVIDENCE).

SHAPE FIDELITY — why the imaginary part is a TWO-SHAPE INPUT and not a factor
list, and what the keep leg is allowed to depend on.
The modeled routine settles the imaginary part BEFORE any index set is put
together, and the outcome of that settling decides whether a keep leg is built at
all. Read first-hand from the modeled source, the branch that reaches the changed
lines is::

    if im.is_zero:
        # allow re-evaluation
        # of self in this case to make
        # the result canonical
        pass
    elif im.is_zero is False:
        return S.EmptySet
    elif ifree != {n}:
        return None
    else:
        ...
        base_set &= _solution_union(Mul.make_args(numer(im)), n)
    base_set -= _solution_union(denoms(f), n)
    return imageset(lam, base_set)

so exactly two outcomes reach an assembly, and they reach it in DIFFERENT shapes:

  * settled zero at every index — the keep step is SKIPPED (the branch body is
    ``pass``, and its own comment says the point of skipping is to let the family
    be re-evaluated into its canonical form). No factor of the imaginary part is
    resolved, no list of its factors is formed, and the index domain reaches the
    denominator step UNNARROWED. The changed denominator line is still executed,
    so this shape is inside the modeled frame and not out of scope.
  * not settled either way, with the imaginary part depending on the index alone
    — the numerator's factors are handed over and resolved one at a time, and the
    index domain is kept down to their zeros before the denominator step.

The other two outcomes return BEFORE any changed line (``S.EmptySet`` when the
imaginary part is settled nonzero, ``None`` when it involves more than the index
variable), so they belong to the unchanged frame and the modeled surface does not
speak for them; ``imaginaryPart`` therefore carries the two shapes that do reach
the assembly, and carries them as an INPUT — the shape is read off the imaginary
part, never chosen by the answer.

Two shapes, two assemblies. A rival that narrows the domain on the settled-zero
shape ANYWAY — by a collection that in fact excludes no index, which is what the
real callees build for an identically zero numerator (measured: the node built
for it is ``UniversalSet()``) — keeps every index the desired behaviour keeps and
still hands the callees a different object. Measured on the family
``imageset(Lambda(n, n/2), Intersection(S.Integers, Interval(0, 5),
evaluate=False))``, whose imaginary part is settled zero: the desired behaviour
answers ``FiniteSet(0, 1/2, 1, 3/2, 2, 5/2)`` and the narrowing counterpart
answers ``ImageSet(Lambda(n, n/2), Range(0, 6, 1))`` — the same six members, a
different object, because narrowing re-evaluates the unevaluated base
intersection. Clause (1) is what makes the two shapes' assemblies different
answers rather than two spellings of one answer, and three reject cases live in
this space (``weak-keeps-when-settled-zero``,
``weak-ignores-the-settled-shape``, ``weak-swaps-the-two-shapes``); the positive
control ``pos-keep-leg-by-shape`` bounds it from the other side.

LEAF IDENTITY — why the domain is an ATOM and the description algebra is CLOSED.
Clause (1) is an equation between DESCRIPTIONS, so its strength is bounded by
what a description can distinguish. If the domain entered the answer as a
payload of indices (``given (s : Set Int)``), then — because a set of integers is
extensional — any re-description holding the same indices would BE the same leaf:
``given ((domain ∩ Z) ∪ (domain \\ Z)) = given domain`` is a theorem, so a rival
that masks the domain with a condition excluding nothing would satisfy clause (1)
while assembling a different object out of the real callees (an ``Intersection``
or a ``Union`` over a ``Complement`` where the test asserts a plain
``ConditionSet``/``FiniteSet``, measured NOT to resolve). Two changes close that:

  * ``given`` is NULLARY. It denotes the index domain handed in, itself; no
    description of the same indices can be substituted for it, because a
    description of the same indices is not the constructor ``given``.
  * the algebra is CLOSED over the operations the routine's callees can perform:
    ``noIndices``, ``either`` and ``otherIndices`` join ``zerosOfAny``, ``meet``
    and ``apart``, so the masked, split, complemented and enlarged-then-cut-back
    reshapes are all EXPRESSIBLE descriptions — and then EXCLUDED by name,
    rather than being unrepresentable (which would leave clause (1) silent about
    them, and the spec silently weaker than it looks).

Three reject cases below live exactly in this space (``weak-masks-the-domain-leaf``,
``weak-splits-the-domain-leaf``, ``weak-echoes-by-de-morgan``), and all three are
measured to produce an object the failing test does not assert.

FACTOR IDENTITY — the SAME argument, one level down, on a collection's members.
Clause (1) bounds what it can distinguish by what a ``zerosOfAny`` payload can
distinguish, and that is the second place the bound bites. If a factor entered
the answer as the FUNCTION giving its value at each index
(``zerosOfAny (gs : List (Int → Option Rat))``), then — because a function is
extensional — any re-presentation of a factor taking the same value at every
index would BE the same payload member: on that carrier
``gs.map (fun g k => if g k = some 0 then some 0 else g k) = gs``
is PROVABLE (``funext``/``by_cases``), so a rival that hands each leg's list to
the callees re-presented factor by factor satisfies clause (1) VERBATIM. In the
repository a factor is an expression, MANY expressions take the same value at
every index (``n**2 - n/2 - 1/2``, ``(n-1)*(2*n+1)/2`` and
``n**2 - n/2 - 1/2 + 0`` — measured value-identical over the probed integers and
three different objects by ``srepr``), and where a factor is unsolvable the node the
real callees build EMBEDS THE FACTOR, so those rivals answer a different object
with identical membership and the failing test's ``==`` fails. Measured with the
harness on that shape: FAIL_TO_PASS 0/1 (``test_imageset_intersect_real``) with
PASS_TO_PASS 46/46. Two changes close it, mirroring the leaf:

  * a factor is an identity-bearing ``Factor``. Its values are not part of it;
    they are read off it by ``valueOf``, so a factor of equal value everywhere is
    a DIFFERENT factor, and no ``Factor`` can be manufactured out of the values
    any factor takes (the handle exposes nothing else).
  * the value reading is a SEPARATE input (``valueOf``), so clause (2) keeps its
    full extensional strength — the surviving indices are still pinned exactly —
    while clause (1) pins the factors themselves.

Two reject cases live exactly in this space (``weak-represents-a-factor``,
``weak-represents-a-denominator``), one per leg, because the node that embeds a
factor is emitted for either list. Both are measured to produce an object the
failing test does not assert. The two positive controls
``pos-pass-factors-through`` and ``pos-name-both-collections`` bound the strictness
from the other side: passing the very factors handed in, however they are named
or re-bound on the way, still verifies.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME-MUTATION — VACUOUS. The nagini class exists because an input carries a
    fractional heap permission an impl can overwrite (the sibling's in-place
    write back into the read-only index/base collection under half-permission).
    This backend is referentially transparent and the method declares NO ``mut``
    binder among its parameters (``domain``, ``imaginaryPart``, ``denominators``,
    ``valueOf`` are immutable values; the ``mut`` local is a fresh result): there
    is no heap, no aliasing, no read-only input to overwrite and no substitute
    probe. Not fabricated.
  * DIVERGENCE / NON-TERMINATION — the nagini sibling carries NO
    ``diverge-*``/``nonterm-*`` case (its totality-shaped attacks are the
    per-index over/under-keep rivals, re-sited below), so there is nothing to
    PORT. Nothing to ship here either, and the reason is a TOOLING limit, not a
    spec hole: this bundle runs under
    ``set_option loom.semantics.termination "total"``, so the verifier discharges
    a termination obligation and a diverging impl is genuinely REJECTED rather
    than verifying vacuously. Measured (a ``while True do pure ()`` prefix
    spliced at the top of the frozen impl region, frozen proof body): exit 1,
    ``error: Decreasing annotations are required in total correctness
    semantics``. So the class is on the RIGHT side of the spec here. What blocks
    shipping it as a reject case is the witness requirement: the diverging
    module does not ELABORATE at all (the same decreasing-annotation error is a
    hard error in the module itself), so a witness cannot hold of the rival and
    the gate would record ``witness-unproven`` — an inconclusive outcome, not a
    pass. There is no ``witness_reference`` route either, since the reference
    replaces the GOLD-side subject, not the rival-side one. Recorded as a
    carrier/tooling limit on the reject lane, with the disposition "correctly
    rejected by the spec, not shippable as a case".
  * PARTIAL-DOMAIN / VALUE — APPLIES, and now on two axes. The nagini rivals
    partition into "drops the keep (real-index) conjunct" and "drops the drop
    (singular) conjunct"; on this carrier those are the two legs of the assembly,
    attacked by ``weak-drops-keep-leg`` and ``weak-drops-apart-leg``. A third
    rival (``weak-ignores-domain``) attacks the ``domain`` binder, which this
    carrier makes independently observable; a fourth
    (``weak-guards-on-one-factor``) is the class in its GUARDED form (correct
    assembly on most inputs, the keep leg silently skipped on the sub-domain
    where the factor list is a singleton); and the SHAPE of the imaginary part is
    a second partial-domain axis of its own, since a rival may be right on one
    shape and wrong on the other — ``weak-keeps-when-settled-zero`` and
    ``weak-ignores-the-settled-shape`` are correct wherever the imaginary part
    arrives as factors and wrong where it is settled zero, and
    ``weak-swaps-the-two-shapes`` trades the two shapes' assemblies.
  * POSITIONAL / BOUNDARY rivals — the POSITIONAL FORM is inexpressible, the
    WRONGNESS is not. The sibling models a backward index LOOP and mishandles the
    FIRST element; there is no loop step here to index off. But this carrier has
    its own boundary tokens — the two factor LISTS and the two roles they play,
    and the two SHAPES and the assemblies they call for — and swapping either
    pair is a one-token error with a real consequence:
    ``weak-swaps-the-two-collections`` keeps the domain down to the DENOMINATOR
    zeros and removes the REAL-INDEX zeros, and ``weak-swaps-the-two-shapes``
    narrows on the shape that calls for no narrowing and leaves the other alone.
    Both are refuted by the assembly clause naming which list, and which shape,
    fills which role.
  * TWO-STEP (second modeled function) rivals — VACUOUS here. The nagini sibling
    contracts a SECOND function (a two-step intersect-then-difference variant)
    and attaches its own positive control + drop-collapse rival to it. This
    bundle models the single functional core as one method; the two-step
    difference-collapse bug is the SAME wrongness as dropping the apart leg,
    already carried by ``weak-drops-apart-leg``. Subsumed.
  * UNGROUNDED-ORACLE ECHO — APPLIES, and it is the class that matters most here,
    because it is the shape a prior audit used to refute the earlier
    index-set-only spec, and its LEAF and MEMBER variants are the shapes that
    refuted the earlier extensional ``given (s : Set Int)`` leaf and the earlier
    extensional ``Int → Option Rat`` factor payload. All are shipped:
    ``weak-echoes-by-de-morgan`` re-derives the surviving indices out of the
    post-image's own vocabulary (complement / union / complement) so that clause
    (2) holds of it by construction while it performs none of the assembly,
    ``weak-masks-the-domain-leaf`` keeps the whole assembly and only re-describes
    the domain leaf as "the indices that either do or do not make some listed
    factor vanish", and ``weak-represents-a-factor`` /
    ``weak-represents-a-denominator`` keep the whole assembly and only re-present
    each of a leg's members as another factor. Under an index-only post-image the
    first is indistinguishable from the desired behaviour; under an EXTENSIONAL
    leaf the second is literally EQUAL to it; under an EXTENSIONAL factor payload
    the last two are literally EQUAL to it. The echo has a SHAPE-level form too:
    ``weak-keeps-when-settled-zero`` narrows the settled-zero shape by a
    collection that excludes no index, so it keeps exactly the right indices
    while describing them by an assembly the routine does not perform. Here
    clause (1) over the atom, over identity-bearing factors and over the two
    shapes rejects all five, and each is measured to answer a different object
    from the one the desired behaviour answers.
  * ECHO OF THE VALUE READING — the specifically NEW shape this carrier admits,
    and it is refused by the carrier itself rather than by a clause. A rival
    cannot build a ``Factor`` out of ``valueOf``: the handle carries only its
    identity, and the values are reached through a function OF it, so there is no
    term of type ``Factor`` derivable from the values that is not already one of
    the factors handed in. Probed while authoring, in the two shapes available:
    fabricating a leg's single member from the whole list
    (``⟨gs.foldl (fun a g => a + g.ident) 0⟩``) and re-minting each member
    from its own identity plus an offset — both REJECTED (exit 1, real
    obligations). The no-op re-mint (each member from its own identity, offset
    zero) is shipped as ``pos-pass-factors-through`` and VERIFIES, so the
    rejection tracks whether the factor handed in is the factor described, not
    whether the impl re-bound it.
  * ECHO OF THE SHAPE — the same refusal one level up: a rival cannot recover
    ``imaginaryPart``'s shape from the indices it would produce, because the two
    shapes are DIFFERENT CONSTRUCTORS of an inductive input rather than two
    values of one payload (a ``zeroThroughout`` input is not the ``factors``
    input whose list vanishes everywhere, even though the two keep the same
    indices). What a rival CAN do is dispatch on the shape and assemble the wrong
    thing for it, which is exactly what the three shape rivals do.

THE WITNESS ON THIS CARRIER. The output is an ``IndexReport`` whose payloads are
lists of ``Factor``, and the method takes a function argument, so a witness
reaches the extracted program through Velvet's extractor
(``extract_program_for`` gives ``restrictToRealValuesExec = NonDetT.run ∘
restrictToRealValues``, and ``NonDetT.run (pure x) = DivM.res x``) and states a
DESCRIPTION INEQUALITY at concrete inputs (``≠ DivM.res (the post-image
description)``). The post-image side is spelled out with explicit constructors —
``IndexReport.given`` where the witness hands in ``ImaginaryPart.zeroThroughout``
and ``IndexReport.meet IndexReport.given (IndexReport.zerosOfAny gs)`` where it
hands in ``ImaginaryPart.factors gs`` — so no witness has to unfold
``keptToReal`` or reason about what a factor evaluates to; ``simp`` (given the
monad's own ``pure``/``bind`` equations, which also reduce the shape ``match`` at
a literal input) then separates the two descriptions structurally: different
constructors, the same constructor holding lists of different length, or
same-length lists holding different ``Factor`` handles. Every witness uses
concrete literal inputs (no ``opaque`` term, so no witness head binds anything
and the consistency probe is vacuous); no ``sorry``/``admit``/``native_decide``/
``axiom`` appears; and the snippet is checked in a file whose ``prove_correct``
block has been stripped, so no tactic script can mask the verdict. Each was
confirmed with real builds to (1) elaborate against its rival (exit 0) and (2)
FAIL against the frozen solution (exit 1, on the SEMANTIC ground that ``simp``
proves the frozen impl produces exactly the claimed description, leaving
``⊢ False``).

FORGERY-CHECKED. Reading a gold-side failure as "semantic" is not evidence on its
own, so a witness is also rebuilt with its claim FLIPPED (``≠`` → ``=``:
asserting the frozen impl DOES produce that description at that input): the
flipped claim must VERIFY against the frozen solution (exit 0) and FAIL against
its rival (exit 1), which shows gold's exit code tracks WHAT IS CLAIMED rather
than the witness's syntactic shape. On the present carrier that control was
re-run for three representative cases — one carried-over leg rival
(``weak-drops-keep-leg``), one identity rival (``weak-masks-the-domain-leaf``)
and one shape rival (``weak-keeps-when-settled-zero``) — covering all three
witness shapes (a structural constructor difference, a leaf difference, and a
settled-zero input). The remaining witnesses' flipped controls were measured on
the earlier carrier of this bundle and are NOT re-measured here; what the gate
itself re-checks for every case, every run, is the two-sided discrimination
(elaborates against the rival, fails against gold).

BINDER / CLAUSE COVERAGE — fifteen reject cases, no two refuted by the same part
of the post-image:
  * ``weak-drops-keep-leg``      — the keep leg is absent under BOTH shapes.
    Exercises the imaginary part's ROLE. Witness
    ``(univ, factors [f₀], [], nowhere)``: the rival's answer is
    ``apart given …`` where the post-image's is ``apart (meet …) …``.
  * ``weak-drops-apart-leg``     — the ``apart`` leg is absent. Exercises
    ``denominators``' ROLE. Witness ``(univ, factors [], [f₀], nowhere)``: top
    constructor ``meet`` vs ``apart``.
  * ``weak-collapses-factor-list`` — both legs present, both roles right, the
    listed factors replaced by a single factor built out of them. Exercises the
    per-factor structure, which no membership-level clause can see. Witness
    ``(univ, factors [f₀, f₁], [], pair)``: a one-element list against a
    two-element one.
  * ``weak-represents-a-factor`` — both legs present, both roles right, the keep
    leg's list LENGTH and ORDER right, and each member replaced by another
    factor. Exercises the per-member IDENTITY of the keep leg's collection, which
    no clause over the members' VALUES can see. Witness
    ``(univ, factors [f₀], [], nowhere)``: ``zerosOfAny [f₁]`` against
    ``zerosOfAny [f₀]``.
  * ``weak-represents-a-denominator`` — the same, on the apart leg, because the
    node that embeds a factor is emitted for either list. Witness
    ``(univ, factors [], [f₀], nowhere)``.
  * ``weak-merges-the-two-collections`` — the keep leg is handed the listed
    factors ``++ denominators`` (an OVER-approximation of the real-index
    collection that the following apart leg removes again, so the surviving
    indices are unchanged). Exercises the CONTENT of the keep leg's list.
    Witness ``(univ, factors [], [f₀], nowhere)``: ``[] ++ [f₀]`` against ``[]``.
  * ``weak-swaps-the-two-collections`` — the two lists trade roles. Exercises
    which binder fills which role. Witness ``(univ, factors [f₀], [], nowhere)``.
  * ``weak-guards-on-one-factor`` — correct assembly except on the sub-domain
    where the listed factors are a singleton, where the keep leg is skipped.
    Exercises the post-image on a partial domain rather than on every input.
    Witness ``(univ, factors [f₀], [], nowhere)``.
  * ``weak-masks-the-domain-leaf`` — the whole assembly is performed, and the
    domain LEAF is replaced by "the indices that either do or do not make some
    listed factor vanish" — the same indices, described differently. Exercises
    the ATOM: under an extensional leaf payload this rival is EQUAL to the
    post-image. Witness ``(univ, factors [f₀], [], nowhere)``: leaf ``meet …`` vs
    ``given``.
  * ``weak-splits-the-domain-leaf`` — the domain leaf is split into the indices
    that do and do not make a listed factor vanish and the two halves are put
    back together. Exercises the ATOM from the other side (a union rather than a
    mask). Witness ``(univ, factors [f₀], [], nowhere)``.
  * ``weak-echoes-by-de-morgan`` — no assembly at all: the surviving index set is
    re-derived from the post-image's own vocabulary as
    ``otherIndices (either (otherIndices given) (either (otherIndices R) D))``.
    Exercises clause (1) alone (clause (2) holds of it by construction, under
    BOTH shapes). Witness ``(univ, factors [f₀], [], nowhere)``: constructor
    ``otherIndices`` vs ``apart``.
  * ``weak-ignores-domain`` — the assembly starts from "every index"
    (``otherIndices noIndices``) instead of the given domain. Exercises
    ``domain``. Witness ``(∅, factors [], [], nowhere)``.
  * ``weak-keeps-when-settled-zero`` — the whole assembly is performed under both
    shapes, and the settled-zero shape is narrowed by a collection that excludes
    no index (the node the real callees build for an identically zero numerator).
    Exercises the SHAPE, and only in its assembly: clause (2) holds of it
    exactly. Witness ``(univ, zeroThroughout, [], nowhere)``: keep leg
    ``meet given (otherIndices noIndices)`` vs ``given``.
  * ``weak-ignores-the-settled-shape`` — the settled-zero shape is treated as an
    EMPTY factor list, i.e. resolved by the same helper with nothing to resolve.
    Exercises the SHAPE on both clauses (an empty collection keeps nothing).
    Witness ``(univ, zeroThroughout, [], nowhere)``.
  * ``weak-swaps-the-two-shapes`` — the two shapes' assemblies trade places: the
    settled-zero shape is narrowed and the factored shape is not. Exercises which
    shape calls for which assembly. Witness
    ``(univ, factors [f₀], [], nowhere)``.
Across the fifteen witnesses ``domain`` ranges over {univ ×14, ∅},
``imaginaryPart`` over {``factors [f₀]`` ×8, ``factors []`` ×4,
``factors [f₀, f₁]``, ``zeroThroughout`` ×2}, ``denominators`` over
{[] ×12, [f₀] ×3} and ``valueOf`` over {the nowhere-vanishing reading, the
reading vanishing at 1 and at -1}, so no binder is held fixed, and the probed
inputs include both degenerate list extremes (empty and two-element) and BOTH
shapes of the imaginary part.

REFINEMENT EVIDENCE (why each reject case is a WRONG impl and not merely a
different one). Every rival's assembly was replayed through the REAL callees
(``solve_linear`` / ``numer`` / ``denoms`` / ``Union`` / ``FiniteSet`` /
``ConditionSet`` / ``&`` / ``-`` / ``imageset``) on all seven families the failing
test asserts, and compared to the objects it asserts. The frozen assembly matches
all 7; every rival below fails at least one (families numbered as in the test's
assertion order):

  rival                            fails family
  weak-drops-keep-leg              1,2,3,4,5,6,7
  weak-drops-apart-leg             5,6,7
  weak-collapses-factor-list       1,2,3,5,6,7
  weak-represents-a-factor         4
  weak-represents-a-denominator    (see below)
  weak-merges-the-two-collections  7
  weak-swaps-the-two-collections   1,2,3,4,5,6,7
  weak-guards-on-one-factor        4
  weak-masks-the-domain-leaf       4
  weak-splits-the-domain-leaf      4
  weak-echoes-by-de-morgan         1,2,3,4,5,6,7
  weak-ignores-domain              3  (the ``S.Naturals0``-indexed family)
  weak-swaps-the-two-shapes        1,2,3,4,5,6,7 (on the factored shape it never
                                   keeps the domain down to the real-making
                                   indices, the same answer as dropping the keep
                                   leg)
  weak-keeps-when-settled-zero     (settled-zero shape; see below)
  weak-ignores-the-settled-shape   (settled-zero shape; see below)

so each one's faithful counterpart would NOT resolve. The per-case ``refinement``
fields name the specific object each rival produces where the test asserts
another.

The three cases whose argument is NOT a measured F2P family, stated for what each
one is:

  * ``weak-represents-a-denominator`` — SYMMETRY. Measured on the asserted
    families: the only ``n``-dependent denominator that reaches the
    factor-embedding node is family 7's, whose family asserts ``S.EmptySet`` (so
    the embedded syntax is washed out), and a constant denominator gives an empty
    node (measured: the node built for the constant denominator ``2`` IS
    ``S.EmptySet``) — so today's F2P suite does not happen to OBSERVE denominator
    syntax. The node that embeds a factor is emitted for EITHER list by the one
    helper both legs call, so a spec that pinned member identity on the keep leg
    only would be asymmetric against the shared helper, and its faithfulness
    would rest on which families the suite happens to assert.
  * ``weak-keeps-when-settled-zero`` — MEASURED OBJECT DIVERGENCE on a
    constructed family of the settled-zero shape, not a measured F2P failure.
    ``FiniteSet(0, 1/2, 1, 3/2, 2, 5/2)`` (desired) against
    ``ImageSet(Lambda(n, n/2), Range(0, 6, 1))`` (narrowing counterpart) for
    ``imageset(Lambda(n, n/2), Intersection(S.Integers, Interval(0, 5),
    evaluate=False))``, as recorded under SHAPE FIDELITY, together with the
    modeled source's own reason for skipping the keep step there ("allow
    re-evaluation of self in this case to make the result canonical"). No claim
    is made here about whether the asserted families cover that shape.
  * ``weak-ignores-the-settled-shape`` — DERIVED from the shared helper's own
    definition rather than replayed: the helper unions one contribution per
    listed factor, so handed the EMPTY list it answers the empty set, and a keep
    step against it leaves the empty base set, i.e. an empty family where the
    desired behaviour answers the family's canonical form. This one also breaks
    clause (2) (it keeps no index at all), so it is the weakest of the three to
    rely on and the easiest to see.

SPEC-STRENGTH PROBES run and deliberately NOT shipped as cases:
  * REASSOCIATING the legs — ``meet (keptToReal …) (apart … …)``-style
    regroupings. Rejected by clause (1) (exit 1, real obligation), so the spec is
    strong here; but replayed through the real callees the corresponding
    regrouping matches all seven asserted objects, i.e. its counterpart WOULD
    resolve. It is therefore a CONSERVATIVE rejection, not a wrong impl, and
    shipping it with a "would not resolve" refinement would be a false claim.
    Recorded here so the over-strict direction of clause (1) is visible rather
    than hidden: the clause pins one assembly, and a caller-visible-equivalent
    regrouping is refused along with the harmful ones.
  * Appending a never-vanishing factor to a leg's list — rejected by clause (1),
    and its counterpart also resolves (the extra factor's zero set is empty), so
    likewise conservative and not shipped.
  * Taking the domain apart from NOTHING (``apart given noIndices`` as the leaf,
    then the normal assembly) — rejected by clause (1) on a real obligation, but
    measured to resolve: the real set algebra simplifies ``X - EmptySet`` to
    ``X``, so the object built is the asserted one on all seven families. A third
    conservative rejection, recorded rather than shipped. It is the reason the
    leaf cases that ARE shipped were each measured individually instead of being
    assumed harmful because they touch the leaf.
  * RE-PRESENTING a factor the real callees can SOLVE. Clause (1) refuses a
    re-presented member of either list regardless of whether the callees name the
    index it contributes; where they DO, the node they emit is the naked index and
    carries no syntax (measured: the factors ``n - 1``, ``2*n - 2``, ``1 - n``
    and ``n/3 - 1/3`` all build the SAME object, ``FiniteSet(1)``), so such a
    counterpart would resolve. That is the fourth conservative direction, and it
    is the price of an obligation stated on the members rather than on the branch
    the callees happen to take for them: the alternative — pinning identity only
    where the callees embed the factor — would make the spec's strength depend on
    a case split the caller cannot see, and would leave the same hole open on
    every family whose factors the callees cannot solve. Recorded, not shipped:
    ``weak-represents-a-factor``, which IS shipped, re-presents a member the
    callees cannot solve, and is measured not to resolve.
  * Correct reshapes that DO verify, beyond the two structural positive controls:
    naming both ``zerosOfAny`` nodes before combining them, hoisting the keep
    node, and reading the keep leg straight off the shape
    (``keptToReal imaginaryPart``) — all shipped below.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the ``pure``
region's ``vanishingSet`` / ``anyVanishes`` / ``IndexReport`` / ``reported`` /
``ImaginaryPart`` / ``keptToReal`` / ``realIndices`` are deep-model references
validated by G-AX, not consumed contracts), and the gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-21596"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the code lines of the frozen `do` block, wholly
# ---- inside the one `-- impl-start` / `-- impl-end` region and unique in the
# ---- file (both facts asserted at load by _swap). Every variant reshapes
# ---- exactly this block. The comment lines above it are left untouched. ----
_IMPL = (
    "    let mut acc : IndexReport := .given\n"
    "    acc := match imaginaryPart with\n"
    "           | .zeroThroughout => acc\n"
    "           | .factors gs => .meet acc (.zerosOfAny gs)\n"
    "    acc := .apart acc (.zerosOfAny denominators)\n"
    "    return acc\n"
)

# ---- the frozen `prove_correct` tactic body. A positive control, the
# ---- admissibility assert that leaves a residual goal the frozen script no
# ---- longer closes, or a RIVAL being given its best shot may RETUNE this body
# ---- (it is elided from the consumer spec view) WITHOUT touching the spec or
# ---- dropping the obligation — the `prove_correct restrictToRealValues by`
# ---- header statement stays byte-identical. Unique in the file. ----
_PROOF = (
    "prove_correct restrictToRealValues by\n"
    "  loom_solve <;> cases imaginaryPart <;>\n"
    "    simp [reported, keptToReal, realIndices]\n"
)

# ---- the strongest tactic body found for a rival while authoring: the shape of
# ---- the imaginary part split on FIRST (so no rival is refuted merely because a
# ---- `match` was left unreduced), membership unfolded, set extensionality and
# ---- the difference/union laws available, the monad's own `pure`/`bind`
# ---- equations available (which also reduce any sequencing residue a
# ---- statement-level `if` leaves behind), and propositional closure at the end.
# ---- Every reject case is refuted WITH all of this available, so no rejection
# ---- rests on a weak script. ----
_STRONG = (
    "prove_correct restrictToRealValues by\n"
    "  loom_solve <;> cases imaginaryPart <;>\n"
    "    simp [reported, keptToReal, realIndices, anyVanishes, vanishingSet,\n"
    "          Set.ext_iff, Set.diff_eq, Set.union_diff_distrib,\n"
    "          NonDetT.run, NonDetT.pure, pure, bind, NonDetT.bind] <;>\n"
    "    tauto\n"
)


def _swap2(a_old, a_new, p_old, p_new):
    """Reshape the impl region AND retune the prove_correct tactic body."""
    return _swap(_swap(_BASE, a_old, a_new), p_old, p_new)


def _rival(impl, proof=_STRONG):
    """A rival module: the impl region reshaped, and the tactic body retuned to
    the strongest one available (the rival's best shot)."""
    return _swap2(_IMPL, impl, _PROOF, proof)


# ---- witness builder. The output is an `IndexReport` (no `DecidableEq` on the
# ---- report: it holds lists of `Factor`), so the refutation is a DESCRIPTION
# ---- INEQUALITY reached through the extractor. `simp` separates the rival's
# ---- description from the post-image's structurally — a different constructor,
# ---- the same constructor holding lists of different length, or same-length
# ---- lists holding different `Factor` handles — so nothing has to be decided
# ---- about what a factor evaluates to. `ims` is the imaginary part the witness
# ---- hands in: a Lean `List Factor` literal (the part arrives AS those factors)
# ---- or None (it is settled zero at every index). The post-image side is
# ---- spelled out with explicit constructors for that shape, so no witness
# ---- unfolds `keptToReal`. Note that the post-image description contains NO set
# ---- payload and NO value reading at all: the domain enters it as the atom
# ---- `IndexReport.given` and the values are read separately, so `dom` and `val`
# ---- are present in the claim only as the method's arguments. The simp set
# ---- carries the monad's own `pure`/`bind` equations, which reduce both the
# ---- extractor's plumbing and the shape `match` at a literal input; it changes
# ---- only which normal form is reached, never what is claimed (the same claim
# ---- is used against gold, where it FAILS).
def _wit(dom, ims, dens, val):
    if ims is None:
        im_arg = "ImaginaryPart.zeroThroughout"
        kept = "IndexReport.given"
    else:
        im_arg = f"(ImaginaryPart.factors {ims})"
        kept = ("(IndexReport.meet IndexReport.given\n"
                f"             (IndexReport.zerosOfAny {ims}))")
    return (
        "extract_program_for restrictToRealValues\n\n"
        "example :\n"
        f"    restrictToRealValuesExec {dom} {im_arg} {dens} {val}\n"
        "      ≠ DivM.res (IndexReport.apart\n"
        f"          {kept}\n"
        f"          (IndexReport.zerosOfAny {dens})) := by\n"
        "  unfold restrictToRealValuesExec restrictToRealValues\n"
        "  simp [NonDetT.run, NonDetT.pure, pure, bind, NonDetT.bind]\n"
    )


# Concrete factor literals used by the witnesses. On this carrier a factor is an
# identity-bearing handle, so a literal is a handle and says nothing at all about
# values — which is the point: every witness below separates descriptions by their
# FACTORS and their SHAPE, never by arithmetic.
_F0 = "[(⟨0⟩ : Factor)]"
_TWO = "[(⟨0⟩ : Factor), (⟨1⟩ : Factor)]"

# Value readings the witnesses and the admissibility probe are stated over. The
# values are a SEPARATE argument, so a witness may hand in the reading that makes
# its point and nothing else depends on it.
#   _NOWHERE — no factor vanishes anywhere. Used by every witness that separates
#              descriptions structurally, so the reading contributes nothing to
#              the separation and cannot be the reason it holds.
#   _PAIR    — the reading under which the factor `⟨0⟩` takes the value 0 at
#              exactly the index 1 and `⟨1⟩` at exactly the index -1 — the two
#              indices the issue's own imaginary part `(n-1)(n+1)` vanishes at —
#              and a nonzero rational value at every other index. Written as an
#              explicit zero pattern rather than as `k - 1` / `k + 1` because the
#              workspace's Mathlib slice carries no `Rat` arithmetic
#              normalisation (no `norm_num`, and `decide` does not reduce
#              `Rat.sub`), so a probe stated with rational subtraction could not
#              be discharged at all; what the cases need from the reading is only
#              its zero pattern, which this gives exactly.
_NOWHERE = "(fun _ _ => some (1 : Rat))"
_PAIR = ("(fun g k => if g.ident = 0 then (if k = 1 then some (0 : Rat) "
         "else some 1)\n"
         "                  else (if k = -1 then some (0 : Rat) else some 1))")
# The reading under which `⟨0⟩` takes NO value at any index: a factor with no
# value somewhere is not a factor equal to zero there, and the admissibility
# probe checks the carrier really says so.
_NOVALUE = "(fun _ _ => (none : Option Rat))"

SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct reshape cannot verify, the
    # spec is SPEC-TOO-STRONG. The assembly clause fixes the ANSWER, so the
    # freedom a correct impl has is in how it BUILDS that answer: which pieces
    # it names first, whether it accumulates or nests, how it re-binds the
    # factors it was handed on the way to describing them, and how it dispatches
    # on the SHAPE the imaginary part arrived in. All four are exercised; the
    # third is the one the FACTOR IDENTITY obligation has to leave alone, and the
    # fourth is the one the SHAPE obligation has to leave alone.
    # =====================================================================
    {
        "id": "pos-hoist-keep-node",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the keep leg — the domain as narrowed (or not) by what the
        # imaginary part was told to be — to a typed local, then take it apart
        # from the undefined-index collection, replacing the mutable accumulator
        # with a nested term. The two shapes are dispatched in the OPPOSITE order
        # to the frozen impl's, which must not matter either.
        "module": _swap(
            _BASE, _IMPL,
            "    let keptDownToReal : IndexReport :=\n"
            "      match imaginaryPart with\n"
            "      | .factors gs => .meet .given (.zerosOfAny gs)\n"
            "      | .zeroThroughout => .given\n"
            "    return .apart keptDownToReal (.zerosOfAny denominators)\n"),
        "rationale": "naming the keep leg before taking it apart from the "
                     "undefined indices builds the SAME description under both "
                     "shapes, so both post-images still hold; a correct reshape "
                     "must verify (else SPEC-TOO-STRONG). Ports the nagini "
                     "pos-control-hoist-local.",
    },
    {
        "id": "pos-name-both-collections",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: recover the factor list the shape carries, name the two
        # per-factor zero collections FIRST, then combine them with the domain —
        # the keep node still built only under the shape that calls for one. Same
        # description, different construction order, and the shape is dispatched
        # on twice rather than once.
        "module": _swap(
            _BASE, _IMPL,
            "    let keepList : List Factor :=\n"
            "      match imaginaryPart with\n"
            "      | .zeroThroughout => []\n"
            "      | .factors gs => gs\n"
            "    let realIdx : IndexReport := .zerosOfAny keepList\n"
            "    let undefIdx : IndexReport := .zerosOfAny denominators\n"
            "    let mut acc : IndexReport := .given\n"
            "    acc := match imaginaryPart with\n"
            "           | .zeroThroughout => acc\n"
            "           | .factors _ => .meet acc realIdx\n"
            "    acc := .apart acc undefIdx\n"
            "    return acc\n"),
        "rationale": "naming both per-factor collections before combining them "
                     "leaves the assembled description unchanged under both "
                     "shapes, so the obligation still discharges; must verify. A "
                     "second structural positive control, defending the "
                     "obligation from a different construction order AND from an "
                     "impl that reads the factor list out of the shape before "
                     "using it.",
    },
    {
        "id": "pos-pass-factors-through",
        "kind": "soundness",
        "expect": "verify",
        # THE STRICTNESS BOUND ON FACTOR IDENTITY. Both legs' lists are walked
        # element by element and each member is re-bound — same handle, so the
        # very factors handed in are what the two collections describe. This is
        # the freedom a faithful implementation actually needs (it may destructure
        # and rebuild the lists it was given on the way to describing them), and
        # it must NOT be refused: what the assembly clause pins is which factors
        # the answer describes, not whether the impl copied the list on the way.
        # The companion probes that must be REJECTED (the same walk emitting a
        # DIFFERENT handle) are shipped as weak-represents-a-factor /
        # weak-represents-a-denominator.
        "module": _swap(
            _BASE, _IMPL,
            "    let dropList : List Factor :=\n"
            "      denominators.map (fun g => ⟨g.ident⟩)\n"
            "    let mut acc : IndexReport := .given\n"
            "    acc := match imaginaryPart with\n"
            "           | .zeroThroughout => acc\n"
            "           | .factors gs =>\n"
            "             .meet acc (.zerosOfAny (gs.map (fun g => ⟨g.ident⟩)))\n"
            "    acc := .apart acc (.zerosOfAny dropList)\n"
            "    return acc\n"),
        "rationale": "re-binding each listed factor to ITSELF describes the very "
                     "factors handed in, in the same order, so both post-images "
                     "still hold and the impl must verify. Bounds the FACTOR "
                     "IDENTITY obligation from the correct side: it refuses a "
                     "member PUT IN PLACE OF a handed-in factor, not an impl "
                     "that walks the lists. Built and measured alongside the two "
                     "rejected variants of the same walk (a member re-minted "
                     "with an offset, and a leg's member fabricated by folding "
                     "the whole list), so the three together show the obligation "
                     "tracks WHICH factors are described rather than the shape "
                     "of the code that describes them.",
    },
    {
        "id": "pos-keep-leg-by-shape",
        "kind": "soundness",
        "expect": "verify",
        # THE STRICTNESS BOUND ON THE SHAPE OBLIGATION. The keep leg is read
        # straight off the shape by the modeled reference `keptToReal` instead of
        # being assembled by a local `match`, and the apart leg is applied to it.
        # What the assembly clause pins is WHICH description each shape calls for,
        # not that the impl spell the dispatch out itself; an impl that defers to
        # the reference must verify, or the shape obligation would be pinning the
        # code rather than the answer.
        "module": _swap(
            _BASE, _IMPL,
            "    let mut acc : IndexReport := keptToReal imaginaryPart\n"
            "    acc := .apart acc (.zerosOfAny denominators)\n"
            "    return acc\n"),
        "rationale": "taking the keep leg straight from the shape builds exactly "
                     "the asked-for description under both shapes, so both "
                     "post-images hold and the impl must verify. Bounds the SHAPE "
                     "obligation from the correct side: it refuses an assembly "
                     "that narrows (or fails to narrow) the WRONG shape, not an "
                     "impl that dispatches on the shape differently.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require` clause (every
    # `domain`/`imaginaryPart`/`denominators`/`valueOf` is in scope), so the usual
    # "a normal input satisfies the precondition" probe is vacuous. The residual
    # risk on a total domain is that the post-image is UNSATISFIABLE / DEGENERATE
    # at the interesting point. This case discharges an in-region assert at the
    # issue's own zero pattern — a two-factor list read by a reading vanishing at
    # 1 and at -1, the indices `(n-1)(n+1)` vanishes at — showing the described
    # index set really does hold BOTH factors' roots, exclude a root of neither,
    # treat a factor with NO value at an index as not vanishing there, actually
    # lose an index to the apart leg, AND keep the two shapes apart: at the very
    # same domain and reading, the settled-zero shape keeps an index that no
    # listed factor vanishes at while the factored shape does not. The
    # surrounding impl is kept verbatim so the method's own obligation still
    # discharges. The assert is live, not decoration: three controls were built
    # during authoring — flipping the "0 is excluded" conjunct to "0 is kept",
    # dropping the SECOND factor from the list in the "-1 is kept" conjunct, and
    # flipping the settled-zero conjunct to "0 is excluded" — and each leaves an
    # unsolved goal (exit 1).
    # =====================================================================
    {
        "id": "admiss-per-factor-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap2(
            _IMPL,
            "    assert (with_name_prefix `assert\n"
            "      ((1 : Int) ∈ reported (Set.univ : Set Int) " + _PAIR + "\n"
            "            (.apart (.meet .given (.zerosOfAny " + _TWO + "))\n"
            "               (.zerosOfAny []))\n"
            "       ∧ (-1 : Int) ∈ reported (Set.univ : Set Int) " + _PAIR + "\n"
            "            (.apart (.meet .given (.zerosOfAny " + _TWO + "))\n"
            "               (.zerosOfAny []))\n"
            "       ∧ (0 : Int) ∉ reported (Set.univ : Set Int) " + _PAIR + "\n"
            "            (.apart (.meet .given (.zerosOfAny " + _TWO + "))\n"
            "               (.zerosOfAny []))\n"
            "       ∧ (1 : Int) ∉ reported (Set.univ : Set Int) " + _NOVALUE + "\n"
            "            (.meet .given (.zerosOfAny " + _F0 + "))\n"
            "       ∧ (1 : Int) ∉ reported (Set.univ : Set Int) " + _PAIR + "\n"
            "            (.apart (.meet .given (.zerosOfAny " + _TWO + "))\n"
            "               (.zerosOfAny " + _F0 + "))\n"
            "       ∧ (0 : Int) ∈ reported (Set.univ : Set Int) " + _PAIR + "\n"
            "            (keptToReal .zeroThroughout)\n"
            "       ∧ (0 : Int) ∉ reported (Set.univ : Set Int) " + _PAIR + "\n"
            "            (keptToReal (.factors " + _TWO + "))))\n"
            + _IMPL,
            _PROOF,
            "prove_correct restrictToRealValues by\n"
            "  loom_solve <;> cases imaginaryPart <;>\n"
            "    simp [reported, keptToReal, realIndices, anyVanishes,\n"
            "          vanishingSet]\n"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "shape the failing test asserts, on seven counts: for a "
                     "two-factor list read by the zero pattern of `(n-1)(n+1)` "
                     "the described index set holds 1 (the first factor's root) "
                     "AND -1 (the second's) — so a degenerate reading in which "
                     "only one listed factor is resolved fails the assert, which "
                     "is exactly what the per-factor structure claims; it "
                     "excludes 0 (a root of neither), so the keep leg is not "
                     "vacuously everything; a factor that takes NO value at an "
                     "index does not count as vanishing there, which is the "
                     "carrier's own content (`none` is not `some 0`); an index "
                     "the apart leg's list vanishes at is really lost, so the "
                     "apart leg is not vacuously empty; and the two SHAPES are "
                     "kept apart at one and the same domain and reading — the "
                     "settled-zero shape keeps the index 0, which the factored "
                     "shape drops — so neither shape's keep leg is a spelling of "
                     "the other's. The impl is kept verbatim so the `ensures` "
                     "clauses still discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and a MEASURED refinement argument (its assembly replayed
    # through the real callees on the failing test's families, or — for the three
    # named under REFINEMENT EVIDENCE — an explicitly weaker argument stated for
    # what it is). Each is given the STRONGEST tactic body available (see
    # _STRONG), so none of these rejections rests on a weak proof script.
    # =====================================================================
    {
        "id": "weak-drops-keep-leg",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the keep leg under BOTH shapes: the index domain is only taken
        # apart from the undefined indices, never kept down to the real-making
        # ones, so indices whose imaginary part is nonzero survive. On the
        # settled-zero shape this is what the routine really does, which is why
        # the rival is refuted at a FACTORED input.
        "module": _rival(
            "    let mut acc : IndexReport := .given\n"
            "    acc := .apart acc (.zerosOfAny denominators)\n"
            "    return acc\n"),
        "refinement": "a counterpart that never keeps the domain down to the "
                      "real-making indices answers with (almost) the whole index "
                      "domain: replayed through the real callees it answers "
                      "`Integers` where the failing test asserts "
                      "`FiniteSet(-1, 1)`, and it misses all SEVEN asserted "
                      "objects. It would NOT resolve.",
        "rationale": "REJECT from the assembly clause: where the imaginary part "
                     "arrives as factors the answer must be "
                     "`apart (meet given …) …`, and this impl's answer "
                     "is `apart given …` — the `meet` node is gone. Also "
                     "violates the index clause. Exercises the imaginary part's "
                     "role; witness at `(univ, factors [f₀], [], nowhere)`, an "
                     "input of the shape that DOES call for a keep node.",
        "witness": _wit("Set.univ", _F0, "[]", _NOWHERE),
    },
    {
        "id": "weak-drops-apart-leg",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the apart leg: the real-making indices are kept but the indices
        # at which the value is undefined are never removed, so a pole survives.
        # That leg is applied under BOTH shapes, so this is wrong under both.
        "module": _rival(
            "    let mut acc : IndexReport := .given\n"
            "    acc := match imaginaryPart with\n"
            "           | .zeroThroughout => acc\n"
            "           | .factors gs => .meet acc (.zerosOfAny gs)\n"
            "    return acc\n"),
        "refinement": "a counterpart that never removes the undefined indices "
                      "keeps a pole: replayed through the real callees it answers "
                      "`FiniteSet(1/2, zoo)` where the test asserts "
                      "`FiniteSet(1/2)`, and on the family whose every surviving "
                      "index is a pole it answers a non-empty set where the test "
                      "asserts `S.EmptySet`. It would NOT resolve.",
        "rationale": "REJECT from the assembly clause: the answer's top node must "
                     "be `apart`, and this impl's is `meet`. Also violates the "
                     "index clause. Exercises `denominators`' role; witness at "
                     "`(univ, factors [], [f₀], nowhere)`.",
        "witness": _wit("Set.univ", "[]", _F0, _NOWHERE),
    },
    {
        "id": "weak-collapses-factor-list",
        "kind": "uniqueness",
        "expect": "reject",
        # Both legs present, both roles right, both shapes dispatched: the
        # imaginary part's factor list is replaced by a SINGLE factor built out of
        # the list. Only the per-factor structure of the keep leg is wrong. This
        # is the rival class an index-set-only post-image cannot see at all.
        "module": _rival(
            "    let mut acc : IndexReport := .given\n"
            "    acc := match imaginaryPart with\n"
            "           | .zeroThroughout => acc\n"
            "           | .factors gs =>\n"
            "             .meet acc (.zerosOfAny\n"
            "               [⟨gs.foldl (fun a g => a + g.ident) 0⟩])\n"
            "    acc := .apart acc (.zerosOfAny denominators)\n"
            "    return acc\n"),
        "refinement": "a counterpart that resolves the imaginary part as ONE "
                      "factor instead of its listed factors cannot name the "
                      "individual indices: the real callees answer "
                      "`ConditionSet(n, Eq((n-1)*(n+1), 0), Integers)` where the "
                      "failing test asserts `FiniteSet(-1, 1)` — a genuinely "
                      "different object with the same members — and it misses six "
                      "of the seven asserted objects. It would NOT resolve.",
        "rationale": "REJECT from the assembly clause: the keep leg must collect "
                     "the zeros of the GIVEN list, and this impl hands it a "
                     "one-element list whose single factor it built out of that "
                     "list. Exercises the per-factor structure; witness at "
                     "`(univ, factors [f₀, f₁], [], pair)`, where a one-element "
                     "list is separated from a two-element one.",
        "witness": _wit("Set.univ", _TWO, "[]", _PAIR),
    },
    {
        "id": "weak-represents-a-factor",
        "kind": "uniqueness",
        "expect": "reject",
        # THE MEMBER RE-PRESENTATION — the rival the FACTOR IDENTITY carrier
        # exists to reject, and the exact shape that refuted an earlier
        # extensional factor payload. The whole assembly is performed correctly,
        # both roles are right, both shapes are dispatched, the keep leg's list
        # keeps its LENGTH and its ORDER, and every value the answer picks out is
        # unchanged; only each MEMBER of that list is another factor put in the
        # place of the one handed in. If a factor were carried as the function
        # giving its value at each index, a value-preserving re-presentation would
        # be PROVABLY the identity on that carrier and this rival's answer would
        # be LITERALLY EQUAL to the post-image's, so the assembly clause would
        # admit it; with a factor an identity-bearing handle, the described
        # factors are not the factors handed in.
        "module": _rival(
            "    let mut acc : IndexReport := .given\n"
            "    acc := match imaginaryPart with\n"
            "           | .zeroThroughout => acc\n"
            "           | .factors gs =>\n"
            "             .meet acc (.zerosOfAny\n"
            "               (gs.map (fun g => ⟨g.ident + 1⟩)))\n"
            "    acc := .apart acc (.zerosOfAny denominators)\n"
            "    return acc\n"),
        "refinement": "a counterpart that hands the keep leg a value-preserving "
                      "re-presentation of each factor does not describe the "
                      "factors it was given, and where the real callees cannot "
                      "name a factor's index they EMBED the factor in the node "
                      "they build: on the family whose imaginary part does not "
                      "split into linear factors they answer "
                      "`ImageSet(Lambda(x, x/2), ConditionSet(n, "
                      "Eq((n - 1)*(2*n + 1)/2, 0), Integers))` where the failing "
                      "test asserts `ImageSet(Lambda(x, x/2), ConditionSet(n, "
                      "Eq(n**2 - n/2 - 1/2, 0), Integers))` — the same indices "
                      "at every probed integer, a different object. Measured "
                      "directly with the harness on this shape: FAIL_TO_PASS 0/1 "
                      "(test_imageset_intersect_real) with PASS_TO_PASS 46/46. "
                      "It would NOT resolve.",
        "rationale": "REJECT from the assembly clause, which is the clause that "
                     "MUST refuse it: in the repository the re-presented factor "
                     "takes the same value at every index, so the surviving "
                     "indices there are exactly the same and no membership-level "
                     "clause could see the difference. (On this carrier the "
                     "values are read off a handle by a separate argument, so the "
                     "index clause is left unprovable for the rival too — "
                     "measured: its residual goal is `valueOf ⟨g.ident + 1⟩ n = "
                     "some 0`, which is neither provable nor refutable. The "
                     "rejection therefore does not DEPEND on the index clause, "
                     "and the assembly clause refutes it outright.) The keep "
                     "leg's collection must hold the factors HANDED IN; this "
                     "impl's holds others. Exercises the "
                     "per-member IDENTITY of a collection, i.e. the one part of "
                     "the post-image that an extensional value payload cannot "
                     "express; witness at `(univ, factors [f₀], [], nowhere)`, "
                     "where `zerosOfAny [f₁]` is separated from `zerosOfAny "
                     "[f₀]`.",
        "witness": _wit("Set.univ", _F0, "[]", _NOWHERE),
    },
    {
        "id": "weak-represents-a-denominator",
        "kind": "uniqueness",
        "expect": "reject",
        # The SAME hole on the other leg. The node that embeds a factor is
        # emitted by the one helper BOTH collections are resolved by, so a spec
        # that pinned member identity on the keep leg only would be asymmetric
        # against that helper and would rest on which families the suite happens
        # to assert. Shipped for the symmetry; see the REFINEMENT EVIDENCE note
        # on why its argument is symmetry rather than a measured family.
        "module": _rival(
            "    let repres : List Factor :=\n"
            "      denominators.map (fun g => ⟨g.ident + 1⟩)\n"
            "    let mut acc : IndexReport := .given\n"
            "    acc := match imaginaryPart with\n"
            "           | .zeroThroughout => acc\n"
            "           | .factors gs => .meet acc (.zerosOfAny gs)\n"
            "    acc := .apart acc (.zerosOfAny repres)\n"
            "    return acc\n"),
        "refinement": "a counterpart that hands the apart leg a value-preserving "
                      "re-presentation of each denominator does not describe the "
                      "denominators it was given, and the node the real callees "
                      "build for a denominator they cannot solve EMBEDS it, so "
                      "the object answered differs from the one the desired "
                      "behaviour answers wherever that node is not washed out. "
                      "The asserted families do not exhibit it (measured: the "
                      "only n-dependent denominator reaching that node belongs "
                      "to the family asserting `S.EmptySet`, and a constant "
                      "denominator's node IS `S.EmptySet`), so this case is "
                      "shipped on the SYMMETRY of the shared helper rather than "
                      "on a measured resolve failure — a conservative, symmetric "
                      "obligation on both legs.",
        "rationale": "REJECT from the assembly clause, for the same reason as the "
                     "keep-leg case: in the repository the re-presented "
                     "denominator takes the same value at every index, so the "
                     "surviving indices are unchanged and only the assembly can "
                     "see the difference (and here too the index clause is left "
                     "unprovable for the rival rather than satisfied by it, since "
                     "a handle's values are read separately). The apart leg's "
                     "collection must hold the denominators HANDED IN; this "
                     "impl's holds others. "
                     "Exercises per-member identity on the SECOND collection, so "
                     "the obligation is not keep-leg-only; witness at "
                     "`(univ, factors [], [f₀], nowhere)`.",
        "witness": _wit("Set.univ", "[]", _F0, _NOWHERE),
    },
    {
        "id": "weak-merges-the-two-collections",
        "kind": "uniqueness",
        "expect": "reject",
        # OVER-APPROXIMATION. The keep leg is handed both lists at once, so it
        # keeps the union of the real-making and the undefined indices; the apart
        # leg then removes the undefined ones again, leaving the surviving indices
        # unchanged. Wrong only in WHICH indices the keep leg names.
        "module": _rival(
            "    let mut acc : IndexReport := .given\n"
            "    acc := match imaginaryPart with\n"
            "           | .zeroThroughout => acc\n"
            "           | .factors gs =>\n"
            "             .meet acc (.zerosOfAny (gs ++ denominators))\n"
            "    acc := .apart acc (.zerosOfAny denominators)\n"
            "    return acc\n"),
        "refinement": "a counterpart whose keep leg is given the denominators too "
                      "names the poles as real-making indices and then removes "
                      "them: on the family whose surviving set is empty the real "
                      "callees answer "
                      "`ImageSet(Lambda(x, x/(x**2-9)), Complement(ConditionSet(n, "
                      "Eq(n**2-9, 0), Integers), …))` where the test asserts "
                      "`S.EmptySet`. It would NOT resolve.",
        "rationale": "REJECT from the assembly clause alone (the index clause "
                     "holds of it — the extra indices are removed again): the "
                     "keep leg's list must be the factors the imaginary part was "
                     "handed over as, and this impl's is those `++ denominators`. "
                     "Exercises the CONTENT of the keep leg's list; witness at "
                     "`(univ, factors [], [f₀], nowhere)`, where `[] ++ [f₀]` is "
                     "separated from `[]`.",
        "witness": _wit("Set.univ", "[]", _F0, _NOWHERE),
    },
    {
        "id": "weak-swaps-the-two-collections",
        "kind": "uniqueness",
        "expect": "reject",
        # BOUNDARY / ROLE swap: the two factor lists trade places, so the domain
        # is kept down to the UNDEFINED indices and the REAL-MAKING ones are
        # removed. A one-token error on this carrier.
        "module": _rival(
            "    let mut acc : IndexReport := .given\n"
            "    acc := .meet acc (.zerosOfAny denominators)\n"
            "    acc := match imaginaryPart with\n"
            "           | .zeroThroughout => acc\n"
            "           | .factors gs => .apart acc (.zerosOfAny gs)\n"
            "    return acc\n"),
        "refinement": "a counterpart that keeps the domain down to the poles and "
                      "removes the real-making indices answers `EmptySet` where "
                      "the failing test asserts `FiniteSet(-1, 1)`, and misses "
                      "all seven asserted objects. It would NOT resolve.",
        "rationale": "REJECT from the assembly clause: the imaginary part's "
                     "factors must fill the keep role and `denominators` the "
                     "apart role. Exercises which binder fills which role; "
                     "witness at `(univ, factors [f₀], [], nowhere)`, where the "
                     "two `zerosOfAny` payloads `[]` and `[f₀]` are separated.",
        "witness": _wit("Set.univ", _F0, "[]", _NOWHERE),
    },
    {
        "id": "weak-guards-on-one-factor",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL DOMAIN. Assembles correctly whenever the imaginary part is
        # handed over as two or more factors, and silently skips the keep leg when
        # it is a singleton — so on the sub-domain of unfactorable imaginary parts
        # the answer keeps every index whose value is not real.
        "module": _rival(
            "    let mut acc : IndexReport := .given\n"
            "    acc := match imaginaryPart with\n"
            "           | .zeroThroughout => acc\n"
            "           | .factors gs =>\n"
            "             if 1 < gs.length then .meet acc (.zerosOfAny gs)\n"
            "             else acc\n"
            "    acc := .apart acc (.zerosOfAny denominators)\n"
            "    return acc\n"),
        "refinement": "a counterpart that skips the keep leg when the imaginary "
                      "part is a single factor answers, on the family whose "
                      "imaginary part does not split, "
                      "`ImageSet(Lambda(n, n/2), Integers)` where the failing "
                      "test asserts `ImageSet(Lambda(x, x/2), ConditionSet(n, "
                      "Eq(n**2 - n/2 - 1/2, 0), Integers))` — every index kept "
                      "instead of only the real-making ones. It would NOT "
                      "resolve.",
        "rationale": "REJECT from both clauses, on a PARTIAL domain: correct "
                     "where the factor list is longer than one, wrong on the "
                     "singleton sub-domain, so it is refuted only by an input in "
                     "that sub-domain. Witness at "
                     "`(univ, factors [f₀], [], nowhere)`.",
        "witness": _wit("Set.univ", _F0, "[]", _NOWHERE),
    },
    {
        "id": "weak-masks-the-domain-leaf",
        "kind": "uniqueness",
        "expect": "reject",
        # THE LEAF MASK — the rival this carrier exists to reject. The entire
        # assembly is performed correctly; only the DOMAIN LEAF is replaced by a
        # re-description of the very same indices: the domain kept down to "the
        # indices that either do or do not make some listed factor vanish", a
        # condition that excludes nothing. Membership is untouched, every leg is
        # present, both roles are right. If the leaf carried a `Set Int` payload
        # this rival's answer would be LITERALLY EQUAL to the post-image's (sets
        # are extensional), so the assembly clause would admit it; with `given` a
        # nullary atom, the leaf is `meet …` where the clause requires `given`.
        # The mask is applied where the imaginary part arrives AS FACTORS, which
        # is the shape the measured family below has.
        "module": _rival(
            "    let mut acc : IndexReport := .given\n"
            "    acc := match imaginaryPart with\n"
            "           | .zeroThroughout => acc\n"
            "           | .factors gs =>\n"
            "             .meet (.meet .given\n"
            "                     (.either (.zerosOfAny gs)\n"
            "                              (.otherIndices (.zerosOfAny gs))))\n"
            "                   (.zerosOfAny gs)\n"
            "    acc := .apart acc (.zerosOfAny denominators)\n"
            "    return acc\n"),
        "refinement": "a counterpart that first narrows the index domain by a "
                      "condition excluding no index does not hand the callees the "
                      "domain itself: on the family whose imaginary part does not "
                      "split into linear factors the real callees answer "
                      "`Union(ImageSet(Lambda(x, x/2), Complement(ConditionSet(n, "
                      "Eq(n**2 - n/2 - 1/2, 0), Integers), …)), Intersection(…))` "
                      "where the failing test asserts `ImageSet(Lambda(x, x/2), "
                      "ConditionSet(n, Eq(n**2 - n/2 - 1/2, 0), Integers))` — the "
                      "same indices, a different object. Measured directly with "
                      "the harness on this shape: FAIL_TO_PASS 0/1 "
                      "(test_imageset_intersect_real) with PASS_TO_PASS 46/46. It "
                      "would NOT resolve.",
        "rationale": "REJECT from the assembly clause ALONE — clause (2) holds of "
                     "it exactly, since the mask excludes no index. The leaf must "
                     "be the atom `given`; this impl's is `meet given (either …)`. "
                     "Exercises the ATOM, i.e. the one part of the post-image that "
                     "an extensional set payload cannot express; witness at "
                     "`(univ, factors [f₀], [], nowhere)`.",
        "witness": _wit("Set.univ", _F0, "[]", _NOWHERE),
    },
    {
        "id": "weak-splits-the-domain-leaf",
        "kind": "uniqueness",
        "expect": "reject",
        # THE LEAF SPLIT — the same hole from the other side, and the reason the
        # algebra carries `either`. The domain leaf is taken apart into the
        # indices that do NOT make a listed factor vanish and the ones that do,
        # and the two halves are put back together: again exactly the domain's own
        # indices, again a different description.
        "module": _rival(
            "    let mut acc : IndexReport := .given\n"
            "    acc := match imaginaryPart with\n"
            "           | .zeroThroughout => acc\n"
            "           | .factors gs =>\n"
            "             .meet (.either (.apart .given (.zerosOfAny gs))\n"
            "                            (.meet .given (.zerosOfAny gs)))\n"
            "                   (.zerosOfAny gs)\n"
            "    acc := .apart acc (.zerosOfAny denominators)\n"
            "    return acc\n"),
        "refinement": "a counterpart that splits the index domain and unions the "
                      "halves back hands the callees a `Union` of a `Complement` "
                      "and an `Intersection` in place of the domain: on the family "
                      "whose imaginary part does not split it answers a `Union` "
                      "over a `Complement` where the failing test asserts "
                      "`ImageSet(Lambda(x, x/2), ConditionSet(n, Eq(n**2 - n/2 - "
                      "1/2, 0), Integers))`. It would NOT resolve.",
        "rationale": "REJECT from the assembly clause ALONE (clause (2) holds "
                     "exactly: the two halves partition the domain). The leaf must "
                     "be `given`; this impl's is `either (apart …) (meet …)`. A "
                     "second, structurally different probe of the ATOM — a union "
                     "rather than a mask — so the rejection does not depend on one "
                     "shape of re-description; witness at "
                     "`(univ, factors [f₀], [], nowhere)`.",
        "witness": _wit("Set.univ", _F0, "[]", _NOWHERE),
    },
    {
        "id": "weak-echoes-by-de-morgan",
        "kind": "uniqueness",
        "expect": "reject",
        # UNGROUNDED-ORACLE ECHO. No assembly at all: the surviving index set is
        # re-derived out of the post-image's own vocabulary, by complementing the
        # union of the three complements/collections, so clause (2) holds of it by
        # construction — under BOTH shapes, since the settled-zero shape's
        # contribution is "every index" — while nothing in the answer names a keep
        # or an apart leg. This is the shape that refuted an earlier
        # index-set-only post-image, re-sited to the description algebra (the
        # earlier form — returning the surviving set as the `given` payload — is
        # no longer even typeable, which is itself part of the carrier).
        "module": _rival(
            "    let realIdx : IndexReport :=\n"
            "      match imaginaryPart with\n"
            "      | .zeroThroughout => .otherIndices .noIndices\n"
            "      | .factors gs => .zerosOfAny gs\n"
            "    return .otherIndices (.either (.otherIndices .given)\n"
            "      (.either (.otherIndices realIdx)\n"
            "               (.zerosOfAny denominators)))\n"),
        "refinement": "a counterpart that describes the surviving indices by "
                      "complementing a union of complements hands the callees a "
                      "`Complement(Union(Complement(Integers, …), …))` in place of "
                      "the kept-and-cut assembly: for the issue's own family the "
                      "real callees answer that nested complement where the "
                      "failing test asserts `FiniteSet(-1, 1)`, and it misses all "
                      "seven asserted objects. It would NOT resolve.",
        "rationale": "REJECT from the assembly clause ALONE — clause (2) is "
                     "satisfied by construction (de Morgan), which is precisely "
                     "why an index-set-only post-image admitted this class. The "
                     "answer's top constructor must be `apart`; this impl's is "
                     "`otherIndices`. Witness at "
                     "`(univ, factors [f₀], [], nowhere)`.",
        "witness": _wit("Set.univ", _F0, "[]", _NOWHERE),
    },
    {
        "id": "weak-ignores-domain",
        "kind": "uniqueness",
        "expect": "reject",
        # Starts the assembly from EVERY index (the complement of the empty
        # description) rather than from the given index domain: both legs are
        # applied to all the integers. Correct on both legs and on both shapes;
        # wrong exactly on the domain the family ranges over.
        "module": _rival(
            "    let mut acc : IndexReport := .otherIndices .noIndices\n"
            "    acc := match imaginaryPart with\n"
            "           | .zeroThroughout => acc\n"
            "           | .factors gs => .meet acc (.zerosOfAny gs)\n"
            "    acc := .apart acc (.zerosOfAny denominators)\n"
            "    return acc\n"),
        "refinement": "a counterpart that assembles from all the integers instead "
                      "of the family's own index domain answers "
                      "`FiniteSet(-1, 1)` for the family indexed by the "
                      "NON-NEGATIVE integers, where the failing test asserts "
                      "`FiniteSet(1)`: the index -1 is outside that family's "
                      "domain. It would NOT resolve.",
        "rationale": "REJECT from the assembly clause (and, at any domain that is "
                     "not everything, the index clause): the leaf must be "
                     "`given`, and this impl's is `otherIndices noIndices`. "
                     "Exercises the `domain` binder; witness at "
                     "`(∅, factors [], [], nowhere)`, where the rival's leaf is "
                     "separated from `given`.",
        "witness": _wit("(∅ : Set Int)", "[]", "[]", _NOWHERE),
    },

    # =====================================================================
    # SHAPE rivals — the three that are right about the legs, the roles, the
    # lists, the members and the leaf, and wrong about WHICH ASSEMBLY THE SHAPE
    # OF THE IMAGINARY PART CALLS FOR. They are the classes a post-image that
    # took the imaginary part as a bare factor list could not state at all: on
    # that carrier the settled-zero outcome had to be spelled as some factor
    # list, and every one of these rivals would have BEEN the post-image.
    # =====================================================================
    {
        "id": "weak-keeps-when-settled-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # THE SHAPE ECHO. Every leg, role, list, member and leaf is right, and on
        # the factored shape the answer is exactly the asked-for one; on the
        # settled-zero shape the domain is narrowed ANYWAY, by a description
        # holding every index — which is precisely what the real callees build for
        # an identically zero numerator (measured: `UniversalSet()`). Membership
        # is therefore untouched: clause (2) holds of this rival exactly, under
        # both shapes. Only the assembly differs, and it differs where the routine
        # performs no narrowing at all.
        "module": _rival(
            "    let mut acc : IndexReport := .given\n"
            "    acc := match imaginaryPart with\n"
            "           | .zeroThroughout =>\n"
            "             .meet acc (.otherIndices .noIndices)\n"
            "           | .factors gs => .meet acc (.zerosOfAny gs)\n"
            "    acc := .apart acc (.zerosOfAny denominators)\n"
            "    return acc\n"),
        "refinement": "a counterpart that narrows the base set even where the "
                      "imaginary part is settled zero throughout keeps every "
                      "index the desired behaviour keeps and still hands the "
                      "callees a different object, because narrowing re-evaluates "
                      "the base set the routine was asked to leave alone (the "
                      "modeled source skips the keep step there precisely to "
                      "'allow re-evaluation of self in this case to make the "
                      "result canonical'). Measured on the family "
                      "`imageset(Lambda(n, n/2), Intersection(S.Integers, "
                      "Interval(0, 5), evaluate=False))`, whose imaginary part is "
                      "settled zero: the desired behaviour answers "
                      "`FiniteSet(0, 1/2, 1, 3/2, 2, 5/2)` and this counterpart "
                      "answers `ImageSet(Lambda(n, n/2), Range(0, 6, 1))` — the "
                      "same six members, a different object. This is a MEASURED "
                      "OBJECT DIVERGENCE on a constructed family of that shape, "
                      "not a measured F2P failure: no claim is made here about "
                      "whether the asserted families cover the settled-zero "
                      "shape.",
        "rationale": "REJECT from the assembly clause ALONE — clause (2) holds of "
                     "it exactly, since the extra keep node excludes no index. "
                     "Where the imaginary part is settled zero the keep leg must "
                     "be the atom `given`, with NO node standing over it; this "
                     "impl's is `meet given (otherIndices noIndices)`. Exercises "
                     "the SHAPE of the imaginary part, the one part of the "
                     "post-image a bare factor list could not state; witness at "
                     "`(univ, zeroThroughout, [], nowhere)`.",
        "witness": _wit("Set.univ", None, "[]", _NOWHERE),
    },
    {
        "id": "weak-ignores-the-settled-shape",
        "kind": "uniqueness",
        "expect": "reject",
        # The other way of collapsing the two shapes into one: the settled-zero
        # outcome is treated as an EMPTY factor list, i.e. handed to the same
        # per-factor collection with nothing to collect. That is the shape a
        # factor-list-only post-image forces on this outcome, and it keeps NO
        # index at all.
        "module": _rival(
            "    let mut acc : IndexReport := .given\n"
            "    acc := match imaginaryPart with\n"
            "           | .zeroThroughout => .meet acc (.zerosOfAny [])\n"
            "           | .factors gs => .meet acc (.zerosOfAny gs)\n"
            "    acc := .apart acc (.zerosOfAny denominators)\n"
            "    return acc\n"),
        "refinement": "a counterpart that resolves the settled-zero outcome as an "
                      "empty list of factors keeps nothing: the shared helper "
                      "unions one contribution per listed factor, so handed the "
                      "EMPTY list it answers the empty set, and keeping the base "
                      "set down to it leaves the empty family where the desired "
                      "behaviour answers the family's canonical form. DERIVED "
                      "from the helper's own definition rather than replayed "
                      "through it; it also breaks the index clause, so it is the "
                      "easiest of the shape rivals to see. It would NOT resolve.",
        "rationale": "REJECT from BOTH clauses on the settled-zero shape: the keep "
                     "leg must be `given` and this impl's is "
                     "`meet given (zerosOfAny [])`, whose indices are empty "
                     "instead of the whole domain. Exercises the SHAPE on the "
                     "membership level as well as the assembly level; witness at "
                     "`(univ, zeroThroughout, [], nowhere)`.",
        "witness": _wit("Set.univ", None, "[]", _NOWHERE),
    },
    {
        "id": "weak-swaps-the-two-shapes",
        "kind": "uniqueness",
        "expect": "reject",
        # BOUNDARY swap on the SHAPE axis: the two shapes' assemblies trade
        # places. The settled-zero outcome is narrowed (and by the denominators,
        # the only list in scope there), and the factored outcome — the one whose
        # factors were handed over precisely to narrow by — is left alone. A
        # one-token error, and on the factored shape it is the pre-change answer.
        "module": _rival(
            "    let mut acc : IndexReport := .given\n"
            "    acc := match imaginaryPart with\n"
            "           | .zeroThroughout =>\n"
            "             .meet acc (.zerosOfAny denominators)\n"
            "           | .factors _ => acc\n"
            "    acc := .apart acc (.zerosOfAny denominators)\n"
            "    return acc\n"),
        "refinement": "a counterpart that narrows on the settled-zero outcome and "
                      "not on the factored one never keeps the domain down to the "
                      "real-making indices where the factors were handed over for "
                      "exactly that: replayed through the real callees it answers "
                      "`Integers` where the failing test asserts "
                      "`FiniteSet(-1, 1)` and misses all seven asserted objects "
                      "(the same measurement as dropping the keep leg, since on "
                      "the factored shape the two answer the same thing), and on "
                      "the settled-zero outcome it additionally keeps the base "
                      "set down to the poles. It would NOT resolve.",
        "rationale": "REJECT from the assembly clause (and the index clause on "
                     "both shapes): which shape calls for a keep node is part of "
                     "the answer, and this impl has them the other way round. "
                     "Exercises the SHAPE dispatch itself; witness at "
                     "`(univ, factors [f₀], [], nowhere)`, the shape whose keep "
                     "node it drops.",
        "witness": _wit("Set.univ", _F0, "[]", _NOWHERE),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) + 1 AXIOM_TESTS; every one is
# accounted for below. The two carriers are NOT the same partition: the sibling
# models an imperative BACKWARD LOOP over integer indices (prepending survivors)
# guarded by a `survives(c, keep, drop)` predicate, and contracts TWO functions
# (a one-step filter and a two-step intersect-then-difference). This bundle
# models the whole computation as ONE method returning the index-set DESCRIPTION
# it assembled, so the sibling's per-index / positional / two-step rivals collapse
# onto the two legs of that assembly, and the carrier adds classes the sibling
# has no analogue for (the per-factor structure of a leg's list, the per-member
# identity of that list, the identity of the leaf the assembly starts from, and
# which of the two SHAPES the imaginary part arrives in calls for a keep leg).
#
#   nagini case                          -> here                          status
#   ---------------------------------------------------------------------------
#   pos-control-hoist-local              -> pos-hoist-keep-node            PORTED
#   (2nd structural positive, no sibling)-> pos-name-both-collections      ADDED
#   (factor-identity bound, no sibling)  -> pos-pass-factors-through       ADDED
#   (shape bound, no sibling)            -> pos-keep-leg-by-shape          ADDED
#   admiss-base-case                     -> admiss-per-factor-nondegenerate RE-AIMED
#   frame-mutation-write-base            -> (none, VACUOUS)                OMITTED
#   partial-domain-collapse-no-keep      -> weak-drops-keep-leg            PORTED
#   value-double-mask-ignore-drop        -> weak-drops-apart-leg           PORTED
#   partial-domain-keep-first (boundary) -> weak-swaps-the-two-collections RE-SITED
#   two-step-pos-control-hoist-drop      -> (subsumed by pos controls)     OMITTED
#   two-step-drop-collapse               -> weak-drops-apart-leg           MERGED
#   (domain-dependence, no sibling)      -> weak-ignores-domain            ADDED
#   (per-factor structure, no sibling)   -> weak-collapses-factor-list     ADDED
#   (per-member identity, no sibling)    -> weak-represents-a-factor       ADDED
#   (per-member identity, no sibling)    -> weak-represents-a-denominator  ADDED
#   (over-approximated leg, no sibling)  -> weak-merges-the-two-collections ADDED
#   (guarded partial domain, no sibling) -> weak-guards-on-one-factor      ADDED
#   (leaf identity, no sibling)          -> weak-masks-the-domain-leaf     ADDED
#   (leaf identity, no sibling)          -> weak-splits-the-domain-leaf    ADDED
#   (oracle echo, no sibling)            -> weak-echoes-by-de-morgan       ADDED
#   (shape echo, no sibling)             -> weak-keeps-when-settled-zero   ADDED
#   (shape collapse, no sibling)         -> weak-ignores-the-settled-shape ADDED
#   (shape boundary, no sibling)         -> weak-swaps-the-two-shapes      ADDED
#   (divergence, no sibling)             -> (none; correctly REJECTED by   NOTED
#                                           the `total` semantics, but not
#                                           shippable — the diverging module
#                                           does not elaborate, so no witness
#                                           can hold of it)
#   ax-ref-survives-kept_seq (AXIOM_TESTS)-> (dropped, G-AX's job)         DROPPED
#
# PORTED (the argument is unchanged; only the carrier is):
#  * partial-domain-collapse-no-keep dropped the KEEP conjunct of the sibling's
#    `survives` guard (retain any index merely not in `drop`). Here the keep
#    conjunct IS the keep leg; a rival that omits it is weak-drops-keep-leg.
#  * value-double-mask-ignore-drop dropped the DROP conjunct (retain any index in
#    `keep`, ignoring `drop`). Here the drop conjunct IS the `apart` leg; a rival
#    that omits it is weak-drops-apart-leg.
# RE-AIMED (admissibility): the sibling's case established that the read-only
#  precondition admits a normal F2P-shaped input (an entry Assert of the loop
#  base-case invariant). This method has NO `require` clause, so that probe is
#  vacuous — nothing could exclude a normal input. It is re-aimed at the residual
#  total-domain risk: that the post-image is UNSATISFIABLE / DEGENERATE at the
#  interesting point. The case discharges an in-region assert showing the
#  described index set holds BOTH factors' roots for the issue's own two-factor
#  list, excludes a root of neither, and keeps the two SHAPES apart at one and the
#  same domain and reading.
# MERGED: two-step-drop-collapse collapsed the difference step of the sibling's
#  SECOND function into a no-op — the identical wrongness as omitting the apart
#  leg, already carried by weak-drops-apart-leg.
# RE-SITED (boundary): partial-domain-keep-first over-keeps the FIRST base element
#  (`survives(...) or i == 1`), a positional attack on the sibling's backward
#  loop. Order-free description algebra has no first element and no loop step, but
#  the boundary tokens here are the two factor LISTS and the two roles they fill
#  (weak-swaps-the-two-collections, measured to miss all seven asserted objects)
#  and the two SHAPES and the assemblies they call for
#  (weak-swaps-the-two-shapes), and trading either pair is the same kind of
#  one-token error with a real consequence.
# ADDED (13): the second, third and fourth positive controls, weak-ignores-domain
#  (this carrier makes the index domain independently observable; the sibling
#  folded it into the loop bound), the seven classes that only exist once the
#  ASSEMBLY is observable — weak-collapses-factor-list (per-factor structure),
#  weak-represents-a-factor and weak-represents-a-denominator (the FACTOR IDENTITY
#  class: the whole assembly performed, the list lengths and order right, only a
#  collection's MEMBERS put in place of by others of equal value everywhere),
#  weak-merges-the-two-collections (an over-approximated leg that the next leg
#  hides again), weak-guards-on-one-factor (a guarded partial domain),
#  weak-masks-the-domain-leaf and weak-splits-the-domain-leaf (the LEAF IDENTITY
#  class: the whole assembly performed, only the domain leaf re-described) and
#  weak-echoes-by-de-morgan (the oracle echo that satisfies the index clause by
#  construction) — and the three that only exist once the SHAPE of the imaginary
#  part is an input rather than a factor list: weak-keeps-when-settled-zero (the
#  shape echo, whose indices are exactly right and whose assembly narrows a domain
#  the routine leaves alone), weak-ignores-the-settled-shape (the settled outcome
#  spelled as an empty factor list) and weak-swaps-the-two-shapes (the two shapes'
#  assemblies traded). Nine of these thirteen rivals keep the surviving indices
#  exactly right on every input, and each is measured — or, for the two named
#  under REFINEMENT EVIDENCE, argued from the shared helper's symmetry or from its
#  definition — to answer a different object from the one the desired behaviour
#  answers.
# OMITTED (2):
#  * frame-mutation-write-base — nagini-specific (fractional heap permissions;
#    the sibling's value-preserving no-op write back into the read-only base
#    under half-permission). This backend is referentially transparent and the
#    method declares no `mut` binder among its parameters, so there is no
#    read-only input to overwrite and no substitute probe. VACUOUS; not
#    fabricated.
#  * two-step-pos-control-hoist-drop — the sibling's positive control on its
#    SECOND (two-step) function. This bundle contracts a single method, so there
#    is no widened two-step function to defend; the four positive controls above
#    already exercise the correct-reshape side of the one modeled obligation.
#
# WITNESS DISCRIMINATION (real builds, and re-checked by the gate's two builds per
# reject case): each witness elaborates against its rival (exit 0 — the rival's
# assembled description provably differs from the post-image's at the probed
# input) and FAILS against the frozen solution (exit 1 — `simp` PROVES the frozen
# impl produces exactly the claimed description, so the `≠` claim reduces to
# `⊢ False` with nothing left to introduce). That gold-side failure is a SEMANTIC
# refutation of the concrete claim, not a missing identifier, a type error, a
# stuck reduction or a timeout — and the FORGERY check described in the module
# docstring (the same claim with `≠` flipped to `=`: gold exit 0, rival exit 1),
# re-run on this carrier for one witness of each of the three shapes, shows gold's
# exit code tracks the claim rather than the witness's shape.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the `pure` region's
# definitions are deep-model references (A-reference) validated there, and this
# manifest gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
