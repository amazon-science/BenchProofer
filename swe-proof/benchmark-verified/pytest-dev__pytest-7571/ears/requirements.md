# Requirements: caplog capture-handler level is restored after each test

## Introduction

The `caplog` fixture in pytest's logging plugin (`src/_pytest/logging.py`,
class `LogCaptureFixture`) lets a test adjust log capturing via
`caplog.set_level(level, logger=None)` and the `caplog.at_level(...)` context
manager. The documented contract is that any log level set through the fixture
is restored automatically at the end of the test.

`LogCaptureFixture.set_level` changes two independent things: the level of a
named `logging` logger, and the level of the fixture's own capture handler
(the `LogCaptureHandler` exposed as `caplog.handler`). As of pytest 6.0, the
teardown finalizer (`LogCaptureFixture._finalize`) restored the logger levels
it had recorded but did **not** restore the capture handler's level. As a
result, a test that raised the handler level via `set_level` left that raised
level in place, and the next test observed a non-zero `caplog.handler.level`
instead of the fresh default.

The goal is to make the capture handler's level participate in the same
save-and-restore lifecycle as logger levels, so that the handler level a test
sees is not contaminated by a prior test, while preserving all existing
caplog capture behavior.

## Requirement 1: Restore the capture handler level after a test that raised it

**User story:** As a pytest user, I want the `caplog` capture handler's level
to be restored to what it was before my test, so that changing the capture
level in one test does not silently leak into unrelated later tests.

**Acceptance criteria**

1. The system SHALL record, on each call to `LogCaptureFixture.set_level`
   within a test, the capture handler's level as it was immediately before
   that call changes it, overwriting any value recorded by an earlier
   `set_level` call in the same test; consequently the retained recorded value
   is the capture handler's level as it was immediately before the most recent
   (last) `set_level` call of that test.
2. WHEN `LogCaptureFixture.set_level` is called during a test, THEN the
   fixture SHALL set the capture handler (`caplog.handler`) to the requested
   level for the remainder of that test's body.
3. WHEN a test that called `set_level` at least once finishes and the fixture
   is finalized, THEN the fixture SHALL restore the capture handler's level to
   the value recorded in criterion 1 (the level in effect immediately before
   the most recent `set_level` call of that test; when a test made exactly one
   `set_level` call, this is equivalently the level before that test touched
   the capture handler at all).
4. WHILE running a subsequent test that has not itself altered the capture
   level, the fixture SHALL present a capture handler whose level equals the
   value that the immediately preceding test's finalization restored per
   criterion 3 (the level recorded per criterion 1 for that preceding test);
   in particular, WHEN a preceding test raised the capture level via a single
   `set_level` call starting from the default initial capture level (numeric
   level `0`), the subsequent test SHALL observe level `0` and not that
   preceding test's raised level. The fixture does NOT guarantee the observed
   level is `0` when the preceding test made more than one `set_level` call
   (in that case the restored — and thus observed — level is the one in effect
   immediately before the preceding test's most recent `set_level` call).
5. IF a test never calls `set_level`, THEN the fixture SHALL leave the capture
   handler level restoration untouched (no recorded handler level to reapply),
   and SHALL NOT change the handler level during finalization.
6. WHEN multiple tests each independently call `set_level` exactly once with
   different levels, THEN each such test SHALL observe the default initial
   handler level at its start and its own requested level after its own
   `set_level` call, independent of the levels requested by other tests. More
   generally, the handler level a test observes at its start is the value the
   preceding test's finalization restored per criterion 3, not any raised
   level left in place by an earlier test's most recent `set_level` call.

## Requirement 2: Preserve logger-level save-and-restore behavior

**User story:** As a pytest user, I want `caplog.set_level` to keep restoring
adjusted logger levels at end of test, so that this pre-existing guarantee is
not regressed by the handler-level fix.

**Acceptance criteria**

1. WHEN `LogCaptureFixture.set_level(level, logger)` is called, THEN the
   fixture SHALL set the named logger's level to the requested level (the root
   logger when `logger` is not given).
2. The system SHALL record, on the first `set_level` for a given logger name
   within a test, that logger's level as it was before the change.
3. WHEN the test finishes and the fixture is finalized, THEN the fixture SHALL
   restore every recorded logger to the level it held before that test's first
   `set_level` for it.
4. The captured log output of a test that raised a logger's level via
   `set_level` SHALL reflect that raised level during the test, and a later
   test that did not raise it SHALL NOT observe messages that were only
   emitted because of the earlier test's raised level.

## Requirement 3: `at_level` context manager restores both levels on exit

**User story:** As a pytest user, I want `caplog.at_level(...)` to restore both
the logger level and the capture handler level when the `with` block exits, so
that temporary level changes are fully local to the block.

**Acceptance criteria**

1. WHEN execution enters a `caplog.at_level(level, logger)` block, THEN the
   fixture SHALL set both the named logger and the capture handler to the
   requested level for the duration of the block.
2. WHEN the `at_level` block exits (normally or via exception), THEN the
   fixture SHALL restore both the named logger's level and the capture
   handler's level to the values they held immediately before the block was
   entered.

## Requirement 4: Preserve existing log-capture access and control

**User story:** As a pytest user, I want the rest of the `caplog` fixture to
behave exactly as before, so that the level-restoration fix does not disturb
capturing, message access, or clearing.

**Acceptance criteria**

1. The `caplog` fixture SHALL continue to expose captured records through
   `records`, `record_tuples`, `messages`, and `text`, with `record_tuples`
   yielding `(logger_name, levelno, message)` tuples and `messages` yielding
   the interpolated messages.
2. The fixture SHALL continue to provide per-phase records via
   `get_records(when)` for the "setup", "call", and "teardown" phases.
3. WHEN `caplog.clear()` is called, THEN the fixture SHALL reset the captured
   records list and the captured log text to empty.
4. The fixture SHALL continue to honor the globally configured / ini-controlled
   capture level, and SHALL allow a test to override that global level, while
   still restoring levels at end of test per Requirements 1–3.
5. The system SHALL continue to capture log records emitted during a test even
   when that test raises an exception.
