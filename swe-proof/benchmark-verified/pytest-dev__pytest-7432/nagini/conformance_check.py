#!/usr/bin/env python3
"""G-CONF differential conformance for pytest-dev__pytest-7432 (nagini).

Refutes (or fails to refute) the R/I refinement leg: does the MODEL's impl
region in `nagini/model.py` agree with the REAL patched repo function it claims
to model? No other gate covers this: G-VERIFY says the impl meets the spec,
G-PBT says no wrong impl meets it, and neither one imports the repository.

===========================================================================
ORACLE CHOICE: the real patched function is CALLED, not transliterated.
===========================================================================

Oracle = `_pytest.skipping.pytest_runtest_makereport(item, call)`
         (`src/_pytest/skipping.py:260`, body 261-306; the gate has already
         applied the gold patch, which splits the trailing `elif` that performs
         the skip-location correction into an independent `if`). Every
         `skipping.py:NNN` reference below is a line of THAT patched file -- the
         file this script actually calls -- so the correction's three conditions
         are at 296/297/298 and its rewrite at 303-306. (At base_commit the same
         lines are one lower, the gold patch inserting a blank line.)

The hook is a `hookimpl(hookwrapper=True)` GENERATOR: `@hookimpl` only tags the
function with an attribute, so the object bound in the module is an ordinary
generator function that can be driven directly, without a pytest session:

    gen = pytest_runtest_makereport(item, call)
    next(gen)                       # advances to `outcome = yield`
    gen.send(outcome)               # runs the body under test
                                    # -> mutates rep.longrepr in place

This is a deliberate STRENGTHENING over the `lean/` sibling, whose docstring
argues that "standing up a live pytest session ... is heavy and unnecessary"
and therefore uses a hand-written "faithful in-process replica of the
POST-PATCH control flow" as its oracle. A replica of the control flow is a
paraphrase of the very thing under test: if the reader mis-transcribed an arm,
the replica and the shadow are wrong together and the diff is silently green.
Here NO line of the oracle's control flow is retyped -- the patched bytes in
/testbed decide every branch, including the `elif` -> `if` split that IS the
gold patch. Verified in-container: the driver reaches the correction and
rewrites `('/int/skipping.py', 238, reason)` to `('/t/test_file.py', 2, reason)`
at ~236k calls/s, so >=1e5 inputs cost well under a second.

===========================================================================
TYPE BRIDGE (mapping.md section 2, inverted)
===========================================================================

The model works over an abstract carrier: a `RunReport(loc_is_triple: bool,
loc_file, loc_line, loc_reason, outcome, xfail_note_present: bool, note_reason,
note_style, explanation, explanation_reason)` plus twelve `bool` branch predicates, the item
definition (`definition_file`, `definition_line`) and the three reasons the
classification may be GIVEN (`declared_reason`, `raised_reason`,
`success_reason`). The real function wants `(item, call, rep)` objects.

The repo keeps the recorded location and the stated verdict in ONE attribute,
`rep.longrepr`: a positional triple `(file, line, reason)` when the report
carries a correctable source location, and a rendered string when the
classification states a standard verdict. The model splits that one attribute
into two slots, so the bridge below splits it the same way and compares BOTH.

Rather than *choose* the abstract booleans and hand-build a matching report --
which is what manufactures phantom disagreements, see below -- this check
generates in the CONCRETE direction and DERIVES the abstract carrier:

  concrete input  =  (exc_kind, when, runxfail, skipped_by_mark_store,
                      xfailed_store, unexpected_success_store,
                      definition_line, internal_line, filename, reason)

  * `exc_kind` picks what the test body raised; the `ExceptionInfo` is produced
    by really raising it (`pytest.skip` / `pytest.xfail` / AssertionError).
  * the report is then built by the REAL factory
    `TestReport.from_item_and_call(item, call)` (`src/_pytest/reports.py:292`),
    so `rep.outcome` and the SHAPE of `rep.longrepr` are decided by repo code,
    never by this script. In particular the positional triple
    `(str(path), lineno, message)` appears exactly when
    `excinfo.errisinstance(skip.Exception)` (reports.py:311-314).
  * the abstract booleans are then READ OFF that realized state exactly as
    mapping.md section 1 specifies:
        loc_is_triple  <- type(rep.longrepr) is tuple        (skipping.py:298)
        loc_file       <- str(rep.longrepr[0])               (skipping.py:306)
        loc_line       <- rep.longrepr[1]                    (skipping.py:306)
        loc_reason     <- rep.longrepr[2]                    (skipping.py:303)
        definition_file<- str(item.reportinfo()[:2][0])      (skipping.py:304)
        definition_line<- item.reportinfo()[:2][1]           (skipping.py:304)
                          -- Optional[int]: `Item.reportinfo` (nodes.py:654-655)
                          answers `(self.fspath, None, "")` for a run item it
                          cannot locate in source, so this carrier is PARTIAL and
                          the model types it Optional[int]. The real hook reads it
                          only inside the correction's guard and asserts it there
                          (:304); the model's precondition supplies it under
                          exactly that guard and nowhere else. The generator
                          therefore emits None only on shapes the correction does
                          not apply to -- see the boundary list.
        skipped_by_mark<- item._store.get(skipped_by_mark_key, True)     (:296)
        declared_reason<- ("declared", xfailed.reason)        (:286/:290/:293)
        raised_reason  <- ("raised", call.excinfo.value.msg)              (:277)
        success_reason <- ("success", item._store[unexpectedsuccess_key]) (:267)
        unexpected_success <- unexpectedsuccess_key in item._store
                              and rep.when == "call"                     (:266)
        suppress_xfail_reporting <- item.config.option.runxfail          (:273)
        xfail_exception<- call.excinfo and isinstance(call.excinfo.value,
                                                     xfail.Exception)    (:275)
        xfailed_present<- truthiness of item._store.get(xfailed_key,None)(:279)
        rep_already_skipped <- rep.skipped, read BEFORE classification    (:279)
        exception_raised    <- call.excinfo is not None                   (:280)
        xfail_raises_mismatch <- raises is not None
                              and not isinstance(call.excinfo.value,raises)(:282)
        phase_is_call       <- call.when == "call"                        (:287)
        xfail_strict        <- xfailed.strict                             (:288)
        outcome (pre-state)      <- OUTCOME_CODE[rep.outcome]
        xfail_note_present (pre) <- hasattr(rep, "wasxfail")
        note_reason (pre-state)  <- origin-tagged recovery of rep.wasxfail
        note_style (pre-state)   <- the style rep.wasxfail reads its reason in,
                                    read off the text: NOTE_STYLE_LEAD_IN for
                                    the `reason: ` form (:277), otherwise
                                    NOTE_STYLE_VERBATIM (:286/:293), and
                                    NOTE_STYLE_ABSENT with no annotation
        explanation (pre-state)  <- EXPLANATION_NONE: no standard verdict has
                                    been stated yet
        explanation_reason (pre) <- ("own", repr(rep.longrepr)): the identity of
                                    the account the RUN itself produced, so a
                                    case that replaced one account with a
                                    different one is a token change here rather
                                    than an invisible one

  The report's skipped state is read at TWO points by the modeled behaviour and
  the two reads are two separate parameters: `rep_already_skipped` is the
  pre-classification read (:279), while `rep_skipped` is the read taken at the
  location correction (:297), i.e. AFTER the classification may have rewritten
  the outcome. The latter is therefore DERIVED, not generated: the shadow is run
  once with the correction's guard made unsatisfiable and the classified outcome
  is read off the result. That cannot mask a wrong classification, because the
  classified outcome is itself part of the compared observable below.

  Observable compared -- EVERY slot the model carries, so that no write the real
  hook performs lands outside it:

    (type(rep.longrepr) is tuple,
     (str(l[0]), l[1], l[2]) if tuple else None,      # the whole location
     OUTCOME_CODE[rep.outcome],
     hasattr(rep, "wasxfail"),
     origin-tagged token recovered from rep.wasxfail, # WHICH reason annotated
     which standard verdict rep.longrepr states,      # NONE / unexpected
                                                      # success / strict xpass
     the reason that stated verdict carries,
     style recovered from rep.wasxfail)               # HOW that reason reads

  versus the same eight components read off the shadow's carrier. The verdict
  components are recovered from the RENDERED text by `_explanation_of`: a
  positional triple is a location and not a verdict; `"Unexpected success"` /
  `"Unexpected success: R"` (skipping.py:269/271) is the unexpected-success
  verdict carrying R; `"[XPASS(strict)] R"` (skipping.py:290) is the strict
  unexpected-pass verdict carrying R; anything else is the account the run
  produced. Recovery reads the text ONLY -- it is never told which arm fired --
  and invariants (I3)/(I4) below assert the recovery is unambiguous on this
  domain, so a model that put the right verdict in the right slot with the wrong
  reason, or that dropped the verdict and kept only the outcome code, disagrees
  here instead of being invisible.

  Comparing the verdict slot is what ties the two arms that write it -- case (a)
  at skipping.py:269-272 and the strict expected-failure arm at :289-290 -- to
  the repo. An earlier projection compared only the 4-tuple
  `(triple?, line, outcome, note?)`; on a strict unexpected pass the test PASSED,
  so `longrepr` is never a tuple and the outcome is `failed` either way, which
  made `rep.longrepr = "[XPASS(strict)] " + xfailed.reason` invisible to this
  check even though `testing/test_skipping.py::TestXFail::test_xfail_xpassed_strict`
  asserts it verbatim. It is inside the compared observable now.

  The annotation's RENDERING is inside it for the same reason, and was added for
  the same kind of miss. An earlier projection inverted the `reason: ` prefix
  back to an origin tag and compared only WHICH reason had annotated; that made
  the imperative arm's `"reason: " + msg` (skipping.py:277) and the mark arms'
  bare `xfailed.reason` (:286, :293) the SAME point of the observable, even
  though the string is printed to the user unaltered (terminal.py:1102-1106) and
  `TestXFail::test_xfail_imperative` matches `"*reason:*hello*"` against exactly
  that line while `test_skipping.py:172`/`:187` assert `callreport.wasxfail`
  equals the mark's reason with no prefix at all. A hook that annotated with the
  right reason in the other arm's style therefore agreed here while breaking
  those PASS_TO_PASS tests. `_note_style` reports the rendering as its own
  component now, so that difference is a disagreement.

===========================================================================
WHY THE CONCRETE DIRECTION IS THE HONEST DOMAIN, NOT A WEAKENED ONE
===========================================================================

Generating the 7 booleans freely (2**7 = 128 points) and hand-assembling a
report to match produced, for an earlier revision of this check, 34 apparent
disagreements, which that revision excluded as unrealizable on TWO claimed repo
invariants. Only ONE of the two survived scrutiny. The other, (I2) below, was
FALSE, and excluding on it hid a real defect in the model -- so the exclusion is
gone and the model was repaired instead. Both claims are still re-asserted
mechanically at startup by `_assert_domain_invariants()`, the surviving one as a
domain filter and the refuted one as a POSITIVE WITNESS of the behaviour it used
to deny, so neither piece of reasoning can silently rot:

  (I1) `xfail_exception AND loc_is_triple` is unsatisfiable.
       A triple `longrepr` requires the excinfo be a `Skipped`
       (reports.py:311); `xfail_exception` requires it be an `XFailed`.
       `XFailed` subclasses `Failed`, NOT `Skipped`
       (`issubclass(xfail.Exception, skip.Exception) is False`), and one
       excinfo cannot be both. Hand-forcing both makes the real hook take
       arm 3, set `rep.outcome = "skipped"`, and thus satisfy the final `if`
       via a FRESHLY re-read `rep.skipped` -- which is exactly why the
       shadow's `rep_skipped` is DERIVED from the classified outcome rather
       than generated freely (see the TYPE BRIDGE note above); a frozen
       `rep_skipped=False` would be a divergence with no preimage in the
       real system. (2 of the 34.)

  (I2) REFUTED -- `unexpected_success AND loc_is_triple` IS satisfiable, and
       this check no longer excludes it. (It accounted for 32 of the 34.)
       The old argument ran: `unexpectedsuccess_key` is written only by
       `TestCaseFunction.addUnexpectedSuccess` (`src/_pytest/unittest.py:232`),
       which CPython's `TestCase.run` calls only when `outcome.success` is
       true, and `unittest.case._Outcome.testPartExecutor` sets
       `success = False` on any `SkipTest`; so the item's call report can never
       also carry a `Skipped` excinfo. The hole in that argument is the phrase
       "on any SkipTest": `TestCase.run` only sees the skips raised INSIDE it.
       `CallInfo.from_call(lambda: item.runtest(), "call")` is one level out
       (`runner.py:255`), and a call-phase hookwrapper -- or any `pytest.skip`
       raised after `runtest` returns -- lands its `Skipped` excinfo on the SAME
       CallInfo whose `addUnexpectedSuccess` already stored the key. Both
       conditions then hold on one real report. Probed in-container against the
       gold-patched repo with a `pytest_runtest_call` hookwrapper that raises
       `pytest.skip` after yielding, over a passing
       `@unittest.expectedFailure` test:

           PRE |skipped|tuple|('.../conftest.py', 38, 'Skipped: late skip ...')
           POST|failed |str  |'Unexpected success'

       so the hook really does replace a positional triple with a stated
       verdict. That is not an unrealizable input; it is a coupling the model
       had failed to describe, and while the exclusion stood the check could not
       have seen the omission. The model now pins it (`LOC_ABSENT`,
       `states_own_verdict`), and the 15,382 points this exclusion used to drop
       are generated and compared like every other point.

So exactly one of the two claims is a domain restriction, and it restricts the
INPUT to what repo code can build -- never the ORACLE'S ANSWER. Excluding on the
oracle's answer is what makes a differential check green by construction, and
(I2) is the cautionary case: it was phrased as an input restriction but was
derived from the very output disagreement it went on to hide. Every excluded
point is still accounted for out loud -- the exhaustive pass reports
`structural_points`, `realizable`, and `unrealizable_by_invariant` counts, so a
domain that quietly collapsed to nothing is visible instead of green.

Non-vacuity is enforced, not hoped for. `--selftest-prepatch` re-runs the whole
comparison against the PRE-patch control flow in place of the oracle and
demands that it FAIL; the F2P branch is additionally asserted to be exercised
(`branch_hits`), so an input domain that never reaches the arm the gold patch
changed cannot report success. Confirmed: pre-patch is refuted at the F2P point
(`exc_kind='skip', runxfail=True, skipped_by_mark=True, when='call'`), where the
correction must still fire post-patch but the pre-patch `elif` chain is consumed
by the `--runxfail` arm and leaves the internal line in place.

The modeled structural space is FINITE (4 exc kinds x 3 phases x 2 runxfail x
3 mark-store states x 5 xfailed shapes x 2 unexpected-success states, times
boundary line/name choices) and far smaller than 1e5, so it is ENUMERATED
EXHAUSTIVELY first -- a stronger check than 1e5 samples of it -- and seeded
fuzz over the same space then fills the count to >=1e5.

No `PSeq`/`ToSeq` shim is needed: this model's carrier is a small class plus
ints and bools, with no Nagini sequence. No `@ContractOnly` callee is consumed
(mapping.md section 3), so nothing is axiomatized-but-unexercised here.

stdlib + the repo under test only (hypothesis is not required; the fuzzer is a
seeded `random.Random`). Pinned seed: 7432 (recorded in mapping.md, G-CONF).
Exit 0 iff zero disagreements.
"""
import itertools
import json
import os
import random
import sys

SEED = 7432
TARGET_INPUTS = 100_000

# --------------------------------------------------------------------------
# Repo imports: the REAL patched module is the oracle.
# --------------------------------------------------------------------------
import _pytest.skipping as SK
from _pytest.skipping import Xfail
from _pytest._code import ExceptionInfo
from _pytest.outcomes import skip as skip_outcome, xfail as xfail_outcome
from _pytest.reports import TestReport
from _pytest.store import Store

REAL_HOOK = SK.pytest_runtest_makereport


# ==========================================================================
# SHADOW -- the impl region of nagini/model.py, copied VERBATIM with only
# contract calls removed. Nothing renamed, reordered, or "simplified".
# ==========================================================================

OUTCOME_PASSED = 0
OUTCOME_FAILED = 1
OUTCOME_SKIPPED = 2

EXPLANATION_NONE = 0
EXPLANATION_UNEXPECTED_SUCCESS = 1
EXPLANATION_STRICT_UNEXPECTED_PASS = 2

# model.py's "there is no positional location" token. The abstraction below uses
# the SAME token when the realized report carries no triple, so the model's
# carrier convention and this harness's reading of a real report agree by
# construction rather than by coincidence.
LOC_ABSENT = -1

# The style an annotation reads its reason in. The string the repo assigns to
# `rep.wasxfail` is printed to the user unaltered (terminal.py:1102-1106), and the
# three annotating writes are not the same function of their reason: :277 writes
# `"reason: " + msg`, :286 and :293 write the reason alone.
NOTE_STYLE_ABSENT = 0
NOTE_STYLE_LEAD_IN = 1
NOTE_STYLE_VERBATIM = 2


class RunReport:
    """model.py RunReport, contracts stripped. Same ten fields, same order."""

    def __init__(self, loc_is_triple, loc_file, loc_line, loc_reason, outcome,
                 xfail_note_present, note_reason, note_style, explanation,
                 explanation_reason):
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


def finalize_skip_location(
    rep,
    definition_file,
    definition_line,
    skipped_by_mark,
    rep_skipped,
    unexpected_success,
    suppress_xfail_reporting,
    xfail_exception,
    xfailed_present,
    rep_already_skipped,
    exception_raised,
    xfail_raises_mismatch,
    phase_is_call,
    xfail_strict,
    declared_reason,
    raised_reason,
    success_reason,
):
    # impl-start  (model.py impl region, contracts removed)
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

    if skipped_by_mark and rep_skipped and rep.loc_is_triple:
        assert definition_line is not None
        rep.loc_file = definition_file
        rep.loc_line = definition_line + 1
    # impl-end


# ==========================================================================
# PRE-PATCH control flow -- used ONLY by --selftest-prepatch to prove this
# check has teeth. Never used as the oracle.
# ==========================================================================

def _prepatch_reference(rep_pre, item, call):
    """The pre-patch chain (correction as the FINAL elif), over the same
    realized objects. Mirrors skipping.py:266-305 before the gold patch."""
    rep = rep_pre
    xfailed = item._store.get(SK.xfailed_key, None)
    if SK.unexpectedsuccess_key in item._store and rep.when == "call":
        reason = item._store[SK.unexpectedsuccess_key]
        rep.longrepr = ("Unexpected success: {}".format(reason) if reason
                        else "Unexpected success")
        rep.outcome = "failed"
    elif item.config.option.runxfail:
        pass
    elif call.excinfo and isinstance(call.excinfo.value, xfail_outcome.Exception):
        rep.wasxfail = "reason: " + str(call.excinfo.value.msg)
        rep.outcome = "skipped"
    elif not rep.skipped and xfailed:
        if call.excinfo:
            raises = xfailed.raises
            if raises is not None and not isinstance(call.excinfo.value, raises):
                rep.outcome = "failed"
            else:
                rep.outcome = "skipped"
                rep.wasxfail = xfailed.reason
        elif call.when == "call":
            if xfailed.strict:
                rep.outcome = "failed"
                rep.longrepr = "[XPASS(strict)] " + xfailed.reason
            else:
                rep.outcome = "passed"
                rep.wasxfail = xfailed.reason
    elif (
        item._store.get(SK.skipped_by_mark_key, True)
        and rep.skipped
        and type(rep.longrepr) is tuple
    ):
        _, _, reason = rep.longrepr
        filename, line = item.reportinfo()[:2]
        assert line is not None
        rep.longrepr = str(filename), line + 1, reason
    return rep


# ==========================================================================
# TYPE BRIDGE: concrete repo objects.
# ==========================================================================

class _Option:
    def __init__(self, runxfail):
        self.runxfail = runxfail


class _Config:
    def __init__(self, runxfail):
        self.option = _Option(runxfail)

    def getini(self, name):
        return False

    def getoption(self, name, default=None):
        if name == "runxfail":
            return self.option.runxfail
        return default


class _Item:
    """Minimal stand-in exposing exactly the surface the hook and the report
    factory touch on a real `Item`."""

    def __init__(self, runxfail, store, definition_line, filename, nodeid):
        self.config = _Config(runxfail)
        self._store = store
        self._definition_line = definition_line
        self._filename = filename
        self.nodeid = nodeid
        self.location = (filename, definition_line, "T.test_x")
        self.keywords = {}
        self.user_properties = []
        self._report_sections = []

    def reportinfo(self):
        # skipping.py:304 consumes [:2]; real items return (path, lineno, name)
        return (self._filename, self._definition_line, "T.test_x")

    # The factory calls these for non-skip failures; real items return a
    # rich repr object -- any non-tuple stands for it faithfully here.
    def repr_failure(self, excinfo, style=None):
        return "<failure repr>"

    def _repr_failure_py(self, excinfo, style=None):
        return "<failure repr>"


class _Call:
    def __init__(self, excinfo, when):
        self.excinfo = excinfo
        self.when = when
        self.duration = 0.0


class _Outcome:
    """The hookwrapper's `outcome` object: only get_result() is used."""

    def __init__(self, rep):
        self._rep = rep

    def get_result(self):
        return self._rep


def _make_excinfo(exc_kind, reason):
    """Produce a REAL ExceptionInfo by really raising, so that the report
    factory classifies it with repo code."""
    if exc_kind == "none":
        return None
    try:
        if exc_kind == "skip":
            skip_outcome(reason)
        elif exc_kind == "xfail":
            xfail_outcome(reason)
        elif exc_kind == "fail":
            raise AssertionError("boom")
        elif exc_kind == "valueerror":
            raise ValueError("boom")
        else:
            raise AssertionError("unknown exc_kind %r" % (exc_kind,))
    except BaseException:
        return ExceptionInfo.from_current()
    raise AssertionError("unreachable")


XFAILED_SHAPES = {
    "none": None,
    "plain": ("r-plain", True, False, None),
    "strict": ("r-strict", True, True, None),
    "raises_match": ("r-match", True, False, (AssertionError,)),
    "raises_nomatch": ("r-nomatch", True, False, (KeyError,)),
    # Empty declared reasons: the boundary at which the repo's rendering of a
    # stated verdict / an annotation degenerates ("[XPASS(strict)] " with
    # nothing after it). WHICH reason reaches the slot must still be pinned.
    "plain_empty": ("", True, False, None),
    "strict_empty": ("", True, True, None),
}


def _build(concrete):
    """concrete -> (item, call, rep). `rep` is built by the REAL factory, so
    its outcome and longrepr SHAPE come from repo code."""
    store = Store()
    if concrete["bymark"] is not None:
        store[SK.skipped_by_mark_key] = concrete["bymark"]
    shape = XFAILED_SHAPES[concrete["xfailed"]]
    if shape is not None:
        store[SK.xfailed_key] = Xfail(*shape)
    if concrete["unexp"]:
        store[SK.unexpectedsuccess_key] = concrete["unexp_reason"]

    item = _Item(concrete["runxfail"], store, concrete["definition_line"],
                 concrete["filename"], concrete["nodeid"])
    excinfo = _make_excinfo(concrete["exc_kind"], concrete["reason"])
    call = _Call(excinfo, concrete["when"])
    rep = TestReport.from_item_and_call(item, call)
    return item, call, rep


OUTCOME_CODE = {"passed": OUTCOME_PASSED, "failed": OUTCOME_FAILED,
                "skipped": OUTCOME_SKIPPED}


def _abstract(item, call, rep):
    """Read the model's carrier off the realized state (mapping.md section 1)."""
    longrepr = rep.longrepr
    loc_is_triple = type(longrepr) is tuple
    xfailed = item._store.get(SK.xfailed_key, None)
    raises = getattr(xfailed, "raises", None) if xfailed else None
    return {
        "loc_is_triple": loc_is_triple,
        # Sentinel when there is no triple: the model still carries an int, and
        # a shadow that wrote unconditionally would be caught by the sentinel
        # check below.
        "loc_line": longrepr[1] if loc_is_triple else _NO_LINE,
        # The triple's other two elements, carried by the model as opaque
        # tokens: the file the location names (skipping.py:306 writes
        # `str(filename)` there) and the skip reason it already carried
        # (skipping.py:303 unpacks it and :306 writes it back unchanged).
        "loc_file": str(longrepr[0]) if loc_is_triple else _NO_FILE,
        "loc_reason": longrepr[2] if loc_is_triple else _NO_REASON,
        "definition_line": item.reportinfo()[:2][1],
        # skipping.py:304+306 `filename, line = item.reportinfo()[:2]` ...
        # `rep.longrepr = str(filename), line + 1, reason`
        "definition_file": str(item.reportinfo()[:2][0]),
        "skipped_by_mark": item._store.get(SK.skipped_by_mark_key, True),
        # The report's skipped state is read TWICE by the modeled behaviour, at
        # two different points, and the two reads are carried by two separate
        # parameters. `rep_already_skipped` is the read taken BEFORE any outcome
        # classification (skipping.py:279 `not rep.skipped`); at that point the
        # priority chain guarantees no earlier case has run, so it is the
        # realized pre-state.  `rep_skipped` is the read taken at the location
        # correction (skipping.py:297), i.e. AFTER classification -- derived
        # below, in `compare`, from the classification's own result.
        "rep_already_skipped": rep.skipped,
        "unexpected_success": (SK.unexpectedsuccess_key in item._store
                               and rep.when == "call"),
        "suppress_xfail_reporting": item.config.option.runxfail,
        "xfail_exception": bool(call.excinfo is not None and isinstance(
            call.excinfo.value, xfail_outcome.Exception)),
        "xfailed_present": bool(xfailed),
        # skipping.py:280 `if call.excinfo:`
        "exception_raised": call.excinfo is not None,
        # skipping.py:281-282 `raises is not None and not isinstance(...)`
        "xfail_raises_mismatch": bool(
            call.excinfo is not None and raises is not None
            and not isinstance(call.excinfo.value, raises)),
        # skipping.py:287 `elif call.when == "call":`
        "phase_is_call": call.when == "call",
        # skipping.py:288 `if xfailed.strict:`
        "xfail_strict": bool(getattr(xfailed, "strict", False)) if xfailed
                        else False,
        # The three reasons the classification may be GIVEN, as opaque tagged
        # tokens (mapping.md section 2: value identity is what the behaviour
        # turns on).  Tagged by ORIGIN so the projection below can recover which
        # reason reached a slot from the text alone, without being told.
        #   declared: skipping.py:286 / :290 / :293 `xfailed.reason`
        #   raised:   skipping.py:277 `"reason: " + call.excinfo.value.msg`
        #   success:  skipping.py:267-269 `item._store[unexpectedsuccess_key]`
        "declared_reason": (("declared", xfailed.reason) if xfailed
                            else _NO_DECLARED),
        "raised_reason": (("raised", str(call.excinfo.value.msg))
                          if (call.excinfo is not None and isinstance(
                              call.excinfo.value, xfail_outcome.Exception))
                          else _NO_RAISED),
        "success_reason": (("success", item._store[SK.unexpectedsuccess_key])
                           if SK.unexpectedsuccess_key in item._store
                           else _NO_SUCCESS),
        # the pre-state of the classification observables
        "outcome": OUTCOME_CODE[rep.outcome],
        "xfail_note_present": hasattr(rep, "wasxfail"),
        "note_reason": (_note_token(rep.wasxfail) if hasattr(rep, "wasxfail")
                        else _NO_NOTE),
        "note_style": (_note_style(rep.wasxfail) if hasattr(rep, "wasxfail")
                       else NOTE_STYLE_ABSENT),
        # No standard verdict has been stated yet: whatever account the RUN
        # produced in that slot is what stands, and its identity is the token,
        # so a case that silently replaced one account with another is caught.
        "explanation": EXPLANATION_NONE,
        "explanation_reason": _own_account(longrepr),
    }


# Sentinels: the model's carrier always holds a value in each slot, so a slot
# that has no realized counterpart holds an unmistakable one and a shadow that
# wrote it unconditionally is caught by the sentinel checks in `compare`.
#
# For the three location elements that sentinel is LOC_ABSENT -- the SAME token
# the model writes when a stated verdict replaces the report's account of itself.
# The two situations are the same situation: there is no positional location to
# read. Sharing the token is what lets `compare` tell "the shadow fabricated a
# location" (any other value) from either of them.
_NO_LINE = LOC_ABSENT      # "the report carries no correctable line"
_NO_FILE = LOC_ABSENT
_NO_REASON = LOC_ABSENT
_NO_NOTE = "<no-annotation>"
_NO_DECLARED = ("declared", "<no-xfail-mark>")
_NO_RAISED = ("raised", "<no-xfail-exception>")
_NO_SUCCESS = ("success", "<no-unexpected-success>")

_UNEXPECTED_SUCCESS_BARE = "Unexpected success"
_UNEXPECTED_SUCCESS_PREFIX = "Unexpected success: "
_STRICT_XPASS_PREFIX = "[XPASS(strict)] "
_RAISED_NOTE_PREFIX = "reason: "


def _own_account(longrepr):
    """The token for `no standard verdict was stated; the run's own account
    stands`. Keyed on the identity of that account, so replacing one account
    with a different one is a token change, not an invisible one."""
    return ("own", repr(longrepr))


def _note_token(wasxfail):
    """Recover WHICH reason reached the expected-failure annotation from the
    text the repo wrote there. The imperative arm renders its reason with a
    `reason: ` prefix (skipping.py:277); the mark arms write the declared reason
    verbatim (:286, :293). The tag is recovered here and compared against the
    token the shadow was handed.

    NOTE: this recovery is deliberately NOT the whole comparison. Inverting the
    prefix back to an origin tag would make the two renderings the same point of
    the observable, and the rendering is itself behaviour -- the string is shown
    to the user unaltered (terminal.py:1102-1106) and the hidden suite asserts it
    in both directions (test_skipping.py:172/:187 forbid a lead-in on the mark
    arms; :333/:351 require one on the imperative arm). So `_note_style` below
    reports the rendering as its own component of the compared observable, and
    the shadow is handed a matching `note_style`; a hook that annotated with the
    right reason in the wrong style is a DISAGREEMENT here, not an invisible
    difference."""
    if wasxfail.startswith(_RAISED_NOTE_PREFIX):
        return ("raised", wasxfail[len(_RAISED_NOTE_PREFIX):])
    return ("declared", wasxfail)


def _note_style(wasxfail):
    """Which STYLE the annotation reads its reason in, read off the text itself
    rather than off which arm wrote it: NOTE_STYLE_LEAD_IN when the annotation
    reads the invariable `reason: ` lead-in and then its reason (skipping.py:277),
    NOTE_STYLE_VERBATIM when it reads the reason alone (:286, :293)."""
    if wasxfail.startswith(_RAISED_NOTE_PREFIX):
        return NOTE_STYLE_LEAD_IN
    return NOTE_STYLE_VERBATIM


def _explanation_of(longrepr, own):
    """Split the repo's single `rep.longrepr` slot into the model's two: which
    standard verdict (if any) is stated to the user, and the reason it carries.

    A positional triple is a source LOCATION, not a stated verdict, so it maps
    to `no verdict stated`; the triple's own three elements are compared
    separately. A string the repo wrote from one of the two verdict templates
    (skipping.py:269/271 and :290) maps to that verdict plus the reason
    recovered out of the template. Anything else is the account the run itself
    produced, carried by its identity."""
    if type(longrepr) is tuple:
        return EXPLANATION_NONE, own
    if isinstance(longrepr, str):
        if longrepr == _UNEXPECTED_SUCCESS_BARE:
            # skipping.py:271 -- an empty recorded reason is left out of the
            # rendering; the reason token it carries is that empty reason.
            return EXPLANATION_UNEXPECTED_SUCCESS, ("success", "")
        if longrepr.startswith(_UNEXPECTED_SUCCESS_PREFIX):
            return (EXPLANATION_UNEXPECTED_SUCCESS,
                    ("success", longrepr[len(_UNEXPECTED_SUCCESS_PREFIX):]))
        if longrepr.startswith(_STRICT_XPASS_PREFIX):
            return (EXPLANATION_STRICT_UNEXPECTED_PASS,
                    ("declared", longrepr[len(_STRICT_XPASS_PREFIX):]))
    return EXPLANATION_NONE, _own_account(longrepr)


def _project(rep, own):
    """The observable the model carries, in full: the recorded location in all
    of its elements, the outcome, whether the expected-failure annotation is
    present and which reason it carries, and which standard verdict the report
    states plus the reason THAT carries.

    Every write the modeled function performs is inside this projection --
    skipping.py:269, :271, :272, :277, :278, :283, :285-286, :289-290,
    :292-293 and :306 -- so no write of the real hook lands outside the compared
    observable."""
    longrepr = rep.longrepr
    triple = type(longrepr) is tuple
    note = hasattr(rep, "wasxfail")
    explanation, explanation_reason = _explanation_of(longrepr, own)
    return (triple,
            (str(longrepr[0]), longrepr[1], longrepr[2]) if triple else None,
            OUTCOME_CODE[rep.outcome],
            note,
            _note_token(rep.wasxfail) if note else None,
            explanation,
            explanation_reason,
            _note_style(rep.wasxfail) if note else NOTE_STYLE_ABSENT)


# ==========================================================================
# DOMAIN INVARIANTS -- mechanically re-asserted, see docstring (I1)/(I2).
# ==========================================================================

def _assert_domain_invariants():
    problems = []
    # (I1) XFailed is not a Skipped, so xfail_exception and a triple longrepr
    #      cannot co-occur through the real factory.
    if issubclass(xfail_outcome.Exception, skip_outcome.Exception):
        problems.append("xfail.Exception unexpectedly subclasses skip.Exception; "
                        "invariant (I1) no longer holds")
    ei_skip = _make_excinfo("skip", "unconditional skip")
    ei_xf = _make_excinfo("xfail", "xf")
    if not ei_skip.errisinstance(skip_outcome.Exception):
        problems.append("a pytest.skip excinfo is not a Skipped")
    if ei_xf.errisinstance(skip_outcome.Exception):
        problems.append("a pytest.xfail excinfo is a Skipped; (I1) broken")
    # The factory must yield a triple exactly for the skip excinfo.
    for kind, want_triple in (("none", False), ("skip", True),
                              ("xfail", False), ("fail", False)):
        c = _base_concrete(exc_kind=kind, when="call")
        _, _, rep = _build(c)
        if (type(rep.longrepr) is tuple) is not want_triple:
            problems.append("factory triple-ness for exc_kind=%r is %r, "
                            "expected %r" % (kind, not want_triple, want_triple))
    # (I2) A case that states a verdict REPLACES the report's single account of
    #      itself, so no positional location survives it. This is asserted
    #      POSITIVELY, on the very point that used to be excluded from the domain
    #      as unrealizable: an unexpected success recorded for a report that
    #      carries a skip triple. It is realizable (a skip raised from a
    #      call-phase hookwrapper reaches the same CallInfo after
    #      addUnexpectedSuccess has written the store key), and the real hook
    #      clobbers the triple with its rendered verdict.
    c2 = _base_concrete(exc_kind="skip", when="call", unexp=True,
                        unexp_reason="because")
    item2, call2, rep2 = _build(c2)
    if type(rep2.longrepr) is not tuple:
        problems.append("the (I2) witness no longer starts from a positional "
                        "triple (%r); invariant (I2) unverified"
                        % (rep2.longrepr,))
    _oracle_real(rep2, item2, call2)
    if type(rep2.longrepr) is tuple:
        problems.append("a stated verdict no longer replaces the positional "
                        "location (%r); invariant (I2) broken" % (rep2.longrepr,))
    if _explanation_of(rep2.longrepr, None)[0] != EXPLANATION_UNEXPECTED_SUCCESS:
        problems.append("the (I2) witness did not end up stating the "
                        "unexpected-success verdict (%r)" % (rep2.longrepr,))
    # (I3) The projection recovers WHICH reason reached a slot from the text the
    #      repo rendered there. That recovery must be injective on this domain,
    #      or a right-slot/wrong-reason model could be scored as agreeing. No
    #      declared reason may render into the imperative arm's template.
    for shape_name, shape in XFAILED_SHAPES.items():
        if shape is None:
            continue
        if shape[0].startswith(_RAISED_NOTE_PREFIX):
            problems.append("declared reason %r (shape %r) renders into the "
                            "imperative annotation template; (I3) broken"
                            % (shape[0], shape_name))
    # (I4) No account the RUN itself produces may look like one of the two
    #      verdict templates, or "the run's own account still stands" would be
    #      indistinguishable from "this verdict was stated".
    for kind in EXC_KINDS:
        for when in WHENS:
            c = _base_concrete(exc_kind=kind, when=when)
            _, _, rep0 = _build(c)
            got = _explanation_of(rep0.longrepr, _own_account(rep0.longrepr))
            if got[0] != EXPLANATION_NONE:
                problems.append(
                    "a pre-classification account (exc_kind=%r, when=%r, "
                    "longrepr=%r) projects to verdict %r; (I4) broken"
                    % (kind, when, rep0.longrepr, got[0]))
    return problems


def _realizable(concrete):
    """Is this concrete point buildable by the real system? Constrains the
    INPUT only -- never the oracle's answer.

    NOTHING is excluded any more. This predicate used to drop every point with
    `unexp and exc_kind == "skip"` on the strength of an argument about
    `unittest.TestCase.run` -- and that argument was too narrow: a skip raised
    OUTSIDE `TestCase.run`, from a call-phase hookwrapper, lands in the same
    `CallInfo` after `addUnexpectedSuccess` has already written the store key, so
    the real system does reach a triple-carrying unexpected-success report. Those
    15,382 points are now generated and compared like any other; the coupling
    they exercise -- a stated verdict replaces the report's single account of
    itself, positional location and all -- is pinned by the model and asserted
    positively in `_assert_domain_invariants()`.
    """
    return True


# ==========================================================================
# The differential comparison.
# ==========================================================================

def _base_concrete(**kw):
    c = {
        "exc_kind": "skip",
        "when": "call",
        "runxfail": False,
        "bymark": True,
        "xfailed": "none",
        "unexp": False,
        "unexp_reason": "",
        "definition_line": 1,
        "filename": "/t/test_sample.py",
        "nodeid": "test_sample.py::test_x",
        "reason": "unconditional skip",
    }
    c.update(kw)
    return c


def compare(concrete, oracle_fn, branch_hits):
    """Run oracle and shadow on one concrete point. Return None if they agree,
    else a dict describing the disagreement."""
    # --- realize, then read the pre-state and the abstract carrier ---
    item, call, rep = _build(concrete)
    abs_in = _abstract(item, call, rep)
    pre_longrepr = rep.longrepr
    pre_reason = pre_longrepr[2] if type(pre_longrepr) is tuple else None

    # --- SHADOW: the model's impl region over the abstract carrier ---
    #
    # `rep_skipped` is the SECOND read of the report's skipped state: the real
    # behaviour reads it at the location correction (skipping.py:297), i.e.
    # AFTER the outcome classification has already run and possibly rewritten
    # the outcome.  It is therefore not a free input -- it is whatever the
    # classification left behind.  Derive it by running the shadow once with the
    # correction disabled (skipped_by_mark=False, so the correction's guard is
    # unsatisfiable) and reading the classified outcome off the result.
    #
    # Using the MODEL to derive one of the model's own parameters cannot mask a
    # wrong classification: the classified outcome is itself compared against
    # the oracle below, so an error in it is reported directly rather than
    # cancelling out.
    def _run_shadow(rep_obj, skipped_by_mark, rep_skipped):
        finalize_skip_location(
            rep_obj,
            abs_in["definition_file"],
            abs_in["definition_line"],
            skipped_by_mark,
            rep_skipped,
            abs_in["unexpected_success"],
            abs_in["suppress_xfail_reporting"],
            abs_in["xfail_exception"],
            abs_in["xfailed_present"],
            abs_in["rep_already_skipped"],
            abs_in["exception_raised"],
            abs_in["xfail_raises_mismatch"],
            abs_in["phase_is_call"],
            abs_in["xfail_strict"],
            abs_in["declared_reason"],
            abs_in["raised_reason"],
            abs_in["success_reason"],
        )

    def _fresh():
        return RunReport(abs_in["loc_is_triple"], abs_in["loc_file"],
                         abs_in["loc_line"], abs_in["loc_reason"],
                         abs_in["outcome"], abs_in["xfail_note_present"],
                         abs_in["note_reason"], abs_in["note_style"],
                         abs_in["explanation"],
                         abs_in["explanation_reason"])

    scratch = _fresh()
    _run_shadow(scratch, False, False)
    rep_skipped_after_classification = scratch.outcome == OUTCOME_SKIPPED

    shadow_rep = _fresh()
    _run_shadow(shadow_rep, abs_in["skipped_by_mark"],
                rep_skipped_after_classification)
    shadow_obs = (shadow_rep.loc_is_triple,
                  (shadow_rep.loc_file, shadow_rep.loc_line,
                   shadow_rep.loc_reason) if shadow_rep.loc_is_triple else None,
                  shadow_rep.outcome,
                  shadow_rep.xfail_note_present,
                  (shadow_rep.note_reason if shadow_rep.xfail_note_present
                   else None),
                  shadow_rep.explanation,
                  shadow_rep.explanation_reason,
                  (shadow_rep.note_style if shadow_rep.xfail_note_present
                   else NOTE_STYLE_ABSENT))

    # A shadow that wrote the location unconditionally would trip this.
    if not abs_in["loc_is_triple"] and (
            shadow_rep.loc_line != _NO_LINE
            or shadow_rep.loc_file != _NO_FILE
            or shadow_rep.loc_reason != _NO_REASON):
        return {"why": "shadow wrote the location with no correctable location",
                "concrete": _fmt(concrete), "abstract": _fmt(abs_in),
                "shadow": shadow_obs, "oracle": None}
    # A shadow that recorded an annotation reason without adding the annotation
    # would trip this.
    if (not abs_in["xfail_note_present"]
            and not shadow_rep.xfail_note_present
            and shadow_rep.note_reason != _NO_NOTE):
        return {"why": "shadow wrote note_reason without adding the annotation",
                "concrete": _fmt(concrete), "abstract": _fmt(abs_in),
                "shadow": shadow_obs, "oracle": None}

    # --- ORACLE: drive the REAL patched hook over the realized objects ---
    oracle_rep = oracle_fn(rep, item, call)
    oracle_obs = _project(oracle_rep, abs_in["explanation_reason"])

    # Record which arm of the modeled decision was taken (non-vacuity).
    fired = (abs_in["skipped_by_mark"] and rep_skipped_after_classification
             and abs_in["loc_is_triple"])
    branch_hits["correction_fired" if fired else "correction_skipped"] += 1
    if fired and abs_in["suppress_xfail_reporting"]:
        branch_hits["f2p_runxfail_and_corrected"] += 1
    # Which slot the real hook actually wrote, so a domain that never made the
    # repo state a verdict -- and therefore never compared one -- is visible.
    if oracle_obs[5] == EXPLANATION_UNEXPECTED_SUCCESS:
        branch_hits["verdict_unexpected_success_stated"] += 1
        if oracle_obs[6] == ("success", ""):
            branch_hits["verdict_reason_empty"] += 1
    elif oracle_obs[5] == EXPLANATION_STRICT_UNEXPECTED_PASS:
        branch_hits["verdict_strict_xpass_stated"] += 1
        if oracle_obs[6] == ("declared", ""):
            branch_hits["verdict_reason_empty"] += 1
    # The coupling the model now pins: a report that arrived carrying a positional
    # location, and a verdict stated over it. The exclusion this check used to
    # apply made exactly this counter unreachable, which is how the omission
    # survived; requiring it below is what stops that happening again.
    if oracle_obs[5] != EXPLANATION_NONE and abs_in["loc_is_triple"]:
        branch_hits["verdict_annihilated_a_location"] += 1
        if oracle_obs[0]:
            return {"why": "a stated verdict left the positional location "
                           "standing in the repo",
                    "concrete": _fmt(concrete), "abstract": _fmt(abs_in),
                    "shadow": shadow_obs, "oracle": oracle_obs}
    if oracle_obs[4] is not None:
        branch_hits["annotation_carries_" + oracle_obs[4][0]] += 1
    for name in ("unexpected_success", "suppress_xfail_reporting",
                 "xfail_exception"):
        if abs_in[name]:
            branch_hits[name] += 1
    if (not abs_in["rep_already_skipped"]) and abs_in["xfailed_present"]:
        branch_hits["xfail_on_failure_arm"] += 1
        # the five sub-cases of the classification's fourth case
        if abs_in["exception_raised"]:
            branch_hits["xfail_raises_mismatch" if abs_in["xfail_raises_mismatch"]
                        else "xfail_raises_match"] += 1
        elif abs_in["phase_is_call"]:
            branch_hits["xpass_strict" if abs_in["xfail_strict"]
                        else "xpass_nonstrict"] += 1

    if oracle_obs != shadow_obs:
        return {"why": "model/repo observable mismatch",
                "concrete": _fmt(concrete), "abstract": _fmt(abs_in),
                "shadow": shadow_obs, "oracle": oracle_obs}

    # The corrected location's file and reason are now ELEMENTS of the compared
    # observable above, not side-checks, because the model carries them. Assert
    # that outright, so a future edit that shrinks the projection back to the
    # line alone fails here instead of quietly narrowing what is compared.
    if fired:
        post = oracle_rep.longrepr
        if post[2] != pre_reason:
            return {"why": "correction did not preserve the reason",
                    "concrete": _fmt(concrete), "abstract": _fmt(abs_in),
                    "shadow": ("reason", pre_reason), "oracle": ("reason", post[2])}
        if post[0] != str(concrete["filename"]):
            return {"why": "correction did not point at the item definition file",
                    "concrete": _fmt(concrete), "abstract": _fmt(abs_in),
                    "shadow": ("filename", str(concrete["filename"])),
                    "oracle": ("filename", post[0])}
        if shadow_obs[1] != (post[0], post[1], post[2]):
            return {"why": "projection no longer carries the whole location",
                    "concrete": _fmt(concrete), "abstract": _fmt(abs_in),
                    "shadow": shadow_obs[1],
                    "oracle": (post[0], post[1], post[2])}
    return None


def _oracle_real(rep, item, call):
    """Drive the REAL patched hook. Nothing about its control flow is retyped."""
    gen = REAL_HOOK(item, call)
    next(gen)                      # advance to `outcome = yield`
    try:
        gen.send(_Outcome(rep))    # run the body under test
    except StopIteration:
        pass
    else:                          # pragma: no cover - hook yields exactly once
        raise AssertionError("hook did not terminate after one send")
    return rep


def _fmt(d):
    if isinstance(d, dict):
        return {k: (v if isinstance(v, (int, bool, str, type(None))) else repr(v))
                for k, v in d.items()}
    return d


# ==========================================================================
# Input generation: exhaustive over the finite structural space, then fuzz.
# ==========================================================================

EXC_KINDS = ("none", "skip", "xfail", "fail", "valueerror")
WHENS = ("setup", "call", "teardown")
BYMARKS = (None, True, False)          # None = key absent -> default True
XFAILEDS = tuple(XFAILED_SHAPES)
# (recorded?, recorded reason). The empty reason is a boundary of its own: the
# repo drops it from the rendering (skipping.py:271), and the model's claim is
# that the slot still carries THAT reason.
UNEXPS = ((False, ""), (True, ""), (True, "because"))
BOUNDARY_LINES = (0, 1, 2, 41, 9999)


def structural_space():
    for exc_kind, when, runxfail, bymark, xfailed, unexp in itertools.product(
            EXC_KINDS, WHENS, (False, True), BYMARKS, XFAILEDS, UNEXPS):
        yield {"exc_kind": exc_kind, "when": when, "runxfail": runxfail,
               "bymark": bymark, "xfailed": xfailed, "unexp": unexp[0],
               "unexp_reason": unexp[1]}


def main(argv):
    prepatch_selftest = "--selftest-prepatch" in argv
    oracle_fn = _prepatch_reference if prepatch_selftest else _oracle_real

    problems = _assert_domain_invariants()
    if problems:
        for p in problems:
            print("DOMAIN INVARIANT BROKEN: %s" % p)
        print(json.dumps({"status": "fail", "reason": "domain invariants",
                          "problems": problems}))
        return 1

    branch_hits = {k: 0 for k in (
        "correction_fired", "correction_skipped", "f2p_runxfail_and_corrected",
        "unexpected_success", "suppress_xfail_reporting", "xfail_exception",
        "xfail_on_failure_arm", "xfail_raises_mismatch", "xfail_raises_match",
        "xpass_strict", "xpass_nonstrict",
        "verdict_unexpected_success_stated", "verdict_strict_xpass_stated",
        "verdict_reason_empty", "verdict_annihilated_a_location",
        "annotation_carries_declared", "annotation_carries_raised")}
    checked = 0
    unrealizable = 0
    structural_points = 0
    disagreements = []

    # ---- boundary cases first, including the exact F2P shape ----------------
    boundary = [
        # F2P: @pytest.mark.skip under --runxfail -- the branch the gold patch
        # changed. Correction MUST still fire.
        _base_concrete(exc_kind="skip", when="call", runxfail=True,
                       bymark=True, definition_line=1),
        # P2P counterpart: same, without --runxfail.
        _base_concrete(exc_kind="skip", when="call", runxfail=False, bymark=True),
        # skip during setup (the common mark-skip path).
        _base_concrete(exc_kind="skip", when="setup", bymark=True),
        # skip not attributed to a mark.
        _base_concrete(exc_kind="skip", when="call", bymark=False),
        # mark-store key absent -> defaults to True.
        _base_concrete(exc_kind="skip", when="call", bymark=None),
        # no exception at all: nothing to correct.
        _base_concrete(exc_kind="none", when="call"),
        # imperative xfail.
        _base_concrete(exc_kind="xfail", when="call"),
        # plain failure with an xfail mark evaluated (arm 4).
        _base_concrete(exc_kind="fail", when="call", xfailed="plain"),
        _base_concrete(exc_kind="fail", when="call", xfailed="strict"),
        _base_concrete(exc_kind="fail", when="call", xfailed="raises_match"),
        _base_concrete(exc_kind="fail", when="call", xfailed="raises_nomatch"),
        # xpass paths -- the strict one is where the stated verdict is written
        # (skipping.py:289-290), including at an empty declared reason.
        _base_concrete(exc_kind="none", when="call", xfailed="plain"),
        _base_concrete(exc_kind="none", when="call", xfailed="strict"),
        _base_concrete(exc_kind="none", when="call", xfailed="strict_empty"),
        _base_concrete(exc_kind="none", when="call", xfailed="plain_empty"),
        _base_concrete(exc_kind="fail", when="call", xfailed="plain_empty"),
        # unittest unexpected success (arm 1).
        _base_concrete(exc_kind="none", when="call", unexp=True,
                       unexp_reason="because"),
        _base_concrete(exc_kind="fail", when="call", unexp=True, unexp_reason=""),
        # definition-line boundaries at the F2P shape.
        _base_concrete(exc_kind="skip", when="call", runxfail=True,
                       definition_line=0),
        _base_concrete(exc_kind="skip", when="call", runxfail=True,
                       definition_line=9999),
        # ABSENT definition line (the reporting machinery answers None, as it
        # does for a run item it cannot locate in source -- Item.reportinfo,
        # nodes.py:654-655). The model carries this as definition_line=None and
        # requires a definition line only where the correction applies, so these
        # points are exactly the complement: reports the correction does NOT
        # apply to, which must still be finalised with no definition line at all.
        # The correcting shapes are deliberately NOT generated with None: there
        # the real hook asserts a definition line, which is the assumption the
        # model's conditioned precondition mirrors.
        _base_concrete(exc_kind="skip", when="call", bymark=False,
                       definition_line=None),
        _base_concrete(exc_kind="none", when="call", definition_line=None),
        _base_concrete(exc_kind="fail", when="call", xfailed="plain",
                       definition_line=None),
        _base_concrete(exc_kind="none", when="call", xfailed="strict",
                       definition_line=None),
        _base_concrete(exc_kind="none", when="call", unexp=True,
                       unexp_reason="because", definition_line=None),
    ]
    for c in boundary:
        if not _realizable(c):
            unrealizable += 1
            continue
        d = compare(c, oracle_fn, branch_hits)
        checked += 1
        if d:
            disagreements.append(("boundary", d))
            break

    # ---- exhaustive enumeration of the finite structural space -------------
    if not disagreements:
        for s in structural_space():
            structural_points += 1
            for line in BOUNDARY_LINES:
                c = _base_concrete(definition_line=line, **s)
                if not _realizable(c):
                    unrealizable += 1
                    continue
                d = compare(c, oracle_fn, branch_hits)
                checked += 1
                if d:
                    disagreements.append(("exhaustive", d))
                    break
            if disagreements:
                break

    # ---- seeded fuzz over the SAME space, to reach >=1e5 -------------------
    if not disagreements:
        rng = random.Random(SEED)
        structural = [s for s in structural_space()]
        while checked < TARGET_INPUTS:
            s = dict(rng.choice(structural))
            c = _base_concrete(
                definition_line=rng.choice(
                    [0, 1, 2, rng.randrange(0, 100000)]),
                filename=rng.choice(
                    ["/t/test_sample.py", "/a/b/test_x.py", "test_rel.py",
                     "/t/weird name.py"]),
                nodeid="test_sample.py::test_%d" % rng.randrange(0, 1000),
                reason=rng.choice(
                    ["unconditional skip", "", "because reasons", "a:b:c"]),
                **s)
            if not _realizable(c):
                unrealizable += 1
                continue
            d = compare(c, oracle_fn, branch_hits)
            checked += 1
            if d:
                disagreements.append(("fuzz", d))
                break

    # ---- verdict -----------------------------------------------------------
    if disagreements:
        phase, d = disagreements[0]
        print("DISAGREEMENT (%s): %s" % (phase, d["why"]))
        print("  concrete input : %r" % (d["concrete"],))
        print("  abstract input : %r" % (d["abstract"],))
        print("  shadow (model) : %r" % (d["shadow"],))
        print("  oracle (repo)  : %r" % (d["oracle"],))
        if prepatch_selftest:
            print("SELFTEST OK: the pre-patch control flow IS refuted by this "
                  "check, so the input domain reaches the changed branch.")
            print(json.dumps({"status": "selftest-pass",
                              "prepatch_refuted": True,
                              "checked": checked,
                              "first_disagreement": d["why"]}))
            return 0
        print(json.dumps({"status": "fail", "checked": checked,
                          "disagreements": 1, "why": d["why"]}))
        return 1

    if prepatch_selftest:
        print("SELFTEST FAILED: the pre-patch control flow was NOT refuted -- "
              "this check is vacuous.")
        print(json.dumps({"status": "selftest-fail", "prepatch_refuted": False,
                          "checked": checked}))
        return 1

    # Non-vacuity: the branch the gold patch changed must have been exercised,
    # and so must every classification case the spec's Group B pins -- a domain
    # that never reaches one of them would compare that case against nothing.
    vacuous = [k for k in ("correction_fired", "f2p_runxfail_and_corrected",
                           "unexpected_success", "suppress_xfail_reporting",
                           "xfail_exception", "xfail_on_failure_arm",
                           "xfail_raises_mismatch", "xfail_raises_match",
                           "xpass_strict", "xpass_nonstrict",
                           # the two slots the classification writes besides
                           # the outcome: a domain that never made the repo
                           # state a verdict, or never made it record an
                           # annotation reason of each origin, would compare
                           # those clauses against nothing at all.
                           "verdict_unexpected_success_stated",
                           "verdict_strict_xpass_stated",
                           "verdict_reason_empty",
                           # the coupling the panel-2 repair pins; see the
                           # comment where this counter is incremented.
                           "verdict_annihilated_a_location",
                           "annotation_carries_declared",
                           "annotation_carries_raised")
               if branch_hits[k] == 0]
    if vacuous:
        print("VACUOUS: modeled arms never exercised: %r (hits %r)"
              % (vacuous, branch_hits))
        print(json.dumps({"status": "fail", "reason": "vacuous input domain",
                          "never_exercised": vacuous,
                          "branch_hits": branch_hits}))
        return 1

    print("G-CONF ok: shadow of model.py impl region (finalize_skip_location) "
          "vs the REAL patched _pytest.skipping.pytest_runtest_makereport "
          "driven in-process: checked=%d inputs (structural space %d points "
          "enumerated exhaustively x boundary lines, then seeded fuzz, "
          "seed=%d), disagreements=0; correction fired %d times (incl. %d at "
          "the F2P --runxfail shape), skipped %d; %d unrealizable points "
          "excluded by invariant I1 (see docstring; I2 is refuted, its points "
          "are compared)."
          % (checked, structural_points, SEED,
             branch_hits["correction_fired"],
             branch_hits["f2p_runxfail_and_corrected"],
             branch_hits["correction_skipped"], unrealizable))
    print(json.dumps({
        "status": "pass",
        "checked": checked,
        "disagreements": 0,
        "seed": SEED,
        "oracle": "_pytest.skipping.pytest_runtest_makereport (real, called)",
        "shadow": "model.py impl-start/impl-end verbatim, contracts stripped",
        "observable": ("loc_is_triple, (loc_file, loc_line, loc_reason), "
                       "outcome, note_present, note_reason, explanation, "
                       "explanation_reason, note_style"),
        "structural_points_enumerated": structural_points,
        "unrealizable_excluded": unrealizable,
        "branch_hits": branch_hits,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
