#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-22080 (nagini).

Refutes (never proves) the refinement leg no other gate covers: does the MODEL
in model.py actually agree with the REAL patched repository code it claims to
model?  G-VERIFY says the impl meets the spec and G-PBT says no wrong impl meets
it; neither one ever imports sympy.  See mapping.md "## G-CONF".

SHADOW -- the impl regions of model.py, copied VERBATIM below, plus the `@Pure`
helpers they call (also verbatim).  Nothing is restructured, renamed or
"simplified": a shadow that paraphrases the impl would only test the paraphrase.
The three modeled functions are

    remainder_operand_level()               -> return level_multiplicative()
    negated_single_operand_enclosed(lvl)    -> return encloses(lvl, leading_minus_cutoff(), False)
    negated_remainder_is_enclosed()         -> s = remainder_operand_level(); ...

and the copied pure dependencies are level_additive/level_multiplicative/
level_power/level_function/encloses/leading_minus_cutoff.  Only contract calls
are deleted (`Requires`/`Ensures`/`MustTerminate`, and `leading_minus_cutoff`'s
`Ensures`); no other token of the impl regions changed.

  * No PSeq/ToSeq shim is needed: the impl regions carry no sequence values at
    all (the model's carrier is a small ordered integer, mapping.md section 2).
  * No `@ContractOnly` callee to stand in for: model.py's `axioms` region is
    empty (meta.json `"axioms": []`), both changed operations are modeled
    DEEPLY.  So every leg below is a real R/I obligation and none is assumed.

ORACLE -- the REAL patched repo functions named in mapping.md section 1, CALLED,
never transliterated.  The gate git-applies patch.diff to /testbed before this
script runs and PYTHONPATH=/testbed makes the patched package importable, so
every oracle is driven end-to-end through the real printer:

  leg A  `remainder_operand_level`  vs  `sympy.printing.precedence.precedence`
         on a real `Mod` node (precedence.py:118 dispatcher + the gold's new
         `"Mod": PRECEDENCE["Mul"]` entry at precedence.py:42).
  leg B  `negated_single_operand_enclosed`  vs  the gold's
         `len(a) == 1 and sign == "-"` branch of `CodePrinter._print_Mul`
         (codeprinter.py:490) reached through the real `doprint(-operand)`,
         i.e. including the real `StrPrinter.parenthesize(item, level,
         strict=False)` (str.py:33-37) and the real float threshold
         `0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"])`.  Run through TWO real
         printer subclasses (`PythonCodePrinter`, `C99CodePrinter`) so the
         behaviour is pinned on the shared base-class branch, not one language.
  leg C  `negated_remainder_is_enclosed`  vs  the composite F2P observation
         `doprint(-Mod(a, b))` -- the `-(x % y)` shape from the issue, tying
         leg A and leg B through the real code.
  leg D  the `encloses` @Pure helper  vs  the REAL
         `StrPrinter.parenthesize(item, level, strict)` predicate on the FULL
         exhaustive 31x31x{False,True} grid of (operand_level, cutoff, strict).
         Leg B alone only ever passes cutoff=55/strict=False, so without leg D
         the helper's other two parameters would go untested.

TYPE BRIDGE (mapping.md section 2, inverted).  The model abstracts a SymPy
expression to the single field the patch reads, its binding strength
`precedence(item)`.  Both directions are explicit:

  carrier -> real operand: `_LevelOperand`, a `Symbol` subclass overriding
    `precedence`, realizes ANY chosen level, because `precedence(item)` returns
    `item.precedence` when that attribute exists (precedence.py:120-121).  The
    real dispatcher, real `parenthesize` and real patched `_print_Mul` then run
    on it unmodified -- a bridge INTO the real function, not a stand-in for it.
    The level is re-read back through the real `precedence()` before it reaches
    the shadow, so a bridge that failed to take effect cannot pass silently.
  real operand -> carrier: `precedence(factor)` itself, for the natural
    `Mod`/`Mul`/`Pow`/function/sum operands.

The shadow's `bool` is bridged back to TEXT the way the patched code assembles
it (`"-(" + inner + ")"` vs `"-" + inner`, with `inner` the real printer's
rendering of the factor -- the unchanged A-tagged context) and compared
BYTE-WISE against the real `_print_Mul` output, so the assembly is diffed too,
not just the decision bit.  The float threshold 55.0 needs no bridging: it is
only ever compared against integer precedences (mapping.md section 2), and this
check drives the real float threshold anyway.

INPUT DOMAIN -- everything counted toward the target satisfies the model's
`Requires`.  `negated_single_operand_enclosed`'s precondition is
`level_additive() <= operand_level <= level_function()`, i.e. the 31 integers
40..70.  That modeled space is FINITE and far smaller than 1e5, so it is
ENUMERATED EXHAUSTIVELY (all 31 levels x 2 real printers), which pins the real
cut-off exactly -- 40..55 must enclose, 56..70 must not, with no level left
untested -- and leg D is enumerated exhaustively over its whole 31x31x2 grid.
Exhaustive enumeration is a STRONGER check on those legs than 1e5 samples of
them, not a weaker one; seeded fuzz then re-covers the same spaces to fill the
count.  Legs A and C range over real `Mod` nodes built from a pool of symbols,
integers, rationals, sums, products, powers and nested `Mod`s.

EXTENDED CARRIER (documented, counted separately).  The expand-pow F2P operand
`create_expand_pow_optimization(4)(x**4)` and `UnevaluatedExpr` operands have
real precedence `49.5`/`59.5`/`999.5` -- non-integer, hence outside the model's
declared `int` carrier (mapping.md section 2).  They are neither dropped nor
rounded: the real float is fed straight into the verbatim `encloses`, which is
exactly the R refinement section 2 claims (only comparison outcomes against the
threshold matter).  Reported as `extended_carrier_samples` and EXCLUDED from the
in-Requires total, so they cannot pad the count.

Crucially the check does NOT decide branch membership from the oracle's output.
`_negated_single_factor` mirrors the real `_print_Mul` prologue line for line
using the repo's own helpers; for an input that IS in that branch the rendering
must equal one of the two modeled assemblies, and a third form is a FAILURE, not
a skip.  Otherwise a shadow/oracle disagreement could hide as an out-of-domain
skip.

Also asserted, so the check cannot pass by exercising nothing: every one of the
31 levels is covered, leg B sees BOTH outcomes, the exact F2P `-(x % y)` shape is
rendered, the extended carrier is reached, and each leg's sample count is
non-zero.  Any shortfall is a FAILURE, never a silent pass.

>= 1e5 in-Requires inputs: boundary cases first (all 31 levels x 2 printers, the
full leg-D grid, the F2P `Mod`/expand-pow shapes, the cut-off neighbours
54/55/56, one natural operand per strength class), then seeded fuzz over the
same spaces to a total of 100000.  Pinned seed SEED = 22080 (mapping.md
"## G-CONF").

Exit 0 iff zero disagreements; on a disagreement the input and both outputs are
printed and the exit status is 1.  stdlib + sympy (the package under test) only.
"""
import json
import random
import sys

SEED = 22080
N_TOTAL = 100_000

from sympy import (Integer, Mod, Mul, Rational, S, Symbol, cos, exp, sin,
                   symbols, tan)
from sympy.codegen.rewriting import create_expand_pow_optimization
from sympy.core.expr import UnevaluatedExpr
from sympy.core.mul import _keep_coeff
from sympy.printing.c import C99CodePrinter
from sympy.printing.precedence import precedence
from sympy.printing.pycode import PythonCodePrinter
from sympy.printing.str import StrPrinter


# ======================================================================
# SHADOW: model.py's pure region + impl regions, copied verbatim with the
# contract calls (Requires/Ensures/MustTerminate) deleted.  Nothing else
# is changed -- no renaming, no restructuring, no simplification.
# ======================================================================

# --- model.py pure-start .. pure-end (contracts stripped) -------------------
def level_additive() -> int:
    # re-binding level of an additive ("+"/"-") operand
    return 40


def level_multiplicative() -> int:
    # re-binding level of a multiplicative ("*"/"%") operand
    return 50


def level_power() -> int:
    # re-binding level of a power ("**") operand
    return 60


def level_function() -> int:
    # re-binding level of a function-call operand
    return 70


def encloses(operand_level: int, cutoff: int, strict: bool) -> bool:
    """The generic enclose-in-parentheses predicate: a rendered operand is
    enclosed iff it re-binds strictly more loosely than its context, or (in the
    non-strict mode used by default) exactly as loosely. Monotone decreasing in
    `operand_level`."""
    if operand_level < cutoff:
        return True
    if not strict:
        return operand_level <= cutoff
    return False


def leading_minus_cutoff() -> int:
    """The cut-off applied to the single operand of a leading-minus rendering.
    It sits above the multiplicative level and below the power level, so a
    leading-minus product- or remainder-level operand is enclosed while a power
    operand need not be -- which is what makes the rendering parse back to the
    intended value."""
    return (level_power() + level_multiplicative()) // 2
# --- end pure region -------------------------------------------------------


# --- remainder_operand_level: model.py impl-start .. impl-end --------------
def shadow_remainder_operand_level() -> int:
    return level_multiplicative()


# --- negated_single_operand_enclosed: model.py impl-start .. impl-end ------
def shadow_negated_single_operand_enclosed(operand_level: int) -> bool:
    return encloses(operand_level, leading_minus_cutoff(), False)


# --- negated_remainder_is_enclosed: model.py impl-start .. impl-end -------
def shadow_negated_remainder_is_enclosed() -> bool:
    s = shadow_remainder_operand_level()
    return shadow_negated_single_operand_enclosed(s)


# ======================================================================
# TYPE BRIDGE (mapping.md section 2, inverted)
# ======================================================================

class _LevelOperand(Symbol):
    """A real SymPy expression whose binding strength is a CHOSEN level.

    Uses the repo's own documented hook: `precedence(item)` returns
    `item.precedence` when the attribute exists (precedence.py:120-121). The
    real dispatcher, the real `parenthesize` and the real patched `_print_Mul`
    then run on it unmodified, so this is a bridge into the real function, not
    a stand-in for it.
    """

    def __new__(cls, name, level):
        obj = Symbol.__new__(cls, name)
        obj._level = level
        return obj

    @property
    def precedence(self):
        return self._level


# the two real printer subclasses the modeled base-class branch is reached through
_PRINTERS = (PythonCodePrinter, C99CodePrinter)


def _render(printer_cls, expr):
    """The REAL patched printer's rendering of `expr` (fresh printer per call so
    no printer state leaks between samples)."""
    return printer_cls().doprint(expr)


def _negated_single_factor(printer_cls, e):
    """Is `-e` in the branch the gold patch adds, and if so what is its single
    factor?  This is the INPUT-DOMAIN filter, so it mirrors the real
    `_print_Mul` prologue (codeprinter.py:456-488) line for line, using the
    repo's own helpers (`as_coeff_Mul`, `_keep_coeff`, `as_ordered_factors`),
    rather than an ad-hoc re-derivation: the numeric coefficient of e.g.
    `2*exp(x)` survives `_keep_coeff` as a SEPARATE factor, so `len(a) == 2`
    there and the modeled branch is NOT taken.

    Returns the single numerator factor when `len(a) == 1 and sign == "-"` and
    the denominator is empty, else None.  Deliberately independent of the
    oracle's OUTPUT, so branch membership can never be inferred from the very
    rendering under test.
    """
    printer = printer_cls()
    expr = -e
    if not isinstance(expr, Mul):
        return None
    c, rest = expr.as_coeff_Mul()
    if c < 0:
        expr = _keep_coeff(-c, rest)
        sign = "-"
    else:
        sign = ""
    a, b = [], []
    if printer.order not in ('old', 'none'):
        args = expr.as_ordered_factors()
    else:
        args = Mul.make_args(expr)
    for item in args:
        if (item.is_commutative and item.is_Pow and item.exp.is_Rational
                and item.exp.is_negative):
            b.append(item)
        else:
            a.append(item)
    a = a or [S.One]
    if b or len(a) != 1 or sign != "-":
        return None
    return a[0]


def _expected_text(enclosed, inner):
    """Bridge the shadow's `bool` back to TEXT the way the patched code
    assembles it, so the byte-wise diff covers the assembly too."""
    return ("-(" + inner + ")") if enclosed else ("-" + inner)


# ======================================================================
# INPUT GENERATION -- every counted input satisfies the model's Requires
# ======================================================================

_ALL_LEVELS = list(range(40, 71))   # level_additive() .. level_function()

x, y, z = symbols("x y z")
_POOL = [x, y, z, Integer(2), Integer(3), Integer(-5), Rational(3, 4),
         x + y, x * y, x ** 2, x ** y, sin(x), cos(y), tan(z), exp(x),
         x + 1, 2 * x, x * y * z]

_EXPAND_POW = create_expand_pow_optimization(4)


def _mod_pairs_boundary():
    """The F2P `Mod` shapes from the issue, plus kin."""
    return [(x, y), (y, z), (x, 2), (x, 3), (x + y, z), (x * y, z),
            (x ** 2, y), (sin(x), y), (x, y + 1), (x, y * z), (x, y ** 2),
            (Mod(x, y), z), (-x, y), (Rational(3, 4) * x, y), (2 * x, 3 * y)]


def _natural_operands_boundary():
    """One natural operand per modeled strength class (mapping.md section 1):
    remainder 50, product 50, power 60, function 70, additive 40."""
    return [Mod(x, y), Mod(x, 2), x * y, x * y * z, x ** 2, x ** y,
            sin(x), cos(y), exp(x), tan(z), x + y, x + 1]


def _extended_carrier_boundary():
    """Operands whose REAL precedence is non-integer (outside the model's
    declared int carrier): the expand-pow F2P operand and UnevaluatedExpr."""
    return [_EXPAND_POW(x ** 4), _EXPAND_POW(x ** 2), _EXPAND_POW(x ** 3),
            UnevaluatedExpr(x * y), UnevaluatedExpr(x ** 2),
            UnevaluatedExpr(Mod(x, y)), UnevaluatedExpr(x),
            UnevaluatedExpr(sin(x))]


def _fuzz_natural(rng):
    which = rng.randrange(5)
    if which == 0:
        return Mod(rng.choice(_POOL), rng.choice(_POOL))
    if which == 1:
        return rng.choice(_POOL) * rng.choice(_POOL)
    if which == 2:
        return rng.choice(_POOL) ** rng.choice([Integer(2), Integer(3), y])
    if which == 3:
        return rng.choice([sin, cos, tan, exp])(rng.choice(_POOL))
    return rng.choice(_POOL) + rng.choice(_POOL)


def _fuzz_extended(rng):
    if rng.random() < 0.5:
        return _EXPAND_POW(rng.choice(_POOL) ** rng.choice([2, 3, 4]))
    return UnevaluatedExpr(rng.choice(_POOL))


# ======================================================================
# THE DIFFERENTIAL CHECK
# ======================================================================

def main() -> int:
    rng = random.Random(SEED)
    fails = []          # (leg, input, shadow, oracle)
    n = {"A": 0, "B_level": 0, "B_natural": 0, "C": 0, "D": 0}
    ext = 0             # extended-carrier samples (excluded from the total)
    skipped = {"not_a_mod": 0, "not_modeled_branch": 0}
    seen_enclosed = set()   # leg B outcomes actually observed
    seen_levels = set()     # leg B carrier values actually exercised
    f2p_seen = False

    def record(leg, inp, sh, orc):
        fails.append((leg, inp, sh, orc))

    # ---- leg D: encloses vs the REAL parenthesize, exhaustive grid --------
    def check_encloses_grid():
        sp = StrPrinter()
        for lvl in _ALL_LEVELS:
            operand = _LevelOperand("q", lvl)
            bare = sp._print(operand)
            for cut in _ALL_LEVELS:
                for strict in (False, True):
                    n["D"] += 1
                    sh = encloses(lvl, cut, strict)
                    real = sp.parenthesize(operand, cut, strict)
                    orc = (real == "(%s)" % bare)
                    if real not in ("(%s)" % bare, bare):
                        record("D encloses (unmodeled parenthesize output)",
                               "level=%d cutoff=%d strict=%r" % (lvl, cut, strict),
                               sh, real)
                    elif sh != orc:
                        record("D encloses vs real parenthesize",
                               "level=%d cutoff=%d strict=%r" % (lvl, cut, strict),
                               sh, orc)

    # ---- leg A: remainder_operand_level vs real precedence(Mod(a, b)) -----
    def check_mod(a, b):
        nonlocal f2p_seen
        try:
            m = Mod(a, b)
        except Exception:
            skipped["not_a_mod"] += 1
            return
        if type(m).__name__ != "Mod":
            # Mod evaluated away (e.g. Mod(x, 1) -> 0): no Mod node to weigh.
            skipped["not_a_mod"] += 1
            return
        n["A"] += 1
        sh = shadow_remainder_operand_level()
        orc = precedence(m)
        if sh != orc:
            record("A remainder_operand_level", m, sh, orc)

        # ---- leg C: the composite -(x % y) observation -------------------
        for P in _PRINTERS:
            factor = _negated_single_factor(P, m)
            if factor is None:
                skipped["not_modeled_branch"] += 1
                continue
            n["C"] += 1
            sh_c = shadow_negated_remainder_is_enclosed()
            inner = _render(P, factor)
            out = _render(P, -m)
            if out != _expected_text(sh_c, inner):
                record("C negated_remainder_is_enclosed [%s]" % P.__name__,
                       m, _expected_text(sh_c, inner), out)
            if P is PythonCodePrinter and inner == "x % y" and out == "-(x % y)":
                f2p_seen = True

    # ---- leg B: negated_single_operand_enclosed vs the real _print_Mul ----
    def check_level(level):
        for P in _PRINTERS:
            operand = _LevelOperand("q", level)
            factor = _negated_single_factor(P, operand)
            if factor is None:
                skipped["not_modeled_branch"] += 1
                continue
            # re-read the carrier through the REAL dispatcher, so a bridge that
            # failed to take effect cannot pass silently
            lvl = precedence(factor)
            if lvl != level:
                record("B bridge did not take effect [%s]" % P.__name__,
                       "level=%d" % level, level, lvl)
                continue
            n["B_level"] += 1
            seen_levels.add(level)
            sh = shadow_negated_single_operand_enclosed(level)
            inner = _render(P, factor)
            out = _render(P, -operand)
            if out != _expected_text(sh, inner):
                record("B negated_single_operand_enclosed [%s]" % P.__name__,
                       "level=%d" % level, _expected_text(sh, inner), out)
            else:
                seen_enclosed.add(sh)

    def check_natural(e):
        """Same leg B obligation, driven by a NATURAL expression: its carrier
        value is the real `precedence(factor)`."""
        for P in _PRINTERS:
            factor = _negated_single_factor(P, e)
            if factor is None:
                skipped["not_modeled_branch"] += 1
                continue
            lvl = precedence(factor)
            if not (isinstance(lvl, int)
                    and level_additive() <= lvl <= level_function()):
                # outside the model's integer carrier / Requires (atoms are
                # 1000); handled by check_extended for the non-integer strengths
                skipped["not_modeled_branch"] += 1
                continue
            n["B_natural"] += 1
            seen_levels.add(lvl)
            sh = shadow_negated_single_operand_enclosed(lvl)
            inner = _render(P, factor)
            out = _render(P, -e)
            if out != _expected_text(sh, inner):
                record("B negated_single_operand_enclosed/natural (level=%r) "
                       "[%s]" % (lvl, P.__name__), e,
                       _expected_text(sh, inner), out)
            else:
                seen_enclosed.add(sh)

    def check_extended(e):
        """EXTENDED CARRIER: real precedence is non-integer, so outside the
        model's declared int carrier. The real float is fed straight into the
        verbatim `encloses` -- counted separately, never toward N_TOTAL."""
        nonlocal ext
        for P in _PRINTERS:
            factor = _negated_single_factor(P, e)
            if factor is None:
                skipped["not_modeled_branch"] += 1
                continue
            lvl = precedence(factor)
            if isinstance(lvl, int):
                skipped["not_modeled_branch"] += 1
                continue
            ext += 1
            sh = encloses(lvl, leading_minus_cutoff(), False)
            inner = _render(P, factor)
            out = _render(P, -e)
            if out != _expected_text(sh, inner):
                record("extended-carrier encloses (level=%r) [%s]"
                       % (lvl, P.__name__), e, _expected_text(sh, inner), out)

    # ---------- boundary cases first ----------
    check_encloses_grid()                  # EXHAUSTIVE 31 x 31 x 2
    for level in _ALL_LEVELS:              # EXHAUSTIVE over the finite domain
        check_level(level)
    for a, b in _mod_pairs_boundary():
        check_mod(a, b)
    for e in _natural_operands_boundary():
        check_natural(e)
    for e in _extended_carrier_boundary():
        check_extended(e)

    boundary_total = sum(n.values())

    # ---------- seeded fuzz over the same spaces, to >= 1e5 ----------
    # N_TOTAL counts inputs that SATISFY the Requires (skips and
    # extended-carrier samples do NOT count toward the target, so a generator
    # that mostly misses the branch cannot shrink the real sample size).
    while sum(n.values()) < N_TOTAL and not fails:
        which = rng.randrange(4)
        if which == 0:
            check_level(rng.choice(_ALL_LEVELS))
        elif which == 1:
            check_mod(rng.choice(_POOL), rng.choice(_POOL))
        elif which == 2:
            check_natural(_fuzz_natural(rng))
        else:
            check_extended(_fuzz_extended(rng))

    total = sum(n.values())

    # ---------- the check must have exercised the modeled behaviour ----------
    problems = []
    if not fails:
        missing = sorted(set(_ALL_LEVELS) - seen_levels)
        if missing:
            problems.append("leg B did not cover all %d modeled levels; "
                            "missing %r" % (len(_ALL_LEVELS), missing))
        if seen_enclosed != {True, False}:
            problems.append("leg B saw only outcome(s) %r -- the wrap decision "
                            "was not exercised both ways"
                            % (sorted(seen_enclosed),))
        if not f2p_seen:
            problems.append("the F2P shape -(x %% y) was never rendered")
        if n["D"] != len(_ALL_LEVELS) * len(_ALL_LEVELS) * 2:
            problems.append("leg D grid incomplete: %d of %d"
                            % (n["D"], len(_ALL_LEVELS) ** 2 * 2))
        if ext == 0:
            problems.append("the extended carrier was never reached")
        for leg in sorted(n):
            if n[leg] == 0:
                problems.append("leg %s exercised 0 inputs" % leg)
        if total < N_TOTAL:
            problems.append("only %d in-Requires inputs, target %d"
                            % (total, N_TOTAL))

    if fails:
        print("G-CONF FAIL: %d disagreement(s) between the model shadow and "
              "the real patched sympy over %d inputs:" % (len(fails), total))
        for leg, inp, sh, orc in fails[:5]:
            print("  leg=%s input=%r shadow=%r oracle=%r" % (leg, inp, sh, orc))
    elif problems:
        print("G-CONF FAIL: the differential ran but did not exercise the "
              "modeled behaviour:")
        for p in problems:
            print("  " + p)

    status = "pass" if (not fails and not problems) else "fail"
    print(json.dumps({
        "status": status,
        "instance": "sympy__sympy-22080",
        "backend": "nagini",
        "shadow": "model.py impl regions (verbatim, contracts stripped): "
                  "remainder_operand_level, negated_single_operand_enclosed, "
                  "negated_remainder_is_enclosed (+ the @Pure region)",
        "oracle": "REAL patched sympy, called: precedence(Mod(a,b)) "
                  "[precedence.py:118] + CodePrinter._print_Mul leading-minus "
                  "branch via doprint [codeprinter.py:490] + "
                  "StrPrinter.parenthesize [str.py:33-37]",
        "printers": [P.__name__ for P in _PRINTERS],
        "samples": total,
        "boundary_samples": boundary_total,
        "per_leg": n,
        "levels_enumerated_exhaustively": len(_ALL_LEVELS),
        "distinct_levels_exercised": len(seen_levels),
        "encloses_grid_exhaustive": n["D"],
        "extended_carrier_samples": ext,
        "skipped_out_of_domain": skipped,
        "seed": SEED,
        "disagreements": len(fails),
        "problems": problems,
    }))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
