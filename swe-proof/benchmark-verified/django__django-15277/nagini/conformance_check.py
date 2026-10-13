#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15277 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with no changes
(the impl regions of this bundle contain no contract calls to strip — they are
already plain Python). There are no @Pure module-level helpers and no
@ContractOnly callees in this bundle; ``clean_charfield``'s impl calls the
other two modeled functions, and those shadows are used directly, exactly as
in model.py. ``LimitComparisonError`` is the model's user-defined stand-in for
the builtin exception the real comparison raises on an absent limit
(mapping.md section 2); the bridge below maps real ``TypeError`` <->
shadow ``LimitComparisonError``.

ORACLE: the REAL patched repo callees the model models per mapping.md
(PYTHONPATH=/testbed; the gate applies patch.diff before this script runs):

  * ``build_char_validators``  <->  the length-validator slot of a freshly
    constructed ``django.db.models.CharField``: the list of ``limit_value``s
    of its ``MaxLengthValidator`` entries (mapping.md section 2 bijection —
    each assembled length validator is abstracted to its limit).
  * ``compare_length``         <->  ``MaxLengthValidator.compare`` (the
    numeric "exceeds the limit" test), with the absent-limit case checked
    via the real ``TypeError``.
  * ``clean_charfield``        <->  the observable of running the assembled
    validators over a candidate value of the given length:
    ``Field.run_validators(value)`` raises ``ValidationError`` iff the length
    validator flags the candidate (a default CharField carries no other
    validators, so any ValidationError here IS the length flag). The model's
    boolean result maps to that flagged/not-flagged observable. The
    end-to-end ``clean`` path is also exercised for non-empty candidates
    (empty candidates are rejected earlier by the orthogonal blank-rejection
    validator, which is outside the modeled path — mapping.md section 2).

Type bridge (mapping.md section 2): ``max_length`` is identity
(``None``/positive int, the values a CharField carries); ``value_length`` is
the integer length of the candidate — realized as a string of exactly that
length, so the domain is ``value_length >= 0``.

>= 1e5 Requires-satisfying inputs: boundary grid + 100000 fuzz
(max_length, value_length) pairs + 20000 compare-only fuzz pairs.
Pinned fuzz seed: 415277.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the repo under test only.
"""
import json
import random
import sys

SEED = 415277
N_FUZZ = 100000
N_COMPARE_FUZZ = 20000


# --- model.py exception class (spec-region carrier, needed by the shadow) ----

class LimitComparisonError(Exception):
    pass


# --- the impl regions of model.py, verbatim ------------------------------------

def compare_length(value_length, limit):
    if limit is None:
        raise LimitComparisonError()
    return value_length > limit


def build_char_validators(max_length):
    validators = []  # type: list
    if max_length is not None:
        validators.append(max_length)
    return validators


def clean_charfield(max_length, value_length):
    validators = build_char_validators(max_length)
    flagged = False
    if len(validators) > 0:
        limit = validators[0]
        flagged = compare_length(value_length, limit)
    return flagged


# --- Django setup ---------------------------------------------------------------

def configure_django():
    """Configure Django just enough to import the ORM field + validator
    classes. Constructing a field and running its validators is pure Python;
    no database is touched."""
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=False)
    import django
    django.setup()


# --- oracles ---------------------------------------------------------------------

def real_limits(max_length):
    """The length-validator slot of a freshly constructed real field, as the
    list of limits (the mapping.md abstraction of the assembled validators)."""
    from django.db.models import CharField
    from django.core.validators import MaxLengthValidator
    if max_length is None:
        f = CharField()
    else:
        f = CharField(max_length=max_length)
    return [v.limit_value for v in f.validators
            if isinstance(v, MaxLengthValidator)]


def real_flag(max_length, value_length):
    """Run the real assembled validators over a candidate of the given length;
    return (flagged, crashed) where flagged means the length validator raised
    ValidationError and crashed means a non-ValidationError escaped (the
    absent-limit comparison failure channel)."""
    from django.db.models import CharField
    from django.core import exceptions
    if max_length is None:
        f = CharField()
    else:
        f = CharField(max_length=max_length)
    value = "x" * value_length
    try:
        f.run_validators(value)
    except exceptions.ValidationError:
        return True, False
    except TypeError:
        return False, True
    return False, False


def real_clean_completes(max_length, value_length):
    """The end-to-end observable: cleaning a non-empty candidate against a
    fresh field completes; ValidationError = length flag, TypeError = the
    absent-limit crash channel."""
    from django.db.models import CharField
    from django.core import exceptions
    if max_length is None:
        f = CharField()
    else:
        f = CharField(max_length=max_length)
    value = "x" * value_length
    try:
        f.clean(value, model_instance=None)
    except exceptions.ValidationError:
        return True, False
    except TypeError:
        return False, True
    return False, False


# --- differential driver ----------------------------------------------------------

def fail(msg):
    print(msg)
    sys.exit(1)


def check_pair(max_length, value_length, use_clean):
    """Diff shadow vs real on one (max_length, value_length) input."""
    # (a) assembled length-validator slot
    shadow_limits = build_char_validators(max_length)
    limits = real_limits(max_length)
    if shadow_limits != limits:
        fail("DISAGREEMENT on max_length=%r:\n"
             "  shadow build_char_validators = %r\n"
             "  real assembled limits        = %r"
             % (max_length, shadow_limits, limits))
    # (b) running the assembled validators over a candidate of this length
    try:
        shadow_flag = clean_charfield(max_length, value_length)
        shadow_crash = False
    except LimitComparisonError:
        shadow_flag, shadow_crash = False, True
    flag, crash = real_flag(max_length, value_length)
    if (shadow_flag, shadow_crash) != (flag, crash):
        fail("DISAGREEMENT on (max_length=%r, value_length=%r):\n"
             "  shadow clean_charfield = flagged=%r crashed=%r\n"
             "  real run_validators    = flagged=%r crashed=%r"
             % (max_length, value_length, shadow_flag, shadow_crash,
                flag, crash))
    # (c) end-to-end clean on non-empty candidates (subset; empty candidates
    # hit the out-of-scope blank-rejection validator first)
    if use_clean and value_length >= 1:
        cflag, ccrash = real_clean_completes(max_length, value_length)
        if (shadow_flag, shadow_crash) != (cflag, ccrash):
            fail("DISAGREEMENT (end-to-end clean) on (max_length=%r, "
                 "value_length=%r):\n"
                 "  shadow clean_charfield = flagged=%r crashed=%r\n"
                 "  real clean             = flagged=%r crashed=%r"
                 % (max_length, value_length, shadow_flag, shadow_crash,
                    cflag, ccrash))


def check_compare(a, b):
    """Diff the shadow comparison against the real validator comparison."""
    from django.core.validators import MaxLengthValidator
    v = MaxLengthValidator(10)   # `compare` reads only its arguments
    try:
        shadow = compare_length(a, b)
        shadow_raised = False
    except LimitComparisonError:
        shadow, shadow_raised = None, True
    try:
        real = v.compare(a, b)
        real_raised = False
    except TypeError:
        real, real_raised = None, True
    if (shadow, shadow_raised) != (real, real_raised):
        fail("DISAGREEMENT on compare_length(%r, %r):\n"
             "  shadow = %r (raised=%r)\n"
             "  real   = %r (raised=%r)"
             % (a, b, shadow, shadow_raised, real, real_raised))


def main():
    configure_django()
    checked = 0

    # boundary grid: absent / small / equal / off-by-one / large maxima x
    # candidate lengths around each limit
    maxima = [None, 1, 2, 3, 5, 10, 100, 255, 256, 1000]
    lengths = [0, 1, 2, 3, 4, 5, 6, 9, 10, 11, 99, 100, 101,
               254, 255, 256, 257, 999, 1000, 1001]
    n_boundary = 0
    for m in maxima:
        for n in lengths:
            check_pair(m, n, use_clean=True)
            checked += 1
            n_boundary += 1

    # compare-only boundary: absent limit + equality neighbourhood
    for a in [0, 1, 5, 10, 255, 256]:
        check_compare(a, None)
        checked += 1
        for b in [0, 1, 5, 10, 255, 256]:
            check_compare(a, b)
            checked += 1

    # randomized fuzz over (max_length, value_length), pinned seed; end-to-end
    # clean exercised on a thinned subset for wall-clock
    rng = random.Random(SEED)
    for i in range(N_FUZZ):
        if rng.random() < 0.25:
            m = None
        else:
            m = rng.randint(1, 600)
        # cluster candidate lengths around the limit to stress the flag edge
        if m is not None and rng.random() < 0.5:
            n = max(0, m + rng.randint(-3, 3))
        else:
            n = rng.randint(0, 700)
        check_pair(m, n, use_clean=(i % 100 == 0))
        checked += 1

    # compare-only fuzz (includes the absent-limit channel)
    for _ in range(N_COMPARE_FUZZ):
        a = rng.randint(0, 100000)
        b = None if rng.random() < 0.1 else rng.randint(0, 100000)
        check_compare(a, b)
        checked += 1

    print("G-CONF OK: shadow impl == real patched field/validator behaviour "
          "on %d inputs (%d boundary + %d fuzz + %d compare fuzz, seed %d); "
          "0 disagreements." % (checked, n_boundary, N_FUZZ,
                                N_COMPARE_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
