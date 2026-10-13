# Requirements: Skipped unittest tests must not run teardown under the debugger option

## Introduction

The framework's `unittest`-style test integration lives in
`src/_pytest/unittest.py`, which adapts `unittest.TestCase` subclasses so they
can be collected and executed by the test runner. When a test case is run with
the interactive post-mortem debugger option enabled (the `--pdb` command-line
option, exposed as the `usepdb` config option), the runner postpones the test
case's `tearDown` so that instance state survives long enough for the debugger
prompt to be useful after a failure. It does this by stashing the bound
`tearDown` method and temporarily replacing `tearDown` on the test-case instance
with a no-op, then invoking the stashed method explicitly during the item's own
teardown step.

A regression made this postponement unconditional whenever the debugger option
was active. As a result, a test case that was marked to be skipped (via
`unittest`'s skip machinery, i.e. the `__unittest_skip__` marker set by
`@unittest.skip` and friends) still had its `tearDown` — and, symptomatically,
its `setUp` — executed when run with `--pdb`, even though a skipped test must not
run either of those fixtures. Without the debugger option the same test was
correctly skipped.

The goal is to ensure that skipped `unittest` test cases are treated as skipped
regardless of the debugger option: their `setUp`/`tearDown` must not run, and
they must be reported as skipped rather than erroring. This must not weaken the
existing debugger behavior for non-skipped tests, nor change any other skip,
setup, or teardown behavior. The behavior modeled here concerns the decision, in
`UnitTestCase`/`TestCaseFunction` within `src/_pytest/unittest.py`, of whether
teardown postponement is arranged for a given test case.

## Requirement 1: Do not run teardown/setup for a skipped unittest test under `--pdb`

**User story:** As a developer running my `unittest` suite with `--pdb`, I want
tests I have marked to skip to remain skipped and their `setUp`/`tearDown` to be
left uncalled, so that the debugger option does not turn a clean skip into a
spurious error from teardown code.

**Acceptance criteria**

1. WHEN a `unittest.TestCase` method has been marked to skip and the run is
   invoked with the interactive-debugger option active, THEN the framework SHALL
   report that test case as skipped and SHALL NOT report it as an error or
   failure.
2. WHEN a `unittest.TestCase` method has been marked to skip and the run is
   invoked with the interactive-debugger option active, THEN the framework SHALL
   NOT invoke the test case's `setUp` method.
3. WHEN a `unittest.TestCase` method has been marked to skip and the run is
   invoked with the interactive-debugger option active, THEN the framework SHALL
   NOT invoke the test case's `tearDown` method, either immediately or by a
   later explicit call.
4. WHEN deciding whether to postpone (stash-and-replace) a test case's
   `tearDown` because the interactive-debugger option is active, THEN the
   framework SHALL arrange that postponement only for a test case that has NOT
   been marked to skip.
5. The system SHALL determine whether a test case (or its class) has been marked
   to skip from the `unittest` skip marker (`__unittest_skip__`) present on the
   underlying test object.

## Requirement 2: Skip handling depends only on the skip marker, not how it was applied

**User story:** As a developer, I want a `unittest.TestCase` test's behavior
under `--pdb` to depend solely on whether its underlying object carries the
`unittest` skip marker, so that whatever API or decorator set that marker
produces identical teardown behavior.

**Acceptance criteria**

1. WHEN a `unittest.TestCase` test whose underlying object carries the
   `unittest` skip marker (`__unittest_skip__`), irrespective of which decorator
   or marker API set that marker, is run with the interactive-debugger option
   active, THEN the framework SHALL report it as skipped and SHALL leave both
   `setUp` and `tearDown` uncalled.
2. The system SHALL make the skip-versus-run and teardown-postponement decisions
   solely from the presence of the `__unittest_skip__` marker on the underlying
   object, and SHALL NOT vary that decision based on the particular mechanism
   used to mark the test as skipped.

## Requirement 3: Preserve teardown postponement for non-skipped tests under `--pdb`

**User story:** As a developer debugging a failing `unittest` test, I want its
`tearDown` to still be deferred until after the debugger prompt, so that the
instance state I need is not cleaned up before I can inspect it.

**Acceptance criteria**

1. WHEN a non-skipped, synchronous `unittest.TestCase` test is run with the
   interactive-debugger option active, THEN the framework SHALL postpone the
   test case's `tearDown` (replacing it with a no-op during the test body) and
   SHALL invoke the real `tearDown` explicitly during the item's own teardown
   step.
2. WHEN a non-skipped `unittest.TestCase` test is run WITHOUT the
   interactive-debugger option, THEN the framework SHALL invoke `tearDown` in
   its normal position and SHALL NOT arrange any postponement.
3. IF a test case is driven by the asynchronous execution path, THEN the
   framework SHALL NOT arrange teardown postponement for it.

## Requirement 4: Preserve existing skip, collection, setup, and teardown behavior

**User story:** As a maintainer, I want all previously working `unittest`
integration behavior to be unchanged, so that this fix does not regress
collection, fixtures, skips, or reporting.

**Acceptance criteria**

1. WHEN a `unittest.TestCase` class itself is marked to skip, THEN the framework
   SHALL skip injecting its setup/teardown fixtures and SHALL still report the
   class's tests as skipped.
2. WHEN a `unittest.TestCase` is not marked to skip, THEN the framework SHALL
   inject its setup/teardown and setup-class fixtures and SHALL run `setUp` and
   `tearDown` as before.
3. The system SHALL continue to collect and run ordinary `unittest.TestCase`
   subclasses, including classes exposing only a `runTest` method, exactly as
   before.
4. The system SHALL continue to honor skips raised at runtime, expected
   failures, and the existing setup/teardown, setUpClass/tearDownClass, and
   setUpModule/tearDownModule interactions without change.
5. The system SHALL continue to report `setUp`/`tearDown` failures, errors, and
   tracebacks for non-skipped tests as before, including deferring the explicit
   teardown call for non-skipped tests run under the interactive-debugger
   option.
