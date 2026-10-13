#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11603 (nagini).

SHADOW: the impl regions of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Exsures) stripped. There are no @Pure helpers and no
@ContractOnly callees in this bundle; PSeq is not used (the whole carrier is
plain booleans), so no shim is needed. CapabilityError copies over as the
shadow's user-defined refusal signal.

ORACLE: the REAL patched repo behaviour the model models per mapping.md — the
deduplication-decision prologue of ``Aggregate.__init__`` in
``django.db.models.aggregates``, exercised through the concrete aggregate
classes. The gate applies patch.diff to /testbed before this script runs.
Bridges (mapping.md section 2):

  * ``allow_dedup`` <-> the per-family class attribute ``allow_distinct``:
    for ``construct_dedup`` we drive the real prologue through EVERY family
    class and read its ``allow_distinct`` as the bridged ``allow_dedup``;
    ``build_mean`` maps to constructing ``Avg(...)`` and ``build_total`` to
    constructing ``Sum(...)`` (their capability flag on the patched tree).
  * ``dedup`` <-> the ``distinct`` keyword argument (identical boolean).
  * shadow normal return value <-> the constructed object's recorded
    ``.distinct`` attribute (read-back fidelity).
  * shadow ``CapabilityError`` <-> real ``TypeError`` refusal (the model uses
    a user-defined exception because a builtin exception in an Exsures
    crashes the Nagini translator; mapping.md section 2).

Input domain: every precondition is just a termination obligation, so ALL
boolean combinations are Requires-satisfying. The exhaustive boundary set is
tiny (2 booleans for construct_dedup across 8 family classes, 1 boolean each
for build_mean/build_total); on top of it we run >= 1e5 randomized draws over
(family, distinct) pairs with a PINNED seed. Pinned fuzz seed: 116030.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the repo under test only.
"""
import json
import random
import sys

SEED = 116030
N_FUZZ = 100000


# --- exception class from model.py (needed by the copied impl) ---------------

class CapabilityError(Exception):
    pass


# --- impl regions of model.py, verbatim, contract calls stripped -------------

def construct_dedup(allow_dedup, dedup):
    if dedup and not allow_dedup:
        raise CapabilityError()
    stored = dedup
    return stored


def build_mean(dedup):
    return construct_dedup(True, dedup)


def build_total(dedup):
    return construct_dedup(True, dedup)


# --- oracle plumbing ----------------------------------------------------------

def configure_django():
    """Configure Django settings just enough to import ORM expression classes.
    Constructing an aggregate only runs its Python __init__; it never opens a
    database connection, so an empty DATABASES is sufficient."""
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=False)
    import django
    django.setup()


def real_outcome(cls, distinct):
    """Drive the real constructor prologue: build the aggregate over a single
    field expression with the given deduplicate request. Returns
    ("ok", recorded) where recorded is the object's stored ``.distinct``, or
    ("raise",) when the prologue refuses with TypeError."""
    try:
        obj = cls("field_name", distinct=distinct)
        return ("ok", getattr(obj, "distinct", None))
    except TypeError:
        return ("raise",)


def shadow_outcome(fn, *args):
    """Run a shadow function; same outcome encoding as real_outcome."""
    try:
        return ("ok", fn(*args))
    except CapabilityError:
        return ("raise",)


def check_construct(fam_name, cls, distinct):
    """construct_dedup vs the real family's prologue decision. The family's
    class-level capability is read off the real class and passed to the shadow
    as the bridged allow_dedup boolean."""
    allow = bool(getattr(cls, "allow_distinct"))
    shadow = shadow_outcome(construct_dedup, allow, bool(distinct))
    real = real_outcome(cls, bool(distinct))
    if shadow != real:
        return ("DISAGREEMENT construct_dedup(allow_dedup=%r, dedup=%r) "
                "[family %s]:\n  shadow (impl region) = %r\n"
                "  real (patched constructor prologue) = %r"
                % (allow, bool(distinct), fam_name, shadow, real))
    return None


def check_family(fn_name, fn, cls, distinct):
    """build_mean/build_total vs constructing the real changed-family object."""
    shadow = shadow_outcome(fn, bool(distinct))
    real = real_outcome(cls, bool(distinct))
    if shadow != real:
        return ("DISAGREEMENT %s(dedup=%r):\n  shadow (impl region) = %r\n"
                "  real (patched %s constructor) = %r"
                % (fn_name, bool(distinct), shadow, cls.__name__, real))
    return None


def main():
    configure_django()
    from django.db.models.aggregates import (
        Aggregate, Avg, Count, Max, Min, StdDev, Sum, Variance,
    )

    families = [
        ("Avg", Avg), ("Sum", Sum), ("Count", Count), ("Max", Max),
        ("Min", Min), ("StdDev", StdDev), ("Variance", Variance),
        ("Aggregate", Aggregate),
    ]
    changed = [("build_mean", build_mean, Avg), ("build_total", build_total, Sum)]

    checked = 0

    # ---- exhaustive boundary: every family x distinct in {False, True} ------
    for fam_name, cls in families:
        for distinct in (False, True):
            err = check_construct(fam_name, cls, distinct)
            if err:
                print(err)
                return 1
            checked += 1
    for fn_name, fn, cls in changed:
        for distinct in (False, True):
            err = check_family(fn_name, fn, cls, distinct)
            if err:
                print(err)
                return 1
            checked += 1

    # ---- randomized fuzz over (family, distinct) pairs (pinned seed) --------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        distinct = rng.random() < 0.5
        if rng.random() < 0.25:
            fn_name, fn, cls = changed[rng.randrange(len(changed))]
            err = check_family(fn_name, fn, cls, distinct)
        else:
            fam_name, cls = families[rng.randrange(len(families))]
            err = check_construct(fam_name, cls, distinct)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched aggregate constructor "
          "decisions on %d inputs (exhaustive boundary over 8 families x "
          "{False,True} + both changed families, plus %d fuzz draws, seed %d);"
          " 0 disagreements." % (checked, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
