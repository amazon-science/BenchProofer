#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11206.

Runs WITHOUT the gold patch applied (gate_ax): the in-container
`django.utils.numberformat.format` is the PRE-PATCH (base_commit) renderer — the
unchanged formatting tail that `Solution.lean` models opaquely, i.e. the
`render` facet of the carrier and the constant `zeroRender`.

THE CARRIER. `Solution.lean` carries a decimal input as the two facets the
modeled operation reads it through:

    structure DecVal where
      amount : Rat                          -- the exact amount it denotes
      render : Option Nat -> List Char      -- the display string THIS value
                                            -- produces at a requested position
                                            -- count

transliterated here as

    carrier(d)      = DecVal(amount = Fraction(d),
                             render = lambda dp: tail(d, dp, <ambient args>))
    plainZero       = DecVal(amount = 0,
                             render = lambda dp: tail(Decimal('0'), dp, <ambient>))
    zeroRender      = plainZero.render

so the `render` facet is not a description of the value from which a display
string could be recomputed — it IS the unchanged tail applied to that very
object. Six obligations are checked against the REAL code:

  (A-reference) the opaque `render`/`zeroRender` == the real unchanged `format`
      tail. The Lean impl returns `renderDecimal (clampSmall number decimalPos)
      decimalPos`, so the shadow reconstructs the PATCHED `format` by inserting
      the gold block into the installed PRE-PATCH source and asserts
          patched_format(number, ...)
            == renderDecimal(clampSmall(carrier(number), decimal_pos), decimal_pos)
      on a boundary matrix (including `Decimal` SUBCLASS inputs and
      high-significance magnitudes at the guard threshold) plus fuzz. The
      pre-patch `format` IS the unchanged renderer, so this is exactly
      "the carrier's display facet == the real unchanged tail", and it is
      falsifiable in both of the places the modeled operation can be wrong:
      WHICH value reaches the tail, and WHEN it is replaced.

  (guard soundness w.r.t. the carrier) the replacement DECISION reads the input
      only through `amount`: any two inputs of equal exact amount — however
      differently written, and whatever their runtime type — get the same
      verdict from the real `abs(number) < cutoff`. Measured over pairs of equal
      amount with different written forms and different runtime types.

  (guard equivalence) the modeled predicate is the real one, exactly:
          ratAbs(amount) < guardCutoff(p)   <->   abs(number) < cutoff
      where `guardCutoff p = resolution p - resolution p / (2 * 10 ** 28)`.
      The lowering is not slack: `abs()` is an arithmetic operation, so it
      MATERIALIZES the magnitude at the ambient working precision (28
      significant digits, ties to even) before the comparison, and a magnitude
      strictly under `cutoff` can materialize AT `cutoff`. Measured on families
      built exactly at / around the threshold with 28..40 significant digits,
      both signs, for every relevant position count.

  (threshold binding) `resolution(p)` == the patch's `cutoff` expression
      `Decimal('0.' + '1'.rjust(p, '0'))` for p in 0..50.

  (render necessity) the display facet is NOT a function of any description of
      the value: exhibited pairs of equal amount (and even of equal
      `as_tuple()`) whose rendered strings differ, because the tail branches on
      `abs(exponent) + len(digits) > 200`, expands with `'{:f}'.format(number)`
      — which dispatches on `type(number).__format__` — and reproduces the
      stated place. This is why `render` travels WITH the value and why
      `clampSmall`'s pass-through case is a claim about the input ITSELF, and it
      is why the replacement case names `plainZero` (a value AND its display
      behaviour) rather than the amount zero.

  (domain of correspondence) the modeled operation is the one the repository
      performs on inputs whose magnitude the ambient environment can
      materialize. `abs(number)` signals (raises `decimal.Overflow`, a trapped
      condition) once the magnitude's adjusted exponent exceeds the ambient
      `Emax`, so those inputs — like `NaN`/`Infinity`, which have no exact
      amount at all — are outside the modeled domain (mapping.md §2). The
      boundary is measured here, and every probe is asserted to be inside it, so
      the corpus cannot silently drift out of scope.

  (domain of correspondence, position counts) the guard equivalence above rests
      on the 28-significant-digit grid just below `10^-max(p,1)` being
      representable, which holds exactly while
      `max(p,1) + 28 <= -getcontext().Etiny() = 1000026`. That is the
      `require positionsInExponentRange decimalPos` clause of `formatDecimal`.
      The bound is measured from BOTH sides here — agreement for every position
      count up to the last admitted one, and disagreement in each direction just
      past it — and it restricts only the REQUESTED POSITION COUNT: subnormal
      and below-`Etiny` input magnitudes are separately measured to agree at
      every admitted position count, so no bound on the input is claimed
      (mapping.md §2).

Imports only stdlib + django (already on the testbed PYTHONPATH); no repo-private
helpers. Exit 0 iff every obligation holds.
"""
import decimal
import functools
import inspect
import random
import sys
from decimal import Decimal
from fractions import Fraction


def _configure_django():
    from django.conf import settings
    if not settings.configured:
        settings.configure(USE_L10N=False, USE_THOUSAND_SEPARATOR=False)


# ---- the gold block (verbatim from patch.diff added lines) ------------------
_ORIG = "    if isinstance(number, Decimal):\n"
_ADDED = (
    "    if isinstance(number, Decimal):\n"
    "\n"
    "        if decimal_pos is not None:\n"
    "            # If the provided number is too small to affect any of the visible\n"
    "            # decimal places, consider it equal to '0'.\n"
    "            cutoff = Decimal('0.' + '1'.rjust(decimal_pos, '0'))\n"
    "            if abs(number) < cutoff:\n"
    "                number = Decimal('0')\n"
    "\n"
)


def _build_formats():
    """Return (prepatch_format, patched_format) from the installed PRE-PATCH src."""
    import django.utils.numberformat as nf
    prepatch_src = inspect.getsource(nf)
    if _ADDED in prepatch_src:
        sys.stderr.write("axiom_check: installed source already carries the gold "
                         "block; G-AX expects the base_commit module.\n")
        sys.exit(2)
    if _ORIG not in prepatch_src:
        sys.stderr.write("axiom_check: could not locate the Decimal branch anchor.\n")
        sys.exit(2)
    patched_src = prepatch_src.replace(_ORIG, _ADDED, 1)
    assert patched_src != prepatch_src
    g_pre, g_pat = {}, {}
    exec(compile(prepatch_src, "<prepatch>", "exec"), g_pre)
    exec(compile(patched_src, "<patched>", "exec"), g_pat)
    return g_pre["format"], g_pat["format"]


# ---- a Decimal subclass, the shape the repository's own suite uses -----------
# tests/utils_tests/test_numberformat.py::TestNumberFormat.test_decimal_subclass
class EuroDecimal(Decimal):
    """A Decimal subclass that formats itself with a currency prefix."""

    def __format__(self, specifier, **kwargs):
        amount = super().__format__(specifier, **kwargs)
        return '€ {}'.format(amount)


# ---- the Lean carrier + pure region, transliterated -------------------------
AMBIENTS = (
    # (decimal_sep, grouping, thousand_sep, force_grouping)
    ('.', 0, '', False),
    ('.', 3, ',', True),
    (',', 2, '.', False),
)


class DecVal(object):
    """Lean `structure DecVal where amount : Rat; render : Option Nat -> List Char`."""

    __slots__ = ('amount', 'render')

    def __init__(self, amount, render):
        self.amount = amount
        self.render = render


def _tail(fmt, obj, dp, ambient):
    """The unchanged rendering tail applied to one object at one position count."""
    decimal_sep, grouping, thousand_sep, force_grouping = ambient
    try:
        return ('OK', str(fmt(obj, decimal_sep, dp, grouping, thousand_sep,
                             force_grouping)))
    except Exception as e:  # noqa: BLE001 — compare raised-exception kinds too
        return ('ERR', type(e).__name__)


def carrier(prepatch_format, number, ambient):
    """The Lean `DecVal` a repo decimal input denotes, at fixed ambient args."""
    return DecVal(Fraction(number),
                  lambda dp: _tail(prepatch_format, number, dp, ambient))


def plain_zero(prepatch_format, ambient):
    """Lean `plainZero` — the value `Decimal('0')` together with its display."""
    return carrier(prepatch_format, Decimal('0'), ambient)


def rat_abs(n):
    """Lean `ratAbs n = max n (-n)`."""
    return max(n, -n)


WORKING_DIGITS = 28                  # Lean `workingDigits`; = getcontext().prec

# Lean `leastExponentMagnitude`; = -getcontext().Etiny() = -(Emin - prec + 1).
# The magnitude of the smallest exponent the ambient environment can place a
# digit at; asserted against the live context in check_ambient_context().
LEAST_EXPONENT_MAGNITUDE = 1000026


@functools.lru_cache(maxsize=None)
def resolution(p):
    """Lean `resolution p = 1 / 10 ^ max p 1`, as an exact Fraction."""
    return Fraction(1, 10 ** max(p, 1))


@functools.lru_cache(maxsize=None)
def guard_cutoff(p):
    """Lean `guardCutoff p = resolution p - resolution p / (2 * 10 ^ workingDigits)`."""
    r = resolution(p)
    return r - r / (2 * 10 ** WORKING_DIGITS)


def positions_in_exponent_range(decimal_pos):
    """Lean `positionsInExponentRange` — the `require` clause of `formatDecimal`.

    `none` requests no positions and imposes nothing; `some p` is admitted while
    the 28-significant-digit grid the guard's threshold sits on is representable,
    i.e. `max p 1 + workingDigits <= leastExponentMagnitude`.
    """
    if decimal_pos is None:
        return True
    return max(decimal_pos, 1) + WORKING_DIGITS <= LEAST_EXPONENT_MAGNITUDE


def below_resolution(v, decimal_pos):
    """Lean `belowResolution` — reads the carrier's `amount` facet only."""
    if decimal_pos is None:
        return False
    return rat_abs(v.amount) < guard_cutoff(decimal_pos)


def clamp_small(v, decimal_pos, zero):
    """Lean `clampSmall d dp = if belowResolution d dp then plainZero else d`."""
    return zero if below_resolution(v, decimal_pos) else v


def render_decimal(v, decimal_pos):
    """Lean `renderDecimal d dp = d.render dp`."""
    return v.render(decimal_pos)


# ---- the repository-side expressions the model is compared against -----------

def real_cutoff(p):
    """The patch's own `cutoff` expression, verbatim."""
    return Decimal('0.' + '1'.rjust(p, '0'))


def real_guard(number, decimal_pos):
    """The patch's own guard, verbatim: `decimal_pos is not None and abs(...) < cutoff`.

    Evaluated in the ambient arithmetic context, exactly as the repository does:
    `abs()` is a context operation, so the magnitude is materialized at the
    ambient precision before the comparison.
    """
    if decimal_pos is None:
        return False
    return abs(number) < real_cutoff(decimal_pos)


def in_scope(number, decimal_pos):
    """Is this call inside the modeled domain (mapping.md §2)?"""
    if not number.is_finite():
        return False                              # no exact amount
    if decimal_pos is None:
        return True                               # the guard is not evaluated
    if not positions_in_exponent_range(decimal_pos):
        return False                              # threshold grid not representable
    try:
        abs(number)
    except decimal.DecimalException:
        return False                              # magnitude not materializable
    return True


# ---- the checks -------------------------------------------------------------

def check_ambient_context():
    """`workingDigits` binds to the ambient working precision."""
    ctx = decimal.getcontext()
    assert ctx.prec == WORKING_DIGITS, (
        "workingDigits (%d) is not the ambient working precision (%d): the "
        "guardCutoff derivation is stated for the default arithmetic context "
        "(mapping.md §2)" % (WORKING_DIGITS, ctx.prec))
    assert ctx.rounding == decimal.ROUND_HALF_EVEN, (
        "the guardCutoff derivation assumes ties-to-even materialization, "
        "ambient rounding is %r" % (ctx.rounding,))
    assert ctx.traps[decimal.Overflow], (
        "the domain-of-correspondence statement assumes Overflow is trapped")
    assert -ctx.Etiny() == LEAST_EXPONENT_MAGNITUDE, (
        "leastExponentMagnitude (%d) is not the magnitude of the ambient "
        "Etiny (%d = Emin %d - prec %d + 1): the `require "
        "positionsInExponentRange decimalPos` bound is stated for the default "
        "arithmetic context (mapping.md §2)"
        % (LEAST_EXPONENT_MAGNITUDE, ctx.Etiny(), ctx.Emin, ctx.prec))
    return ctx.prec, ctx.Emax, ctx.Etiny()


def check_threshold_binding():
    """(threshold binding) resolution(p) == the real `cutoff` for every relevant p."""
    for p in range(0, 51):
        assert Fraction(real_cutoff(p)) == resolution(p), (
            "resolution refinement unsound at decimal_pos=%d: cutoff=%s, "
            "resolution=%s" % (p, real_cutoff(p), resolution(p)))
    return 51


def exact(units, exponent, sign=0):
    """`sign * units * 10^exponent`, built WITHOUT an arithmetic operation.

    The `Decimal((sign, digits, exponent))` constructor neither rounds nor
    signals, so probes with more significant digits than the ambient precision
    survive intact — `scaleb`/`*`/`-` would materialize them first and the
    threshold families below would collapse onto the threshold they bracket.
    """
    return Decimal((sign, tuple(int(c) for c in str(units)), exponent))


def _threshold_family(p):
    """Magnitudes at and around `guardCutoff p`, at 28..40 significant digits.

    `guardCutoff p` is exactly `(10^29 - 5) / 10^(29+m)` with `m = max(p,1)`, i.e.
    half a unit in the 28th significant digit below `10^-m`; these probes bracket
    it so the equivalence check cannot pass by never reaching the interesting
    magnitudes.
    """
    m = max(p, 1)
    e = -(29 + m)                       # one unit here is 10^-(29+m)
    cut = 10 ** 29                      # cutoff == resolution p, in those units
    thr = cut - 5                       # guardCutoff p, in those units
    ulp = 10                            # 10^-(28+m), the 28-digit spacing below cut
    units = [thr, thr - 1, thr + 1,
             cut, cut - ulp, cut - ulp - 1, cut + ulp,
             cut - 1, cut - 2, cut - 5 * 1,
             10 ** 29 - 1]              # 29 nines: materializes UP to cut
    out = [exact(u, e, s) for u in units for s in (0, 1)]
    for extra_digits in (30, 40):       # more nines: still materialize UP to cut
        out += [exact(10 ** extra_digits - 1, -(extra_digits + m), s)
                for s in (0, 1)]
    out += [exact(10 ** 28 - 1, -(28 + m), s) for s in (0, 1)]  # 28 nines: exact
    return out


def check_guard_equivalence(rng):
    """(guard equivalence) the modeled predicate == the real one, exactly."""
    n = 0
    for p in (0, 1, 2, 3, 8, 12):
        probes = list(_threshold_family(p))
        # high-significance random magnitudes near the threshold
        m = max(p, 1)
        for _ in range(400):
            digits = ''.join(rng.choice('0123456789') for _ in range(rng.randint(28, 40)))
            digits = '9' * rng.randint(0, 28) + digits
            digits = digits[:45]
            d = exact(int(digits), -(len(digits) + m - 1 - rng.randint(0, 2)),
                      rng.randint(0, 1))
            probes.append(d)
        # ordinary magnitudes, so the check is not only about the boundary
        probes += [Decimal('0'), Decimal('-0'), Decimal('0E-303'), Decimal('1'),
                   Decimal('-1234.567'), exact(1, -m - 1), exact(1, -m),
                   Decimal('9e9999'), Decimal('9e-9999')]
        for d in probes:
            assert in_scope(d, p), "guard probe out of the modeled domain: %s" % d
            modeled = rat_abs(Fraction(d)) < guard_cutoff(p)
            real = real_guard(d, p)
            assert modeled == real, (
                "guard equivalence unsound at decimal_pos=%d on %s: "
                "modeled(ratAbs amount < guardCutoff)=%r, real(abs(number) < "
                "cutoff)=%r  [abs(number)=%s, guardCutoff=%s]"
                % (p, d, modeled, real, abs(d), guard_cutoff(p)))
            n += 1
        # `none` requests no positions: nothing is below resolution, either side
        for d in probes[:8]:
            v = DecVal(Fraction(d), None)
            assert below_resolution(v, None) is False and real_guard(d, None) is False
            n += 1
    return n


def _equal_amount_pairs():
    """Pairs of equal exact amount that the repository nonetheless distinguishes.

    The third element is a position count to probe. The last two pairs have equal
    `as_tuple()` as well: they differ only in runtime type, which no description
    of the value records — that is the pair the `render` facet exists for.
    """
    euro = EuroDecimal('1.23')
    euro_small = EuroDecimal('0.' + '0' * 299 + '1234')
    return [
        (Decimal('3.'), Decimal('3.0'), None),
        (Decimal('3.'), Decimal('3.0'), 3),
        (Decimal('0'), Decimal('0E-303'), 3),
        (Decimal('0'), Decimal('0E-303'), None),
        (Decimal('1'), Decimal('1.000'), None),
        (Decimal('1.2'), Decimal('12E-1'), None),
        (euro, Decimal(euro.as_tuple()), None),
        (euro, Decimal(euro.as_tuple()), 2),
        (euro_small, Decimal(euro_small.as_tuple()), None),
    ]


def check_guard_reads_amount_only(prepatch_format):
    """(guard soundness) equal amount => equal verdict from the REAL guard."""
    n = 0
    for a, b, _dp in _equal_amount_pairs():
        assert Fraction(a) == Fraction(b), (str(a), str(b))
        for p in (None, 0, 1, 2, 3, 8, 12, 30):
            assert in_scope(a, p) and in_scope(b, p)
            assert real_guard(a, p) == real_guard(b, p), (
                "the real guard separates two inputs of equal amount (%s vs %s "
                "at decimal_pos=%r): modeling the decision as a function of the "
                "carrier's `amount` facet would be unsound"
                % (str(a), str(b), p))
            n += 1
    return n


def check_render_necessity(prepatch_format):
    """(render necessity) the display facet is not a function of a description."""
    diverging = 0
    type_only = 0
    for a, b, dp in _equal_amount_pairs():
        ra = _tail(prepatch_format, a, dp, AMBIENTS[0])
        rb = _tail(prepatch_format, b, dp, AMBIENTS[0])
        if ra != rb:
            diverging += 1
            if a.as_tuple() == b.as_tuple():
                # equal amount AND equal written form, different display: no
                # description of the value can determine the display string.
                type_only += 1
    assert diverging, (
        "no exhibited equal-amount pair renders differently: the necessity "
        "argument for carrying the display behaviour is not measured here")
    assert type_only, (
        "no exhibited pair with EQUAL as_tuple() renders differently: the "
        "measurement that the display facet is not reconstructible from the "
        "written form is missing, and it is the one an F2P row turns on")
    return diverging, type_only


def check_plain_zero_binding(prepatch_format):
    """(binding) plainZero == `Decimal('0')` with its display; zeroRender is its facet."""
    assert "number = Decimal('0')" in _ADDED, (
        "the replacement value in the gold block is not `Decimal('0')`; the "
        "plainZero binding is stale")
    for ambient in AMBIENTS:
        z = plain_zero(prepatch_format, ambient)
        assert z.amount == 0
        for dp in (None, 0, 1, 3, 8):
            assert z.render(dp) == _tail(prepatch_format, Decimal('0'), dp, ambient)
    return True


def check_reference(prepatch_format, patched_format, number, decimal_pos, ambient):
    """(A-reference) patched(number) == renderDecimal(clampSmall(carrier(number)))."""
    assert in_scope(number, decimal_pos), (
        "probe outside the modeled domain: %s at decimal_pos=%r" % (number, decimal_pos))
    decimal_sep, grouping, thousand_sep, force_grouping = ambient
    oracle = _tail(patched_format, number, decimal_pos, ambient)
    v = carrier(prepatch_format, number, ambient)
    zero = plain_zero(prepatch_format, ambient)
    shadow = render_decimal(clamp_small(v, decimal_pos, zero), decimal_pos)
    assert shadow == oracle, (
        "A-reference unsound (the carrier's display facet composed with the "
        "modeled replacement != the real behaviour) on number=%r (%s) "
        "decimal_pos=%r ambient=%r: patched=%r  modeled=%r"
        % (str(number), type(number).__name__, decimal_pos, ambient, oracle, shadow))


def check_domain_boundary():
    """(domain of correspondence) measure where `abs()` stops materializing."""
    emax = decimal.getcontext().Emax
    inside = exact(9, emax)                      # adjusted exponent == Emax
    outside = exact(9, emax + 1)                 # adjusted exponent  > Emax
    abs(inside)                                  # must not signal
    assert in_scope(inside, 3), "the Emax boundary probe should be in scope"
    signalled = False
    try:
        abs(outside)
    except decimal.DecimalException as e:
        signalled = type(e).__name__
    assert signalled == 'Overflow', (
        "expected the magnitude of 9E+%d to signal Overflow, got %r: the "
        "domain-of-correspondence statement in mapping.md §2 is stale"
        % (emax + 1, signalled))
    assert not in_scope(outside, 3), "in_scope must exclude the signalling side"
    assert in_scope(outside, None), (
        "with no requested position count the magnitude is never taken, so the "
        "input is inside the modeled domain")
    return emax


def _position_probes(p):
    """A handful of magnitudes straddling `guardCutoff p`, for p up to ~10^6.

    Same shape as `_threshold_family`, kept short because each `Fraction(d)` at
    these exponents materializes a million-digit denominator.
    """
    m = max(p, 1)
    e = -(29 + m)                       # one unit here is 10^-(29+m)
    cut = 10 ** 29                      # cutoff == resolution p, in those units
    out = [exact(u, e, s)
           for u in (cut - 5, cut - 4, cut - 6, cut - 1)   # around guardCutoff p
           for s in (0, 1)]
    out.append(exact(10 ** 28 - 1, -(28 + m)))             # 28 nines: exact
    return out


def check_position_range_boundary():
    """(domain, position counts) measure where the guard equivalence stops as the
    REQUESTED POSITION COUNT grows, and that the `require` clause is that place.

    `guardCutoff p` sits half a unit in the 28th significant digit below
    `10^-max(p,1)`, i.e. at exponent `-(max(p,1) + 28)`. The ambient environment
    can only place a digit down to `Etiny = Emin - prec + 1 = -1000026`, so once
    `max(p,1) + 28` exceeds `1000026` the materialization of a magnitude in that
    window is coarser than the derivation assumes and the two readings part — in
    BOTH directions, which is why the clause is a domain restriction and not a
    one-sided slackening:

      * just past the bound the model normalizes magnitudes the repository keeps
        (the modeled predicate is TRUE where the real one is FALSE);
      * far past it — position counts beyond `leastExponentMagnitude` itself, for
        which the real `cutoff` literal is below `Etiny` and materializes to
        zero — the repository normalizes nothing at all while the model still
        does (FALSE where the real one is TRUE).

    Reported: the largest admitted count, that the next one already disagrees,
    and the disagreement counts on both out-of-domain sides.
    """
    last_in = LEAST_EXPONENT_MAGNITUDE - WORKING_DIGITS          # 999998
    assert positions_in_exponent_range(last_in), last_in
    assert not positions_in_exponent_range(last_in + 1), (
        "the `require` clause admits a position count whose threshold grid is "
        "below the ambient Etiny")
    checked = 0
    for p in (last_in - 2, last_in - 1, last_in):
        for d in _position_probes(p):
            assert in_scope(d, p), (
                "an admitted position count is reported out of the modeled "
                "domain: decimal_pos=%d" % p)
            modeled = rat_abs(Fraction(d)) < guard_cutoff(p)
            real = real_guard(d, p)
            assert modeled == real, (
                "guard equivalence unsound at an ADMITTED position count "
                "(decimal_pos=%d, %s): modeled=%r real=%r — the `require "
                "positionsInExponentRange` bound is too loose"
                % (p, d, modeled, real))
            checked += 1
    diverging = {}
    for p in (last_in + 1, LEAST_EXPONENT_MAGNITUDE + 1):
        assert not positions_in_exponent_range(p), p
        n = 0
        for d in _position_probes(p):
            assert not in_scope(d, p), (
                "in_scope must exclude position counts the `require` clause "
                "rejects: decimal_pos=%d" % p)
            if (rat_abs(Fraction(d)) < guard_cutoff(p)) != real_guard(d, p):
                n += 1
        assert n, (
            "no disagreement found at decimal_pos=%d, which the `require` "
            "clause excludes: the bound may be stricter than the measurement "
            "supports (mapping.md §2)" % p)
        diverging[p] = n
    return last_in, checked, diverging


def check_input_magnitude_unbounded():
    """(domain, position counts) the restriction is on `decimal_pos` ALONE.

    Input magnitudes at and below the ambient `Etiny` — the ones `abs()` returns
    as a subnormal, or rounds to zero — are NOT excluded, and do not need to be:
    for any admitted position count the threshold window sits at exponent
    `-(max(p,1)+28) >= Etiny`, so such a magnitude is far below the window and
    both readings agree on it. Measured rather than argued, at admitted position
    counts including the largest one.
    """
    tiny = -LEAST_EXPONENT_MAGNITUDE                    # getcontext().Etiny()
    probes = []
    for e in (tiny + 2, tiny, tiny - 1, tiny - 40, decimal.getcontext().Emin):
        for units in (1, 5, 10 ** 29 - 5):
            for s in (0, 1):
                d = exact(units, e, s)
                probes.append((d, Fraction(d)))
    n = 0
    for p in (0, 1, 3, 8, LEAST_EXPONENT_MAGNITUDE - WORKING_DIGITS):
        for d, amount in probes:
            assert in_scope(d, p), (
                "a below-Etiny input magnitude is reported out of the modeled "
                "domain at an admitted position count: %s, decimal_pos=%d"
                % (d, p))
            modeled = rat_abs(amount) < guard_cutoff(p)
            real = real_guard(d, p)
            assert modeled == real, (
                "guard equivalence unsound on a below-Etiny input magnitude at "
                "an admitted position count (%s, decimal_pos=%d): modeled=%r "
                "real=%r — the modeled domain would have to bound the INPUT too"
                % (d, p, modeled, real))
            n += 1
    return n


def _representation_variants():
    """Written forms that denote a value in several ways (trailing zeros, stated
    place), including the ones the >200-digit branch of the tail separates."""
    return [Decimal('3.'), Decimal('3.0'), Decimal('3.000'),
            Decimal('0'), Decimal('-0'), Decimal('0.000'), Decimal('0E-303'),
            Decimal('0E+5'), Decimal('1'), Decimal('1.000'),
            Decimal('1.200'), Decimal('-1.20'),
            Decimal((0, (1, 2, 3), -305)), Decimal((1, (5,), 201)),
            Decimal('12e-4'), Decimal('12E+4')]


def _subclass_variants():
    """`Decimal` SUBCLASS inputs — an F2P row turns on one (test_decimal_subclass).

    The pass-through case of `clampSmall` hands the tail the input ITSELF, and
    `'{:f}'.format(number)` dispatches on `type(number).__format__`, so these
    probes fail for any model whose carrier reconstructs the value it passes on.
    """
    return [EuroDecimal('1.23'), EuroDecimal('-1.23'), EuroDecimal('0'),
            EuroDecimal('1234.5678'), EuroDecimal('0.001'),
            EuroDecimal('0.0001'), EuroDecimal('1e16'),
            EuroDecimal('0.' + '0' * 299 + '1234'),
            EuroDecimal(str(exact(10 ** 29 - 5, -32))),
            EuroDecimal('9e-19')]


def _boundary_decimals():
    out = [Decimal('0'), Decimal('-0'), Decimal('3.'), Decimal('3.0'),
           Decimal('1234'), Decimal('1234.2'), Decimal('-1234.33'),
           Decimal('0.00000001'), Decimal('9e-19'), Decimal('.00000000000099'),
           Decimal('1e16'), Decimal('9e9999'), Decimal('9e201'), Decimal('9e200'),
           Decimal('1e-7'), Decimal('1e-8'), Decimal('1e-9'), Decimal('1e-10'),
           Decimal('1e-11'), Decimal('1e-199'), Decimal('1e-200'),
           Decimal('1' + '0' * 300),
           Decimal('0.' + '0' * 299 + '1234'),    # the F2P discriminator
           Decimal('1.2345e999')]
    out += _representation_variants()
    out += _subclass_variants()
    # exact-threshold boundaries: 10^-max(p,1) and just-below for each p
    for p in (0, 1, 2, 3, 8):
        out.append(exact(1, -max(p, 1)))                    # == cutoff (kept)
        out.append(exact(1, -max(p, 1) - 1))                # < cutoff (normalized)
        out.append(exact(1, -max(p, 1) - 1, 1))             # negative, normalized
        out += _threshold_family(p)[:12]                    # materialization boundary
    return out


def main():
    _configure_django()
    prepatch_format, patched_format = _build_formats()
    rng = random.Random(11206)

    prec, emax, etiny = check_ambient_context()
    n_thresh = check_threshold_binding()
    n_guard = check_guard_equivalence(rng)
    n_amount = check_guard_reads_amount_only(prepatch_format)
    n_pairs, n_typeonly = check_render_necessity(prepatch_format)
    check_plain_zero_binding(prepatch_format)
    check_domain_boundary()
    last_pos, n_pos, pos_diverging = check_position_range_boundary()
    n_tiny = check_input_magnitude_unbounded()

    dec_pos_choices = [None, 0, 1, 2, 3, 8]

    # boundary matrix
    n_boundary = 0
    for number in _boundary_decimals():
        for decimal_pos in dec_pos_choices:
            for ambient in AMBIENTS:
                check_reference(prepatch_format, patched_format, number,
                                decimal_pos, ambient)
                n_boundary += 1

    # randomized fuzz
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
            # magnitudes with more significant digits than the ambient precision,
            # placed at the materialization boundary of a random position count
            m = max(rng.choice([0, 1, 2, 3, 8]), 1)
            digits = '9' * rng.randint(25, 32) + ''.join(
                rng.choice('0123456789') for _ in range(rng.randint(0, 8)))
            return cls(exact(int(digits), -(len(digits) + m - 1),
                             rng.randint(0, 1)))
        return cls(rng.choice(['0', '-0', '3.', '3.0', '1e16', '9e9999',
                               '1e-200', '1e-300', '0E-303', '1.000']))

    n_fuzz = 20000
    for _ in range(n_fuzz):
        number = rand_dec()
        decimal_pos = rng.choice(dec_pos_choices)
        ambient = rng.choice(AMBIENTS)
        check_reference(prepatch_format, patched_format, number, decimal_pos,
                        ambient)

    print("G-AX OK: ambient working precision %d (ties to even) == workingDigits; "
          "resolution==cutoff for decimal_pos 0..%d; guard equivalence "
          "(ratAbs amount < guardCutoff <-> abs(number) < cutoff) sound on %d "
          "threshold/high-significance probes; the real guard agrees on %d "
          "equal-amount pair probes (so the decision reads `amount` only); "
          "A-reference (patched == renderDecimal(clampSmall(carrier))) sound on "
          "%d boundary + %d fuzz inputs, subclass inputs included; render "
          "necessity measured on %d equal-amount pairs that render differently, "
          "%d of them with equal as_tuple(); domain of correspondence bounded at "
          "Emax=%d and, for requested position counts, at %d (= -Etiny %d - "
          "workingDigits): %d threshold probes agree at the last three admitted "
          "counts, %s past it; below-Etiny input magnitudes agree on %d probes "
          "at admitted counts, so the input itself is not bounded"
          % (prec, n_thresh - 1, n_guard, n_amount, n_boundary, n_fuzz, n_pairs,
             n_typeonly, emax, last_pos, -etiny, n_pos,
             ", ".join("%d disagreement(s) at decimal_pos=%d" % (v, k)
                       for k, v in sorted(pos_diverging.items())),
             n_tiny))
    return 0


if __name__ == "__main__":
    sys.exit(main())
