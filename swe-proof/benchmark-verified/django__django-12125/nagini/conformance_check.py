#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12125 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The model IS Python: the impl operates on
plain List[int] code-point lists, so it runs directly. The @Pure helpers
`dotted_path` / `import_line` copy over as plain functions on a minimal PSeq
shim (they appear only in contracts, but are kept and cross-checked here for
completeness). There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.db.migrations.serializer.TypeSerializer.serialize`, invoked on a real
class object. The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched package importable.

Type bridge (mapping.md section 2): every text is a List[int] of Unicode code
points (s <-> [ord(ch) for ch in s]); the branch flag is the plain boolean
`value.__module__ == builtins.__name__`; the oracle's 2-tuple (string, imports)
maps to (List[int], List[int]) with the import set refined as either the empty
list (empty set) or the single member's code points (singleton set).

Input domain (mapping.md sections 1-2): the modeled function's inputs are the
three texts a class object carries (its module path, its simple leaf name, its
fully-qualified name) plus the built-in flag. Each generated input is realized
as a REAL class object with those attributes set, then fed to the real
serializer; the same texts (as code points) feed the shadow. The two values
the real method special-cases before reaching the modeled branch (the ORM base
class and the None type) are outside the modeled domain per mapping.md and are
excluded from generation. Generated shapes span: top-level classes (qualified
== simple), classes nested at depth 1-3 (qualified strictly extends simple),
enum classes, real built-in types, empty texts, and non-ASCII texts.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz classes.
Pinned fuzz seed: 12125.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random fuzzing; no hypothesis needed).
"""
import builtins
import enum
import json
import random
import string
import sys
import types

SEED = 12125
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the pure helpers use ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure helpers from model.py, contracts stripped ---------------------------

def dotted_path(module, qualified_name):
    """The non-built-in rendering, keyed by the FULLY-QUALIFIED name:
    module ++ '.' ++ qualified_name. '.' == U+002E == 46."""
    return module + PSeq(46) + qualified_name


def import_line(module):
    """The one accompanying import statement: "import " followed by the module
    path. "import " == U+0069 6D 70 6F 72 74 20."""
    return PSeq(105, 109, 112, 111, 114, 116, 32) + module


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def serialize_type(module, simple_name, qualified_name, module_is_builtin):
    if module_is_builtin:
        frag = []                            # type: List[int]
        frag = frag + simple_name            # the bare simple name
        imp = []                             # type: List[int]
        return (frag, imp)
    else:
        # frag = module + "." + qualified_name
        frag2 = []                           # type: List[int]
        frag2 = frag2 + module
        frag2 = frag2 + [46]                 # '.'
        frag2 = frag2 + qualified_name
        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
        return (frag2, imp2)
    # impl-end (verbatim copy ends here)


# --- bridge: str <-> List[int] of code points ---------------------------------

def cps(s):
    return [ord(ch) for ch in s]


def decode(lst):
    return "".join(chr(c) for c in lst)


def check_value(serializer_cls, value):
    """Run shadow and oracle on one class object; return an error string on
    disagreement, else None."""
    module = value.__module__
    simple_name = value.__name__
    qualified_name = value.__qualname__
    module_is_builtin = (module == builtins.__name__)

    frag_cps, imp_cps = serialize_type(cps(module), cps(simple_name),
                                       cps(qualified_name), module_is_builtin)

    # cross-check the pure helpers stay in lock-step with the impl region
    if not module_is_builtin:
        assert ToSeq(frag_cps) == dotted_path(ToSeq(cps(module)),
                                              ToSeq(cps(qualified_name)))
        assert ToSeq(imp_cps) == import_line(ToSeq(cps(module)))

    real_string, real_imports = serializer_cls(value).serialize()

    # bridge the shadow output back to the oracle's (str, set) shape
    shadow_string = decode(frag_cps)
    shadow_imports = set() if len(imp_cps) == 0 else {decode(imp_cps)}

    if shadow_string != real_string or shadow_imports != real_imports:
        return ("DISAGREEMENT\n"
                "  module=%r simple_name=%r qualified_name=%r builtin=%r\n"
                "  shadow=(%r, %r)\n  real=(%r, %r)"
                % (module, simple_name, qualified_name, module_is_builtin,
                   shadow_string, shadow_imports, real_string, real_imports))
    return None


def make_class(module, qualname, name):
    cls = types.new_class("C")
    cls.__module__ = module
    cls.__qualname__ = qualname
    cls.__name__ = name
    return cls


def boundary_values():
    targets = []

    # top-level classes (qualified name == simple name)
    class TopLevel:
        pass
    targets.append(TopLevel)

    # nested classes (qualified name strictly extends the simple name)
    class Outer:
        class Inner:
            pass

        class Middle:
            class Deep:
                pass
    targets += [Outer, Outer.Inner, Outer.Middle, Outer.Middle.Deep]

    # nested enum shapes
    class Host:
        class NestedIntEnum(enum.IntEnum):
            A = 1

        class NestedEnum(enum.Enum):
            X = "X"
    targets += [Host.NestedIntEnum, Host.NestedEnum]

    # real built-in types (built-in branch). The None type is excluded: the
    # real method special-cases it before the modeled branch (out of domain
    # per mapping.md), as is the ORM base class.
    targets += [int, str, list, dict, bool, bytes, float, tuple, set,
                frozenset, complex]

    # module-top-level nesting with a real module path
    targets += [ModTop, ModTop.NestA, ModTop.NestA.NestB]

    # synthetic extremes: empty / dotted / non-ASCII texts
    targets += [
        make_class("", "Q", "Q"),
        make_class("m", "", ""),
        make_class("", "", ""),
        make_class("a.b.c.d", "W.X.Y.Z", "Z"),
        make_class("pkg.sub", "Enclosing.Leaf", "Leaf"),
        make_class("päkkåge", "Über.Kläss", "Kläss"),
        make_class(builtins.__name__, "FakeBuiltin", "FakeBuiltin"),
        make_class(builtins.__name__, "Outer.FakeNested", "FakeNested"),
        make_class("x" * 300, "y" * 300, "y" * 300),
    ]
    return targets


class ModTop:
    class NestA:
        class NestB:
            pass


def main():
    # Django needs configured settings before ORM-adjacent modules load.
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure()
    from django.db.migrations.serializer import TypeSerializer  # REAL patched callee

    checked = 0
    n_boundary = 0
    for value in boundary_values():
        err = check_value(TypeSerializer, value)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    ident_head = string.ascii_letters + "_"
    ident_tail = string.ascii_letters + string.digits + "_"
    unicode_extra = "éüßαω中"

    def rand_ident():
        n = rng.randint(1, 10)
        head = rng.choice(ident_head)
        tail = "".join(rng.choice(ident_tail) for _ in range(n - 1))
        if rng.random() < 0.05:
            tail += rng.choice(unicode_extra)
        return head + tail

    def rand_module():
        depth = rng.randint(1, 4)
        return ".".join(rand_ident() for _ in range(depth))

    for _ in range(N_FUZZ):
        leaf = rand_ident()
        roll = rng.random()
        if roll < 0.10:
            # built-in branch: module names the built-in namespace
            module = builtins.__name__
            qualname = leaf
        else:
            module = rand_module()
            if roll < 0.55:
                # nested: qualified name = enclosing chain ++ '.' ++ leaf
                chain = ".".join(rand_ident()
                                 for _ in range(rng.randint(1, 3)))
                qualname = chain + "." + leaf
            else:
                # top level: qualified name == leaf
                qualname = leaf
        value = make_class(module, qualname, leaf)
        err = check_value(TypeSerializer, value)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched serializer on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
