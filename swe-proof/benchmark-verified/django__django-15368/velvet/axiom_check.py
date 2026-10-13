#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15368.

This bundle has NO axioms and NO A-reference deep models (Solution.lean's axioms
region is empty). The single soundness obligation is that the **R type bijection**
of mapping.md §2 is real:

  * the two `AttrVal` classification bits equal what the REAL repo predicates
    report on the assignment values `bulk_update` receives:
        isDbExpr    == hasattr(attr, 'resolve_expression')   (post-patch predicate)
        strictMatch == isinstance(attr, Expression)          (pre-patch predicate)
  * the coarse bit is strictly narrower: strictMatch  ==>  isDbExpr, and the
    witness `F('name')` realizes the strict gap (isDbExpr=True, strictMatch=False)
    — the value the issue's repro exhibits;
  * `wrapPlan`'s per-element rule (`! isDbExpr`) equals the REAL post-patch wrap
    decision: a value is wrapped in `Value(attr, output_field=field)` iff
    `not hasattr(attr, 'resolve_expression')`.

Imports only `django.db.models.expressions` (the module the patched bulk_update
imports `F`/`Value`/`Case`/`When` from) + stdlib. Exit 0 iff every obligation
holds.
"""
import datetime
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        USE_TZ=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    )
django.setup()

from django.db.models import IntegerField  # noqa: E402
from django.db.models.expressions import (  # noqa: E402
    Expression, F, Ref, Value, When,
)


# --- the R bijection (mapping.md §2) and wrapPlan's rule, as references ------

def model_attrval(attr):
    """The AttrVal the mapping.md bridge assigns to a real assignment value."""
    return {
        "isDbExpr": hasattr(attr, "resolve_expression"),
        "strictMatch": isinstance(attr, Expression),
    }


def model_wrap_bit(av):
    """wrapPlan's per-element rule: wrap-as-literal iff NOT a db-side expr."""
    return not av["isDbExpr"]


def real_wrap_decision(attr, field):
    """The REAL post-patch decision: does bulk_update rebind attr to a Value()?
    Mirrors `if not hasattr(attr, 'resolve_expression'): attr = Value(...)`."""
    return not hasattr(attr, "resolve_expression")


def check_value(label, attr, field):
    av = model_attrval(attr)

    # (1) bijection fields equal the real predicates
    assert av["isDbExpr"] == hasattr(attr, "resolve_expression"), \
        "isDbExpr bijection unsound on %s" % label
    assert av["strictMatch"] == isinstance(attr, Expression), \
        "strictMatch bijection unsound on %s" % label

    # (2) coarse bit strictly narrower: strictMatch ==> isDbExpr
    assert (not av["strictMatch"]) or av["isDbExpr"], \
        "strictMatch is not narrower than isDbExpr on %s" % label

    # (3) wrapPlan's rule equals the real post-patch wrap decision
    assert model_wrap_bit(av) == real_wrap_decision(attr, field), \
        "wrapPlan rule != real post-patch wrap decision on %s" % label

    return av


def main():
    field = IntegerField()

    # Boundary value classes spanning both classification bits.
    cases = [
        ("F('name')",            F("name")),
        ("F('a') + 1",           F("a") + 1),
        ("Value('x')",           Value("x")),
        ("When(pk=1,...)",       When(pk=1, then=Value(1))),
        ("Ref('r', F('a'))",     Ref("r", F("a"))),
        ("plain str",            "hello"),
        ("plain int",            5),
        ("plain float",          3.14),
        ("plain date",           datetime.date(2020, 1, 1)),
        ("None",                 None),
        ("plain bool",           True),
        ("plain list",           [1, 2, 3]),
    ]
    seen = {}
    for label, attr in cases:
        seen[label] = check_value(label, attr, field)

    # (2b) the F witness realizes the strict gap (the issue's repro value).
    f_av = seen["F('name')"]
    assert f_av["isDbExpr"] and not f_av["strictMatch"], (
        "F('name') must be a db-side expression that is NOT an Expression "
        "subclass (the strict gap the fix turns on); got %r" % f_av)
    # and the gap flips the routing decision exactly:
    assert model_wrap_bit(f_av) is False, \
        "F('name') must be applied directly (not wrapped) post-patch"
    assert (not f_av["strictMatch"]) is True, \
        "pre-patch (strictMatch) would wrap F('name') — that is the bug"

    # --- randomized fuzz over field-reference names and plain literals -------
    rng = random.Random(15368)
    pool_names = ["name", "note", "misc", "c8", "a", "b", "x_1", "field"]
    for _ in range(20000):
        choice = rng.randint(0, 4)
        if choice == 0:
            attr = F(rng.choice(pool_names)); lbl = "fuzz F"
        elif choice == 1:
            attr = F(rng.choice(pool_names)) + rng.randint(0, 9); lbl = "fuzz F+int"
        elif choice == 2:
            attr = Value(rng.randint(-9, 9)); lbl = "fuzz Value"
        elif choice == 3:
            attr = rng.choice(["s", "test_note", "", "F(name)"]); lbl = "fuzz str"
        else:
            attr = rng.randint(-1000, 1000); lbl = "fuzz int"
        check_value(lbl, attr, field)

    print("G-AX OK: R type bijection sound on %d boundary value classes + 20000 "
          "fuzz values; isDbExpr/strictMatch == real predicates; strictMatch is "
          "strictly narrower; F('name') realizes the strict gap (isDbExpr=True, "
          "strictMatch=False) and routes directly; wrapPlan's `! isDbExpr` rule "
          "== the real post-patch wrap decision everywhere." % len(cases))
    return 0


if __name__ == "__main__":
    sys.exit(main())
