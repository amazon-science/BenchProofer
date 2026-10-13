#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-7590 (nagini).

SHADOW: the impl regions of model.py (`number_literal_id`,
`c_number_literal_id`), copied verbatim below with the contract calls
stripped. The @Pure helpers are specification-side only (the impl inlines
the code-point constants). The one @ContractOnly callee, `ident_mangle`,
calls the REAL repo function: the trailing identifier's component id is
obtained from the real unchanged identifier id-generator
(``ASTIdentifier.get_id``), exactly as the real code obtains it — this is
also how the model's `ident_id` input is defined (its Requires pins
`ident_id == ident_mangle(ident)`).

ORACLE: the REAL patched repo functions per mapping.md, imported from
/testbed after the gate applies patch.diff:
  * cpp leg — the real ``sphinx.domains.cpp.DefinitionParser._parse_literal``
    run on each generated token (terminated by ')'); the produced AST node's
    ``get_id`` (versions 3 and 4) is the real mangled id the shadow must
    reproduce.
  * simpler-dialect leg — the real ``sphinx.domains.c.DefinitionParser
    ._parse_literal`` on each token; the produced numeric literal's text,
    framed by the real shared id framing (``ASTNumberLiteral.get_id`` of the
    cpp module — the deep-modelled `number_id_seq` callee), is the real id.

Type bridge (mapping.md section 2): all character data str <-> List[int] of
code points; shadow outputs are decoded via chr for the comparison. The
model inputs are derived from each token by replaying the real UNCHANGED
regex boundaries (the literal-match pipeline and the recognised-suffix /
UDL-identifier regexes), which mapping.md abstracts as the inputs
`suffixed` / `ident` / `trail` / `valid`:
  * cpp: `lit` = the matched numeric text including a recognised suffix when
    one matches (the parser's definition[pos:self.pos] boundary), `ident` =
    the UDL identifier that follows an unsuffixed literal (empty when none),
    `suffixed` = the recognised-suffix regex matched;
  * c-domain: `lit` = the matched numeric text, `trail` = the maximal
    trailing run over the suffix alphabet, `valid` = the recognised-suffix
    regex consumes exactly that run.

Input domain: generated tokens keep every model Requires satisfied by
construction — nonempty numeric text, trailing identifier never the one
reserved short-abbreviation identifier, `ident_id` supplied from the real
generator. Boundary: the full (numeric base x trailing run) matrices from
the bundle's G-AX check plus UDL identifier pairings. Fuzz: random numeric
bases, suffix runs, and identifiers until >= 1e5 checks. Pinned seed: 7590.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + sphinx (the repo under test) only.
"""
import json
import random
import sys
import warnings

warnings.filterwarnings("ignore")

SEED = 7590
N_TARGET = 100000
ID_VERSIONS = (3, 4)
SUFFIX_ALPHABET = "uUlLfF"
RESERVED = "std"  # outside the contracted identifier domain (model Requires)


# --- impl regions of model.py, verbatim, contract calls stripped -------------

def number_literal_id(lit, ident, suffixed, ident_id):
    if not suffixed and len(ident) > 0:
        # user-defined literal: mangle as the call ident(literal),
        # concatenating the prefix, the identifier id, the numeric id and the
        # framing 'E's.
        result = [99, 108, 76, 95, 90, 108, 105] + ident_id \
            + [69, 76] + lit + [69, 69]  # type: List[int]
        return result
    else:
        # ordinary numeric literal: its id is 'L' + text + 'E'
        out = [76] + lit + [69]  # type: List[int]
        return out
    # impl-end


def c_number_literal_id(lit, trail, valid):
    if valid:
        # the recognised numeric suffix is consumed into the literal text
        out = [76] + lit + trail + [69]  # type: List[int]
        return out
    else:
        # the trailing run is not a valid suffix: the literal text is just `lit`
        plain = [76] + lit + [69]  # type: List[int]
        return plain
    # impl-end


# --- bridge -------------------------------------------------------------------

def to_codes(s):
    return [ord(c) for c in s]


def from_codes(cs):
    return "".join(chr(c) for c in cs)


def main():
    from sphinx.domains.cpp import (
        DefinitionParser as CppParser, ASTIdentifier, ASTNumberLiteral,
    )
    from sphinx.domains import c as c_domain
    from sphinx.util.cfamily import (
        integers_literal_suffix_re, float_literal_suffix_re,
        float_literal_re, binary_literal_re, hex_literal_re,
        integer_literal_re, octal_literal_re,
    )

    class CppConfig:
        cpp_id_attributes = []
        cpp_paren_attributes = []

    class CConfig:
        c_id_attributes = []
        c_paren_attributes = []

    def match_literal(token):
        """Replay the real literal-match pipeline (float first, then the int
        bases): returns (numeric_text, is_float) or None."""
        m = float_literal_re.match(token)
        if m and m.group(0):
            return m.group(0), True
        for rx in (binary_literal_re, hex_literal_re, integer_literal_re,
                   octal_literal_re):
            m = rx.match(token)
            if m and m.group(0):
                return m.group(0), False
        return None

    def suffix_consumed(is_float, rest):
        """What the recognised-suffix regex consumes at this position of the
        token (rest is followed by the ')' terminator = a word boundary)."""
        rx = float_literal_suffix_re if is_float else integers_literal_suffix_re
        m = rx.match(rest + ")")
        if m and m.group(0) and m.group(0) == rest[:len(m.group(0))]:
            return m.group(0)
        return ""

    def maximal_run(rest):
        i = 0
        while i < len(rest) and rest[i] in SUFFIX_ALPHABET:
            i += 1
        return rest[:i]

    # --- cpp leg ----------------------------------------------------------------

    def real_ident_id(ident, version):
        # the REAL unchanged identifier id-generator (the @ContractOnly callee)
        return ASTIdentifier(ident).get_id(version)

    def check_cpp(token):
        """token = numeric base + trailing text; derive the model inputs by
        replaying the unchanged regex boundaries, then diff shadow vs the real
        patched parser. Returns error string or None."""
        split = match_literal(token)
        if split is None:
            return None  # not a numeric-literal token; outside the domain
        base, is_float = split
        rest = token[len(base):]
        consumed = suffix_consumed(is_float, rest)
        if consumed:
            # recognised suffix: parser folds it into the literal text
            lit, ident, suffixed = base + consumed, "", True
            after = rest[len(consumed):]
        else:
            lit, suffixed = base, False
            m_ident = None
            import re as _re
            m_ident = _re.match(r'[a-zA-Z_][a-zA-Z0-9_]*', rest)
            ident = m_ident.group(0) if m_ident else ""
            after = rest[len(ident):]
        if after:
            return None  # leftover text: the token isn't one literal
        if ident == RESERVED:
            return None  # outside the model's contracted identifier domain
        for v in ID_VERSIONS:
            ident_id = to_codes(real_ident_id(ident, v)) if ident else []
            shadow = from_codes(number_literal_id(
                to_codes(lit), to_codes(ident), suffixed, ident_id))
            try:
                p = CppParser(token + ")", location=None, config=CppConfig())
                ast = p._parse_literal()
                if ast is None or p.definition[p.pos:] != ")":
                    return ("DISAGREEMENT on cpp token %r: real parser did "
                            "not consume the whole token (shadow id %r)"
                            % (token, shadow))
                real = ast.get_id(v)
            except Exception as e:
                return ("DISAGREEMENT on cpp token %r (v%d):\n"
                        "  shadow id = %r\n  real parser raised %r"
                        % (token, v, shadow, e))
            if shadow != real:
                return ("DISAGREEMENT on cpp token %r (v%d, lit=%r ident=%r "
                        "suffixed=%r):\n  shadow id = %r\n  real id = %r"
                        % (token, v, lit, ident, suffixed, shadow, real))
        return None

    # --- simpler-dialect leg -----------------------------------------------------

    def check_c(token):
        split = match_literal(token)
        if split is None:
            return None
        base, is_float = split
        rest = token[len(base):]
        trail = maximal_run(rest)
        if rest != trail:
            return None  # trailing text beyond the suffix alphabet
        consumed = suffix_consumed(is_float, trail)
        valid = bool(trail) and consumed == trail
        shadow = from_codes(c_number_literal_id(
            to_codes(base), to_codes(trail), valid))
        try:
            p = c_domain.DefinitionParser(token + ")", location=None,
                                          config=CConfig())
            lit_node = p._parse_literal()
            if lit_node is None:
                return ("DISAGREEMENT on c token %r: real parser produced "
                        "no literal (shadow id %r)" % (token, shadow))
            # the shared id framing is the real cpp ASTNumberLiteral.get_id
            real = ASTNumberLiteral(lit_node.data).get_id(4)
        except Exception as e:
            return ("DISAGREEMENT on c token %r:\n  shadow id = %r\n"
                    "  real parser raised %r" % (token, shadow, e))
        if shadow != real:
            return ("DISAGREEMENT on c token %r (lit=%r trail=%r valid=%r):"
                    "\n  shadow id = %r\n  real id = %r"
                    % (token, base, trail, valid, shadow, real))
        return None

    # --- input generation ----------------------------------------------------------

    ints = ["5", "0", "075", "0x0123456789ABCDEF", "0XF", "0b1", "0B1", "12"]
    decimal_floats = ["5e42", "5e+42", "5e-42", "5.", "5.e42", "5.e+42",
                      "5.e-42", ".5", ".5e42", ".5e+42", ".5e-42", "5.0",
                      "5.0e42", "5.0e+42", "5.0e-42"]
    hex_floats = ["0x" + f for f in
                  ["ApF", "Ap+F", "Ap-F", "A.", "A.pF", "A.p+F", "A.p-F",
                   ".A", ".ApF", ".Ap+F", ".Ap-F", "A.B", "A.BpF", "A.Bp+F",
                   "A.Bp-F"]]
    bases = ints + decimal_floats + hex_floats
    suffix_runs = ["", "u", "U", "l", "L", "f", "F", "ul", "uL", "Ul", "lu",
                   "Lu", "ll", "LL", "uu", "ull", "llu", "lul", "ff", "fff",
                   "fl", "lf", "uf", "fu"]
    udl_idents = ["_udl", "q_J", "uludl", "fudl", "_", "a", "Z9", "_1_2_3",
                  "stdx", "st", "astd", "operator", "i", "s"]

    checked = 0

    # boundary matrices
    for base in bases:
        for run in suffix_runs:
            for chk in (check_cpp, check_c):
                err = chk(base + run)
                if err:
                    print(err)
                    return 1
                checked += 1
        for ident in udl_idents:
            err = check_cpp(base + ident)
            if err:
                print(err)
                return 1
            checked += 1

    # fuzz
    rng = random.Random(SEED)
    ident_start = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    ident_alpha = ident_start + "0123456789"

    def rand_base():
        kind = rng.randint(0, 3)
        if kind == 0:
            return str(rng.randint(0, 10 ** rng.randint(1, 9)))
        if kind == 1:  # decimal float
            a = str(rng.randint(0, 999))
            b = str(rng.randint(0, 999))
            s = a + "." + b
            if rng.random() < 0.5:
                s += "e" + rng.choice(["", "+", "-"]) + str(rng.randint(0, 99))
            return s
        if kind == 2:  # hex int
            return "0x" + "".join(rng.choice("0123456789abcdefABCDEF")
                                  for _ in range(rng.randint(1, 8)))
        return "0b" + "".join(rng.choice("01") for _ in range(rng.randint(1, 8)))

    while checked < N_TARGET:
        base = rand_base()
        kind = rng.randint(0, 2)
        if kind == 0:
            run = "".join(rng.choice(SUFFIX_ALPHABET)
                          for _ in range(rng.randint(0, 4)))
            token = base + run
            err = check_cpp(token) or check_c(token)
        elif kind == 1:
            n = rng.randint(1, 10)
            ident = rng.choice(ident_start) + "".join(
                rng.choice(ident_alpha) for _ in range(n - 1))
            if ident == RESERVED:
                ident += "_"
            err = check_cpp(base + ident)
        else:
            err = check_cpp(base) or check_c(base)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched literal parsing/mangling "
          "on %d token checks (seed %d; cpp + simpler-dialect legs); "
          "0 disagreements." % (checked, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
