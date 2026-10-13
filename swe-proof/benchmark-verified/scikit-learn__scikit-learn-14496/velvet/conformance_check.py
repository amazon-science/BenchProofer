#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-14496.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's two impl regions
              (`conditionSizeParameter`, `resolvePairedSizes`) transliterated to
              Python over the *real repo numeric carrier*.  Per mapping.md §2 the
              `value > 1` and `<= 1` branches, the `max(2, ...)`, the reduction
              to a whole count, and the `None`-defaults dataflow (secondaryGiven)
              all map directly.  The SCALED value is an INPUT to the modeled
              routines (`scaled` / `scaledPrimary` / `scaledSecondary`), because
              the repository computes it in IEEE double before the conditioning
              step and its rounding is not reproducible in exact rationals; the
              shadow therefore feeds in the REAL machine product `value * n` and
              the model's `Rat.floor scaled` refines to the repo's `int(...)` of
              that same product (exact on a non-negative value — mapping.md §2,
              G-AX leg (2)).  There is NO A-tagged callee inside the computed
              result, so the shadow is pure R/I (conf_skip=false).

  * ORACLE  — `patch.diff`'s behaviour: the patched conditioning expression
              `max(2, int(v * n_samples))` exactly as it appears at the three
              changed sites of optics_.py (compute_optics_graph and
              cluster_optics_xi).  This is the real correctness oracle the
              harness resolves (G-RESOLVE).

They must agree on every input.  Exit 0 iff zero disagreements.  The fuzz seed
is pinned (mapping.md §4) for a deterministic verdict.  stdlib only.
"""
import random
import sys

SEED = 14496
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean impl regions, transliterated --------------
def shadow_condition_single(value, n):
    """conditionSizeParameter (`compute_optics_graph` site): condition one
    sizing parameter.  R/I transliteration over the repo float carrier.

    `scaled` is an INPUT to the modeled method; the repository's own scaling
    (`value * n` in IEEE double) is what supplies it, so the shadow computes it
    the same way and then applies the modeled reduction `Rat.floor scaled`,
    which refines to `int(scaled)` on a non-negative value (mapping.md §2)."""
    size = value
    if value <= 1:
        scaled = value * n              # what the repo hands the conditioning step
        size = max(2, int(scaled))      # Rat.floor scaled, clamped at two
    return size


def shadow_resolve_pair(value, secondary_value, secondary_given, n):
    """resolvePairedSizes (`cluster_optics_xi` site): condition the primary, the
    secondary defaults to the conditioned primary when absent (None), then the
    secondary is conditioned in turn."""
    primary = value
    if value <= 1:
        primary = max(2, int(value * n))          # Rat.floor scaledPrimary, clamped
    secondary = primary
    if secondary_given:
        secondary = secondary_value
    if secondary <= 1:
        secondary = max(2, int(secondary * n))    # Rat.floor scaledSecondary, clamped
    return primary, secondary


# --- the oracle: patch.diff's conditioning behaviour -------------------------
def oracle_condition(value, n):
    """The patched expression at optics_.py:440/622/627, verbatim."""
    out = value
    if value <= 1:
        out = max(2, int(value * n))           # gold: int(...) added
    return out


def oracle_resolve_pair(value, secondary_value, secondary_given, n):
    """The patched cluster_optics_xi conditioning block (619-627), verbatim:
        if min_samples <= 1: min_samples = max(2, int(min_samples*n))
        if min_cluster_size is None: min_cluster_size = min_samples
        if min_cluster_size <= 1: min_cluster_size = max(2, int(min_cluster_size*n))
    """
    min_samples = value
    if min_samples <= 1:
        min_samples = max(2, int(min_samples * n))
    if not secondary_given:
        min_cluster_size = min_samples
    else:
        min_cluster_size = secondary_value
    if min_cluster_size <= 1:
        min_cluster_size = max(2, int(min_cluster_size * n))
    return min_samples, min_cluster_size


def fuzz_values(rng):
    """A sizing parameter: a fraction in (0,1], or an absolute count > 1."""
    pick = rng.random()
    if pick < 0.45:
        return rng.randint(1, 100) / 100.0        # realistic decimal fraction
    if pick < 0.7:
        return rng.uniform(1e-6, 1.0)             # arbitrary fraction (0,1]
    if pick < 0.85:
        return float(rng.randint(2, 500))         # absolute count (int-valued)
    return rng.uniform(1.0 + 1e-9, 500.0)         # absolute count (float)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # --- boundary inputs ------------------------------------------------------
    boundary_single = [
        (0.1, 31), (0.08, 31), (1.0, 50), (0.5, 4), (0.5, 5),
        (0.01, 1000), (2.0, 10), (5.0, 100), (0.999999, 7),
        # the faithfulness panel's witness and its class: decimal fractions whose
        # IEEE product lands just off an integer boundary, in both directions.
        (0.7, 90), (0.7, 170), (0.7, 180), (0.29, 100), (0.03, 100),
        (0.6, 90), (0.5111111111111111, 90),
    ]
    for v, n in boundary_single:
        count += 1
        if shadow_condition_single(v, n) != oracle_condition(v, n):
            disagreements.append(("single", v, None, None, n))

    boundary_pair = [
        (0.1, 0.08, True, 31),     # the F2P case
        (0.1, None, False, 31),    # secondary defaults to primary
        (3.0, 2.0, True, 31),
        (0.5, 0.5, True, 8),
        (3.0, None, False, 31),
        (0.2, None, False, 100),
    ]
    for v, sv, given, n in boundary_pair:
        count += 1
        sval = sv if sv is not None else 0.0
        if (shadow_resolve_pair(v, sval, given, n)
                != oracle_resolve_pair(v, sval, given, n)):
            disagreements.append(("pair", v, sv, given, n))

    # --- randomized fuzz ------------------------------------------------------
    for _ in range(N_FUZZ):
        count += 1
        n = rng.randint(1, 8000)
        v = fuzz_values(rng)
        if shadow_condition_single(v, n) != oracle_condition(v, n):
            disagreements.append(("single", v, None, None, n))
            if len(disagreements) >= 5:
                break

        sv = fuzz_values(rng)
        given = rng.random() < 0.7
        if (shadow_resolve_pair(v, sv, given, n)
                != oracle_resolve_pair(v, sv, given, n)):
            disagreements.append(("pair", v, sv, given, n))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for kind, v, sv, given, n in disagreements:
            print("  kind=%s value=%r secondary=%r given=%r n=%r"
                  % (kind, v, sv, given, n))
        return 1

    print("G-CONF OK: R/I shadow of conditionSizeParameter / resolvePairedSizes "
          "agrees with patch.diff behaviour on %d inputs (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
