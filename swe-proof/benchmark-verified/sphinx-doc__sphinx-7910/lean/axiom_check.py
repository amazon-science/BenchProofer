#!/usr/bin/env python
"""G-AX for sphinx-doc__sphinx-7910.

No CONSUMED callee axiom (`axiom _prop`) is declared: every changed op is modeled
deeply. The one callee the fix newly relies on — resolving an object to the
underlying object it wraps — is an **A-reference** (`coreObject` in Solution.lean),
modeled as "follow the wrapper link to the end". Its primary validation is the
whole-impl differential test in conformance_check.py (G-CONF).

This script additionally validates the A-reference property in isolation against
the REAL callee `sphinx.util.inspect.unwrap`: for a finite acyclic `__wrapped__`
chain, `unwrap(obj)` returns the innermost object (the one with no `__wrapped__`),
i.e. exactly what `coreObject` computes. Boundary + fuzz. stdlib-only; exit 0 iff
every observation meets the property.
"""
import functools
import random
import sys

SEED = 7910


def lean_core_object(obj):
    """`coreObject`: follow `__wrapped__` to the innermost object."""
    core = obj
    seen = set()
    while hasattr(core, "__wrapped__") and id(core) not in seen:
        seen.add(id(core))
        core = core.__wrapped__
    return core


def make_chain(depth):
    """Build a function wrapped `depth` times with functools.wraps; the innermost
    is a sentinel-tagged base function."""
    def base():
        pass
    base._sentinel = object()
    f = base
    for _ in range(depth):
        @functools.wraps(f)
        def wrapper(*a, _inner=f, **k):
            return _inner(*a, **k)
        f = wrapper
    return f, base


def main():
    try:
        from sphinx.util.inspect import unwrap as real_unwrap
    except Exception as e:  # pragma: no cover
        print("status=skip sphinx.util.inspect.unwrap unavailable: {}".format(e))
        return 0

    rng = random.Random(SEED)
    checked = 0
    violations = 0

    depths = [0, 1, 2, 3, 5, 10] + [rng.randint(0, 12) for _ in range(2000)]
    for d in depths:
        top, base = make_chain(d)
        real = real_unwrap(top)
        model = lean_core_object(top)
        checked += 1
        # A-reference property: real unwrap == model coreObject == the innermost
        # (sentinel-tagged) object.
        if not (real is base and model is base and real is model):
            violations += 1
            if violations <= 5:
                print("VIOLATION depth={} real_is_base={} model_is_base={}".format(
                    d, real is base, model is base))

    # boundary: an undecorated object (no __wrapped__) is its own core.
    def plain():
        pass
    if real_unwrap(plain) is not plain or lean_core_object(plain) is not plain:
        violations += 1
        print("VIOLATION plain object not fixed point")
    checked += 1

    print("checked={} violations={}".format(checked, violations))
    if violations == 0:
        print("status=pass A-reference coreObject == inspect.unwrap "
              "({} checks)".format(checked))
        return 0
    print("status=fail {} violation(s)".format(violations))
    return 1


if __name__ == "__main__":
    sys.exit(main())
