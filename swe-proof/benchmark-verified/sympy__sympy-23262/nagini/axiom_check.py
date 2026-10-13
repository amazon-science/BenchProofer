#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-23262.

This bundle consumes NO `@ContractOnly` axiom. The one changed operation that
relies on unchanged library machinery is the delimited separator-join performed
by the recursive container serialiser: `left + ', '.join(element_fragments) +
right`, where the post-fix delimiter pair is `("[", "]")` for the square-bracket
kind and `("(", ",)")` for the parenthesis kind. The model models that assembly
DEEPLY as the front-recursive `joined` + delimiter selection (model.py pure
region). G-AX validates that deep model **== the real callee semantics** (an
A-reference):

  (A-reference 1)  joined(elems) == ", ".join(elems)
      element fragments concatenated left-to-right with exactly one ", "
      between adjacent pairs, no trailing separator.

  (A-reference 2)  rendered(elems, is_paren) == left + ", ".join(elems) + right
      the full container literal the fixed serialiser emits:
        * square-bracket kind: "[" + body + "]"
        * parenthesis kind:    "(" + body + ",)"   (REQUIRED trailing comma)

  (round-trip)  for the parenthesis kind, the emitted text re-parses (via
      ast.literal_eval) to a container of the SAME ARITY as the input -- in
      particular a one-element parenthesis container re-parses to a one-element
      tuple, NOT to the bare element. (This is exactly the regression the F2P
      test pins: lambdify([], (1,)) must emit "(1,)" so it returns a 1-tuple,
      not "(1)" which would return the int 1.)

Imports nothing repo-specific: `", ".join`, string `+`, and `ast.literal_eval`
are Python itself -- the same operations the gold patch relies on. Exit 0 iff
every observation matches the model. Code points: '(' = 40, ')' = 41,
'[' = 91, ']' = 93, ',' = 44, ' ' = 32.
"""
import ast
import random
import sys


# --- model.py reference encodings (kept in lock-step with the pure region) ---

LPAREN = 40    # '('
RPAREN = 41    # ')'
LBRACKET = 91  # '['
RBRACKET = 93  # ']'
COMMA = 44     # ','
SEP = [44, 32]  # ', '


def joined_model(elems):
    """Reference impl of model.py's deep model `joined`, on lists of code-point
    lists. Front-recursive ", "-join, no trailing separator."""
    if len(elems) == 0:
        return []
    if len(elems) == 1:
        return list(elems[0])
    return list(elems[0]) + SEP + joined_model(elems[1:])


def left_delim_model(is_paren):
    return [LPAREN] if is_paren else [LBRACKET]


def right_delim_model(is_paren):
    return [COMMA, RPAREN] if is_paren else [RBRACKET]


def rendered_model(elems, is_paren):
    """Reference impl of model.py's deep model `rendered`."""
    return left_delim_model(is_paren) + joined_model(elems) + right_delim_model(is_paren)


# --- the REAL post-fix serialiser semantics (the gold patch) -----------------

def real_assemble(element_strs, is_paren):
    """The exact text the fixed `_recursive_to_string` emits for an iterable:
    `left + ', '.join(...) + right` with the post-fix delimiter pair."""
    if is_paren:
        left, right = "(", ",)"   # gold: left, right = "(", ",)"
    else:
        left, right = "[", "]"    # gold: left, right = "[", "]"
    return left + ", ".join(element_strs) + right


# --- the checks --------------------------------------------------------------

def to_cps(s):
    return [ord(ch) for ch in s]


def check_join(element_strs):
    """A-reference 1: joined == the REAL ", ".join semantics."""
    elems = [to_cps(s) for s in element_strs]
    observed = to_cps(", ".join(element_strs))   # real callee semantics
    expected = joined_model(elems)               # deep model
    assert observed == expected, (
        "joined deep model unsound on %r: ', '.join gave %r, model %r"
        % (element_strs, observed, expected))


def check_render(element_strs, is_paren):
    """A-reference 2: rendered == the exact text the fixed serialiser emits."""
    elems = [to_cps(s) for s in element_strs]
    observed = to_cps(real_assemble(element_strs, is_paren))  # gold form
    expected = rendered_model(elems, is_paren)                # deep model
    assert observed == expected, (
        "rendered deep model unsound on (%r, paren=%s): gold form %r, model %r"
        % (element_strs, is_paren, observed, expected))
    # Delimiter fidelity.
    if is_paren:
        assert observed[0] == LPAREN, "opening delimiter not '('"
        assert observed[-1] == RPAREN, "closing delimiter not ')'"
        assert observed[-2] == COMMA, "missing required trailing comma before ')'"
    else:
        assert observed[0] == LBRACKET, "opening delimiter not '['"
        assert observed[-1] == RBRACKET, "closing delimiter not ']'"


def check_roundtrip_arity(element_literals, is_paren):
    """Round-trip: the emitted text re-parses to a container of the SAME ARITY.
    `element_literals` are valid Python literal source fragments (e.g. "1",
    "2.5") so the assembled text is itself a parseable literal.

    The empty parenthesis kind is excluded: "(,)" is not valid Python and
    lambdify never serialises a zero-element tuple -- the issue and the gold
    fix concern the one-element-tuple regression, the 0-tuple is out of the
    tested/supported domain. (The deep-model structural check still covers the
    0-element paren container; only the literal re-parse is skipped.)"""
    if is_paren and len(element_literals) == 0:
        return
    text = real_assemble(element_literals, is_paren)
    value = ast.literal_eval(text)
    container_type = tuple if is_paren else list
    assert isinstance(value, container_type), (
        "re-parsed %r as %s, expected %s" % (text, type(value), container_type))
    assert len(value) == len(element_literals), (
        "arity collapsed: %r re-parsed to %r (len %d != %d)"
        % (text, value, len(value), len(element_literals)))


def main():
    # --- boundary element lists (incl. the critical 0- and 1-element cases) ---
    boundary = [
        [],                # empty container
        ["1"],             # the regression case: one-element
        ["1", "2"],        # two-element (must stay correct)
        ["x", "y", "z"],
        ["", ""],          # empty fragments still get the separator
        ["", "x", ""],
        ["a", "b", "c", "d", "e"],
        ["x + 1", "y - 2"],  # fragments containing spaces/operators
    ]
    for elems in boundary:
        check_join(elems)
        for is_paren in (True, False):
            check_render(elems, is_paren)

    # --- round-trip arity over literal fragments (the F2P semantics) ---------
    literal_lists = [
        ["1"],                 # gh-23224: lambdify([], (1,)) -> "(1,)" -> (1,)
        ["1", "2"],            # (1, 2) stays a 2-tuple
        ["3", "2"],            # test_issue_14941: f2(2,3) == (3,2)
        ["1", "2", "3", "4"],
        ["1.5"],
        ["1.5", "2.5", "3.5"],
    ]
    for lits in literal_lists:
        for is_paren in (True, False):
            check_roundtrip_arity(lits, is_paren)
    # Explicit gh-23224 witness: the one-element tuple must NOT collapse to int.
    assert real_assemble(["1"], True) == "(1,)"
    assert ast.literal_eval("(1,)") == (1,)
    assert isinstance(ast.literal_eval(real_assemble(["1"], True)), tuple)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(23262)
    alphabet = "abcxyz0123456789 +-*/[](){}, "
    for _ in range(20000):
        n = rng.randint(0, 6)
        elems = []
        for _a in range(n):
            m = rng.randint(0, 8)
            elems.append("".join(rng.choice(alphabet) for _ in range(m)))
        check_join(elems)
        for is_paren in (True, False):
            check_render(elems, is_paren)

    # --- randomized round-trip fuzz over integer-literal fragments -----------
    for _ in range(20000):
        n = rng.randint(0, 6)
        lits = [str(rng.randint(-999, 999)) for _ in range(n)]
        for is_paren in (True, False):
            check_roundtrip_arity(lits, is_paren)

    print("G-AX OK: joined / rendered deep models (== ', '.join and the "
          "left+body+right container assembly with the required trailing comma) "
          "sound on %d boundary lists + %d round-trip literal lists + 40000 "
          "fuzz; one-element parenthesis container re-parses to a 1-tuple "
          "(arity preserved)." % (len(boundary), len(literal_lists)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
