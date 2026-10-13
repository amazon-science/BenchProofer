#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15375 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (`terminal : Bool` ↔ the `summarize` flag, `defaultVal : Option
              Int` ↔ the `default=` keyword, `Resolved.isTerminal` ↔
              `bool(result.is_summary)`, `Resolved.hasFallback` ↔
              `isinstance(result, Coalesce)`). There is NO A-tagged callee in the
              impl region, so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `Aggregate.resolve_expression` applied at base_commit (the harness
              applies patch.diff before this runs), observed as
              `(bool(result.is_summary), isinstance(result, Coalesce))`.

The observable per input is the pair `(isTerminal, hasFallback)` of the prepared
clause. The model says: the prepared clause always carries the requested
terminal marker (whether or not a fallback is supplied), and is the fallback
form exactly when a fallback value is supplied. The oracle must agree on every
input. Exit 0 iff zero disagreements; any disagreement is a mechanical
R/I-fidelity counterexample (e.g. a fallback wrapper that silently drops the
terminal marker — the pre-patch bug).

Runs in-container (the prebuilt SWE-Bench instance image), `django` + stdlib
only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 15375
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


# --- the R/I shadow: Solution.lean `prepared`, transliterated ----------------
def shadow_prepared(terminal, default_val):
    """`prepared terminal defaultVal` transliterated to Python. Returns the
    observable pair (isTerminal, hasFallback). With no fallback the clause is
    the bare aggregation; with a fallback it is the fallback form; either way it
    carries the requested terminal marker (mapping.md §2)."""
    has_fallback = default_val is not None
    is_terminal = bool(terminal)
    return (is_terminal, has_fallback)


# --- the oracle: patch.diff's behaviour --------------------------------------
def oracle_prepared(terminal, default_val):
    """patch.diff's behaviour: the patched `Aggregate.resolve_expression`.
    Builds a real terminal-style aggregate carrying a constant source (so it
    resolves without a DB), supplies the `default=`, resolves with
    `summarize=terminal`, and observes (bool(is_summary), isinstance Coalesce)."""
    from django.db.models import Sum, Value
    from django.db.models.functions.comparison import Coalesce

    agg = Sum(Value(1), default=default_val)
    res = agg.resolve_expression(
        query=None, allow_joins=True, reuse=None, summarize=terminal,
    )
    return (bool(res.is_summary), isinstance(res, Coalesce))


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4): the full terminal × fallback grid
    yield (False, None)
    yield (True, None)
    yield (False, 0)        # the issue's `default=0`
    yield (True, 0)         # the F2P scenario: summarize + default=0
    yield (False, 1)
    yield (True, -1)
    yield (True, 0)
    yield (False, 12345)
    for _ in range(n):
        terminal = rng.choice([False, True])
        # default: None (no fallback) or an arbitrary integer fallback value;
        # only presence is observable (the value content is I-tagged, flows
        # unchanged into the wrapper's fallback slot).
        if rng.random() < 0.5:
            default_val = None
        else:
            default_val = rng.randint(-10_000, 10_000)
        yield (terminal, default_val)


def main():
    _configure_django()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for terminal, default_val in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_prepared(terminal, default_val)
        oracle = oracle_prepared(terminal, default_val)
        if shadow != oracle:
            disagreements.append(((terminal, default_val), shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for inp, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of prepareAggregate agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
