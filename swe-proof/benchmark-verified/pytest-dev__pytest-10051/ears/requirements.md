# Requirements: keep `caplog.get_records()` consistent with `caplog.records` after `caplog.clear()`

## Introduction

pytest's `caplog` fixture (`LogCaptureFixture` in `src/_pytest/logging.py`)
exposes captured log records two ways during a test:

- `caplog.records` — the live list of records captured for the current phase,
  backed by the capture handler (`LogCaptureHandler`, whose `records`
  attribute the property returns).
- `caplog.get_records(when)` — the records captured for a named test phase
  (`"setup"`, `"call"`, `"teardown"`), read from a per-phase mapping stored on
  the test item's stash under `caplog_records_key`.

At the start of each phase the framework stores the handler's current `records`
list object into that per-phase mapping, so during the "call" phase
`caplog.get_records("call")` and `caplog.records` are the *same* list object and
compare equal.

The defect: `caplog.clear()` delegates to the handler, which *replaces* its
`records` attribute with a brand-new empty list (via its `reset()` path) instead
of emptying the existing list in place. The per-phase mapping still references
the original list object, so after `clear()` the two views diverge:
`caplog.get_records("call")` keeps pointing at the old, now-orphaned list — it
neither reflects the clear nor receives records logged afterwards, while
`caplog.records` tracks the new list.

Goal: make `caplog.clear()` empty the captured records without detaching the
per-phase views onto them, so `get_records(<current phase>)` stays coupled to
`caplog.records` across a clear and through subsequent logging — without
disturbing other phases' records or any other capture behavior.

## Requirement 1: Clearing empties records without detaching the per-phase view

**User story:** As a test author, I want `caplog.clear()` to reset the captured
records while keeping `caplog.get_records()` for the current phase in sync with
`caplog.records`, so that assertions comparing the two remain valid before and
after a clear.

**Acceptance criteria**

1. The system SHALL preserve the invariant that, during the "call" phase and
   before any clear, `caplog.get_records("call")` and `caplog.records` are equal.
2. WHEN `caplog.clear()` is called during the "call" phase, THEN
   `caplog.records` SHALL become empty.
3. WHEN `caplog.clear()` is called during the "call" phase, THEN
   `caplog.get_records("call")` SHALL become empty (equal to an empty list).
4. WHEN `caplog.clear()` is called, THEN `caplog.get_records(<current phase>)`
   and `caplog.records` SHALL still refer to the same underlying record
   collection, so they SHALL remain equal.
5. WHEN a log message is emitted after `caplog.clear()` during the "call"
   phase, THEN both `caplog.records` and `caplog.get_records("call")` SHALL
   contain that newly emitted record.
6. WHILE the current phase is "call", after a clear followed by further logging,
   `caplog.get_records("call")` SHALL reflect exactly the records emitted since
   the clear, in emission order, and SHALL NOT contain any record captured
   before the clear.

## Requirement 2: Clearing must not affect other phases' captured records

**User story:** As a test author, I want clearing during one phase to leave the
records captured in other phases untouched, so that setup/teardown log records
remain available.

**Acceptance criteria**

1. WHEN `caplog.clear()` is called during the "call" phase, THEN the records
   returned by `caplog.get_records("setup")` SHALL be unchanged (the same
   records, in the same order, as before the clear).
2. The system SHALL keep the set of phase names tracked for the item
   (the keys of the per-phase records mapping) unchanged across a `caplog.clear()`
   call.
3. IF records were captured in a phase other than the current one, THEN
   `caplog.clear()` SHALL NOT remove or alter those records.

## Requirement 3: Preserve existing clear semantics for text and records list

**User story:** As a test author relying on the documented behavior of
`caplog.clear()`, I want it to keep resetting both the record list and the
captured log text, so that existing usage continues to work.

**Acceptance criteria**

1. WHEN `caplog.clear()` is called, THEN `caplog.records` SHALL be emptied.
2. WHEN `caplog.clear()` is called, THEN the captured log text (`caplog.text`)
   SHALL be reset to empty.
3. WHEN new messages are logged after `caplog.clear()`, THEN `caplog.records`,
   `caplog.record_tuples`, and `caplog.messages` SHALL reflect those new
   messages and no messages captured before the clear.

## Requirement 4: Preserve all other caplog capture and level behavior

**User story:** As a pytest user, I want the log-capture fixture's other
behaviors to be unaffected by this change, so that no existing functionality
regresses.

**Acceptance criteria**

1. The system SHALL continue to capture log records emitted during a test into
   `caplog.records`, and expose them via `caplog.record_tuples`,
   `caplog.messages`, and `caplog.text`.
2. The system SHALL continue to record log entries separately per test phase and
   make each phase's records available through `caplog.get_records(when)` for
   `"setup"`, `"call"`, and `"teardown"`.
3. The system SHALL keep `caplog.set_level(...)` and `caplog.at_level(...)`
   working as before, including restoring logger and handler levels at the end
   of the test.
4. WHEN a log-record emission fails (an emit error) while `logging.raiseExceptions`
   is enabled, THEN the capture handler SHALL surface the error rather than
   silently swallowing it.
5. The system SHALL preserve capture of records emitted at each stage such that,
   after a test logs during setup and call, the tracked phase names include both
   `"setup"` and `"call"`.
