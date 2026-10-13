#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-16766.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean
`implementation_indexedCode` skeleton and diffs it against the REAL patched
method `PythonCodePrinter._print_Indexed` over a discrete catalogue plus >=1e5
randomized draws.

  observable: the source string produced for an `Indexed` access
  `base[i1, i2, ...]`.
    shadow:  base ++ "[" ++ ", ".join(rendered subscripts) ++ "]"
    real:    PythonCodePrinter()._print(IndexedBase(name)[idx...])

We construct each `Indexed` from an `IndexedBase` and a tuple of indices, then
read back the printer's rendering of the base and of each index to obtain the
INPUTS (`base`, `subscripts`) the Lean model is parameterized over — so the
diff isolates the assembly step (the only thing the patch changed).

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 20240626
N_RANDOM = 120_000  # >= 1e5


# ---- Python shadow of implementation_indexedCode ---------------------------

def shadow_indexed_code(base, subscripts):
    # transliteration of problem_spec_indexedCode / implementation_indexedCode:
    #   result = base ++ "[" ++ String.intercalate ", " subscripts ++ "]"
    return "{}[{}]".format(base, ", ".join(subscripts))


def main():
    from sympy import IndexedBase, Symbol, Integer
    from sympy.printing.pycode import PythonCodePrinter

    prntr = PythonCodePrinter()

    # candidate base names and index expression builders
    base_names = ["p", "q", "A", "data", "x_1", "M"]
    sym_names = ["i", "j", "k", "n", "m"]

    def make_index(rng):
        """Return a sympy index expression (varied: int literal or symbol)."""
        r = rng.random()
        if r < 0.5:
            return Integer(rng.randint(-9, 99))
        return Symbol(rng.choice(sym_names))

    disagreements = 0
    checked = 0
    rng = random.Random(SEED)

    # discrete catalogue: the F2P case + a spread of arities
    discrete = [
        ("p", [Integer(0), Integer(1)]),   # F2P: p[0, 1]
        ("p", [Integer(0)]),
        ("q", [Symbol("i")]),
        ("A", [Symbol("i"), Symbol("j")]),
        ("data", [Integer(3), Symbol("k"), Integer(-2)]),
    ]

    def run_case(name, indices):
        nonlocal disagreements, checked
        b = IndexedBase(name)
        expr = b[tuple(indices)] if len(indices) > 1 else b[indices[0]]
        # real rendering
        real = prntr._print(expr)
        # recover the inputs the Lean model sees, using the SAME unchanged callees
        base_str = str(expr.args[0])
        subs = [prntr._print(ind) for ind in expr.args[1:]]
        shadow = shadow_indexed_code(base_str, subs)
        checked += 1
        if real != shadow:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH name={name} idx={indices}: real={real!r} shadow={shadow!r}")

    for name, indices in discrete:
        run_case(name, indices)

    for _ in range(N_RANDOM):
        name = rng.choice(base_names)
        arity = rng.randint(1, 4)
        indices = [make_index(rng) for _ in range(arity)]
        run_case(name, indices)

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
