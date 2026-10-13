#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-7910.

Executes the REAL library primitive the patch calls -- `inspect.unwrap` (the
function `sphinx.util.inspect.unwrap` delegates to; the repo wrapper only adds a
`ValueError` guard that still returns the identity) -- and asserts that every
observation matches the `canonical` axiom encoded in model.py.

The axiom (A-consumed) claims, for the member object `obj` handed to the hook:

  * canonical(obj) preserves the inclusion-relevant identity of obj
      - has_doc           (obj.__doc__ truthiness)
      - cls_name          (the class component of obj.__qualname__)
      - is_class_member   (ground-truth ownership)
    because functools.wraps copies __doc__/__qualname__/__module__/__name__ onto
    the wrapper, so unwrapping changes none of them;
  * the recovered object's namespace records the GROUND-TRUTH ownership:
        obj.cls_name in canonical(obj).__globals__
        and (name in canonical(obj).__globals__[cls_path].__dict__)
    holds exactly when obj is a genuine member of its class -- because the
    ORIGINAL function's __globals__ is the module in which the function (and its
    class) is genuinely defined, whereas a decorator-wrapped object's OWN
    __globals__ is the decorator module's and need not contain the class.

The discriminating scenario (the F2P test `test_class_decorated_doc`): a method
decorated with `functools.wraps` whose decorator lives in a DIFFERENT module
than the owning class, so the wrapper's __globals__ lacks the class. We rebuild
that exact shape here.

Imports only the standard library (`functools`, `inspect`, `types`). Exit 0 iff
every obligation holds.
"""
import functools
import inspect
import sys
import types


# --- a decorator whose closure/globals live in a SEPARATE module --------------
# We synthesize a module to host the decorator so that the wrapper function's
# __globals__ is that module's namespace, NOT the namespace in which the owning
# classes (built below in this module) are defined. This is exactly the
# cross-module shape of the repository's test (decorator in
# sphinx/testing/util.py, classes in tests/test_ext_napoleon.py).

_deco_mod = types.ModuleType("axcheck_decorator_module")
exec(
    "import functools\n"
    "def simple_decorator(f):\n"
    "    @functools.wraps(f)\n"
    "    def wrapper(*args, **kwargs):\n"
    "        return f(*args, **kwargs)\n"
    "    return wrapper\n"
    "def double_decorator(f):\n"
    "    @functools.wraps(f)\n"
    "    def wrapper(*args, **kwargs):\n"
    "        return f(*args, **kwargs)\n"
    "    return wrapper\n",
    _deco_mod.__dict__,
)
simple_decorator = _deco_mod.simple_decorator
double_decorator = _deco_mod.double_decorator


# --- sample owning classes (this module's namespace is `globals()`) -----------

class SampleClass:
    def __special_doc__(self):
        """SampleClass.__special_doc__.DOCSTRING"""
        pass

    @simple_decorator
    def __decorated_special__(self):
        """decorated special with doc"""
        pass

    @simple_decorator
    def __init__(self):
        """decorated init with doc"""
        pass

    @simple_decorator
    def _decorated_private(self):
        """decorated private with doc"""
        pass

    @double_decorator
    @simple_decorator
    def __twice_decorated__(self):
        """twice-decorated special with doc"""
        pass

    def __special_undoc__(self):
        pass


class SampleError(Exception):
    @simple_decorator
    def __decorated_special__(self):
        """decorated special on an Exception subclass"""
        pass

    def __special_doc__(self):
        """SampleError.__special_doc__.DOCSTRING"""
        pass


# --- the checks ---------------------------------------------------------------

def cls_path_of(obj):
    """The single-component class path from obj.__qualname__ (the repository's
    `obj.__qualname__.rpartition('.')[0]`)."""
    qualname = getattr(obj, "__qualname__", "")
    cls_path, _, _ = qualname.rpartition(".")
    return cls_path


def real_cls_is_owner(globals_ns, cls_path, name):
    """The repository's `cls = globals[cls_path]; cls and hasattr(cls,name) and
    name in cls.__dict__`, guarded by the KeyError that the code's try/except
    converts to cls_is_owner=False."""
    if cls_path not in globals_ns:
        return False
    cls = globals_ns[cls_path]
    return bool(cls and hasattr(cls, name) and name in cls.__dict__)


def check(owner_cls, name, expect_owned):
    """Validate the `canonical` axiom for one member object."""
    obj = getattr(owner_cls, name)
    canon = inspect.unwrap(obj)              # the REAL library primitive

    # (a) identity preserved across unwrap (functools.wraps copies metadata)
    assert canon is not None, "unwrap returned None for %s.%s" % (
        owner_cls.__name__, name)
    assert bool(getattr(canon, "__doc__", False)) == \
        bool(getattr(obj, "__doc__", False)), \
        "has_doc not preserved for %s.%s" % (owner_cls.__name__, name)
    assert cls_path_of(canon) == cls_path_of(obj), \
        "cls_name (qualname class component) not preserved for %s.%s" % (
            owner_cls.__name__, name)

    cls_path = cls_path_of(obj)

    # ground-truth ownership of the member by its class
    truth = bool(owner_cls and hasattr(owner_cls, name) and
                 name in owner_cls.__dict__)
    assert truth == expect_owned, \
        "test fixture wrong: %s.%s owned=%r expected %r" % (
            owner_cls.__name__, name, truth, expect_owned)

    # (b) ground-truth membership recovered through the UNWRAPPED namespace
    recovered = real_cls_is_owner(canon.__globals__, cls_path, name)
    assert recovered == truth, (
        "AXIOM UNSOUND: unwrapped-namespace ownership %r != ground truth %r "
        "for %s.%s" % (recovered, truth, owner_cls.__name__, name))

    return obj, canon, cls_path, truth


def main():
    decorated = [
        (SampleClass, "__decorated_special__"),
        (SampleClass, "__init__"),
        (SampleClass, "_decorated_private"),
        (SampleClass, "__twice_decorated__"),
        (SampleError, "__decorated_special__"),
    ]
    undecorated = [
        (SampleClass, "__special_doc__"),
        (SampleClass, "__special_undoc__"),
        (SampleError, "__special_doc__"),
    ]

    discriminators = 0
    for owner_cls, name in decorated:
        obj, canon, cls_path, truth = check(owner_cls, name, expect_owned=True)
        # The DISCRIMINATOR: for a cross-module decorated member, the wrapper's
        # own __globals__ does NOT contain the class, while the unwrapped
        # original's __globals__ DOES. This is exactly the bug the patch fixes.
        wrapper_sees = real_cls_is_owner(obj.__globals__, cls_path, name)
        unwrapped_sees = real_cls_is_owner(canon.__globals__, cls_path, name)
        assert wrapper_sees is False, (
            "expected wrapper namespace to miss the class for %s.%s" % (
                owner_cls.__name__, name))
        assert unwrapped_sees is True, (
            "expected unwrapped namespace to find the class for %s.%s" % (
                owner_cls.__name__, name))
        # the patched choice includes (False) where the pre-patch skips (None)
        discriminators += 1

    for owner_cls, name in undecorated:
        obj, canon, cls_path, truth = check(owner_cls, name, expect_owned=True)
        # undecorated: unwrap is the identity, both namespaces agree
        assert inspect.unwrap(obj) is obj, \
            "unwrap not identity on undecorated %s.%s" % (
                owner_cls.__name__, name)
        assert real_cls_is_owner(obj.__globals__, cls_path, name) is True

    print("G-AX OK: canonical (== inspect.unwrap) sound on %d decorated "
          "(cross-module wraps) + %d undecorated members; %d discriminating "
          "cases where wrapper namespace misses the class but the unwrapped "
          "namespace recovers true ownership" % (
              len(decorated), len(undecorated), discriminators))
    return 0


if __name__ == "__main__":
    sys.exit(main())
