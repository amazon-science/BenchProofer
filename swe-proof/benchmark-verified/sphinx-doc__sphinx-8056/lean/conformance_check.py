#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-8056.

The bundle models ONE fragment: the field-list normalization decision inside
`NumpyDocstring._consume_fields` (sphinx/ext/napoleon/docstring.py). Its Lean
implementation (`implementation_normalizeEntries`) decides, for a grouping flag
and a list of already-read raw entries `(name, type, desc)`, the normalized
entry list:

    for (name, typ, desc) in raws:
        if splitGrouped and name:                         # CHANGED branch  [R/I]
            for piece in name.split(","):
                fields.append((piece.strip(), typ, desc))
        elif name or typ or desc:                         # unchanged keep   [R/I]
            fields.append((name, typ, desc))

This script transliterates that decision into Python (`shadow_normalize`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH `_consume_fields` decision (docstring.py:269-281 post-patch), with the
unchanged entry-reading (`_consume_field`) and section-boundary detection
abstracted away as the input list `raws` (those are unchanged bookkeeping, not
modeled). The `multiple` parameter is the grouping flag, set True by
`_parse_parameters_section` under `napoleon_use_param` (post-patch).

The model's `trim` strips exactly Python `str.strip()`'s default set — the
`str.isspace()` code points (U+0009–U+000D, U+001C–U+0020, U+0085, U+00A0,
U+1680, U+2000–U+200A, U+2028, U+2029, U+202F, U+205F, U+3000) — so
`piece.strip()` == `trim piece` on ALL inputs, including Unicode whitespace such
as NBSP; the fuzz corpus includes those characters.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 8056 (also in mapping.md).
"""
import sys

SEED = 8056
N = 120_000

# Exactly Python str.strip()'s default removal set: the str.isspace() code points.
# Mirrors Solution.lean's isBlank.
_BLANK = (
    "\t\n\x0b\x0c\r"                                # U+0009-U+000D
    "\x1c\x1d\x1e\x1f\x20"                          # U+001C-U+0020
    "\x85\xa0\u1680"                                  # NEL, NBSP, OGHAM SPACE MARK
    "\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a"
    "\u2028\u2029\u202f\u205f\u3000"
)
assert set(_BLANK) == {chr(i) for i in range(0x110000) if chr(i).isspace()}


# --- ORACLE: the post-patch _consume_fields decision ------------------------
def oracle_normalize(split_grouped: bool, raws):
    fields = []
    for (name, typ, desc) in raws:
        if split_grouped and name:                 # post-patch: multiple and _name
            for piece in name.split(","):
                fields.append((piece.strip(), typ, tuple(desc)))
        elif name or typ or desc:
            fields.append((name, typ, tuple(desc)))
    return fields


# --- shadow of implementation_normalizeEntries ------------------------------
# Mirrors Solution.lean: commaPieces == split(","), trim == strip over the domain.
def _comma_pieces(name: str):
    return name.split(",")            # commaPieces is exactly delimiter split on ','


def _trim(cs: str) -> str:
    i, j = 0, len(cs)
    while i < j and cs[i] in _BLANK:
        i += 1
    while j > i and cs[j - 1] in _BLANK:
        j -= 1
    return cs[i:j]


def shadow_normalize(split_grouped: bool, raws):
    fields = []
    for (name, typ, desc) in raws:
        if split_grouped and name != "":
            for piece in _comma_pieces(name):
                fields.append((_trim(piece), typ, tuple(desc)))
        elif name != "" or typ != "" or desc:
            fields.append((name, typ, tuple(desc)))
    return fields


def disagree(sg, raws):
    got = oracle_normalize(sg, raws)
    want = shadow_normalize(sg, raws)
    if got != want:
        return (sg, raws, got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


# name alphabet: identifiers, commas, blanks (ASCII + Unicode whitespace,
# NBSP included — the str.strip() faithfulness case), and arg sigils.
_NAME_ALPHA = ['a', 'b', 'x', '1', '2', '_', '*', ',', ' ', '\t', '\n', '\r',
               '\x0b', '\x0c', '\x1c', '\x85', '\xa0', '\u1680', '\u2003',
               '\u2028', '\u202f', '\u3000']
_TYPE_ALPHA = ['', 'int', 'str', 'array_like', 'array_like, optional']
_DESC_ALPHA = [[], ["d"], ["line1", "line2"]]


def _edge_cases():
    out = []
    raw_sets = [
        [],
        [("", "", [])],
        [("x1, x2", "array_like", ["Input arrays"])],
        [("x1, x2", "array_like, optional", ["Input arrays"])],
        [("arg1", "str", ["desc"])],
        [("a,b,c", "int", [])],
        [("a,", "int", [])],
        [(",a", "int", [])],
        [(" a , b ", "T", ["d"])],
        [("*args, **kwargs", "", ["Variable length"])],
        [("", "onlytype", [])],
        [("", "", ["onlydesc"])],
        [("a, b", "t", ["d"]), ("c", "u", []), ("", "", [])],
        [(",", "t", [])],
        [(",,", "t", [])],
        [("x1,\xa0x2", "array_like", ["NBSP after comma"])],
        [(" a　,\x85b ", "T", ["Unicode blanks"])],
    ]
    for sg in (False, True):
        for raws in raw_sets:
            out.append((sg, raws))
    return out


def _rand_name(rnd):
    ln = next(rnd) % 8
    return "".join(_NAME_ALPHA[next(rnd) % len(_NAME_ALPHA)] for _ in range(ln))


def main() -> int:
    checked = 0

    for sg, raws in _edge_cases():
        d = disagree(sg, raws)
        if d:
            print(f"DISAGREE edge sg={d[0]} raws={d[1]!r}: oracle={d[2]} shadow={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        sg = (next(rnd) % 2 == 0)
        nentries = next(rnd) % 4
        raws = []
        for _ in range(nentries):
            name = _rand_name(rnd)
            typ = _TYPE_ALPHA[next(rnd) % len(_TYPE_ALPHA)]
            desc = _DESC_ALPHA[next(rnd) % len(_DESC_ALPHA)]
            raws.append((name, typ, desc))
        d = disagree(sg, raws)
        if d:
            print(f"DISAGREE fuzz sg={d[0]} raws={d[1]!r}: oracle={d[2]} shadow={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
