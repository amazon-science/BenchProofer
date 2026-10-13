#!/usr/bin/env python
"""G-CONF: differential conformance for django__django-13343.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the COMPOSED Lean
skeletons

    implementation_deconstructStorage ∘ implementation_initStorage

and diffs it against the REAL patched callees: construct a `FileField` with each
storage-argument shape, call the REAL `.deconstruct()`, and compare the value
recorded under `kwargs['storage']` — by OBJECT IDENTITY — against the shadow's
prediction, over the full discrete matrix plus >=1e5 randomized draws.

Observable: `kwargs.get('storage')` after deconstruct, classified as
  ('absent',)            -> key omitted
  ('callable', obj)      -> the original callable object
  ('inst', obj)          -> a resolved Storage instance

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import os
import random
import sys
import tempfile

SEED = 20240613
N_RANDOM = 120_000  # >= 1e5


def setup_django():
    d = tempfile.mkdtemp()
    sys.path.insert(0, d)
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=True,
    )
    django.setup()


# ---- shadow of implementation_initStorage ∘ implementation_deconstructStorage
# arg is one of:
#   ("default",)          -> .useDefault
#   ("inst", obj)         -> .inst obj           (a non-default Storage instance)
#   ("callable", c, res)  -> .callable           (c the callable; res the produced inst)
# default_obj is the project default_storage identity.
def shadow(arg, default_obj):
    # implementation_initStorage: resolve to (storage, storage_callable)
    if arg[0] == "default":
        storage, storage_callable = default_obj, None
    elif arg[0] == "inst":
        storage, storage_callable = arg[1], None
    else:  # callable
        storage, storage_callable = arg[2], arg[1]
    # implementation_deconstructStorage: classify kwargs['storage']
    if storage is default_obj:
        return ("absent",)
    if storage_callable is not None:
        return ("callable", storage_callable)
    return ("inst", storage)


def classify_real(field, default_obj):
    """Run the REAL deconstruct and classify kwargs['storage'] by identity."""
    *_, kwargs = field.deconstruct()
    if "storage" not in kwargs:
        return ("absent",)
    val = kwargs["storage"]
    if callable(val):
        return ("callable", val)
    return ("inst", val)


def main():
    setup_django()
    from django.db.models.fields.files import FileField
    from django.core.files.storage import (
        FileSystemStorage, default_storage,
    )

    # The identity the patched code compares against (`default_storage`).
    default_obj = default_storage

    # A small pool of distinct non-default Storage instances + callables.
    inst_pool = [FileSystemStorage(location="/tmp/s%d" % i) for i in range(4)]

    def make_callable_fresh(idx):
        produced = FileSystemStorage(location="/tmp/c%d" % idx)
        fn = lambda: produced  # noqa: E731
        return fn, produced

    callable_pool = [make_callable_fresh(i) for i in range(4)]

    def callable_returns_default():
        return default_storage

    # Build (arg_descriptor, FileField-builder) cases.
    def build_default():
        return FileField(), ("default",)

    def build_inst(obj):
        return FileField(storage=obj), ("inst", obj)

    def build_callable(fn, produced):
        return FileField(storage=fn), ("callable", fn, produced)

    def build_callable_default():
        # callable resolving to default_storage -> storage IS default -> absent
        return FileField(storage=callable_returns_default), \
            ("callable", callable_returns_default, default_obj)

    case_builders = []
    case_builders.append(build_default)
    for obj in inst_pool:
        case_builders.append(lambda obj=obj: build_inst(obj))
    for fn, produced in callable_pool:
        case_builders.append(lambda fn=fn, produced=produced: build_callable(fn, produced))
    case_builders.append(build_callable_default)

    disagreements = 0
    checked = 0

    def run_case(builder):
        nonlocal disagreements, checked
        field, arg = builder()
        got = classify_real(field, default_obj)
        exp = shadow(arg, default_obj)
        checked += 1
        # compare tag + object identity
        ok = got[0] == exp[0] and (len(got) == 1 or got[1] is exp[1])
        if not ok:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH arg={arg[0]}: real={got[0]}/{id(got[-1]) if len(got)>1 else '-'} "
                      f"shadow={exp[0]}/{id(exp[-1]) if len(exp)>1 else '-'}")

    # full discrete matrix
    for b in case_builders:
        run_case(b)

    # randomized draws
    rng = random.Random(SEED)
    for _ in range(N_RANDOM):
        run_case(rng.choice(case_builders))

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
