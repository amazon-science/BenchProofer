#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14007.

The conversion of INSERT-returned rows is modeled DEEPLY in Solution.lean by
`convertRows`/`convertRow` (the `pure` region) — an A-reference, NOT a consumed
axiom. This script validates that deep model against the REAL unchanged callee
it abstracts, `SQLCompiler.apply_converters` (django/db/models/sql/compiler.py),
on boundary cases plus randomized fuzzing.

`apply_converters` is reproduced here VERBATIM (it is a small, self-contained
loop with no Django dependency beyond `self.connection`, which the converter
callables receive but, for integer converters, ignore). Running the real method
body — rather than a paraphrase — is what makes this an executable soundness
check. Imports: stdlib only. Exit 0 iff every obligation holds.
"""
import random
import sys

SEED = 14007
N_FUZZ = 20_000


# --- the REAL callee: SQLCompiler.apply_converters, body verbatim ------------
# Source: django/db/models/sql/compiler.py:1110 @ base_commit.
#   def apply_converters(self, rows, converters):
#       connection = self.connection
#       converters = list(converters.items())
#       for row in map(list, rows):
#           for pos, (convs, expression) in converters:
#               value = row[pos]
#               for converter in convs:
#                   value = converter(value, expression, connection)
#               row[pos] = value
#           yield row
# Reproduced as a free function: `converters` is the {pos: (convs, expression)}
# dict get_converters builds; expression/connection are opaque args the
# converters receive (integer converters ignore them).
def real_apply_converters(rows, converters, connection=None):
    converters = list(converters.items())
    out = []
    for row in map(list, rows):
        for pos, (convs, expression) in converters:
            value = row[pos]
            for converter in convs:
                value = converter(value, expression, connection)
            row[pos] = value
        out.append(row)
    return out


# --- the deep model: Solution.lean convertRow / convertRows ------------------
def convert_row(convs, row):
    # convertRow : List (Int -> Int) -> List Int -> List Int
    #   _,        []      => []
    #   [],       v :: vs => v :: vs
    #   f :: fs,  v :: vs => f v :: convertRow fs vs
    out = []
    for j, v in enumerate(row):
        if j < len(convs):
            out.append(convs[j](v))
        else:
            out.append(v)
    return out


def convert_rows(convs, rows):
    return [convert_row(convs, row) for row in rows]


# --- bridge: a Lean `Int -> Int` converter `f` becomes a real converter chain
# entry `(convs=[wrapped], expression)` where `wrapped(value, expr, conn) = f(value)`
# placed at the matching column position. The mapping.md bijection: column j's
# chain is convs[j]. We present the same per-column transform to both sides. ---
def to_real_converters(convs, ncols):
    """Build the {pos: (chain, expression)} dict for columns 0..ncols-1."""
    converters = {}
    for j in range(min(len(convs), ncols)):
        f = convs[j]
        # close over f; the real chain ignores expression/connection
        converters[j] = ([(lambda val, expr, conn, _f=f: _f(val))], object())
    return converters


def check(convs, rows, label):
    ncols = max((len(r) for r in rows), default=0)
    model = convert_rows(convs, rows)
    real = real_apply_converters(rows, to_real_converters(convs, ncols))
    if model != real:
        print(f"G-AX FAIL [{label}]: convs={[c.__name__ for c in convs]} "
              f"rows={rows}\n  model={model}\n  real ={real}", file=sys.stderr)
        return False
    return True


def main():
    rng = random.Random(SEED)
    ok = True
    n_checked = 0

    # named integer converters (model from_db_value / backend converters)
    ident = lambda v: v;          ident.__name__ = "ident"
    inc = lambda v: v + 1;        inc.__name__ = "inc"
    dbl = lambda v: v * 2;        dbl.__name__ = "dbl"
    neg = lambda v: -v;           neg.__name__ = "neg"
    sq = lambda v: v * v;         sq.__name__ = "sq"
    POOL = [ident, inc, dbl, neg, sq]

    # boundary cases
    boundary = [
        ([], []),                                  # empty everything
        ([], [[1, 2, 3]]),                         # no converters -> identity
        ([ident], []),                             # converters but no rows
        ([inc], [[10]]),                           # single column, single row
        ([inc, dbl], [[1, 2], [3, 4], [5, 6]]),    # multi-col, multi-row
        ([inc], [[1, 2, 3]]),                      # short converter list (cols 1,2 pass)
        ([inc, dbl, neg], [[7]]),                  # converter list longer than row
        ([ident, ident], [[0, 0], [-1, -1]]),      # negatives, zeros
        ([dbl], [[2**31], [-(2**31)]]),            # large ints
    ]
    for convs, rows in boundary:
        ok &= check(convs, rows, "boundary")
        n_checked += 1

    # randomized fuzz
    for _ in range(N_FUZZ):
        ncols = rng.randint(0, 4)
        nconvs = rng.randint(0, ncols + 1)   # sometimes shorter, sometimes longer
        convs = [rng.choice(POOL) for _ in range(nconvs)]
        nrows = rng.randint(0, 4)
        rows = [[rng.randint(-1000, 1000) for _ in range(ncols)] for _ in range(nrows)]
        ok &= check(convs, rows, "fuzz")
        n_checked += 1
        if not ok:
            break

    if ok:
        print(f"G-AX OK: convertRows deep model == real apply_converters on "
              f"{len(boundary)} boundary + {N_FUZZ} fuzz cases (seed={SEED}). "
              f"No consumed axioms.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
