#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for scikit-learn__scikit-learn-15100.

The bundle models `strip_accents_unicode(s)`: remove accent marks from a text
string. Post-patch rule (the gold edit):

    try:
        s.encode("ASCII", errors="strict")     # pure ASCII -> no accents
        return s
    except UnicodeEncodeError:
        normalized = unicodedata.normalize('NFKD', s)
        return ''.join(c for c in normalized if not unicodedata.combining(c))

The two callees the function reads but does NOT change — `unicodedata.normalize`
and `unicodedata.combining` — are A-references: the SHADOW of
`implementation_stripAccents` uses the REAL routines for them (so the model is
validated against the actual library behavior), and the only R refinement is the
ASCII-encodability guard, modeled as "every code point < 128".

ORACLE  = faithful in-process replica of the POST-PATCH `strip_accents_unicode`
          (the `encode("ASCII", strict)` / `UnicodeEncodeError` mechanism).
SHADOW  = op-for-op transliteration of `implementation_stripAccents`
          (`s.all isAscii` with isAscii = ord(c) < 128, then the same
          decompose-and-filter, using the real `unicodedata` callees).

A zero-disagreement run confirms the R leg (ASCII guard ⇔ all code points < 128)
and the A-reference modeling against the real callees.

stdlib-only. Pinned seed: 15100 (also in mapping.md).
"""
import random
import sys
import unicodedata

SEED = 15100
N = 120_000


# --- ORACLE: faithful in-process replica of POST-PATCH strip_accents_unicode --
def oracle(s):
    try:
        s.encode("ASCII", errors="strict")
        return s
    except UnicodeEncodeError:
        normalized = unicodedata.normalize("NFKD", s)
        return "".join(c for c in normalized if not unicodedata.combining(c))


# --- SHADOW of implementation_stripAccents (R + A-reference legs) -------------
# isAscii = (ord(c) < 128); canonDecompose / isCombiningMark = real callees.
def is_ascii(s):
    return all(ord(c) < 128 for c in s)


def shadow(s):
    if is_ascii(s):
        return s
    normalized = unicodedata.normalize("NFKD", s)
    return "".join(c for c in normalized if not (unicodedata.combining(c) != 0))


def disagree(s):
    got = oracle(s)
    want = shadow(s)
    if got != want:
        return (s, got, want)
    return None


def _edge_cases():
    cases = []
    # F2P inputs
    cases += [chr(241)]                       # ñ pre-composed
    cases += [chr(110) + chr(771)]            # n + COMBINING TILDE (decomposed)
    cases += ["ö"]                      # o + diaeresis (decomposed)
    cases += ["̀́̂̃"]     # bare combining marks
    cases += ["ȫ"]                # multiple marks on one char
    # existing test material
    cases += ["\xe0\xe9\xee\xf5\xfb", "this is a test"]
    # boundary / structural
    cases += ["", "a", "ASCII only 123", "\x7f", "\x80", "ÿ"]
    cases += ["café", "café", "Å", "Å"]
    cases += ["mixed café and ASCII", "\U0001F600", "naïve", "naïve"]
    return cases


def _rand_string(rng):
    n = rng.randint(0, 12)
    out = []
    for _ in range(n):
        kind = rng.random()
        if kind < 0.35:
            out.append(chr(rng.randint(0x20, 0x7E)))            # ASCII printable
        elif kind < 0.55:
            out.append(chr(rng.randint(0x00C0, 0x017F)))        # Latin accented
        elif kind < 0.75:
            out.append(chr(rng.randint(0x0300, 0x036F)))        # combining marks
        else:
            cp = rng.randint(0x00A0, 0x2FFF)
            out.append(chr(cp))
    return "".join(out)


def main() -> int:
    checked = 0
    for s in _edge_cases():
        d = disagree(s)
        if d:
            print(f"DISAGREE edge: s={d[0]!r} oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        s = _rand_string(rng)
        d = disagree(s)
        if d:
            print(f"DISAGREE rand: s={d[0]!r} oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
