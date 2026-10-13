#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-13439.

This bundle ships **no `@ContractOnly` axiom** and **no A-reference deep model**:
the changed behaviour (report the composite's size as the cardinality of its
stage collection) is modeled directly with `len(steps)` over a `List[int]`
carrier, and the proof consumes no callee contract. There is therefore no callee
contract to validate against a real implementation.

What this script does instead, for completeness and to make the single
refinement assumption explicit and machine-checkable: it exercises the fact
refinement.md relies on — the gold patch's `__len__` returns `len(self.steps)`,
i.e. exactly the number of stages the composite was constructed from, every
stage counted once including the final stage and any inert ('passthrough'/None)
placeholder stages. It does so with a stdlib-only stand-in for a step list (a
plain Python `list` of `(name, estimator)` 2-tuples, mirroring `Pipeline.steps`)
and the gold `__len__` body (`len(self.steps)`), checking that the reported size
equals the constructed stage count across:

  * single-stage and multi-stage collections,
  * collections that include inert 'passthrough' / None placeholder stages,
  * the F2P scenario: a 2-step pipeline reports size 2,

and that the model's `composite_size` reference (`len(steps)` over the abstract
`List[int]`) agrees with the gold `__len__` on every one. Imports only the
standard library (no sklearn, nothing repo-specific). Exit 0 iff every
observation matches the model.
"""
import sys


class FakePipeline:
    """Stdlib-only stand-in carrying just the touched field `steps` (a list of
    (name, estimator) 2-tuples) and the gold patch's `__len__` body."""

    def __init__(self, steps):
        self.steps = list(steps)

    def __len__(self):
        # gold hunk verbatim: returns the length of the Pipeline
        return len(self.steps)


def composite_size(steps):
    """Reference of model.py's `composite_size`: the reported size is the
    cardinality of the stage collection."""
    return len(steps)


def check(steps):
    """The gold __len__ on a real-shaped step list must equal the constructed
    stage count, and must equal the model's abstract size on the same count."""
    pipe = FakePipeline(steps)
    n = len(steps)
    # gold __len__ counts every stage once (no stage dropped, none doubled)
    assert len(pipe) == n, (
        "gold __len__ must report the full stage count %d, got %d for %r"
        % (n, len(pipe), steps))
    # model's abstract size (len over the List[int] carrier, one int per stage)
    # agrees on the same cardinality
    assert composite_size(list(range(n))) == n
    assert composite_size(list(range(n))) == len(pipe)


def main():
    est = object()

    # --- single-stage and multi-stage collections ----------------------------
    check([("clf", est)])
    check([("a", est), ("clf", est)])
    check([("a", est), ("b", est), ("clf", est)])

    # --- inert placeholder stages still counted ('passthrough' / None) --------
    check([("a", "passthrough"), ("clf", est)])
    check([("a", None), ("b", "passthrough"), ("clf", est)])
    check([("a", None), ("b", None), ("c", None)])

    # --- the F2P scenario: make_pipeline(DummyTransf(), SVC()) -> 2 steps -----
    f2p = FakePipeline([("dummytransf", est), ("svc", est)])
    assert len(f2p) == 2, "F2P: a 2-step pipeline must report len == 2"
    assert composite_size([0, 1]) == 2

    # --- breadth over many sizes (including 0 and a large count) --------------
    for n in [0, 1, 2, 3, 5, 8, 13, 50]:
        check([("s%d" % i, est) for i in range(n)])

    print("G-AX OK: no consumed axiom / no A-reference; the gold __len__ "
          "(len(self.steps)) reports the full stage count on single/multi/"
          "placeholder collections, and the model's len(steps) matches it "
          "(F2P 2-step -> 2).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
