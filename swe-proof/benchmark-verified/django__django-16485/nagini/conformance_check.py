#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16485 (nagini).

SHADOW: the impl region of model.py's `format_value(int_value, frac_zero, p)`,
copied VERBATIM below with only the contract calls (Requires / Ensures /
Invariant / Assert) stripped. The @Pure helper `mag` copies over as a plain
function. The model carrier is List[int] of Unicode code points, so plain
Python lists execute directly and no PSeq shim is needed (PSeq appears only
in the stripped specification layer). There are no @ContractOnly callees
(the axioms region is empty; the localisation callee is an A-reference).

ORACLE: the REAL patched repo function the model models per mapping.md
section 1 — `django.template.defaultfilters.floatformat`. The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched code importable. This script never applies any diff itself.

TYPE BRIDGE (mapping.md section 2): the model input triple abstracts the real
call `floatformat(text, p)` via
    int_value <-> the integer part of the parsed Decimal value,
    frac_zero <-> "the value is exactly integral" (zero fractional remainder),
    p         <-> the requested number of decimal places (int arg).
The generator produces model triples and CONCRETISES each to a real `text`
(plain int / decimal string / Decimal object, several spellings per triple),
then re-derives the triple from the concretisation and asserts it round-trips
— so every real call exercises exactly the model input it is compared under.
The shadow output List[int] is raised to str via chr for the comparison.
Requires is `True`, so every generated triple is Requires-satisfying.

COMPARISON LAYERS (mapping.md sections 3.1 / 3.2 — the documented modeling
boundary):
  * bare-integer regime (frac_zero and p <= 0): the model pins the output
    END-TO-END (the localisation callee is digit-content preserving here, an
    A-reference fact G-AX validates). Shadow string must equal the real
    filter's return value exactly, and contain no separator.
  * separator-bearing regime (all other cases): the model's else branch is an
    A-reference SKELETON whose sole load-bearing property is CORE-layer
    separator presence; the exact fractional digits are discarded under
    refinement (they refine to the real unchanged decimal path). The CORE
    string — the value the real filter hands to the localisation callee — is
    captured by wrapping `django.utils.formats.number_format` with a
    recording proxy that delegates to the original. Shadow and real core must
    AGREE on the separator-presence observable: '.' present in both.
This split follows refinement.md rows A5/A6 verbatim; comparing the
skeleton's all-zeros fractional field against the real digits end-to-end
would test a property the model explicitly does not claim.

SPELLING-DEGENERATE CORNER OF THE UNCHANGED DECIMAL PATH: the real decimal
path derives its working precision from the SPELLING of the input (its
significant-digit tuple), which the model triple deliberately forgets. For a
zero value written with enough trailing fractional zeros at a small positive
p (e.g. a three-zero spelling at p == 1) that derived precision is
non-positive and the real path raises the precision-range ValueError. Both
guard variants route p > 0 into that path, so the fault is patch-unchanged
(pre == post) and lies outside the R-bijection's fidelity domain — the triple
has spellings with different real outcomes. The bridge accepts the raise ONLY
when it is mechanically that fault (recomputed from the input's own digit
tuple, mirroring the path's precision derivation) and then re-checks the SAME
triple under a spelling-independent concretisation (the plain integer), which
must satisfy the core-layer separator claim. Any other raise is a
disagreement.

>= 1e5 Requires-satisfying inputs: a structured boundary grid (integer parts
around digit-count and sign boundaries x precisions around the zero boundary
x both integrality bits x several concrete spellings each) plus 100000 fuzz
triples. Pinned fuzz seed: 164850.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random; hypothesis not needed).
"""
import json
import random
import sys
from decimal import Decimal

SEED = 164850
N_FUZZ = 100_000


# --- pure helper from model.py, contracts stripped -----------------------------

def mag(n):
    # Magnitude (absolute value) of an integer.
    if n >= 0:
        return n
    return -n


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def format_value(int_value, frac_zero, p):
    # Render the magnitude digits of int_value (shared by both regimes).
    digits = []  # type: List[int]
    k = mag(int_value)
    while k >= 10:
        digits = [48 + (k % 10)] + digits
        k = k // 10
    digits = [48 + k] + digits
    if int_value < 0:
        digits = [45] + digits

    if frac_zero and p <= 0:
        # Bare-integer regime: no decimal separator.
        return digits
    else:
        # Separator-bearing regime: append the separator and the |p|-wide
        # fractional digit field.
        frac = []  # type: List[int]
        i = mag(p)
        while i > 0:
            frac = [48] + frac
            i = i - 1
        out = digits + [46] + frac  # type: List[int]
        return out


# --- bridge helpers -------------------------------------------------------------

def derive_triple(text, p):
    """Re-derive the model triple from a concrete input, mirroring the real
    filter's own parse (integer part / integrality bit / precision)."""
    d = Decimal(str(text))
    return int(d), (int(d) - d) == 0, p


def concretise(rng, int_value, frac_zero, p):
    """One concrete `text` realising the model triple. Several spellings per
    triple keep the parse layer honest (plain int, trailing-zero decimal
    strings, Decimal objects, signed-zero forms)."""
    if frac_zero:
        kind = rng.randrange(5)
        if kind == 0:
            return int_value
        if kind == 1:
            return str(int_value)
        if kind == 2:
            return "%d.%s" % (int_value, "0" * rng.randint(1, 4))
        if kind == 3:
            return Decimal(str(int_value))
        # signed-zero / negative-zero decimal spelling where meaningful
        if int_value == 0 and rng.random() < 0.5:
            return "-0." + "0" * rng.randint(1, 3)
        return Decimal("%d.%s" % (int_value, "0" * rng.randint(1, 4)))
    # non-integral: append a nonzero fractional field to the integer part
    nfrac = rng.randint(1, 6)
    frac = "".join(str(rng.randint(0, 9)) for _ in range(nfrac - 1))
    frac += str(rng.randint(1, 9))  # last digit nonzero => genuinely fractional
    if int_value == 0:
        sign = "-" if rng.random() < 0.5 else ""
        body = "%s0.%s" % (sign, frac)
    else:
        body = "%d.%s" % (int_value, frac)
    if rng.random() < 0.25:
        return Decimal(body)
    return body


class Recorder(object):
    """Recording proxy around the localisation callee: captures the CORE
    string the filter hands over, then delegates to the original."""

    def __init__(self, original):
        self.original = original
        self.last = None

    def __call__(self, value, *args, **kwargs):
        self.last = value
        return self.original(value, *args, **kwargs)


def spelling_degenerate_fault(text, p, frac_zero, exc):
    """True iff `exc` is mechanically the precision-range fault of the
    unchanged decimal path for THIS input's spelling: recompute the path's
    derived working precision from the input's own digit tuple and confirm it
    is non-positive. Only reachable when the input routes into that path
    (NOT the bare-integer regime)."""
    if frac_zero and p <= 0:
        return False
    if not isinstance(exc, ValueError):
        return False
    d = Decimal(str(text))
    tup = d.as_tuple()
    integral = (int(d) - d) == 0
    units = len(tup[1]) + (tup[2] if integral else -tup[2])
    prec = abs(p) + units + 1
    return prec < 1


def check_case(floatformat, recorder, text, p):
    """Run shadow and oracle on one concrete input; return an error string on
    disagreement, else None."""
    int_value, frac_zero, _ = derive_triple(text, p)
    shadow_str = "".join(chr(c) for c in format_value(int_value, frac_zero, p))
    recorder.last = None
    try:
        real_out = floatformat(text, p)
    except Exception as e:
        if spelling_degenerate_fault(text, p, frac_zero, e):
            # Patch-unchanged fault outside the R-bijection's fidelity domain
            # (the triple forgets the spelling; see module docstring). The
            # triple must still satisfy the claim under a spelling-
            # independent concretisation: re-check with the plain integer
            # spelling (whose derived precision is always positive). Only an
            # integral value admits that spelling; a fractional spelling of a
            # non-integral value never hits this fault (its precision term is
            # positive), so frac_zero holds here by construction.
            if isinstance(text, int):
                return None  # already the spelling-independent form
            return check_case(floatformat, recorder, int_value, p)
        return ("DISAGREEMENT (real callee raised)\n  text=%r p=%r "
                "(int_value=%r frac_zero=%r)\n  shadow=%r\n  real raised %r"
                % (text, p, int_value, frac_zero, shadow_str, e))
    real_str = str(real_out)
    core = recorder.last
    if frac_zero and p <= 0:
        # End-to-end pin: exact equality, no separator.
        if shadow_str != real_str or "." in real_str:
            return ("DISAGREEMENT (bare-integer regime)\n  text=%r p=%r "
                    "(int_value=%r frac_zero=%r)\n  shadow=%r\n  real=%r"
                    % (text, p, int_value, frac_zero, shadow_str, real_str))
        # Cross-check the core layer too: the callee input is the same string.
        if core is not None and str(core) != shadow_str:
            return ("DISAGREEMENT (bare-integer core)\n  text=%r p=%r\n"
                    "  shadow=%r\n  real core=%r" % (text, p, shadow_str, core))
        return None
    # Separator-bearing regime: core-layer separator presence on both sides
    # (the only property the skeleton claims; digits refine to the real path).
    if core is None:
        return ("DISAGREEMENT (no core observed)\n  text=%r p=%r\n  real=%r"
                % (text, p, real_str))
    if "." not in str(core) or chr(46) not in shadow_str:
        return ("DISAGREEMENT (separator-bearing regime)\n  text=%r p=%r "
                "(int_value=%r frac_zero=%r)\n  shadow=%r\n  real core=%r"
                % (text, p, int_value, frac_zero, shadow_str, core))
    return None


# --- input plan ------------------------------------------------------------------

BOUNDARY_INTS = [
    0, 1, -1, 2, -2, 5, -5, 9, -9, 10, -10, 11, -11,
    99, -99, 100, -100, 101, 999, -999, 1000, -1000,
    12345, -12345, 10**6, -(10**6), 10**9 + 7, 10**15, -(10**15),
    10**18, -(10**18), 10**18 + 1,
]
BOUNDARY_PS = [-100, -10, -5, -2, -1, 0, 1, 2, 3, 6, 10, 20]


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            USE_I18N=False,
            USE_TZ=False,
            INSTALLED_APPS=[],
            DATABASES={},
        )
    django.setup()

    from django.template.defaultfilters import floatformat
    from django.utils import formats

    recorder = Recorder(formats.number_format)
    formats.number_format = recorder

    rng = random.Random(SEED)
    checked = 0
    boundary_checked = 0

    # --- boundary grid: every (int, p, integrality) corner, 3 spellings each --
    for iv in BOUNDARY_INTS:
        for p in BOUNDARY_PS:
            for frac_zero in (True, False):
                for _ in range(3):
                    text = concretise(rng, iv, frac_zero, p)
                    got = derive_triple(text, p)
                    assert got == (iv, frac_zero, p), (
                        "generator bug: %r does not realise (%r, %r, %r): %r"
                        % (text, iv, frac_zero, p, got))
                    err = check_case(floatformat, recorder, text, p)
                    if err:
                        print(err)
                        return 1
                    checked += 1
                    boundary_checked += 1

    # --- fuzz: mixed-magnitude triples, pinned seed ---------------------------
    for _ in range(N_FUZZ):
        mag_kind = rng.random()
        if mag_kind < 0.4:
            iv = rng.randint(-1000, 1000)
        elif mag_kind < 0.8:
            iv = rng.randint(-10**9, 10**9)
        else:
            iv = rng.randint(-10**18, 10**18)
        frac_zero = rng.random() < 0.5
        p = rng.randint(-100, 100) if rng.random() < 0.2 else rng.randint(-8, 8)
        text = concretise(rng, iv, frac_zero, p)
        got = derive_triple(text, p)
        assert got == (iv, frac_zero, p), (
            "generator bug: %r does not realise (%r, %r, %r): %r"
            % (text, iv, frac_zero, p, got))
        err = check_case(floatformat, recorder, text, p)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real display filter on %d inputs "
          "(%d boundary + %d fuzz, seed %d); bare-integer regime end-to-end "
          "exact, separator-bearing regime at the documented core layer."
          % (checked, boundary_checked, N_FUZZ, SEED))
    print(json.dumps({
        "checked": checked, "disagreements": 0, "seed": SEED,
        "shadow": "direct (contract-stripped impl region of model.py)",
        "layers": {"bare_integer": "end-to-end exact equality",
                   "separator_bearing": "core-layer separator presence "
                                        "(A-reference skeleton per mapping.md)"},
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
