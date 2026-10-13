#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14493 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`passBudgetExceeded`) transliterated to Python over the *real*
              repo types via the mapping.md bijection (`Nat` ↔ non-negative
              `int`, `List Bool` ↔ `list[bool]`). There are NO A-tagged callees
              in the impl region (mapping.md §3), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `ManifestFilesMixin.post_process` summary computation, replicated
              exactly from `django/contrib/staticfiles/storage.py` AS PATCHED
              (the added `substitutions = False` before the bounded
              `for i in range(self.max_post_process_passes)` loop, the per-pass
              `substitutions = substitutions or subst`, and the early
              `if not substitutions: break`). The observable is the value of
              `substitutions` read at the trailing `if substitutions:` test —
              i.e. whether `post_process` would yield the
              'Max post-process passes exceeded.' RuntimeError.

They must agree on every Requires-satisfying input (`limit <= len(flags)`). Exit
0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample. Notably the inputs include `limit == 0`, the regression the gold
patch fixes (pre-patch this raised UnboundLocalError; the oracle below is the
PATCHED code, which returns False).

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 14493
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean passBudgetExceeded, transliterated --------
def shadow_over_budget(flags, limit):
    """passBudgetExceeded(flags, limit) transliterated to Python.
    `while i < limit and (i == 0 or flags[i-1]):  exhausted = flags[i]; i += 1`
    starting from `exhausted = False`."""
    exhausted = False
    i = 0
    while i < limit and (i == 0 or flags[i - 1]):
        exhausted = flags[i]
        i += 1
    return exhausted


# --- the ORACLE: patch.diff's behaviour (patched storage.py loop) ------------
def oracle_post_process_summary(flags, limit):
    """The value of `substitutions` read at the trailing `if substitutions:` of
    the PATCHED ManifestFilesMixin.post_process, over the abstract inputs.

    Mirrors django/contrib/staticfiles/storage.py as patched:

        substitutions = False                       # <-- the gold patch line
        for i in range(self.max_post_process_passes):
            substitutions = False
            for name, hashed_name, processed, subst in self._post_process(...):
                ...
                substitutions = substitutions or subst
            if not substitutions:
                break
        if substitutions:
            yield 'All', None, RuntimeError('Max post-process passes exceeded.')

    Per the mapping (mapping.md §2) each outer pass `i` reduces to its aggregate
    `subst` outcome, which we model as `flags[i]`.
    """
    substitutions = False
    for i in range(limit):
        substitutions = flags[i]
        if not substitutions:
            break
    return substitutions


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield ([], 0)                       # zero budget, no flags (the bug case)
    yield ([True], 0)                   # zero budget, flags present
    yield ([False], 0)
    yield ([True], 1)                   # full budget, always changing
    yield ([False], 1)                  # settles immediately
    yield ([True, True], 2)
    yield ([True, False], 2)            # changes once then settles
    yield ([False, True], 2)
    yield ([True, True, True], 3)
    yield ([True, True, False], 3)
    for _ in range(n):
        length = rng.randint(0, 12)
        flags = [rng.random() < 0.5 for _ in range(length)]
        limit = rng.randint(0, length)   # honour require: limit <= len(flags)
        yield (flags, limit)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for flags, limit in fuzz_inputs(N_FUZZ, rng):
        assert limit <= len(flags), "fuzz violated require limit <= len(flags)"
        count += 1
        shadow = shadow_over_budget(flags, limit)
        oracle = oracle_post_process_summary(flags, limit)
        if bool(shadow) != bool(oracle):
            disagreements.append((flags, limit, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for flags, limit, sh, orc in disagreements:
            print("  flags=%r limit=%r shadow=%r oracle=%r"
                  % (flags, limit, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of passBudgetExceeded agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements (incl. limit=0)."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
