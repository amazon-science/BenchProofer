# properties.py — PBT falsification battery for sympy__sympy-15809.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a full model.py variant built by region-surgery that edits ONLY
# inside the `# impl-start` / `# impl-end` block (so the frozen spec — axioms,
# pure helpers, pre/post-conditions, signature — is byte-identical and
# same_spec holds). The runner stamps each with verify(host, Nagini) + same_spec.
#
# Defended surface (the spec this battery attacks):
#   lattice_reduce(operands: List[int], identity, zero, single, aggregate) -> int
#   models MinMaxBase.__new__ (the Min/Max lattice fold). `operands` is READ-ONLY
#   (Acc(list_pred(operands), 1/2)); identity/zero/single/aggregate are four
#   pairwise-DISTINCT int sentinels (precondition), so each postcondition clause
#   pins exactly one branch. FOUR @Pure @ContractOnly axioms classify the input.
#   The first two model the ONE ordered pre-filter scan's FIRST decisive event
#   (NOT mere containment: a collection can carry a non-comparable operand and
#   still not be rejected, because the scan stops earlier at an absorbing
#   operand); the last two model the SEPARATE canonical-set pass that compares
#   the survivors AGAINST ONE ANOTHER, which is PARTIAL — an operand the
#   per-operand scan passes over can still be one that pass cannot place, and
#   then its comparison failure propagates instead of a canonical set:
#       has_noncomparable_operand(ops)    -> bool (Implies(len==0, not Result()))
#       has_absorbing_operand(ops)        -> bool (Implies(len==0, not Result());
#                                                 Implies(Result(), not
#                                                 has_noncomparable_operand(ops))
#                                                 — EXCLUSIVITY: one scan has one
#                                                 first decisive event)
#       canonical_reduction_defined(ops)  -> bool (Implies(len==0, Result()))
#       canonical_count(ops)              -> int  (Requires
#                                                 canonical_reduction_defined(ops)
#                                                 — PARTIAL; >=0;
#                                                 Implies(len==0, ==0))
#   The load-bearing postcondition clauses:
#     (P-empty)     Implies(len(operands)==0, Result()==identity)         [THE FIX]
#     (P-emptyset)  Implies(notNC & notAbs & defined, Implies(count==0,
#                                                            Result()==identity))
#     (P-abs)       Implies(notNC & has_absorbing, Result()==zero)
#     (P-single)    Implies(notNC & notAbs & defined, Implies(count==1,
#                                                            Result()==single))
#     (P-agg)       Implies(notNC & notAbs & defined, Implies(count>=2,
#                                                            Result()==aggregate))
#     (P-total)     Implies(notNC & defined,
#                           Result() in {identity,zero,single,aggregate})
#     (P-oblig)     Ensures(not has_noncomparable_operand(operands))   [closes atk_2]
#     (P-defined)   Ensures(has_absorbing_operand(operands) or
#                           canonical_reduction_defined(operands))
#                   — the mirror obligation: a NORMAL return is admissible only
#                     where the scan already decided or that pass is defined, so
#                     a rival cannot invent a value where the real pass fails
#     (P-frame)     Ensures(Acc(list_pred(operands), 1/2))             [read-only]
#     (X)           Exsures(NonComparableOperand, has_noncomparable_operand(ops))
#                   Exsures(NonComparableOperand, Acc(list_pred(operands), 1/2))
#                   Exsures(ReductionUndefined, notNC & notAbs & not defined)
#                   Exsures(ReductionUndefined, Acc(list_pred(operands), 1/2))
#                   — each failure carries its OWN guard, so the two are not
#                     interchangeable and neither is an unguarded escape hatch
#
# Oracle-grounding note (ungrounded-oracle class): the four axioms are NOT an
# answer-key oracle for Result() that an impl can echo — they are predicates over
# the INPUT (cardinality/comparability/definedness/canonical-count), and the impl
# has no way to MATERIALIZE a sentinel from them except by executing the concrete
# branch logic the spec pins. There is no opaque "expected result" value to
# return. The closest echo risks are the two obligation clauses: an impl could
# try to satisfy `not has_noncomparable_operand(operands)` by NOT raising, or
# (P-defined) by NOT propagating the canonical-set pass's failure — but it cannot
# make either predicate true or false; it can only AVOID a normal return (i.e.
# raise) where the predicate forbids one. The "drop the non-comparable raise"
# rival (weak-drop-nc below) and the "undefined pass -> identity" rival
# (weak-undefined-pass-to-identity below) are exactly those wrong-echo attempts
# and MUST be rejected by (P-oblig) and (P-defined) respectively; the first is
# the residual SPEC-TOO-WEAK hole (atk_2) the 2nd refinement closed. So in place
# of a classic ungrounded-oracle-echo we supply (a) those obligation attacks and
# (b) the cheapest-impl positive control as a grounded honest control.

from pathlib import Path

INSTANCE = "sympy__sympy-15809"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl-region body (everything between # impl-start and
# # impl-end, markers exclusive). Every variant is produced by _swap on _BASE
# touching ONLY text inside this block.
_GOLD_IMPL = """    # (The stale guard `if len(operands) == 0: raise EmptyReductionRejected()`
    #  is absent: the empty collection is handled by the empty-canonical-set
    #  branch below, returning the identity element.)
    # The unchanged comparability pre-filter rejects a non-comparable operand
    # before any result branch (the empty collection passes, having no operand).
    if has_noncomparable_operand(operands):
        raise NonComparableOperand()
    if has_absorbing_operand(operands):
        return zero
    # The survivors reach the canonical-set pass, which compares them against one
    # another; where it cannot, it yields no canonical set and its failure
    # propagates (the empty collection is defined here, having nothing to
    # compare).
    if not canonical_reduction_defined(operands):
        raise ReductionUndefined()
    count = canonical_count(operands)  # type: int
    if count == 0:
        return identity
    if count == 1:
        return single
    return aggregate"""

# Sanity: the gold impl text must appear verbatim and uniquely in _BASE.
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block drift — re-sync _GOLD_IMPL"


# ---------------------------------------------------------------------------
# 1. POSITIVE CONTROL (soundness) — structurally DIFFERENT, still CORRECT.
#    The impl is straight-line control flow over opaque @Pure axiom results
#    (no loop, hence no loop invariant / framing lemma to preserve — cf. pilot
#    bug #2/#3, which do not apply here). We change only the EXECUTABLE SHAPE:
#      * keep the mandatory non-comparable raise FIRST (the spec obligates it);
#      * keep the absorbing -> zero short-circuit;
#      * replace the cascade of `if count==0 / if count==1 / return` with an
#        if/elif/else over the SAME `count`, and reorder so the >=2 branch is
#        written before the ==1 branch (count>=2 tested first, then ==1, then
#        the count==0 / else identity branch).
#    The pinned facts each branch establishes are identical, so the gold proof
#    obligations still discharge. MUST verify — else SPEC-TOO-STRONG.
_POS_IMPL = """    # Structurally-different but behaviourally-identical reduction: the
    # mandatory non-comparable rejection stays first, then the absorbing
    # short-circuit, then the mandatory reduction-undefined propagation written
    # with the polarity flipped (a positive guard whose else-arm carries the
    # rest), then an if/elif/else over the canonical count in a different branch
    # order (>=2 first, then ==1, else the empty-set identity).
    if has_noncomparable_operand(operands):
        raise NonComparableOperand()
    if has_absorbing_operand(operands):
        return zero
    if canonical_reduction_defined(operands):
        count = canonical_count(operands)  # type: int
        if count >= 2:
            return aggregate
        elif count == 1:
            return single
        else:
            return identity
    else:
        raise ReductionUndefined()"""


# ---------------------------------------------------------------------------
# 2. ADMISSIBILITY — the precondition must ACCEPT a normal F2P-shaped input.
#    The Requires is permission-only (Acc(list_pred(operands),1/2)) plus the
#    four sentinels pairwise-distinct; it places NO length/value constraint on
#    the operand collection, so an F2P-shaped EMPTY collection (Min()/Max()),
#    a single survivor (Min(x)), and a >=2 aggregate (Min(x,y)) are all
#    in-domain. We keep the full gold impl and add, at the TOP of impl,
#    derivable assertions that confirm the half-permission we hold is real and
#    usable (a 1/4 read share is obtainable; the length is readable and
#    non-negative; the four sentinels are pairwise distinct as the precondition
#    promised). If this fails to verify => PRECOND-TOO-STRONG.
_ADMISS_IMPL = """    Assert(Acc(list_pred(operands), 1 / 4))
    Assert(len(operands) >= 0)
    Assert(identity != zero and identity != single and identity != aggregate)
    Assert(zero != single and zero != aggregate and single != aggregate)
""" + _GOLD_IMPL


# ---------------------------------------------------------------------------
# 3. FRAME-MUTATION (MANDATORY — read-only input). A rival that WRITES to the
#    read-only operand collection to (vacuously) try to satisfy a postcondition.
#    With only Acc(list_pred(operands), 1/2) the assignment operands[0] = zero
#    requires FULL permission and MUST be rejected for INSUFFICIENT PERMISSION.
#    The write is inserted AFTER the non-comparable raise and absorbing branch
#    (so operands is provably non-empty at the write only on a path where count
#    could be read) and BEFORE the count read; every gold branch is kept so the
#    rejection is attributable to the WRITE, not to a proof gap. expect=reject.
#    Refinement: the repo callee receives a `frozenset`/tuple of sympified Expr
#    operands; the gold __new__ never mutates the caller's *args. A faithful
#    patch that mutated an operand in place (e.g. overwriting the first operand
#    with cls.zero) would corrupt the reduction — Min(x, y) would behave as
#    Min(-oo, y) == -oo instead of the aggregate Min(x, y), so test_Min / many
#    P2P aggregate assertions FAIL. A verifying mutator is a true
#    verify-not-resolve break.
_FRAME_IMPL = _swap(
    _GOLD_IMPL,
    "    count = canonical_count(operands)  # type: int",
    "    operands[0] = zero\n    count = canonical_count(operands)  # type: int",
)


# ---------------------------------------------------------------------------
# 4. UNIQUENESS — DROP THE NON-COMPARABLE RAISE (== atk_2, the residual
#    SPEC-TOO-WEAK hole the 2nd refinement closed). Remove the leading
#    `if has_noncomparable_operand: raise` so a non-comparable collection falls
#    through to a NORMAL outcome (zero/identity/single/aggregate) instead of
#    raising. expect=reject — it MUST violate (P-oblig)
#    Ensures(not has_noncomparable_operand(operands)): on a non-comparable
#    collection the normal-return path is reached, but the obligation forbids a
#    normal return there.
#    Refinement: this refines to "gold + suppress the unchanged comparability
#    ValueError" — Min(I)/Min(I,x)/Max(S.ComplexInfinity,1)/Min(cos(x),sin(x))
#    .subs(x,I) would no longer raise ValueError, so the `raises(ValueError,...)`
#    lines in F2P test_Min / test_Max FAIL (pytest RC=1). Confirmed by the
#    re-audit (atk_2 VERIFIED 27.5s BEFORE the fix). A verifying rival is the
#    exact verify-not-resolve break this clause exists to stop.
_DROP_NC_IMPL = """    if has_absorbing_operand(operands):
        return zero
    # NON-COMPARABLE RAISE DROPPED: a non-comparable collection now returns a
    # normal outcome instead of being rejected (the residual spec-too-weak hole
    # atk_2). (P-oblig) must reject this. The rest of the reduction is gold, so
    # the rejection is attributable to the suppressed raise and not to any other
    # clause: the reduction-undefined propagation below is reached only on the
    # collections the gold impl reaches it on.
    if has_noncomparable_operand(operands):
        return identity
    if not canonical_reduction_defined(operands):
        raise ReductionUndefined()
    count = canonical_count(operands)  # type: int
    if count == 0:
        return identity
    if count == 1:
        return single
    return aggregate"""


# ---------------------------------------------------------------------------
# 5. UNIQUENESS — EMPTY -> ZERO (== atk_3). On the empty-canonical-set branch
#    (count==0) return the annihilator `zero` instead of the identity element.
#    expect=reject — violates (P-empty)/(P-emptyset): the empty collection
#    (count 0, no NC, no absorbing) must yield `identity`, and zero != identity
#    by the precondition.
#    Refinement: this makes Min() == -oo (the annihilator) instead of +oo (the
#    identity), and Max() == +oo instead of -oo — F2P test_Min/test_Max assert
#    Min() == S.Infinity, Max() == S.NegativeInfinity, so both FAIL. A real patch
#    that returned cls.zero for the empty fold would not resolve.
_EMPTY_ZERO_IMPL = _swap(
    _GOLD_IMPL,
    "    if count == 0:\n        return identity",
    "    if count == 0:\n        return zero",
)


# ---------------------------------------------------------------------------
# 6. UNIQUENESS — EMPTY -> SINGLE (== atk_8). On the empty-canonical-set branch
#    return the single-survivor sentinel instead of identity. expect=reject —
#    violates (P-empty)/(P-emptyset): count==0 must yield identity, single !=
#    identity by the precondition.
#    Refinement: `single` ↦ list(args).pop() (a concrete survivor); returning it
#    on the EMPTY fold has no survivor to return at all — the faithful refinement
#    is gold with the empty branch returning a survivor that does not exist /
#    the wrong value, so Min()/Max() no longer equal the identity element and
#    F2P test_Min/test_Max FAIL.
_EMPTY_SINGLE_IMPL = _swap(
    _GOLD_IMPL,
    "    if count == 0:\n        return identity",
    "    if count == 0:\n        return single",
)


# ---------------------------------------------------------------------------
# 7. UNIQUENESS — ABSORBING -> IDENTITY (== atk_5). On the absorbing-operand
#    branch return the identity element instead of the annihilator `zero`.
#    expect=reject — violates (P-abs): notNC & has_absorbing must yield zero,
#    identity != zero by the precondition.
#    Refinement: the ShortCircuit path returns cls.zero (e.g. Max(oo, x) == oo).
#    Returning cls.identity instead makes Max(oo, x) == -oo (and Min(-oo, x) ==
#    +oo), inverting the absorbing element — P2P/F2P assertions about the
#    annihilator collapse FAIL. A real patch swapping the short-circuit return
#    would not resolve.
_ABS_IDENTITY_IMPL = _swap(
    _GOLD_IMPL,
    "    if has_absorbing_operand(operands):\n        return zero",
    "    if has_absorbing_operand(operands):\n        return identity",
)


# ---------------------------------------------------------------------------
# 8. UNIQUENESS — SWAP SINGLE/AGGREGATE (== atk_4). count==1 returns the
#    aggregate sentinel and count>=2 returns the single sentinel (the two
#    survivor branches swapped). expect=reject — violates (P-single)
#    (count==1 -> single) and (P-agg) (count>=2 -> aggregate); single !=
#    aggregate by the precondition.
#    Refinement: Min(x) (one survivor) would assemble an aggregate object
#    instead of returning the operand x, and Min(x,y) (two survivors) would
#    return a single survivor instead of the aggregate — both break the
#    constructor's documented one-survivor/many-survivor contract, failing P2P
#    idempotence/aggregate assertions. A real patch swapping these branches
#    would not resolve.
_SWAP_IMPL = """    if has_noncomparable_operand(operands):
        raise NonComparableOperand()
    if has_absorbing_operand(operands):
        return zero
    if not canonical_reduction_defined(operands):
        raise ReductionUndefined()
    count = canonical_count(operands)  # type: int
    if count == 0:
        return identity
    if count == 1:
        return aggregate
    return single"""


# ---------------------------------------------------------------------------
# 9. UNIQUENESS — OVER-RAISE ON COMPARABLE (== atk_10). Raise NonComparableOperand
#    UNCONDITIONALLY (even on a fully-comparable / empty collection). expect=
#    reject — violates (P-total) Implies(notNC, Result() in {...}) AND (P-empty):
#    on a comparable collection (in particular the empty one, where
#    has_noncomparable_operand is provably False by its axiom) the function must
#    return a normal outcome, not raise.
#    Refinement: this refines to "gold + raise ValueError unconditionally",
#    re-introducing the very rejection the patch DELETED (and worse, rejecting
#    every comparable input). Min()/Max()/Min(x)/Min(x,y) would all raise
#    ValueError, so F2P test_Min/test_Max (which assert Min()==oo etc. and the
#    survivor/aggregate cases) and essentially all P2P FAIL. A real patch that
#    kept (or broadened) the empty-args raise would not resolve — it is the
#    prepatch bug's superset.
_OVER_RAISE_IMPL = """    # OVER-RAISE: reject EVERY collection, including the comparable / empty one
    # the patch is supposed to accept. (P-total) and (P-empty) must reject this.
    raise NonComparableOperand()"""


# ---------------------------------------------------------------------------
# 10. UNIQUENESS — UNDEFINED CANONICAL-SET PASS -> IDENTITY. The rival keeps the
#     two scan outcomes, then, instead of propagating the canonical-set pass's
#     comparison failure, RETURNS the identity element on the collections that
#     pass cannot reduce (it never reads the partial count there, so the
#     rejection cannot come from that observation's precondition). expect=reject
#     — violates (P-defined) Ensures(has_absorbing_operand(operands) or
#     canonical_reduction_defined(operands)): a normal return is admissible only
#     where the scan already decided or the pass is defined.
#     Refinement: `Min(x, x + I)` — the per-operand scan passes `x + I` over
#     (is_real is None, not a number), and `_find_localzeros` -> `_is_connected`
#     then evaluates `x >= x + I` and propagates
#     `TypeError("Invalid comparison of complex I")`. A patch returning the
#     identity element there would make `Min(x, x + I) == oo`, silently answering
#     a comparison sympy declines to make, and the P2P
#     `raises(TypeError, lambda: Min(x, x + I))`-shaped assertions on the complex
#     comparison path FAIL.
_UNDEF_IDENTITY_IMPL = """    if has_noncomparable_operand(operands):
        raise NonComparableOperand()
    if has_absorbing_operand(operands):
        return zero
    # UNDEFINED-PASS FAILURE SUPPRESSED: instead of propagating the canonical-set
    # pass's comparison failure this returns the identity element. (P-defined)
    # must reject this.
    if not canonical_reduction_defined(operands):
        return identity
    count = canonical_count(operands)  # type: int
    if count == 0:
        return identity
    if count == 1:
        return single
    return aggregate"""


# ---------------------------------------------------------------------------
# 11. UNIQUENESS — OVER-PROPAGATE THE REDUCTION-UNDEFINED FAILURE. The rival
#     fails with ReductionUndefined on EVERY collection the scan did not decide,
#     including the ones whose canonical-set pass is perfectly defined (and the
#     empty one). expect=reject — the Exsures guard for that failure demands
#     `not canonical_reduction_defined(operands)`, which does not hold there, and
#     (P-empty)/(P-total) demand a normal outcome.
#     Refinement: this refines to "gold + propagate the complex-comparison
#     TypeError for every reduction that reaches the canonical-set pass", so
#     `Min()`, `Min(x)`, `Min(x, y)` all fail — F2P test_Min/test_Max and nearly
#     all P2P FAIL. It is the mirror of the empty-args rejection: a spec that
#     admitted it would let a rival trade one unconditional failure for another.
_UNDEF_OVER_RAISE_IMPL = """    if has_noncomparable_operand(operands):
        raise NonComparableOperand()
    if has_absorbing_operand(operands):
        return zero
    # OVER-PROPAGATE: fail as reduction-undefined on every uncollapsed
    # collection, including the empty one and every collection whose
    # canonical-set pass is defined. The Exsures guard and (P-empty) must reject.
    raise ReductionUndefined()"""


# ---------------------------------------------------------------------------
# 12. UNIQUENESS — SWAP THE TWO FAILURE MODES. The rival raises the
#     reduction-undefined failure where the ordered scan met a non-comparable
#     operand, and the non-comparable rejection where the canonical-set pass is
#     undefined: the two real callees are collapsed into one and then crossed.
#     expect=reject — each Exsures carries its OWN guard
#     (NonComparableOperand => has_noncomparable_operand; ReductionUndefined =>
#     not has_noncomparable_operand and not has_absorbing_operand and not
#     canonical_reduction_defined), so neither crossed raise can discharge the
#     clause it lands in.
#     Refinement: the two failures are different repo events with different
#     types — the scan's per-operand `ValueError` (miscellaneous.py:521-523 at
#     base_commit) versus the comparison `TypeError` that `_is_connected`
#     propagates out of `Expr.__ge__` (expr.py:295). Crossing them makes
#     `Min(I)` fail with the comparison error and `Min(x, x + I)` with the
#     comparability error, so the `raises(ValueError, ...)` lines in F2P
#     test_Min/test_Max FAIL.
_SWAP_FAILURES_IMPL = """    # FAILURE MODES CROSSED: the scan's rejection and the canonical-set pass's
    # propagated failure are raised as each other. Each Exsures guard must
    # reject its crossed raise.
    if has_noncomparable_operand(operands):
        raise ReductionUndefined()
    if has_absorbing_operand(operands):
        return zero
    if not canonical_reduction_defined(operands):
        raise NonComparableOperand()
    count = canonical_count(operands)  # type: int
    if count == 0:
        return identity
    if count == 1:
        return single
    return aggregate"""


SPEC_TESTS = [
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_IMPL),
        "rationale": (
            "structurally-different but CORRECT impl: keeps the mandatory "
            "non-comparable raise and the absorbing short-circuit, then selects "
            "the survivor outcome with an if/elif/else over the SAME canonical "
            "count in a different branch order (>=2, then ==1, else identity). "
            "No loop/invariant/lemma is involved (straight-line over opaque @Pure "
            "axioms), so the gold proof obligations still discharge. Must verify; "
            "if it cannot, the postcondition is SPEC-TOO-STRONG (rejects a "
            "faithful correct implementation)."
        ),
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS_IMPL),
        "rationale": (
            "the precondition is permission-only (Acc(list_pred(operands),1/2)) "
            "plus the four sentinels pairwise-distinct; it constrains neither "
            "length nor values, so the empty collection (Min()/Max()), a single "
            "survivor and a >=2 aggregate are all in-domain. The added "
            "top-of-impl assertions confirm a 1/4 read share is derivable from "
            "the 1/2 held, the length is readable/non-negative, and the four "
            "sentinels are distinct as promised. Must verify; if it cannot, "
            "PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mutate-readonly-operands",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME_IMPL),
        "refinement": (
            "the gold MinMaxBase.__new__ never mutates the caller's operand "
            "tuple; it builds a frozenset and reads it. A faithful patch that "
            "overwrote an operand in place (operands[0] = cls.zero) would corrupt "
            "the reduction: Min(x, y) would behave as Min(-oo, y) == -oo instead "
            "of the aggregate Min(x, y), so test_Min and many P2P aggregate "
            "assertions FAIL. A verifying mutator is a true verify-not-resolve "
            "break."
        ),
        "rationale": (
            "REJECT must come from the PERMISSION SYSTEM: operands holds only "
            "Acc(list_pred(operands),1/2); the write operands[0]=zero needs full "
            "permission and is rejected for insufficient permission. Every gold "
            "branch is kept so the failure is attributable to the WRITE, not a "
            "proof gap. If it verifies, the frame is unguarded (FRAME-MUTATION "
            "SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "weak-drop-noncomparable-raise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _DROP_NC_IMPL),
        "refinement": (
            "refines to 'gold + suppress the unchanged comparability ValueError': "
            "Min(I) / Min(I, x) / Max(S.ComplexInfinity, 1) / "
            "Min(cos(x), sin(x)).subs(x, I) would no longer raise ValueError, so "
            "the raises(ValueError, ...) lines in F2P test_Min/test_Max FAIL "
            "(pytest RC=1). This is the residual spec-too-weak hole atk_2 (it "
            "VERIFIED 27.5s before the 2nd refinement added (P-oblig)); a "
            "verifying rival here is the exact verify-not-resolve break that "
            "clause exists to stop."
        ),
        "rationale": (
            "REJECT comes from (P-oblig) Ensures(not has_noncomparable_operand("
            "operands)): dropping the raise lets a non-comparable collection "
            "reach the normal-return path, but the obligation forbids a normal "
            "return when has_noncomparable_operand holds. The Exsures alone only "
            "PERMITS the raise; (P-oblig) OBLIGATES it. If it verifies, the "
            "non-comparable rejection is unconstrained (SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "weak-empty-to-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _EMPTY_ZERO_IMPL),
        "refinement": (
            "returns the annihilator zero on the empty-canonical-set branch: "
            "Min() == -oo (instead of +oo) and Max() == +oo (instead of -oo). "
            "F2P test_Min/test_Max assert Min() == S.Infinity and "
            "Max() == S.NegativeInfinity, so both FAIL. A real patch returning "
            "cls.zero for the empty fold would not resolve."
        ),
        "rationale": (
            "REJECT comes from (P-empty)/(P-emptyset): the empty collection "
            "(count 0, no NC, no absorbing) must yield identity, and zero != "
            "identity by the precondition. If it verifies, the empty->identity "
            "fix is not pinned (SPEC-TOO-WEAK / the prepatch family)."
        ),
    },
    {
        "id": "weak-empty-to-single",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _EMPTY_SINGLE_IMPL),
        "refinement": (
            "returns the single-survivor sentinel on the empty fold. `single` "
            "maps to list(args).pop() (a concrete survivor); the empty fold has "
            "no survivor, so the faithful refinement returns the wrong/nonexistent "
            "value and Min()/Max() no longer equal the identity element — F2P "
            "test_Min/test_Max FAIL. A real patch wiring the empty branch to a "
            "survivor would not resolve."
        ),
        "rationale": (
            "REJECT comes from (P-empty)/(P-emptyset): count==0 must yield "
            "identity, and single != identity by the precondition. If it "
            "verifies, the empty->identity fix is not pinned (SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "weak-absorbing-to-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ABS_IDENTITY_IMPL),
        "refinement": (
            "returns the identity element on the absorbing (ShortCircuit) branch "
            "instead of the annihilator zero: Max(oo, x) == -oo (instead of oo) "
            "and Min(-oo, x) == +oo, inverting the absorbing element. P2P/F2P "
            "assertions about the annihilator collapse FAIL. A real patch "
            "swapping the short-circuit return would not resolve."
        ),
        "rationale": (
            "REJECT comes from (P-abs): notNC & has_absorbing must yield zero, "
            "and identity != zero by the precondition. If it verifies, the "
            "absorbing branch is not pinned (SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "weak-swap-single-aggregate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _SWAP_IMPL),
        "refinement": (
            "swaps the two survivor branches: count==1 assembles an aggregate "
            "object (instead of returning the lone operand x for Min(x)) and "
            "count>=2 returns a single survivor (instead of the aggregate for "
            "Min(x,y)). Both break the constructor's one-survivor/many-survivor "
            "contract, failing P2P idempotence (Min(x)==x) and aggregate "
            "assertions. A real patch swapping these branches would not resolve."
        ),
        "rationale": (
            "REJECT comes from (P-single) (count==1 -> single) and (P-agg) "
            "(count>=2 -> aggregate); single != aggregate by the precondition, so "
            "neither swapped branch can satisfy its clause. If it verifies, the "
            "survivor-cardinality branches are not pinned (SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "weak-over-raise-on-comparable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _OVER_RAISE_IMPL),
        "refinement": (
            "raises unconditionally — refines to 'gold + raise ValueError on "
            "EVERY collection', a superset of the prepatch empty-args bug. "
            "Min()/Max()/Min(x)/Min(x,y) all raise ValueError, so F2P "
            "test_Min/test_Max (Min()==oo, single/aggregate cases) and nearly all "
            "P2P FAIL. A real patch that kept/broadened the empty-args raise would "
            "not resolve."
        ),
        "rationale": (
            "REJECT comes from (P-total) Implies(not has_noncomparable_operand, "
            "Result() in {identity,zero,single,aggregate}) together with "
            "(P-empty): on a comparable collection (in particular the empty one, "
            "where has_noncomparable_operand is provably False by its axiom) the "
            "function MUST return a normal outcome, so an unconditional raise is "
            "an inadmissible exception. If it verifies, totality on the "
            "comparable domain is not enforced (SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "weak-undefined-pass-to-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _UNDEF_IDENTITY_IMPL),
        "refinement": (
            "suppresses the canonical-set pass's propagated comparison failure "
            "and returns the identity element instead. On Min(x, x + I) the real "
            "callee propagates TypeError('Invalid comparison of complex I') out "
            "of _find_localzeros -> _is_connected -> Expr.__ge__ "
            "(miscellaneous.py:552/574, expr.py:295 at base_commit); this rival "
            "answers oo instead, i.e. it decides a comparison sympy declines to "
            "make. The complex-comparison assertions on the Min/Max path FAIL."
        ),
        "rationale": (
            "REJECT comes from (P-defined) Ensures(has_absorbing_operand("
            "operands) or canonical_reduction_defined(operands)): a NORMAL "
            "return is admissible only where the ordered scan already decided "
            "the outcome or the canonical-set pass is defined. The rival never "
            "reads the partial canonical_count on the undefined class, so the "
            "rejection is attributable to that obligation and not to the count "
            "observation's precondition. If it verifies, the reduction is free "
            "to invent a value where the real pass fails (SPEC-TOO-WEAK, the "
            "hole a spec that claimed totality on the whole comparable domain "
            "leaves open)."
        ),
    },
    {
        "id": "weak-over-propagate-undefined",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _UNDEF_OVER_RAISE_IMPL),
        "refinement": (
            "fails as reduction-undefined on every uncollapsed collection, i.e. "
            "'gold + propagate the complex-comparison TypeError for every "
            "reduction that reaches the canonical-set pass'. Min(), Min(x) and "
            "Min(x, y) would all fail, so F2P test_Min/test_Max (Min()==oo, the "
            "single-survivor and aggregate cases) and nearly all P2P FAIL. It is "
            "the mirror of the empty-args rejection the patch removes."
        ),
        "rationale": (
            "REJECT comes from the Exsures guard for that failure — "
            "Exsures(ReductionUndefined, not has_noncomparable_operand and not "
            "has_absorbing_operand and not canonical_reduction_defined) — "
            "together with (P-empty)/(P-total): on a collection whose pass IS "
            "defined (in particular the empty one, where the definedness axiom "
            "gives Result() True) the failure is inadmissible and a normal "
            "outcome is obligatory. If it verifies, the new failure leg is an "
            "unguarded escape hatch that would let any rival trade the empty-args "
            "rejection for this one (SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "weak-swap-failure-modes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _SWAP_FAILURES_IMPL),
        "refinement": (
            "crosses the two real failures: the ordered scan's per-operand "
            "ValueError (miscellaneous.py:521-523) and the comparison TypeError "
            "_is_connected propagates (expr.py:295) are raised as each other, so "
            "Min(I) fails with the comparison error and Min(x, x + I) with the "
            "comparability error. The raises(ValueError, ...) lines in F2P "
            "test_Min/test_Max FAIL."
        ),
        "rationale": (
            "REJECT comes from the two Exsures clauses each carrying its OWN "
            "guard: NonComparableOperand demands has_noncomparable_operand, and "
            "ReductionUndefined demands not has_noncomparable_operand and not "
            "has_absorbing_operand and not canonical_reduction_defined. Neither "
            "crossed raise can discharge the clause it lands in. If it verifies, "
            "the two distinct repo events are interchangeable under the spec "
            "(SPEC-TOO-WEAK: two callees collapsed into one)."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE — four @ContractOnly A-consumed axioms. Each encodes only its
# WEAKEST property the proof consumes (the empty-collection / non-negativity
# facts); the soundness probes run the REAL sympy Min/Max (gold applied) and
# confirm the encoded Ensures holds, and the containment probes confirm every
# callee-input the MODEL can reach lies inside each axiom's Requires domain.
# These mirror (and re-run independently) the obligations axiom_check.py checks.
#
# Three of the four Requires domains are Acc(list_pred(operands), 1/4) alone — a
# pure permission predicate with NO value/length restriction — so EVERY List[int]
# the model can construct (any cardinality, any opaque ids) is trivially inside
# them. `canonical_count` is the exception: it is PARTIAL, adding
# Requires(canonical_reduction_defined(operands)), because the canonical-set pass
# that yields a cardinality can instead propagate a comparison failure over the
# survivors and then has no cardinality to report. So the containment obligation
# is NOT vacuous for that one — the model must call it only under the definedness
# guard, which the containment probe below states and the verifier enforces at
# every call site. The rest of the content is SOUNDNESS of each encoded Ensures,
# which we attack by fuzzing the boundary (empty), single, >=2, the
# non-comparable raise, and the undefined-pass paths of the real callee.

_AX_NONCOMP_SOUNDNESS_PROBE = r'''
import random, sys
try:
    from sympy import Min, Max, S, Symbol, I, cos, sin
except Exception as exc:  # environment mismatch -> skip, not fail
    print("AX SKIP: cannot import sympy in this interpreter (%r)" % (exc,))
    sys.exit(0)

# has_noncomparable_operand axiom: Ensures(Implies(len(operands)==0, not Result())).
# The proof ALSO consumes (via (P-oblig)/Exsures) that a NON-empty collection
# carrying a non-comparable operand IS rejected. Soundness check on the REAL
# callee:
#   (1) the EMPTY reduction NEVER raises a comparability ValueError (so
#       has_noncomparable_operand([]) == False — the encoded Ensures holds);
#   (2) every collection containing a non-comparable operand (I / zoo / nan,
#       alone, mixed, at a random position; and the substituted
#       Min/Max(cos(x),sin(x)).subs(x,I)) DOES raise ValueError (the unchanged
#       comparability path the F2P tests assert).
x = Symbol("x")
pool = [Symbol(n) for n in ("a", "b", "c", "d", "e")]
noncomp = [I, S.ComplexInfinity, S.NaN]
checks = 0
for cls in (Min, Max):
    # (1) empty -> must NOT raise (returns the identity element)
    try:
        r = cls()
    except Exception as exc:
        print("AXIOM-UNSOUND: %s() empty reduction raised %r — "
              "has_noncomparable_operand([]) must be False" % (cls.__name__, exc))
        sys.exit(1)
    checks += 1
    # (2) every non-comparable collection -> must raise ValueError
    fixed = [(I,), (S.ComplexInfinity,), (S.NaN,), (I, x), (x, I),
             (S.ComplexInfinity, x), (S.NaN, x)]
    for ops in fixed:
        raised = False
        try:
            cls(*ops)
        except ValueError:
            raised = True
        if not raised:
            print("AXIOM-UNSOUND: %s(*%r) did NOT raise on a non-comparable "
                  "operand — has_noncomparable_operand must be True here"
                  % (cls.__name__, ops))
            sys.exit(1)
        checks += 1
    # substituted-expression path
    raised = False
    try:
        cls(cos(x), sin(x)).subs(x, I)
    except ValueError:
        raised = True
    if not raised:
        print("AXIOM-UNSOUND: %s(cos(x),sin(x)).subs(x,I) did NOT raise"
              % cls.__name__)
        sys.exit(1)
    checks += 1

# fuzz: comparable set + one non-comparable at a random position must raise
rng = random.Random(15809)
for cls in (Min, Max):
    for _ in range(1500):
        k = rng.randint(0, 4)
        ops = [rng.choice(pool) for _ in range(k)] + [rng.choice(noncomp)]
        rng.shuffle(ops)
        raised = False
        try:
            cls(*ops)
        except ValueError:
            raised = True
        if not raised:
            print("AXIOM-UNSOUND: %s(*%r) carrying a non-comparable operand did "
                  "NOT raise" % (cls.__name__, ops))
            sys.exit(1)
        checks += 1
print("AXIOM-SOUND (has_noncomparable_operand): empty reduction never raises a "
      "comparability error (Ensures Implies(len==0,not Result()) holds) and every "
      "non-comparable collection raises ValueError, over %d observations." % checks)
sys.exit(0)
'''


_AX_ABSORB_SOUNDNESS_PROBE = r'''
import random, sys
try:
    from sympy import Min, Max, S, Symbol
except Exception as exc:
    print("AX SKIP: cannot import sympy in this interpreter (%r)" % (exc,))
    sys.exit(0)

# has_absorbing_operand axiom: Ensures(Implies(len(operands)==0, not Result()))
# AND Ensures(Implies(Result(), not has_noncomparable_operand(operands))).
# The proof consumes that the EMPTY collection admits NO absorbing operand, so
# the empty reduction does NOT short-circuit to the annihilator cls.zero
# (Min.zero=-oo, Max.zero=+oo). Soundness: the empty reduction yields the
# IDENTITY element (Min()=+oo, Max()=-oo), never the annihilator.
# The EXCLUSIVITY clause is checked at the bottom against the REAL ordered scan
# cls._new_args_filter: whichever decisive event it meets FIRST is the only one
# observed, so the two predicates can never both hold on any collection.
ident = {Min: S.Infinity, Max: S.NegativeInfinity}
annih = {Min: S.NegativeInfinity, Max: S.Infinity}
checks = 0
for cls in (Min, Max):
    try:
        r = cls()
    except Exception as exc:
        print("AXIOM-UNSOUND: %s() empty reduction raised %r" % (cls.__name__, exc))
        sys.exit(1)
    if r == annih[cls] and ident[cls] != annih[cls]:
        print("AXIOM-UNSOUND: %s() empty reduction collapsed to the annihilator "
              "%r — has_absorbing_operand([]) must be False" % (cls.__name__, annih[cls]))
        sys.exit(1)
    if r != ident[cls]:
        print("AXIOM-UNSOUND: %s() empty reduction != identity %r (got %r)"
              % (cls.__name__, ident[cls], r))
        sys.exit(1)
    checks += 1
# sanity: the absorbing operand DOES short-circuit on a NON-empty collection,
# confirming the predicate is non-trivial (cls.zero present -> returns cls.zero).
pool = [Symbol(n) for n in ("a", "b", "c")]
rng = random.Random(158091)
for cls in (Min, Max):
    z = annih[cls]
    for _ in range(500):
        k = rng.randint(0, 3)
        ops = [rng.choice(pool) for _ in range(k)] + [z]
        rng.shuffle(ops)
        try:
            r = cls(*ops)
        except Exception as exc:
            print("AXIOM-UNSOUND: %s(*%r) with the annihilator raised %r"
                  % (cls.__name__, ops, exc))
            sys.exit(1)
        if r != z:
            print("AXIOM check: %s(*%r) with the annihilator did NOT collapse to "
                  "%r (got %r)" % (cls.__name__, ops, z, r))
            sys.exit(1)
        checks += 1

# --- EXCLUSIVITY: Implies(has_absorbing_operand, not has_noncomparable_operand)
# Resolved through the REAL ordered scan cls._new_args_filter, exactly as the
# constructor consumes it (frozenset(cls._new_args_filter(sympify(a) for a in
# args))). Whichever decisive event the scan meets FIRST is the only outcome, so
# the two predicates are mutually exclusive. This is checked on collections that
# carry BOTH an absorbing and a non-comparable operand, in BOTH orders — the
# class the containment reading of these predicates gets wrong.
from sympy import I, zoo, nan, oo, Integer, Rational, sympify
from sympy.core.operations import ShortCircuit


def _scan_outcome(cls, raw):
    """The first decisive event of the REAL scan: 'noncomparable', 'absorbing'
    or 'ok'."""
    gen = (sympify(a) for a in raw)
    try:
        frozenset(cls._new_args_filter(gen))
        return "ok"
    except ShortCircuit:
        return "absorbing"
    except ValueError:
        return "noncomparable"


x2 = Symbol("x")
excl_pool = [Symbol("a", real=True), Symbol("b", real=True),
             Symbol("p", positive=True), Integer(0), Integer(3),
             Rational(-7, 3), oo, -oo, I, zoo, nan]
# deterministic both-orders catalogue over {absorbing, non-comparable}
for cls in (Min, Max):
    z = annih[cls]
    for bad in (I, zoo, nan):
        for raw in ([z, bad], [bad, z], [Symbol("a", real=True), z, bad],
                    [Symbol("a", real=True), bad, z]):
            out = _scan_outcome(cls, raw)
            nc = out == "noncomparable"
            ab = out == "absorbing"
            if nc and ab:
                print("AXIOM-UNSOUND: %s(*%r) reports BOTH scan events — the "
                      "exclusivity clause Implies(has_absorbing, not "
                      "has_noncomparable) fails" % (cls.__name__, raw))
                sys.exit(1)
            # the real constructor must agree with the scan's first event
            try:
                v = cls(*raw)
                raised = False
            except ValueError:
                raised = True
            if nc != raised:
                print("AXIOM-UNSOUND: %s(*%r) scan says %r but the constructor "
                      "%s" % (cls.__name__, raw, out,
                              "raised" if raised else "returned"))
                sys.exit(1)
            if ab and v != z:
                print("AXIOM-UNSOUND: %s(*%r) scan says absorbing but the "
                      "constructor returned %r (expected the annihilator %r)"
                      % (cls.__name__, raw, v, z))
                sys.exit(1)
            checks += 1
# fuzz the same obligation over mixed collections
rng2 = random.Random(1580911)
for cls in (Min, Max):
    z = annih[cls]
    for _ in range(3000):
        k = rng2.randint(0, 5)
        raw = [rng2.choice(excl_pool) for _ in range(k)]
        out = _scan_outcome(cls, raw)
        if out == "noncomparable" and out == "absorbing":
            print("AXIOM-UNSOUND: %s(*%r) both events" % (cls.__name__, raw))
            sys.exit(1)
        try:
            v = cls(*raw)
            raised = False
        except ValueError:
            raised = True
        if (out == "noncomparable") != raised:
            print("AXIOM-UNSOUND: %s(*%r) scan %r vs constructor %s"
                  % (cls.__name__, raw, out, "raised" if raised else "returned"))
            sys.exit(1)
        if out == "absorbing" and v != z:
            print("AXIOM-UNSOUND: %s(*%r) absorbing but got %r"
                  % (cls.__name__, raw, v))
            sys.exit(1)
        checks += 1
print("AXIOM-SOUND (has_absorbing_operand): empty reduction never collapses to "
      "the annihilator (Ensures Implies(len==0,not Result()) holds); the "
      "annihilator short-circuits on a non-empty collection; and the two scan "
      "events are MUTUALLY EXCLUSIVE (Implies(Result(), not "
      "has_noncomparable_operand) holds) with the constructor agreeing with the "
      "real scan's first decisive event on both orders of "
      "{absorbing, non-comparable}, over %d observations." % checks)
sys.exit(0)
'''


_AX_COUNT_SOUNDNESS_PROBE = r'''
import random, sys
try:
    from sympy import Min, Max, S, Symbol
except Exception as exc:
    print("AX SKIP: cannot import sympy in this interpreter (%r)" % (exc,))
    sys.exit(0)

# canonical_count axiom: Ensures(Result() >= 0) and
# Ensures(Implies(len(operands)==0, Result()==0)). The model reads the count via
# the branches: count==0 -> identity, count==1 -> single, count>=2 -> aggregate.
# Soundness on the REAL callee, observing the canonical count through the
# constructor's OBSERVABLE branch outcome:
#   empty   (count 0)  -> the empty-canonical-set branch -> the IDENTITY element;
#   one survivor (count 1) -> returns the lone operand itself;
#   >=2 survivors (count>=2) -> assembles an aggregate of the same lattice.
# A negative count is impossible (a set cardinality is never negative where the
# pass yields a set at all); the empty->count-0 fact is witnessed by
# empty->identity. NOTE the axiom is PARTIAL — it claims a cardinality only where
# canonical_reduction_defined holds — so this probe observes it ONLY on operand
# collections that pass can reduce. The collections it CANNOT (survivors the scan
# passes over that still do not compare against one another, e.g. x and x + I)
# are the ax-reduction-defined-soundness probe's subject, and the model reads no
# count on them.
ident = {Min: S.Infinity, Max: S.NegativeInfinity}
checks = 0
for cls in (Min, Max):
    # empty -> count 0 -> identity element (Implies(len==0, count==0))
    r = cls()
    if r != ident[cls]:
        print("AXIOM-UNSOUND: %s() empty reduction != identity %r (got %r) — "
              "canonical_count([]) must be 0 (empty-set branch)"
              % (cls.__name__, ident[cls], r))
        sys.exit(1)
    checks += 1
    # single survivor -> count 1 -> the operand itself
    for nm in ("p", "q", "r", "s"):
        s = Symbol(nm)
        if cls(s) != s:
            print("AXIOM check: %s(%s) single survivor != operand" % (cls.__name__, nm))
            sys.exit(1)
        checks += 1
    # >=2 survivors -> count>=2 -> aggregate of the same lattice
    a, b = Symbol("a"), Symbol("b")
    agg = cls(a, b)
    if agg.func is not cls:
        print("AXIOM check: %s(a,b) >=2 survivors did not assemble an aggregate "
              "(got %r)" % (cls.__name__, agg))
        sys.exit(1)
    checks += 1

# fuzz: every collection the canonical-set pass CAN reduce (plain symbols, which
# it compares without failing) yields one of the three count classes, never
# raising, never a negative observable.
pool = [Symbol(n) for n in ("a", "b", "c", "d")]
rng = random.Random(1580909)
for cls in (Min, Max):
    for _ in range(2000):
        k = rng.randint(0, 5)
        ops = [rng.choice(pool) for _ in range(k)]
        distinct = set(ops)
        r = cls(*ops)   # must NOT raise where the pass is defined
        if k == 0:
            if r != ident[cls]:
                print("AXIOM-UNSOUND: %s() empty != identity in fuzz" % cls.__name__)
                sys.exit(1)
        elif len(distinct) == 1:
            only = next(iter(distinct))
            if r != only:
                print("AXIOM check: %s single survivor mismatch" % cls.__name__)
                sys.exit(1)
        else:
            if r.func is not cls:
                print("AXIOM check: %s aggregate mismatch" % cls.__name__)
                sys.exit(1)
        checks += 1
print("AXIOM-SOUND (canonical_count): count is non-negative and the empty "
      "collection reduces to count 0 (empty->identity); single->operand, "
      ">=2->aggregate, over %d observations." % checks)
sys.exit(0)
'''


_AX_DEFINED_SOUNDNESS_PROBE = r'''
import random, sys
try:
    from sympy import (Min, Max, S, Symbol, I, oo, zoo, nan, sympify, sign,
                       Order, Integer, Rational)
    from sympy.core.operations import ShortCircuit
except Exception as exc:  # environment mismatch -> skip, not fail
    print("AX SKIP: cannot import sympy in this interpreter (%r)" % (exc,))
    sys.exit(0)

# canonical_reduction_defined axiom: Ensures(Implies(len(operands)==0, Result())).
ident = {Min: S.Infinity, Max: S.NegativeInfinity}
annih = {Min: S.NegativeInfinity, Max: S.Infinity}


def _scan_outcome(cls, raw):
    """First decisive event of the REAL ordered scan cls._new_args_filter."""
    gen = (sympify(a) for a in raw)
    try:
        frozenset(cls._new_args_filter(gen))
        return "ok"
    except ShortCircuit:
        return "absorbing"
    except ValueError:
        return "noncomparable"


def _construct(cls, raw):
    try:
        return ("value", cls(*raw))
    except ValueError as exc:
        return ("valueerror", exc)
    except Exception as exc:
        return ("failure", exc)


x = Symbol("x")
a = Symbol("a", real=True)
checks = 0
undefined_seen = 0

# (1) the EMPTY reduction: the pass has nothing to compare, so it cannot fail
for cls in (Min, Max):
    kind, val = _construct(cls, [])
    if kind != "value" or val != ident[cls]:
        print("AXIOM-UNSOUND: %s() empty reduction gave (%s, %r); the "
              "canonical-set pass must be DEFINED on the empty collection"
              % (cls.__name__, kind, val))
        sys.exit(1)
    checks += 1

# (2)/(3) catalogue: the scan's first event decides, and only where the scan says
# 'ok' may the canonical-set pass fail.
catalogue = []
for bad in (x + I, x + 2 * I, x - I, I * x, sign(x), Order(x)):
    catalogue += [[x, bad], [bad, x], [a, bad], [bad, a], [bad], [bad, bad],
                  [oo, bad], [bad, oo], [-oo, bad], [bad, -oo],
                  [I, bad], [bad, I], [Integer(3), bad], [bad, Rational(-7, 3)]]
catalogue += [[], [x], [x, x], [x, a], [a, Integer(2)], [oo], [-oo], [oo, x],
              [-oo, x], [I], [zoo], [nan], [I, x]]
for cls in (Min, Max):
    for raw in catalogue:
        out = _scan_outcome(cls, raw)
        kind, val = _construct(cls, raw)
        if out == "noncomparable":
            if kind != "valueerror":
                print("AXIOM-UNSOUND: %s(*%r) scan says noncomparable but the "
                      "constructor gave (%s, %r)" % (cls.__name__, raw, kind, val))
                sys.exit(1)
        elif out == "absorbing":
            if kind != "value" or val != annih[cls]:
                print("AXIOM-UNSOUND: %s(*%r) scan already decided (absorbing) "
                      "yet the reduction gave (%s, %r) instead of the annihilator "
                      "%r — canonical_reduction_defined must be vacuously true "
                      "where the pass is never reached"
                      % (cls.__name__, raw, kind, val, annih[cls]))
                sys.exit(1)
        else:
            if kind == "valueerror":
                print("AXIOM-UNSOUND: %s(*%r) scan says ok yet the constructor "
                      "raised the scan's own error %r"
                      % (cls.__name__, raw, val))
                sys.exit(1)
            if kind == "failure":
                undefined_seen += 1
        checks += 1

if undefined_seen == 0:
    print("AXIOM check: no witness of an UNDEFINED canonical-set pass was "
          "observed — the predicate would be trivially true and the model's "
          "failure leg unreachable")
    sys.exit(1)

# fuzz the same obligation over mixed collections
pool = [x, a, Symbol("p", positive=True), Integer(0), Integer(3),
        Rational(-7, 3), oo, -oo, I, zoo, nan, x + I, x - I, I * x, sign(x),
        Order(x)]
rng = random.Random(15809011)
for cls in (Min, Max):
    for _ in range(1500):
        k = rng.randint(0, 4)
        raw = [rng.choice(pool) for _ in range(k)]
        out = _scan_outcome(cls, raw)
        kind, val = _construct(cls, raw)
        if out == "noncomparable" and kind != "valueerror":
            print("AXIOM-UNSOUND: %s(*%r) scan noncomparable, got (%s, %r)"
                  % (cls.__name__, raw, kind, val))
            sys.exit(1)
        if out == "absorbing" and (kind != "value" or val != annih[cls]):
            print("AXIOM-UNSOUND: %s(*%r) scan absorbing, got (%s, %r)"
                  % (cls.__name__, raw, kind, val))
            sys.exit(1)
        if out == "ok" and kind == "valueerror":
            print("AXIOM-UNSOUND: %s(*%r) scan ok yet raised %r"
                  % (cls.__name__, raw, val))
            sys.exit(1)
        if out == "ok" and kind == "failure":
            undefined_seen += 1
        checks += 1
print("AXIOM-SOUND (canonical_reduction_defined): the empty reduction cannot "
      "fail in the canonical-set pass (Ensures Implies(len==0, Result()) holds); "
      "the predicate is vacuously true wherever the ordered scan already decided "
      "the outcome (an absorbing operand still collapses the reduction to the "
      "annihilator even alongside an operand that pass cannot place); and it is "
      "NON-TRIVIAL — %d observations reached the pass and it propagated its own "
      "comparison failure, the class the model's failure leg covers. %d "
      "observations total." % (undefined_seen, checks))
sys.exit(0)
'''


_AX_CONTAINMENT_PROBE = r'''
import sys
# Containment for the four axioms, in two parts.
#
# (a) THREE of them — has_noncomparable_operand, has_absorbing_operand,
#     canonical_reduction_defined — have a PURE permission Requires,
#     Acc(list_pred(operands), 1/4), with NO value or length restriction. The
#     model constructs `operands: List[int]` of arbitrary cardinality and opaque
#     ids and passes the SAME reference to each (no projection, no filtering), so
#     every callee-input it can reach is a List[int], which trivially lies inside
#     a permission-only domain. AXIOM-TOO-WEAK-FOR-CALLER cannot arise for these.
#
# (b) canonical_count is PARTIAL: it adds
#     Requires(canonical_reduction_defined(operands)), so its domain is a REAL
#     condition and containment is NOT vacuous. Every one of the model's call
#     sites is dominated by that guard — the impl reads the count only after
#     `if not canonical_reduction_defined(operands): raise ReductionUndefined()`,
#     and each postcondition that mentions the count is a nested Implies whose
#     antecedent establishes definedness first. Those are VERIFIER obligations:
#     Viper checks the precondition at every call site and at every use in a
#     contract, so G-VERIFY (and the `pos-control-branch-reorder` variant, whose
#     guard has the opposite polarity) is the mechanical evidence that no call
#     escapes the domain — an unguarded read does not verify at all.
#     The part a probe can add is the WITNESS that the guarded domain is not
#     empty where the model needs it: the branch classes the model's control flow
#     distinguishes must really be inside it on the REAL callee.
try:
    from sympy import Min, Max, S, Symbol
except Exception as exc:  # environment mismatch -> skip, not fail
    print("AX SKIP: cannot import sympy in this interpreter (%r)" % (exc,))
    sys.exit(0)

classes = {
    "empty": [],
    "single": [7],
    "two": [7, 11],
    "many": [1, 2, 3, 4, 5],
}
for name, ops in classes.items():
    if not isinstance(ops, list):
        print("containment: %s is not a List[int]" % name)
        sys.exit(1)

# The same cardinality classes on the REAL callee: each must reach a DEFINED
# canonical-set pass (it returns a value rather than propagating a comparison
# failure), so the count observation the model reads on that branch is inside
# canonical_count's Requires domain. The empty class is the load-bearing one: the
# definedness axiom's Ensures(Implies(len==0, Result())) is exactly what puts the
# empty collection in the count's domain, which (P-empty) needs.
p, q, r_, s_, t_ = (Symbol(n) for n in ("p", "q", "r", "s", "t"))
real_classes = {
    "empty": (),
    "single": (p,),
    "two": (p, q),
    "many": (p, q, r_, s_, t_),
}
checks = 0
for cls in (Min, Max):
    for name, ops in real_classes.items():
        try:
            cls(*ops)
        except Exception as exc:
            print("containment: %s(*%r) (class %s) did not reach a defined "
                  "canonical-set pass (%r) — canonical_count's Requires domain "
                  "would not cover the branch the model reads there"
                  % (cls.__name__, ops, name, exc))
            sys.exit(1)
        checks += 1

print("AXIOM-COVERED: every model-reachable operand collection (cardinality "
      "classes empty/single/two/many) is a List[int], trivially inside the "
      "permission-only Requires Acc(list_pred(operands),1/4) of "
      "has_noncomparable_operand / has_absorbing_operand / "
      "canonical_reduction_defined. canonical_count is PARTIAL (it also requires "
      "canonical_reduction_defined), so its domain condition is discharged by the "
      "verifier at every call site and contract use — an unguarded read does not "
      "verify — and each of the %d real reductions in those classes reaches a "
      "DEFINED pass, so the branches the model reads a count on are inside that "
      "domain." % checks)
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-noncomparable-soundness",
        "axiom": "has_noncomparable_operand",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_NONCOMP_SOUNDNESS_PROBE,
        "rationale": (
            "the axiom encodes Implies(len==0, not Result()) and underpins "
            "(P-oblig)/Exsures. The real sympy Min/Max empty reduction never "
            "raises a comparability error (so the encoded Ensures holds), and "
            "every non-comparable collection (I/zoo/nan, alone/mixed/random "
            "position; subs path) raises ValueError. A counterexample to either "
            "would be AXIOM-UNSOUND. Mirrors axiom_check.py."
        ),
    },
    {
        "id": "ax-absorbing-soundness",
        "axiom": "has_absorbing_operand",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_ABSORB_SOUNDNESS_PROBE,
        "rationale": (
            "the axiom encodes Implies(len==0, not Result()): the empty "
            "reduction admits no absorbing operand, so it never short-circuits "
            "to the annihilator cls.zero — confirmed on the real callee (empty -> "
            "identity element); the annihilator does short-circuit on a non-empty "
            "collection (predicate non-trivial). A collapse to the annihilator on "
            "the empty collection would be AXIOM-UNSOUND. It ALSO encodes the "
            "exclusivity clause Implies(Result(), not "
            "has_noncomparable_operand(operands)), checked against the REAL "
            "ordered scan cls._new_args_filter on collections carrying BOTH an "
            "absorbing and a non-comparable operand in BOTH orders: whichever "
            "decisive event the scan meets FIRST is the only one observed, so "
            "the two can never both hold. A collection reporting both events "
            "would be AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-reduction-defined-soundness",
        "axiom": "canonical_reduction_defined",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_DEFINED_SOUNDNESS_PROBE,
        "rationale": (
            "the axiom encodes Implies(len==0, Result()) and underpins "
            "(P-defined)/(P-total)/Exsures(ReductionUndefined). It models the "
            "canonical-set pass, a DIFFERENT observation from the ordered scan: "
            "the scan judges each operand alone (miscellaneous.py:521-523 at "
            "base_commit), while _find_localzeros -> _is_connected compares the "
            "survivors against one another (miscellaneous.py:552/574) and can "
            "propagate TypeError('Invalid comparison of complex ...') out of "
            "Expr.__ge__ (expr.py:295) for operands the scan passed over. The "
            "probe confirms on the real callee that (1) the EMPTY reduction "
            "cannot fail there (the encoded Ensures), (2) the predicate is "
            "vacuously true wherever the scan already decided — an absorbing "
            "operand still collapses the reduction to the annihilator in BOTH "
            "operand orders even alongside an operand the pass cannot place — and "
            "(3) it is NON-TRIVIAL: collections whose every operand the scan "
            "passes over and whose pass still fails do exist, so the model's "
            "failure leg is reachable rather than dead. A collection whose scan "
            "says 'ok' yet raises the scan's OWN error, or an empty reduction "
            "that fails, would be AXIOM-UNSOUND. Mirrors axiom_check.py."
        ),
    },
    {
        "id": "ax-canonical-count-soundness",
        "axiom": "canonical_count",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_COUNT_SOUNDNESS_PROBE,
        "rationale": (
            "the axiom encodes Result()>=0 and Implies(len==0, Result()==0), "
            "PARTIALLY — under Requires(canonical_reduction_defined(operands)). "
            "The real callee's observable branch outcome witnesses the count "
            "class: empty -> identity (count 0), single -> operand (count 1), "
            ">=2 -> aggregate (count>=2). The probe observes it only where that "
            "pass IS defined (plain symbols, which it compares without failing); "
            "the collections it cannot reduce are the "
            "ax-reduction-defined-soundness probe's subject and the model reads "
            "no count on them. A non-zero empty count would be AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-containment-all",
        "axiom": ("has_noncomparable_operand,has_absorbing_operand,"
                  "canonical_reduction_defined,canonical_count"),
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": (
            "three of the four axioms share a permission-only Requires "
            "(Acc(list_pred(operands),1/4)) with no value/length restriction; the "
            "model passes the same List[int] reference (any cardinality, opaque "
            "ids) to each, so every callee-input it can reach is trivially "
            "in-domain. canonical_count is PARTIAL — it also requires "
            "canonical_reduction_defined(operands) — so its containment is a REAL "
            "obligation, discharged by the verifier at every call site and "
            "contract use (the impl reads the count only behind the definedness "
            "guard; each count postcondition is a nested Implies whose antecedent "
            "establishes definedness first), which is why an unguarded read does "
            "not verify. The probe adds the witness that the guarded domain "
            "covers the branch classes the model distinguishes: each of the "
            "empty/single/two/many reductions reaches a DEFINED pass on the real "
            "callee, the empty one by the definedness axiom's own Ensures."
        ),
    },
]
