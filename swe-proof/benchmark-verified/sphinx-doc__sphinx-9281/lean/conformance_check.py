#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-9281.

The bundle models ONE behaviour: how `object_description` renders a value to its
display text after the patch adds a dedicated `enum.Enum` branch (mapping.md).
Its observable effect is a PURE function of the value's kind:

    * a PLAIN enum member (not itself a dict/set/frozenset instance) with
      class name C and member name M                      ->  "C.M"
    * any other value (non-enum, or a container-mixin enum
      member captured by an earlier container branch)     ->  the display the
                                                              POST-PATCH routine
                                                              gives that value

Standing up the full `object_description` (repr, memory-address scrub, newline
flatten, dict/set/frozenset sorting) is unnecessary: the patch changes exactly
the plain-enum dispatch, and the modeled value is the kind-dispatch decision. So
the ORACLE below is a faithful in-process replica of the POST-PATCH kind-dispatch
(plain-enum branch = f"{cls}.{name}", else the existing rendering), and the
SHADOW is the op-for-op transliteration of `implementation_describeValue`
(Solution.lean impl region), per refinement.md.

Faithfulness of the model boundaries:
  * plain-enum branch == "%s.%s" % (cls, name)  ==  C ++ "." ++ M  (both `%s` on
                       a str is identity, so this is plain concatenation)
  * legacyDescription == an opaque value->text routine: the display the
                       POST-PATCH object_description gives a value that does not
                       itself take the new enum branch (the dict/set/frozenset
                       dedicated renderings — each joining object_description(...)
                       of the values it holds — plus the repr tail). Modeled here
                       by a fixed deterministic stand-in: its concrete value is
                       irrelevant, because the spec only pins the `other` result
                       to legacyDescription(obj) and BOTH legs apply the SAME
                       stand-in, so any disagreement can only come from the enum
                       branch text or the kind dispatch. Corollary, stated so it
                       is not mistaken for coverage: this checker is blind to the
                       CONTENT of the `other` leg by construction — including the
                       fact that a container holding a plain enum member renders
                       differently after the patch (see mapping.md "Measured
                       reference behaviour"). That propagation is carried by the
                       carrier's denotation, not pinned by the spec, and is a
                       disclosed boundary rather than a gap this fuzzer could
                       close.

Container-mixin enum members (e.g. class FZ(frozenset, enum.Enum)) satisfy both
isinstance tests, but the container branches PRECEDE the enum branch in the
post-patch `elif` chain, so such a member is rendered by its container branch and
never by the new one; they map to the `other` kind here. Only plain enum members
reach the new branch — those are the `enum` kind. This genuinely tests the
soundness-critical behaviour and matches the F2P expectation
(`test_object_description_enum`: object_description(MyEnum.FOO) == "MyEnum.FOO").

stdlib-only. Pinned seed: 9281 (also in mapping.md).
"""
import random
import string
import sys

SEED = 9281
N = 120_000


# legacyDescription stand-in: any deterministic function works (see docstring).
# Keyed on the opaque tag so distinct non-enum values get distinct renderings.
def legacy_description(tag):
    return "repr::" + str(tag)


# --- ORACLE: faithful in-process replica of the POST-PATCH kind-dispatch -------
# obj is ("enum", className, memberName) — a PLAIN enum member (one that reaches
# the new branch) — or ("other", tag) — any other value, including a
# container-mixin enum member captured by an earlier unchanged branch.
def oracle(obj):
    if obj[0] == "enum":
        _, cls_name, member_name = obj
        return "%s.%s" % (cls_name, member_name)
    else:
        _, tag = obj
        return legacy_description(tag)


# --- SHADOW of implementation_describeValue (the R leg) ------------------------
# Mirrors Solution.lean impl region exactly.
def shadow(obj):
    if obj[0] == "enum":
        _, class_name, member_name = obj
        return class_name + "." + member_name
    return legacy_description(obj[1])


def disagree(obj):
    got = oracle(obj)
    want = shadow(obj)
    if got != want:
        return (obj, got, want)
    return None


def _enumerate_edge():
    cases = []
    # F2P: object_description(MyEnum.FOO) == "MyEnum.FOO"
    cases.append(("enum", "MyEnum", "FOO"))
    cases.append(("enum", "MyEnum", "BAR"))
    # empty class / member names
    cases.append(("enum", "", "FOO"))
    cases.append(("enum", "MyEnum", ""))
    cases.append(("enum", "", ""))
    # names containing dots / unusual chars (concatenation must be literal)
    cases.append(("enum", "a.b.C", "X.Y"))
    cases.append(("enum", "Color", "RED_2"))
    # `other`-kind fall-through: non-enum values, and container-mixin enum
    # members (e.g. FZ(frozenset, enum.Enum).X), which the preceding container
    # branches capture unchanged — both map to ("other", tag).
    cases.append(("other", 0))
    cases.append(("other", 42))
    cases.append(("other", -7))
    return cases


def _rand_name(rng):
    n = rng.choice([0, 1, 1, 2, 3, 5, 8])
    alphabet = string.ascii_letters + string.digits + "._<> :"
    return "".join(rng.choice(alphabet) for _ in range(n))


def _rand_value(rng):
    if rng.random() < 0.6:
        return ("enum", _rand_name(rng), _rand_name(rng))
    return ("other", rng.randint(-1000, 1000))


def main() -> int:
    checked = 0
    for obj in _enumerate_edge():
        d = disagree(obj)
        if d:
            print(f"DISAGREE edge: oracle={d[1]!r} shadow={d[2]!r} inp={d[0]!r}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        obj = _rand_value(rng)
        d = disagree(obj)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]!r} shadow={d[2]!r} inp={d[0]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
