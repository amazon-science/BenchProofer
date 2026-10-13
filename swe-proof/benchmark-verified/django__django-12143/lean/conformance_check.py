#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-12143.

The bundle models ONE function: the per-row primary-key selection inside
`ModelAdmin._get_edited_object_pks` (`django/contrib/admin/options.py`). That
method compiles a per-row key pattern from the formset marker (`prefix`) and the
primary-key field name (`self.model._meta.pk.name`), then returns the POST values
whose key matches:

    pk_pattern = re.compile(r'{}-\\d+-{}$'.format(re.escape(prefix), pkName))
    return [value for key, value in request.POST.items() if pk_pattern.match(key)]

Standing up the full admin/ORM stack to drive the real method is heavy and
unnecessary: the modeled value is a PURE function of the observables the method
consumes — the marker `prefix`, the pk field name `pkName`, and the ordered
`(key, value)` POST pairs. The ORACLE below is a faithful in-process replica of
the EXACT patched control flow, using the GENUINE stdlib `re` engine and the
GENUINE `re.escape` — the two UNCHANGED callees whose composite effect the Lean
`matchesRowKey` models DEEPLY (A-reference). The SHADOW is the op-for-op
transliteration of `implementation_rowKeySelection` (refinement.md).

Comparing the shadow against the real `re`-engine oracle over >=1e5 fuzzed
inputs is exactly the validation that the deep matcher model equals the real
(escaped-prefix) regex matcher. They compare as ordered lists of values.

Type bijection (mapping.md): a Python `str` (per code point) <-> Lean
`List Char`; a POST value <-> an opaque payload carried through unchanged
(modeled by a distinct string tag so multiplicity/order are observable);
`request.POST.items()` order <-> list order.

Modeled semantics under test (mapping.md):
  * `pkName` is a Python identifier ([A-Za-z_][A-Za-z0-9_]*, ASCII), hence
    regex-literal and free of `-`; matched literally by the model too;
  * the digit class is Unicode-aware: `\\d` on a py3 `str` pattern accepts the
    decimal digits of every decimal number system (Unicode general category
    Nd). The Lean `isDecimalDigit`/`digitRanges` reproduce exactly the 54 Nd
    runs (580 code points) of the engine's shipped Unicode data (unidata
    9.0.0, extracted in-container by enumerating `re.compile(r'\\d').match`);
  * end-of-key tolerance: `$` accepts the true end of the key OR a position
    just before ONE final newline; the Lean `atEnd` mirrors this.
The fuzzer deliberately includes markers laden with regex metacharacters
(`$ . * + ? ^ ( ) [ ] | \\`) — the data-loss case in the issue — plus the F2P
marker `form$`, non-Latin decimal digits and digit-like non-Nd near-misses in
the row-index position, and keys with trailing/embedded newlines.

stdlib-only. Pinned seed: 20240627 (also in mapping.md / meta.json).
"""
import random
import re
import sys

SEED = 20240627
N_CASES = 120_000


# --- ORACLE: faithful replica of the patched selection, real `re` engine -----
def oracle_select(mark, pk_name, items):
    """items: list of (key:str, value); returns list of values, in order."""
    pk_pattern = re.compile(r'{}-\d+-{}$'.format(re.escape(mark), pk_name))
    return [value for key, value in items if pk_pattern.match(key)]


# --- SHADOW: op-for-op transliteration of implementation_rowKeySelection ------

# `digitRanges` transliterated: the Nd runs (inclusive scalar-value bounds) of
# the engine's shipped Unicode data. Spelled out (NOT delegated to `re` or
# `unicodedata`) so the shadow stays independent of the oracle.
_DIGIT_RANGES = [
    (0x30, 0x39), (0x660, 0x669), (0x6F0, 0x6F9), (0x7C0, 0x7C9),
    (0x966, 0x96F), (0x9E6, 0x9EF), (0xA66, 0xA6F), (0xAE6, 0xAEF),
    (0xB66, 0xB6F), (0xBE6, 0xBEF), (0xC66, 0xC6F), (0xCE6, 0xCEF),
    (0xD66, 0xD6F), (0xDE6, 0xDEF), (0xE50, 0xE59), (0xED0, 0xED9),
    (0xF20, 0xF29), (0x1040, 0x1049), (0x1090, 0x1099), (0x17E0, 0x17E9),
    (0x1810, 0x1819), (0x1946, 0x194F), (0x19D0, 0x19D9), (0x1A80, 0x1A89),
    (0x1A90, 0x1A99), (0x1B50, 0x1B59), (0x1BB0, 0x1BB9), (0x1C40, 0x1C49),
    (0x1C50, 0x1C59), (0xA620, 0xA629), (0xA8D0, 0xA8D9), (0xA900, 0xA909),
    (0xA9D0, 0xA9D9), (0xA9F0, 0xA9F9), (0xAA50, 0xAA59), (0xABF0, 0xABF9),
    (0xFF10, 0xFF19), (0x104A0, 0x104A9), (0x11066, 0x1106F),
    (0x110F0, 0x110F9), (0x11136, 0x1113F), (0x111D0, 0x111D9),
    (0x112F0, 0x112F9), (0x11450, 0x11459), (0x114D0, 0x114D9),
    (0x11650, 0x11659), (0x116C0, 0x116C9), (0x11730, 0x11739),
    (0x118E0, 0x118E9), (0x11C50, 0x11C59), (0x16A60, 0x16A69),
    (0x16B50, 0x16B59), (0x1D7CE, 0x1D7FF), (0x1E950, 0x1E959),
]


def is_decimal_digit(ch):
    """`isDecimalDigit`: membership in one of the decimal-digit runs (any
    decimal number system, not only '0'..'9')."""
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in _DIGIT_RANGES)


def strip_prefix(p, s):
    """`stripPrefix?`: literal (char-for-char) prefix consumption -> remainder
    or None."""
    if s.startswith(p):
        return s[len(p):]
    return None


def at_end(s):
    """`atEnd`: end-of-key position — nothing left, or exactly one trailing
    newline."""
    return s == '' or s == '\n'


def matches_row_key(mark, pk_name, key):
    """`matchesRowKey`: key decomposes literally as
    mark ++ '-' ++ ds ++ '-' ++ pkName ++ tail with ds a non-empty run of
    Unicode decimal digits and tail at end-of-key (atEnd)."""
    r1 = strip_prefix(mark, key)
    if r1 is None:
        return False
    if not r1.startswith('-'):
        return False
    r2 = r1[1:]
    i = 0
    while i < len(r2) and is_decimal_digit(r2[i]):
        i += 1
    ds, rest = r2[:i], r2[i:]
    if ds == '' or not rest.startswith('-'):
        return False
    r3 = rest[1:]
    tail = strip_prefix(pk_name, r3)
    if tail is None:
        return False
    return at_end(tail)


def shadow_select(mark, pk_name, items):
    acc = []
    for key, value in items:               # for kv in items do
        if matches_row_key(mark, pk_name, key):
            acc.append(value)              # acc := acc ++ [kv.2]
    return acc


# --- fuzzing ------------------------------------------------------------------
# non-Latin decimal digits (all in Nd) exercised in the row-index position.
_UNI_DIGITS = ['٠', '٩', '۰', '०', '๐', '０',
               '９', '\U000104A0', '\U0001D7CE', '\U0001E950']
# digit-like near-misses: NOT decimal digits (superscripts, fractions,
# circled/ideographic) — must be rejected by both sides.
_UNI_NONDIGITS = ['²', '½', '⁰', '①', '〇']
_MARK_AL = (list('ab01-') + ['$', '.', '*', '+', '?', '^', '(', ')', '[', ']',
                             '|', '\\', '{', '}', '\n'])
_KEY_AL = (list('ab0123-') + ['$', '.', '*', '+', '(', ')', '[', ']', '|',
                              '\\', '\n', ' '] + _UNI_DIGITS + _UNI_NONDIGITS)
_PK = ['uuid', 'id', 'pk', 'a1', 'x_y', 'name', 'field2']


def rand_str(rng, alphabet, lo, hi):
    return ''.join(rng.choice(alphabet) for _ in range(rng.randint(lo, hi)))


def rand_case(rng):
    mark = rand_str(rng, _MARK_AL, 0, 5)
    pk_name = rng.choice(_PK)
    n = rng.randint(0, 6)
    items = []
    for j in range(n):
        # ~half the keys are constructed to plausibly match `mark`; the rest
        # are free-form. A distinct tag per pair makes order/multiplicity/value
        # observable in the compared output.
        if rng.random() < 0.5:
            if rng.random() < 0.3:
                pool = list('0123456789') + _UNI_DIGITS
                idx = ''.join(rng.choice(pool)
                              for _ in range(rng.randint(1, 3)))
            else:
                idx = str(rng.randint(0, 99))
            tail = rng.choice(['-' + pk_name, '-' + pk_name + 'x', '', '-z',
                               '-' + pk_name + '\n',
                               '-' + pk_name + '\n\n'])
            key = mark + '-' + idx + tail
        else:
            key = rand_str(rng, _KEY_AL, 0, 12)
        items.append((key, 'v%d' % j))
    return mark, pk_name, items


# Exact F2P shape (tests/admin_changelist/tests.py): marker `form$`, pk `uuid`.
F2P_CASES = [
    ('form$', 'uuid', [
        ('form$-TOTAL_FORMS', '2'),
        ('form$-INITIAL_FORMS', '2'),
        ('form$-0-uuid', 'PK0'),
        ('form$-0-load', '10'),
        ('_save', 'Save'),
    ]),
    ('form', 'uuid', [
        ('form-0-uuid', 'PK0'),
        ('form-1-uuid', 'PK1'),
        ('form-0-load', '10'),
    ]),
    # non-Latin decimal digit in the row-index position: MUST be selected.
    ('form', 'uuid', [
        ('form-١-uuid', 'PKA'),
        ('form-١٩7-uuid', 'PKB'),
        ('form-²-uuid', 'NO1'),
        ('form-3①-uuid', 'NO2'),
    ]),
    # end-of-key tolerance: one trailing newline matches; two do not.
    ('form', 'uuid', [
        ('form-1-uuid\n', 'NL1'),
        ('form-1-uuid\n\n', 'NL2'),
        ('form-1-uuid\nx', 'NL3'),
    ]),
]


def main() -> int:
    rng = random.Random(SEED)
    mism = 0
    examples = []
    checked = 0

    def compare(mark, pk_name, items):
        nonlocal mism, checked
        want = oracle_select(mark, pk_name, items)
        got = shadow_select(mark, pk_name, items)
        checked += 1
        if want != got:
            if len(examples) < 10:
                examples.append({"mark": mark, "pk": pk_name,
                                 "keys": [k for k, _ in items],
                                 "oracle": want, "shadow": got})
            return True
        return False

    for c in F2P_CASES:
        if compare(*c):
            mism += 1

    for _ in range(N_CASES):
        mark, pk_name, items = rand_case(rng)
        if compare(mark, pk_name, items):
            mism += 1

    import json
    status = "pass" if mism == 0 else "fail"
    print(json.dumps({
        "status": status, "instance": "django__django-12143",
        "seed": SEED, "checked": checked, "mismatches": mism,
        "examples": examples,
    }))
    return 0 if mism == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
