#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-13496
(nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The model IS Python:
`refit_to_size` dispatching over `reuse_and_extend` / `rebuild_all` runs
directly over plain lists. The @Pure helpers (`FRESH_MEMBER`,
`effective_reuse`, `fresh_run`, `lemma_fresh_snoc`) copy over as plain
functions; `PSeq` becomes a tuple shim. There are no @ContractOnly callees
(the axioms region is empty).

ORACLE: the REAL patched repo behaviour the model models per mapping.md —
`sklearn.ensemble.IsolationForest`'s incremental roster: the constructor's
`warm_start` option is stored and later read at fit time to decide whether
the existing `self.estimators_` are kept (and merely extended up to
`n_estimators`) or the whole forest is rebuilt. The gate applies the gold
patch to /testbed before this script runs and sets PYTHONPATH so the patched
package is what imports here; this script does NOT apply any patch itself.

Type bridge (mapping.md section 2):
  * the roster of already-fitted members (an object list) maps to a
    `List[int]` of member identities: the k-th prior member gets identity k
    (non-negative and distinct, satisfying the precondition); a member of
    the refit roster that IS (object identity) some prior member maps to
    that member's identity, and any other member is freshly built and maps
    to the sentinel -1 (`FRESH_MEMBER()`). Prior members are held as LIVE
    references and freshness is decided with `is`, so a recycled memory
    address can never masquerade as a survivor;
  * the requested total maps identically to `target_count` (the estimator's
    configured member count);
  * the caller's construction-time reuse option maps identically to
    `requested_reuse` (a plain bool).

Per observation the shadow `refit_to_size(existing_ids, n_total, w)` output
is diffed elementwise against the bridged real roster after the refit.

Input domain (the Requires): identities non-negative and
`len(existing) <= target_count` — both satisfied by construction of the
bridge (positional identities; the real estimator itself rejects shrinking a
kept roster, so only enlarging refits are generated, exactly the Requires).

>= 1e5 Requires-satisfying inputs:
  * 100000 constructor-forwarding fuzz cases: construct the estimator with a
    fuzzed option value (or omit it, exercising the default) under varied
    other constructor settings, and diff the shadow's pure reuse decision
    `effective_reuse(w, have)` against the real fit-time predicate rebuilt
    from the stored option (`clf.warm_start and have`) for both membership
    states — this is the exact data flow under specification: the option
    must be carried through construction faithfully;
  * a real double-fit battery (boundary cases incl. the 10->20 scenario,
    equal-size refit, first-ever fit with an empty roster, plus fuzz), each
    case run for BOTH option values, diffing the full shadow roster against
    the bridged real `estimators_` (prefix preservation / all-fresh rebuild,
    exact final size).

Pinned fuzz seed: 134960 (recorded here).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy only.
"""
import random
import sys
import warnings

import numpy as np

SEED = 134960
N_FLAG_FUZZ = 100000
N_FIT_FUZZ = 60          # fuzzed double-fit scenarios (each run for both options)


# --- PSeq shim: the model's pure sequences over a plain tuple -----------------

class _Seq(tuple):
    def take(self, n):
        return _Seq(self[:max(n, 0)])

    def drop(self, n):
        return _Seq(self[max(n, 0):])

    def __add__(self, other):
        return _Seq(tuple(self) + tuple(other))


def PSeq(*xs):
    return _Seq(xs)


# --- SHADOW: model.py pure region, contracts stripped --------------------------

def FRESH_MEMBER():
    return -1


def effective_reuse(requested_reuse, have_members):
    return requested_reuse and have_members


def fresh_run(n):
    if n <= 0:
        return PSeq(0).take(0)
    return PSeq(FRESH_MEMBER()) + fresh_run(n - 1)


def lemma_fresh_snoc(n):
    if n == 0:
        return True
    return lemma_fresh_snoc(n - 1)


# --- SHADOW: model.py impl region, verbatim, contract calls stripped -----------

def reuse_and_extend(existing, target_count):
    result = []  # type: list
    j = 0
    while j < len(existing):
        result.append(existing[j])
        j = j + 1
    while len(result) < target_count:
        result.append(FRESH_MEMBER())
    return result


def rebuild_all(target_count):
    result = []  # type: list
    while len(result) < target_count:
        result.append(FRESH_MEMBER())
    return result


def refit_to_size(existing, target_count, requested_reuse):
    if requested_reuse and len(existing) > 0:
        return reuse_and_extend(existing, target_count)
    else:
        return rebuild_all(target_count)


# --- oracle plumbing ------------------------------------------------------------

def _fail(msg, scenario, shadow_out, real_out):
    print("DISAGREEMENT: %s" % msg)
    print("  scenario          = %r" % (scenario,))
    print("  shadow output     = %r" % (shadow_out,))
    print("  real (bridged)    = %r" % (real_out,))
    sys.exit(1)


def _fit_objs(clf, X):
    """Fit and return the roster as LIVE object references (mirrors the
    identity abstraction: holding the objects alive makes `is`-freshness
    sound against address recycling)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        clf.fit(X)
    return list(clf.estimators_)


def _bridge(result_objs, existing_objs):
    """Lower the real refit roster to model identities: position k of the
    prior roster is identity k; anything not (by `is`) a prior member is a
    freshly-built member, i.e. the sentinel -1."""
    out = []
    for obj in result_objs:
        ident = FRESH_MEMBER()
        for j, e in enumerate(existing_objs):
            if obj is e:
                ident = j
                break
        out.append(ident)
    return out


def check_flag_forwarding(IsolationForest, rng):
    """1e5 constructor cases: the option the caller supplies must be stored
    faithfully, so the fit-time reuse predicate equals the shadow's pure
    `effective_reuse` for both membership states."""
    checked = 0
    for i in range(N_FLAG_FUZZ):
        w = rng.random() < 0.5
        omit = rng.random() < 0.1  # exercise the default (opt-out) too
        kwargs = {
            "n_estimators": rng.randint(1, 50),
            "max_samples": rng.choice(["auto", 0.5, 1.0, 8]),
            "max_features": rng.choice([1.0, 0.5, 1]),
            "bootstrap": rng.random() < 0.5,
            "random_state": rng.randint(0, 10**6),
        }
        if not omit:
            kwargs["warm_start"] = w
        requested = False if omit else w
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            clf = IsolationForest(**kwargs)
        stored = clf.warm_start
        for have in (False, True):
            shadow = effective_reuse(requested, have)
            real = bool(stored and have)
            if shadow != real:
                _fail("reuse decision differs (option not carried through)",
                      {"case": i, "requested": requested, "omitted": omit,
                       "have_members": have, "kwargs": kwargs},
                      shadow, real)
        checked += 1
    return checked


def check_refit(IsolationForest, n_first, n_total, w, seed):
    """One full double-fit observation: fit n_first members (unless n_first
    is 0: first-ever fit over an empty roster), enlarge to n_total, refit;
    diff the shadow roster against the bridged real one."""
    rng = np.random.RandomState(seed)
    X = rng.randn(16, 2)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        clf = IsolationForest(n_estimators=max(n_first, 1), max_samples=16,
                              random_state=rng, warm_start=w)
    if n_first > 0:
        existing_objs = _fit_objs(clf, X)
    else:
        existing_objs = []
    clf.set_params(n_estimators=n_total)
    result_objs = _fit_objs(clf, X)

    existing_ids = list(range(len(existing_objs)))  # non-negative, distinct
    existing_snapshot = list(existing_ids)
    shadow_out = refit_to_size(existing_ids, n_total, w)
    real_out = _bridge(result_objs, existing_objs)

    scenario = {"n_first": n_first, "n_total": n_total,
                "requested_reuse": w, "seed": seed}
    if existing_ids != existing_snapshot:
        _fail("shadow mutated its read-only input roster", scenario,
              shadow_out, real_out)
    if len(real_out) != n_total:
        _fail("real roster size differs from the requested total", scenario,
              shadow_out, real_out)
    if shadow_out != real_out:
        _fail("refit roster differs (prefix preservation / rebuild)",
              scenario, shadow_out, real_out)
    # keep prior members alive through the identity comparisons above
    assert len(existing_objs) == n_first


def main():
    try:
        from sklearn.ensemble import IsolationForest
    except Exception as exc:
        print("ERROR: cannot import the estimator under test: %r" % (exc,))
        return 2

    rng = random.Random(SEED)

    # ---- 1e5 constructor-forwarding fuzz ----
    n_flag = check_flag_forwarding(IsolationForest, rng)

    # ---- real double-fit battery: boundary + fuzz, both option values ----
    boundary = [
        (10, 20),   # the enlarge-after-fit scenario
        (0, 1),     # first-ever fit: empty roster, reuse decision is moot
        (0, 5),
        (1, 1),     # equal-size refit (no new members on reuse)
        (1, 2),
        (5, 5),
        (3, 4),
        (2, 9),
        (7, 13),
    ]
    n_fit = 0
    for (a, b) in boundary:
        for w in (False, True):
            check_refit(IsolationForest, a, b, w, seed=rng.randint(0, 10**6))
            n_fit += 1
    for _ in range(N_FIT_FUZZ):
        a = rng.randint(0, 10)
        b = a + rng.randint(0, 8)
        if b == 0:
            b = 1
        for w in (False, True):
            check_refit(IsolationForest, a, b, w, seed=rng.randint(0, 10**6))
            n_fit += 1

    print("G-CONF OK: shadow of the model impl agrees with the real patched "
          "estimator over %d constructor-forwarding cases (x2 membership "
          "states) + %d full double-fit rosters (prefix preservation, "
          "all-fresh rebuild, exact size); seed=%d" % (n_flag, n_fit, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
