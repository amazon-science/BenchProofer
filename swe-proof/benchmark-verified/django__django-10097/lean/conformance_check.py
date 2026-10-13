#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-10097.

The bundle models ONE thing: the acceptance predicate of the credentials
(userinfo) group of `URLValidator.regex`, which the gold patch rewrites from
`\\S+(?::\\S*)?` to `[^\\s:@/]+(?::[^\\s:@/]*)?` (mapping.md).

* ORACLE — the POST-PATCH behaviour: `re.fullmatch` of the gold inner group
  against the credentials segment. This is the real repo semantics of the edited
  sub-pattern (the `regex` construction in `django/core/validators.py`), driven
  directly with Python's own `re` engine — no re-implementation.
* SHADOW — the op-for-op transliteration of `implementation_urlUserinfoValid`
  (Solution.lean impl region), per refinement.md (rows 1–6).

We diff SHADOW vs ORACLE over an edge set (incl. the F2P invalid-URL userinfo
segments) plus >=10^5 fuzzed segments over an alphabet that stresses the reserved
delimiters and whitespace. Exit 0 iff zero disagreements.

stdlib-only. Pinned seed: 10097 (also in mapping.md).
"""
import random
import re
import sys

SEED = 10097
N = 150000

# Gold POST-PATCH inner group (the credentials segment, `@` excluded).
GOLD_USERINFO = re.compile(r'[^\s:@/]+(?::[^\s:@/]*)?')


def oracle(s: str) -> bool:
    """Post-patch semantics: does the whole segment match the gold inner group?"""
    return re.fullmatch(GOLD_USERINFO, s) is not None


# --- SHADOW of implementation_urlUserinfoValid (the R/I legs) -----------------
# isUserinfoWhitespace mirrors the Lean spec's explicit 29-code-point class:
# ASCII \t \n \v \f \r space, U+001C-1F, U+0085, U+00A0, U+1680, U+2000-200A,
# U+2028, U+2029, U+202F, U+205F, U+3000. This must be Python re's Unicode \s
# exactly; the assertion below checks the equivalence against the real engine
# over the full code-point space, so the shadow cannot silently drift.
_WS_CODEPOINTS = (
    list(range(0x9, 0xE)) + [0x20] + list(range(0x1C, 0x20)) +
    [0x85, 0xA0, 0x1680] + list(range(0x2000, 0x200B)) +
    [0x2028, 0x2029, 0x202F, 0x205F, 0x3000]
)
_WS = set(chr(n) for n in _WS_CODEPOINTS)

# Lean-class ↔ Python-\s equivalence over every code point.
_S_RE = re.compile(r"\s")
for _n in range(0x110000):
    _c = chr(_n)
    if (_S_RE.match(_c) is not None) != (_c in _WS):
        print("WS CLASS MISMATCH at U+%04X" % _n)
        print("status=fail")
        sys.exit(1)


def is_userinfo_char(c: str) -> bool:
    # isUserinfoChar: !isUserinfoWhitespace && != ':' && != '@' && != '/'
    return (c not in _WS) and c != ':' and c != '@' and c != '/'


def shadow(s: str) -> bool:
    if len(s) == 0:               # s.isEmpty
        return False
    if s[0] == ':':               # s.head? == some ':'
        return False
    if not (s.count(':') <= 1):   # Nat.ble (s.count ':') 1
        return False
    if not all(is_userinfo_char(c) or c == ':' for c in s):
        return False
    return True


def disagree(s):
    got, want = oracle(s), shadow(s)
    if got != want:
        return (s, got, want)
    return None


def _edge_cases():
    return [
        "",              # empty -> reject
        "foo",           # user only -> accept
        "foo:bar",       # user:pass -> accept
        "foo:",          # empty password -> accept
        ":pass",         # leading colon -> reject
        ":",             # only colon -> reject
        "foo:bar:baz",   # two colons -> reject  (F2P: foo:bar:baz@...)
        "foo/bar",       # slash -> reject        (F2P: foo/bar@...)
        "foo@bar",       # at-sign -> reject       (F2P: foo@bar@...)
        "foo:bar@baz",   # at-sign in pass -> reject (F2P: foo:bar@baz@...)
        "foo:bar/baz",   # slash in pass -> reject   (F2P: foo:bar/baz@...)
        "foo bar",       # space -> reject
        "foo\tbar",      # tab -> reject
        "foo\fbar",      # form feed (\s but not Lean isWhitespace) -> reject
        "foo\vbar",      # vertical tab (\s but not Lean isWhitespace) -> reject
        "a",             # single admissible char -> accept
        "a:",            # single char user, empty pass -> accept
        "%40",           # percent-encoded, admissible -> accept
        "-.~_!$&'()*+,;=%40",  # from valid_urls.txt userinfo -> accept
        "é世",  # non-whitespace Unicode (é, 世) -> accept
    ] + [
        # every Python-\s code point, alone and embedded -> reject
        w for n in _WS_CODEPOINTS for w in (chr(n), "a" + chr(n) + "b")
    ] + [
        # non-\s Unicode look-alikes near the class boundaries -> accept
        "a​b",      # ZERO WIDTH SPACE (not \s)
        "a᠎b",      # MONGOLIAN VOWEL SEPARATOR (not \s in Python 3)
        "a⁠b",      # WORD JOINER (not \s)
        "a﻿b",      # ZERO WIDTH NO-BREAK SPACE (not \s)
    ]


def main() -> int:
    checked = 0
    for s in _edge_cases():
        d = disagree(s)
        if d:
            print("DISAGREE edge: seg=%r oracle=%s shadow=%s" % (d[0], d[1], d[2]))
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    # Alphabet that stresses the reserved delimiters and whitespace — ASCII AND
    # the full Unicode \s class — plus admissible chars incl. non-\s Unicode.
    alphabet = (list("abcXYZ019-._~%") + [":", "@", "/"]
                + [chr(n) for n in _WS_CODEPOINTS]
                + ["é", "世", "​", "⁠", "﻿", "᠎"])
    for _ in range(N):
        n = rng.randint(0, 8)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        d = disagree(s)
        if d:
            print("DISAGREE fuzz: seg=%r oracle=%s shadow=%s" % (d[0], d[1], d[2]))
            print("status=fail")
            return 1
        checked += 1

    print("status=pass checked=%s" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
