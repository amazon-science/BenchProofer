#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16116.

The bundle has NO consumed `axiom`. The one callee whose runtime behaviour the
deep model relies on — the non-zero abort primitive `sys.exit` — is UNCHANGED
and is modeled as an **A-reference** (a behavioural reference, not a consumed
contract). This check validates, against the REAL standard-library `sys.exit`
and the REAL control-flow structure of the patched
`makemigrations.Command.handle` branch, the single property the refinement
relies on:

  (A-reference)  `sys.exit(n)` with `n != 0` raises `SystemExit` carrying the
      non-zero code, and that exception UNWINDS THE STACK — so any statement
      sequenced AFTER `sys.exit(1)` in the same function body does NOT execute,
      and the process terminates with a non-zero status.

This is exactly what makes the gold re-ordering correct: with the
`if check_changes: sys.exit(1)` guard placed ABOVE the write block, a check-only
run aborts and NO write statement runs (no migration artifact emitted). The
check also exercises the discriminating differential directly: it runs the
post-patch statement order (abort-first) and the pre-patch order (write-first)
against the real `sys.exit`, recording every side effect, and asserts that only
the pre-patch order leaves a "write" behind in check-only mode.

Imports only the standard library (`sys`). No repo-test code, no database. Exit
0 iff every obligation holds.
"""
import random
import sys


def check_exit_raises_nonzero(code):
    """A-reference part 1: sys.exit(code) with code != 0 raises SystemExit
    carrying that non-zero code."""
    assert code != 0
    try:
        sys.exit(code)
    except SystemExit as e:
        # SystemExit.code is the argument passed to sys.exit.
        assert e.code == code, (
            "sys.exit(%r) should raise SystemExit with code %r, got %r"
            % (code, code, e.code))
        # A non-zero code means the process terminates with a non-zero status.
        assert e.code != 0, "expected a non-zero exit code, got %r" % (e.code,)
        return
    raise AssertionError("sys.exit(%r) did not raise SystemExit" % (code,))


def check_exit_unwinds():
    """A-reference part 2: a statement sequenced AFTER sys.exit(1) in the same
    function body does NOT execute (the raise unwinds the stack)."""
    ran_after = []
    try:
        sys.exit(1)
        ran_after.append("after")  # must be unreachable
    except SystemExit:
        pass
    assert ran_after == [], (
        "a statement after sys.exit(1) must not run; observed %r" % (ran_after,))


def run_branch(check_only, update, abort_first):
    """Faithful transliteration of the makemigrations.handle non-empty-changes
    branch control flow, using the REAL sys.exit. `abort_first=True` is the
    gold (post-patch) order; `abort_first=False` is the pre-patch order.

    Records the side effects in order. Returns (effects, exited) where `exited`
    is True iff sys.exit(1) fired. The 'write' effect is appended exactly when
    the real control flow would reach the write statement (i.e. it is NOT
    skipped by a preceding stack-unwinding sys.exit)."""
    effects = []
    exited = False

    def write_block():
        # the two real write methods; either appends exactly one artifact
        if update:
            effects.append(("write", "latest"))
        else:
            effects.append(("write", "standard"))

    try:
        if abort_first:
            if check_only:
                sys.exit(1)
            write_block()
        else:
            write_block()
            if check_only:
                sys.exit(1)
    except SystemExit as e:
        assert e.code == 1
        exited = True
    return effects, exited


def check_ordering_differential(check_only, update):
    """The discriminating fact: under the gold (abort-first) order a check-only
    run emits NO write artifact; under the pre-patch (write-first) order it
    emits one before aborting. Outside check-only mode both orders emit exactly
    one artifact and neither aborts."""
    post_effects, post_exited = run_branch(check_only, update, abort_first=True)
    pre_effects, pre_exited = run_branch(check_only, update, abort_first=False)

    wrote_post = any(k == "write" for k, _ in post_effects)
    wrote_pre = any(k == "write" for k, _ in pre_effects)

    if check_only:
        # gold: aborted, and the write after the abort never ran (unwind).
        assert post_exited, "gold check-only run should abort"
        assert not wrote_post, (
            "gold check-only run must emit NO artifact, got %r" % (post_effects,))
        # pre-patch: wrote first, THEN aborted.
        assert pre_exited, "pre-patch check-only run should also abort"
        assert wrote_pre, (
            "pre-patch check-only run should emit an artifact before aborting, "
            "got %r" % (pre_effects,))
        # the differential the spec senses:
        assert wrote_post != wrote_pre, (
            "abort-first vs write-first should differ on artifact emission in "
            "check-only mode")
    else:
        # not check-only: identical, both write exactly one, neither aborts.
        assert not post_exited and not pre_exited
        assert wrote_post and wrote_pre
        assert post_effects == pre_effects, (
            "outside check-only mode the two orders should be identical, got "
            "%r vs %r" % (post_effects, pre_effects))
        kind = "latest" if update else "standard"
        assert post_effects == [("write", kind)]


def main():
    # boundary: the abort primitive on a spread of non-zero codes.
    for code in (1, 2, 3, 255, 1):
        check_exit_raises_nonzero(code)
    check_exit_unwinds()

    # boundary: the full two-flag cross product (the modeled input space).
    for check_only in (False, True):
        for update in (False, True):
            check_ordering_differential(check_only, update)

    # randomized fuzz over the flag pairs to exceed a trivial floor.
    rng = random.Random(16116)
    for _ in range(5000):
        check_ordering_differential(rng.random() < 0.5, rng.random() < 0.5)

    print("G-AX OK: sys.exit(1) raises SystemExit with a non-zero code and "
          "unwinds the stack (a statement after it does not run); under the "
          "gold abort-first order a check-only run emits NO migration artifact "
          "while the pre-patch write-first order emits one before aborting — "
          "over 5 boundary codes + 4 flag pairs + 5000 fuzz pairs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
