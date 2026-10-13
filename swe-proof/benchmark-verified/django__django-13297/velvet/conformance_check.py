#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13297 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types (an ordered `dict`), via the
              mapping.md bijection (`List (Nat × Value)` ↔ ordered dict items,
              `Value` ↔ runtime value, `Wrapper.reported = none`, and
              `coerce (deferOne v) v.tag = genuine v`). There is NO A-tagged
              callee in this bundle, so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `_wrap_url_kwargs_with_deprecation_warning` applied at base_commit
              (the harness applies patch.diff before this runs), followed by the
              real type-dispatching consumer `CharField.to_python` — the path
              the issue's `... .objects.get(slug=value)` filter reaches.

Observable per input mapping = the ordered list of `(key, coerced_value)`, where
`coerced_value` is the GENUINE value the consumer yields. The model says every
entry coerces to its original value (genuine, of its own type), key and order
preserved. The oracle must agree on every input. Exit 0 iff zero disagreements;
any disagreement is a mechanical R/I-fidelity counterexample (e.g. a wrapper
that masquerades and is handed through un-coerced).

Runs in-container (the prebuilt SWE-Bench instance image), `django` + stdlib
only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys
import warnings

SEED = 13297
N_FUZZ = 100_000


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={},
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
        )
    django.setup()


# --- the R/I shadow: Solution.lean deferredOf + coerce, transliterated -------
def shadow_observable(mapping):
    """deferredOf(entries) then coerce(deferOne v) v.tag for each value.
    deferOne reports `none`, so coerce is always `genuine v`: every entry
    coerces to its original value, key and order preserved."""
    return [(key, value) for key, value in mapping.items()]


# --- the oracle: patch.diff's behaviour + the real consumer ------------------
def oracle_observable(mapping):
    """patch.diff's behaviour: the patched
    `_wrap_url_kwargs_with_deprecation_warning`, then `CharField.to_python`
    (the type-dispatching consumer). Returns (key, coerced) where `coerced`
    must be a GENUINE str; if the consumer hands a wrapper through un-coerced
    (the pre-patch crash), `coerced` is NOT a genuine str and the observables
    diverge."""
    from django.views.generic.base import (
        _wrap_url_kwargs_with_deprecation_warning as wrap,
    )
    from django.db.models.fields import CharField

    f = CharField()
    out = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        context_kwargs = wrap(mapping)
        for key, wrapper in context_kwargs.items():
            coerced = f.to_python(wrapper)
            # genuine-ness is the observable: a non-str (passthrough wrapper)
            # is recorded as a sentinel so it can never match the shadow.
            if type(coerced) is str:
                out.append((key, coerced))
            else:
                out.append((key, ("<non-genuine:%s>" % type(coerced).__name__)))
    return out


def fuzz_inputs(n, rng):
    sample_keys = ["offer_slug", "artist_name", "key", "foo", "slug", "pk",
                   "name", "id", "value"]
    alphabet = list("abcdefghijklmnopqrstuvwxyz0123456789-_ /é•'<>ABCDEF")
    # boundary cases first
    yield {}
    yield {"offer_slug": "Rene Magritte"}
    yield {"artist_name": "Rene Magritte"}
    yield {"slug": ""}
    yield {"key": "value", "foo": "bar"}
    yield {"offer_slug": "a b/c", "name": "Joe's Crab Shack"}
    yield {"k1": "Ünïcödé", "k2": "•bullet•", "k3": "<script>"}
    for _ in range(n):
        m = rng.randint(0, 4)
        d = {}
        for _ in range(m):
            k = rng.choice(sample_keys)
            vlen = rng.randint(0, 24)
            v = "".join(rng.choice(alphabet) for _ in range(vlen))
            d[k] = v
        yield d


def main():
    _configure_django()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for mapping in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_observable(mapping)
        oracle = oracle_observable(mapping)
        if shadow != oracle:
            disagreements.append((mapping, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for m, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (m, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of deferMapping agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
