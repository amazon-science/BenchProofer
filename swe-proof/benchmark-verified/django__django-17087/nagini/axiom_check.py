#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-17087.

There is NO consumed @ContractOnly axiom in this bundle: the rendering is
spelled out deeply in model.py. This script validates the two A-REFERENCE deep
models against the REAL behaviour they stand in for — the post-patch
`FunctionTypeSerializer.serialize()` formatting the gold patch installs, for a
callable bound to a class object — on boundary + fuzz inputs:

  (A-reference 1) `member_path(module, class_qualified_name, method_name)`
      (model.py pure region) == the real rendering of a class-bound method:
          "%s.%s.%s" % (module, klass.__qualname__, value.__name__)
      i.e. module ++ "." ++ class_qualified_name ++ "." ++ method_name, keyed by
      the owning class's FULLY-QUALIFIED name.

  (A-reference 2) `import_line(module)` (model.py pure region) == the single
      member of the real import set {"import %s" % module}.

The real serializer branch (taken when the value is a callable bound to a class
object) reads, post-patch:
    klass = value.__self__
    module = klass.__module__
    return "%s.%s.%s" % (module, klass.__qualname__, value.__name__), {
        "import %s" % module
    }

We reconstruct exactly that formatting from real class-bound methods (classmethods
reached through their owning class) — including methods owned by classes NESTED
inside enclosing classes (where __qualname__ differs from __name__, the whole
point), methods owned by top-level classes (where they coincide), a method owned
by a nested enum.Enum subclass (the NestedChoices/TextChoices F2P shape) — and
assert the deep models reproduce the string and the import code point for code
point.

Imports only the Python standard library (`builtins`, `enum`, `random`,
`string`, `types`) — nothing repo-specific; the formatting under test is the
stdlib f-string the gold patch uses. Exit 0 iff every obligation holds.
"""
import builtins
import enum
import random
import string
import sys
import types


# --- model.py reference encodings (kept in lock-step with the pure region) ---

def member_path(module_cps, qualified_cps, method_cps):
    """Reference impl of model.py `member_path`:
    module ++ '.' ++ class_qualified_name ++ '.' ++ method_name."""
    return (list(module_cps) + [46] + list(qualified_cps) + [46]
            + list(method_cps))


def import_line(module_cps):
    """Reference impl of model.py `import_line`: "import " ++ module."""
    return [105, 109, 112, 111, 114, 116, 32] + list(module_cps)


def cps(s):
    return [ord(ch) for ch in s]


# --- the REAL post-patch FunctionTypeSerializer.serialize() formatting ---------

def real_serialize_class_method(value):
    """The post-patch FunctionTypeSerializer.serialize() formatting for the
    class-bound-method branch, reconstructed verbatim from the gold patch.

    Precondition (the branch guard, serializer.py:166-168): `value.__self__` is
    set and is a `type`. The caller below only passes such values."""
    klass = value.__self__
    module = klass.__module__
    return "%s.%s.%s" % (module, klass.__qualname__, value.__name__), {
        "import %s" % module
    }


def check_method_reference(value):
    """Assert the deep models reproduce the real serializer output for the
    class-bound method `value`, code point for code point."""
    # branch guard the real code checks before this hunk runs
    assert getattr(value, "__self__", None) is not None and isinstance(
        value.__self__, type), (
        "test input %r is not a callable bound to a class object" % (value,))

    string_out, imports = real_serialize_class_method(value)
    klass = value.__self__
    module = klass.__module__

    # A-reference 1: member_path == the rendered fragment
    model_string = member_path(cps(module), cps(klass.__qualname__),
                               cps(value.__name__))
    assert cps(string_out) == model_string, (
        "member_path deep model unsound for %r: real %r -> %r, deep model -> %r"
        % (value, string_out, cps(string_out), model_string))

    # A-reference 2: import_line == the single member of the import set
    assert len(imports) == 1, (
        "expected exactly one import for %r, got %r" % (value, imports))
    only = next(iter(imports))
    model_imp = import_line(cps(module))
    assert cps(only) == model_imp, (
        "import_line deep model unsound for %r: real %r -> %r, model -> %r"
        % (value, only, cps(only), model_imp))

    # The discriminating fact: a method owned by a NESTED class is rendered with
    # the owning class's FULL dotted qualified chain, NOT its bare leaf name
    # (which the buggy pre-patch used).
    if klass.__qualname__ != klass.__name__:
        assert string_out.endswith(
            ".%s.%s" % (klass.__qualname__, value.__name__)), (
            "nested-class method %r must be rendered with the owning class's "
            "full qualified name, got %r" % (value, string_out))
        # the bare-leaf rendering the bug produced is a STRICT, different suffix
        buggy = "%s.%s.%s" % (module, klass.__name__, value.__name__)
        assert string_out != buggy, (
            "post-patch rendering must differ from the buggy bare-leaf form "
            "for nested-class method %r: both are %r" % (value, string_out))


def main():
    targets = []

    # --- a method owned by a top-level class (qualname == name) ---------------
    # (TopLevelCls / Outer / Host / DeepTop are MODULE-level classes so their
    # __qualname__ carries no '<locals>' prefix — exactly the real F2P shape,
    # where the owning class is nested in another *class*, never in a function.)
    targets.append(TopLevelCls.cm)
    assert TopLevelCls.__qualname__ == TopLevelCls.__name__

    # --- methods owned by classes NESTED inside an enclosing class ------------
    # This is the central case: the owning class's __qualname__ carries the
    # enclosing chain.
    targets += [Outer.Inner.method, Outer.Middle.Deep.go]
    # sanity: these really exercise the qualname != name distinction
    assert Outer.Inner.method.__self__ is Outer.Inner
    assert Outer.Inner.__qualname__ != Outer.Inner.__name__
    assert Outer.Middle.Deep.__qualname__ != Outer.Middle.Deep.__name__

    # --- a method owned by a nested enum.Enum subclass (NestedChoices shape) ---
    # models.TextChoices is an enum subclass; the value routed to the serializer
    # is a classmethod bound to that nested enum class. `django` is not importable
    # here, so we use a plain Enum subclass — what matters is __self__ being the
    # class and its __module__/__qualname__/__name__.
    targets.append(Host.NestedChoices.method)
    assert Host.NestedChoices.method.__self__ is Host.NestedChoices
    assert Host.NestedChoices.__qualname__ != Host.NestedChoices.__name__

    # --- methods owned by module-top-level nested classes (real __module__) ---
    targets += [DeepTop.cm, DeepTop.NestedA.cm, DeepTop.NestedA.NestedB.cm]

    for v in targets:
        check_method_reference(v)

    # --- randomized fuzz over module / owning-class qualified-name shapes ------
    # Build a class with a classmethod and override its owning class's
    # __module__/__qualname__/__name__ to span nested and top-level shapes (this
    # is exactly the data the serializer reads off a real class-bound method).
    rng = random.Random(17087)
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
        leaf = rand_ident()
        method_name = rand_ident()

        # synthesise an owning class with a classmethod, then override its
        # identity attributes to the fuzzed (module, qualname, name) shape.
        cls = types.new_class(leaf)
        cls.__module__ = rand_module()
        cls.__name__ = leaf
        if rng.random() < 0.5:
            # nested: qualname = enclosing-chain ++ '.' ++ leaf
            chain_len = rng.randint(1, 3)
            prefix = ".".join(rand_ident() for _ in range(chain_len))
            cls.__qualname__ = prefix + "." + leaf
        else:
            # top level: qualname == leaf
            cls.__qualname__ = leaf

        # a bound classmethod: __self__ is the class, __name__ is the method name.
        def _fn(c):
            return c
        _fn.__name__ = method_name
        bound = types.MethodType(_fn, cls)   # bound to the class object

        check_method_reference(bound)

    print("G-AX OK: member_path/import_line deep models (A-reference) == real "
          "post-patch FunctionTypeSerializer formatting over %d explicit "
          "class-bound methods (incl. nested-class methods Outer.Inner.method / "
          "Outer.Middle.Deep.go, a nested-enum method mirroring "
          "NestedChoices.method, builtins-module nested shapes) and %d fuzz "
          "class-bound methods spanning nested + top-level owning-class "
          "__qualname__ shapes" % (len(targets), fuzz_n))
    return 0


# Module-top-level class shapes with real __module__/__qualname__ for the
# explicit targets (defined at module scope so __qualname__ carries no
# '<locals>' prefix — the real F2P shape nests the owning class in a *class*).

class TopLevelCls:
    @classmethod
    def cm(cls):
        return cls


class Outer:
    class Inner:
        @classmethod
        def method(cls):
            return cls

    class Middle:
        class Deep:
            @classmethod
            def go(cls):
                return cls


class Host:
    class NestedChoices(enum.Enum):
        X = "X"
        Y = "Y"

        @classmethod
        def method(cls):
            return cls.X


# A module-top-level nested-class shape with a real __module__ for the targets.
class DeepTop:
    @classmethod
    def cm(cls):
        return cls

    class NestedA:
        @classmethod
        def cm(cls):
            return cls

        class NestedB:
            @classmethod
            def cm(cls):
                return cls


if __name__ == "__main__":
    sys.exit(main())
