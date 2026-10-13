#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for pytest-dev__pytest-7236.

The bundle models ONE decision: whether teardown postponement is arranged for a
`unittest`-style test case inside `TestCaseFunction.runtest` (mapping.md). The
modeled value is a PURE Boolean function of three observables the real method
reads:

    isAsync  -- is_async_function(self.obj)            (selects the if/else branch)
    usePdb   -- bool(self.config.getoption("usepdb"))  (the --pdb option)
    skipped  -- _is_skipped(self.obj)
                 == bool(getattr(self.obj, "__unittest_skip__", False))

Post-patch rule (the gold edit ADDS `and not _is_skipped(self.obj)` to the
synchronous-path guard; the async branch never reaches the postponement code):

    if isAsync:                      result = False
    elif usePdb and not skipped:     result = True
    else:                            result = False

Standing up the full pytest collection + a live TestCase under --pdb to observe
whether `tearDown` was replaced is heavy and unnecessary: the modeled value is
this pure decision over observables the real method exposes. So the ORACLE below
is a faithful in-process replica of the POST-PATCH guard, and the SHADOW is the
op-for-op transliteration of `implementation_deferTeardown` (Solution.lean impl
region), per refinement.md.

This genuinely tests the soundness-critical clause: a skipped case under the
debugger option (isAsync=False, usePdb=True, skipped=True) must NOT have its
teardown postponed — matching the F2P expectation
(`test_pdb_teardown_skipped[@unittest.skip]`: tracked == []).

The input space is only 8 points (three Booleans); it is enumerated exhaustively
in addition to a seeded fuzz loop. stdlib-only. Pinned seed: 7236 (also in
mapping.md).
"""
import itertools
import random
import sys

SEED = 7236
N = 200_000


# --- ORACLE: faithful in-process replica of the POST-PATCH guard --------------
def oracle(isAsync, usePdb, skipped):
    if isAsync:
        return False
    if usePdb and not skipped:
        return True
    return False


# --- SHADOW of implementation_deferTeardown (the R/I leg) ---------------------
# Mirrors Solution.lean impl region exactly.
def shadow(isAsync, usePdb, skipped):
    if isAsync:
        return False
    if usePdb and (not skipped):
        return True
    return False


def disagree(inp):
    got = oracle(*inp)
    want = shadow(*inp)
    if got != want:
        return (inp, got, want)
    return None


def main() -> int:
    checked = 0

    # Exhaustive enumeration of the 8-point input space.
    for inp in itertools.product([False, True], repeat=3):
        d = disagree(inp)
        if d:
            print(f"DISAGREE exhaustive: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    # Seeded fuzz (redundant given exhaustion, kept for the gate convention).
    rng = random.Random(SEED)
    for _ in range(N):
        inp = (rng.random() < 0.5, rng.random() < 0.5, rng.random() < 0.5)
        d = disagree(inp)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
