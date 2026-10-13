#!/usr/bin/env python3
r"""G-CONF for django__django-13512.

We compare the R/I Python shadow of `implementation_jsonEncodeString` (the Lean
impl, transliterated op-for-op per refinement.md) against the REAL post-patch
JSON string-leaf serializer, over >=1e5 fuzzed text values. Zero disagreements
=> exit 0.

Modeled object (mapping.md / refinement.md): the JSON serializer's string-leaf
renderer -- the function turning a text value `s` into its quoted JSON string
literal. The gold patch flips `json.dumps(value, cls=...)` ->
`json.dumps(value, ensure_ascii=False, cls=...)` at both changed sites; the only
behavioral delta is that string leaves render every non-ASCII character literally
(was `\uXXXX`). The whole-document structural walk is flag-independent and is the
unchanged json.dumps machinery (not modeled here).

  * Oracle  = the REAL stdlib serializer for a string leaf, i.e.
              json.dumps(s, ensure_ascii=False) (default encoder -- the F2P tests
              use the default encoder; `cls=field.encoder` is None there).
  * Shadow  = the op-for-op transliteration of implementation_jsonEncodeString:
              '"' + ''.join(escapeChar(c) for c in s) + '"', with escapeChar the
              Python shadow of the Lean `escapeChar` def.

Type bijection (mapping.md): s:List Char <-> s:str (per code point, astral chars
are one Char / one code point); result:List Char <-> result:str.
stdlib-only. Pinned fuzz seed = 13512.
"""
import json
import random
import sys

SEED = 13512
N = 200_000


def escape_char(c: str) -> str:
    """Python shadow of the Lean `escapeChar` (the ensure_ascii=False table)."""
    n = ord(c)
    if n == 0x22:
        return '\\"'
    if n == 0x5c:
        return '\\\\'
    if n == 0x08:
        return '\\b'
    if n == 0x09:
        return '\\t'
    if n == 0x0a:
        return '\\n'
    if n == 0x0c:
        return '\\f'
    if n == 0x0d:
        return '\\r'
    if n < 0x20:
        return '\\u00' + format(n // 16, 'x') + format(n % 16, 'x')
    return c


def shadow(s: str) -> str:
    return '"' + ''.join(escape_char(c) for c in s) + '"'


def oracle(s: str) -> str:
    # The REAL post-patch string-leaf rendering.
    return json.dumps(s, ensure_ascii=False)


# Alphabet spanning every escape regime + the flag-sensitive ranges.
_ALPHABET = (
    [chr(i) for i in range(0x00, 0x20)]              # all C0 controls
    + list(' !"#$%&\'()*+,-./0123456789:;<=>?@'
           'ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`'
           'abcdefghijklmnopqrstuvwxyz{|}~')          # printable ASCII (incl. " \ /)
    + [chr(i) for i in (0x7f, 0x80, 0xa0, 0xe9, 0xf1, 0x141)]  # DEL, C1, Latin-1, Latin-ext
    + ['中', '你', '好', '世', '界', 'ż', 'ń']         # CJK / Latin diacritics
    + ['\U0001F600', '\U0001F431', '\U0001F4A9']      # astral / emoji
)


def main() -> int:
    rng = random.Random(SEED)
    mism = 0
    examples = []
    # boundary cases first
    boundary = ['', 'a', '中', '😀🐱', '你好，世界',
                'he said "hi"\n\tand \\ done', '\x00\x01\x1f\x7f', '/slash/',
                # directed escape-regime boundaries
                '\x07', '\x08', '\x09', '\x0a', '\x0b', '\x0c', '\x0d', '\x1f',
                '\x20', '"', '\\', '\x7f', '\x80', '\xa0', 'é', 'ń',
                '￿', '\U00010000', '\U0001f600', '\U0010ffff']
    samples = boundary + [
        ''.join(rng.choice(_ALPHABET) for _ in range(rng.randint(0, 40)))
        for _ in range(N)
    ]
    for s in samples:
        if shadow(s) != oracle(s):
            mism += 1
            if len(examples) < 8:
                examples.append({"input": s, "shadow": shadow(s),
                                 "oracle": oracle(s)})
    status = "pass" if mism == 0 else "fail"
    print(json.dumps({
        "status": status,
        "instance": "django__django-13512",
        "checked": len(samples),
        "mismatches": mism,
        "examples": examples,
        "seed": SEED,
    }))
    return 0 if mism == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
