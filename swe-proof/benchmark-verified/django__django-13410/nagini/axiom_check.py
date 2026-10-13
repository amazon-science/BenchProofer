#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13410.

Executes the REAL low-level locking primitive (`fcntl.flock`, the unchanged
library callee the helpers wrap) on real file descriptors and asserts that
every observation matches the model's axioms, as encoded in model.py.

The model abstracts the primitive as two contract-only functions:

  (A-consumed) `primitive_lock(available)`:
      * on a NORMAL completion (the lock WAS available) it yields THE EMPTY
        VALUE ITSELF (`Ensures(Result() is None)`), not a stand-in number. The
        real `fcntl.flock` returns Python's empty value `None` on success, so
        the model carries the callee's actual value rather than an abstraction
        of it, and the clause is sound by identity.

        THAT CLAUSE IS CHECKED IN BOTH DIRECTIONS, and the second direction is
        the point. Positively: the real value IS the empty one. Negatively: that
        value answers NONE of the questions a number answers — it does not count
        as "set", it cannot be ordered against a number, and it cannot enter
        arithmetic — so no body can read a granted-or-refused outcome off it and
        the outcome must be taken from the control flow, which is where it is.
        The negative controls below assert exactly that on the real value, and
        they also show what a STAND-IN NUMBER would have licensed: any number
        does count as "set" and does order against zero, so a model that carried
        the success value as a number would let a body report the outcome by
        interrogating it and get the OPPOSITE answer from the one the real
        callee's value gives. That is not a hypothetical — it is the reading
        this check exists to refute.
      * on contention (the lock was NOT available) it does NOT complete
        normally but raises `LockUnavailable`. The real `fcntl.flock` with the
        non-blocking flag raises `OSError` (specifically `BlockingIOError`,
        EAGAIN/EWOULDBLOCK) when another holder owns an incompatible lock.

      * on a normal completion the SUBJECT description holds the lock it
        requested (`Ensures(holds_lock())`). Observed directly: after a granted
        acquisition, an independent descriptor's incompatible non-blocking
        request is REFUSED.
      * on a refusal it does not move the subject's standing in the REQUESTED
        lock (`holds_lock() == Old(holds_lock())`). Observed directly: a refused
        non-blocking request leaves the existing holder's lock exactly as it was.

  (A-consumed) `primitive_release()`:
      * releasing a lock the caller already holds completes normally and yields
        THE EMPTY VALUE (`Ensures(Result() is None)`; real
        `fcntl.flock(fd, LOCK_UN)` returns `None`); it does not signal
        contention. The same negative controls are applied to the release value,
        because the release helper's report is decided the same way.
      * it leaves the SUBJECT no longer holding the lock
        (`Ensures(holds_lock() is False)`). Observed directly: after the release,
        the subject retains no claim once no other holder can mask the probe.
        This is the second direction of the state observation, the one that makes
        it reversible rather than monotone.

        NOTE, and it is the whole reason this check is written per-description:
        `flock(2)` locks belong to OPEN FILE DESCRIPTIONS, not to files. The
        model's `holds_lock()` is the subject's own claim (mapping.md §1/§3.3),
        so this clause says "the subject let go", NOT "the file is unlocked".
        The two readings disagree exactly when another description holds a
        compatible shared claim — the instance's own `test_shared_lock` world —
        where the real callee leaves an aggregate probe still answering "held"
        while the subject's claim is genuinely gone. The block below asserts
        both halves of that, so the distinction is executable evidence rather
        than prose.

Imports nothing repo-specific: `fcntl`, `os`, `tempfile` are the Python
standard library; `fcntl.flock` is the very callee the gold patch wraps. Exit 0
iff every obligation holds. If `fcntl` is unavailable (non-POSIX), the posix
branch under specification does not exist and the check is vacuously sound.
"""
import os
import sys
import tempfile


def main():
    try:
        import fcntl
    except ImportError:
        # Non-POSIX: the modelled posix branch is not compiled; vacuously sound.
        print("G-AX OK (vacuous): fcntl unavailable, posix lock branch absent")
        return 0

    def check_empty_value(value, who):
        """Assert that `value` is what the model's value clause says it is, and
        that it is USELESS for deciding an outcome.

        Positive direction: `Ensures(Result() is None)` — the value IS the empty
        value, so the model carries the real callee's own value.

        Negative direction (the controls): the empty value answers no numeric
        interrogation, so a body cannot derive the reported boolean from it. Each
        control is paired with the answer A STAND-IN NUMBER would have given, so
        the reading the model must NOT license is refuted by measurement rather
        than asserted by prose: under a numeric carrier every one of these
        interrogations succeeds and answers the OPPOSITE way, which is precisely
        how a body could report a granted acquisition as a failure (or an
        outright error) while still satisfying a spec written over the number.
        """
        assert value is None, (
            "%s axiom unsound: the real callee returned %r, but the model's "
            "value clause says the value is the empty value" % (who, value))
        # (a) "is it set?" — the interrogation a truthiness test performs.
        assert not value, (
            "%s axiom unsound: the real value %r counts as 'set', so a body "
            "could report the outcome by testing it" % (who, value))
        assert bool(-1) is True, (
            "negative control broken: a stand-in number must count as 'set', "
            "which is what makes carrying the value as a number unsound")
        # (b) ordering and (c) arithmetic — a number answers both; the empty
        # value refuses both, and refusing is the property the clause preserves.
        for probe, run in (("order", lambda: value < 0),
                           ("arith", lambda: value - value)):
            try:
                run()
            except TypeError:
                continue
            raise AssertionError(
                "%s axiom unsound: the real value %r answered a numeric "
                "interrogation (%s); a body could then decide the reported "
                "outcome from the value" % (who, value, probe))
        assert (-1 < 0) is True and (-1) - (-1) == 0, (
            "negative control broken: a stand-in number must answer ordering "
            "and arithmetic, which the empty value does not")
        # (d) the PRE-PATCH interrogation: "does the value equal the number that
        # would have meant success?" The empty value does not, so a helper that
        # decides that way reports FAILURE on a lock it holds — the bug.
        assert (value == 0) is False, (
            "%s axiom unsound: the real value %r compares equal to 0, which "
            "would hide the always-reports-failure bug" % (who, value))

    fd_path = None
    try:
        tf = tempfile.NamedTemporaryFile(prefix="dj13410_", delete=False)
        fd_path = tf.name
        tf.close()

        # --- primitive_lock NORMAL completion (lock available) --------------
        # First holder acquires an exclusive lock: the real flock hands back THE
        # EMPTY VALUE, which is exactly what the model's value clause says and
        # which answers none of the questions a number answers (checked in both
        # directions by check_empty_value). Observed across blocking and
        # non-blocking acquisition modes.
        for flags in (fcntl.LOCK_EX, fcntl.LOCK_EX | fcntl.LOCK_NB,
                      fcntl.LOCK_SH, fcntl.LOCK_SH | fcntl.LOCK_NB):
            with open(fd_path) as f1:
                ret = fcntl.flock(f1.fileno(), flags)
                check_empty_value(ret, "primitive_lock(flags=%r)" % (flags,))
                # release for the next iteration
                rel = fcntl.flock(f1.fileno(), fcntl.LOCK_UN)
                check_empty_value(rel, "primitive_release")

        # --- primitive_lock CONTENTION (lock NOT available) -----------------
        # First holder takes an exclusive lock; a second descriptor requesting
        # an incompatible lock NON-BLOCKING must raise OSError (BlockingIOError,
        # EAGAIN/EWOULDBLOCK) — the out-of-band contention signal the model's
        # Exsures(LockUnavailable, available is False) stands in for.
        contention_observed = 0
        for second_flags in (fcntl.LOCK_EX | fcntl.LOCK_NB,
                             fcntl.LOCK_SH | fcntl.LOCK_NB):
            with open(fd_path) as f1, open(fd_path) as f2:
                got = fcntl.flock(f1.fileno(), fcntl.LOCK_EX)
                check_empty_value(got, "primitive_lock (setup holder)")
                raised = False
                try:
                    fcntl.flock(f2.fileno(), second_flags)
                except OSError:
                    # BlockingIOError is a subclass of OSError; the gold patch
                    # catches BlockingIOError, the problem statement says OSError.
                    raised = True
                assert raised, (
                    "primitive_lock axiom unsound: a non-blocking request "
                    "(flags=%r) for an exclusively-held lock did NOT raise; "
                    "the contention signal Exsures(LockUnavailable) relies on "
                    "is absent" % (second_flags,))
                contention_observed += 1
                fcntl.flock(f1.fileno(), fcntl.LOCK_UN)
        assert contention_observed == 2

        # --- primitive_release NORMAL completion ----------------------------
        # Releasing a held lock hands back the empty value and does not raise.
        with open(fd_path) as f1:
            check_empty_value(fcntl.flock(f1.fileno(), fcntl.LOCK_EX),
                              "primitive_lock")
            rel = fcntl.flock(f1.fileno(), fcntl.LOCK_UN)
            check_empty_value(rel, "primitive_release")

        # --- the STATE observation, BOTH directions ------------------------
        # Ensures(holds_lock()) on a granted acquisition and
        # Ensures(holds_lock() is False) after a release are the reversible
        # state clauses the helpers' exit-state postconditions consume.
        #
        # WHOSE claim is being observed is load-bearing. `flock(2)` locks are
        # PER-OPEN-FILE-DESCRIPTION, not per-file, and the model's holds_lock()
        # is the SUBJECT description's own claim (mapping.md §1/§3.3). An
        # aggregate "is any lock in force on this file" probe is a DIFFERENT
        # observable and is NOT what the clauses assert: the two come apart
        # whenever a second description holds a compatible shared claim, which is
        # precisely the instance's own `test_shared_lock` world. Checking the
        # clauses against the aggregate probe would report the model unsound for
        # a claim it never makes, so the check below observes the subject's claim.
        #
        # `subject_holds` isolates the subject: it drains every OTHER holder and
        # then probes what remains, so a surviving record can only be the
        # subject's. It restores nothing, so each scenario configures its world
        # afresh.
        def any_lock_in_force(probe):
            """AGGREGATE reading: does ANY description hold a lock on the file?"""
            try:
                fcntl.flock(probe.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                return True
            fcntl.flock(probe.fileno(), fcntl.LOCK_UN)
            return False

        def subject_holds(others):
            """PER-DESCRIPTION reading (the model's holds_lock()): does the
            SUBJECT still hold its claim, once no other holder can mask it?"""
            for o in others:
                try:
                    fcntl.flock(o.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass
            with open(fd_path) as pr:
                return any_lock_in_force(pr)

        # SHARED-HOLDER WORLD — the scenario that distinguishes the two readings
        # and the one the instance's F2P `test_shared_lock` exercises. The model's
        # release clause Ensures(holds_lock() is False) must hold HERE, under the
        # per-description reading, on the REAL callee.
        with open(fd_path) as s1, open(fd_path) as s2:
            assert fcntl.flock(s1.fileno(), fcntl.LOCK_SH) is None
            assert fcntl.flock(s2.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB) is None
            # subject s1 releases; a compatible claim (s2's) is still outstanding.
            assert fcntl.flock(s1.fileno(), fcntl.LOCK_UN) is None
            with open(fd_path) as pr:
                aggregate_still_held = any_lock_in_force(pr)
            assert aggregate_still_held, (
                "setup unsound: the second shared holder's claim vanished, so "
                "this world does not distinguish the two readings")
            assert not subject_holds([s2]), (
                "primitive_release axiom unsound: after the subject's release "
                "the SUBJECT still holds its claim "
                "(Ensures(holds_lock() is False) fails) in the shared-holder "
                "world")
        # The assertion pair above is the point of this block: the AGGREGATE
        # observable is True at that program point while the model's clause is
        # False, which is exactly why holds_lock() is refined per description.


        with open(fd_path) as sub, open(fd_path) as other, open(fd_path) as probe:
            assert not any_lock_in_force(probe), (
                "setup unsound: the lock is already in force before any "
                "acquisition")
            # direction 1: a granted acquisition PUTS the lock in force.
            assert fcntl.flock(sub.fileno(), fcntl.LOCK_EX) is None
            assert any_lock_in_force(probe), (
                "primitive_lock axiom unsound: after a granted acquisition the "
                "lock is NOT in force (Ensures(holds_lock()) fails); a third "
                "party's non-blocking request was granted")
            # preservation: a REFUSED request moves nothing — the lock is still
            # in force afterwards, exactly as before the refused attempt.
            refused = False
            try:
                fcntl.flock(other.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                refused = True
            assert refused, "setup unsound: the contended request was granted"
            assert any_lock_in_force(probe), (
                "primitive_lock axiom unsound: a REFUSED request changed the "
                "lock state (the Exsures preservation conjunct "
                "holds_lock() == Old(holds_lock()) fails)")
            # direction 2: a release TAKES the lock out of force. This is what
            # makes the observation reversible, hence positional.
            assert fcntl.flock(sub.fileno(), fcntl.LOCK_UN) is None
            assert not any_lock_in_force(probe), (
                "primitive_release axiom unsound: after the release the lock is "
                "STILL in force (Ensures(holds_lock() is False) fails)")

    finally:
        if fd_path is not None and os.path.exists(fd_path):
            os.unlink(fd_path)

    print("G-AX OK: real fcntl.flock returns THE EMPTY VALUE on normal "
          "completion for acquire and release -- and that value does not count "
          "as 'set', does not order against a number and does not enter "
          "arithmetic, while a stand-in number answers all three the opposite "
          "way, so the empty-value clause is sound AND the numeric reading it "
          "replaces is refuted -- raises OSError on non-blocking contention, "
          "gives the SUBJECT description the requested claim on a granted "
          "acquisition, leaves the subject's standing in the requested lock "
          "untouched on a refused one, and ends the subject's claim on release "
          "(the state observation is reversible in both directions) -- INCLUDING "
          "in the shared-holder world, where another description's compatible "
          "claim survives and an aggregate probe would still answer 'held' "
          "though the subject's claim is gone; primitive_lock / primitive_release "
          "axioms sound under the per-description reading the model uses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
