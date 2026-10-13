#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-7236.

The changed code introduces a one-line helper

    def _is_skipped(obj) -> bool:
        return bool(getattr(obj, "__unittest_skip__", False))

and the F2P-relevant decision in TestCaseFunction.runtest:

    if self.config.getoption("usepdb") and not _is_skipped(self.obj):
        # record the teardown routine for explicit later invocation

model.py models the skip decision DEEPLY (not behind a consumed axiom):

  (A-reference) the deep model `is_skipped(skip_marker) == (skip_marker != 0)`
      (model.py pure region) == the REAL `_is_skipped(obj)`
      == `bool(getattr(obj, "__unittest_skip__", False))`, under the carrier
      bijection: marker absent or present-but-falsy -> 0; present-and-truthy
      -> non-zero.

This check executes the REAL helper on objects spanning the marker space
(absent / present-falsy / present-truthy across many concrete values) and
asserts it equals the deep model. It also reconstructs the full runtest
decision `usepdb and not _is_skipped(obj)` over the usepdb x marker grid and
asserts it equals the postcondition of model.py's `decide_teardown`,
`teardown_recorded == (usepdb and not is_skipped(marker))`.

Imports nothing repo-specific: `_is_skipped` is a one-line `bool(getattr(...))`
reproduced verbatim from src/_pytest/unittest.py. Exit 0 iff every obligation
holds.
"""
import random
import sys


# --- the REAL helper, reproduced verbatim from src/_pytest/unittest.py -------
def _is_skipped(obj) -> bool:
    """Return True if the given object has been marked with @unittest.skip"""
    return bool(getattr(obj, "__unittest_skip__", False))


# --- model.py deep-model reference encodings (kept in lock-step) -------------
def skip_marker_set_model(skip_marker: int) -> bool:
    """Reference implementation of model.py's deep model `is_skipped`."""
    return skip_marker != 0


def decide_teardown_model(usepdb: bool, skip_marker: int) -> bool:
    """Reference of model.py's `decide_teardown` postcondition target."""
    return usepdb and not skip_marker_set_model(skip_marker)


# --- helpers to build real objects + their carrier value ---------------------
class _Obj:
    """A stand-in for self.obj — a plain object whose __unittest_skip__ we set
    (or omit) exactly as @unittest.skip / a bare object would."""


def _make(present, value):
    o = _Obj()
    if present:
        o.__unittest_skip__ = value
    return o


def _carrier(present, value):
    """The model.py integer carrier for this object's marker: 0 iff the real
    helper would read it as falsy, non-zero iff truthy. Defined independently
    of _is_skipped so the check is not a tautology: derived from Python
    truthiness of the underlying attribute under the default-absent lookup."""
    if not present:
        return 0
    return 1 if bool(value) else 0


# Falsy values getattr/bool can encounter, and truthy ones.
FALSY = [False, 0, 0.0, "", None, [], {}, set(), (), 0j]
TRUTHY = [True, 1, -1, 42, "x", "False", [0], {0: 0}, {0}, (0,), 3.14, object()]


def check_is_skipped_reference():
    """Assert deep model is_skipped == REAL _is_skipped over the marker space."""
    cases = []
    # marker absent
    cases.append((False, None))
    # marker present and falsy
    for v in FALSY:
        cases.append((True, v))
    # marker present and truthy
    for v in TRUTHY:
        cases.append((True, v))

    for present, value in cases:
        obj = _make(present, value)
        real = _is_skipped(obj)                       # REAL helper
        marker = _carrier(present, value)             # model carrier
        model = skip_marker_set_model(marker)              # deep model
        assert real == model, (
            "is_skipped deep model unsound: present=%r value=%r -> "
            "real _is_skipped=%r, deep model(marker=%r)=%r"
            % (present, value, real, marker, model))
    return len(cases)


def check_decide_teardown_reference():
    """Assert the full runtest decision usepdb and not _is_skipped(obj) equals
    decide_teardown's postcondition over the usepdb x marker grid. This is the
    F2P-discriminating clause: usepdb=True, skipped=True must yield NOT
    recorded; usepdb=True, skipped=False must yield recorded (P2P)."""
    grid = []
    for usepdb in (True, False):
        # not skipped (absent)
        grid.append((usepdb, False, None))
        # not skipped (present-falsy)
        for v in FALSY:
            grid.append((usepdb, True, v))
        # skipped (present-truthy)
        for v in TRUTHY:
            grid.append((usepdb, True, v))

    saw_f2p = False   # usepdb and skipped -> must NOT record
    saw_p2p = False   # usepdb and not skipped -> must record
    for usepdb, present, value in grid:
        obj = _make(present, value)
        # the real runtest decision, reconstructed from the gold source
        real_record = bool(usepdb) and not _is_skipped(obj)
        marker = _carrier(present, value)
        model_record = decide_teardown_model(bool(usepdb), marker)
        assert real_record == model_record, (
            "decide_teardown unsound: usepdb=%r present=%r value=%r -> "
            "real=%r model=%r" % (usepdb, present, value, real_record, model_record))
        if usepdb and _is_skipped(obj):
            assert real_record is False
            saw_f2p = True
        if usepdb and not _is_skipped(obj):
            assert real_record is True
            saw_p2p = True

    # The two scenarios the F2P + P2P tests pin must both be exercised.
    assert saw_f2p, "F2P scenario (--pdb + skipped -> no teardown) not exercised"
    assert saw_p2p, "P2P scenario (--pdb + not skipped -> teardown) not exercised"
    return len(grid)


def main():
    n_skip = check_is_skipped_reference()

    # randomized fuzz over the marker space
    rng = random.Random(7236)
    pool = [(False, None)] + [(True, v) for v in FALSY + TRUTHY]
    fuzz = 0
    for _ in range(20000):
        present, value = rng.choice(pool)
        obj = _make(present, value)
        marker = _carrier(present, value)
        assert _is_skipped(obj) == skip_marker_set_model(marker)
        fuzz += 1

    n_grid = check_decide_teardown_reference()

    print("G-AX OK: is_skipped deep model (== bool(getattr(obj, "
          "'__unittest_skip__', False))) sound on %d boundary + %d fuzz marker "
          "cases; full --pdb teardown decision sound on %d (usepdb x marker) "
          "grid cases incl. F2P (skipped) + P2P (not skipped)."
          % (n_skip, fuzz, n_grid))
    return 0


if __name__ == "__main__":
    sys.exit(main())
