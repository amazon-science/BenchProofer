#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-15345.

This bundle consumes NO `@ContractOnly` axiom. The one changed operation that
relies on unchanged library machinery is the separator-join performed by the
printer's `stringify(args, ", ")` (`sympy/printing/str.py:35-36`), which is a
plain `", ".join([...])`. The model models that join DEEPLY as the front-
recursive `joined` (model.py pure region). G-AX validates that deep model
**== the real callee semantics** (an A-reference):

  (A-reference 1)  joined(operands) == ", ".join(operands)
      i.e. the operands concatenated left-to-right with exactly one ", "
      between adjacent pairs and no trailing separator.

  (A-reference 2)  rendered(name, operands) == name + "[" + ", ".join(ops) + "]"
      i.e. the full surface assembly: recognised name, opening square bracket,
      ", "-joined operand body, closing square bracket — the exact text the
      gold patch makes the Mathematica printer emit for a recognised function
      application (`"%s[%s]" % (mfunc, self.stringify(expr.args, ", "))`).

Imports nothing repo-specific: `", ".join` and `str` formatting are Python
itself — the same operations the gold patch relies on. Exit 0 iff every
observation matches the model. Code points: '[' = 91, ']' = 93, ',' = 44,
' ' = 32 (and the rejected round-paren delimiters '(' = 40, ')' = 41).
"""
import random
import sys


# --- model.py reference encodings (kept in lock-step with the pure region) ---

LBRACKET = 91   # '['
RBRACKET = 93   # ']'
SEP = [44, 32]  # ', '


def joined_model(operands):
    """Reference impl of model.py's deep model `joined`, on lists of code-point
    lists. Front-recursive ", "-join, no trailing separator."""
    if len(operands) == 0:
        return []
    if len(operands) == 1:
        return list(operands[0])
    return list(operands[0]) + SEP + joined_model(operands[1:])


def rendered_model(name, operands):
    """Reference impl of model.py's deep model `rendered`."""
    return list(name) + [LBRACKET] + joined_model(operands) + [RBRACKET]


# --- the checks --------------------------------------------------------------

def to_cps(s):
    return [ord(ch) for ch in s]


def check_join(operand_strs):
    """A-reference 1: joined == the REAL ", ".join semantics."""
    operands = [to_cps(s) for s in operand_strs]
    observed = to_cps(", ".join(operand_strs))   # real callee semantics
    expected = joined_model(operands)            # deep model
    assert observed == expected, (
        "joined deep model unsound on %r: ', '.join gave %r, model %r"
        % (operand_strs, observed, expected))


def check_render(name_str, operand_strs):
    """A-reference 2: rendered == name + '[' + ", ".join(ops) + ']' (the exact
    surface text the gold patch emits for a recognised application)."""
    operands = [to_cps(s) for s in operand_strs]
    observed = to_cps("%s[%s]" % (name_str, ", ".join(operand_strs)))  # gold form
    expected = rendered_model(to_cps(name_str), operands)              # deep model
    assert observed == expected, (
        "rendered deep model unsound on (%r, %r): gold form %r, model %r"
        % (name_str, operand_strs, observed, expected))
    # The application delimiters are square brackets, never round parens.
    assert observed[len(name_str)] == LBRACKET, "opening delimiter not '['"
    assert observed[len(observed) - 1] == RBRACKET, "closing delimiter not ']'"
    assert LBRACKET != 40 and RBRACKET != 41, "bracket/paren confusion"


def main():
    # --- boundary operand lists (the spec requires >= 1 operand) -------------
    boundary_args = [
        ["x"],
        ["x", "2"],
        ["2", "x"],
        ["x", "y", "z"],
        ["y", "z"],
        ["a", "b", "c", "d", "e"],
        ["", ""],              # empty operands still get the separator
        ["", "x", ""],
        ["Sin[x]", "Cos[y]"],  # nested already-rendered forms
        ["x + 1", "y - 2"],    # operands containing spaces/operators
        ["x, y"],              # a single operand that itself contains ", "
        ["Max[a, b]", "c"],
    ]
    names = ["Max", "Min", "f", "ArcSin", "Conjugate"]

    for args in boundary_args:
        check_join(args)
        for nm in names:
            check_render(nm, args)

    # --- end-to-end witnesses matching the F2P test --------------------------
    assert to_cps("%s[%s]" % ("Max", ", ".join(["2", "x"]))) == to_cps("Max[2, x]")
    assert (to_cps("%s[%s]" % ("Max", ", ".join(["x", "y", "z"]))) ==
            to_cps("Max[x, y, z]"))
    assert to_cps("%s[%s]" % ("Min", ", ".join(["y", "z"]))) == to_cps("Min[y, z]")

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(15345)
    alphabet = "abcxyz0123456789 +-*/[](){}, "
    for _ in range(20000):
        n = rng.randint(1, 6)
        args = []
        for _a in range(n):
            m = rng.randint(0, 8)
            args.append("".join(rng.choice(alphabet) for _ in range(m)))
        check_join(args)
        nm = "".join(rng.choice("abcMaxMin") for _ in range(rng.randint(1, 5)))
        check_render(nm, args)

    print("G-AX OK: joined / rendered deep models (== ', '.join and the "
          "name[body] surface assembly) sound on %d boundary operand lists x "
          "%d names + 3 F2P witnesses + 20000 fuzz" %
          (len(boundary_args), len(names)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
