#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12125.

There is NO consumed @ContractOnly axiom in this bundle: the rendering is
spelled out deeply in model.py. This script validates the two A-REFERENCE deep
models against the REAL behaviour they stand in for — the post-patch
`TypeSerializer.serialize()` formatting the gold patch installs — on boundary +
fuzz inputs:

  (A-reference 1) `dotted_path(module, qualified_name)` (model.py pure region)
      == the real non-built-in rendering of a class object:
          "%s.%s" % (module, self.value.__qualname__)
      i.e. module ++ "." ++ qualified_name, keyed by the FULLY-QUALIFIED name.

  (A-reference 2) `import_line(module)` (model.py pure region) == the single
      member of the real import set {"import %s" % module}.

  We also confirm the built-in branch the spec models (simple name, empty
  import set) reproduces the real `self.value.__name__, set()`.

The real serializer reads:
    module = self.value.__module__
    if module == builtins.__name__:
        return self.value.__name__, set()
    else:
        return "%s.%s" % (module, self.value.__qualname__), {"import %s" % module}

We reconstruct exactly that formatting from real class objects — including
classes NESTED inside enclosing classes (where __qualname__ differs from
__name__, the whole point), top-level classes (where they coincide), nested
enums / nested TextChoices-style enums (the F2P shapes), and built-in types —
and assert the deep models reproduce the string and the import code point for
code point.

Imports only the Python standard library (`builtins`, `enum`, `random`,
`string`, `types`) — nothing repo-specific; the formatting under test is the
two stdlib f-strings the gold patch uses. Exit 0 iff every obligation holds.
"""
import builtins
import enum
import random
import string
import sys
import types


# --- model.py reference encodings (kept in lock-step with the pure region) ---

def dotted_path(module_cps, qualified_cps):
    """Reference impl of model.py `dotted_path`: module ++ '.' ++ qualified."""
    return list(module_cps) + [46] + list(qualified_cps)


def import_line(module_cps):
    """Reference impl of model.py `import_line`: "import " ++ module."""
    return [105, 109, 112, 111, 114, 116, 32] + list(module_cps)


def cps(s):
    return [ord(ch) for ch in s]


# --- the REAL post-patch TypeSerializer.serialize() formatting ----------------

def real_serialize_type(value):
    """The post-patch TypeSerializer.serialize() formatting, reconstructed
    verbatim from the gold patch (only the special-case table for
    models.Model / type(None) is repo-specific and irrelevant to the change;
    every input below has a __module__)."""
    module = value.__module__
    if module == builtins.__name__:
        return value.__name__, set()
    else:
        return "%s.%s" % (module, value.__qualname__), {"import %s" % module}


def check_type_reference(value):
    """Assert the deep models reproduce the real serializer output for `value`,
    code point for code point, in both branches."""
    string_out, imports = real_serialize_type(value)
    module = value.__module__
    if module == builtins.__name__:
        # built-in branch: bare simple name, no import.
        assert string_out == value.__name__, (
            "builtin branch: real %r != __name__ %r" % (string_out, value.__name__))
        assert imports == set(), (
            "builtin branch: expected empty import set, got %r" % (imports,))
        # the spec models this branch as (simple_name, []) — matched above.
        return
    # non-built-in branch: A-reference 1 + 2.
    model_string = dotted_path(cps(module), cps(value.__qualname__))
    assert cps(string_out) == model_string, (
        "dotted_path deep model unsound for %r: real %r -> %r, deep model -> %r"
        % (value, string_out, cps(string_out), model_string))
    assert len(imports) == 1, (
        "expected exactly one import for %r, got %r" % (value, imports))
    only = next(iter(imports))
    model_imp = import_line(cps(module))
    assert cps(only) == model_imp, (
        "import_line deep model unsound for %r: real %r -> %r, model -> %r"
        % (value, only, cps(only), model_imp))
    # The discriminating fact: a nested class is rendered with the FULL dotted
    # qualified chain, NOT the bare leaf name (which the buggy pre-patch used).
    if value.__qualname__ != value.__name__:
        assert string_out.endswith("." + value.__qualname__), (
            "nested class %r must be rendered with its full qualified name, "
            "got %r" % (value, string_out))
        assert not string_out.endswith("." + value.__name__) or \
            value.__qualname__.endswith("." + value.__name__), (
            "sanity: leaf-name rendering must be a strict suffix")


def main():
    targets = []

    # --- top-level classes (qualname == name) ---------------------------------
    class TopLevel:
        pass

    class AnotherTop:
        pass

    targets += [TopLevel, AnotherTop]

    # --- classes NESTED inside an enclosing class (qualname != name) ----------
    # This is the central case: __qualname__ carries the enclosing chain.
    class Outer:
        class Inner:
            pass

        class Middle:
            class Deep:
                pass

    targets += [Outer, Outer.Inner, Outer.Middle, Outer.Middle.Deep]
    # sanity: these really exercise the qualname != name distinction
    assert Outer.Inner.__qualname__ != Outer.Inner.__name__
    assert Outer.Middle.Deep.__qualname__ != Outer.Middle.Deep.__name__

    # --- nested enums (the NestedEnum F2P shape) ------------------------------
    class Host:
        class NestedEnum(enum.IntEnum):
            A = 1
            B = 2

        # a nested enum.Enum subclass mirroring models.TextChoices (which is an
        # enum subclass); we use a plain Enum since `django` is not importable
        # here — the serializer routes the *class* (a type) through
        # TypeSerializer, and what matters is __module__/__qualname__/__name__.
        class NestedChoices(enum.Enum):
            X = 'X'
            Y = 'Y'

    targets += [Host.NestedEnum, Host.NestedChoices]
    assert Host.NestedEnum.__qualname__ != Host.NestedEnum.__name__

    # --- built-in types (built-in branch: bare name, no import) ---------------
    targets += [int, str, list, dict, bool, type(None), bytes, float, tuple]
    for t in [int, str, list]:
        assert t.__module__ == builtins.__name__

    # --- a class defined at this module's top level (real __module__) ---------
    targets += [DeepTop, DeepTop.NestedA, DeepTop.NestedA.NestedB]

    for v in targets:
        check_type_reference(v)

    # --- randomized fuzz over module / qualified-name shapes ------------------
    # Build classes dynamically with varied (module, qualname) and check both
    # the nested (qualname has dotted prefix) and top-level shapes.
    rng = random.Random(12125)
    ident_head = string.ascii_letters + "_"
    ident_tail = string.ascii_letters + string.digits + "_"

    def rand_ident():
        n = rng.randint(1, 10)
        return rng.choice(ident_head) + "".join(
            rng.choice(ident_tail) for _ in range(n - 1))

    def rand_module():
        depth = rng.randint(1, 4)
        return ".".join(rand_ident() for _ in range(depth))

    fuzz_n = 20000
    for _ in range(fuzz_n):
        # synthesise a class and override its __module__/__qualname__ to span
        # nested and top-level shapes (this is exactly the data the serializer
        # reads off a real class object).
        cls = types.new_class(rand_ident())
        cls.__module__ = rand_module()
        leaf = rand_ident()
        if rng.random() < 0.5:
            # nested: qualname = enclosing-chain ++ '.' ++ leaf
            chain_len = rng.randint(1, 3)
            prefix = ".".join(rand_ident() for _ in range(chain_len))
            cls.__qualname__ = prefix + "." + leaf
        else:
            # top level: qualname == leaf
            cls.__qualname__ = leaf
        cls.__name__ = leaf
        check_type_reference(cls)

    print("G-AX OK: dotted_path/import_line deep models (A-reference) == real "
          "post-patch TypeSerializer formatting over %d explicit targets "
          "(incl. nested classes, nested enums, builtins) and %d fuzz classes "
          "spanning nested + top-level __qualname__ shapes"
          % (len(targets), fuzz_n))
    return 0


# A module-top-level nested-class shape with a real __module__ for the targets.
class DeepTop:
    class NestedA:
        class NestedB:
            pass


if __name__ == "__main__":
    sys.exit(main())
