# Requirements: skip teardown for class-level skipped unittest TestCases under --pdb

## Introduction

pytest integrates `unittest.TestCase` classes through `src/_pytest/unittest.py`.
When the `--pdb` option is active, pytest postpones a test case's `tearDown()`
call so that, if the test fails, the instance state is still available at the
post-mortem debugger prompt. To avoid running teardown code for tests that are
never actually executed, pytest already suppresses this postponed `tearDown()`
for tests skipped by a decorator on the **test method**.

The defect: a `unittest.TestCase` **class** decorated with a skip marker (for
example `unittest.skip` applied at the class level) is reported as skipped when
run normally, but under `--pdb` its `setUp()`/`tearDown()` are still invoked,
causing spurious errors and an unexpected post-mortem debugger session. This is
the same problem previously fixed for method-level skips, now occurring for
class-level skips.

The goal is to make the `--pdb` teardown-postponement logic in the
`TestCaseFunction.runtest` path (module `src/_pytest/unittest.py`) consider skip
markers on the **enclosing test-case class** in addition to the test method, so
that no user `setUp`/`tearDown` code runs for a skipped class, while preserving
existing behavior for non-skipped tests and for method-level skips.

The affected code path is the branch that, when the `usepdb` option is enabled,
replaces the test case instance's `tearDown` with a no-op and stores the
original for later explicit invocation. The skip detection relies on the
`__unittest_skip__` attribute set by skip decorators (checked by the module's
`_is_skipped` helper).

## Requirement 1: Do not run teardown for class-level skipped TestCases under --pdb

**User story:** As a developer running my unittest suite with `pytest --pdb`, I
want a `TestCase` class decorated to be skipped to be fully skipped, so that its
`setUp`/`tearDown` code does not execute and no debugger prompt is triggered for
a test that should never run.

**Acceptance criteria**

1. WHEN a `unittest.TestCase` subclass is marked as skipped at the class level
   (via a decorator that sets the unittest skip marker on the class) and the
   suite is run with the `--pdb` option enabled, THEN pytest SHALL NOT invoke
   that test case's user-defined `setUp` or `tearDown` methods.
2. WHEN such a class-level-skipped test case is collected and run under `--pdb`,
   THEN pytest SHALL report the test as skipped and SHALL NOT report it as an
   error or failure.
3. WHEN running a class-level-skipped test case under `--pdb`, THEN pytest SHALL
   NOT enter the post-mortem debugger for that test.
4. IF the enclosing test-case class carries the unittest skip marker, THEN the
   teardown-postponement branch in the runtest path SHALL treat the test as
   skipped and SHALL NOT replace the instance's `tearDown` with a deferred/no-op
   substitute that would later be explicitly invoked.
5. The behavior described SHALL hold regardless of whether the class-level skip
   originates from the unittest skip decorator or from pytest's own skip marker
   applied to the class.

## Requirement 2: Preserve method-level skip behavior under --pdb

**User story:** As a developer, I want method-level skipped unittest tests to
keep behaving correctly under `--pdb`, so that fixing the class-level case does
not regress the already-working method-level case.

**Acceptance criteria**

1. WHEN an individual test method of a `unittest.TestCase` is marked as skipped
   (via a decorator setting the unittest skip marker on the method) and the
   suite runs with `--pdb`, THEN pytest SHALL NOT invoke that test's
   `setUp`/`tearDown` and SHALL report the test as skipped.
2. The system SHALL apply this method-level suppression whether the skip comes
   from the unittest skip decorator or from pytest's skip marker on the method.

## Requirement 3: Preserve teardown execution for non-skipped tests under --pdb

**User story:** As a developer debugging a failing unittest test with `--pdb`, I
want `tearDown` to still run (after the debugger) for tests that are not
skipped, so that class-level skip handling does not disable normal teardown.

**Acceptance criteria**

1. WHEN a `unittest.TestCase` test that is not skipped at either the method or
   class level runs with `--pdb`, THEN pytest SHALL still ensure the test's
   `tearDown` is ultimately executed (postponed so that instance state remains
   available at the debugger prompt on failure), keeping the existing `--pdb`
   teardown behavior.
2. The system SHALL keep the normal (non-`--pdb`) execution of `setUp` and
   `tearDown` unchanged for all non-skipped unittest tests.

## Requirement 4: Preserve normal skip reporting

**User story:** As a developer, I want skipped unittest tests (method- or
class-level) to be reported as skipped during ordinary runs, so that skip
semantics are unchanged outside of `--pdb`.

**Acceptance criteria**

1. WHEN a `unittest.TestCase` class or method marked as skipped is run without
   `--pdb`, THEN pytest SHALL report the affected test(s) as skipped and SHALL
   NOT execute their `setUp`/`tearDown` bodies.
2. The system SHALL continue to detect the unittest skip marker
   (`__unittest_skip__`) on both classes and methods when determining skip
   status.
