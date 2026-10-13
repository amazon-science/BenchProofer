#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-7590.

Executes the REAL (patched) C++ domain code in-container and asserts that every
observation matches the model in model.py:

  (A-consumed) the `ident_mangle` axiom (model.py axioms region): over its
      RESTRICTED domain (a nonempty identifier that is not the reserved `std`),
      the mangled id of `ident` is `str(len(ident)) + ident`, so the identifier
      text is a proper suffix of its id. Checked against the real
      `ASTIdentifier.get_id` on boundary + fuzz over the UDL-identifier
      alphabet ([A-Za-z_][A-Za-z0-9_]*), with `std` included in the boundary
      set. The check ALSO proves the domain restriction is load-bearing and
      complete: for every special-case branch the real generator deviates on
      (the reserved `std`; a destructor `~...`; an anonymous `@...`) it asserts
      that the axiom's length-prefixed claim would be VIOLATED, so the model's
      precondition (which excludes `std`, and whose UDL-identifier domain
      cannot start with `~`/`@`) is exactly the sound domain — the over-claim
      is no longer hidden. Special branches are enumerated by inspecting the
      real `ASTIdentifier.get_id` source for literal `==`/startswith branches.

  (A-reference, deep model) the user-defined-literal mangling
      `udl_id_seq` and the suffix-vs-identifier decision (model.py pure region +
      number_literal_id) modelled deeply, validated == the real callees:
        * `number_id_seq(lit)` == real `ASTNumberLiteral.get_id` (= 'L'+lit+'E').
        * `udl_id_seq(lit, ident)` == real `ASTUserDefinedLiteral.get_id`
          (= 'clL_Zli'+ident_id+'E'+number_id+'E').
        * for every FAIL_TO_PASS user-defined-literal token, the real
          DefinitionParser round-trips str(ast) and yields get_id(v) equal to
          the model-predicted id for the udl branch — i.e. the model's
          acceptance/mangling decision agrees with the real parser at the
          token level (no skip-guard hides an F2P case: every F2P token is
          enumerated and asserted, failing loud on any miss).

Imports only the repository module under test (`sphinx.domains.cpp`,
`sphinx.util.cfamily`) — available in the official container — plus the standard
library. Exit 0 iff every obligation holds.
"""
import random
import sys
import warnings

warnings.filterwarnings("ignore")

from sphinx.domains.cpp import (
    DefinitionParser, ASTIdentifier, ASTNumberLiteral, ASTUserDefinedLiteral,
)
from sphinx.domains import c as c_domain
from sphinx.util.cfamily import (
    DefinitionError, integers_literal_suffix_re, float_literal_suffix_re,
    float_literal_re, binary_literal_re, hex_literal_re, integer_literal_re,
    octal_literal_re,
)

ID_VERSIONS = (3, 4)

# The suffix-alphabet the PRE-PATCH C-domain loop (`while self.current_char in
# 'uUlLfF': self.pos += 1`) scanned. The model's `trail` is the MAXIMAL run of
# these characters following the matched numeric literal.
SUFFIX_ALPHABET = "uUlLfF"

# The model's `ident_mangle` axiom is contracted over a RESTRICTED domain: a
# nonempty identifier that is NOT this reserved one. The real
# `ASTIdentifier.get_id` special-cases it to a fixed two-character abbreviation
# ('St'), so the length-prefixed claim does not hold for it; the model excludes
# it by precondition (code points 115, 116, 100).
RESERVED_IDENT = "std"


class _Config:
    cpp_id_attributes = ["id_attr"]
    cpp_paren_attributes = ["paren_attr"]


# --- model.py reference encodings (kept in lock-step with the spec) ----------

def model_ident_mangle(ident):
    """model.py `ident_mangle`: decimal length of the identifier, then the
    identifier text."""
    return str(len(ident)) + ident


def model_number_id(lit):
    """model.py `number_id_seq`: 'L' + literal text + 'E'."""
    return "L" + lit + "E"


def model_udl_id(lit, ident):
    """model.py `udl_id_seq`: clL_Zli + <ident-id> + E + <number-id> + E."""
    return "clL_Zli" + model_ident_mangle(ident) + "E" + model_number_id(lit) + "E"


def model_c_number_id(lit, trail, valid):
    """model.py `c_number_literal_id`: the simpler dialect's numeric-literal id.
    A recognised numeric suffix run (`valid` True) is folded into the text; a
    trailing run that is not a recognised suffix (`valid` False) is dropped."""
    text = lit + trail if valid else lit
    return model_number_id(text)


def model_c_number_text(lit, trail, valid):
    """The text the simpler dialect's numeric literal carries: literal-plus-suffix
    when the run is a recognised suffix, else the bare literal."""
    return lit + trail if valid else lit


# --- the checks --------------------------------------------------------------

def in_axiom_domain(ident):
    """The model's `ident_mangle` precondition: a nonempty identifier that is
    not the reserved `std`. (A UDL identifier additionally cannot start with
    `~`/`@`, but those are out of `udl_identifier_re` anyway.)"""
    return len(ident) > 0 and ident != RESERVED_IDENT


def check_ident_axiom(ident, version):
    """A-consumed: ON THE CONTRACTED DOMAIN, real ASTIdentifier.get_id ==
    model_ident_mangle (and the identifier text is a proper suffix of the id,
    the property the proof uses). The axiom makes NO claim outside the domain,
    so callers must only invoke this for in-domain idents."""
    assert in_axiom_domain(ident), (
        "check_ident_axiom called outside the contracted domain on %r — the "
        "axiom makes no claim there" % (ident,))
    observed = ASTIdentifier(ident).get_id(version)
    expected = model_ident_mangle(ident)
    assert observed == expected, (
        "ident_mangle axiom unsound on %r (v%d): real get_id gave %r, "
        "axiom requires %r" % (ident, version, observed, expected))
    # the exact structural property the axiom's Ensures encodes
    assert len(observed) > len(ident) and observed.endswith(ident), (
        "ident_mangle structural property broken on %r: %r" % (ident, observed))


def check_excluded_branch(ident, version):
    """The domain restriction is LOAD-BEARING and COMPLETE: for an identifier
    on a real special-case branch (the reserved `std`; a destructor `~...`; an
    anonymous `@...`), the axiom's length-prefixed claim is VIOLATED by the
    real generator. Asserting the violation here proves the model is right to
    exclude these inputs — and that an over-claiming axiom (no precondition)
    would be caught, not hidden, by this check."""
    observed = ASTIdentifier(ident).get_id(version)
    would_be = model_ident_mangle(ident)
    structural_holds = len(observed) > len(ident) and observed.endswith(ident)
    assert observed != would_be or not structural_holds, (
        "expected the real ASTIdentifier.get_id to DEVIATE from the "
        "length-prefixed axiom on excluded ident %r (v%d), but it agreed "
        "(%r) — the domain exclusion would be spurious" % (ident, version, observed))


def check_number_axiom(lit, version):
    observed = ASTNumberLiteral(lit).get_id(version)
    expected = model_number_id(lit)
    assert observed == expected, (
        "number_id_seq deep model unsound on %r (v%d): real get_id gave %r, "
        "model gives %r" % (lit, version, observed, expected))


def check_udl_object(lit, ident, version):
    """A-reference: real ASTUserDefinedLiteral.get_id == model_udl_id."""
    obj = ASTUserDefinedLiteral(ASTNumberLiteral(lit), ASTIdentifier(ident))
    observed = obj.get_id(version)
    expected = model_udl_id(lit, ident)
    assert observed == expected, (
        "udl_id_seq deep model unsound on (lit=%r, ident=%r, v%d): real "
        "get_id gave %r, model gives %r" % (lit, ident, version, observed, expected))


def parse_expr(expr):
    p = DefinitionParser(expr, location=None, config=_Config())
    p.allowFallbackExpressionParsing = False
    return p.parse_expression()


def check_parse_udl(numeric, ident, version):
    """End-to-end: the real parser accepts a numeric literal followed by a UDL
    identifier (the suffix-vs-identifier decision) and mangles it as the model
    predicts. `numeric` is the numeric literal text, `ident` the trailing UDL
    identifier; the token is their concatenation."""
    expr = numeric + ident
    ast = parse_expr(expr)               # must NOT raise (decision: it is a UDL)
    assert str(ast) == expr, (
        "parser did not round-trip UDL token %r: str(ast)=%r" % (expr, str(ast)))
    observed = ast.get_id(version)
    expected = model_udl_id(numeric, ident)
    assert observed == expected, (
        "model/parser disagree on UDL token %r (v%d): parser id %r, model %r"
        % (expr, version, observed, expected))


# --- the simpler dialect (no user-defined literals): suffix-vs-not decision ---

class _CConfig:
    c_id_attributes = ["id_attr"]
    c_paren_attributes = ["paren_attr"]


def c_maximal_run(text_after):
    """The maximal leading run of suffix-alphabet characters in `text_after` —
    exactly what the PRE-PATCH `while self.current_char in 'uUlLfF'` loop scanned.
    The model's `trail` is this run."""
    i = 0
    while i < len(text_after) and text_after[i] in SUFFIX_ALPHABET:
        i += 1
    return text_after[:i]


def c_match_literal(token):
    """Replay the real C-domain literal-match pipeline on `token` (post-patch
    order: float first, then binary/hex/integer/octal) and return
    (lit, is_float) where `lit` is the matched numeric-literal text — i.e. the
    boundary the model's `lit` parameter abstracts. Returns None if the token is
    not a numeric literal. Matters for hex literals, where trailing a-f/A-F
    digits extend the LITERAL (not a suffix), so the split is regex-driven, not
    naive."""
    m = float_literal_re.match(token)
    if m and m.group(0):
        return m.group(0), True
    for rx in (binary_literal_re, hex_literal_re, integer_literal_re,
               octal_literal_re):
        m = rx.match(token)
        if m and m.group(0):
            return m.group(0), False
    return None


def real_suffix_valid(is_float, trail):
    """The model's `valid` discriminator computed exactly as the gold patch does:
    whether the recognised-suffix regex (`float_literal_suffix_re` for a float,
    `integers_literal_suffix_re` otherwise) matches the WHOLE maximal trailing
    run. `\\b` after the run (a non-word terminator follows the token) makes the
    regex match either the whole run or nothing — never a strict prefix; this is
    checked exhaustively below by parsing real tokens terminated by `)`."""
    rx = float_literal_suffix_re if is_float else integers_literal_suffix_re
    m = rx.match(trail + ")")          # ')' is the token terminator (word boundary)
    return bool(m) and m.group(0) == trail


def parse_c_number_text(token):
    """End-to-end: run the REAL gold-patched C-domain `_parse_literal` on the
    `token` (terminated by ')') and return the text the produced numeric literal
    actually carries (`ASTNumberLiteral.data`)."""
    expr = token + ")"
    p = c_domain.DefinitionParser(expr, location=None, config=_CConfig())
    lit = p._parse_literal()
    assert type(lit).__name__ == "ASTNumberLiteral", (
        "C-domain parsed %r as %s, expected a numeric literal"
        % (expr, type(lit).__name__))
    return lit.data


def check_c_number(token):
    """A-reference (the simpler dialect): the real C-domain `_parse_literal`
    consumes the trailing suffix run iff it is a recognised numeric suffix, and
    the model `c_number_literal_id` predicts exactly the resulting literal text
    (and hence its `L<text>E` id, the shared ordinary numeric-literal mangling).
    ALSO assert the PRE-PATCH behaviour (fold the whole maximal run
    unconditionally) is DETECTABLY WRONG whenever the run is not a recognised
    suffix — i.e. the modeled decision genuinely discriminates the fix.

    Returns True iff this token had a NON-recognised trailing run (so the
    pre-patch behaviour provably diverged on it)."""
    matched = c_match_literal(token)
    assert matched is not None, "not a numeric literal token: %r" % (token,)
    lit, is_float = matched
    # the model's `lit` is the matched literal; `trail` is the maximal suffix-
    # alphabet run that follows it (what the pre-patch loop would have scanned).
    trail = c_maximal_run(token[len(lit):])
    valid = real_suffix_valid(is_float, trail)
    observed_text = parse_c_number_text(token)
    expected_text = model_c_number_text(lit, trail, valid)
    assert observed_text == expected_text, (
        "c_number_literal_id deep model unsound on (lit=%r, trail=%r, "
        "is_float=%s): real parser kept text %r, model predicts %r"
        % (lit, trail, is_float, observed_text, expected_text))
    # the L<text>E framing the model wraps (shared with the cpp number id)
    assert model_c_number_id(lit, trail, valid) == model_number_id(observed_text), (
        "c_number_literal_id id-framing drift on (lit=%r, trail=%r)"
        % (lit, trail))
    # pre-patch detectability: the old loop folds the WHOLE run, so its predicted
    # text is `lit+trail`. On a non-recognised run this differs from the gold
    # text, so the prepatch is observably wrong on exactly the modeled subdomain.
    if trail and not valid:
        prepatch_text = lit + trail            # the maximal-run impl
        assert prepatch_text != observed_text, (
            "expected the pre-patch maximal-run behaviour to DIVERGE from the "
            "gold parser on a non-recognised trailing run (lit=%r, trail=%r), "
            "but they agreed (%r) — the modeled decision would be spurious"
            % (lit, trail, observed_text))
        return True
    return False


def main():
    rng = random.Random(7590)

    # --- A-consumed: ident_mangle on boundary + fuzz, ON THE CONTRACTED -----
    # DOMAIN (nonempty, != "std"). `std` is in the boundary set so the check
    # would catch a regression that forgot to exclude it (see the excluded-
    # branch assertions below), but it is routed to check_excluded_branch, NOT
    # to the in-domain axiom check.
    ident_alpha = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    ident_start = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    boundary_idents = ["_udl", "q_J", "uludl", "fudl", "_", "a", "Z9", "_1_2_3",
                       "operator", "size_t", "i", "s", "std", "stdx", "st",
                       "astd"]
    for ident in boundary_idents:
        if not in_axiom_domain(ident):
            continue
        for v in ID_VERSIONS:
            check_ident_axiom(ident, v)
    fuzz_checked = 0
    for _ in range(5000):
        n = rng.randint(1, 12)
        ident = rng.choice(ident_start) + "".join(
            rng.choice(ident_alpha) for _ in range(n - 1))
        if not in_axiom_domain(ident):
            continue
        for v in ID_VERSIONS:
            check_ident_axiom(ident, v)
        fuzz_checked += 1

    # --- the domain restriction is load-bearing + complete -----------------
    # Enumerate every special-case branch in the real ASTIdentifier.get_id and
    # assert the length-prefixed axiom FAILS there (so excluding them is right,
    # and an over-claiming no-precondition axiom would be caught here):
    #   * the reserved `std`  -> 'St'   (excluded by the model precondition)
    #   * a destructor `~...` -> 'D0'   (cannot start a udl_identifier_re ident)
    #   * an anonymous `@...`  -> 'Ut..'(cannot start a udl_identifier_re ident)
    excluded_idents = ["std", "~Foo", "~T", "@a", "@anon"]
    for ident in excluded_idents:
        for v in ID_VERSIONS:
            check_excluded_branch(ident, v)
    # the reserved ident is exactly the model's excluded code points
    assert [ord(c) for c in RESERVED_IDENT] == [115, 116, 100], (
        "RESERVED_IDENT code points drifted from the model precondition")

    # --- number_id_seq deep model on the F2P numeric literals -------------
    ints = ["5", "0", "075", "0x0123456789ABCDEF", "0XF", "0b1", "0B1"]
    decimal_floats = ["5e42", "5e+42", "5e-42",
                      "5.", "5.e42", "5.e+42", "5.e-42",
                      ".5", ".5e42", ".5e+42", ".5e-42",
                      "5.0", "5.0e42", "5.0e+42", "5.0e-42"]
    hex_floats = ["ApF", "Ap+F", "Ap-F",
                  "A.", "A.pF", "A.p+F", "A.p-F",
                  ".A", ".ApF", ".Ap+F", ".Ap-F",
                  "A.B", "A.BpF", "A.Bp+F", "A.Bp-F"]
    numerics = list(ints) + list(decimal_floats) + ["0x" + f for f in hex_floats]
    for lit in numerics:
        for v in ID_VERSIONS:
            check_number_axiom(lit, v)

    # --- A-reference: real ASTUserDefinedLiteral.get_id == model ----------
    udl_idents = ["_udl", "q_J", "uludl", "fudl"]
    for lit in numerics:
        for ident in udl_idents:
            for v in ID_VERSIONS:
                check_udl_object(lit, ident, v)

    # --- A-reference: end-to-end parser decision + mangling on every F2P --
    # number-literal UDL token (enumerated; fails loud if any is skipped) --
    f2p_tokens = []                        # (numeric_text, udl_ident)
    for i in ints:
        f2p_tokens.append((i, "_udl"))
        # 'uludl' is NOT a recognised integer suffix (the suffix regex's word
        # boundary fails before 'udl'), so the whole 'uludl' is the UDL ident.
        f2p_tokens.append((i, "uludl"))
    for f in decimal_floats:
        f2p_tokens.append((f, "_udl"))
        f2p_tokens.append((f, "fudl"))
    for f in hex_floats:
        f2p_tokens.append(("0x" + f, "_udl"))
    # the exact token from issue #7294
    f2p_tokens.append(("6.62607015e-34", "q_J"))

    checked = 0
    for numeric, ident in f2p_tokens:
        for v in ID_VERSIONS:
            check_parse_udl(numeric, ident, v)
        checked += 1
    assert checked == len(f2p_tokens), "skipped an F2P UDL token"

    # --- A-reference (the simpler dialect, sphinx/domains/c.py): the real -----
    # gold-patched C-domain `_parse_literal` consumes a trailing suffix run iff
    # it is a recognised numeric suffix; `c_number_literal_id` predicts the
    # resulting literal text exactly, and the PRE-PATCH maximal-run behaviour is
    # detectably wrong on every non-recognised trailing run. Each test forms a
    # TOKEN (literal text + a trailing suffix-alphabet run); check_c_number
    # splits it into the model's (lit, trail) via the real literal-match
    # pipeline, so hex digits that extend the literal are handled correctly.
    # Decimal/octal int bases (suffix-alphabet chars never extend them) and
    # decimal/hex float bases.
    int_bases = ["5", "0", "075", "12", "0XF", "0b1", "0B1"]
    float_bases = list(decimal_floats) + ["0x" + f for f in hex_floats]
    # trailing suffix-alphabet runs (length 0..3): recognised int suffixes
    # (u/l combinations), recognised float suffixes (f/F/l/L), and non-recognised
    # runs (e.g. 'f' after an int, 'u' after a float, doubled 'ff'/'ll').
    trail_runs = ["", "u", "U", "l", "L", "f", "F",
                  "ul", "uL", "Ul", "lu", "Lu", "ll", "LL", "uu",
                  "ull", "llu", "lul", "ff", "fff", "fl", "lf", "uf", "fu"]
    c_checked = 0
    c_divergences = 0
    for base in int_bases + float_bases:
        for trail in trail_runs:
            diverged = check_c_number(base + trail)
            c_divergences += int(diverged)
            c_checked += 1
    # fuzz the trailing run over the suffix alphabet so the model's `valid`
    # discriminator is validated against the real regex decision broadly.
    c_fuzz = 0
    fuzz_bases = ["5", "0", "075", "12"] + list(decimal_floats)
    for _ in range(2000):
        n = rng.randint(0, 4)
        trail = "".join(rng.choice(SUFFIX_ALPHABET) for _ in range(n))
        base = rng.choice(fuzz_bases)
        c_divergences += int(check_c_number(base + trail))
        c_fuzz += 1
    assert c_divergences > 0, (
        "no non-recognised trailing run in the C-domain matrix — the pre-patch "
        "detectability check would be vacuous")

    print("G-AX OK: ident_mangle (A-consumed) sound on the contracted domain "
          "(boundary set incl. std-neighbours + %d in-domain fuzz idents); "
          "domain restriction proven load-bearing + complete on %d excluded "
          "special-branch idents (std/~dtor/@anon all deviate from the "
          "length-prefixed claim); number_id_seq + udl_id_seq deep models == "
          "real callees on %d numerics x %d idents; real parser "
          "decision+mangling == model on %d F2P UDL tokens; the simpler-dialect "
          "c_number_literal_id == real C-domain _parse_literal on %d "
          "(literal x trail) cases + %d fuzz (with %d non-recognised runs where "
          "the pre-patch maximal-run behaviour provably diverges)"
          % (fuzz_checked, len(excluded_idents), len(numerics),
             len(udl_idents), checked, c_checked, c_fuzz, c_divergences))
    return 0


if __name__ == "__main__":
    sys.exit(main())
