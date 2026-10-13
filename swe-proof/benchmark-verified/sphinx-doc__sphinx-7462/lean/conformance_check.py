#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-7462.

The bundle models the two `unparse` `ast.Tuple` branches that the fix touches:

* display-token view (`sphinx/domains/python.py`) → renderTupleSig
* source-text view (`sphinx/pycode/ast.py`)       → renderTupleText

Both assemble a sequence display from the ALREADY-RENDERED element pieces. The
per-element recursion (`unparse(elem)`) is UNCHANGED and is universally
quantified in the Lean theorems, so here the inputs are abstract already-rendered
elements: a `List[List[token]]` for the token view and a `List[str]` for the
text view. A token is modeled as a `(kind, text)` pair, matching `SigToken`
(`punct`/`text`); `desc_sig_punctuation('', s)` → `("punct", s)`.

ORACLE = faithful replica of the POST-PATCH branch bodies.
SHADOW = op-for-op transliteration of the `implementation_*` impl regions
         (Solution.lean), per refinement.md.

This differential-tests the soundness-critical empty-sequence clause for BOTH
functions:
* empty tuple (display)  → exactly [('punct','('), ('punct',')')], no pop/crash;
* empty tuple (text)     → exactly '()', not ''.

stdlib-only. Pinned seed: 7462 (also in mapping.md / meta.json).
"""
import random
import sys

SEED = 7462
N = 120_000

SEP = ("punct", ", ")
# pool of already-rendered element token-lists (stand-ins for unparse(elem))
TOKEN_ELEM_POOL = [
    [("text", "int")],
    [("text", "str")],
    [("text", "Foo"), ("punct", "["), ("text", "int"), ("punct", "]")],
    [("punct", "("), ("punct", ")")],
    [("text", "a"), ("punct", "."), ("text", "b")],
]
TEXT_ELEM_POOL = ["int", "str", "Foo[int]", "a.b", "1", "...", "lambda x: ..."]


# --- ORACLE: faithful replica of POST-PATCH branch bodies ---------------------
def oracle_sig(elems):
    # post-patch sphinx/domains/python.py ast.Tuple branch
    if elems:
        result = []
        for elem in elems:
            result.extend(elem)            # result.extend(unparse(elem))
            result.append(SEP)             # result.append(desc_sig_punctuation('', ', '))
        result.pop()
    else:
        result = [("punct", "("), ("punct", ")")]
    return result


def oracle_text(elems):
    # post-patch sphinx/pycode/ast.py ast.Tuple branch
    if elems:
        return ", ".join(elems)
    else:
        return "()"


# --- SHADOW of the implementation_* impl regions (the R/I legs) ---------------
def shadow_sig(elems):
    if not elems:                          # elems.isEmpty
        return [("punct", "("), ("punct", ")")]
    result = []
    for elem in elems:                     # for elem in elems
        result = result + elem             # result := result ++ elem
        result = result + [SEP]            # result := result ++ [punct ", "]
    return result[:-1] if result else result  # result.dropLast


def shadow_text(elems):
    if not elems:                          # elems.isEmpty
        return "()"
    return ", ".join(elems)                # String.intercalate ", " elems


def _edge_cases():
    sig = [
        [],                                          # F2P: empty tuple display
        [[("text", "int")]],                         # singleton
        [[("text", "int")], [("text", "str")]],      # two elements
        [[("punct", "("), ("punct", ")")]],          # element is itself ()
        [[], [("text", "x")]],                        # empty rendered element
    ]
    text = [
        [],                                          # F2P: empty tuple text -> "()"
        ["int"],
        ["int", "str", "float"],
        ["1", "2", "3"],
        [""],                                        # one empty element text
    ]
    return sig, text


def main() -> int:
    checked = 0
    sig_edges, text_edges = _edge_cases()
    for elems in sig_edges:
        got, want = oracle_sig(elems), shadow_sig(elems)
        if got != want:
            print(f"DISAGREE edge sig: oracle={got!r} shadow={want!r} elems={elems!r}")
            print("status=fail"); return 1
        checked += 1
    for elems in text_edges:
        got, want = oracle_text(elems), shadow_text(elems)
        if got != want:
            print(f"DISAGREE edge text: oracle={got!r} shadow={want!r} elems={elems!r}")
            print("status=fail"); return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        n = rng.randint(0, 5)
        elems_sig = [list(rng.choice(TOKEN_ELEM_POOL)) for _ in range(n)]
        got, want = oracle_sig(elems_sig), shadow_sig(elems_sig)
        if got != want:
            print(f"DISAGREE fuzz sig: oracle={got!r} shadow={want!r} elems={elems_sig!r}")
            print("status=fail"); return 1
        checked += 1

        m = rng.randint(0, 5)
        elems_text = [rng.choice(TEXT_ELEM_POOL) for _ in range(m)]
        got, want = oracle_text(elems_text), shadow_text(elems_text)
        if got != want:
            print(f"DISAGREE fuzz text: oracle={got!r} shadow={want!r} elems={elems_text!r}")
            print("status=fail"); return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
