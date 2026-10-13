#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for matplotlib__matplotlib-21568.

The bundle models ONE pure string transform: the math-mode label produced for a
short tick-label string (`texLabel` in Solution.lean). The modeled value is a
pure function of one observable (mapping.md):

    text : str   (the raw tick label, e.g. "Jan 1990-01-01 00:00")

Post-patch rule (the real edit, lib/matplotlib/dates.py):

    ret = re.sub(r'([a-zA-Z]+)', r'}$\\1$\\mathdefault{', text)
    ret = ret.replace('-', '{-}').replace(':', '{:}')
    ret = ret.replace(' ', r'\\;')
    ret = '$\\mathdefault{' + ret + '}$'
    ret = ret.replace('$\\mathdefault{}$', '')

The ORACLE below is the EXACT post-patch expression (including the real
`re.sub`). The SHADOW is the op-for-op transliteration of
`implementation_texLabel` (refinement.md): the deep-modeled run-lifting
(`bracketLetterRuns`), the per-character symbol rewrite accumulated in a loop
(`escapeMathSym`), the outer `$\\mathdefault{` ... `}$` wrap, and the
left-to-right token deletion (`dropToken`). They must agree on every input.

This genuinely tests the deep model of the regex run-lifting (the A-reference
leg, also checked by G-AX) AND the new per-symbol escaping of `:` and ` ` (the R
leg that is the heart of the fix): in particular labels containing colons,
spaces, multiple letter runs, leading/trailing letters, and the empty string.

stdlib-only. Pinned seed: 21568 (also in mapping.md).
"""
import random
import re
import sys

SEED = 21568
N = 200_000


# --- ORACLE: the EXACT post-patch transform ---------------------------------
def oracle(text):
    p = r'([a-zA-Z]+)'
    ret = re.sub(p, r'}$\1$\\mathdefault{', text)
    ret = ret.replace('-', '{-}').replace(':', '{:}')
    ret = ret.replace(' ', r'\;')
    ret = '$\\mathdefault{' + ret + '}$'
    ret = ret.replace('$\\mathdefault{}$', '')
    return ret


# --- SHADOW of implementation_texLabel (refinement.md) ----------------------
def _bracket_letter_runs(text):
    # Stage 1: lift each maximal ASCII-letter run out of the math group.
    out = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c.isascii() and c.isalpha():
            j = i
            while j < n and text[j].isascii() and text[j].isalpha():
                j += 1
            out.extend(list("}$"))
            out.extend(list(text[i:j]))
            out.extend(list("$\\mathdefault{"))
            i = j
        else:
            out.append(c)
            i += 1
    return out


def _escape_math_sym(c):
    if c == '-':
        return ['{', '-', '}']
    if c == ':':
        return ['{', ':', '}']
    if c == ' ':
        return ['\\', ';']
    return [c]


def _drop_token(token, chars):
    # left-to-right, non-overlapping deletion of `token` (a string) from chars.
    out = []
    i, n = 0, len(chars)
    tl = len(token)
    while i < n:
        if "".join(chars[i:i + tl]) == token:
            i += tl
        else:
            out.append(chars[i])
            i += 1
    return out


def shadow(text):
    lifted = _bracket_letter_runs(text)
    escaped = []
    for c in lifted:                       # the `for c in lifted do` loop
        escaped.extend(_escape_math_sym(c))
    wrapped = list("$\\mathdefault{") + escaped + list("}$")
    return "".join(_drop_token("$\\mathdefault{}$", wrapped))


def disagree(text):
    got = oracle(text)
    want = shadow(text)
    if got != want:
        return (text, got, want)
    return None


def _enumerate_edge():
    return [
        "",
        "Jan",
        "Jan 1990-01-01 00:00",
        "1990-01-01",
        "01-01 00",
        "01 00:00",
        "Jan 01",
        "00:00:00",
        "59.5",
        "Feb",
        "Jan-01",            # letter run immediately followed by hyphen
        "-",                 # lone hyphen
        ":",                 # lone colon
        " ",                 # lone space
        "::--  ",            # only symbols
        "abc",               # all letters -> empty math group dropped
        "a b c",             # letters separated by spaces
        "1996-Jan-01",       # mixed
        "Jan$\\mathdefault{04:00}$",  # already-mathy text
        "20:00",
        "AB12CD",            # alternating letter/digit runs
    ]


# Character pool: letters, digits, and the three special symbols + a few others
POOL = list("abcXYZ0123456789-: .,/JanFeb")


def main() -> int:
    checked = 0
    for t in _enumerate_edge():
        d = disagree(t)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        k = rng.randint(0, 24)
        t = "".join(rng.choice(POOL) for _ in range(k))
        d = disagree(t)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
