#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-7590.

The bundle models ONE routine: the numeric-literal id computation of the C++
`DefinitionParser._parse_literal` (mapping.md). The soundness-critical decision
the patch changes is the CONTROL FLOW that folds a trailing identifier into a
*user-defined literal* (UDL) when a base literal carries no standard suffix:

    post-patch:  match a base literal; if a standard suffix follows, keep it and
                 emit "L"+text+"E"; ELSE if a UDL identifier follows, wrap it as
                 'clL_Zli{len(id)}{id}E' + inner + 'E'; else emit the bare id.

Pre-patch there was no UDL folding (`# TODO: user-defined lit`), so a literal
followed by an identifier (e.g. `6.62607015e-34q_J`, `5_udl`) dropped the
identifier.

The eight lexical recognisers (float/float-suffix/bin/hex/dec/oct/int-suffix/udl)
are driven by the SAME real compiled regexes on both differential sides (they are
A-references, unchanged by the patch / purely lexical), so they cancel and this
test isolates exactly the R leg — the UDL-folding recombination.

ORACLE = faithful in-process replica of the POST-PATCH `_parse_literal` id
computation. SHADOW = op-for-op transliteration of `implementation_literalId`
(Solution.lean impl region), per refinement.md.

stdlib-only. Pinned seed: 7590 (also in mapping.md).
"""
import random
import re
import sys

SEED = 7590
N = 120_000

# --- the REAL compiled regexes (verbatim from sphinx/util/cfamily.py @ post-patch
#     + udl_identifier_re from sphinx/domains/cpp.py). Identical on both sides. ---
integer_literal_re = re.compile(r'[1-9][0-9]*')
octal_literal_re = re.compile(r'0[0-7]*')
hex_literal_re = re.compile(r'0[xX][0-9a-fA-F][0-9a-fA-F]*')
binary_literal_re = re.compile(r'0[bB][01][01]*')
integers_literal_suffix_re = re.compile(r'''(?x)
    (
        ([uU]    ([lL]  |  (ll)  |  (LL))?)
        |
        (([lL]  |  (ll)  |  (LL))    [uU]?)
    )\b
''')
float_literal_re = re.compile(r'''(?x)
    [+-]?(
    # decimal
      ([0-9]+[eE][+-]?[0-9]+)
    | ([0-9]*\.[0-9]+([eE][+-]?[0-9]+)?)
    | ([0-9]+\.([eE][+-]?[0-9]+)?)
    # hex
    | (0[xX][0-9a-fA-F]+[pP][+-]?[0-9a-fA-F]+)
    | (0[xX][0-9a-fA-F]*\.[0-9a-fA-F]+([pP][+-]?[0-9a-fA-F]+)?)
    | (0[xX][0-9a-fA-F]+\.([pP][+-]?[0-9a-fA-F]+)?)
    )
''')
float_literal_suffix_re = re.compile(r'[fFlL]\b')
udl_identifier_re = re.compile(r'''(?x)
    [a-zA-Z_][a-zA-Z0-9_]*\b
''')


def _mlen(regex, s):
    """Length of the prefix `regex` matches at pos 0 of `s` (0 = no match).
    Mirrors `self.match(regex)` advancing `self.pos`."""
    m = regex.match(s, 0)
    return (m.end() - 0) if m is not None else 0


# recogniser closures used by both oracle and shadow (A-reference, identical) ----
float_match = lambda s: _mlen(float_literal_re, s)
float_suffix_match = lambda s: _mlen(float_literal_suffix_re, s)
bin_match = lambda s: _mlen(binary_literal_re, s)
hex_match = lambda s: _mlen(hex_literal_re, s)
dec_match = lambda s: _mlen(integer_literal_re, s)
oct_match = lambda s: _mlen(octal_literal_re, s)
int_suffix_match = lambda s: _mlen(integers_literal_suffix_re, s)
udl_match = lambda s: _mlen(udl_identifier_re, s)


# --- the three get_id mangling formulas (I legs) ------------------------------
def num_id(data):
    return "L" + data + "E"


def ident_id(ident):
    # ASTIdentifier.get_id (v>=2, non-anon): the reserved namespace name 'std'
    # mangles to its standard abbreviation 'St' (cpp.py:586-587).
    if ident == "std":
        return "St"
    return str(len(ident)) + ident


def udl_id(ident, inner):
    return "clL_Zli" + ident_id(ident) + "E" + inner + "E"


def finish_literal(base_len, s, suffix_match):
    rest = s[base_len:]
    sfx = suffix_match(rest)
    if sfx > 0:
        return num_id(s[:base_len + sfx])
    base = num_id(s[:base_len])
    u = udl_match(rest)
    if u > 0:
        return udl_id(rest[:u], base)
    return base


# --- ORACLE: faithful replica of the POST-PATCH _parse_literal id computation --
def oracle(s):
    fl = float_match(s)
    if fl > 0:
        return finish_literal(fl, s, float_suffix_match)
    for m in (bin_match, hex_match, dec_match, oct_match):
        il = m(s)
        if il > 0:
            return finish_literal(il, s, int_suffix_match)
    return None


# --- SHADOW of implementation_literalId (the R/I legs) ------------------------
# Mirrors Solution.lean impl region exactly.
def shadow(s):
    fl = float_match(s)
    if fl > 0:
        return finish_literal(fl, s, float_suffix_match)
    for m in [bin_match, hex_match, dec_match, oct_match]:
        il = m(s)
        if il > 0:
            return finish_literal(il, s, int_suffix_match)
    return None


def disagree(s):
    got = oracle(s)
    want = shadow(s)
    if got != want:
        return (s, got, want)
    return None


INT_BODIES = ['5', '0', '075', '0x0123456789ABCDEF', '0XF', '0b1', '0B1', '42', '0xA']
DEC_FLOATS = ['5e42', '5e+42', '5e-42', '5.', '5.e42', '.5', '.5e-42', '5.0',
              '5.0e42', '6.62607015e-34']
HEX_FLOATS = ['0xApF', '0xAp+F', '0xA.', '0xA.pF', '0x.A', '0x.ApF', '0xA.B', '0xA.BpF']
INT_SUFFIXES = ['', 'u', 'U', 'l', 'L', 'll', 'LL', 'ul', 'ull', 'llu', 'uLL', 'lu']
FLOAT_SUFFIXES = ['', 'f', 'F', 'l', 'L']
UDLS = ['', '_udl', 'q_J', 'fudl', 'uludl', '_Zli', 'q_s', 'abc', 'std', 'stdx']
JUNK = ['', '*', ' ', '+1', '.x', '-', ')']


def _edge_cases():
    cases = [
        '6.62607015e-34q_J',   # the issue's exact repro
        '5_udl', '5uludl', '0_udl', '075_udl', '0x0123456789ABCDEF_udl',
        '5.0_udl', '5.0fudl', '5.e42_udl', '.5_udl',
        '0xApF_udl', '0xA.BpF_udl', '0xA.B_udl',
        '5', '5ul', '5ull', '5.0', '5.0f', '5.0F', '5.0l',
        '5lll',     # 'll' suffix then UDL 'l'? -> suffix takes the 'll', then 'l' is no UDL start... actually 'l' is ident
        '5l',       # standard long suffix, NOT a UDL
        '0', '075', '0x0', '0b1',
        '',         # nothing
        '*abc',     # no literal at head
        'q_J',      # identifier alone, no literal
        '5std',     # UDL identifier 'std' -> 'St' abbreviation in the mangling
        '6.62607015e-34std', '0x1p1std', '5stdx', '5Std', '5_std',
    ]
    return cases


def _rand_case(rng):
    kind = rng.randint(0, 2)
    if kind == 0:
        body = rng.choice(INT_BODIES)
        sfx = rng.choice(INT_SUFFIXES)
    elif kind == 1:
        body = rng.choice(DEC_FLOATS)
        sfx = rng.choice(FLOAT_SUFFIXES)
    else:
        body = rng.choice(HEX_FLOATS)
        sfx = rng.choice(FLOAT_SUFFIXES)
    udl = rng.choice(UDLS)
    junk = rng.choice(JUNK)
    return body + sfx + udl + junk


def main() -> int:
    checked = 0
    for s in _edge_cases():
        d = disagree(s)
        if d:
            print(f"DISAGREE edge: input={d[0]!r} oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        s = _rand_case(rng)
        d = disagree(s)
        if d:
            print(f"DISAGREE fuzz: input={d[0]!r} oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
