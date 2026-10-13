#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-9320.

Executes the REAL stdlib callees the modeled code relies on
(`os.path.expanduser`, `os.path.isdir`) and asserts that every observation
satisfies the corresponding `@ContractOnly` axiom in model.py.

The two axioms (both A-consumed) encode only the WEAKEST facts the proof needs:

  (expand_home)  os.path.expanduser('')  ==  ''
      Expanding the home prefix of the EMPTY path leaves it empty (there is no
      leading '~' to expand). Modeled: Implies(len(x)==0, len(Result())==0).

  (path_is_dir) os.path.isdir('')        is  False
      The EMPTY path is never an existing directory. Modeled:
      Implies(len(x)==0, Result()==False).

These are the two facts that make the ordinary (strict) path validator REJECT
an empty response -- which is exactly why, pre-patch, pressing Enter at the
re-prompt raised a validation error and looped forever instead of aborting.

Imports nothing repo-specific: `os.path` is the Python standard library -- the
very module the patched code calls (`from os import path`). Exit 0 iff every
obligation holds.
"""
import os
import os.path
import random
import sys


def check_expand_home_empty():
    """Axiom expand_home: expanding the empty path yields an empty path."""
    observed = os.path.expanduser("")
    assert observed == "", (
        "expand_home axiom unsound: os.path.expanduser('') gave %r, "
        "axiom requires the empty string" % (observed,))


def check_path_is_dir_empty():
    """Axiom path_is_dir: the empty path is never an existing directory."""
    observed = os.path.isdir("")
    assert observed is False, (
        "path_is_dir axiom unsound: os.path.isdir('') gave %r, "
        "axiom requires False" % (observed,))


def check_strict_rejects_empty():
    """End-to-end witness of the relied-on consequence: the strict validator's
    guard `not path.isdir(path.expanduser(x))` fires on the empty response, so
    an empty response is rejected by the strict validator. (This is the branch
    the pre-patch re-prompt took, raising instead of aborting.)"""
    x = ""
    expanded = os.path.expanduser(x)
    assert not os.path.isdir(expanded), (
        "strict-validator guard does not fire on empty input: "
        "expanduser(%r)=%r, isdir=%r" % (x, expanded, os.path.isdir(expanded)))


def check_nonempty_consistency():
    """Boundary + fuzz: the axioms only constrain the empty case, but confirm
    the real callees are total (never raise) on the kinds of responses the
    prompt feeds them, so the weakest-contract claim is honest and the
    non-empty path stays on the ordinary existing-directory requirement."""
    boundary = [
        "/", ".", "..", os.getcwd(), os.path.expanduser("~"),
        "/nonexistent_dir_xyz_123", "relative/path", "a", "  ",
        "/tmp", "~", "~/", "~nouser_xyz/sub",
    ]
    for s in boundary:
        # both callees are total on str input (no exception)
        _ = os.path.expanduser(s)
        _ = os.path.isdir(s)

    rng = random.Random(9320)
    alphabet = list("abc/.~ _-0123456789")
    for _ in range(20000):
        n = rng.randint(0, 16)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        expanded = os.path.expanduser(s)
        isdir = os.path.isdir(s)
        # The only axiomatized obligation: empty -> empty / not-a-dir.
        if s == "":
            assert expanded == "", "expanduser('') != ''"
            assert isdir is False, "isdir('') is not False"


def main():
    check_expand_home_empty()
    check_path_is_dir_empty()
    check_strict_rejects_empty()
    check_nonempty_consistency()
    print("G-AX OK: expand_home + path_is_dir axioms sound on the empty-path "
          "obligation (os.path.expanduser('')=='' , os.path.isdir('') is "
          "False) + 12 boundary + 20000 fuzz totality observations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
