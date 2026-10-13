#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-10844
(nagini backend).

Refutes (never proves) the refinement leg: does the MODEL in model.py agree with
the REAL patched repository function it claims to model?

SHADOW
------
`shadow_pair_similarity_index` below is the `# impl-start` / `# impl-end` region
of `nagini/model.py::pair_similarity_index` copied VERBATIM, with only the
contract calls removed (this region contains no Requires/Ensures/Invariant/
Assert/Fold/Unfold/Acc/MustTerminate inside the markers, so nothing but the
enclosing contracts had to be dropped; the comments and the statement structure
are byte-for-byte the model's). The `# pure-start` region is empty -- the model
declares no `@Pure` helpers -- and the impl region uses no `PSeq`/`ToSeq`
carriers, so no sequence shim is needed here.

The three `@ContractOnly` callees the region invokes have no body to copy, so
each is realized by the REAL numeric operation it axiomatizes (mapping.md
section 1 / section 3), exercising the axiom instead of assuming it:

  * `ratio(a, b, m)` -> real division `a / b`  (supervised.py:859, `tk / pk`,
    `tk / qk`)
  * `root(x, m)`     -> `numpy.sqrt`           (supervised.py:859, `np.sqrt`)
  * `mul(x, y)`      -> real multiplication `*`(supervised.py:859, the product
    of the two roots)

Each realization additionally asserts its own `Requires` at call time, so an
input that would use an axiom outside its domain is reported rather than
silently evaluated (that is how the model's overflow-freedom claim -- nothing
above `m` is ever handed to the root -- is actually executed here).

ORACLE
------
The REAL patched repo function, CALLED, not transliterated:
`sklearn.metrics.cluster.supervised.fowlkes_mallows_score`
(sklearn/metrics/cluster/supervised.py:852-859 at base_commit
97523985b39ecde369d83352d7c3baf403b60a22; mapping.md section 1). The gate
applies patch.diff to /testbed and sets PYTHONPATH before this script runs, so
the import resolves the PATCHED source -- verified in-container: the loaded
`fowlkes_mallows_score` ends in
`return np.sqrt(tk / pk) * np.sqrt(tk / qk) if tk != 0. else 0.`
over `contingency_matrix(...).astype(np.int64)`. The script re-reads that source
line at startup and refuses to run if the patch is not in effect, so a
patch-apply failure can never be reported as conformance.

TYPE BRIDGE (mapping.md section 2, inverted)
--------------------------------------------
The model works over the abstract carrier `(tk, pk, qk, m)` of interpreted
reals; the repo function's observable input is a pair of label arrays. Rather
than RE-DERIVING the three pair-counts (a reimplementation of the repo's own
`np.dot(c.data, c.data) - n_samples` lines would test the reimplementation),
the bridge OBSERVES the real function's own aggregates: a `sys.settrace` frame
hook scoped to `fowlkes_mallows_score.__code__` reads `tk`, `pk`, `qk` out of
the real frame at its return event. Those numpy integer scalars are mapped to
the model carrier by `float(...)` (exact: every count observed is asserted
below 2**53), and `m` is the maximum magnitude of the integer domain the fix
widens into -- `float(np.iinfo(np.int64).max)`, fixed by the repo, mapping.md
section 2. So the compared observable is:

    shadow(float(tk), float(pk), float(qk), INT64_MAX_F)  ==  real score

with EXACT float equality (the shadow performs literally the same three IEEE
operations in the same order as the patched line, so any tolerance would only
hide a real reassociation difference -- the pre-patch order is caught by exact
equality on ordinary inputs and by `nan` on the overflow workload).

INPUT DOMAIN AND COUNT
----------------------
Every generated input is checked against the model's `Requires`
(`m >= 1`, `tk >= 0`, `0 <= pk <= m`, `0 <= qk <= m`, `tk <= pk`, `tk <= qk`).
A real repo input that VIOLATED them would mean the model's precondition
excludes reachable behaviour, so such a case is reported as a disagreement, not
skipped. (None occurs: the marginals dominate the concordant count by the
counting identities of mapping.md section 2.)

  1. boundary catalogue: empty input, singleton, both branches of the impl
     (`tk == 0` and `tk != 0`), perfect agreement (index 1.0), relabelled
     perfect agreement, the exact F2P workload of
     test_int_overflow_mutual_info_fowlkes_mallows_score -- whose marginals
     satisfy `pk, qk <= m` while `pk * qk > m`, i.e. the large-count regime the
     specification is about -- plus scaled variants of it.
  2. EXHAUSTIVE enumeration of the label-pair space for every sample count
     n <= EXHAUSTIVE_N with labels in `range(n)` (66282 pairs): for these sizes
     the reachable input space is finite and is covered completely, which is
     stronger than sampling it.
  3. seeded fuzz over larger label arrays to carry the total past 1e5.

Pinned seed: SEED = 10844 (recorded in mapping.md, section "G-CONF").

NEGATIVE CONTROL
----------------
Before the real comparison the script proves it is CAPABLE of failing: the
pre-patch evaluation order (`tk / np.sqrt(pk * qk)` in the int64 domain) and
three other plausible-but-wrong tails are run against the oracle on the
boundary catalogue, and the script exits 1 if any of them fails to be caught.
A check that cannot refute anything is worse than no check.

Exit 0 iff zero disagreements. stdlib + numpy + the patched repo only.
"""
import inspect
import itertools
import json
import random
import sys
import warnings

import numpy as np

from sklearn.metrics.cluster.supervised import fowlkes_mallows_score

SEED = 10844
EXHAUSTIVE_N = 4          # exhaustive over all label pairs of size <= 4
N_FUZZ = 40_000           # fuzz draws; total checks = catalogue + 66282 + N_FUZZ
MAX_REPORTED = 5

# mapping.md section 2: `m` is the maximum representable magnitude of the
# integer domain the marginals are widened into (`.astype(np.int64)`).
INT64_MAX_F = float(np.iinfo(np.int64).max)
EXACT_FLOAT_INT = 2 ** 53


# --------------------------------------------------------------------------
# @ContractOnly callees -> the REAL numeric operations they axiomatize.
# Each asserts its own model Requires so an out-of-domain use is reported.
# --------------------------------------------------------------------------

class RequiresViolation(Exception):
    pass


def _req(cond, what):
    if not cond:
        raise RequiresViolation(what)


def ratio(a: float, b: float, m: float) -> float:
    """model.py `ratio` axiom -> real division a / b (supervised.py:859)."""
    _req(b > 0.0, "ratio: b > 0")
    _req(a >= 0.0, "ratio: a >= 0")
    _req(a <= b, "ratio: a <= b")
    _req(b <= m, "ratio: b <= m")
    return a / b


def root(x: float, m: float) -> float:
    """model.py `root` axiom -> numpy.sqrt (supervised.py:859)."""
    _req(x >= 0.0, "root: x >= 0")
    _req(x <= m, "root: x <= m (representability gate)")
    return float(np.sqrt(x))


def mul(x: float, y: float) -> float:
    """model.py `mul` axiom -> real multiplication x * y (supervised.py:859)."""
    _req(0.0 <= x <= 1.0, "mul: x in [0, 1]")
    _req(0.0 <= y <= 1.0, "mul: y in [0, 1]")
    return x * y


# --------------------------------------------------------------------------
# SHADOW: model.py impl region, verbatim (contracts stripped).
# --------------------------------------------------------------------------

def shadow_pair_similarity_index(tk: float, pk: float, qk: float,
                                 m: float) -> float:
    # impl-start
    if tk != 0.0:
        # Form the two unit-interval conditional ratios FIRST; each is
        # representable (<= 1 <= m), so neither operand fed to the root, nor the
        # final product, can overflow the domain. The cross product of the two
        # marginals is never formed. (A concordant pair forces both marginals
        # strictly positive, since each marginal dominates the concordant count.)
        r_p = ratio(tk, pk, m)
        r_q = ratio(tk, qk, m)
        result = mul(root(r_p, m), root(r_q, m))
    else:
        result = 0.0
    return result
    # impl-end


# --------------------------------------------------------------------------
# ORACLE: call the real patched fowlkes_mallows_score and observe its own
# aggregates (the type bridge) out of its frame.
# --------------------------------------------------------------------------

_TARGET_CODE = fowlkes_mallows_score.__code__
_captured = {}


def _trace_local(frame, event, arg):
    if event == "return":
        loc = frame.f_locals
        _captured["v"] = (loc.get("tk"), loc.get("pk"), loc.get("qk"))
    return _trace_local


def _trace_global(frame, event, arg):
    if event == "call" and frame.f_code is _TARGET_CODE:
        return _trace_local
    return None


def observe(labels_true, labels_pred):
    """Return (real score, (tk, pk, qk)) from ONE call of the real patched
    function -- the aggregates are the real frame's own values, never recomputed
    here."""
    _captured.clear()
    old = sys.gettrace()
    sys.settrace(_trace_global)
    try:
        score = fowlkes_mallows_score(labels_true, labels_pred)
    finally:
        sys.settrace(old)
    if "v" not in _captured:
        raise RuntimeError("bridge failed: could not observe tk/pk/qk in the "
                           "real fowlkes_mallows_score frame")
    return float(score), _captured["v"]


def check_patch_applied():
    src = inspect.getsource(fowlkes_mallows_score)
    need = ("np.sqrt(tk / pk) * np.sqrt(tk / qk)", "astype(np.int64)")
    missing = [s for s in need if s not in src]
    if missing:
        print("G-CONF ERROR: the imported fowlkes_mallows_score is not the "
              "patched version (missing %r); oracle invalid." % (missing,))
        print(json.dumps({"status": "error",
                          "reason": "gold patch not in effect"}))
        return False
    return True


# --------------------------------------------------------------------------
# Requires screen on the model carrier
# --------------------------------------------------------------------------

def requires_failure(tk, pk, qk, m):
    if not m >= 1.0:
        return "m >= 1.0"
    if not tk >= 0.0:
        return "tk >= 0.0"
    if not (pk >= 0.0 and pk <= m):
        return "0.0 <= pk <= m"
    if not (qk >= 0.0 and qk <= m):
        return "0.0 <= qk <= m"
    if not tk <= pk:
        return "tk <= pk"
    if not tk <= qk:
        return "tk <= qk"
    return None


# --------------------------------------------------------------------------
# Wrong tails: the negative control (must all be refuted)
# --------------------------------------------------------------------------

def wrong_prepatch(tk, pk, qk, m):
    """The pre-patch order: form the cross product first (supervised.py:859
    before patch.diff), in the int64 domain the fix widens into."""
    if tk != 0.0:
        prod = np.int64(pk) * np.int64(qk)
        return float(np.int64(tk) / np.sqrt(prod))
    return 0.0


def wrong_squared(tk, pk, qk, m):
    if tk != 0.0:
        return (tk / pk) * (tk / qk)
    return 0.0


def wrong_single_ratio(tk, pk, qk, m):
    if tk != 0.0:
        return float(np.sqrt(tk / pk))
    return 0.0


def wrong_zero_branch(tk, pk, qk, m):
    if tk != 0.0:
        return shadow_pair_similarity_index(tk, pk, qk, m)
    return 0.5


WRONG_TAILS = (("prepatch-cross-product-first", wrong_prepatch),
               ("no-square-roots", wrong_squared),
               ("single-ratio-drop-qk", wrong_single_ratio),
               ("zero-branch-nonzero", wrong_zero_branch))


# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------

def f2p_workload():
    """The exact labels of
    sklearn/metrics/cluster/tests/test_supervised.py::
    test_int_overflow_mutual_info_fowlkes_mallows_score (the F2P test)."""
    x = np.array([1] * (52632 + 2529) + [2] * (14660 + 793)
                 + [3] * (3271 + 204) + [4] * (814 + 39) + [5] * (316 + 20))
    y = np.array([0] * 52632 + [1] * 2529 + [0] * 14660 + [1] * 793
                 + [0] * 3271 + [1] * 204 + [0] * 814 + [1] * 39
                 + [0] * 316 + [1] * 20)
    return x, y


def scaled_overflow_workload(rep):
    """The F2P shape tiled `rep` times: same marginals-fit / cross-product-
    overflows regime, deeper into it."""
    x, y = f2p_workload()
    return np.tile(x, rep), np.tile(y, rep)


def boundary_catalogue():
    cat = [
        ("empty", np.array([], dtype=np.int64), np.array([], dtype=np.int64)),
        ("singleton", np.array([0]), np.array([0])),
        ("singleton-relabel", np.array([3]), np.array([7])),
        ("perfect", np.array([0, 0, 1, 1]), np.array([0, 0, 1, 1])),
        ("perfect-relabelled", np.array([0, 0, 1, 1]), np.array([1, 1, 0, 0])),
        ("tk-zero-split", np.array([0, 0, 0, 0]), np.array([0, 1, 2, 3])),
        ("tk-zero-other-side", np.array([0, 1, 2, 3]), np.array([0, 0, 0, 0])),
        ("all-one-cluster", np.array([0, 0, 0, 0]), np.array([0, 0, 0, 0])),
        ("all-distinct", np.array([0, 1, 2, 3]), np.array([0, 1, 2, 3])),
        ("partial", np.array([0, 0, 1, 1, 2, 2]), np.array([0, 1, 1, 2, 2, 0])),
        ("skew", np.array([0] * 9 + [1]), np.array([0] * 5 + [1] * 5)),
    ]
    x, y = f2p_workload()
    cat.append(("F2P-overflow-witness", x, y))
    for rep in (2, 3):
        sx, sy = scaled_overflow_workload(rep)
        cat.append(("F2P-scaled-x%d" % rep, sx, sy))
    return cat


def exhaustive_pairs(nmax):
    """All (labels_true, labels_pred) with n <= nmax samples and labels in
    range(n): the reachable input space at these sizes, enumerated in full."""
    for n in range(1, nmax + 1):
        for lt in itertools.product(range(n), repeat=n):
            for lp in itertools.product(range(n), repeat=n):
                yield np.array(lt), np.array(lp)


def fuzz_pairs(rng, count):
    for _ in range(count):
        n = rng.randint(2, 80)
        k_true = rng.randint(1, max(2, n // 2))
        k_pred = rng.randint(1, max(2, n // 2))
        lt = np.array([rng.randrange(k_true) for _ in range(n)])
        lp = np.array([rng.randrange(k_pred) for _ in range(n)])
        yield lt, lp


# --------------------------------------------------------------------------

def bridge(triple):
    """mapping.md section 2: each non-negative integer count -> the equal real.
    Exact for every count observed (asserted < 2**53)."""
    tk, pk, qk = (int(v) for v in triple)
    for v in (tk, pk, qk):
        if abs(v) >= EXACT_FLOAT_INT:
            raise RuntimeError("bridge inexact: count %d >= 2**53" % v)
    return float(tk), float(pk), float(qk)


def negative_control():
    """The check must be capable of refuting a wrong tail; report which
    boundary input catches each."""
    caught = {}
    for name, _tail in WRONG_TAILS:
        caught[name] = str("")
    for label, lt, lp in boundary_catalogue():
        score, triple = observe(lt, lp)
        tk, pk, qk = bridge(triple)
        for name, tail in WRONG_TAILS:
            if caught[name]:
                continue
            try:
                got = float(tail(tk, pk, qk, INT64_MAX_F))
            except Exception as exc:                     # noqa: BLE001
                caught[name] = "%s raised %s" % (label, type(exc).__name__)
                continue
            if got != score:
                caught[name] = "%s (%r != %r)" % (label, got, score)
    blind = [n for n, v in caught.items() if not v]
    return caught, blind


def main():
    if not check_patch_applied():
        return 1

    # the pre-patch negative control overflows int64 on purpose
    np.seterr(all="ignore")
    warnings.simplefilter("ignore")

    caught, blind = negative_control()
    if blind:
        print("G-CONF FAIL: negative control blind -- the check cannot refute "
              "%s, so a green verdict would certify nothing." % (blind,))
        print(json.dumps({"status": "fail", "reason": "negative control blind",
                          "blind": blind}))
        return 1
    for name, where in sorted(caught.items()):
        print("negative-control refuted %-30s at %s" % (name, where))

    catalogue = boundary_catalogue()
    n_exh = 0
    checked = 0
    branch_zero = 0
    branch_nonzero = 0
    overflow_regime = 0
    bad = []

    def check(label, lt, lp):
        nonlocal checked, branch_zero, branch_nonzero, overflow_regime
        score, triple = observe(lt, lp)
        tk, pk, qk = bridge(triple)
        why = requires_failure(tk, pk, qk, INT64_MAX_F)
        if why is not None:
            # A reachable repo input outside the model's Requires is a FINDING
            # about the model's precondition, not something to skip.
            bad.append((label, tk, pk, qk, "Requires violated: " + why, score))
            return
        try:
            got = shadow_pair_similarity_index(tk, pk, qk, INT64_MAX_F)
        except RequiresViolation as exc:
            bad.append((label, tk, pk, qk,
                        "axiom domain violated: %s" % exc, score))
            return
        checked += 1
        if tk == 0.0:
            branch_zero += 1
        else:
            branch_nonzero += 1
        if pk * qk > INT64_MAX_F:
            overflow_regime += 1
        if float(got) != score:
            bad.append((label, tk, pk, qk, got, score))

    for label, lt, lp in catalogue:
        check(label, lt, lp)
        if len(bad) >= MAX_REPORTED:
            break

    if not bad:
        for lt, lp in exhaustive_pairs(EXHAUSTIVE_N):
            check("exhaustive", lt, lp)
            n_exh += 1
            if len(bad) >= MAX_REPORTED:
                break

    if not bad:
        rng = random.Random(SEED)
        for lt, lp in fuzz_pairs(rng, N_FUZZ):
            check("fuzz", lt, lp)
            if len(bad) >= MAX_REPORTED:
                break

    if bad:
        print("G-CONF FAIL: %d disagreement(s) between the model impl region "
              "and the real patched fowlkes_mallows_score:" % len(bad))
        for label, tk, pk, qk, got, score in bad:
            print("  [%s] tk=%r pk=%r qk=%r m=%r -> shadow=%r oracle=%r"
                  % (label, tk, pk, qk, INT64_MAX_F, got, score))
        print(json.dumps({"status": "fail", "checked": checked,
                          "disagreements": len(bad), "seed": SEED}))
        return 1

    print("G-CONF OK: model.py impl region (verbatim, ratio/root/mul realized "
          "by the real /, np.sqrt, *) == real patched fowlkes_mallows_score "
          "exactly on %d Requires-satisfying inputs "
          "(%d boundary + %d exhaustive n<=%d + %d fuzz, seed=%d); "
          "branches tk==0: %d, tk!=0: %d; large-count regime (pk*qk > m): %d; "
          "0 disagreements."
          % (checked, len(catalogue), n_exh, EXHAUSTIVE_N, N_FUZZ,
             SEED, branch_zero, branch_nonzero, overflow_regime))
    print(json.dumps({"status": "pass", "checked": checked,
                      "disagreements": 0, "seed": SEED,
                      "exhaustive_n": EXHAUSTIVE_N,
                      "branch_tk_zero": branch_zero,
                      "branch_tk_nonzero": branch_nonzero,
                      "overflow_regime_inputs": overflow_regime,
                      "negative_control_refuted": sorted(caught),
                      "oracle": "sklearn.metrics.cluster.supervised."
                                "fowlkes_mallows_score (patched, called)",
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly callees call the real "
                                "numeric operations)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
