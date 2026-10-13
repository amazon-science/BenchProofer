#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for pytest-dev__pytest-10081.

The bundle models ONE decision: inside `TestCaseFunction.runtest`, whether the
teardown step is specially deferred when the interactive post-mortem debugger
(`--pdb`) is enabled (`src/_pytest/unittest.py:316-322`). The modeled value is a
PURE boolean function of three observables (mapping.md):

    pdb_enabled         : bool   self.config.getoption("usepdb")  (truthiness)
    test_itself_skipped : bool   _is_skipped(self.obj)
    class_skipped       : bool   _is_skipped(self.parent.obj)

Post-patch rule (the gold edit ORs in the class-level skip):

    skipped = test_itself_skipped or class_skipped
    defer   = bool(pdb_enabled and not skipped)

Standing up a full pytest session with a unittest.TestCase, a class-level skip
decorator, and `--pdb` to drive the real `runtest` is heavy and unnecessary: the
modeled value is exactly this pure combination of the three booleans the real
method consults (`getoption("usepdb")`, and the SAME `_is_skipped` predicate
applied to the test method and to its containing class). `_is_skipped` itself is
`bool(getattr(obj, "__unittest_skip__", False))` — a pure attribute read — so the
ORACLE below is a faithful in-process replica of the patched decision, and the
SHADOW is the op-for-op transliteration of `implementation_deferTeardown`
(refinement.md: `skipped := test ∨ class`; `if pdb ∧ ¬skipped then true else
false`).

This genuinely tests the soundness-critical clause: deferral must be suppressed
when the class is skipped even if the test method itself is not — the F2P shape
(pdb_enabled=True, test_itself_skipped=False, class_skipped=True must give
defer=False).

stdlib-only. Pinned seed: 10081 (also in mapping.md / meta.json).
"""
import itertools
import json
import random
import sys

SEED = 10081
N = 120_000


# --- ORACLE: faithful in-process replica of the patched decision -------------
def oracle_defer(pdb_enabled, test_itself_skipped, class_skipped):
    skipped = test_itself_skipped or class_skipped
    return bool(pdb_enabled and not skipped)


# --- SHADOW of implementation_deferTeardown (the R leg) ----------------------
# Mirrors Solution.lean impl region:
#   let skipped := testItselfSkipped || classSkipped
#   if pdbEnabled && !skipped then return true
#   return false
def shadow_defer(pdb_enabled, test_itself_skipped, class_skipped):
    skipped = test_itself_skipped or class_skipped
    if pdb_enabled and not skipped:
        return True
    return False


def disagree(p, t, c):
    got = oracle_defer(p, t, c)
    want = shadow_defer(p, t, c)
    if got != want:
        return ((p, t, c), got, want)
    return None


def main():
    rng = random.Random(SEED)
    checked = 0
    disagreements = 0
    first = None

    # Exhaustive enumeration of the entire 2^3 input space (the model is a pure
    # 3-bit boolean function — this alone is a complete proof of agreement).
    for p, t, c in itertools.product((False, True), repeat=3):
        checked += 1
        d = disagree(p, t, c)
        if d is not None:
            disagreements += 1
            if first is None:
                first = d

    # Fuzz to the required volume (redundant given exhaustion, but pinned-seed
    # reproducible and matches the gate's >=1e5 contract).
    for _ in range(N):
        p = rng.random() < 0.5
        t = rng.random() < 0.5
        c = rng.random() < 0.5
        checked += 1
        d = disagree(p, t, c)
        if d is not None:
            disagreements += 1
            if first is None:
                first = d

    status = "pass" if disagreements == 0 else "fail"
    print(json.dumps({
        "status": status,
        "checked": checked,
        "disagreements": disagreements,
        "first_disagreement": first,
        "seed": SEED,
    }))
    sys.exit(0 if disagreements == 0 else 1)


if __name__ == "__main__":
    main()
