#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-10081 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outcomes:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`shouldDeferCleanup`, routed through the deep model `shouldDefer`)
              transliterated to Python over the real repo types. There are NO
              A-tagged callees in the impl region (no axioms), so the shadow is
              pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched postponement guard inside
              `TestCaseFunction.runtest`, i.e. the gold line
                  skipped = _is_skipped(self.obj) or _is_skipped(self.parent.obj)
                  postpone = usepdb and not skipped
              evaluated with the *real* `_pytest.unittest._is_skipped` callee
              (G-RESOLVE applies the gold patch before this runs). The observable
              per mapping.md §2 is the boolean `postpone` (whether the cleanup
              step is deferred).

The two boolean inputs `unitSkipped` / `groupSkipped` are not fed to the oracle
directly: they are realised as actual objects whose skip marker attribute
(`__unittest_skip__`) is set in a variety of truthy/falsy encodings, and the
oracle observes them THROUGH the real `_is_skipped`. This refutes the R-identity
of steps 2/3 (real `_is_skipped(obj) ↔ Bool input`) as well as the I boolean
composition. They must agree on every input. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 10081
N_FUZZ = 100_000

# The real, unchanged callee (patch adds a second call site but does not alter
# the function). Importing the module is safe: `_is_skipped` is a leaf helper
# that only reads an attribute.
from _pytest.unittest import _is_skipped


# --- realising a Bool input as a real object the oracle observes via _is_skipped
# Encodings whose `bool(getattr(obj, "__unittest_skip__", False))` is True.
_SKIPPED_ENCODINGS = [True, 1, "x", object(), [0], (None,)]
# Encodings whose result is False (including the attribute being absent).
_NOTSKIPPED_ENCODINGS = ["__ABSENT__", False, 0, "", None, [], ()]


def make_obj(skipped, rng):
    """Build an object carrying a skip-marker encoding consistent with `skipped`,
    sampling across truthy/falsy / missing-attribute encodings so the R-identity
    of `_is_skipped` is exercised, not just the bool."""
    enc = rng.choice(_SKIPPED_ENCODINGS if skipped else _NOTSKIPPED_ENCODINGS)
    obj = type("Marker", (), {})()
    if enc != "__ABSENT__":
        obj.__unittest_skip__ = enc
    return obj


# --- the R/I shadow: Solution.lean shouldDefer / shouldDeferCleanup -----------
def shadow_should_defer(debugger_active, unit_skipped, group_skipped):
    """shouldDefer (pure region) / shouldDeferCleanup impl transliterated."""
    skipped = unit_skipped or group_skipped          # step 4 (I)
    return bool(debugger_active and not skipped)      # step 5 (I)


def oracle_should_defer(debugger_active, unit_obj, group_obj):
    """patch.diff's behaviour: the gold guard line, evaluated with the real
    `_is_skipped` over the realised objects."""
    skipped = _is_skipped(unit_obj) or _is_skipped(group_obj)
    return bool(debugger_active and not skipped)


def fuzz_inputs(n, rng):
    # boundary: full 2**3 cross product of (debugger, unit, group) bools first
    for d in (False, True):
        for u in (False, True):
            for g in (False, True):
                yield (d, u, g)
    # then randomized re-sampling to exceed the fuzz floor deterministically
    for _ in range(n):
        yield (rng.random() < 0.5, rng.random() < 0.5, rng.random() < 0.5)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for d, u, g in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_should_defer(d, u, g)
        # realise the two skip-bools as real objects observed through _is_skipped
        oracle = oracle_should_defer(d, make_obj(u, rng), make_obj(g, rng))
        if shadow != oracle:
            disagreements.append((d, u, g, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for d, u, g, sh, orc in disagreements:
            print("  debugger=%r unit=%r group=%r shadow=%r oracle=%r"
                  % (d, u, g, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of shouldDeferCleanup agrees with patch.diff "
          "behaviour (real _is_skipped) on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
