# properties.py — PBT falsification battery for django__django-13158.
#
# NOT a Nagini module; a manifest of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT.
#
# Defended surface (read from model.py + refinement.md + the gold patch + the
# single F2P test_union_none):
#
#   The change has two gold hunks, modelled deeply over a minimal Query
#   (`where_empty: bool` = WHERE-tree emptiness/is_empty; `child_empty: List[bool]`
#   = each combined-query constituent's is_empty flag):
#     * set_empty (model `mark_matching_nothing`) now RECURSES into every
#       constituent  -> postcond `Forall(k: child_empty[k] == True)`;
#     * clone (model `duplicate`) now DEEP-COPIES the constituents into a fresh,
#       independently-owned list -> postcond grants FULL `Acc(list_pred(Result()
#       .child_empty))` while the source keeps only its half (Acc(...,1/2)).
#   `none` composes duplicate-then-mark and must leave the SOURCE untouched
#   (Old(...) clauses) while the returned copy matches nothing at every level
#   (own + every constituent, hence the @Pure `all_marked`).
#
# READ-ONLY inputs (Acc(...,1/2)):
#   * matches_nothing(q): q.where_empty at 1/2  -> frame-mutation MANDATORY
#   * duplicate(q):       q.where_empty AND q.child_empty (+ list_pred) at 1/2
#                          -> frame-mutation MANDATORY (this is the deep-copy
#                             independence site: the #1 thing the patch fixes)
#
# Region-surgery: every variant is _BASE with a single _swap INSIDE one
# # impl-start / # impl-end block, so the frozen spec (axioms/pure/pre/post/
# invariants + signatures + the module-level ghost lemma_all_marked) is never
# touched -> same_spec is guaranteed True for every spec case.
#
# TERMINATION (total correctness — closes the vacuous-divergence hole):
# every contracted function carries Requires(MustTerminate(...)) with strictly
# decreasing measures (none: len+4 > duplicate: 3 > Query(): 2;
# mark_matching_nothing/matches_nothing: 2; ghost lemma: len+1). Nagini is a
# partial-correctness verifier by default, so WITHOUT the obligation a rival
# that diverges before returning — bare self-recursion of the contracted
# routine, or an endless loop — satisfies every Ensures VACUOUSLY and verifies
# (the G-PANEL-1 counterexample found by the audit). With it, a self-call is
# rejected (no strictly smaller measure is available) and an unbounded loop is
# rejected ("Loop might not take all unsatisfied obligations"), while the
# bounded constituent loops (measure len - i, decreasing) remain admitted —
# verified against both attack shapes during repair (cases 4b below).

from pathlib import Path

INSTANCE = "django__django-13158"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# 1. FRAME-MUTATION (MANDATORY — read-only inputs exist)
# ---------------------------------------------------------------------------

# 1a. matches_nothing(q): q.where_empty is Acc(...,1/2) = read-only. A rival that
#     WRITES the half-permission field to "produce" the answer must be rejected
#     for INSUFFICIENT PERMISSION. The gold postcond (Result()==q.where_empty)
#     is kept verbatim; the rejection is attributable to the write, not to a
#     value mismatch.
_FM_MATCHES = _swap(
    _BASE,
    "    return q.where_empty\n    # impl-end",
    # write to the half-permission field before returning it
    "    q.where_empty = q.where_empty\n"
    "    return q.where_empty\n    # impl-end",
)

# 1b. duplicate(q): q.child_empty is Acc(...,1/2) + list_pred at 1/2 = read-only.
#     The pre-patch BUG was exactly a shallow share that then let the source's
#     constituents be mutated. This rival mutates the read-only source list in
#     place (writes q.child_empty[i]) instead of building a fresh owned list,
#     then aliases. It must be rejected for INSUFFICIENT PERMISSION on the source
#     half-owned list_pred. Gold loop/invariants kept verbatim.
_FM_DUPLICATE = _swap(
    _BASE,
    "        obj.child_empty.append(q.child_empty[i])\n"
    "        i = i + 1\n"
    "    return obj\n    # impl-end",
    # write into the half-owned SOURCE list (frame violation), then append a copy
    "        q.child_empty[i] = q.child_empty[i]\n"
    "        obj.child_empty.append(q.child_empty[i])\n"
    "        i = i + 1\n"
    "    return obj\n    # impl-end",
)


# ---------------------------------------------------------------------------
# 2. PARTIAL-DOMAIN (correct on most of the F2P/P2P domain, diverges on a
#    sub-domain: the LAST constituent / an empty-vs-nonempty length class)
# ---------------------------------------------------------------------------

# 2a. mark_matching_nothing: loop bound `i < len-1` marks every constituent
#     EXCEPT the last. Correct for len(child_empty) in {0,1}? No: for len>=1 it
#     leaves the last flag False. test_union_none uses a 2-constituent union
#     (qs1.union(qs2)); a real patch that recursed into all-but-the-last
#     combined_query would leave the final union operand still matching its rows,
#     so qs3.none() would NOT return [] -> F2P FAILS. Must be rejected by the
#     postcond Forall(k: child_empty[k]==True).
_PD_MARK_LAST = _swap(
    _BASE,
    "    while i < len(q.child_empty):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(q.where_empty) and q.where_empty == True)",
    "    while i < len(q.child_empty) - 1:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(q.where_empty) and q.where_empty == True)",
)

# 2b. duplicate: copies the right number of flags but pins the LAST copied flag
#     to True regardless of the source. For a source whose last constituent is
#     NOT empty (the normal F2P state: qs3 still returns [0,1,8,9], so its
#     constituents are non-empty), the copy's last flag would read True while the
#     source's reads False -> the copy is NOT a faithful duplicate. A real patch
#     that fabricated the last flag would make qs3 (the SOURCE) appear partly
#     empty after a none()-style clone, or yield a wrong copy. Must be rejected
#     by Forall(k: Result().child_empty[k]==q.child_empty[k]).
_PD_DUP_LASTFLAG = _swap(
    _BASE,
    "        obj.child_empty.append(q.child_empty[i])\n"
    "        i = i + 1\n"
    "    return obj\n    # impl-end",
    # write True for the final index, the source flag elsewhere
    "        if i == len(q.child_empty) - 1:\n"
    "            obj.child_empty.append(True)\n"
    "        else:\n"
    "            obj.child_empty.append(q.child_empty[i])\n"
    "        i = i + 1\n"
    "    return obj\n    # impl-end",
)


# ---------------------------------------------------------------------------
# 3. UNGROUNDED-ORACLE / WRONG-CONSTANT echo on `none`
# ---------------------------------------------------------------------------
# The postconditions here are GROUNDED in the inputs (Result() flags pinned
# elementwise to True via the deep-copy + recursion; source pinned to Old(...)),
# so there is no @Pure answer-key an impl could echo to skip the work. The
# closest "echo" is to fabricate the copy directly. We still build the strongest
# wrong-copy rival: `none` returns a copy whose constituent vector is forced to a
# WRONG shape (mark the source's flags via mark on the SOURCE, returning a copy
# that ALIASES). This is the real bug the patch fixes (shared constituents).

# 3a. none: mutate the SOURCE then return it (no duplicate). The source's own
#     full permission is held, so where_empty=True succeeds, but the postcond
#     demands the SOURCE be UNCHANGED (q.where_empty == Old(q.where_empty)). A
#     real patch that emptied the live query instead of a copy would mutate qs3
#     in place: qs3.none() would return [] but qs3 would then ALSO return [] (not
#     [0,1,8,9]) -> the assertNumbersEqual(qs3, [0,1,8,9]) half of F2P FAILS.
#     Must be rejected by q.where_empty == Old(q.where_empty).
_ORACLE_NONE_INPLACE = _swap(
    _BASE,
    "    c = duplicate(q)\n"
    "    mark_matching_nothing(c)\n"
    "    lemma_all_marked(ToSeq(c.child_empty))\n"
    "    return c\n    # impl-end",
    # empty the SOURCE and return it (no independent copy) — the pre-fix shape
    "    mark_matching_nothing(q)\n"
    "    lemma_all_marked(ToSeq(q.child_empty))\n"
    "    return q\n    # impl-end",
)


# ---------------------------------------------------------------------------
# 4. CONTROL-FLOW-EFFECT — N/A (see assessment). All four functions are
#    value-returning with fully-pinned outputs and no raise/side-effect channel
#    invisible to the abstraction; the only side effect (mutating *q in
#    mark_matching_nothing / none) is already fully pinned by Old(...)/Forall
#    postconditions. No capability-token case is added.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 4b. NON-TERMINATION (vacuous-divergence — the audited G-PANEL-1 hole)
# ---------------------------------------------------------------------------

# 4b-i. none: bare self-recursion. Under partial correctness this discharges
#     every Ensures vacuously (the callee's own contract supplies them); the
#     MustTerminate obligation rejects it because no strictly smaller measure
#     is available for the self-call.
_NT_NONE_SELF = _swap(
    _BASE,
    "    c = duplicate(q)\n"
    "    mark_matching_nothing(c)\n"
    "    lemma_all_marked(ToSeq(c.child_empty))\n"
    "    return c\n    # impl-end",
    "    return none(q)\n    # impl-end",
)

# 4b-ii. none: endless loop before the real body (semantically infinite —
#     `i` never decreases below 0 — but not syntactically dead, so it reaches
#     the verifier rather than the dead-code translator check). Under partial
#     correctness the postcondition after the loop is satisfiable only
#     vacuously; the MustTerminate obligation rejects the unbounded loop (no
#     decreasing measure is carried).
_NT_NONE_LOOP = _swap(
    _BASE,
    "    c = duplicate(q)\n"
    "    mark_matching_nothing(c)\n"
    "    lemma_all_marked(ToSeq(c.child_empty))\n"
    "    return c\n    # impl-end",
    "    j = 0\n"
    "    while j >= 0:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(q.where_empty))\n"
    "        Invariant(Acc(q.child_empty) and Acc(list_pred(q.child_empty)))\n"
    "        Invariant(j >= 0)\n"
    "        # invariants-end\n"
    "        j = j + 1\n"
    "    c = duplicate(q)\n"
    "    mark_matching_nothing(c)\n"
    "    lemma_all_marked(ToSeq(c.child_empty))\n"
    "    return c\n    # impl-end",
)


# ---------------------------------------------------------------------------
# 5. POSITIVE CONTROLS (soundness — structurally different but CORRECT impls
#    that MUST verify). These keep every gold invariant valid (only the
#    EXECUTABLE shape changes: extra correct locals / a no-op identity write to
#    a FULLY-owned field), so a failure here would be SPEC-TOO-STRONG, not a
#    proof gap.
# ---------------------------------------------------------------------------

# 5a. mark_matching_nothing: write the constituent flag through a local boolean
#     bound to True. Same value written -> the Forall invariant proof is
#     identical; just a different executable shape. Must verify.
_POS_MARK = _swap(
    _BASE,
    "        q.child_empty[i] = True\n"
    "        i = i + 1\n"
    "    # impl-end",
    "        flag = True  # type: bool\n"
    "        q.child_empty[i] = flag\n"
    "        i = i + 1\n"
    "    # impl-end",
)

# 5b. duplicate: read the source values into correct locals before the writes
#     (obj.where_empty and the appended flag). Values are unchanged, so every
#     gold invariant (obj.where_empty == q.where_empty; the per-element Forall)
#     stays valid. Different shape, must verify.
_POS_DUP = _swap(
    _swap(
        _BASE,
        "    obj.where_empty = q.where_empty\n",
        "    w = q.where_empty  # type: bool\n"
        "    obj.where_empty = w\n",
    ),
    "        obj.child_empty.append(q.child_empty[i])\n"
    "        i = i + 1\n"
    "    return obj\n    # impl-end",
    "        val = q.child_empty[i]  # type: bool\n"
    "        obj.child_empty.append(val)\n"
    "        i = i + 1\n"
    "    return obj\n    # impl-end",
)

# 5c. matches_nothing: bind the read into a local then return it (read-only
#     respected — no write to the half-permission field). Different shape from
#     the bare `return q.where_empty`, must verify.
_POS_MATCHES = _swap(
    _BASE,
    "    return q.where_empty\n    # impl-end",
    "    r = q.where_empty  # type: bool\n"
    "    return r\n    # impl-end",
)


# ---------------------------------------------------------------------------
# 6. ADMISSIBILITY — a self-call confirming the precondition admits a normal
#    F2P-shaped input. test_union_none builds a fresh compound query (qs3 =
#    qs1.union(qs2)), i.e. a Query() with two non-empty constituents, calls
#    none() on it, expects the copy empty everywhere and the source intact.
#    We exercise the public composite `none` on exactly that shape and assert the
#    F2P observable. If the precondition rejected this normal input, that would
#    be PRECOND-TOO-STRONG. Edits stay inside the `none` impl region.
# ---------------------------------------------------------------------------
_ADMISS = _swap(
    _BASE,
    "    c = duplicate(q)\n"
    "    mark_matching_nothing(c)\n"
    "    lemma_all_marked(ToSeq(c.child_empty))\n"
    "    return c\n    # impl-end",
    # build a fresh F2P-shaped 2-constituent compound, run the composite,
    # and assert the F2P observable: copy empty everywhere, source untouched.
    "    src = Query()\n"
    "    src.child_empty.append(False)\n"
    "    src.child_empty.append(False)\n"
    "    Assert(len(src.child_empty) == 2)\n"
    "    Assert(src.where_empty == False)\n"
    "    cp = duplicate(src)\n"
    "    mark_matching_nothing(cp)\n"
    "    lemma_all_marked(ToSeq(cp.child_empty))\n"
    "    Assert(cp.where_empty == True)\n"
    "    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(cp.child_empty),\n"
    "                                          cp.child_empty[k] == True))))\n"
    "    Assert(src.where_empty == False)\n"
    "    Assert(len(src.child_empty) == 2)\n"
    "    c = duplicate(q)\n"
    "    mark_matching_nothing(c)\n"
    "    lemma_all_marked(ToSeq(c.child_empty))\n"
    "    return c\n    # impl-end",
)


SPEC_TESTS = [
    # --- FRAME-MUTATION (mandatory) ---
    {
        "id": "frame-mutation-matches_nothing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FM_MATCHES,
        "refinement": (
            "matches_nothing models the UNCHANGED is_empty observable, read by the "
            "compound-result compiler. A faithful real patch never WRITES the query's "
            "WHERE-emptiness while merely observing it; is_empty is a pure read. A "
            "rival that mutates the observable to fabricate the answer is not the gold "
            "is_empty and would corrupt the live query the compiler later reads, so it "
            "would not resolve test_union_none's source-intact half."
        ),
        "rationale": (
            "q.where_empty is held at Acc(...,1/2) (read-only). The write "
            "`q.where_empty = q.where_empty` needs full permission and is rejected for "
            "INSUFFICIENT PERMISSION by the fractional-permission system, not by the "
            "value postcondition (which is kept verbatim)."
        ),
    },
    {
        "id": "frame-mutation-duplicate-source-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FM_DUPLICATE,
        "refinement": (
            "The gold clone hunk's whole point is that the copy's combined_queries are "
            "INDEPENDENT of the source (deep copy). A rival that writes into the "
            "source's constituent list is the pre-patch shallow-share bug surface: "
            "mutating the copy reaches the source, so emptying the none()-copy would "
            "corrupt qs3 -> the assertNumbersEqual(qs3, [0,1,8,9]) half of "
            "test_union_none FAILS. Faithful patch does not write the source."
        ),
        "rationale": (
            "q.child_empty + list_pred(q.child_empty) are held at 1/2 (read-only "
            "source). The write `q.child_empty[i] = ...` needs full list_pred and is "
            "rejected for INSUFFICIENT PERMISSION on the half-owned source list."
        ),
    },
    # --- PARTIAL-DOMAIN ---
    {
        "id": "partial-domain-mark-skip-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PD_MARK_LAST,
        "refinement": (
            "Marking every constituent EXCEPT the last is exactly a set_empty that "
            "recurses into all-but-the-last combined_query. test_union_none's qs3 = "
            "qs1.union(qs2) has 2 constituents; leaving the last one matching its rows "
            "means qs3.none() still emits the second operand's rows, so "
            "assertSequenceEqual(qs3.none(), []) FAILS. The real partial patch does "
            "NOT resolve the F2P."
        ),
        "rationale": (
            "The postcondition Forall(k: 0<=k<len -> q.child_empty[k]==True) is "
            "violated at k = len-1 (left False); rejection comes from "
            "mark_matching_nothing's constituent-marking postcondition clause."
        ),
    },
    {
        "id": "partial-domain-duplicate-fabricate-last-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PD_DUP_LASTFLAG,
        "refinement": (
            "A clone that fabricates the LAST constituent flag (True regardless of the "
            "source) is not a faithful deep copy. In the F2P state qs3's constituents "
            "are non-empty (qs3 returns [0,1,8,9]); a clone whose last flag is forced "
            "empty mis-copies the query, so any read of the copy's constituents "
            "diverges from the source. The real patch copies each flag verbatim; this "
            "fabricating patch would not produce a faithful clone -> would not resolve."
        ),
        "rationale": (
            "The postcondition Forall(k: Result().child_empty[k]==q.child_empty[k]) is "
            "violated at k = len-1 whenever q.child_empty[len-1]==False; rejection "
            "comes from duplicate's flag-preservation postcondition clause."
        ),
    },
    # --- WRONG-COPY / in-place echo on the composite ---
    {
        "id": "none-mutate-source-no-copy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ORACLE_NONE_INPLACE,
        "refinement": (
            "Emptying the live query and returning it (no independent copy) is the "
            "wrong fix: qs3.none() would return [] but qs3 itself would then ALSO "
            "return [] instead of [0,1,8,9], so assertNumbersEqual(qs3, [0,1,8,9]) "
            "FAILS. A faithful patch copies before emptying (QuerySet.none = _chain "
            "then set_empty); this in-place variant does not resolve the F2P."
        ),
        "rationale": (
            "none's source-intact postcondition q.where_empty == Old(q.where_empty) "
            "(and the Old(...) constituent clauses) is violated because the source was "
            "marked; rejection comes from none's source-unchanged postcondition."
        ),
    },
    # --- NON-TERMINATION (vacuous divergence; must reject) ---
    {
        "id": "nonterm-none-self-recursion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _NT_NONE_SELF,
        "refinement": (
            "A none() that never returns is not QuerySet.none: the real composite "
            "always delivers its emptied clone (the F2P observable IS the returned "
            "value: assertSequenceEqual(qs3.none(), [])). A diverging real patch "
            "would hang the test instead of resolving it."
        ),
        "rationale": (
            "Bare self-recursion discharges every Ensures vacuously under partial "
            "correctness (this was the audited G-PANEL-1 counterexample). The "
            "MustTerminate(len+4) obligation rejects the self-call: no strictly "
            "smaller measure is available ('Callee ... might not take all "
            "unsatisfied obligations')."
        ),
    },
    {
        "id": "nonterm-none-endless-loop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _NT_NONE_LOOP,
        "refinement": (
            "Same F2P grounds as the self-recursion case: a none() that loops "
            "forever never returns the emptied copy, so the test hangs rather than "
            "passes; a diverging real patch does not resolve."
        ),
        "rationale": (
            "An unbounded `while True` before the real body makes the postcondition "
            "unreachable, hence vacuously satisfied under partial correctness. The "
            "MustTerminate obligation rejects the loop ('Loop might not take all "
            "unsatisfied obligations') since it carries no decreasing measure."
        ),
    },
    # --- POSITIVE CONTROLS (must verify) ---
    {
        "id": "positive-mark-local-flag",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MARK,
        "rationale": (
            "Writes True through a typed local instead of the literal — same value, so "
            "every gold invariant (incl. the per-element Forall) is preserved. A "
            "structurally-different CORRECT impl must verify (else SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "positive-duplicate-read-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DUP,
        "rationale": (
            "Reads the source where_empty / each flag into correct locals before the "
            "writes; values unchanged, so obj.where_empty==q.where_empty and the "
            "per-element copy Forall invariants stay valid. Different shape, must "
            "verify (else SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "positive-matches-local-read",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MATCHES,
        "rationale": (
            "Binds the half-permission read into a local then returns it (no write to "
            "the read-only field). Different shape from the bare return, must verify "
            "(else SPEC-TOO-STRONG)."
        ),
    },
    # --- ADMISSIBILITY (must verify) ---
    {
        "id": "admissibility-f2p-shaped-compound",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "Builds the F2P-shaped input (a fresh 2-constituent compound, like "
            "qs1.union(qs2)), runs the composite duplicate-then-mark on it, and asserts "
            "the F2P observable (copy empty everywhere, source untouched). The "
            "preconditions of duplicate/mark_matching_nothing must admit this normal "
            "input (else PRECOND-TOO-STRONG)."
        ),
    },
]

# No @ContractOnly axioms (meta.json axioms == []); the lone deep model
# `all_marked` is an A-reference validated executably by axiom_check.py / G-AX,
# not a consumed contract. The axiom lane is therefore vacuous here.
AXIOM_TESTS = []
