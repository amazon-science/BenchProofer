#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-14017 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of `refinement.md`: the deep
admissibility-guard model of Solution.lean (`combineResult` + the branch on
`isFilterNode || isCondition`) transliterated to Python, differential-tested
against `patch.diff`'s behaviour — the gold-patched `Q._combine` — over the four
operand classes the change distinguishes:

  * a filter-condition container `Q` (empty and non-empty)        -> admit
  * an operand advertising a boolean condition (conditional=True) -> admit
  * an operand advertising conditional=False                      -> reject
  * an operand with no `conditional` attribute at all             -> reject

ORACLE CHOICE — we drive the REAL gold-patched `Q._combine` (the harness applies
patch.diff at base_commit before this runs in-container) and observe only its
ADMIT/REJECT verdict (did it raise `TypeError`, or return a combined node?). The
change touches ONLY the admissibility guard on line 43; the node construction
that follows (the empty-operand short-circuits and `obj.add(...)`) is UNCHANGED
by the patch, so the differential is over the verdict the guard decides — exactly
the behaviour `combineResult` pins. The conditional operands are built without a
database via `Value(..., output_field=BooleanField())` (conditional=True) and
`Value(..., output_field=IntegerField())` (conditional=False); a bare `object()`
models an operand with no `conditional` attribute.

  * SHADOW  — `combineResult(other, combined)` transliterated: admit iff
              `isinstance(other, Q)` (isFilterNode) or `getattr(other,
              'conditional', False) is True` (isCondition); else reject.

They must agree on the verdict for every operand. Exit 0 iff zero disagreements.
stdlib + django only. The fuzz seed is pinned (mapping.md §4).
"""
import os
import random
import sys

SEED = 14017
N_FUZZ = 100_000


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
            ],
            DATABASES={},
        )
    django.setup()


def shadow_verdict(is_filter_node, is_condition):
    """combineResult transliterated: 'ok' iff admissible, else 'error'."""
    if is_filter_node or is_condition:
        return 'ok'
    return 'error'


def oracle_verdict(combine, self_node, other):
    """patch.diff's behaviour: the gold-patched Q._combine. Returns 'ok' if it
    admits `other` (builds/returns a node) and 'error' if it rejects with the
    TypeError the inadmissible guard raises. A non-empty left `self_node` is used
    so the empty/elif short-circuits do not mask the guard; any node-construction
    machinery after the guard is UNCHANGED and irrelevant to the verdict."""
    try:
        combine(self_node, other, self_node.AND)
        return 'ok'
    except TypeError:
        return 'error'


def operands(rng, Q, Value, BooleanField, IntegerField):
    """Yield (label, other) test points over the four operand classes, with the
    two observables the guard reads recorded for the shadow."""
    def cond_true():
        return Value(True, output_field=BooleanField())

    def cond_false():
        return Value(1, output_field=IntegerField())

    # boundary cases first (plan §4.1 step 4)
    yield ('Q-empty', Q())
    yield ('Q-nonempty', Q(a=1))
    yield ('Q-multi', Q(a=1, b=2))
    yield ('conditional-True', cond_true())
    yield ('conditional-False', cond_false())
    yield ('plain-object', object())
    yield ('int', 5)
    yield ('str', 'x')
    yield ('none', None)
    yield ('list', [1, 2])

    builders = [
        lambda: Q(),
        lambda: Q(x=rng.randint(0, 9)),
        lambda: Q(p=rng.randint(0, 9), q=rng.randint(0, 9)),
        cond_true,
        cond_false,
        lambda: object(),
        lambda: rng.randint(-100, 100),
        lambda: rng.choice(['a', 'bb', '']),
        lambda: None,
        lambda: [rng.randint(0, 5)],
    ]
    for _ in range(N_FUZZ):
        yield ('fuzz', rng.choice(builders)())


def main():
    _setup_django()
    from django.db.models.query_utils import Q
    from django.db.models import Value
    from django.db.models.fields import BooleanField, IntegerField

    rng = random.Random(SEED)
    self_node = Q(seed=1)  # non-empty left operand; isolates the guard verdict

    disagreements = []
    count = 0
    for label, other in operands(rng, Q, Value, BooleanField, IntegerField):
        count += 1
        is_filter_node = isinstance(other, Q)
        is_condition = getattr(other, 'conditional', False) is True
        shadow = shadow_verdict(is_filter_node, is_condition)
        oracle = oracle_verdict(Q._combine, self_node, other)
        if shadow != oracle:
            disagreements.append((label, repr(other), shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for label, o, sh, orc in disagreements:
            print("  input=%s(%s) shadow=%r oracle=%r" % (label, o, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of combineConditions agrees with patch.diff "
          "(gold-patched Q._combine) admissibility verdict over %d inputs "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
