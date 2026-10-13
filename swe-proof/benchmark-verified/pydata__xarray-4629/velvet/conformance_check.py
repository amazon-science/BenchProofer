#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-4629.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo types (a `list[dict]` of source
              attribute mappings), via the mapping.md bijection (a mapping
              *object* ↔ a `Handle`; its contents ↔ `Entries`; the
              allocate-fresh + copy-contents sequence ↔ `dict(...)`). The impl
              region has NO A-consumed callee (axioms region is empty); the
              deep-copy A-reference is itself an I-transliteration here, so the
              whole shadow is R/I.
  * ORACLE  — patch.diff's behaviour: the patched
              `xarray.core.merge.merge_attrs(variable_attrs,
              combine_attrs="override")` applied at base_commit (the real
              correctness oracle, G-RESOLVE). The harness applies patch.diff
              before this runs.

Because the behaviour under change is an object-identity / aliasing property
(not a pure value), we compare the THREE observable consequences the spec pins,
each computed identically on both sides:

  (1) returned contents                         dict(result) == dict(sources[0])
  (2) result is a distinct object               result is not any source
  (3) source frame after mutating the result    sources unchanged

They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 4629
N_FUZZ = 100_000


# --- the R/I shadow: combineFirst's impl region, transliterated --------------

def shadow_combine_first(sources):
    """`combineFirst` impl over real dict objects: allocate a fresh object
    (mapping.md: fresh Handle + Function.update + bump), copy sources[0]'s
    contents into it, return it. The R/I transliteration of the do-block is
    exactly `dict(sources[0])`."""
    assert sources, "require sources != []"
    return dict(sources[0])


# --- the oracle: patch.diff's behaviour --------------------------------------

def oracle_combine_first(sources):
    """patch.diff behaviour: the patched merge_attrs under combine_attrs
    'override'. Resolved from the repo at base_commit with the gold patch
    applied (the harness applies patch.diff before this runs)."""
    from xarray.core.merge import merge_attrs
    return merge_attrs(sources, "override")


# --- the three observable consequences, computed identically on both sides ---

def observe(combine, sources):
    """Return a comparable tuple of the three identity/contents observables.
    `sources` is consumed fresh per call by the driver."""
    pre = [dict(d) for d in sources]
    result = combine(sources)
    contents = dict(result)                              # (1)
    distinct = tuple(result is not d for d in sources)   # (2)
    # (3) mutate result with a guaranteed-absent key, observe source frame
    sentinel = "__conf_sentinel__"
    while any(sentinel in d for d in sources) or sentinel in result:
        sentinel += "x"
    result[sentinel] = "MUTATED"
    frame_ok = tuple(dict(d) == pre[i] for i, d in enumerate(sources))
    return (contents, distinct, frame_ok)


def rand_dict(rng):
    keys = ["a", "b", "x", "y", "key", "", "a b", "0", "ünïcode", "k" * 9]
    vals = ["b", "c", "d", "0", "", "value", "•", "V" * 6]
    n = rng.randint(0, 5)
    return {rng.choice(keys): rng.choice(vals) for _ in range(n)}


def fuzz_inputs(n, rng):
    # boundary cases first
    yield [{"a": "b"}, {"a": "c"}]
    yield [{"x": "0"}, {"x": "1"}]            # the F2P MCVE
    yield [{"x": "0"}]
    yield [{}]
    yield [{}, {"a": "b"}]
    yield [{"a": "b", "c": "d"}, {}]
    yield [{"a": "1"}, {"a": "2"}, {"a": "3"}]
    for _ in range(n):
        k = rng.randint(1, 4)                 # require non-empty
        yield [rand_dict(rng) for _ in range(k)]


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for src_template in fuzz_inputs(N_FUZZ, rng):
        count += 1
        # independent fresh copies for the two observers (each observer mutates
        # its own result; comparing them requires identical fresh inputs)
        shadow = observe(shadow_combine_first, [dict(d) for d in src_template])
        oracle = observe(oracle_combine_first, [dict(d) for d in src_template])
        if shadow != oracle:
            disagreements.append((src_template, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of combineFirst agrees with patch.diff "
          "behaviour (returned-contents, distinct-identity, source-frame) on "
          "%d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
