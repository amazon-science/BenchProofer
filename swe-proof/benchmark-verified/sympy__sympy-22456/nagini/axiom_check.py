#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-22456.

There is no consumed `@ContractOnly` axiom in model.py: the operation that
changed — how an atomic string-valued token reconstructs itself from its
positional arguments — is modelled DEEPLY (a direct, text-preserving rebuild).
This check validates that deep model against REALITY by exercising the REAL
`sympy.codegen.ast.String` (the very class the gold patch edits), confirming:

  (1) the type-abstraction bijection the model relies on: a `String` built from
      a text `t` exposes `text == t`;
  (2) the argument count the model pins: `String(t).args == ()` (length 0) — the
      defining text is held OFF the positional-argument list;
  (3) the argument-invariance the model's postcondition encodes — and the F2P
      test asserts — holds post-fix:
          st.func(*st.args)    == st        (the new, discriminating invariance)
          st.func(**st.kwargs()) == st      (the pre-existing kwargs invariance)
      with the rebuilt token carrying EXACTLY the original text (the model's
      `ToSeq(Result().text) == ToSeq(s.text)` clause), even for NON-empty text —
      the precise case the pre-fix reconstruction (a generic positional rebuild
      that cannot source the excluded text slot) loses.

Boundary + fuzz family of texts, including the F2P literal 'foobar'. The F2P
cases are enumerated explicitly and any skip is a loud failure (no skip-guard,
no double-mask: the rebuilt object is compared by full token equality, the same
relation the test uses). Imports only `sympy.codegen.ast`. Exit 0 iff sound.
"""
import random
import sys

from sympy.codegen.ast import String


def check_text_bijection(t):
    """(1) The model's `text: List[int]` carrier <-> the real `String.text`."""
    st = String(t)
    assert st.text == t, (
        "text bijection broken on %r: String(t).text == %r" % (t, st.text))


def check_arg_count(t):
    """(2) The model's `arg_count(s) == 0`: the defining text is off args."""
    st = String(t)
    assert st.args == (), (
        "arg_count model unsound on %r: String(t).args == %r (expected ())"
        % (t, st.args))


def check_argument_invariance(t):
    """(3) The deep model's reconstruction postcondition: rebuilding from the
    (empty) positional arguments yields a token equal to the original, carrying
    exactly the original text. Asserted at full token-equality (not a masked
    proxy)."""
    st = String(t)

    rebuilt_args = st.func(*st.args)          # the changed reconstruction op
    assert rebuilt_args == st, (
        "argument invariance broken on %r: func(*args) == %r, original %r"
        % (t, rebuilt_args, st))
    # the model pins the rebuilt text equals the original text, element-wise
    assert rebuilt_args.text == st.text, (
        "rebuilt text != original on %r: %r vs %r"
        % (t, rebuilt_args.text, st.text))

    rebuilt_kwargs = st.func(**st.kwargs())   # the pre-existing invariance
    assert rebuilt_kwargs == st, (
        "kwargs invariance broken on %r: func(**kwargs()) == %r, original %r"
        % (t, rebuilt_kwargs, st))


def main():
    # --- F2P case enumerated explicitly (must NOT be skipped) --------------
    f2p_texts = ['foobar']
    for t in f2p_texts:
        check_text_bijection(t)
        check_arg_count(t)
        check_argument_invariance(t)

    # --- boundary family --------------------------------------------------
    boundary = [
        '',            # empty text: invariance must hold trivially
        'a',           # single char
        'foobar',      # the F2P literal
        'foo bar',     # whitespace
        "Joe's",       # apostrophe
        'a"b',         # quote
        '<x>&amp;',    # html-ish content
        'café',        # non-ascii
        'Ω≈ç√∫',       # unicode
        'x' * 200,     # long
        ' ',           # whitespace only
        '\n\t',        # control chars
    ]
    for t in boundary:
        check_text_bijection(t)
        check_arg_count(t)
        check_argument_invariance(t)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(22456)
    alphabet = ('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
                '0123456789 _-.,;:!?\'"<>&#=()[]{}'
                'éàüΩπ•λ')
    for _ in range(20000):
        n = rng.randint(0, 24)
        t = ''.join(rng.choice(alphabet) for _ in range(n))
        check_text_bijection(t)
        check_arg_count(t)
        check_argument_invariance(t)

    print("G-AX OK: String argument invariance (func(*args) == self) and the "
          "text/arg-count bijections sound on %d F2P + %d boundary + 20000 fuzz "
          "texts" % (len(f2p_texts), len(boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
