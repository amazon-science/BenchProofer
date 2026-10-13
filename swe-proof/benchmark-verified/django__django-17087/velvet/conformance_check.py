#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-17087 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`buildReference` / `referencePath`) transliterated to Python over
              the *real* repo types (Python `str` / list of `str`), via the
              mapping.md bijection (Lean `String` ↔ Python `str`,
              `List String` ↔ the dotted reference split on '.'). The impl
              region has NO A-tagged callee — the module path, the enclosing
              qualifier chain, and the member name are inputs read off the value
              being serialized — so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `FunctionTypeSerializer.serialize()` (the bound-method branch:
              `self.value.__self__` is a class), applied at base_commit. We feed
              it a REAL bound class method whose enclosing class is nested an
              arbitrary, controlled number of levels deep inside a synthetic
              module, and read back the dotted reference string the serializer
              emits.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image); stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import string
import sys
import types


SEED = 17087
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean referencePath, transliterated -------------

def shadow_reference(module, cls_chain, member):
    """referencePath (Solution.lean pure region) transliterated to a dotted str.

    `out = (module :: clsChain) ++ [memberName]`, rendered as the '.'-joined
    dotted path the serializer emits. The `List String` carrier maps to the
    dotted string via the mapping.md bijection (join on '.')."""
    return ".".join([module] + list(cls_chain) + [member])


# --- the oracle: the patched FunctionTypeSerializer.serialize ----------------

def _make_nested_classmethod(module_name, cls_chain, member):
    """Build, inside a synthetic module `module_name`, a tower of nested classes
    named by `cls_chain` (outermost first) whose innermost class carries a
    classmethod named `member`. Return the BOUND classmethod object
    (`Inner.member`) — exactly the kind of value the issue reports
    (a class method of a nested class used as a default).

    The bound method's `__self__` is the innermost class, whose `__qualname__`
    is the full dotted chain (gold) and whose `__name__` is just the innermost
    name (pre-patch)."""
    # Create a real module so `__module__` is a clean importable-looking name.
    mod = types.ModuleType(module_name)
    sys.modules[module_name] = mod

    # Build the innermost class first, then wrap outward, fixing __qualname__ to
    # reflect the nesting (Python sets __qualname__ from the lexical nesting; we
    # construct it explicitly so the chain is exactly cls_chain).
    inner_name = cls_chain[-1]

    def _cm(cls):
        return cls
    # The bound method's `__name__` is read off the underlying function, so set
    # it to the member name the serializer will emit as the final component.
    _cm.__name__ = member
    _cm.__qualname__ = ".".join(cls_chain + [member])
    classdict = {member: classmethod(_cm)}
    inner = type(inner_name, (object,), classdict)
    inner.__module__ = module_name
    inner.__qualname__ = ".".join(cls_chain)
    # Expose the tower on the module under the outermost name so it is reachable
    # (not strictly required by the bound-method branch, which reads attributes
    # off the class object directly).
    setattr(mod, cls_chain[0], inner)

    bound = getattr(inner, member)  # the bound classmethod: __self__ is `inner`
    return bound


def oracle_reference(module, cls_chain, member):
    """patch.diff's behaviour: serialize a bound class method of a nested class
    and return the dotted reference string the serializer emits."""
    from django.db.migrations.serializer import serializer_factory

    bound = _make_nested_classmethod(module, cls_chain, member)
    try:
        result, _imports = serializer_factory(bound).serialize()
    finally:
        sys.modules.pop(module, None)
    return result


# --- fuzzing -----------------------------------------------------------------

_IDENT_START = string.ascii_uppercase
_IDENT_REST = string.ascii_letters + string.digits


def _ident(rng, upper=True):
    n = rng.randint(1, 8)
    first = rng.choice(_IDENT_START if upper else string.ascii_lowercase)
    return first + "".join(rng.choice(_IDENT_REST) for _ in range(n))


def _module(rng):
    # a dotted module path of 1..3 lowercase segments
    k = rng.randint(1, 3)
    return ".".join(_ident(rng, upper=False) for _ in range(k))


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4):
    # the gold F2P shape: a class method of a nested (depth-2) class.
    yield ("migrations.test_writer",
           ["WriterTests", "NestedChoices"], "method")
    # the prior depth-1 case (the only one the pre-patch already handled right):
    yield ("appname.models", ["Capability"], "default")
    yield ("mod", ["A"], "m")                       # minimal depth-1
    yield ("a.b.c", ["Outer", "Inner"], "f")        # depth-2
    yield ("pkg", ["L0", "L1", "L2"], "go")         # depth-3
    yield ("pkg", ["L0", "L1", "L2", "L3", "L4"], "deep")  # depth-5
    yield ("x", ["Cls"], "Cls")                     # member name == class name
    yield ("x", ["Same", "Same"], "Same")           # repeated names
    for _ in range(n):
        depth = rng.randint(1, 5)
        module = _module(rng)
        cls_chain = [_ident(rng) for _ in range(depth)]
        member = _ident(rng, upper=rng.random() < 0.5)
        yield (module, cls_chain, member)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for module, cls_chain, member in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_reference(module, cls_chain, member)
        oracle = oracle_reference(module, cls_chain, member)
        if shadow != oracle:
            disagreements.append((module, cls_chain, member, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for module, chain, member, sh, orc in disagreements:
            print("  module=%r chain=%r member=%r shadow=%r oracle=%r"
                  % (module, chain, member, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildReference agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
