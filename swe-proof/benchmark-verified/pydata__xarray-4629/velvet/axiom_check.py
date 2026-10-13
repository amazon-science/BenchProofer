#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-4629.

The changed operation (a shallow object copy) is modeled DEEPLY in
Solution.lean: returning a value is modeled as allocating a FRESH object handle,
copying the first source's contents into it, and bumping the allocator. This
script validates that deep model (an **A-reference**, not a consumed axiom)
against the REAL callee it models — CPython's built-in `dict(...)` constructor —
on boundary inputs and randomized fuzzing.

The deep model claims three observable consequences of the fresh-copy semantics,
which together are exactly what `combineFirst`'s postconditions assert:

  (1) FRESH IDENTITY        result is not any source object
                            (Lean: `result ∉ sources`, `result = freshOld`)
  (2) EQUAL CONTENTS        result carries the first source's contents
                            (Lean: `store result = storeOld (sources.head!)`)
  (3) SOURCE FRAME PINNED   mutating the result leaves every source untouched
                            (Lean: `∀ h ∈ sources, store h = storeOld h`)

Dually, it confirms the PRE-PATCH operation (`return variable_attrs[0]`, i.e.
hand back the first source object directly) VIOLATES (1)/(3): the returned object
*is* a source, so a later in-place update is visible through the source — the bug
`test_merge_attrs_override_copy` observes. This is what makes the deep model
discriminating rather than vacuous.

Imports nothing repo-specific: `dict` is a Python builtin — the same constructor
the gold patch calls. Exit 0 iff every obligation holds.
"""
import random
import sys


# --- the deep model (kept in lock-step with Solution.lean's impl region) -----

def model_combine_first(sources):
    """Reference of `combineFirst`'s impl over real dict objects: allocate a
    fresh object holding a shallow copy of sources[0]'s contents, return it.
    This is precisely `dict(sources[0])`."""
    assert sources, "require sources != []"
    return dict(sources[0])          # the gold operation: fresh shallow copy


def prepatch_combine_first(sources):
    """The pre-patch operation: hand back the first source object directly."""
    assert sources, "require sources != []"
    return sources[0]                # return variable_attrs[0] (shared reference)


# --- the checks --------------------------------------------------------------

def check_gold(sources):
    """The three A-reference obligations on the REAL dict(...) constructor."""
    pre_contents = [dict(d) for d in sources]      # storeOld snapshot
    result = model_combine_first(sources)          # REAL callee: dict(sources[0])

    # (1) FRESH IDENTITY: the result is its own object, not any source
    for d in sources:
        assert result is not d, (
            "freshness violated: dict(%r) returned an existing source object"
            % (sources[0],))

    # (2) EQUAL CONTENTS: result == first source's pre-state contents
    assert dict(result) == pre_contents[0], (
        "contents mismatch: result=%r expected=%r"
        % (dict(result), pre_contents[0]))

    # (3) SOURCE FRAME PINNED: mutating the result must not touch any source.
    # Pick a key guaranteed absent so the mutation is observable.
    sentinel = "__gax_sentinel__"
    while any(sentinel in d for d in sources) or sentinel in result:
        sentinel += "x"
    result[sentinel] = "MUTATED"
    for i, d in enumerate(sources):
        assert dict(d) == pre_contents[i], (
            "source frame violated: mutating the result changed source[%d] "
            "(%r -> %r)" % (i, pre_contents[i], dict(d)))


def check_prepatch_is_buggy(sources):
    """Confirm the pre-patch op VIOLATES freshness/frame (the bug is real)."""
    pre_first = dict(sources[0])
    result = prepatch_combine_first(sources)
    # the returned object IS the first source (alias), so the freshness clause
    # `result ∉ sources` is false ...
    assert result is sources[0], "expected pre-patch to alias the first source"
    # ... and mutating the result is visible through that source:
    sentinel = "__gax_sentinel__"
    while sentinel in result:
        sentinel += "x"
    result[sentinel] = "MUTATED"
    assert dict(sources[0]) != pre_first, (
        "pre-patch should have leaked the mutation into the first source")


def rand_dict(rng):
    keys = ["a", "b", "x", "y", "key", "", "a b", "0", "ünïcode", "long" * 5]
    vals = ["b", "c", "d", "0", "", "value", "•", "B" * 7]
    n = rng.randint(0, 5)
    return {rng.choice(keys): rng.choice(vals) for _ in range(n)}


def main():
    # --- boundary cases --------------------------------------------------
    boundary = [
        [{"a": "b"}, {"a": "c"}],          # the issue's MCVE (x=0 / x=1)
        [{"x": "0"}],                       # single source
        [{}],                               # empty first source
        [{}, {"a": "b"}],                   # empty first, non-empty rest
        [{"a": "b", "c": "d"}, {}],         # multi-entry first
        [{"k": "v"}] * 1,                   # one source
        [{"a": "1"}, {"a": "2"}, {"a": "3"}],
        [{"shared": "x"}],                  # contents that look mutable
    ]
    # aliased-input edge: same object appears twice in the list
    shared = {"a": "b"}
    boundary.append([shared, shared])

    for sources in boundary:
        check_gold([dict(d) for d in sources])          # fresh copies per trial
        check_prepatch_is_buggy([dict(d) for d in sources])

    # --- randomized fuzz -------------------------------------------------
    rng = random.Random(4629)
    N = 20000
    for _ in range(N):
        k = rng.randint(1, 4)                            # require non-empty
        sources = [rand_dict(rng) for _ in range(k)]
        check_gold(sources)
        # rebuild fresh (check_gold mutated the result, not the sources, but be
        # safe) for the buggy-direction check
        sources2 = [rand_dict(rng) for _ in range(rng.randint(1, 4))]
        check_prepatch_is_buggy(sources2)

    print("G-AX OK: deep fresh-copy model (== real dict(...) constructor) sound "
          "on %d boundary + %d fuzz inputs; fresh-identity, equal-contents, and "
          "source-frame obligations hold, and the pre-patch direct-return "
          "violates them (the observed bug)." % (len(boundary), N))
    return 0


if __name__ == "__main__":
    sys.exit(main())
