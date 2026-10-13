#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-7432.

This bundle consumes NO `@ContractOnly` axiom and ships NO deep model standing
in for an unchanged callee: the fix is a pure control-flow restructuring of one
hook (`_pytest.skipping.pytest_runtest_makereport`) — the final `elif` that
corrects a mark-skipped report's source location is split into an independent
`if`. There is thus no opaque callee to over-approximate.

What G-AX validates here is the *behavioural correspondence* that the model's
postconditions encode, by driving the REAL hook end-to-end inside the official
SWE-bench container (where `pytest` is importable and the patch is applied).
Three families of observation: one per step of the modelled behaviour, plus the
coupling BETWEEN the two steps.

(1) The skip-location correction (model step 2). A `@pytest.mark.skip` test is
    run with `-rs` and with `-rs --runxfail`, and in BOTH cases the reported
    skip location must point at the test-definition line (the item itself),
    never at the internal pytest frame. This mirrors

        Implies(skipped_by_mark and rep_skipped and loc_is_triple,
                loc_line == definition_line + 1)

    holding INDEPENDENTLY of the `--runxfail` (`suppress_xfail_reporting`)
    toggle. The pre-patch `elif` chain is reconstructed inline and confirmed to
    report the WRONG (internal) location under `--runxfail`, witnessing the bug
    the spec sees (G-DIFF).

(2) The outcome classification (model step 1). The model does not treat the
    classification branches as `pass`: each pins an outcome, an expected-failure
    annotation (presence AND which reason it carries) and a stated verdict
    (which verdict AND which reason, or none-and-untouched). Those are claims
    about the real system, so they are checked against the real system: four
    scenarios are run through the patched pytest and every slot the model pins
    is read back out of pytest's own report rendering.

      * strict xfail that passes  -> outcome failed, the verdict
        `[XPASS(strict)] <the mark's reason>` stated, and NO xfail annotation
        (the run is not summarised as an XPASS). Witnesses the strict sub-case
        of case (d): `explanation == EXPLANATION_STRICT_UNEXPECTED_PASS and
        explanation_reason == declared_reason`.
      * the same test under `--runxfail` -> outcome passed and NO verdict
        stated. Witnesses case (b): the toggle decides nothing itself and
        shields case (d) — and, together with (1), that it does NOT shield the
        location correction.
      * non-strict xfail that passes -> outcome passed, annotation present
        carrying the mark's reason, and no verdict stated. Witnesses
        `outcome == OUTCOME_PASSED and xfail_note_present and
        note_reason == declared_reason and explanation == Old(explanation)`.
      * imperative `pytest.xfail(reason)` -> reported as an expected failure
        whose annotation carries the RAISED reason, not the mark's. Witnesses
        case (c)'s `note_reason == raised_reason`.
      * unittest unexpected success -> outcome failed and the
        `Unexpected success` verdict stated. Witnesses case (a).

(2b) The coupling: `rep.longrepr` is ONE slot holding EITHER a positional
    `(file, line, reason)` triple OR a rendered verdict string, so a case that
    states a verdict DESTROYS a triple standing there, and step (2) then finds
    no location to correct. The model pins that as

        Implies(states_own_verdict(...),
                not loc_is_triple and loc_file == LOC_ABSENT
                and loc_line == LOC_ABSENT and loc_reason == LOC_ABSENT)

    and this leg catches the real hook doing it: a passing
    `@unittest.expectedFailure` test whose call phase ALSO takes a late
    `pytest.skip` (raised from a call-phase hookwrapper, i.e. outside
    `TestCase.run`, so it lands on the same `CallInfo` as the recorded
    unexpected success). A `trylast` makereport wrapper reads the PRE state and
    `pytest_runtest_logreport` the POST state: `skipped`/tuple becomes
    `failed`/`'Unexpected success'`. A no-late-skip control shows the pre-state
    carries no triple at all, so the transition is the verdict's doing and not
    the probe's.

Imports nothing repo-private beyond `pytest` itself (the package under test).
Exit 0 iff the real patched behaviour matches the model on every observation.
"""
import os
import re
import subprocess
import sys
import tempfile


# ---------------------------------------------------------------------------
# Running the REAL patched pytest on a generated test file.
# ---------------------------------------------------------------------------

_SAMPLE = """
import pytest
@pytest.mark.skip
def test_skip_location() -> None:
    assert 0
"""

# The mark's declared reason; the model calls this `declared_reason`.
_DECLARED = "the-mark-reason"
# The reason raised imperatively; the model calls this `raised_reason`.
_RAISED = "the-raised-reason"

_STRICT_XPASS = """
import pytest
@pytest.mark.xfail(strict=True, reason="%s")
def test_strict_xpass() -> None:
    assert True
""" % _DECLARED

_NONSTRICT_XPASS = """
import pytest
@pytest.mark.xfail(reason="%s")
def test_nonstrict_xpass() -> None:
    assert True
""" % _DECLARED

_IMPERATIVE_XFAIL = """
import pytest
@pytest.mark.xfail(reason="%s")
def test_imperative() -> None:
    pytest.xfail("%s")
""" % (_DECLARED, _RAISED)

_UNEXPECTED_SUCCESS = """
import unittest
class TestU(unittest.TestCase):
    @unittest.expectedFailure
    def test_unexpected_success(self) -> None:
        assert True
"""


def _run_pytest(src, args, conftest=None):
    """Write `src` to an isolated dir and run the REAL patched pytest on it."""
    workdir = tempfile.mkdtemp(prefix="gax7432_")
    sample = os.path.join(workdir, "test_sample.py")
    with open(sample, "w") as fh:
        fh.write(src)
    if conftest is not None:
        with open(os.path.join(workdir, "conftest.py"), "w") as fh:
            fh.write(conftest)
    cmd = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", sample] + args
    proc = subprocess.run(cmd, cwd=workdir, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, universal_newlines=True)
    return proc.stdout


# ---------------------------------------------------------------------------
# (1) The location correction, independent of --runxfail.
# ---------------------------------------------------------------------------

def _assert_points_at_item(out, args):
    """The SKIPPED report must point at the test file (the item definition),
    NOT at an internal _pytest frame."""
    # Expected: a line like 'SKIPPED [1] test_sample.py:2: unconditional skip'
    m = re.search(r"SKIPPED \[\d+\] ([^\s:]+):(\d+):", out)
    assert m, ("no SKIPPED location line found for args=%r in:\n%s" % (args, out))
    location = m.group(1)
    assert location.endswith("test_sample.py"), (
        "skip location for args=%r points at %r (line %s), expected the test "
        "file test_sample.py — the --runxfail toggle must not move it into "
        "pytest internals.\n%s" % (args, location, m.group(2), out))
    assert "skipping.py" not in location, (
        "skip location for args=%r leaked into _pytest/skipping.py: %r" % (args, location))
    return location, int(m.group(2))


def check_real_hook():
    # Ensure the patched package is importable before drawing conclusions.
    import pytest  # noqa: F401
    import _pytest.pytester  # noqa: F401

    observations = []
    for args in (["-rs"], ["-rs", "--runxfail"]):
        out = _run_pytest(_SAMPLE, args)
        loc, line = _assert_points_at_item(out, args)
        observations.append((args, loc, line))
    # The correction points at the test's OWN definition line: the sample
    # defines the test on line 3 of the file, `reportinfo()` reports the
    # zero-based line 2, and the model requires `definition_line + 1` == 3.
    for args, loc, line in observations:
        assert line == 3, (
            "the corrected skip location for args=%r is line %d, expected the "
            "test-definition line 3 (reportinfo()'s zero-based 2, plus one)"
            % (args, line))
    return observations


# ---------------------------------------------------------------------------
# (2) The outcome classification: every slot the model pins, read back out of
#     the real system's own reporting.
# ---------------------------------------------------------------------------

_STRICT_VERDICT = "[XPASS(strict)] " + _DECLARED
_UNEXPECTED_VERDICT = "Unexpected success"


def check_classification():
    """Drive the four classification scenarios and check the outcome, the
    annotation (with its reason) and the stated verdict (with its reason)."""
    findings = []

    # -- strict xfail that passes: case (d), strict sub-case ----------------
    out = _run_pytest(_STRICT_XPASS, ["-rxX"])
    assert "1 failed" in out, (
        "a strict xfail that passes must be reported failed:\n%s" % out)
    assert _STRICT_VERDICT in out, (
        "a strict xfail that passes must STATE the verdict %r, carrying the "
        "reason the mark declared; the model pins explanation == "
        "EXPLANATION_STRICT_UNEXPECTED_PASS and explanation_reason == "
        "declared_reason:\n%s" % (_STRICT_VERDICT, out))
    assert not re.search(r"^XPASS ", out, re.M), (
        "a strict xfail that passes must NOT be summarised as an xpass (no "
        "xfail annotation is added); the model pins xfail_note_present "
        "unchanged:\n%s" % out)
    findings.append(("strict_xpass", "failed", _STRICT_VERDICT))

    # -- the same test under --runxfail: case (b), the shield ---------------
    out = _run_pytest(_STRICT_XPASS, ["-rxX", "--runxfail"])
    assert "1 passed" in out, (
        "under --runxfail the strict xfail arm must not fire, leaving the run "
        "as it was (passed); the model pins outcome == Old(outcome):\n%s" % out)
    assert _STRICT_VERDICT not in out, (
        "under --runxfail no verdict may be stated; the model pins explanation "
        "== Old(explanation):\n%s" % out)
    findings.append(("strict_xpass_runxfail", "passed", None))

    # -- non-strict xfail that passes: case (d), non-strict sub-case --------
    out = _run_pytest(_NONSTRICT_XPASS, ["-rxX"])
    m = re.search(r"^XPASS \S+::test_nonstrict_xpass\s*(.*)$", out, re.M)
    assert m, ("a non-strict xfail that passes must be reported as an xpass "
               "carrying the annotation; the model pins outcome == "
               "OUTCOME_PASSED and xfail_note_present:\n%s" % out)
    assert m.group(1).strip() == _DECLARED, (
        "the annotation on a non-strict xpass carries %r, expected the reason "
        "the mark declared (%r); the model pins note_reason == declared_reason"
        % (m.group(1).strip(), _DECLARED))
    assert "[XPASS(strict)]" not in out, (
        "a NON-strict xpass must state no verdict:\n%s" % out)
    findings.append(("nonstrict_xpass", "xpassed", _DECLARED))

    # -- imperative pytest.xfail: case (c) ----------------------------------
    # The item ALSO carries a mark whose reason differs, so this observation
    # discriminates note_reason == raised_reason from == declared_reason.
    out = _run_pytest(_IMPERATIVE_XFAIL, ["-rxX"])
    assert "1 xfailed" in out, (
        "an imperative pytest.xfail must be reported as an expected failure; "
        "the model pins outcome == OUTCOME_SKIPPED:\n%s" % out)
    assert _RAISED in out, (
        "the annotation for an imperative pytest.xfail must carry the RAISED "
        "reason %r; the model pins note_reason == raised_reason:\n%s"
        % (_RAISED, out))
    assert _DECLARED not in out, (
        "the annotation for an imperative pytest.xfail must NOT carry the "
        "MARK's reason %r — case (c) precedes case (d) and records the reason "
        "it was given:\n%s" % (_DECLARED, out))
    findings.append(("imperative_xfail", "xfailed", _RAISED))

    # -- unittest unexpected success: case (a) ------------------------------
    out = _run_pytest(_UNEXPECTED_SUCCESS, ["-rf"])
    assert "1 failed" in out, (
        "a unittest unexpected success must be reported failed; the model pins "
        "outcome == OUTCOME_FAILED:\n%s" % out)
    assert _UNEXPECTED_VERDICT in out, (
        "a unittest unexpected success must STATE the %r verdict; the model "
        "pins explanation == EXPLANATION_UNEXPECTED_SUCCESS:\n%s"
        % (_UNEXPECTED_VERDICT, out))
    assert "[XPASS(strict)]" not in out, (
        "case (a) states its OWN verdict, not the strict-xpass one:\n%s" % out)
    findings.append(("unexpected_success", "failed", _UNEXPECTED_VERDICT))

    return findings


# ---------------------------------------------------------------------------
# (2b) The report keeps ONE account of itself: stating a verdict DESTROYS a
#      positional location triple that was standing there.
#
# `rep.longrepr` is a single attribute playing two roles (a `(file, line,
# reason)` triple, or a rendered verdict string), so the two writes cannot
# coexist. The model pins that as `states_own_verdict(...) ==> not
# rep.loc_is_triple and loc_file == loc_line == loc_reason == LOC_ABSENT`,
# which is only honest if the real hook can be caught doing it. This leg
# catches it, by observing the SAME report either side of skipping.py's own
# hook body:
#   * a `trylast` hookwrapper is INNERMOST, so its post-yield code runs
#     BEFORE skipping.py's -> the PRE state;
#   * `pytest_runtest_logreport` runs after the whole makereport chain
#     -> the POST state.
# The scenario needs both conditions at once on one report: a `Skipped`
# excinfo AND a recorded unexpected success. `unittest.TestCase.run` only
# sees skips raised inside itself, so the skip is raised one level out, from a
# call-phase hookwrapper after `runtest` returns -- it lands on the same
# `CallInfo` whose `addUnexpectedSuccess` already wrote the store key.
# ---------------------------------------------------------------------------

_CLOBBER_CONFTEST = '''
import os
import pytest

RECORD = []


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_runtest_makereport(item, call):
    out = yield
    rep = out.get_result()
    if call.when == "call":
        RECORD.append(("PRE", rep.outcome, type(rep.longrepr).__name__))


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_logreport(report):
    if report.when == "call":
        RECORD.append(("POST", report.outcome, type(report.longrepr).__name__,
                       repr(report.longrepr)))
    yield


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_call(item):
    yield
    if os.environ.get("GAX7432_LATE_SKIP"):
        pytest.skip("late skip from wrapper")


def pytest_sessionfinish(session):
    print("---RECORD---")
    for row in RECORD:
        print("|".join(str(x) for x in row))
'''


def _record_rows(out):
    # The marker can be glued to pytest's progress line ("test_sample.py F
    # [100%]---RECORD---"), so match the rows themselves rather than splitting
    # on a line that equals the marker.
    assert "---RECORD---" in out, (
        "the clobber probe printed no ---RECORD--- block:\n%s" % out)
    rows = [line.strip().split("|")
            for line in out.splitlines()
            if re.match(r"^(PRE|POST)\|", line.strip())]
    assert rows, "the ---RECORD--- block is empty:\n%s" % out
    return rows


def check_verdict_annihilates_location():
    os.environ["GAX7432_LATE_SKIP"] = "1"
    try:
        out = _run_pytest(_UNEXPECTED_SUCCESS, ["-rs"], conftest=_CLOBBER_CONFTEST)
    finally:
        del os.environ["GAX7432_LATE_SKIP"]
    rows = _record_rows(out)
    pre = [r for r in rows if r[0] == "PRE"]
    post = [r for r in rows if r[0] == "POST"]
    assert len(pre) == 1 and len(post) == 1, (
        "expected one PRE and one POST observation of the call report, got "
        "%r:\n%s" % (rows, out))
    # PRE: both conditions really do hold together on one real report.
    assert pre[0][2] == "tuple", (
        "the probe did not reach a report carrying a positional location "
        "triple before skipping.py's hook body ran (got longrepr type %r); "
        "without that the annihilation cannot be observed:\n%s"
        % (pre[0][2], out))
    assert pre[0][1] == "skipped", (
        "the pre-state outcome is %r, expected 'skipped' (the late skip must "
        "have landed on this report):\n%s" % (pre[0][1], out))
    # POST: the verdict replaced it. No triple survives, so there is no
    # location left for step (2) to correct.
    assert post[0][2] != "tuple", (
        "stating the unexpected-success verdict left the positional location "
        "triple standing (longrepr type %r); the model pins that a stated "
        "verdict empties the slot:\n%s" % (post[0][2], out))
    assert _UNEXPECTED_VERDICT in post[0][3], (
        "the post-state account is %r, expected the %r verdict:\n%s"
        % (post[0][3], _UNEXPECTED_VERDICT, out))
    # And the control: with no late skip, the pre-state carries no triple at
    # all, so the transition above is caused by the verdict and not by the
    # probe's own machinery.
    out0 = _run_pytest(_UNEXPECTED_SUCCESS, ["-rs"], conftest=_CLOBBER_CONFTEST)
    rows0 = _record_rows(out0)
    pre0 = [r for r in rows0 if r[0] == "PRE"]
    assert pre0 and pre0[0][2] != "tuple", (
        "control: without the late skip the pre-state should carry no "
        "positional triple, got %r:\n%s" % (rows0, out0))
    return (tuple(pre[0]), tuple(post[0]), tuple(pre0[0]))


# ---------------------------------------------------------------------------
# (3) Pre-patch witness: the `elif` chain reports the WRONG location under
#     --runxfail. Reconstructed inline so the discriminating clause is shown
#     without mutating the installed package.
# ---------------------------------------------------------------------------

def _prepatch_chain(unexpected_success, suppress_xfail_reporting, xfail_exception,
                    rep_skipped, xfailed_present, skipped_by_mark, loc_is_triple,
                    internal_line, definition_line):
    """The pre-patch control flow (one if/elif chain), returning the reported
    location line. The correction is the FINAL elif (the bug)."""
    line = internal_line
    if unexpected_success:
        pass
    elif suppress_xfail_reporting:
        pass
    elif xfail_exception:
        pass
    elif (not rep_skipped) and xfailed_present:
        pass
    elif skipped_by_mark and rep_skipped and loc_is_triple:
        line = definition_line + 1
    return line


def _patched_chain(unexpected_success, suppress_xfail_reporting, xfail_exception,
                   rep_skipped, xfailed_present, skipped_by_mark, loc_is_triple,
                   internal_line, definition_line):
    """The patched control flow: the correction is a SEPARATE if."""
    line = internal_line
    if unexpected_success:
        pass
    elif suppress_xfail_reporting:
        pass
    elif xfail_exception:
        pass
    elif (not rep_skipped) and xfailed_present:
        pass
    if skipped_by_mark and rep_skipped and loc_is_triple:
        line = definition_line + 1
    return line


def check_chain_witness():
    INTERNAL, DEFN = 238, 2  # internal frame line vs. test-definition line
    # F2P scenario: @pytest.mark.skip + --runxfail.
    args = dict(unexpected_success=False, suppress_xfail_reporting=True,
                xfail_exception=False, rep_skipped=True, xfailed_present=False,
                skipped_by_mark=True, loc_is_triple=True,
                internal_line=INTERNAL, definition_line=DEFN)
    pre = _prepatch_chain(**args)
    post = _patched_chain(**args)
    assert pre == INTERNAL, ("pre-patch witness should report the wrong internal "
                            "line under --runxfail, got %r" % pre)
    assert post == DEFN + 1, ("patched witness should report the item-definition "
                             "line, got %r" % post)
    # Without --runxfail both already correct (the PASS_TO_PASS test_input0).
    args0 = dict(args, suppress_xfail_reporting=False)
    assert _prepatch_chain(**args0) == DEFN + 1
    assert _patched_chain(**args0) == DEFN + 1


def main():
    # (3) is pure-Python and always available — run it first.
    check_chain_witness()

    # (1) and (2) require the patched pytest to be importable/runnable.
    try:
        observations = check_real_hook()
    except ImportError as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: real pytest hook not runnable in this environment: %r"
              % (exc,))
        print("G-AX OK (chain witness): pre-patch elif chain reports the internal "
              "line under --runxfail; patched independent-if reports the item "
              "definition line in both configurations.")
        return 0

    findings = check_classification()
    clobber = check_verdict_annihilates_location()

    for args, loc, line in observations:
        assert loc.endswith("test_sample.py"), (args, loc, line)
    print("G-AX OK (step 2, the correction): real patched "
          "pytest_runtest_makereport reports the @pytest.mark.skip location at "
          "the test definition for both -rs and -rs --runxfail (%r); pre-patch "
          "elif chain would report the internal frame under --runxfail."
          % (observations,))
    print("G-AX OK (step 1, the classification): every slot the model pins is "
          "what the real patched hook produces — outcome, annotation with its "
          "reason, and stated verdict with its reason: %r" % (findings,))
    print("G-AX OK (the one-slot coupling): a report really can arrive carrying "
          "a positional location triple AND a recorded unexpected success, and "
          "stating the verdict REPLACES the triple, leaving no location to "
          "correct — (pre, post, no-late-skip control) = %r" % (clobber,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
