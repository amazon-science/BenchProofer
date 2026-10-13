#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-16886 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (the per-symbol
              code table `codeOf` and its per-word assembly `codesOf`)
              transliterated to Python over the real repo type (`str`), wrapped
              in the UNCHANGED I-ops of `encode_morse` (whitespace
              normalization, unmapped-symbol filtering, `sep`/`word_sep` joins,
              trailing-whitespace suffix). There are no A-tagged callees in the
              impl region (no consumed axiom), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `sympy.crypto.crypto.encode_morse` applied at base_commit (the
              real correctness oracle, G-RESOLVE; the harness applies patch.diff
              before this runs).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + repo only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import string
import sys

SEED = 16886
N_FUZZ = 100_000
WHITESPACE = string.whitespace

# --- the R/I shadow: Solution.lean codeOf, transliterated --------------------
# codeOf (c : Char) : List Char  -- canonical telegraphic code per symbol.
_CODE = {
    'A': ".-",     'B': "-...",  'C': "-.-.",  'D': "-..",
    'E': ".",      'F': "..-.",  'G': "--.",   'H': "....",
    'I': "..",     'J': ".---",  'K': "-.-",   'L': ".-..",
    'M': "--",     'N': "-.",    'O': "---",   'P': ".--.",
    'Q': "--.-",   'R': ".-.",   'S': "...",   'T': "-",
    'U': "..-",    'V': "...-",  'W': ".--",   'X': "-..-",
    'Y': "-.--",   'Z': "--..",
    '0': "-----",  '1': ".----", '2': "..---", '3': "...--",
    '4': "....-",  '5': ".....", '6': "-....", '7': "--...",
    '8': "---..",  '9': "----.",
    '.': ".-.-.-", ',': "--..--", ':': "---...", ';': "-.-.-.",
    '?': "..--..", '-': "-....-", '_': "..--.-", '(': "-.--.",
    ')': "-.--.-", "'": ".----.", '=': "-...-",  '+': ".-.-.",
    '/': "-..-.",  '@': ".--.-.", '$': "...-..-", '!': "-.-.--",
}


def shadow_encode(msg, sep='|'):
    """encode_morse rebuilt from the R/I shadow of codesOf (`_CODE`) plus the
    unchanged surrounding I-ops, transliterated faithfully from crypto.py."""
    mapping = dict(_CODE)                 # shadow of char_morse
    assert sep not in mapping
    word_sep = 2 * sep
    mapping[" "] = word_sep
    suffix = bool(msg) and msg[-1] in WHITESPACE
    # normalize whitespace
    msg = (' ' if word_sep else '').join(msg.split())
    # omit unmapped chars (translate(msg, None, ''.join(chars - ok)))
    chars = set(''.join(msg.split()))
    ok = set(mapping.keys())
    delete = chars - ok
    msg = ''.join(c for c in msg if c not in delete)
    morsestring = []
    words = msg.split()
    for word in words:
        morseword = [mapping[letter] for letter in word]   # codesOf word
        morsestring.append(sep.join(morseword))
    return word_sep.join(morsestring) + (word_sep if suffix else '')


def oracle_encode(msg, sep='|'):
    """patch.diff's behaviour: the patched encode_morse (gold applied)."""
    from sympy.crypto.crypto import encode_morse
    return encode_morse(msg, sep=sep)


def fuzz_inputs(n, rng):
    table_syms = list(_CODE.keys())
    spaces = [' ', '  ', '\t', '\n']
    unmapped = list("abcdefghz%^&*\"`~[]{}<>#") + ["é", "•"]
    alphabet = table_syms + spaces + unmapped
    # boundary cases first
    yield ("", '|')
    yield ("12345", '|')          # the F2P-style digit string (1 corrected)
    yield ("67890", '|')
    yield ("1", '|')
    yield ("ATTACK RIGHT FLANK", '|')
    yield ("!@#$%^&*()_+", '|')
    yield (" ", '|')
    yield (" ", '`')
    yield (" ", '``')
    yield ("HELLO WORLD ", '|')   # trailing-whitespace suffix
    yield ("0123456789", '|')
    yield ("THE QUICK BROWN FOX 1234", '|')
    seps = ['|', '`', '#', '*', '%', '^']
    for _ in range(n):
        k = rng.randint(0, 20)
        msg = "".join(rng.choice(alphabet) for _ in range(k))
        sep = rng.choice(seps)
        # encode_morse asserts sep not in mapping; all chosen seps are off-table.
        yield (msg, sep)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for msg, sep in fuzz_inputs(N_FUZZ, rng):
        count += 1
        try:
            shadow = shadow_encode(msg, sep)
        except AssertionError:
            continue   # sep in mapping: encode_morse would also assert; skip
        oracle = oracle_encode(msg, sep)
        if shadow != oracle:
            disagreements.append((msg, sep, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for msg, sep, sh, orc in disagreements:
            print("  msg=%r sep=%r shadow=%r oracle=%r" % (msg, sep, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of encodeWord (codesOf + unchanged I-ops) "
          "agrees with patch.diff behaviour on %d inputs (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
