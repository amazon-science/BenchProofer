# properties.py — PBT manifest for scikit-learn__scikit-learn-25973.
#
# NOT a Nagini module; an adversarial falsification battery the runner
# (swebench_nagini.pbt) parses. Spec cases are full model.py variants that share
# the frozen spec byte-for-byte (region-surgery: ONLY the text inside
# # impl-start / # impl-end is edited) with a swapped implementation, checked by
# Nagini verify + markers.same_spec. Axiom cases are real-callee probes executed
# in the instance Docker image.
#
# Defended surface (read from model.py / refinement.md / mapping.md):
#   select_features(src, n_scorings) -> SelectionResult
#     READ-ONLY input: Requires(Acc(src.size, 1/2) and Acc(src.reusable, 1/2)).
#       => FRAME-MUTATION probe is MANDATORY (overwriting src must fail for
#          insufficient permission).
#     Load-bearing postconditions:
#       (P1) presents_family(Result().cv, src)      — abstract capability naming the
#            reported source AND the configured one; the ONLY grantor is
#            secure_reusable_source; un-Foldable, ref-tied (not value-tied).
#       (P2) Result().cv.size == src.size, Result().cv.reusable == True,
#            Result().cv.size > 0.
#       (P3) Forall k<n_scorings: counts[k] == draw_count(Result().cv.reusable,
#            Result().cv.size, k)  — count produced by drawing the WITNESSED source.
#       (P4) Forall k: counts[k] == src.size ;  (P5) Forall k: counts[k] >= 1.
#       (P6) len(counts) == n_scorings; counts carried through SelectionResult.
#       (P7) has_ledger(Result().cv) and draws_taken(Result().cv) == n_scorings
#            — the reported source HANDED OUT exactly one draw per scoring step.
#       (P8) scores_kept(Result().cv) == n_scorings — and exactly one score was
#            KEPT per draw. Because keep_score may run only while its own draw is
#            the single outstanding one (Requires draws_taken == scores_kept + 1)
#            and draw_splits may run only while none is outstanding (Requires
#            draws_taken == scores_kept), (P7)+(P8) pin the two effects to strictly
#            ALTERNATE: draw, keep, draw, keep, ... A total tally alone would not.
#       (P9) Forall k<n_scorings: counts[k] == score_from_draw(Result().cv, k) —
#            the reported record IS the journal those kept scores wrote, so no entry
#            can be a number remembered from outside the step that reports it.
#   secure_reusable_source(src) (A-consumed axiom == check_cv): preserves family
#       size, reusable==True, sole grantor of presents_family(result, argument);
#       grants has_ledger with draws_taken == scores_kept == 0. Requires src.size>=0.
#   presents_family (A-consumed, abstract @ContractOnly @Predicate): unforgeable,
#       and names the PAIR (drawn source, configured source).
#   has_ledger / draws_taken / scores_kept / score_from_draw (A-consumed): the two
#       ledgers and the journal. Abstract, so no impl can grant them or set a tally;
#       draw_splits is the only +1 on draws_taken, keep_score the only +1 on
#       scores_kept and the only writer of the journal.
#   draw_splits (A-consumed axiom == one real .split() draw): advances the draw
#       ledger by one and returns that draw's count; the ONLY way to obtain a draw,
#       and takeable only with no draw outstanding.
#   keep_score (A-consumed axiom == the per-candidate aggregation + store): advances
#       the kept-score ledger by one and commits the outstanding draw's count to the
#       journal; runnable ONLY while exactly one draw is outstanding.
#   draw_count / step_completes (A-reference deep model): per-draw split count.
#
# Three independent load-bearing pins, attacked separately below:
#   (P1) pins WHICH object the steps report and WHOSE family it presents — the
#        capability has no value-level witness (src.size is identical whether or
#        not a re-presenting source was secured, and a same-size family is
#        constructible), so a rival MUST route Result().cv through
#        secure_reusable_source(src) itself.
#   (P7) pins THAT the steps drew it n_scorings times. (P1)-(P6) alone cannot: the
#        spec forces cv.reusable==True and cv.size==src.size, so
#        draw_count(True, src.size, k) == src.size for EVERY k — the recorded
#        counts collapse to a constant and are byte-identical whether each step
#        drew or one remembered number was reused.
#   (P8)+(P9) pin WHEN each draw happened relative to the score it fed. (P7) alone
#        cannot: a total tally is reached just as well by taking every draw up
#        front and then reporting remembered numbers, which is the shape the
#        pre-repair spec admitted. The alternation preconditions plus the journal
#        equality reject it.
# Every reject case below attacks exactly one of those pins, and every refinement
# argues why the rival's faithful real patch would NOT resolve
# test_cv_generator_support (or, for the schedule case, why no admissible edit at
# the change site can produce that schedule at all).

from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-25973"
FLOAT_ENCODING = None  # meta.json float_encoding is null (the behaviour is control-flow / iterable-reuse)

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact gold impl region (between # impl-start / # impl-end) — the ONLY text
# any variant is allowed to touch, so same_spec is guaranteed.
_GOLD_IMPL = """\
    # impl-start
    cv = secure_reusable_source(src)  # type: SplitSource
    Assert(cv.size == src.size)
    used = []  # type: List[int]
    i = 0
    while i < n_scorings:
        # invariants-start
        Invariant(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
        Invariant(Acc(cv.size, 1 / 2) and Acc(cv.reusable, 1 / 2))
        Invariant(cv.size == src.size and cv.size > 0 and cv.reusable == True)
        Invariant(presents_family(cv, src))
        Invariant(has_ledger(cv))
        Invariant(draws_taken(cv) == i)
        Invariant(scores_kept(cv) == i)
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
                score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
        # the configured source is untouched by the steps: when it is one-shot,
        # its ledger still shows only the securing step's draw and no score kept
        # from any draw of it.
        Invariant(has_ledger(src))
        Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
        Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
        Invariant(0 <= i and i <= n_scorings)
        Invariant(Acc(list_pred(used)))
        Invariant(len(used) == i)
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                used[k] == draw_count(cv.reusable, cv.size, k))))
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                used[k] == src.size)))
        # the measure: `n_scorings - i` steps remain, strictly fewer each pass;
        # `+ 1` keeps it positive on the final pass (0 remaining).
        Invariant(MustTerminate(n_scorings - i + 1))
        # invariants-end
        # step i draws the secured source (`i` draws preceded it) and keeps the
        # score built from that draw before the next step draws.
        c = draw_splits(cv)  # type: int
        keep_score(cv, c)
        used.append(c)
        i = i + 1
    return SelectionResult(used, cv)
    # impl-end"""

# The gold loop's invariant block, reused verbatim by the variants that keep it
# (so a rejection is attributable to the edited STATEMENTS, not to weakened
# invariants). This is a string constant, not code: `_variant` only ever splices
# text into the impl region.
_GOLD_INV = """\
        # invariants-start
        Invariant(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
        Invariant(Acc(cv.size, 1 / 2) and Acc(cv.reusable, 1 / 2))
        Invariant(cv.size == src.size and cv.size > 0 and cv.reusable == True)
        Invariant(presents_family(cv, src))
        Invariant(has_ledger(cv))
        Invariant(draws_taken(cv) == i)
        Invariant(scores_kept(cv) == i)
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
                score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
        Invariant(has_ledger(src))
        Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
        Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
        Invariant(0 <= i and i <= n_scorings)
        Invariant(Acc(list_pred(used)))
        Invariant(len(used) == i)
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                used[k] == draw_count(cv.reusable, cv.size, k))))
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                used[k] == src.size)))
        Invariant(MustTerminate(n_scorings - i + 1))
        # invariants-end
"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: gold impl region not found verbatim")
    if src.count(old) != 1:
        raise AssertionError("not unique: gold impl region appears more than once")
    return src.replace(old, new, 1)


def _variant(new_impl):
    """Build a full model.py whose ONLY change vs _BASE is the impl region."""
    return _swap(_BASE, _GOLD_IMPL, new_impl)


# ---------------------------------------------------------------------------
# SPEC cases
# ---------------------------------------------------------------------------

# (1) POSITIVE CONTROL — soundness. Structurally different but CORRECT: the
# record is appended BEFORE the score is kept (the two effects on the ledger are
# untouched, only the list write moves) and a redundant local carries the count.
# Must verify (else SPEC-TOO-STRONG).
_IMPL_POS = """\
    # impl-start
    cv = secure_reusable_source(src)  # type: SplitSource
    Assert(cv.size == src.size)
    used = []  # type: List[int]
    i = 0
    while i < n_scorings:
""" + _GOLD_INV + """        # same draw, recorded first and kept second.
        c = draw_splits(cv)  # type: int
        used.append(c)
        keep_score(cv, c)
        i = i + 1
    return SelectionResult(used, cv)
    # impl-end"""

# (1b) POSITIVE CONTROL #2 — soundness, a DIFFERENT structural shape: prove
# (Assert) the step's draw equals the secured family before keeping it. Keeps all
# gold invariants; adds only redundant in-region Asserts the verifier discharges.
# Must verify.
_IMPL_POS2 = """\
    # impl-start
    cv = secure_reusable_source(src)  # type: SplitSource
    Assert(cv.size == src.size)
    Assert(cv.reusable == True)
    used = []  # type: List[int]
    i = 0
    while i < n_scorings:
""" + _GOLD_INV + """        Assert(draw_count(cv.reusable, cv.size, i) == cv.size)
        got = draw_splits(cv)  # type: int
        Assert(got == cv.size)
        keep_score(cv, got)
        Assert(scores_kept(cv) == i + 1)
        used.append(got)
        i = i + 1
    return SelectionResult(used, cv)
    # impl-end"""

# (2) ADMISSIBILITY — the precondition and the modelled operations' own domains
# must admit a normal F2P-shaped input. Two probes, then the gold body:
#   (a) the CARRIER admits the exact reported one-shot generator shape (size 5,
#       reusable False) and the deep draw model says such a source presents its
#       family once and nothing after — i.e. the input class the bug is about is
#       inside the type's domain, not excluded by it;
#   (b) the whole modelled chain runs on the ACTUAL in-domain input: secure it,
#       take a REAL draw of the secured source, and keep that draw's score,
#       reaching draws_taken == scores_kept == 1. (The probe cannot be run on a
#       hand-built source: `has_ledger` is abstract and only the securing axiom
#       grants it, which is precisely why no rival can fabricate a ledger.)
# The loop then continues from step 1 with the gold invariants verbatim. Must
# verify (else PRECOND-TOO-STRONG).
_IMPL_ADMISS = """\
    # impl-start
    probe = SplitSource(5, False)  # type: SplitSource
    Assert(probe.size == 5 and probe.reusable == False)
    Assert(draw_count(probe.reusable, probe.size, 0) == 5)
    Assert(draw_count(probe.reusable, probe.size, 1) == 0)
    cv = secure_reusable_source(src)  # type: SplitSource
    Assert(cv.size == src.size and cv.reusable == True)
    Assert(draws_taken(cv) == 0 and scores_kept(cv) == 0)
    first = draw_splits(cv)  # type: int
    Assert(first == src.size and first >= 1)
    keep_score(cv, first)
    Assert(draws_taken(cv) == 1 and scores_kept(cv) == 1)
    used = []  # type: List[int]
    used.append(first)
    i = 1
    while i < n_scorings:
""" + _GOLD_INV + """        c = draw_splits(cv)  # type: int
        keep_score(cv, c)
        used.append(c)
        i = i + 1
    return SelectionResult(used, cv)
    # impl-end"""

# (3) FRAME-MUTATION — MANDATORY (src is read-only: Acc(src.size,1/2)). A rival
# that WRITES to the read-only input to satisfy the postcondition vacuously. Here
# it tries to overwrite src.size (e.g. to force src.size == cv.size or to coerce
# the (P4) counts[k]==src.size relation). select_features holds only half
# permission on src.size, so the assignment requires (and lacks) full permission:
# must be REJECTED for insufficient permission. A byte-fuzzer never thinks to
# mutate the input. Gold invariants/body kept verbatim so the rejection is
# attributable to the write alone.
_IMPL_FRAME = """\
    # impl-start
    cv = secure_reusable_source(src)  # type: SplitSource
    Assert(cv.size == src.size)
    src.size = cv.size
    used = []  # type: List[int]
    i = 0
    while i < n_scorings:
""" + _GOLD_INV + """        c = draw_splits(cv)  # type: int
        keep_score(cv, c)
        used.append(c)
        i = i + 1
    return SelectionResult(used, cv)
    # impl-end"""

# (4) UNGROUNDED-ORACLE ECHO — never secure a source: record src.size directly
# (echo) and report a hand-built value-equal source as Result().cv. The recorded
# counts (P3/P4/P5) and the value pins (P2) are all satisfied by echo, but (P1)
# presents_family(Result().cv, src) CANNOT be: the capability is abstract and
# obtainable ONLY from secure_reusable_source, which this rival never calls, and
# neither can (P7)/(P8)/(P9), since the ledgers and the journal do not exist for a
# hand-built source. Must be REJECTED on (P1).
# refinement: its faithful real patch echoes the configured family size and draws
# the configured self.cv directly per candidate without calling check_cv, so the
# second candidate scoring aggregates an empty score set (_validation.py:274 draw
# -> :309 aggregate -> :1946 scores[0]) -> IndexError ->
# test_cv_generator_support still FAILS. Verifying here would be a true
# verify-not-resolve break (SPEC-TOO-WEAK).
_IMPL_ECHO = """\
    # impl-start
    echo = SplitSource(src.size, True)  # type: SplitSource
    used = []  # type: List[int]
    i = 0
    while i < n_scorings:
        # invariants-start
        Invariant(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
        Invariant(Acc(echo.size, 1 / 2) and Acc(echo.reusable, 1 / 2))
        Invariant(echo.size == src.size and echo.size > 0 and echo.reusable == True)
        # the configured source is never touched at all, so its ledgers keep the
        # entry values the precondition gave them.
        Invariant(has_ledger(src))
        Invariant(draws_taken(src) == 0 and scores_kept(src) == 0)
        Invariant(0 <= i and i <= n_scorings)
        Invariant(Acc(list_pred(used)))
        Invariant(len(used) == i)
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                used[k] == draw_count(echo.reusable, echo.size, k))))
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                used[k] == src.size)))
        Invariant(MustTerminate(n_scorings - i + 1))
        # invariants-end
        used.append(draw_count(echo.reusable, echo.size, i))
        i = i + 1
    return SelectionResult(used, echo)
    # impl-end"""

# (5) CONTROL-FLOW-EFFECT — the launder attack. Secure a source A (gets
# presents_family(A, src)), draw and keep on A the right number of times, but
# report a FRESH value-equal copy B (same size, same facet) as Result().cv. Every
# VALUE pin (P2/P3/P4/P5) holds on B, yet presents_family(B, src) was never
# granted (the token is tied to the object REFERENCE the axiom returned, not to
# its value) and B carries no ledger. Must be REJECTED on (P1).
# refinement: a real patch that secures a re-presenting source but then threads a
# freshly-built value-equal CV object into the per-candidate cross_val_score draws
# an object that, unless itself run through check_cv, is a one-shot iterable and
# exhausts after the first candidate -> IndexError; only the object check_cv
# returned (_split.py:2353-2403, list materialised at :2357 and re-yielded at
# :2402) re-presents its family. So a faithful launder patch does NOT resolve.
_IMPL_LAUNDER = """\
    # impl-start
    secured = secure_reusable_source(src)  # type: SplitSource
    Assert(presents_family(secured, src))
    cv = SplitSource(secured.size, secured.reusable)  # type: SplitSource
    Assert(cv.size == src.size)
    used = []  # type: List[int]
    i = 0
    while i < n_scorings:
        # invariants-start
        Invariant(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
        Invariant(Acc(secured.size, 1 / 4) and Acc(secured.reusable, 1 / 4))
        Invariant(has_ledger(secured))
        Invariant(secured.size == src.size and secured.reusable == True)
        Invariant(draws_taken(secured) == i and scores_kept(secured) == i)
        Invariant(Acc(cv.size, 1 / 2) and Acc(cv.reusable, 1 / 2))
        Invariant(cv.size == src.size and cv.size > 0 and cv.reusable == True)
        Invariant(has_ledger(src))
        Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
        Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
        Invariant(MustTerminate(n_scorings - i + 1))
        Invariant(0 <= i and i <= n_scorings)
        Invariant(Acc(list_pred(used)))
        Invariant(len(used) == i)
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                used[k] == draw_count(cv.reusable, cv.size, k))))
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                used[k] == src.size)))
        # invariants-end
        c = draw_splits(secured)  # type: int
        keep_score(secured, c)
        used.append(c)
        i = i + 1
    return SelectionResult(used, cv)
    # impl-end"""

# (6) PARTIAL-DOMAIN — correct on the boundary domain, wrong elsewhere. This
# rival models the PRE-PATCH semantics: it secures NO re-presenting source; it
# draws the configured (one-shot) source directly, recording draw_count(False,..)
# i.e. src.size on step 0 then 0 on every later step. For n_scorings==1 it would
# even satisfy (P4)/(P5) (single step only), but it diverges on the sub-domain
# n_scorings>=2 (step 1 records 0) and never carries presents_family or a ledger.
# Must be REJECTED (fails (P1) always; fails (P4)/(P5) for k>=1).
# refinement: this is literally the pre-patch control flow (score every candidate
# off the configured self.cv, never calling check_cv) — the second candidate
# scoring draws an exhausted generator, _aggregate_score_dicts indexes an empty
# list (_validation.py:1946) -> the reported IndexError;
# test_cv_generator_support FAILS. A verify here is a true verify-not-resolve.
_IMPL_PARTIAL = """\
    # impl-start
    oneshot = SplitSource(src.size, False)  # type: SplitSource
    used = []  # type: List[int]
    i = 0
    while i < n_scorings:
        # invariants-start
        Invariant(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
        Invariant(Acc(oneshot.size, 1 / 2) and Acc(oneshot.reusable, 1 / 2))
        Invariant(oneshot.size == src.size and oneshot.size > 0 and oneshot.reusable == False)
        Invariant(has_ledger(src))
        Invariant(draws_taken(src) == 0 and scores_kept(src) == 0)
        Invariant(0 <= i and i <= n_scorings)
        Invariant(Acc(list_pred(used)))
        Invariant(len(used) == i)
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                used[k] == draw_count(oneshot.reusable, oneshot.size, k))))
        Invariant(MustTerminate(n_scorings - i + 1))
        # invariants-end
        used.append(draw_count(oneshot.reusable, oneshot.size, i))
        i = i + 1
    return SelectionResult(used, oneshot)
    # impl-end"""

# (7) PARTIAL-DOMAIN (last step) — secures the proper source, draws and keeps
# once per step (so (P1)/(P7)/(P8) all hold) but records 0 for the FINAL step
# instead of the family it drew: a fence-post slip in the REPORT. Correct on steps
# 0..n-2, diverges on step n-1: violates (P3)/(P4)/(P5) and (P9) there. Must be
# REJECTED.
# refinement: a real patch that reports a zero score for the last candidate it
# scored is reporting a score no draw produced; the faithful shape — scoring the
# final candidate on an empty split set — aggregates an empty score list
# (_validation.py:1946) -> IndexError on that candidate, so it does NOT resolve.
_IMPL_FENCEPOST = """\
    # impl-start
    cv = secure_reusable_source(src)  # type: SplitSource
    Assert(cv.size == src.size)
    used = []  # type: List[int]
    i = 0
    while i < n_scorings:
        # invariants-start
        Invariant(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
        Invariant(Acc(cv.size, 1 / 2) and Acc(cv.reusable, 1 / 2))
        Invariant(cv.size == src.size and cv.size > 0 and cv.reusable == True)
        Invariant(presents_family(cv, src))
        Invariant(has_ledger(cv))
        Invariant(draws_taken(cv) == i)
        Invariant(scores_kept(cv) == i)
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
                score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
        Invariant(has_ledger(src))
        Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
        Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
        Invariant(0 <= i and i <= n_scorings)
        Invariant(Acc(list_pred(used)))
        Invariant(len(used) == i)
        Invariant(MustTerminate(n_scorings - i + 1))
        # invariants-end
        c = draw_splits(cv)  # type: int
        keep_score(cv, c)
        if i + 1 == n_scorings:
            used.append(0)
        else:
            used.append(c)
        i = i + 1
    return SelectionResult(used, cv)
    # impl-end"""

# (8) SUPPORTING mechanical near-miss — off-by-value on the first step: record
# one more split than the step's draw presented. Everything else is the gold
# behaviour, so the rejection isolates the value pins (P3)/(P4)/(P9).
_IMPL_OFFVALUE = """\
    # impl-start
    cv = secure_reusable_source(src)  # type: SplitSource
    Assert(cv.size == src.size)
    used = []  # type: List[int]
    i = 0
    while i < n_scorings:
        # invariants-start
        Invariant(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
        Invariant(Acc(cv.size, 1 / 2) and Acc(cv.reusable, 1 / 2))
        Invariant(cv.size == src.size and cv.size > 0 and cv.reusable == True)
        Invariant(presents_family(cv, src))
        Invariant(has_ledger(cv))
        Invariant(draws_taken(cv) == i)
        Invariant(scores_kept(cv) == i)
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
                score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
        Invariant(has_ledger(src))
        Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
        Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
        Invariant(0 <= i and i <= n_scorings)
        Invariant(Acc(list_pred(used)))
        Invariant(len(used) == i)
        Invariant(MustTerminate(n_scorings - i + 1))
        # invariants-end
        c = draw_splits(cv)  # type: int
        keep_score(cv, c)
        if i == 0:
            used.append(c + 1)
        else:
            used.append(c)
        i = i + 1
    return SelectionResult(used, cv)
    # impl-end"""

# (9) POSITIVE CONTROL #3 — soundness, a genuinely different loop SHAPE: count
# DOWN on a `remaining` counter instead of up on an index, phrasing the ledgers,
# the journal and the length invariants in terms of `n_scorings - remaining`.
# Draws once per step and keeps that draw's score, so it is correct and must
# VERIFY. This guards the (P7)/(P8)/(P9) repair against over-fitting to the gold
# loop's `i`-indexed shape.
_IMPL_POS3 = """\
    # impl-start
    cv = secure_reusable_source(src)  # type: SplitSource
    Assert(cv.size == src.size)
    used = []  # type: List[int]
    remaining = n_scorings  # type: int
    while remaining > 0:
        # invariants-start
        Invariant(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
        Invariant(Acc(cv.size, 1 / 2) and Acc(cv.reusable, 1 / 2))
        Invariant(cv.size == src.size and cv.size > 0 and cv.reusable == True)
        Invariant(presents_family(cv, src))
        Invariant(has_ledger(cv))
        Invariant(has_ledger(src))
        Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
        Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
        # the measure counts DOWN with `remaining`; `+ 1` keeps it above the
        # modelled operations' measure on the final pass.
        Invariant(MustTerminate(remaining + 1))
        Invariant(0 <= remaining and remaining <= n_scorings)
        Invariant(Acc(list_pred(used)))
        Invariant(len(used) == n_scorings - remaining)
        Invariant(draws_taken(cv) == n_scorings - remaining)
        Invariant(scores_kept(cv) == n_scorings - remaining)
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
                score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(used),
                used[k] == draw_count(cv.reusable, cv.size, k))))
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(used),
                                                used[k] == src.size)))
        # invariants-end
        got = draw_splits(cv)  # type: int
        keep_score(cv, got)
        used.append(got)
        remaining = remaining - 1
    return SelectionResult(used, cv)
    # impl-end"""

# (10) UNDRAWN-SOURCE / CACHED-DRAW — the counterexample class the value pins
# alone could not reject. It secures the proper source (so (P1)/(P2) hold on the
# REPORTED object) and records exactly the right numbers, but it takes ONE draw
# before the loop and keeps a score off that remembered number at every step: the
# steps themselves never draw. Because the spec forces cv.reusable==True and
# cv.size==src.size, draw_count(True, src.size, k) is the constant src.size, so
# (P3)/(P4)/(P5)/(P6) are ALL satisfied by the remembered number. (P8)'s
# alternation must reject it: the second keep_score runs with no draw outstanding.
# refinement: the faithful real patch hoists check_cv before the loop, draws the
# secured source once, and scores every candidate off that one remembered
# aggregate without re-drawing — so the per-candidate draw site is never fed the
# secured source. Keeping the real per-candidate cross_val_score there (the site
# the change exists to fix) leaves it drawing the configured one-shot generator,
# which exhausts after the first candidate -> IndexError; test_cv_generator_support
# FAILS. This faithful patch shape was machine-confirmed non-resolving.
_IMPL_CACHED_DRAW = """\
    # impl-start
    cv = secure_reusable_source(src)  # type: SplitSource
    Assert(cv.size == src.size)
    k = draw_splits(cv)  # type: int
    Assert(k == src.size)
    used = []  # type: List[int]
    i = 0
    while i < n_scorings:
        # invariants-start
        Invariant(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
        Invariant(Acc(cv.size, 1 / 2) and Acc(cv.reusable, 1 / 2))
        Invariant(cv.size == src.size and cv.size > 0 and cv.reusable == True)
        Invariant(presents_family(cv, src))
        Invariant(has_ledger(cv))
        Invariant(draws_taken(cv) == 1)
        Invariant(scores_kept(cv) == i)
        Invariant(k == src.size)
        Invariant(has_ledger(src))
        Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
        Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
        Invariant(MustTerminate(n_scorings - i + 1))
        Invariant(0 <= i and i <= n_scorings)
        Invariant(Acc(list_pred(used)))
        Invariant(len(used) == i)
        Invariant(Forall(int, lambda j: Implies(0 <= j and j < i,
                used[j] == draw_count(cv.reusable, cv.size, j))))
        Invariant(Forall(int, lambda j: Implies(0 <= j and j < i,
                                                used[j] == src.size)))
        # invariants-end
        # CHEAT: keep a score per step off ONE pre-loop draw; steps never draw.
        keep_score(cv, k)
        used.append(k)
        i = i + 1
    return SelectionResult(used, cv)
    # impl-end"""

# (11) ECHO WITHOUT ANY DRAW — the same class in its purest form: secure the
# source (so (P1)/(P2) hold on the reported object) and echo the input's family
# size at every step, never drawing and never keeping at all. Every value pin
# (P3)-(P6) is satisfied by the echo; both ledgers stand at 0. Must be REJECTED on
# (P7)/(P8). This is the shape the pre-repair spec's total tally admitted with no
# draw performed anywhere in the routine.
# refinement: identical faithful patch to (10) — the secured source is computed
# and then never drawn per candidate, so each candidate scoring consumes the
# configured one-shot generator and the second one raises IndexError;
# test_cv_generator_support FAILS.
_IMPL_ECHO_SECURED = """\
    # impl-start
    cv = secure_reusable_source(src)  # type: SplitSource
    Assert(cv.size == src.size)
    used = []  # type: List[int]
    i = 0
    while i < n_scorings:
        # invariants-start
        Invariant(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
        Invariant(Acc(cv.size, 1 / 2) and Acc(cv.reusable, 1 / 2))
        Invariant(cv.size == src.size and cv.size > 0 and cv.reusable == True)
        Invariant(presents_family(cv, src))
        Invariant(has_ledger(cv))
        Invariant(draws_taken(cv) == 0 and scores_kept(cv) == 0)
        Invariant(has_ledger(src))
        Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
        Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
        Invariant(0 <= i and i <= n_scorings)
        Invariant(Acc(list_pred(used)))
        Invariant(len(used) == i)
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                used[k] == draw_count(cv.reusable, cv.size, k))))
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                used[k] == src.size)))
        Invariant(MustTerminate(n_scorings - i + 1))
        # invariants-end
        # ECHO CHEAT: record the input family size; no draw is ever performed.
        used.append(src.size)
        i = i + 1
    return SelectionResult(used, cv)
    # impl-end"""

# (12) DRAIN-THEN-ECHO — the recorded refutation of the pre-repair spec, carried
# forward as a standing case. It burns the WHOLE draw tally in a throwaway
# pre-loop (so a total-tally obligation is met exactly) and then reports one
# remembered number per step, keeping the scores in the reporting loop. Under a
# total-tally spec every clause held; under the alternation the second pre-loop
# draw is already illegal (a draw with one outstanding), so it must be REJECTED.
# refinement: the faithful real patch secures the source with check_cv and drains
# it before the round loop while leaving the per-candidate cross_val_score drawing
# the configured self.cv — machine-measured on the real repo: the F2P test
# test_cv_generator_support raises IndexError: list index out of range and FAILS
# (72/72 P2P pass), so it does NOT resolve.
_IMPL_DRAIN_ECHO = """\
    # impl-start
    cv = secure_reusable_source(src)  # type: SplitSource
    Assert(cv.size == src.size)
    k = 0  # type: int
    j = 0
    while j < n_scorings:
        # invariants-start
        Invariant(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
        Invariant(Acc(cv.size, 1 / 2) and Acc(cv.reusable, 1 / 2))
        Invariant(cv.size == src.size and cv.size > 0 and cv.reusable == True)
        Invariant(presents_family(cv, src))
        Invariant(has_ledger(cv))
        Invariant(draws_taken(cv) == j)
        Invariant(scores_kept(cv) == 0)
        Invariant(has_ledger(src))
        Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
        Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
        Invariant(MustTerminate(n_scorings - j + 1))
        Invariant(0 <= j and j <= n_scorings)
        Invariant(Implies(j > 0, k == src.size))
        # invariants-end
        # DRAIN: take the whole tally up front, outside any scoring step.
        k = draw_splits(cv)
        j = j + 1
    used = []  # type: List[int]
    i = 0
    while i < n_scorings:
        Invariant(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
        Invariant(Acc(cv.size, 1 / 2) and Acc(cv.reusable, 1 / 2))
        Invariant(cv.size == src.size and cv.size > 0 and cv.reusable == True)
        Invariant(presents_family(cv, src))
        Invariant(has_ledger(cv))
        Invariant(draws_taken(cv) == n_scorings)
        Invariant(scores_kept(cv) == i)
        Invariant(k == src.size)
        Invariant(has_ledger(src))
        Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
        Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
        Invariant(MustTerminate(n_scorings - i + 1))
        Invariant(0 <= i and i <= n_scorings)
        Invariant(Acc(list_pred(used)))
        Invariant(len(used) == i)
        Invariant(Forall(int, lambda j2: Implies(0 <= j2 and j2 < i,
                used[j2] == draw_count(cv.reusable, cv.size, j2))))
        Invariant(Forall(int, lambda j2: Implies(0 <= j2 and j2 < i,
                                                used[j2] == src.size)))
        # ECHO: report the remembered number the pre-loop drain produced.
        keep_score(cv, k)
        used.append(k)
        i = i + 1
    return SelectionResult(used, cv)
    # impl-end"""

# (13) UNEVEN SCHEDULE — the residual freedom a pair of total tallies leaves:
# pipeline the effects two steps at a time (draw, draw, keep, keep). Both tallies
# still land on n_scorings and every reported entry is a genuine journal entry, so
# (P1)-(P7) and (P9) all hold; only the alternation preconditions reject it. Must
# be REJECTED.
# refinement: no admissible edit can produce this schedule. A candidate's score is
# obtained only from a cross_val_score call that draws (_validation.py:274),
# consumes the draw (:282-299) and aggregates it (:309) within itself before
# returning, and the candidate loop (_sequential.py:304-317) is sequential — so at
# the change site there is no way to take a second candidate's draw before the
# first candidate's score exists. The shape this rival stands for — holding an
# un-aggregated draw while taking another from the same source — is exactly how a
# configured one-shot source is consumed twice for one kept score, which is the
# reported failure, so admitting it would let a spec-satisfying rival describe a
# routine the change site cannot implement.
_IMPL_PIPELINED = """\
    # impl-start
    cv = secure_reusable_source(src)  # type: SplitSource
    Assert(cv.size == src.size)
    used = []  # type: List[int]
    i = 0
    while i < n_scorings:
""" + _GOLD_INV + """        # CHEAT: two draws in flight before either score is kept.
        c1 = draw_splits(cv)  # type: int
        c2 = draw_splits(cv)  # type: int
        keep_score(cv, c1)
        keep_score(cv, c2)
        used.append(c1)
        used.append(c2)
        i = i + 2
    return SelectionResult(used, cv)
    # impl-end"""

# (14) POSITIVE CONTROL #4 — soundness, and the sharp edge of the alternation
# pin: do all n_scorings draw/keep PAIRS first (each draw immediately aggregated,
# which is what the real per-candidate cross_val_score does) and only afterwards
# copy the journal's value into the report. This is a legitimately different
# shape whose faithful patch DOES resolve (every candidate scoring draws the
# secured source), so it MUST verify — the repair pins the draw/keep interleaving
# and the journal identity, not the position of the list write.
_IMPL_PAIRS_THEN_REPORT = """\
    # impl-start
    cv = secure_reusable_source(src)  # type: SplitSource
    Assert(cv.size == src.size)
    k = 0  # type: int
    j = 0
    while j < n_scorings:
        # invariants-start
        Invariant(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
        Invariant(Acc(cv.size, 1 / 2) and Acc(cv.reusable, 1 / 2))
        Invariant(cv.size == src.size and cv.size > 0 and cv.reusable == True)
        Invariant(presents_family(cv, src))
        Invariant(has_ledger(cv))
        Invariant(draws_taken(cv) == j and scores_kept(cv) == j)
        Invariant(Forall(int, lambda k2: Implies(0 <= k2 and k2 < scores_kept(cv),
                score_from_draw(cv, k2) == draw_count(cv.reusable, cv.size, k2))))
        Invariant(has_ledger(src))
        Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
        Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
        Invariant(MustTerminate(n_scorings - j + 1))
        Invariant(0 <= j and j <= n_scorings)
        Invariant(Implies(j > 0, k == src.size))
        # invariants-end
        k = draw_splits(cv)
        keep_score(cv, k)
        j = j + 1
    used = []  # type: List[int]
    i = 0
    while i < n_scorings:
        Invariant(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
        Invariant(Acc(cv.size, 1 / 2) and Acc(cv.reusable, 1 / 2))
        Invariant(cv.size == src.size and cv.size > 0 and cv.reusable == True)
        Invariant(presents_family(cv, src))
        Invariant(has_ledger(cv))
        Invariant(draws_taken(cv) == n_scorings and scores_kept(cv) == n_scorings)
        Invariant(k == src.size)
        Invariant(has_ledger(src))
        Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
        Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
        Invariant(MustTerminate(n_scorings - i + 1))
        Invariant(Forall(int, lambda k2: Implies(0 <= k2 and k2 < scores_kept(cv),
                score_from_draw(cv, k2) == draw_count(cv.reusable, cv.size, k2))))
        Invariant(0 <= i and i <= n_scorings)
        Invariant(Acc(list_pred(used)))
        Invariant(len(used) == i)
        Invariant(Forall(int, lambda k2: Implies(0 <= k2 and k2 < i,
                used[k2] == draw_count(cv.reusable, cv.size, k2))))
        Invariant(Forall(int, lambda k2: Implies(0 <= k2 and k2 < i,
                                                used[k2] == src.size)))
        used.append(k)
        i = i + 1
    return SelectionResult(used, cv)
    # impl-end"""


SPEC_TESTS = [
    {"id": "pos-control-record-before-keep", "kind": "soundness", "expect": "verify",
     "module": _variant(_IMPL_POS),
     "rationale": "structurally-different CORRECT impl (the step records its draw "
                  "before keeping the score; all gold invariants kept verbatim) must "
                  "verify; else SPEC-TOO-STRONG."},

    {"id": "pos-control-assert-shape", "kind": "soundness", "expect": "verify",
     "module": _variant(_IMPL_POS2),
     "rationale": "a second correct shape (adds redundant in-region Asserts the "
                  "verifier discharges, including scores_kept after the keep) must "
                  "verify; else SPEC-TOO-STRONG."},

    {"id": "pos-control-countdown-shape", "kind": "soundness", "expect": "verify",
     "module": _variant(_IMPL_POS3),
     "rationale": "a third correct shape that counts DOWN on `remaining` instead of "
                  "up on an index, phrasing the ledger/journal/length invariants as "
                  "n_scorings - remaining. Draws and keeps once per step, so it must "
                  "verify; guards the (P7)/(P8)/(P9) repair against over-fitting to "
                  "the gold loop's i-indexed shape (else SPEC-TOO-STRONG)."},

    {"id": "pos-control-pairs-then-report", "kind": "soundness", "expect": "verify",
     "module": _variant(_IMPL_PAIRS_THEN_REPORT),
     "rationale": "the sharp edge of the alternation pin: n_scorings draw/keep PAIRS "
                  "(each draw aggregated before the next, exactly what a "
                  "per-candidate cross_val_score does) followed by a separate "
                  "reporting loop. Its faithful patch feeds every candidate scoring "
                  "the secured source and DOES resolve, so it must verify — the "
                  "repair pins the draw/keep interleaving and the journal identity, "
                  "not where the list write sits (else SPEC-TOO-STRONG)."},

    {"id": "admiss-oneshot-input", "kind": "admissibility", "expect": "verify",
     "module": _variant(_IMPL_ADMISS),
     "rationale": "the precondition + the secure_reusable_source / draw_splits / "
                  "keep_score domains must admit a representative F2P-shaped one-shot "
                  "source (size 5, reusable False) — the exact reported generator "
                  "shape — and let it be drawn and its score kept; else "
                  "PRECOND-TOO-STRONG."},

    {"id": "frame-mutate-src-size", "kind": "uniqueness", "expect": "reject",
     "module": _variant(_IMPL_FRAME),
     "refinement": "writing to the configured CV source's family size has no "
                   "real-patch counterpart that resolves: the failure is iterable "
                   "exhaustion of a one-shot generator, which mutating a size scalar "
                   "cannot address; the faithful patch still draws an exhausted "
                   "generator for the second candidate -> IndexError, so "
                   "test_cv_generator_support FAILS.",
     "rationale": "src is read-only (Requires Acc(src.size,1/2)); the assignment "
                  "src.size=... needs full permission -> rejected for INSUFFICIENT "
                  "PERMISSION (the permission system, not a postcondition clause). "
                  "MANDATORY frame-mutation probe; a byte-fuzzer never finds it."},

    {"id": "echo-no-securing", "kind": "uniqueness", "expect": "reject",
     "module": _variant(_IMPL_ECHO),
     "refinement": "the faithful real patch echoes the configured family size and "
                   "scores every candidate off self.cv directly without calling "
                   "check_cv; the second candidate scoring draws an exhausted "
                   "generator, _aggregate_score_dicts indexes an empty list "
                   "(_validation.py:1946) -> IndexError; test_cv_generator_support "
                   "FAILS.",
     "rationale": "fails postcondition (P1) presents_family(Result().cv, src): the "
                  "capability is abstract (no body) and obtainable ONLY from "
                  "secure_reusable_source, which this rival never calls. A value-only "
                  "echo (P2/P3/P4/P5 all satisfied) cannot fabricate it, nor the "
                  "ledgers (P7)/(P8) nor the journal (P9)."},

    {"id": "launder-value-equal-copy", "kind": "uniqueness", "expect": "reject",
     "module": _variant(_IMPL_LAUNDER),
     "refinement": "a real patch that secures a re-presenting source but threads a "
                   "freshly-built value-equal CV object into the per-candidate "
                   "cross_val_score draws an object that, unless itself run through "
                   "check_cv, is a one-shot iterable exhausting after the first "
                   "candidate -> IndexError; only the object check_cv returned "
                   "(_split.py:2353-2403) re-presents its family. So the launder "
                   "patch does NOT resolve.",
     "rationale": "does all the drawing and keeping on the properly secured source "
                  "yet reports a value-equal copy: fails (P1) "
                  "presents_family(Result().cv, src) (the token is tied to the object "
                  "REFERENCE the axiom returned, not to its (size, reusable) VALUE) "
                  "and (P7)/(P8) (the copy carries no ledger). Control-flow/identity "
                  "effect invisible to the value abstraction — exactly what the "
                  "capability predicate discriminates."},

    {"id": "partial-domain-prepatch-oneshot", "kind": "uniqueness", "expect": "reject",
     "module": _variant(_IMPL_PARTIAL),
     "refinement": "this IS the pre-patch control flow: score every candidate off the "
                   "configured one-shot source (never call check_cv). The first "
                   "scoring yields the full family, every later one yields 0 -> "
                   "_aggregate_score_dicts on an empty list -> the reported "
                   "IndexError; test_cv_generator_support FAILS.",
     "rationale": "fails (P1) presents_family(Result().cv, src) (never secured) AND, "
                  "on the sub-domain n_scorings>=2, fails (P4) counts[k]==src.size "
                  "and (P5) counts[k]>=1 because draw_count(False,size,k>=1)==0. A "
                  "partial-domain rival correct only at n_scorings==1."},

    {"id": "partial-domain-last-step-zero", "kind": "uniqueness", "expect": "reject",
     "module": _variant(_IMPL_FENCEPOST),
     "refinement": "reporting a zero for the last candidate scored is reporting a "
                   "count no draw produced; its faithful shape — scoring the final "
                   "candidate on an empty split set — aggregates an empty score list "
                   "(_validation.py:1946) -> IndexError on that candidate, so the "
                   "patch does NOT resolve.",
     "rationale": "draws and keeps correctly (so (P1)/(P7)/(P8) hold) but pins the "
                  "FINAL step's reported count to 0, violating (P3)/(P4)/(P5) and the "
                  "journal identity (P9) on the sub-domain k==n_scorings-1. Reasoned "
                  "partial-domain (last element) attack."},

    {"id": "off-value-step0", "kind": "uniqueness", "expect": "reject",
     "module": _variant(_IMPL_OFFVALUE),
     "refinement": "recording one more split than the source yields on the first "
                   "scoring has no faithful real-patch counterpart that resolves — "
                   "over-counting splits is not behaviour the change produces; the "
                   "count is determined by the source's actual draw.",
     "rationale": "supporting near-miss: step 0 records c+1, violating (P3) "
                  "counts[0]==draw_count(...,0)==src.size, (P4) counts[0]==src.size "
                  "and (P9) the journal identity. Cheap value off-by-one; carries a "
                  "real (if thin) refinement."},

    {"id": "undrawn-cached-single-draw", "kind": "uniqueness", "expect": "reject",
     "module": _variant(_IMPL_CACHED_DRAW),
     "refinement": "the faithful real patch hoists check_cv before the loop, draws "
                   "the secured source once and scores every candidate off that one "
                   "remembered aggregate, never re-drawing — so the per-candidate "
                   "draw site keeps consuming the configured one-shot generator, "
                   "which exhausts after the first candidate -> IndexError; "
                   "test_cv_generator_support FAILS. Machine-confirmed non-resolving.",
     "rationale": "the counterexample class the value pins alone CANNOT reject: it "
                  "secures the proper source (P1)/(P2) and, because the spec forces "
                  "cv.reusable==True and cv.size==src.size, the constant "
                  "draw_count(True,src.size,k)==src.size makes (P3)/(P4)/(P5)/(P6) "
                  "all satisfiable by ONE remembered pre-loop draw. Rejected by the "
                  "(P8) alternation: the second keep_score runs with no draw "
                  "outstanding (draws_taken == scores_kept + 1 fails)."},

    {"id": "undrawn-echo-secured-source", "kind": "uniqueness", "expect": "reject",
     "module": _variant(_IMPL_ECHO_SECURED),
     "refinement": "same faithful patch as the cached-draw rival: the secured source "
                   "is computed and then never drawn per candidate, so each candidate "
                   "scoring consumes the one-shot generator and the second raises "
                   "IndexError; test_cv_generator_support FAILS.",
     "rationale": "the purest form of the same class — secure the source so (P1)/(P2) "
                  "hold on the reported object, then echo src.size at every step with "
                  "NO draw and NO keep anywhere. All value pins (P3)-(P6) satisfied by "
                  "the echo. Rejected on (P7)/(P8): both ledgers stand at 0."},

    {"id": "drain-tally-then-echo", "kind": "uniqueness", "expect": "reject",
     "module": _variant(_IMPL_DRAIN_ECHO),
     "refinement": "the faithful real patch secures the source with check_cv and "
                   "drains it before the round loop while the per-candidate "
                   "cross_val_score keeps drawing the configured self.cv — measured "
                   "on the real repo: test_cv_generator_support raises IndexError: "
                   "list index out of range and FAILS (P2P 72/72 pass). It does NOT "
                   "resolve.",
     "rationale": "the shape a TOTAL-tally obligation admits and the reason the "
                  "ledger pair is stated as an alternation: every draw is taken up "
                  "front, outside any scoring step, and the steps then report one "
                  "remembered number each. (P1)-(P7) and (P9) are all satisfiable "
                  "this way. Rejected at the second pre-loop draw_splits, whose "
                  "Requires draws_taken == scores_kept forbids taking a draw while "
                  "one is outstanding."},

    {"id": "uneven-draw-keep-schedule", "kind": "uniqueness", "expect": "reject",
     "module": _variant(_IMPL_PIPELINED),
     "refinement": "no admissible edit can produce this schedule: a candidate's score "
                   "comes only from a cross_val_score call that draws "
                   "(_validation.py:274), consumes (:282-299) and aggregates (:309) "
                   "within itself, and the candidate loop (_sequential.py:304-317) is "
                   "sequential, so the change site cannot take a second candidate's "
                   "draw before the first candidate's score exists. The shape it "
                   "stands for — holding an un-aggregated draw while taking another "
                   "from the same source — is exactly how a configured one-shot "
                   "source is consumed twice for one kept score, i.e. the reported "
                   "failure, so admitting it would let a verifying rival describe a "
                   "routine the change site cannot implement.",
     "rationale": "the residual freedom a pair of TOTAL tallies leaves: two draws in "
                  "flight, then two keeps. Both tallies still reach n_scorings and "
                  "every reported entry is a genuine journal entry, so "
                  "(P1)-(P7)+(P9) hold. Rejected only by the alternation "
                  "precondition on the second draw_splits (draws_taken == "
                  "scores_kept)."},
]


# ---------------------------------------------------------------------------
# AXIOM cases — the A-consumed axioms (secure_reusable_source == check_cv;
# presents_family / has_ledger / draws_taken / scores_kept / score_from_draw,
# abstract; draw_splits == one real .split() draw; keep_score == the
# per-candidate aggregation) + the A-reference deep model (draw_count). The
# probes EXECUTE the real check_cv / real CV source .split() / the real patched
# SequentialFeatureSelector.fit (never scrape source), open nothing on disk,
# import only sklearn+numpy (present in the image), and exit 0 iff the obligation
# holds. The logic mirrors the bundle's axiom_check.py (the established G-AX
# oracle). apply_gold=True: check_cv itself is UNCHANGED by the patch, but the
# third probe drives the PATCHED caller, and applying the patch keeps the other
# two faithful to the post-patch caller config.
# ---------------------------------------------------------------------------

# axiom-soundness: secure_reusable_source == check_cv. On a one-shot split
# GENERATOR (the exact F2P input) and on a KFold splitter, the source check_cv
# returns must (a) preserve the split-family size [Result().size == src.size],
# (b) re-present that family on EVERY draw [Result().reusable == True; every draw
# yields the full positive count == draw_count(True,size,*)], and the RAW
# generator must exhaust after the first draw [== draw_count(False,size,prior)],
# confirming the differential is real. Any disagreement => AXIOM-UNSOUND.
_PROBE_SOUND = r'''
import sys
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import check_cv, LeaveOneGroupOut, KFold


def draw_count(reusable, size, prior_draws):
    """Reference of model.py's pure draw_count (kept in lock-step)."""
    assert size >= 0 and prior_draws >= 0
    if reusable:
        return size
    if prior_draws == 0:
        return size
    return 0


def n_splits_drawn(cv_source, X, y):
    return sum(1 for _ in cv_source.split(X, y))


def _grouped(n_groups, random_state):
    X, y = make_classification(n_samples=40, n_features=6, random_state=random_state)
    groups = np.zeros_like(y, dtype=int)
    step = y.size // n_groups
    for g in range(n_groups):
        end = (g + 1) * step if g + 1 < n_groups else y.size
        groups[g * step:end] = g
    return X, y, groups


def check_materialise_and_reuse(n_groups, n_draws):
    X, y, groups = _grouped(n_groups, random_state=0)
    logo = LeaveOneGroupOut()
    size = logo.get_n_splits(groups=groups)
    assert size == n_groups, "setup: expected %d groups got %d" % (n_groups, size)
    splits = logo.split(X, y, groups=groups)          # one-shot generator (F2P input)
    reusable = check_cv(splits, y, classifier=True)   # secure once, before scoring
    first = n_splits_drawn(reusable, X, y)
    assert first == size, (
        "AXIOM-UNSOUND: check_cv(generator) yielded %d splits, configured family "
        "had %d (Ensures Result().size==src.size)" % (first, size))
    for k in range(n_draws):
        observed = n_splits_drawn(reusable, X, y)
        expected = draw_count(True, size, k)
        assert observed == expected, (
            "AXIOM-UNSOUND: draw %d of the materialised source yielded %d, "
            "draw_count(True,%d,%d)=%d" % (k, observed, size, k, expected))
        assert observed >= 1, "draw %d non-positive count %d" % (k, observed)


def check_materialise_splitter(n_folds, n_draws):
    X, y, _ = _grouped(3, random_state=1)
    kf = KFold(n_splits=n_folds)
    reusable = check_cv(kf, y, classifier=True)
    for k in range(n_draws):
        observed = n_splits_drawn(reusable, X, y)
        expected = draw_count(True, n_folds, k)
        assert observed == expected, (
            "AXIOM-UNSOUND (splitter): draw %d yielded %d, draw_count(True,%d,%d)=%d"
            % (k, observed, n_folds, k, expected))


def check_oneshot_exhaustion(n_groups, n_draws):
    X, y, groups = _grouped(n_groups, random_state=2)
    logo = LeaveOneGroupOut()
    size = logo.get_n_splits(groups=groups)
    splits = logo.split(X, y, groups=groups)          # RAW one-shot generator
    for k in range(n_draws):
        observed = sum(1 for _ in splits)
        expected = draw_count(False, size, k)
        assert observed == expected, (
            "AXIOM-UNSOUND (one-shot): draw %d of raw generator yielded %d, "
            "draw_count(False,%d,%d)=%d" % (k, observed, size, k, expected))
    assert size >= 1, "setup: family size must be positive"


def main():
    for n_groups in (2, 3, 4, 5):
        for n_draws in (1, 2, 3, 5):
            check_materialise_and_reuse(n_groups, n_draws)
    for n_folds in (2, 3, 5):
        for n_draws in (1, 2, 4):
            check_materialise_splitter(n_folds, n_draws)
    for n_groups in (2, 3, 4):
        for n_draws in (1, 2, 3, 4):
            check_oneshot_exhaustion(n_groups, n_draws)
    print("AXIOM-SOUND: secure_reusable_source == real check_cv (size preserved + "
          "presents_family on every draw == draw_count(True,size,*)); raw generator "
          "exhausts after first draw (draw_count(False,size,prior): size then 0).")
    return 0


sys.exit(main())
'''

# axiom-containment: which inputs does the MODEL actually pass to
# secure_reusable_source? From select_features.Requires: src.size > 0, n_scorings
# >= 1, and reusable is UNCONSTRAINED (any bool). The axiom Requires src.size >= 0
# — strictly WIDER than the caller-reachable src.size > 0, which is SOUND
# (covering more is fine, never a defect). This probe confirms every
# caller-reachable shape (size in {1..N}, reusable in {True,False}) is admitted by
# the real check_cv (no ValueError / no degenerate result) AND lies in the axiom's
# stated domain. A reachable input outside the domain would be
# AXIOM-TOO-WEAK-FOR-CALLER; none exists here.
_PROBE_COVER = r'''
import sys
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import check_cv, LeaveOneGroupOut, KFold

# The caller (select_features) can ONLY reach secure_reusable_source with:
#   src.size > 0           (Requires(src.size > 0))
#   src.reusable in {True, False}   (unconstrained boolean facet)
# The axiom Requires(src.size >= 0). Containment obligation: every caller-reachable
# (size, reusable) must lie in {size >= 0} -> trivially true for size > 0, and the
# real check_cv must accept the corresponding real source without raising.

def n_splits_drawn(cv_source, X, y):
    return sum(1 for _ in cv_source.split(X, y))


def _grouped(n_groups, random_state):
    X, y = make_classification(n_samples=40, n_features=6, random_state=random_state)
    groups = np.zeros_like(y, dtype=int)
    step = y.size // n_groups
    for g in range(n_groups):
        end = (g + 1) * step if g + 1 < n_groups else y.size
        groups[g * step:end] = g
    return X, y, groups


def main():
    # Enumerate the caller-reachable family sizes (size > 0) for BOTH facet values:
    #   reusable == False -> a one-shot LeaveOneGroupOut generator
    #   reusable == True  -> a re-presenting KFold splitter
    for size in (1, 2, 3, 4, 5):
        # containment of the axiom domain: caller reaches size > 0, axiom covers size >= 0
        assert size >= 0, "size %d outside axiom Requires(src.size>=0)" % size

        if size == 1:
            # LeaveOneGroupOut needs >=2 groups; the size-1 family is a KFold/identity
            # case. Skip the generator construction but still assert domain containment.
            continue

        X, y, groups = _grouped(size, random_state=size)
        logo = LeaveOneGroupOut()
        real_size = logo.get_n_splits(groups=groups)
        assert real_size == size, "setup mismatch %d != %d" % (real_size, size)

        # reusable == False facet: a one-shot generator (size > 0) — check_cv must
        # accept it (no ValueError) and return a usable source.
        gen = logo.split(X, y, groups=groups)
        secured = check_cv(gen, y, classifier=True)
        drawn = n_splits_drawn(secured, X, y)
        assert drawn == size, (
            "caller-reachable one-shot source (size=%d) not admitted as expected: "
            "check_cv result drew %d" % (size, drawn))

        # reusable == True facet: a KFold splitter (size > 0).
        kf = KFold(n_splits=size)
        secured_kf = check_cv(kf, y, classifier=True)
        drawn_kf = n_splits_drawn(secured_kf, X, y)
        assert drawn_kf == size, (
            "caller-reachable splitter (size=%d) not admitted: drew %d" % (size, drawn_kf))

    print("AXIOM-COVERED: every caller-reachable secure_reusable_source input "
          "(src.size>0, reusable in {True,False}) lies in the axiom Requires "
          "domain (src.size>=0, strictly wider -> sound) and the real check_cv "
          "admits the corresponding real source without raising. No reachable "
          "input is outside the covered domain.")
    return 0


sys.exit(main())
'''

# axiom-soundness #2: the SCHEDULE the two ledgers encode. draw_splits requires
# draws_taken == scores_kept (no draw outstanding) and keep_score requires
# draws_taken == scores_kept + 1 (its own draw outstanding), i.e. the modelled
# draws and kept scores strictly ALTERNATE and there is exactly one draw per kept
# score. This probe drives the REAL patched SequentialFeatureSelector.fit and
# measures that schedule off the real run: the object check_cv returns is drawn
# exactly once per candidate scoring, each draw presents the full family, and each
# draw's splits are all consumed before the next draw begins (so the score built
# from a draw exists before another draw is taken). It also measures the modelled
# unit: the number of draws equals the number of candidate scorings the repo's own
# arithmetic prescribes (sum over rounds r of n_features - r), NOT the number of
# rounds — which is what makes draws_taken(Result().cv) == n_scorings the faithful
# tally. Any disagreement => AXIOM-UNSOUND.
_PROBE_SCHEDULE = r'''
import sys
import numpy as np
import sklearn.feature_selection._sequential as seqmod
from sklearn.feature_selection import SequentialFeatureSelector
from sklearn.model_selection import LeaveOneGroupOut


class Null:
    """Trivial constant classifier: no numeric behaviour can perturb the counts."""
    _estimator_type = "classifier"

    def get_params(self, deep=True):
        return {}

    def set_params(self, **kw):
        return self

    def fit(self, X, y=None):
        self.classes_ = np.unique(y)
        return self

    def predict(self, X):
        return np.zeros(X.shape[0], dtype=int)


def make_data(n_features, n_samples=40):
    rng = np.random.RandomState(0)
    X = rng.rand(n_samples, n_features)
    y = np.array([i % 2 for i in range(n_samples)], dtype=int)
    groups = np.zeros_like(y)
    groups[y.size // 2:] = 1
    return X, y, groups


def measure(n_features, k):
    """Drive the real patched fit; return (per-draw split counts, trace)."""
    X, y, groups = make_data(n_features)
    splits = LeaveOneGroupOut().split(X, y, groups=groups)   # one-shot generator
    trace = []          # "draw" / "split" events, in real order
    per_draw = []       # splits presented, per draw
    real_check_cv = seqmod.check_cv

    class Counting:
        """Instrumentation around the object check_cv returns: one entry per
        real .split() draw. No repo logic is re-authored — the wrapper only
        counts what the real object yields."""

        def __init__(self, inner):
            self.inner = inner

        def split(self, *a, **kw):
            trace.append("draw")
            n = 0
            for pair in self.inner.split(*a, **kw):
                n += 1
                trace.append("split")
                yield pair
            per_draw.append(n)

        def get_n_splits(self, *a, **kw):
            return self.inner.get_n_splits(*a, **kw)

    def counting_check_cv(cv, yy=None, classifier=False):
        return Counting(real_check_cv(cv, yy, classifier=classifier))

    seqmod.check_cv = counting_check_cv
    try:
        SequentialFeatureSelector(Null(), n_features_to_select=k, tol=None,
                                  scoring="accuracy", cv=splits,
                                  direction="forward").fit(X, y)
    finally:
        seqmod.check_cv = real_check_cv
    return per_draw, trace


def main():
    for n_features, k in ((5, 3), (4, 2), (6, 5), (3, 1), (7, 2)):
        X, _y, groups = make_data(n_features)
        family = len(set(groups.tolist()))            # LeaveOneGroupOut family size
        per_draw, trace = measure(n_features, k)

        # (1) the modelled UNIT: one draw per candidate scoring, which the repo's
        # own arithmetic fixes at sum(n_features - r) over the k rounds — not k.
        scorings = sum(n_features - r for r in range(k))
        assert len(per_draw) == scorings, (
            "AXIOM-UNSOUND (unit): real patched fit drew the secured source %d "
            "times, candidate scorings = %d (rounds = %d)"
            % (len(per_draw), scorings, k))

        # (2) every draw presents the full positive family == draw_count(True,size,*).
        assert per_draw == [family] * scorings, (
            "AXIOM-UNSOUND (draw_count): per-draw counts %r, expected %d each"
            % (per_draw, family))

        # (3) the SCHEDULE: each draw's splits are all consumed before the next
        # draw begins, so the score aggregated from a draw exists before another
        # draw is taken -> draws and kept scores alternate one-for-one.
        expected_trace = ["draw"] + ["split"] * family
        assert trace == expected_trace * scorings, (
            "AXIOM-UNSOUND (schedule): draw/split trace is not %d repetitions of "
            "%r; head=%r" % (scorings, expected_trace, trace[:12]))

    print("AXIOM-SOUND (schedule): on the real patched fit the secured source is "
          "drawn exactly ONCE per candidate scoring (sum over rounds of "
          "n_features - r, not the round count), every draw presents the full "
          "positive family, and each draw is fully consumed before the next "
          "begins — so draws_taken/scores_kept advance one-for-one in step, which "
          "is what draw_splits' Requires(draws_taken==scores_kept) and keep_score's "
          "Requires(draws_taken==scores_kept+1) encode.")
    return 0


sys.exit(main())
'''

AXIOM_TESTS = [
    {"id": "ax-sound-secure-reusable-source", "axiom": "secure_reusable_source",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _PROBE_SOUND,
     "rationale": "executes the REAL check_cv on a one-shot generator (the F2P "
                  "input) + a KFold splitter and the RAW generator; asserts size "
                  "preservation + presents_family-on-every-draw (==draw_count(True,"
                  "size,*)) and the raw-generator exhaustion (==draw_count(False,"
                  "size,prior)). Any disagreement => AXIOM-UNSOUND."},

    {"id": "ax-cover-secure-reusable-source", "axiom": "secure_reusable_source",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _PROBE_COVER,
     "rationale": "the caller can reach secure_reusable_source only with src.size>0 "
                  "(both reusable facets); the axiom Requires src.size>=0 (strictly "
                  "wider -> sound). Confirms every caller-reachable real source is "
                  "admitted by check_cv. A reachable input outside the domain would "
                  "be AXIOM-TOO-WEAK-FOR-CALLER; none exists."},

    {"id": "ax-sound-draw-keep-schedule", "axiom": "keep_score",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _PROBE_SCHEDULE,
     "rationale": "drives the REAL patched fit and measures the schedule the two "
                  "ledgers encode: the secured source is drawn exactly once per "
                  "candidate scoring (the modelled unit — sum over rounds of "
                  "n_features - r, not the round count), each draw presents the full "
                  "family, and each draw is fully consumed before the next begins. "
                  "Validates draw_splits' Requires(draws_taken==scores_kept), "
                  "keep_score's Requires(draws_taken==scores_kept+1) and the "
                  "one-score-per-draw journal. Any disagreement => AXIOM-UNSOUND."},
]
