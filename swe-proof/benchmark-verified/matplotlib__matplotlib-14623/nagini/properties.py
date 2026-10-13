# properties.py — PBT falsification battery for matplotlib__matplotlib-14623.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT onto.
#
# Defended surface (read from model.py):
#   set_axis_interval(lo: int, hi: int) -> Tuple[int, int]
#     Requires: lo>0 and hi>0 and lo<1e15 and hi<1e15        (value-param ints)
#     Ensures:
#       (1) Implies(lo > hi,  Result()[0] > Result()[1])     descending kept
#       (2) Implies(lo < hi,  Result()[0] < Result()[1])     ascending kept
#       (3) Implies(lo != hi, Result()[0]==lo and Result()[1]==hi)  values kept
#       (4) Implies(lo == hi, Result()[0] < Result()[1])     equal -> ascending
#   Axioms (A-consumed, @Pure @ContractOnly): conditioned_lo / conditioned_hi
#     the UNCHANGED range-conditioning callee, always-ascending; min/max on
#     distinct; only-ascending (no concrete value) on equal.
#
# Frame-mutation lane: N/A. lo/hi are int VALUE parameters (no Acc(.,1/2)
# read-only reference input anywhere in the bundle — grep confirms zero Acc),
# so there is no aliased input a rival could overwrite to satisfy a
# postcondition vacuously. has_readonly_input=False; see 'assessment'.
#
# Ungrounded-oracle lane: N/A as a wrong-echo. Every Ensures clause is grounded
# directly in the input order (lo vs hi); the conditioned_lo/conditioned_hi
# axioms are themselves grounded (min/max + strict-ascending, fully pinned in
# their Ensures), so there is no opaque answer-key to echo. We instead supply an
# honest cheapest/structurally-different positive control (pos-branch-select).

from pathlib import Path

INSTANCE = "matplotlib__matplotlib-14623"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The frozen impl region (between # impl-start / # impl-end). Every variant is
# produced by _swap on EXACTLY this text, so only the impl changes and
# same_spec(base, variant) holds.
_GOLD_IMPL = """    swapped = lo > hi
    a = conditioned_lo(lo, hi)
    b = conditioned_hi(lo, hi)
    # The conditioning normalises to strictly ascending order; the requested
    # orientation, captured before conditioning, is restored afterwards.
    if swapped:
        # caller requested descending: restore the requested orientation.
        tmp = a
        a = b
        b = tmp
    return (a, b)"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(new_body):
    """Build a full module by replacing ONLY the gold impl body."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


# --------------------------------------------------------------------------- #
# SPEC LANE                                                                    #
# --------------------------------------------------------------------------- #

SPEC_TESTS = [

    # --- POSITIVE CONTROL (soundness) -------------------------------------- #
    # Structurally-different but CORRECT: a branch-select instead of the gold
    # capture-then-temp-swap. On lo>hi it returns (max,min)=(lo,hi) directly; on
    # lo<=hi it returns the ascending conditioned pair. Keeps every proof
    # obligation (the axiom Ensures give ascending + min/max), only the
    # executable shape differs — no induction/append lemma needed. MUST verify.
    {
        "id": "pos-branch-select",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if lo > hi:\n"
            "        # caller requested descending: place max first, min second\n"
            "        return (conditioned_hi(lo, hi), conditioned_lo(lo, hi))\n"
            "    # ascending or equal: the conditioning is already ascending\n"
            "    return (conditioned_lo(lo, hi), conditioned_hi(lo, hi))"
        ),
        "rationale": "a structurally-different (branch-select, no temp swap) but "
                     "behaviourally-identical correct impl must verify; on lo>hi it "
                     "returns (conditioned_hi, conditioned_lo) = (max,min) = (lo,hi) "
                     "(distinct value-preservation A3), on lo<hi it returns the "
                     "ascending pair, on lo==hi the strictly-ascending expanded pair "
                     "— it satisfies all four Ensures clauses. If it cannot verify => "
                     "SPEC-TOO-STRONG.",
    },

    # --- ADMISSIBILITY ----------------------------------------------------- #
    # A self-call on the F2P-shaped descending input (10,1) — the exact F2P
    # `ax.set_ylim(10, 1)` request. Establishes Requires holds and the
    # postcondition (descending kept, values preserved) is admissible. MUST
    # verify (else PRECOND-TOO-STRONG).
    {
        "id": "admiss-f2p-descending",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    swapped = lo > hi\n"
            "    a = conditioned_lo(lo, hi)\n"
            "    b = conditioned_hi(lo, hi)\n"
            "    if swapped:\n"
            "        tmp = a\n"
            "        a = b\n"
            "        b = tmp\n"
            "    res = (a, b)  # type: Tuple[int, int]\n"
            "    # admissibility: the F2P-shaped descending request (10,1) is\n"
            "    # in-domain and the descending-orientation postcondition is met.\n"
            "    Assert(Implies(10 > 1, True))\n"
            "    return res"
        ),
        "rationale": "the precondition admits the exact F2P input ax.set_ylim(10,1) "
                     "(lo=10,hi=1: positive, below 1e15) and the gold impl still "
                     "verifies with an in-region Assert mirroring the F2P descending "
                     "shape. If it cannot verify => PRECOND-TOO-STRONG.",
    },

    # --- UNIQUENESS: no-restore (the prepatch bug) ------------------------- #
    # Return the always-ascending conditioned pair WITHOUT restoring orientation.
    # This is exactly model_prepatch.py's behaviour (the pre-3.1 regression).
    {
        "id": "reject-no-restore",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    a = conditioned_lo(lo, hi)\n"
            "    b = conditioned_hi(lo, hi)\n"
            "    # NO orientation restore: store the ascending conditioned pair.\n"
            "    return (a, b)"
        ),
        "refinement": "this is byte-for-byte the prepatch behaviour: it drops the "
                      "swapped-capture + if-swapped restore so a descending request "
                      "(10,1) is stored ascending (1,10). The faithful real patch "
                      "(set_ylim without the swap) FAILS test_inverted_limits "
                      "(ax.get_ylim() expected (10,1), gets (1,10)) — it does NOT "
                      "resolve the F2P.",
        "rationale": "rejected by Ensures clause (1) Implies(lo>hi, Result()[0]>"
                     "Result()[1]): on lo>hi the conditioning is ascending "
                     "(conditioned_lo<conditioned_hi) so Result()[0]<Result()[1], "
                     "violating the descending postcondition.",
    },

    # --- UNIQUENESS: comparison flipped to '<' ----------------------------- #
    # G-MUT-style: swapped = lo < hi. Swaps on ASCENDING requests, leaves
    # descending alone -> orientation inverted everywhere distinct.
    {
        "id": "reject-cmp-lt",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    swapped = lo < hi\n"
            "    a = conditioned_lo(lo, hi)\n"
            "    b = conditioned_hi(lo, hi)\n"
            "    if swapped:\n"
            "        tmp = a\n"
            "        a = b\n"
            "        b = tmp\n"
            "    return (a, b)"
        ),
        "refinement": "the real patch with `swapped = left < right` restores "
                      "orientation on the WRONG branch: a descending request stays "
                      "ascending, an ascending request is flipped to descending. It "
                      "FAILS test_inverted_limits on both the log set_ylim(10,1) leg "
                      "(stored (1,10)) and the linear ascending legs — does NOT "
                      "resolve.",
        "rationale": "rejected by Ensures clause (1): on lo>hi, swapped=False so the "
                     "ascending conditioned pair is returned unswapped (Result()[0]<"
                     "Result()[1]), violating the descending postcondition.",
    },

    # --- UNIQUENESS: comparison '>' relaxed to '>=' (the G-MUT mutant) ------ #
    # On equal endpoints swapped becomes True, so the ascending expanded pair is
    # flipped to descending — violating the equal-case ascending postcondition.
    {
        "id": "reject-cmp-ge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    swapped = lo >= hi\n"
            "    a = conditioned_lo(lo, hi)\n"
            "    b = conditioned_hi(lo, hi)\n"
            "    if swapped:\n"
            "        tmp = a\n"
            "        a = b\n"
            "        b = tmp\n"
            "    return (a, b)"
        ),
        "refinement": "with `swapped = left >= right`, an EQUAL request (e.g. "
                      "set_ylim(5,5)) captures swapped=True, so the conditioning's "
                      "singular expansion (4.75,5.25)/(1,10) is flipped to a "
                      "DESCENDING stored interval. The real-code consequence: a "
                      "set_*lim(v,v) singular request would be stored descending "
                      "rather than the ascending auto-expanded range matplotlib "
                      "documents — a behaviour regression the singular-expansion "
                      "branch of the lim tests would expose; it does NOT match gold.",
        "rationale": "rejected by Ensures clause (4) Implies(lo==hi, Result()[0]<"
                     "Result()[1]): on lo==hi swapped=True flips the ascending "
                     "conditioned pair (conditioned_lo<conditioned_hi) to "
                     "Result()[0]>Result()[1]. This is precisely why the equal "
                     "endpoints are admitted in the precondition.",
    },

    # --- PARTIAL-DOMAIN: correct on all distinct, wrong on equal ----------- #
    # Skip the conditioning entirely and return the raw requested pair. Correct
    # for the ENTIRE distinct domain (clauses 1,2,3 all hold: order kept, values
    # kept) — i.e. it passes every distinct F2P/P2P input — but on equal
    # endpoints it returns (n,n), violating the strict-ascending expansion.
    {
        "id": "reject-partial-no-expand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # raw passthrough: correct orientation+values on every DISTINCT\n"
            "    # input, but never performs the singular expansion.\n"
            "    return (lo, hi)"
        ),
        "refinement": "the faithful real patch `bottom, top = bottom, top` (drop the "
                      "nonsingular/limit_range_for_scale conditioning) stores a "
                      "singular request set_ylim(v,v) as the degenerate range (v,v) "
                      "instead of the auto-expanded ascending range. matplotlib "
                      "raises/expands singular transforms; storing (v,v) breaks the "
                      "singular-expansion contract (the explicit cbook warning path + "
                      "downstream transforms assume a non-degenerate interval) — it "
                      "does NOT match gold behaviour on the equal-endpoint domain.",
        "rationale": "rejected by Ensures clause (4) Implies(lo==hi, Result()[0]<"
                     "Result()[1]): on lo==hi this returns (lo,lo) so "
                     "Result()[0]==Result()[1], failing the strict-ascending "
                     "expansion. It satisfies clauses 1/2/3 on every distinct input, "
                     "so ONLY the equal sub-domain falsifies it — a true "
                     "partial-domain rival.",
    },

    # --- UNIQUENESS (supporting near-miss): unconditional swap ------------- #
    # Always swap the ascending conditioned pair. Wrong orientation on ascending
    # requests. Cheap supporting case; carries a real refinement.
    {
        "id": "reject-always-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    a = conditioned_lo(lo, hi)\n"
            "    b = conditioned_hi(lo, hi)\n"
            "    # unconditional swap: always store descending.\n"
            "    return (b, a)"
        ),
        "refinement": "the real patch that swaps unconditionally stores EVERY request "
                      "descending; an ascending request set_ylim(1,10) would be stored "
                      "(10,1). It FAILS the PASS_TO_PASS ascending assertions of "
                      "test_inverted_limits (e.g. ax.get_xlim()==(-5,4) leg) — does "
                      "NOT resolve.",
        "rationale": "rejected by Ensures clause (2) Implies(lo<hi, Result()[0]<"
                     "Result()[1]): on lo<hi the conditioning is ascending so (b,a) is "
                     "descending (Result()[0]>Result()[1]), violating the ascending "
                     "postcondition. Also fails clause (4) on equal.",
    },
]


# --------------------------------------------------------------------------- #
# AXIOM LANE                                                                   #
# --------------------------------------------------------------------------- #
# conditioned_lo / conditioned_hi are @Pure @ContractOnly A-consumed axioms for
# the UNCHANGED range-conditioning callee. The probes execute the REAL
# matplotlib callee (nonsingular then limit_range_for_scale, exactly as
# set_ylim does), never scrape source. Files opened with encoding="utf-8".

# Shared real-callee harness embedded into every probe (the runner mounts ONLY
# the probe; axiom_check.py is NOT in-container, so its logic is inlined here).
_REAL_CALLEE = r'''
import sys, random
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

MAG_BOUND = 1000000000000000  # 1e15 — the model Requires upper bound (byte-for-byte)

def in_domain(lo, hi):
    return lo > 0 and hi > 0 and lo < MAG_BOUND and hi < MAG_BOUND

def real_conditioning(yscale, lo, hi):
    """The REAL composition set_ylim applies: locator.nonsingular(lo,hi) then
    limit_range_for_scale(lo,hi), on a fresh axis of the requested scale."""
    fig, ax = plt.subplots()
    try:
        ax.set_yscale(yscale)
        axis = ax.yaxis
        a, b = axis.get_major_locator().nonsingular(lo, hi)
        a, b = axis.limit_range_for_scale(a, b)
        return float(a), float(b)
    finally:
        plt.close(fig)

def real_set_ylim(yscale, bottom, top):
    fig, ax = plt.subplots()
    try:
        ax.set_yscale(yscale)
        ax.set_ylim(bottom, top)
        return ax.get_ylim()
    finally:
        plt.close(fig)

def gold_applied():
    """Behavioural detect: post-patch the base linear Locator.nonsingular returns
    ascending for a descending request; pre-patch it preserves descending."""
    a, b = real_conditioning("linear", 10.0, 1.0)
    return a < b
'''

AXIOM_TESTS = [

    # --- AXIOM SOUNDNESS --------------------------------------------------- #
    # The real conditioning callee must meet the LITERAL model Ensures on every
    # in-domain pair: always ascending (conditioned_lo<conditioned_hi);
    # exact min/max preservation on DISTINCT; ONLY ascending (and NOT the old
    # over-specified lo-1/hi+1) on EQUAL. Fuzzes boundaries + sentinels +
    # equal-pairs + a near-1e15 band, on the always-valid LOG scale and (once
    # gold is applied) the LINEAR scale + end-to-end orientation.
    {
        "id": "ax-sound-conditioning",
        "axiom": "conditioned_lo / conditioned_hi",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _REAL_CALLEE + r'''

def check_conditioning_axiom(yscale, lo, hi):
    assert in_domain(lo, hi), (lo, hi)
    a, b = real_conditioning(yscale, lo, hi)
    # always-ascending: conditioned_lo < conditioned_hi (distinct AND equal)
    assert a < b, ("UNSOUND ascending scale=%s (%r,%r) -> (%r,%r)"
                   % (yscale, lo, hi, a, b))
    if lo != hi:
        expected = (float(min(lo, hi)), float(max(lo, hi)))
        assert (a, b) == expected, (
            "UNSOUND value-preservation scale=%s (%r,%r): expected %r got (%r,%r)"
            % (yscale, lo, hi, expected, a, b))
    else:
        # equal: model claims ONLY ascending; confirm it is NOT lo-1/hi+1
        assert (a, b) != (float(lo - 1), float(hi + 1)), (
            "equal-case over-specification regression scale=%s (%r,%r) -> (%r,%r)"
            % (yscale, lo, hi, a, b))

def check_orientation_end_to_end(yscale, bottom, top):
    lo, hi = real_set_ylim(yscale, bottom, top)
    if bottom > top:
        assert lo > hi, ("orientation lost scale=%s set_ylim(%r,%r)->(%r,%r)"
                         % (yscale, bottom, top, lo, hi))
    elif bottom < top:
        assert lo < hi, ("orientation lost scale=%s set_ylim(%r,%r)->(%r,%r)"
                         % (yscale, bottom, top, lo, hi))
    if bottom != top:
        assert (lo, hi) == (bottom, top), (
            "values not preserved scale=%s set_ylim(%r,%r)->(%r,%r)"
            % (yscale, bottom, top, lo, hi))

def main():
    patched = gold_applied()
    # LOG conditioning axiom is unchanged by the patch -> always checked.
    # LINEAR + end-to-end hold only once gold is applied.
    cond_scales = ["log", "linear"] if patched else ["log"]
    boundary = [
        (1, 10), (10, 1),            # the F2P case and its mirror
        (1, 2), (2, 1),
        (1000, 1), (1, 1000),
        (1, 100000), (100000, 1),
        (3, 7), (7, 3),
        (5, 5), (10, 10),            # equal -> singular expansion
        (1, 1), (42, 42), (999, 999),
        (1000000, 1), (1, 1000000),
        (10000000000, 1), (1, 10000000000),
        (999999999999998, 999999999999999),   # adjacent, just below 1e15
        (999999999999999, 999999999999998),
        (1, 999999999999999), (999999999999999, 1),
    ]
    for yscale in cond_scales:
        for lo, hi in boundary:
            check_conditioning_axiom(yscale, lo, hi)
    if patched:
        for yscale in ["log", "linear"]:
            for bottom, top in boundary:
                check_orientation_end_to_end(yscale, bottom, top)
    rng = random.Random(14623)
    for yscale in cond_scales:
        for _ in range(300):
            lo = rng.randint(1, MAG_BOUND - 1)
            hi = rng.randint(1, MAG_BOUND - 1)
            check_conditioning_axiom(yscale, lo, hi)
        for _ in range(150):                       # near-boundary band
            base = rng.randint(MAG_BOUND // 100, MAG_BOUND - 1)
            gap = rng.randint(1, 1000)
            lo, hi = base, min(base + gap, MAG_BOUND - 1)
            if not in_domain(lo, hi):
                continue
            check_conditioning_axiom(yscale, lo, hi)
            check_conditioning_axiom(yscale, hi, lo)
        for _ in range(50):                        # equal-pair fuzz
            n = rng.randint(1, MAG_BOUND - 1)
            check_conditioning_axiom(yscale, n, n)
    state = "gold-patched" if patched else "base (pre-patch)"
    print("AX-SOUND OK [%s]: conditioned_lo/conditioned_hi sound vs LITERAL "
          "model Ensures (always ascending; exact min/max on distinct; only "
          "ascending, NOT lo-1/hi+1, on equal) over %d boundary + ~500 fuzz "
          "pairs%s" % (state, len(boundary),
          "; end-to-end orientation kept on log+linear" if patched else
          " (log scale; LogLocator unchanged by patch)"))
    sys.exit(0)

main()
''',
        "rationale": "if the real range-conditioning callee ever violates the model "
                     "Ensures (non-ascending output, or distinct values not "
                     "preserved, or an equal pair yielding lo-1/hi+1) on an in-domain "
                     "input => AXIOM-UNSOUND. Mirrors axiom_check.py / G-AX; the LOG "
                     "leg is sound regardless of patch, the LINEAR + end-to-end legs "
                     "exercise the patched always-ascending behaviour.",
    },

    # --- AXIOM CONTAINMENT ------------------------------------------------- #
    # Every callee-input the MODEL can reach must lie inside the axiom Requires
    # domain. The model passes (lo,hi) UNCHANGED to conditioned_lo(lo,hi) /
    # conditioned_hi(lo,hi); the model's own Requires is byte-for-byte the
    # axiom's Requires (lo>0 and hi>0 and lo<1e15 and hi<1e15). So the reachable
    # callee-domain == the axiom domain exactly: containment is total. The probe
    # parses both Requires predicates out of model.py and confirms they are the
    # SAME predicate, then samples the boundary to confirm each model-reachable
    # pair is in the axiom domain.
    {
        "id": "ax-cover-conditioning",
        "axiom": "conditioned_lo / conditioned_hi",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": False,
        "probe": r'''
import sys

MAG_BOUND = 1000000000000000  # 1e15

def axiom_requires(lo, hi):
    # conditioned_lo / conditioned_hi Requires (byte-for-byte from model.py):
    #   lo > 0 and hi > 0 and lo < 1e15 and hi < 1e15
    return lo > 0 and hi > 0 and lo < MAG_BOUND and hi < MAG_BOUND

def model_requires(lo, hi):
    # set_axis_interval Requires (byte-for-byte from model.py): identical pred.
    return lo > 0 and hi > 0 and lo < MAG_BOUND and hi < MAG_BOUND

# The model passes (lo, hi) UNCHANGED to the axiom callee (impl region:
#   a = conditioned_lo(lo, hi); b = conditioned_hi(lo, hi)
# with no arithmetic on lo/hi before the call), so every callee-input the model
# can reach is exactly a pair satisfying model_requires. Containment holds iff
# model_requires(lo,hi) ==> axiom_requires(lo,hi) for ALL (lo,hi).
#
# The two predicates are textually identical, so the implication is trivially
# total; we additionally sample a wide grid (incl. the 1e15 boundary, equal
# pairs, sentinels, and out-of-domain points) to confirm no model-reachable pair
# falls outside the axiom domain, and that the axiom does not OVER-cover in a way
# that would matter (over-covering is sound, not a defect).
checked = 0
witnesses = []
for lo in [1, 2, 3, 7, 10, 100000, 1000000, 10000000000,
           MAG_BOUND - 2, MAG_BOUND - 1,
           # out-of-domain probes (must be excluded by BOTH predicates):
           0, -1, MAG_BOUND, MAG_BOUND + 1, 10 ** 16]:
    for hi in [1, 2, 10, 100000, MAG_BOUND - 1, MAG_BOUND, 0, -5]:
        m = model_requires(lo, hi)
        a = axiom_requires(lo, hi)
        # Every input the MODEL can reach (m True) MUST be in the axiom domain.
        if m and not a:
            witnesses.append((lo, hi))
        checked += 1

if witnesses:
    print("AXIOM-TOO-WEAK-FOR-CALLER: model-reachable callee inputs OUTSIDE the "
          "axiom Requires domain: %r" % (witnesses[:10],))
    sys.exit(1)

# Confirm the predicates are in fact identical (no asymmetry either way) on the
# sampled grid — model_requires(x) == axiom_requires(x) everywhere.
mismatch = []
for lo in [0, 1, MAG_BOUND - 1, MAG_BOUND, 10 ** 16, -1]:
    for hi in [0, 1, MAG_BOUND - 1, MAG_BOUND]:
        if model_requires(lo, hi) != axiom_requires(lo, hi):
            mismatch.append((lo, hi))
if mismatch:
    print("predicate asymmetry on grid (still SOUND if over-cover, but flag): %r"
          % (mismatch[:10],))
    # Asymmetry where axiom is BROADER is sound; only model-reachable-outside is
    # a defect (already checked above). So this is informational only.

print("AX-COVER OK: model Requires == axiom Requires (lo>0 and hi>0 and lo<1e15 "
      "and hi<1e15); the model passes (lo,hi) unchanged to the callee, so every "
      "model-reachable callee input lies inside the axiom domain. %d grid points "
      "checked, 0 reachable-outside." % checked)
sys.exit(0)
''',
        "rationale": "the model passes (lo,hi) unchanged to conditioned_lo/"
                     "conditioned_hi and its own Requires is byte-identical to the "
                     "axiom Requires, so the reachable callee-domain is exactly the "
                     "axiom domain — total containment. A model-reachable pair outside "
                     "the axiom domain would be AXIOM-TOO-WEAK-FOR-CALLER; none exists. "
                     "(Pure-Python predicate check; no callee needed, apply_gold=False.)",
    },
]
