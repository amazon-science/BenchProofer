#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-5262 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo type (`str`), via the mapping.md
              bijection (`List Char` <-> `str`, `Char.ofNat (ord ch)` <-> ch).
              The impl region has NO A-tagged callee left as a real-repo call:
              the only callee (`self.buffer.mode`) is the modeled INPUT, fuzzed
              directly here. So the shadow is pure R/I (the `stripped` fold).
  * ORACLE  — `patch.diff`'s behaviour: the patched `EncodedFile.mode` property
              applied at base_commit (the real correctness oracle, G-RESOLVE).
              We construct a real `EncodedFile` over a stub buffer whose `.mode`
              is the fuzzed descriptor and read the patched property.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied),
stdlib only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 5262
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean stripped / stripStep, transliterated -------
def shadow_mode(raw_mode):
    """stripped (raw_mode.toList) transliterated to str: drop every 'b', keep
    every other code point in order. This is the R/I shadow of the impl's
    backward `while` fold (which computes exactly that concatenation)."""
    return "".join("" if ch == "b" else ch for ch in raw_mode)


# --- the oracle: patch.diff's behaviour (the patched property) ----------------
class _StubBuffer(object):
    """Minimal stand-in for the wrapped byte stream: only `.mode` is consulted
    by the patched `EncodedFile.mode` property."""
    def __init__(self, mode):
        self.mode = mode


def oracle_mode(raw_mode):
    """patch.diff's behaviour: the patched EncodedFile.mode property. Resolved
    from the repo at base_commit with the gold patch applied (the harness
    applies patch.diff before this runs)."""
    from _pytest.capture import EncodedFile  # patched: adds the `mode` property
    ef = EncodedFile(_StubBuffer(raw_mode), "utf-8")
    return ef.mode


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    boundary = [
        "", "b", "bb", "bbb",
        "r", "w", "a", "r+", "w+", "a+",
        "rb", "wb", "ab", "rb+", "wb+", "ab+",
        "br", "bw", "b+", "rbrb", "bxbxb",
        "+", "+b", "b+b",
        "B", "Rb", "rB", "0b", "b0",
    ]
    for s in boundary:
        yield s
    alphabet = list("rwab+xtUB0 ") + ["b", "b", "b"] + ["é", "•"]
    for _ in range(n):
        k = rng.randint(0, 16)
        yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_mode(s)
        oracle = oracle_mode(s)
        if shadow != oracle:
            disagreements.append((s, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of textStreamMode agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
