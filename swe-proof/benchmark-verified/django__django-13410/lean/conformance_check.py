#!/usr/bin/env python
"""G-CONF: differential conformance for django__django-13410.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_acquire` / `implementation_release` skeletons and diffs them
against the REAL patched `django.core.files.locks.lock` / `unlock`.

The lower-level locking primitive (`fcntl.flock`) is NOT re-implemented; it is
the `outcome` argument. We drive the real `lock`/`unlock` while substituting a
fake `flock` whose behavior corresponds to each `outcome` value:

  outcome = ok ()            -> flock returns None  (operation completed)
  outcome = error wouldBlock -> flock raises BlockingIOError (non-blocking miss)
  outcome = error (other c)  -> flock raises a NON-blocking OSError with errno c

  shadow_acquire(outcome)  vs  real lock(f, flags)    observable: returned bool / propagated exc
  shadow_release(outcome)  vs  real unlock(f)         observable: returned bool / propagated exc

The widened error model matters: the gold `lock` catches ONLY BlockingIOError
and propagates every other OSError; `unlock` catches nothing. The shadow must
agree on which channel each outcome lands in (returned bool vs. propagated exc).

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 13410
N_RANDOM = 120_000  # >= 1e5

# outcome carriers (R shadow of Outcome = Except FlockErr Unit)
OK = ("ok",)
ERR_WB = ("error", "wouldBlock")
ERR_OTHER = ("error", "other", 9)  # e.g. EBADF (errno 9), a non-blocking OSError


# ---- shadow of implementation_acquire / implementation_release -------------

def shadow_acquire(outcome):
    # try: flock(...); return True  except BlockingIOError: return False
    # (any other OSError propagates -> not turned into a status)
    if outcome[0] == "ok":
        return True
    if outcome[1] == "wouldBlock":
        return False
    return ("EXC", "OSError")  # `.other` channel: propagated


def shadow_release(outcome):
    # flock(..., LOCK_UN); return True   (no handled signal channel)
    if outcome[0] == "ok":
        return True
    # any raised signal propagates unchanged
    return ("EXC", "OSError")


# ---- the real patched locks.lock / locks.unlock ----------------------------

def real_observe(fn_name, outcome):
    import fcntl
    from django.core.files import locks

    orig = fcntl.flock
    try:
        def fake_flock(fd, flags):
            if outcome[0] == "ok":
                return None
            if outcome[1] == "wouldBlock":
                raise BlockingIOError(11, "Resource temporarily unavailable")
            # a non-blocking OSError (NOT a BlockingIOError subclass)
            raise OSError(outcome[2], "simulated non-blocking lock error")
        fcntl.flock = fake_flock
        # locks.lock/unlock captured `fcntl` at module import; patch the same obj
        f = 3  # a bare fd; _fd(f) returns it unchanged (no .fileno attr)
        try:
            if fn_name == "lock":
                return locks.lock(f, locks.LOCK_EX)
            else:
                return locks.unlock(f)
        except OSError:
            # a propagated signal: collapse to a single tag (the Lean model
            # carries an errno code, but the observable channel is "propagated").
            return ("EXC", "OSError")
    finally:
        fcntl.flock = orig


def main():
    rng = random.Random(SEED)

    # the full outcome domain is small; exhaustively, then fuzz the driving
    # sequence (varying the errno on the `.other` channel) to exercise every
    # code path repeatedly.
    base_cases = [OK, ERR_WB, ERR_OTHER]

    disagreements = 0
    checked = 0

    def check(fn_name, shadow_fn, outcome):
        nonlocal disagreements, checked
        got = real_observe(fn_name, outcome)
        exp = shadow_fn(outcome)
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH {fn_name} outcome={outcome}: real={got!r} shadow={exp!r}")

    for outcome in base_cases:
        check("lock", shadow_acquire, outcome)
        check("unlock", shadow_release, outcome)

    for _ in range(N_RANDOM):
        r = rng.random()
        if r < 0.34:
            outcome = OK
        elif r < 0.67:
            outcome = ERR_WB
        else:
            # a non-blocking errno: EXCLUDE the codes Python auto-promotes to
            # BlockingIOError (EAGAIN 11 / EWOULDBLOCK / EINPROGRESS 115 /
            # EALREADY 114), which `lock` WOULD catch.
            outcome = ("error", "other", rng.choice([1, 2, 5, 9, 13, 22, 9999]))
        if rng.random() < 0.5:
            check("lock", shadow_acquire, outcome)
        else:
            check("unlock", shadow_release, outcome)

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
