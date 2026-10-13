#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8265.

This bundle consumes NO `@ContractOnly` axiom.  The one string operation the
patch builds on is modelled DEEPLY over `PSeq[int]`:

  (A-reference) `join_comma` (model.py pure region) == the real CPython
      `', '.join(parts)`.  `join_comma` concatenates the rendered members with
      a single ', ' (code points 44, 32) between consecutive members.

The remaining operations are bare bracket-character concatenation, modelled
deeply and identically in both the model and the real patch (literal '(' ')'
'[' ']' code points), so there is nothing opaque to axiomatize: each member's
own rendering and a non-group index's rendering are unchanged upstream
computations that the model takes as already-rendered inputs.

This script runs the REAL `', '.join` on boundary inputs (including the F2P
tuple witness and the P2P subscript witness) plus randomized fuzz and asserts
the deep model agrees with the real callee.  It also asserts the two bug-witness
properties the twin relies on:

  * the gold standalone-group rendering `(m0, m1, ...)` differs from the
    pre-patch bare-join rendering `m0, m1, ...`  (site 1 discriminator); and
  * the gold simple-group index body `base[m0, m1]` differs from the pre-patch
    body `base[(m0, m1)]` that the standalone-group parenthesisation would
    otherwise induce  (site 2 / coupling discriminator).

Imports nothing repo-specific (only `random`/`sys`).  Exit 0 iff every
obligation holds.
"""
import random
import sys


# --- model.py deep-model reference encodings (kept in lock-step) -------------

def join_comma(parts):
    """Reference implementation of model.py's `join_comma`, on lists of code
    points.  parts: List[List[int]] -> List[int]."""
    if len(parts) == 0:
        return []
    out = list(parts[0])
    for p in parts[1:]:
        out.append(44)   # ','
        out.append(32)   # ' '
        out.extend(p)
    return out


def tuple_render(elts):
    """Reference of model.py `tuple_render` (gold): '(' join ')' if non-empty,
    else '()'."""
    if len(elts) > 0:
        return [40] + join_comma(elts) + [41]
    return [40, 41]


def subscript_render(value, elts, simple_tuple, slice_rendered):
    """Reference of model.py `subscript_render` (gold)."""
    if simple_tuple:
        body = join_comma(elts)
    else:
        body = list(slice_rendered)
    return list(value) + [91] + body + [93]


# --- the checks --------------------------------------------------------------

def check_join_reference(parts):
    """Assert the deep model join_comma(parts) == the REAL ', '.join(parts)."""
    strs = ["".join(chr(c) for c in p) for p in parts]
    observed = [ord(ch) for ch in ", ".join(strs)]         # real callee
    expected = join_comma(parts)                           # deep model
    assert observed == expected, (
        "join_comma deep model unsound on %r: ', '.join gave %r, "
        "deep model gives %r" % (strs, observed, expected))


def cps(s):
    return [ord(ch) for ch in s]


def main():
    # --- join_comma deep model (A-reference): boundary member lists -------
    boundary_parts = [
        [],                                   # join of nothing -> ""
        [cps("1")],                           # single member -> itself
        [cps("1"), cps("2"), cps("3")],       # the F2P tuple members
        [cps("int"), cps("int")],             # the P2P subscript members
        [cps(""), cps("")],                   # empty members
        [cps("a"), cps("b")],
        [cps("x, y"), cps("z")],              # a ', ' inside a member
        [cps("None"), cps("None")],
        [cps("lines"), cps("color"), cps("width")],
    ]
    for parts in boundary_parts:
        check_join_reference(parts)

    # --- randomized fuzz over a punctuation-rich alphabet -----------------
    rng = random.Random(8265)
    alphabet = cps(", ()[]abZ09_.")
    for _ in range(30000):
        nparts = rng.randint(0, 5)
        parts = []
        for _ in range(nparts):
            m = rng.randint(0, 8)
            parts.append([rng.choice(alphabet) for _ in range(m)])
        check_join_reference(parts)

    # --- bug-witness 1 (site 1, the F2P tuple): the twin discriminates ----
    # The standalone group (1, 2, 3) must render WITH round brackets; the
    # pre-patch bare join (no brackets) is a different string -- this is the
    # F2P discrimination the spec encodes.
    tup = [cps("1"), cps("2"), cps("3")]
    gold_tuple = tuple_render(tup)
    bug_tuple = join_comma(tup)                # pre-patch: no surrounding ()
    assert gold_tuple != bug_tuple, "site-1 twin does not discriminate"
    assert "".join(chr(c) for c in gold_tuple) == "(1, 2, 3)"
    assert "".join(chr(c) for c in bug_tuple) == "1, 2, 3"

    # empty group is unchanged by the fix: '()' both ways
    assert "".join(chr(c) for c in tuple_render([])) == "()"

    # --- bug-witness 2 (site 2, the P2P subscript): coupling discriminator -
    # A simple group used as an index must render as base[m0, m1] (bare join,
    # no inner round brackets).  The pre-patch body would be the standalone
    # group's own (parenthesised) rendering base[(m0, m1)] -- a different
    # string -- which is why the subscript site is fixed alongside the tuple.
    val = cps("Tuple")
    sub = [cps("int"), cps("int")]
    gold_sub = subscript_render(val, sub, True, [])
    bug_sub = list(val) + [91] + tuple_render(sub) + [93]   # base[(int, int)]
    assert gold_sub != bug_sub, "site-2 twin does not discriminate"
    assert "".join(chr(c) for c in gold_sub) == "Tuple[int, int]"
    assert "".join(chr(c) for c in bug_sub) == "Tuple[(int, int)]"

    # a non-group index is rendered verbatim and is unaffected by the fix
    g = subscript_render(cps("x"), [], False, cps("1"))
    assert "".join(chr(c) for c in g) == "x[1]"

    print("G-AX OK: join_comma deep model (== ', '.join) sound on %d boundary "
          "+ 30000 fuzz inputs; twin discriminates the fix from the bug at "
          "both the standalone-group site (F2P (1, 2, 3)) and the simple-group "
          "index site (P2P Tuple[int, int])" % len(boundary_parts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
