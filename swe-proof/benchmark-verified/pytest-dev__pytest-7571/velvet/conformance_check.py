#!/usr/bin/env python3
r"""G-CONF differential conformance check for pytest-dev__pytest-7571 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (`self.handler.level` <-> FixtureState.level : Int;
              `self._initial_handler_level` <-> savedLevel : Option Int). The
              shadow is `restoreState ∘ setLevelState* ∘ initState` (the
              `runLifecycle` postcondition generalized to a sequence of sets):
                  initState lvl0      : level=lvl0,  savedLevel=None
                  setLevelState lvl   : level=lvl,   savedLevel=prev level
                  restoreState        : if savedLevel is not None: level=savedLevel
              There are NO A-tagged callees in the computed output (no consumed
              axioms — refinement.md §C), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: a real patched `LogCaptureFixture`
              constructed against a dummy node, driven through the same
              `set_level(...)*` then `_finalize()` cycle; we read
              `fixture.handler.level` (the real correctness oracle, G-RESOLVE).
              The harness applies patch.diff at base_commit before this runs.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + pytest's
own `_pytest` package only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import logging
import random
import sys

SEED = 7571
N_FUZZ = 100_000

# Level values to fuzz over: 0 (NOTSET / ambient) plus a spread of the kind of
# integer levels set_level accepts. Includes the F2P-tested 41/43.
LEVELS = [0, 1, 10, 20, 30, 40, 41, 42, 43, 50, 99]


# --- SHADOW: restoreState . setLevelState* . initState -----------------------
def shadow(lvl0, set_seq):
    level = lvl0
    saved = None  # Option Int  (None == none)
    for lvl in set_seq:
        saved = level          # setLevelState: record level currently in effect
        level = lvl            # then move to requested level
    if saved is not None:      # restoreState: reinstate iff one was recorded
        level = saved
    return level


# --- ORACLE: patched real LogCaptureFixture lifecycle ------------------------
def _make_fixture():
    """Build a real LogCaptureFixture with a real LogCaptureHandler wired into
    a minimal item whose `_store` exposes the handler under caplog_handler_key,
    exactly as the runtime does (logging.py:683-684)."""
    from _pytest.logging import (
        LogCaptureFixture,
        LogCaptureHandler,
        caplog_handler_key,
    )
    from _pytest.store import Store

    class _DummyItem:
        def __init__(self):
            self._store = Store()

    item = _DummyItem()
    handler = LogCaptureHandler()
    item._store[caplog_handler_key] = handler
    return LogCaptureFixture(item)


def oracle(lvl0, set_seq):
    fixture = _make_fixture()
    # Establish the ambient handler level (a fresh handler is NOTSET==0; allow
    # the shadow's general lvl0 by setting the handler directly first).
    fixture.handler.setLevel(lvl0)
    for lvl in set_seq:
        fixture.set_level(lvl)
    fixture._finalize()
    return fixture.handler.level


def inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield (0, [])                 # ambient, no set -> finalize is a no-op
    yield (0, [41])               # the F2P single-set case (test1/test3)
    yield (0, [43])
    yield (0, [42])               # the issue's minimal example
    yield (0, [10, 20])           # two sets: restore to the FIRST set's level
    yield (0, [41, 43, 50])       # three sets
    yield (20, [])                # non-zero ambient, no set
    yield (20, [40])              # non-zero ambient, one set
    for _ in range(n):
        lvl0 = rng.choice(LEVELS)
        k = rng.randint(0, 4)
        seq = [rng.choice(LEVELS) for _ in range(k)]
        yield (lvl0, seq)


def main():
    rng = random.Random(SEED)
    try:
        _make_fixture()  # import / wiring guard
    except Exception as e:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not build patched LogCaptureFixture: %r" % e)
        return 2

    disagreements = []
    count = 0
    for lvl0, seq in inputs(N_FUZZ, rng):
        count += 1
        sh = shadow(lvl0, seq)
        try:
            orc = oracle(lvl0, seq)
        except Exception as e:
            disagreements.append(((lvl0, seq), sh, "ORACLE-RAISED:%r" % e))
            if len(disagreements) >= 5:
                break
            continue
        if sh != orc:
            disagreements.append(((lvl0, seq), sh, orc))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for inp, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of runLifecycle (restoreState . setLevelState* "
          ". initState) agrees with patch.diff (patched LogCaptureFixture "
          "set_level/_finalize) on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
