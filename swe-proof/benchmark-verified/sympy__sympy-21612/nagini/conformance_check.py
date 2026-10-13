#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-21612 (nagini).

SHADOW  — the impl region of model.py, copied VERBATIM below with the
          contract calls (Requires/Ensures/Invariant) stripped; the @Pure
          helpers `is_composite_form` / `needs_brackets` and the `Factor`
          carrier copy over as plain Python. No @ContractOnly callees and no
          PSeq usage in this bundle.

BRIDGE  — mapping.md section 2: each reciprocal denominator factor maps to a
          Factor with `parts` = the part count of the reciprocated quantity
          and `form` = its structural-form tag (product <-> 1, power <-> 2,
          anything else <-> 0). The quotient-rendering scaffolding AROUND
          the modeled decision (factor ordering, sign handling,
          numerator/denominator gathering, per-item rendering and joining,
          and the first-occurrence wrapping pass that consumes the flags) is
          unchanged by the patch; the bridge replays it verbatim from the
          repo source, with the per-factor bracket decision replaced by the
          shadow's flag list. The assembled text is compared to the real
          printer's output with `==` — the only logic that can differ is
          the modeled decision.

ORACLE  — the REAL patched textual printer (PYTHONPATH=/testbed, gold patch
          applied by the gate before this script runs): the product-printing
          method of the string printer, invoked through doprint on freshly
          constructed product expressions with reciprocal denominator
          factors of every structural kind.

Input domain: the modeled preconditions demand only read access to the
factor list (parts >= 0, form >= 0 hold by construction of the facets), so
every gathered factor run is Requires-satisfying. Expressions vary the
numerator factors (symbols, sums, applied functions, signed coefficients)
and the denominator factors (atomic reciprocals; reciprocals of products,
of powers, of reciprocals — the issue's shape; of sums; of function
applications; multi-part unevaluated products; repeated factors; negative
non-unit exponents that take the other gathering branch).

>= 1e5 Requires-satisfying inputs: boundary expressions + fuzz expressions
until 100000 comparisons. Pinned seed: 21612.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the repo package only.
"""
import random
import sys

SEED = 21612
N_TARGET = 100_000

# ---------------------------------------------------------------------------
# model.py carrier + pure region + impl region, VERBATIM with contract
# statement lines (Requires/Ensures/Invariant) stripped.
# ---------------------------------------------------------------------------


class Factor:
    def __init__(self, parts, form):
        self.parts = parts
        self.form = form


def is_composite_form(form):
    return form == 1 or form == 2


def needs_brackets(parts, form):
    return parts != 1 and is_composite_form(form)


def bracket_flags(factors):
    result = []
    i = 0
    while i < len(factors):
        f = factors[i]
        flag = f.parts != 1 and (f.form == 1 or f.form == 2)
        result.append(flag)
        i = i + 1
    return result


# ---------------------------------------------------------------------------
# Bridge: replay the unchanged rendering scaffolding with the modeled
# decision supplied by the shadow (facet extraction per mapping.md sec. 2).
# ---------------------------------------------------------------------------


def form_tag(base, Mul, Pow):
    if isinstance(base, Mul):
        return 1
    if isinstance(base, Pow):
        return 2
    return 0


def shadow_print_mul(printer, expr):
    """The product-printing body with the per-factor bracket decision
    replaced by the shadow's flag list; everything else is the unchanged
    scaffolding replayed verbatim. Returns None when the expression takes
    the special early branch that never reaches the modeled decision."""
    from sympy import S, Mul, Pow, Rational, Number
    from sympy.core.function import _coeff_isneg
    from sympy.core.mul import _keep_coeff
    from sympy.printing.precedence import precedence

    prec = precedence(expr)

    args = expr.args
    if args[0] is S.One or any(
            isinstance(a, Number) or
            a.is_Pow and all(ai.is_Integer for ai in a.args)
            for a in args[1:]):
        return None  # early branch: the modeled decision is not reached

    c, e = expr.as_coeff_Mul()
    if c < 0:
        expr = _keep_coeff(-c, e)
        sign = "-"
    else:
        sign = ""

    a = []  # items in the numerator
    b = []  # items that are in the denominator (if any)

    recip_items = []   # reciprocal denominator items, in factor order
    facets = []        # the corresponding Factor carriers

    if printer.order not in ('old', 'none'):
        args = expr.as_ordered_factors()
    else:
        args = Mul.make_args(expr)

    def apow(i):
        b, e = i.as_base_exp()
        eargs = list(Mul.make_args(e))
        if eargs[0] is S.NegativeOne:
            eargs = eargs[1:]
        else:
            eargs[0] = -eargs[0]
        e = Mul._from_args(eargs)
        if isinstance(i, Pow):
            return i.func(b, e, evaluate=False)
        return i.func(e, evaluate=False)

    for item in args:
        if (item.is_commutative and
                isinstance(item, Pow) and
                bool(item.exp.as_coeff_Mul()[0] < 0)):
            if item.exp is not S.NegativeOne:
                b.append(apow(item))
            else:
                # facet extraction replaces the in-line guard; the decision
                # itself is taken by the shadow below
                recip_items.append(item)
                facets.append(Factor(len(item.args[0].args),
                                     form_tag(item.base, Mul, Pow)))
                b.append(item.base)
        elif item.is_Rational and item is not S.Infinity:
            if item.p != 1:
                a.append(Rational(item.p))
            if item.q != 1:
                b.append(Rational(item.q))
        else:
            a.append(item)

    # SHADOW DECISION: one flag per reciprocal factor, in factor order
    flags = bracket_flags(facets)
    pow_paren = [item for item, fl in zip(recip_items, flags) if fl]

    a = a or [S.One]

    a_str = [printer.parenthesize(x, prec, strict=False) for x in a]
    b_str = [printer.parenthesize(x, prec, strict=False) for x in b]

    # unchanged first-occurrence wrapping pass consuming the flags
    for item in pow_paren:
        if item.base in b:
            b_str[b.index(item.base)] = "(%s)" % b_str[b.index(item.base)]

    if not b:
        return sign + '*'.join(a_str)
    elif len(b) == 1:
        return sign + '*'.join(a_str) + "/" + b_str[0]
    else:
        return sign + '*'.join(a_str) + "/(%s)" % '*'.join(b_str)


# ---------------------------------------------------------------------------
# Expression generation.
# ---------------------------------------------------------------------------


def build_pools():
    from sympy import symbols, Function, Pow, Mul
    x, y, z, w = symbols("x y z w")
    f = Function("f")
    numerators = [
        x, y, z, w, x + y, x + y + z, f(x), f(x, y), x + 1,
    ]

    def recip(base):
        return Pow(base, -1, evaluate=False)

    denominators = [
        Pow(x, -1),                                    # atomic
        Pow(z, -1),
        recip(x * y),                                  # product, 2 parts
        recip(x * y * z),                              # product, 3 parts
        recip(Pow(y, -1)),                             # reciprocal-of-reciprocal
        recip(Pow(w, -1)),
        recip(Pow(y, 2)),                              # power, 2 parts
        recip(Pow(x + y, 3)),
        recip(x + y),                                  # sum: 2 parts, non-composite form
        recip(f(x)),                                   # applied function: 1 part
        recip(f(x, y)),                                # applied function: 2 parts
        recip(Mul(y, y, evaluate=False)),              # repeated-part product
        recip(Mul(x, y, evaluate=False)),
        Pow(z, -2),                                    # non-unit negative exp branch
        Pow(x + y, -2),
    ]
    return numerators, denominators


def gen_expr(rng, numerators, denominators):
    from sympy import Mul, Integer
    n_num = rng.randint(1, 3)
    n_den = rng.randint(1, 3)
    facs = [rng.choice(numerators) for _ in range(n_num)]
    facs += [rng.choice(denominators) for _ in range(n_den)]
    rng.shuffle(facs)
    if rng.random() < 0.25:
        coeff = rng.choice([-7, -3, -1, 2, 3, 5])
        facs = [Integer(coeff)] + facs
    return Mul(*facs, evaluate=False)


def boundary_exprs():
    from sympy import symbols, Pow, Mul
    x, y = symbols("x y")
    return [
        # the issue's shape: a reciprocal-of-a-reciprocal denominator factor
        Mul(x, Pow(Pow(y, -1), -1, evaluate=False), evaluate=False),
        # the repeated-part product shape (issue #14160's neighbourhood)
        Mul(-2, x, Pow(Mul(y, y, evaluate=False), -1, evaluate=False),
            evaluate=False),
        Mul(x, Pow(y, -1), evaluate=False),
        Mul(x, Pow(x * y, -1), evaluate=False),
        Mul(x, Pow(x + y, -1), evaluate=False),
        Mul(x, Pow(Pow(y, 2), -1, evaluate=False), evaluate=False),
        Mul(x, Pow(Pow(y, -1), -1, evaluate=False),
            Pow(Pow(y, -1), -1, evaluate=False), evaluate=False),
    ]


def main():
    from sympy import Mul
    from sympy.printing.str import StrPrinter

    printer = StrPrinter()
    rng = random.Random(SEED)
    numerators, denominators = build_pools()

    checked = 0
    skipped = 0

    def run_one(expr):
        nonlocal checked, skipped
        if not isinstance(expr, Mul):
            skipped += 1
            return None
        shadow = shadow_print_mul(printer, expr)
        if shadow is None:
            skipped += 1
            return None
        real = printer.doprint(expr)
        if shadow != real:
            return ("DISAGREEMENT\n  expr=%s\n  shadow=%r\n  real=%r"
                    % (repr(expr), shadow, real))
        checked += 1
        return None

    for expr in boundary_exprs():
        err = run_one(expr)
        if err:
            print("G-CONF FAIL (seed=%d):" % SEED)
            print(err)
            return 1

    while checked < N_TARGET:
        err = run_one(gen_expr(rng, numerators, denominators))
        if err:
            print("G-CONF FAIL (seed=%d):" % SEED)
            print(err)
            return 1

    print("G-CONF OK: model.py impl shadow (bracket decision) composed with "
          "the unchanged rendering scaffolding agrees with the real patched "
          "printer on %d product expressions (%d skipped as out-of-region, "
          "seed=%d), 0 disagreements." % (checked, skipped, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
