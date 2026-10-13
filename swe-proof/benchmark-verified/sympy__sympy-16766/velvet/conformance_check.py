#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-16766 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `renderAccess` impl region
              transliterated to Python over the *real* repo carrier (`str`).
              `accessRender base indices` assembles the access text:
                  base + "[" + joinComma(indices) + "]"
              where `joinComma` interleaves ", " between consecutive
              already-rendered subscript fragments (no leading/trailing
              separator). The bijection (mapping.md §2): Lean `List Char` ↔ `str`
              char-for-char; the `indices : List (List Char)` ↔ the list of the
              subscripts' already-rendered strings. The components fed to the
              shadow (the carrier's text `str(base)` and each `self._print(ind)`)
              are taken from the REAL printer — they are unchanged rendering
              helpers, part of the input carrier, not re-modeled here.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `PythonCodePrinter._print_Indexed`, the actual Python the gold
              patch ships (the harness applies patch.diff at base_commit before
              this runs).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), where `sympy` is
importable and patch.diff is applied. stdlib + sympy only; no Docker/DB. The
fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 16766
N_FUZZ = 100_000


# --- SHADOW: Solution.lean joinComma / accessRender, transliterated ----------
def join_comma(fragments):
    """joinComma: interleave ", " between consecutive fragments; the empty list
    joins to "" and a single fragment joins to itself."""
    return ", ".join(fragments)


def shadow_access(base_text, index_texts):
    """accessRender base indices: base + "[" + joinComma indices + "]"."""
    return base_text + "[" + join_comma(index_texts) + "]"


# --- ORACLE: patch.diff's behaviour, the real patched _print_Indexed ---------
def oracle_access(printer, expr):
    """Drive the REAL patched PythonCodePrinter._print_Indexed on an Indexed
    expression `expr` and return its rendered string."""
    return printer._print_Indexed(expr)


def main():
    from sympy import symbols, Integer, Symbol
    from sympy.printing.pycode import PythonCodePrinter
    from sympy.tensor import IndexedBase

    rng = random.Random(SEED)
    printer = PythonCodePrinter()

    # A pool of distinct base names and a pool of index expressions whose
    # rendered forms are stable. We always recompute the per-component strings
    # from the SAME printer the oracle uses, so the shadow consumes the real
    # `str(base)` / `self._print(ind)` outputs (mapping.md: unchanged helpers).
    base_names = ["p", "q", "q_name", "A", "data", "x1", "M_2", "tbl"]
    i, j, k, m, n = symbols("i j k m n")
    index_pool = [
        Integer(0), Integer(1), Integer(2), Integer(7), Integer(42),
        i, j, k, m, n, i + 1, 2 * j, i + j, k - 3, m * n,
    ]

    def build_case(base_name, idx_exprs):
        base = IndexedBase(Symbol(base_name))
        expr = base[tuple(idx_exprs)] if len(idx_exprs) > 1 else base[idx_exprs[0]]
        return expr

    def render_components(expr):
        # expr.args[0] is the IndexedBase carrier; args[1:] the indices — the
        # same decomposition the gold patch uses. str(base) and self._print(ind)
        # are the unchanged-helper outputs (R / input-carrier).
        base = expr.args[0]
        index = expr.args[1:]
        base_text = str(base)
        index_texts = [printer._print(ind) for ind in index]
        return base_text, index_texts

    disagreements = []
    count = 0

    def check(expr):
        nonlocal count
        count += 1
        base_text, index_texts = render_components(expr)
        shadow = shadow_access(base_text, index_texts)
        oracle = oracle_access(printer, expr)
        if shadow != oracle:
            disagreements.append((str(expr), shadow, oracle))

    # boundary cases first (plan §4.1 step 4)
    boundary = [
        ("p", [Integer(0)]),                       # the issue's example p[0]
        ("p", [Integer(0), Integer(1)]),           # the exact F2P case p[0, 1]
        ("p", [Integer(0), Integer(1), Integer(2)]),  # 3 subscripts
        ("q_name", [i]),                           # symbolic single index
        ("A", [i, j]),                             # two symbolic indices
        ("data", [i + 1, 2 * j]),                  # compound index expressions
        ("M_2", [k - 3, m * n, Integer(7)]),       # mixed compound + literal
    ]
    for base_name, idx in boundary:
        check(build_case(base_name, idx))

    for _ in range(N_FUZZ):
        base_name = rng.choice(base_names)
        nidx = rng.randint(1, 4)
        idx = [rng.choice(index_pool) for _ in range(nidx)]
        check(build_case(base_name, idx))
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for e, sh, orc in disagreements:
            print("  expr=%r shadow=%r oracle=%r" % (e, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of renderAccess agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
