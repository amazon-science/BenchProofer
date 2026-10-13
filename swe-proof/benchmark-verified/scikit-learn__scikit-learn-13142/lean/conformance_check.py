#!/usr/bin/env python3
"""G-CONF for scikit-learn__scikit-learn-13142.

Differential test of the R/I legs of `implementation_fit_predict` against the
behaviour of the GOLD-PATCHED `fit_predict` (patch.diff), over the abstracted
input domain declared in mapping.md.

Abstraction (mapping.md): the EM/selection loop of `fit_predict` reduces to a
sequence of trials `[(config, score), ...]`. The gold-patched code selects the
highest-scoring trial (strict `>` on `lower_bound`, so the EARLIEST trial
attaining the max wins ties) and returns the labels produced under that selected
config: `labelsOf(best_config)`. The pre-patch code instead returns labels under
the LAST trial's config.

`labelsOf` is the A-reference callee (deterministic function of a config); it is
left IDENTICAL on both legs (a fixed deterministic stub), exactly as G-CONF
requires for an A-tagged callee. Selecting the right config is the R/I content
under test.

- `shadow_impl`        : transliteration of Solution.lean `implementation_fit_predict`.
- `reference_patched`  : independent model of the gold-patched selection semantics.
They must agree on every fuzzed input. (As a guard we also assert the pre-patch
model `reference_prepatch` DISAGREES on at least one discriminating input, so the
test could actually catch the bug.)

stdlib-only; exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 13142          # pinned in mapping.md
N = 200_000


def labelsOf(config):
    # Fixed deterministic A-reference stub: a config maps to a reproducible label
    # vector. Identical on both legs.
    rng = random.Random("labelsOf:%d" % config)
    return [rng.randrange(0, 5) for _ in range(8)]


def shadow_impl(trials):
    # Mirrors implementation_fit_predict (Solution.lean): fold selecting best by
    # strict `>`, earliest-tie wins; return labelsOf of the selected config.
    best = None  # (config, score)
    for (config, score) in trials:
        if best is None:
            best = (config, score)
        elif score > best[1]:
            best = (config, score)
    if best is None:
        return []
    return labelsOf(best[0])


def reference_patched(trials):
    # Independent model of gold-patched fit_predict: pick best config then run
    # the final label computation under it.
    if not trials:
        return []
    max_lower_bound = None
    best_config = None
    for (config, score) in trials:
        if max_lower_bound is None or score > max_lower_bound:
            max_lower_bound = score
            best_config = config
    return labelsOf(best_config)        # final e-step AFTER _set_parameters(best)


def reference_prepatch(trials):
    # Pre-patch (buggy): final e-step runs BEFORE _set_parameters(best), i.e. on
    # the parameters left after the last trial.
    if not trials:
        return []
    max_lower_bound = None
    best_config = None
    for (config, score) in trials:
        if max_lower_bound is None or score > max_lower_bound:
            max_lower_bound = score
            best_config = config
    last_config = trials[-1][0]
    return labelsOf(last_config)


def gen(rng):
    n = rng.randint(1, 8)
    # small score range so ties + non-last maxima occur frequently
    return [(rng.randint(0, 10_000), rng.randint(0, 5)) for _ in range(n)]


def main():
    rng = random.Random(SEED)
    mismatches = 0
    bug_caught = False
    for _ in range(N):
        trials = gen(rng)
        a = shadow_impl(trials)
        b = reference_patched(trials)
        if a != b:
            mismatches += 1
            if mismatches <= 5:
                print(f"MISMATCH impl={a} patched={b} trials={trials}")
        if reference_patched(trials) != reference_prepatch(trials):
            bug_caught = True
    if mismatches:
        print(f"status=fail mismatches={mismatches}/{N}")
        sys.exit(1)
    if not bug_caught:
        print("status=fail discriminating-input-never-generated")
        sys.exit(1)
    print(f"status=pass checked={N} zero-disagreements (bug-discriminating inputs present)")
    sys.exit(0)


if __name__ == "__main__":
    main()
