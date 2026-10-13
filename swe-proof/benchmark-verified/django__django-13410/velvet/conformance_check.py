#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13410 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl regions
              (`acquireLock`, routed through the pure model `acquiredOk`, and
              `releaseLock` = constant True) transliterated to Python. There are
              NO A-tagged callees in the impl region (no axioms), so the shadow
              is pure R/I:
                  acquireLock(succeeded) = True,  acquireLock(contended) = False
                  releaseLock()          = True
  * ORACLE  — `patch.diff`'s behaviour: the patched POSIX wrappers
              `django.core.files.locks.lock` / `.unlock`, applied at base_commit
              (the real correctness oracle, G-RESOLVE). The two `LockOutcome`
              values are NOT fed to the oracle directly: each is realised as a
              REAL `fcntl.flock` outcome on REAL file descriptors —
                  succeeded  ↔ flock returns (resource free / shared-compatible)
                  contended  ↔ flock raises BlockingIOError (LOCK_NB on a held
                               conflicting resource)
              exactly the mechanism the F2P tests exercise — and the oracle
              observes it THROUGH the real `lock`/`unlock`. This refutes the
              R-identity of A1 (real flock outcome ↔ LockOutcome) as well as the
              I boolean results.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), Django importable,
stdlib only, on a POSIX host with fcntl. The fuzz seed is pinned (mapping.md §4)
for a deterministic verdict.
"""
import os
import random
import sys
import tempfile

SEED = 13410
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean acquiredOk / releaseLock, transliterated ---

def shadow_acquire(outcome):
    """acquireLock (acquiredOk): True iff the primitive's outcome is 'succeeded'."""
    return outcome == "succeeded"


def shadow_release():
    """releaseLock: constant True."""
    return True


# --- the oracle: patch.diff behaviour via the real patched locks module ------

def _import_locks():
    from django.core.files import locks
    return locks


def oracle_acquire_free(locks, path, nonblocking):
    """Realise outcome 'succeeded': acquire an EXCLUSIVE lock on a FREE file via
    the real patched `lock`. Returns the real boolean it reports."""
    flags = locks.LOCK_EX | (locks.LOCK_NB if nonblocking else 0)
    with open(path) as f:
        try:
            return bool(locks.lock(f, flags))
        finally:
            locks.unlock(f)


def oracle_acquire_contended(locks, path, second_flags):
    """Realise outcome 'contended': hold an EXCLUSIVE lock on one open file
    description, then attempt a NON-BLOCKING acquire (`second_flags`, with
    LOCK_NB set) on a second, independent open file description of the same file
    (flock conflicts across open descriptions on Linux). Both an exclusive and a
    shared non-blocking request conflict with a held exclusive lock. Returns the
    real boolean the second `lock` reports (the patched wrapper catches
    BlockingIOError -> False)."""
    with open(path) as f1, open(path) as f2:
        held = locks.lock(f1, locks.LOCK_EX)        # take the lock (should be True)
        try:
            return bool(locks.lock(f2, second_flags))
        finally:
            if held:
                locks.unlock(f1)


def oracle_acquire_shared_ok(locks, path):
    """Realise outcome 'succeeded' via a SHARED-compatible non-blocking acquire:
    hold a SHARED lock, then a second SHARED|NB acquire succeeds (shared locks
    are compatible). Returns the real boolean reported."""
    with open(path) as f1, open(path) as f2:
        held = locks.lock(f1, locks.LOCK_SH)
        try:
            return bool(locks.lock(f2, locks.LOCK_SH | locks.LOCK_NB))
        finally:
            if held:
                locks.unlock(f1)


def oracle_release(locks, path):
    """Realise the release path: acquire then release a held lock; return the
    real boolean `unlock` reports."""
    with open(path) as f:
        locks.lock(f, locks.LOCK_EX)
        return bool(locks.unlock(f))


def main():
    locks = _import_locks()
    if not hasattr(locks, "LOCK_EX") or getattr(locks, "LOCK_NB", 0) == 0:
        # File locking unsupported on this build (the fcntl branch is inactive):
        # the modeled POSIX behaviour cannot be exercised here.
        print("G-CONF SKIP: fcntl locking unavailable on this platform "
              "(LOCK_NB == 0); POSIX branch not exercised.")
        return 0

    rng = random.Random(SEED)

    # Each scenario pairs a realised real outcome with the LockOutcome it
    # refines, so we diff shadow(LockOutcome) against the real reported boolean.
    #   name, builder(locks, path) -> real_bool, modeled LockOutcome, kind
    scenarios = [
        ("acquire_free_blocking",
         lambda l, p: oracle_acquire_free(l, p, False), "succeeded", "acquire"),
        ("acquire_free_nonblocking",
         lambda l, p: oracle_acquire_free(l, p, True), "succeeded", "acquire"),
        ("acquire_shared_compatible",
         lambda l, p: oracle_acquire_shared_ok(l, p), "succeeded", "acquire"),
        ("acquire_contended_ex_nb",
         lambda l, p: oracle_acquire_contended(l, p, l.LOCK_EX | l.LOCK_NB),
         "contended", "acquire"),
        ("acquire_contended_sh_nb",
         lambda l, p: oracle_acquire_contended(l, p, l.LOCK_SH | l.LOCK_NB),
         "contended", "acquire"),
        ("release_held",
         lambda l, p: oracle_release(l, p), None, "release"),
    ]

    disagreements = []
    count = 0
    with tempfile.TemporaryDirectory() as d:
        # A handful of real files with varied content/size; the lock outcome is
        # independent of content, but we vary them to fuzz the descriptor path.
        paths = []
        for i in range(8):
            p = os.path.join(d, "f%d.bin" % i)
            with open(p, "wb") as fh:
                fh.write(os.urandom(rng.randint(0, 4096)))
            paths.append(p)

        for _ in range(N_FUZZ):
            name, builder, outcome, kind = rng.choice(scenarios)
            path = rng.choice(paths)
            count += 1
            real = builder(locks, path)
            if kind == "acquire":
                shadow = shadow_acquire(outcome)
            else:
                shadow = shadow_release()
            if shadow != real:
                disagreements.append((name, outcome, shadow, real))
                if len(disagreements) >= 5:
                    break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for name, outcome, sh, real in disagreements:
            print("  scenario=%s outcome=%r shadow=%r oracle=%r"
                  % (name, outcome, sh, real))
        return 1
    print("G-CONF OK: R/I shadow of acquireLock/releaseLock agrees with "
          "patch.diff behaviour (real fcntl.flock outcomes) on %d inputs "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
