#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15277 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`configureValidators`) transliterated to Python. Inputs are read
              via the mapping.md bijection:
                 priorValidators ↔ the validators present on the field before the
                                    length-bound decision (the `validators` kwarg;
                                    CharField.default_validators is empty)
                 lengthBound     ↔ the field's optional max length (None ↔ none)
              There is NO axiom model to leave as a real callee here (the bundle
              ships no consumed axioms); the entire impl region is R/I.
  * ORACLE  — `patch.diff`'s behaviour: the `validators` list actually carried by
              a real patched CharField after __init__ (the real correctness
              oracle, G-RESOLVE), abstracted to the same tag sequence.

Both are abstracted to a sequence of tags: a length-bound check is
('L', limit_value); any other validator is ('E',). They must agree on every
input. Exit 0 iff zero disagreements; any disagreement is a mechanical
R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, patched), Django +
stdlib only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        USE_TZ=False,
        USE_I18N=False,
        USE_L10N=False,
        DATABASES={},
        INSTALLED_APPS=[],
    )
    django.setup()

from django.core import validators as v
from django.db.models import CharField

SEED = 15277
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean configureValidators -----------------------

def shadow_validators(prior_tags, length_bound):
    """configureValidators (Solution.lean): append a single length-bound check
    iff a length bound is configured (lengthBound.isSome), else leave the prior
    list verbatim. `prior_tags` is the abstracted prior list (all ('E',) here,
    since the carried validators are opaque); `length_bound` is None | int."""
    if length_bound is not None:
        return list(prior_tags) + [("L", length_bound)]
    return list(prior_tags)


# --- the oracle: patch.diff's CharField.validators ---------------------------

def abstract(validator):
    """Abstract one real validator to its tag: a MaxLengthValidator is the
    length-bound check ('L', its configured bound); anything else is opaque
    ('E',)."""
    if isinstance(validator, v.MaxLengthValidator):
        return ("L", validator.limit_value)
    return ("E",)


def oracle_validators(prior_validators, max_length):
    """Build a real patched CharField and read the abstracted validators list it
    actually carries after __init__."""
    field = CharField(max_length=max_length, validators=tuple(prior_validators))
    return [abstract(x) for x in field.validators]


def make_prior(rng, k):
    """k opaque pre-existing validators (none of them MaxLengthValidator)."""
    pool = [
        v.MinLengthValidator(rng.randint(0, 9)),
        v.MinValueValidator(rng.randint(0, 9)),
        v.MaxValueValidator(rng.randint(0, 9)),
        v.RegexValidator(r"\d+"),
        v.validate_slug,
    ]
    return [rng.choice(pool) for _ in range(k)]


def gen_cases(n_fuzz, rng):
    # boundary cases first (plan §4.1 step 4): the F2P scenario + neighbours
    yield ([], None)              # F2P: Value('test') CharField — no max_length
    yield ([], 0)                 # bound configured (zero)
    yield ([], 1)                 # bound configured (one)
    yield ([], 255)               # typical bound
    yield ([], -5)                # negative bound still configured (is not None)
    yield (make_prior(rng, 2), None)   # prior validators, no bound -> verbatim
    yield (make_prior(rng, 3), 32)     # prior validators + bound
    for _ in range(n_fuzz):
        k = rng.randint(0, 4)
        prior = make_prior(rng, k)
        # max_length: None ~30% of the time, else a small/large int
        if rng.random() < 0.3:
            ml = None
        else:
            ml = rng.choice([0, 1, 2, 10, 100, 255, 65535, rng.randint(0, 10000)])
        yield (prior, ml)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for (prior, ml) in gen_cases(N_FUZZ, rng):
        count += 1
        prior_tags = [("E",)] * len(prior)
        shadow = shadow_validators(prior_tags, ml)
        oracle = oracle_validators(prior, ml)
        if shadow != oracle:
            disagreements.append((len(prior), ml, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for nprior, ml, sh, orc in disagreements:
            print("  n_prior=%r max_length=%r shadow=%r oracle=%r"
                  % (nprior, ml, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of configureValidators agrees with patch.diff "
          "CharField.validators on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
