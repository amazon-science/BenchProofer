#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-9281.

This bundle consumes NO `@ContractOnly` axiom. The only modelled callee is the
deep model `enum_rendering` (model.py pure region): the rendering of a member
of an enumerated type is the owning type's name, a single dot ``.``, then the
member's own name -- as a sequence of Unicode code points.

G-AX validates that deep model (A-reference) against the REAL behaviour the
gold patch produces for a member of an enumerated type:

    "%s.%s" % (object.__class__.__name__, object.name)

i.e. the actual `enum.Enum` member's owning-class name and member name joined
by a dot. We construct real `enum.Enum` classes (boundary cases + randomized
fuzz over class/member names, member values of varied types, and the
multiple-members-per-class shape), evaluate the real formatting, and assert it
equals the deep model `enum_rendering` on the corresponding code-point
sequences. Exit 0 iff every observation matches.

Imports nothing repo-specific: `enum` is the Python standard library -- the
same module the gold patch dispatches on (`isinstance(object, enum.Enum)`).
"""
import enum
import random
import string
import sys


def dot():
    """model.py pure helper `dot`: the single separator code point U+002E."""
    return [46]


def enum_rendering(class_name, member_name):
    """Reference implementation of model.py's deep model `enum_rendering`, on
    code-point lists: owning-type name ++ '.' ++ member name."""
    return list(class_name) + dot() + list(member_name)


def real_gold_rendering(member):
    """The REAL rendering the gold patch emits for an enumerated-type member:
        "%s.%s" % (member.__class__.__name__, member.name)
    returned as a list of Unicode code points."""
    text = "%s.%s" % (member.__class__.__name__, member.name)
    return [ord(ch) for ch in text]


def check_member(member):
    """Assert the deep model enum_rendering(...) == the REAL gold rendering."""
    class_name = [ord(ch) for ch in member.__class__.__name__]
    member_name = [ord(ch) for ch in member.name]
    expected = real_gold_rendering(member)          # real callee/formatting
    observed = enum_rendering(class_name, member_name)  # deep model
    assert observed == expected, (
        "enum_rendering deep model unsound on %r: gold rendering gives %r, "
        "deep model gives %r" % (member, expected, observed))
    # Also pin the structural shape the spec asserts: the result is exactly the
    # class name, a dot, then the member name -- and the dot separates them.
    assert observed == class_name + [46] + member_name
    assert chr(46) == "."


def main():
    # --- boundary cases: the issue's own example + edges ------------------
    class MyEnum(enum.Enum):
        FOO = 1
        BAR = 2

    class ValuedEnum(enum.Enum):
        ValueA = 10
        ValueB = 20

    class StrEnum(enum.Enum):
        A = "alpha"
        B = "beta"

    class SingleMember(enum.Enum):
        ONLY = object()

    class IntEnum(enum.IntEnum):
        X = 1
        Y = 2

    class Underscored(enum.Enum):
        _hidden_like = 1
        Mixed_Case_99 = 2

    boundary_members = [
        MyEnum.FOO, MyEnum.BAR,
        ValuedEnum.ValueA, ValuedEnum.ValueB,
        StrEnum.A, StrEnum.B,
        SingleMember.ONLY,
        IntEnum.X, IntEnum.Y,
        Underscored._hidden_like, Underscored.Mixed_Case_99,
    ]
    for m in boundary_members:
        check_member(m)
        # The repr fallback (what the PRE-PATCH code would have emitted) is the
        # ugly value-revealing form, and must DIFFER from the gold rendering --
        # this is exactly the behavioural change the F2P test observes.
        if "=" not in repr(m) and ":" not in repr(m):
            # IntEnum members repr as a plain int-ish form; only assert the
            # difference where the default Enum repr applies.
            pass
        else:
            assert real_gold_rendering(m) != [ord(c) for c in repr(m)], (
                "gold rendering should differ from the ugly repr for %r" % (m,))

    # --- randomized fuzz: many freshly-built Enum classes -----------------
    rng = random.Random(9281)
    name_start = string.ascii_letters + "_"
    name_rest = string.ascii_letters + string.digits + "_"

    def random_identifier():
        n = rng.randint(1, 12)
        s = rng.choice(name_start)
        s += "".join(rng.choice(name_rest) for _ in range(n - 1))
        return s

    for _ in range(5000):
        class_name = random_identifier()
        # 1..4 distinct member names with arbitrary distinct values
        k = rng.randint(1, 4)
        members = {}
        used = set()
        while len(members) < k:
            mname = random_identifier()
            # The functional Enum API reserves _sunder_ and __dunder__ names.
            if mname in used or mname.startswith("_") or mname.endswith("_"):
                continue
            used.add(mname)
            members[mname] = len(members) + 1
        EnumCls = enum.Enum(class_name, members)
        for mname in members:
            check_member(EnumCls[mname])

    print("G-AX OK: enum_rendering deep model (== gold "
          "'%%s.%%s'%%(cls.__name__, member.name)) sound on %d boundary + "
          "5000 randomized Enum classes" % len(boundary_members))
    return 0


if __name__ == "__main__":
    sys.exit(main())
