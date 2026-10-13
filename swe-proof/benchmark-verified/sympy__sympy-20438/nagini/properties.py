# properties.py — PBT manifest for sympy__sympy-20438. NOT a Nagini module; a
# record of adversarial falsification cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT.
#
# Defended surface (read from model.py / refinement.md / mapping.md):
#   * product_subset_of_finite(elems: List[int], finite_id) -> bool
#       READ-ONLY input  elems          (Acc(list_pred(elems), 1/2))
#       LOAD-BEARING post  Result() == all_in(ToSeq(elems), finite_id)
#       all_in is a GROUNDED oracle: it fully unfolds to member(finite_id, e)
#       over the ACTUAL input handles -- it is a function of the args, not an
#       opaque answer key, so there is no wrong "echo" to build (see assessment).
#       impl: back-to-front fold  res = member(finite_id, e) and res.
#   * finite_sets_equal(elems_a, id_a, elems_b, id_b) -> bool
#       READ-ONLY inputs elems_a, elems_b (both Acc(...,1/2))
#       LOAD-BEARING post  Result() == (all_in(a,id_b) and all_in(b,id_a))
#       impl: a_sub_b and b_sub_a via two calls to product_subset_of_finite.
#   * simplify_equality_route(both_arith, elems_a, id_a, elems_b, id_b) -> int
#       READ-ONLY inputs elems_a, elems_b (both Acc(...,1/2))
#       LOAD-BEARING post  Implies(both_arith, Result() == ARITH_PATH())
#         AND Implies(not both_arith, Result() != ARITH_PATH())
#         AND Implies(not both_arith, Result() == collection_outcome(
#                       all_in(a,id_b) and all_in(b,id_a)))
#       impl: guarded routing -- arithmetic path for both_arith, otherwise defer
#       to finite_sets_equal (the collection-equality decision). Pins the
#       operand-kind guard: a collection operand is never routed to ARITH_PATH().
#   * member: @Pure @ContractOnly axiom with NO value Ensures -- only purity +
#       totality relied on (A-consumed, unchanged FiniteSet.contains).
#       all_in folds are A-reference deep models (validated == real callee).
#
# Region-surgery (_swap on _BASE) edits ONLY inside the # impl-start/# impl-end
# regions, so every spec case is same_spec by construction (the frozen
# axioms/pure/pre/post-conditions are never touched).
from pathlib import Path

INSTANCE = "sympy__sympy-20438"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors (all strictly inside an impl region of _BASE).
# ---------------------------------------------------------------------------

# product_subset_of_finite gold impl body (back-to-front membership fold).
_PSOF_GOLD = """    res = True
    i = len(elems)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(elems), 1 / 2))
        Invariant(0 <= i and i <= len(elems))
        Invariant(res == all_in(ToSeq(elems).drop(i), finite_id))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        e = elems[i - 1]
        Assert(ToSeq(elems).drop(i - 1)[0] == e)
        Assert(ToSeq(elems).drop(i - 1).drop(1) == ToSeq(elems).drop(i))
        res = member(finite_id, e) and res
        i = i - 1
    Assert(ToSeq(elems).drop(0) == ToSeq(elems))
    return res"""

# finite_sets_equal gold impl body (mutual-subset conjunction).
_FSE_GOLD = """    a_sub_b = product_subset_of_finite(elems_a, id_b)
    b_sub_a = product_subset_of_finite(elems_b, id_a)
    return a_sub_b and b_sub_a"""

# simplify_equality_route gold impl body (operand-kind routing guard).
_ROUTE_GOLD = """    if both_arith:
        # Both operands arithmetic: take the unchanged arithmetic-reduction path.
        return ARITH_PATH()
    # At least one operand is a collection: do NOT attempt the arithmetic
    # reduction (which has no defined result for a collection operand); defer to
    # the collection-equality decision of behaviour (2).
    equal = finite_sets_equal(elems_a, id_a, elems_b, id_b)
    return collection_outcome(equal)"""


# ===========================================================================
# (1) FRAME-MUTATION — MANDATORY: elems is read-only (Acc(...,1/2)).
# A rival that WRITES to elems to drive the fold must be rejected for
# INSUFFICIENT PERMISSION (the loop holds only 1/2 of list_pred(elems), enough
# to read elems[i-1] but not to assign elems[i-1]=...). The gold invariants are
# kept VERBATIM so the rejection is attributable solely to the write.
# ===========================================================================
_frame_mut_psof = _swap(
    _BASE,
    _PSOF_GOLD,
    """    res = True
    i = len(elems)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(elems), 1 / 2))
        Invariant(0 <= i and i <= len(elems))
        Invariant(res == all_in(ToSeq(elems).drop(i), finite_id))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        e = elems[i - 1]
        Assert(ToSeq(elems).drop(i - 1)[0] == e)
        Assert(ToSeq(elems).drop(i - 1).drop(1) == ToSeq(elems).drop(i))
        res = member(finite_id, e) and res
        elems[i - 1] = e  # WRITE to read-only input -> insufficient permission
        i = i - 1
    Assert(ToSeq(elems).drop(0) == ToSeq(elems))
    return res""",
)

# Frame mutation on the second function's read-only inputs (write to elems_a).
_frame_mut_fse = _swap(
    _BASE,
    _FSE_GOLD,
    """    if len(elems_a) > 0:
        elems_a[0] = elems_a[0]  # WRITE to read-only input -> insufficient permission
    a_sub_b = product_subset_of_finite(elems_a, id_b)
    b_sub_a = product_subset_of_finite(elems_b, id_a)
    return a_sub_b and b_sub_a""",
)


# ===========================================================================
# (2) PARTIAL-DOMAIN (product_subset_of_finite) — correct on most inputs but
# DROPS the first enumerated element (stop the fold at i > 1, leaving res ==
# all_in(...drop(1)) instead of all_in(...)). Diverges exactly when the FIRST
# product element is the disagreeing one.
# Refinement: the faithful real patch would be
#     fuzzy_and(b_fs.contains(x) for x in list(a_ps)[1:])
# which SKIPS the first enumerated tuple. On F2P witness b.is_subset(d) with
# d={1}: every tuple of b is a NON-member, but skipping the first tuple while
# the rest are still non-members still yields False here -- so pick the sharper
# witness: a one-element product whose single tuple is a non-member would be
# decided True (vacuous), and more generally any product whose ONLY disagreeing
# element is the first is misdecided. test_issue_19378 b.is_subset(d) and the
# fuzz harness (which injects an alien tuple at arbitrary positions, incl. the
# first) would FAIL, so this faithful patch does NOT resolve.
# ===========================================================================
_partial_first_psof = _swap(
    _BASE,
    _PSOF_GOLD,
    """    res = True
    i = len(elems)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(elems), 1 / 2))
        Invariant(1 <= i and i <= len(elems))
        Invariant(res == all_in(ToSeq(elems).drop(i), finite_id))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        e = elems[i - 1]
        Assert(ToSeq(elems).drop(i - 1)[0] == e)
        Assert(ToSeq(elems).drop(i - 1).drop(1) == ToSeq(elems).drop(i))
        res = member(finite_id, e) and res
        i = i - 1
    return res  # never folds elems[0]: equals all_in(drop(1)), not all_in(all)""",
)


# ===========================================================================
# (3) CHEAPEST WRONG (product_subset_of_finite) — the pre-patch skeleton:
# decide containment by emptiness, NEVER reading member. This is the exact
# model_prepatch.py body.
# Refinement: corresponds to the pre-patch repo where NO (ProductSet,FiniteSet)
# rule exists, so the dispatcher returns None / falls back wrong. On the F2P
# witness b.is_subset(c) (true answer True, b non-empty) this yields False, and
# b.is_subset(d) likewise yields False -- the issue. It does NOT resolve.
# ===========================================================================
_empty_psof = _swap(
    _BASE,
    _PSOF_GOLD,
    """    empty = len(elems) == 0
    return empty  # ignores member entirely (pre-patch: containment never computed)""",
)


# ===========================================================================
# (4) PARTIAL-DOMAIN / one-direction (finite_sets_equal) — equality reduced to
# ONLY the first containment (drops b_sub_a).
# Refinement: faithful real patch would be
#     tfn[a.is_subset(b)]            # only lhs ⊆ rhs, not mutual
# For A={1}, B={1,2}: A⊆B True but B⊄A, so real equality is False while this
# returns True. More directly on an F2P-adjacent witness, any pair where the
# first set is a strict subset of the second is misdecided True. test_issue_19378
# / test_Eq assert S.false for non-equal sets where one-direction containment
# holds, so this faithful patch does NOT resolve.
# ===========================================================================
_one_dir_fse = _swap(
    _BASE,
    _FSE_GOLD,
    """    a_sub_b = product_subset_of_finite(elems_a, id_b)
    return a_sub_b  # only one direction; drops b ⊆ a""",
)


# ===========================================================================
# (5) POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT, while
# KEEPING the back-to-front fold (so the front-recursive all_in unfold still
# triggers — per pilot warning #3 a forward-append would need an unprovable
# all_in(a+b) lemma). The shape change: hoist the membership read into a named
# local `m`, restructure `res = member(...) and res` as `res = m and res`, and
# reorder the two framing Asserts. All gold invariants/framing pins are KEPT.
# If a faithful correct impl of this shape cannot verify => SPEC-TOO-STRONG.
# ===========================================================================
_pos_ctrl_psof = _swap(
    _BASE,
    _PSOF_GOLD,
    """    res = True
    i = len(elems)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(elems), 1 / 2))
        Invariant(0 <= i and i <= len(elems))
        Invariant(res == all_in(ToSeq(elems).drop(i), finite_id))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        e = elems[i - 1]
        Assert(ToSeq(elems).drop(i - 1).drop(1) == ToSeq(elems).drop(i))
        Assert(ToSeq(elems).drop(i - 1)[0] == e)
        m = member(finite_id, e)
        res = m and res
        i = i - 1
    Assert(ToSeq(elems).drop(0) == ToSeq(elems))
    return res""",
)


# ===========================================================================
# (6) ADMISSIBILITY — the precondition must admit a normal F2P-shaped input.
# finite_sets_equal already CALLS product_subset_of_finite twice, so
# establishing the callee's Requires (Acc(list_pred(elems),1/2)) from the
# caller's own halves IS the admissibility witness (the gold self-calls type-
# check the precondition against a real input). We confirm the precondition is
# satisfiable and ROUND-TRIPS by asserting both read-only inputs remain readable
# after the two calls -- the returned 1/2 permissions compose back. If this
# cannot verify => PRECOND-TOO-STRONG.
#
# NOTE (adjudication 2026-06-17): the prior body additionally issued a THIRD
# self-call `again = product_subset_of_finite(elems_a, id_b)` plus
# `Assert(again == a_sub_b)`. The two perm round-trip Asserts both PASS (the
# precondition is genuinely admissible), but that determinism Assert is a
# PROOF-ENGINEERING over-reach: Nagini cannot auto-discharge `again == a_sub_b`
# (it would need both callee-postcondition instances over ToSeq(elems_a) live
# at once with the ToSeq terms recognised identical), and inserting a call
# between b_sub_a and the return also breaks the finite_sets_equal postcondition
# framing. That is NOT the admissibility property under test, so it was removed.
# The retained Asserts are the faithful admissibility witness (perms round-trip,
# precondition satisfiable); spec untouched, edit confined to the impl region.
# ===========================================================================
_admiss_fse = _swap(
    _BASE,
    _FSE_GOLD,
    """    a_sub_b = product_subset_of_finite(elems_a, id_b)
    b_sub_a = product_subset_of_finite(elems_b, id_a)
    # admissibility: both read-only inputs remain readable after the two gold
    # self-calls -- the returned 1/2 permissions round-trip, so the precondition
    # Acc(list_pred(elems),1/2) admits a normal F2P-shaped input.
    Assert(Acc(list_pred(elems_a), 1 / 2))
    Assert(Acc(list_pred(elems_b), 1 / 2))
    return a_sub_b and b_sub_a""",
)


# ===========================================================================
# (7) NO-GUARD ROUTING (simplify_equality_route) — the pre-patch skeleton:
# the operand-kind guard is absent, so the arithmetic-reduction path is taken
# UNCONDITIONALLY (return ARITH_PATH()), even for a collection operand. This is
# the exact model_prepatch_3.py body.
# Refinement: corresponds to the PRE-PATCH repo where _eval_simplify has no
# isinstance(_, Expr) guard, so a collection equality falls through to
# dif = lhs - rhs / dif.equals(0) and raises AttributeError (the issue's
# Eq(b,c).simplify() traceback) -- the collection rule is never reached. It does
# NOT resolve (F2P test_issue_19378 expects Eq(c,b).simplify() is S.true).
# ===========================================================================
_no_guard_route = _swap(
    _BASE,
    _ROUTE_GOLD,
    """    # no operand-kind guard: always take the arithmetic-reduction path
    return ARITH_PATH()""",
)


# ===========================================================================
# (8) WRONG-OUTCOME ROUTING (simplify_equality_route) — keeps the guard (the
# collection branch is reached) but decides the collection equality by the
# WRONG fold: only one direction (drops b ⊆ a), so the returned collection
# outcome diverges whenever the two collections are not mutually contained.
# Refinement: a faithful real patch that reaches _eval_is_eq but reduces it to
# tfn[lhs.is_subset(rhs)] (one direction) -- F2P/test_Eq assert S.false for
# non-equal sets where one-direction containment holds, so it does NOT resolve.
# ===========================================================================
_wrong_outcome_route = _swap(
    _BASE,
    _ROUTE_GOLD,
    """    if both_arith:
        return ARITH_PATH()
    # collection branch reached, but decided by only one containment direction
    one_dir = product_subset_of_finite(elems_a, id_b)
    return collection_outcome(one_dir)""",
)


# ===========================================================================
# (9) POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT routing:
# the guard is rephrased as `if not both_arith: <collection branch> else: <arith>`
# (the two branches swapped in source order) and the collection result hoisted
# into a named local. Behaviour identical to gold. It MUST verify; if it cannot,
# the routing postcondition is SPEC-TOO-STRONG.
# ===========================================================================
_pos_ctrl_route = _swap(
    _BASE,
    _ROUTE_GOLD,
    """    if not both_arith:
        # collection branch: defer to the collection-equality decision
        equal = finite_sets_equal(elems_a, id_a, elems_b, id_b)
        out = collection_outcome(equal)
        return out
    # both operands arithmetic: take the unchanged arithmetic-reduction path
    return ARITH_PATH()""",
)


SPEC_TESTS = [
    {
        "id": "frame-mut-psof",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_mut_psof,
        "refinement": (
            "Writing back the (unchanged) handle is a no-op on the VALUE fold, "
            "so a 'faithful' real patch that mutates the enumerated product in "
            "place would still compute the same membership conjunction and could "
            "look correct on the F2P tests -- the value abstraction cannot see "
            "the write. The spec must reject it on PERMISSION grounds: the gold "
            "contract grants only Acc(list_pred(elems),1/2), a read-only view of "
            "the product enumeration, exactly matching the real rule which only "
            "iterates `for x in a_ps`. A patch that mutates a_ps would corrupt a "
            "shared/cached ProductSet and is not what the gold patch does."
        ),
        "rationale": (
            "Rejection comes from the permission system: elems[i-1]=e needs full "
            "write permission to list_pred(elems) but the precondition/invariant "
            "grant only 1/2. INSUFFICIENT PERMISSION, not a postcondition failure."
        ),
    },
    {
        "id": "frame-mut-fse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_mut_fse,
        "refinement": (
            "elems_a[0]=elems_a[0] is a value no-op, so a real patch mutating one "
            "operand of the equality test would still produce the mutual-subset "
            "conjunction and pass the F2P value checks; the abstraction is blind "
            "to the write. Both equality operands are read-only (Acc(...,1/2)) "
            "because the real _eval_is_eq only reads lhs/rhs via is_subset -- it "
            "never mutates them. A mutating patch is unfaithful."
        ),
        "rationale": (
            "Rejection from the permission system: assigning elems_a[0] needs "
            "full list_pred(elems_a) permission; the caller holds only 1/2."
        ),
    },
    {
        "id": "partial-first-psof",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _partial_first_psof,
        "refinement": (
            "Stopping the fold at i>1 yields Result == all_in(drop(1)): the FIRST "
            "enumerated tuple is never membership-checked. The faithful real patch "
            "is fuzzy_and(b_fs.contains(x) for x in list(a_ps)[1:]) -- it skips the "
            "first product element. On any product whose first enumerated tuple is "
            "the disagreeing one (a non-member while the rest are members, or a "
            "member while the rest fix the answer) the decision flips. The fuzz "
            "harness in axiom_check.py injects an alien tuple at arbitrary positions "
            "including the first, and test_issue_19378's b.is_subset(d) sweep would "
            "be misdecided, so the patch does NOT resolve."
        ),
        "rationale": (
            "Rejection from the postcondition Result()==all_in(ToSeq(elems),"
            "finite_id): the returned value equals all_in over the tail drop(1), "
            "not the full sequence, so the equality fails for any elems whose head "
            "membership differs from True."
        ),
    },
    {
        "id": "empty-cheapest-psof",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _empty_psof,
        "refinement": (
            "Deciding containment by emptiness (the model_prepatch.py body) never "
            "reads member, so it equals len==0 not the membership conjunction. The "
            "faithful real correspondent is the PRE-PATCH repo with NO "
            "(ProductSet,FiniteSet) dispatch rule: b.is_subset(c) returns None and "
            "b.is_subset(d) is wrong -- the exact reported bug. It does NOT resolve "
            "(F2P test_issue_19378 expects b.is_subset(c) is True, b non-empty)."
        ),
        "rationale": (
            "Rejection from the postcondition: True/False driven by len(elems)==0 "
            "is not all_in(ToSeq(elems),finite_id) whenever the product is "
            "non-empty and some element's membership is False (or all True)."
        ),
    },
    {
        "id": "one-direction-fse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _one_dir_fse,
        "refinement": (
            "Returning only a_sub_b reduces equality to lhs ⊆ rhs, dropping the "
            "reverse containment. The faithful real patch tfn[a.is_subset(b)] "
            "decides A=={1}, B=={1,2} as True (A⊆B) though they are unequal. The "
            "F2P/test_Eq witnesses assert S.false for non-equal sets where "
            "one-direction containment holds, so the patch does NOT resolve."
        ),
        "rationale": (
            "Rejection from the postcondition Result()==(all_in(a,id_b) and "
            "all_in(b,id_a)): dropping the second conjunct makes Result true when "
            "all_in(a,id_b) holds but all_in(b,id_a) is false."
        ),
    },
    {
        "id": "pos-control-reshape-psof",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_ctrl_psof,
        "rationale": (
            "A structurally-different but CORRECT impl (membership hoisted to a "
            "named local, the two framing Asserts reordered) that keeps the "
            "back-to-front fold and ALL gold invariants/framing pins. It must "
            "verify; if it cannot, the postcondition is SPEC-TOO-STRONG. The shape "
            "change is local-variable / statement-reorder only (pilot-safe: no "
            "loop-direction flip, no dropped framing assert)."
        ),
    },
    {
        "id": "admiss-fse-selfcall",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss_fse,
        "rationale": (
            "The precondition Acc(list_pred(elems),1/2) must admit a normal "
            "F2P-shaped input: finite_sets_equal establishes the callee's Requires "
            "from its own 1/2 halves (the gold self-calls type-check the "
            "precondition against a real input), and the returned permissions "
            "round-trip -- both lists remain readable after the calls. If this "
            "cannot verify, the precondition is PRECOND-TOO-STRONG. Uses only "
            "permissions the gold proof already holds."
        ),
    },
    {
        "id": "no-guard-route",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _no_guard_route,
        "refinement": (
            "Returning ARITH_PATH() unconditionally drops the operand-kind guard: "
            "a collection equality is routed into the arithmetic-reduction path. "
            "The faithful real correspondent is the PRE-PATCH _eval_simplify with "
            "no isinstance(_, Expr) guard, where a Set equality falls through to "
            "dif = lhs - rhs / dif.equals(0) and raises AttributeError (the issue's "
            "Eq(b,c).simplify() traceback) -- the collection rule is never reached. "
            "F2P test_issue_19378 expects Eq(c,b).simplify() is S.true, so it does "
            "NOT resolve."
        ),
        "rationale": (
            "Rejection from the postcondition Implies(not both_arith, Result() != "
            "ARITH_PATH()): a collection operand (both_arith False) returns "
            "ARITH_PATH(), violating the guard's defer-to-collection-rule contract."
        ),
    },
    {
        "id": "wrong-outcome-route",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _wrong_outcome_route,
        "refinement": (
            "Keeps the guard (the collection branch is reached) but decides the "
            "collection equality by only one containment direction (drops b subset "
            "a). The faithful real patch reduces _eval_is_eq to "
            "tfn[lhs.is_subset(rhs)]; F2P/test_Eq assert S.false for non-equal sets "
            "where one-direction containment holds, so it does NOT resolve."
        ),
        "rationale": (
            "Rejection from the postcondition Result() == collection_outcome("
            "all_in(a,id_b) and all_in(b,id_a)): dropping the second conjunct makes "
            "the collection outcome wrong whenever all_in(a,id_b) holds but "
            "all_in(b,id_a) is false."
        ),
    },
    {
        "id": "pos-control-route-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_ctrl_route,
        "rationale": (
            "A structurally-different but CORRECT routing (the two guard branches "
            "swapped in source order, the collection result hoisted into a named "
            "local) with behaviour identical to gold. It must verify; if it cannot, "
            "the routing postcondition is SPEC-TOO-STRONG."
        ),
    },
]


# ===========================================================================
# AXIOM LANE — the bundle has one @ContractOnly axiom (member) and two
# A-reference deep models (the all_in folds). We mirror axiom_check.py's logic
# (read on the HOST at load time, embedded into each self-contained probe so the
# runner -- which mounts ONLY the probe at /work -- can run it in the instance
# image with the gold patch applied). Each probe imports only stdlib + sympy,
# prints a diagnostic, and sys.exit(0) iff the obligation holds.
# ===========================================================================

# member axiom: A-consumed. Its ONLY contract is purity (determinism) + totality
# (a definite truth value), NO value Ensures. Soundness probe: real
# FiniteSet.contains is deterministic and returns a definite bool (S.true/S.false,
# never None) on concrete element handles -- the weakest sufficient contract the
# spec relies on. Containment probe: every callee-input the MODEL can reach is a
# concrete element handle (mapping.md §2: tuples/integers from a fully-decidable
# product / finite set), which is exactly the domain on which contains is
# definite -- the caller never reaches a symbolic element for which contains
# would be undecided.
_MEMBER_SOUND_PROBE = r'''
import itertools, random, sys
from sympy import FiniteSet, ProductSet, S
from sympy.abc import x

FAIL = []
def fail(m):
    FAIL.append(m); print("VIOLATION:", m)

def real_member(finite, el):
    c1 = finite.contains(el)
    c2 = finite.contains(el)
    if c1 != c2:
        fail("contains non-deterministic: %r in %r -> %r vs %r" % (el, finite, c1, c2))
    if c1 not in (S.true, S.false):
        fail("contains not a definite bool: %r in %r -> %r" % (el, finite, c1))
    return c1 is S.true

# F2P witnesses (the exact concrete element handles the caller reaches)
a = FiniteSet(1, 2)
b = ProductSet(a, a)
c = FiniteSet((1, 1), (1, 2), (2, 1), (2, 2))
d = FiniteSet(1)
for prod, fin in ((b, c), (b, d)):
    for el in list(prod):
        real_member(fin, el)
        # boundary: an alien handle definitely NOT in the set must still be definite
        real_member(fin, (9, 9))

# Fuzz: concrete integer / tuple-of-integer handles vs random finite targets.
# These are EXACTLY the handles the model can reach (concrete, fully decidable).
rng = random.Random(20438)
pool = [0, 1, 2, 3]
for _ in range(3000):
    k = rng.randint(1, 2)
    comps = [FiniteSet(*rng.sample(pool, rng.randint(1, 3))) for _ in range(k)]
    prod = ProductSet(*comps)
    universe = list(itertools.product(*[list(cc) for cc in comps]))
    m = rng.randint(0, len(universe))
    chosen = rng.sample(universe, m)
    tuples = [t[0] if len(t) == 1 else t for t in chosen]
    fin = FiniteSet(*tuples) if tuples else FiniteSet()
    for el in list(prod):
        real_member(fin, el)
    # sentinel non-members
    real_member(fin, (7, 7) if k == 2 else 7)

if FAIL:
    print("MEMBER AXIOM FAILED: %d violation(s)" % len(FAIL)); sys.exit(1)
print("MEMBER OK: FiniteSet.contains deterministic + definite-bool total on every "
      "concrete handle the caller reaches (weakest sufficient contract holds).")
sys.exit(0)
'''

# A-reference 1: product_subset_of_finite's all_in fold == the real
# ProductSet.is_subset(FiniteSet) decision, asserted DIRECTLY on the enumerated
# product elements (no double-mask). Soundness: the deep fold must equal the real
# post-patch callee on every caller-reachable input; fuzz alien-tuple injection at
# the first/last/interior positions and the raise/None boundary.
_SUBSET_REF_PROBE = r'''
import itertools, random, sys
from sympy import FiniteSet, ProductSet, S

FAIL = []
def fail(m):
    FAIL.append(m); print("VIOLATION:", m)

def real_member(finite, el):
    cc = finite.contains(el)
    if cc not in (S.true, S.false):
        fail("contains not definite: %r in %r -> %r" % (el, finite, cc))
        return False
    return cc is S.true

def all_in(elems, finite):
    return all(real_member(finite, e) for e in elems)

def check_subset(prod, finite):
    elems = list(prod)
    model = all_in(elems, finite)
    real = prod.is_subset(finite)
    if real is not True and real is not False:
        fail("is_subset not definite: %r.is_subset(%r) -> %r" % (prod, finite, real)); return
    if bool(real) != model:
        fail("subset mismatch: %r.is_subset(%r) real=%r model(all_in)=%r"
             % (prod, finite, real, model))

# F2P witnesses
a = FiniteSet(1, 2); b = ProductSet(a, a)
c = FiniteSet((1, 1), (1, 2), (2, 1), (2, 2)); d = FiniteSet(1)
if b.is_subset(c) is not True:  fail("F2P b.is_subset(c)!=True: %r" % (b.is_subset(c),))
if b.is_subset(d) is not False: fail("F2P b.is_subset(d)!=False: %r" % (b.is_subset(d),))
check_subset(b, c); check_subset(b, d)

# Fuzz with alien-tuple injection at first/last/interior positions so a
# fold that skips any one position would diverge here.
rng = random.Random(120438)
pool = [0, 1, 2, 3]
for _ in range(4000):
    k = rng.randint(1, 2)
    comps = [FiniteSet(*rng.sample(pool, rng.randint(1, 3))) for _ in range(k)]
    prod = ProductSet(*comps)
    universe = list(itertools.product(*[list(cc) for cc in comps]))
    m = rng.randint(0, len(universe))
    chosen = list(rng.sample(universe, m))
    r = rng.random()
    if r < 0.33 and chosen:
        chosen[0] = (9, 9) if k == 2 else (9,)            # corrupt FIRST
    elif r < 0.66 and chosen:
        chosen[-1] = (9, 9) if k == 2 else (9,)           # corrupt LAST
    tuples = [t[0] if len(t) == 1 else t for t in chosen]
    fin = FiniteSet(*tuples) if tuples else FiniteSet()
    try:
        check_subset(prod, fin)
    except Exception as e:
        fail("subset fuzz raised %r on prod=%r fin=%r" % (e, prod, fin))

if FAIL:
    print("SUBSET A-REF FAILED: %d violation(s)" % len(FAIL)); sys.exit(1)
print("SUBSET A-REF OK: ProductSet.is_subset(FiniteSet) == all_in fold on every "
      "F2P witness + 4000 fuzz products (first/last/interior corruptions caught).")
sys.exit(0)
'''

# A-reference 2: finite_sets_equal's mutual-subset fold == real
# Eq(A,B).simplify(). Soundness on F2P witnesses + fuzz; both directions exercised
# (one-direction-true / mutual-false pairs included).
_EQUAL_REF_PROBE = r'''
import random, sys
from sympy import FiniteSet, ProductSet, Eq, S, Interval

FAIL = []
def fail(m):
    FAIL.append(m); print("VIOLATION:", m)

def real_member(finite, el):
    cc = finite.contains(el)
    if cc not in (S.true, S.false):
        fail("contains not definite: %r in %r -> %r" % (el, finite, cc)); return False
    return cc is S.true

def all_in(elems, finite):
    return all(real_member(finite, e) for e in elems)

def check_equal(A, B):
    model = all_in(list(A), B) and all_in(list(B), A)
    real = Eq(A, B).simplify()
    if real is not S.true and real is not S.false:
        fail("Eq not definite: Eq(%r,%r).simplify()=%r" % (A, B, real)); return
    if (real is S.true) != model:
        fail("equality mismatch: Eq(%r,%r).simplify()=%r model(mutual-subset)=%r"
             % (A, B, real, model))

# F2P witnesses
a = FiniteSet(1, 2); b = ProductSet(a, a)
c = FiniteSet((1, 1), (1, 2), (2, 1), (2, 2))
if Eq(c, b).simplify() is not S.true:  fail("F2P Eq(c,b)!=S.true: %r" % (Eq(c,b).simplify(),))
if Eq(a, c).simplify() is not S.false: fail("F2P Eq(a,c)!=S.false: %r" % (Eq(a,c).simplify(),))
if Eq(ProductSet(FiniteSet(1), FiniteSet(2)), Interval(1, 2)) is not S.false:
    fail("F2P(test_Eq) Eq(ProductSet({1},{2}),Interval(1,2))!=S.false")
check_equal(c, b); check_equal(a, c)

# one-direction-true / mutual-false discriminators (catch a dropped conjunct)
for (A, B) in [(FiniteSet(1), FiniteSet(1, 2)),
               (FiniteSet(1, 2), FiniteSet(1)),
               (FiniteSet(1, 2), FiniteSet(2, 3))]:
    check_equal(A, B)

# Fuzz pairs of small-integer finite sets (both equal and unequal).
rng = random.Random(220438)
pool = [0, 1, 2, 3]
for _ in range(3000):
    sa = FiniteSet(*rng.sample(pool, rng.randint(1, 4)))
    sb = FiniteSet(*rng.sample(pool, rng.randint(1, 4)))
    try:
        check_equal(sa, sb)
    except Exception as e:
        fail("equal fuzz raised %r on %r,%r" % (e, sa, sb))

if FAIL:
    print("EQUAL A-REF FAILED: %d violation(s)" % len(FAIL)); sys.exit(1)
print("EQUAL A-REF OK: Eq(A,B).simplify() == mutual-subset fold on every F2P "
      "witness + one-direction discriminators + 3000 fuzz pairs.")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-member-sound",
        "axiom": "member",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _MEMBER_SOUND_PROBE,
        "rationale": (
            "member's only obligation is purity (determinism) + totality (definite "
            "bool) -- no value Ensures. If the real FiniteSet.contains were "
            "non-deterministic or returned None/unevaluated on a concrete handle "
            "the caller reaches, the axiom would be AXIOM-UNSOUND. The probe also "
            "covers containment: every handle exercised is concrete (the only kind "
            "the model can pass), and contains is definite on exactly that domain."
        ),
    },
    {
        "id": "ax-subset-ref",
        "axiom": "all_in (product_subset_of_finite deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _SUBSET_REF_PROBE,
        "rationale": (
            "A-reference: the all_in fold must equal the real post-patch "
            "ProductSet.is_subset(FiniteSet) on every caller-reachable (concrete) "
            "product. Asserted directly on enumerated elements (no double-mask) "
            "with alien-tuple injection at first/last/interior positions; any "
            "divergence is an A-reference unsoundness (verify would not imply "
            "resolve)."
        ),
    },
    {
        "id": "ax-equal-ref",
        "axiom": "finite_sets_equal mutual-subset deep model",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _EQUAL_REF_PROBE,
        "rationale": (
            "A-reference: the mutual-subset fold must equal real "
            "Eq(A,B).simplify() on every caller-reachable concrete finite-set pair, "
            "including one-direction-true/mutual-false discriminators that would "
            "expose a dropped conjunct. Divergence is an A-reference unsoundness."
        ),
    },
]
