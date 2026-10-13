#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_evalf against
the patch.diff behaviour (the post-patch numeric evaluation of a function-
application expression tree).

The impl region has R/I content (the accumulator `for` loop over the argument
subexpressions, with an early `none`-abort and a final apply-implementation step,
recursing structurally into each argument). This runs a real fuzz.

The shadow reproduces the Lean impl's control flow op-for-op:
    eval(num n)  = n
    eval(atom)   = none                         (a bare symbol has no value)
    eval(app f args):
        vals = []                               -- let mut vals := []
        for a in args:                          -- for a in args.attach
            v = eval(a)                          --   recurse on the argument
            if v is None: return None            --   early return none
            vals.append(v)                       --   vals := vals ++ [v]
        return f(vals)                           -- return some (f vals)

The patched side is an INDEPENDENT reconstruction built on the real repo: each
modeled node is a genuine `implemented_function` whose `_imp_` is a strict linear
form, assembled into a real SymPy expression tree; the POST-patch `_eval_evalf`
recurses into the arguments (`Float(self._imp_(*[i.evalf(prec) for i in
self.args]), prec)`), so `expr.evalf()` returns a numeric `Float` exactly when
every leaf is numeric. We bridge that `Float` back to an integer and compare to
the shadow.

Type bijection (see mapping.md): the Lean `Expr` tree ↔ a SymPy expression tree
over `Integer` leaves, a single free `Symbol` for `atom`, and
`implemented_function` application nodes; `Option Int` result `some n` ↔ a numeric
`Float` equal to `n`, `none` ↔ a result that is still symbolic (`not is_number`).

Modeling assumption (mapping.md): the node implementations modeled are STRICT in
every argument — the result is numeric iff every argument is numeric. The
demonstrated cases (`lambda x: x**2`, `lambda x: 2*x`) are strict; we fuzz with
strict linear node implementations (fixed nonzero coefficients + offset) so no
multiplicative annihilation or order simplification can make a symbolic argument
disappear. This is exactly the behavior the modeled branch (recursive `_imp_`)
produces.

stdlib + sympy only. exit 0 iff zero disagreements over >=10^5 fuzzed trees.
"""
import random
import sys

SEED = 12096          # pinned in mapping.md
N = 120_000           # >= 10^5

try:
    from sympy import Integer, Symbol
    from sympy.utilities.lambdify import implemented_function
except Exception as e:  # pragma: no cover
    print(f"G-CONF ERROR: sympy unavailable: {e}")
    sys.exit(2)

X = Symbol('x')

# Strict linear node implementations: result = offset + sum(coef_i * arg_i),
# coefficients cycling through a fixed nonzero tuple so EVERY argument is used.
COEFS = {
    'A': (1, (1, 1, 1)),
    'B': (5, (2, 3, 4)),
    'C': (0, (1, 2, 3)),
    'D': (-7, (3, 1, 2)),
}


def lean_node(k, vs):
    off, cs = COEFS[k]
    return off + sum(cs[i % len(cs)] * v for i, v in enumerate(vs))


def _make_imp(k):
    off, cs = COEFS[k]

    def imp(*a):
        return off + sum(cs[i % len(cs)] * a[i] for i in range(len(a)))

    return imp


SYM = {k: implemented_function('N' + k, _make_imp(k)) for k in COEFS}


def gen(rng, depth):
    if depth <= 0 or rng.random() < 0.4:
        if rng.random() < 0.25:
            return ('atom',)
        return ('num', rng.randint(-30, 30))
    k = rng.choice(list(COEFS))
    n = rng.randint(1, 3)
    return ('app', k, [gen(rng, depth - 1) for _ in range(n)])


def shadow(t):
    """R/I shadow of implementation_evalf (Option Int as Python int|None)."""
    if t[0] == 'num':
        return t[1]
    if t[0] == 'atom':
        return None
    vals = []
    for a in t[2]:
        v = shadow(a)
        if v is None:
            return None
        vals.append(v)
    return lean_node(t[1], vals)


def to_sympy(t):
    if t[0] == 'num':
        return Integer(t[1])
    if t[0] == 'atom':
        return X
    return SYM[t[1]](*[to_sympy(a) for a in t[2]])


def patched(t):
    """Independent reconstruction of POST-patch evalf on the real expression
    tree: numeric Float iff fully numeric, else symbolic (-> None)."""
    sv = to_sympy(t).evalf()
    if sv.is_number:
        return int(round(float(sv)))
    return None


def fixed_cases():
    # Boundary/regression cases, incl. the F2P discriminator: a nested
    # application of an implemented function (f(f(2))) must evaluate.
    return [
        ('num', 7),
        ('atom',),
        ('app', 'A', [('num', 2)]),
        ('app', 'A', [('app', 'A', [('num', 2)])]),         # nested -> must eval
        ('app', 'B', [('app', 'C', [('num', 2)])]),         # f(g(2)) shape
        ('app', 'A', [('atom',)]),                          # symbolic arg -> None
        ('app', 'B', [('num', 1), ('atom',), ('num', 3)]),  # one symbolic -> None
        ('app', 'D', [('app', 'A', [('num', 4), ('num', 5)]),
                      ('app', 'B', [('num', 6)])]),
    ]


def main() -> int:
    rng = random.Random(SEED)
    # depth 3 still exercises nested compositions (f(g(h(.)))) — the core fix —
    # while keeping the SymPy oracle within the container budget over >=10^5 trees.
    cases = fixed_cases() + [gen(rng, 3) for _ in range(N)]

    disagreements = 0
    examples = []
    for t in cases:
        got = shadow(t)
        want = patched(t)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((t, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for t, g, w in examples:
            print(f"  tree={t} shadow={g} patched={w}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
