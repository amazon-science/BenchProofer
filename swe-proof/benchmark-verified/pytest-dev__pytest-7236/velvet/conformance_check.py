#!/usr/bin/env python3
"""G-CONF differential conformance for pytest-dev__pytest-7236 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs. This
bundle has NO axiomatized callees, so the entire impl region of both modeled
methods is R/I and is covered here; there is nothing for G-AX (no axiom_check.py)
and no A-tagged callee left as a real-repo call.

Two coupled sites, each a pure boolean decision:

  * SITE B — `markedSkipped`: whether the object bears the skip mark, i.e. the
    new helper `_is_skipped(obj)`.
  * SITE A — `teardownPostponed`: whether `TestCaseFunction.runtest` defers the
    test's teardown (sets `_explicit_tearDown` + stubs `tearDown`), observable
    as the real `tearDown` being deferred-then-run vs. never running.

ORACLE CHOICE — why we transliterate the patched source expressions instead of
driving live pytest sessions:
  The patched booleans live inside `TestCaseFunction.runtest`, reached only
  through a full pytest collection + runtest protocol with `--pdb`, an
  `unittest.TestCase` subclass, a configured `Config`, and the debugging plugin.
  Building that machinery in-container purely to read back two booleans is
  impractical and would not isolate the modeled behaviour. So, per the worker
  prompt, the ORACLE for each site is the patched source expression
  transliterated VERBATIM from the gold patch:

    site B (src/_pytest/unittest.py, _is_skipped):
        return bool(getattr(obj, "__unittest_skip__", False))
    site A (src/_pytest/unittest.py, runtest):
        # reached only in the non-async branch:
        #   if is_async_function(self.obj): self._testcase(self)   # no deferral
        #   else:
        #       if self.config.getoption("usepdb") and not _is_skipped(self.obj):
        #           <defer teardown>
        postpone = (not async_test) and (usepdb and not is_skipped)

  The SHADOW for each site is the modeled formula from Solution.lean's
  post-image. We differential-test SHADOW vs ORACLE exhaustively over the
  boolean cube (1 input for site B, 3 for site A) plus seeded fuzz. Exit 0 iff
  zero disagreements. stdlib only.
"""
import itertools
import random
import sys

SEED = 7236
N_FUZZ = 100_000


# --- SITE B: markedSkipped (== _is_skipped) ----------------------------------

def shadow_marked_skipped(skip_marked):
    """markedSkipped transliterated: `return skipMarked`."""
    return skip_marked


def oracle_marked_skipped(skip_marked):
    """Patched source `_is_skipped(obj)`:
        return bool(getattr(obj, "__unittest_skip__", False))
    `skip_marked` bridges the truthiness of the skip-mark attribute
    (mapping.md §2): an object whose `__unittest_skip__` is truthy <-> True."""

    class _Obj:
        pass

    obj = _Obj()
    if skip_marked:
        obj.__unittest_skip__ = True   # truthy mark present
    # else: attribute absent -> getattr default False
    return bool(getattr(obj, "__unittest_skip__", False))


# --- SITE A: teardownPostponed -----------------------------------------------

def shadow_teardown_postponed(async_test, debugger_active, skip_marked):
    """teardownPostponed transliterated:
    `!asyncTest && debuggerActive && !markedSkipped(skipMarked)`."""
    skipped = shadow_marked_skipped(skip_marked)
    return (not async_test) and debugger_active and (not skipped)


def oracle_teardown_postponed(async_test, debugger_active, skip_marked):
    """Patched source (TestCaseFunction.runtest), transliterated verbatim.
    The deferral is reached only in the non-async else-branch; inside it the
    guard is `usepdb and not _is_skipped(self.obj)`. `debugger_active` bridges
    `self.config.getoption("usepdb")`, `async_test` bridges
    `is_async_function(self.obj)`, `skip_marked` bridges the skip mark read by
    `_is_skipped(self.obj)` (mapping.md §2)."""
    if async_test:
        # `if is_async_function(self.obj): self._testcase(self)` -> no deferral
        return False
    # else branch:
    is_skipped = oracle_marked_skipped(skip_marked)
    if debugger_active and not is_skipped:
        return True   # deferral branch taken
    return False


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # --- SITE B: exhaustive over the 1 boolean input + fuzz ------------------
    site_b = list(itertools.product([False, True], repeat=1))
    site_b += [(rng.random() < 0.5,) for _ in range(N_FUZZ)]
    for (sm,) in site_b:
        count += 1
        s = bool(shadow_marked_skipped(sm))
        o = bool(oracle_marked_skipped(sm))
        if s != o:
            disagreements.append(("markedSkipped", sm, s, o))
            if len(disagreements) >= 5:
                break

    # --- SITE A: exhaustive over the 2^3 = 8 boolean inputs + fuzz -----------
    if len(disagreements) < 5:
        site_a = list(itertools.product([False, True], repeat=3))
        site_a += [tuple(rng.random() < 0.5 for _ in range(3))
                   for _ in range(N_FUZZ)]
        for async_test, debugger_active, skip_marked in site_a:
            count += 1
            s = bool(shadow_teardown_postponed(
                async_test, debugger_active, skip_marked))
            o = bool(oracle_teardown_postponed(
                async_test, debugger_active, skip_marked))
            if s != o:
                disagreements.append((
                    "teardownPostponed",
                    (async_test, debugger_active, skip_marked), s, o))
                if len(disagreements) >= 5:
                    break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadows of markedSkipped and teardownPostponed agree "
          "with the patched source expressions on %d inputs "
          "(2 + 8 exhaustive + fuzz, seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
