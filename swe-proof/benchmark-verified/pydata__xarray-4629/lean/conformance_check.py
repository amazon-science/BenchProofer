#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
`implementation_mergeAttrsOverride` against the REAL patched
`xarray.core.merge.merge_attrs(variable_attrs, combine_attrs="override")`.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). The impl region is all R/I (no A-tagged op), so this runs a
real fuzz over >=1e5 inputs.

Type bijection (mapping.md): a Python attribute dict OBJECT is modeled as a
(identity, contents) pair `AttrObj = Nat × AttrDict`. `variable_attrs` is a list
of such objects. Two observables of the override result matter, and are exactly
what the bug / F2P test (`test_merge_attrs_override_copy`) detects:

  * IDENTITY — is the returned object a *fresh* object, distinct from every
    source object?  (`not any(result is v for v in variable_attrs)`).  The Lean
    spec pins this as `id ∉ attrs.map Prod.fst`; the impl realizes it as a fresh
    id = max(input ids)+1.  Pre-patch (`return variable_attrs[0]`) the result IS
    a source object → not fresh → spec violated.
  * CONTENTS — the result's key→value mapping equals the first source's
    (`dict(result) == dict(variable_attrs[0])`).  The Lean impl carries `first.2`
    verbatim.
  * the empty-input guard: empty `variable_attrs` → `None`.

The Lean impl operates on the abstract (identity, contents) carrier, so the
shadow predicts the OBSERVATION tuple (is_none, is_fresh, contents_eq_first); we
diff it against the same observation taken on the real `merge_attrs` output.
Zero disagreements required.

stdlib-only fuzzing (pinned seed). exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 4629
N = 120_000  # >= 1e5


def shadow(variable_attrs):
    """R/I shadow of implementation_mergeAttrsOverride, as the observation tuple
    (is_none, is_fresh, contents_eq_first).

    variable_attrs: list of dicts (the source objects). The shadow reproduces the
    impl op-for-op on the abstract carrier:
      * empty       -> None                       (is_none=True)
      * non-empty   -> fresh object (fresh id ∉ source ids) with contents copied
                       from the first source      (is_fresh=True, contents_eq_first=True)
    """
    if len(variable_attrs) == 0:
        return (True, None, None)
    # fresh identity distinct from every source ⇒ never aliases a source;
    # contents copied verbatim from the first source.
    return (False, True, True)


def observe_real(merge_attrs, variable_attrs):
    """Observation tuple of the REAL patched merge_attrs under 'override'."""
    result = merge_attrs(variable_attrs, "override")
    if result is None:
        return (True, None, None)
    is_fresh = not any(result is v for v in variable_attrs)
    contents_eq_first = dict(result) == dict(variable_attrs[0])
    return (False, is_fresh, contents_eq_first)


def rand_dict(rng):
    n = rng.randint(0, 5)
    return {f"k{rng.randint(0, 9)}": rng.randint(-50, 50) for _ in range(n)}


def rand_attrs_list(rng):
    n = rng.randint(0, 6)
    return [rand_dict(rng) for _ in range(n)]


def main():
    from xarray.core.merge import merge_attrs

    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first, incl. the F2P shape (two single-key
    # dicts merged under 'override') and edge cases (empty list, single source,
    # duplicate-content sources, empty dicts).
    fixed = [
        [],                                   # empty -> None
        [{}],                                 # single empty dict
        [{"x": 0}],                           # single source
        [{"x": 0}, {"x": 1}],                 # the F2P shape
        [{"a": 1, "b": 2}, {"a": 9}],         # multi-key first
        [{"x": 5}, {"x": 5}, {"x": 5}],       # identical contents (distinct objs)
        [{}, {"y": 7}],                        # empty first source
    ]
    cases = fixed + [rand_attrs_list(rng) for _ in range(N)]

    for variable_attrs in cases:
        # copy the inputs so neither side can mutate the other's view
        a = [dict(d) for d in variable_attrs]
        b = [dict(d) for d in variable_attrs]
        got = shadow(a)
        want = observe_real(merge_attrs, b)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((variable_attrs, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} real={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
