#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11951.

This bundle has NO consumed @ContractOnly axiom: the changed operation is plain
integer min/max selection, modeled deeply over ints in model.py. There are two
soundness obligations G-AX checks here, both with real Python integer
operations (stdlib only):

  (1) A-reference — the only relied-on property of the UNCHANGED callee
      `ops.bulk_batch_size(fields, objs)` is that it returns a NON-NEGATIVE
      integer (which `max(., 1)` then lifts to >= 1). The real backend
      implementations at base_commit are pure formulas over `len(objs)`,
      `len(fields)`, and `max_query_params`:
          base   : len(objs)
          sqlite : 500                        if len(fields) == 1
                   max_query_params // n       if len(fields) > 1
                   len(objs)                   otherwise
          oracle : a backend positive cap
      We reproduce these formulas and assert the result is >= 0 over a wide
      sweep, matching the `raw_backend_limit >= 0` Requires in model.py.

  (2) Deep-model equivalence — the model's `clamped_max` and
      `effective_batch_size` must agree EXACTLY with the real Python integer
      operations the patch performs:
          max_batch_size = max(raw_backend_limit, 1)
          effective      = min(requested, max_batch_size) if requested  # >0
                           else max_batch_size            # auto/absent
      over boundary cases + randomized fuzz.

Exit 0 iff every obligation holds.
"""
import random
import sys


# --- model.py deep-model reference encodings (kept in lock-step) -------------

def model_clamped_max(raw_backend_limit):
    """Reference of model.py's `clamped_max`: max(., 1) over a non-neg int."""
    assert raw_backend_limit >= 0
    return raw_backend_limit if raw_backend_limit >= 1 else 1


def model_effective_batch_size(requested, raw_backend_limit):
    """Reference of model.py's `effective_batch_size` impl skeleton."""
    assert requested >= 0 and raw_backend_limit >= 0
    max_batch_size = model_clamped_max(raw_backend_limit)
    if requested > 0:
        if requested < max_batch_size:
            return requested
        return max_batch_size
    return max_batch_size


# --- the REAL patch arithmetic (gold patch, plain Python ints) ---------------

def real_patch_effective(requested, raw_backend_limit):
    """The gold patch's computation, with `requested == 0` modelling the
    falsy/auto `batch_size` (None) and `requested > 0` the explicit case.

        max_batch_size = max(raw_backend_limit, 1)
        batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size
    """
    max_batch_size = max(raw_backend_limit, 1)
    batch_size = requested  # 0 models None (falsy); a real explicit size is >0
    return min(batch_size, max_batch_size) if batch_size else max_batch_size


# --- (1) A-reference: real bulk_batch_size formulas return non-negative ints -

def backend_returns(num_fields, num_objs, max_query_params):
    """Reproduce the real backends' pure return formulas (base + sqlite)."""
    out = []
    # base/operations.py:68
    out.append(num_objs)
    # sqlite3/operations.py:27
    if num_fields == 1:
        out.append(500)
    elif num_fields > 1:
        out.append(max_query_params // num_fields)
    else:
        out.append(num_objs)
    return out


def check_backend_nonneg():
    rng = random.Random(119510)
    cases = 0
    for _ in range(20000):
        num_fields = rng.randint(0, 64)
        num_objs = rng.randint(0, 100000)
        max_query_params = rng.randint(1, 4000)
        for v in backend_returns(num_fields, num_objs, max_query_params):
            assert isinstance(v, int) and v >= 0, (
                "bulk_batch_size reference returned a non-int/negative value "
                "%r (fields=%d objs=%d mqp=%d)"
                % (v, num_fields, num_objs, max_query_params))
            cases += 1
    # explicit boundaries
    for nf, no, mqp in [(0, 0, 1), (1, 0, 1), (2, 0, 2), (1, 1, 1),
                        (5, 999, 2000), (64, 100000, 4000)]:
        for v in backend_returns(nf, no, mqp):
            assert v >= 0
            cases += 1
    return cases


# --- (2) deep model == real patch arithmetic --------------------------------

def check_equiv(requested, raw_backend_limit):
    expected = real_patch_effective(requested, raw_backend_limit)
    observed = model_effective_batch_size(requested, raw_backend_limit)
    assert observed == expected, (
        "deep model disagrees with gold patch arithmetic on "
        "(requested=%d, raw_backend_limit=%d): model=%r patch=%r"
        % (requested, raw_backend_limit, observed, expected))
    # also assert the model.py postconditions hold on the observed value
    cm = max(raw_backend_limit, 1)
    assert observed >= 1
    assert observed <= cm
    if requested > 0:
        assert observed <= requested
        assert observed == (requested if requested <= cm else cm)
    else:
        assert observed == cm


def main():
    n_backend = check_backend_nonneg()

    # boundary cases for the arithmetic equivalence -- the discriminating ones
    boundary = [
        (0, 0), (0, 1), (0, 5), (0, 1000),       # auto/absent request
        (1, 1), (1, 5), (5, 5),                   # request <= max
        (6, 5), (1001, 1000), (1000000, 500),     # request > max (the bug case)
        (1, 0), (3, 0),                           # backend reports 0 -> clamp 1
        (500, 500), (501, 500), (499, 500),       # around the sqlite single-field cap
    ]
    for requested, raw in boundary:
        check_equiv(requested, raw)

    # randomized fuzz over the integer domain (incl. requested == max edges)
    rng = random.Random(11951)
    n_fuzz = 0
    for _ in range(200000):
        raw = rng.randint(0, 5000)
        # bias toward the boundary requested in {0, raw-1, raw, raw+1, big}
        choice = rng.randint(0, 5)
        if choice == 0:
            requested = 0
        elif choice == 1:
            requested = max(0, raw - 1)
        elif choice == 2:
            requested = raw
        elif choice == 3:
            requested = raw + 1
        elif choice == 4:
            requested = rng.randint(0, 5000)
        else:
            requested = rng.randint(5001, 100000)
        check_equiv(requested, raw)
        n_fuzz += 1

    print("G-AX OK: bulk_batch_size reference non-negative on %d obs; deep "
          "model == gold patch min/max arithmetic on %d boundary + %d fuzz "
          "(requested, raw_backend_limit) pairs; all model.py postconditions "
          "hold." % (n_backend, len(boundary), n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
