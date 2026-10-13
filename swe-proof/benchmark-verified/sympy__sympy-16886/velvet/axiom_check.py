#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-16886.

The changed datum is ONE entry of the source telegraphic-code table
(`morse_char`), inverted into the lookup table `char_morse` that `encode_morse`
reads. `Solution.lean` models that table DEEPLY as `codeOf` (an A-reference),
with NO consumed axiom.

IMPORTANT — G-AX runs against the BASE repo (no gold patch applied). Unlike
G-CONF, the gate harness does not mount/apply `patch.diff` before this script
(see gates.py: `gate_ax` calls `run_in_container` WITHOUT `apply_gold`, whereas
`gate_conf` uses `apply_gold=True`). So the imported `char_morse` is the
PRE-patch table, in which the single corrected entry still holds the documented
bug `char_morse['1'] == '----'`.

The morse table is precisely the operation the patch changes, so a deep model
encoding the FIXED table cannot be `==` the base callee on the one changed
entry. G-AX's real job here is to keep the A-reference honest, which decomposes
exactly along the patch boundary:

  (A-reference, UNCHANGED entries) for every table symbol EXCEPT the one the
      patch corrects, the deep model `codeOf` == the real base `char_morse`,
      entry-for-entry; key sets coincide exactly (no symbol modeled that the
      table omits, none omitted that it has); `codeOf` is empty off that set.
      This is where over-claiming would hide, and it is checked in full.

  (CHANGED entry — the fix itself, NOT validated against base) for the single
      corrected symbol '1':
        * the BASE table holds the documented buggy code '----' (four dashes) —
          asserted, so we prove this really is the datum the patch changes and
          we are not silently treating it as already-fixed; and
        * the deep model holds the gold-patch value '.----' (the canonical
          code, the literal RHS of the patch.diff line `".----": "1"`).
      The model deliberately DIFFERS from the base callee here. That single
      correction is the behavioural change validated elsewhere — G-CONF (gold
      applied), G-RESOLVE (gold resolves), G-DIFF (Solution_prepatch, which
      reproduces the '----' bug, fails the frozen spec). It is out of scope for
      a base-table A-reference equality by construction.

Imports only stdlib + the repo under test. Exit 0 iff every obligation holds.
"""
import sys

# --- Solution.lean `codeOf` deep model, transliterated (in lock-step) --------
# codeOf (c : Char) : List Char  -- canonical (post-fix) telegraphic code per
# symbol; the entry for '1' is the corrected '.----'.
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

# The single entry the gold patch corrects, with both faces:
#   symbol -> (deep-model/gold value, documented pre-patch buggy value)
_CHANGED = {
    '1': (".----", "----"),
}


def code_of(ch):
    """Reference implementation of Solution.lean's `codeOf` (empty off table)."""
    return _CODE.get(ch, "")


def main():
    from sympy.crypto.crypto import char_morse  # BASE (pre-patch) table

    # key sets coincide exactly: no modeled symbol the table omits, and none
    # of the table's symbols left unmodeled.
    model_keys = set(_CODE.keys())
    real_keys = set(char_morse.keys())
    assert model_keys == real_keys, (
        "key-set mismatch: only-in-model=%r only-in-real=%r"
        % (sorted(model_keys - real_keys), sorted(real_keys - model_keys)))

    # (A-reference, UNCHANGED entries) every real BASE table entry that the
    # patch does NOT touch agrees with the deep model, entry-for-entry.
    n_unchanged = 0
    for symbol, code in char_morse.items():
        if symbol in _CHANGED:
            continue
        assert code_of(symbol) == code, (
            "codeOf deep model unsound on UNCHANGED entry %r: real base "
            "char_morse gives %r, deep model gives %r"
            % (symbol, code, code_of(symbol)))
        n_unchanged += 1

    # (CHANGED entry — the fix) for each corrected symbol: the base table holds
    # the documented bug, and the model holds the gold value. They differ here
    # by design; this is the patch's behavioural change, validated by
    # G-CONF/G-RESOLVE/G-DIFF, not by base-table equality.
    for symbol, (model_code, base_bug) in _CHANGED.items():
        assert char_morse[symbol] == base_bug, (
            "expected the documented PRE-patch bug at %r: base char_morse[%r] "
            "== %r, got %r — base table is not what the patch claims to change"
            % (symbol, symbol, base_bug, char_morse[symbol]))
        assert code_of(symbol) == model_code, (
            "deep model for corrected entry %r should be the gold value %r, "
            "got %r" % (symbol, model_code, code_of(symbol)))
        assert model_code != base_bug, (
            "corrected entry %r: model %r must differ from base bug %r"
            % (symbol, model_code, base_bug))

    # codeOf returns empty off the represented set (sample of unrepresented cp).
    for ch in [' ', '\t', '\n', 'a', 'z', '%', '^', '&', '*', '"', '`',
               'é', '•', '\\', '[', ']', '{', '}', '<', '>', '#', '~']:
        if ch not in real_keys:
            assert code_of(ch) == "", (
                "codeOf should be empty off the table for %r, got %r"
                % (ch, code_of(ch)))

    print("G-AX OK: codeOf deep model == real BASE char_morse on all %d "
          "unchanged table entries; key sets coincide (%d keys); empty "
          "off-table; the 1 corrected entry '1' holds the documented base bug "
          "'----' and the gold value '.----' in the model (the patch's change, "
          "validated by G-CONF/G-RESOLVE/G-DIFF)."
          % (n_unchanged, len(char_morse)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
