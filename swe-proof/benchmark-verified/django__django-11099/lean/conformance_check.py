#!/usr/bin/env python3
r"""G-CONF — mechanical differential conformance for django__django-11099.

The bundle models TWO functions: applying `ASCIIUsernameValidator` and
`UnicodeUsernameValidator` (django/contrib/auth/validators.py). Each is
`RegexValidator.__call__`: it ACCEPTS a value iff
`self.regex.search(str(value)) is not None`, with the post-patch regex
`r'^[\w.@+-]+\Z'` compiled under `re.ASCII` (ascii) / flags `0` (unicode).

The Lean implementations (`implementation_validateAscii` / `_validateUnicode`)
compute, as an R/I shadow:

    result = (len(username) >= 1) and all(is_allowed(c) for c in username)

where the per-character predicate `isAllowed*` is an A-REFERENCE callee: it is
the UNCHANGED `[\w.@+-]` class membership, so this differential test leaves it as
the REAL repo callee — i.e. `re.compile(r'[\w.@+-]', flags).fullmatch(c)`.

The ORACLE is a faithful in-process replica of the POST-PATCH validator: the real
compiled regex `^[\w.@+-]+\Z` under the validator's own flags. Accept ⇔ match.

Both legs are run over every input in a corpus mixing allowed characters,
disallowed characters (space, apostrophe, non-ASCII letters), and crucially
trailing / embedded `'\n'` — the `\Z`-vs-`$` discriminator the fix turns on. The
shadow must agree with the real regex on every input, for BOTH validators.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 1109920190320 (also in
mapping.md).
"""
import re
import sys

SEED = 1109920190320
N = 120_000

# Per-validator real regexes (post-patch) and the per-char class test.
ASCII_FULL = re.compile(r'^[\w.@+-]+\Z', re.ASCII)
UNI_FULL = re.compile(r'^[\w.@+-]+\Z', 0)
ASCII_CHAR = re.compile(r'[\w.@+-]', re.ASCII)
UNI_CHAR = re.compile(r'[\w.@+-]', 0)


# --- ORACLE: the real post-patch validator (accept ⇔ regex matches) ----------
def oracle_accept(full_re, s):
    return full_re.search(s) is not None


# --- SHADOW: implementation_validate* (R/I leg) ------------------------------
# is_allowed(c) is the A-reference callee left as the REAL [\w.@+-] class test.
def is_allowed(char_re, c):
    return char_re.fullmatch(c) is not None


def shadow_accept(char_re, s):
    chars = list(s)                       # str -> List Char (mapping.md)
    if len(chars) < 1:                    # username.isEmpty -> reject
        return False
    ok = True
    for c in chars:                       # for c in username do ...
        if not is_allowed(char_re, c):
            ok = False
    return ok


def disagree(name, full_re, char_re, s):
    got = oracle_accept(full_re, s)
    want = shadow_accept(char_re, s)
    if got != want:
        return (name, s, got, want)
    return None


# --- input corpus ------------------------------------------------------------
ALLOWED_ASCII = list("abcXYZ09_.@+-")
DISALLOWED = list(" '!/\\\t") + ["\n", "\r", "É", "–", " ", "é", "أ"]
ALPHABET = ALLOWED_ASCII + DISALLOWED + ["\n"]   # extra '\n' weight


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked edges pinning the \\Z-vs-$ discriminator."""
    return [
        "",                  # empty -> reject (the `+` quantifier)
        "glenn",             # all allowed -> accept
        "GLEnN",
        "jean-marc",
        "abc\n",             # THE fix: trailing newline -> reject (\Z, not $)
        "trailingnewline\n",
        "abc\n\n",           # two trailing newlines -> reject either way
        "a\nb",              # embedded newline -> reject
        "\n",                # lone newline -> reject
        "jean marc",         # space -> reject
        "o'connell",         # apostrophe -> reject
        "user.name@host",    # punctuation in class -> accept
        "_",                 # underscore alone -> accept
        "a\r",               # trailing CR -> reject (CR not in class; \Z anyway)
        "abc\nx",            # newline not last -> reject
    ]


def _rand_str(rnd):
    length = next(rnd) % 8           # 0..7 chars
    out = []
    for _ in range(length):
        out.append(ALPHABET[next(rnd) % len(ALPHABET)])
    return "".join(out)


def main() -> int:
    checked = 0
    legs = [("ascii", ASCII_FULL, ASCII_CHAR), ("unicode", UNI_FULL, UNI_CHAR)]

    for s in _enumerate_edge():
        for name, full_re, char_re in legs:
            d = disagree(name, full_re, char_re, s)
            if d:
                print(f"DISAGREE edge {d[0]} {d[1]!r}: oracle={d[2]} shadow={d[3]}")
                print("status=fail")
                return 1
            checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        s = _rand_str(rnd)
        for name, full_re, char_re in legs:
            d = disagree(name, full_re, char_re, s)
            if d:
                print(f"DISAGREE fuzz {d[0]} {d[1]!r}: oracle={d[2]} shadow={d[3]}")
                print("status=fail")
                return 1
            checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
