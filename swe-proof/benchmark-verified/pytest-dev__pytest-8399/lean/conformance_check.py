#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for pytest-dev__pytest-8399.

The bundle models ONE routine: the construction of the synthesized setup–teardown
fixture's name in `_make_xunit_fixture` (mapping.md). The modeled value is a PURE
function of the two string observables the real expression reads:

    setupName  (= setup_name)
    qualname   (= obj.__qualname__)

Post-patch rule (the gold edit PREPENDS a leading `_` private marker to the
f-string):

    name = "_" + f"unittest_{setup_name}_fixture_{obj.__qualname__}"

The ORACLE below is a faithful in-process replica of the POST-PATCH f-string. The
SHADOW is the op-for-op transliteration of `implementation_generatedFixtureName`
(Solution.lean impl region), per refinement.md: append the marker, the template
head, setupName, the template tail, and qualname in order.

This genuinely tests the soundness-critical clause: the generated name must begin
with `_` (so the consumer hides it at default verbosity — the F2P expectation),
while the remaining components are exactly the descriptive name. A pre-patch
shadow (no leading `_`) disagrees on every input.

stdlib-only. Pinned seed: 8399 (also in mapping.md).
"""
import random
import sys

SEED = 8399
N = 120_000

ID_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_."


# --- ORACLE: faithful in-process replica of the POST-PATCH name expression ----
def oracle(setup_name, qualname):
    return "_" + f"unittest_{setup_name}_fixture_{qualname}"


# --- SHADOW: op-for-op transliteration of implementation_generatedFixtureName --
def shadow(setup_name, qualname):
    name = ""
    name = name + "_"
    name = name + "unittest_"
    name = name + setup_name
    name = name + "_fixture_"
    name = name + qualname
    return name


def rand_str(rng, max_len=24):
    n = rng.randint(0, max_len)
    return "".join(rng.choice(ID_CHARS) for _ in range(n))


def main():
    rng = random.Random(SEED)

    # Hand-picked edge cases (incl. the F2P scenario).
    cases = [
        ("", ""),
        ("setUpClass", "MyTestCase"),
        ("setup_class", "Test"),
        ("setUpModule", "module"),
        ("setup_method", "Outer.Inner"),     # dotted qualname (nested class)
        ("", "X"),
        ("Y", ""),
        ("a_b_c", "A.B.C.D"),
    ]
    for _ in range(N):
        cases.append((rand_str(rng), rand_str(rng)))

    mism = 0
    first = None
    for setup_name, qualname in cases:
        o = oracle(setup_name, qualname)
        s = shadow(setup_name, qualname)
        if o != s:
            mism += 1
            if first is None:
                first = (setup_name, qualname, o, s)

    if mism == 0:
        print(f"G-CONF pass: {len(cases)} inputs, 0 disagreements (seed={SEED})")
        sys.exit(0)
    else:
        print(f"G-CONF FAIL: {mism}/{len(cases)} disagreements; first={first}")
        sys.exit(1)


if __name__ == "__main__":
    main()
