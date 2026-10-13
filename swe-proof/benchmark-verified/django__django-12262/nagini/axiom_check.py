#!/usr/bin/env python3
"""G-AX / deep-model soundness check for django__django-12262.

This bundle consumes NO `@ContractOnly` axiom: the keyword-binding decision is
membership/duplication control-flow logic over the binder's own inputs, modelled
DEEPLY by the `outcome` fold in model.py. There is therefore no opaque library
callee to over-approximate. What this script validates is the A-reference of the
deep model: that the abstract `outcome` fold (re-encoded here in lock-step with
model.py) computes EXACTLY the keyword-binding outcome of the REAL fixed
control flow that the gold patch establishes -- the post-patch `parse_bits`
keyword branch:

    for each successfully-extracted keyword `param`:
        if param not in params and param not in kwonly and varkw is None:
            -> UNEXPECTED              (outcome code 1)
        elif param already recorded:
            -> DUPLICATE               (outcome code 2)
        else:
            record it (consume from unhandled if positional/keyword-only)
    -> OK                              (outcome code 0)

We run that real decision (a faithful transcription of the patched repo branch,
including the construction of `unhandled_kwargs` from `kwonly`/`kwonly_defaults`
exactly as the repo does) against the abstract model over boundary cases and
heavy randomized fuzzing, and assert they agree on every input. We also assert
that the abstract model strictly DISAGREES with the pre-patch (buggy) decision
on the two witness families the issue describes, so the differential is real.

stdlib-only imports; exit 0 iff every observation matches.
"""
import itertools
import random
import sys


# --- model.py reference encodings (kept in lock-step with the pure region) ---

def m_contains(seq, x):
    return x in seq


def m_acceptable(positional, keyword_only, catch_all, name):
    return catch_all or m_contains(positional, name) or m_contains(keyword_only, name)


def m_outcome(supplied, positional, keyword_only, catch_all):
    """Abstract `outcome` fold from model.py (0 OK, 1 UNEXPECTED, 2 DUPLICATE)."""
    seen = []
    for name in supplied:
        if not m_acceptable(positional, keyword_only, catch_all, name):
            return 1
        if m_contains(seen, name):
            return 2
        seen.append(name)
    return 0


# --- the REAL fixed parse_bits keyword decision (post-patch repo branch) ------

def real_fixed_outcome(supplied, params, kwonly, kwonly_defaults, varkw_none):
    """Faithful transcription of the post-patch `parse_bits` keyword-handling
    branch (django/template/library.py), reduced to its outcome code.

    The post-patch condition is `param not in params and param not in kwonly
    and varkw is None`. `unhandled_kwargs` is still maintained exactly as the
    repo builds/consumes it (it now governs only the 'still required' final
    check, not acceptability)."""
    kwargs = {}                      # the recorded keyword arguments
    unhandled_kwargs = [k for k in kwonly
                        if not kwonly_defaults or k not in kwonly_defaults]
    for param in supplied:
        if param not in params and param not in kwonly and varkw_none:
            return 1                 # unexpected keyword argument
        elif param in kwargs:
            return 2                 # multiple values for keyword argument
        else:
            kwargs[param] = True
            if param in unhandled_kwargs:
                unhandled_kwargs.remove(param)
    return 0


def real_buggy_outcome(supplied, params, kwonly, kwonly_defaults, varkw_none):
    """The PRE-patch (buggy) branch: condition used `unhandled_kwargs` instead
    of `kwonly`. Used only to confirm the differential is real."""
    kwargs = {}
    unhandled_kwargs = [k for k in kwonly
                        if not kwonly_defaults or k not in kwonly_defaults]
    for param in supplied:
        if param not in params and param not in unhandled_kwargs and varkw_none:
            return 1
        elif param in kwargs:
            return 2
        else:
            kwargs[param] = True
            if param in unhandled_kwargs:
                unhandled_kwargs.remove(param)
    return 0


def check_match(supplied, params, kwonly, kwonly_defaults, catch_all):
    """Assert the abstract `outcome` == the real fixed decision."""
    varkw_none = not catch_all
    expected = real_fixed_outcome(supplied, params, kwonly, kwonly_defaults, varkw_none)
    observed = m_outcome(supplied, params, kwonly, catch_all)
    assert observed == expected, (
        "deep model unsound on supplied=%r params=%r kwonly=%r defaults=%r "
        "catch_all=%r: real fixed parse_bits -> %r, model outcome -> %r"
        % (supplied, params, kwonly, kwonly_defaults, catch_all, expected, observed))


def main():
    # --- boundary cases: the two witness families from the issue -------------
    # Bug 1: keyword-only WITH default, supplied once -> must be OK (0).
    assert real_buggy_outcome([1], [], [1], {1}, True) == 1   # buggy: UNEXPECTED
    assert real_fixed_outcome([1], [], [1], {1}, True) == 0   # fixed: OK
    check_match([1], [], [1], {1}, False)

    # Bug 2: keyword-only no default, supplied twice -> must be DUPLICATE (2).
    assert real_buggy_outcome([1, 1], [], [1], set(), True) == 1   # buggy: UNEXPECTED
    assert real_fixed_outcome([1, 1], [], [1], set(), True) == 2   # fixed: DUPLICATE
    check_match([1, 1], [], [1], set(), False)

    # assorted explicit boundaries
    explicit = [
        ([], [], [], set(), False),
        ([], [], [], set(), True),
        ([1], [1], [], set(), False),             # positional supplied as kwarg
        ([1, 1], [1], [], set(), False),          # positional twice -> DUPLICATE
        ([9], [], [], set(), False),              # unknown, no catch-all -> UNEXPECTED
        ([9], [], [], set(), True),               # unknown, catch-all -> OK
        ([1, 2], [], [1, 2], {2}, False),         # mix default / no-default kwonly
        ([2, 2], [], [1, 2], {2}, False),         # defaulted kwonly twice -> DUPLICATE
        ([1, 9, 1], [], [1], set(), False),       # UNEXPECTED before the duplicate
        ([1, 1, 9], [], [1], set(), False),       # DUPLICATE before the unknown
    ]
    for supplied, params, kwonly, defaults, catch_all in explicit:
        check_match(supplied, params, kwonly, defaults, catch_all)

    # --- exhaustive small enumeration ----------------------------------------
    names = [1, 2, 3]
    name_universe = [0, 1, 2, 3, 9]   # 0/9 are never declared
    for params in _subsets(names):
        for kwonly in _subsets([n for n in names if n not in params]):
            for defaults in _subsets(kwonly):
                for catch_all in (False, True):
                    for length in range(0, 4):
                        for supplied in itertools.product(name_universe, repeat=length):
                            check_match(list(supplied), list(params), list(kwonly),
                                        set(defaults), catch_all)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(12262)
    universe = list(range(0, 8))
    for _ in range(40000):
        params = _rand_subset(rng, universe)
        rest = [n for n in universe if n not in params]
        kwonly = _rand_subset(rng, rest)
        defaults = set(_rand_subset(rng, kwonly))
        catch_all = rng.random() < 0.5
        n = rng.randint(0, 8)
        supplied = [rng.choice(universe) for _ in range(n)]
        check_match(supplied, params, kwonly, defaults, catch_all)

    print("G-AX OK: abstract outcome fold == real fixed parse_bits keyword "
          "decision on 12 boundary + exhaustive small enumeration + 40000 fuzz "
          "inputs; pre-patch differential confirmed on both issue witnesses.")
    return 0


def _subsets(xs):
    for r in range(0, len(xs) + 1):
        for c in itertools.combinations(xs, r):
            yield list(c)


def _rand_subset(rng, xs):
    return [x for x in xs if rng.random() < 0.5]


if __name__ == "__main__":
    sys.exit(main())
