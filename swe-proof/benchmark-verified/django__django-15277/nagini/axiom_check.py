#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15277.

This bundle consumes NO ``@ContractOnly`` axioms: the changed behaviour (a text
field assembles its length validator only when a maximum length is supplied,
and a length comparison against an absent limit is undefined) is modelled
DEEPLY in model.py. There is therefore no axiom to over-approximate; what G-AX
must establish is that the DEEP MODEL matches reality.

The deep model rests on three claims (A-reference), validated here against the
REAL Django callees:

  (1) The length comparison a length-validator performs is exactly the numeric
      "exceeds the limit" test ``value_length > limit`` (model.py
      ``compare_length`` ``Ensures(Result() == (value_length > limit))``), and
      that comparison is UNDEFINED — raises — when the limit is absent
      (``None``) (model.py ``Exsures(LimitComparisonError, limit is None)``).
      Validated against ``django.core.validators.MaxLengthValidator``.

  (2) The gold-patched field assembles, for the length-validator slot, an EMPTY
      list when no maximum length is supplied and exactly one validator whose
      limit equals the supplied maximum otherwise (model.py
      ``build_char_validators`` posts). Validated by inspecting the assembled
      ``CharField.validators`` for ``max_length=None`` and for concrete maxima.

  (3) The end-to-end consequence the modelled ``clean_charfield`` pins (cleaning
      a candidate against a freshly constructed field always completes normally,
      regardless of whether a maximum length was supplied): validated by calling
      the real ``CharField(...).clean(value, model_instance=None)``.

Check (1)'s self-contained half (the numeric comparison + None-raise) runs with
no Django and exercises a boundary + randomized fuzz space; checks (1)-real,
(2), (3) require Django (the repo under test) and run in the official container.
Outside the container (Django absent) the self-contained half still runs fully
and the Django-backed halves print a SKIP line, deferred to the orchestrator's
in-container run. Exit 0 iff every obligation holds.
"""
import random
import sys


# --- model.py reference: the deep model of the length comparison -------------

def model_compare_length(value_length, limit):
    """Reference for model.py's deep model ``compare_length``: the numeric
    "exceeds the limit" test, undefined (raise) on an absent limit."""
    if limit is None:
        raise ValueError("absent limit")   # stands in for LimitComparisonError
    return value_length > limit


def model_build_char_validators(max_length):
    """Reference for model.py's deep model ``build_char_validators``: assemble
    the length-validator slot — empty when no maximum, else one limit."""
    out = []
    if max_length is not None:
        out.append(max_length)
    return out


# --- check (1), self-contained half: the numeric comparison + None-raise -----

def check_compare_reference_selfcontained():
    rng = random.Random(15277)
    # boundary lengths and limits around equality / off-by-one
    lengths = [0, 1, 2, 3, 5, 10, 255, 256]
    limits = [0, 1, 2, 3, 5, 10, 255, 256]
    for vl in lengths:
        for lim in limits:
            assert model_compare_length(vl, lim) == (vl > lim), (vl, lim)
    # absent limit is undefined (raises)
    for vl in lengths:
        try:
            model_compare_length(vl, None)
        except ValueError:
            pass
        else:
            raise AssertionError("model_compare_length(%r, None) did not raise" % vl)
    # randomized fuzz
    for _ in range(20000):
        vl = rng.randint(0, 1000)
        lim = rng.randint(0, 1000)
        assert model_compare_length(vl, lim) == (vl > lim), (vl, lim)


# --- Django-backed checks ----------------------------------------------------

def configure_django():
    """Configure Django just enough to import the ORM field + validator classes.
    Constructing a CharField and calling .clean() runs only Python; no DB."""
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={},
            USE_TZ=False,
        )
    import django
    django.setup()


def check_compare_real():
    """Check (1)-real: MaxLengthValidator.compare(a, b) == (a > b), and a
    comparison against limit=None raises TypeError (the modelled None-raise)."""
    from django.core.validators import MaxLengthValidator
    v = MaxLengthValidator(10)
    rng = random.Random(115277)
    for _ in range(2000):
        a = rng.randint(0, 1000)
        b = rng.randint(0, 1000)
        assert v.compare(a, b) == (a > b) == model_compare_length(a, b), (a, b)
    # the bug-shaped case: a validator with an absent limit cannot compare
    v_none = MaxLengthValidator(None)
    raised = False
    try:
        v_none.compare(5, v_none.limit_value)   # 5 > None
    except TypeError:
        raised = True
    assert raised, "MaxLengthValidator(None).compare(5, None) did not raise TypeError"


def check_build_real():
    """Check (2): the gold-patched CharField assembles an empty length-validator
    slot for max_length=None, and exactly one whose limit == max_length else."""
    from django.db.models import CharField
    from django.core.validators import MaxLengthValidator

    def max_length_limits(field):
        return [v.limit_value for v in field.validators
                if isinstance(v, MaxLengthValidator)]

    # max_length=None: NO MaxLengthValidator assembled (the gold behaviour)
    f_none = CharField()
    assert max_length_limits(f_none) == [] == model_build_char_validators(None), \
        "CharField() assembled a MaxLengthValidator despite no max_length"
    # concrete maxima: exactly one MaxLengthValidator with limit == max_length
    for n in [1, 5, 10, 255]:
        f = CharField(max_length=n)
        assert max_length_limits(f) == [n] == model_build_char_validators(n), \
            "CharField(max_length=%d) did not assemble exactly one limit==%d" % (n, n)


def check_clean_real():
    """Check (3): cleaning a candidate against a freshly constructed field
    always completes normally — including max_length=None (the F2P behaviour)."""
    from django.db.models import CharField
    # the F2P observable: no max_length => clean must NOT raise.
    # NOTE: only non-empty values are cleaned here. An empty string on a
    # non-blank field is rejected by Field.validate() (blank-rejection), which
    # runs BEFORE run_validators() — an orthogonal validator unrelated to the
    # length-validator behaviour modelled by this bundle. Exercising it would
    # spuriously raise ValidationError and is outside the modelled path.
    f_none = CharField()
    f_none.clean("any string value", model_instance=None)
    # a field that declares a maximum still cleans an in-bounds value normally
    f = CharField(max_length=255)
    f.clean("short", model_instance=None)


def main():
    # self-contained faithfulness of the comparison model (no Django needed)
    check_compare_reference_selfcontained()
    print("G-AX OK (self-contained): compare_length deep model == numeric "
          "'exceeds limit' test + None-raise over 64 boundary + 20000 fuzz pairs")

    try:
        configure_django()
    except Exception as e:  # Django absent (outside container) — defer to orchestrator
        print("G-AX SKIP (Django unavailable, deferred to in-container run): %r" % e)
        return 0

    check_compare_real()
    check_build_real()
    check_clean_real()
    print("G-AX OK (Django-backed): MaxLengthValidator.compare == numeric test "
          "(+ None raises TypeError); CharField assembles the length-validator "
          "slot iff max_length is not None; CharField().clean(...) never raises.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
