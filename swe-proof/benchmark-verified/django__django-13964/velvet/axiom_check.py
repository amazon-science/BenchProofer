#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13964.

Validates the ONE kind-A-reference deep model of Solution.lean against the REAL
Django notion it models. G-AX runs in-container against the repo AS-IS (no gold
patch applied), so it may validate ONLY UNCHANGED callees/notions — never the
operation the patch changes (SPEC_GUIDE §0.7). The single A-reference here is:

  (A-reference) `isEmpty` (Solution.lean pure region) == the real membership
      test `x in field.empty_values`, where for an ordinary Django Field
      `empty_values == list(validators.EMPTY_VALUES) == [None, '', [], (), {}]`.
      `empty_values` lives in `django/db/models/fields/__init__.py` and is
      UNCHANGED by the patch (the patch edits only the `elif` condition in
      `Model._prepare_related_fields_for_save`, `django/db/models/base.py`), so
      this membership test is a sound A-reference against the in-container repo:
        pyNone   -> True            (None  in empty_values)
        pyStr cs -> len(cs)==0      (''    in empty_values; non-empty str not)
        pyColl n -> n==0            ([],(),{} in empty_values; non-empty not)
        pyInt k  -> False           (no integer in empty_values)

The per-reference decision `resolvedKey` (empty stored key -> adopt the related
object's pk; else keep the stored key) is NOT validated here: it IS the operation
the gold patch changes, so the in-container (unpatched) callee would disagree by
construction. That decision is an I-leg in refinement.md (§A5), refuted instead
by G-CONF, whose oracle is the repo WITH the gold patch applied.

There is NO A-consumed axiom in this bundle. Imports only Django (the package
the gold patch lives in) + stdlib. Exit 0 iff the A-reference holds.
"""
import random
import sys


# --- Solution.lean deep-model reference encodings (lock-step with `isEmpty`) --

def model_is_empty(v):
    """Reference implementation of Solution.lean's `isEmpty` over the PyVal
    bijection (mapping.md §2): None<->pyNone, str<->pyStr, sized
    list/tuple/dict<->pyColl, int<->pyInt."""
    if v is None:
        return True                      # pyNone
    if isinstance(v, str):
        return len(v) == 0               # pyStr cs -> cs.isEmpty
    if isinstance(v, (list, tuple, dict)):
        return len(v) == 0               # pyColl n -> n == 0
    if isinstance(v, int) and not isinstance(v, bool):
        return False                     # pyInt _ -> false
    raise AssertionError("value %r outside the modeled PyVal shapes" % (v,))


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
            ],
            DATABASES={'default': {
                'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
            DEFAULT_AUTO_FIELD='django.db.models.AutoField',
        )
    django.setup()


def check_empty_values_reference():
    """A-reference 1: model_is_empty(v) == (v in field.empty_values) for the
    REAL ordinary Field's empty_values, over boundary + fuzz."""
    from django.db import models
    field = models.CharField(max_length=50)
    empty_values = field.empty_values     # real: [None, '', [], (), {}]
    # sanity: this is exactly EMPTY_VALUES for an ordinary field
    from django.core import validators
    assert list(empty_values) == list(validators.EMPTY_VALUES), \
        "unexpected field.empty_values: %r" % (empty_values,)

    boundary = [
        None,
        '', 'a', 'foo', 'jeff', ' ', '0', 'False', 'None',
        [], [1], [0], ['x'],
        (), (1,), (0,),
        {}, {1: 2}, {'k': 'v'},
        0, 1, -1, 5, 12345, -98765,
    ]
    for v in boundary:
        observed = v in empty_values                  # real callee
        expected = model_is_empty(v)                  # deep model
        assert observed == expected, (
            "isEmpty deep model unsound on %r: (x in field.empty_values)=%r, "
            "model gives %r" % (v, observed, expected))

    rng = random.Random(13964)
    for _ in range(20000):
        kind = rng.randint(0, 3)
        if kind == 0:                                 # str
            n = rng.randint(0, 6)
            v = ''.join(rng.choice('ab09 #x') for _ in range(n))
        elif kind == 1:                               # int
            v = rng.randint(-1000, 1000)
        elif kind == 2:                               # collection
            n = rng.randint(0, 4)
            shape = rng.randint(0, 2)
            if shape == 0:
                v = [0] * n
            elif shape == 1:
                v = tuple([0] * n)
            else:
                v = {i: i for i in range(n)}
        else:                                         # None
            v = None
        observed = v in empty_values
        expected = model_is_empty(v)
        assert observed == expected, (
            "isEmpty deep model unsound on fuzz %r: real=%r model=%r"
            % (v, observed, expected))
    return len(boundary)


def main():
    _configure_django()
    n_boundary = check_empty_values_reference()
    print("G-AX OK: isEmpty deep model (== `x in field.empty_values`) sound on "
          "%d boundary + 20000 fuzz values against the unchanged Field.empty_values. "
          "The empty->adopt decision (resolvedKey) is the patched operation and is "
          "validated by G-CONF (patched oracle), not here. No A-consumed axiom."
          % (n_boundary,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
