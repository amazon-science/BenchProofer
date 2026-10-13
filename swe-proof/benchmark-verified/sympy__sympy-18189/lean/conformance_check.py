#!/usr/bin/env python
"""G-CONF — differential test of the R/I shadow of implementation_diophantine
against the patch.diff behaviour (post-patch `diophantine`).

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). The impl region is NOT all-A-tagged: it has R/I structure
(the `syms != var` reorder branch — accumulate per-tuple reindex, then return;
fall through to the canonical solve when `syms == var`). The single abstract
subroutine `solveCanonical eq permute` is left as the REAL repo callee
`diophantine(eq, param, permute=permute)` — exactly the recursive call the
post-patch reorder branch consumes. The shadow therefore reproduces the
post-patch reorder branch op-for-op (mapping.md / refinement.md).

ORACLE  = the real patched `diophantine(eq, syms=<syms>, permute=permute)`.
SHADOW  = reindex each tuple of the real `diophantine(eq, param, permute=permute)`
          into canonical (`var`) order using `dict_sym_index`, exactly mirroring
          implementation_diophantine.

The discriminating clause is mode propagation: on the reorder branch the
canonical solve MUST run under the caller's `permute`. The prepatch (the real
bug) runs it under base-only mode, so for `permute=True` sum-of-even-powers
equations the oracle yields the full sign/value-permuted solution set while a
mode-dropping shadow would yield only the base family — caught here.

stdlib + sympy fuzzing. exit 0 iff zero disagreements. Pinned seed: 18189.
"""
import random
import sys

SEED = 18189
N = 120_000


def shadow(diophantine, default_sort_key, eq, syms, permute):
    """R/I shadow of implementation_diophantine. The A-reference op
    (the recursive canonical solve) is the REAL repo callee."""
    var = list(eq.expand(force=True).free_symbols)
    var.sort(key=default_sort_key)
    syms = [i for i in syms if i in var]
    if syms and syms != var:
        dict_sym_index = dict(zip(syms, range(len(syms))))
        base = diophantine(eq, permute=permute)            # solveCanonical eq permute
        return {tuple(t[dict_sym_index[i]] for i in var) for t in base}
    return diophantine(eq, permute=permute)


def main() -> int:
    from sympy import symbols, default_sort_key
    from sympy.solvers.diophantine import diophantine

    rng = random.Random(SEED)
    # Two variables suffice to exercise the order-dependence bug; symbol names
    # are chosen so that default_sort_key ordering is non-trivial.
    m, n = symbols("m n", integer=True)
    a, b, c = symbols("a b c", integer=True)
    var_pool = [(m, n), (a, b), (n, c)]

    def make_eq(rng):
        x, y = rng.choice(var_pool)
        kind = rng.choice(["sq", "even4", "sq3"])
        # right-hand constant chosen as a sum of two squares/even powers so the
        # equation is solvable and permute produces a rich sign/value family.
        p = rng.randint(1, 4)
        q = rng.randint(1, 4)
        if kind == "sq":
            const = p * p + q * q
            return x ** 2 + y ** 2 - const, (x, y)
        elif kind == "sq3":
            r = rng.randint(1, 3)
            const = p * p + q * q + r * r
            z = rng.choice([c, a, m])
            return x ** 2 + y ** 2 + z ** 2 - const, (x, y, z)
        else:
            const = p ** 4 + q ** 4
            return x ** 4 + y ** 4 - const, (x, y)

    # Deterministic boundary cases first, incl. the exact issue equation.
    fixed = []
    issue_eq = n ** 4 + m ** 4 - 2 ** 4 - 3 ** 4
    fixed.append((issue_eq, (m, n), True))
    fixed.append((issue_eq, (n, m), True))
    fixed.append((issue_eq, (m, n), False))
    fixed.append((m ** 2 + n ** 2 - 25, (n, m), True))
    fixed.append((m ** 2 + n ** 2 - 25, (m, n), True))
    fixed.append((a ** 2 + b ** 2 + c ** 2 - 14, (c, b, a), True))

    disagreements = 0
    examples = []
    checked = 0

    def run_case(eq, syms_tuple, permute):
        nonlocal disagreements
        try:
            want = diophantine(eq, syms=syms_tuple, permute=permute)
        except Exception:
            return  # skip inputs the real solver rejects
        try:
            got = shadow(diophantine, default_sort_key, eq, list(syms_tuple), permute)
        except Exception as e:
            disagreements += 1
            if len(examples) < 10:
                examples.append((eq, syms_tuple, permute, f"<shadow raised {e!r}>", want))
            return
        if set(got) != set(want):
            disagreements += 1
            if len(examples) < 10:
                examples.append((eq, syms_tuple, permute, got, want))

    for eq, syms_tuple, permute in fixed:
        run_case(eq, syms_tuple, permute)
        checked += 1
        if disagreements:
            break

    if not disagreements:
        for _ in range(N):
            eq, base_vars = make_eq(rng)
            order = list(base_vars)
            rng.shuffle(order)
            permute = rng.random() < 0.5
            run_case(eq, tuple(order), permute)
            checked += 1
            if disagreements:
                break

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements (checked={checked})")
        for eq, st, pm, g, w in examples:
            print(f"  eq={eq} syms={st} permute={pm}\n    shadow={g}\n    real  ={w}")
        print("status=fail")
        return 1

    print(f"G-CONF OK: checked={checked} inputs, 0 disagreements (seed={SEED})")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
