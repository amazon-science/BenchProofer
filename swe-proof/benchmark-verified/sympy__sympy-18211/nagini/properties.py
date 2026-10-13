# properties.py — PBT falsification battery for sympy__sympy-18211.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a full model.py variant built by region-surgery that edits ONLY
# inside the `# impl-start` / `# impl-end` block of `solution_set_of_relation`
# (the two helper-class constructors' impl regions are left byte-identical), so
# the frozen spec — axioms, pure helpers, pre/post-conditions, signatures — is
# untouched and markers.same_spec holds. The runner stamps each with
# verify(host, Nagini) + same_spec.
#
# ---------------------------------------------------------------------------
# Defended surface (the spec this battery attacks)
#
#   solution_set_of_relation(rel: Relation) -> SolutionSet
#
#   `rel` is a READ-ONLY input: every field is held at Acc(rel.field, 1/2)
#   (Requires/Ensures both half-permission), so the function may READ rel but
#   may NEVER write it. => the FRAME-MUTATION probe is MANDATORY.
#
#   Precondition: rel.n_free == 1 (univariate) and rel.solvability in {0,1}
#   (the stated two-way solver domain: 0 = determined, 1 = undecided). No other
#   constraint.
#
#   Postcondition (three load-bearing obligations):
#     (P-tot) TOTALITY — no Exsures is declared, so the method must RETURN
#             NORMALLY on BOTH tags; it may never let the solver's
#             SolverUndecided escape.
#     (P0) determined tag (solvability == 0):
#             Result().is_fallback == False AND Result().cond == solved_cond(rel)
#             AND Result().sym == solved_sym(rel)
#             AND Result().over_reals == solved_reals(rel)
#          i.e. a genuine solver set (not the fabricated fallback), pinned
#          FIELD-FOR-FIELD to the solver's OWN returned set via the three
#          value-abstract accessors solved_cond / solved_sym / solved_reals.
#     (P1) undecided tag (solvability == 1):
#             Result().is_fallback == True AND Result().cond == rel.token AND
#             Result().sym == rel.sym AND Result().over_reals == True
#          i.e. the symbolic fallback built directly from the relation.
#
#   The discriminating change is purely CONTROL-FLOW / EXCEPTION-HANDLING: the
#   pre-patch returned the solver result directly (no handler), so on the
#   undecided tag SolverUndecided escaped and (P-tot) was violated
#   (== model_prepatch.py). The gold patch wraps the call in
#   try/except SolverUndecided and, on the signal, builds the fallback.
#
# ---------------------------------------------------------------------------
# Oracle-grounding note (ungrounded-oracle-echo class — why a WRONG echo does
# NOT exist here, directive 2):
#
#   The determined branch is pinned to solved_cond(rel) / solved_sym(rel) /
#   solved_reals(rel), three @Pure @ContractOnly accessors. But each is
#   GROUNDED in the input: a deterministic pure function of `rel`, and the
#   solve_univariate axiom's Ensures already forces the solver's OWN return to
#   carry exactly those three field values. So an impl that branches on
#   rel.solvability and builds
#   SolutionSet(False, solved_cond(rel), solved_sym(rel), solved_reals(rel))
#   directly produces the SAME fields the real solver returns — it is CORRECT,
#   not a wrong echo. There is no opaque
#   answer-key whose echo would diverge from the truth. We therefore (a) do NOT
#   include a "wrong echo" reject case (it would be a true-positive that verifies
#   AND resolves, not a defect), and (b) instead use that explicit-branch shape
#   as a structurally-different POSITIVE CONTROL (it must verify), and pin the
#   real spec strength with the partial-domain / control-flow / frame attacks
#   below, which DO diverge from the gold behaviour.

from pathlib import Path

INSTANCE = "sympy__sympy-18211"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl-region body of solution_set_of_relation (everything
# between its # impl-start / # impl-end markers, markers exclusive). Every
# variant is produced by _swap on _BASE touching ONLY text inside this block.
_GOLD_IMPL = """    syms = rel.n_free
    Assert(syms == 1)
    x = rel.sym
    try:
        xset = solve_univariate(rel)  # type: SolutionSet
    except SolverUndecided:
        # The solver is undecided: build the symbolic fallback set directly from
        # the relation (its defining condition), the variable, over the reals.
        xset = SolutionSet(True, rel.token, x, True)
    return xset"""

# Sanity: the gold impl text must appear verbatim and uniquely in _BASE.
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block drift — re-sync _GOLD_IMPL"


# ---------------------------------------------------------------------------
# 1. POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT.
#    Instead of try/except, branch EXPLICITLY on the read-only tag
#    rel.solvability (read at the 1/2 permission held). For the determined tag
#    it still CALLS the solver (so the determined result is the solver's own set,
#    cond == solved_cond(rel)); for the undecided tag it builds the fallback
#    WITHOUT entering the try (the solver would raise, so we never call it). This
#    is a faithful correct shape — it makes both postcondition branches hold and
#    nothing escapes. It does NOT drop any obligation: the determined branch is
#    discharged exactly as the gold's normal-return path, the undecided branch as
#    the gold's except path. MUST verify; else SPEC-TOO-STRONG.
#
#    Note: we keep the call to solve_univariate(rel) on the determined tag so the
#    proof obtains Result().cond == solved_cond(rel) from the axiom's Ensures
#    (the only sound way to get that pin) — no induction/fold lemma is needed, so
#    this is a safe positive control (pilot bug #2/#3 avoided: no dropped framing
#    assert, no forward-append-vs-fold).
#
#    PROOF-ENGINEERING NOTE (why the determined-branch call is wrapped in a
#    try/except SolverUndecided, even though solvability==0 makes the except dead):
#    solve_univariate declares Exsures(SolverUndecided, ...). Nagini discharges a
#    method's "raises no exceptions" obligation SYNTACTICALLY — a call to a method
#    that declares an Exsures must be caught (or the caller must re-declare it),
#    EVEN WHEN the current path condition (here rel.solvability == 0) contradicts
#    the Exsures' condition (rel.solvability == 1) and so makes the exceptional
#    edge semantically infeasible. The verifier does not fold the branch's
#    path-condition into the callee's exceptional postcondition to prove the edge
#    unreachable; it requires a syntactic handler. So an UNCAUGHT determined-tag
#    call leaves the method-level no-escape obligation undischargeable
#    ("Exhale might fail. Assertion 'method raises no exceptions' might not hold")
#    — a PROOF GAP, NOT the spec rejecting a correct output. The except clause is
#    provably dead under the solvability==0 guard (it reconstructs the same
#    fallback the undecided branch would), so the OUTPUT is byte-identically
#    correct and the impl stays structurally different from the gold (it branches
#    explicitly on the read-only tag rather than letting try/except drive the
#    dichotomy). Verifies in 24s; same_spec preserved (edit inside impl region
#    only). Without the handler the case is a false SPEC-TOO-STRONG.
_POS_BRANCH_IMPL = """    syms = rel.n_free
    Assert(syms == 1)
    x = rel.sym
    if rel.solvability == 0:
        try:
            xset = solve_univariate(rel)  # type: SolutionSet
        except SolverUndecided:
            # Unreachable under the solvability==0 guard (the axiom's Exsures
            # condition is solvability==1), but the syntactic handler discharges
            # the method's no-escape obligation; the OUTPUT is the same fallback.
            xset = SolutionSet(True, rel.token, x, True)
    else:
        # solvability == 1: the solver would raise; build the fallback directly.
        xset = SolutionSet(True, rel.token, x, True)
    return xset"""


# ---------------------------------------------------------------------------
# 2. ADMISSIBILITY — the precondition must ACCEPT a normal F2P-shaped input.
#    The F2P relation Eq(x*cos(x) - 3*sin(x), 0) is univariate (n_free == 1) and
#    UNDECIDED (solvability == 1, the solver raises NotImplementedError). We keep
#    the full gold impl and add, at the top, derivable assertions that the
#    precondition admits exactly such an input: a 1/4 read share of each field is
#    obtainable from the 1/2 held, the univariate count is 1, and the tag lies in
#    the two-way domain {0,1}. If this fails to verify => PRECOND-TOO-STRONG.
_ADMISS_IMPL = """    Assert(Acc(rel.n_free, 1 / 4) and Acc(rel.token, 1 / 4))
    Assert(Acc(rel.sym, 1 / 4) and Acc(rel.solvability, 1 / 4))
    Assert(rel.n_free == 1)
    Assert(rel.solvability == 0 or rel.solvability == 1)
""" + _GOLD_IMPL


# ---------------------------------------------------------------------------
# 3. FRAME-MUTATION (MANDATORY — read-only input). A rival that WRITES to the
#    read-only field rel.solvability so it can dodge the dichotomy: it flips the
#    tag to 1 and then unconditionally returns the fallback. With only
#    Acc(rel.solvability, 1/2) the assignment rel.solvability = 1 needs FULL
#    permission and MUST be rejected for insufficient permission. Every postcond
#    obligation it would otherwise satisfy is kept reachable, so the rejection is
#    attributable to the WRITE, not to a proof gap. expect=reject.
#
#    Refinement: the repo callee receives `self`, an IMMUTABLE Sympy Relational
#    (Basic instances are immutable — no rebindable solvability attribute exists;
#    the "is it solvable" fact is computed inside solve_univariate_inequality,
#    not a writable field of self). A faithful real patch cannot mutate `self` to
#    force the fallback branch; one that, per impossibility, forced every relation
#    down the fallback path would return ConditionSet(x, self, Reals) even for a
#    DETERMINED relation, so the P2P test_univariate_relational_as_set (which
#    observes the real solver sets, e.g. (x-1)*(x-2) > 0 -> a genuine Interval
#    union) would FAIL. So a verifying mutator is a true verify-not-resolve break.
_FRAME_MUTATE_IMPL = """    syms = rel.n_free
    Assert(syms == 1)
    x = rel.sym
    rel.solvability = 1
    return SolutionSet(True, rel.token, x, True)"""


# ---------------------------------------------------------------------------
# 4. CONTROL-FLOW-EFFECT (totality dropped) — the LITERAL pre-patch bug. Remove
#    the handler and return the solver result directly. On the undecided tag the
#    solver raises SolverUndecided, which escapes — but the frozen spec declares
#    NO Exsures, so the totality obligation ("method raises no exceptions") is
#    unprovable. This is exactly model_prepatch.py. expect=reject.
#
#    Refinement: this is the pre-patch _eval_as_set (return
#    solve_univariate_inequality(self, x, relational=False) with no try/except).
#    On the F2P relation Eq(x*cos(x) - 3*sin(x), 0) the real solver raises
#    NotImplementedError, which propagates out of as_set() instead of returning
#    ConditionSet(x, self, Reals) — F2P test_issue_18188 FAILS. The canonical
#    verify-not-resolve rival (== model_prepatch.py / G-DIFF).
_NO_HANDLER_IMPL = """    syms = rel.n_free
    Assert(syms == 1)
    x = rel.sym
    xset = solve_univariate(rel)  # type: SolutionSet
    return xset"""


# ---------------------------------------------------------------------------
# 5. PARTIAL-DOMAIN (wrong fallback condition) — correct on the determined tag
#    and on totality, but on the undecided tag builds a fallback whose defining
#    condition is some OTHER token (rel.sym, the variable's identity) rather than
#    rel.token (the relation's identity). is_fallback/over_reals/sym are still
#    correct, so it fails ONLY on the (P1) clause Result().cond == rel.token.
#    expect=reject.
#
#    Refinement: a real patch that built ConditionSet(x, x, S.Reals) — using the
#    bound symbol as the CONDITION instead of `self` — produces
#    ConditionSet(x, x, Reals) (a degenerate "x is real" set, not the relation's
#    solution set). On F2P Eq(x*cos(x) - 3*sin(x), 0).as_set() the expected
#    ConditionSet(x, Eq(x*cos(x) - 3*sin(x), 0), Reals) would NOT be produced
#    (the condition is the relation, not x) — test_issue_18188 FAILS. So a
#    verifying rival is a true verify-not-resolve break.
_WRONG_COND_IMPL = """    syms = rel.n_free
    Assert(syms == 1)
    x = rel.sym
    try:
        xset = solve_univariate(rel)  # type: SolutionSet
    except SolverUndecided:
        xset = SolutionSet(True, rel.sym, x, True)
    return xset"""


# ---------------------------------------------------------------------------
# 6. UNIQUENESS (fallback not flagged as fallback) — on the undecided tag it
#    returns a set with the right cond/sym/over_reals but is_fallback == False.
#    Fails ONLY on the (P1) clause Result().is_fallback == True. expect=reject.
#
#    Refinement: this corresponds to a real patch that, on the
#    NotImplementedError, returned a CONCRETE solver-flavoured set rather than the
#    ConditionSet fallback — e.g. returning S.Reals (a UniversalSet) instead of
#    ConditionSet(x, self, S.Reals). On F2P test_issue_18188, as_set() would then
#    return Reals (or any non-ConditionSet), not the expected
#    ConditionSet(x, Eq(...), Reals) — the assertion compares for equality and
#    FAILS. is_fallback is the modeled observable that distinguishes "a genuine
#    solver set" from "the symbolic ConditionSet fallback"; flipping it is a true
#    verify-not-resolve break.
_NOT_FALLBACK_IMPL = """    syms = rel.n_free
    Assert(syms == 1)
    x = rel.sym
    try:
        xset = solve_univariate(rel)  # type: SolutionSet
    except SolverUndecided:
        xset = SolutionSet(False, rel.token, x, True)
    return xset"""


# ---------------------------------------------------------------------------
# 7. PARTIAL-DOMAIN (swap the two branches) — returns the FALLBACK on the
#    determined tag and the solver set on the undecided tag (catch the signal but
#    re-raise-style return of the solver value is impossible after a raise, so we
#    instead branch explicitly the WRONG way). Correct in structure but inverts
#    the dichotomy: on solvability == 0 it returns the fallback (is_fallback
#    True), violating (P0) is_fallback == False / cond == solved_cond(rel).
#    expect=reject.
#
#    Refinement: a real patch that inverted the condition — returning
#    ConditionSet(x, self, Reals) when the solver SUCCEEDS and the solver set when
#    it fails — is incoherent in the real code (you cannot get the solver set on a
#    NotImplementedError), but its observable effect on a DETERMINED relation is
#    to discard the genuine solution set and return the ConditionSet fallback. On
#    the P2P determined relations (test_univariate_relational_as_set observes real
#    solver sets) the result would be the ConditionSet instead of the Interval/
#    union — those P2P assertions FAIL. A verifying rival is verify-not-resolve.
_BRANCH_SWAP_IMPL = """    syms = rel.n_free
    Assert(syms == 1)
    x = rel.sym
    if rel.solvability == 0:
        xset = SolutionSet(True, rel.token, x, True)
    else:
        xset = solve_univariate(rel)
    return xset"""


# ---------------------------------------------------------------------------
# 8. PARTIAL-DOMAIN (determined result with fabricated sym/over_reals) — calls
#    the solver on the determined tag, keeps its condition token, but REBUILDS
#    the returned set with fabricated bound-symbol / base-domain fields. This
#    is correct on is_fallback and cond, so it isolates the (P0) clauses
#    Result().sym == solved_sym(rel) and Result().over_reals ==
#    solved_reals(rel): the fabricated values are not provably equal to the
#    solver's own projections. expect=reject.
#
#    Refinement: a real patch that, on a determined relation, replaced the
#    solver's returned set with a rebuilt object carrying a different bound
#    symbol or base domain would not return the solver's genuine solution set;
#    P2P test_univariate_relational_as_set observes the actual solver sets
#    (e.g. (x-1)*(x-2) > 0 -> a genuine Interval union), so such a substituted
#    result FAILS those assertions. A verifying rival is verify-not-resolve.
_FABRICATED_FIELDS_IMPL = """    syms = rel.n_free
    Assert(syms == 1)
    x = rel.sym
    try:
        xset = solve_univariate(rel)  # type: SolutionSet
        xset = SolutionSet(False, solved_cond(rel), 12345, False)
    except SolverUndecided:
        xset = SolutionSet(True, rel.token, x, True)
    return xset"""


SPEC_TESTS = [
    {
        "id": "pos-control-explicit-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_BRANCH_IMPL),
        "rationale": (
            "structurally-different but CORRECT impl: branches explicitly on the "
            "read-only tag rel.solvability instead of letting try/except drive the "
            "dichotomy. For the determined tag it still CALLS solve_univariate so "
            "the proof obtains Result().cond == solved_cond(rel) from the axiom "
            "Ensures (the only sound source of that pin); for the undecided tag it "
            "builds the fallback directly. Both postcondition branches hold and "
            "nothing escapes. The determined-branch call is wrapped in "
            "try/except SolverUndecided (dead under the solvability==0 guard) "
            "purely to discharge Nagini's SYNTACTIC no-escape obligation: a call "
            "to a method declaring an Exsures must be caught even when the path "
            "condition makes the exceptional edge infeasible (the verifier does "
            "not fold the branch guard into the callee's exceptional postcondition "
            "— a proof-engineering limitation, not a spec defect). The OUTPUT is "
            "byte-identical to the gold's. No framing assert / fold lemma is "
            "dropped. Must verify; if it cannot for an OUTPUT reason, the "
            "postcondition is SPEC-TOO-STRONG (rejects a faithful correct impl)."
        ),
    },
    {
        "id": "admiss-f2p-undecided-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS_IMPL),
        "rationale": (
            "the precondition is n_free==1 and solvability in {0,1} plus "
            "half-permission on each field; an F2P-shaped input (a univariate, "
            "undecided relation like Eq(x*cos(x)-3*sin(x),0), solvability==1) is "
            "in-domain. The added top-of-impl assertions confirm a 1/4 read share "
            "is derivable from the 1/2 held, the univariate count is 1, and the "
            "tag is in the two-way domain. Must verify; if it cannot, "
            "PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mutate-readonly-solvability",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME_MUTATE_IMPL),
        "refinement": (
            "the repo callee receives `self`, an IMMUTABLE Sympy Relational "
            "(Basic instances are immutable; there is no writable solvability "
            "attribute — solvability is decided inside solve_univariate_inequality, "
            "not stored on self). A faithful patch cannot mutate self to force the "
            "fallback branch. One that (per impossibility) forced every relation "
            "down the fallback path would return ConditionSet(x, self, Reals) even "
            "for a DETERMINED relation, so P2P test_univariate_relational_as_set "
            "(which observes the real solver sets, e.g. (x-1)*(x-2)>0 -> an "
            "Interval union) would FAIL. A verifying mutator is verify-not-resolve."
        ),
        "rationale": (
            "REJECT must come from the PERMISSION SYSTEM: rel.solvability is held "
            "only at Acc(rel.solvability, 1/2); the write rel.solvability = 1 "
            "needs FULL permission and is rejected for insufficient permission. "
            "Every postcondition obligation is otherwise reachable, so the failure "
            "is attributable to the write, not a proof gap. If it verifies, the "
            "read-only frame is unguarded (FRAME-MUTATION SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "control-flow-no-handler-totality",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _NO_HANDLER_IMPL),
        "refinement": (
            "this is the literal PRE-PATCH _eval_as_set: return "
            "solve_univariate_inequality(self, x, relational=False) with no "
            "try/except. On the F2P relation Eq(x*cos(x)-3*sin(x),0) the real "
            "solver raises NotImplementedError, which propagates out of as_set() "
            "instead of returning ConditionSet(x, self, Reals) — "
            "test_issue_18188 FAILS. The canonical verify-not-resolve rival "
            "(== model_prepatch.py / G-DIFF)."
        ),
        "rationale": (
            "REJECT comes from the TOTALITY obligation: the frozen spec declares "
            "NO Exsures, so the method must return normally on both tags. On the "
            "undecided tag (solvability==1) solve_univariate's Exsures lets "
            "SolverUndecided escape; with no handler the 'method raises no "
            "exceptions' obligation is unprovable. If it verifies, the spec does "
            "not actually require totality (SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "partial-domain-wrong-fallback-cond",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _WRONG_COND_IMPL),
        "refinement": (
            "on the undecided tag this builds the fallback with cond == rel.sym "
            "(the variable's identity) instead of rel.token (the relation's "
            "identity) — the real analogue is ConditionSet(x, x, S.Reals) instead "
            "of ConditionSet(x, self, S.Reals). On F2P "
            "Eq(x*cos(x)-3*sin(x),0).as_set() the expected ConditionSet(x, "
            "Eq(x*cos(x)-3*sin(x),0), Reals) would NOT be produced (the defining "
            "condition is the bare symbol, not the relation) — test_issue_18188 "
            "FAILS. A verifying rival is verify-not-resolve."
        ),
        "rationale": (
            "REJECT comes from the (P1) clause Result().cond == rel.token: the "
            "impl sets cond == rel.sym, which is not provably == rel.token (sym "
            "and token are independent fields). is_fallback/sym/over_reals are "
            "still correct, so the failure isolates the condition pin. If it "
            "verifies, the fallback's defining condition is unpinned "
            "(partial-domain SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "uniqueness-fallback-not-flagged",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _NOT_FALLBACK_IMPL),
        "refinement": (
            "on the undecided tag this returns a set with the right "
            "cond/sym/over_reals but is_fallback == False — the real analogue is "
            "returning a concrete solver-flavoured set (e.g. S.Reals, a "
            "UniversalSet) on the NotImplementedError instead of "
            "ConditionSet(x, self, S.Reals). On F2P test_issue_18188 as_set() "
            "would return that non-ConditionSet value, and the assertion "
            "result == ConditionSet(x, Eq(...), Reals) FAILS. A verifying rival "
            "is verify-not-resolve."
        ),
        "rationale": (
            "REJECT comes from the (P1) clause Result().is_fallback == True: the "
            "impl sets is_fallback == False, which the postcondition forbids on "
            "the undecided tag. is_fallback is the modeled observable that "
            "distinguishes a genuine solver set from the symbolic fallback; if "
            "this verifies, that distinction is unpinned (SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "partial-domain-fabricated-determined-fields",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FABRICATED_FIELDS_IMPL),
        "refinement": (
            "on the determined tag this keeps the solver's condition token but "
            "rebuilds the result with a fabricated bound symbol (12345) and "
            "base-domain flag (False) — the real analogue is discarding the "
            "solver's returned Set and substituting a reconstructed set with "
            "different structure. P2P test_univariate_relational_as_set observes "
            "the genuine solver sets on determined relations, so a substituted "
            "result FAILS those assertions. A verifying rival is "
            "verify-not-resolve."
        ),
        "rationale": (
            "REJECT comes from the (P0) clauses Result().sym == solved_sym(rel) "
            "and Result().over_reals == solved_reals(rel): the impl sets "
            "sym == 12345 and over_reals == False, neither provably equal to the "
            "solver's own value-abstract projections. is_fallback and cond are "
            "still correct, so the failure isolates the field pins. If it "
            "verifies, the determined branch's non-condition fields are unpinned "
            "(partial-domain SPEC-TOO-WEAK — the exact hole the panel's attack "
            "class exploits)."
        ),
    },
    {
        "id": "partial-domain-branch-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _BRANCH_SWAP_IMPL),
        "refinement": (
            "inverts the dichotomy: on the determined tag (solvability==0) it "
            "returns the fallback SolutionSet(True, ...) and on the undecided tag "
            "it calls the solver. The real observable effect on a DETERMINED "
            "relation is to discard the genuine solution set and return the "
            "ConditionSet fallback. P2P test_univariate_relational_as_set observes "
            "real solver sets on determined relations (e.g. (x-1)*(x-2)>0 -> an "
            "Interval union); the result would be a ConditionSet instead and those "
            "assertions FAIL. A verifying rival is verify-not-resolve."
        ),
        "rationale": (
            "REJECT comes from the (P0) clause Implies(solvability==0, "
            "is_fallback==False and cond==solved_cond(rel)): on the determined "
            "tag the impl returns is_fallback==True with cond==rel.token, "
            "violating both conjuncts (it is provably the fallback, and rel.token "
            "is not provably == solved_cond(rel)). If it verifies, the determined "
            "branch is not pinned to the solver's own set (SPEC-TOO-WEAK)."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE
#
# Two A-consumed axioms over the UNCHANGED callee
# solve_univariate_inequality(expr, gen, relational=False):
#   * solve_univariate — the partial solver: solvability 0 => returns a Set
#     normally (is_fallback False, cond == solved_cond(rel)); solvability 1 =>
#     raises NotImplementedError (SolverUndecided). Stated two-way domain
#     carve-out (Requires solvability in {0,1}); other solver outcomes
#     (ValueError/TypeError/RecursionError/non-termination) have no carrier.
#   * solved_cond — the same solver viewed as a value accessor (Requires
#     solvability==0; Ensures True, value abstract), pinning the determined
#     result to the solver's own returned Set.
#
# axiom_check.py (G-AX) already exercises both in-container. We mirror its two
# obligations as PBT probes so the battery re-runs them independently. The
# probes embed the same logic (call the REAL callee, classify, never scrape
# source — pilot bug #4 avoided) and import only sympy + stdlib (no bundle file
# is mounted in-container — pilot bug #6 avoided; any file open uses
# encoding='utf-8' — pilot bug #5 avoided).

# --- (A) axiom-soundness: the solve_univariate dichotomy over its STATED domain.
# For every relation the axiom would tag IN-DOMAIN, assert the real solver obeys
# the dichotomy (determined => returns a Set, never the ConditionSet fallback, no
# raise; undecided => raises NotImplementedError). A non-{determined,undecided}
# outcome is recorded as DOMAIN-EXCLUDED (sound carve-out), and we require the
# carve-out to be NON-EMPTY so the Requires solvability in {0,1} is load-bearing.
_SOLVE_UNIVARIATE_SOUNDNESS_PROBE = r'''
import random, signal, sys
from sympy import (S, Symbol, cos, sin, sqrt, exp, log, Eq, Ne, Abs, cbrt,
                   sign, Min, Max, floor, Rational)
from sympy.sets.sets import Set
from sympy.sets.conditionset import ConditionSet
from sympy.solvers.inequalities import solve_univariate_inequality

PER_CALL_TIMEOUT_S = 8
DETERMINED, UNDECIDED, EXCLUDED = 0, 1, -1


class _CallTimeout(Exception):
    pass


def _alarm(signum, frame):
    raise _CallTimeout()


def real_verdict(expr, gen):
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(PER_CALL_TIMEOUT_S)
    try:
        rv = solve_univariate_inequality(expr, gen, relational=False)
        return (DETERMINED, rv)
    except NotImplementedError:
        return (UNDECIDED, None)
    except _CallTimeout:
        return (EXCLUDED, "timeout/non-termination")
    except Exception as e:
        return (EXCLUDED, "%s: %s" % (type(e).__name__, str(e)[:60]))
    finally:
        signal.alarm(0)


def assert_determined(expr, gen):
    tag, rv = real_verdict(expr, gen)
    if tag == UNDECIDED:
        print("AXIOM-UNSOUND: %r tagged DETERMINED but solver raised "
              "NotImplementedError" % (expr,)); sys.exit(1)
    if tag == EXCLUDED:
        print("AXIOM-UNSOUND: %r tagged DETERMINED but solver reported "
              "out-of-domain outcome %r" % (expr, rv)); sys.exit(1)
    if not isinstance(rv, Set):
        print("AXIOM-UNSOUND: DETERMINED result for %r is not a Set (%r)"
              % (expr, type(rv).__name__)); sys.exit(1)
    if rv == ConditionSet(gen, expr, S.Reals):
        print("AXIOM-UNSOUND: DETERMINED result for %r equals the symbolic "
              "fallback ConditionSet(x, self, Reals); is_fallback==False pin "
              "violated" % (expr,)); sys.exit(1)


def assert_undecided(expr, gen):
    tag, rv = real_verdict(expr, gen)
    if tag == DETERMINED:
        print("AXIOM-UNSOUND: %r tagged UNDECIDED but solver returned a Set %r"
              % (expr, rv)); sys.exit(1)
    if tag == EXCLUDED:
        print("AXIOM-UNSOUND: %r tagged UNDECIDED but solver reported "
              "out-of-domain outcome %r (not NotImplementedError)"
              % (expr, rv)); sys.exit(1)


def classify(expr, gen):
    tag, rv = real_verdict(expr, gen)
    if tag == DETERMINED:
        if not isinstance(rv, Set):
            print("AXIOM-UNSOUND: in-domain DETERMINED result for %r not a Set "
                  "(%r)" % (expr, type(rv).__name__)); sys.exit(1)
        if rv == ConditionSet(gen, expr, S.Reals):
            print("AXIOM-UNSOUND: in-domain DETERMINED result for %r equals the "
                  "symbolic fallback" % (expr,)); sys.exit(1)
    return tag


x = Symbol('x')

# (a) the EXACT two F2P relations must be UNDECIDED (NotImplementedError).
f2p = [
    Eq(x * cos(x) - 3 * sin(x), 0),
    Eq(x ** 2 + sqrt(x * 2) + sin(x), 0),
]
for expr in f2p:
    assert_undecided(expr, x)

# (b) in-domain DETERMINED battery: must return a Set, never the fallback.
determined = [
    x ** 2 >= 4, x > 0, x < 0, x >= 1, x <= -1,
    sin(x) > 0, cos(x) <= 0, exp(x) > 2, log(x) > 0,
    Eq(x, 0), Eq(x - 3, 0), Eq(x ** 2, 4),
    x ** 2 - 1 < 0, x ** 2 + 1 > 0, x ** 3 - x >= 0,
    (x - 1) * (x - 2) > 0, Abs(x) < 2, Ne(x, 0),
]
for expr in determined:
    assert_determined(expr, x)

# (c) broader families: classify; the carve-out must be NON-EMPTY.
carveout = [
    cbrt(x) > 0, sign(x) > 0, Eq(log(x), 0), Eq(log(log(x)), 0),
    Eq(Min(1, x), 0), Max(0, x) > 1,
    2 * x ** (Rational(1, 3)) + 3 * x ** 2 - 3 <= 0,
    floor(x) > 0,
]
n_excluded = 0
for expr in carveout:
    if classify(expr, x) == EXCLUDED:
        n_excluded += 1
if n_excluded < 1:
    print("CARVE-OUT VACUOUS: no broader-family relation landed out-of-domain; "
          "the stated solvability in {0,1} precondition would carve out nothing")
    sys.exit(1)

# (d) randomized fuzz across all families, classified the same way.
rng = random.Random(18211)
ctors = [lambda e: e > 0, lambda e: e >= 0, lambda e: e < 0,
         lambda e: e <= 0, lambda e: Eq(e, 0), lambda e: Ne(e, 0)]
gens = [
    lambda r: r.choice(ctors)(
        sum(r.randint(-5, 5) * x ** k for k in range(r.randint(1, 3) + 1)) or x),
    lambda r: r.choice(ctors)(sin(x) + r.randint(-3, 3) * x),
    lambda r: r.choice(ctors)(cos(x) - r.randint(0, 3)),
    lambda r: r.choice(ctors)(exp(x) - r.randint(1, 4)),
    lambda r: r.choice(ctors)(cbrt(x) + r.randint(-2, 2)),
    lambda r: r.choice(ctors)(sign(x) * r.randint(1, 3)),
    lambda r: r.choice(ctors)(log(x) + r.randint(-2, 2)),
    lambda r: r.choice(ctors)(Min(r.randint(-2, 2), x)),
    lambda r: r.choice(ctors)(Max(r.randint(-2, 2), x)),
    lambda r: r.choice(ctors)(floor(x) + r.randint(-2, 2)),
]
n_fuzz = 200
for _ in range(n_fuzz):
    try:
        expr = rng.choice(gens)(rng)
    except (TypeError, ValueError):
        continue
    try:
        if not getattr(expr, 'free_symbols', set()):
            continue
    except Exception:
        continue
    classify(expr, x)

print("AXIOM-SOUND: solve_univariate dichotomy holds over its stated domain "
      "(2 F2P UNDECIDED, %d DETERMINED return Sets never the fallback, "
      "carve-out non-empty: %d/%d broader families out-of-domain, %d fuzz "
      "classified)." % (len(determined), n_excluded, len(carveout), n_fuzz))
sys.exit(0)
'''


# --- (B) axiom-containment: every callee-input the MODEL can reach lies inside
# the axiom's Requires domain (solvability in {0,1}). The model calls
# solve_univariate(rel) ONLY under its own Requires (rel.solvability in {0,1}),
# i.e. only on relations the abstraction TAGS determined-or-undecided. The
# containment obligation is therefore: the model never passes the callee a
# relation whose real outcome is out-of-domain. Because the model's own Requires
# is solvability in {0,1} (the SAME predicate as the axiom's Requires), the
# containment is definitional. We make it executable by confirming the two F2P
# inputs the model is built to handle (the undecided witnesses) and a battery of
# determined witnesses all land IN-DOMAIN under the real callee — i.e. the model
# only ever drives the solver on relations that genuinely return-or-raise
# NotImplementedError, never an out-of-domain one. (A reachable out-of-domain
# input would be AXIOM-TOO-WEAK-FOR-CALLER — but the model's Requires excludes
# it, so this must hold.)
_SOLVE_UNIVARIATE_CONTAINMENT_PROBE = r'''
import signal, sys
from sympy import S, Symbol, cos, sin, sqrt, exp, log, Eq, Ne, Abs
from sympy.sets.sets import Set
from sympy.sets.conditionset import ConditionSet
from sympy.solvers.inequalities import solve_univariate_inequality

PER_CALL_TIMEOUT_S = 8
DETERMINED, UNDECIDED, EXCLUDED = 0, 1, -1


class _CallTimeout(Exception):
    pass


def _alarm(signum, frame):
    raise _CallTimeout()


def real_verdict(expr, gen):
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(PER_CALL_TIMEOUT_S)
    try:
        rv = solve_univariate_inequality(expr, gen, relational=False)
        return (DETERMINED, rv)
    except NotImplementedError:
        return (UNDECIDED, None)
    except _CallTimeout:
        return (EXCLUDED, "timeout/non-termination")
    except Exception as e:
        return (EXCLUDED, "%s: %s" % (type(e).__name__, str(e)[:60]))
    finally:
        signal.alarm(0)


x = Symbol('x')

# The MODEL only calls solve_univariate(rel) when its own Requires holds:
#   rel.n_free == 1  AND  rel.solvability in {0, 1}
# i.e. only on relations the abstraction tags determined-or-undecided. The
# axiom's Requires is the SAME predicate (solvability in {0,1}), so every
# model-reachable callee-input is, by construction, inside the axiom's domain.
# We witness this: the undecided inputs (the F2P relations, solvability==1) and a
# battery of determined inputs (solvability==0) must ALL land in-domain
# (DETERMINED or UNDECIDED) under the real callee — never EXCLUDED. A model
# carrier for an EXCLUDED relation cannot be built (solvability in {0,1} has no
# preimage there), so reaching one would be AXIOM-TOO-WEAK-FOR-CALLER.
undecided_reachable = [
    Eq(x * cos(x) - 3 * sin(x), 0),     # F2P #1
    Eq(x ** 2 + sqrt(x * 2) + sin(x), 0),  # F2P #2
]
determined_reachable = [
    x ** 2 >= 4, x > 0, x < 0, Eq(x, 0), Eq(x ** 2, 4),
    sin(x) > 0, cos(x) <= 0, exp(x) > 2, log(x) > 0,
    (x - 1) * (x - 2) > 0, Abs(x) < 2, Ne(x, 0),
]
for expr in undecided_reachable:
    tag, rv = real_verdict(expr, x)
    if tag != UNDECIDED:
        print("AXIOM-TOO-WEAK-FOR-CALLER: model-reachable undecided witness %r "
              "is not UNDECIDED under the real callee (tag=%r, rv=%r)"
              % (expr, tag, rv))
        sys.exit(1)
for expr in determined_reachable:
    tag, rv = real_verdict(expr, x)
    if tag == EXCLUDED:
        print("AXIOM-TOO-WEAK-FOR-CALLER: model-reachable determined witness %r "
              "lands OUT-OF-DOMAIN under the real callee (%r) — the model's "
              "Requires solvability in {0,1} would have no carrier for it"
              % (expr, rv))
        sys.exit(1)
    if tag == DETERMINED and not isinstance(rv, Set):
        print("AXIOM-TOO-WEAK-FOR-CALLER: determined witness %r returned a "
              "non-Set %r" % (expr, type(rv).__name__))
        sys.exit(1)
print("AXIOM-COVERED: every model-reachable callee-input (the model's Requires "
      "solvability in {0,1}) is inside the solve_univariate axiom's Requires "
      "domain — %d undecided + %d determined witnesses all land in-domain "
      "(determined Set / NotImplementedError), none out-of-domain."
      % (len(undecided_reachable), len(determined_reachable)))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-solve-univariate-soundness",
        "axiom": "solve_univariate",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _SOLVE_UNIVARIATE_SOUNDNESS_PROBE,
        "rationale": (
            "solve_univariate models the UNCHANGED solver "
            "solve_univariate_inequality(..., relational=False). The proof "
            "consumes the dichotomy over its stated two-way domain (Requires "
            "solvability in {0,1}): determined => returns a Set, never the "
            "ConditionSet fallback, no raise; undecided => raises "
            "NotImplementedError. The probe runs the REAL solver under a per-call "
            "timeout, asserts the dichotomy on every in-domain relation, and "
            "requires the carve-out to be NON-EMPTY (other outcomes have no "
            "carrier). A violation is AXIOM-UNSOUND. Mirrors axiom_check.py."
        ),
    },
    {
        "id": "ax-solve-univariate-containment",
        "axiom": "solve_univariate",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _SOLVE_UNIVARIATE_CONTAINMENT_PROBE,
        "rationale": (
            "the model calls solve_univariate(rel) only under its own Requires "
            "(solvability in {0,1}), the SAME predicate as the axiom's Requires, "
            "so every model-reachable callee-input is definitionally inside the "
            "axiom's domain. The probe witnesses this: the model-reachable "
            "undecided inputs (the F2P relations) and a battery of determined "
            "inputs ALL land in-domain (DETERMINED/UNDECIDED) under the real "
            "callee, never out-of-domain. A reachable out-of-domain input would "
            "be AXIOM-TOO-WEAK-FOR-CALLER."
        ),
    },
]
