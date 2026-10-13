"""Twin-artifact model for pytest-dev__pytest-7432.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A post-run report is finalised by two INDEPENDENT steps.

  (1) Outcome classification. The report's outcome, its expected-failure
      annotation and the verdict explanation the report shows the user are
      decided by the FIRST applicable case of a priority-ordered
      classification, and by nothing else:

        (a) an unexpected success was recorded for the run -> the outcome
            becomes failed, the report states that verdict to the user, carrying
            the reason that was recorded alongside that unexpected success, and
            no expected-failure annotation is added;
        (b) otherwise, expected-failure reporting is toggled off -> the
            outcome, the annotation and the stated verdict are all left exactly
            as the run left them. This toggle only declines to interfere: it
            decides nothing itself and it shields every remaining case from
            applying;
        (c) otherwise, an expected failure was raised imperatively -> the
            outcome becomes skipped and the annotation is added, carrying the
            reason that was raised, rendered in the lead-in style: what the user
            reads is the lead-in ``reason: `` and then that reason;
        (d) otherwise, the report is not already in the skipped state and an
            expected-failure mark was evaluated for the run -> the decision
            follows what the run did:
              * an exception was raised, outside the exception set the mark
                declares -> outcome failed, no annotation, no stated verdict;
              * an exception was raised, inside that set (or the mark declares
                no set) -> outcome skipped, annotation added, carrying the
                reason the mark declared, rendered verbatim: what the user reads
                is that reason itself and nothing else;
              * no exception was raised, in the call phase, mark strict ->
                outcome failed AND the report states that verdict to the user,
                carrying the reason the mark declared; no annotation is added.
                A run that was required to fail and passed anyway is reported
                as a failure whose stated verdict says so: an outcome code
                alone does not tell the user what happened;
              * no exception was raised, in the call phase, mark not strict ->
                outcome passed, annotation added, carrying the reason the mark
                declared, rendered verbatim as above;
              * no exception was raised, outside the call phase -> nothing is
                decided;
        (e) otherwise nothing is decided: outcome, annotation and stated
            verdict are left as the run left them.

      A verdict is stated by case (a) and by the strict sub-case of (d), and by
      NO other case: what the remaining cases record about themselves they
      record in the annotation. Stating a verdict REPLACES the report's single
      account of itself (see below), so a case that states one thereby discards
      any positional location the run had recorded, in every element.
      Whichever of the two slots a case uses, the
      reason it records there is the reason it was GIVEN -- the reason the mark
      declared, the reason that was raised imperatively, or the reason recorded
      alongside the unexpected success. A case may not invent a reason, drop
      one, or carry another case's. Nor may it render one in a style other than
      its own: an annotation added by the imperative case reads its reason
      behind the lead-in, an annotation added by a mark case reads its reason
      verbatim, and these are two DIFFERENT texts for one and the same reason,
      so a case that renders another case's style tells the user something the
      case it is is not entitled to say.

      A case that states no verdict of its own must leave the report's verdict
      slot exactly as the run left it: not only the KIND (no verdict stated)
      but its CONTENT, which is the account the run itself produced there. A
      test that failed for its own reasons keeps the account of that failure;
      overwriting it would discard the user's only record of that failure.
      Every observable this behaviour can write is therefore pinned in every
      case: which verdict is stated and the reason it carries, whether the
      annotation is present, the reason IT carries and the style it renders that
      reason in, the outcome, and the recorded location in all of its elements.

  (2) Skip-location correction. When a test is skipped by a skip-style mark,
      the post-run report's recorded source location must be corrected to point
      at the test's own definition (the location the reporting machinery
      surfaces to the user), rather than at the internal frame where the skip
      was raised. This correction is governed solely by its own three
      conditions:

        (C) the run was skipped by a skip-style mark, AND the report is in the
            skipped state, AND the report's recorded location is a positional
            triple (the only shape that carries a correctable source line).

      When (C) holds the corrected location names the test's own definition:
      the definition file, and the definition line (one past the zero-based
      definition line the reporting machinery returns). The skip reason the
      location already carried is kept as it is -- the correction moves where
      the report points, and changes nothing about what it says.

      The test's own definition line is a PARTIAL observable, and its partiality
      is part of this behaviour rather than an aside. The reporting machinery
      answers with a definition line only for a run it can locate in source; for
      a run it cannot locate it answers that there is NO definition line at all.
      A definition line is guaranteed exactly where (C) holds -- a run skipped by
      a skip-style mark whose report still carries a correctable positional
      triple is a run the reporting machinery can locate -- and the finalisation
      is entitled to one exactly there. Everywhere else it is not entitled to
      one: a report the correction does not apply to must be finalised all the
      same, and finalised WITHOUT a definition line, because for such a report
      there need not be one to have. A finalisation that needs the test's own
      definition line in order to finalise a report the correction leaves alone
      is asking for something that need not exist, and the report it was given
      then does not get finalised at all.

  The two steps meet in ONE place, and only there. The report keeps a SINGLE
  account of itself, and that account is EITHER a positional location triple
  OR a rendered standard verdict, never both. So the two steps are coupled in
  exactly one direction: a case of step (1) that states a verdict of its own
  overwrites that account, discarding any positional location that stood there,
  and condition (C) of step (2) is then read on the account AS IT STANDS -- a
  report whose account has just become a stated verdict has no triple left to
  correct. Nothing else couples them. In particular step (2) is INDEPENDENT of
  the expected-failure reporting toggle: the toggle governs step (1) only, and
  never suppresses the skip-location correction. And the correction never
  revises the outcome, the annotation or the stated verdict: it neither states
  a verdict nor removes one.

  The report's skipped state is read TWICE, at two different points, and the
  two reads are carried by two separate parameters: ``rep_already_skipped`` is
  the state the classification of step (1) case (d) tests, and ``rep_skipped``
  is the state condition (C) of step (2) tests.

The report is modelled as a minimal class carrying only the observables this
behaviour touches: whether its recorded location is a positional triple, and
that triple's file, line and reason; the outcome (an int code); whether the
expected-failure annotation is present, which reason it carries and in which
STYLE that reason is rendered; and which standard verdict the report states to
the user, plus the reason that stated verdict carries. The location group and
the stated-verdict group are two VIEWS
OF ONE SLOT, not two slots: ``loc_is_triple`` says which of the two the slot
currently holds, so when a verdict is stated the shape becomes false and the
three positional elements become ``LOC_ABSENT`` -- there is no longer any
file, line or reason to read. Files and reasons are carried as opaque ``int`` tokens --
value identity is what the behaviour turns on, not their text -- so "carries
the reason the mark declared" is stated as equality with that reason's token.
How a slot RENDERS the reason it carries is not decoration around the reason:
it is the text the user actually reads, so it is behaviour and is pinned too,
alongside WHICH reason reaches WHICH slot. The annotation renders its reason in
one of two styles, carried as an observable of its own, ``note_style``:
``NOTE_STYLE_LEAD_IN`` means the annotation reads the invariable lead-in
``reason: `` followed by the reason it carries; ``NOTE_STYLE_VERBATIM`` means it
reads that reason exactly, with nothing added and nothing dropped -- so an
annotation whose reason is empty is itself empty under the verbatim style, while
under the lead-in style it still reads that lead-in. ``NOTE_STYLE_ABSENT`` is
the style a report carrying no annotation is in. Which style an annotation uses
is determined by the case that added it, and is NOT recoverable from the reason
token it carries (two cases may be given equal reason tokens and still render
them differently), so it is an observable in its own right rather than a
function of the others: an imperatively raised expected failure is annotated in
the lead-in style, an expected-failure mark's reason is annotated verbatim, and
a case that adds no annotation leaves the style as it stands, exactly as it
leaves the annotation's presence and its reason.
The stated verdict is one of ``EXPLANATION_NONE`` (none was stated; whatever
the run itself produced stands in that slot), ``EXPLANATION_UNEXPECTED_SUCCESS``
or ``EXPLANATION_STRICT_UNEXPECTED_PASS``. WHICH verdict is stated and the
reason it carries are behaviour and are pinned, and so is the text each stated
verdict is rendered as, which the verdict itself determines and no
implementation is free to reword: ``EXPLANATION_STRICT_UNEXPECTED_PASS`` reads
``[XPASS(strict)] `` followed by the reason it carries, and
``EXPLANATION_UNEXPECTED_SUCCESS`` reads ``Unexpected success: `` followed by
the reason it carries, or bare ``Unexpected success`` when that reason is
empty. Booleans model the run-classification
predicates. The recorded location is an ``int`` line number; correction sets it
to the definition line. The test's OWN definition line -- what the reporting
machinery answers when asked where the test being reported on is defined -- is by
contrast an ``Optional[int]``: ``None`` is that machinery answering that the test
has no definition line at all, and an ``int`` is the zero-based line it answers
with. The two are different observables and only one of them is partial: the
report always has a recorded line to read (``LOC_ABSENT`` once its one account
has become a stated verdict), while the test being reported on need not have a
definition line for the machinery to answer with.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
# Completion obligation: a measure that must strictly decrease at every call and
# every iteration, so the finalisation discharges the clauses below only by
# actually REACHING its return. A finalisation that never comes back leaves the
# report un-finalised and the run hanging, and must not count as satisfying a
# single clause about what the finalised report says.
from nagini_contracts.obligations import MustTerminate

# The three outcome codes a post-run report can carry.
OUTCOME_PASSED = 0
OUTCOME_FAILED = 1
OUTCOME_SKIPPED = 2

# Which standard verdict, if any, the report states to the user. NONE means the
# finalisation stated none of its own and whatever the run produced stands.
EXPLANATION_NONE = 0
EXPLANATION_UNEXPECTED_SUCCESS = 1
EXPLANATION_STRICT_UNEXPECTED_PASS = 2

# In which STYLE the expected-failure annotation renders the reason it carries,
# i.e. what the user actually reads on that line. A reason token alone does not
# say this: one and the same reason renders as two different texts under the two
# styles, so the style is carried separately and pinned separately.
#   ABSENT   -- the report carries no annotation, so there is no rendering.
#   LEAD_IN  -- the annotation reads the invariable lead-in "reason: " and then
#               the reason it carries. Under this style an annotation carrying
#               an empty reason still reads that lead-in.
#   VERBATIM -- the annotation reads the reason it carries and nothing else, so
#               an annotation carrying an empty reason reads as empty.
NOTE_STYLE_ABSENT = 0
NOTE_STYLE_LEAD_IN = 1
NOTE_STYLE_VERBATIM = 2

# The designated "there is no positional location" token. The recorded location
# and the stated verdict are two views of one slot, so once a verdict is stated
# the slot holds no file, no line and no reason: all three positional elements
# read as this token, and no correctable location is left.
LOC_ABSENT = -1


class RunReport:
    def __init__(self, loc_is_triple: bool, loc_file: int, loc_line: int,
                 loc_reason: int, outcome: int, xfail_note_present: bool,
                 note_reason: int, note_style: int, explanation: int,
                 explanation_reason: int) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.loc_is_triple) and self.loc_is_triple is loc_is_triple)  # type: ignore
        Ensures(Acc(self.loc_file) and self.loc_file == loc_file)  # type: ignore
        Ensures(Acc(self.loc_line) and self.loc_line == loc_line)  # type: ignore
        Ensures(Acc(self.loc_reason) and self.loc_reason == loc_reason)  # type: ignore
        Ensures(Acc(self.outcome) and self.outcome == outcome)  # type: ignore
        Ensures(Acc(self.xfail_note_present) and self.xfail_note_present is xfail_note_present)  # type: ignore
        Ensures(Acc(self.note_reason) and self.note_reason == note_reason)  # type: ignore
        Ensures(Acc(self.note_style) and self.note_style == note_style)  # type: ignore
        Ensures(Acc(self.explanation) and self.explanation == explanation)  # type: ignore
        Ensures(Acc(self.explanation_reason) and self.explanation_reason == explanation_reason)  # type: ignore
        self.loc_is_triple = loc_is_triple
        self.loc_file = loc_file
        self.loc_line = loc_line
        self.loc_reason = loc_reason
        self.outcome = outcome
        self.xfail_note_present = xfail_note_present
        self.note_reason = note_reason
        self.note_style = note_style
        self.explanation = explanation
        self.explanation_reason = explanation_reason


# axioms-start
# (no unchanged callee needs axiomatizing: the location correction, the outcome
#  classification and their governing predicates are modelled directly)
# axioms-end


# pure-start
@Pure
def states_own_verdict(unexpected_success: bool, suppress_xfail_reporting: bool,
                       xfail_exception: bool, rep_already_skipped: bool,
                       xfailed_present: bool, exception_raised: bool,
                       phase_is_call: bool, xfail_strict: bool) -> bool:
    """Do the classification predicates select one of the two cases that state
    a verdict of their own -- case (a), or the strict sub-case of case (d)?

    Those are exactly the cases that overwrite the report's single account of
    itself, and therefore exactly the cases that leave no positional location
    behind. Every other case records what it has to say in the annotation and
    leaves the account alone.
    """
    return unexpected_success or (
        (not suppress_xfail_reporting) and (not xfail_exception)
        and (not rep_already_skipped) and xfailed_present
        and (not exception_raised) and phase_is_call and xfail_strict
    )


@Pure
def definition_line_budget(definition_line: Optional[int]) -> int:
    """The completion budget the finalisation is given: derived from the test's
    own definition line where the reporting machinery answers with one, and from
    nothing else where it answers that there is none.

    A budget is owed on EVERY report to be finalised -- including a report whose
    test has no definition line at all -- because the obligation to come back and
    hand a finalised report over is not conditional on any location being
    available to read.
    """
    return 2 if definition_line is None else definition_line + 2
# pure-end


def finalize_skip_location(
    rep: RunReport,
    definition_file: int,
    definition_line: Optional[int],
    skipped_by_mark: bool,
    rep_skipped: bool,
    unexpected_success: bool,
    suppress_xfail_reporting: bool,
    xfail_exception: bool,
    xfailed_present: bool,
    rep_already_skipped: bool,
    exception_raised: bool,
    xfail_raises_mismatch: bool,
    phase_is_call: bool,
    xfail_strict: bool,
    declared_reason: int,
    raised_reason: int,
    success_reason: int,
) -> None:
    # pre-conditions-start
    Requires(Acc(rep.loc_is_triple))
    Requires(Acc(rep.loc_file))
    Requires(Acc(rep.loc_line))
    Requires(Acc(rep.loc_reason))
    Requires(Acc(rep.outcome))
    Requires(Acc(rep.xfail_note_present))
    Requires(Acc(rep.note_reason))
    Requires(Acc(rep.note_style))
    Requires(Acc(rep.explanation))
    Requires(Acc(rep.explanation_reason))
    # The test's own definition line is available exactly where the correction
    # applies, and is a non-negative line there. The reporting machinery answers
    # with a definition line only for a run it can locate in source, and a run
    # skipped by a skip-style mark whose report still carries a correctable
    # positional triple is such a run. For every OTHER report the answer may be
    # that the test has no definition line at all, and the finalisation is owed
    # nothing: availability is therefore CONDITIONED on the correction's own three
    # conditions rather than demanded of every report. Every report is admissible
    # here, including one whose test has no definition line, and each of them must
    # be finalised all the same.
    Requires(
        Implies(
            skipped_by_mark and rep_skipped and rep.loc_is_triple,
            definition_line is not None and definition_line >= 0,
        )
    )
    # The finalisation is carried out to completion and hands the report back:
    # the caller receives a finalised report, it is not left waiting on one. The
    # budget is derived from the definition line where there is one so that a
    # finalisation may delegate to a smaller one; what is ruled out is coming
    # back round to finalise on a budget no smaller than this one. Demanded of
    # every admissible input -- including one whose test has no definition line
    # at all, which is owed a budget like any other -- so this obliges the
    # finalisation and restricts no input.
    Requires(MustTerminate(definition_line_budget(definition_line)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(rep.loc_is_triple))
    Ensures(Acc(rep.loc_file))
    Ensures(Acc(rep.loc_line))
    Ensures(Acc(rep.loc_reason))
    Ensures(Acc(rep.outcome))
    Ensures(Acc(rep.xfail_note_present))
    Ensures(Acc(rep.note_reason))
    Ensures(Acc(rep.note_style))
    Ensures(Acc(rep.explanation))
    Ensures(Acc(rep.explanation_reason))
    # === where the two steps meet: one slot, two views ====================
    # Stating a verdict overwrites the report's single account of itself, so a
    # case that states one leaves NO positional location: neither the shape nor
    # any of its three elements survives.
    Ensures(
        Implies(
            states_own_verdict(unexpected_success, suppress_xfail_reporting,
                               xfail_exception, rep_already_skipped,
                               xfailed_present, exception_raised,
                               phase_is_call, xfail_strict),
            (not rep.loc_is_triple)
            and rep.loc_file == LOC_ABSENT
            and rep.loc_line == LOC_ABSENT
            and rep.loc_reason == LOC_ABSENT,
        )
    )
    # That is the ONLY way the shape of the recorded location changes: nothing
    # here creates a positional location that the run had not recorded, and no
    # case other than the two verdict-stating ones discards one.
    Ensures(
        Implies(
            not states_own_verdict(unexpected_success, suppress_xfail_reporting,
                                   xfail_exception, rep_already_skipped,
                                   xfailed_present, exception_raised,
                                   phase_is_call, xfail_strict),
            rep.loc_is_triple == Old(rep.loc_is_triple),
        )
    )
    # === step (2): the skip-location correction ===========================
    # The skip-location correction fires exactly on its own three conditions,
    # INDEPENDENTLY of the expected-failure reporting toggle and of the other
    # outcome-classification predicates: when a skip-mark skip has a positional
    # location triple, the recorded location becomes the test's own definition
    # -- the definition file and the definition line -- while the skip reason
    # the location carried is kept, so what the user is told does not change,
    # only where the report points. Its third condition is read on the account
    # as it STANDS, which is why a stated verdict (having replaced the account)
    # leaves nothing for it to correct. Where the correction fires there IS a
    # definition line to point at, which is what entitles this clause to say
    # which line the report ends up recording.
    Ensures(
        Implies(
            skipped_by_mark and rep_skipped and Old(rep.loc_is_triple)
            and not states_own_verdict(unexpected_success,
                                       suppress_xfail_reporting,
                                       xfail_exception, rep_already_skipped,
                                       xfailed_present, exception_raised,
                                       phase_is_call, xfail_strict),
            rep.loc_is_triple
            and definition_line is not None
            and rep.loc_line == definition_line + 1
            and rep.loc_file == definition_file
            and rep.loc_reason == Old(rep.loc_reason),
        )
    )
    # When neither the correction applies nor a verdict is stated, the recorded
    # location is left untouched in every element.
    Ensures(
        Implies(
            (not states_own_verdict(unexpected_success,
                                    suppress_xfail_reporting,
                                    xfail_exception, rep_already_skipped,
                                    xfailed_present, exception_raised,
                                    phase_is_call, xfail_strict))
            and not (skipped_by_mark and rep_skipped and Old(rep.loc_is_triple)),
            rep.loc_line == Old(rep.loc_line)
            and rep.loc_file == Old(rep.loc_file)
            and rep.loc_reason == Old(rep.loc_reason),
        )
    )
    # === step (1): the outcome classification ==============================
    # Case (a) — a recorded unexpected success decides the outcome outright,
    # and takes precedence over every other case. The report states that
    # verdict to the user, carrying the reason recorded alongside the
    # unexpected success. No annotation is added.
    Ensures(
        Implies(
            unexpected_success,
            rep.outcome == OUTCOME_FAILED
            and rep.explanation == EXPLANATION_UNEXPECTED_SUCCESS
            and rep.explanation_reason == success_reason
            and rep.xfail_note_present == Old(rep.xfail_note_present)
            and rep.note_reason == Old(rep.note_reason)
            and rep.note_style == Old(rep.note_style),
        )
    )
    # Case (b) — with expected-failure reporting toggled off, the outcome, the
    # annotation and the stated verdict are ALL left as the run left them: the
    # toggle decides nothing, and it shields cases (c) and (d) from applying at
    # all.
    Ensures(
        Implies(
            (not unexpected_success) and suppress_xfail_reporting,
            rep.outcome == Old(rep.outcome)
            and rep.xfail_note_present == Old(rep.xfail_note_present)
            and rep.note_reason == Old(rep.note_reason)
            and rep.note_style == Old(rep.note_style)
            and rep.explanation == Old(rep.explanation)
            and rep.explanation_reason == Old(rep.explanation_reason),
        )
    )
    # Case (c) — an imperatively raised expected failure is reported as a skip
    # and carries the expected-failure annotation, whose reason is the reason
    # that was raised, rendered in the lead-in style: the user reads the lead-in
    # and then that reason, which is a DIFFERENT text from the same reason
    # standing on its own. No verdict is stated over the run's own presentation.
    Ensures(
        Implies(
            (not unexpected_success) and (not suppress_xfail_reporting)
            and xfail_exception,
            rep.outcome == OUTCOME_SKIPPED and rep.xfail_note_present
            and rep.note_reason == raised_reason
            and rep.note_style == NOTE_STYLE_LEAD_IN
            and rep.explanation == Old(rep.explanation)
            and rep.explanation_reason == Old(rep.explanation_reason),
        )
    )
    # Case (d) — a run that is not already skipped and carries an evaluated
    # expected-failure mark is classified by what the run actually did. The
    # four sub-cases below are exhaustive together with the fifth (no
    # exception, outside the call phase), where nothing is decided. Every
    # annotation this case adds carries the reason the mark declared.
    Ensures(
        Implies(
            (not unexpected_success) and (not suppress_xfail_reporting)
            and (not xfail_exception)
            and (not rep_already_skipped) and xfailed_present
            and exception_raised and xfail_raises_mismatch,
            rep.outcome == OUTCOME_FAILED
            and rep.xfail_note_present == Old(rep.xfail_note_present)
            and rep.note_reason == Old(rep.note_reason)
            and rep.note_style == Old(rep.note_style)
            and rep.explanation == Old(rep.explanation)
            and rep.explanation_reason == Old(rep.explanation_reason),
        )
    )
    Ensures(
        Implies(
            (not unexpected_success) and (not suppress_xfail_reporting)
            and (not xfail_exception)
            and (not rep_already_skipped) and xfailed_present
            and exception_raised and (not xfail_raises_mismatch),
            rep.outcome == OUTCOME_SKIPPED and rep.xfail_note_present
            and rep.note_reason == declared_reason
            and rep.note_style == NOTE_STYLE_VERBATIM
            and rep.explanation == Old(rep.explanation)
            and rep.explanation_reason == Old(rep.explanation_reason),
        )
    )
    # The strict sub-case: a run the mark required to fail passed anyway. The
    # outcome becomes failed AND the report states that verdict to the user,
    # carrying the reason the mark declared; no annotation is added.
    Ensures(
        Implies(
            (not unexpected_success) and (not suppress_xfail_reporting)
            and (not xfail_exception)
            and (not rep_already_skipped) and xfailed_present
            and (not exception_raised) and phase_is_call and xfail_strict,
            rep.outcome == OUTCOME_FAILED
            and rep.explanation == EXPLANATION_STRICT_UNEXPECTED_PASS
            and rep.explanation_reason == declared_reason
            and rep.xfail_note_present == Old(rep.xfail_note_present)
            and rep.note_reason == Old(rep.note_reason)
            and rep.note_style == Old(rep.note_style),
        )
    )
    Ensures(
        Implies(
            (not unexpected_success) and (not suppress_xfail_reporting)
            and (not xfail_exception)
            and (not rep_already_skipped) and xfailed_present
            and (not exception_raised) and phase_is_call
            and (not xfail_strict),
            rep.outcome == OUTCOME_PASSED and rep.xfail_note_present
            and rep.note_reason == declared_reason
            and rep.note_style == NOTE_STYLE_VERBATIM
            and rep.explanation == Old(rep.explanation)
            and rep.explanation_reason == Old(rep.explanation_reason),
        )
    )
    Ensures(
        Implies(
            (not unexpected_success) and (not suppress_xfail_reporting)
            and (not xfail_exception)
            and (not rep_already_skipped) and xfailed_present
            and (not exception_raised) and (not phase_is_call),
            rep.outcome == Old(rep.outcome)
            and rep.xfail_note_present == Old(rep.xfail_note_present)
            and rep.note_reason == Old(rep.note_reason)
            and rep.note_style == Old(rep.note_style)
            and rep.explanation == Old(rep.explanation)
            and rep.explanation_reason == Old(rep.explanation_reason),
        )
    )
    # Case (e) — no case applies: the outcome, the annotation and the stated
    # verdict are left as the run left them.
    Ensures(
        Implies(
            (not unexpected_success) and (not suppress_xfail_reporting)
            and (not xfail_exception)
            and not ((not rep_already_skipped) and xfailed_present),
            rep.outcome == Old(rep.outcome)
            and rep.xfail_note_present == Old(rep.xfail_note_present)
            and rep.note_reason == Old(rep.note_reason)
            and rep.note_style == Old(rep.note_style)
            and rep.explanation == Old(rep.explanation)
            and rep.explanation_reason == Old(rep.explanation_reason),
        )
    )
    # post-conditions-end
    # impl-start
    if unexpected_success:
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
    elif skipped_by_mark and rep_skipped and rep.loc_is_triple:
        assert definition_line is not None
        rep.loc_file = definition_file
        rep.loc_line = definition_line + 1
    # impl-end
