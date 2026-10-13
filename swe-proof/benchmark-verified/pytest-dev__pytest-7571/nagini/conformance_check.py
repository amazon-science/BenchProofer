#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-7571 (nagini).

SHADOW: the impl regions of model.py (``CaptureController.__init__``,
``set_level``, ``teardown_restore``, ``run_raise_then_teardown``), copied
VERBATIM below with only the contract calls (Requires / Ensures / Invariant /
Assert) stripped. The pure region is empty and there are no @ContractOnly
callees (mapping.md section 3: no consumed axioms), so the shadow is plain
executable Python with no shim.

ORACLE: the REAL patched repo object the model models per mapping.md
section 1 -- ``_pytest.logging.LogCaptureFixture``, driving its ``__init__``
/ ``set_level`` / ``_finalize`` on a real ``LogCaptureHandler``. The gate
applies patch.diff to /testbed and sets PYTHONPATH=/testbed before this
script runs, so the import resolves to the patched module. The fixture is
wired to the handler through a minimal item carrying a ``_pytest.store.Store``
under ``caplog_handler_key``, exactly the wiring ``pytest_runtest_setup``
performs (same construction axiom_check.py validated in-container).

TYPE BRIDGE (mapping.md section 2):
  * ``sink_level: int``      <->  ``fixture.handler.level`` (the handler's
    integer threshold; ``handler.setLevel(L)`` <-> ``sink_level = L``)
  * ``saved_level: Optional[int]`` <-> ``fixture._initial_handler_level``
    (``None`` sentinel <-> ``None``)
  * the constructor's ``sink_level`` parameter materializes the handler's
    pre-existing ambient threshold, so the oracle sets ``handler.setLevel(
    ambient)`` before constructing the fixture.
  * the logger-level facet (``set_level``'s ``logger`` argument and the
    logger dict) is an unmodelled unchanged facet; the oracle passes a
    dedicated logger name so probes stay self-contained (``_finalize``
    restores it each lifecycle).

The observable compared after EVERY operation is the state pair
``(sink_level, saved_level)`` <-> ``(handler.level, _initial_handler_level)``.

INPUT PLAN (>= 1e5 Requires-satisfying probes; the preconditions demand only
field access, so every int is admissible): a boundary grid of (ambient, level)
threshold pairs over the stdlib level constants, the off-by-one band around
them, negatives and extremes -- each run through the full lifecycle
(init -> set -> teardown, compared after each step) plus the end-to-end
``run_raise_then_teardown`` driver and the no-set lifecycle (teardown with
nothing recorded must leave the sink untouched); then randomized fuzz
lifecycles with 1..3 level-setting operations per lifecycle (re-setting
overwrites the record in both worlds) until at least 100000 fuzz probes ran.
Pinned fuzz seed: 7571. Exit 0 iff zero disagreements; on disagreement prints
the operation sequence and both states and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 7571
N_FUZZ_TARGET = 100000
LOGGER_NAME = "sbu.conf.pytest7571"


# --- the impl regions of model.py, verbatim, contract calls stripped ---------

class CaptureController:
    def __init__(self, sink_level):
        self.saved_level = None  # type: Optional[int]
        self.sink_level = sink_level  # type: int


def set_level(self, level):
    self.saved_level = self.sink_level
    self.sink_level = level


def teardown_restore(self):
    if self.saved_level is not None:
        self.sink_level = self.saved_level


def run_raise_then_teardown(level, ambient):
    controller = CaptureController(ambient)
    set_level(controller, level)
    teardown_restore(controller)
    return controller.sink_level


# --- oracle: the real patched repo fixture (mapping.md section 1) -------------

def _oracle_bindings():
    from _pytest.logging import (LogCaptureFixture, LogCaptureHandler,
                                 caplog_handler_key)
    from _pytest.store import Store
    return LogCaptureFixture, LogCaptureHandler, caplog_handler_key, Store


class Oracle(object):
    """One real-fixture lifecycle: a fresh LogCaptureHandler at the given
    ambient threshold, wired into a fresh LogCaptureFixture the way pytest
    wires the caplog fixture."""

    def __init__(self, bindings, ambient):
        LogCaptureFixture, LogCaptureHandler, caplog_handler_key, Store = bindings
        self.handler = LogCaptureHandler()
        self.handler.setLevel(ambient)

        class _Item(object):
            pass

        item = _Item()
        item._store = Store()
        item._store[caplog_handler_key] = self.handler
        self.fixture = LogCaptureFixture(item)

    def set_level(self, level):
        self.fixture.set_level(level, logger=LOGGER_NAME)

    def finalize(self):
        self.fixture._finalize()

    def state(self):
        # the two bridged facets (mapping.md section 2)
        return (self.handler.level,
                getattr(self.fixture, "_initial_handler_level", "<missing>"))


# --- differential driver -------------------------------------------------------

class Disagreement(Exception):
    pass


def compare(trace, ctrl, oracle):
    shadow_state = (ctrl.sink_level, ctrl.saved_level)
    real_state = oracle.state()
    if shadow_state != real_state:
        raise Disagreement(
            "DISAGREEMENT after %s:\n"
            "  shadow (impl region)  (sink_level, saved_level) = %r\n"
            "  real (patched fixture) (handler.level, recorded) = %r"
            % (trace, shadow_state, real_state))


def run_lifecycle(bindings, ambient, levels):
    """One lifecycle: construct at `ambient`, apply each level-set in
    `levels`, tear down; state compared after every operation. Returns the
    number of probes compared."""
    probes = 0
    trace = "init(ambient=%r)" % (ambient,)
    ctrl = CaptureController(ambient)
    oracle = Oracle(bindings, ambient)
    compare(trace, ctrl, oracle)
    probes += 1
    for lvl in levels:
        trace += " ; set_level(%r)" % (lvl,)
        set_level(ctrl, lvl)
        oracle.set_level(lvl)
        compare(trace, ctrl, oracle)
        probes += 1
    trace += " ; teardown"
    teardown_restore(ctrl)
    oracle.finalize()
    compare(trace, ctrl, oracle)
    probes += 1
    return probes


def run_e2e(bindings, ambient, level):
    """The end-to-end driver observable: run_raise_then_teardown vs the real
    composed lifecycle's post-teardown handler threshold."""
    shadow = run_raise_then_teardown(level, ambient)
    oracle = Oracle(bindings, ambient)
    oracle.set_level(level)
    oracle.finalize()
    real = oracle.handler.level
    if shadow != real:
        raise Disagreement(
            "DISAGREEMENT on run_raise_then_teardown(level=%r, ambient=%r):\n"
            "  shadow (impl region)   = %r\n"
            "  real (patched fixture post-teardown handler level) = %r"
            % (level, ambient, shadow, real))
    return 1


def boundary_levels():
    # stdlib level constants, the off-by-one band around each, the odd
    # in-between values the suite exercises, negatives and extremes
    vals = set()
    for base in (0, 10, 20, 30, 40, 50):
        vals.update((base - 1, base, base + 1))
    vals.update((41, 42, 43, 5, 25, 35, 60, 100, 255, 1000, 10 ** 6,
                 -50, 2 ** 31, 2 ** 31 - 1))
    return sorted(vals)


def main():
    try:
        bindings = _oracle_bindings()
    except Exception as exc:  # oracle import must succeed in-container
        print("ERROR: cannot import the real patched fixture: %r" % (exc,))
        return 1

    checked = 0
    try:
        blevels = boundary_levels()
        n_boundary_pairs = 0
        for ambient in blevels:
            # no-set lifecycle: teardown with nothing recorded
            checked += run_lifecycle(bindings, ambient, [])
            for level in blevels:
                checked += run_lifecycle(bindings, ambient, [level])
                checked += run_e2e(bindings, ambient, level)
                n_boundary_pairs += 1
        # a few fixed multi-set lifecycles at the boundary (record overwrite)
        for seq in ([0, 41], [41, 0], [41, 43, 0], [50, 50], [0, 0, 0]):
            checked += run_lifecycle(bindings, 0, seq)
            checked += run_lifecycle(bindings, 30, seq)
        n_boundary = checked

        # randomized fuzz lifecycles (pinned seed)
        rng = random.Random(SEED)
        fuzz = 0
        pool = blevels + [None]  # None -> draw a fresh random int
        while fuzz < N_FUZZ_TARGET:
            def draw():
                v = rng.choice(pool)
                if v is None:
                    v = rng.randint(-10 ** 9, 10 ** 9)
                return v
            ambient = draw()
            k = rng.randint(1, 3) if rng.random() < 0.9 else 0
            levels = [draw() for _ in range(k)]
            n = run_lifecycle(bindings, ambient, levels)
            n += run_e2e(bindings, draw(), draw())
            fuzz += n
            checked += n
    except Disagreement as exc:
        print(str(exc))
        return 1

    print("G-CONF OK: shadow impl == real patched fixture on %d probes "
          "(%d boundary incl. %d (ambient,level) grid pairs + %d fuzz, "
          "seed %d); 0 disagreements."
          % (checked, n_boundary, n_boundary_pairs, fuzz, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
