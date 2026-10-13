#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11951 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (the impl region itself contains no Requires/Ensures lines)
and the @Pure helper `clamped_max` copied over as a plain function. There are
no @ContractOnly callees and no PSeq usage in this bundle; the carrier is
plain ints, so no shim is needed.

ORACLE: the REAL patched repo code the model models per mapping.md —
`django.db.models.query.QuerySet._batched_insert`, specifically the
effective-batch-size decision inside it. The gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed makes the patched code
importable. Because the decision is embedded in a method that then slices the
work into batches, the oracle observes the effective size through the real
method's own slicing behavior:

  * the backend-capacity callee (`ops.bulk_batch_size`) is stubbed on the
    live connection to return the fuzzed `raw_backend_limit` — per mapping.md
    this callee is an UNCHANGED A-reference whose value enters the model only
    as an opaque non-negative int input, so injecting the int here is exactly
    the modeling boundary;
  * the per-batch row-insertion method (`_insert`) is stubbed on the queryset
    instance to record the length of each batch it receives (no DB I/O);
  * the object list handed to the real method has length
    `max(raw_backend_limit, 1) + 1`, strictly greater than any value the
    shadow can produce, so the FIRST recorded batch length equals the real
    effective batch size exactly (and a hypothetical real value >= the list
    length still cannot falsely agree with the shadow, which is always
    strictly below the list length).

Type bridge (mapping.md "Type abstraction"): all quantities are plain ints.
`requested == 0` models the absent/auto request and is passed to the real
method as None (the only falsy value the public entry point permits);
`requested > 0` is passed verbatim. `raw_backend_limit >= 0` is the stubbed
callee's return value. Outputs compare with `==` on ints.

Input domain (the model's Requires): requested >= 0, raw_backend_limit >= 0.
Boundary cases cover 0/1 on both axes, requested equal to / one below / one
above the clamped maximum, and over-large requests; fuzz biases requested
toward those same edges. Fuzz keeps raw_backend_limit modest (<= 120) so the
per-input batch count stays small; the boundary set covers larger magnitudes.

>= 1e5 Requires-satisfying inputs: 24 boundary + 100000 fuzz pairs.
Pinned fuzz seed: 11951.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 11951
N_FUZZ = 100_000


# --- pure helper from model.py, decorator + contracts stripped ---------------

def clamped_max(raw_backend_limit):
    if raw_backend_limit >= 1:
        return raw_backend_limit
    return 1


# --- the impl region of model.py, verbatim -----------------------------------

def effective_batch_size(requested, raw_backend_limit):
    max_batch_size = clamped_max(raw_backend_limit)
    if requested > 0:
        if requested < max_batch_size:
            result = requested
        else:
            result = max_batch_size
    else:
        result = max_batch_size
    return result


# --- oracle: observe the real method's effective batch size ------------------

def real_effective(qs, ops, requested, raw_backend_limit):
    """Run the REAL patched QuerySet._batched_insert with the backend
    capacity stubbed to `raw_backend_limit` and return the effective batch
    size it actually used (the length of the first batch it sliced)."""
    # The object list must be strictly longer than any possible effective
    # size so the first slice length equals the effective size exactly.
    n_objs = clamped_max(raw_backend_limit) + 1
    objs = list(range(n_objs))
    fields = ["f"]

    batches = []

    def fake_bulk_batch_size(fields, objs):
        return raw_backend_limit

    def fake_insert(item, **kwargs):
        batches.append(len(item))
        return []

    ops.bulk_batch_size = fake_bulk_batch_size
    qs._insert = fake_insert
    try:
        # Bridge: requested == 0 models the absent/auto request (None); the
        # public entry point only ever passes None or a positive int here.
        batch_size = requested if requested > 0 else None
        qs._batched_insert(objs, fields, batch_size)
    finally:
        del ops.bulk_batch_size  # restore the class-level method
        del qs._insert

    if not batches:
        return None  # no batch produced: itself a disagreement signal
    return batches[0]


def check_case(qs, ops, requested, raw_backend_limit):
    shadow_out = effective_batch_size(requested, raw_backend_limit)
    real_out = real_effective(qs, ops, requested, raw_backend_limit)
    if shadow_out != real_out:
        return ("DISAGREEMENT\n  requested=%r raw_backend_limit=%r\n"
                "  shadow=%r\n  real=%r"
                % (requested, raw_backend_limit, shadow_out, real_out))
    return None


def boundary_cases():
    return [
        (0, 0), (0, 1), (0, 2), (0, 5), (0, 500), (0, 5000),  # auto request
        (1, 0), (3, 0),                       # backend reports 0 -> clamp to 1
        (1, 1), (1, 5), (5, 5), (4, 5),       # request <= clamped max
        (6, 5), (501, 500), (1000000, 500),   # request above the clamped max
        (499, 500), (500, 500),               # around a typical backend cap
        (2, 1), (1, 2),                       # tiny cross cases
        (5001, 5000), (5000, 5000), (4999, 5000),  # around a large max
        (2 ** 31, 100), (2 ** 63, 1),         # huge explicit requests
    ]


def rand_pair(rng):
    raw = rng.randint(0, 120)
    cm = raw if raw >= 1 else 1
    choice = rng.randint(0, 5)
    if choice == 0:
        requested = 0                      # auto/absent
    elif choice == 1:
        requested = max(0, cm - 1)
    elif choice == 2:
        requested = cm
    elif choice == 3:
        requested = cm + 1
    elif choice == 4:
        requested = rng.randint(0, 200)
    else:
        requested = rng.randint(201, 10 ** 9)  # far over-large request
    return requested, raw


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=["django.contrib.contenttypes",
                            "django.contrib.auth"],
        )
        django.setup()
    from django.contrib.auth.models import User
    from django.db import connections

    qs = User.objects.all()
    ops = connections[qs.db].ops

    checked = 0
    for requested, raw in boundary_cases():
        err = check_case(qs, ops, requested, raw)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        requested, raw = rand_pair(rng)
        err = check_case(qs, ops, requested, raw)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real effective batch size on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary_cases()), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
