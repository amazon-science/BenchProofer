#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-8399 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged op of Solution.lean's impl region (`privatizeName`)
              transliterated to Python over the real repo type (`str`), via the
              mapping.md bijection (`List Char` <-> `str`): given the descriptive
              label `base`, prepend exactly one underscore -> `"_" + base`. There
              is no A-tagged callee in the impl region (the identifier is built
              purely from its given label), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched, F2P-graded callee
              `_pytest.unittest._make_xunit_fixture` applied at base_commit with
              the gold patch applied. We read the generated fixture's registered
              lookup name (`fixture._pytestfixturefunction.name`) — the exact
              identifier the `--fixtures` listing keys on. The pre-patch name
              for the same inputs is `f"unittest_{setup_name}_fixture_{qualname}"`
              (= `base`); the relation under test is `oracle == "_" + base`.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image) with the gold patch
applied; stdlib only. The fuzz seed is pinned (mapping.md §4) for determinism.
"""
import random
import string
import sys

SEED = 8399
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean privatizeName, transliterated -------------
def shadow_private_name(base):
    """privatizeName (base.toList) transliterated to str: prepend one '_'.
    `'_' :: base` over `List Char` is `"_" + base` over `str` (mapping.md)."""
    return "_" + base


# --- the oracle: the patched, F2P-graded repo callee -------------------------
# Configurations exactly as the two real call sites invoke _make_xunit_fixture
# (see _inject_setup_teardown_fixtures): the class-setup and the method-setup.
_CONFIGS = [
    # (setup_name, teardown_name, cleanup_name, scope, pass_self)
    ("setUpClass", "tearDownClass", "doClassCleanups", "class", False),
    ("setup_method", "teardown_method", None, "function", True),
]


def _make_class(qualname, setup_name):
    """A dummy test class exposing `setup_name` (so the callee builds a fixture)
    and carrying the fuzzed `__qualname__` that flows into the generated name."""

    def _setup(*args, **kwargs):
        pass

    cls = type("Dummy", (object,), {setup_name: staticmethod(_setup)})
    cls.__qualname__ = qualname
    return cls


def oracle_private_name(qualname, cfg):
    """patch.diff's behaviour: the registered lookup name the patched callee
    assigns to the generated fixture for class `qualname` under config `cfg`."""
    from _pytest.unittest import _make_xunit_fixture

    setup_name, teardown_name, cleanup_name, scope, pass_self = cfg
    obj = _make_class(qualname, setup_name)
    fixture = _make_xunit_fixture(
        obj, setup_name, teardown_name, cleanup_name,
        scope=scope, pass_self=pass_self,
    )
    if fixture is None:  # pragma: no cover — setup is present, so never None
        return None
    return fixture._pytestfixturefunction.name


def base_label(qualname, setup_name):
    """The pre-patch (un-privatized) descriptive label = `base` of privatizeName.
    This is the unique-lookup name format the call site uses, sans privatization."""
    return f"unittest_{setup_name}_fixture_{qualname}"


def fuzz_qualnames(n, rng):
    # boundary / realistic cases first
    yield "Tests"
    yield "MyTestCase"
    yield "Test"
    yield "A"
    yield "Outer.Inner"
    yield "TestCase_with_underscores"
    yield "Test123"
    yield ""  # degenerate but legal qualname fragment
    alphabet = string.ascii_letters + string.digits + "_."
    for _ in range(n):
        k = rng.randint(1, 30)
        yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for qualname in fuzz_qualnames(N_FUZZ, rng):
        for cfg in _CONFIGS:
            setup_name = cfg[0]
            count += 1
            base = base_label(qualname, setup_name)
            shadow = shadow_private_name(base)
            try:
                oracle = oracle_private_name(qualname, cfg)
            except Exception as e:  # pragma: no cover
                print("G-CONF FAIL: oracle raised on qualname=%r cfg=%r: %r"
                      % (qualname, setup_name, e))
                return 1
            if shadow != oracle:
                disagreements.append((qualname, setup_name, shadow, oracle))
                if len(disagreements) >= 5:
                    break
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for q, sn, sh, orc in disagreements:
            print("  qualname=%r setup=%r shadow=%r oracle=%r" % (q, sn, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of privatizeName ('_' + base) agrees with "
          "patch.diff behaviour (_make_xunit_fixture generated name) on %d "
          "inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
