#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sympy__sympy-20916.

The bundle models ONE thing: the trailing-digit split step of `split_super_sub`
(`sympy/printing/conventions.py:65-68`), whose behavior the gold patch changes by
rewriting the module regex `_name_with_digits_p` from `^([a-zA-Z]+)([0-9]+)$` to
`^([^\\W\\d_]+)(\\d+)$` with `re.U` (mapping.md).

* ORACLE — the POST-PATCH behaviour: `_name_with_digits_p.match(name)` with the
  gold regex, returning `(name, sub)` when it matches (`m.groups()`) or
  `(name, None)` when it does not. This is the real repo semantics of the edited
  regex, driven directly with Python's own `re` engine — no re-implementation.
* SHADOW — the op-for-op transliteration of `implementation_splitTrailingDigits`
  (Solution.lean impl region), per refinement.md (rows 1, 4-10). The two
  A-reference character classes (rows 2-3, `isUnicodeLetter` / `isUnicodeDigit`)
  are left as the REAL repo callee: Python's `re` engine evaluating `[^\\W\\d_]`
  and `\\d` under `re.U`.

We diff SHADOW vs ORACLE over an edge set (incl. the F2P Unicode cases: `w1`,
`w𝟙`, `ω1`, `ω11`, `w𝟙2𝟙`, … and the `$`-before-one-final-`\n` rule: Python's
non-MULTILINE `$` also matches just before a single terminating newline, so
`"a1\n"` splits to `('a','1')` while `"a1\n\n"`, `"a1\r"` do not) plus >=10^5
fuzzed names drawn from an alphabet that stresses ASCII letters/digits,
Greek/Cyrillic letters, non-ASCII decimal digits, `_`, `^`, `\n`, `\r`, and
separators. Exit 0 iff zero disagreements.

stdlib-only. Pinned seed: 20916 (also in mapping.md).
"""
import random
import re
import sys

SEED = 20916
N = 150_000

# Gold POST-PATCH regex (the edited `_name_with_digits_p`).
GOLD = re.compile(r'^([^\W\d_]+)(\d+)$', re.U)

# A-reference character classes, evaluated by the REAL `re` engine under re.U.
_LETTER = re.compile(r'[^\W\d_]', re.U)
_DIGIT = re.compile(r'\d', re.U)


def is_unicode_letter(c: str) -> bool:
    return _LETTER.match(c) is not None


def is_unicode_digit(c: str) -> bool:
    return _DIGIT.match(c) is not None


def oracle(name: str):
    """Post-patch semantics: (base, sub) on a match, else (name, None)."""
    m = GOLD.match(name)
    if m:
        return (m.group(1), m.group(2))
    return (name, None)


def _take_while(name, pred):
    i = 0
    while i < len(name) and pred(name[i]):
        i += 1
    return name[:i]


def _drop_while(name, pred):
    i = 0
    while i < len(name) and pred(name[i]):
        i += 1
    return name[i:]


def shadow(name: str):
    # transliteration of implementation_splitTrailingDigits
    base = _take_while(name, is_unicode_letter)
    rest = _drop_while(name, is_unicode_letter)
    digits = _take_while(rest, is_unicode_digit)
    trailer = _drop_while(rest, is_unicode_digit)
    if base != "" and digits != "" and (trailer == "" or trailer == "\n"):
        return (base, digits)
    return (name, None)


def disagree(name):
    got, want = oracle(name), shadow(name)
    if got != want:
        return (name, got, want)
    return None


def _edge_cases():
    return [
        "",                # empty -> no split
        "w1",              # ASCII base + ASCII digit -> ('w', '1')
        "w11",             # -> ('w', '11')
        "ω1",         # ω1 -> ('ω', '1')     (F2P)
        "ω11",        # ω11 -> ('ω', '11')   (F2P)
        "w\U0001D7D9",     # w𝟙 -> ('w', '𝟙')     (F2P, non-ASCII digit)
        "w\U0001D7D9\U0001D7D9",   # w𝟙𝟙 -> ('w', '𝟙𝟙')
        "w\U0001D7D92\U0001D7D9",  # w𝟙2𝟙 -> ('w', '𝟙2𝟙')  (mixed digits)
        "beta",            # letters only -> no split
        "beta13",          # -> ('beta', '13')
        "13",              # digits only -> no split (needs >=1 letter)
        "w1a",             # letters-digits-letters -> no split
        "a1b2",            # -> no split
        "w_1",             # underscore breaks it -> no split
        "_1",              # leading underscore -> no split
        "аб123", # Cyrillic аб123 -> ('аб', '123')
        "x²",         # x + superscript-two (\d? no) -> depends on re
        "١٢",    # Arabic-Indic digits only -> no split
        "w١",         # w + Arabic-Indic digit -> ('w', '١')
        "a1\n",            # $ matches before ONE final newline -> ('a', '1')
        "beta13\n",        # -> ('beta', '13')
        "ω1\n",       # Greek + digit + newline -> ('ω', '1')
        "a1\n\n",          # two newlines -> no split
        "a1\r",            # \r is not the tolerated newline -> no split
        "a1\r\n",          # -> no split
        "a\n",             # letters-only + newline -> no split
        "1\n",             # digits-only + newline -> no split
        "a1\nb",           # newline not final -> no split
        "a\n1",            # newline inside -> no split
        "\n",              # newline only -> no split
    ]


def main() -> int:
    checked = 0
    for s in _edge_cases():
        d = disagree(s)
        if d:
            print(f"DISAGREE edge: name={d[0]!r} oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    # Alphabet stressing: ASCII letters/digits, Greek + Cyrillic letters,
    # mathematical + Arabic-Indic decimal digits (\d matches), `_`, `^`, space.
    alphabet = (list("abcXYZ") + list("019") +
                ["ω", "α", "Β", "а", "б"] +   # ω α Β а б
                ["\U0001D7D9", "\U0001D7DA", "١", "٢"] +      # 𝟙 𝟚 ١ ٢
                ["_", "^", " ", "²"] +                              # underscore, caret, space, ²
                ["\n", "\r"])                                       # newline (the `$` end rule), CR
    for _ in range(N):
        n = rng.randint(0, 8)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        d = disagree(s)
        if d:
            print(f"DISAGREE fuzz: name={d[0]!r} oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"status=pass checked={checked}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
