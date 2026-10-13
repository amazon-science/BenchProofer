#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13023 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (there are none inside the impl region itself; the pre/post
conditions live outside it). The model's user-defined exception classes copy
over unchanged. The three @ContractOnly callees (`construct_numeric`,
`from_floating`, `accepted_value`) are axiomatized stand-ins for REAL repo
callees, so here each one calls the REAL callee it models (mapping.md sec 1/3):

  * ``construct_numeric``  -> the stdlib canonical numeric constructor
    ``decimal.Decimal(value)``; its four distinct low-level rejection classes
    are re-raised as the model's user-defined stand-ins
    (ConstructorMalformedError / ConstructorOperandError /
    ConstructorDomainError / ConstructorRangeError), which is exactly the
    class<->stand-in binding mapping.md sec 1 declares. The fourth
    (OverflowError -> ConstructorRangeError) is the shape the coercion does NOT
    classify: the shadow lets it propagate, exactly as the real function does.
  * ``from_floating``      -> the field's rounding-context float conversion
    ``field.context.create_decimal_from_float(value)`` (the same field
    instance the oracle runs on, so both sides share one context), as the
    accepted-case value accessor.
  * ``convert_floating``   -> that SAME call, as the accept-or-refuse callee the
    floating branch dispatches to. Distinct from the constructor and invoked
    OUTSIDE the coercion's uniform-failure handling, so its wrong-typed-operand
    rejection (raised for a value satisfying the branch's isinstance test
    without being a real float) propagates, exactly as the real function does.
  * ``accepted_value``     -> the constructor's own returned token on an
    accepted value (the same ``decimal.Decimal(value)`` call, viewed as a
    value accessor); the shadow's accepted path returns it via
    ``construct_numeric`` directly.

ORACLE: the REAL patched repo function the model models per mapping.md sec 1 —
``django.db.models.fields.DecimalField.to_python`` on a
``DecimalField(max_digits=4, decimal_places=2)`` instance (the shape the
instance's tests use). The gate applies patch.diff to /testbed before this
script runs. Outcomes are compared as observations:

  normal return  -> compared by null-ness and, for constructed Decimals,
                    exact string form (total value equality, NaN-safe);
  validation failure (django.core.exceptions.ValidationError)
                 <-> the shadow's ValidationFailure;
  any other escaping exception class -> reported as a raw escape (and a
                    disagreement if the other side classified differently).

TYPE BRIDGE (mapping.md sec 2): the supplied value collapses to an integer
acceptance kind: None -> 0; a value satisfying the coercion's floating-branch
test -> 1 if the floating conversion accepts it as an operand, else 7 if that
conversion refuses it (the branch guards on isinstance while the conversion
type-checks exactly, so the guard admits strictly more); otherwise the kind in
{2,3,4,5,6} that the real constructor's behaviour on the value exhibits
(accept / malformed-literal / wrong-typed-operand / out-of-domain /
out-of-representable-range). The floating branch has THREE outcomes, not two:
the conversion also refuses a value whose operand type it accepts (it takes int
as well as float) but whose magnitude lies outside what its own context can
represent, with a class distinct from TypeError and from the constructor's
OverflowError -> kind 8. Every Python value therefore lowers to a
Requires-satisfying kind in 0..8, and a value that lowered to NO kind is a hard
FAILURE of this gate (not a skip), because a silent skip is how an undeclared
escaping class would hide from the comparison.

INPUTS: >= 1e5 Requires-satisfying values = boundary cases covering every
kind (including the instance's 8 canonical invalid values, and the kind-6
coordinate forms on both sides of the C ssize_t/long boundary) + 100000 fuzz
values over all shapes, whose coordinate-form generator now straddles that
boundary. Pinned fuzz seed: 130230.

COST: a kind-8 probe has to straddle the conversion context's Emax (999999), so
it is a million-digit integer, and one comparison of it costs ~40s (an exact
million-digit conversion on the bridge, on the shadow and on the oracle). The
float-branch pool holding those probes is therefore built once and shared, and
each of its members is compared once, in the boundary pass; a fuzz draw that
re-draws a pool member is the identical object and reuses that comparison. The
compared value set, the pool's order and the seeded draw sequence are all
unchanged by this -- only the repetition is.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib only (plain random; no hypothesis needed).
"""
import decimal
import json
import random
import sys

SEED = 130230
N_FUZZ = 100000


# --- exception classes from model.py (user-defined stand-ins), verbatim ------

class ConstructorMalformedError(Exception):
    pass


class ConstructorOperandError(Exception):
    pass


class ConstructorDomainError(Exception):
    pass


class ConstructorRangeError(Exception):
    pass


class ConversionRangeError(Exception):
    pass


class ValidationFailure(Exception):
    pass


# --- real-callee plumbing ------------------------------------------------------
# The model abstracts the supplied value to an integer kind; the axiomatized
# callees are functions of the VALUE in the repo. The current value is threaded
# through a module-level holder so the impl region below can stay verbatim
# (kind-only signatures).

_CURRENT = [None]   # the value the current shadow call operates on
_FIELD = None       # the DecimalField instance (set in main; shared context)


def from_floating():
    """REAL callee: the field's rounding-context float conversion (value
    accessor for the accepted floating case)."""
    return _FIELD.context.create_decimal_from_float(_CURRENT[0])


def convert_floating(kind):
    """REAL callee: the SAME rounding-context float conversion, viewed as the
    accept-or-refuse callee the floating branch dispatches to. It is DISTINCT
    from the canonical constructor and is invoked OUTSIDE the coercion's
    uniform-failure handling. Its wrong-typed-operand rejection surfaces as the
    model's ConstructorOperandError stand-in (the same low-level class the
    constructor raises on kind 4, per mapping.md sec 1)."""
    try:
        return _FIELD.context.create_decimal_from_float(_CURRENT[0])
    except TypeError:
        raise ConstructorOperandError()
    except Exception:                            # noqa: BLE001
        # the conversion accepted the operand TYPE but refused the magnitude,
        # which lies outside what its own context can represent: a rejection
        # class distinct from TypeError and from the constructor's OverflowError
        raise ConversionRangeError()


def construct_numeric(kind):
    """REAL callee: the canonical numeric constructor, with its four distinct
    rejection classes surfaced as the model's user-defined stand-ins (the
    class<->stand-in binding of mapping.md sec 1). The accepted return IS the
    constructor's own token (the accepted_value accessor's value)."""
    try:
        return decimal.Decimal(_CURRENT[0])
    except decimal.InvalidOperation:
        raise ConstructorMalformedError()
    except TypeError:
        raise ConstructorOperandError()
    except OverflowError:
        raise ConstructorRangeError()
    except ValueError:
        raise ConstructorDomainError()


# --- the impl region of model.py, verbatim (no contract calls to strip) -------

def coerce_to_numeric(kind):
    if kind == 0:
        return None
    if kind == 1 or kind == 7 or kind == 8:
        return convert_floating(kind)
    try:
        return construct_numeric(kind)
    except ConstructorMalformedError:
        raise ValidationFailure()
    except ConstructorOperandError:
        raise ValidationFailure()
    except ConstructorDomainError:
        raise ValidationFailure()


# --- type bridge: value -> acceptance kind (mapping.md sec 2) ------------------

def value_kind(value):
    """None -> 0; a value satisfying the coercion's floating-branch test -> 1 if
    the floating conversion accepts it, else 7 if that conversion refuses it as a
    wrong-typed operand; else the kind {2,3,4,5,6} the real constructor's
    behaviour exhibits. Returns None for an undeclared rejection class (outside
    the Requires domain)."""
    if value is None:
        return 0
    if isinstance(value, float):
        # The branch's guard is isinstance, but the conversion type-checks
        # exactly, so the guard admits values the conversion refuses (kind 7).
        try:
            _FIELD.context.create_decimal_from_float(value)
            return 1
        except TypeError:
            return 7
        except Exception:
            # accepted as an operand TYPE but refused for magnitude: kind 8, a
            # distinct rejection class from both TypeError and the
            # constructor's OverflowError
            return 8
    try:
        decimal.Decimal(value)
        return 2
    except decimal.InvalidOperation:
        return 3
    except TypeError:
        return 4
    except OverflowError:
        return 6
    except ValueError:
        return 5
    except Exception:
        return None


# --- outcome observation --------------------------------------------------------

def _decstr(d):
    # exact total form; distinguishes 3 / 3.0 / -0 / NaN / Infinity reliably
    return str(d)


# mapping.md sec 2: each user-defined stand-in denotes one REAL repo exception
# class (a builtin in an `Exsures` crashes the Nagini translator, which is the
# only reason the stand-ins exist). A raw escape must therefore be compared under
# the stand-in -> real-class binding, or the shadow and the oracle would be
# reported as disagreeing purely because the model had to rename the class.
_STANDIN_TO_REAL = {
    "ConstructorMalformedError": "InvalidOperation",
    "ConstructorOperandError": "TypeError",
    "ConstructorDomainError": "ValueError",
    "ConstructorRangeError": "OverflowError",
    "ConversionRangeError": "Overflow",
}


def shadow_outcome(value):
    _CURRENT[0] = value
    kind = value_kind(value)
    if kind is None:
        return ("out-of-domain",)
    try:
        r = coerce_to_numeric(kind)
    except ValidationFailure:
        return ("validation-failure",)
    except Exception as e:  # noqa: BLE001 — a raw escape from the shadow
        name = type(e).__name__
        return ("raw", _STANDIN_TO_REAL.get(name, name))
    if r is None:
        return ("return-none",)
    return ("return", _decstr(r))


def real_outcome(field, ValidationError, value):
    try:
        r = field.to_python(value)
    except ValidationError:
        return ("validation-failure",)
    except Exception as e:  # noqa: BLE001 — a raw escape from the repo function
        return ("raw", type(e).__name__)
    if r is None:
        return ("return-none",)
    return ("return", _decstr(r))


# --- inputs ---------------------------------------------------------------------

def boundary_cases():
    cases = [
        # absent (kind 0)
        None,
        # floating (kind 1) incl. IEEE specials and extremes
        0.0, -0.0, 1.0, -1.0, 2.4, 2.0625, 2.1875, 3.1415926535897,
        1e308, -1e308, 1e-308, 1.5e-300,
        float("inf"), float("-inf"), float("nan"),
        # constructor-accepted (kind 2)
        "3", "3.14", "0", "-1", "1e3", "2.0625", "+0.0", " 3.5 ", "  10\n",
        "1_000", "Infinity", "-Infinity", "1E+6", ".5", "5.", "NaN", "nan",
        "sNaN",
        0, 1, -7, True, False, 2 ** 64, 10 ** 30,
        decimal.Decimal("1.5"), decimal.Decimal("-0"), decimal.Decimal("NaN"),
        # malformed literal (kind 3)
        "abc", "non-numeric string", "1.2.3", "$5", "12,34", "", " ",
        "NaNx", "1 2", "0x10", "one", "--3", "1/2", "\x00",
        # wrong-typed operand (kind 4)
        {}, set(), object(), complex(), b"non-numeric byte-string", b"123",
        {1: 2}, {"a"}, frozenset(), bytearray(b"x"), 3.5j, type, (lambda: 0),
        range(3), Ellipsis, NotImplemented,
        # out-of-domain (kind 5)
        (), [], (1, 2), [1, 2, 3], [0], (0,),
        (2, (1,), 0), (-1, (1,), 0), ("0", (1,), 0), (0, "1", 0),
        (0, (10,), 0), (0, (-1,), 0), (0, (1,), "x"), (0, (1,), 1.5),
        (0, (1,), 0, 0), (0, None, 0), (0, ((1,),), 0),
        # accepted coordinate forms (kind 2) — the same arm, inside the range
        (0, (1,), 0), (1, (1, 2, 3), -2), (0, (), 0), (0, (1,), "F"),
        (0, (1,), "n"), (0, (1,), "N"), (0, [1], 0),
        # out-of-representable-range (kind 6) — the UNCLASSIFIED shape, on the
        # far side of the C ssize_t/long boundary in each component position
        (0, (1,), 2 ** 63), (0, (1,), -2 ** 63 - 1), (0, (1,), 10 ** 100),
        (0, (1,), -10 ** 100), (0, (10 ** 100,), 0), (10 ** 100, (1,), 0),
        [0, (1,), 2 ** 63], [0, (10 ** 100,), 0],
        # ...and the boundary itself, which is still kind 3 (InvalidOperation)
        (0, (1,), 2 ** 63 - 1), (0, (1,), -2 ** 63),
        # the instance's 8 canonical invalid values, verbatim
        (), [], {}, set(), object(), complex(),
        "non-numeric string", b"non-numeric byte-string",
    ]
    # floating-branch values the conversion REFUSES (kind 7): they satisfy the
    # coercion's isinstance(value, float) test without being real floats, so the
    # branch is taken and the conversion's TypeError escapes (line 1501 is
    # outside the try). Genuine float subclasses are kind 1 and included above.
    cases.extend(_float_branch_refused())
    return cases


_SPOOFERS = None    # the float-branch pool, built once (see _float_branch_refused)


def _float_branch_refused():
    """The float-branch pool, built ONCE and shared. The pool is a constant of
    this check and its kind-8 members are million-digit integers, so rebuilding
    it per fuzz draw repeated that construction ~500 times for no added
    coverage. Membership, order and length are unchanged, so the seeded
    generator draws exactly the same sequence it drew before."""
    global _SPOOFERS
    if _SPOOFERS is None:
        _SPOOFERS = _build_float_branch_refused()
    return _SPOOFERS


def _build_float_branch_refused():
    """Values satisfying isinstance(v, float) that create_decimal_from_float
    refuses as an operand. Django's own SimpleLazyObject is one such class."""
    class _AttrSpoof:
        __class__ = float

    class _PropSpoof:
        @property
        def __class__(self):
            return float

    out = [_AttrSpoof(), _PropSpoof()]
    try:
        from unittest.mock import MagicMock, Mock, NonCallableMock
        out += [MagicMock(spec=float), Mock(spec=float),
                NonCallableMock(spec=float)]
    except Exception:                            # noqa: BLE001
        pass
    try:
        from django.utils.functional import SimpleLazyObject
        for fac in (lambda: 1.5, lambda: float("inf"), lambda: float("nan"),
                    lambda: 0.0, lambda: -1e308, lambda: 2.0625):
            out.append(SimpleLazyObject(fac))
    except Exception:                            # noqa: BLE001
        pass
    # genuine float subclass -> kind 1 (accepted), the control for the above
    class _MyFloat(float):
        pass
    out += [_MyFloat(1.5), _MyFloat(float("inf"))]
    # INT-payload spoofers straddling the conversion context's Emax: the
    # conversion accepts int operands too, so these pass its exact type check
    # (they are NOT kind-7 TypeError cases) and are refused only for magnitude
    # -> kind 8. Genuine floats cap near 1e308, far inside Emax, so a
    # genuine-floats-plus-TypeError-spoofers generator cannot reach this
    # boundary. Both sides of it are included.
    class _IntSpoof(int):
        __class__ = float
    _emax = _FIELD.context.Emax
    out += [_IntSpoof(10 ** _emax), _IntSpoof(10 ** (_emax + 1)),
            _IntSpoof(-(10 ** (_emax + 1))), _IntSpoof(10 ** (_emax + 5)),
            _IntSpoof(0), _IntSpoof(7), _IntSpoof(-7)]
    return out


def fuzz_value(rng):
    shape = rng.randint(0, 9)
    if shape == 0:
        return None
    if shape == 1:
        # floats: mostly finite, occasional specials, and occasionally a value
        # that satisfies the floating-branch test WITHOUT being a real float
        # (kind 7) — the shape a genuine-floats-only generator never reaches.
        p = rng.randint(0, 19)
        if p == 0:
            return rng.choice([float("inf"), float("-inf"), float("nan"),
                               0.0, -0.0])
        if p == 1:
            return rng.choice(_float_branch_refused())
        return rng.uniform(-1e6, 1e6) * (10.0 ** rng.randint(-30, 30))
    if shape == 2:
        return rng.randint(-10 ** rng.randint(0, 24), 10 ** rng.randint(0, 24))
    if shape == 3:
        # numeric-ish strings (some accepted, some malformed)
        parts = []
        if rng.random() < 0.5:
            parts.append(rng.choice(["", "+", "-", "--"]))
        parts.append("".join(rng.choice("0123456789")
                             for _ in range(rng.randint(0, 6))))
        if rng.random() < 0.5:
            parts.append(".")
            parts.append("".join(rng.choice("0123456789")
                                 for _ in range(rng.randint(0, 6))))
        if rng.random() < 0.3:
            parts.append(rng.choice(["e", "E"])
                         + rng.choice(["", "+", "-"])
                         + "".join(rng.choice("0123456789")
                                   for _ in range(rng.randint(0, 3))))
        return "".join(parts)
    if shape == 4:
        # junk strings
        junk = "abcXYZ$%@,/ \t!?one two_" + "0123456789.-+eE"
        return "".join(rng.choice(junk) for _ in range(rng.randint(0, 12)))
    if shape == 5:
        # wrong-typed operands
        c = rng.randint(0, 5)
        if c == 0:
            return {rng.randint(0, 9): rng.randint(0, 9)}
        if c == 1:
            return set(rng.randint(0, 9) for _ in range(rng.randint(1, 4)))
        if c == 2:
            return complex(rng.random(), rng.random())
        if c == 3:
            return object()
        if c == 4:
            return bytes(rng.randint(0, 255) for _ in range(rng.randint(0, 6)))
        return bytearray(rng.randint(0, 255) for _ in range(rng.randint(0, 6)))
    if shape == 6:
        # list/tuple shapes, incl. 3-element coordinate-like ones. The component
        # pool STRADDLES the C ssize_t/long boundary, so this generator reaches
        # the kind-6 (OverflowError) rejection as well as kind 2/5 — the previous
        # small-int-only pool is exactly what let the boundary go unshadowed.
        if rng.random() < 0.35:
            big = rng.choice([2 ** 63, 2 ** 63 + 1, -2 ** 63 - 1, 10 ** 100,
                              -10 ** 100, 10 ** 400])
            where = rng.randint(0, 2)
            coord = [rng.choice([0, 1]), (rng.randint(0, 9),), rng.randint(-5, 5)]
            if where == 0:
                coord[2] = big
            elif where == 1:
                coord[1] = (abs(big),)
            else:
                coord[0] = abs(big)
            return tuple(coord) if rng.random() < 0.5 else list(coord)
        n = rng.randint(0, 5)
        pool = [-3, -1, 0, 1, 2, 9, 12, 2 ** 63 - 1, -2 ** 63, 2 ** 63,
                -2 ** 63 - 1, 10 ** 100]
        seq = [rng.choice(pool) for _ in range(n)]
        return tuple(seq) if rng.random() < 0.5 else list(seq)
    if shape == 7:
        return decimal.Decimal(rng.randint(-10 ** 6, 10 ** 6)) / 100
    if shape == 8:
        return rng.choice([True, False])
    # accepted string specials
    return rng.choice(["Infinity", "-Infinity", "NaN", "-NaN", "sNaN",
                       "1_0", " 7 ", "\t8\n", ".5", "5."])


# --- driver ---------------------------------------------------------------------

def main():
    global _FIELD
    import django.conf
    if not django.conf.settings.configured:
        django.conf.settings.configure()
    from django.core.exceptions import ValidationError
    from django.db.models.fields import DecimalField

    _FIELD = DecimalField(max_digits=4, decimal_places=2)

    checked = 0
    out_of_domain = 0

    # The float-branch pool is a FIXED shared list and EVERY member of it is
    # compared in the boundary pass below. The fuzz generator draws from that
    # same list, so such a draw is the IDENTICAL object, and both sides of the
    # comparison are deterministic functions of the value -- so the outcome
    # established for that member is reused rather than recomputed. Nothing
    # leaves the compared set and every draw is still accounted for: the pool's
    # kind-8 members straddle the conversion context's Emax, which makes each of
    # them a million-digit integer whose single comparison costs ~40s of exact
    # conversion (bridge, shadow and oracle), and the generator re-draws those
    # four values ~100 times.
    pool_ids = set()
    known = {}

    def diff(value):
        vid = id(value)
        if vid in known:
            return known[vid]
        so = shadow_outcome(value)
        if so == ("out-of-domain",):
            res = "skip"
        else:
            ro = real_outcome(_FIELD, ValidationError, value)
            if so != ro:
                print("DISAGREEMENT on value %r (type %s, bridge kind %r):\n"
                      "  shadow (impl region + real callees) = %r\n"
                      "  real (patched DecimalField.to_python) = %r"
                      % (value, type(value).__name__, value_kind(value), so, ro))
                res = "fail"
            else:
                res = "ok"
        if vid in pool_ids:
            known[vid] = res
        return res

    boundary = boundary_cases()
    pool_ids.update(id(o) for o in _float_branch_refused())
    for v in boundary:
        r = diff(v)
        if r == "fail":
            return 1
        if r == "skip":
            out_of_domain += 1
        else:
            checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        v = fuzz_value(rng)
        r = diff(v)
        if r == "fail":
            return 1
        if r == "skip":
            out_of_domain += 1
        else:
            checked += 1

    if out_of_domain:
        # The bridge is TOTAL: mapping.md sec 2 claims every value lowers to a
        # kind in 0..8. A value that lowers to no kind would be silently skipped
        # here, which is exactly how an undeclared escaping class could hide from
        # this gate — so a skip is a HARD FAILURE, not a warning.
        print("BRIDGE-DOMAIN VIOLATION: %d values lowered to no declared kind, "
              "so the shadow was never compared against the real function on "
              "them. The bridge claims totality over 0..8; an undeclared "
              "rejection class means the model is missing a leg."
              % out_of_domain)
        return 1

    print("G-CONF OK: shadow impl == real patched DecimalField.to_python on "
          "%d inputs (%d boundary + %d fuzz, seed %d); 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "out_of_domain": out_of_domain,
                      "shadow": "direct (contract-stripped impl region; "
                                "axiomatized callees call the real "
                                "decimal constructor / float-context "
                                "conversion)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
