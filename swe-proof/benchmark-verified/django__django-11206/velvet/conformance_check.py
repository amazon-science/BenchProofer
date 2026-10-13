#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11206 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo type, via the mapping.md correspondence
              (`DecVal` ↔ (`Fraction(number)`, the unchanged tail applied to that
              very object), `int|None` ↔ `Option Nat`):
                  out = renderDecimal (clampSmall number decimal_pos) decimal_pos
              `clampSmall`/`belowResolution`/`guardCutoff`/`resolution` are the
              R/I content and are transliterated here, over the CARRIER: the
              decision is taken from the `amount` facet alone (an exact
              `Fraction`, never a `Decimal` operation), and the value handed
              onward is either the input itself or `plainZero`. The A-tagged
              `render`/`zeroRender` facets are NOT replaced by a model: they are
              the REAL unchanged repo renderer (the pre-patch `format`),
              reconstructed in-container by stripping the gold block from the
              installed source. So the shadow is exactly the impl's "select which
              value the unchanged renderer receives, then render it".
  * ORACLE  — `patch.diff`'s behaviour: the patched `django.utils.numberformat
              .format` (the harness git-applies the gold patch before this runs;
              gate_conf passes apply_gold=True), the real correctness oracle.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. The fuzz deliberately includes
  * inputs of equal amount but different written form (trailing zeros, an
    all-zero digit string at a stated place, the >200-digit branch of the tail);
  * `Decimal` SUBCLASS inputs, whose display behaviour no description of the
    value records — an F2P row turns on one, and they are the inputs on which a
    shadow that rebuilt the value it passes on would disagree here;
  * magnitudes with more significant digits than the ambient working precision,
    placed at the materialization boundary of the guard — the inputs on which a
    shadow comparing the exact magnitude against `resolution p` (rather than
    against `guardCutoff p`) would disagree here.

Calls outside the modeled domain (mapping.md §2: a non-finite input, a magnitude
the ambient environment cannot materialize, or a requested position count past
the one `require positionsInExponentRange decimalPos` admits) are not fuzzed; the
boundaries themselves are measured by axiom_check.py. The largest ADMITTED
position count is drawn here explicitly, so the bound is exercised from inside.

Runs in-container (the prebuilt SWE-Bench instance image, patched), stdlib +
django only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import decimal
import functools
import inspect
import random
import re
import sys
from decimal import Decimal
from fractions import Fraction

SEED = 11206
N_FUZZ = 100_000
WORKING_DIGITS = 28                 # Lean `workingDigits`; = getcontext().prec
# Lean `leastExponentMagnitude`; = -getcontext().Etiny() = -(Emin - prec + 1).
# Asserted against the live context in main().
LEAST_EXPONENT_MAGNITUDE = 1000026
# The largest requested position count `require positionsInExponentRange` admits.
LAST_POSITION_COUNT = LEAST_EXPONENT_MAGNITUDE - WORKING_DIGITS      # 999998


def _configure_django():
    from django.conf import settings
    if not settings.configured:
        settings.configure(USE_L10N=False, USE_THOUSAND_SEPARATOR=False)


# ---- reconstruct the PRE-PATCH renderer from the installed PATCHED source ----
# The installed module carries the gold block (apply_gold=True). Strip it to
# recover the unchanged renderer = the carrier's `render` facet (mapping.md §3.1).
_STRIP_RE = re.compile(
    r"\n[ \t]*if decimal_pos is not None:\n"
    r"(?:[ \t]*#.*\n|[ \t]*cutoff = Decimal\([^\n]*\n|"
    r"[ \t]*if abs\(number\) < cutoff:\n|"
    r"[ \t]*number = Decimal\('0'\)\n|[ \t]*\n)+",
    re.MULTILINE)


def _build_prepatch_format(patched_format_module):
    src = inspect.getsource(patched_format_module)
    if "cutoff = Decimal(" not in src:
        sys.stderr.write("conformance_check: installed source does NOT carry the "
                         "gold block; G-CONF expects the gold patch applied.\n")
        sys.exit(2)
    stripped, n = _STRIP_RE.subn("\n", src, count=1)
    if n != 1 or "cutoff = Decimal(" in stripped:
        sys.stderr.write("conformance_check: failed to strip the normalization "
                         "block cleanly (n=%d).\n" % n)
        sys.exit(2)
    g = {}
    exec(compile(stripped, "<prepatch>", "exec"), g)
    return g["format"]


# ---- a Decimal subclass, the shape the repository's own suite uses -----------
# tests/utils_tests/test_numberformat.py::TestNumberFormat.test_decimal_subclass
class EuroDecimal(Decimal):
    """A Decimal subclass that formats itself with a currency prefix."""

    def __format__(self, specifier, **kwargs):
        amount = super().__format__(specifier, **kwargs)
        return '€ {}'.format(amount)


# ---- the Lean carrier + pure region, transliterated (R/I content) ------------

def rat_abs(n):
    """Lean `ratAbs n = max n (-n)`."""
    return max(n, -n)


@functools.lru_cache(maxsize=None)
def resolution(p):
    """Lean `resolution p = 1 / 10 ^ max p 1`, as an exact Fraction."""
    return Fraction(1, 10 ** max(p, 1))


@functools.lru_cache(maxsize=None)
def guard_cutoff(p):
    """Lean `guardCutoff p = resolution p - resolution p / (2 * 10 ^ workingDigits)`."""
    r = resolution(p)
    return r - r / (2 * 10 ** WORKING_DIGITS)


def below_resolution(amount, decimal_pos):
    """Lean `belowResolution` — a function of the `amount` facet alone."""
    if decimal_pos is None:
        return False
    return rat_abs(amount) < guard_cutoff(decimal_pos)


def positions_in_exponent_range(decimal_pos):
    """Lean `positionsInExponentRange` — the `require` clause of `formatDecimal`.

    The guard's threshold sits at exponent `-(max(p,1) + workingDigits)`, so the
    correspondence is claimed exactly while that exponent is one the ambient
    environment can place a digit at (mapping.md §2).
    """
    if decimal_pos is None:
        return True
    return max(decimal_pos, 1) + WORKING_DIGITS <= LEAST_EXPONENT_MAGNITUDE


def in_scope(number, decimal_pos):
    """Is this call inside the modeled domain (mapping.md §2)?"""
    if not number.is_finite():
        return False
    if decimal_pos is None:
        return True
    if not positions_in_exponent_range(decimal_pos):
        return False
    try:
        abs(number)
    except decimal.DecimalException:
        return False
    return True


def main():
    _configure_django()
    import django.utils.numberformat as nf
    patched_format = nf.format
    prepatch_format = _build_prepatch_format(nf)

    ctx = decimal.getcontext()
    assert ctx.prec == WORKING_DIGITS and ctx.rounding == decimal.ROUND_HALF_EVEN, (
        "the ambient arithmetic context is not the one mapping.md §2 states "
        "(prec=%r rounding=%r)" % (ctx.prec, ctx.rounding))
    assert -ctx.Etiny() == LEAST_EXPONENT_MAGNITUDE, (
        "leastExponentMagnitude (%d) is not the magnitude of the ambient Etiny "
        "(%d): the position-count domain of mapping.md §2 is stale"
        % (LEAST_EXPONENT_MAGNITUDE, ctx.Etiny()))

    def shadow(number, decimal_pos, grouping, thousand_sep, force_grouping):
        # `clampSmall`: the decision comes from the carrier's `amount` facet, and
        # the value handed to the unchanged renderer is either the input ITSELF
        # (pass-through: its display behaviour travels with it) or `plainZero`.
        amount = Fraction(number)
        carried = Decimal('0') if below_resolution(amount, decimal_pos) else number
        # `renderDecimal`: the real unchanged renderer, applied to that value.
        return str(prepatch_format(carried, '.', decimal_pos, grouping,
                                   thousand_sep, force_grouping))

    def oracle(number, decimal_pos, grouping, thousand_sep, force_grouping):
        return str(patched_format(number, '.', decimal_pos, grouping,
                                  thousand_sep, force_grouping))

    rng = random.Random(SEED)
    dec_pos_choices = [None, 0, 1, 2, 3, 8]
    group_choices = [0, 3, 2]
    tsep_choices = ['', ',', '.']
    fg_choices = [True, False]

    def rand_dec():
        kind = rng.randint(0, 6)
        cls = EuroDecimal if rng.random() < 0.15 else Decimal
        if kind == 0:
            return cls(rng.randint(-10 ** 6, 10 ** 6))
        if kind == 1:
            return cls(str(Decimal(rng.randint(-9999, 9999))
                           .scaleb(rng.randint(-320, 320))))
        if kind == 2:
            return cls('0.' + '0' * rng.randint(0, 310) + str(rng.randint(1, 9999)))
        if kind == 3:
            sign = '-' if rng.random() < 0.5 else ''
            return cls(sign + str(rng.randint(0, 10 ** 8)) + '.' +
                       str(rng.randint(0, 10 ** 6)))
        if kind == 4:
            # written forms that denote the same amount in different ways,
            # including all-zero digit strings at a stated place
            digits = rng.choice(['0', '00', str(rng.randint(1, 999)),
                                 str(rng.randint(1, 9)) + '0' * rng.randint(1, 6)])
            return cls(Decimal((rng.randint(0, 1), tuple(int(c) for c in digits),
                               rng.randint(-320, 320))))
        if kind == 5:
            # more significant digits than the ambient precision, sitting at the
            # materialization boundary of some position count
            m = max(rng.choice([0, 1, 2, 3, 8]), 1)
            digits = '9' * rng.randint(25, 32) + ''.join(
                rng.choice('0123456789') for _ in range(rng.randint(0, 8)))
            return cls(Decimal((rng.randint(0, 1), tuple(int(c) for c in digits),
                               -(len(digits) + m - 1))))
        return cls(rng.choice(['0', '-0', '3.', '3.0', '1e16', '9e9999',
                               '1e-200', '1e-300', '0E-303', '1.000']))

    def threshold_family(p):
        """Magnitudes at and around `guardCutoff p` (the materialization boundary)."""
        m = max(p, 1)
        unit = Decimal(1).scaleb(-(29 + m))
        thr = Decimal(10 ** 29 - 5).scaleb(-(29 + m))        # == guardCutoff p
        cut = Decimal(1).scaleb(-m)                          # == cutoff
        ulp28 = Decimal(1).scaleb(-(28 + m))
        base = [thr, thr - unit, thr + unit, cut, cut - ulp28, cut + ulp28,
                Decimal(10 ** 29 - 1).scaleb(-(29 + m)),
                Decimal(10 ** 30 - 1).scaleb(-(30 + m)),
                Decimal(10 ** 28 - 1).scaleb(-(28 + m))]
        return [s * d for d in base for s in (Decimal(1), Decimal(-1))]

    def boundary_inputs():
        decs = [Decimal('0'), Decimal('3.'), Decimal('1234.2'),
                Decimal('0.00000001'), Decimal('9e-19'),
                Decimal('1e-7'), Decimal('1e-8'), Decimal('1e-9'),
                Decimal('1e-10'), Decimal('1e-11'), Decimal('1e-200'),
                Decimal('1' + '0' * 300), Decimal('0.' + '0' * 299 + '1234'),
                # equal amount, different written form
                Decimal('3.0'), Decimal('3.000'), Decimal('-0'),
                Decimal('0.000'), Decimal('0E-303'), Decimal('0E+5'),
                Decimal('1.000'), Decimal('1.200'), Decimal('-1.20'),
                Decimal((0, (1, 2, 3), -305)), Decimal((1, (5,), 201)),
                Decimal('12e-4'), Decimal('12E+4'),
                # equal amount, equal written form, different runtime type
                EuroDecimal('1.23'), EuroDecimal('-1.23'), EuroDecimal('0'),
                EuroDecimal('0.001'), EuroDecimal('0.0001'),
                EuroDecimal('1234.5678'), EuroDecimal('1e16'),
                EuroDecimal('0.' + '0' * 299 + '1234'), EuroDecimal('9e-19')]
        for p in (0, 1, 2, 3, 8):
            decs.append(Decimal(1).scaleb(-max(p, 1)))       # == cutoff
            decs.append(Decimal(1).scaleb(-max(p, 1) - 1))   # < cutoff
            decs.append(-Decimal(1).scaleb(-max(p, 1) - 1))
            decs += threshold_family(p)
        for number in decs:
            for decimal_pos in dec_pos_choices:
                yield (number, decimal_pos, 0, '', False)
                yield (number, decimal_pos, 3, ',', True)
        # The LARGEST requested position count the modeled domain admits
        # (mapping.md §2): at this count the guard's threshold still lands on an
        # exponent the ambient environment can place a digit at, so the
        # materialization the `guardCutoff` derivation assumes is available. The
        # magnitudes below straddle that threshold, built with the exact tuple
        # constructor (`scaleb` would round them onto it). axiom_check.py
        # measures the count just past the bound, where the two readings part.
        for units in (10 ** 29 - 6, 10 ** 29 - 5, 10 ** 29 - 4, 1):
            for sign in (0, 1):
                yield (Decimal((sign, tuple(int(c) for c in str(units)),
                                -(29 + LAST_POSITION_COUNT))),
                       LAST_POSITION_COUNT, 0, '', False)
        yield (Decimal('1.23'), LAST_POSITION_COUNT, 3, ',', True)
        yield (EuroDecimal('1.23'), LAST_POSITION_COUNT, 0, '', False)

    disagreements = []
    count = 0
    skipped = 0

    def compare(args):
        nonlocal count, skipped
        if not in_scope(args[0], args[1]):
            skipped += 1
            return
        count += 1
        sh = shadow(*args)
        orc = oracle(*args)
        if sh != orc:
            disagreements.append((args, sh, orc))

    for args in boundary_inputs():
        compare(args)
        if len(disagreements) >= 5:
            break

    if not disagreements:
        for _ in range(N_FUZZ):
            args = (rand_dec(), rng.choice(dec_pos_choices),
                    rng.choice(group_choices), rng.choice(tsep_choices),
                    rng.choice(fg_choices))
            compare(args)
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for args, sh, orc in disagreements:
            number, dp, g, ts, fg = args
            print("  number=%r (%s) decimal_pos=%r grouping=%r thousand_sep=%r "
                  "force_grouping=%r shadow=%r oracle=%r"
                  % (str(number), type(number).__name__, dp, g, ts, fg, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of formatDecimal (clampSmall over the DecVal "
          "carrier — decision from the `amount` facet, value handed on either the "
          "input itself or plainZero — composed with the real unchanged renderer) "
          "agrees with patch.diff behaviour on %d inputs (seed=%d), 0 "
          "disagreements; %d draws outside the modeled domain were not compared."
          % (count, SEED, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
