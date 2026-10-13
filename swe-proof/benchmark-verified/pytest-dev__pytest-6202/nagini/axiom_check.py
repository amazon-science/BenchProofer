#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-6202.

This bundle consumes NO `@ContractOnly` axiom. The two sequence operations the
patch touches are modelled DEEPLY over `PSeq[int]`:

  (A-reference) `join_dot` (model.py pure region) == the real CPython
      `".".join(parts)`. `join_dot` concatenates the name parts with a single
      '.' (code point 46) between consecutive parts.

  (A-reference) `replace_db` (the deep model of the pre-patch substitution used
      only in model_prepatch.py's impl) == the real CPython
      `s.replace(".[", "[")`: left-to-right, non-overlapping replacement of the
      two-code-point pattern '.[' ([46, 91]) by '[' ([91]).

This script runs the REAL str.join / str.replace on boundary inputs (including
the F2P collection witness) plus randomized fuzz and asserts both deep models
agree with the real callees. It also asserts the bug-witness property the twin
relies on: on the F2P part list the gold result (the plain dot-join) differs
from the pre-patch result (the dot-join with the substitution applied) -- so the
spec genuinely discriminates the fix from the bug.

Imports nothing repo-specific (only `random`/`sys`). Exit 0 iff every
obligation holds.
"""
import random
import sys


# --- model.py deep-model reference encodings (kept in lock-step) -------------

def join_dot(parts):
    """Reference implementation of model.py's `join_dot`, on lists of code
    points. parts: List[List[int]] -> List[int]."""
    if len(parts) == 0:
        return []
    out = list(parts[0])
    for p in parts[1:]:
        out.append(46)  # '.'
        out.extend(p)
    return out


def replace_db(s):
    """Reference implementation of model_prepatch.py's `replace_db`, on a list
    of code points: left-to-right non-overlapping '.[' -> '[' (46,91 -> 91)."""
    out = []
    j = 0
    n = len(s)
    while j < n:
        if j + 1 < n and s[j] == 46 and s[j + 1] == 91:
            out.append(91)
            j += 2
        else:
            out.append(s[j])
            j += 1
    return out


# --- the checks --------------------------------------------------------------

def check_join_reference(parts):
    """Assert the deep model join_dot(parts) == the REAL '.'.join(parts)."""
    strs = ["".join(chr(c) for c in p) for p in parts]
    observed = [ord(ch) for ch in ".".join(strs)]          # real callee
    expected = join_dot(parts)                             # deep model
    assert observed == expected, (
        "join_dot deep model unsound on %r: str.join gave %r, "
        "deep model gives %r" % (strs, observed, expected))


def check_replace_reference(codepoints):
    """Assert the deep model replace_db(s) == the REAL s.replace('.[', '[')."""
    s = "".join(chr(c) for c in codepoints)
    observed = [ord(ch) for ch in s.replace(".[", "[")]    # real callee
    expected = replace_db(codepoints)                      # deep model
    assert observed == expected, (
        "replace_db deep model unsound on %r: str.replace gave %r, "
        "deep model gives %r" % (s, observed, expected))


def cps(s):
    return [ord(ch) for ch in s]


def main():
    # --- join_dot deep model (A-reference): boundary part lists -----------
    boundary_parts = [
        [],                                   # join of nothing -> ""
        [cps("testone")],                     # single part -> itself
        [cps("TestX"), cps("testmethod_one")],
        [cps("TestY"), cps("testmethod_one")],
        # the F2P collection witness: a parametrised test under a class
        [cps("TestY"), cps("testmethod_two[.[]")],
        [cps(""), cps("")],                   # empty parts
        [cps("a.b"), cps("c")],               # a '.' inside a part
        [cps("x"), cps("[")], [cps("x"), cps(".[")],
        [cps(".["), cps(".[")],
        [cps("test_boo[..[]")],               # the issue's headline example
    ]
    for parts in boundary_parts:
        check_join_reference(parts)

    # --- replace_db deep model (A-reference): boundary strings ------------
    boundary_replace = [
        "", ".", "[", ".[", "..[", ".[.[", "[.[", ".[]", "[.[]",
        "TestY.testmethod_two[.[]",            # the joined F2P path
        "test_boo[..[]",
        "a.b.c", "....", "[[[[", ".[.[.[",
        "no brackets here", "trailing.", ".[lead",
    ]
    for s in boundary_replace:
        check_replace_reference(cps(s))

    # --- randomized fuzz over a '.['-rich alphabet ------------------------
    rng = random.Random(6202)
    alphabet = cps(".[]abT0_")
    for _ in range(30000):
        # random join over up to 4 parts
        nparts = rng.randint(0, 4)
        parts = []
        for _ in range(nparts):
            m = rng.randint(0, 8)
            parts.append([rng.choice(alphabet) for _ in range(m)])
        check_join_reference(parts)
        # random replace over a single string
        k = rng.randint(0, 16)
        s = [rng.choice(alphabet) for _ in range(k)]
        check_replace_reference(s)

    # --- bug-witness: the twin discriminates fix from bug -----------------
    # On the F2P part list, the gold result (plain join) must differ from the
    # pre-patch result (join then substitution) -- this is what the spec senses.
    witness = [cps("TestY"), cps("testmethod_two[.[]")]
    gold = join_dot(witness)
    bug = replace_db(join_dot(witness))
    assert gold != bug, "twin does not discriminate on the F2P witness"
    assert "".join(chr(c) for c in gold) == "TestY.testmethod_two[.[]"
    assert "".join(chr(c) for c in bug) == "TestY.testmethod_two[[]"

    print("G-AX OK: join_dot deep model (== str.join) + replace_db deep model "
          "(== str.replace) sound on %d + %d boundary inputs and 30000 fuzz "
          "rounds; twin discriminates the fix from the bug on the F2P witness"
          % (len(boundary_parts), len(boundary_replace)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
