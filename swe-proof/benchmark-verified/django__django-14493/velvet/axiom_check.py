#!/usr/bin/env python3
"""G-AX soundness check for django__django-14493.

This bundle declares NO axioms and NO `:|`-stub method, and models NO repo
callee deeply (mapping.md §3): the modeled behavior is a self-contained
control-flow computation over abstract carriers (`flags : List Bool`,
`limit : Nat`). The one repo callee inside the modeled loop,
`ManifestFilesMixin._post_process`, is UNCHANGED by the patch and is abstracted
into the input `flags` rather than modeled — so there is no callee contract to
validate against a real execution.

G-AX is therefore degenerate here. To still ship an executable, falsifiable
G-AX artifact, this script validates the **modeling invariant** that the pure
spec function `overBudget(flags, limit)` (the postcondition `passBudgetExceeded`
must satisfy) equals the value the PATCHED `post_process` loop reads at its
trailing `if substitutions:` test — over boundary + fuzzed abstract inputs. This
is the same correspondence G-CONF tests; here it documents that the spec's
postcondition oracle is the patched behaviour and, crucially, that the
zero-budget case yields `False` (no UnboundLocalError, the regression the gold
patch fixes).

stdlib-only. Exit 0 iff every obligation holds.
"""
import random
import sys


def over_budget(flags, limit):
    """The pure spec function overBudget(flags, limit) from Solution.lean:
    decide(0 < limit) && (all j < limit -> flags[j] == True)."""
    return limit > 0 and all(flags[j] for j in range(limit))


def patched_summary(flags, limit):
    """The value `substitutions` read at `if substitutions:` of the PATCHED
    post_process loop (django/contrib/staticfiles/storage.py with the gold
    `substitutions = False` initializer). Mirrors the oracle of G-CONF."""
    substitutions = False
    for i in range(limit):
        substitutions = flags[i]
        if not substitutions:
            break
    return substitutions


def check(flags, limit):
    spec = over_budget(flags, limit)
    real = patched_summary(flags, limit)
    assert bool(spec) == bool(real), (
        "modeling invariant unsound on flags=%r limit=%r: spec overBudget=%r, "
        "patched post_process summary=%r" % (flags, limit, spec, real))


def main():
    # --- boundary cases: the zero-budget regression is FIRST -----------------
    boundary = [
        ([], 0),            # the bug case: loop never runs -> must be False
        ([True], 0),
        ([False], 0),
        ([True], 1),        # full budget, still changing -> True
        ([False], 1),       # settles immediately -> False
        ([True, True], 2),  # exhausted budget while changing -> True
        ([True, False], 2),
        ([False, True], 2),
        ([True, True, True], 3),
        ([True, True, False], 3),
    ]
    for flags, limit in boundary:
        check(flags, limit)

    # zero-budget invariant, asserted explicitly (the patched behaviour)
    for flags in ([], [True], [False], [True, False, True]):
        assert patched_summary(flags, 0) is False, "zero-budget must be False"
        assert over_budget(flags, 0) is False, "spec zero-budget must be False"

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(14493)
    n_fuzz = 20000
    for _ in range(n_fuzz):
        length = rng.randint(0, 12)
        flags = [rng.random() < 0.5 for _ in range(length)]
        limit = rng.randint(0, length)
        check(flags, limit)

    print("G-AX OK: no axioms / deep-model references to validate (mapping.md "
          "§3); modeling invariant overBudget == patched post_process summary "
          "sound on %d boundary + %d fuzz inputs (incl. zero-budget => False)."
          % (len(boundary), n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
