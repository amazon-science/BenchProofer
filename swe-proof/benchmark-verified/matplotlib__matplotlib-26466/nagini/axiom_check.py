#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-26466.

This bundle consumes NO `@ContractOnly` axiom and references NO deep-model
A-reference (the `axioms` and `pure` regions of model.py are empty): the modeled
delta -- "retain a fresh, independently-owned copy of the caller's 2-component
reference coordinate, not an alias of the caller's container" -- is expressed
DIRECTLY in Nagini via fractional `list_pred` permissions (the caller keeps a
read share of its input; the constructed object fully owns a distinct fresh
pair).

G-AX therefore reduces to a BEHAVIOURAL-EQUIVALENCE / DECOUPLING check against
the REAL repo callees: construct the two real objects from a MUTABLE numpy array
coordinate, then mutate that array IN PLACE after construction, and assert the
coordinate the object retained is unchanged AND equals the two component values
present at construction time -- exactly the postcondition the model pins
(`Result()` is a fresh length-2 pair carrying the input's two components, decoupled
from the input). This is the property the hidden F2P test
(`test_annotate_and_offsetfrom_copy_input`) observes (it mutates `of_xy[:]=1`
and `an_xy[:]=2` after the calls and compares the two rendered figures).

The script also asserts (for documentation, mirroring G-DIFF) that the modeled
DECOUPLING is the post-patch behaviour: it constructs from arrays of two known
values and checks the retained pair equals those values both before AND after an
in-place mutation of the source array.

Imports only `numpy` and the repo's own `matplotlib` (the very package the patch
lives in) -- no Nagini, nothing model-specific. Exit 0 iff every obligation holds.
"""
import sys

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.text import OffsetFrom


def as_pair(value):
    """Read the retained coordinate as a plain (x, y) tuple of Python floats.

    The retained value is the model's `Result()` (a length-2 ordered pair). It
    may be a tuple of scalars (post-patch) or an ndarray (the aliasing bug);
    either way we read its two components by index 0 / index 1, mirroring the
    model's `Result()[0]`, `Result()[1]`."""
    x, y = value[0], value[1]
    return (float(x), float(y))


def check_decoupled(retained_getter, make_input, mutate, label):
    """Construct an object from a MUTABLE 2-component array input, record the
    retained pair, mutate the source array in place, and assert the retained
    pair (a) equals the components present at construction time and (b) does NOT
    change when the source is later mutated -- the model's freshness/decoupling
    postcondition validated on the REAL callee."""
    src = make_input()                       # mutable numpy array, e.g. [.5, .5]
    v0, v1 = float(src[0]), float(src[1])     # the two components at this moment
    obj = retained_getter(src)               # run the REAL constructor
    before = as_pair(obj())                   # retained pair right after construction
    assert before == (v0, v1), (
        "%s: retained pair %r != input components %r at construction"
        % (label, before, (v0, v1)))
    mutate(src)                               # caller mutates its own array in place
    after = as_pair(obj())                    # retained pair after the mutation
    assert after == (v0, v1), (
        "%s: retained pair changed to %r after the caller mutated its input "
        "(expected the fixed construction-time pair %r) -- the object aliased "
        "the caller's container instead of copying it" % (label, after, (v0, v1)))
    return (v0, v1)


def main():
    n_checks = 0

    # ----- Site #1: OffsetFrom retains ref_coord -----------------------------
    # OffsetFrom stores the reference coordinate directly on self._ref_coord;
    # read it back as the retained pair.
    def offsetfrom_retainer(src):
        fig = plt.figure()
        ax = fig.add_subplot()
        (line,) = ax.plot([0, 2], [0, 2])
        of = OffsetFrom(line, src)            # REAL constructor (site #1)
        plt.close(fig)
        return lambda: of._ref_coord

    # ----- Site #2: Annotation (_AnnotationBase) retains xy -------------------
    # Annotation.__init__ -> _AnnotationBase.__init__ stores self.xy; read back.
    def annotation_retainer(src):
        fig = plt.figure()
        ax = fig.add_subplot()
        ann = ax.annotate("foo", xy=src, xytext=(10, 0),
                          textcoords="offset points")  # REAL constructor (site #2)
        plt.close(fig)
        return lambda: ann.xy

    boundary = [
        (np.array([0.5, 0.5]), lambda a: a.__setitem__(slice(None), 1)),
        (np.array([-4.0, 1.0]), lambda a: a.__setitem__(1, 3)),
        (np.array([1.0, 1.0]), lambda a: a.__setitem__(slice(None), 2)),
        (np.array([0.0, 0.0]), lambda a: a.__setitem__(0, 9.0)),
        (np.array([3.25, -7.75]), lambda a: a.__setitem__(slice(None), -1)),
    ]
    for arr, mut in boundary:
        check_decoupled(offsetfrom_retainer, lambda a=arr: a.copy(),
                        mut, "OffsetFrom._ref_coord")
        check_decoupled(annotation_retainer, lambda a=arr: a.copy(),
                        mut, "Annotation.xy")
        n_checks += 2

    # ----- fuzz: random 2-vectors and random in-place mutations --------------
    rng = np.random.default_rng(26466)
    for _ in range(150):
        base = rng.uniform(-100.0, 100.0, size=2)

        def mk(a=base):
            return a.copy()

        # mutate one or both components to fresh random values
        if rng.random() < 0.5:
            idx = int(rng.integers(0, 2))
            newv = float(rng.uniform(-100.0, 100.0))

            def mut(a, idx=idx, newv=newv):
                a[idx] = newv
        else:
            newv = float(rng.uniform(-100.0, 100.0))

            def mut(a, newv=newv):
                a[:] = newv

        check_decoupled(offsetfrom_retainer, mk, mut, "OffsetFrom._ref_coord/fuzz")
        check_decoupled(annotation_retainer, mk, mut, "Annotation.xy/fuzz")
        n_checks += 2

    print("G-AX OK: real OffsetFrom._ref_coord and Annotation.xy each retain a "
          "fresh, decoupled copy of the caller's 2-component array (unchanged "
          "after %d in-place mutations of the source); matches the model's "
          "freshness/value postcondition. No consumed axiom." % n_checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
