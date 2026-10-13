#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-7590.

The bundle has NO consumed axioms; it has A-references — deep models in
`Solution.lean`'s `pure` region that must equal their real callees:

  (A-reference, A2) `matchTypeTag`   == `re.match(float_literal_suffix_re, rest)`
  (A-reference, A3) `matchSuffixName`== `re.match(udl_identifier_re,     rest)`
  (A-reference, A4) `numberLitId`    == `ASTNumberLiteral.get_id`  ("L%sE")
  (A-reference, A5) `identId`        == `ASTIdentifier.get_id` (v>=2, ordinary)
  (I,          A6) `suffixedLitId`   == `ASTUserDefinedLiteral.get_id`
                                        ('clL_Zli{}E{}E'.format(...))

Strategy: this gate runs at base_commit (the gold patch is NOT applied), so the
NEW regexes / class added by the patch do not exist in-tree. We therefore
reproduce the real callees' definitions **verbatim** from the gold patch
(provenance: mapping.md §3, patch.diff), build the real-callee reference with
the standard-library `re` engine and the verbatim id-mangling formulas, and
differential-test our Lean deep models (re-encoded here, mirroring the Lean
`def`s line for line) against that reference over the FAIL_TO_PASS matrix plus
randomized fuzz. The subtle, model-prone piece — the `\b` word-boundary logic
that distinguishes a type suffix from a UDL identifier — is checked against the
actual regex engine, not against another hand reproduction.

stdlib-only (`re`, `random`, `sys`). Exit 0 iff every obligation holds.
"""
import re
import random
import sys

# --- REAL callees, reproduced verbatim from the gold patch -------------------
# float_literal_suffix_re : sphinx/util/cfamily.py (NEW, patch.diff)
FLOAT_SUFFIX_RE = re.compile(r'[fFlL]\b')
# udl_identifier_re : sphinx/domains/cpp.py (NEW, patch.diff)
UDL_IDENT_RE = re.compile(r'''(?x)
    [a-zA-Z_][a-zA-Z0-9_]*\b   # note, no word boundary in the beginning
''')
# float_literal_re : sphinx/util/cfamily.py:44 (UNCHANGED) -- used to derive the
# (floatText, rest) split that the model takes as input.
FLOAT_RE = re.compile(r'''(?x)
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


def real_number_lit_id(text):                       # ASTNumberLiteral.get_id
    return "L%sE" % text


def real_ident_id(ident):                           # ASTIdentifier.get_id, v>=2
    # ordinary-name case only (a UDL suffix is never anon / never '~').
    if ident == "std":
        return "St"
    return str(len(ident)) + ident


def real_udl_id(lit_text, ident):                   # ASTUserDefinedLiteral.get_id
    return 'clL_Zli{}E{}E'.format(real_ident_id(ident), real_number_lit_id(lit_text))


def real_parsed_float_id(float_text, rest):
    """The id the real post-patch float branch produces, via the real regexes
    and the real get_id formulas."""
    m = FLOAT_SUFFIX_RE.match(rest)
    if m and m.start() == 0:
        return real_number_lit_id(float_text + m.group(0))
    m = UDL_IDENT_RE.match(rest)
    if m and m.start() == 0:
        return real_udl_id(float_text, m.group(0))
    return real_number_lit_id(float_text)


# --- LEAN deep models, re-encoded mirroring Solution.lean's `pure` region ----

def _is_ascii_alpha(c):
    # mirrors Lean Char.isAlpha (ASCII-only: isUpper || isLower)
    return ('a' <= c <= 'z') or ('A' <= c <= 'Z')


def _is_ascii_digit(c):
    return '0' <= c <= '9'


def is_word_char(c):
    return _is_ascii_alpha(c) or _is_ascii_digit(c) or c == '_'


def is_ident_start(c):
    return _is_ascii_alpha(c) or c == '_'


def is_type_tag_char(c):
    return c in ('f', 'F', 'l', 'L')


def model_match_type_tag(rest):
    if not rest:
        return None
    c, cs = rest[0], rest[1:]
    if is_type_tag_char(c):
        if not cs:
            return c
        return None if is_word_char(cs[0]) else c
    return None


def model_match_suffix_name(rest):
    if not rest:
        return None
    c, cs = rest[0], rest[1:]
    if is_ident_start(c):
        run = c
        for d in cs:
            if is_word_char(d):
                run += d
            else:
                break
        return run
    return None


def model_number_lit_id(text):
    return "L" + text + "E"


def model_ident_id(ident):
    if ident == "std":
        return "St"
    return str(len(ident)) + ident


def model_suffixed_lit_id(lit_text, ident):
    return "clL_Zli" + model_ident_id(ident) + "E" + model_number_lit_id(lit_text) + "E"


def model_parsed_float_id(float_text, rest):
    tag = model_match_type_tag(rest)
    if tag is not None:
        return model_number_lit_id(float_text + tag)
    name = model_match_suffix_name(rest)
    if name is not None:
        return model_suffixed_lit_id(float_text, name)
    return model_number_lit_id(float_text)


# --- differential checks -----------------------------------------------------

def check_suffix_regex(rest):
    """matchTypeTag model == re.match(float_literal_suffix_re) presence/char."""
    m = FLOAT_SUFFIX_RE.match(rest)
    real = m.group(0) if (m and m.start() == 0) else None
    model = model_match_type_tag(rest)
    assert model == real, (
        "matchTypeTag unsound on %r: real float_literal_suffix_re -> %r, "
        "model -> %r" % (rest, real, model))


def check_udl_regex(rest):
    """matchSuffixName model == re.match(udl_identifier_re) consumed text."""
    m = UDL_IDENT_RE.match(rest)
    real = m.group(0) if (m and m.start() == 0) else None
    model = model_match_suffix_name(rest)
    assert model == real, (
        "matchSuffixName unsound on %r: real udl_identifier_re -> %r, "
        "model -> %r" % (rest, real, model))


def check_full_id(float_text, rest):
    """parsedFloatId model == real (regex + get_id formulas) composite."""
    real = real_parsed_float_id(float_text, rest)
    model = model_parsed_float_id(float_text, rest)
    assert model == real, (
        "parsedFloatId unsound on (%r,%r): real -> %r, model -> %r"
        % (float_text, rest, real, model))


def check_float_split(token):
    """The (floatText, rest) input contract: when float_literal_re matches a
    prefix, floatText = matched prefix and rest = remainder. (Sanity: the model
    consumes exactly what the unchanged recognizer produced.)"""
    m = FLOAT_RE.match(token)
    if not m or m.start() != 0:
        return None
    float_text = token[:m.end()]
    rest = token[m.end():]
    check_full_id(float_text, rest)
    return float_text, rest


def main():
    # FAIL_TO_PASS matrix pieces (tests/test_domain_cpp.py::test_expressions).
    decimal_floats = ['5e42', '5e+42', '5e-42',
                      '5.', '5.e42', '5.e+42', '5.e-42',
                      '.5', '.5e42', '.5e+42', '.5e-42',
                      '5.0', '5.0e42', '5.0e+42', '5.0e-42']
    hex_floats = ['ApF', 'Ap+F', 'Ap-F',
                  'A.', 'A.pF', 'A.p+F', 'A.p-F',
                  '.A', '.ApF', '.Ap+F', '.Ap-F',
                  'A.B', 'A.BpF', 'A.Bp+F', 'A.Bp-F']

    boundary_rest = [
        '', 'f', 'F', 'l', 'L',          # type suffixes (no following word char)
        '_udl', 'q_J', 'fudl', '_J',     # UDL names (incl. 'f' that starts a name)
        'fF', 'll', 'LL', 'uludl',       # multi-char tails
        'x', ' ', ';', '*', ')',         # non-word terminators
        'abc', 'Z9_', '__', 'e', 'p',
    ]
    float_texts = ['6.62607015e-34', '5.0', '5e42', '0xA.BpF', '.5', 'A.']

    # A2/A3: the regex boundary logic, against the real engine.
    rng = random.Random(7590)
    alphabet = list("fFlLuU_qJabZ09. ;*)+-eEpx")
    rest_cases = list(boundary_rest)
    for _ in range(40000):
        n = rng.randint(0, 8)
        rest_cases.append("".join(rng.choice(alphabet) for _ in range(n)))
    for rest in rest_cases:
        check_suffix_regex(rest)
        check_udl_regex(rest)

    # A4/A5/A6: the full id composite, against the real regexes + get_id.
    for ft in float_texts:
        for rest in rest_cases:
            check_full_id(ft, rest)

    # F2P exact tokens: float + each tested suffix, and the UDL variants.
    f2p_tokens = []
    for f in decimal_floats:
        for suffix in ['', 'f', 'F', 'l', 'L']:
            f2p_tokens.append(f + suffix)
        f2p_tokens.append(f + '_udl')
        f2p_tokens.append(f + 'fudl')
    for f in hex_floats:
        for suffix in ['', 'f', 'F', 'l', 'L']:
            f2p_tokens.append('0x' + f + suffix)
        f2p_tokens.append('0x' + f + '_udl')
    # the headline case from the issue (#7294 / #7590)
    f2p_tokens.append('6.62607015e-34q_J')
    checked_splits = 0
    for tok in f2p_tokens:
        if check_float_split(tok) is not None:
            checked_splits += 1

    # explicit headline assertion (real == expected from the test).
    ft, rest = '6.62607015e-34', 'q_J'
    assert real_parsed_float_id(ft, rest) == 'clL_Zli3q_JEL6.62607015e-34EE'
    assert model_parsed_float_id(ft, rest) == 'clL_Zli3q_JEL6.62607015e-34EE'

    print("G-AX OK: matchTypeTag/matchSuffixName deep models == real "
          "float_literal_suffix_re/udl_identifier_re on %d rest cases; "
          "parsedFloatId composite == real get_id over %d float-texts and the "
          "F2P token matrix (%d float splits); headline 6.62607015e-34q_J sound."
          % (len(rest_cases), len(float_texts), checked_splits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
