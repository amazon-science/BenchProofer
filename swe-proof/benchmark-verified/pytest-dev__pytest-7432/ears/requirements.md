# Requirements: correct skip-location reporting under `--runxfail`

## Introduction

When a test is skipped by a skip mark (`@pytest.mark.skip` or
`@pytest.mark.skipif`), pytest reports a short-test-summary line (enabled with
`-rs`) that should point at the *test's own definition* — e.g. the file and line
of the decorated test function — rather than at the internal framework site where
the skip signal was raised.

This location correction is performed in the report post-processing hook
`pytest_runtest_makereport` in `src/_pytest/skipping.py`. In the affected
version, that correction was chained as the final alternative of the hook's
expected-failure dispatch (the sequence of mutually exclusive branches that
handle unexpected successes, the `--runxfail` option, raised xfail signals, and
xfail-marked results). Because the `--runxfail` option is handled by an earlier
branch in that same chain, enabling `--runxfail` caused the skip-location
correction to be skipped entirely — so mark-skipped tests reported their location
as an internal path inside `src/_pytest/skipping.py` instead of the test's own
file. `--runxfail` is documented to affect only xfail handling and must not
change how skips are reported.

The goal is to make the skip-location correction an **independent** decision that
is evaluated for every reported result, so it fires whenever the result is a
mark-skipped result with a structured location, regardless of which
expected-failure branch (if any) was taken — while leaving all existing
xfail/skip outcome behavior unchanged.

## Requirement 1: Skip-mark location reporting is independent of `--runxfail`

**User story:** As a pytest user who runs my suite with `--runxfail`, I want
tests skipped by a skip mark to still report their own source location in the
skip summary, so that the `--runxfail` option does not corrupt unrelated skip
reporting.

**Acceptance criteria**
1. WHEN a test is skipped by a skip mark and the run also enables `--runxfail`
   and short-summary skip reporting (`-rs`), THEN the reported skip location
   SHALL point at the location of the test item's own definition (the test's file
   and line), not at a location inside `src/_pytest/skipping.py` or any other
   internal framework module.
2. The system SHALL treat the skip-location correction performed in
   `pytest_runtest_makereport` as an independent decision that is evaluated for
   every reported result, regardless of whether any expected-failure branch
   (unexpected-success handling, the `--runxfail` branch, raised-xfail handling,
   or xfail-mark handling) was taken for that result.
3. IF a reported result was skipped by a skip mark, its recorded outcome is
   "skipped", and its recorded location is the structured triple form
   (file name, line, reason), THEN the hook SHALL rewrite the recorded location
   so that its file and line identify the test item's own definition while
   preserving the original skip reason text.
4. IF the reported result does not satisfy all three of those conditions (skipped
   by a skip mark, outcome "skipped", structured-triple location), THEN the hook
   SHALL leave the recorded location unchanged.

## Requirement 2: Skip-mark location reporting without `--runxfail` (kept behavior)

**User story:** As a pytest user, I want a mark-skipped test to report its own
source location in the skip summary in an ordinary run, so that existing correct
behavior is preserved.

**Acceptance criteria**
1. WHEN a test is skipped by a skip mark and short-summary skip reporting (`-rs`)
   is enabled without `--runxfail`, THEN the reported skip location SHALL point
   at the location of the test item's own definition.
2. The system SHALL produce the same corrected skip location for a mark-skipped
   test whether or not `--runxfail` is enabled; enabling `--runxfail` SHALL NOT
   change the reported skip location.
3. WHEN a mark-skipped test is reported, THEN the reported skip reason text SHALL
   be identical to the reason it would report without `--runxfail`.

## Requirement 3: `--runxfail` continues to affect only xfail handling (kept behavior)

**User story:** As a pytest user, I want `--runxfail` to keep its documented
effect on expected-failure tests only, so that its behavior is unchanged apart
from no longer corrupting skip reporting.

**Acceptance criteria**
1. WHILE `--runxfail` is enabled, the system SHALL still run xfail-marked tests
   normally and report their real pass/fail outcome instead of converting them to
   xfailed/xpassed.
2. The system SHALL NOT alter, suppress, or add any effect of `--runxfail` on
   expected-failure handling beyond the pre-existing behavior; the only change is
   that `--runxfail` no longer suppresses the skip-location correction.
3. WHEN `--runxfail` is enabled and a test is skipped by a skip mark (not an xfail
   mark), THEN the system SHALL report it as skipped exactly as it would without
   `--runxfail`.

## Requirement 4: Expected-failure dispatch outcomes are preserved (kept behavior)

**User story:** As a pytest maintainer, I want all existing expected-failure and
skip outcome behavior to remain intact, so that decoupling the skip-location
correction does not regress any reporting.

**Acceptance criteria**
1. The system SHALL continue to report an xfail-marked test that fails as an
   expected failure (xfailed) and one that unexpectedly passes as xpassed, with
   the existing reason text.
2. IF an xfail mark is strict and the test unexpectedly passes, THEN the system
   SHALL report it as a failure with the existing strict-xpass explanation.
3. IF an xfail mark specifies an expected raised exception type, THEN the system
   SHALL report the test as an expected failure only when the raised exception
   matches, and as a failure otherwise.
4. The system SHALL continue to honor imperatively raised xfail signals during a
   test, reporting the result as an expected failure with the given reason.
5. WHEN an unexpected success is recorded on the call phase, THEN the system SHALL
   continue to report it as a failure with the existing unexpected-success
   message.
6. The system SHALL keep the existing reporting of `skipif` conditions,
   unconditional skips, skip reasons, skip folding/summarization, and the
   report-character (`-r`) selection of which outcomes are summarized.

## Requirement 5: No change to how the corrected location is computed (kept behavior)

**User story:** As a pytest maintainer, I want the computation of the corrected
skip location to be unchanged, so that only the decision of *when* it is applied
is modified.

**Acceptance criteria**
1. The system SHALL derive the corrected location from the test item's own
   reported definition information, unchanged from before.
2. The system SHALL preserve the reason component of the structured location when
   applying the correction, replacing only the file and line components.
