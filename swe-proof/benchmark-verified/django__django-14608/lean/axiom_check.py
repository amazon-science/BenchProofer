#!/usr/bin/env python3
"""G-AX — validate the deep-model A-reference for django__django-14608.

The modeled behavior constructs its non-form error collection via the form-set's
`ErrorList` class. That constructor's class-string behavior is modeled DEEPLY in
Solution.lean as `mkErrorList` (an A-reference, not a consumed axiom):

  ErrorList(initlist, error_class=c).error_class  ==  mkErrorList(initlist, c).cssClass
  ErrorList(initlist).data (the carried messages) ==  mkErrorList(initlist, _).messages

with the class string given by:
  error_class is None  -> 'errorlist'
  error_class == c     -> 'errorlist {}'.format(c)   (i.e. 'errorlist ' + c)

This check imports and runs the REAL repo callee (`django.forms.utils.ErrorList`)
on boundary + fuzzed inputs and asserts the deep model reproduces both its
`error_class` (CSS class) field and its carried data.

exit 0 iff the deep model matches the real callee on every input.
"""
import os
import random
import sys

SEED = 14608          # pinned in mapping.md
N = 120_000           # >= 10^5


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            USE_I18N=False,
            INSTALLED_APPS=[],
            DATABASES={},
        )
    django.setup()


# ---- Python mirror of the Lean deep model -----------------------------------

def model_css_class(extra_class):
    """Mirror of Lean `mkErrorList(...).cssClass`."""
    if extra_class is None:
        return "errorlist"
    return "errorlist " + extra_class


def model_messages(initlist):
    """Mirror of Lean `mkErrorList(...).messages`."""
    return list(initlist) if initlist is not None else []


# ---- Fuzz -------------------------------------------------------------------

def rand_messages(rng):
    pool = [
        "Please submit at most 1 form.",
        "Please submit at least 3 forms.",
        "You may only specify a drink once.",
        "Grace is not a Zombie",
        "", "a", "é", "<b>x</b>", "ManagementForm data is missing",
    ]
    k = rng.randint(0, 5)
    return [rng.choice(pool) for _ in range(k)]


def rand_extra_class(rng):
    return rng.choice([None, "nonform", "nonfield", "", "x y", "errorlist"])


def main() -> int:
    _setup_django()
    from django.forms.utils import ErrorList

    rng = random.Random(SEED)

    fixed = [
        ([], None),
        ([], "nonform"),
        (["Please submit at most 1 form."], "nonform"),
        (["Please submit at least 3 forms."], "nonform"),
        (["You may only specify a drink once."], "nonform"),
        (["Grace is not a Zombie"], "nonform"),
        (["a", "b", "c"], None),
        ([""], "nonform"),
    ]
    cases = fixed + [(rand_messages(rng), rand_extra_class(rng)) for _ in range(N)]

    mismatches = 0
    examples = []
    for initlist, extra in cases:
        real = ErrorList(list(initlist), error_class=extra) if extra is not None \
            else ErrorList(list(initlist))
        real_css = real.error_class
        real_data = list(real)  # carried messages (ErrorList is list-like)

        m_css = model_css_class(extra)
        m_data = model_messages(initlist)

        if real_css != m_css or real_data != m_data:
            mismatches += 1
            if len(examples) < 10:
                examples.append((initlist, extra, (m_css, m_data), (real_css, real_data)))

    if mismatches:
        print(f"G-AX FAIL: deep model diverges from real ErrorList on "
              f"{mismatches} inputs")
        for il, ex, m, r in examples:
            print(f"  initlist={il!r} extra={ex!r} model={m!r} real={r!r}")
        return 1

    print(f"G-AX OK: deep model == ErrorList constructor on {len(cases)} inputs "
          f"(seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
