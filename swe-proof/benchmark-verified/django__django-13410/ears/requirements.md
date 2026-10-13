# Requirements: POSIX advisory file-lock status reporting

## Introduction

`django/core/files/locks.py` provides portable advisory file-locking helpers,
exposing `lock(f, flags)` and `unlock(f)` together with the flag constants
`LOCK_EX`, `LOCK_SH`, and `LOCK_NB`. On POSIX platforms (the branch that uses
the `fcntl` module), these helpers wrap `fcntl.flock`.

The POSIX implementation reports the outcome of a locking operation incorrectly.
It assumes the underlying primitive returns a status code that can be compared
to zero, but `fcntl.flock` signals its result through two different channels: it
returns nothing (a value of `None`) when the operation completes successfully,
and it raises an exception when a request cannot be satisfied. Because `None`
never compares equal to zero, both `lock` and `unlock` always report failure —
even after a lock is actually acquired or released. This defeats callers that
use the non-blocking flag (`LOCK_NB`) to discover whether they obtained a lock.

The goal is to make the POSIX `lock` and `unlock` helpers report a correct
boolean status: success when the operation completes, and — for a non-blocking
request that cannot be granted right now — failure, without disturbing any of
the other file utilities in this package.

## Requirement 1: `lock` reports success when a lock is granted

**User story:** As a developer acquiring an advisory file lock, I want `lock` to
return a truthful success value, so that I can rely on it to know the lock was
obtained.

**Acceptance criteria**

1. WHEN `lock(f, flags)` is called on the POSIX implementation and the
   underlying `fcntl.flock` call completes without raising, THEN `lock` SHALL
   return the boolean `True`.
2. The system SHALL return a value that is the boolean `True` itself (identical
   to `True`), not merely a truthy value, when a lock is granted.
3. WHEN an exclusive lock is requested with `LOCK_EX` on an file that is not
   currently locked, THEN `lock` SHALL return `True`.
4. WHEN a shared lock is requested with `LOCK_SH` on a file, THEN `lock` SHALL
   return `True`.
5. WHILE one open handle already holds a shared lock on a file, IF another open
   handle requests a shared lock on the same file with the non-blocking flag
   (`LOCK_SH | LOCK_NB`), THEN `lock` SHALL return `True`, because shared locks
   are compatible with one another.

## Requirement 2: `lock` reports failure when a non-blocking request cannot be granted

**User story:** As a developer using non-blocking locks, I want `lock` to return
failure when the lock cannot be acquired right now, so that I can react instead
of blocking or wrongly believing I hold the lock.

**Acceptance criteria**

1. WHEN `lock(f, flags)` is called with the non-blocking flag (`LOCK_NB`) and the
   requested lock cannot be granted immediately because a conflicting lock is
   held, THEN the underlying primitive signals this out of band by raising, and
   `lock` SHALL return the boolean `False`.
2. The system SHALL return a value that is the boolean `False` itself (identical
   to `False`), not merely a falsy value, when a non-blocking request cannot be
   satisfied.
3. WHILE one open handle already holds an exclusive lock on a file, IF another
   open handle requests an exclusive lock on the same file with the non-blocking
   flag (`LOCK_EX | LOCK_NB`), THEN `lock` SHALL return `False`.
4. WHILE one open handle already holds an exclusive lock on a file, IF another
   open handle requests a shared lock on the same file with the non-blocking
   flag (`LOCK_SH | LOCK_NB`), THEN `lock` SHALL return `False`.
5. IF the underlying primitive raises any signal other than the
   cannot-be-granted-right-now (would-block) condition, THEN `lock` SHALL NOT
   convert it into a boolean status and SHALL allow that error to propagate to
   the caller.

## Requirement 3: `unlock` reports success when a lock is released

**User story:** As a developer releasing an advisory file lock, I want `unlock`
to return a truthful success value, so that I can rely on it to know the lock was
released.

**Acceptance criteria**

1. WHEN `unlock(f)` is called on the POSIX implementation and the underlying
   `fcntl.flock` release call completes without raising, THEN `unlock` SHALL
   return the boolean `True`.
2. The system SHALL return a value that is the boolean `True` itself (identical
   to `True`), not merely a truthy value, when a lock is released.
3. WHEN a previously acquired exclusive or shared lock on a file is released,
   THEN `unlock` SHALL return `True`.

## Requirement 4: Preserve the existing locking API and unrelated file utilities

**User story:** As a maintainer of the file utilities package, I want the public
locking interface and every other file helper to keep working unchanged, so that
the fix does not introduce regressions.

**Acceptance criteria**

1. The system SHALL continue to expose `lock`, `unlock`, `LOCK_EX`, `LOCK_SH`,
   and `LOCK_NB` from the locks module, with `LOCK_EX`, `LOCK_SH`, and `LOCK_NB`
   taking their values from the `fcntl` module on POSIX platforms.
2. The `locks` module SHALL remain importable from the file utilities package
   without error.
3. The system SHALL leave the non-POSIX (Windows / `nt`) locking code path and
   the file-locking-unsupported fallback path unchanged in behavior.
4. The system SHALL keep the behavior of all other file utilities in the package
   unchanged — including file wrappers and their mode/read/write/seek/iteration
   behavior, content files, named and spooled temporary files, safe file moves,
   and image-dimension inspection.
