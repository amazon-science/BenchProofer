#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11206 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert and type comments) stripped. The
@Pure helpers (pow10 / threshold_exp / below_cutoff / zeros / zero_render /
opt_seq) copy over as plain functions on a small PSeq shim; only `pow10` is
actually reached by the stripped impl (the rest served the proof). There are
no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md --
`django.utils.numberformat.format`. The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched module
importable.

Input bridge (mapping.md section 2): a model input (coeff, exponent,
decimal_pos) is the magnitude decomposition of a Decimal `number`:
value = coeff * 10**exponent with coeff >= 0, obtained exactly from
`abs(number).as_tuple()` (the same decomposition axiom_check.py uses). The
modeled domain is `decimal_pos is not None` with a non-negative int, and the
'.' separator with default grouping (the pinned domain of mapping.md
section 3.1). Both signs of `number` are fed: the model discards the sign at
the decomposition, matching the repo function's magnitude-based decision.

Result bridge (mapping.md section 2): the shadow returns either a code-point
list (the collapsed rendering; '0'=48, '.'=46) or None ("no collapse, the
ordinary path governs"). So:

  * shadow is not None  ->  the real output must equal exactly the shadow's
    code points decoded to a string;
  * shadow is None      ->  the real output must equal the UNCHANGED ordinary
    rendering of `number` itself. That renderer is recovered from the real
    patched source by stripping the inserted collapse block and exec'ing the
    result (the pre-change function body, which has no collapse), then applied
    to the unchanged `number`. This keeps the check non-circular: if the
    shadow's decision diverges from the real one on any input, the two sides
    disagree.

>= 1e5 Requires-satisfying inputs: fixed boundary cases (problem-statement
witnesses, F2P/P2P magnitudes, the exact-threshold strict edge for
decimal_pos 0..29) + randomized fuzz straddling the visibility threshold.
Pinned fuzz seed: 11206.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import random
import re
import sys
import types
from decimal import Decimal, getcontext

SEED = 11206
N_TOTAL = 100_000

# Generous exact precision (comparisons/as_tuple are exact anyway).
getcontext().prec = 400

# --- configure Django settings before importing the formatter ----------------
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=False,
        USE_TZ=False,
        USE_L10N=False,
        USE_THOUSAND_SEPARATOR=False,
        DATABASES={},
        INSTALLED_APPS=[],
        USE_I18N=False,
    )
    django.setup()

from django.utils import numberformat as real_nf

patched_format = real_nf.format  # REAL patched callee (the oracle)


def build_base_format():
    """Recover the unchanged ordinary renderer: the same function with the
    inserted collapse block stripped (everything between the Decimal-branch
    header and the large-digit-budget comment), exec'd as a fresh module."""
    src_path = real_nf.__file__
    if src_path.endswith(".pyc"):
        src_path = src_path[:-1]
    with open(src_path, "r") as fh:
        src = fh.read()
    base_src, n = re.subn(
        r"(if isinstance\(number, Decimal\):\n)"
        r".*?"
        r"(\n        # Format values with more than 200 digits)",
        r"\1\2",
        src,
        flags=re.DOTALL,
    )
    if n != 1:
        raise SystemExit(
            "G-CONF ERROR: could not locate/strip the inserted block; n=%d" % n)
    mod = types.ModuleType("numberformat_base")
    mod.__dict__["__file__"] = src_path
    exec(compile(base_src, src_path + " (base)", "exec"), mod.__dict__)
    return mod.format


base_format = build_base_format()


# --- PSeq shim: immutable sequence with the ops the pure region uses ----------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(x):
    return PSeq._wrap(x)


# --- pure helpers from model.py, decorators/contracts stripped ---------------

def pow10(n):
    if n == 0:
        return 1
    return 10 * pow10(n - 1)


def threshold_exp(decimal_pos):
    if decimal_pos >= 1:
        return decimal_pos
    return 1


def below_cutoff(coeff, exponent, decimal_pos):
    if coeff == 0:
        return True
    if exponent + threshold_exp(decimal_pos) >= 0:
        return False
    return coeff < pow10(-(exponent + threshold_exp(decimal_pos)))


def zeros(n):
    if n == 0:
        return PSeq(48).take(0)
    return PSeq(48) + zeros(n - 1)


def zero_render(decimal_pos):
    if decimal_pos == 0:
        return PSeq(48)
    return PSeq(48, 46) + zeros(decimal_pos)


def opt_seq(x):
    if x is None:
        return PSeq(0).take(0)
    return ToSeq(x)


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def format_small(coeff, exponent, decimal_pos):
    # The visibility threshold is 10 ** -p; a magnitude strictly smaller than it
    # is treated as zero and rendered as a padded zero, otherwise this routine
    # contributes nothing and the ordinary path takes over.
    p = decimal_pos
    if p < 1:
        p = 1
    shifted = exponent + p
    is_small = False
    if coeff == 0:
        is_small = True
    elif shifted < 0 and coeff < pow10(-shifted):
        is_small = True
    if not is_small:
        return None
    # Build the padded-zero rendering. When at least one fractional place is
    # requested, build the run of zero digits by prepending (matching the
    # front-recursive `zeros`), then prefix the '0' and decimal separator.
    if decimal_pos == 0:
        result = [48]
        return result
    frac = []
    i = decimal_pos
    while i > 0:
        frac = [48] + frac
        i = i - 1
    result = [48, 46] + frac
    return result


# --- input bridge -------------------------------------------------------------

def coeff_exponent(number):
    """The non-negative magnitude decomposition used by model.py:
    value = coeff * 10**exponent, coeff >= 0 (the integer of the digit tuple)."""
    _, digits, exponent = abs(number).as_tuple()
    coeff = 0
    for d in digits:
        coeff = coeff * 10 + d
    return coeff, exponent


def check_case(number, decimal_pos):
    """Diff the shadow against the real function on one (number, decimal_pos).
    Returns an error string on disagreement, else None."""
    coeff, exponent = coeff_exponent(number)
    shadow = format_small(coeff, exponent, decimal_pos)
    real = patched_format(number, '.', decimal_pos)
    if shadow is not None:
        expected = ''.join(chr(c) for c in shadow)
        ok = real == expected
        got = expected
    else:
        # No collapse: the real output must be the unchanged ordinary
        # rendering of the very same value.
        got = base_format(number, '.', decimal_pos)
        ok = real == got
    if not ok:
        return ("DISAGREEMENT\n  number=%r decimal_pos=%d"
                "\n  coeff=%d exponent=%d"
                "\n  shadow=%r (-> %r)\n  real=%r"
                % (str(number), decimal_pos, coeff, exponent, shadow, got,
                   real))
    return None


# --- input pool ---------------------------------------------------------------

def boundary_cases():
    """(value-string, decimal_pos) pairs: problem-statement witnesses, the
    F2P/P2P magnitudes, strict-threshold edges, huge/ordinary/negative/zero."""
    cases = [
        ('1e-199', 2), ('1e-200', 2), ('1e-201', 2),
        ('1e-7', 8), ('1e-8', 8), ('1e-9', 8), ('1e-10', 8), ('1e-11', 8),
        ('0.00000001', 8),                  # == threshold: NOT collapsed
        ('9e-19', 2),
        ('.00000000000099', 0),
        ('0.' + '0' * 299 + '1234', 3),
        ('1' + '0' * 300, 3),
        ('1.2345e999', 2), ('9e9999', 3), ('9e201', 0), ('9e200', 0),
        ('0', 0), ('0', 5), ('0.0', 4), ('-0', 2),
        ('1234.5678', 2), ('-1234.33', 1),
        ('-9e-50', 4), ('-1e-3', 3), ('-1e-4', 3),
        ('0.1', 0), ('0.09', 0), ('0.05', 1), ('0.04', 1),
        ('0.001', 3), ('0.0009', 3),
    ]
    # the exact-threshold edge for every dp 0..29: at / ten-times / one-tenth /
    # negated / zero
    for dp in range(0, 30):
        e = dp if dp >= 1 else 1
        at = Decimal(1).scaleb(-e)
        for v in (at, at.scaleb(1), at.scaleb(-1), -at, Decimal(0)):
            cases.append((str(v), dp))
    return cases


def rand_case(rng):
    dp = rng.randint(0, 20)
    coeff = rng.randint(1, 9999)
    exp = rng.randint(-(dp + 8), 4)
    sign = rng.choice(['', '-'])
    number = Decimal('%s%dE%d' % (sign, coeff, exp))
    return number, dp


def main():
    rng = random.Random(SEED)
    checked = 0
    for value, dp in boundary_cases():
        err = check_case(Decimal(value), dp)
        if err:
            print(err)
            return 1
        checked += 1
    n_boundary = checked

    while checked < N_TOTAL:
        number, dp = rand_case(rng)
        err = check_case(number, dp)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real numberformat.format on %d inputs "
          "(%d boundary + %d fuzz, seed %d), 0 disagreements."
          % (checked, n_boundary, checked - n_boundary, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
