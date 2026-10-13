#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-26323
(nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant) stripped. The `Child` class and the @Pure
helper `is_configurable` copy over as a plain class / plain function. There
are no @ContractOnly callees in this bundle (no consumed axioms).

ORACLE: the REAL patched repo method the model models per mapping.md —
`sklearn.compose.ColumnTransformer.set_output` — called on an UNFITTED
composite (the modeled domain: only the explicitly-listed children plus the
leftover-columns handler are reachable). The gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed resolves the patched
package.

Type bridge (mapping.md section 2):
  * a model Child with kind==1 (configurable estimator)  <->  a fresh real
    transformer instance (drawn from a small pool of stateless transformers);
    kind==0 (routing sentinel)  <->  one of the two routing strings the
    composite treats as non-estimators.
  * the model's integer cfg  <->  the child's recorded output-container entry
    (the per-estimator record consulted by the output-config reader). cfg==0
    <-> no entry recorded (the unconfigured default every fresh instance
    starts in — the Requires cfg==0 domain); a nonzero code <-> the concrete
    container string requested, under the pinned code table
    {1: "pandas", 2: "default"}. A routing string carries no record, so it
    always reads back 0.
  * `requested != 0`  <->  a genuine container is requested (never the None
    no-op), exercised with both concrete container strings.
  * the model's `children` list  <->  the composite's explicitly-listed
    children in order; `leftover`  <->  the leftover-columns handler passed
    via the composite's dedicated keyword.

Input domain: every generated input satisfies the Requires — kinds in {0,1},
all children and the leftover start unconfigured (fresh objects), the
leftover is a distinct object from every listed child, requested != 0.

>= 1e5 Requires-satisfying inputs: exhaustive small-shape boundary
enumeration (every kind-vector for 0..4 children x 3 leftover choices x
2 container codes x sentinel-string choice) + 100000 fuzz trials.
Pinned fuzz seed: 26323.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the in-image sklearn only.
"""
import itertools
import json
import random
import sys

SEED = 26323
N_FUZZ = 100_000

# pinned bijection: model integer cfg code <-> concrete container string
CODE2STR = {1: "pandas", 2: "default"}
STR2CODE = {v: k for k, v in CODE2STR.items()}

SENTINEL_STRINGS = ("passthrough", "drop")


# --- the pure region of model.py, contracts stripped --------------------------

class Child:
    def __init__(self, kind, cfg):
        self.kind = kind  # 1 == configurable estimator, 0 == sentinel
        self.cfg = cfg    # configured output code; 0 == default/unset


def is_configurable(c):
    return c.kind == 1


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def configure_output(children, leftover, requested):
    i = 0
    while i < len(children):
        c = children[i]
        if is_configurable(c):
            c.cfg = requested
        i = i + 1
    if is_configurable(leftover):
        leftover.cfg = requested


# --- bridge: model kinds/codes <-> real composite children --------------------

def make_estimator_pool():
    """Fresh, cheap, stateless transformer instances. These all use the
    standard per-estimator output-container record the mapping's cfg
    observable is defined over (a transformer with a customized set_output
    that stores its choice elsewhere would need a different read-back, so the
    pool sticks to the standard-record ones)."""
    from sklearn.preprocessing import StandardScaler, Normalizer, MaxAbsScaler
    from sklearn.feature_selection import VarianceThreshold
    return (StandardScaler, Normalizer, MaxAbsScaler, VarianceThreshold)


def observed_code(child):
    """Read back the child's recorded output-container entry as a model code.
    A routing string has no record; an estimator without a record is at the
    unconfigured default (code 0)."""
    if isinstance(child, str):
        return 0
    rec = getattr(child, "_sklearn_output_config", None)
    if not rec or "transform" not in rec:
        return 0
    val = rec["transform"]
    if val not in STR2CODE:
        return -1  # outside the pinned code table: always a disagreement
    return STR2CODE[val]


def run_case(kinds, leftover_kind, requested, est_classes, sentinel_pick):
    """One Requires-satisfying input: build the real unfitted composite and
    the shadow objects, run both, and compare every observable.

    kinds: tuple of 0/1 for the explicitly-listed children (in order).
    leftover_kind: 0 or 1 for the leftover-columns handler.
    requested: model code in CODE2STR (nonzero).
    est_classes: per-position estimator class picks (cycled).
    sentinel_pick: per-position choice between the two routing strings.
    Returns an error string on disagreement, else None.
    """
    from sklearn.compose import ColumnTransformer

    # real children (fresh objects: the cfg==0 / distinctness Requires holds)
    real_children = []
    for pos, kind in enumerate(kinds):
        if kind == 1:
            real_children.append(est_classes[pos % len(est_classes)]())
        else:
            real_children.append(SENTINEL_STRINGS[sentinel_pick[pos % len(sentinel_pick)]])
    if leftover_kind == 1:
        real_leftover = est_classes[len(kinds) % len(est_classes)]()
    else:
        real_leftover = SENTINEL_STRINGS[sentinel_pick[len(kinds) % len(sentinel_pick)]]

    # Requires: everything starts unconfigured
    for ch in real_children:
        assert observed_code(ch) == 0
    assert observed_code(real_leftover) == 0

    ct = ColumnTransformer(
        [("t%d" % k, tr, [k]) for k, tr in enumerate(real_children)],
        remainder=real_leftover,
    )
    ct.set_output(transform=CODE2STR[requested])  # REAL patched method

    real_codes = [observed_code(ch) for ch in real_children]
    real_leftover_code = observed_code(real_leftover)

    # shadow (distinct fresh objects; Requires holds by construction)
    shadow_children = [Child(kind, 0) for kind in kinds]
    shadow_leftover = Child(leftover_kind, 0)
    configure_output(shadow_children, shadow_leftover, requested)
    shadow_codes = [c.cfg for c in shadow_children]
    shadow_kinds = [c.kind for c in shadow_children]

    if (shadow_codes != real_codes
            or shadow_leftover.cfg != real_leftover_code
            or shadow_kinds != list(kinds)
            or shadow_leftover.kind != leftover_kind):
        return ("DISAGREEMENT\n"
                "  input: kinds=%r leftover_kind=%r requested=%r (%r)\n"
                "  real children=%r\n"
                "  shadow codes=%r leftover=%r\n"
                "  real   codes=%r leftover=%r"
                % (kinds, leftover_kind, requested, CODE2STR[requested],
                   real_children,
                   shadow_codes, shadow_leftover.cfg,
                   real_codes, real_leftover_code))
    return None


def boundary_cases():
    """Exhaustive small shapes: every kind-vector for 0..4 listed children,
    every leftover kind (covering both routing strings), both container codes,
    and both sentinel-string phase choices."""
    cases = []
    for n in range(0, 5):
        for kinds in itertools.product((0, 1), repeat=n):
            for leftover_kind in (0, 1):
                for requested in CODE2STR:
                    for phase in ((0, 1), (1, 0)):
                        cases.append((kinds, leftover_kind, requested, phase))
    return cases


def main():
    pool = make_estimator_pool()
    rng = random.Random(SEED)
    checked = 0

    for kinds, leftover_kind, requested, phase in boundary_cases():
        err = run_case(kinds, leftover_kind, requested, pool, phase)
        if err:
            print(err)
            return 1
        checked += 1
    n_boundary = checked

    for _ in range(N_FUZZ):
        n = rng.randint(0, 5)
        kinds = tuple(rng.randint(0, 1) for _ in range(n))
        leftover_kind = rng.randint(0, 1)
        requested = rng.choice(list(CODE2STR))
        phase = tuple(rng.randint(0, 1) for _ in range(2))
        est_classes = tuple(rng.choice(pool) for _ in range(3))
        err = run_case(kinds, leftover_kind, requested, est_classes, phase)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real configuration propagation on %d "
          "inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
