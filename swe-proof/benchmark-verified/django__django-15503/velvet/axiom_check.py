#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15503.

`Solution.lean` carries NO consumed axioms (the `axioms` region is empty). Its
soundness liabilities are two **A-reference deep models** in the `pure` region —
each a spelled-out model of an UNCHANGED callee that the modeled function calls.
G-AX runs the REAL callees in-container (boundary + fuzz) and asserts every
observation matches the deep model.  Exit 0 iff every obligation holds.

The two A-reference deep models (mapping.md §3):

  (A-reference 1) `compilePrefix` / `keySeg` / `canonicalDigits` / `arraySeg`
      models the UNCHANGED repo callee
        `django.db.models.fields.json.compile_json_path(ks, include_root=False)`
      on the spec domain (lists of "simple" keys — non-empty ASCII alphanumeric
      runs). The model: a numeric (all-digit) key becomes an array segment
      `[n]` with the integer normal form (leading zeros stripped, empty -> 0);
      every other simple key becomes an object member `."k"`.

  (A-reference 2) `memberSeg` models the final-key quoting rule
        `".%s" % json.dumps(key_transform)`
      (the body of the patched `compile_json_path_final_key` on the base
      HasKeyLookup) on the SAME simple-key domain: `json.dumps` of an ASCII
      alphanumeric string is just that string wrapped in double quotes, so
      `memberSeg k == '."' + k + '"'`.

`compile_json_path` is the real repo callee (unchanged by the gold patch);
`json` is the Python standard library — the same module the gold patch calls.
Imports nothing solution-specific. stdlib + the in-tree django only.
"""
import json
import random
import sys

from django.db.models.fields.json import compile_json_path

SEED = 15503
N_FUZZ = 20000

# --- mapping.md bijection: a "simple" key is a non-empty ASCII alnum run ------
_LETTERS = [chr(c) for c in range(ord("a"), ord("z") + 1)]
_LETTERS += [chr(c) for c in range(ord("A"), ord("Z") + 1)]
_DIGITS = [chr(c) for c in range(ord("0"), ord("9") + 1)]
_SIMPLE_ALPHABET = _LETTERS + _DIGITS


def is_numeric_key(k):
    """Solution.lean `isNumericKey`: non-empty all-digit run."""
    return len(k) > 0 and all(ch in _DIGITS for ch in k)


def canonical_digits(k):
    """Solution.lean `canonicalDigits`: strip leading zeros; empty residue -> '0'."""
    i = 0
    while i < len(k) and k[i] == "0":
        i += 1
    r = k[i:]
    return r if r else "0"


def key_seg_model(k):
    """Solution.lean `keySeg`: numeric -> array segment, else object member."""
    if is_numeric_key(k):
        return "[" + canonical_digits(k) + "]"
    return '."' + k + '"'


def compile_prefix_model(keys):
    """Solution.lean `compilePrefix`: front-recursive concat of `keySeg`."""
    return "".join(key_seg_model(k) for k in keys)


def member_seg_model(k):
    """Solution.lean `memberSeg`: the queried key located by name."""
    return '."' + k + '"'


# --- the A-reference checks against the REAL callees -------------------------

def check_prefix_reference(keys):
    """A-reference 1: compile_prefix_model(keys) == real compile_json_path."""
    observed = compile_json_path(list(keys), include_root=False)   # real callee
    expected = compile_prefix_model(keys)                          # deep model
    assert observed == expected, (
        "compilePrefix deep model unsound on %r: compile_json_path gave %r, "
        "deep model gives %r" % (keys, observed, expected))


def check_final_key_reference(k):
    """A-reference 2: member_seg_model(k) == '.%s' % json.dumps(k)."""
    observed = ".%s" % json.dumps(k)                               # real json.dumps
    expected = member_seg_model(k)                                 # deep model
    assert observed == expected, (
        "memberSeg deep model unsound on %r: '.%%s'%%json.dumps gave %r, "
        "deep model gives %r" % (k, observed, expected))


def random_simple_key(rng):
    n = rng.randint(1, 8)
    return "".join(rng.choice(_SIMPLE_ALPHABET) for _ in range(n))


def main():
    # --- boundary simple keys (numeric / leading-zero / mixed / letters) -----
    boundary_keys = [
        "0", "1", "9", "00", "007", "000", "42", "123", "777", "999",
        "1000000000000000000000",        # large numeric: arbitrary precision
        "a", "Z", "foo", "nested", "lorem", "ipsum", "array",
        "1a", "a1", "1e5", "0x1", "abc123", "x9",
    ]
    for k in boundary_keys:
        check_prefix_reference([k])       # single interior key
        check_final_key_reference(k)      # final-key quoting rule

    # boundary key-lists (multi-segment prefixes, incl. F2P shapes) -----------
    boundary_lists = [
        [], ["nested"], ["array", "0"], ["nested", "456"],
        ["array", "0", "789"], ["123", "456", "789"],
        ["a", "1", "b", "00", "c"], ["foo", "007", "bar"],
    ]
    for ks in boundary_lists:
        check_prefix_reference(ks)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        check_final_key_reference(random_simple_key(rng))
        m = rng.randint(0, 5)
        ks = [random_simple_key(rng) for _ in range(m)]
        check_prefix_reference(ks)

    print("G-AX OK: compilePrefix deep model (== compile_json_path) and "
          "memberSeg deep model (== '.%%s'%%json.dumps) sound on %d boundary "
          "keys + %d boundary lists + %d fuzz rounds"
          % (len(boundary_keys), len(boundary_lists), N_FUZZ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
