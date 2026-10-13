#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-16792 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `buildArgList` impl region
              transliterated to Python over the *real* repo carrier. For each
              requested argument the impl computes `argFor`: an array-like
              symbol receives its extent-derived dimension metadata
              `[(0, d-1) for d in shape]`; a plain scalar receives none. The
              full result is `argList` = those arguments in the requested order
              (count + order preserved). The bijection (mapping.md §2):
              Lean `Arg.bounds : List (Int × Int)` ↔ the real `Argument`'s
              `dimensions` attribute, with the empty list `[]` ↔ `None`/empty
              (no metadata) and a non-empty list of pairs ↔ the same `(lo, hi)`
              tuples.
  * ORACLE  — `patch.diff`'s behaviour: the patched code path that builds the
              positional argument list. We drive the REAL, patched
              `CCodeGen().routine(name, expr, argument_sequence=...)` in-process
              (the harness applies patch.diff at base_commit before this runs)
              and read back each produced argument's `.dimensions`. This is the
              actual Python the gold patch ships.

They must agree on every input: for each requested argument, the SHADOW's
modeled bounds must equal the ORACLE's real `dimensions` (under the None↔[]
bijection), in order. Exit 0 iff zero disagreements; any disagreement is a
mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), where `sympy` is
importable and patch.diff is applied. stdlib + sympy only; no Docker/DB. The
fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 16792
N_FUZZ = 100_000


def normalize_dims(dims):
    """The mapping.md bijection on the observable: a real `Argument.dimensions`
    of None (or empty) ↔ the Lean empty `bounds` list `[]`; a non-empty list of
    `(lo, hi)` sympy Integer pairs ↔ the same list of plain-int pairs."""
    if not dims:                      # None or empty -> no metadata
        return []
    return [(int(lo), int(hi)) for (lo, hi) in dims]


# --- SHADOW: Solution.lean argFor / argList, transliterated ------------------
def extent_bounds(extents):
    """extentBounds: each axis extent d -> the inclusive bound pair (0, d-1)."""
    return [(0, d - 1) for d in extents]


def shadow_arg_bounds(array_like, extents):
    """argFor for a freshly-built request, as `bounds` (mapping.md): an
    array-like symbol carries its extent-derived dimension metadata, a scalar
    carries none. (For the inputs fuzzed here a resolved array-like symbol gets
    the SAME extent-derived bounds at scan time, so `argFor` agrees on both
    legs; the prepatch is what diverges on the fresh leg — see refinement.md.)"""
    return extent_bounds(extents) if array_like else []


def shadow_arg_list(specs):
    """argList: the per-request argument map, in the requested order."""
    return [shadow_arg_bounds(al, ext) for (al, ext) in specs]


# --- ORACLE: patch.diff's behaviour, the real patched routine() --------------
def oracle_arg_dims(symbols):
    """Drive the REAL patched code path and read each produced argument's
    dimension metadata, in order.

    `symbols` is the requested argument_sequence (MatrixSymbol = array-like,
    Symbol = scalar; an IndexedBase request is normalized by routine() to its
    `.label`, a shapeless Symbol, BEFORE the modeled loop — mapping.md §2
    normalization note — so it reaches the fall-through as a scalar). The
    expression is the constant 1.0, so NONE of the requested symbols appears in
    it: every requested argument therefore takes the fall-through 'build fresh'
    leg the issue is about (an array argument not present in the wrapped
    expression). This is exactly the F2P scenario and its generalization over
    shapes / mixes."""
    from sympy import S
    from sympy.utilities.codegen import CCodeGen
    gen = CCodeGen()
    routine = gen.routine("f", S(1.0), argument_sequence=tuple(symbols))
    # routine.arguments preserves the requested order for these inputs.
    by_name = {str(a.name): a for a in routine.arguments}
    return [normalize_dims(by_name[str(s)].dimensions) for s in symbols]


def fuzz_inputs(n, rng):
    """Yield argument_sequences as lists of (sympy_symbol, array_like, extents).

    We build distinct-named MatrixSymbols (array-like, with a shape), plain
    Symbols (scalar), and IndexedBases (normalized by routine() to their
    shapeless `.label` Symbol before the modeled loop, hence a SCALAR request
    there — mapping.md §2 normalization note; the shadow spec accordingly maps
    them with array_like=False). Names are kept unique within a sequence so the
    requested order is unambiguous."""
    from sympy import IndexedBase, MatrixSymbol, Symbol

    def matrix(name, rows, cols):
        return (MatrixSymbol(name, rows, cols), True, [rows, cols])

    def scalar(name):
        return (Symbol(name), False, [])

    def indexed(name, *shape):
        # normalized to `.label` (a plain Symbol) before the fall-through
        # loop => reaches the modeled arm as a scalar request.
        return (IndexedBase(name, shape=tuple(shape)), False, [])

    # boundary cases first (plan §4.1 step 4)
    yield [matrix("x", 2, 1)]                          # the exact F2P case
    yield [matrix("x", 1, 1)]                          # 1x1 array-like
    yield [matrix("x", 3, 4)]                          # rectangular
    yield [scalar("y")]                                # scalar only
    yield [matrix("x", 2, 1), scalar("y")]             # mix, array first
    yield [scalar("y"), matrix("x", 2, 1)]             # mix, scalar first
    yield [matrix("x", 5, 1), matrix("z", 1, 7)]       # two arrays
    yield [scalar("p"), scalar("q")]                   # two scalars
    yield [matrix("a", 9, 9), scalar("b"), matrix("c", 2, 3)]
    yield [indexed("A", 3)]                            # IndexedBase, 1-D
    yield [indexed("B", 2, 4)]                         # IndexedBase, 2-D
    yield [indexed("A", 3), matrix("x", 2, 1), scalar("y")]  # full mix

    for _ in range(n):
        k = rng.randint(1, 5)
        seq = []
        for j in range(k):
            name = "v%d" % j
            r = rng.random()
            if r < 0.45:
                rows = rng.randint(1, 9)
                cols = rng.randint(1, 9)
                seq.append(matrix(name, rows, cols))
            elif r < 0.60:
                dims = [rng.randint(1, 9)
                        for _ in range(rng.randint(1, 3))]
                seq.append(indexed(name, *dims))
            else:
                seq.append(scalar(name))
        yield seq


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for seq in fuzz_inputs(N_FUZZ, rng):
        count += 1
        symbols = [s for (s, _, _) in seq]
        specs = [(al, ext) for (_, al, ext) in seq]
        shadow = shadow_arg_list(specs)
        oracle = oracle_arg_dims(symbols)
        if shadow != oracle:
            disagreements.append((
                [str(s) for s in symbols], shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for names, sh, orc in disagreements:
            print("  args=%r shadow=%r oracle=%r" % (names, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildArgList agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
