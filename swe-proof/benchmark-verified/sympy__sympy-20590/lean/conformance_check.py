#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
`implementation_immutableInstances` against the post-patch behaviour.

The impl region is NOT all-A-tagged: it is a genuine conjunction-fold (I/R
content) over the ancestry layers' layout-pinning flags. There is no consumed
callee axiom and no A-reference op, so the shadow is purely the fold —
`result = all(otherLayers)` — and the "real behaviour" leg is CPython's ACTUAL
instance-layout semantics: we dynamically build a linear class chain in which
each ancestry layer declares an empty fixed-attribute set (`__slots__ = ()`) iff
its flag is true, plus the (post-patch) fixed mixin layer which ALWAYS declares
one, then observe `hasattr(instance, '__dict__')`.

We assert zero disagreements between the Lean fold prediction and the observed
CPython immutability over >= 10^5 fuzzed ancestry configurations.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 20590          # pinned in mapping.md
N = 120_000           # >= 10^5


def lean_shadow(other_layers):
    """R/I shadow of implementation_immutableInstances:
        immutable := true; for pins in otherLayers: immutable := immutable && pins
    i.e. the conjunction-fold. The post-patch fixed mixin layer pins its layout,
    so it contributes the `true` initial accumulator."""
    immutable = True
    for pins in other_layers:
        immutable = immutable and pins
    return immutable


def cpython_observed(other_layers):
    """Build the real CPython instance-layout configuration and OBSERVE whether
    the resulting instance carries a per-instance attribute dictionary.

    Chain: a base mixin layer that pins its layout (post-patch: `__slots__ = ()`)
    then one subclass per flag in `other_layers`, each declaring `__slots__ = ()`
    iff its flag is true (otherwise leaving its layout open). The instance is
    immutable iff it has no `__dict__`."""
    # The fixed mixin layer (post-patch) pins its layout.
    cls = type("Mixin", (object,), {"__slots__": ()})
    for i, pins in enumerate(other_layers):
        body = {"__slots__": ()} if pins else {}
        cls = type("Layer%d" % i, (cls,), body)
    inst = cls()
    return not hasattr(inst, "__dict__")


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary configurations first.
    fixed = [
        [],                       # only the fixed mixin -> immutable
        [True],
        [False],                  # one open layer -> mutable
        [True, True, True],
        [True, False, True],      # a single open layer anywhere reopens the dict
        [False, False],
        [True] * 8,
        [True] * 7 + [False],
    ]
    cases = fixed + [
        [rng.random() < 0.7 for _ in range(rng.randint(0, 12))]
        for _ in range(N)
    ]

    for layers in cases:
        predicted = lean_shadow(layers)
        observed = cpython_observed(layers)
        if predicted != observed:
            disagreements += 1
            if len(examples) < 10:
                examples.append((layers, predicted, observed))

    if disagreements:
        print("G-CONF FAIL: %d disagreements over %d cases" % (disagreements, len(cases)))
        for layers, pred, obs in examples:
            print("  layers=%r predicted_immutable=%r observed_immutable=%r"
                  % (layers, pred, obs))
        return 1

    print("G-CONF PASS: 0 disagreements over %d fuzzed configurations (seed=%d)"
          % (len(cases), SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
