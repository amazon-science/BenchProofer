#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-22456.

Executes the REAL repo object (`sympy.codegen.ast.String`) on inputs (boundary
text values plus randomized fuzzing) and asserts that the bundle's single
deep-model reference matches the real callee, as encoded in Solution.lean.

IMPORTANT — what G-AX may and may NOT check (SPEC_GUIDE §0.7):
  G-AX runs against the repo AS-IS (the gold patch is NOT applied; only G-CONF
  applies it). It therefore validates ONLY the contracts of callees the patch
  leaves UNCHANGED. It must NEVER assert the behavior the patch CHANGES — that
  is the operation under specification, validated against the patched object by
  G-CONF (the argument-invariance reproduction), not borrowed here as an axiom.

The single kind-A check (there are NO consumed axioms in this bundle):

  (A-reference) the deep model `exposedArgs s = []` (Solution.lean pure region)
      == the real `String(text).args`. The positional-argument view of the
      atomic string object is modeled deeply (the empty list), not behind a
      consumed axiom; G-AX validates that deep model against the real callee:
        String(t).args == ()   for every text t.
      This structural inspection is UNCHANGED by the patch (`text` stays in
      `not_in_args`, so it is never passed to the `Basic` constructor — `args`
      is `()` both pre- and post-patch). It is the empty positional view that
      makes `func(*args)` a zero-argument call — the call the new nullary `func`
      is built to accept. The reconstruction-call semantics themselves
      (`func(*args)==self`, `func(**kwargs())==self`, `kwargs()=={}`) are the
      CHANGED operation and are deliberately NOT asserted here; G-CONF checks
      them against the patched object.

Imports only `sympy` (the repo under test) + stdlib. Exit 0 iff the unchanged
A-reference holds on every observed input.
"""
import random
import sys


def check_args_reference(String, t):
    """A-reference (UNCHANGED callee): the deep model exposedArgs == [] equals
    the real String.args == ()."""
    observed = String(t).args
    assert observed == (), (
        "exposedArgs deep model unsound on %r: String(t).args == %r, "
        "deep model requires ()" % (t, observed))


def main():
    from sympy.codegen.ast import String

    boundary = [
        "", "foobar", "foo", "a", "text", "String('x')", " ", "\t\n",
        "héllo", "x" * 64, "0", "&<>\"'", "Joe's", "Can't",
    ]
    for t in boundary:
        check_args_reference(String, t)

    rng = random.Random(22456)
    alphabet = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    "0123456789 _-.,;:'\"<>&é•")
    N = 20000
    for _ in range(N):
        k = rng.randint(0, 24)
        t = "".join(rng.choice(alphabet) for _ in range(k))
        check_args_reference(String, t)

    # A subclass of String inherits the same UNCHANGED structural inspection:
    # `text` remains in `not_in_args`, so its args view is also empty.
    class Signifier(String):
        pass
    for t in ["foobar", "", "x"]:
        observed = Signifier(t).args
        assert observed == (), (
            "subclass exposedArgs deep model unsound on %r: args == %r, "
            "requires ()" % (t, observed))

    print("G-AX OK: exposedArgs deep model (== String.args == ()) sound on "
          "%d boundary + %d fuzz text inputs + subclass. (UNCHANGED callee; the "
          "changed reconstruction-call invariance is checked by G-CONF on the "
          "patched object.)" % (len(boundary), N))
    return 0


if __name__ == "__main__":
    sys.exit(main())
