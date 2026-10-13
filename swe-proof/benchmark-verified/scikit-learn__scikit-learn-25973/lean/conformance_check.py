#!/usr/bin/env python3
"""G-CONF for scikit-learn__scikit-learn-25973.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_repeatedEvaluations` (the Lean impl,
transliterated op-for-op per refinement.md) against the REAL patched mechanism
of `SequentialFeatureSelector.fit` over >=1e5 fuzzed inputs. Zero
disagreements => exit 0.

The modeled function is `fit`'s repeated scoring loop. `fit` evaluates many
candidate features; each candidate calls `cross_val_score(..., cv=...)`, which
internally runs the splits supplied by the cv source. The bug: when the cv
source is a single-traversal iterable (a generator), reading it once drains it,
so every later evaluation sees an EMPTY split set and the run breaks. The fix
materialises the splits ONCE up front via `check_cv(self.cv, ...)`, producing a
reusable cross-validator whose `.split()` re-yields the complete split set on
every call; that reusable object is then threaded into every `cross_val_score`.

We isolate that mechanism by driving the REAL patched callees `check_cv` and
`_CVIterableWrapper` (sklearn.model_selection) — exactly what the fix inserts —
with a single-traversal generator (`oneShot=True`) or a re-readable list
(`oneShot=False`) of split tokens, then record the split set OBSERVED by each of
`numEvals` consultations. The patched path captures once, so every consultation
observes the complete set.

Type bijection (mapping.md):
  folds : List Nat          <-> the sequence of split tokens the cv source yields
  oneShot : Bool            <-> the source is a single-traversal generator
  numEvals : Nat            <-> number of candidate-feature evaluations in `fit`
  result : List (List Nat)  <-> per-evaluation observed split set, in order

Exit 0 iff zero disagreements over >=1e5 fuzzed inputs. stdlib + sklearn only.
"""
import random
import sys

from sklearn.model_selection import check_cv


# --- shadow: R/I transliteration of implementation_repeatedEvaluations --------
def shadow(folds, one_shot, num_evals):
    """Mirror of the Lean impl: capture the collection once, then every
    evaluation observes the complete collection. `one_shot` is not consulted."""
    shared = list(folds)
    observed = []
    for _ in range(num_evals):
        observed.append(list(shared))
    return observed


# --- oracle: drive the REAL patched mechanism (check_cv reuse) ----------------
def make_source(folds, one_shot):
    """A cv source carrying `folds` as split tokens. Each token n becomes a
    (train, test) split ([n], [n]); the token n IS recovered from train[0].

    one_shot=True  -> a generator (single traversal; drained after one read).
    one_shot=False -> a list (re-readable)."""
    pairs = [([n], [n]) for n in folds]
    if one_shot:
        return (p for p in pairs)          # generator: single-traversal
    return list(pairs)                      # list: re-readable


def observed_tokens(checked):
    """Read the split tokens a checked cross-validator yields on one .split()."""
    return [int(train[0]) for (train, test) in checked.split()]


def oracle(folds, one_shot, num_evals):
    """Run the REAL patched `fit` mechanism: materialise the cv source ONCE with
    check_cv, then consult the reusable result once per evaluation."""
    source = make_source(folds, one_shot)
    checked = check_cv(source, y=None, classifier=False)   # the line the fix adds
    observed = []
    for _ in range(num_evals):
        observed.append(observed_tokens(checked))           # cv reused each eval
    return observed


def main():
    rng = random.Random(25973)   # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for _ in range(N):
        n_folds = rng.randint(0, 6)
        folds = [rng.randint(0, 9) for _ in range(n_folds)]
        one_shot = rng.random() < 0.5
        num_evals = rng.randint(0, 6)

        o = oracle(folds, one_shot, num_evals)
        s = shadow(folds, one_shot, num_evals)
        if o != s:
            disagreements += 1
            if first is None:
                first = (folds, one_shot, num_evals, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
