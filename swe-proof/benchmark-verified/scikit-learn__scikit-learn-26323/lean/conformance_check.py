#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for scikit-learn__scikit-learn-26323.

The bundle models ONE behavior: the output-container propagation inside
`ColumnTransformer.set_output` (mapping.md). The chosen container `transform` is
applied to every contained transformer AND — the fix — to the fall-back
`remainder` transformer, unless that slot is one of the reserved sentinels
`"passthrough"`/`"drop"`.

Post-patch behavior (the gold edit):

    for trans in transformers:
        _safe_set_output(trans, transform=transform)
    if self.remainder not in {"passthrough", "drop"}:
        _safe_set_output(self.remainder, transform=transform)

Standing up the full sklearn estimator machinery is unnecessary: the modeled
value is the pure record-the-container operation over each slot. So the ORACLE
below is a faithful in-process replica of the POST-PATCH behavior, and the SHADOW
is the op-for-op transliteration of `implementation_setOutput` (Solution.lean impl
region), per refinement.md.

A transformer slot is represented as the string "passthrough"/"drop" for a
sentinel (Lean `Transformer.passthrough`/`.drop`) or as a dict
`{"id": int, "output": str}` for an estimator (Lean `Transformer.est id output`),
matching the mapping.md bijection. `_safe_set_output(est, transform)` records the
container: the estimator's `output` becomes `transform`; sentinels are untouched.

This genuinely tests the soundness-critical clause: the returned remainder slot
must have its container set when it is an estimator (the F2P
`test_remainder_set_output`), not left at its prior value.

stdlib-only. Pinned seed: 26323 (also in mapping.md).
"""
import random
import sys

SEED = 26323
N = 120_000

SENTINELS = ("passthrough", "drop")


def _set_output_slot(transform, slot):
    """Deep model of _safe_set_output on one slot (Lean `setOutput`)."""
    if isinstance(slot, dict):
        return {"id": slot["id"], "output": transform}
    return slot  # sentinel: unchanged


# --- ORACLE: faithful in-process replica of the POST-PATCH set_output ----------
def oracle(transformers, remainder, transform):
    out_transformers = [_set_output_slot(transform, t) for t in transformers]
    out_remainder = remainder
    if remainder not in SENTINELS:
        out_remainder = _set_output_slot(transform, remainder)
    return (out_transformers, out_remainder)


# --- SHADOW of implementation_setOutput (the R/I legs) -------------------------
# Mirrors Solution.lean impl region exactly:
#   for trans in transformers: out := out ++ [setOutput transform trans]
#   outRemainder := setOutput transform remainder
# (the real patch's sentinel guard is subsumed by setOutput being a no-op on a
# sentinel; the oracle keeps the guard, so this differential genuinely tests
# that the subsumption is sound)
def shadow(transformers, remainder, transform):
    out_transformers = []
    for trans in transformers:
        out_transformers = out_transformers + [_set_output_slot(transform, trans)]
    out_remainder = _set_output_slot(transform, remainder)
    return (out_transformers, out_remainder)


def disagree(transformers, remainder, transform):
    got = oracle(transformers, remainder, transform)
    want = shadow(transformers, remainder, transform)
    if got != want:
        return ((transformers, remainder, transform), got, want)
    return None


def _est(i, output):
    return {"id": i, "output": output}


def _edge_cases():
    cases = []
    # empty contained collection; estimator remainder (the bug's domain)
    cases.append(([], _est(0, "default"), "pandas"))
    # remainder = each sentinel (no-op on remainder)
    cases.append(([_est(1, "default")], "passthrough", "pandas"))
    cases.append(([_est(1, "default")], "drop", "pandas"))
    # remainder estimator whose container already equals transform
    cases.append(([_est(1, "pandas")], _est(2, "pandas"), "pandas"))
    # F2P configuration: one contained VarianceThreshold + VarianceThreshold remainder
    cases.append(([_est(10, "default")], _est(11, "default"), "pandas"))
    cases.append(([_est(10, "pandas")], _est(11, "pandas"), "default"))
    # mixed slots with sentinels interleaved
    cases.append(([_est(1, "default"), "passthrough", _est(2, "default"), "drop"],
                  _est(3, "default"), "pandas"))
    return cases


def _rand_slot(rng):
    r = rng.random()
    if r < 0.30:
        return rng.choice(SENTINELS)
    return _est(rng.randint(0, 9999), rng.choice(["default", "pandas"]))


def _rand_inputs(rng):
    n = rng.randint(0, 12)
    transformers = [_rand_slot(rng) for _ in range(n)]
    remainder = _rand_slot(rng)
    transform = rng.choice(["default", "pandas"])
    return transformers, remainder, transform


def main() -> int:
    checked = 0
    for transformers, remainder, transform in _edge_cases():
        d = disagree(transformers, remainder, transform)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} input={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        transformers, remainder, transform = _rand_inputs(rng)
        d = disagree(transformers, remainder, transform)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} input={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
