#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-8399 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant) stripped. The impl is plain Python over
List[int], so no PSeq shim is needed for it; the @Pure helpers
`begins_private` / `listed` copy over as plain functions operating on lists
(they are used only for self-consistency assertions on the shadow's output).
There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo behaviour the model models per mapping.md — the
name each auto-generated setup/teardown helper fixture is registered under.
The gate applies patch.diff to /testbed before this script runs and sets
PYTHONPATH=/testbed, so importing `_pytest.python` / `_pytest.unittest`
resolves the patched in-tree source. Each of the five generating sites is
driven with a real owning object (a module, a plain class, or a TestCase
subclass carrying the relevant hook), and the registered fixture name is read
back from the fixture marker the real code attaches
(`fn._pytestfixturefunction.name`).

TYPE BRIDGE (mapping.md section 2): a name `str` maps to `List[int]` of
Unicode code points (`ord`/`chr` pointwise). The model's input `label` is the
descriptive label — the constant middle segment of the site plus the owning
object's (qual)name, exactly as mapping.md binds it — reconstructed here
independently of the oracle from the object handed to the real code. The
shadow's output codepoint list is rendered back to `str` and compared to the
real registered name for equality.

INPUT DOMAIN: Requires demands a readable, non-empty label whose first code
point is not the privacy marker (95). Every generated label here starts with
a constant lowercase-letter segment, so Requires holds by construction (and
is asserted per input). Fuzz varies the owning object's name/qualname over
identifier-ish strings, dotted qualnames, digits, spaces and non-ASCII
letters, cycling through all five generating sites.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz inputs.
Pinned fuzz seed: 8399.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import random
import string
import sys
import types
import unittest

SEED = 8399
N_FUZZ = 100_000

PRIVACY_MARKER = 95  # the code point '_'


# --- pure helpers from model.py, contracts stripped ---------------------------

def begins_private(name):
    """True iff the name begins with the privacy marker code point."""
    return len(name) > 0 and name[0] == PRIVACY_MARKER


def listed(name, verbose):
    if verbose > 0:
        return True
    return not begins_private(name)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def generated_fixture_name(label):
    result = [PRIVACY_MARKER]  # type: list
    i = 0
    while i < len(label):
        result = result + [label[i]]
        i = i + 1
    return result


# --- bridge: str <-> List[int] of code points ----------------------------------

def to_codepoints(s):
    return [ord(ch) for ch in s]


def to_str(cps):
    return "".join(chr(c) for c in cps)


# --- oracle drivers: run the REAL patched generating sites --------------------
# Each driver returns (label, real_registered_name). The label is the
# site's constant middle segment plus the owning object's (qual)name — the
# model's abstract input per mapping.md — built from the same object the real
# code reads, never from the real code's output.

def _fixture_name(fn):
    return fn._pytestfixturefunction.name


def drive_module_setup(pp, mod_name):
    mod = types.ModuleType(mod_name)
    mod.setup_module = lambda: None
    pp.Module._inject_setup_module_fixture(types.SimpleNamespace(obj=mod))
    real = _fixture_name(getattr(mod, "_Module__pytest_setup_module"))
    return "xunit_setup_module_fixture_" + mod.__name__, real


def drive_function_setup(pp, mod_name):
    mod = types.ModuleType(mod_name)
    mod.setup_function = lambda: None
    pp.Module._inject_setup_function_fixture(types.SimpleNamespace(obj=mod))
    real = _fixture_name(getattr(mod, "_Module__pytest_setup_function"))
    return "xunit_setup_function_fixture_" + mod.__name__, real


def drive_class_setup(pp, qualname):
    cls = type("C", (), {"setup_class": classmethod(lambda c: None)})
    cls.__qualname__ = qualname
    pp.Class._inject_setup_class_fixture(types.SimpleNamespace(obj=cls))
    real = _fixture_name(getattr(cls, "_Class__pytest_setup_class"))
    return "xunit_setup_class_fixture_" + cls.__qualname__, real


def drive_method_setup(pp, qualname):
    cls = type("C", (), {"setup_method": lambda self, m: None})
    cls.__qualname__ = qualname
    pp.Class._inject_setup_method_fixture(types.SimpleNamespace(obj=cls))
    real = _fixture_name(getattr(cls, "_Class__pytest_setup_method"))
    return "xunit_setup_method_fixture_" + cls.__qualname__, real


def drive_unittest(pu, setup_name, qualname):
    # the two hooks the real caller (_inject_setup_teardown_fixtures) passes
    if setup_name == "setUpClass":
        body = {"setUpClass": classmethod(lambda c: None)}
        teardown, cleanup, scope, pass_self = "tearDownClass", "doClassCleanups", "class", False
    else:
        body = {"setup_method": lambda self, m: None}
        teardown, cleanup, scope, pass_self = "teardown_method", None, "function", True
    cls = type("T", (unittest.TestCase,), body)
    cls.__qualname__ = qualname
    fx = pu._make_xunit_fixture(cls, setup_name, teardown, cleanup, scope, pass_self)
    label = "unittest_%s_fixture_%s" % (setup_name, cls.__qualname__)
    return label, _fixture_name(fx)


def check_one(site_id, label, real_name):
    """Diff the shadow against the real registered name for one input.
    Returns an error string on disagreement, else None."""
    cps = to_codepoints(label)
    # Requires: readable, non-empty label whose first code point is ordinary
    assert len(cps) > 0 and cps[0] != PRIVACY_MARKER, (
        "generated input violates Requires: %r" % (label,))
    shadow_cps = generated_fixture_name(cps)
    shadow_name = to_str(shadow_cps)
    # self-consistency of the shadow with the copied pure helpers
    assert begins_private(shadow_cps)
    assert not listed(shadow_cps, 0) and listed(shadow_cps, 1)
    if shadow_name != real_name:
        return ("DISAGREEMENT at site %s\n  label=%r\n  shadow=%r\n  real=%r"
                % (site_id, label, shadow_name, real_name))
    return None


def boundary_names():
    """Owning-object names/qualnames covering the edges: minimal, dotted /
    deeply nested, digits, underscores (leading/trailing), spaces, empty
    suffix, long, and non-ASCII."""
    return [
        "m", "M", "test_mod", "MyTestCase", "Outer.Inner", "A.B.C.D",
        "x" * 200, "_private", "__dunder__", "trailing_", "0", "9lives",
        "a b", "", "pkg.sub.mod", "Test-1", "é", "λσ", "名前", "Ünïcode.Ω",
    ]


def main():
    import _pytest.python as pp     # REAL patched module (PYTHONPATH=/testbed)
    import _pytest.unittest as pu   # REAL patched module

    sites = [
        ("module_setup", lambda name: drive_module_setup(pp, name)),
        ("function_setup", lambda name: drive_function_setup(pp, name)),
        ("class_setup", lambda name: drive_class_setup(pp, name)),
        ("method_setup", lambda name: drive_method_setup(pp, name)),
        ("unittest_setUpClass", lambda name: drive_unittest(pu, "setUpClass", name)),
        ("unittest_setup_method", lambda name: drive_unittest(pu, "setup_method", name)),
    ]

    checked = 0
    for name in boundary_names():
        for site_id, drive in sites:
            label, real = drive(name)
            err = check_one(site_id, label, real)
            if err:
                print(err)
                return 1
            checked += 1

    rng = random.Random(SEED)
    alphabet = string.ascii_letters + string.digits + "_"
    extras = ".. __" + "éλΩ名"
    for k in range(N_FUZZ):
        n = rng.randint(0, 40)
        chars = []
        for _ in range(n):
            if rng.random() < 0.1:
                chars.append(rng.choice(extras))
            else:
                chars.append(rng.choice(alphabet))
        name = "".join(chars)
        site_id, drive = sites[k % len(sites)]
        label, real = drive(name)
        err = check_one(site_id, label, real)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real generated fixture name on %d inputs "
          "(%d boundary x %d sites + %d fuzz, seed %d)."
          % (checked, len(boundary_names()), len(sites), N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
