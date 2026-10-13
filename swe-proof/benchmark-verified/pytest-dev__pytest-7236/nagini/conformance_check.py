#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-7236 (nagini).

SHADOW: the impl region of model.py, copied VERBATIM below with the contract
calls stripped (Requires/Ensures removed; nothing else changed), plus the
@Pure helper `skip_marker_set` copied over as a plain function and the
minimal `TestCaseItem` class with its Ensures stripped. No PSeq/PSet is used
by the model, so no collection shim is needed. There are no @ContractOnly
callees in this bundle (the skip predicate is a deep model, A-reference).

ORACLE: the REAL patched repo code the model models per mapping.md — the
teardown-recording branch of `_pytest.unittest.TestCaseFunction.runtest`.
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched package importable. `runtest` is
invoked unbound on a minimal item stub carrying exactly the attributes the
method touches (config, obj, _testcase, name, _explicit_tearDown); the
oracle observable is whether `_explicit_tearDown` was recorded (is not None
afterwards), which per mapping.md section 2 is the repo-side reading of the
model's `teardown_recorded` flag. The real introduced helper
`_pytest.unittest._is_skipped` is also diffed directly against the deep
model `skip_marker_set` under the carrier bijection.

Type bridge (mapping.md section 2):
  - `postmortem_mode: bool`  <-> the truthy "usepdb" config option value
    (the stub config returns the flag from getoption("usepdb")).
  - `skip_marker: int`       <-> the value read from the marker attribute
    under a default-absent lookup on the item's test object: carrier 0 iff
    the marker is absent or present-but-falsy, non-zero iff present with a
    truthy value. The carrier is computed independently of the real helper
    (from Python truthiness of the underlying attribute), so the diff is
    not a tautology.
  - `teardown_recorded: bool` <-> the teardown routine was recorded for
    explicit later invocation (`_explicit_tearDown is not None` after
    `runtest`).

Input domain: every (mode flag, marker configuration) pair is one
Requires-satisfying input (the shadow item starts with
teardown_recorded == False, exactly the precondition; the stub starts with
_explicit_tearDown = None, the repo-side equivalent). Boundary cases: both
flag values crossed with marker absent, every stock falsy value, and a
spread of truthy values (bool/int/str/collections/object). Fuzz: random
marker presence x random values incl. large/negative ints, plus random
flag, until >= 1e5 total comparisons.

Pinned fuzz seed: 72360 (recorded here).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs, then exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 72360
TARGET_CHECKS = 100_000


# --- model.py class, Ensures stripped ------------------------------------------

class TestCaseItem:
    def __init__(self, postmortem_mode, skip_marker):
        self.postmortem_mode = postmortem_mode
        self.skip_marker = skip_marker
        self.teardown_recorded = False


# --- @Pure helper from model.py, decorator stripped ----------------------------

def skip_marker_set(skip_marker):
    return skip_marker != 0


# --- the impl region of model.py, verbatim, contracts stripped -----------------

def decide_teardown(item):
    if item.postmortem_mode and not skip_marker_set(item.skip_marker):
        item.teardown_recorded = True


# --- oracle bridge --------------------------------------------------------------

MARKER_ATTR = "__unittest_skip__"


class _Config:
    """Stub config: getoption('usepdb') returns the post-mortem flag;
    getvalue('trace') returns False so the tracing pre-step is a no-op."""

    def __init__(self, usepdb):
        self._usepdb = usepdb

    def getoption(self, name):
        assert name == "usepdb"
        return self._usepdb

    def getvalue(self, name):
        return False


class _TestCaseStub:
    """Minimal stand-in for the wrapped test-case instance: exposes the
    tearDown routine the recording branch captures, and is callable with
    result=... as a no-op (the run itself is outside the modeled boundary)."""

    def tearDown(self):
        pass

    def __call__(self, result=None):
        pass


def _make_obj(present, value):
    """A plain sync test function carrying (or not) the skip marker,
    exactly the object the marker lookup reads."""
    def f():
        pass
    if present:
        setattr(f, MARKER_ATTR, value)
    return f


def _carrier(present, value):
    """The model.py integer carrier for this marker configuration: 0 iff
    absent or present-but-falsy, non-zero iff present-and-truthy. Derived
    from Python truthiness of the underlying attribute, independently of
    the real helper, so the diff is not circular. Non-zero ints keep their
    own value (any non-zero int is a valid truthy carrier)."""
    if not present:
        return 0
    if isinstance(value, int) and not isinstance(value, bool):
        return value  # 0 stays 0 (falsy); non-zero keeps its value
    return 1 if bool(value) else 0


# Falsy values the marker attribute can hold, and truthy ones.
FALSY = [False, 0, 0.0, "", None, [], {}, set(), (), 0j]
TRUTHY = [True, 1, -1, 42, 2 ** 63, "x", "False", [0], {0: 0}, {0}, (0,),
          3.14, object()]


def main():
    from _pytest.unittest import TestCaseFunction, _is_skipped

    checked = 0

    def real_recorded(usepdb, obj):
        """Run the REAL patched runtest on a minimal item stub and report
        whether the teardown routine was recorded for later invocation."""
        item = TestCaseFunction.__new__(TestCaseFunction)
        item.config = _Config(usepdb)
        item.obj = obj
        item.name = "check_case"
        item._testcase = _TestCaseStub()
        item._explicit_tearDown = None  # repo-side "not yet recorded"
        TestCaseFunction.runtest(item)
        return item._explicit_tearDown is not None

    def check(usepdb, present, value, label):
        nonlocal checked
        obj = _make_obj(present, value)
        marker = _carrier(present, value)

        # real helper vs deep model over the same marker configuration
        helper_real = _is_skipped(obj)
        helper_model = skip_marker_set(marker)
        if helper_real != helper_model:
            print("DISAGREEMENT (marker predicate) on %s\n"
                  "  present=%r value=%r carrier=%r\n"
                  "  real=%r shadow=%r"
                  % (label, present, value, marker, helper_real, helper_model))
            sys.exit(1)

        # full recording decision: real runtest vs shadow impl
        real = real_recorded(usepdb, obj)
        shadow_item = TestCaseItem(bool(usepdb), marker)
        decide_teardown(shadow_item)  # precondition: teardown_recorded False
        shadow = shadow_item.teardown_recorded
        if real != shadow:
            print("DISAGREEMENT (recording decision) on %s\n"
                  "  usepdb=%r present=%r value=%r carrier=%r\n"
                  "  real recorded=%r shadow teardown_recorded=%r"
                  % (label, usepdb, present, value, marker, real, shadow))
            sys.exit(1)
        checked += 2  # one predicate comparison + one decision comparison

    # --- boundary grid: both flags x marker space --------------------------------
    for usepdb in (True, False):
        check(usepdb, False, None, "boundary:absent")
        for v in FALSY:
            check(usepdb, True, v, "boundary:falsy=%r" % (v,))
        for v in TRUTHY:
            check(usepdb, True, v, "boundary:truthy=%r" % (v,))

    n_boundary = checked

    # --- randomised fuzz until >= TARGET_CHECKS ----------------------------------
    rng = random.Random(SEED)
    pool = FALSY + TRUTHY
    trial = 0
    while checked < TARGET_CHECKS:
        usepdb = rng.random() < 0.5
        shape = rng.randrange(4)
        if shape == 0:
            present, value = False, None
        elif shape == 1:
            present, value = True, rng.choice(pool)
        elif shape == 2:
            present, value = True, rng.randint(-(2 ** 40), 2 ** 40)
        else:
            present, value = True, rng.choice([0, 1, -1, True, False])
        check(usepdb, present, value, "fuzz#%d" % trial)
        trial += 1

    print("G-CONF OK: shadow impl == real recording decision on %d comparisons "
          "(%d boundary, %d fuzz trials, seed %d); marker-predicate and "
          "full-decision diffs both clean." % (checked, n_boundary, trial, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
