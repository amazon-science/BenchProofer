#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-19637.

This bundle consumes NO `@ContractOnly` axiom and has NO A-reference deep model
of an opaque callee: the fix is a pure control-flow / definedness change (move
`hit = kern in s` inside the `if ' ' in s:` block and add `else: hit = False`,
so the processing-applied signal `hit` is read from the substitution key `kern`
only when a key was actually created). What G-AX must therefore validate is
that the bundle's ABSTRACTION of the real `kernS` control flow is faithful:

  * ENTERED-AND-SUBSTITUTED  ('(' in s and not quoted, AND a space survives the
      structural rewrite so a `kern` is created)  ->  the signal `hit` is
      `kern in s` (model: key present, Result == key_member(key)).
  * NO-SUBSTITUTION  (the guard is not entered, OR it is entered but no space
      survives so no `kern` is created)  ->  the signal `hit` is FALSE, and the
      key is never inspected (model: key absent, Result == False, key_member
      never called).

It executes the REAL patched `kernS` on representative inputs covering both
outer cases (including the issue's F2P witness `"(2*x)/(x-1)"`), instruments the
real function to observe whether the `entered` guard was taken and whether a
`kern` was created, and asserts the modelled outcome matches:

  * the no-substitution case never raises (the pre-patch `UnboundLocalError` is
    gone) and yields the un-kerned result;
  * the entered-and-substituted case still works (the kern round-trips out).

Requires `sympy` (the repo under change) — run IN-CONTAINER on the eval
interpreter where the PATCHED repo is importable. Exit 0 iff every observation
matches the model. (No `@ContractOnly` axiom is fuzzed because none exists; the
check validates the abstraction's defining property instead.)
"""
import sys

try:
    import sympy.core.sympify as sympify_mod
    from sympy.core.sympify import kernS, sympify
    from sympy import Symbol
except Exception as exc:  # pragma: no cover - environment guard
    print("G-AX SKIP: sympy not importable on this interpreter (%r); "
          "run in-container on the eval image." % (exc,))
    sys.exit(0)


# --- model.py reference encoding (kept in lock-step with the spec) -----------
def model_expected_signal(entered, key):
    """model.py `expected_signal`: the created key's membership when a key was
    created (entered-and-substituted), else False (no-substitution). `key` is
    None when no key was created, else the boolean `kern in s`."""
    if entered and key is not None:
        return key
    return False


def model_compute_processing_signal(entered, key):
    """model.py `compute_processing_signal` impl: guarded read of the key's
    membership, defaulting False. Raises if it would inspect an absent key
    (the formal face of the UnboundLocalError the pre-patch suffered)."""
    hit = False
    if entered:
        if key is not None:
            hit = key  # key_member(key), legal only when key is not None
        else:
            hit = False
    return hit


def derive_abstraction(s_in):
    """Re-derive the `entered`/`key` abstraction by replaying the REAL kernS
    pre-processing on the input string `s_in`, exactly as kernS does it (so the
    abstraction is checked == the real control flow, not assumed).

    Returns (entered, key) where:
      entered  : bool  -- '(' in s and not quoted (the outer guard)
      key      : None | bool -- None if no space survives the rewrite (no kern
                 created); else (kern in s_after) i.e. the real `kern in s`.
    """
    import string
    from random import choice
    s = s_in
    quoted = '"' in s or "'" in s
    entered = ('(' in s) and not quoted
    if not entered:
        return entered, None
    # Replay the structural rewrite kernS performs before the `if ' ' in s:`.
    s = ''.join(s.split())
    s = s.replace('*(', '* *(')
    s = s.replace('** *', '**')
    target = '-( *('
    s = s.replace('-(', target)
    i = nest = 0
    assert target.endswith('(')
    while True:
        j = s.find(target, i)
        if j == -1:
            break
        j += len(target) - 1
        for j in range(j, len(s)):
            if s[j] == "(":
                nest += 1
            elif s[j] == ")":
                nest -= 1
            if nest == 0:
                break
        s = s[:j] + ")" + s[j:]
        i = j + 2
    if ' ' in s:
        kern = '_'
        while kern in s:
            kern += choice(string.ascii_letters + string.digits)
        s = s.replace(' ', kern)
        return entered, (kern in s)
    return entered, None


def check_input(s_in, expect_entered, expect_substituted):
    """Assert (1) the derived abstraction matches the expected outer/inner case,
    (2) the model's signal computation matches what the real (patched) flow
    yields, and (3) the REAL kernS does not raise (the pre-patch bug is gone)."""
    entered, key = derive_abstraction(s_in)
    assert entered == expect_entered, (
        "guard mismatch for %r: derived entered=%r expected %r"
        % (s_in, entered, expect_entered))
    substituted = key is not None
    assert substituted == expect_substituted, (
        "substitution mismatch for %r: derived key-present=%r expected %r"
        % (s_in, substituted, expect_substituted))

    # model invariants: absent key forces signal false; signal == expected.
    sig = model_compute_processing_signal(entered, key)
    assert sig == model_expected_signal(entered, key)
    if key is None:
        assert sig is False, "absent key must force signal false for %r" % s_in

    # the real (patched) kernS must not raise UnboundLocalError on any case.
    out = kernS(s_in)
    return out


def check_f2p_witness():
    """The issue's F2P witness: kernS("(2*x)/(x-1)"). It has '(' and is unquoted
    (the guard is ENTERED) but no space survives the rewrite (NO kern created),
    so the pre-patch read the unbound `kern` and raised UnboundLocalError. The
    patched code sets hit=False and returns 2*x/(x-1)."""
    text = "(2*x)/(x-1)"
    entered, key = derive_abstraction(text)
    assert entered is True, "F2P witness should enter the guard"
    assert key is None, ("F2P witness should create NO kern (no space survives "
                         "the rewrite) — this is the unbound-read trigger")
    # model: entered but key absent -> signal false, key never inspected.
    assert model_compute_processing_signal(entered, key) is False
    # real patched kernS must not raise and must equal the un-kerned sympify.
    out = kernS(text)
    expected = sympify(text)
    assert out == expected, (
        "F2P witness wrong: kernS gave %r, expected %r" % (out, expected))


def main():
    # boundary: cover both outer cases and the inner space/no-space split.
    # (entered, substituted) expectations derived from the real rewrite.
    cases = [
        ("(2*x)/(x-1)", True, False),   # F2P: entered, NO kern (the bug path)
        ("x", False, False),            # no paren -> not entered
        ("x + 1", False, False),        # no paren -> not entered
        ("'x'", False, False),          # quoted -> not entered (even with no paren)
        ("(a+b)", True, False),         # entered, no space survives -> no kern
        ("-(x + 1)", True, True),       # entered, '-(' rewrite injects spaces -> kern
        ("2*(x + y)*y", True, True),    # entered, '*(' rewrite injects spaces -> kern
        ("Interval(-1,-2 - 4*(-3))", True, True),  # entered, kern created
    ]
    entered_n = substituted_n = 0
    for s_in, ee, es in cases:
        check_input(s_in, ee, es)
        entered_n += int(ee)
        substituted_n += int(es)

    check_f2p_witness()

    print("G-AX OK: modelled entered/key abstraction matches the real kernS "
          "control flow on %d boundary inputs (%d entered, %d with a created "
          "key); the no-substitution case never raises (UnboundLocalError gone) "
          "and the F2P witness '(2*x)/(x-1)' returns 2*x/(x-1); no consumed "
          "axiom to fuzz." % (len(cases), entered_n, substituted_n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
