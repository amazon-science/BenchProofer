# properties.py — PBT falsification battery for pytest-dev__pytest-7432.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes. Each SPEC case is a full model.py variant that
# shares the FROZEN spec byte-for-byte (only the impl region — between
# `# impl-start` and `# impl-end` — is edited, GUARANTEEING same_spec) and is
# checked by Nagini verify. There are no @ContractOnly axioms / deep models in
# this bundle (meta.axioms == [], deep_model_references == []), so AXIOM_TESTS is
# empty.
#
# --- The defended surface ---------------------------------------------------
# finalize_skip_location(rep, definition_file, definition_line, skipped_by_mark,
#     rep_skipped, unexpected_success, suppress_xfail_reporting,
#     xfail_exception, xfailed_present, rep_already_skipped, exception_raised,
#     xfail_raises_mismatch, phase_is_call, xfail_strict, declared_reason,
#     raised_reason, success_reason) -> None
#
# rep: RunReport carries the nine observables the behaviour touches —
# (loc_is_triple: bool, loc_file: int, loc_line: int, loc_reason: int,
# outcome: int, xfail_note_present: bool, note_reason: int, explanation: int,
# explanation_reason: int). The precondition grants FULL permission Acc(...) on
# all nine — rep is a WRITABLE input (the function is SUPPOSED to write the
# recorded location, the outcome, the annotation and the stated verdict). There
# is NO Acc(x, 1/2) read-only object input, so the classic permission-frame
# mutation attack (overwrite a half-perm input) is N/A here; the analogue is the
# VALUE frame Implies(not V, rep.loc_is_triple == Old(rep.loc_is_triple)) — see
# REJ-frame.
#
# The postcondition has THREE groups, and all three are load-bearing.
#
# Group A — the skip-location correction (step 2 of the modelled behaviour):
#   (P0) Implies(V, not rep.loc_is_triple and rep.loc_file == LOC_ABSENT
#                   and rep.loc_line == LOC_ABSENT
#                   and rep.loc_reason == LOC_ABSENT)          [verdict annihilates]
#   (P1) Implies(not V, rep.loc_is_triple == Old(rep.loc_is_triple))  [shape frame]
#   (P2) Implies(C, rep.loc_is_triple and definition_line is not None
#                   and rep.loc_line == definition_line + 1
#                   and rep.loc_file == definition_file
#                   and rep.loc_reason == Old(rep.loc_reason))      [correction fires]
#   (P3) Implies(not C', the whole recorded location is framed)      [frame complement]
# where V := states_own_verdict(...) — the two cases that write a rendered
# verdict into the report's single account of itself, namely (Q-a) and the strict
# sub-case of (Q-d) — and C := skipped_by_mark and rep_skipped and
# Old(rep.loc_is_triple) and not V, C' := skipped_by_mark and rep_skipped and
# Old(rep.loc_is_triple).
# (P0) is why the shape frame is conditional: rep.longrepr is ONE attribute that
# holds EITHER a positional triple OR a verdict string, so a case that states a
# verdict destroys a location standing there and leaves nothing to correct. The
# annihilation is pinned POSITIVELY (all three elements read LOC_ABSENT) rather
# than merely left unconstrained, so "the slot holds no location" is observable.
# (P2) pins all THREE elements of the corrected location: the report must point
# at the test's own definition FILE and line, and must keep the skip reason it
# already carried — the correction moves where the report points and changes
# nothing about what it says.
#
# Group A' — AVAILABILITY of the test's own definition line, which is a PARTIAL
# observable (definition_line: Optional[int]; None is the reporting machinery
# answering that the test has no definition line at all, as it does for a run it
# cannot locate in source). The precondition is CONDITIONED on the correction's
# own three conditions:
#   (A0) Requires(Implies(skipped_by_mark and rep_skipped and rep.loc_is_triple,
#                         definition_line is not None and definition_line >= 0))
# So a report the correction does NOT apply to is admissible with no definition
# line at all, and must be finalised all the same. (A0) is a strictly WEAKER
# precondition than an unconditional `definition_line >= 0` — the domain is
# wider, so every clause above is a claim about more inputs. Its teeth:
# an impl may only read the definition line where (A0) supplies one, i.e. under
# the correction's own guard (or after an explicit absent-case branch of its
# own), because everywhere else there may be no line to read. The reject cases
# rej-hoist-unconditional / rej-hoist-assert / rej-hoist-partial-guard cover the
# three ways to get that wrong, rej-abandon-absent covers refusing to finalise
# the report at all when there is no line, and pos-absent-branch /
# pos-preguard-hoist / pos-budget-echo are the honest impls that must stay
# ADMITTED (else PRECOND/SPEC-TOO-STRONG). admiss-absent witnesses that the
# widened domain is non-empty, so (A0) is not vacuously weaker.
#
# Group B — the outcome classification (step 1). The report's outcome and its
# expected-failure annotation are pinned as a function of the inputs by the
# FIRST applicable case of a priority-ordered classification:
#   (Q-a) unexpected_success                       -> outcome FAILED, note framed
#   (Q-b) else suppress_xfail_reporting            -> outcome AND note both framed
#   (Q-c) else xfail_exception                     -> outcome SKIPPED, note set
#   (Q-d) else (not rep_already_skipped) and xfailed_present -> five sub-cases,
#         keyed on exception_raised / xfail_raises_mismatch / phase_is_call /
#         xfail_strict, each pinning outcome and note exactly
#   (Q-e) else                                     -> outcome AND note both framed
#
# Group C — the CONTENT each case records (what the report actually tells the
# user), which is a second observable dimension of the very same cases:
#   (R-1) the annotation's reason is the reason the case was GIVEN: raised_reason
#         in (Q-c), declared_reason in (Q-d)'s raises-match and non-strict
#         sub-cases, framed everywhere else. A case may not invent a reason,
#         drop one, or carry another case's.
#   (R-2) which standard verdict the report STATES is pinned per case:
#         EXPLANATION_UNEXPECTED_SUCCESS in (Q-a),
#         EXPLANATION_STRICT_UNEXPECTED_PASS in (Q-d)'s strict sub-case, and
#         framed in EVERY other case — so exactly two cases may state one.
#   (R-3) the stated verdict of the strict sub-case carries declared_reason.
#   (R-4) the stated verdict of (Q-a) carries success_reason — the reason
#         recorded alongside the unexpected success.
#
# Groups A+B+C together leave NO observable free: each of the nine fields is
# pinned, in every one of the nine cases, either to a function of the inputs or
# to its Old value. So a "wrong impl that still verifies" cannot live in an
# unconstrained slot of this model; it would have to live outside the model's
# nine observables, and the nine are exactly what the modelled behaviour writes.
#
# Group D — completion. Requires(MustTerminate(definition_line_budget(
# definition_line))) — i.e. definition_line + 2 where the reporting machinery
# supplies a definition line and 2 where it answers that there is none — obliges
# the finalisation to REACH its return, so none of A/B/C can be satisfied
# vacuously by a body that never comes back. Without it every clause above holds
# of `while True: pass` (partial correctness), which is a wrong impl that no
# postcondition can reject — see REJ-diverge, and note that the admissibility
# self-call therefore has to descend to a strictly smaller budget. The budget is
# TOTAL — owed on every admissible input, including one with no definition line
# at all — which is what makes rej-abandon-absent (come back only when the
# correction applies) a rejected impl rather than an unconstrained one.
#
# Group C is what makes the two failure-reporting cases distinguishable from a
# bare outcome code. An outcome of FAILED is written by four different
# sub-cases; without Group C an impl could set the code and say nothing, or say
# the wrong thing, and no clause would notice — while its faithful patch drops
# the explanation the strict-xpass and unexpected-success P2P tests read
# verbatim. The `note_reason` / `explanation` / `explanation_reason` observables
# are modelled as opaque int TOKENS, so Group C pins reason IDENTITY (which
# reason reached which slot) and never the rendering, which is presentation.
#
# The spec is GROUNDED: every clause pins a field to a function of the inputs
# (definition_line + 1, definition_file, a constant code, an argument token, or
# Old(...)), fully unfolded — no postcondition defers to a @Pure answer key, so
# the ungrounded-oracle-echo class does not apply to Groups A/B/C. The one @Pure
# helper an impl could echo is definition_line_budget, which appears in the
# completion obligation and not in any postcondition; echoing it (budget - 1) is
# an ADMITTED impl, not a break, because it is total by construction and its
# faithful refinement must therefore handle an absent definition line — see
# pos-budget-echo. We also supply honest cheapest-impl positive controls.
#
# The behaviour under specification: the location correction is governed solely
# by its own three conditions and is INDEPENDENT of the expected-failure
# reporting toggle, which governs the classification only. The F2P scenario
# (test_xfail_run_with_skip_mark[test_input1-expected1], args ["-rs","--runxfail"])
# fixes: skipped_by_mark=True, rep_skipped=True, loc_is_triple=True,
# suppress_xfail_reporting=True, the other booleans False.

from pathlib import Path

INSTANCE = "pytest-dev__pytest-7432"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact gold impl body that lives between `# impl-start` and `# impl-end`.
# Every variant is built by replacing this single, unique block — so the FROZEN
# spec (everything outside the impl region) is never touched and same_spec holds.
_GOLD_IMPL = """    if unexpected_success:
        # the recorded unexpected success decides the outcome and is stated to
        # the user, carrying its own reason; no annotation.
        rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
        rep.explanation_reason = success_reason
        rep.outcome = OUTCOME_FAILED
        # the verdict goes into the report's one account of itself: any
        # positional location that stood there is gone.
        rep.loc_is_triple = False
        rep.loc_file = LOC_ABSENT
        rep.loc_line = LOC_ABSENT
        rep.loc_reason = LOC_ABSENT
    elif suppress_xfail_reporting:
        # expected-failure reporting is toggled off: decline to interfere, and
        # shield the remaining classification cases from applying.
        pass
    elif xfail_exception:
        # an expected failure was raised imperatively: annotate with the reason
        # that was raised, read behind this case's lead-in.
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED
    elif (not rep_already_skipped) and xfailed_present:
        # an evaluated expected-failure mark on a run that is not already
        # skipped: classify by what the run actually did, recording the reason
        # the mark declared wherever this case records one.
        if exception_raised:
            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
            else:
                rep.outcome = OUTCOME_SKIPPED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM
        elif phase_is_call:
            if xfail_strict:
                # required to fail, passed anyway: state that verdict, into the
                # same one account, so no positional location survives here
                # either.
                rep.outcome = OUTCOME_FAILED
                rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
                rep.explanation_reason = declared_reason
                rep.loc_is_triple = False
                rep.loc_file = LOC_ABSENT
                rep.loc_line = LOC_ABSENT
                rep.loc_reason = LOC_ABSENT
            else:
                rep.outcome = OUTCOME_PASSED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM

    if skipped_by_mark and rep_skipped and rep.loc_is_triple:
        assert definition_line is not None
        rep.loc_file = definition_file
        rep.loc_line = definition_line + 1"""


def _swap_impl(new_body):
    """Return _BASE with the gold impl body replaced by new_body. Editing ONLY
    inside the impl region guarantees same_spec (the runner re-checks this)."""
    if _GOLD_IMPL not in _BASE:
        raise AssertionError("drift: gold impl body not found in model.py")
    if _BASE.count(_GOLD_IMPL) != 1:
        raise AssertionError("not unique: gold impl body")
    return _BASE.replace(_GOLD_IMPL, new_body, 1)


# The correct classification chain — including the content each case records —
# reused by the variants that keep it intact so that a case aimed at Group A is
# not accidentally also a Group B/C failure (a case must be attributable to the
# clause it targets).
_CHAIN = """    if unexpected_success:
        rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
        rep.explanation_reason = success_reason
        rep.outcome = OUTCOME_FAILED
        rep.loc_is_triple = False
        rep.loc_file = LOC_ABSENT
        rep.loc_line = LOC_ABSENT
        rep.loc_reason = LOC_ABSENT
    elif suppress_xfail_reporting:
        pass
    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED
    elif (not rep_already_skipped) and xfailed_present:
        if exception_raised:
            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
            else:
                rep.outcome = OUTCOME_SKIPPED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM
        elif phase_is_call:
            if xfail_strict:
                rep.outcome = OUTCOME_FAILED
                rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
                rep.explanation_reason = declared_reason
                rep.loc_is_triple = False
                rep.loc_file = LOC_ABSENT
                rep.loc_line = LOC_ABSENT
                rep.loc_reason = LOC_ABSENT
            else:
                rep.outcome = OUTCOME_PASSED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM"""

# The correct location correction, likewise reused.
_CORRECTION = """    if skipped_by_mark and rep_skipped and rep.loc_is_triple:
        assert definition_line is not None
        rep.loc_file = definition_file
        rep.loc_line = definition_line + 1"""


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-different CORRECT impls; MUST
# verify (else SPEC-TOO-STRONG). No induction lemma is required: the spec
# helpers are all direct boolean/arithmetic, so a step-reorder or a local
# reshape keeps the gold proof valid.
# ===========================================================================

# POS-1: the location-correction `if` is performed FIRST, then the outcome
# classification. The two steps DO meet in one place — both write the report's
# single account of itself — but in this order the correction's write is DEAD
# wherever they meet: the only cases that touch the location are the two that
# state a verdict, and they overwrite all four location facts afterwards.
# Enumerated exhaustively: the two orders agree on every one of the 16384
# abstract inputs (11 branch booleans x the shape flag x two definition_file
# tokens, LOC_ABSENT among them, x two definition_line values). Observably
# identical, so it MUST verify — a spec that rejected it would be forbidding a
# dead store. The sharp form, where the reordered write SURVIVES, is
# rej-stale-shape and is rejected.
_POS_REORDER = _CORRECTION + "\n\n" + _CHAIN

# POS-2: the classification is written as a flat guarded cascade instead of an
# if/elif chain — each case carries the negation of every higher-priority case
# explicitly. Same priority order, same effects, same recorded content,
# different control-flow shape. This is the honest structural variant that a
# chain-collapse attack only pretends to be: it preserves every case's EFFECT.
# Must verify.
_POS_FLATGUARDS = """    if unexpected_success:
        rep.outcome = OUTCOME_FAILED
        rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
        rep.explanation_reason = success_reason
        rep.loc_reason = LOC_ABSENT
        rep.loc_line = LOC_ABSENT
        rep.loc_file = LOC_ABSENT
        rep.loc_is_triple = False
    if (not unexpected_success) and (not suppress_xfail_reporting) \\
            and xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED
    if (not unexpected_success) and (not suppress_xfail_reporting) \\
            and (not xfail_exception) \\
            and (not rep_already_skipped) and xfailed_present:
        if exception_raised and xfail_raises_mismatch:
            rep.outcome = OUTCOME_FAILED
        if exception_raised and (not xfail_raises_mismatch):
            rep.outcome = OUTCOME_SKIPPED
            rep.xfail_note_present = True
            rep.note_reason = declared_reason
            rep.note_style = NOTE_STYLE_VERBATIM
        if (not exception_raised) and phase_is_call and xfail_strict:
            rep.outcome = OUTCOME_FAILED
            rep.explanation_reason = declared_reason
            rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
            rep.loc_reason = LOC_ABSENT
            rep.loc_line = LOC_ABSENT
            rep.loc_file = LOC_ABSENT
            rep.loc_is_triple = False
        if (not exception_raised) and phase_is_call and (not xfail_strict):
            rep.outcome = OUTCOME_PASSED
            rep.xfail_note_present = True
            rep.note_reason = declared_reason
            rep.note_style = NOTE_STYLE_VERBATIM

""" + _CORRECTION

# POS-3: same behaviour, but the correction's guard reads rep.loc_is_triple into
# a local first (local-variable reshape) and the corrected location's two
# elements are written in the opposite order. The local is read AFTER the
# classification, which is exactly where the repo's own guard reads the shape
# (skipping.py:297), so it equals the shape the correction is entitled to see;
# the correction still fires on exactly C and still lands the same location.
# Must verify.
_POS_LOCALSHAPE = _CHAIN + "\n\n" + """    is_triple = rep.loc_is_triple
    if skipped_by_mark and rep_skipped and is_triple:
        assert definition_line is not None
        rep.loc_line = definition_line + 1
        rep.loc_file = definition_file"""

# POS-4: the reason each case records is read into a local per case instead of
# being written from the argument directly, and the strict sub-case states its
# verdict before setting the outcome. Same recorded content, different data
# flow: Group C pins WHICH reason reaches WHICH slot, not how it got there, so
# this must verify (else the spec has over-fitted to the gold statement order).
_POS_REASON_LOCALS = """    if unexpected_success:
        rep.outcome = OUTCOME_FAILED
        rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
        rep.explanation_reason = success_reason
        gone = LOC_ABSENT
        rep.loc_is_triple = False
        rep.loc_file = gone
        rep.loc_line = gone
        rep.loc_reason = gone
    elif suppress_xfail_reporting:
        pass
    elif xfail_exception:
        imperative = raised_reason
        rep.xfail_note_present = True
        rep.note_reason = imperative
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED
    elif (not rep_already_skipped) and xfailed_present:
        from_mark = declared_reason
        if exception_raised:
            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
            else:
                rep.outcome = OUTCOME_SKIPPED
                rep.xfail_note_present = True
                rep.note_reason = from_mark
                rep.note_style = NOTE_STYLE_VERBATIM
        elif phase_is_call:
            if xfail_strict:
                rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
                rep.explanation_reason = from_mark
                rep.outcome = OUTCOME_FAILED
                nowhere = LOC_ABSENT
                rep.loc_is_triple = False
                rep.loc_file = nowhere
                rep.loc_line = nowhere
                rep.loc_reason = nowhere
            else:
                rep.outcome = OUTCOME_PASSED
                rep.xfail_note_present = True
                rep.note_reason = from_mark
                rep.note_style = NOTE_STYLE_VERBATIM

""" + _CORRECTION

# POS-5: the impl branches on the definition line's ABSENCE inside the
# correction's guard instead of relying on (A0) to rule it out. The absent branch
# is dead under (A0) — where the correction fires there IS a definition line —
# so the two agree on every admissible input, and the impl reads the line only
# where one is available. This is the honest cheapest handling of a partial
# observable and MUST verify (else the spec forbids checking for absence).
_POS_ABSENT_BRANCH = _CHAIN + "\n\n" + """    if skipped_by_mark and rep_skipped and rep.loc_is_triple:
        if definition_line is None:
            pass
        else:
            rep.loc_file = definition_file
            rep.loc_line = definition_line + 1"""

# POS-6: the corrected location is computed BEFORE the classification, but under
# the correction's own three conditions read on the PRE-classification state —
# which is exactly where (A0) supplies a definition line. The write still happens
# under the post-classification guard, so a verdict-stating case still leaves no
# location behind. Reading the definition line early is fine as long as it is
# read only where there is one; that is the distinction (A0) draws, and this
# case is the ADMITTED side of it (rej-hoist-unconditional is the rejected side).
# Must verify.
_POS_PREGUARD_HOIST = """    corrected_file = LOC_ABSENT
    corrected_line = LOC_ABSENT
    if skipped_by_mark and rep_skipped and rep.loc_is_triple:
        assert definition_line is not None
        corrected_file = definition_file
        corrected_line = definition_line + 1

""" + _CHAIN + """

    if skipped_by_mark and rep_skipped and rep.loc_is_triple:
        rep.loc_file = corrected_file
        rep.loc_line = corrected_line"""

# POS-7: the ONE @Pure helper in the spec is definition_line_budget, and it is
# echo-able: budget - 1 is definition_line + 1 wherever a definition line
# exists. Echoing it must be ADMITTED rather than rejected, because the helper is
# TOTAL — it answers for the absent case too — so an impl that computes the
# corrected line through it has already handled absence and may read it
# anywhere. That is what distinguishes this from rej-hoist-unconditional, which
# reads the raw definition line outside any guard. Must verify.
_POS_BUDGET_ECHO = """    budget = definition_line_budget(definition_line)
    corrected_file = definition_file

""" + _CHAIN + """

    if skipped_by_mark and rep_skipped and rep.loc_is_triple:
        rep.loc_file = corrected_file
        rep.loc_line = budget - 1"""


# ===========================================================================
# ADMISSIBILITY — a self-call on an F2P-shaped input must establish the Requires
# (else PRECOND-TOO-STRONG). The gold impl runs first; then we construct a fresh
# F2P-shaped RunReport (a skip-mark skip with a positional-triple location) and
# self-call finalize_skip_location with the EXACT F2P booleans (the --runxfail
# scenario: suppress_xfail_reporting=True), then assert the corrected location is
# the test definition (file AND line) with the skip reason kept, AND that the
# toggle left the outcome/annotation/stated verdict alone.
#
# The self-call passes definition_line - 1 under a `definition_line >= 1` guard,
# which is what discharges the completion obligation: the callee's budget
# (definition_line - 1) + 2 is strictly smaller than this frame's
# definition_line + 2, and definition_line - 1 >= 0 satisfies the location
# precondition. The guard is SATISFIABLE (definition_line is any non-negative
# int), so the branch is genuinely verified rather than vacuous — the control
# for that is admiss-vacuity-control below, which is the same body with an
# Assert(False) added and MUST be rejected.
_ADMISS_BODY = """    # admissibility witness: a normal F2P-shaped input must satisfy Requires.
    # positional triple, internal file 91 line 238 reason 44, already skipped,
    # no annotation, no stated verdict.
    if definition_line is not None and definition_line >= 1:
        witness = RunReport(True, 91, 238, 44, OUTCOME_SKIPPED, False, 0,
                            NOTE_STYLE_ABSENT, EXPLANATION_NONE, 0)
        finalize_skip_location(witness, 17, definition_line - 1, True, True,
                               False, True, False, False, True, True, False,
                               True, False, 71, 72, 73)
        Assert(witness.loc_line == definition_line)  # correction fired
        Assert(witness.loc_file == 17)       # the definition file
        Assert(witness.loc_reason == 44)     # the skip reason is kept as it was
        Assert(witness.loc_is_triple is True)  # no verdict stated => shape kept (P1)
        Assert(witness.outcome == OUTCOME_SKIPPED)   # toggle decided nothing
        Assert(witness.xfail_note_present is False)  # no annotation added (Q-b)
        Assert(witness.explanation == EXPLANATION_NONE)  # no verdict stated"""

_ADMISS = _GOLD_IMPL + "\n\n" + _ADMISS_BODY

# The vacuity control for the case above: identical, plus an Assert(False) in the
# guarded branch. If the guard were infeasible this would verify and the
# admissibility case would be proving nothing, so this MUST be rejected.
_ADMISS_VACUITY = (_GOLD_IMPL + "\n\n" + _ADMISS_BODY
                   + "\n        Assert(False)")

# The ABSENT-case admissibility witness: (A0) admits a report the correction does
# not apply to with NO definition line at all, and such a report must still be
# finalised — with its recorded location framed (P3) and its classification
# unchanged. This is what makes the widened domain non-vacuous: if `None` were not
# genuinely admissible here, conditioning availability would have weakened the
# precondition on paper only. Nested under a present-line guard purely so this
# frame's completion budget (definition_line + 2 >= 3) is strictly larger than the
# callee's (definition_line_budget(None) == 2).
_ADMISS_ABSENT_BODY = """    # admissibility witness: NO definition line at all, correction not applicable.
    if definition_line is not None and definition_line >= 1:
        absent = RunReport(True, 91, 238, 44, OUTCOME_SKIPPED, False, 0,
                           NOTE_STYLE_ABSENT, EXPLANATION_NONE, 0)
        finalize_skip_location(absent, 17, None, False, True, False, True,
                               False, False, True, True, False, True, False,
                               71, 72, 73)
        Assert(absent.loc_line == 238)   # not-C: the location is framed (P3)
        Assert(absent.loc_file == 91)
        Assert(absent.loc_reason == 44)
        Assert(absent.loc_is_triple is True)         # shape framed (P1)
        Assert(absent.outcome == OUTCOME_SKIPPED)    # toggle decided nothing
        Assert(absent.explanation == EXPLANATION_NONE)"""

_ADMISS_ABSENT = _GOLD_IMPL + "\n\n" + _ADMISS_ABSENT_BODY

# Its vacuity control, as above: MUST be rejected, or the absent-case witness is
# dead code and witnesses nothing.
_ADMISS_ABSENT_VACUITY = (_GOLD_IMPL + "\n\n" + _ADMISS_ABSENT_BODY
                          + "\n        Assert(False)")


# ===========================================================================
# UNIQUENESS / REJECT cases — same-spec WRONG impls. Each MUST be rejected (else
# SPEC-TOO-WEAK). Each carries a refinement: why its faithful real patch would
# NOT resolve the F2P/P2P.
#
# Group A cases (the location correction) come first, then Group B cases (the
# outcome classification), then Group C cases (the content each case records).
# The Group B cases keep the correction verbatim and damage the classification,
# so only the classification clauses can reject them; the Group C cases keep
# BOTH the correction and the classification's outcome/annotation decisions
# verbatim and damage only what the report tells the user, so only the content
# clauses can reject them.
# ===========================================================================

# --- Group A: the location correction --------------------------------------

# REJ-prepatch (CONTROL-FLOW-EFFECT, the canonical attack): the correction hangs
# off the classification chain as one more alternative rather than standing on
# its own. When suppress_xfail_reporting=True (the --runxfail F2P scenario), the
# chain takes case (b) and the chained correction is SUPPRESSED, leaving loc_line
# at Old(loc_line). C still holds (skipped_by_mark & rep_skipped & loc_is_triple
# all True), so (P2) demands loc_line == definition_line + 1 but the impl leaves
# it unchanged => REJECT.
_REJ_PREPATCH = _CHAIN + "\n" + """    elif skipped_by_mark and rep_skipped and rep.loc_is_triple:
        assert definition_line is not None
        rep.loc_file = definition_file
        rep.loc_line = definition_line + 1"""

# REJ-runxfail-guard (PARTIAL-DOMAIN): fire the correction only when NOT
# suppress_xfail_reporting. Correct on the no-runxfail sub-domain (test_input0)
# but on the F2P (suppress_xfail_reporting=True) it leaves loc_line untouched
# while C holds => violates (P2) => REJECT. This is the same defect expressed as
# a guard rather than as chain linkage.
_REJ_RUNXFAIL_GUARD = _CHAIN + "\n\n" + """    if (not suppress_xfail_reporting) and skipped_by_mark and rep_skipped \\
            and rep.loc_is_triple:
        assert definition_line is not None
        rep.loc_file = definition_file
        rep.loc_line = definition_line + 1"""

# REJ-offbyone (PARTIAL-DOMAIN / value): forget the `+ 1`. Fires on exactly C but
# stores definition_line instead of definition_line + 1 => violates (P2) which
# pins == definition_line + 1 => REJECT.
_REJ_OFFBYONE = _CHAIN + "\n\n" + """    if skipped_by_mark and rep_skipped and rep.loc_is_triple:
        assert definition_line is not None
        rep.loc_file = definition_file
        rep.loc_line = definition_line"""

# REJ-frame (VALUE-FRAME MUTATION — the read-only analogue): the correction also
# writes rep.loc_is_triple (flips the recorded shape). The function HAS full
# permission to loc_is_triple, so this is not a permission error; instead it
# violates the explicit shape-frame clause (P1) Implies(not V, rep.loc_is_triple
# == Old(rep.loc_is_triple)) => REJECT. The chain here states no verdict on the
# inputs that reach the correction, so V is false and (P1) bites. (rep has no Acc(.,1/2) read-only field, so
# the permission-frame variant is N/A; this is its value-frame counterpart.)
_REJ_FRAME = _CHAIN + "\n\n" + """    if skipped_by_mark and rep_skipped and rep.loc_is_triple:
        assert definition_line is not None
        rep.loc_file = definition_file
        rep.loc_line = definition_line + 1
        rep.loc_is_triple = False"""

# --- Group A': the coupling between the two steps (clause (P0)) -------------
#
# rep.longrepr is ONE attribute holding EITHER a positional triple OR a rendered
# verdict string. The four cases below are the ways an impl can get that wrong
# while leaving the correction and the whole classification otherwise verbatim,
# so only (P0)/(P1) can reject them.

_ANNIH_A = """        rep.loc_is_triple = False
        rep.loc_file = LOC_ABSENT
        rep.loc_line = LOC_ABSENT
        rep.loc_reason = LOC_ABSENT
"""
_ANNIH_STRICT = """                rep.loc_is_triple = False
                rep.loc_file = LOC_ABSENT
                rep.loc_line = LOC_ABSENT
                rep.loc_reason = LOC_ABSENT
"""
assert _CHAIN.count(_ANNIH_A) == 1, "drift: case (a) annihilation not unique"
assert _CHAIN.count(_ANNIH_STRICT) == 1, "drift: strict annihilation not unique"

# REJ-verdict-keeps-loc (TWO-SLOT FICTION): case (a) states its verdict but
# leaves the positional location standing. That is the reading the real hook
# contradicts — the string assignment at skipping.py:269/271 replaces the tuple —
# so (P0) demands the three elements read LOC_ABSENT and this impl leaves them at
# their old values => REJECT.
_REJ_VERDICT_KEEPS_LOC = (_CHAIN.replace(_ANNIH_A, "", 1) + "\n\n" + _CORRECTION)

# REJ-strict-keeps-loc: the same fiction in the OTHER verdict-stating case (the
# strict sub-case of (Q-d), skipping.py:290). Kept separate from the case above so
# each of the two arms of `states_own_verdict` is attacked on its own.
_REJ_STRICT_KEEPS_LOC = (_CHAIN.replace(_ANNIH_STRICT, "", 1) + "\n\n"
                         + _CORRECTION)

# REJ-nonverdict-destroys-loc (the converse over-approximation): a case that
# states NO verdict — the imperative expected-failure arm (skipping.py:275-278) —
# discards the positional location anyway. The real hook only writes wasxfail and
# outcome there, so (P1) demands the shape be framed => REJECT. Refinement: a
# patch that emptied the longrepr of an imperatively-xfailed report would lose the
# skip location the reporting tests read.
_REJ_NONVERDICT_DESTROYS_LOC = (_CHAIN.replace(
    """    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED""",
    """    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED
        rep.loc_is_triple = False
        rep.loc_file = LOC_ABSENT
        rep.loc_line = LOC_ABSENT
        rep.loc_reason = LOC_ABSENT""", 1) + "\n\n" + _CORRECTION)

# REJ-stale-shape (READS THE WRONG STATE): snapshot the location shape BEFORE the
# classification and correct afterwards on the snapshot. The repo's guard
# `type(rep.longrepr) is tuple` at skipping.py:297 runs AFTER the chain, so this
# fires on a report whose account a verdict has since replaced and writes a file
# and a line into a slot that must read absent => REJECT on (P0). This is the
# sharp form of the reordering that pos-reorder shows to be harmless: there the
# write is dead, here it survives.
_REJ_STALE_SHAPE = ("    stale_triple = rep.loc_is_triple\n" + _CHAIN + "\n\n"
                    + _CORRECTION.replace("rep.loc_is_triple", "stale_triple"))

# REJ-partial-annihilation (HALF-OBSERVABLE): case (a) drops the triple SHAPE but
# leaves the three positional elements readable, i.e. it empties the slot in name
# only. (P0) pins all four, precisely so "there is no location" cannot be recorded
# as "there is a location nobody is supposed to look at" => REJECT.
_REJ_PARTIAL_ANNIHILATION = (_CHAIN.replace(
    _ANNIH_A, "        rep.loc_is_triple = False\n", 1) + "\n\n" + _CORRECTION)

# REJ-overfire (PARTIAL-DOMAIN): drop the `skipped_by_mark` conjunct from the
# guard. When skipped_by_mark=False but rep_skipped & loc_is_triple are True
# (e.g. an imperative pytest.skip() call, not a skip MARK), C is False so (P3)
# demands loc_line == Old(loc_line), yet this impl rewrites it => REJECT.
_REJ_OVERFIRE = _CHAIN + "\n\n" + """    if rep_skipped and rep.loc_is_triple and definition_line is not None:
        rep.loc_file = definition_file
        rep.loc_line = definition_line + 1"""

# REJ-noop (cheap SUPPORTING case, still carries a refinement): do nothing at
# all. When C holds, (P2) demands loc_line == definition_line + 1 but the impl
# leaves it at Old(loc_line) => REJECT. (Also violates Groups B and C, which is
# fine: a do-nothing impl is wrong on every count.)
_REJ_NOOP = """    pass"""

# REJ-touch-else (PARTIAL-DOMAIN, off-domain write): correct on C, but on the
# complement it actively scrambles loc_line (sets it to definition_line + 1
# unconditionally). On not-C this violates (P3) => REJECT. Refinement: a real
# patch that rewrites every report's location would corrupt non-skip reports,
# breaking the P2P suite and the skip-without-mark cases.
_REJ_TOUCH_ELSE = _CHAIN + "\n\n" + """    if definition_line is not None:
        rep.loc_line = definition_line + 1
        rep.loc_file = definition_file"""

# REJ-loc-file-drop (PARTIAL-DOMAIN / the corrected location is a TRIPLE): the
# line is corrected but the file is left pointing where it was. (P2) pins all
# three elements of the corrected location, so leaving loc_file at Old(loc_file)
# violates it => REJECT.
_REJ_LOC_FILE_DROP = _CHAIN + "\n\n" + """    if skipped_by_mark and rep_skipped and rep.loc_is_triple:
        assert definition_line is not None
        rep.loc_line = definition_line + 1"""

# REJ-loc-reason-clobber (CONTROL-FLOW-EFFECT / off-slot write): the correction
# lands the right file and line but also overwrites the skip reason the location
# carried with the mark's declared reason. (P2) pins loc_reason ==
# Old(loc_reason) — the correction moves where the report points and changes
# nothing about what it says => REJECT.
_REJ_LOC_REASON_CLOBBER = _CHAIN + "\n\n" + """    if skipped_by_mark and rep_skipped and rep.loc_is_triple:
        assert definition_line is not None
        rep.loc_file = definition_file
        rep.loc_line = definition_line + 1
        rep.loc_reason = declared_reason"""

# --- Group A'': availability of the definition line (clause (A0)) ------------
#
# The test's own definition line is PARTIAL: for a run the reporting machinery
# cannot locate in source there is no definition line at all. (A0) supplies one
# exactly where the correction applies, so these four impls each read (or refuse
# to finalise) where (A0) supplies nothing. They are the cases that make the
# conditioned precondition load-bearing rather than decorative: under an
# UNCONDITIONAL `definition_line >= 0` all four of the first three would verify.

# REJ-hoist-unconditional (MODELING-BOUNDARY / partial-domain): the corrected
# location is computed up front, outside every guard, and applied later under the
# correct guard. Abstractly the write lands in the same place, but the definition
# line is READ where (A0) does not supply one => REJECT.
# Refinement: the real hook obtains the definition location by asking the
# reporting machinery for it, and that question has no answer for a run it cannot
# locate; asking it for every report — as this impl's faithful patch must, since
# it consumes a definition line before it knows the correction applies — leaves
# every report of such a run unfinalised, and the reporting tests that build
# their own un-locatable run items fail.
_REJ_HOIST_UNCONDITIONAL = """    corrected_file = definition_file
    corrected_line = definition_line + 1

""" + _CHAIN + """

    if skipped_by_mark and rep_skipped and rep.loc_is_triple:
        rep.loc_file = corrected_file
        rep.loc_line = corrected_line"""

# REJ-hoist-assert (the same defect, stated as an assumption): assert the
# definition line into existence at the top and then hoist. The assertion is
# exactly the claim (A0) declines to make of every report => REJECT.
# Refinement: same patch as above, and the same unfinalised reports.
_REJ_HOIST_ASSERT = ("    assert definition_line is not None\n"
                     + _REJ_HOIST_UNCONDITIONAL)

# REJ-hoist-partial-guard (PARTIAL-DOMAIN, the near miss): read the definition
# line under only ONE of the correction's three conditions. A run skipped by a
# skip-style mark whose report is not skipped, or whose account is no longer a
# positional triple, is not a run (A0) supplies a definition line for => REJECT.
# This is the sharp case: it shows the guard the read needs is the correction's
# OWN guard, not merely something in its neighbourhood.
_REJ_HOIST_PARTIAL_GUARD = """    corrected_file = definition_file
    corrected_line = LOC_ABSENT
    if skipped_by_mark:
        assert definition_line is not None
        corrected_line = definition_line + 1

""" + _CHAIN + """

    if skipped_by_mark and rep_skipped and rep.loc_is_triple:
        rep.loc_file = corrected_file
        rep.loc_line = corrected_line"""

# REJ-underfire-budget (PARTIAL-DOMAIN / boundary, via the completion helper):
# correct only where the budget says the definition line is at least 2, i.e. skip
# the correction on the first two lines of a file. C holds there and (P2) demands
# the corrected line => REJECT. Guards the boundary that the widened domain makes
# reachable: definition_line == 0 is still admissible under the correction.
_REJ_UNDERFIRE_BUDGET = _CHAIN + "\n\n" + """    if skipped_by_mark and rep_skipped and rep.loc_is_triple:
        if definition_line_budget(definition_line) >= 4:
            assert definition_line is not None
            rep.loc_file = definition_file
            rep.loc_line = definition_line + 1"""

# REJ-abandon-absent (COMPLETION / the preservation obligation): finalise, and
# come back, only when the correction applies; on every other report never come
# back at all. Every postcondition still holds vacuously there, so ONLY Group D
# can reject this => REJECT. Refinement: a patch that hangs on any report the
# correction does not apply to hangs the whole run.
_REJ_ABANDON_ABSENT = _CHAIN + "\n\n" + """    if skipped_by_mark and rep_skipped and rep.loc_is_triple:
        assert definition_line is not None
        rep.loc_file = definition_file
        rep.loc_line = definition_line + 1
    else:
        while True:
            Assert(True)"""

# --- Group B: the outcome classification -----------------------------------
# These keep the location correction VERBATIM and damage only the
# classification. Group A cannot see them at all; they are rejected by the
# classification clauses (Q-a)..(Q-e) alone.

# REJ-classify-drop-xfailmark (CONTROL-FLOW-EFFECT): keep the correction and the
# first three classification cases, drop case (d) — the expected-failure-mark
# path — entirely. On an input where a marked expected failure actually failed
# (xfailed_present, not already skipped, exception raised, inside the declared
# raises set), (Q-d) demands outcome SKIPPED with the annotation set, but this
# impl leaves both as the run left them => REJECT.
_REJ_CLASSIFY_DROP_XFAILMARK = """    if unexpected_success:
        rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
        rep.explanation_reason = success_reason
        rep.outcome = OUTCOME_FAILED
    elif suppress_xfail_reporting:
        pass
    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED

""" + _CORRECTION

# REJ-classify-dropall (CONTROL-FLOW-EFFECT / full removal): keep ONLY the
# location correction; drop the whole classification. Violates (Q-a) immediately
# (unexpected_success must yield outcome FAILED) and (Q-c)/(Q-d) besides
# => REJECT.
_REJ_CLASSIFY_DROPALL = _CORRECTION

# REJ-classify-drop-toggle (PRECEDENCE): drop case (b), the expected-failure
# reporting toggle, so the later cases are no longer shielded by it. With
# suppress_xfail_reporting=True and xfail_exception=True, (Q-b) demands outcome
# and annotation be left as the run left them, but this impl classifies the
# imperative expected failure anyway => REJECT.
_REJ_CLASSIFY_DROP_TOGGLE = """    if unexpected_success:
        rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
        rep.explanation_reason = success_reason
        rep.outcome = OUTCOME_FAILED
    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED
    elif (not rep_already_skipped) and xfailed_present:
        if exception_raised:
            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
            else:
                rep.outcome = OUTCOME_SKIPPED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM
        elif phase_is_call:
            if xfail_strict:
                rep.outcome = OUTCOME_FAILED
                rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
                rep.explanation_reason = declared_reason
            else:
                rep.outcome = OUTCOME_PASSED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM

""" + _CORRECTION

# REJ-classify-drop-unexpected (PRECEDENCE): drop case (a), the highest-priority
# unexpected-success case. With unexpected_success=True, (Q-a) demands outcome
# FAILED and the annotation framed; this impl instead falls through to whichever
# lower case matches (or to no case at all) => REJECT.
_REJ_CLASSIFY_DROP_UNEXPECTED = """    if suppress_xfail_reporting:
        pass
    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED
    elif (not rep_already_skipped) and xfailed_present:
        if exception_raised:
            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
            else:
                rep.outcome = OUTCOME_SKIPPED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM
        elif phase_is_call:
            if xfail_strict:
                rep.outcome = OUTCOME_FAILED
                rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
                rep.explanation_reason = declared_reason
            else:
                rep.outcome = OUTCOME_PASSED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM

""" + _CORRECTION

# REJ-classify-reorder (BOUNDARY / PRECEDENCE): every case body is kept, but the
# priority order is REVERSED. On an input where two cases both match (e.g.
# unexpected_success=True together with suppress_xfail_reporting=True) the
# reversed order picks the wrong one: (Q-a) demands outcome FAILED, this impl
# takes the toggle case and leaves the outcome alone => REJECT. This is the case
# a spec that only checked "each body exists somewhere" would miss.
_REJ_CLASSIFY_REORDER = """    if (not rep_already_skipped) and xfailed_present:
        if exception_raised:
            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
            else:
                rep.outcome = OUTCOME_SKIPPED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM
        elif phase_is_call:
            if xfail_strict:
                rep.outcome = OUTCOME_FAILED
                rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
                rep.explanation_reason = declared_reason
            else:
                rep.outcome = OUTCOME_PASSED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM
    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED
    elif suppress_xfail_reporting:
        pass
    elif unexpected_success:
        rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
        rep.explanation_reason = success_reason
        rep.outcome = OUTCOME_FAILED

""" + _CORRECTION

# REJ-classify-merge (CONTROL-FLOW-EFFECT): collapse the four classification
# cases into one disjunctive guard with an empty body — the shape that keeps the
# chain's CONDITIONS while discarding every EFFECT. (Q-a) alone rejects it
# (unexpected_success must yield outcome FAILED) => REJECT.
_REJ_CLASSIFY_MERGE = """    if (unexpected_success or suppress_xfail_reporting or xfail_exception
            or ((not rep_already_skipped) and xfailed_present)):
        pass

""" + _CORRECTION

# REJ-classify-strict-flip (BOUNDARY / value): case (d)'s no-exception call-phase
# sub-case is classified with the strictness test INVERTED — a strict expected
# failure that unexpectedly passed is reported as passed-with-annotation and a
# non-strict one as failed. (Q-d) pins strict -> FAILED (annotation framed) and
# non-strict -> PASSED with the annotation set, so both sub-cases are violated
# => REJECT. Refinement: a real patch that swapped these reports a strict
# unexpected pass as a pass, breaking the strict-xfail P2P tests.
_REJ_CLASSIFY_STRICT_FLIP = """    if unexpected_success:
        rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
        rep.explanation_reason = success_reason
        rep.outcome = OUTCOME_FAILED
    elif suppress_xfail_reporting:
        pass
    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED
    elif (not rep_already_skipped) and xfailed_present:
        if exception_raised:
            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
            else:
                rep.outcome = OUTCOME_SKIPPED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM
        elif phase_is_call:
            if xfail_strict:
                rep.outcome = OUTCOME_PASSED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM
            else:
                rep.outcome = OUTCOME_FAILED
                rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
                rep.explanation_reason = declared_reason

""" + _CORRECTION

# REJ-classify-note-only (PARTIAL-DOMAIN): every case sets the annotation
# correctly but never revises the outcome. The annotation half of (Q-a)/(Q-c)/
# (Q-d) holds while the outcome half does not (e.g. xfail_exception must yield
# outcome SKIPPED) => REJECT. Guards against a spec that pinned only the
# annotation and left the outcome free.
_REJ_CLASSIFY_NOTE_ONLY = """    if unexpected_success:
        rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
        rep.explanation_reason = success_reason
    elif suppress_xfail_reporting:
        pass
    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
    elif (not rep_already_skipped) and xfailed_present:
        if exception_raised:
            if not xfail_raises_mismatch:
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM
        elif phase_is_call:
            if xfail_strict:
                rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
                rep.explanation_reason = declared_reason
            else:
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM

""" + _CORRECTION

# REJ-classify-skipped-read (the TWO-READS case): case (d)'s guard is written
# against rep_skipped — the state condition (C) tests — instead of
# rep_already_skipped, the state the classification tests. The two reads are
# distinct parameters precisely because the real report's skipped state is read
# at two different points. On an input where they differ (rep_already_skipped
# False, rep_skipped True, xfailed_present True, an exception raised inside the
# declared set) (Q-d) demands outcome SKIPPED with the annotation set, but this
# impl skips case (d) entirely => REJECT.
_REJ_CLASSIFY_SKIPPED_READ = """    if unexpected_success:
        rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
        rep.explanation_reason = success_reason
        rep.outcome = OUTCOME_FAILED
    elif suppress_xfail_reporting:
        pass
    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED
    elif (not rep_skipped) and xfailed_present:
        if exception_raised:
            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
            else:
                rep.outcome = OUTCOME_SKIPPED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM
        elif phase_is_call:
            if xfail_strict:
                rep.outcome = OUTCOME_FAILED
                rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
                rep.explanation_reason = declared_reason
            else:
                rep.outcome = OUTCOME_PASSED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM

""" + _CORRECTION

# REJ-classify-phase-blind (PARTIAL-DOMAIN): case (d)'s no-exception sub-case
# drops the call-phase test, so a marked expected failure that raised nothing
# OUTSIDE the call phase is classified anyway. (Q-d)'s fifth sub-case pins
# outcome and annotation to what the run left them there, but this impl revises
# both => REJECT.
_REJ_CLASSIFY_PHASE_BLIND = """    if unexpected_success:
        rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
        rep.explanation_reason = success_reason
        rep.outcome = OUTCOME_FAILED
    elif suppress_xfail_reporting:
        pass
    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED
    elif (not rep_already_skipped) and xfailed_present:
        if exception_raised:
            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
            else:
                rep.outcome = OUTCOME_SKIPPED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM
        else:
            if xfail_strict:
                rep.outcome = OUTCOME_FAILED
                rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
                rep.explanation_reason = declared_reason
            else:
                rep.outcome = OUTCOME_PASSED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM

""" + _CORRECTION

# --- Group C: the content each case records ---------------------------------
# These keep the location correction AND every case's outcome/annotation
# decision verbatim, and damage only what the report tells the user. Groups A
# and B cannot see them at all; only the content clauses (R-1)..(R-3) reject
# them.

# REJ-content-strict-silent (the OUTCOME-CODE-ONLY case): the strict
# no-exception call-phase sub-case sets the outcome to FAILED and states
# nothing. Every Group A and Group B clause is satisfied — outcome FAILED is
# exactly what (Q-d) demands there — but (R-2) demands the report state that
# verdict => REJECT. Refinement: an outcome of FAILED is written by four
# different sub-cases, so a report that carries the code and says nothing tells
# the user only that the test failed, never that it failed BECAUSE it was
# required to fail and passed; the strict-xpass P2P tests read that explanation
# verbatim => does NOT resolve.
_REJ_CONTENT_STRICT_SILENT = """    if unexpected_success:
        rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
        rep.explanation_reason = success_reason
        rep.outcome = OUTCOME_FAILED
    elif suppress_xfail_reporting:
        pass
    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED
    elif (not rep_already_skipped) and xfailed_present:
        if exception_raised:
            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
            else:
                rep.outcome = OUTCOME_SKIPPED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM
        elif phase_is_call:
            if xfail_strict:
                rep.outcome = OUTCOME_FAILED
            else:
                rep.outcome = OUTCOME_PASSED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM

""" + _CORRECTION

# REJ-content-unexpected-silent (the same defect on the other stating case):
# case (a) sets the outcome to FAILED and states nothing. (Q-a)'s outcome half
# holds; (R-2) demands EXPLANATION_UNEXPECTED_SUCCESS => REJECT. Refinement: a
# unittest expectedFailure test that unexpectedly passed is then reported as a
# bare failure with no indication of why => the unexpected-success P2P tests
# fail => does NOT resolve.
_REJ_CONTENT_UNEXPECTED_SILENT = """    if unexpected_success:
        rep.outcome = OUTCOME_FAILED
    elif suppress_xfail_reporting:
        pass
    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED
    elif (not rep_already_skipped) and xfailed_present:
        if exception_raised:
            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
            else:
                rep.outcome = OUTCOME_SKIPPED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM
        elif phase_is_call:
            if xfail_strict:
                rep.outcome = OUTCOME_FAILED
                rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
                rep.explanation_reason = declared_reason
            else:
                rep.outcome = OUTCOME_PASSED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM

""" + _CORRECTION

# REJ-content-verdict-swap (BOUNDARY / which verdict): both stating cases state
# a verdict, but they state EACH OTHER'S. (R-2) pins WHICH verdict each case
# states, so both are violated => REJECT. Refinement: the two explanations are
# what distinguishes an unexpectedly-passing unittest expectedFailure from a
# strict expected-failure mark that passed; swapping them makes each report
# describe the other situation => both P2P families fail => does NOT resolve.
_REJ_CONTENT_VERDICT_SWAP = """    if unexpected_success:
        rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
        rep.explanation_reason = success_reason
        rep.outcome = OUTCOME_FAILED
    elif suppress_xfail_reporting:
        pass
    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED
    elif (not rep_already_skipped) and xfailed_present:
        if exception_raised:
            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
            else:
                rep.outcome = OUTCOME_SKIPPED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM
        elif phase_is_call:
            if xfail_strict:
                rep.outcome = OUTCOME_FAILED
                rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
                rep.explanation_reason = declared_reason
            else:
                rep.outcome = OUTCOME_PASSED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM

""" + _CORRECTION

# REJ-content-strict-reason (value / whose reason): the strict sub-case states
# the right verdict but carries the reason that was RAISED imperatively instead
# of the reason the mark DECLARED. On an input where the two tokens differ,
# (R-3) demands explanation_reason == declared_reason => REJECT. Refinement:
# the strict report would quote an unrelated reason (or nothing, since no
# exception was raised in this sub-case at all), so the reported explanation
# does not match the mark's reason => the strict-xfail P2P tests fail => does
# NOT resolve.
_REJ_CONTENT_STRICT_REASON = """    if unexpected_success:
        rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
        rep.explanation_reason = success_reason
        rep.outcome = OUTCOME_FAILED
    elif suppress_xfail_reporting:
        pass
    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED
    elif (not rep_already_skipped) and xfailed_present:
        if exception_raised:
            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
            else:
                rep.outcome = OUTCOME_SKIPPED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM
        elif phase_is_call:
            if xfail_strict:
                rep.outcome = OUTCOME_FAILED
                rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
                rep.explanation_reason = raised_reason
            else:
                rep.outcome = OUTCOME_PASSED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM

""" + _CORRECTION

# REJ-content-note-reason-swap (value / whose reason, the two reason sources):
# the annotation is added in exactly the right cases, but the imperative case
# carries the mark's declared reason and the mark's cases carry the imperatively
# raised one. (R-1) pins each case's annotation to the reason that case was
# GIVEN => REJECT. Refinement: an imperatively raised expected failure would be
# annotated with an unrelated mark's reason (or with nothing), and a marked one
# with a reason no exception supplied; the P2P suite asserts each annotation's
# reason text => does NOT resolve.
_REJ_CONTENT_NOTE_REASON_SWAP = """    if unexpected_success:
        rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
        rep.explanation_reason = success_reason
        rep.outcome = OUTCOME_FAILED
    elif suppress_xfail_reporting:
        pass
    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = declared_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED
    elif (not rep_already_skipped) and xfailed_present:
        if exception_raised:
            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
            else:
                rep.outcome = OUTCOME_SKIPPED
                rep.xfail_note_present = True
                rep.note_reason = raised_reason
                rep.note_style = NOTE_STYLE_VERBATIM
        elif phase_is_call:
            if xfail_strict:
                rep.outcome = OUTCOME_FAILED
                rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
                rep.explanation_reason = declared_reason
            else:
                rep.outcome = OUTCOME_PASSED
                rep.xfail_note_present = True
                rep.note_reason = raised_reason
                rep.note_style = NOTE_STYLE_VERBATIM

""" + _CORRECTION

# REJ-content-note-reason-drop (PARTIAL-DOMAIN): the annotation is added in
# every right case but its reason is never recorded — the annotation is a bare
# flag. (R-1) pins the annotation's reason in (Q-c) and in (Q-d)'s two
# annotating sub-cases => REJECT. Refinement: every expected-failure report
# would render an empty reason where the declared or raised one belongs, which
# is what the xfail-reporting P2P tests assert => does NOT resolve.
_REJ_CONTENT_NOTE_REASON_DROP = """    if unexpected_success:
        rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
        rep.explanation_reason = success_reason
        rep.outcome = OUTCOME_FAILED
    elif suppress_xfail_reporting:
        pass
    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED
    elif (not rep_already_skipped) and xfailed_present:
        if exception_raised:
            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
            else:
                rep.outcome = OUTCOME_SKIPPED
                rep.xfail_note_present = True
                rep.note_style = NOTE_STYLE_VERBATIM
        elif phase_is_call:
            if xfail_strict:
                rep.outcome = OUTCOME_FAILED
                rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
                rep.explanation_reason = declared_reason
            else:
                rep.outcome = OUTCOME_PASSED
                rep.xfail_note_present = True
                rep.note_style = NOTE_STYLE_VERBATIM

""" + _CORRECTION

# REJ-content-note-style-swap (value / whose rendering): every annotation lands
# in the right case carrying the right reason, but each annotating case renders
# it in the OTHER annotating case's style — the imperative case reads its reason
# verbatim, the mark's cases read theirs behind the lead-in. (R-1) pins each
# annotating case's note_style, not merely its reason => REJECT. Refinement:
# what the user reads for an imperatively raised expected failure loses the
# lead-in the imperative case is entitled to, and every mark-annotated report
# gains one it is not, so both renderings are wrong text for the right reason;
# the xfail-reporting P2P tests read that rendered line => does NOT resolve.
_REJ_CONTENT_NOTE_STYLE_SWAP = """    if unexpected_success:
        rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
        rep.explanation_reason = success_reason
        rep.outcome = OUTCOME_FAILED
    elif suppress_xfail_reporting:
        pass
    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_VERBATIM
        rep.outcome = OUTCOME_SKIPPED
    elif (not rep_already_skipped) and xfailed_present:
        if exception_raised:
            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
            else:
                rep.outcome = OUTCOME_SKIPPED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_LEAD_IN
        elif phase_is_call:
            if xfail_strict:
                rep.outcome = OUTCOME_FAILED
                rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
                rep.explanation_reason = declared_reason
            else:
                rep.outcome = OUTCOME_PASSED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_LEAD_IN

""" + _CORRECTION

# REJ-content-note-style-merged (CONTROL-FLOW-EFFECT / one shared rendering for
# cases entitled to different ones): each annotating case still records the
# reason it was given, but the STYLE that reason is read in is decided once, at
# a single site common to all of them, so every annotation reads in one style.
# The reason each case carries is untouched, and so is which case annotates:
# only the rendering collapses. (R-1) pins note_style per annotating case, and
# the imperative case's style differs from the mark cases' => REJECT.
# Refinement: one shared rendering site means one rendering, so whichever style
# it settles on is wrong for the other cases' reports; the xfail-reporting P2P
# tests read the rendered line for both families => does NOT resolve.
_REJ_CONTENT_NOTE_STYLE_MERGED = """    if unexpected_success:
        rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
        rep.explanation_reason = success_reason
        rep.outcome = OUTCOME_FAILED
    elif suppress_xfail_reporting:
        pass
    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.outcome = OUTCOME_SKIPPED
    elif (not rep_already_skipped) and xfailed_present:
        if exception_raised:
            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
            else:
                rep.outcome = OUTCOME_SKIPPED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
        elif phase_is_call:
            if xfail_strict:
                rep.outcome = OUTCOME_FAILED
                rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
                rep.explanation_reason = declared_reason
            else:
                rep.outcome = OUTCOME_PASSED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
    if rep.xfail_note_present:
        rep.note_style = NOTE_STYLE_VERBATIM

""" + _CORRECTION

# REJ-frame-note-style (FRAME, on the new observable): the classification is
# gold in every slot, except that the raises-MISMATCH sub-case — which adds no
# annotation at all — also stamps a rendering style onto the annotation slot it
# did not write. (R-1) frames note_style in every case that adds no annotation,
# exactly as it frames the annotation's presence and its reason => REJECT.
# Refinement: a report that arrived already carrying an annotation would have
# the rendering of that annotation rewritten by a case that has nothing to say
# about it, so the user reads that earlier reason in a style it was never
# recorded in => does NOT resolve.
_REJ_FRAME_NOTE_STYLE = _CHAIN.replace(
    """            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED""",
    """            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
                rep.note_style = NOTE_STYLE_VERBATIM""", 1) + "\n\n" + _CORRECTION
if "rep.note_style = NOTE_STYLE_VERBATIM\n            else:" not in \
        _REJ_FRAME_NOTE_STYLE:
    raise AssertionError("drift: raises-mismatch sub-case not found in _CHAIN")

# REJ-content-overstate (CONTROL-FLOW-EFFECT / a non-stating case states):
# case (d)'s raises-MISMATCH sub-case gets the outcome right (FAILED) but also
# states the strict-unexpected-pass verdict, which belongs to a different
# sub-case entirely. (R-2) frames the stated verdict in every case but the two
# that state one => REJECT. Refinement: a marked expected failure that raised
# the wrong exception type would be reported as though it had passed
# unexpectedly, replacing the actual failure explanation => the xfail-raises
# P2P tests fail => does NOT resolve.
_REJ_CONTENT_OVERSTATE = """    if unexpected_success:
        rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
        rep.explanation_reason = success_reason
        rep.outcome = OUTCOME_FAILED
    elif suppress_xfail_reporting:
        pass
    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED
    elif (not rep_already_skipped) and xfailed_present:
        if exception_raised:
            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
                rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
                rep.explanation_reason = declared_reason
            else:
                rep.outcome = OUTCOME_SKIPPED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM
        elif phase_is_call:
            if xfail_strict:
                rep.outcome = OUTCOME_FAILED
                rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
                rep.explanation_reason = declared_reason
            else:
                rep.outcome = OUTCOME_PASSED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM

""" + _CORRECTION

# REJ-content-toggle-states (PRECEDENCE x CONTENT): the toggle case keeps the
# outcome and the annotation as the run left them — satisfying (Q-b)'s outcome
# and annotation halves — but states a verdict anyway. (Q-b) frames the stated
# verdict too: a toggle that declines to interfere decides NOTHING, including
# what the report says => REJECT. Refinement: with expected-failure reporting
# toggled off, reports would acquire an explanation the run never produced,
# which is exactly the interference that configuration exists to prevent => the
# --runxfail P2P tests fail => does NOT resolve.
_REJ_CONTENT_TOGGLE_STATES = """    if unexpected_success:
        rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS
        rep.explanation_reason = success_reason
        rep.outcome = OUTCOME_FAILED
    elif suppress_xfail_reporting:
        rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
    elif xfail_exception:
        rep.xfail_note_present = True
        rep.note_reason = raised_reason
        rep.note_style = NOTE_STYLE_LEAD_IN
        rep.outcome = OUTCOME_SKIPPED
    elif (not rep_already_skipped) and xfailed_present:
        if exception_raised:
            if xfail_raises_mismatch:
                rep.outcome = OUTCOME_FAILED
            else:
                rep.outcome = OUTCOME_SKIPPED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM
        elif phase_is_call:
            if xfail_strict:
                rep.outcome = OUTCOME_FAILED
                rep.explanation = EXPLANATION_STRICT_UNEXPECTED_PASS
                rep.explanation_reason = declared_reason
            else:
                rep.outcome = OUTCOME_PASSED
                rep.xfail_note_present = True
                rep.note_reason = declared_reason
                rep.note_style = NOTE_STYLE_VERBATIM

""" + _CORRECTION


# REJ-content-success-reason-drop (PARTIAL-DOMAIN, on the other stating case):
# case (a) states the right verdict but records no reason with it, leaving
# Old(explanation_reason). (R-2)'s verdict identity holds; (R-4) demands the
# stated verdict carry the reason recorded alongside the unexpected success =>
# REJECT. Refinement: the report would say only that a success was unexpected
# and never which expectation was defied, so the reason the run recorded is
# dropped from the only place it is shown => does NOT resolve.
_SUCCESS_WRITE = "        rep.explanation_reason = success_reason\n"
if _CHAIN.count(_SUCCESS_WRITE) != 1:
    raise AssertionError("drift: case (a) reason write not unique in _CHAIN")
_REJ_CONTENT_SUCCESS_REASON_DROP = (
    _CHAIN.replace(_SUCCESS_WRITE, "", 1) + "\n\n" + _CORRECTION)

# REJ-content-success-reason-swap (value / whose reason): case (a) states the
# right verdict but carries the reason the MARK declared instead of the one
# recorded alongside the unexpected success. On an input where the two tokens
# differ, (R-4) is violated => REJECT. Refinement: the report would quote an
# unrelated expectation's reason (and in the real unexpected-success situation
# there is no evaluated mark to take one from at all) => does NOT resolve.
_REJ_CONTENT_SUCCESS_REASON_SWAP = (
    _CHAIN.replace(_SUCCESS_WRITE,
                   "        rep.explanation_reason = declared_reason\n", 1)
    + "\n\n" + _CORRECTION)


SPEC_TESTS = [
    # ---- positive controls (must verify) ----
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_impl(_POS_REORDER),
        "rationale": "correcting first makes the correction's write DEAD "
                     "wherever the two steps meet: the cases that touch the "
                     "location are exactly the two that state a verdict, and "
                     "they overwrite all four location facts afterwards. The two "
                     "orders were enumerated and agree on all 16384 abstract "
                     "inputs, so this is observably identical and must verify "
                     "(else SPEC-TOO-STRONG: the spec would be forbidding a dead "
                     "store). Its sharp counterpart, where the reordered write "
                     "survives, is rej-stale-shape. No induction lemma needed "
                     "(boolean/arith helpers only).",
    },
    {
        "id": "pos-flatguards",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_impl(_POS_FLATGUARDS),
        "rationale": "the classification rewritten as a flat guarded cascade "
                     "with every higher-priority case negated explicitly: same "
                     "priority order, same effects, same recorded content, "
                     "different control-flow shape. This is the honest "
                     "counterpart of the chain-merge attack — it preserves each "
                     "case's EFFECT — so it must verify or the spec has "
                     "over-fitted to the if/elif form.",
    },
    {
        "id": "pos-localshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_impl(_POS_LOCALSHAPE),
        "rationale": "read loc_is_triple into a local before the correction "
                     "guard and write the corrected location's two elements in "
                     "the opposite order. The local is read after the "
                     "classification, which is where the repo reads the shape "
                     "too (skipping.py:297); the correction still "
                     "fires on exactly C and lands the same location. "
                     "Local-variable reshape must verify.",
    },
    {
        "id": "pos-reason-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_impl(_POS_REASON_LOCALS),
        "rationale": "each case's recorded reason is routed through a local and "
                     "the strict sub-case states its verdict before setting the "
                     "outcome. The content clauses pin WHICH reason reaches "
                     "WHICH slot and which verdict each case states, never the "
                     "data flow or the statement order, so this correct variant "
                     "must verify (else the content clauses have over-fitted to "
                     "the gold statement sequence).",
    },
    {
        "id": "pos-absent-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_impl(_POS_ABSENT_BRANCH),
        "rationale": "the impl checks the definition line for ABSENCE inside the "
                     "correction's guard instead of leaning on (A0) to rule it "
                     "out. The absent branch is dead under (A0), so this agrees "
                     "with gold on every admissible input while reading the line "
                     "only where one exists. The honest cheapest handling of a "
                     "partial observable must verify, else the spec forbids "
                     "checking for absence at all.",
    },
    {
        "id": "pos-preguard-hoist",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_impl(_POS_PREGUARD_HOIST),
        "rationale": "the corrected location is computed before the "
                     "classification but UNDER the correction's own three "
                     "conditions, which is exactly where (A0) supplies a "
                     "definition line; the write still happens under the "
                     "post-classification guard, so a verdict-stating case still "
                     "leaves no location behind. Reading the definition line "
                     "early must stay admitted as long as it is read only where "
                     "there is one — this is the admitted side of the line (A0) "
                     "draws, rej-hoist-unconditional the rejected side. If this "
                     "were rejected the precondition would be TOO STRONG.",
    },
    {
        "id": "pos-budget-echo",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_impl(_POS_BUDGET_ECHO),
        "rationale": "the corrected line is computed by echoing the completion "
                     "helper (budget - 1) hoisted to the top. definition_line_"
                     "budget is TOTAL — it answers for the absent case too — so "
                     "an impl reading the line through it has already handled "
                     "absence and may read it anywhere; echoing the one @Pure "
                     "helper in the spec must therefore be admitted rather than "
                     "rejected. Must verify.",
    },
    # ---- admissibility (must verify) ----
    {
        "id": "admiss-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap_impl(_ADMISS),
        "rationale": "a self-call on an F2P-shaped input (skip-mark skip, "
                     "positional triple, expected-failure reporting toggled "
                     "off, definition_line - 1 >= 0 under the guard) must "
                     "establish Requires and yield the corrected location "
                     "(file 17, line definition_line, the skip reason kept) "
                     "with the outcome, annotation and stated verdict left "
                     "alone, on a strictly smaller completion budget. If the "
                     "call site cannot establish Requires for this normal "
                     "input => PRECOND-TOO-STRONG.",
    },
    {
        "id": "admiss-vacuity-control",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_ADMISS_VACUITY),
        "refinement": "not a behavioural variant: this is the control proving "
                      "admiss-f2p is not vacuous. If the guarded branch were "
                      "unreachable, an Assert(False) inside it would verify and "
                      "the admissibility case would witness nothing.",
        "rationale": "the same body as admiss-f2p plus Assert(False) in the "
                     "guarded branch. MUST be rejected; if it verified, the "
                     "admissibility witness would be dead code.",
    },
    {
        "id": "admiss-absent",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap_impl(_ADMISS_ABSENT),
        "rationale": "a self-call passing NO definition line at all (None) on a "
                     "report the correction does not apply to must establish "
                     "Requires and come back with the recorded location framed "
                     "and the classification untouched. This is what makes the "
                     "conditioned availability precondition (A0) a genuine "
                     "WIDENING of the domain rather than a paper one: if None "
                     "were not admissible here, nothing would have been weakened. "
                     "If the call site cannot establish Requires for a report "
                     "with no definition line => PRECOND-TOO-STRONG.",
    },
    {
        "id": "admiss-absent-vacuity-control",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_ADMISS_ABSENT_VACUITY),
        "refinement": "not a behavioural variant: the control proving "
                      "admiss-absent is not vacuous.",
        "rationale": "the same body as admiss-absent plus Assert(False) in the "
                     "guarded branch. MUST be rejected; if it verified, the "
                     "absent-case witness would be dead code and the widened "
                     "domain would be witnessed by nothing.",
    },
    {
        "id": "rej-hoist-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_HOIST_UNCONDITIONAL),
        "refinement": "the real hook obtains the definition location by asking "
                      "the reporting machinery for it, and that question has no "
                      "answer for a run it cannot locate in source. This impl "
                      "consumes a definition line before it knows the correction "
                      "applies, so its faithful patch must ask for every report; "
                      "every report of an un-locatable run is then left "
                      "unfinalised, and the reporting tests that build their own "
                      "un-locatable run items fail while the target scenario "
                      "still passes.",
        "rationale": "reads the definition line outside every guard, where (A0) "
                      "supplies none => must be REJECTED. Under an "
                      "unconditional `definition_line >= 0` precondition this "
                      "impl verifies, which is exactly the weakness (A0) closes.",
    },
    {
        "id": "rej-hoist-assert",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_HOIST_ASSERT),
        "refinement": "the same patch as rej-hoist-unconditional; asserting the "
                      "definition line into existence is what that patch's "
                      "unfinalised reports die on.",
        "rationale": "the same defect stated as an assumption at the top of the "
                     "body: the assertion is precisely the claim (A0) declines "
                     "to make of every report => must be REJECTED.",
    },
    {
        "id": "rej-hoist-partial-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_HOIST_PARTIAL_GUARD),
        "refinement": "asking the reporting machinery for a definition line "
                      "whenever a skip-style mark is involved — regardless of "
                      "whether the report is skipped and still carries a "
                      "correctable triple — still asks it about runs it cannot "
                      "locate, so those reports are left unfinalised.",
        "rationale": "reads the definition line under only ONE of the "
                     "correction's three conditions => must be REJECTED. The "
                     "sharp case: the guard the read needs is the correction's "
                     "own guard, not something in its neighbourhood.",
    },
    {
        "id": "rej-underfire-budget",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_UNDERFIRE_BUDGET),
        "refinement": "a patch that corrects the location only for tests defined "
                      "past the second line of their file leaves the reported "
                      "location pointing into pytest's internals for the rest, "
                      "which is the very defect being fixed.",
        "rationale": "correct only where the completion budget is at least 4, "
                     "i.e. where the definition line is at least 2, so it "
                     "under-fires on the boundary lines that (A0) still admits "
                     "under the correction; (P2) demands the corrected line "
                     "there => must be REJECTED.",
    },
    {
        "id": "rej-abandon-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_ABANDON_ABSENT),
        "refinement": "a patch that never returns from finalising any report the "
                      "correction does not apply to hangs the entire run, so no "
                      "test reports at all.",
        "rationale": "comes back ONLY where the correction applies. Every "
                     "postcondition holds vacuously on the reports it abandons, "
                     "so only Group D's total completion budget can reject this "
                     "=> must be REJECTED. This is the preservation obligation "
                     "the widened domain carries: a report with no definition "
                     "line is still owed a finalisation.",
    },
    {
        "id": "rej-diverge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl("    while True:\n        pass"),
        "refinement": "the finalisation never returns, so the report is never "
                      "finalised and the run never comes back — every hidden "
                      "test hangs => does NOT resolve. Under partial "
                      "correctness alone this impl satisfies every clause "
                      "vacuously, which is exactly what the completion "
                      "obligation exists to stop.",
        "rationale": "no postcondition can reject a body that never reaches "
                     "its return; Requires(MustTerminate(definition_line + 2)) "
                     "can, and does — the loop has no decreasing measure. "
                     "Rejection from the completion obligation.",
    },
    # ---- uniqueness / reject: Group A, the location correction ----
    {
        "id": "rej-prepatch-elif",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_PREPATCH),
        "refinement": "this IS the pre-patch control flow (the correction "
                      "chained as one more alternative of the classification). "
                      "On the F2P scenario "
                      "test_xfail_run_with_skip_mark[test_input1-expected1] "
                      "(args ['-rs','--runxfail']) the toggle case is taken and "
                      "the chained correction is skipped, so the real hook "
                      "reports the internal skipping.py line, not the "
                      "test-definition line => the F2P assertion fails => does "
                      "NOT resolve.",
        "rationale": "C holds under the toggle (skipped_by_mark & rep_skipped & "
                     "loc_is_triple all True) so (P2) demands "
                     "loc_line==definition_line+1, but the chain linkage leaves "
                     "it at Old(loc_line). Rejection comes from postcondition (P2).",
    },
    {
        "id": "rej-runxfail-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_RUNXFAIL_GUARD),
        "refinement": "gating the correction on `not suppress_xfail_reporting` "
                      "reproduces the defect semantically: with the toggle set "
                      "the correction never fires, so the real hook reports the "
                      "internal line on the F2P scenario => the test_input1 "
                      "assertion fails => does NOT resolve.",
        "rationale": "on the F2P (suppress_xfail_reporting=True) C still holds so "
                     "(P2) demands the corrected line, but the guard suppresses "
                     "the write. Rejection comes from postcondition (P2).",
    },
    {
        "id": "rej-offbyone",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_OFFBYONE),
        "refinement": "storing definition_line (not +1) reports "
                      "`test_sample.py:1` instead of the actual definition line "
                      "`:2`; the F2P test asserts the item-definition location "
                      "=> the reported line is off by one => does NOT resolve.",
        "rationale": "(P2) pins loc_line == definition_line + 1 exactly; storing "
                     "definition_line violates it. Rejection from (P2).",
    },
    {
        "id": "rej-frame-mutation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_FRAME),
        "refinement": "flipping rep.loc_is_triple changes the recorded location "
                      "SHAPE (tuple -> non-tuple). The real hook never rewrites "
                      "the longrepr shape; downstream reporting that depends on "
                      "the triple shape would misformat the skip line => does "
                      "NOT resolve (and corrupts the P2P reporting tests).",
        "rationale": "value-frame analogue of frame-mutation: rep has full "
                     "permission to loc_is_triple (no Acc(.,1/2) read-only field "
                     "exists), so this is NOT a permission error; it violates the "
                     "explicit shape-frame postcondition (P1) "
                     "Implies(not states_own_verdict(...), rep.loc_is_triple == "
                     "Old(rep.loc_is_triple)) — no verdict is stated on the "
                     "inputs that reach this write, so the antecedent holds. "
                     "Rejection from (P1).",
    },
    # ---- uniqueness / reject: Group A', the coupling between the two steps ----
    {
        "id": "rej-verdict-keeps-loc",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_VERDICT_KEEPS_LOC),
        "refinement": "case (a) writes the 'Unexpected success' verdict into "
                      "rep.longrepr (skipping.py:269/271) — the SAME attribute the "
                      "positional triple lives in — so the location cannot survive "
                      "it. An impl that keeps the triple there is describing a "
                      "report the real hook cannot produce: the correction at :297 "
                      "would then re-enter on a report whose account is a string, "
                      "and the faithful patch would have to keep TWO longrepr "
                      "slots, which is not the object pytest has => does NOT "
                      "resolve. Witnessed in-container: a passing "
                      "@unittest.expectedFailure test that also takes a late skip "
                      "arrives skipped/tuple and leaves failed/'Unexpected "
                      "success' (see axiom_check.py leg (2b)).",
        "rationale": "with unexpected_success=True and Old(loc_is_triple)=True, V "
                     "holds, so (P0) demands not loc_is_triple and all three "
                     "positional elements == LOC_ABSENT; this impl leaves them at "
                     "their Old values. Rejection from (P0).",
    },
    {
        "id": "rej-strict-keeps-loc",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_STRICT_KEEPS_LOC),
        "refinement": "the same two-slot fiction in the strict sub-case, whose "
                      "verdict write is skipping.py:290. Same argument: one "
                      "attribute, two roles, so the '[XPASS(strict)] ...' string "
                      "replaces any triple standing there => does NOT resolve.",
        "rationale": "on the strict-xpass input V holds via the second arm of "
                     "states_own_verdict, so (P0) bites exactly as above. Kept "
                     "separate from rej-verdict-keeps-loc so each arm of the "
                     "predicate is attacked on its own. Rejection from (P0).",
    },
    {
        "id": "rej-nonverdict-destroys-loc",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_NONVERDICT_DESTROYS_LOC),
        "refinement": "the imperative expected-failure arm (skipping.py:275-278) "
                      "writes only rep.wasxfail and rep.outcome; it never touches "
                      "rep.longrepr. An impl that empties the location there loses "
                      "the report's own account of itself, so an imperatively "
                      "xfailed test would report no location at all => breaks the "
                      "skip/xfail reporting P2P tests => does NOT resolve.",
        "rationale": "the converse over-approximation of (P0): with "
                     "xfail_exception=True and no verdict stated, V is false, so "
                     "(P1) demands the shape be framed and (P3) demands the "
                     "elements be framed. Rejection from (P1).",
    },
    {
        "id": "rej-stale-shape",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_STALE_SHAPE),
        "refinement": "the repo decides the correction on the account AS IT "
                      "STANDS: `type(rep.longrepr) is tuple` at skipping.py:297 "
                      "executes after the classification chain. Deciding it on a "
                      "snapshot taken beforehand writes str(filename) and line + 1 "
                      "into a longrepr that now holds a verdict string — in the "
                      "real object that means REPLACING the verdict with a tuple, "
                      "so an unexpected success would be reported as a skip "
                      "location instead of 'Unexpected success' => breaks the "
                      "unittest P2P tests => does NOT resolve.",
        "rationale": "reads the shape from the wrong state. With "
                     "unexpected_success=True and Old(loc_is_triple)=True the "
                     "snapshot is True, so the correction fires after the "
                     "annihilation and leaves loc_file == definition_file, "
                     "loc_line == definition_line + 1 where (P0) demands "
                     "LOC_ABSENT. Rejection from (P0). Contrast pos-reorder, where "
                     "the same reordering is harmless because the write is dead.",
    },
    {
        "id": "rej-partial-annihilation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_PARTIAL_ANNIHILATION),
        "refinement": "dropping the shape flag but leaving the file, line and "
                      "reason readable models a longrepr that is 'not a tuple' and "
                      "yet still carries the tuple's three elements. No Python "
                      "object is in that state — the attribute holds one value — so "
                      "the faithful patch does not exist; the closest real "
                      "behaviour keeps the triple, which rej-verdict-keeps-loc "
                      "already refutes => does NOT resolve.",
        "rationale": "(P0) pins all FOUR facts, not just the shape, precisely so "
                     "'there is no location' cannot be recorded as 'there is a "
                     "location nobody is supposed to look at'. Rejection from "
                     "(P0) on the three element conjuncts.",
    },
    {
        "id": "rej-overfire",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_OVERFIRE),
        "refinement": "dropping the skipped_by_mark conjunct fires the correction "
                      "for skips that are NOT skip-mark skips (e.g. imperative "
                      "pytest.skip() with a tuple longrepr). The real hook leaves "
                      "those untouched; rewriting their location moves it to the "
                      "wrong line => breaks the skip-reporting P2P tests => does "
                      "NOT resolve.",
        "rationale": "with skipped_by_mark=False, rep_skipped=True, "
                     "loc_is_triple=True, C is False so (P3) demands "
                     "loc_line==Old(loc_line), yet the impl rewrites it. "
                     "Rejection from (P3).",
    },
    {
        "id": "rej-touch-else",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_TOUCH_ELSE),
        "refinement": "rewriting the location UNCONDITIONALLY corrects skip-mark "
                      "reports but also clobbers the location of every "
                      "non-skip-mark report (passed/failed/xfailed). The real "
                      "hook touches only the C-case; an unconditional rewrite "
                      "scrambles unrelated reports => breaks the P2P suite => "
                      "does NOT resolve.",
        "rationale": "on not-C inputs (P3) demands loc_line==Old(loc_line), but "
                     "the unconditional write changes it. Rejection from (P3).",
    },
    {
        "id": "rej-noop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_NOOP),
        "refinement": "doing nothing never corrects the skip location, so the "
                      "F2P scenario still reports the internal skipping.py line "
                      "=> does NOT resolve. (Cheap supporting case; the reasoned "
                      "attacks above and below are the primary battery.)",
        "rationale": "when C holds (P2) demands loc_line==definition_line+1 but "
                     "loc_line stays Old(loc_line). Rejection from (P2).",
    },
    {
        "id": "rej-loc-file-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_LOC_FILE_DROP),
        "refinement": "correcting the line but not the file leaves the report "
                      "pointing at the internal frame's FILE with the test's "
                      "own line number — a location that names no real source "
                      "position at all. The F2P assertion reads the whole "
                      "`<file>:<line>: <reason>` skip line => does NOT resolve.",
        "rationale": "(P2) pins the corrected location's three elements "
                     "together: loc_file == definition_file as well as "
                     "loc_line == definition_line + 1. Leaving loc_file at "
                     "Old(loc_file) violates (P2).",
    },
    {
        "id": "rej-loc-reason-clobber",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_LOC_REASON_CLOBBER),
        "refinement": "overwriting the skip reason the location carried replaces "
                      "the message the user asked to see with an unrelated "
                      "token; the F2P assertion reads the reason as well as the "
                      "file and line => does NOT resolve.",
        "rationale": "(P2) pins loc_reason == Old(loc_reason) — the correction "
                     "moves where the report points and changes nothing about "
                     "what it says. Rejection from (P2).",
    },
    # ---- uniqueness / reject: Group B, the outcome classification ----
    # Each of these keeps the location correction VERBATIM, so Group A cannot
    # see it; only the classification clauses (Q-a)..(Q-e) reject it.
    {
        "id": "rej-classify-drop-xfailmark",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CLASSIFY_DROP_XFAILMARK),
        "refinement": "the correction is kept verbatim and the whole "
                      "expected-failure-MARK classification case is deleted. "
                      "The F2P scenario (a skip-mark skip) still passes, but "
                      "every report that a `@pytest.mark.xfail` should have "
                      "reclassified is left with the run's raw outcome and no "
                      "annotation: xfailed tests report as failed and xpassed "
                      "tests as passed-without-annotation. That is the exact "
                      "wrong impl a location-only spec admitted — 23 "
                      "PASS_TO_PASS xfail tests (test_xfail_simple, "
                      "test_xfail_xpassed, test_xfail_imperative, ...) fail "
                      "=> does NOT resolve.",
        "rationale": "on (not unexpected_success, not toggle, not "
                     "xfail_exception, not rep_already_skipped, xfailed_present, "
                     "exception_raised, not xfail_raises_mismatch) clause (Q-d) "
                     "demands outcome==OUTCOME_SKIPPED with the annotation set, "
                     "but this impl leaves both as the run left them. Rejection "
                     "comes from the classification clause (Q-d), which Group A "
                     "cannot express.",
    },
    {
        "id": "rej-classify-dropall",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CLASSIFY_DROPALL),
        "refinement": "keep ONLY the location correction and delete the entire "
                      "outcome classification. The F2P still passes; every "
                      "expected-failure and unittest unexpected-success report "
                      "is left unclassified, so 29 PASS_TO_PASS tests fail "
                      "=> does NOT resolve.",
        "rationale": "with unexpected_success=True, (Q-a) demands "
                     "outcome==OUTCOME_FAILED but the impl leaves "
                     "Old(rep.outcome); (Q-c) and (Q-d) are violated likewise. "
                     "Rejection from (Q-a).",
    },
    {
        "id": "rej-classify-drop-toggle",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CLASSIFY_DROP_TOGGLE),
        "refinement": "deleting the expected-failure-reporting toggle case "
                      "removes the shield it provides: with the toggle set, the "
                      "later cases now classify anyway, so expected-failure "
                      "outcomes are rewritten in exactly the configuration that "
                      "asked for them to be reported as-is => the --runxfail "
                      "P2P tests fail => does NOT resolve.",
        "rationale": "with suppress_xfail_reporting=True and "
                     "xfail_exception=True, (Q-b) demands outcome and annotation "
                     "both equal Old(...), but this impl sets "
                     "outcome==OUTCOME_SKIPPED and the annotation. Rejection "
                     "from (Q-b).",
    },
    {
        "id": "rej-classify-drop-unexpected",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CLASSIFY_DROP_UNEXPECTED),
        "refinement": "deleting the highest-priority unexpected-success case "
                      "leaves a unittest expectedFailure test that unexpectedly "
                      "passed reported as a pass instead of a failure => the "
                      "unittest unexpected-success P2P tests fail => does NOT "
                      "resolve.",
        "rationale": "with unexpected_success=True, (Q-a) demands "
                     "outcome==OUTCOME_FAILED; this impl falls through to a "
                     "lower case (or to none) and leaves the outcome unrevised. "
                     "Rejection from (Q-a).",
    },
    {
        "id": "rej-classify-reorder",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CLASSIFY_REORDER),
        "refinement": "every case BODY is present but the priority order is "
                      "reversed, so on any report matching two cases the wrong "
                      "one wins — e.g. a unittest unexpected success under the "
                      "reporting toggle is left unclassified instead of failed, "
                      "and a marked expected failure pre-empts the imperative "
                      "case => the xfail and unexpected-success P2P tests fail "
                      "=> does NOT resolve.",
        "rationale": "with unexpected_success=True and "
                     "suppress_xfail_reporting=True, (Q-a) demands "
                     "outcome==OUTCOME_FAILED but the reversed chain takes the "
                     "toggle case and leaves the outcome alone. Rejection from "
                     "(Q-a) — a clause that pins the case bodies without their "
                     "PRIORITY would miss this.",
    },
    {
        "id": "rej-classify-merge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CLASSIFY_MERGE),
        "refinement": "collapsing the four cases into one disjunctive guard "
                      "keeps their CONDITIONS and discards every EFFECT: no "
                      "report is ever reclassified, so the whole xfail and "
                      "unexpected-success suite fails => does NOT resolve. "
                      "Contrast pos-flatguards, which reshapes the chain while "
                      "keeping the effects and must verify.",
        "rationale": "with unexpected_success=True, (Q-a) demands "
                     "outcome==OUTCOME_FAILED but the merged guard's body is "
                     "empty. Rejection from (Q-a).",
    },
    {
        "id": "rej-classify-strict-flip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CLASSIFY_STRICT_FLIP),
        "refinement": "inverting the strictness test in the no-exception "
                      "call-phase sub-case reports a STRICT expected failure "
                      "that unexpectedly passed as a pass, and a non-strict one "
                      "as a failure — the exact inversion of what strict xfail "
                      "means => the strict-xfail P2P tests fail => does NOT "
                      "resolve.",
        "rationale": "on (…, not exception_raised, phase_is_call, xfail_strict) "
                     "(Q-d) pins outcome==OUTCOME_FAILED with the annotation "
                     "framed, but the impl sets OUTCOME_PASSED and the "
                     "annotation; the non-strict sub-case is violated "
                     "symmetrically. Rejection from (Q-d).",
    },
    {
        "id": "rej-classify-note-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CLASSIFY_NOTE_ONLY),
        "refinement": "setting the expected-failure annotation without ever "
                      "revising the outcome leaves xfailed tests reported as "
                      "failures that merely carry an annotation, so the "
                      "xfail P2P tests fail on the outcome even though the "
                      "annotation is right => does NOT resolve.",
        "rationale": "with xfail_exception=True, (Q-c) demands BOTH "
                     "outcome==OUTCOME_SKIPPED and the annotation; this impl "
                     "satisfies only the annotation half. Rejection from (Q-c) "
                     "— a clause pinning the annotation alone would miss it.",
    },
    {
        "id": "rej-classify-skipped-read",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CLASSIFY_SKIPPED_READ),
        "refinement": "the classification's guard is written against the "
                      "skipped state that the LOCATION condition tests rather "
                      "than the one the classification tests. The real report's "
                      "skipped state is read at two distinct points and the "
                      "earlier cases can change it in between, so conflating "
                      "the two reads misclassifies every report whose state "
                      "changed => the xfail P2P tests fail => does NOT resolve.",
        "rationale": "on an input where the two reads differ "
                     "(rep_already_skipped=False, rep_skipped=True, "
                     "xfailed_present=True, exception_raised=True, "
                     "xfail_raises_mismatch=False) (Q-d) demands "
                     "outcome==OUTCOME_SKIPPED with the annotation set, but this "
                     "impl's guard is false so it classifies nothing. Rejection "
                     "from (Q-d).",
    },
    {
        "id": "rej-classify-phase-blind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CLASSIFY_PHASE_BLIND),
        "refinement": "dropping the call-phase test classifies a marked "
                      "expected failure that raised nothing during setup or "
                      "teardown as though it had unexpectedly passed during the "
                      "call, so setup/teardown reports of xfail-marked tests "
                      "are rewritten => the xfail P2P tests fail => does NOT "
                      "resolve.",
        "rationale": "on (…, not exception_raised, not phase_is_call) (Q-d)'s "
                     "fifth sub-case pins outcome and annotation to Old(...), "
                     "but this impl revises both. Rejection from (Q-d).",
    },
    # ---- uniqueness / reject: Group C, the content each case records ----
    # Each of these keeps the location correction AND every case's outcome and
    # annotation decision verbatim, so Groups A and B cannot see it; only the
    # content clauses (R-1)..(R-3) reject it.
    {
        "id": "rej-content-strict-silent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CONTENT_STRICT_SILENT),
        "refinement": "the strict no-exception call-phase sub-case sets the "
                      "outcome to failed and states nothing. Four different "
                      "sub-cases write that same outcome, so the report then "
                      "tells the user only that the test failed — never that it "
                      "failed because it was required to fail and passed "
                      "anyway. The strict-xpass P2P tests read that explanation "
                      "verbatim (an exact longrepr equality and an output-line "
                      "match) => those P2P tests fail while the F2P still "
                      "passes => does NOT resolve.",
        "rationale": "every Group A and Group B clause is satisfied — this impl "
                     "is behaviourally identical to gold on the outcome and the "
                     "annotation in every case. (R-2) demands "
                     "rep.explanation == EXPLANATION_STRICT_UNEXPECTED_PASS in "
                     "that sub-case, and the impl leaves Old(rep.explanation). "
                     "Rejection from (R-2), which no outcome-only spec can "
                     "express.",
    },
    {
        "id": "rej-content-unexpected-silent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CONTENT_UNEXPECTED_SILENT),
        "refinement": "case (a) sets the outcome to failed and states nothing, "
                      "so a unittest expectedFailure test that unexpectedly "
                      "passed is reported as a bare failure with no indication "
                      "of why it failed => the unexpected-success P2P tests, "
                      "which match the reported explanation, fail => does NOT "
                      "resolve.",
        "rationale": "(Q-a)'s outcome and annotation halves hold; (R-2) demands "
                     "rep.explanation == EXPLANATION_UNEXPECTED_SUCCESS and the "
                     "impl leaves Old(rep.explanation). Rejection from (R-2).",
    },
    {
        "id": "rej-content-verdict-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CONTENT_VERDICT_SWAP),
        "refinement": "both stating cases state a verdict, but each states the "
                      "OTHER's. The two explanations are what distinguishes an "
                      "unexpectedly-passing unittest expectedFailure from a "
                      "strict expected-failure mark whose test passed, so each "
                      "report now describes the other situation => both P2P "
                      "families fail => does NOT resolve.",
        "rationale": "the outcome is right in both cases and a verdict IS "
                     "stated in both, so a clause that only asked whether some "
                     "explanation was recorded would admit this. (R-2) pins "
                     "WHICH verdict each case states, so both instances "
                     "violate it. Rejection from (R-2).",
    },
    {
        "id": "rej-content-strict-reason",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CONTENT_STRICT_REASON),
        "refinement": "the strict sub-case states the right verdict but carries "
                      "the imperatively raised reason instead of the reason the "
                      "mark declared — and no exception was raised in that "
                      "sub-case at all, so the quoted reason is unrelated to "
                      "the report. The strict-xfail P2P tests assert the "
                      "mark's reason appears in the explanation => does NOT "
                      "resolve.",
        "rationale": "(R-3) pins explanation_reason == declared_reason in that "
                     "sub-case; on an input where the two reason tokens differ "
                     "the impl records the wrong one. Rejection from (R-3).",
    },
    {
        "id": "rej-content-note-reason-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CONTENT_NOTE_REASON_SWAP),
        "refinement": "the annotation is added in exactly the right cases but "
                      "the imperative case carries the mark's declared reason "
                      "and the mark's cases carry the imperatively raised one, "
                      "so every annotation quotes a reason its own case was "
                      "never given => the xfail-reason P2P tests (which assert "
                      "the annotation's text) fail => does NOT resolve.",
        "rationale": "(R-1) pins each annotating case's note_reason to the "
                     "reason that case was GIVEN (raised_reason in (Q-c), "
                     "declared_reason in (Q-d)'s annotating sub-cases); on an "
                     "input where the two tokens differ both are violated. "
                     "Rejection from (R-1).",
    },
    {
        "id": "rej-content-note-reason-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CONTENT_NOTE_REASON_DROP),
        "refinement": "the annotation becomes a bare flag: present in the right "
                      "cases, carrying no reason. Every expected-failure report "
                      "then renders an empty reason where the declared or "
                      "raised one belongs, which is exactly what the "
                      "xfail-reporting P2P tests assert => does NOT resolve.",
        "rationale": "(R-1) pins note_reason in (Q-c) and in (Q-d)'s two "
                     "annotating sub-cases; this impl leaves Old(note_reason) "
                     "in all three. Rejection from (R-1) — the annotation's "
                     "PRESENCE alone, which Group B pins, does not see it.",
    },
    {
        "id": "rej-content-note-style-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CONTENT_NOTE_STYLE_SWAP),
        "refinement": "every annotation lands in the right case carrying the "
                      "right reason, but each annotating case reads it in the "
                      "OTHER annotating case's style: the imperative case drops "
                      "the lead-in it is entitled to and the mark's cases gain "
                      "one they are not. The reason is right and the text the "
                      "user reads is wrong in both families, and the "
                      "xfail-reporting P2P tests read that rendered line => "
                      "does NOT resolve.",
        "rationale": "(R-1) pins note_style per annotating case — "
                     "NOTE_STYLE_LEAD_IN in (Q-c), NOTE_STYLE_VERBATIM in "
                     "(Q-d)'s two annotating sub-cases — so this impl violates "
                     "it in all three. Rejection from (R-1); note_reason and "
                     "the annotation's presence are gold here, so no other "
                     "clause sees this.",
    },
    {
        "id": "rej-content-note-style-merged",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CONTENT_NOTE_STYLE_MERGED),
        "refinement": "which case annotates, and the reason each annotation "
                      "carries, are gold; only the RENDERING collapses to one "
                      "shared site, so every annotation reads in a single "
                      "style. One rendering site means one rendering, which is "
                      "then wrong for whichever family it does not match => the "
                      "xfail-reporting P2P tests fail => does NOT resolve.",
        "rationale": "(R-1) pins note_style per annotating case and the "
                     "imperative case's style differs from the mark cases', so "
                     "no single value satisfies all three. Rejection from "
                     "(R-1). This is the shape a merge of the annotating cases "
                     "takes once the rendering is observable: on the reason "
                     "tokens alone the merge is indistinguishable from gold.",
    },
    {
        "id": "rej-frame-note-style",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_FRAME_NOTE_STYLE),
        "refinement": "the classification is gold in every slot except that the "
                      "raises-MISMATCH sub-case, which adds no annotation at "
                      "all, stamps a rendering style onto the annotation slot it "
                      "never wrote. A report that arrived already annotated then "
                      "has that annotation's rendering rewritten by a case with "
                      "nothing to say about it, so the user reads an earlier "
                      "reason in a style it was never recorded in => does NOT "
                      "resolve.",
        "rationale": "(R-1) frames note_style == Old(note_style) in every case "
                     "that adds no annotation, exactly as it frames the "
                     "annotation's presence and its reason; this impl writes it "
                     "in one such case. Rejection from that frame conjunct.",
    },
    {
        "id": "rej-content-overstate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CONTENT_OVERSTATE),
        "refinement": "the raises-MISMATCH sub-case gets its outcome right but "
                      "also states the verdict that belongs to a different "
                      "sub-case, so a marked expected failure that raised the "
                      "wrong exception type is reported as though it had passed "
                      "unexpectedly, replacing the actual failure explanation "
                      "=> the xfail-raises P2P tests fail => does NOT resolve.",
        "rationale": "the outcome is OUTCOME_FAILED exactly as (Q-d) demands, "
                     "so Group B is satisfied. (R-2) frames the stated verdict "
                     "in every case but the two that state one, so stating one "
                     "here violates it. Rejection from (R-2).",
    },
    {
        "id": "rej-content-toggle-states",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CONTENT_TOGGLE_STATES),
        "refinement": "with expected-failure reporting toggled off the outcome "
                      "and the annotation are left alone but the report "
                      "acquires an explanation the run never produced — exactly "
                      "the interference that configuration exists to prevent "
                      "=> the --runxfail P2P tests, which assert the reports "
                      "come through as the run left them, fail => does NOT "
                      "resolve.",
        "rationale": "(Q-b)'s outcome and annotation halves hold, so an "
                     "outcome-only reading of case (b) admits this. (Q-b) also "
                     "frames rep.explanation == Old(rep.explanation): a toggle "
                     "that declines to interfere decides nothing, including "
                     "what the report says. Rejection from (Q-b)'s stated-"
                     "verdict conjunct.",
    },
    {
        "id": "rej-content-success-reason-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CONTENT_SUCCESS_REASON_DROP),
        "refinement": "case (a) states the right verdict but records no reason "
                      "with it, so the report says only that a success was "
                      "unexpected and never which expectation was defied — the "
                      "reason the run recorded is dropped from the one place it "
                      "is shown => the unexpected-success P2P tests, which "
                      "match the reported reason, fail => does NOT resolve.",
        "rationale": "(Q-a)'s outcome, annotation and verdict-identity halves "
                     "all hold, so both Group B and (R-2) admit this. (R-4) "
                     "demands explanation_reason == success_reason and the impl "
                     "leaves Old(explanation_reason). Rejection from (R-4).",
    },
    {
        "id": "rej-content-success-reason-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_REJ_CONTENT_SUCCESS_REASON_SWAP),
        "refinement": "case (a) states the right verdict but carries the "
                      "reason the MARK declared instead of the one recorded "
                      "alongside the unexpected success, so the report quotes "
                      "an unrelated expectation's reason — and in the real "
                      "unexpected-success situation there is no evaluated mark "
                      "to take a reason from at all => does NOT resolve.",
        "rationale": "a verdict IS stated and it IS the right one, and it does "
                     "carry SOME reason, so every clause short of reason "
                     "identity admits this. (R-4) pins the stated verdict's "
                     "reason to success_reason; on an input where the two "
                     "tokens differ the impl records the wrong one. Rejection "
                     "from (R-4).",
    },
]

# No @ContractOnly axioms and no A-reference deep models in this bundle
# (meta.axioms == [], deep_model_references == []): the modelled behaviour is a
# control-flow and content specification of one hook, modelled directly. There
# is no opaque callee to over-approximate, so the axiom lane is vacuous.
AXIOM_TESTS = []
