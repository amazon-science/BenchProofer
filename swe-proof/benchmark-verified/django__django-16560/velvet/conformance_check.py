#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-16560 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md: the five
observable projections of an optional violation error code threaded through a
constraint, as modeled DEEPLY in Solution.lean's `pure` region and computed by
its methods, transliterated to Python and differential-tested against the REAL
gold-patched `django.db.models.constraints` at base_commit+gold.

There are NO axioms and NO deep-model reference to a library callee in this
bundle: every unchanged sub-computation is a FREE INPUT, so the whole impl
region is R/I-tagged (conf_skip=false). The five legs:

  * recordErrorCode   (store)        — `BaseConstraint(...).violation_error_code`
  * serializeWithCode (kwarg map)    — `BaseConstraint(...).deconstruct()[2]`
  * constraintsEqual  (==)           — `CheckConstraint(...) == CheckConstraint(...)`
  * renderConstraint  (text form)    — `repr(CheckConstraint(...))`
  * validateWithCode  (check report) — `CheckConstraint(...).validate(...)`, with
        the UNCHANGED validity predicate `Q.check` stubbed to the free `isValid`
        bit (mapping.md §2/§3); the raised error's `.code` is the observable.

ORACLE = the real gold-patched constraint objects (the harness git-applies the
gold patch before this runs; PYTHONPATH=/testbed so the patched tree wins).
SHADOW = Solution.lean's recordedCode / withCodeKwarg / constraintEq /
renderedWithCode / checkResult, transliterated via the mapping.md bijection
(`Option (List Char)` ↔ `str | None`; `List Char` ↔ `str`).

For each fuzzed input we compare the observable pair (SHADOW, ORACLE); exit 0
iff zero disagreements. stdlib + Django only; fuzz seed pinned (mapping.md §4).
"""
import random
import sys

# Minimal settings so importing the constraint classes + lazy message
# translation + `%`-templating is safe without a database or app registry.
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        USE_I18N=False,
        INSTALLED_APPS=[],
    )

from django.db.models.constraints import BaseConstraint, CheckConstraint  # patched
from django.db.models.query_utils import Q
from django.core.exceptions import ValidationError

SEED = 16560
N_FUZZ = 100_000

# A controllable stand-in for the UNCHANGED per-instance validity predicate
# (`Q.check`), which Solution.lean abstracts as the free `isValid` bit. The real
# predicate does a DB query; here we drive its boolean outcome directly so the
# REAL patched `validate` body (the changed lines) runs against every branch.
_VALIDITY = {"ok": True}


def _fake_q_check(self, against, using=None):
    return _VALIDITY["ok"]


Q.check = _fake_q_check  # monkeypatch the unchanged predicate (free input)


class _FakeMeta:
    pass


class _FakeModel:
    _meta = _FakeMeta()


class _FakeInstance:
    """validate() reads only `_get_field_value_map`; the values are irrelevant
    because the validity predicate is stubbed."""
    def _get_field_value_map(self, meta, exclude=None):
        return {}


# ---- SHADOW: Solution.lean transliterated -----------------------------------

def shadow_recorded(code):
    """recordedCode: the supplied code, else absent."""
    return code


def shadow_kwargs_has_code(code):
    """withCodeKwarg: an explicit binding is added iff a code is set."""
    return code is not None


def shadow_eq(other_equal, code_a, code_b):
    """constraintEq: other fields agree AND codes coincide."""
    return bool(other_equal) and (code_a == code_b)


def shadow_repr_fragment(code):
    """renderedWithCode: the fragment appended iff a code is set; `shown` is the
    value formatter's rendering of the code (repr), per mapping.md §2."""
    if code is None:
        return None
    return " violation_error_code=%r" % code


def shadow_validate(is_valid, code):
    """checkResult: accept (None) when valid; on a violation report the code."""
    if is_valid:
        return (True, None)
    return (False, code)


# ---- ORACLE: the real gold-patched constraint objects -----------------------

def oracle_recorded(code):
    c = BaseConstraint(name="n", violation_error_code=code)
    return c.violation_error_code


def oracle_kwargs_has_code(code):
    c = BaseConstraint(name="n", violation_error_code=code)
    _, _, kwargs = c.deconstruct()
    return ("violation_error_code" in kwargs,
            kwargs.get("violation_error_code"))


def oracle_eq(check, name_a, name_b, code_a, code_b):
    ca = CheckConstraint(check=check, name=name_a, violation_error_code=code_a)
    cb = CheckConstraint(check=check, name=name_b, violation_error_code=code_b)
    return ca == cb


def oracle_other_equal(check, name_a, name_b):
    """Equality of the OTHER observable fields: compare with codes absent."""
    ca = CheckConstraint(check=check, name=name_a)
    cb = CheckConstraint(check=check, name=name_b)
    return ca == cb


def oracle_repr_fragment(code):
    c = CheckConstraint(check=Q(x=1), name="n", violation_error_code=code)
    r = repr(c)
    frag = " violation_error_code=%r" % code if code is not None else None
    if code is None:
        return (False, None, r)
    return (frag in r, frag, r)


def oracle_validate(is_valid, code):
    """Run the REAL patched CheckConstraint.validate with the validity predicate
    stubbed to `is_valid`. Returns (accepted, code_or_None)."""
    _VALIDITY["ok"] = is_valid
    c = CheckConstraint(check=Q(x=1), name="n", violation_error_code=code)
    try:
        c.validate(_FakeModel(), _FakeInstance())
        return (True, None)
    except ValidationError as e:
        return (False, getattr(e, "code", "__missing__"))


def rand_code(rng):
    choices = [None, "custom_code", "fake_discount", "baz", "more_than_one",
               "overlapping_must_be_excluded", "", "a", "UPPER", "with space",
               "unique", "1", "é•"]
    return rng.choice(choices)


def rand_name(rng):
    return rng.choice(["n", "price", "unique", "base_name", "x", "n"])


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    CHECK = Q(x=1)

    def record(leg, *info):
        disagreements.append((leg, *info))

    # Boundary: the explicit code values the F2P tests use, plus None.
    boundary_codes = [None, "custom_code", "fake_discount", "baz",
                      "more_than_one", "overlapping_must_be_excluded", ""]
    bool_cube = [False, True]

    def one(code, code_b, name_a, name_b, is_valid):
        nonlocal count
        count += 1
        # leg 1: store
        if shadow_recorded(code) != oracle_recorded(code):
            record("store", code, shadow_recorded(code), oracle_recorded(code))
        # leg 2: deconstruct kwarg map
        o_has, o_val = oracle_kwargs_has_code(code)
        if shadow_kwargs_has_code(code) != o_has:
            record("kwargs-presence", code, shadow_kwargs_has_code(code), o_has)
        if o_has and o_val != code:
            record("kwargs-value", code, code, o_val)
        # leg 3: equality
        oe = oracle_other_equal(CHECK, name_a, name_b)
        sh = shadow_eq(oe, code, code_b)
        orc = oracle_eq(CHECK, name_a, name_b, code, code_b)
        if sh != orc:
            record("eq", (name_a, name_b, code, code_b), sh, orc)
        # leg 4: text form fragment
        o_present, o_frag, _ = oracle_repr_fragment(code)
        sh_frag = shadow_repr_fragment(code)
        sh_present = sh_frag is not None
        if sh_present != o_present:
            record("repr-presence", code, sh_present, o_present)
        if o_present and sh_frag != o_frag:
            record("repr-fragment", code, sh_frag, o_frag)
        # leg 5: validate report
        sh_v = shadow_validate(is_valid, code)
        orc_v = oracle_validate(is_valid, code)
        if sh_v != orc_v:
            record("validate", (is_valid, code), sh_v, orc_v)

    # Exhaustive boundary sweep over codes x codes x validity.
    for ca in boundary_codes:
        for cb in boundary_codes:
            for iv in bool_cube:
                one(ca, cb, "n", "price", iv)
        if disagreements:
            break

    # Randomized fuzz to a high input count.
    while count < N_FUZZ and not disagreements:
        one(rand_code(rng), rand_code(rng), rand_name(rng), rand_name(rng),
            rng.random() < 0.5)

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for d in disagreements[:8]:
            print("  ", ascii(d))
        return 1
    print("G-CONF OK: R/I shadow of the five violation-error-code projections "
          "(store / kwargs / eq / text-form / validate-report) agrees with the "
          "gold-patched django constraint objects on %d inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
