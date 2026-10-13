#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14787 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated to
              Python over the *real* repo types, via the mapping.md bijection
              (object attribute env ↔ assoc list; absent ↔ None). It computes
              `mergePlan` (lookupAttr / firstDefined / mergeAt) from the OBSERVED
              source/base environments. No consumed axiom appears in the impl, so
              the whole impl region is R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.utils.decorators._multi_decorate` applied at base_commit
              (the harness applies patch.diff before this runs). The object the
              decorator chain receives is observed per assigned name through a
              capturing decorator — exactly the F2P observation channel.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys
from functools import partial, WRAPPER_ASSIGNMENTS

SEED = 14787
N_FUZZ = 100_000

_ABSENT = object()
ASSIGNED = list(WRAPPER_ASSIGNMENTS)


# --- the R/I shadow: Solution.lean lookupAttr/mergeAt/mergePlan -------------

def lookup_attr(env, n):
    for (k, v) in env:
        if k == n:
            return v
    return _ABSENT


def first_defined(a, b):
    return a if a is not _ABSENT else b


def merge_at(src_env, base_env, n):
    return first_defined(lookup_attr(src_env, n), lookup_attr(base_env, n))


def merge_plan(src_env, base_env, names):
    return [(n, merge_at(src_env, base_env, n)) for n in names]


def observe_env(obj, names):
    env = []
    for n in names:
        v = getattr(obj, n, _ABSENT)
        if v is not _ABSENT:
            env.append((n, v))
    return env


def shadow_presented(method_obj, base_obj):
    """mergePlan(observe method, observe base) — the R/I shadow of the impl."""
    src_env = observe_env(method_obj, ASSIGNED)
    base_env = observe_env(base_obj, ASSIGNED)
    return merge_plan(src_env, base_env, ASSIGNED)


# --- the oracle: patch.diff's behaviour via real patched _multi_decorate ----

def oracle_presented(method_func, base_obj):
    """Observe, per assigned name, the object the decorator chain receives from
    the PATCHED django _multi_decorate. base_obj is informational; the real base
    is the partial _multi_decorate itself builds. We compare against the shadow
    computed from that same real base (see make_case)."""
    from django.utils.decorators import _multi_decorate

    seen = {}

    def capturing(func):
        # Record what the decorator sees on the object handed to it.
        for n in ASSIGNED:
            seen[n] = getattr(func, n, _ABSENT)

        def inner(*a, **k):
            return func(*a, **k)
        return inner

    wrapper = _multi_decorate(capturing, method_func)
    # Invoke so the closure builds bound_method and runs the decorator chain.

    class _Holder:
        pass
    inst = _Holder()
    # _wrapper expects (self, *args); call it bound to a dummy self.
    wrapper(inst)
    return [(n, seen.get(n, _ABSENT)) for n in ASSIGNED]


def make_method(attrs_to_remove, attrs_to_set):
    """A fresh function with its identity attributes tweaked, standing in for the
    decorated `method`."""
    def method(self):
        return 'tests'
    for n in attrs_to_remove:
        try:
            delattr(method, n)
        except (AttributeError, TypeError):
            pass
    for n, v in attrs_to_set.items():
        try:
            setattr(method, n, v)
        except (AttributeError, TypeError):
            pass
    return method


def fuzz_cases(n, rng):
    # boundary cases first
    yield ([], {})                                    # unmodified method
    yield ([], {'__name__': 'hello_world'})           # custom name
    yield ([], {'__module__': 'tests'})               # custom module
    yield ([], {'__name__': 'm', '__qualname__': 'C.m', '__module__': 'tests'})
    yield ([], {'__doc__': 'docs'})
    settable = ['__name__', '__qualname__', '__module__', '__doc__']
    values = ['method', 'hello_world', 'tests', 'C.m', '', 'mod.sub', 'x',
              'a doc', '__main__']
    for _ in range(n):
        to_set = {nm: rng.choice(values)
                  for nm in settable if rng.random() < 0.6}
        yield ([], to_set)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for to_remove, to_set in fuzz_cases(N_FUZZ, rng):
        count += 1
        method_func = make_method(to_remove, to_set)
        # The real base is the partial _multi_decorate builds internally; build
        # an identical one here so the shadow sees the same base environment.
        class _H:
            pass
        base_obj = partial(method_func.__get__(_H(), _H))

        oracle = oracle_presented(method_func, base_obj)
        shadow = shadow_presented(method_func, base_obj)
        if shadow != oracle:
            disagreements.append((to_set, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for cfg, sh, orc in disagreements:
            print("  cfg=%r\n   shadow=%r\n   oracle=%r" % (cfg, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildPresentedAttrs agrees with patch.diff "
          "behaviour (patched _multi_decorate) on %d inputs (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
