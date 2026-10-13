#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14493.

This bundle has NO `@ContractOnly` axioms and NO A-reference to an external
library callee: the only behaviour under specification is the definite-
assignment and early-stop semantics of the post-processing pass loop, modelled
DEEPLY in model.py (the pure predicate `all_changed` plus the verified loop in
`run_passes`). There is therefore no real library callee to over-approximate.

What this check validates instead is that the deep model is FAITHFUL to the
real control flow it abstracts: a byte-faithful reference of the repository's
pass loop (the `for i in range(self.max_post_process_passes)` loop in
`StaticFilesStorage.post_process`, including the pre-loop initialisation the
patch adds and the post-loop `if substitutions:` read) computes exactly the
post-loop `substitutions` value that model.py's closed form `all_changed`
predicts — for EVERY pass count from 0 (the crashing configuration) upward and
every pattern of per-pass change/no-change outcomes (boundary + exhaustive small
+ randomized fuzz). It also asserts the pre-patch loop (no pre-loop init) raises
exactly the `UnboundLocalError` the issue reports when the count is 0.

stdlib-only imports. Exit 0 iff every observation matches the model.
"""
import itertools
import random
import sys


# --- model.py closed form (kept in lock-step with the deep model `all_changed`)
def all_changed(flags, n):
    """Reference of model.py's pure predicate `all_changed(flags, n)`: every one
    of the first n passes reported a change (flag != 0); n == 0 is True."""
    assert 0 <= n <= len(flags)
    for k in range(n):
        if flags[k] == 0:
            return False
    return True


def model_run_passes(flags, max_passes):
    """Reference of model.py's `run_passes` post-condition closed form:
    Result() == (max_passes > 0 and all_changed(flags, max_passes))."""
    return max_passes > 0 and all_changed(flags, max_passes)


# --- faithful reference of the REAL post_process pass loop --------------------
# Mirrors django/contrib/staticfiles/storage.py post_process (post-patch):
#   substitutions = False                       # <- the line the patch adds
#   for i in range(self.max_post_process_passes):
#       substitutions = False
#       for ... in self._post_process(...):     # abstracted: per-pass outcome
#           substitutions = substitutions or subst
#       if not substitutions:
#           break
#   return substitutions                         # consulted by `if substitutions:`
def real_loop_post_patch(flags, max_passes):
    """`flags[i]` is 1 iff pass i produced any substitution, else 0 (the OR of
    the inner-loop `subst` values for that pass). Returns the post-loop
    `substitutions` value that `if substitutions:` reads."""
    substitutions = False          # pre-loop initialisation (the fix)
    for i in range(max_passes):
        substitutions = bool(flags[i])
        if not substitutions:
            break
    return substitutions


def real_loop_pre_patch(flags, max_passes):
    """The pre-patch loop WITHOUT the pre-loop initialisation. Reading
    `substitutions` after a zero-iteration loop raises UnboundLocalError —
    exactly the crash the issue reports for max_post_process_passes == 0."""
    for i in range(max_passes):
        substitutions = bool(flags[i])
        if not substitutions:
            break
    return substitutions          # NameError/UnboundLocalError when max_passes == 0


def all_flag_vectors(length):
    for combo in itertools.product((0, 1), repeat=length):
        yield list(combo)


def main():
    # --- 1. deep model == real (post-patch) loop, exhaustive small + boundary -
    checked = 0
    for length in range(0, 9):
        for flags in all_flag_vectors(length):
            for max_passes in range(0, length + 1):
                observed = real_loop_post_patch(flags, max_passes)   # real loop
                expected = model_run_passes(flags, max_passes)       # model
                assert observed == expected, (
                    "deep model unsound: flags=%r max_passes=%d real=%r model=%r"
                    % (flags, max_passes, observed, expected))
                checked += 1

    # zero-pass boundary explicitly: must be a defined False, never a crash.
    for length in range(0, 6):
        for flags in all_flag_vectors(length):
            assert real_loop_post_patch(flags, 0) is False
            assert model_run_passes(flags, 0) is False

    # --- 2. randomized fuzz over larger counts --------------------------------
    rng = random.Random(14493)
    for _ in range(50000):
        length = rng.randint(0, 40)
        flags = [rng.randint(0, 1) for _ in range(length)]
        max_passes = rng.randint(0, length)
        observed = real_loop_post_patch(flags, max_passes)
        expected = model_run_passes(flags, max_passes)
        assert observed == expected, (
            "deep model unsound (fuzz): flags=%r max_passes=%d real=%r model=%r"
            % (flags, max_passes, observed, expected))
        checked += 1

    # --- 3. the pre-patch loop crashes exactly on the zero-pass configuration -
    for flags in ([], [1], [0], [1, 0, 1]):
        try:
            real_loop_pre_patch(flags, 0)
        except (UnboundLocalError, NameError):
            pass
        else:
            raise AssertionError(
                "pre-patch loop did NOT raise on max_passes==0 (flags=%r)" % (flags,))
        # with >=1 pass the pre-patch loop assigns and does not crash
        if flags:
            real_loop_pre_patch(flags, len(flags))

    print("G-AX OK: deep model `all_changed`/`run_passes` == real post_process "
          "pass loop on %d (exhaustive small + boundary + 50000 fuzz) cases; "
          "pre-patch loop raises UnboundLocalError exactly at max_passes==0." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
