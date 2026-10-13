#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-14248 (nagini).

SHADOW: the impl regions of model.py's `render_sum`, `render_sum_space` and
`render_product`, copied VERBATIM below with the contract calls
(Requires/Ensures/Invariant/Assert) stripped. The @Pure helpers the impls
call (`empty`, `is_neg`, `body`, `sep_plus`, `sep_minus`, `sep_space`,
`star`, `contrib`, `contrib_space`, `lead`) copy over as plain functions;
`PSeq` becomes a small immutable-tuple shim carrying the `take`/`drop`/`+`
operations the helpers use. There are no @ContractOnly callees in this
bundle (mapping.md section 3: all three behaviours are modelled deeply).

ORACLE: the REAL patched repo callees the model models per mapping.md
section 1 — `sympy.printing.str.StrPrinter._print_MatAdd` (for
`render_sum`), `sympy.printing.pretty.pretty.PrettyPrinter._print_MatAdd`
(for `render_sum_space`), and `sympy.printing.str.StrPrinter._print_MatMul`
(for `render_product`), each invoked directly on a default-constructed
printer over generated matrix expressions. The gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed makes the patched
package importable.

Type bridge (mapping.md section 2): each model function's inputs are the
per-child renders plus the structural boolean facts, derived from the SAME
expression the oracle is called on:

  * `render_sum(terms)`: `terms[k]` is the code-point sequence of
    `printer.parenthesize(arg, precedence(expr))` for `expr.args[k]` — the
    exact per-term input the modeled method computes before its join loop.
  * `render_sum_space(terms, negs)`: `terms[k]` is the code-point sequence
    of the single-row picture `printer._print(item)` for `expr.args[k]`
    (the refinement covers flat single-line pictures, mapping.md section 2;
    the generator only builds single-row items and any multi-row draw is
    resampled, never silently passed), and `negs[k]` is the truthiness of
    the structural negativity test `S(item.args[0]).is_negative` on that
    item — a boolean INPUT, not derived from the rendered text
    (mapping.md section 2.2).
  * `render_product(factors, neg)`: `neg` is the truthiness of the
    structural negative-numeric-leading-coefficient test on the product,
    and `factors[k]` is the code-point sequence of
    `printer.parenthesize(arg, precedence(e))` over the args of the
    coefficient-normalised product `e` (the product with the negative
    numeric coefficient folded back positive when `neg`, else the product
    itself) — mapping.md section 2.1.

The model's List[int] result maps back to the returned str via the same
code-point encoding; comparison is exact string equality.

Input domain: the model's Requires demand only list access, >= 1 child,
and len(negs) == len(terms); the bridge feeds exactly the child-render /
boolean inputs the patched repo methods themselves derive, over randomly
generated n-by-n matrix sums and products (1..6 terms; integer / rational /
float / assumption-carrying symbolic coefficients, including the
structurally-negative-yet-no-leading-minus and the
leading-minus-yet-not-structurally-negative regimes, single-child sums and
products, and coefficient -1 folding to an empty-coefficient factor list).
Boundary cases first, then fuzz to >= 1e5 comparisons overall. Pinned fuzz
seed: 1424814248 (recorded here and in the summary line).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys
from typing import List

SEED = 1424814248
N_SUM = 40_000        # render_sum vs the str sum-printer
N_SPACE = 20_000      # render_sum_space vs the pretty sum-printer
N_PROD = 45_000       # render_product vs the str product-printer
N_TOTAL = N_SUM + N_SPACE + N_PROD  # 105_000 >= 1e5


# --- PSeq shim: immutable code-point sequence ---------------------------------

class PSeq(tuple):
    """Immutable sequence literal with the take/drop/+ operations the pure
    helpers use."""
    def __new__(cls, *items):
        return super(PSeq, cls).__new__(cls, items)

    def take(self, n):
        return PSeq(*tuple.__getitem__(self, slice(0, n)))

    def drop(self, n):
        return PSeq(*tuple.__getitem__(self, slice(n, len(self))))

    def __add__(self, other):
        return PSeq(*(tuple(self) + tuple(other)))


def pseq_of(s):
    """Code-point sequence of a str (mapping.md section 2 bijection)."""
    return PSeq(*[ord(ch) for ch in s])


# --- @Pure helpers from model.py, contracts stripped ---------------------------

def empty() -> PSeq:
    """The empty code-point sequence."""
    return PSeq(45).take(0)


def is_neg(t: PSeq) -> bool:
    """A rendered term that already begins with a leading minus (U+002D)."""
    return len(t) > 0 and t[0] == 45


def body(t: PSeq) -> PSeq:
    """The rendered term with a single leading minus stripped, if present."""
    if is_neg(t):
        return t.drop(1)
    return t


def sep_plus() -> PSeq:
    # ' + '
    return PSeq(32, 43, 32)


def sep_minus() -> PSeq:
    # ' - '
    return PSeq(32, 45, 32)


def star() -> PSeq:
    # '*'
    return PSeq(42)


def contrib(t: PSeq) -> PSeq:
    """The infix contribution of one non-leading sum term: a leading-minus
    term becomes ' - '<body>; any other term becomes ' + '<term>."""
    if is_neg(t):
        return sep_minus() + body(t)
    return sep_plus() + body(t)


def lead(t: PSeq) -> PSeq:
    """The leading sum term: a leading-minus term keeps its minus; otherwise
    rendered bare (no infix separator)."""
    if is_neg(t):
        return PSeq(45) + body(t)
    return body(t)


def sep_space() -> PSeq:
    # ' '
    return PSeq(32)


def contrib_space(t: PSeq, n: bool) -> PSeq:
    """The infix contribution of one non-leading sum term under the
    single-space join discipline: a STRUCTURALLY-negative term (the boolean
    fact n, an input alongside the rendered term) becomes ' '<term> (the term
    emitted in full, any minus kept); any other term becomes ' + '<term>.
    The decision is n, NOT a test on the rendered text."""
    if n:
        return sep_space() + t
    return sep_plus() + t


# --- the impl regions of model.py, verbatim, contract calls stripped -----------

def render_sum(terms: List[PSeq]) -> List[int]:
    result = []  # type: List[int]
    i = len(terms)
    while i > 1:
        t = terms[i - 1]
        piece = list(contrib(t))  # type: List[int]
        result = piece + result
        i = i - 1
    t0 = terms[0]
    head = list(lead(t0))  # type: List[int]
    result = head + result
    return result


def render_sum_space(terms: List[PSeq], negs: List[bool]) -> List[int]:
    result = []  # type: List[int]
    i = len(terms)
    while i > 1:
        t = terms[i - 1]
        n = negs[i - 1]
        piece = list(contrib_space(t, n))  # type: List[int]
        result = piece + result
        i = i - 1
    t0 = terms[0]
    head = list(t0)  # type: List[int]
    result = head + result
    return result


def render_product(factors: List[PSeq], neg: bool) -> List[int]:
    result = []  # type: List[int]
    i = len(factors)
    while i > 1:
        t = factors[i - 1]
        piece = list(star() + t)  # type: List[int]
        result = piece + result
        i = i - 1
    t0 = factors[0]
    head = list(t0)  # type: List[int]
    result = head + result
    if neg:
        result = [45] + result
    return result


def to_str(codes: List[int]) -> str:
    return "".join(chr(c) for c in codes)


# --- differential drivers -------------------------------------------------------

def check_sum(env, expr):
    """render_sum vs the real str sum-printer on one matrix sum; returns an
    error string on disagreement, None on agreement."""
    p = env["str_printer"]
    precedence = env["precedence"]
    term_strs = [p.parenthesize(arg, precedence(expr)) for arg in expr.args]
    real = p._print_MatAdd(expr)
    shadow = to_str(render_sum([pseq_of(t) for t in term_strs]))
    if shadow != real:
        return ("DISAGREEMENT (sum join)\n  expr: %r\n  terms: %r"
                "\n  shadow=%r\n  real=%r" % (expr, term_strs, shadow, real))
    return None


def check_space(env, expr):
    """render_sum_space vs the real pretty sum-printer on one matrix sum;
    returns (error-or-None, compared) — compared False when a picture is
    multi-row (outside the flat single-line refinement; caller resamples)."""
    pp = env["pretty_printer"]
    S = env["S"]
    items = []
    negs = []
    for item in expr.args:
        pic = pp._print(item)
        if pic.height() != 1:
            return None, False
        items.append(str(pic))
        negs.append(bool(S(item.args[0]).is_negative))
    real_pic = pp._print_MatAdd(expr)
    if real_pic.height() != 1:
        return None, False
    real = str(real_pic)
    shadow = to_str(render_sum_space([pseq_of(t) for t in items], negs))
    if shadow != real:
        return ("DISAGREEMENT (single-space sum join)\n  expr: %r"
                "\n  items: %r\n  negs: %r\n  shadow=%r\n  real=%r"
                % (expr, items, negs, shadow, real)), True
    return None, True


def check_prod(env, expr):
    """render_product vs the real str product-printer on one matrix product;
    returns an error string on disagreement, None on agreement."""
    p = env["str_printer"]
    precedence = env["precedence"]
    _keep_coeff = env["_keep_coeff"]
    c, m = expr.as_coeff_mmul()
    neg = bool(c.is_number and c < 0)
    e = _keep_coeff(-c, m) if neg else expr
    factor_strs = [p.parenthesize(arg, precedence(e)) for arg in e.args]
    if len(factor_strs) < 1:
        return None  # outside the model's Requires (len(factors) >= 1)
    real = p._print_MatMul(expr)
    shadow = to_str(render_product([pseq_of(f) for f in factor_strs], neg))
    if shadow != real:
        return ("DISAGREEMENT (product sign)\n  expr: %r\n  neg: %r"
                "\n  factors: %r\n  shadow=%r\n  real=%r"
                % (expr, neg, factor_strs, shadow, real))
    return None


# --- expression generators ------------------------------------------------------

def make_env():
    from sympy import MatrixSymbol, Symbol, S, Rational, Float
    from sympy.matrices.expressions.matadd import MatAdd
    from sympy.matrices.expressions.matmul import MatMul
    from sympy.printing.str import StrPrinter
    from sympy.printing.pretty.pretty import PrettyPrinter
    from sympy.printing.precedence import precedence
    from sympy.core.mul import _keep_coeff

    n = Symbol('n', integer=True)
    mats = [MatrixSymbol(nm, n, n) for nm in ("A", "B", "C", "D", "E")]
    y = Symbol('y', negative=True)   # assumption-negative symbolic coeff
    z = Symbol('z', positive=True)
    w = Symbol('w')                  # unknown sign
    # scalar coefficients: identity, positive/negative integers, rationals,
    # floats, and assumption-carrying symbols (y negative, -y positive,
    # 2*y negative) — covering both structural/text agreement and divergence.
    coeffs = [S(1), S(2), S(3), S(-1), S(-2), S(-5),
              Rational(1, 2), Rational(-3, 4), Rational(7, 3),
              Float(2.5), Float(-1.5),
              y, -y, 2 * y, z, -z, w, -w]
    return {
        "MatAdd": MatAdd, "MatMul": MatMul, "S": S,
        "str_printer": StrPrinter(), "pretty_printer": PrettyPrinter(),
        "precedence": precedence, "_keep_coeff": _keep_coeff,
        "mats": mats, "coeffs": coeffs,
    }


def rand_product(env, rng):
    """A random matrix product: scalar coefficient times 1..3 matrix symbols
    (single-row in every printer used here)."""
    mats = env["mats"]
    k = rng.randint(1, 3)
    prod = mats[rng.randrange(len(mats))]
    for _ in range(k - 1):
        prod = prod * mats[rng.randrange(len(mats))]
    if rng.random() < 0.75:
        prod = env["coeffs"][rng.randrange(len(env["coeffs"]))] * prod
    return prod


def rand_sum(env, rng):
    """A random matrix sum of 1..6 product terms (may combine/reorder; the
    bridge reads the constructed node's own child list)."""
    MatAdd = env["MatAdd"]
    k = rng.randint(1, 6)
    terms = [rand_product(env, rng) for _ in range(k)]
    expr = MatAdd(*terms)
    if not isinstance(expr, MatAdd) or len(expr.args) < 1:
        return None
    return expr


def boundary_sums(env):
    """Hand-picked sums: the documented witness shapes, a leading-minus
    first term, an all-negative sum, a single-term sum, and the
    structurally-negative-without-leading-minus regime."""
    from sympy import Symbol
    MatAdd = env["MatAdd"]
    A, B, C = env["mats"][:3]
    y = Symbol('y', negative=True)
    out = []
    for e in [A - A * B - B,
              A * B * C - A * B - B * C,
              -A + y * B,
              y * A + B,
              -A - B - C,
              MatAdd(A),
              MatAdd(-A),
              A + B,
              -(A * B) + A,
              2 * y * A + B]:
        if isinstance(e, MatAdd) and len(e.args) >= 1:
            out.append(e)
    return out


def boundary_prods(env):
    """Hand-picked products: negative/positive numeric coefficients
    (including -1, which folds to a bare factor list), rationals, floats,
    symbolic coefficients of every assumed sign, and single-factor
    products."""
    from sympy import Rational, Float, Symbol
    MatMul = env["MatMul"]
    A, B, C = env["mats"][:3]
    y = Symbol('y', negative=True)
    out = []
    for e in [-A, -A * B, -A * B * C, -2 * A, -3 * A * B,
              Rational(-1, 2) * A, Float(-2.5) * A * B,
              2 * A, Rational(1, 2) * A * B, Float(1.5) * A,
              y * A, -y * A, 2 * y * A * B,
              A, A * B, MatMul(A), MatMul(A, B)]:
        if isinstance(e, MatMul):
            out.append(e)
    return out


def main():
    env = make_env()
    rng = random.Random(SEED)
    checked = {"sum": 0, "space": 0, "prod": 0}

    # Boundary cases first: every hand-picked sum goes through BOTH sum
    # disciplines; every hand-picked product through the product check.
    for expr in boundary_sums(env):
        err = check_sum(env, expr)
        if err:
            print(err)
            return 1
        checked["sum"] += 1
        err, compared = check_space(env, expr)
        if err:
            print(err)
            return 1
        if compared:
            checked["space"] += 1
    for expr in boundary_prods(env):
        err = check_prod(env, expr)
        if err:
            print(err)
            return 1
        checked["prod"] += 1

    # Fuzz: random sums against the str discipline.
    while checked["sum"] < N_SUM:
        expr = rand_sum(env, rng)
        if expr is None:
            continue
        err = check_sum(env, expr)
        if err:
            print(err)
            return 1
        checked["sum"] += 1

    # Fuzz: random sums against the pretty single-space discipline
    # (multi-row draws are resampled, never counted).
    while checked["space"] < N_SPACE:
        expr = rand_sum(env, rng)
        if expr is None:
            continue
        err, compared = check_space(env, expr)
        if err:
            print(err)
            return 1
        if compared:
            checked["space"] += 1

    # Fuzz: random products against the product-sign discipline.
    while checked["prod"] < N_PROD:
        expr = rand_product(env, rng)
        if not isinstance(expr, env["MatMul"]):
            continue
        err = check_prod(env, expr)
        if err:
            print(err)
            return 1
        checked["prod"] += 1

    total = sum(checked.values())
    print("G-CONF OK: shadow impls == real printer methods on %d inputs "
          "(%d spaced-sign sum + %d single-space sum + %d product, seed %d)."
          % (total, checked["sum"], checked["space"], checked["prod"], SEED))
    print(json.dumps({"checked": total, "disagreements": 0, "seed": SEED,
                      "per_function": checked,
                      "shadow": "direct (contract-stripped impl regions)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
