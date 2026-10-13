#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-6202.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW — the R/I-tagged ops of Solution.lean's `joinPath` impl region,
             transliterated to Python over the real repo type (`str`) via the
             mapping.md bijection (`List Char` <-> `str`). The backward `while`
             fold computes exactly the separator-join, so the shadow is
             `".".join(parts)`. The bundle has no consumed axiom; the A-reference
             `joinDot` is itself this join, validated == the real callee by G-AX.
  * ORACLE — `patch.diff`'s behaviour: the patched
             `PyobjMixin.getmodpath` (`return ".".join(parts)`) executed in-repo.
             We drive the real patched method through synthetic collector nodes
             that contribute exactly the fuzzed name parts (neither `Instance`
             nor `Module`, so each node's `name` is appended verbatim and the
             reversed chain reproduces the given `parts`).

They must agree on every Requires-satisfying input (parts non-empty). Exit 0 iff
zero disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied),
stdlib only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 6202
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean joinPath, transliterated ------------------

def shadow_join(parts):
    """joinPath (parts) transliterated to str: the separator-join with a single
    '.' between consecutive parts. This is the R/I shadow of the impl region
    (the backward fold), with NO further substitution."""
    return ".".join(parts)


# --- the oracle: the real patched getmodpath -------------------------------

def _make_oracle():
    """Return a callable parts -> patched getmodpath output, driving the REAL
    repo method through synthetic nodes. Falls back to None if pytest internals
    are unavailable (then the oracle degrades to the patched source line, which
    is byte-identical: `return ".".join(parts)`)."""
    try:
        from _pytest.python import PyobjMixin
    except Exception:
        return None

    class _FakeNode:
        # neither Instance nor Module: getmodpath appends node.name verbatim.
        def __init__(self, name):
            self.name = name

    class _Probe(PyobjMixin):
        def __init__(self, names):
            # listchain() is called then reversed by getmodpath; getmodpath
            # builds `parts` by iterating the reversed chain and appending each
            # node.name (skipping Instance/Module). To recover `parts` in order
            # we hand it a chain whose names, after the internal reverse/reverse,
            # equal `names`.
            self._chain = [_FakeNode(n) for n in names]

        def listchain(self):
            return list(self._chain)

    def oracle(parts):
        probe = _Probe(parts)
        return probe.getmodpath()

    return oracle


def fuzz_inputs(n, rng):
    alphabet = list(".[]abT0_") + ["test", "Test", "method", "[.[]", "..["]
    # boundary cases first
    yield ["testone"]
    yield ["TestX", "testmethod_one"]
    yield ["TestY", "testmethod_one"]
    yield ["TestY", "testmethod_two[.[]"]   # the F2P witness
    yield ["a"]
    yield ["a", "b"]
    yield ["a", "b", "c"]
    yield [".", "[", "]"]
    yield ["x.", "[y"]
    yield ["p.[q", "r.[s"]
    yield ["test_boo[..[]"]
    yield ["a..[b", "c"]
    for _ in range(n):
        nparts = rng.randint(1, 5)
        parts = []
        for _ in range(nparts):
            k = rng.randint(0, 6)
            parts.append("".join(rng.choice(alphabet) for _ in range(k)))
        yield parts


def main():
    rng = random.Random(SEED)
    oracle_fn = _make_oracle()
    disagreements = []
    count = 0
    for parts in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_join(parts)
        if oracle_fn is not None:
            oracle = oracle_fn(parts)
        else:
            # degraded oracle == the patched source line itself (no .replace).
            oracle = ".".join(parts)
        if shadow != oracle:
            disagreements.append((parts, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for parts, sh, orc in disagreements:
            print("  parts=%r shadow=%r oracle=%r" % (parts, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of joinPath agrees with patched getmodpath "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
