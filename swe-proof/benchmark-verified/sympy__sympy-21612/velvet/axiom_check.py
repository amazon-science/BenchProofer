#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-21612.

`Solution.lean` consumes NO opaque axiom (meta.json axioms == []). `DenomFactor`
is a `structure` whose five fields are OBSERVATIONS of a real denominator slot,
and `bracketDenomFactors` is proven purely structurally over whatever
`DenomFactor` values it is given. The kind-A obligation here is an A-REFERENCE
about the OBSERVATION pipeline and about the parts of the rendering the patch
does NOT change — NOT about the operation the patch changes.

IMPORTANT — what G-AX may and may NOT assert here (SPEC_GUIDE §0.7):
  The bracketing GATE is the operation the patch CHANGES
  (`isinstance(item.base, Mul)` -> `isinstance(item.base, (Mul, Pow))`). The
  fidelity of the modeled gate against the *patched* `_print_Mul` is the job of
  G-CONF, which runs with patch.diff APPLIED. G-AX runs against the UNPATCHED
  base_commit source (the harness does NOT apply the patch for G-AX — axioms are
  about callees that behave identically pre/post). So G-AX must assert only what
  is TRUE AT BASE: the observation readings, and the deep model's agreement with
  the real loaded `_print_Mul` on inputs whose bracketing the patch does NOT
  change. Asserting the patched bracket (`(1/y)`) against the base printer
  (which still prints `1/y`) would be unsound — and would be validating the
  changed op against the function under change, which §0.7 forbids.

  The REQUEST-RESOLUTION rule, however, IS unchanged by the patch and therefore
  IS in scope here. The real function satisfies each protective-bracket request
  by wrapping `b_str[b.index(item.base)]` — a value-equality FIRST-occurrence
  lookup applied once per raising slot — and `patch.diff` does not touch that
  line. So the base-commit printer is authoritative about it, and obligation (2)
  below grounds the model's `firstSlotWithKey` / `applyWraps` pipeline against
  the REAL loaded base function on multi-slot denominators that hold EQUAL inner
  expressions. That is the strongest thing G-AX can say here and it is exactly
  the aliasing class an idealized per-slot rendering gets wrong.

This script executes the REAL (base-commit) `sympy` over a wide family of
unevaluated quotients and asserts:

  (1) OBSERVATION SOUNDNESS — the five modeled observations are the real ones,
      for every denominator slot of every generated quotient:
        • for a reciprocal slot, `item.base is item.args[0]` (the factor
          decomposition mapping.md §1 relies on, so
          `len(item.args[0].args) == len(item.base.args)`);
        • `shape`        == the disjoint 3-way `isinstance(value, Mul/Pow/_)`;
        • `components`   == `len(value.args)`;
        • `rendered`     == `self.parenthesize(value, prec, strict=False)`,
                            the UNCHANGED inner sub-render callee;
        • `isReciprocal` == the slot came from the `item.exp is S.NegativeOne`
                            branch (the only slots the real `pow_paren` list can
                            ever hold);
        • `innerKey`     == an identity code that is EQUAL for two slots exactly
                            when the real slot values compare equal — the same
                            equality the real `b.index` lookup uses.

  (2) DEEP-MODEL FIDELITY ON UNCHANGED-BEHAVIOUR INPUTS — for every generated
      quotient in which NO slot's bracketing is changed by the patch (i.e. no
      reciprocal slot has a `power` inner with components != 1; the `product`
      arm, the no-bracket arm, AND the whole request-resolution block are
      byte-identical pre/post), the modeled rendering assembled through
      `_print_Mul`'s unchanged scaffold equals the string the REAL loaded
      base-commit `_print_Mul` produces. The family deliberately includes
      quotients whose denominator slots hold EQUAL inner expressions, so this
      obligation grounds `firstSlotWithKey` + `applyWraps` (one wrap per raising
      slot, all landing on the earliest matching slot) in the real loaded
      function.

  (3) NON-VACUITY OF THE `power` TRIGGER — there EXISTS a slot whose inner is a
      POWER (shape=power, components!=1) for which the MODEL brackets but the
      BASE printer leaves bare. That difference IS the behavioural change the
      patch makes (and which G-CONF, patch applied, confirms the model matches).
      It shows the modeled `power` trigger is not dead. We do NOT assert the
      model equals the base segment on these — at base they legitimately differ.

  (4) NON-VACUITY OF THE RESOLUTION RULE — among the inputs checked by (2) there
      EXISTS one where two slots share an `innerKey` and both raise a request, so
      the model wraps the earliest slot TWICE and leaves the later one bare. Its
      agreement with the base printer in (2) is then a real check of the
      aliasing, not an accident of every slot being distinct.

Imports only `sympy`. Sound at base_commit (no patch needed). Exit 0 iff every
obligation holds.
"""
import random
import sys
import warnings

warnings.filterwarnings("ignore")

from sympy import Symbol, Mul, Pow, Rational, S, Integer, Number
from sympy.core.mul import _keep_coeff
from sympy.printing.str import StrPrinter
from sympy.printing.precedence import precedence


# --- model reference encodings (kept in lock-step with Solution.lean) ---------
def observe_shape(value):
    """`DenomFactor.shape` ↔ type(slot value): product / power / simple."""
    if isinstance(value, Mul):
        return "product"
    if isinstance(value, Pow):
        return "power"
    return "simple"


def shape_is_compound(shape):
    """`shapeIsCompound` — product or power."""
    return shape in ("product", "power")


def needs_brackets(f):
    """`needsBrackets f = f.isReciprocal && (f.components != 1)
                          && shapeIsCompound f.shape` — the PATCHED gate, as the
    model encodes it. (Validated against the patched real gate by G-CONF, NOT
    here.)"""
    return (f["isReciprocal"] and f["components"] != 1
            and shape_is_compound(f["shape"]))


def wrap_text(t):
    """`wrapText`."""
    return "(" + t + ")"


def first_slot_with_key(k, slots):
    """`firstSlotWithKey` — position of the FIRST slot with that innerKey."""
    for i, f in enumerate(slots):
        if f["innerKey"] == k:
            return i
    return len(slots)


def wrap_at(texts, k):
    """`wrapAt`."""
    if k >= len(texts):
        return list(texts)
    out = list(texts)
    out[k] = wrap_text(out[k])
    return out


def bracket_targets(slots):
    """`bracketTargets slots slots` — one entry per raising slot, naming the
    position its inner expression is FOUND at."""
    return [first_slot_with_key(f["innerKey"], slots)
            for f in slots if needs_brackets(f)]


def apply_wraps(texts, ks):
    """`applyWraps` — requests satisfied in order, cumulatively."""
    for k in ks:
        texts = wrap_at(texts, k)
    return texts


def slot_texts(slots):
    """`slotTexts`."""
    return [f["rendered"] for f in slots]


def render_denom_factors(slots):
    """`renderDenomFactors`."""
    return apply_wraps(slot_texts(slots), bracket_targets(slots))


def needs_brackets_prepatch(f):
    """The PRE-PATCH gate (`len(...) != 1 and isinstance(item.base, Mul)`) —
    product-only. Used purely to decide which slots the patch changes, and to
    witness deterministically that the model's patched gate genuinely differs
    from the pre-patch gate on a power slot."""
    return (f["isReciprocal"] and f["components"] != 1
            and f["shape"] == "product")


def patch_changes_slot(f):
    """Does the patch change THIS slot's bracketing? The patch widens the gate
    from `Mul` to `(Mul, Pow)`, so the only slots whose bracketing flips are the
    reciprocal `power` inners with components != 1. Everything else (simple,
    product, non-reciprocal) is byte-identical pre/post and therefore
    authoritative at base_commit."""
    return needs_brackets(f) != needs_brackets_prepatch(f)


# --- read the real slots out of a real quotient, then run the model ----------
def observe_slots(printer, expr):
    """`_print_Mul`'s unchanged gathering scaffold (base-commit source), returning
    the real numerator strings and the five modeled observations of each real
    denominator slot. Every reading comes from the REAL SymPy objects; nothing is
    taken from the real function's `pow_paren` list or its `b.index` lookup (the
    model must decide those itself)."""
    prec = precedence(expr)
    c, e = expr.as_coeff_Mul()
    if c < 0:
        expr = _keep_coeff(-c, e)
        sign = "-"
    else:
        sign = ""
    a = []
    b = []
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
                b.append(apow(item))
                recip.append(False)
            else:
                # observation-soundness invariant the mapping relies on:
                assert item.base is item.args[0], (
                    "factor decomposition broken: item.base is not item.args[0] "
                    "for %r" % (item,))
                assert len(item.args[0].args) == len(item.base.args), (
                    "components observation drift on %r" % (item,))
                b.append(item.base)
                recip.append(True)
        elif item.is_Rational and item is not S.Infinity:
            if item.p != 1:
                a.append(Rational(item.p))
            if item.q != 1:
                b.append(Rational(item.q))
                recip.append(False)
        else:
            a.append(item)
    a = a or [S.One]
    a_str = [printer.parenthesize(x, prec, strict=False) for x in a]
    b_str = [printer.parenthesize(x, prec, strict=False) for x in b]

    # `innerKey`: equal codes exactly when the real slot values compare equal —
    # the same equality the real `b.index(item.base)` lookup uses.
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
    for i in range(len(b)):
        for j in range(len(b)):
            assert (codes[i] == codes[j]) == bool(b[i] == b[j]), (
                "innerKey observation unsound: code equality disagrees with real "
                "slot-value equality at %d/%d in %r" % (i, j, expr))

    slots = [{"rendered": b_str[k],
              "shape": observe_shape(b[k]),
              "components": len(b[k].args),
              "isReciprocal": recip[k],
              "innerKey": codes[k]} for k in range(len(b))]
    return sign, a_str, slots


def model_render(printer, expr):
    """The full string the model produces through `_print_Mul`'s unchanged
    assembly (str.py:358-363), i.e. the deep model embedded in its real caller."""
    sign, a_str, slots = observe_slots(printer, expr)
    b_str = render_denom_factors(slots)
    if not slots:
        return sign + '*'.join(a_str), slots
    elif len(slots) == 1:
        return sign + '*'.join(a_str) + "/" + b_str[0], slots
    else:
        return sign + '*'.join(a_str) + "/(%s)" % '*'.join(b_str), slots


# --- branch guard ------------------------------------------------------------
def is_first_branch(expr):
    """`_print_Mul`'s FIRST arm handles the special unevaluated forms and is not
    the modeled altitude; skip those inputs."""
    args = expr.args
    return (args[0] is S.One) or any(
        isinstance(a, Number) or (a.is_Pow and all(ai.is_Integer for ai in a.args))
        for a in args[1:])


# --- fuzz family -------------------------------------------------------------
def inv(b):
    return Pow(b, -1, evaluate=False)


def sym(rng):
    return rng.choice([Symbol('x'), Symbol('y'), Symbol('z'), Symbol('w')])


def denom_inner(rng):
    r = rng.random()
    if r < 0.28:
        return sym(rng)
    elif r < 0.56:
        return Mul(*[sym(rng) for _ in range(rng.randint(2, 3))], evaluate=False)
    elif r < 0.84:
        return Pow(sym(rng), rng.choice([-1, -2, -3]), evaluate=False)
    else:
        return Pow(sym(rng), rng.choice([2, 3]), evaluate=False)


def make_expr(rng):
    """Denominator slots drawn from a SMALL POOL sampled WITH REPLACEMENT, so
    equal inner expressions recur across slots (the aliasing class), with some
    slots raised to an exponent other than -1 (non-reciprocal slots)."""
    num = []
    if rng.random() < 0.4:
        num.append(Integer(rng.choice([-2, -3, 2, 3])))
    num += [sym(rng) for _ in range(rng.randint(1, 2))]
    n = rng.randint(1, 4)
    pool = [denom_inner(rng) for _ in range(max(1, n - rng.randint(0, 2)))]
    den = []
    for _ in range(n):
        base = rng.choice(pool)
        if rng.random() < 0.2:
            den.append(Pow(base, rng.choice([-2, -3]), evaluate=False))
        else:
            den.append(inv(base))
    return Mul(*(num + den), evaluate=False)


def boundary():
    x, y, z, w = Symbol('x'), Symbol('y'), Symbol('z'), Symbol('w')
    p = inv(Mul(y, z, evaluate=False))          # product inner (unchanged arm)
    g = inv(inv(y))                             # power inner   (changed arm)
    return [
        Mul(x, p, p, evaluate=False),           # DUPLICATE product inners: the
        Mul(x, p, p, p, evaluate=False),        # aliasing class, unchanged
        Mul(x, inv(Mul(y, y, evaluate=False)),
            inv(Mul(y, y, evaluate=False)), evaluate=False),
        Mul(x, inv(Mul(y, z, evaluate=False)),
            inv(Mul(z, y, evaluate=False)), evaluate=False),
        Mul(x, p, inv(y), evaluate=False),
        Mul(x, inv(y), p, evaluate=False),
        Mul(x, inv(y), inv(z), evaluate=False),
        Mul(x, inv(y), evaluate=False),
        Mul(-2, x, inv(Mul(y, y, evaluate=False)), evaluate=False),  # #14160
        Mul(x, inv(Mul(x, y, z, evaluate=False)), evaluate=False),
        Mul(x, Pow(Mul(y, z, evaluate=False), -2, evaluate=False),
            p, evaluate=False),                 # non-reciprocal slot + alias
        Mul(x, w, inv(Mul(y, z, evaluate=False)), evaluate=False),
        Mul(x, g, evaluate=False),              # F2P inner: CHANGED, so (2) skips
        Mul(x, g, g, evaluate=False),           # the reviewer's witness: CHANGED
        Mul(x, inv(Pow(y, 2, evaluate=False)), evaluate=False),
    ]


def main():
    rng = random.Random(21612)
    printers = [StrPrinter(), StrPrinter({'order': 'none'})]

    checked = 0
    unchanged_checked = 0        # inputs whose base string we asserted equal
    saw_power_trigger = False    # (3) non-vacuity of the widened gate
    saw_aliased_request = False  # (4) non-vacuity of the resolution rule, INSIDE
                                 #     the unchanged-behaviour set
    exprs = boundary() + [make_expr(rng) for _ in range(20000)]
    for expr in exprs:
        if is_first_branch(expr):
            continue
        for printer in printers:
            model_str, slots = model_render(printer, expr)
            real_str = printer._print_Mul(expr)     # the REAL loaded function
            checked += 1

            changed = [f for f in slots if patch_changes_slot(f)]
            if not changed:
                # (1)+(2): on inputs the patch does NOT re-bracket, the deep model
                # must reproduce the REAL loaded base-commit string — including the
                # request-resolution behaviour, which the patch leaves untouched.
                assert model_str == real_str, (
                    "A-reference unsound on unchanged-behaviour input %r: model "
                    "%r != real base _print_Mul %r (slots=%r)"
                    % (expr, model_str, real_str, slots))
                unchanged_checked += 1
                # (4): did this input actually exercise the aliasing?
                raising = [f for f in slots if needs_brackets(f)]
                keys = [f["innerKey"] for f in raising]
                if len(keys) != len(set(keys)):
                    saw_aliased_request = True
            else:
                # (3): the patch CHANGES some slot's bracketing (the only such
                # slots are reciprocal power inners with != 1 component). The
                # model gate (patched) brackets them; the pre-patch gate does not.
                # We do NOT compare against the live base string here — base and
                # patched legitimately differ (this difference IS the bug fix;
                # G-CONF validates the model against the PATCHED printer). We only
                # witness, deterministically, that the model encodes the change.
                for f in changed:
                    assert (f["isReciprocal"] and f["shape"] == "power"
                            and f["components"] != 1), (
                        "unexpected changed-slot observation %r" % (f,))
                    assert needs_brackets(f) and not needs_brackets_prepatch(f), (
                        "non-vacuity logic drift on %r" % (f,))
                saw_power_trigger = True

    assert saw_power_trigger, (
        "non-vacuity FAILED: no reciprocal slot with a POWER inner expression "
        "(components != 1) was exercised, so the modeled `power` trigger — the "
        "behavioural change the patch makes — would be dead.")
    assert saw_aliased_request, (
        "non-vacuity FAILED: no unchanged-behaviour input had two raising slots "
        "sharing an innerKey, so obligation (2) never exercised the "
        "request-resolution rule (`firstSlotWithKey` / cumulative `applyWraps`) "
        "and its agreement with the base printer would say nothing about the "
        "aliasing.")

    print("G-AX OK: observation pipeline sound (item.base is item.args[0]; "
          "shape/components/rendered/isReciprocal read from the real slot; "
          "innerKey equality == real slot-value equality) and the deep model "
          "renderDenomFactors, assembled through _print_Mul's unchanged "
          "scaffold, matches the REAL loaded base-commit _print_Mul on %d "
          "unchanged-behaviour quotients out of %d (boundary + 20000 fuzz "
          "quotients, both orderings) — including quotients whose denominator "
          "slots hold EQUAL inner expressions, which grounds the unchanged "
          "request-resolution rule (firstSlotWithKey + cumulative applyWraps) in "
          "the real function; the `power` bracket trigger is non-vacuous (the "
          "model brackets a power inner the base printer leaves bare — the bug "
          "fix, validated against the patched printer by G-CONF)."
          % (unchanged_checked, checked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
