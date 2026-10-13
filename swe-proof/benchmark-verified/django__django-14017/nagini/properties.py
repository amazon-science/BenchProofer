# properties.py — PBT manifest for django__django-14017.
#
# NOT a Nagini module; an adversarial falsification battery the runner
# (swebench_nagini.pbt) parses and executes. Each SPEC_TESTS case is a full
# model.py variant that shares the FROZEN spec byte-for-byte (same_spec) and
# edits ONLY the # impl-start/# impl-end region; the runner stamps verify vs.
# reject against `expect`.
#
# Defended surface (from model.py / refinement.md / mapping.md):
#   combine(other_is_container, other_is_boolean_operand, other_empty,
#           self_empty, conn) -> Combined
# is the abstraction of Q._combine. ALL five inputs are pass-by-VALUE primitives
# (four bool, one int) — there is NO heap parameter, hence NO Acc(x,1/2)
# read-only input. So the FRAME-MUTATION class does NOT apply (there is nothing
# to overwrite to satisfy a postcondition vacuously); see 'assessment'.
#
# The postcondition's load-bearing clauses (all GROUNDED in the input args, no
# @Pure answer-key / ungrounded oracle to echo):
#   P1  Ensures(other_is_container or other_is_boolean_operand)              # accept-domain
#   P2  Ensures(Implies(other_empty, branch == 0))                          # branch select
#   P3  Ensures(Implies(not other_empty and self_empty, branch == 1))       # branch select
#   P4  Ensures(Implies(not other_empty and not self_empty, branch == 2))   # branch select
#   P5  Ensures(Implies(branch == 2, connector == conn))                    # merge carries conn
#   X1  Exsures(OperandTypeRejected, not other_is_container
#                                    and not other_is_boolean_operand)      # reject ONLY both-false
#   T1  Requires(MustTerminate(2))                                          # totality: must answer
# T1 is the totality obligation: Nagini is a partial-correctness verifier by
# default, so without it a diverging body would satisfy every value
# postcondition vacuously (verified rival: see weak-diverge-no-answer).
# The discriminating content of the gold change lives in P1+X1 (accept a
# non-container that is usable as a boolean filter condition); the branch/conn
# clauses P2-P5 pin the unchanged downstream identity/merge behaviour.

from pathlib import Path

INSTANCE = "django__django-14017"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The full gold impl region (everything between the impl markers). Each variant
# rewrites ONLY text inside this block, so same_spec is guaranteed.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    # impl-start
    if not (other_is_container or other_is_boolean_operand):
        raise OperandTypeRejected()

    # If the operand is empty, ignore it and just use the container (a copy).
    if other_empty:
        return Combined(0, conn)
    # Or if the container is empty, ignore it and just use the operand (a copy).
    elif self_empty:
        return Combined(1, conn)

    # Both sides non-empty: a fresh container under the requested connector,
    # joining the container and the operand.
    obj = Combined(2, conn)
    return obj
    # impl-end"""

assert _GOLD_IMPL in _BASE, "gold impl block drift — update _GOLD_IMPL"


# === 1. POSITIVE CONTROL (soundness) =======================================
# A structurally-DIFFERENT but behaviourally-IDENTICAL impl: compute the branch
# tag into a local first and use a single tail return, and order the emptiness
# checks differently (test self_empty inside the not-other_empty arm with an
# explicit else rather than an elif chain). Straight-line control flow, no fold
# / induction lemma needed, so the gold proof still discharges. MUST verify
# (else SPEC-TOO-STRONG).
_POS = _swap(
    _BASE,
    _GOLD_IMPL,
    """    # impl-start
    # Structural variant: same decision, reshaped control flow + single return.
    if not (other_is_boolean_operand or other_is_container):
        raise OperandTypeRejected()

    b = 2  # type: int
    if other_empty:
        b = 0
    else:
        if self_empty:
            b = 1
        else:
            b = 2
    result = Combined(b, conn)  # type: Combined
    return result
    # impl-end""",
)


# === 2. ADMISSIBILITY ======================================================
# The admissibility caller must live INSIDE the impl region (anything after the
# # impl-end marker is part of the canonical spec view and would break
# same_spec). Nagini cannot define a sibling top-level function between the
# in-body markers, and a self-call to combine recurses — so the admissibility
# probe is realised as the gold impl PROCEEDED BY an explicit reachability
# witness for the discriminating F2P shape. We construct the exact Combined
# result the F2P operand (Q() & Exists(...): non-container boolean operand,
# non-empty, into an empty container -> branch 1) must produce, and the
# symmetric merge shape (-> branch 2 carrying conn), asserting each satisfies
# the postcondition's branch/connector pins. If these legitimate, in-domain
# witnesses cannot be constructed/asserted the spec is internally inconsistent /
# PRECOND-TOO-STRONG. The gold decision is then executed normally, so the case
# still verifies as a faithful impl.
_ADMISS = _swap(
    _BASE,
    _GOLD_IMPL,
    """    # impl-start
    # Admissibility witnesses for the F2P operand shapes (constructed, asserted
    # against the postcondition's branch/connector pins, then discarded):
    #   Q() & Exists(is_poc): non-container boolean operand, non-empty, into an
    #   empty container -> branch 1 carrying conn.
    w1 = Combined(1, conn)  # type: Combined
    Assert(w1.branch == 1 and w1.connector == conn)
    #   Exists(is_poc) & Q(salary=...): same operand into a NON-empty container
    #   -> merge branch 2 carrying EXACTLY conn.
    w2 = Combined(2, conn)  # type: Combined
    Assert(w2.branch == 2 and w2.connector == conn)
    # Gold decision (faithful), so the case verifies end-to-end.
    if not (other_is_container or other_is_boolean_operand):
        raise OperandTypeRejected()
    if other_empty:
        return Combined(0, conn)
    elif self_empty:
        return Combined(1, conn)
    obj = Combined(2, conn)
    return obj
    # impl-end""",
)


# === 3. UNGROUNDED-ORACLE ECHO =============================================
# N/A: the postcondition is fully GROUNDED in the input args (the four boolean
# predicates and conn); there is NO @Pure answer-key / opaque marker an impl
# could echo without doing the work. There is therefore no wrong echo to build.
# The honest cheapest-impl positive control is the POS case above (it does the
# minimal decision and verifies). See 'assessment'.


# === 4. UNIQUENESS / PARTIAL-DOMAIN rivals (expect reject) =================

# 4a. PREPATCH NARROWED GUARD — the actual bug. Reject any non-container,
#     ignoring the boolean-operand predicate. Diverges on the discriminating
#     sub-domain (other_is_container=False, other_is_boolean_operand=True):
#     raises instead of accepting. Must be REJECTED by X1 (the Exsures permits
#     OperandTypeRejected ONLY when BOTH predicates are false).
_REJ_PREPATCH = _swap(
    _BASE,
    _GOLD_IMPL,
    """    # impl-start
    if not other_is_container:
        raise OperandTypeRejected()
    if other_empty:
        return Combined(0, conn)
    elif self_empty:
        return Combined(1, conn)
    obj = Combined(2, conn)
    return obj
    # impl-end""",
)

# 4b. MIRROR-NARROWED GUARD — accept only boolean operands, reject pure
#     same-kind containers. Diverges on the (other_is_container=True,
#     other_is_boolean_operand=False) sub-domain. Must be REJECTED by X1 (raises
#     where the spec forbids: at least one predicate is true).
_REJ_MIRROR = _swap(
    _BASE,
    _GOLD_IMPL,
    """    # impl-start
    if not other_is_boolean_operand:
        raise OperandTypeRejected()
    if other_empty:
        return Combined(0, conn)
    elif self_empty:
        return Combined(1, conn)
    obj = Combined(2, conn)
    return obj
    # impl-end""",
)

# 4c. ACCEPT-EVERYTHING — drop the rejection guard entirely; never raise.
#     Returns normally on the neither-acceptable operand (both predicates
#     false). Must be REJECTED by P1 Ensures(other_is_container or
#     other_is_boolean_operand): a normal return is reachable for an operand
#     that is neither.
_REJ_ACCEPT_ALL = _swap(
    _BASE,
    _GOLD_IMPL,
    """    # impl-start
    if other_empty:
        return Combined(0, conn)
    elif self_empty:
        return Combined(1, conn)
    obj = Combined(2, conn)
    return obj
    # impl-end""",
)

# 4d. SWAPPED IDENTITY BRANCHES — return the operand-copy tag (1) on an empty
#     OPERAND and the container-copy tag (0) on an empty container. Correct
#     accept-domain, wrong branch selection. Must be REJECTED by P2
#     Implies(other_empty, branch == 0).
_REJ_BRANCH_SWAP = _swap(
    _BASE,
    _GOLD_IMPL,
    """    # impl-start
    if not (other_is_container or other_is_boolean_operand):
        raise OperandTypeRejected()
    if other_empty:
        return Combined(1, conn)
    elif self_empty:
        return Combined(0, conn)
    obj = Combined(2, conn)
    return obj
    # impl-end""",
)

# 4e. WRONG MERGE CONNECTOR — accept-domain and branch selection correct, but
#     the merge carries a connector OTHER than the requested conn. Must be
#     REJECTED by P5 Implies(branch == 2, connector == conn). conn+1 is distinct
#     from conn for every int.
_REJ_CONN = _swap(
    _BASE,
    _GOLD_IMPL,
    """    # impl-start
    if not (other_is_container or other_is_boolean_operand):
        raise OperandTypeRejected()
    if other_empty:
        return Combined(0, conn)
    elif self_empty:
        return Combined(1, conn)
    obj = Combined(2, conn + 1)
    return obj
    # impl-end""",
)

# 4f. CONTROL-FLOW-EFFECT — accept the neither-operand by returning normally
#     (here pick branch 2) instead of raising. This is the raise-vs-return
#     discriminator made explicit: the spec's exceptional contract X1 plus the
#     normal-return accept-domain P1 must together forbid a normal return on the
#     both-false operand. Must be REJECTED (P1 fails on both-predicates-false).
#     Distinct from 4c: keeps a guard but on the WRONG (always-true) condition,
#     so it never raises and returns a merge tag.
_REJ_CFE = _swap(
    _BASE,
    _GOLD_IMPL,
    """    # impl-start
    if False:
        raise OperandTypeRejected()
    if other_empty:
        return Combined(0, conn)
    elif self_empty:
        return Combined(1, conn)
    obj = Combined(2, conn)
    return obj
    # impl-end""",
)


# 4g. NON-TERMINATION — diverges instead of answering on an accepted branch
#     (the audited weakness class). Correct guard, but the empty-container
#     identity branch spins forever, so every value postcondition holds only
#     vacuously under partial correctness. The totality obligation T1
#     Requires(MustTerminate(2)) cannot be discharged by an endless loop with
#     no strictly decreasing measure -> the obligation leak check REJECTS it.
#     Refinement: its faithful real patch widens the guard correctly but hangs
#     the empty-container branch, so combining a boolean operand into an empty
#     container never returns; the F2P tests time out -> does NOT resolve.
_REJ_DIVERGE = _swap(
    _BASE,
    _GOLD_IMPL,
    """    # impl-start
    if not (other_is_container or other_is_boolean_operand):
        raise OperandTypeRejected()
    if other_empty:
        return Combined(0, conn)
    elif self_empty:
        while True:
            Invariant(True)
    obj = Combined(2, conn)
    return obj
    # impl-end""",
)


SPEC_TESTS = [
    {
        "id": "pos-control-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS,
        "rationale": "structurally-different correct impl (computed branch local + single tail "
                     "return, nested-if instead of elif chain) keeps straight-line control flow; "
                     "no fold/induction lemma needed so the gold proof still discharges. Must "
                     "verify against P1-P5/X1, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "a positive-control caller invokes combine on the exact F2P operand shapes "
                     "(Q() & Exists(...): non-container boolean operand, non-empty, into empty/"
                     "non-empty container) and asserts the postcondition-pinned branch (1 then 2) "
                     "and connector. combine's Requires is empty, so a failure here would be "
                     "PRECOND-TOO-STRONG / an internally-inconsistent postcondition.",
    },
    {
        "id": "weak-prepatch-narrowed-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_PREPATCH,
        "refinement": "this IS the pre-patch bug (`if not isinstance(other, Q): raise TypeError`). "
                      "Its faithful real patch keeps the old narrow guard, so Q() & Exists(...) "
                      "still raises TypeError and the F2P tests test_boolean_expression_combined / "
                      "test_boolean_expression_combined_with_empty_Q FAIL -> does NOT resolve.",
        "rationale": "rejected by X1 Exsures(OperandTypeRejected, not other_is_container and not "
                     "other_is_boolean_operand): on (container=False, boolean=True) it raises, "
                     "which X1 permits ONLY when both predicates are false.",
    },
    {
        "id": "weak-mirror-narrowed-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_MIRROR,
        "refinement": "accepts only self-declared boolean operands and rejects same-kind Q "
                      "containers. A faithful patch with this guard would raise TypeError on "
                      "Q() & Q(...) and break the P2P CombinableTests (test_and/test_or, "
                      "test_reversed_and/or) which combine Q with Q -> does NOT resolve.",
        "rationale": "rejected by X1: on (container=True, boolean=False) it raises, but X1 forbids "
                     "rejecting when at least one predicate is true.",
    },
    {
        "id": "weak-accept-everything",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_ACCEPT_ALL,
        "refinement": "drops the rejection guard entirely. A faithful patch that accepts any "
                      "object (e.g. Value(1) or a plain int) would not raise TypeError on a "
                      "non-Q non-conditional operand, then crash downstream on .deconstruct()/"
                      ".add() and break the P2P tests that rely on _combine rejecting bad operands "
                      "-> does NOT resolve.",
        "rationale": "rejected by P1 Ensures(other_is_container or other_is_boolean_operand): on "
                     "the both-false operand it returns normally, violating the normal-return "
                     "accept-domain.",
    },
    {
        "id": "weak-branch-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_BRANCH_SWAP,
        "refinement": "swaps the two identity branches (empty operand -> operand-copy, empty "
                      "container -> container-copy). The real analogue returns type(other)(...) "
                      "when the OPERAND is empty (should be a copy of self) and type(self)(...) "
                      "when SELF is empty (should be a copy of other), so Exists(is_poc) & Q() "
                      "would yield an empty Q instead of an Exists-carrying node -> the F2P "
                      "with_empty_Q subtests FAIL -> does NOT resolve.",
        "rationale": "rejected by P2 Implies(other_empty, branch == 0): on an empty operand it "
                     "returns branch 1.",
    },
    {
        "id": "weak-wrong-merge-connector",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_CONN,
        "refinement": "the merge node carries conn+1 instead of the requested conn. The real "
                      "analogue sets obj.connector to the wrong connector (AND vs OR), so "
                      "Q(salary__lt=15) | Exists(is_poc) would build an AND node and "
                      "test_boolean_expression_combined would return the wrong rows -> does NOT "
                      "resolve.",
        "rationale": "rejected by P5 Implies(branch == 2, connector == conn): on the both-non-"
                     "empty merge it carries conn+1 != conn.",
    },
    {
        "id": "weak-diverge-no-answer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_DIVERGE,
        "refinement": "correct acceptance guard, but the empty-container identity branch spins "
                      "forever instead of returning the operand copy. The real analogue hangs "
                      "Q._combine whenever the calling container is empty, so combining a boolean "
                      "operand into an empty container never returns and the F2P tests time out "
                      "-> does NOT resolve.",
        "rationale": "rejected by T1 Requires(MustTerminate(2)): an endless loop with no strictly "
                     "decreasing measure fails the obligation leak check ('Loop might not take "
                     "all unsatisfied obligations from the context'). Under partial correctness "
                     "alone this variant VERIFIED — the totality obligation is load-bearing.",
    },
    {
        "id": "weak-control-flow-no-raise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_CFE,
        "refinement": "keeps a syntactic guard but on an always-false condition, so it NEVER "
                      "raises and returns a merge tag even for the neither-acceptable operand. "
                      "The raise/return difference is invisible to a pure value abstraction; the "
                      "real analogue would silently build a Q node from a junk operand instead of "
                      "raising TypeError, breaking the P2P guard-relying tests -> does NOT resolve.",
        "rationale": "rejected by P1 Ensures(other_is_container or other_is_boolean_operand): on "
                     "the both-false operand it returns normally; the exceptional contract X1 is "
                     "the only sanctioned outcome there. Control-flow-effect discriminator.",
    },
]


# No @ContractOnly axioms and no A-reference deep models in this bundle
# (meta.json axioms == [], deep_model_references == []; the axioms/pure regions
# of model.py are comment-only). The single soundness obligation — that the
# boolean-predicate abstraction equals the real post-patch Q._combine — is the
# bundle's axiom_check.py / G-AX concern, not a PBT axiom probe.
AXIOM_TESTS = []
