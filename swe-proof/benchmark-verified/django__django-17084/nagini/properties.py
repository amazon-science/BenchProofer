# properties.py — PBT falsification battery for django__django-17084.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a FULL model.py whose SPEC (axioms/pure/pre/post-conditions
# + the requires_subquery_wrap signature + the @Pure any_referenced_flag helper)
# is BYTE-IDENTICAL to the frozen model.py and differs ONLY inside the impl
# region (which, together with the nested invariants region, is elided from the
# spec view). Built by region-surgery: every variant is produced by replacing the
# full gold impl BODY with a new body, so markers.same_spec is GUARANTEED (the
# spec view never sees the impl/invariants).
#
# --- Defended surface (from model.py + refinement.md + mapping.md + the F2P) ---
# requires_subquery_wrap(window_flags: List[bool], subquery_flags: List[bool],
#                        other_forces_wrap: bool) -> bool
# Inputs:
#   window_flags    : READ-ONLY  — Acc(list_pred(window_flags), 1/2)
#   subquery_flags  : READ-ONLY  — Acc(list_pred(subquery_flags), 1/2)
#   other_forces_wrap : bool      — immutable scalar (no permission concern)
# Load-bearing postcondition clauses:
#   (P) the PIN:  Result() == ( any_referenced_flag(ToSeq(window_flags))
#                               or any_referenced_flag(ToSeq(subquery_flags))
#                               or other_forces_wrap )
#       — the wrap decision is EXACTLY the three-term disjunction. This is the
#         complete decision; the NEW term is the window disjunct.
#   (W) the CHANGE / discriminating consequence:
#         Implies(any_referenced_flag(ToSeq(window_flags)), Result())
#       — a single window-containing reference FORCES the wrap regardless of the
#         subquery flags and the collapsed remainder. This is precisely what the
#         gold patch adds (refs_window) and what the F2P
#         test_referenced_window_requires_wrapping observes (an aggregate over a
#         Coalesce(Window(...),0.0) annotation must wrap -> sql.count("select")==2).
#   (F) the FRAME: Acc(list_pred(window_flags),1/2) and
#         Acc(list_pred(subquery_flags),1/2) are RE-ENSURED — the inputs are
#         read-only and may not be written.
#   (T) TOTALITY: Requires(MustTerminate(2)) — the decision must actually
#         ANSWER. Nagini is a partial-correctness verifier by default, so
#         without this obligation a same-spec impl that diverges before
#         returning (an unbounded loop ahead of the gold body) satisfies
#         clauses P/W vacuously on every never-reached exit and is ADMITTED —
#         exactly the P1 hole the audit exploited. Every loop must carry a
#         strictly decreasing, bounded-below MustTerminate measure.
#
# --- Oracle grounding (ungrounded-oracle-echo class) ---
# any_referenced_flag is a @Pure helper, BUT it is GROUNDED in the input: it is a
# total function of ToSeq(window_flags)/ToSeq(subquery_flags), fully unfolded
# (front-recursive OR-fold), with NO opaque answer key. An impl that simply
# returns the three-term disjunction expression is therefore CORRECT (it equals
# clause P verbatim), not a wrong echo — there is no wrong value to echo. So the
# ungrounded-oracle-echo attack does NOT apply here; in its place we include an
# honest cheapest-impl positive control (`pos-direct`) that returns the
# disjunction directly (expect verify).
#
# --- Axiom lane ---
# There is NO consumed @ContractOnly axiom (the axioms region is empty). The only
# deep model is the A-reference any_referenced_flag == Python any(...) over the
# resolved contains_over_clause/subquery flags, already validated in-container by
# axiom_check.py / G-AX (12 boundary + 20000 fuzz lists + the attribute-resolution
# semantics). We add ONE containment cross-check probe that (a) re-derives the
# fold == any() equivalence over the full caller-reachable boolean-list domain
# (incl. the empty boundary the loops hit) and (b) re-confirms the
# contains_over_clause/subquery attribute resolution the model's elements carry,
# so the AXIOM-lane verdict is grounded rather than empty.
from pathlib import Path

INSTANCE = "django__django-17084"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused

_BASE = (Path(__file__).parent / "model.py").read_text()

# The full gold impl BODY (everything between '    # impl-start\n' and the
# '    # impl-end' line). Editing ONLY this region keeps same_spec True.
_A = "    # impl-start\n"
_B = "    # impl-end"
_ia = _BASE.index(_A) + len(_A)
_ib = _BASE.index(_B)
_GOLD_BODY = _BASE[_ia:_ib]


def _impl(new_body: str) -> str:
    """Replace ONLY the gold impl body (impl + nested invariants region) with
    new_body. The spec view elides impl/invariants, so the spec signature (and
    thus markers.same_spec) is unchanged."""
    if _GOLD_BODY not in _BASE:
        raise AssertionError("drift: gold impl body not found")
    if _BASE.count(_GOLD_BODY) != 1:
        raise AssertionError("not unique: gold impl body")
    return _BASE.replace(_GOLD_BODY, new_body, 1)


# ===========================================================================
# Shared loop fragments — kept VERBATIM from gold so positive controls KEEP the
# proof obligations they still need (pilot bug 2). Both loops are BACKWARD and
# match the FRONT-recursive any_referenced_flag unfold (one unfold per step), so
# no f(a+b)==f(a)+f(b) lemma is needed (pilot bug 3). The only reshape applied is
# reordering the two independent loops + re-threading which result each second
# loop must preserve.
# ===========================================================================

# The gold WINDOW loop AS THE FIRST loop (gold's own first loop, verbatim).
_WIN_LOOP_FIRST = """\
    refs_subquery = False
    refs_window = False
    i = len(window_flags)
    while i > 0:
        Invariant(Acc(list_pred(window_flags), 1 / 2))
        Invariant(Acc(list_pred(subquery_flags), 1 / 2))
        Invariant(wseq == ToSeq(window_flags))
        Invariant(sseq == ToSeq(subquery_flags))
        Invariant(0 <= i and i <= len(window_flags))
        Invariant(refs_window == any_referenced_flag(wseq.drop(i)))
        Invariant(MustTerminate(i + 1))
        Assert(wseq.drop(i - 1)[0] == wseq[i - 1])
        Assert(wseq.drop(i - 1).drop(1) == wseq.drop(i))
        refs_window = window_flags[i - 1] or refs_window
        i = i - 1
    Assert(refs_window == any_referenced_flag(wseq))
"""

# The gold SUBQUERY loop AS THE SECOND loop (gold's own second loop, verbatim;
# carries the finished refs_window as an invariant).
_SUB_LOOP_SECOND = """\
    j = len(subquery_flags)
    while j > 0:
        Invariant(Acc(list_pred(window_flags), 1 / 2))
        Invariant(Acc(list_pred(subquery_flags), 1 / 2))
        Invariant(wseq == ToSeq(window_flags))
        Invariant(sseq == ToSeq(subquery_flags))
        Invariant(refs_window == any_referenced_flag(wseq))
        Invariant(0 <= j and j <= len(subquery_flags))
        Invariant(refs_subquery == any_referenced_flag(sseq.drop(j)))
        Invariant(MustTerminate(j + 1))
        Assert(sseq.drop(j - 1)[0] == sseq[j - 1])
        Assert(sseq.drop(j - 1).drop(1) == sseq.drop(j))
        refs_subquery = subquery_flags[j - 1] or refs_subquery
        j = j - 1
    Assert(refs_subquery == any_referenced_flag(sseq))
    Assert(refs_window == any_referenced_flag(wseq))
"""

# The SUBQUERY loop AS THE FIRST loop (for the reorder positive control): nothing
# about refs_window has been computed yet, so it carries no refs_window invariant.
_SUB_LOOP_FIRST = """\
    refs_subquery = False
    refs_window = False
    j = len(subquery_flags)
    while j > 0:
        Invariant(Acc(list_pred(window_flags), 1 / 2))
        Invariant(Acc(list_pred(subquery_flags), 1 / 2))
        Invariant(wseq == ToSeq(window_flags))
        Invariant(sseq == ToSeq(subquery_flags))
        Invariant(0 <= j and j <= len(subquery_flags))
        Invariant(refs_subquery == any_referenced_flag(sseq.drop(j)))
        Invariant(MustTerminate(j + 1))
        Assert(sseq.drop(j - 1)[0] == sseq[j - 1])
        Assert(sseq.drop(j - 1).drop(1) == sseq.drop(j))
        refs_subquery = subquery_flags[j - 1] or refs_subquery
        j = j - 1
    Assert(refs_subquery == any_referenced_flag(sseq))
"""

# The WINDOW loop AS THE SECOND loop (for the reorder positive control): carries
# the finished refs_subquery as an invariant.
_WIN_LOOP_SECOND = """\
    i = len(window_flags)
    while i > 0:
        Invariant(Acc(list_pred(window_flags), 1 / 2))
        Invariant(Acc(list_pred(subquery_flags), 1 / 2))
        Invariant(wseq == ToSeq(window_flags))
        Invariant(sseq == ToSeq(subquery_flags))
        Invariant(refs_subquery == any_referenced_flag(sseq))
        Invariant(0 <= i and i <= len(window_flags))
        Invariant(refs_window == any_referenced_flag(wseq.drop(i)))
        Invariant(MustTerminate(i + 1))
        Assert(wseq.drop(i - 1)[0] == wseq[i - 1])
        Assert(wseq.drop(i - 1).drop(1) == wseq.drop(i))
        refs_window = window_flags[i - 1] or refs_window
        i = i - 1
    Assert(refs_window == any_referenced_flag(wseq))
    Assert(refs_subquery == any_referenced_flag(sseq))
"""

_SNAP = (
    "    wseq = ToSeq(window_flags)  # type: PSeq[bool]\n"
    "    sseq = ToSeq(subquery_flags)  # type: PSeq[bool]\n"
)


# ===========================================================================
# POSITIVE CONTROLS (expect verify) — a correct impl in a DIFFERENT shape must
# still verify; else the spec is SPEC-TOO-STRONG.
# ===========================================================================

# pos-direct: the honest cheapest impl — return the three-term disjunction
# expression DIRECTLY (no loops). Because any_referenced_flag is GROUNDED in the
# input, this expression is literally clause P's RHS, so it must verify. It also
# stands in for the (N/A) ungrounded-oracle-echo class: there is no wrong value
# to echo, so the only echo is the correct one.
_POS_DIRECT = (
    "    return (\n"
    "        any_referenced_flag(ToSeq(window_flags))\n"
    "        or any_referenced_flag(ToSeq(subquery_flags))\n"
    "        or other_forces_wrap\n"
    "    )\n"
)

# pos-reorder: compute the SUBQUERY accumulator FIRST, then the WINDOW accumulator
# (gold does window first). Two independent backward loops merely reordered, each
# keeping its full gold framing invariants (only which result the second loop must
# preserve changes). The final return ORs the three terms in a DIFFERENT textual
# order (window first) than gold. A correct impl in this shape MUST verify; if it
# cannot, the postcondition is SPEC-TOO-STRONG.
_POS_REORDER = (
    _SNAP
    + _SUB_LOOP_FIRST
    + _WIN_LOOP_SECOND
    + "    return refs_window or refs_subquery or other_forces_wrap\n"
)

# admiss: the gold body verbatim, but FIRST re-derive in-region that the
# precondition admits a normal input: build two concrete F2P-shaped flag lists
# (a single True window flag = the Coalesce(Window(...)) annotation; an
# all-False subquery list), read both half-permission inputs, and Assert that on
# the F2P-shaped input clause W's antecedent holds and clause P's RHS is forced
# True by the window term alone. (A self-CALL is no longer usable for this
# probe: the spec's Requires(MustTerminate(2)) forbids a same-measure callee —
# the obligation-leak check would reject the call for the wrong reason. The
# in-region derivation checks the same admissibility content: the Requires are
# establishable for a legitimate input and the discriminating clause is
# reachable, not vacuous.) If any Requires were vacuous or over-strong, these
# asserts would fail — PRECOND-TOO-STRONG. The gold body follows so the whole
# module still verifies.
_ADMISS = (
    "    probe_w = [True]  # type: List[bool]\n"
    "    probe_s = [False]  # type: List[bool]\n"
    "    Assert(len(window_flags) >= 0)  # admissibility: half-perm read of input usable\n"
    "    Assert(len(subquery_flags) >= 0)  # admissibility: half-perm read of input usable\n"
    "    Assert(any_referenced_flag(ToSeq(probe_w)))  # clause W antecedent satisfiable (F2P shape)\n"
    "    Assert(any_referenced_flag(ToSeq(probe_w))\n"
    "           or any_referenced_flag(ToSeq(probe_s))\n"
    "           or False)  # clause P RHS forced True by the window term alone\n"
    "\n"
    + _GOLD_BODY
)


# ===========================================================================
# UNIQUENESS / REJECT rivals (expect reject) — each shares the spec and changes
# ONLY the impl; if any VERIFIES, the spec admits a wrong impl (SPEC-TOO-WEAK).
# Each carries the refinement argument that its faithful real patch would NOT
# resolve the F2P/P2P, so a verifying rival is a true verify-not-resolve break.
# ===========================================================================

# drop-window: the PRE-PATCH bug verbatim — never accumulate the window term;
# return only (other_forces_wrap or refs_subquery). This is exactly
# model_prepatch.py. Must REJECT on clause P / clause W: on a window-only input
# (one True window flag, all subquery flags False, other_forces_wrap False) the
# postcondition demands Result()==True (window term True) but this impl returns
# False. The subquery loop is kept (correct refs_subquery) so the rejection is
# attributable to the missing window disjunct, not a stray proof failure.
_DROP_WINDOW = (
    _SNAP
    + _SUB_LOOP_FIRST
    + "    return other_forces_wrap or refs_subquery\n"
)

# wrong-and: replace the OR-reduction in the wrap decision with the subquery term
# ANDed against the window term in place of the new disjunct — i.e. return
# (other_forces_wrap or refs_subquery or (refs_subquery and refs_window)). This
# collapses the window term into a no-op (refs_subquery or (refs_subquery and X)
# == refs_subquery), so it agrees with gold ONLY when refs_subquery or
# other_forces_wrap already forces the wrap. On a window-only input it returns
# False, violating clause W. Must REJECT.
_WRONG_AND = (
    _SNAP
    + _WIN_LOOP_FIRST
    + _SUB_LOOP_SECOND
    + "    return other_forces_wrap or refs_subquery or (refs_subquery and refs_window)\n"
)

# swap-names: a CORRECT alternate-shape positive control. It accumulates the value
# any_referenced_flag(subquery_flags) into a local NAMED `refs_window`, and the
# value any_referenced_flag(window_flags) into a local NAMED `refs_subquery`, then
# returns `other_forces_wrap or refs_subquery or refs_window`. The variable NAMES
# are swapped relative to gold, but the RETURNED VALUE is
#   other_forces_wrap or any_referenced_flag(window_flags)
#                     or any_referenced_flag(subquery_flags)
# which is byte-for-byte clause P's RHS (the final OR is symmetric in the two
# accumulators). The window contribution still flows into Result() — via the
# locally-misnamed `refs_subquery`. So both clause P AND clause W hold: on a
# window-only input (window=[True], subquery=[False], other=False) refs_subquery
# (sourced from window_flags) is True, hence Result()==True and clause W is
# satisfied. This is NOT a faithful wrong impl — its real-patch correlate is the
# gold accumulation with the two LOCAL variable names exchanged, which emits
# identical SQL and RESOLVES the F2P. A correct impl in this shape MUST verify; if
# it could not, the postcondition would be SPEC-TOO-STRONG. (It was previously
# mislabeled expect=reject on the mistaken belief that clause W distinguishes it;
# clause W constrains Result(), not variable provenance, so it does not.)
_SWAP_TERMS = (
    _SNAP
    # accumulate refs_window from the SUBQUERY flags (wrong source)
    + """\
    refs_subquery = False
    refs_window = False
    i = len(subquery_flags)
    while i > 0:
        Invariant(Acc(list_pred(window_flags), 1 / 2))
        Invariant(Acc(list_pred(subquery_flags), 1 / 2))
        Invariant(wseq == ToSeq(window_flags))
        Invariant(sseq == ToSeq(subquery_flags))
        Invariant(0 <= i and i <= len(subquery_flags))
        Invariant(refs_window == any_referenced_flag(sseq.drop(i)))
        Invariant(MustTerminate(i + 1))
        Assert(sseq.drop(i - 1)[0] == sseq[i - 1])
        Assert(sseq.drop(i - 1).drop(1) == sseq.drop(i))
        refs_window = subquery_flags[i - 1] or refs_window
        i = i - 1
    Assert(refs_window == any_referenced_flag(sseq))
    j = len(window_flags)
    while j > 0:
        Invariant(Acc(list_pred(window_flags), 1 / 2))
        Invariant(Acc(list_pred(subquery_flags), 1 / 2))
        Invariant(wseq == ToSeq(window_flags))
        Invariant(sseq == ToSeq(subquery_flags))
        Invariant(refs_window == any_referenced_flag(sseq))
        Invariant(0 <= j and j <= len(window_flags))
        Invariant(refs_subquery == any_referenced_flag(wseq.drop(j)))
        Invariant(MustTerminate(j + 1))
        Assert(wseq.drop(j - 1)[0] == wseq[j - 1])
        Assert(wseq.drop(j - 1).drop(1) == wseq.drop(j))
        refs_subquery = window_flags[j - 1] or refs_subquery
        j = j - 1
    Assert(refs_subquery == any_referenced_flag(wseq))
"""
    + "    return other_forces_wrap or refs_subquery or refs_window\n"
)

# frame-mut: MANDATORY frame-mutation probe. window_flags is read-only (half
# permission), so this rival WRITES to it (append). It must FAIL for INSUFFICIENT
# PERMISSION before any postcondition is even considered — list_pred mutation
# (append) needs FULL permission and the input is held at Acc(list_pred(.),1/2).
# The gold body follows unchanged so the rejection is attributable to the single
# illegal write.
_FRAME_MUT = (
    "    window_flags.append(True)  # ILLEGAL: window_flags is read-only (Acc(list_pred(.),1/2))\n"
    + _GOLD_BODY
)

# nonterm-diverge: THE hole the P1 audit exploited (atk_2.py): keep the gold
# decision verbatim but DIVERGE first (an unbounded loop ahead of it). Under
# partial correctness the postconditions hold vacuously on every (never-reached)
# exit, so the pre-fix spec ADMITTED this impl even though its faithful patch
# hangs every aggregation call (the F2P harness times out; does NOT resolve).
# The spec's Requires(MustTerminate(2)) makes the obligation-leak check reject
# the loop (it takes no termination measure). NOTE: the loop must be
# statically-reachable-exit-shaped (`while k >= 0`, an Invariant, the gold body
# after it intact) — a literal `while True:` makes Nagini flag the trailing
# gold body as dead code, a TRANSLATION error, which would make this case
# trivially "rejected" for the wrong reason.
_NONTERM = (
    """    # NONTERMINATION: diverge before the (verbatim) gold decision.
    k = 0
    while k >= 0:
        Invariant(k >= 0)
        k = k + 1
"""
    + _GOLD_BODY
)

# frame-mut-sub: symmetric frame attack on the OTHER read-only input,
# subquery_flags, to satisfy the wrap decision vacuously by injecting a True flag.
# Same rejection: writing to a half-permission input is not permitted.
_FRAME_MUT_SUB = (
    "    subquery_flags.append(True)  # ILLEGAL: subquery_flags is read-only (Acc(list_pred(.),1/2))\n"
    + _GOLD_BODY
)


SPEC_TESTS = [
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_DIRECT),
        "rationale": (
            "The honest cheapest correct impl: return the three-term disjunction "
            "expression directly. any_referenced_flag is GROUNDED in the input "
            "(a total function of ToSeq(window_flags)/ToSeq(subquery_flags)), so "
            "this expression is exactly clause P's RHS and MUST verify (it also "
            "implies clause W). If it cannot verify, the postcondition is "
            "SPEC-TOO-STRONG. Also documents that the ungrounded-oracle-echo class "
            "is N/A: the only echo of the grounded oracle is the correct answer."
        ),
    },
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "A correct impl that accumulates the SUBQUERY term FIRST then the "
            "WINDOW term (gold does window first), and returns the disjunction in a "
            "different textual order (window first). Two independent backward loops "
            "merely reordered, each keeping its full gold framing invariants and "
            "matching the front-recursive any_referenced_flag unfold (no induction "
            "lemma needed, pilot bugs 2 and 3 avoided). It satisfies clauses P, W, "
            "and F, so it MUST verify; if it cannot, the postcondition is "
            "SPEC-TOO-STRONG (rejects a faithful correct decision)."
        ),
    },
    {
        "id": "admiss",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "Re-derives IN-REGION, on a concrete F2P-shaped input ([True] window "
            "flags = the Coalesce(Window(...),0.0) annotation, [False] subquery "
            "flags, other_forces_wrap False), that both half-permission inputs are "
            "readable, clause W's antecedent is satisfiable (not vacuous), and "
            "clause P's RHS is forced True by the window term alone. (A self-call "
            "probe is unusable under Requires(MustTerminate(2)) — the "
            "obligation-leak check would reject the same-measure recursion for the "
            "wrong reason — so the admissibility content is derived in-region "
            "instead.) If any Requires were vacuous or over-strong these asserts "
            "would fail: PRECOND-TOO-STRONG. The gold body follows so the module "
            "verifies."
        ),
    },
    {
        "id": "nonterm-diverge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NONTERM),
        "refinement": (
            "Keeps the gold decision verbatim but DIVERGES first (an unbounded "
            "statically-reachable-exit loop ahead of it). Its faithful real patch "
            "inserts an endless loop at the top of the wrap-decision block in "
            "get_aggregation, so EVERY aggregation call hangs: the F2P "
            "test_referenced_window_requires_wrapping (and every P2P touching "
            "aggregate()) times out in the harness. It does NOT resolve. This is "
            "the exact same-spec impl the P1 audit built (atk_2.py): under "
            "partial correctness clauses P/W hold vacuously on the never-reached "
            "exit, so the pre-fix spec ADMITTED it."
        ),
        "rationale": (
            "Rejected by clause T (Requires(MustTerminate(2))): the divergent loop "
            "carries no termination measure, so Nagini's obligation-leak check "
            "fails ('Loop might not take all unsatisfied obligations from the "
            "context'). NOTE: the loop must be statically-reachable-exit-shaped "
            "(`while k >= 0`, an Invariant, code after it intact) — a literal "
            "`while True:` makes Nagini flag the trailing gold body as dead code, "
            "a TRANSLATION error, which would make this case trivially 'rejected' "
            "for the wrong reason."
        ),
    },
    {
        "id": "drop-window",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_WINDOW),
        "refinement": (
            "This is the PRE-PATCH skeleton verbatim (model_prepatch.py): no "
            "refs_window accumulation, return other_forces_wrap or refs_subquery. "
            "Its faithful real patch is the unpatched get_aggregation, which the "
            "F2P test_referenced_window_requires_wrapping rejects: an aggregate over "
            "a Coalesce(Window(...),0.0) annotation is NOT wrapped, so the emitted "
            "SQL is the illegal aggregate(window()) (sql.count('select')==1, and on "
            "PostgreSQL psycopg2 raises GroupingError) instead of the required "
            "wrapped form (sql.count('select')==2). It does NOT resolve."
        ),
        "rationale": (
            "Rejected by the PIN (clause P) and the discriminating consequence "
            "(clause W): on a window-only input (window=[True], subquery all False, "
            "other_forces_wrap False) clause P demands Result()==True (the window "
            "disjunct) but this impl returns False; clause W "
            "(any_referenced_flag(window) implies Result()) is also violated. This "
            "is exactly the G-DIFF failure model_prepatch.py exhibits."
        ),
    },
    {
        "id": "wrong-and",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WRONG_AND),
        "refinement": (
            "Replaces the new window DISJUNCT with refs_subquery AND refs_window "
            "(return other_forces_wrap or refs_subquery or (refs_subquery and "
            "refs_window)) — algebraically equal to other_forces_wrap or "
            "refs_subquery, i.e. the window term is a no-op. Its faithful real patch "
            "would force the wrap for a windowed annotation only when the aggregate "
            "ALSO references a subquery annotation; the F2P references a window-only "
            "annotation (no subquery), so the aggregation is left unwrapped and the "
            "illegal aggregate(window()) SQL is emitted. It does NOT resolve."
        ),
        "rationale": (
            "Rejected by clauses P and W: on a window-only input the impl returns "
            "False while any_referenced_flag(window)==True forces Result()==True. "
            "Value-level/structural attack — the window term is present in the "
            "source text but neutralized by the AND, so it pins only the part of the "
            "domain where the subquery term already decides."
        ),
    },
    {
        "id": "swap-names",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_SWAP_TERMS),
        "rationale": (
            "A CORRECT alternate-shape positive control with the two LOCAL "
            "accumulator names swapped relative to gold: the value "
            "any_referenced_flag(subquery_flags) is bound to a local named "
            "`refs_window` and any_referenced_flag(window_flags) to a local named "
            "`refs_subquery`, then it returns "
            "`other_forces_wrap or refs_subquery or refs_window`. The RETURNED VALUE "
            "is byte-for-byte clause P's RHS (the final OR is symmetric in the two "
            "accumulators), and the window contribution still reaches Result() via "
            "the locally-misnamed `refs_subquery`. So both clause P and clause W "
            "hold (on window=[True], subquery=[False], other=False: refs_subquery is "
            "True so Result()==True, satisfying clause W). It MUST verify; if it "
            "could not, the postcondition would be SPEC-TOO-STRONG. Its real-patch "
            "correlate is the gold accumulation with the two LOCAL variable names "
            "exchanged — identical emitted SQL, RESOLVES the F2P. (Previously "
            "mislabeled expect=reject on the mistaken belief that clause W "
            "distinguishes it; clause W constrains Result(), not variable "
            "provenance, so it does not — the swap is a no-op for the output.)"
        ),
    },
    {
        "id": "frame-mut",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT),
        "refinement": (
            "Writes to the read-only source window_flags.append(True) before "
            "deciding. A real patch that mutated the caller's collected flag list "
            "(or, upstream, self.annotations during the wrap-decision pass) would "
            "corrupt the query's annotation state — every aggregation P2P test "
            "relies on the annotation set surviving the get_aggregation decision "
            "unchanged; it does NOT resolve. A byte-fuzzer never constructs this "
            "write — it is the project's #1 weakness class."
        ),
        "rationale": (
            "Rejected for INSUFFICIENT PERMISSION (the permission system / clause "
            "F): window_flags is held at Acc(list_pred(window_flags), 1/2), so "
            "appending (a list_pred mutation) is not permitted — full permission is "
            "required to mutate. The rejection is attributable to the single illegal "
            "write (the gold body follows unchanged)."
        ),
    },
    {
        "id": "frame-mut-sub",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT_SUB),
        "refinement": (
            "Symmetric frame attack on the OTHER read-only input: "
            "subquery_flags.append(True) to vacuously force the wrap. A real patch "
            "mutating the subquery-flag source would likewise corrupt the query's "
            "annotation state across the decision; it does NOT resolve."
        ),
        "rationale": (
            "Rejected for INSUFFICIENT PERMISSION (clause F): subquery_flags is held "
            "at Acc(list_pred(subquery_flags), 1/2); the append to a half-permission "
            "input is not permitted. Attributable to the single illegal write."
        ),
    },
]


# ===========================================================================
# AXIOM lane. This bundle consumes NO @ContractOnly axioms (the axioms region is
# empty). The only deep model is the A-reference any_referenced_flag == Python
# any(...) over the resolved contains_over_clause/subquery flags, already
# validated IN-CONTAINER by axiom_check.py / G-AX. We add ONE containment-style
# cross-check that (a) re-derives the fold == any() equivalence over the full
# caller-reachable boolean-list domain (incl. the empty boundary the loops hit)
# and (b) re-confirms the contains_over_clause/subquery attribute resolution the
# model's element values carry (Window leaf True; composite = any-over-sources;
# Subquery.subquery True; getattr defaults True/False), so the AXIOM-lane verdict
# is grounded rather than empty. Probe is self-contained (stdlib only), opens any
# file with encoding="utf-8" (none needed here), and exits 0 iff the obligation
# holds. The full real-callee G-AX check lives in axiom_check.py.
# ===========================================================================

_CONTAINMENT_PROBE = r'''
import sys, random

# --- the model's deep model any_referenced_flag (front-recursive OR-fold) ----
def any_referenced_flag(flags):
    if len(flags) == 0:
        return False
    return bool(flags[0]) or any_referenced_flag(flags[1:])

# (A-reference 1) containment + equivalence: the model can pass to the OR-fold
# ONLY a finite List[bool] (window_flags or subquery_flags). Python any() is
# TOTAL over every finite boolean list, so every caller-reachable input lies in
# the callee's domain (containment holds by totality). Re-confirm fold == any()
# over the full reachable domain, incl. the empty-list boundary the loops hit
# when len(flags)==0.
boundary = [
    [], [True], [False],
    [True, True], [True, False], [False, True], [False, False],
    [False, False, False], [False, False, True],
    [True] * 5, [False] * 5, [False, False, True, False],
]
for flags in boundary:
    assert any(flags) == any_referenced_flag(list(flags)), (
        "fold != any() on boundary %r" % (flags,))

rng = random.Random(17084)
checked = 0
for _ in range(20000):
    n = rng.randint(0, 16)              # the model admits any non-negative length
    flags = [rng.random() < 0.5 for _ in range(n)]
    assert any(flags) == any_referenced_flag(flags), (
        "fold != any() on fuzz %r" % (flags,))
    checked += 1

# (A-reference 2) the element VALUES the model carries == Django's resolved
# attribute reads. Faithful stdlib stand-ins mirror expressions.py exactly:
#   Window.contains_over_clause = True ; (no `subquery` attr -> default False)
#   plain leaf (Col/Value): contains_over_clause = False ; no subquery
#   Subquery.subquery = True ; Subquery.contains_over_clause = False
#   composite (Coalesce/Func): contains_over_clause = any(e and
#       e.contains_over_clause for e in source_expressions); no own subquery attr
# window_flags[k]   == getattr(annotation, "contains_over_clause", True)  (default True, conservative)
# subquery_flags[k] == getattr(annotation, "subquery", False)            (default False)
class _Leaf:
    contains_over_clause = False
class _Window:
    contains_over_clause = True
class _Subquery:
    contains_over_clause = False
    subquery = True
class _Composite:
    def __init__(self, sources):
        self._sources = sources
    @property
    def contains_over_clause(self):
        return any(e is not None and e.contains_over_clause for e in self._sources)
class _Bare:
    pass

def win(a):
    return getattr(a, "contains_over_clause", True)
def sub(a):
    return getattr(a, "subquery", False)

# Window leaf -> over True, subquery default False
assert win(_Window()) is True and sub(_Window()) is False
# plain leaf -> both False
assert win(_Leaf()) is False and sub(_Leaf()) is False
# Subquery leaf -> subquery True, over False
assert sub(_Subquery()) is True and win(_Subquery()) is False
# Composite Coalesce(Window(...), 0.0) -> over True (the F2P annotation)
assert win(_Composite([_Window(), _Leaf()])) is True
assert sub(_Composite([_Window(), _Leaf()])) is False
# Composite of plain leaves / None -> over False
assert win(_Composite([_Leaf(), _Leaf(), None])) is False
# Composite containing a Subquery but no Window -> over False
assert win(_Composite([_Subquery(), _Leaf()])) is False
# Bare object lacking BOTH attrs -> conservative defaults (over True, subquery False)
assert win(_Bare()) is True and sub(_Bare()) is False

print("CONTAINMENT OK: every caller-reachable input (finite List[bool], incl. "
      "the empty boundary) lies in the any() domain; fold == any() over %d fuzz "
      "+ %d boundary lists; contains_over_clause/subquery attribute resolution "
      "matches expressions.py." % (checked, len(boundary)))
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "containment-fold-any",
        "axiom": "any_referenced_flag == Python any() (A-reference)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _CONTAINMENT_PROBE,
        "rationale": (
            "There is no consumed @ContractOnly axiom; the changed OR-reduction is "
            "modelled DEEPLY by the front-recursive @Pure fold any_referenced_flag. "
            "The fold refines Python any(), which is TOTAL over every finite "
            "List[bool] — so every input the model can reach (any finite boolean "
            "list, incl. the empty boundary the backward loops hit at len 0) is "
            "inside the callee's domain: containment holds, no caller-reachable "
            "input is AXIOM-TOO-WEAK-FOR-CALLER. The probe also re-confirms the "
            "element-value semantics the model carries "
            "(contains_over_clause/subquery resolution, incl. the F2P "
            "Coalesce(Window(...),0.0) composite -> True). The full real-callee "
            "G-AX check lives in axiom_check.py."
        ),
    },
]
