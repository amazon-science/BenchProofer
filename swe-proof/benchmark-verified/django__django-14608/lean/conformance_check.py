#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_nonFormErrors
against the patch.diff behaviour (the POST-patch production of the non-form error
collection in `full_clean`).

The impl region has R/I content (the branch structure of `full_clean`'s non-form
error production: early return when unbound, append a management message, replace
on a raised validation error). The shadow reproduces the Lean impl's control flow
op-for-op. The error-collection constructor op is A-tagged (a deep-model reference
to the real `ErrorList` constructor), so — per the G-CONF protocol — it is
realised here by the REAL repo callee `django.forms.utils.ErrorList`.

The patched side is an independent reconstruction of the POST-patch `full_clean`
non-form-error production: the collection is built with `error_class='nonform'`,
returned early when unbound, appended-to on a management error, and replaced with
`ErrorList(e.error_list, error_class='nonform')` on a raised validation error.

We compare both the rendered CSS class (`error_class`) and the carried messages
over >=10^5 fuzzed inputs. exit 0 iff zero disagreements.
"""
import random
import sys


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(USE_I18N=False, INSTALLED_APPS=[], DATABASES={})
    django.setup()


def shadow(ErrorList, is_bound, mgmt_valid, mgmt_error, raised):
    """R/I shadow of implementation_nonFormErrors:
        nonForm = ErrorList(error_class='nonform')   -- mkErrorList [] (some "nonform")
        if not is_bound: return nonForm              -- early return
        if not mgmt_valid: nonForm.append(mgmt_error)
        if raised is not None:
            nonForm = ErrorList(raised, error_class='nonform')
        return nonForm
    """
    non_form = ErrorList(error_class='nonform')   # A-reference: real callee
    if not is_bound:
        return non_form.error_class, list(non_form)
    if not mgmt_valid:
        non_form.append(mgmt_error)
    if raised is not None:
        non_form = ErrorList(raised, error_class='nonform')  # A-reference: real callee
    return non_form.error_class, list(non_form)


def patched(ErrorList, is_bound, mgmt_valid, mgmt_error, raised):
    """Independent reconstruction of the POST-patch full_clean non-form error
    production."""
    nfe = ErrorList(error_class='nonform')
    if not is_bound:
        return nfe.error_class, list(nfe)
    if not mgmt_valid:
        nfe.append(mgmt_error)
    try:
        if raised is not None:
            raise _Raise(raised)
    except _Raise as e:
        nfe = ErrorList(e.error_list, error_class='nonform')
    return nfe.error_class, list(nfe)


class _Raise(Exception):
    def __init__(self, error_list):
        self.error_list = error_list


def rand_case(rng):
    is_bound = rng.random() < 0.85
    mgmt_valid = rng.random() < 0.5
    mgmt_error = rng.choice(["ManagementForm data is missing", "bad mgmt", ""])
    if rng.random() < 0.5:
        raised = None
    else:
        pool = ["Please submit at most 1 form.",
                "Please submit at least 3 forms.",
                "You may only specify a drink once.", "Grace is not a Zombie", ""]
        raised = [rng.choice(pool) for _ in range(rng.randint(0, 4))]
    return is_bound, mgmt_valid, mgmt_error, raised


def main() -> int:
    _setup_django()
    from django.forms.utils import ErrorList

    SEED = 14608
    N = 120_000
    rng = random.Random(SEED)

    fixed = [
        (False, True, "m", None),
        (False, False, "m", ["x"]),
        (True, True, "m", None),
        (True, False, "ManagementForm data is missing", None),
        (True, True, "m", ["Please submit at most 1 form."]),
        (True, True, "m", ["Please submit at least 3 forms."]),
        (True, True, "m", ["You may only specify a drink once."]),
        (True, False, "m", ["Grace is not a Zombie"]),  # append then replace
        (True, True, "m", []),
    ]
    cases = fixed + [rand_case(rng) for _ in range(N)]

    disagreements = 0
    examples = []
    for c in cases:
        got = shadow(ErrorList, *c)
        want = patched(ErrorList, *c)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((c, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for c, g, w in examples:
            print(f"  in={c!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
