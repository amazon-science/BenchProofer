#!/usr/bin/env python3
"""G-CONF conformance check for sphinx-doc__sphinx-7590.

Differential-tests the R/I shadow of `Solution.lean`'s impl region
(`literalIdAfterFloat` + the pure-region models it calls) against the behaviour
of `patch.diff` (the gold patch), which the harness has applied in-tree before
running this script. The oracle is therefore the REAL post-patch C++ literal
parser (`sphinx.domains.cpp.DefinitionParser`).

Bridge (mapping.md §2): a literal token is a Python `str` ↔ a Lean `List Char`.
For a token whose float prefix `float_literal_re` recognizes, the Lean model
takes `(floatText, rest)` = (matched prefix, remainder); its output is the id
string `ast.get_id(version)` the literal node produces. We feed each fuzzed
token to the real parser, take the produced node's id, and compare to the
shadow's `parsed_float_id(floatText, rest)`. Zero disagreements ⇒ exit 0.

Only the **float branch** is modeled, so we restrict the differential to tokens
whose float prefix is non-empty (the modeled site). stdlib + repo only; seed
pinned to 7590 (mapping.md §4).
"""
import random
import re
import sys

# --- R/I shadow: transliteration of Solution.lean's impl + pure region -------


def _is_ascii_alpha(c):
    return ('a' <= c <= 'z') or ('A' <= c <= 'Z')


def _is_ascii_digit(c):
    return '0' <= c <= '9'


def is_word_char(c):
    return _is_ascii_alpha(c) or _is_ascii_digit(c) or c == '_'


def is_ident_start(c):
    return _is_ascii_alpha(c) or c == '_'


def is_type_tag_char(c):
    return c in ('f', 'F', 'l', 'L')


def match_type_tag(rest):
    if not rest:
        return None
    c, cs = rest[0], rest[1:]
    if is_type_tag_char(c):
        if not cs:
            return c
        return None if is_word_char(cs[0]) else c
    return None


def match_suffix_name(rest):
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


def number_lit_id(text):
    return "L" + text + "E"


def ident_id(ident):
    if ident == "std":
        return "St"
    return str(len(ident)) + ident


def suffixed_lit_id(lit_text, ident):
    return "clL_Zli" + ident_id(ident) + "E" + number_lit_id(lit_text) + "E"


def parsed_float_id(float_text, rest):
    tag = match_type_tag(rest)
    if tag is not None:
        return number_lit_id(float_text + tag)
    name = match_suffix_name(rest)
    if name is not None:
        return suffixed_lit_id(float_text, name)
    return number_lit_id(float_text)


# --- real oracle: the patched repo parser ------------------------------------

def build_oracle():
    from sphinx.util.cfamily import float_literal_re
    from sphinx.domains.cpp import DefinitionParser

    class _Cfg:
        cpp_id_attributes = ["id_attr"]
        cpp_paren_attributes = ["paren_attr"]

    def real_id(token):
        """Parse `token` as a C++ expression and return its level-3 id, or None
        if it is not parseable / not a single literal."""
        try:
            parser = DefinitionParser(token, location=None, config=_Cfg())
            parser.allowFallbackExpressionParsing = False
            ast = parser.parse_expression()
        except Exception:
            return None
        # only compare when the whole token parsed as one expression
        if str(ast) != token:
            return None
        try:
            full = ast.get_id(version=3)
        except Exception:
            return None
        # strip the version prefix the test also strips (idActual[len(prefix):])
        from sphinx.domains.cpp import _id_prefix
        prefix = _id_prefix[3]
        return full[len(prefix):] if full.startswith(prefix) else full

    return float_literal_re, real_id


def main():
    try:
        float_literal_re, real_id = build_oracle()
    except Exception as e:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not import patched repo parser: %r" % e)
        return 2

    rng = random.Random(7590)

    # deterministic float-prefix corpus (the F2P matrix) + fuzzed suffixes.
    decimal_floats = ['5e42', '5e+42', '5e-42',
                      '5.', '5.e42', '5.e+42', '5.e-42',
                      '.5', '.5e42', '.5e+42', '.5e-42',
                      '5.0', '5.0e42', '5.0e+42', '5.0e-42']
    hex_floats = ['ApF', 'Ap+F', 'Ap-F',
                  'A.', 'A.pF', 'A.p+F', 'A.p-F',
                  '.A', '.ApF', '.Ap+F', '.Ap-F',
                  'A.B', 'A.BpF', 'A.Bp+F', 'A.Bp-F']
    float_prefixes = list(decimal_floats) + ['0x' + h for h in hex_floats]

    # suffix alphabet: type tags, UDL-ident chars, and a few terminators that
    # keep the token a single literal expression.
    suffix_alpha = list("fFlLuU_qJabcZ09")
    fixed_suffixes = ['', 'f', 'F', 'l', 'L', '_udl', 'fudl', 'q_J', '_J',
                      'uludl', 'ludl', 'Fudl', 'abc', '_', '__9']

    compared = 0
    disagreements = 0
    examples = []

    def consider(token):
        nonlocal compared, disagreements
        m = float_literal_re.match(token)
        if not m or m.start() != 0 or m.end() == 0:
            return
        float_text = token[:m.end()]
        rest = token[m.end():]
        shadow = parsed_float_id(float_text, rest)
        oracle = real_id(token)
        if oracle is None:
            # token not a single parseable literal expression -> out of scope
            return
        compared += 1
        if shadow != oracle:
            disagreements += 1
            if len(examples) < 20:
                examples.append((token, shadow, oracle))

    # deterministic matrix
    for fp in float_prefixes:
        for sfx in fixed_suffixes:
            consider(fp + sfx)
    # headline case from the issue
    consider('6.62607015e-34q_J')

    # fuzz to >= 1e5 total comparisons
    target = 100000
    while compared < target:
        fp = rng.choice(float_prefixes)
        n = rng.randint(0, 9)
        sfx = "".join(rng.choice(suffix_alpha) for _ in range(n))
        consider(fp + sfx)

    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements (seed=7590). Examples:"
              % (disagreements, compared))
        for tok, sh, orc in examples:
            print("  token=%r shadow=%r oracle=%r" % (tok, sh, orc))
        return 1

    print("G-CONF OK: R/I shadow of literalIdAfterFloat agrees with patch.diff "
          "behaviour on %d float-literal tokens (seed=7590), 0 disagreements."
          % compared)
    return 0


if __name__ == "__main__":
    sys.exit(main())
