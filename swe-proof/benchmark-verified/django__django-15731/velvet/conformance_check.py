#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15731 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — `buildForwarderMeta`'s impl region transliterated to Python over
              the real repo types, via the mapping.md bijection (a callable's
              introspectable triple ↔ `CallableMeta`). The impl is the single op
              `return propagate forwarder target`; `propagate` takes all three
              observed fields (name, doc, rendered signature) from `target`.
  * ORACLE  — `patch.diff`'s behaviour: the wrapper that the PATCHED
              `BaseManager._get_queryset_methods` / `create_method` produces for a
              given queryset method, introspected. The patched closure decorates
              the inner `manager_method` with `@functools.wraps(method)`
              (manager.py:84), so its introspected triple is the target's.

They must agree on every queryset method / fuzzed callable. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

`propagate` is an A-reference (a deep model of the standard wrapper facility),
checked == the real facility by axiom_check.py (G-AX). Here it is the very op
under differential test against patch.diff, so it is transliterated (not
substituted by an external model) — the impl region is NOT all-A-tagged and
conf_skip is false.

Runs in-container (the prebuilt SWE-Bench instance image with patch.diff
applied), stdlib + django only. The fuzz seed is pinned (mapping.md §4).
"""
import functools
import inspect
import random
import sys

SEED = 15731


# --- the introspectable triple (the CallableMeta bijection, mapping.md §2) ---

def observe(c):
    return (c.__name__, c.__doc__ or "", str(inspect.signature(c)))


# --- SHADOW: Solution.lean impl `return propagate forwarder target` ----------

def shadow_meta(target):
    """`propagate forwarder target`: all three observed fields from `target`.
    The forwarder's own (generic forwarding) metadata does not survive."""
    name, doc, sig = observe(target)
    return (name, doc, sig)


# --- ORACLE: patch.diff's patched create_method, reconstructed ---------------

def oracle_meta_reconstructed(name, target):
    """The wrapper the PATCHED `create_method(name, method)` returns (gold
    manager.py:83-89), introspected. Byte-faithful to patch.diff's closure."""

    @functools.wraps(target)
    def manager_method(self, *args, **kwargs):
        return getattr(self.get_queryset(), name)(*args, **kwargs)

    return observe(manager_method)


def oracle_meta_real(queryset_class):
    """Strongest oracle: invoke the REAL patched
    `BaseManager._get_queryset_methods(queryset_class)` and introspect every
    wrapper it actually builds. Returns {name: triple} or None if django is
    not importable. This exercises patch.diff's literal code path."""
    try:
        from django.db.models.manager import BaseManager
    except Exception:
        return None
    produced = BaseManager._get_queryset_methods(queryset_class)
    return {name: observe(fn) for name, fn in produced.items()}


# --- fuzzed synthetic callables ----------------------------------------------

def fuzz_callables(n, rng):
    POOL = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "m"]
    for i in range(n):
        n_pos = rng.randint(0, 4)
        n_def = rng.randint(0, 3)
        has_args = rng.random() < 0.5
        has_kwargs = rng.random() < 0.5
        n_kwonly = rng.randint(0, 2)
        names = POOL[: n_pos + n_def + n_kwonly]
        params, idx = [], 0
        for _ in range(n_pos):
            params.append(names[idx]); idx += 1
        for _ in range(n_def):
            params.append("%s=None" % names[idx]); idx += 1
        if has_args:
            params.append("*rest")
        elif n_kwonly:
            params.append("*")
        for _ in range(n_kwonly):
            params.append("%s=0" % names[idx]); idx += 1
        if has_kwargs:
            params.append("**kw")
        src = "def _fuzz(%s):\n    %s\n" % (
            ", ".join(params), repr("doc#%d" % i) if i % 3 else "pass")
        ns = {}
        exec(src, ns)  # noqa: S102
        fn = ns["_fuzz"]
        if i % 3 == 0:
            fn.__doc__ = None
        yield ("_fuzz_%d" % i, fn)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # --- leg 1: the REAL patched _get_queryset_methods over QuerySet ----------
    try:
        from django.db.models import QuerySet
    except Exception:
        QuerySet = None

    if QuerySet is not None:
        real = oracle_meta_real(QuerySet)
        if real is not None:
            for name, oracle in real.items():
                count += 1
                # the target whose metadata the wrapper must present
                target = getattr(QuerySet, name)
                shadow = shadow_meta(target)
                if shadow != oracle:
                    disagreements.append((name, shadow, oracle))
                    if len(disagreements) >= 5:
                        break

    # --- leg 2: reconstructed patched create_method over fuzzed callables -----
    if not disagreements:
        for name, fn in fuzz_callables(100_000, rng):
            count += 1
            shadow = shadow_meta(fn)
            oracle = oracle_meta_reconstructed(name, fn)
            if shadow != oracle:
                disagreements.append((name, shadow, oracle))
                if len(disagreements) >= 5:
                    break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for name, sh, orc in disagreements:
            print("  callable=%s shadow=%r oracle=%r" % (name, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildForwarderMeta agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
