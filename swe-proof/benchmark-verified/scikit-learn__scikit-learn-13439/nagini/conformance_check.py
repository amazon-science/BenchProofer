#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-13439
(nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The model IS Python: `composite_size` is a
single plain function over a plain list. There are no @Pure helpers, no
@ContractOnly callees (the axioms region is empty), and no PSeq usage, so no
shim is needed.

ORACLE: the REAL patched repo function the model models per mapping.md —
`sklearn.pipeline.Pipeline.__len__`, i.e. the size reported by `len(pipe)`
for a composite estimator. The gate applies the gold patch to /testbed
before this script runs and sets PYTHONPATH so the patched package is what
imports here; this script does NOT apply any patch itself.

Type bridge (mapping.md section 2): the composite's ordered stage collection
(`pipe.steps`, a list of (name, estimator) 2-tuples) maps to the model's
`List[int]` carrier with one opaque element per stage; the element values are
irrelevant to the size query, only the cardinality is observed. So for a real
composite holding N stages the shadow input is `list(range(N))`, and the
observation compared is `len(pipe)` (oracle) vs `composite_size(...)`
(shadow), both plain ints.

Input domain: the model's precondition is just read access to the stage
list, so every finite stage count N >= 0 is Requires-satisfying. Two oracle
constructions cover it:
  * normally constructed composites (the constructor validates that
    non-final stages expose the transformer interface and the final stage
    exposes fit, and it accepts inert None / 'passthrough' placeholders) —
    exercised with duck-typed dummy stages, placeholders included; the
    constructor requires at least one stage, so this lane covers N >= 1;
  * objects allocated without running the constructor, with the stage list
    attached directly — valid receivers for the size query, which reads only
    the stage list; this lane covers N == 0 and arbitrary compositions.

>= 1e5 Requires-satisfying inputs: boundary stage counts (0, 1, 2, 3 and the
F2P-shaped 2-stage composite) plus 100000 fuzz cases over random stage
counts and random per-stage kinds (transformer / None / 'passthrough').
Pinned fuzz seed: 13439.

Exit 0 iff zero disagreements; on disagreement prints the input and both
sides' observations and exits 1. stdlib only (plus the repo under test).
"""
import json
import random
import sys

from typing import List

SEED = 13439
N_FUZZ = 100_000


# --- the impl region of model.py, verbatim, contracts stripped ---------------

def composite_size(steps: List[int]) -> int:
    # impl-start
    return len(steps)
    # impl-end


# --- duck-typed stages for normally-constructed composites -------------------

class DummyTransform(object):
    """Minimal stage exposing the transformer interface the constructor
    checks for (fit / transform)."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X


class DummyEstimator(object):
    """Minimal final stage exposing fit."""

    def fit(self, X, y=None):
        return self


def make_stage(kind, i):
    """One stage of the requested kind: a duck-typed transformer, or an
    inert placeholder (None / 'passthrough')."""
    if kind == 0:
        return ("s%d" % i, DummyTransform())
    if kind == 1:
        return ("s%d" % i, None)
    return ("s%d" % i, "passthrough")


def build_pipeline_constructed(Pipeline, kinds):
    """A normally-constructed composite with len(kinds) stages: non-final
    stages are transformers or inert placeholders; the final stage is a
    fit-bearing estimator or an inert placeholder."""
    steps = [make_stage(k, i) for i, k in enumerate(kinds[:-1])]
    last = len(kinds) - 1
    if kinds[last] == 0:
        steps.append(("s%d" % last, DummyEstimator()))
    else:
        steps.append(make_stage(kinds[last], last))
    return Pipeline(steps)


def build_pipeline_raw(Pipeline, kinds):
    """A composite allocated without the constructor, stage list attached
    directly (the size query reads only the stage list). Covers the empty
    collection and arbitrary compositions."""
    pipe = Pipeline.__new__(Pipeline)
    pipe.steps = [make_stage(k, i) for i, k in enumerate(kinds)]
    return pipe


def check(Pipeline, kinds, constructed):
    """Diff the shadow against the real size query on a composite with
    len(kinds) stages."""
    if constructed:
        pipe = build_pipeline_constructed(Pipeline, kinds)
    else:
        pipe = build_pipeline_raw(Pipeline, kinds)
    n = len(pipe.steps)
    # bridge: one opaque int per real stage
    shadow = composite_size(list(range(n)))
    real = len(pipe)  # the REAL patched size query
    if shadow != real:
        print("DISAGREEMENT\n  stage kinds=%r constructed=%r n_stages=%d\n"
              "  shadow composite_size=%r\n  real len(pipe)=%r"
              % (kinds, constructed, n, shadow, real))
        return False
    return True


def main():
    from sklearn.pipeline import Pipeline  # REAL patched repo class

    checked = 0

    # --- boundary cases -------------------------------------------------------
    boundary = [
        ([], False),                 # empty stage collection (raw receiver)
        ([0], True), ([0], False),   # single stage
        ([1], True), ([2], True),    # single inert placeholder as final stage
        ([0, 0], True),              # 2 stages (the F2P-shaped composite)
        ([0, 0], False),
        ([1, 0], True),              # inert placeholder + estimator
        ([2, 0], True),
        ([0, 1], True),              # inert final stage
        ([0, 0, 0], True),
        ([1, 2, 0], True),           # both placeholder kinds present
        ([1, 1, 1], False),
        ([0] * 50, True),            # larger composite
    ]
    for kinds, constructed in boundary:
        if not check(Pipeline, kinds, constructed):
            return 1
        checked += 1

    # also sanity: the F2P-shaped 2-stage composite reports size 2
    pipe2 = build_pipeline_constructed(Pipeline, [0, 0])
    if len(pipe2) != 2 or composite_size([0, 1]) != len(pipe2):
        print("DISAGREEMENT\n  F2P-shaped 2-stage composite\n"
              "  shadow=%r real=%r" % (composite_size([0, 1]), len(pipe2)))
        return 1
    checked += 1

    # --- fuzz: 1e5 random compositions, pinned seed ---------------------------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        constructed = rng.random() < 0.5
        lo = 1 if constructed else 0
        n = rng.randint(lo, 12)
        kinds = [rng.randint(0, 2) for _ in range(n)]
        if not check(Pipeline, kinds, constructed):
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real size query on %d composites "
          "(boundary + fuzz, seed %d)." % (checked, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
