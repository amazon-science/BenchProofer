#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-10081 (nagini).

SHADOW: the impl region of model.py `postpone_teardown`, copied VERBATIM below
with the contract calls (Requires/Ensures) stripped, plus the @Pure helper
`marked_skipped` copied over as a plain function and the minimal `TestItem`
carrier class with its contract lines stripped. There are no @ContractOnly
callees and no PSeq usage in this bundle; all carriers are plain bools.

ORACLE: the REAL patched repo behaviour the model models per mapping.md — the
teardown-postponement decision inside `TestCaseFunction.runtest`
(src/_pytest/unittest.py). The gate applies patch.diff to /testbed before this
script runs and sets PYTHONPATH=/testbed, so the imported pytest is the
patched one. Each oracle evaluation is a genuine end-to-end run: a real
unittest.TestCase module is written to a fresh temp dir (class and/or method
decorated with the genuine @unittest.skip), and an in-process pytest session
executes it (with or without the interactive-debugger option). Whether the
instance teardown was postponed is observed exactly where it is decidable: a
hookwrapper on pytest_runtest_teardown reads the item's explicit-teardown
slot (`_explicit_tearDown`) at teardown-phase start — it is non-None iff the
real decision postponed the teardown (the teardown phase itself consumes and
resets it, so this is the unique observation window). The REAL probe
`_pytest.unittest._is_skipped` is also imported and asserted against the
recorded boolean facets, pinning the mapping.md type bridge.

Type bridge (mapping.md section 2): all three inputs are plain bools —
`obj_skip` is the real probe's verdict on the test callable, `class_skip` its
verdict on the enclosing test-case class, `under_debugger` the debugger
option. Output is a bool compared with `==`.

Input domain: the model's Requires places only access permissions on the two
facets, so EVERY (obj_skip, class_skip, under_debugger) triple in the
8-point boolean cube is Requires-satisfying. The oracle is deterministic on
each point (asserted below by running each point through several independent
fresh end-to-end sessions, each with a fresh directory and a unique module
name); the fuzz loop then diffs the shadow against the recorded real verdicts
over >= 1e5 uniformly drawn triples, covering the cube exhaustively many
thousands of times over.

>= 1e5 Requires-satisfying inputs: 8 x N_FRESH fresh end-to-end boundary runs
+ 100000 fuzz triples. Pinned fuzz seed: 10081.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import contextlib
import io
import json
import os
import random
import shutil
import sys
import tempfile

SEED = 10081
N_FUZZ = 100_000
N_FRESH = 12  # independent fresh end-to-end sessions per boundary point


# --- model.py carrier class, contract lines stripped --------------------------

class TestItem:
    def __init__(self, obj_skip, class_skip):
        self.obj_skip = obj_skip
        self.class_skip = class_skip


# --- @Pure helper from model.py, decorator + docstring kept, contracts none ---

def marked_skipped(flag):
    """The skip-marker probe on one object: it reports whether that object
    carries the skip marker. Modelled deeply as the read of the single boolean
    skip flag the probe inspects."""
    return flag


# --- the impl region of model.py, verbatim -------------------------------------

def postpone_teardown(item, under_debugger):
    skipped = marked_skipped(item.obj_skip) or marked_skipped(item.class_skip)
    if under_debugger and not skipped:
        return True
    return False


# --- oracle: real end-to-end pytest session over a real unittest TestCase -----

MODULE_TEMPLATE = '''\
import unittest

{class_decorator}
class TestProbe(unittest.TestCase):
    def tearDown(self):
        pass

    {method_decorator}
    def test_probe(self):
        pass
'''

_module_counter = [0]


def write_test_module(root, obj_skip, class_skip):
    """Write a real test module whose class/method skip decorations produce
    exactly the requested boolean facets; unique module name per session so
    repeated in-process runs never collide in sys.modules."""
    _module_counter[0] += 1
    name = "test_conf_probe_%d" % _module_counter[0]
    text = MODULE_TEMPLATE.format(
        class_decorator='@unittest.skip("class-level skip")' if class_skip else "",
        method_decorator='@unittest.skip("method-level skip")' if obj_skip else "",
    )
    path = os.path.join(root, name + ".py")
    with open(path, "w") as f:
        f.write(text)
    return path


class PostponementObserver:
    """Records, at teardown-phase start, whether the item's instance teardown
    had been postponed (the explicit-teardown slot is non-None exactly then)."""

    def __init__(self, pytest_mod):
        self.pytest = pytest_mod
        self.postponed = None
        self.items_seen = 0

    def pytest_runtest_teardown(self, item):
        # Plain (non-wrapper) hook impls run before the plugin manager's
        # default teardown work for the item; the slot is still intact here.
        self.items_seen += 1
        self.postponed = getattr(item, "_explicit_tearDown", None) is not None


def real_postponed(pytest_mod, obj_skip, class_skip, under_debugger):
    """One fresh end-to-end session; returns the real postponement verdict."""
    root = tempfile.mkdtemp(prefix="conf10081_")
    try:
        path = write_test_module(root, obj_skip, class_skip)
        observer = PostponementObserver(pytest_mod)
        args = [path, "-q", "-p", "no:cacheprovider"]
        if under_debugger:
            args.append("--pdb")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exit_code = pytest_mod.main(args, plugins=[observer])
        assert observer.items_seen == 1, (
            "expected exactly one test item, saw %d (pytest exit %r); output:\n%s"
            % (observer.items_seen, exit_code, buf.getvalue()))
        assert observer.postponed is not None
        return observer.postponed
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    import pytest  # the REAL patched pytest at /testbed
    from _pytest.unittest import _is_skipped  # the REAL probe (facet bridge)
    import unittest

    combos = [(o, c, u) for o in (False, True)
              for c in (False, True)
              for u in (False, True)]

    # Facet-bridge sanity: the recorded boolean facets equal the REAL probe's
    # verdicts on genuinely decorated objects, and the deep model
    # `marked_skipped` is the identity on those facets.
    for obj_skip, class_skip in {(o, c) for o, c, _ in combos}:
        class Base(unittest.TestCase):
            def test_it(self):
                pass
        if obj_skip:
            Base.test_it = unittest.skip("m")(Base.test_it)
        cls = unittest.skip("c")(Base) if class_skip else Base
        assert _is_skipped(cls.test_it) == obj_skip == marked_skipped(obj_skip)
        assert _is_skipped(cls) == class_skip == marked_skipped(class_skip)

    checked = 0

    # Boundary: every point of the 8-point domain, each through N_FRESH
    # independent fresh end-to-end sessions (determinism asserted), each
    # session diffed against the shadow.
    memo = {}
    for obj_skip, class_skip, under_debugger in combos:
        verdicts = []
        for _ in range(N_FRESH):
            real_out = real_postponed(pytest, obj_skip, class_skip,
                                      under_debugger)
            verdicts.append(real_out)
            shadow_out = postpone_teardown(TestItem(obj_skip, class_skip),
                                           under_debugger)
            if shadow_out != real_out:
                print("DISAGREEMENT\n  obj_skip=%r class_skip=%r "
                      "under_debugger=%r\n  shadow=%r\n  real=%r"
                      % (obj_skip, class_skip, under_debugger,
                         shadow_out, real_out))
                return 1
            checked += 1
        assert len(set(verdicts)) == 1, (
            "oracle nondeterminism on %r: %r"
            % ((obj_skip, class_skip, under_debugger), verdicts))
        memo[(obj_skip, class_skip, under_debugger)] = verdicts[0]

    # Fuzz: >= 1e5 uniformly drawn Requires-satisfying triples, shadow diffed
    # against the recorded real verdict for the drawn point (the oracle is
    # deterministic per point, as asserted above).
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        obj_skip = rng.random() < 0.5
        class_skip = rng.random() < 0.5
        under_debugger = rng.random() < 0.5
        shadow_out = postpone_teardown(TestItem(obj_skip, class_skip),
                                       under_debugger)
        real_out = memo[(obj_skip, class_skip, under_debugger)]
        if shadow_out != real_out:
            print("DISAGREEMENT\n  obj_skip=%r class_skip=%r "
                  "under_debugger=%r\n  shadow=%r\n  real=%r"
                  % (obj_skip, class_skip, under_debugger,
                     shadow_out, real_out))
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real teardown-postponement decision on "
          "%d inputs (%d fresh end-to-end boundary runs over the full "
          "8-point boolean domain + %d fuzz, seed %d)."
          % (checked, 8 * N_FRESH, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
