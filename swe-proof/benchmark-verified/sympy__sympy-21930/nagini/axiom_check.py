#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-21930.

This bundle ships NO consumed `@ContractOnly` axiom. The changed operation —
each operator's `_latex` rendering, and its interaction with the surrounding
power printer — is modelled DEEPLY in model.py as the pure functions
`grouped_token` (the token is the intrinsic body wrapped as one LaTeX group
`{ body }`) and `appended_super_is_outer` (an exponent appended after the token
binds to the whole group because the token ends in `}`).

This script validates those DEEP MODELS against the REAL SymPy LaTeX printer
(the library under change), the A-reference checks of refinement.md:

  (A-reference 1)  the rendered token of each of the three operators equals
      `grouped_token(body)` = "{" + intrinsic_body + "}", where `intrinsic_body`
      is the operator's pre-fix rendering (which contains an intrinsic "^").

  (A-reference 2)  when the operator is raised to a power, the composite the
      LaTeX power printer emits is `with_exponent(token, exp)` =
      token + "^{" + exp + "}", i.e. the appended exponent superscript sits
      immediately after the token's closing "}" (model `appended_super_is_outer`
      holds: the token ends in "}"), so the exponent binds to the whole group
      and does NOT collide with the body's interior "^".

Imports only `sympy` — the library under test, the module whose printer is the
real callee (the analogue of the reference bundle importing stdlib `html`).
Exit 0 iff every observation matches the deep model.
"""
import sys

import sympy as sp
from sympy.physics.secondquant import (
    B, Bd, F, Fd, AntiSymmetricTensor as AT,
)

LBRACE, RBRACE, CARET = "{", "}", "^"


def grouped_token(body):
    """Deep model: the rendered token is the body wrapped as one group."""
    return LBRACE + body + RBRACE


def appended_super_is_outer(token):
    """Deep model: an appended exponent binds outside the token iff the token
    ends in a closing brace (is a self-delimited group)."""
    return len(token) > 0 and token[-1] == RBRACE


def intrinsic_body(token):
    """Strip one outer LaTeX group `{ ... }`; the recovered intrinsic body is
    the operator's pre-fix rendering."""
    assert token.startswith(LBRACE) and token.endswith(RBRACE), token
    return token[1:-1]


def check_operator(name, obj, expected_body):
    """A-reference 1: the real `_latex` token equals grouped_token(body), and
    the intrinsic body carries an interior superscript (so the wrap matters)."""
    token = sp.latex(obj)
    # the real token is the deep model applied to the operator's intrinsic body
    assert token == grouped_token(expected_body), (
        "%s: real latex %r != grouped_token(%r) == %r"
        % (name, token, expected_body, grouped_token(expected_body)))
    body = intrinsic_body(token)
    assert body == expected_body, (
        "%s: recovered body %r != %r" % (name, body, expected_body))
    assert CARET in body, (
        "%s: intrinsic body %r lacks the interior '^' that motivates the group"
        % (name, body))
    # a self-delimited group: opens with '{', closes with '}'
    assert token[0] == LBRACE and token[-1] == RBRACE, token
    assert len(token) == len(body) + 2, token
    return token


def check_power_safe(name, obj):
    """A-reference 2: raising the operator to a power yields a composite in
    which the appended exponent superscript follows the token's closing '}'
    (the deep model `appended_super_is_outer` holds), so the exponent binds to
    the whole group rather than colliding with the body's interior '^'."""
    token = sp.latex(obj)
    assert appended_super_is_outer(token), (
        "%s: token %r is not a self-delimited group; an appended exponent "
        "would collide with the interior superscript" % (name, token))
    composite = sp.latex(obj ** 2)
    # the composite must contain the whole token followed immediately by the
    # exponent superscript "^{2}" (with_exponent(token, "2"))
    expected_fragment = token + CARET + LBRACE + "2" + RBRACE
    assert expected_fragment in composite, (
        "%s: composite %r does not contain %r — the appended exponent does not "
        "bind to the whole group" % (name, composite, expected_fragment))
    # and the malformed bare double-superscript (interior body + '^{2}') must
    # NOT be what the printer emits at top level
    bare = intrinsic_body(token) + CARET + LBRACE + "2" + RBRACE
    assert bare not in composite, (
        "%s: composite %r contains the malformed bare double superscript %r"
        % (name, composite, bare))


def main():
    i = sp.Symbol("i")
    a, b = sp.symbols("a b")
    ii, jj = sp.symbols("i j")
    zero = sp.Symbol("0")

    # --- A-reference 1: the three rendered tokens == grouped_token(body) -----
    operators = [
        ("CreateBoson(Bd)", Bd(i), r"b^\dagger_{i}"),
        ("CreateFermion(Fd)", Fd(i), r"a^\dagger_{i}"),
        ("AntiSymmetricTensor", AT("t", (a, b), (ii, jj)), r"t^{ab}_{ij}"),
    ]
    for name, obj, body in operators:
        token = check_operator(name, obj, body)
        # fuzz the index/state labels — the wrap structure is label-invariant
    # label fuzz for the creation operators
    for lab in ["i", "j", "p", "q", "n", "m", "0", "alpha"]:
        s = sp.Symbol(lab)
        tb = sp.latex(Bd(s))
        assert tb == grouped_token(intrinsic_body(tb)), (Bd, lab, tb)
        tf = sp.latex(Fd(s))
        assert tf == grouped_token(intrinsic_body(tf)), (Fd, lab, tf)

    # --- A-reference 2: power-safety on each operator ------------------------
    for name, obj in [
        ("CreateBoson(Bd)", Bd(zero)),
        ("CreateFermion(Fd)", Fd(zero)),
        ("AntiSymmetricTensor", AT("t", (a, b), (ii, jj))),
    ]:
        check_power_safe(name, obj)

    # --- the exact issue-19661 witness from the problem statement ------------
    from sympy.physics.secondquant import Commutator
    got = sp.latex(Commutator(Bd(zero) ** 2, B(zero)))
    expected = r'- \left[b_{0},{b^\dagger_{0}}^{2}\right]'
    assert got == expected, (
        "issue 19661 witness: got %r, expected %r" % (got, expected))

    print("G-AX OK: deep models grouped_token + appended_super_is_outer match "
          "the real SymPy LaTeX printer on the 3 changed operators (token == "
          "{body}, interior '^' present, power-safe) and the issue-19661 "
          "witness renders {b^\\dagger_{0}}^{2}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
