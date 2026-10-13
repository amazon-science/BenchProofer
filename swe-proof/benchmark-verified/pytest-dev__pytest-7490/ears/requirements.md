# Requirements: Honor expected-failure markers added while a test is running

## Introduction

The pytest test runner supports an "expected failure" (xfail) annotation:
when a test carries an xfail marker, a failure of that test is reported as an
expected failure (`xfailed`) rather than as a hard failure, and — for a
non-strict xfail — an unexpected pass is reported as `xpassed`, while a strict
xfail that unexpectedly passes is reported as a failure.

A test may acquire an xfail marker in two ways: statically (a decorator on the
test) or dynamically at run time, by calling `request.node.add_marker(...)`
from inside the test body (or from a fixture during setup).

The affected module is `src/_pytest/skipping.py`, specifically the hook
functions `pytest_runtest_setup`, `pytest_runtest_call`, and
`pytest_runtest_makereport`, together with the marker-evaluation helpers
`evaluate_skip_marks` and `evaluate_xfail_marks`.

Regression: in the current behavior, an xfail marker added dynamically **from
within the test body** is not honored — such a failing test is reported as a
hard failure instead of an expected failure. This previously worked. The goal
is to restore honoring of dynamically-added xfail markers while preserving all
existing skip/xfail/strict/runxfail behavior.

The effective xfail annotation consulted when the outcome is reported must be
resolved as a most-specific-known-first cascade between what was known before
the test body ran and what is known after it ran: an annotation already
established before the body ran is authoritative; only when no annotation was
established beforehand is the after-the-body annotation consulted (which may
itself still be "no annotation").

## Requirement 1: Honor an xfail marker added during the test body

**User story:** As a test author, I want to add an xfail marker to a test from
inside the test body, so that a subsequent failure of that test is treated as
an expected failure rather than a hard failure.

**Acceptance criteria**

1. WHEN a test body adds a non-strict xfail marker to its own node and then
   the test fails, THEN the runner SHALL report that test as an expected
   failure (xfailed) and SHALL NOT report it as a hard failure.
2. The system SHALL re-derive the effective xfail annotation from the item's
   markers after the test body has run, so that a marker introduced during the
   body is observed before the outcome is reported.
3. IF an xfail annotation was already established before the test body ran,
   THEN the runner SHALL keep that earlier annotation as authoritative and
   SHALL NOT overwrite it with the after-the-body observation.
4. IF no xfail annotation was established before the test body ran, THEN the
   runner SHALL adopt whatever xfail annotation is derivable from the markers
   present after the body ran (including "no annotation").

## Requirement 2: Strict xfail added during the test body on a passing test

**User story:** As a test author, I want a strict xfail marker added at run
time to still enforce strictness, so that an unexpected pass is flagged as a
failure.

**Acceptance criteria**

1. WHEN a test body adds a strict xfail marker to its own node and the test
   then passes (does not fail), THEN the runner SHALL report that test as a
   failure.
2. The system SHALL preserve the reason, run, and strict attributes of the
   dynamically-added xfail annotation when deciding the reported outcome.

## Requirement 3: Preserve statically-marked xfail behavior

**User story:** As a test author, I want statically-declared xfail markers to
keep working exactly as before, so that existing suites are unaffected.

**Acceptance criteria**

1. WHEN a test carries a statically-declared xfail marker and the test fails,
   THEN the runner SHALL report it as an expected failure (xfailed).
2. WHEN a test carries a non-strict statically-declared xfail marker and the
   test passes, THEN the runner SHALL report it as an unexpected pass
   (xpassed).
3. WHEN a test carries a strict statically-declared xfail marker and the test
   passes, THEN the runner SHALL report it as a failure with a strict
   unexpected-pass explanation.
4. IF a statically-declared xfail marker specifies an expected exception set
   via `raises`, THEN the runner SHALL report the test as an expected failure
   only when the raised exception is an instance of that set, and SHALL report
   it as a failure otherwise.
5. IF a statically-declared xfail marker's condition evaluates to false, THEN
   the runner SHALL NOT treat a failure of that test as an expected failure.

## Requirement 4: Preserve the `runxfail` option

**User story:** As a user running with `--runxfail`, I want xfail markers to be
ignored for reporting, so that the underlying failures/passes are shown
directly.

**Acceptance criteria**

1. WHILE the `runxfail` option is enabled, the runner SHALL NOT convert a
   failing xfail-marked test into an expected failure and SHALL NOT convert a
   passing xfail-marked test into an unexpected pass; the test's real outcome
   SHALL be reported.
2. WHILE the `runxfail` option is enabled, the runner SHALL NOT short-circuit a
   test that carries an xfail marker whose run attribute is false; the test
   body SHALL be allowed to run.
3. WHILE the `runxfail` option is disabled, IF a test carries an xfail marker
   whose run attribute is false, THEN the runner SHALL skip execution of the
   test body and report it as an expected failure with a not-run indication in
   the reason.

## Requirement 5: Preserve skip and skipif behavior

**User story:** As a test author, I want skip and skipif markers to keep
behaving as before, so that skip handling is unchanged by this fix.

**Acceptance criteria**

1. WHEN a test carries a skip or a satisfied skipif marker, THEN the runner
   SHALL skip the test before its body runs and report it as skipped.
2. The system SHALL record whether a test was skipped due to a skip/skipif
   marker, and SHALL use that record when adjusting the reported failure
   location of a mark-based skip.
3. The system SHALL evaluate skip markers independently of xfail markers, so
   that establishing the skip state does not depend on the `runxfail` option.

## Requirement 6: Honor an xfail marker added during fixture setup, and not-run dynamic xfail

**User story:** As a test author, I want dynamic xfail markers added during
fixture setup to also be honored, so that setup-time and body-time dynamic
marking behave consistently.

**Acceptance criteria**

1. WHEN a fixture used by a test adds an xfail marker during setup and the test
   then fails, THEN the runner SHALL report the test as an expected failure.
2. IF a dynamically-added xfail marker specifies that the test body should not
   run, THEN the runner SHALL honor that marker when the `runxfail` option is
   disabled.
