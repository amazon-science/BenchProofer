#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for pytest-dev__pytest-7571.

The bundle models ONE behavior: the capture-handler level lifecycle of
`LogCaptureFixture` (mapping.md) across a test — `__init__` (initial handler
level), a sequence of `set_level(level)` calls, then `_finalize` (teardown). Its
observable is the capture handler's numeric level after teardown.

Standing up the full pytest fixture machinery to drive the real method is heavy
and unnecessary: the modeled value is a PURE function of the observables the code
reads/writes (the initial `self.handler.level` and the ordered `set_level`
levels). So the ORACLE below is a faithful in-process replica of the POST-PATCH
lifecycle (`_initial_handler_level` recorded per call + re-applied at teardown),
and the SHADOW is the op-for-op transliteration of
`implementation_captureLevel` (Solution.lean impl region), per refinement.md.

This genuinely tests the soundness-critical clause: after a test that raised the
threshold, teardown returns the handler to the level held *before* the last raise
(its initial level for a single raise) — matching the F2P expectation that a
later test sees `caplog.handler.level == 0`, not the raised value.

stdlib-only. Pinned seed: 7571 (also in mapping.md).
"""
import random
import sys

SEED = 7571
N = 120_000

# Standard logging levels plus the issue's idiosyncratic ones (41/42/43).
LEVEL_POOL = [0, 10, 20, 30, 40, 41, 42, 43, 50]


# --- ORACLE: faithful in-process replica of the POST-PATCH lifecycle ----------
class _OracleFixture:
    def __init__(self, initial_level):
        self._handler_level = initial_level
        self._initial_handler_level = None        # gold: __init__ adds this

    def set_level(self, level):
        self._initial_handler_level = self._handler_level   # gold: record-before-set
        self._handler_level = level

    def finalize(self):
        if self._initial_handler_level is not None:         # gold: re-apply
            self._handler_level = self._initial_handler_level


def oracle(inp):
    fx = _OracleFixture(inp["initialLevel"])
    for lvl in inp["levels"]:
        fx.set_level(lvl)
    fx.finalize()
    return fx._handler_level


# --- SHADOW of implementation_captureLevel (the R/I legs) ---------------------
# Mirrors Solution.lean impl region exactly: thread (handler, recorded); each
# raise records the current handler then sets it; teardown re-applies the record.
def shadow(inp):
    st = (inp["initialLevel"], None)            # (current, recorded)
    for lvl in inp["levels"]:
        st = (lvl, st[0])
    recorded = st[1]
    return recorded if recorded is not None else st[0]


def disagree(inp):
    got = oracle(inp)
    want = shadow(inp)
    if got != want:
        return (inp, got, want)
    return None


def _enumerate_edge():
    cases = []
    # F2P: one raise from a fresh (0) handler -> restored to 0 (leak fixed)
    cases.append(dict(initialLevel=0, levels=[41]))
    # no raise -> left at initial
    cases.append(dict(initialLevel=0, levels=[]))
    cases.append(dict(initialLevel=20, levels=[]))
    # two raises -> level before the LAST raise
    cases.append(dict(initialLevel=0, levels=[41, 43]))
    # three raises
    cases.append(dict(initialLevel=0, levels=[41, 42, 43]))
    # nonzero initial, single raise -> back to initial
    cases.append(dict(initialLevel=30, levels=[42]))
    # raise to the same value
    cases.append(dict(initialLevel=10, levels=[10]))
    cases.append(dict(initialLevel=10, levels=[10, 10, 10]))
    return cases


def main() -> int:
    checked = 0
    for inp in _enumerate_edge():
        d = disagree(inp)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        initial = rng.choice(LEVEL_POOL) if rng.random() < 0.8 else rng.randint(-5, 100)
        n = rng.randint(0, 6)
        levels = []
        for _ in range(n):
            levels.append(rng.choice(LEVEL_POOL) if rng.random() < 0.8
                          else rng.randint(-5, 100))
        inp = dict(initialLevel=initial, levels=levels)
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
