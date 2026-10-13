#!/usr/bin/env python3
r"""G-AX executable soundness check for django__django-13512.

Executes the REAL stdlib callee (`json.dumps(s, ensure_ascii=False)`) on
boundary inputs and randomized fuzzing, and asserts that the deep model
`json_escaped_seq` (the Lean `jsonChar`/`jsonEscapedSeq` fold, transliterated)
reproduces it EXACTLY, including the surrounding string-literal quotes.

The single kind-A check (A-reference; there are NO consumed axioms):

  (A-reference) the deep model `'"' + ''.join(json_char(c) for c in s) + '"'`
      == the real `json.dumps(s, ensure_ascii=False)`. The changed rendering
      operation is modeled DEEPLY (mapping.md §3.1), not behind a consumed
      axiom; G-AX validates that deep model against the real callee:

        0x22 (")            -> \"
        0x5c (\)            -> \\
        0x08,0x09,0x0a,0x0c,0x0d -> \b \t \n \f \r
        v < 0x20 otherwise  -> \u00xx  (lowercase, two leading zeros)
        v >= 0x20 otherwise -> the code point itself (incl. ALL v >= 0x80)

The last clause — code points >= U+0080 pass through literally — is the whole
behaviour at issue (the patch's `ensure_ascii=False`).

We also sanity-check that the DEFAULT serializer (`ensure_ascii=True`, the
pre-patch behaviour) DIFFERS from the model on non-ASCII, so the model is
pinned to the patched behaviour and not vacuously true.

Imports nothing repo-specific: `json` is the Python standard library — the same
module the gold patch calls. Exit 0 iff every obligation holds.
"""
import json
import random
import sys

# --- model.py reference encodings (kept in lock-step with Solution.lean) -----

_SHORT = {
    0x22: '\\"',
    0x5c: '\\\\',
    0x08: '\\b',
    0x09: '\\t',
    0x0a: '\\n',
    0x0c: '\\f',
    0x0d: '\\r',
}


def json_char(c):
    """Reference of Solution.lean `jsonChar` for one character `c` (str of
    length 1): the JSON text of that code point inside a string literal under
    ensure_ascii=False."""
    v = ord(c)
    if v in _SHORT:
        return _SHORT[v]
    if v < 0x20:
        return '\\u%04x' % v          # \u00xx, lowercase, two leading zeros
    return c                          # else [c] — literal pass-through


def json_escaped_seq(s):
    """Reference of Solution.lean `jsonEscapedSeq`: concatenate per-code-point
    renderings (no quotes)."""
    return "".join(json_char(c) for c in s)


def model_serialize(s):
    """Solution.lean `serializeStringValue`: quote + body + quote."""
    return '"' + json_escaped_seq(s) + '"'


# --- the checks --------------------------------------------------------------

def check_reference(s):
    """Assert the deep model == the REAL json.dumps(s, ensure_ascii=False)."""
    observed = json.dumps(s, ensure_ascii=False)      # real callee (patched)
    expected = model_serialize(s)                     # deep model
    assert observed == expected, (
        "json_escaped_seq deep model unsound on %r: json.dumps(...,"
        " ensure_ascii=False) gave %r, deep model gives %r"
        % (s, observed, expected))


def main():
    specials = ['"', '\\', '/', '\b', '\t', '\n', '\f', '\r',
                '\x00', '\x01', '\x1f', '\x7f', '\x80', '\xa0']
    # the ASCII/non-ASCII boundary, astral plane, and the issue's own examples
    nonascii = ['中', '国', '你', '好', '，', '世',
                '界', '\U0001f600', '\U0001f431', 'jaźń',
                'é', '•', '퟿', '']
    ordinary = list("aZ0 ;#x39271{}[]:,") + ['~', '`', '!', '@']

    boundary = [""]
    boundary += specials
    boundary += nonascii
    boundary += [c + c for c in specials + nonascii]
    boundary += [
        "你好 世界",
        "你好，世界",
        "😀🐱",
        '["你好，世界", "jaźń"]',     # already-formatted text, still a str leaf
        '{"a": "你好 世界"}',
        "Joe's \"quoted\" path\\back",
        "line\nbreak\ttab",
        "mix 中a国b😀c",
        "".join(specials),
        "".join(nonascii),
        # full sweep of control code points 0x00..0x1f
        "".join(chr(i) for i in range(0x20)),
    ]
    for s in boundary:
        check_reference(s)

    # --- randomized fuzz ----------------------------------------------------
    rng = random.Random(13512)
    alphabet = specials + nonascii + ordinary
    # extra raw code points spanning the whole BMP + astral
    pool = list(range(0x00, 0x80)) + [0x7f, 0x80, 0xa0, 0x2022,
                                      0x4e2d, 0x4f60, 0xff0c, 0xd7ff,
                                      0xe000, 0xfffd, 0x10000, 0x1f600,
                                      0x10ffff]
    for _ in range(20000):
        n = rng.randint(0, 24)
        chars = []
        for _ in range(n):
            if rng.random() < 0.5:
                chars.append(rng.choice(alphabet))
            else:
                chars.append(chr(rng.choice(pool)))
        check_reference("".join(chars))

    # --- non-vacuity: the model is pinned to the PATCHED behaviour, and the
    #     pre-patch default (ensure_ascii=True) DIFFERS on non-ASCII. ---------
    diverged = False
    for s in nonascii:
        if json.dumps(s) != model_serialize(s):       # default ensure_ascii=True
            diverged = True
            break
    assert diverged, (
        "model would also match ensure_ascii=True — it does not discriminate "
        "the patched behaviour")
    # and on pure-ASCII the two modes agree (sanity)
    for s in ["a", "foo", "{}", '"x\\y', "\t\n"]:
        assert json.dumps(s) == json.dumps(s, ensure_ascii=False) == model_serialize(s), (
            "ASCII disagreement on %r" % s)

    print("G-AX OK: json_escaped_seq deep model (== json.dumps(., "
          "ensure_ascii=False)) sound on %d boundary + 20000 fuzz inputs; "
          "diverges from ensure_ascii=True on non-ASCII (non-vacuous)."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
