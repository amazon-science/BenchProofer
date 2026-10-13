#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-17630.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean skeleton
`implementation_matrixSum` (= `canonicalizeMatrixSum terms`: drop additive-
identity terms, canonically order the surviving named terms) and diffs it
against the REAL patched constructor-postprocessor for `Add` over matrix-valued
terms, i.e. `Add(*terms).doit()` where every term is a `MatrixSymbol` or a
`ZeroMatrix`. This is exactly the all-matrix-terms branch the fix changes.

The Lean↔Python bijection (mapping.md):
  MatSumTerm.zeroMatrix   <-> ZeroMatrix(n, n)          (shaped additive identity)
  MatSumTerm.named name   <-> MatrixSymbol(name, n, n)  (a named matrix)
  MatSum.matrix names     <-> a matrix-valued result whose MatrixSymbol args,
                             read in order, are `names`   (names==[] => ZeroMatrix)
  MatSum.scalar           <-> a shapeless scalar `sympy.core.numbers.Zero`
                             (the pre-patch shape-losing outcome; the FIX never
                              produces it, so any scalar result here is a FAIL)

Domain (the proof's preconditions, faithful to the modeled branch):
  - terms non-empty (the all-matrix branch is only reached with matrices != []);
  - no `scalarZero` term (the fix never seeds a scalar identity into the matrix
    list — scalarZero models exactly the pre-patch injection);
  - surviving names distinct (real `MatAdd.doit` also combines like terms
    `A + A -> 2*A` via `glom`; out of scope for this fix, whose F2P scenarios use
    only distinct symbols and zero blocks).

Exit 0 iff zero disagreements over the boundary catalogue + >=1e5 randomized
draws. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 20240630
N_RANDOM = 120_000  # >= 1e5


# ---- Python shadow (transliteration of the Lean impl + spec) ----

def surviving_names(terms):
    """filterMap named -> name (survivingNames)."""
    return [t[1] for t in terms if t[0] == "named"]


def shadow_matrixsum(terms):
    """Shadow of implementation_matrixSum / canonicalizeMatrixSum on the fix's
    (no-scalarZero) domain. Returns ('matrix', sorted_names) — the fix is always
    matrix-valued. `terms` is a list of ('zeroMatrix',) / ('named', name)."""
    names = surviving_names(terms)
    if not names:
        return ("matrix", [])
    return ("matrix", sorted(names))  # Python str sort == Lean String <= (codepoint)


def classify_real(res):
    """Map a real sympy result to the MatSum bijection."""
    from sympy import MatrixSymbol, ZeroMatrix, MatAdd
    from sympy.core.numbers import Zero
    if isinstance(res, Zero) or res == 0:
        return ("scalar",)
    if isinstance(res, ZeroMatrix):
        return ("matrix", [])
    if isinstance(res, MatrixSymbol):
        return ("matrix", [res.name])
    if isinstance(res, MatAdd):
        # every arg must be a MatrixSymbol on the Nodup / no-explicit domain
        if all(isinstance(a, MatrixSymbol) for a in res.args):
            return ("matrix", [a.name for a in res.args])
        return ("other-matadd", [type(a).__name__ for a in res.args])
    return ("other", type(res).__name__)


def main():
    from sympy import MatrixSymbol, ZeroMatrix, Add

    rng = random.Random(SEED)
    disagreements = 0
    checked = 0
    N = 2  # common square shape; the fix's behavior is shape-independent here

    # distinct-name pool (single/multi char; exercises codepoint ordering)
    POOL = ["a", "b", "c", "d", "e", "X", "Y", "Z0", "x1", "x2",
            "A10", "A2", "aa", "ab", "m", "M", "zz", "q"]

    def build_terms(names, n_zero):
        """Return (lean_terms, sympy_args) with `names` named + `n_zero` zeros,
        in a randomized interleaving (order must not matter to the result)."""
        items = [("named", nm) for nm in names] + [("zeroMatrix",)] * n_zero
        rng.shuffle(items)
        sym = []
        for it in items:
            if it[0] == "named":
                sym.append(MatrixSymbol(it[1], N, N))
            else:
                sym.append(ZeroMatrix(N, N))
        return items, sym

    def check(lean_terms, sym_args, tag):
        nonlocal disagreements, checked
        if not sym_args:
            return
        real = classify_real(Add(*sym_args))
        exp = shadow_matrixsum(lean_terms)
        checked += 1
        if real != exp:
            disagreements += 1
            if disagreements <= 8:
                print(f"MISMATCH [{tag}] terms={lean_terms} real={real} shadow={exp}")

    # ----- boundary catalogue (incl. the exact F2P scenarios) -----
    boundary = [
        [("zeroMatrix",), ("zeroMatrix",)],                 # test_zero_matrix_add: Z+Z
        [("zeroMatrix",)],                                  # single zero
        [("named", "a")],                                   # single named
        [("named", "a"), ("zeroMatrix",)],                  # the b*b block: a + Z
        [("named", "a"), ("zeroMatrix",), ("zeroMatrix",)], # extra zeros
        [("zeroMatrix",), ("zeroMatrix",), ("zeroMatrix",)],# all zero (>2)
        [("named", "b"), ("named", "a")],                   # ordering b+a -> [a,b]
        [("named", "c"), ("named", "a"), ("named", "b")],
        [("named", "b"), ("named", "a"), ("zeroMatrix",)],
    ]
    for i, t in enumerate(boundary):
        _, sym = build_terms([x[1] for x in t if x[0] == "named"],
                             sum(1 for x in t if x[0] == "zeroMatrix"))
        # rebuild lean_terms to match the shuffled sym order
        lean_terms = []
        for a in sym:
            if isinstance(a, ZeroMatrix):
                lean_terms.append(("zeroMatrix",))
            else:
                lean_terms.append(("named", a.name))
        check(lean_terms, sym, f"boundary-{i}")

    # ----- randomized draws over the fix's domain -----
    for k in range(N_RANDOM):
        n_named = rng.randint(0, 4)
        n_zero = rng.randint(0, 4)
        if n_named + n_zero == 0:
            n_zero = 1  # keep non-empty (all-matrix branch)
        names = rng.sample(POOL, n_named)  # distinct (Nodup)
        lean_terms, sym = build_terms(names, n_zero)
        check(lean_terms, sym, "rand")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
