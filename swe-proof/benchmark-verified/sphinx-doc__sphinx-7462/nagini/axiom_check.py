#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-7462.

This bundle consumes NO `@ContractOnly` axiom. The two member-joining
operations the patch builds on are modelled DEEPLY:

  (A-reference 1) `join_tokens` (model.py pure region) == the real upstream
      token interleaving: the members in order with a single ', ' separator
      token between consecutive members (the loop
      `for e: result.extend(unparse(e)); result.append(', '); ...; result.pop()`
      on a non-empty group). Modelled as a sequence-of-token-texts join with
      a one-token separator PSeq(44, 32).

  (A-reference 2) `join_comma` (model.py pure region) == the real CPython
      `', '.join(parts)` on a non-empty group.

The two changed operations are the EMPTY-group cases, which are concrete in
both model and patch:

  * token surface: an empty group renders as exactly the two tokens '(' ')'
    (gold) where the pre-patch code removed a non-existent trailing separator
    (`result.pop()` on the empty list) and produced no '(' ')' pair; and
  * text surface: an empty group renders as exactly the string "()" (gold)
    where the pre-patch code returned the empty join "".

This script runs the REAL `', '.join` and a faithful transcription of the real
token loop on boundary inputs (including the F2P non-empty witnesses and the
empty-group witnesses) plus randomized fuzz, asserting the deep models agree
with the real callees on the unchanged non-empty case AND that the twin
discriminates the gold empty-group rendering from the pre-patch one at BOTH
sites.

Imports nothing repo-specific (only `random`/`sys`). Exit 0 iff every
obligation holds.
"""
import random
import sys


# --- model.py deep-model reference encodings (kept in lock-step) -------------

def join_tokens(parts):
    """Reference of model.py `join_tokens`, on lists of token texts (each a
    list of code points). Returns a list of token texts: the members in order
    with a single ', ' separator token between consecutive members.
    parts: List[List[int]] -> List[List[int]] (token-text sequence)."""
    if len(parts) == 0:
        return []
    out = [list(parts[0])]
    for p in parts[1:]:
        out.append([44, 32])   # the single ', ' separator token
        out.append(list(p))
    return out


def join_comma(parts):
    """Reference of model.py `join_comma`, on lists of code points.
    parts: List[List[int]] -> List[int]."""
    if len(parts) == 0:
        return []
    out = list(parts[0])
    for p in parts[1:]:
        out.append(44)   # ','
        out.append(32)   # ' '
        out.extend(p)
    return out


def tuple_tokens(elts):
    """Reference of model.py `tuple_tokens` (gold, site A): the join tokens if
    non-empty, else the two tokens '(' ')'."""
    if len(elts) > 0:
        return join_tokens(elts)
    return [[40], [41]]


def tuple_text(elts):
    """Reference of model.py `tuple_text` (gold, site B): '(' join ')'... no:
    the comma join if non-empty, else the string '()'."""
    if len(elts) > 0:
        return join_comma(elts)
    return [40, 41]


# --- faithful transcription of the REAL upstream callees ---------------------

def real_token_loop(parts):
    """Faithful transcription of the upstream non-empty token-rendering loop in
    sphinx/domains/python.py's `unparse` Tuple branch (each member already
    rendered into its own token-text list):

        result = []
        for elem in elts:
            result.extend(<tokens of elem>)
            result.append(', ')
        result.pop()

    For an EMPTY group this reproduces the upstream defect: `result.pop()` on
    the empty list raises IndexError (exactly the crash in the bug report).
    Returns the flattened token-text sequence for a non-empty group."""
    result = []
    for p in parts:
        result.extend([list(p)])      # each member contributes its own token(s)
        result.append([44, 32])       # the ', ' punctuation token
    result.pop()                       # drop the trailing separator (crashes on [])
    return result


def real_str_join(parts):
    """The real CPython ', '.join over the members rendered as strings."""
    strs = ["".join(chr(c) for c in p) for p in parts]
    return [ord(ch) for ch in ", ".join(strs)]


# --- the checks --------------------------------------------------------------

def check_token_reference(parts):
    """Non-empty: model join_tokens(parts) == the real token loop."""
    if len(parts) == 0:
        return
    observed = real_token_loop(parts)        # real loop
    expected = join_tokens(parts)            # deep model
    assert observed == expected, (
        "join_tokens deep model unsound on %r: real loop gave %r, "
        "deep model gives %r" % (parts, observed, expected))


def check_comma_reference(parts):
    """Non-empty: model join_comma(parts) == the real ', '.join."""
    if len(parts) == 0:
        return
    observed = real_str_join(parts)          # real callee
    expected = join_comma(parts)             # deep model
    assert observed == expected, (
        "join_comma deep model unsound on %r: ', '.join gave %r, "
        "deep model gives %r" % (parts, observed, expected))


def cps(s):
    return [ord(ch) for ch in s]


def main():
    # --- boundary member lists --------------------------------------------
    boundary_parts = [
        [cps("int")],                          # single member -> itself
        [cps("int"), cps("int")],              # the F2P Tuple[int, int] members
        [cps("1"), cps("2"), cps("3")],        # the F2P (1, 2, 3) members
        [cps(""), cps("")],                    # empty members
        [cps("a"), cps("b")],
        [cps("x, y"), cps("z")],               # a ', ' inside a member
        [cps("None"), cps("None")],
        [cps("os.path")],
    ]
    for parts in boundary_parts:
        check_token_reference(parts)
        check_comma_reference(parts)

    # --- randomized fuzz over a punctuation-rich alphabet -----------------
    rng = random.Random(7462)
    alphabet = cps(", ()[]abZ09_.")
    for _ in range(30000):
        nparts = rng.randint(1, 5)             # non-empty (the unchanged case)
        parts = []
        for _ in range(nparts):
            m = rng.randint(0, 8)
            parts.append([rng.choice(alphabet) for _ in range(m)])
        check_token_reference(parts)
        check_comma_reference(parts)

    # --- bug-witness: the EMPTY group, at BOTH sites ----------------------
    # Site A (token surface). Gold renders '(' ')'; the pre-patch loop does
    # `result.pop()` on the empty list -> IndexError. We model that crash as
    # "the gold two-token rendering is unreachable for the pre-patch skeleton";
    # the abstract pre-patch image is the empty token sequence (no '(' ')'),
    # which differs from the gold.
    gold_tok_empty = tuple_tokens([])
    assert gold_tok_empty == [[40], [41]], gold_tok_empty
    # the pre-patch token loop crashes on the empty group:
    crashed = False
    try:
        real_token_loop([])
    except IndexError:
        crashed = True
    assert crashed, "pre-patch token loop did NOT crash on empty group"
    # abstract pre-patch image (unconditional join) vs gold:
    bug_tok_empty = join_tokens([])            # == []  (no '(' ')')
    assert gold_tok_empty != bug_tok_empty, "site-A twin does not discriminate"

    # Site B (text surface). Gold renders "()"; pre-patch returns "".
    gold_txt_empty = tuple_text([])
    assert "".join(chr(c) for c in gold_txt_empty) == "()"
    bug_txt_empty = join_comma([])             # the real ', '.join([]) == ""
    assert ", ".join([]) == "", "real ', '.join([]) is not the empty string"
    assert real_str_join([]) == [], "real ', '.join([]) is not empty"
    assert gold_txt_empty != bug_txt_empty, "site-B twin does not discriminate"
    assert "".join(chr(c) for c in bug_txt_empty) == ""

    # --- the non-empty cases are UNCHANGED by the fix (both surfaces) ------
    # Tuple[int, int] token surface stays the comma-token interleaving:
    assert tuple_tokens([cps("int"), cps("int")]) == \
        [cps("int"), [44, 32], cps("int")]
    # (1, 2, 3) text surface stays "1, 2, 3":
    assert "".join(chr(c) for c in tuple_text([cps("1"), cps("2"), cps("3")])) \
        == "1, 2, 3"

    print("G-AX OK: join_tokens (== real token loop) and join_comma "
          "(== ', '.join) sound on %d boundary + 30000 fuzz non-empty inputs; "
          "twin discriminates the gold empty-group rendering from the pre-patch "
          "one at BOTH the token site ('(' ')' vs crash/empty) and the text "
          "site ('()' vs '')" % len(boundary_parts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
