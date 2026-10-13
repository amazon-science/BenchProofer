#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13568.

This instance axiomatizes NO library callee: the operation the patch introduces
— the existential search over the model's declared unique constraints —
``any(constraint.fields == (USERNAME_FIELD,) for constraint in
cls._meta.total_unique_constraints)`` — is fully expressible and is modelled
DEEPLY in model.py (the pure ``any_covers`` / ``covers`` predicates plus the
verified loop). The ``axioms`` region of model.py is empty.

There is therefore no axiom ``Ensures`` to over-approximate. What this script
validates instead is that the model's deep predicate reproduces the REAL Django
semantics the refinement (refinement.md, mapping.md §2) relies on:

  (1) ``UniqueConstraint.fields`` is the tuple of supplied field names, so
      ``constraint.fields == (USERNAME_FIELD,)`` is exact single-field
      1-tuple equality (a composite key never matches);
  (2) ``Options.total_unique_constraints`` keeps only ``UniqueConstraint``s
      whose ``condition is None`` (an unconditional / "total" constraint), so a
      conditional constraint is excluded from the iterated collection.

The model's reference encoding of the predicate is mirrored here as
``covers``/``any_covers`` over the parallel (span, single, total) records, and
asserted to agree with real Django on boundary + randomized fuzz inputs.

If Django is importable (it is in the SWE-bench container) the script builds
genuine ``UniqueConstraint`` objects and compares the model predicate against
the real ``constraint.fields == (username,)`` test and the real
``total_unique_constraints`` ``condition is None`` filter. If Django is not
importable, the same semantics are exercised against a faithful stdlib stand-in
(tuple equality + ``condition is None`` filtering) so the script is still a
meaningful soundness check. Exit 0 iff every observation agrees with the model.
"""
import random
import sys


# --- model.py reference encodings (kept in lock-step with the deep model) ----

def covers(span, single, total, field):
    """Reference of model.py's pure `covers`: an unconditional single-field
    constraint over `field`."""
    return total == 1 and span == 1 and single == field


def any_covers(records, field):
    """Reference of model.py's pure `any_covers`: some record covers `field`.
    `records` is a list of (span, single, total) triples."""
    return any(covers(sp, sg, tt, field) for (sp, sg, tt) in records)


# --- field-name <-> int code abstraction (mapping.md §2) ----------------------

NAMES = ['username', 'email', 'phone', 'login', 'uid', 'handle']
CODE = {n: i for i, n in enumerate(NAMES)}


def _try_import_django():
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(INSTALLED_APPS=[], DATABASES={})
        django.setup()
        from django.db.models import Q, UniqueConstraint
        return Q, UniqueConstraint
    except Exception:
        return None, None


def _real_total_filter(constraints, UniqueConstraint):
    """Mirror Options.total_unique_constraints: keep UniqueConstraints whose
    condition is None (django/db/models/options.py:837-841)."""
    return [
        c for c in constraints
        if isinstance(c, UniqueConstraint) and c.condition is None
    ]


def _real_covers(total_constraints, username):
    """Mirror the patched predicate:
    any(constraint.fields == (username,) for constraint in total_constraints)."""
    return any(c.fields == (username,) for c in total_constraints)


def check_case_real(spec_fields, username, Q, UniqueConstraint):
    """Build real UniqueConstraints from a list of (fields_tuple, conditional)
    specs, run the REAL filter + predicate, compare to the model predicate."""
    real_constraints = []
    model_records = []
    for idx, (fields, conditional) in enumerate(spec_fields):
        cond = Q(password__isnull=False) if conditional else None
        uc = UniqueConstraint(fields=list(fields),
                              name='c%d' % idx, condition=cond)
        real_constraints.append(uc)
        span = len(fields)
        single = CODE[fields[0]] if span >= 1 else -1
        total = 0 if conditional else 1
        model_records.append((span, single, total))

    real_total = _real_total_filter(real_constraints, UniqueConstraint)
    real_result = _real_covers(real_total, username)
    model_result = any_covers(model_records, CODE[username])
    assert real_result == model_result, (
        "deep model disagrees with real Django on %r (username=%r): "
        "real=%r model=%r" % (spec_fields, username, real_result, model_result))


def check_case_stdlib(spec_fields, username):
    """Faithful stdlib stand-in: tuple equality + condition-None filtering."""
    # build (fields_tuple, condition) like UniqueConstraint stores them
    constraints = [(tuple(fields), None if not conditional else "Q")
                   for (fields, conditional) in spec_fields]
    total = [(f, c) for (f, c) in constraints if c is None]
    real_result = any(f == (username,) for (f, c) in total)
    model_records = []
    for (fields, conditional) in spec_fields:
        span = len(fields)
        single = CODE[fields[0]] if span >= 1 else -1
        total_flag = 0 if conditional else 1
        model_records.append((span, single, total_flag))
    model_result = any_covers(model_records, CODE[username])
    assert real_result == model_result, (
        "deep model disagrees with stdlib semantics on %r (username=%r): "
        "real=%r model=%r" % (spec_fields, username, real_result, model_result))


def main():
    Q, UniqueConstraint = _try_import_django()
    use_real = UniqueConstraint is not None
    check = ((lambda s, u: check_case_real(s, u, Q, UniqueConstraint))
             if use_real else check_case_stdlib)

    # --- boundary cases -------------------------------------------------------
    boundary = [
        ([], 'username'),                                          # no constraints
        ([(('username',), False)], 'username'),                    # exact total match
        ([(('username',), True)], 'username'),                     # conditional -> no match
        ([(('email',), False)], 'username'),                       # wrong field
        ([(('username', 'email'), False)], 'username'),            # composite -> no match
        ([(('email', 'username'), False)], 'username'),            # composite -> no match
        ([(('username',), True), (('username',), False)], 'username'),  # one total matches
        ([(('email',), False), (('username',), False)], 'username'),    # later one matches
        ([(('username',), True), (('email',), True)], 'username'),      # all conditional
        ([(('login',), False)], 'username'),                       # different single field
        ([(('username',), False), (('username',), False)], 'username'),  # duplicates
        ([(('username', 'email', 'phone'), False)], 'username'),   # 3-field composite
    ]
    for spec, user in boundary:
        check(spec, user)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(13568)
    for _ in range(4000):
        n = rng.randint(0, 5)
        spec = []
        for _ in range(n):
            k = rng.randint(1, 3)
            fields = tuple(rng.choice(NAMES) for _ in range(k))
            conditional = rng.random() < 0.4
            spec.append((fields, conditional))
        user = rng.choice(NAMES)
        check(spec, user)

    mode = "real Django UniqueConstraint" if use_real else "stdlib stand-in"
    print("G-AX OK: deep model (any_covers/covers) == %s tuple-equality + "
          "total_unique_constraints(condition is None) semantics on %d boundary "
          "+ 4000 fuzz constraint lists" % (mode, len(boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
