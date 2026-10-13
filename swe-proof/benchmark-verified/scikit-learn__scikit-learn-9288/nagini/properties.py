# properties.py — PBT manifest for scikit-learn__scikit-learn-9288.
#
# NOT a Nagini module: a record of adversarially-reasoned falsification cases.
# The runner (swebench_nagini.pbt) parses SPEC_TESTS / AXIOM_TESTS and stamps a
# RESULT. Spec cases are full model.py variants built by region-surgery (only the
# text inside # impl-start/# impl-end is edited — including the nested invariants,
# which the spec_view elides — so the frozen spec (axioms / pure seed_vector /
# pre- / post-conditions / signatures) is byte-identical and same_spec holds).
# Axiom cases are real-callee probes executed in the instance Docker image.
#
# ---------------------------------------------------------------- DEFENDED SURFACE
# Modeled function (model.py):
#   restart_seeds(config: int, n_restarts: int) -> List[int]
# Inputs: BOTH are plain pass-by-value `int` (an integer RNG configuration and a
# non-negative restart count). There is NO heap/reference input and NO Acc(x,1/2)
# read-only parameter, so the FRAME-MUTATION class does NOT apply (there is nothing
# on the heap an impl could overwrite to satisfy the postcondition vacuously) —
# see 'assessment'. The result list is freshly allocated; Acc(list_pred(Result()))
# is an OUTPUT permission, not an input frame to mutate. Requires is just
# `n_restarts >= 0`, so admissibility is near-trivial (a non-negative count).
#
# Load-bearing postcondition clauses (what an attacker must defeat):
#   (P1) Acc(list_pred(Result()))                 — owns the returned list
#   (P2) len(Result()) == n_restarts              — length pinned to the count
#   (P3) ToSeq(Result()) == seed_vector(source_state(config), n_restarts)
#        THE discriminating clause. seed_vector is the @Pure front-recursive
#        advancing draw fold
#            seed_vector(s,0)   = []
#            seed_vector(s,n)   = [draw(s)] + seed_vector(advance(s), n-1)
#        i.e. element k is draw(advance^k(source_state(config))). This is FULLY
#        GROUNDED in the inputs (it unfolds definitionally through the abstract
#        deterministic symbols source_state/advance/draw); it is NOT an opaque
#        answer-key oracle. The CHEAPEST honest impl is exactly to materialise this
#        fold (which is what the gold loop does with the prefix++rest invariant).
#        => There is no "wrong echo": echoing seed_vector IS the spec, so the
#        UNGROUNDED-ORACLE-ECHO class is N/A; instead we add an honest cheapest
#        positive control. The attacks below all perturb how the vector ADVANCES.
#
# ---------------------------------------------------------------- THE REAL CHANGE
# Gold patch (sklearn/cluster/k_means_.py): hoist
#   seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init)
# OUT of the multi-worker (else) branch to BEFORE the strategy split, and make the
# single-worker (n_jobs==1) branch loop `for seed in seeds: kmeans_single(...,
# random_state=seed)` instead of handing the one live `random_state` object to
# every restart. restart_seeds models the single-worker per-restart seed list; its
# postcondition pins it to the SAME up-front advancing draw vector the multi-worker
# branch consumes. The pre-patch bug (live object reused -> every restart sees the
# same first draw) is reject rival (1) below.
#
# F2P regression test (PR 9288):
#   test_result_of_kmeans_equal_in_diff_n_jobs:
#     X = RandomState(0).normal(size=(50,10))
#     assert_array_equal(KMeans(..., random_state=0, n_jobs=1).fit(X).labels_,
#                        KMeans(..., random_state=0, n_jobs=2).fit(X).labels_)
#   It resolves IFF both strategies consume the same per-restart seed vector, so
#   the argmin-of-inertia kept restart agrees. Each reject rival's refinement is
#   grounded in exactly that observable: a faithful real patch with that rival's
#   seeding would feed the single-worker restarts a DIFFERENT seed vector than the
#   multi-worker branch, so a restart explores a different clustering and the kept
#   labels_ can diverge between n_jobs=1 and n_jobs=2 — the F2P assertion fails.
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-9288"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The entire gold impl body (between the markers, invariants included). Editing
# only inside this block keeps the spec regions untouched, so every variant is
# same_spec with model.py. Kept byte-exact (it is the surgery anchor).
_GOLD_IMPL = """    start = source_state(config)
    cur = start
    result = []  # type: List[int]
    i = 0
    while i < n_restarts:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n_restarts)
        Invariant(len(result) == i)
        # "what is built ++ the draw vector of the rest == the whole vector":
        # `result` is the first i restart seeds and `cur` is the state the i-th
        # restart's seed is drawn at, so the draw vector of the remaining
        # n-i restarts from `cur` completes exactly the full vector.
        Invariant(ToSeq(result) + seed_vector(cur, n_restarts - i) ==
                  seed_vector(start, n_restarts))
        Invariant(MustTerminate(n_restarts - i + 1))
        # invariants-end
        # The remaining vector is non-empty (i < n_restarts), so it unfolds to
        # its head draw at `cur` followed by the vector from the advanced state
        # -- exactly the move performed below.
        Assert(seed_vector(cur, n_restarts - i) ==
               PSeq(draw(cur)) + seed_vector(advance(cur), n_restarts - i - 1))
        result = result + [draw(cur)]
        cur = advance(cur)
        i = i + 1
    return result"""

assert _GOLD_IMPL in _BASE, "gold impl block drifted from model.py"


# ------------------------------------------------------------------ POSITIVE
# (soundness) A structurally-DIFFERENT but CORRECT impl: LOCAL-VARIABLE RESHAPE.
# We keep the forward loop direction, every Invariant verbatim and the unfold
# Assert verbatim (the gold proof obligations, per AVOID #2/#3 — NO loop-direction
# flip against the front-recursive fold, NO dropped framing assert), and only
# reshape the executable mutation: hoist advance(cur) into a local `nxt` computed
# BEFORE the append, then assign `cur = nxt`. draw/advance are @Pure, so
# `draw(cur)` appended and `cur == nxt == advance(cur_old)` are identical to the
# gold step; the Assert sits before the mutation where `cur` is unchanged, so it
# still discharges. Must verify; if not, SPEC-TOO-STRONG.
_POS_RESHAPE = _swap(
    _GOLD_IMPL,
    "        result = result + [draw(cur)]\n"
    "        cur = advance(cur)\n"
    "        i = i + 1",
    "        nxt = advance(cur)\n"
    "        result = result + [draw(cur)]\n"
    "        cur = nxt\n"
    "        i = i + 1")

# (soundness, honest cheapest control) Since (P3) is grounded — the postcondition
# IS the seed_vector fold — the cheapest honest impl just rebuilds that fold by the
# same forward loop. This is essentially the gold body with an explicit local for
# the drawn value; included as the honest counterpart to the (N/A) ungrounded echo.
# Different shape (named `val`), same proof. Must verify.
_POS_NAMED_VAL = _swap(
    _GOLD_IMPL,
    "        result = result + [draw(cur)]\n"
    "        cur = advance(cur)\n"
    "        i = i + 1",
    "        val = draw(cur)\n"
    "        result = result + [val]\n"
    "        cur = advance(cur)\n"
    "        i = i + 1")

# ------------------------------------------------------------------ ADMISSIBILITY
# Requires is only `n_restarts >= 0`. A normal F2P-shaped count (n_init is a
# non-negative int) is admitted. We keep the gold proof and add a top-of-impl
# Assert that the precondition value is establishable (trivially in-domain). If
# this cannot verify, PRECOND-TOO-STRONG. (No new heap/loop obligation introduced.)
_ADMISS = _swap(
    _GOLD_IMPL,
    "    start = source_state(config)\n",
    "    # Admissibility: the Requires admits a normal F2P-shaped restart count\n"
    "    # (n_init is a non-negative int, e.g. 10); the precondition is establishable.\n"
    "    Assert(n_restarts >= 0)\n"
    "    start = source_state(config)\n")

# ------------------------------------------------------------------ REJECT rivals
# (1) PRE-PATCH BUG — live source reused across restarts (constant list). Every
# restart emits the SAME first draw draw(start); `cur` is never advanced. The
# result is [draw(start)] * n_restarts, a constant vector. This is exactly the
# pre-patch single-worker path (random_state=random_state handed to every restart,
# collapsing to the one shared draw) — model_prepatch's behaviour.
_ATK_CONSTANT = _swap(
    _GOLD_IMPL,
    "        result = result + [draw(cur)]\n"
    "        cur = advance(cur)\n"
    "        i = i + 1",
    "        # WRONG (pre-patch): reuse the one live source -> every restart sees\n"
    "        # the same first draw; the state is never advanced.\n"
    "        result = result + [draw(start)]\n"
    "        i = i + 1")

# (2) OFF-BY-ONE / SHIFT — advance the state BEFORE drawing, so restart 0 emits
# draw(advance(start)) instead of draw(start). The whole vector is shifted by one
# draw: result == seed_vector(advance(start), n) != seed_vector(start, n).
_ATK_SHIFT = _swap(
    _GOLD_IMPL,
    "        result = result + [draw(cur)]\n"
    "        cur = advance(cur)\n"
    "        i = i + 1",
    "        # WRONG: advance the state BEFORE reading the draw, shifting the whole\n"
    "        # vector by one (restart 0 gets draw(advance(start)), not draw(start)).\n"
    "        cur = advance(cur)\n"
    "        result = result + [draw(cur)]\n"
    "        i = i + 1")

# (3) PARTIAL-DOMAIN — last element wrong. Correct for restarts 0..n-2 (the
# advancing draws), but the FINAL restart is seeded from draw(start) instead of
# draw(advance^(n-1)(start)). Correct on the whole input domain EXCEPT the last
# position; diverges only when n_restarts >= 2 (and trivially correct for n<=1, so
# a length-class fuzzer that only tries n in {0,1} would miss it).
_ATK_LAST = _swap(
    _GOLD_IMPL,
    "        result = result + [draw(cur)]\n"
    "        cur = advance(cur)\n"
    "        i = i + 1",
    "        # WRONG (partial-domain): the last restart is seeded from draw(start)\n"
    "        # rather than the (n-1)-fold-advanced draw; correct elsewhere.\n"
    "        if i + 1 < n_restarts:\n"
    "            result = result + [draw(cur)]\n"
    "        else:\n"
    "            result = result + [draw(start)]\n"
    "        cur = advance(cur)\n"
    "        i = i + 1")

# (4) LENGTH SHORTFALL (cheap SUPPORTING near-miss, still carries a refinement) —
# drop the last restart entirely: loop while i < n_restarts - 1. Result has length
# n_restarts - 1 for n_restarts >= 1, violating (P2) len(Result()) == n_restarts
# (and (P3)). A supporting case, not a substitute for the reasoned attacks above.
_ATK_SHORT = _swap(
    _GOLD_IMPL,
    "    while i < n_restarts:",
    "    while i < n_restarts - 1:  # WRONG: drops the final restart (length short)")


SPEC_TESTS = [
    {
        "id": "pos-localvar-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_RESHAPE),
        "rationale": "structurally-different CORRECT impl (advance hoisted into a "
                     "local `nxt` before the append). Forward loop + every Invariant "
                     "+ the unfold Assert kept verbatim (no proof obligation dropped, "
                     "no loop-direction flip against the front-recursive fold), so it "
                     "must verify; if not, SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-cheapest-named-val",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_NAMED_VAL),
        "rationale": "honest cheapest control: (P3) is grounded — the postcondition "
                     "IS the seed_vector fold, so there is no wrong echo; rebuilding "
                     "the fold by the same forward loop (drawn value named `val`) is "
                     "the cheapest faithful impl. Must verify (soundness).",
    },
    {
        "id": "admiss-nonneg-count",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS),
        "rationale": "Requires is only n_restarts >= 0; a normal F2P-shaped restart "
                     "count (n_init, a non-negative int) is admitted. The added "
                     "Assert(n_restarts >= 0) is establishable from the precondition. "
                     "If this cannot verify, PRECOND-TOO-STRONG.",
    },
    {
        "id": "atk-constant-live-source",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ATK_CONSTANT),
        "refinement": "This is the PRE-PATCH bug: the single-worker branch hands the "
                      "one live random_state to every restart, so each restart's "
                      "effective seed collapses to the one shared first draw "
                      "(constant vector). The multi-worker branch consumes the "
                      "advancing randint(int32.max, size=n_init) vector. The faithful "
                      "real patch with this seeding feeds the two strategies DIFFERENT "
                      "per-restart seeds, so the argmin-of-inertia kept restart can "
                      "differ between n_jobs=1 and n_jobs=2 — "
                      "test_result_of_kmeans_equal_in_diff_n_jobs's "
                      "assert_array_equal(labels_) fails: NOT resolved.",
        "rationale": "rejects on (P3): a constant ToSeq(Result()) = [draw(start)]*n "
                      "cannot equal the advancing seed_vector(source_state(config), n) "
                      "= [draw(start), draw(advance(start)), ...] for the abstract "
                      "draw/advance (no value claim lets the verifier collapse the "
                      "advanced states), so the postcondition is unprovable.",
    },
    {
        "id": "atk-shift-advance-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ATK_SHIFT),
        "refinement": "Advancing before drawing shifts the entire per-restart seed "
                      "vector by one draw (restart k gets draw(advance^(k+1)(start))). "
                      "A real patch consuming this shifted vector in the single-worker "
                      "branch (while the multi-worker branch still uses the un-shifted "
                      "randint(size=n_init) vector) feeds every restart a different "
                      "seed than the other strategy, so the kept labels_ diverge "
                      "between n_jobs=1 and n_jobs=2: NOT resolved.",
        "rationale": "rejects on (P3): ToSeq(Result()) == seed_vector(advance(start), "
                      "n) != seed_vector(source_state(config), n); the head element "
                      "alone is draw(advance(start)) vs draw(start), abstractly "
                      "distinct, so the postcondition cannot be discharged.",
    },
    {
        "id": "atk-partial-last-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ATK_LAST),
        "refinement": "Correct on restarts 0..n-2 but seeds the FINAL restart from "
                      "draw(start) instead of the (n-1)-fold-advanced draw. A faithful "
                      "real patch with the last restart mis-seeded would have the "
                      "single-worker branch explore a different final clustering than "
                      "the multi-worker branch; on any input where that last restart "
                      "wins the argmin, n_jobs=1 and n_jobs=2 keep different labels_ — "
                      "the F2P assert_array_equal fails: NOT resolved. (Trivially "
                      "correct for n_restarts <= 1, so a length-class fuzzer trying "
                      "only n in {0,1} would miss it — this is the partial-domain hole.)",
        "rationale": "rejects on (P3): the last element of ToSeq(Result()) is "
                      "draw(start) while seed_vector pins draw(advance^(n-1)(start)); "
                      "for n_restarts >= 2 these are abstractly distinct, so the "
                      "tail of the postcondition equality is unprovable.",
    },
    {
        "id": "atk-length-shortfall",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ATK_SHORT),
        "refinement": "Dropping the final restart yields only n_restarts-1 seeds. A "
                      "real patch producing one fewer per-restart seed than n_init "
                      "would run one fewer restart in the single-worker branch than "
                      "the multi-worker branch, so the two strategies do not even "
                      "explore the same set of restarts — the kept argmin can differ "
                      "and the F2P assert_array_equal fails: NOT resolved. (Cheap "
                      "SUPPORTING near-miss; still carries a real refinement.)",
        "rationale": "rejects on (P2): len(Result()) == n_restarts is violated "
                      "(length is n_restarts-1 for n_restarts >= 1), and "
                      "consequently (P3) cannot hold either.",
    },
]


# ------------------------------------------------------------------ AXIOM lane
# The bundle has NO @ContractOnly axioms with a claimed Ensures (meta.axioms == []).
# source_state / advance / draw are A-REFERENCE abstract pure symbols (empty
# Ensures): the proof consumes no callee contract, it only unfolds the deep model
# seed_vector definitionally. So there is no axiom-soundness "Ensures violation" to
# fuzz in the contract sense. What MUST hold for the A-reference deep model to be
# faithful is the DISCRIMINATING empirical fact the model relies on (validated by
# G-AX / axiom_check.py): the real up-front draw vector ADVANCES (its entries are
# position-dependent, NOT one shared source value repeated), the pre-patch
# live-object reuse genuinely diverges from it, and the end-to-end patched KMeans
# is n_jobs-invariant (the literal F2P observation). We run the REAL numpy RNG +
# real patched sklearn (never scrape source) in the instance image under the gold
# patch (apply_gold=True, since the end-to-end check observes patched KMeans).
#
# Read the bundle's G-AX oracle on the HOST at load time; the runner mounts ONLY
# the probe at /work, so axiom_check.py's source is embedded into the probe string.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")

# axiom-soundness probe: this IS axiom_check.py's main() — it EXECUTES the real
# RandomState/randint and the real patched KMeans and asserts the three
# discriminating obligations (advancing vector; live-reuse divergence; n_jobs
# invariance). Reused verbatim (the G-AX ground truth).
_AX_SOUND_PROBE = _AXIOM_CHECK_SRC

# axiom-containment probe: the A-reference symbols have UNCONSTRAINED domains
# (source_state: int->int over any config; advance/draw: int->int over any state).
# The model reaches them only via: source_state(config) for the caller's int
# config, then advance applied 0..n_restarts-1 times, with draw read at each state
# (i.e. exactly the randint(int32.max, size=n_restarts) up-front vector). We
# confirm soundly against the REAL callee that the real source accepts every
# caller-reachable shape — any int config, and any non-negative restart count
# n_init (the loop length / size argument) including the boundaries 0 and 1 and a
# large count — without out-of-domain rejection. A reachable (config, n) the real
# randint could not produce would be AXIOM-TOO-WEAK-FOR-CALLER; none exists.
_AX_CONTAIN_PROBE = r'''#!/usr/bin/env python3
"""axiom-containment probe for scikit-learn__scikit-learn-9288.

The A-reference symbols source_state/advance/draw are abstract pure functions
with UNCONSTRAINED domains (int -> int). The model reaches them only as the
up-front draw vector: source_state(config) for the caller's int config, then draw
read at advance^k(state) for k = 0 .. n_restarts-1 — exactly
    np.random.RandomState(config).randint(np.iinfo(np.int32).max, size=n_restarts)
(the real callee, per mapping.md). This probe confirms soundly, against the REAL
numpy RNG, that every caller-reachable shape is in-domain: any int config (incl.
sentinels) and any non-negative restart count n (incl. the boundaries 0 and 1 and
a large count) produce a well-formed up-front draw vector of exactly that length,
with no out-of-domain rejection. No reachable (config, n) falls outside the real
callee's domain, so the unconstrained A-reference domain covers everything the
caller can reach. Exit 0 iff every probed shape yields a length-n int vector.
"""
import sys

import numpy as np
from sklearn.utils import check_random_state


def _upfront(config, n):
    rng = check_random_state(config)  # int branch -> RandomState(config)
    vec = rng.randint(np.iinfo(np.int32).max, size=n)
    return [int(s) for s in vec]


def main():
    # restart-count boundaries + length classes the caller can reach
    counts = [0, 1, 2, 3, 5, 10, 50]
    # int config sentinels + a sweep (the F2P uses random_state=0)
    configs = [0, 1, 2, 7, 42, 12345, 2 ** 16, 2 ** 31 - 1]
    for config in configs:
        for n in counts:
            try:
                vec = _upfront(config, n)
            except Exception as e:  # noqa: BLE001
                print("CONTAINMENT FAIL: real source rejected reachable shape "
                      "config=%r n=%r: %s: %s"
                      % (config, n, type(e).__name__, e))
                return 1
            if len(vec) != n:
                print("CONTAINMENT FAIL: up-front vector length %d != n=%d for "
                      "config=%r" % (len(vec), n, config))
                return 1
            if not all(isinstance(s, int) for s in vec):
                print("CONTAINMENT FAIL: non-int draw in vector for config=%r n=%r: "
                      "%r" % (config, n, vec))
                return 1
    print("CONTAINMENT OK: real RandomState(config).randint(int32.max, size=n) "
          "accepts every caller-reachable shape (%d configs x %d counts incl. "
          "0/1/large) and yields a length-n int vector; the unconstrained "
          "A-reference domain covers all reachable inputs."
          % (len(configs), len(counts)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-advancing-vector",
        "axiom": "seed_vector",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # the end-to-end obligation observes the PATCHED KMeans
        "probe": _AX_SOUND_PROBE,
        "rationale": "executes the real numpy RandomState/randint and the real "
                     "patched KMeans (G-AX ground truth, axiom_check.py): (A-ref 1) "
                     "the up-front randint(int32.max, size=n_init) vector ADVANCES "
                     "(distinct position-dependent entries) over 50 configs, so the "
                     "abstract draw/advance really move the seed; (A-ref 2) the bug's "
                     "live RandomState(config) reuse diverges from the fix's fresh "
                     "RandomState(seeds[0]) over 50 configs; (end-to-end) patched "
                     "KMeans labels_ are n_jobs-invariant (the literal F2P). If the "
                     "real callee contradicted the deep model's discriminating fact, "
                     "the A-reference would be UNSOUND.",
    },
    {
        "id": "ax-contain-upfront-shape",
        "axiom": "seed_vector",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "the A-reference symbols have unconstrained int domains and the "
                     "model reaches them only as the up-front draw vector "
                     "source_state(config) advanced 0..n_restarts-1 times == real "
                     "randint(int32.max, size=n_restarts). This confirms the real "
                     "source accepts every caller-reachable shape (any int config; "
                     "any non-negative count incl. 0/1/large) and returns a length-n "
                     "int vector, so no reachable input falls outside the domain. A "
                     "rejected reachable shape would be AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
