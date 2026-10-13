#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for scikit-learn__scikit-learn-13779.

The bundle models ONE behavior: the per-sample-weight support-validation loop at
the top of `_BaseVoting.fit` (mapping.md). When weights are supplied, `fit` walks
its roster of `(name, estimator)` slots; an empty (`None`) slot is passed over
(the gold fix), and the first PRESENT estimator that does not accept per-sample
weights rejects the roster naming it.

Standing up sklearn / numpy / the full `fit` machinery to drive the real loop is
unnecessary: the modeled value is this pure walk over the roster. The estimator
object's only property the loop observes is the boolean
`has_fit_parameter(step, 'sample_weight')`, so a slot is projected to
`(name, None)` for an empty slot or `(name, accepts_bool)` for a present one
(mapping.md bijection). The ORACLE below is a faithful in-process replica of the
POST-PATCH loop, and the SHADOW is the op-for-op transliteration of
`implementation_checkWeightSupport` (Solution.lean impl region), per refinement.md.

The outcome is "OK" (loop falls through, `fit` proceeds) or ("ERR", name) (the
roster is rejected naming the offending estimator). This genuinely tests the
soundness-critical clause: a `None` slot must NOT reject (the F2P
`set_params(lr=None)` then `fit(..., sample_weight=...)` scenario), and the first
present non-supporting estimator must reject naming it.

stdlib-only. Pinned seed: 13779 (also in mapping.md).
"""
import random
import sys

SEED = 13779
N = 120_000


def _err(name):
    return "Underlying estimator '" + name + "' does not support sample weights."


# --- ORACLE: faithful in-process replica of the POST-PATCH loop ---------------
#   for name, step in self.estimators:
#       if step is None: continue
#       if not has_fit_parameter(step, 'sample_weight'):
#           raise ValueError(... % name)
# step projected to None (empty) or a bool (accepts weights).
def oracle(estimators):
    for name, step in estimators:
        if step is None:
            continue
        accepts = step  # bool = has_fit_parameter(step, 'sample_weight')
        if not accepts:
            return ("ERR", _err(name))
    return ("OK", None)


# --- SHADOW of implementation_checkWeightSupport (the R/I legs) ----------------
# Mirrors Solution.lean impl region exactly:
#   for slot in estimators: (name, step) := slot
#     match step: none => pure (); some accepts => if accepts then pure ()
#                                                   else return error (errMsg name)
#   return ok ()
def shadow(estimators):
    for slot in estimators:
        name, step = slot
        if step is None:
            pass
        else:
            accepts = step
            if accepts:
                pass
            else:
                return ("ERR", _err(name))
    return ("OK", None)


def disagree(estimators):
    got = oracle(estimators)
    want = shadow(estimators)
    if got != want:
        return (estimators, got, want)
    return None


def _edge_cases():
    cases = []
    # empty roster
    cases.append([])
    # F2P scenario: a None slot followed by an accepting estimator -> must be OK
    cases.append([("lr", None), ("rf", True)])
    cases.append([("lr", True), ("rf", True)])         # all present, all accept
    cases.append([("rf", True), ("lr", None)])         # None at the end
    cases.append([("lr", None), ("rf", None)])         # all None -> OK (loop falls through)
    cases.append([("lr", None)])                       # single None slot
    cases.append([("lr", False)])                      # single present non-supporting -> ERR lr
    # present non-supporting BEFORE a None slot -> ERR (rejects before reaching None)
    cases.append([("svc", False), ("lr", None)])
    # None BEFORE a non-supporting present -> ERR (skip None, then reject)
    cases.append([("lr", None), ("svc", False)])
    # accepting then non-supporting -> ERR names the second
    cases.append([("rf", True), ("svc", False), ("lr", True)])
    return cases


_NAMES = ["lr", "rf", "svc", "gnb", "knn", "mlp", "dt", "ada"]


def _rand_roster(rng):
    n = rng.randint(0, 8)
    roster = []
    for _ in range(n):
        name = rng.choice(_NAMES)
        kind = rng.randint(0, 2)  # 0 None, 1 accepts, 2 not-accepts
        if kind == 0:
            roster.append((name, None))
        elif kind == 1:
            roster.append((name, True))
        else:
            roster.append((name, False))
    return roster


def main() -> int:
    checked = 0
    for est in _edge_cases():
        d = disagree(est)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} estimators={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        est = _rand_roster(rng)
        d = disagree(est)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} estimators={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
