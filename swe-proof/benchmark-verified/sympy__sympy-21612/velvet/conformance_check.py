#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-21612 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `bracketDenomFactors` impl
              region, transliterated to Python over the real repo carrier. The
              modeled altitude is the WHOLE denominator-slot rendering step: the
              shadow reads the five observations of each denominator slot
              (`rendered`, `shape`, `components`, `isReciprocal`, `innerKey`)
              from the REAL SymPy objects (the A-reference observations, left as
              the real `self.parenthesize` / `type` / `len(args)`), and then
              computes the slot texts with `renderDenomFactors` — the model's own
              request/resolution pipeline (`bracketTargets` locating each request
              by `firstSlotWithKey`, `applyWraps` folding them in order).
              CRITICALLY, the shadow does NOT reuse the real function's
              `pow_paren` list or its `b.index(item.base)` lookup: that lookup is
              precisely the behaviour the model claims to reproduce, so borrowing
              it would make this check tautological. Instead the shadow builds its
              own `isReciprocal` flags and its own `innerKey` identity codes from
              the slot values and lets the transliterated model decide both WHICH
              slots raise a request and WHERE each request lands. The surrounding
              `_print_Mul` machinery (numerator/denominator gathering, sign, the
              `'%s/(%s)'` join) is the function's UNCHANGED scaffold and is
              reproduced verbatim from the base-commit source so that the only
              modeled difference is the slot-rendering step.
  * ORACLE  — `patch.diff`'s behaviour: the patched `StrPrinter._print_Mul`,
              run in-process on the same expressions (the harness applies
              patch.diff to /testbed before this script runs). The real
              correctness oracle (G-RESOLVE).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

The fuzz family is deliberately heavy on DUPLICATE inner expressions (a pool of
inners is sampled WITH REPLACEMENT for the denominator slots) because that is the
input class the request-resolution rule is about: the real function wraps
`b_str[b.index(item.base)]`, a value-equality FIRST-occurrence lookup applied once
per raising slot, so N slots holding equal inner expressions wrap the earliest
slot N times and leave the later ones bare. A fuzz family of distinct inners would
not separate the model's `firstSlotWithKey` resolution from an idealized per-slot
map, and this check would pass while the spec drifted. Non-reciprocal denominator
slots (`apow(item)` results for exponents other than -1, and `Rational(item.q)`
denominators) are also generated, since they never raise a request.

stdlib + sympy only. The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict. Runs in-process; no DB, no network.
"""
import random
import sys
import warnings

warnings.filterwarnings("ignore")

from sympy import Symbol, Mul, Pow, Rational, S, Integer, Number
from sympy.core.mul import _keep_coeff
from sympy.printing.str import StrPrinter
from sympy.printing.precedence import precedence

SEED = 21612
N_FUZZ = 100_000


# --- A-reference observations: read from the REAL SymPy slot object -----------
def observe_shape(value):
    """`DenomFactor.shape` ↔ type(slot value): product / power / simple."""
    if isinstance(value, Mul):
        return "product"
    if isinstance(value, Pow):
        return "power"
    return "simple"


# --- SHADOW side: Solution.lean's PURE SURFACE, transliterated ----------------
# One function per Lean `def`, same names, same recursion. Nothing here reads a
# SymPy object; the observations are handed in as plain values.
def shape_is_compound(shape):
    """`shapeIsCompound` — product or power."""
    return shape in ("product", "power")


def needs_brackets(f):
    """`needsBrackets f = f.isReciprocal && (f.components != 1)
                          && shapeIsCompound f.shape`."""
    return (f["isReciprocal"] and f["components"] != 1
            and shape_is_compound(f["shape"]))


def wrap_text(t):
    """`wrapText t = "(" ++ t ++ ")"`."""
    return "(" + t + ")"


def first_slot_with_key(k, slots):
    """`firstSlotWithKey` — the position of the FIRST slot with that innerKey,
    or past the end (== length) when no slot has it."""
    for i, f in enumerate(slots):
        if f["innerKey"] == k:
            return i
    return len(slots)


def wrap_at(texts, k):
    """`wrapAt` — wrap the text at position `k`; a position past the end wraps
    nothing."""
    if k >= len(texts):
        return list(texts)
    out = list(texts)
    out[k] = wrap_text(out[k])
    return out


def bracket_targets(slots):
    """`bracketTargets slots slots` — one entry per raising slot, each naming the
    position its inner expression is FOUND at (not the position it was raised
    from), in slot order."""
    return [first_slot_with_key(f["innerKey"], slots)
            for f in slots if needs_brackets(f)]


def apply_wraps(texts, ks):
    """`applyWraps` — satisfy the requests in order against the text produced so
    far, so two requests naming the same position wrap that text twice."""
    for k in ks:
        texts = wrap_at(texts, k)
    return texts


def slot_texts(slots):
    """`slotTexts` — the slots' own rendered texts, before any request."""
    return [f["rendered"] for f in slots]


def render_denom_factors(slots):
    """`renderDenomFactors slots
          = applyWraps (slotTexts slots) (bracketTargets slots slots)`."""
    return apply_wraps(slot_texts(slots), bracket_targets(slots))


# --- SHADOW: the model routed into _print_Mul's unchanged scaffold ------------
def shadow_print_mul(printer, expr):
    """`_print_Mul`'s unchanged scaffold (base-commit source) with the modeled
    denominator-slot rendering (`renderDenomFactors`, reading the A-reference
    observations from the real slot objects) substituted for the real function's
    `pow_paren` / `b.index` wrap block. This is the R/I shadow of
    `bracketDenomFactors` embedded in its real caller."""
    prec = precedence(expr)
    c, e = expr.as_coeff_Mul()
    if c < 0:
        expr = _keep_coeff(-c, e)
        sign = "-"
    else:
        sign = ""
    a = []
    b = []
    # Parallel to `b`: whether the slot arose as the RECIPROCAL of its value
    # (`DenomFactor.isReciprocal`). Built by the shadow itself rather than read
    # off the real `pow_paren` list — the point of this check is that the model
    # decides which slots raise a request.
    recip = []
    if printer.order not in ('old', 'none'):
        args = expr.as_ordered_factors()
    else:
        args = Mul.make_args(expr)

    def apow(i):
        bb, ee = i.as_base_exp()
        eargs = list(Mul.make_args(ee))
        if eargs[0] is S.NegativeOne:
            eargs = eargs[1:]
        else:
            eargs[0] = -eargs[0]
        ee = Mul._from_args(eargs)
        if isinstance(i, Pow):
            return i.func(bb, ee, evaluate=False)
        return i.func(ee, evaluate=False)

    for item in args:
        if (item.is_commutative and isinstance(item, Pow)
                and bool(item.exp.as_coeff_Mul()[0] < 0)):
            if item.exp is not S.NegativeOne:
                # a denominator slot that did NOT arise as a reciprocal
                b.append(apow(item))
                recip.append(False)
            else:
                b.append(item.base)
                recip.append(True)
        elif item.is_Rational and item is not S.Infinity:
            if item.p != 1:
                a.append(Rational(item.p))
            if item.q != 1:
                # likewise non-reciprocal
                b.append(Rational(item.q))
                recip.append(False)
        else:
            a.append(item)
    a = a or [S.One]
    a_str = [printer.parenthesize(x, prec, strict=False) for x in a]
    b_str = [printer.parenthesize(x, prec, strict=False) for x in b]

    # === the modeled op: build the DenomFactor observations, run the model ====
    # `innerKey` is an identity code for the slot's VALUE: two slots get the same
    # code exactly when their values compare equal (`==` on SymPy objects, the
    # same equality `list.index` uses). Assigned by first occurrence.
    codes = []
    reps = []
    for v in b:
        code = None
        for i, r in enumerate(reps):
            if r == v:
                code = i
                break
        if code is None:
            code = len(reps)
            reps.append(v)
        codes.append(code)
    slots = [{"rendered": b_str[k],
              "shape": observe_shape(b[k]),
              "components": len(b[k].args),
              "isReciprocal": recip[k],
              "innerKey": codes[k]} for k in range(len(b))]
    b_str = render_denom_factors(slots)
    # =========================================================================

    if not b:
        return sign + '*'.join(a_str)
    elif len(b) == 1:
        return sign + '*'.join(a_str) + "/" + b_str[0]
    else:
        return sign + '*'.join(a_str) + "/(%s)" % '*'.join(b_str)


# --- ORACLE: patch.diff's behaviour, the real patched _print_Mul -------------
def oracle_print_mul(printer, expr):
    return printer._print_Mul(expr)


# --- branch guard ------------------------------------------------------------
def is_first_branch(expr):
    """`_print_Mul` has TWO arms (str.py:258). The FIRST arm handles the special
    unevaluated forms (leading `One`, any `Number` in args[1:], or an
    integer-base/integer-exp `Pow` factor) and is NOT touched by the patch — the
    edited gate lives only in the MAIN (second) arm. The modeled function
    `bracketDenomFactors` is the main arm's denominator-slot rendering, so G-CONF
    compares main-arm inputs only (where the patch's behaviour lives; the F2P
    and #14160 anchors both route here). Inputs that hit the first arm are
    out of the modeled altitude and skipped."""
    args = expr.args
    return (args[0] is S.One) or any(
        isinstance(a, Number) or (a.is_Pow and all(ai.is_Integer for ai in a.args))
        for a in args[1:])


# --- fuzzed unevaluated Mul expressions with reciprocal denominators ---------
def inv(b):
    return Pow(b, -1, evaluate=False)


def sym(rng):
    return rng.choice([Symbol('x'), Symbol('y'), Symbol('z'), Symbol('w')])


def denom_inner(rng):
    """An inner expression for a denominator slot, ranging over the three shapes
    the bracketing predicate distinguishes. Symbol-based so the host `Mul` stays
    on the patched MAIN arm (no Numbers / integer-base powers in the non-leading
    factors)."""
    r = rng.random()
    if r < 0.28:                      # simple
        return sym(rng)
    elif r < 0.56:                    # product (≥2 components)
        k = rng.randint(2, 3)
        return Mul(*[sym(rng) for _ in range(k)], evaluate=False)
    elif r < 0.84:                    # power, negative exponent (symbol base, so
        ex = rng.choice([-1, -2, -3])  # inv(power) is not an int-base int-exp Pow)
        return Pow(sym(rng), ex, evaluate=False)
    else:                             # power, positive exponent
        return Pow(sym(rng), rng.choice([2, 3]), evaluate=False)


def make_expr(rng):
    """A quotient whose denominator slots are drawn from a SMALL POOL of inners
    sampled WITH REPLACEMENT, so equal inner expressions recur across slots — the
    input class the request-resolution rule is about. Some slots are raised with
    an exponent other than -1, which makes them NON-reciprocal denominator slots
    that raise no request."""
    num = []
    if rng.random() < 0.4:
        # leading factor may be a negative integer coefficient (args[0], not
        # checked by the first-arm test) to exercise the sign path.
        num.append(Integer(rng.choice([-2, -3, 2, 3])))
    num += [sym(rng) for _ in range(rng.randint(1, 2))]
    n = rng.randint(1, 4)
    pool = [denom_inner(rng) for _ in range(max(1, n - rng.randint(0, 2)))]
    den = []
    for _ in range(n):
        base = rng.choice(pool)                 # REUSE -> duplicate inners
        if rng.random() < 0.2:
            # exponent != -1: a non-reciprocal slot (the real `apow` path)
            den.append(Pow(base, rng.choice([-2, -3]), evaluate=False))
        else:
            den.append(inv(base))
    return Mul(*(num + den), evaluate=False)


def fuzz_cases(n, rng):
    x, y, z, w = Symbol('x'), Symbol('y'), Symbol('z'), Symbol('w')
    f = inv(Mul(y, z, evaluate=False))
    g = inv(inv(y))
    # boundary cases first (plan §4.1 step 4) — the F2P + #14160 anchors, plus the
    # equal-inner points where an idealized per-slot rendering diverges from the
    # real first-occurrence resolution.
    yield Mul(x, f, f, evaluate=False)             # x/((((y*z)))*(y*z))
    yield Mul(x, g, g, evaluate=False)             # x/(((1/y))*1/y)
    yield Mul(x, f, f, f, evaluate=False)          # three co-targeted requests
    yield Mul(x, inv(inv(y)), evaluate=False)                       # x/(1/y) (F2P)
    yield Mul(x, inv(y), evaluate=False)                           # x/y
    yield Mul(x, inv(Mul(y, z, evaluate=False)), evaluate=False)   # x/((y*z))
    yield Mul(-2, x, inv(Mul(y, y, evaluate=False)),
              evaluate=False)                                      # -2*x/(y*y) (#14160)
    yield Mul(x, inv(Pow(y, 2, evaluate=False)), evaluate=False)   # x/(y**2)
    yield Mul(x, inv(y), inv(z), evaluate=False)
    yield Mul(x, inv(inv(y)), inv(inv(z)), evaluate=False)
    yield Mul(x, z, inv(inv(y)), evaluate=False)
    yield Mul(x, inv(inv(y)), inv(Mul(z, w, evaluate=False)), evaluate=False)
    # a non-reciprocal slot aliasing a reciprocal one, both orderings
    yield Mul(x, Pow(y, -2, evaluate=False), inv(Pow(y, 2, evaluate=False)),
              evaluate=False)
    yield Mul(x, inv(Pow(y, 2, evaluate=False)), Pow(y, -2, evaluate=False),
              evaluate=False)
    # equal-valued inners written in different factor orders
    yield Mul(x, inv(Mul(y, z, evaluate=False)), inv(Mul(z, y, evaluate=False)),
              evaluate=False)
    for _ in range(n):
        yield make_expr(rng)


def main():
    rng = random.Random(SEED)
    printers = [StrPrinter(), StrPrinter({'order': 'none'})]
    fails = 0
    checked = 0
    skipped = 0
    for expr in fuzz_cases(N_FUZZ, rng):
        if is_first_branch(expr):
            skipped += 1
            continue
        for printer in printers:
            shadow = shadow_print_mul(printer, expr)
            oracle = oracle_print_mul(printer, expr)
            checked += 1
            if shadow != oracle:
                fails += 1
                if fails <= 10:
                    print("DISAGREE expr=%r shadow=%r oracle=%r"
                          % (expr, shadow, oracle), file=sys.stderr)
    if fails:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs (seed %d)."
              % (fails, checked, SEED), file=sys.stderr)
        return 1
    print("G-CONF OK: R/I shadow of bracketDenomFactors (renderDenomFactors "
          "transliterated over the real slot observations, in _print_Mul's "
          "main-arm scaffold, WITHOUT reusing the real pow_paren/b.index wrap "
          "block) agrees with patch.diff behaviour on %d inputs (seed=%d), 0 "
          "disagreements (%d first-arm inputs skipped — out of modeled "
          "altitude)." % (checked, SEED, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
