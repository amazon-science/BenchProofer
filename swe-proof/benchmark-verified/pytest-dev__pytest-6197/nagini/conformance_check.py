#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-6197 (nagini).

SHADOW: the impl region of model.py, copied VERBATIM below with only the
contract calls (Requires/Ensures/Invariant/Assert/MustTerminate) stripped:
``access_object`` (the guarded load-on-demand transition) and
``enumerate_children`` (the no-load discovery phase), plus the ``Container``
carrier whose constructor establishes ``loaded=False, load_count=0``. The
pure and axioms regions are empty and there are no @ContractOnly callees
(mapping.md section 3: the load primitive is modelled deeply in-line).

ORACLE: the REAL patched repo functions the model models per mapping.md
section 1 — ``_pytest.python.PyobjMixin.obj`` (the property getter; the
access phase) and ``_pytest.python.Package.collect`` (the discovery phase),
driven on real ``Package`` collector nodes built over on-disk package
layouts. The gate applies patch.diff to /testbed and sets
PYTHONPATH=/testbed before this script runs, so ``import _pytest`` resolves
to the patched source tree.

TYPE BRIDGE (mapping.md section 2): the repo state is the collector node's
lazily-mounted ``_obj`` attribute and the side effect of ``_getobj()``; the
model carrier is ``Container(loaded: bool, load_count: int)``.
  * ``loaded``      <->  ``getattr(node, "_obj", None) is not None``
  * ``load_count``  <->  number of executions of ``node._getobj`` (observed
                         by wrapping the bound method with a counting shim;
                         the counter's origin is an arbitrary k >= 0 because
                         the contracts constrain only deltas from Old(...)).
  * ``access_object(c)``      <->  reading ``node.obj``
  * ``enumerate_children(c)`` <->  draining the ``node.collect()`` generator
  * ``Container()``           <->  a freshly constructed ``Package`` node

Requires-satisfying inputs are (loaded, load_count) states with
load_count >= 0, crossed with op sequences. Real-side realization of an
initial state: fresh node (loaded=False); ``node.obj = module`` via the real
setter or one genuine first read of ``node.obj`` (loaded=True); the counter
is then re-based to the chosen k. A "attribute present but None" variant of
the unloaded state is also realized (the bridge maps ``_obj is None`` to
unloaded regardless of attribute presence). The model's in-line load
transition denotes a COMPLETING load, so genuine first reads are only issued
on layouts whose package body imports cleanly; a layout whose package body
raises is still exercised through the discovery phase (where the oracle must
not trigger it at all) and through already-mounted access.

INPUT PLAN (>= 1e5 Requires-satisfying inputs): 10 boundary package layouts
+ 24 fuzz layouts; boundary trials sweep every layout x initial-state
realization x a fixed op-sequence menu; fuzz trials draw random layout,
initial state (k in 0..1000) and op sequence (length 2..5) until at least
100000 post-op state comparisons have been checked. Pinned seed: 6197.
Exit 0 iff zero disagreements; on disagreement prints the input and both
states and exits 1. stdlib only.
"""
import json
import os
import random
import sys
import tempfile
import types

SEED = 6197
N_TARGET = 100000


# --- shadow carrier: model.py Container, contract lines stripped --------------

class Container(object):
    def __init__(self):
        self.loaded = False        # underlying object not yet loaded
        self.load_count = 0        # number of load side effects performed


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def access_object(c):
    if not c.loaded:
        c.loaded = True
        c.load_count = c.load_count + 1


def enumerate_children(c):
    # Enumeration of children proceeds without touching the container's own
    # underlying object; no load is triggered here.
    pass


# --- oracle: real patched collector nodes -------------------------------------

class Oracle(object):
    """Boots one real pytest config/session over a scratch root and builds
    the package layouts the probes run against."""

    def __init__(self):
        os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        import _pytest.config as _config
        from _pytest.main import Session
        from _pytest.python import Package
        import py
        self._Package = Package
        self._py = py
        self.root = tempfile.mkdtemp(prefix="conf6197_")
        self.layouts = self._build_layouts(self.root)
        config = _config._prepareconfig([self.root, "-p", "no:cacheprovider"])
        self.session = Session(config)

    def _build_layouts(self, root):
        def mk(name, files, raising=False):
            base = os.path.join(root, name)
            os.makedirs(base)
            for rel, content in files:
                path = os.path.join(base, rel)
                d = os.path.dirname(path)
                if not os.path.isdir(d):
                    os.makedirs(d)
                with open(path, "w") as f:
                    f.write(content)
            return {"name": name,
                    "init": os.path.join(base, "__init__.py"),
                    "raising": raising}

        layouts = []
        # boundary layouts
        layouts.append(mk("pkg_empty", [("__init__.py", "")]))
        layouts.append(mk("pkg_one_test", [
            ("__init__.py", ""),
            ("test_a.py", "def test_a():\n    assert True\n")]))
        layouts.append(mk("pkg_nonmatching", [
            ("__init__.py", ""),
            ("util.py", "X = 1\n")]))
        layouts.append(mk("pkg_plaindir", [
            ("__init__.py", ""),
            ("data/notes.txt", "n\n")]))
        layouts.append(mk("pkg_nested", [
            ("__init__.py", ""),
            ("sub/__init__.py", ""),
            ("sub/test_b.py", "def test_b():\n    assert True\n")]))
        layouts.append(mk("pkg_raising", [
            ("__init__.py", "raise RuntimeError('package body side effect')\n"),
            ("test_c.py", "def test_c():\n    assert True\n")],
            raising=True))
        layouts.append(mk("pkg_marked", [
            ("__init__.py",
             "import pytest\npytestmark = pytest.mark.slow\n"),
            ("test_d.py", "def test_d():\n    assert True\n")]))
        layouts.append(mk("pkg_many", [("__init__.py", "")] + [
            ("test_m%d.py" % i, "def test_m%d():\n    assert True\n" % i)
            for i in range(10)]))
        layouts.append(mk("pkg_mixed", [
            ("__init__.py", "VALUE = 42\n"),
            ("test_e.py", "def test_e():\n    assert True\n"),
            ("helper.py", "Y = 2\n"),
            ("data/blob.bin", "b\n")]))
        layouts.append(mk("pkg_deep", [
            ("__init__.py", ""),
            ("inner/__init__.py", ""),
            ("inner/deeper/__init__.py", ""),
            ("inner/deeper/test_f.py", "def test_f():\n    assert True\n")]))
        # fuzz layouts (deterministic: dedicated seeded rng)
        rng = random.Random(SEED + 1)
        for i in range(24):
            files = [("__init__.py", "")]
            for j in range(rng.randint(0, 5)):
                files.append(("test_f%02d_%d.py" % (i, j),
                              "def test_f%02d_%d():\n    assert True\n"
                              % (i, j)))
            for j in range(rng.randint(0, 3)):
                files.append(("mod_f%02d_%d.py" % (i, j), "Z = %d\n" % j))
            if rng.random() < 0.4:
                files.append(("subpkg/__init__.py", ""))
                files.append(("subpkg/test_s%02d.py" % i,
                              "def test_s%02d():\n    assert True\n" % i))
            if rng.random() < 0.3:
                files.append(("plain/afile.txt", "t\n"))
            layouts.append(mk("pkg_fz%02d" % i, files))
        return layouts

    def fresh_node(self, layout):
        """A fresh collector node over the layout, with the load primitive
        wrapped by a counting shim (the load_count observable)."""
        node = self._Package(self._py.path.local(layout["init"]), self.session)
        real_getobj = node._getobj
        counter = [0]

        def counting_getobj():
            counter[0] += 1
            return real_getobj()

        node._getobj = counting_getobj
        return node, counter


class RealContainer(object):
    """One realized Requires-satisfying input on the oracle side."""

    def __init__(self, oracle, layout, loaded, k, realize):
        self.layout = layout
        self.node, self.counter = oracle.fresh_node(layout)
        if loaded:
            if realize == "genuine":
                _ = self.node.obj          # one real first read mounts it
            else:
                self.node.obj = types.ModuleType("conf6197_mounted")
        elif realize == "none_attr":
            self.node.obj = None           # attribute present, still unmounted
        self.counter[0] = k                # counter origin is arbitrary k >= 0

    def observe(self):
        return (getattr(self.node, "_obj", None) is not None, self.counter[0])

    def enumerate(self):
        for _ in self.node.collect():
            pass

    def access(self):
        _ = self.node.obj


# --- differential driver -------------------------------------------------------

def report(layout, realize, history, op, shadow, real):
    print("DISAGREEMENT")
    print("  layout       = %s (raising=%s)" % (layout["name"],
                                                layout["raising"]))
    print("  realization  = %s" % (realize,))
    print("  ops so far   = %r (failing op: %s)" % (history, op))
    print("  shadow state = (loaded=%s, load_count=%d)" % shadow)
    print("  real state   = (loaded=%s, load_count=%d)" % real)


def run_trial(oracle, layout, loaded, k, realize, ops, counter_box):
    """Apply one op sequence to shadow and real from the same initial state;
    compare (loaded, load_count) after realization and after every op.
    Returns True on agreement throughout."""
    c = Container()
    c.loaded = loaded
    c.load_count = k
    rc = RealContainer(oracle, layout, loaded, k, realize)

    shadow = (c.loaded, c.load_count)
    real = rc.observe()
    if shadow != real:
        report(layout, realize, [], "<initial>", shadow, real)
        return False
    counter_box[0] += 1

    history = []
    for op in ops:
        # A genuine first read on a layout whose package body raises is
        # outside the completing-load bridge domain (see docstring); probe
        # the discovery phase there instead.
        if op == "access" and layout["raising"] and not c.loaded:
            op = "enum"
        history.append(op)
        if op == "enum":
            enumerate_children(c)
        else:
            access_object(c)
        try:
            if op == "enum":
                rc.enumerate()
            else:
                rc.access()
        except Exception as exc:
            print("DISAGREEMENT: real side raised %r" % (exc,))
            report(layout, realize, history, op,
                   (c.loaded, c.load_count), rc.observe())
            return False
        shadow = (c.loaded, c.load_count)
        real = rc.observe()
        if shadow != real:
            report(layout, realize, history, op, shadow, real)
            return False
        counter_box[0] += 1
    return True


def main():
    oracle = Oracle()
    checked = [0]

    op_menu = [("enum",), ("access",),
               ("enum", "enum"), ("access", "access"),
               ("enum", "access"), ("access", "enum"),
               ("enum", "access", "enum", "access"),
               ("access", "enum", "enum", "access")]
    init_menu = [(False, 0, "plain"), (False, 1, "none_attr"),
                 (True, 0, "setter"), (True, 3, "genuine"),
                 (True, 7, "setter")]

    # boundary sweep: every layout x initial state x op-sequence menu
    for layout in oracle.layouts:
        for loaded, k, realize in init_menu:
            if layout["raising"] and realize == "genuine":
                realize = "setter"
            for ops in op_menu:
                if not run_trial(oracle, layout, loaded, k, realize,
                                 ops, checked):
                    return 1
    n_boundary = checked[0]

    # randomized fuzz until the input budget is met (pinned seed)
    rng = random.Random(SEED)
    while checked[0] < N_TARGET:
        layout = rng.choice(oracle.layouts)
        loaded = rng.random() < 0.5
        k = rng.randint(0, 1000)
        if loaded:
            realize = ("setter" if layout["raising"]
                       else rng.choice(("setter", "genuine")))
        else:
            realize = rng.choice(("plain", "plain", "none_attr"))
        ops = tuple(rng.choice(("enum", "access"))
                    for _ in range(rng.randint(2, 5)))
        if not run_trial(oracle, layout, loaded, k, realize, ops, checked):
            return 1

    print("G-CONF OK: shadow impl == real patched collector on %d state "
          "comparisons (%d boundary + fuzz to budget, seed %d) over %d "
          "package layouts; 0 disagreements."
          % (checked[0], n_boundary, SEED, len(oracle.layouts)))
    print(json.dumps({"checked": checked[0], "disagreements": 0,
                      "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
