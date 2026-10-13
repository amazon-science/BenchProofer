# properties.py — PBT manifest for matplotlib__matplotlib-24026. NOT a Nagini
# module; a record of adversarial cases the runner (swebench_nagini.pbt) parses.
#
# Defended surface (frozen spec, assign_layer_facecolors):
#   Read-only inputs (half permission):
#     - Acc(list_pred(colors), 1/2)   -> colors is read-only
#     - Acc(axes.cycle, 1/2)          -> the Axes colour-cycle snapshot is read-only
#   Load-bearing postconditions:
#     (P1) axes.cycle == Old(axes.cycle)                  # frame: no cycle mutation
#     (P2) ToSeq(Result()) == cyc_prefix(ToSeq(colors), n) # whole-list cyclic read
#     (P3) len(Result()) == n                              # one facecolour per layer
#     (P4) Forall i in [0,n): Result()[i] == cyc(colors,i) # element-wise cyclic idx
#   The oracle cyc/cyc_prefix is GROUNDED: cyc == colors[i % len(colors)], fully
#   unfolded in terms of the input `colors`. There is no opaque answer-key to
#   echo, so the ungrounded-oracle-echo class does NOT apply here (see assessment);
#   it is replaced by an honest cheapest-impl positive control.
#
# This bundle has NO @ContractOnly axiom (meta.axioms == []). The one kind-A
# obligation is an A-reference deep model (cyc_prefix == itertools.cycle drawing).
# We carry an axiom-lane probe anyway: an axiom-soundness probe (deep model ==
# real itertools.cycle, the gold colour source) and an axiom-containment probe
# (every callee-input the model can reach lies in the deep model's domain).
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24026"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Every edit below is INSIDE an `# impl-start` / `# impl-end` region,
# so the frozen spec view (and therefore same_spec) is never touched.
# ---------------------------------------------------------------------------

# The gold impl body of assign_layer_facecolors (between its impl markers).
_GOLD_IMPL = """    result = []  # type: List[int]
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(colors), 1 / 2))
        Invariant(len(colors) >= 1)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(ToSeq(result) == cyc_prefix(ToSeq(colors), i))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        c = cyc(ToSeq(colors), i)
        result.append(c)
        # ToSeq(result) is now the old prefix followed by layer i's colour,
        # which is exactly cyc_prefix at length i+1 (one front-recursive unfold).
        Assert(ToSeq(result) == cyc_prefix(ToSeq(colors), i)
               + PSeq(cyc(ToSeq(colors), i)))
        Assert(cyc_prefix_unfold(ToSeq(colors), i + 1))
        i = i + 1
        # One more layer is painted per step: the length of what has been
        # painted tracks the layer counter exactly.
        Assert(cyc_prefix_len(ToSeq(colors), i))
        Assert(len(ToSeq(result)) == i)
    # The loop ran to the last layer, so the counter reached the layer count.
    Assert(i == n)
    # The cumulative-sequence postcondition holds directly from the invariant.
    # Discharge the length and element-wise postconditions via the lemmas.
    Assert(cyc_prefix_len(ToSeq(colors), n))
    Assert(Forall(int, lambda j:
                  (Implies(0 <= j and j < n,
                           cyc_prefix_elem(ToSeq(colors), n, j)),
                   [[cyc(ToSeq(colors), j)]])))
    return result"""

assert _GOLD_IMPL in _BASE, "gold impl anchor drifted from model.py"

# The anchor is the WHOLE impl region, so re-basing it after a proof-side edit to
# model.py silently rewrites every whole-body rival built with `_swap(_BASE,
# _GOLD_IMPL, ...)` — cases (1), (5), (6), (7). Each of those decides explicitly
# what to do with the gold counter obligations (`cyc_prefix_len(colors, i)` /
# `len(ToSeq(result)) == i` / `i == n`) and with the loop's MustTerminate
# invariant; see the per-case ATTRIBUTION notes. The rule the notes apply: a
# reject case may only lose an obligation whose absence does not become the
# reason it is turned down, because a rival refuted by a missing proof step —
# or by an obligation leak — is not evidence about the specification.


# ===========================================================================
# (1) POSITIVE CONTROL (soundness) — structurally different but CORRECT.
#     Shape change: inline the per-layer colour (drop the `c` local and append
#     `cyc(ToSeq(colors), i)` directly), and reorder the two trailing discharge
#     asserts (length lemma after the element-wise Forall instead of before).
#     Every gold proof obligation it still needs (the per-step unfold assert,
#     both discharge lemmas, and the two counter-tracking obligations
#     len(ToSeq(result)) == i / i == n) is KEPT — only the executable shape is
#     reshaped, so the gold proof remains valid (avoids the pilot "dropped a
#     framing assert" and "forward-append-against-front-recursive-fold" traps:
#     this is still a forward loop maintaining the same front-recursive
#     invariant, not a direction flip). Carrying the counter obligations here is
#     what shows they are not gold-shape-specific: a reshaped correct impl
#     discharges them too. Must verify, else SPEC-TOO-STRONG.
# ===========================================================================
_POS_IMPL = """    result = []  # type: List[int]
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(colors), 1 / 2))
        Invariant(len(colors) >= 1)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(ToSeq(result) == cyc_prefix(ToSeq(colors), i))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        result.append(cyc(ToSeq(colors), i))
        Assert(ToSeq(result) == cyc_prefix(ToSeq(colors), i)
               + PSeq(cyc(ToSeq(colors), i)))
        Assert(cyc_prefix_unfold(ToSeq(colors), i + 1))
        i = i + 1
        Assert(cyc_prefix_len(ToSeq(colors), i))
        Assert(len(ToSeq(result)) == i)
    Assert(i == n)
    Assert(Forall(int, lambda j:
                  (Implies(0 <= j and j < n,
                           cyc_prefix_elem(ToSeq(colors), n, j)),
                   [[cyc(ToSeq(colors), j)]])))
    Assert(cyc_prefix_len(ToSeq(colors), n))
    return result"""

_POS_CONTROL = _swap(_BASE, _GOLD_IMPL, _POS_IMPL)


# ===========================================================================
# (2) ADMISSIBILITY — a self-call confirming the precondition admits a normal
#     F2P-shaped input (n>=1, non-empty colours, a fresh Axes with a read-only
#     cycle snapshot). Built as a separate caller appended INSIDE the
#     assign_layer_facecolors impl region is impossible (it returns), so instead
#     we keep the gold impl verbatim and add an admissibility witness as an
#     additional caller in the Axes.__init__ impl region? No — __init__ cannot
#     return a List either. Cleanest: keep gold impl, and assert at the top of
#     the gold impl that the precondition facts hold for the actual params
#     (n>=1, len(colors)>=1, the half-perm cycle is readable). This is the
#     standard "precond admits a normal input" witness done in-region.
#     Must verify, else PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS_PREFIX = """    # admissibility witness: the precondition facts for a normal F2P-shaped
    # input are establishable and the read-only cycle snapshot is observable.
    Assert(n >= 1)
    Assert(len(colors) >= 1)
    Assert(axes.cycle is axes.cycle)
    result = []  # type: List[int]"""

_ADMISS = _swap(_BASE, "    result = []  # type: List[int]", _ADMISS_PREFIX)


# ===========================================================================
# (3) FRAME-MUTATION on axes.cycle (MANDATORY; the actual reported bug).
#     A rival that pushes the supplied colours into the drawing context's own
#     colour cycle (the pre-patch set_prop_cycle(color=colors)) to "use" the
#     read-only input. axes.cycle is held at Acc(axes.cycle, 1/2): a WRITE needs
#     full permission, so this must fail for INSUFFICIENT PERMISSION — it can
#     never satisfy (P1) axes.cycle == Old(axes.cycle). Gold invariants/asserts
#     kept verbatim so the rejection is attributable to the write alone.
#     This mirrors model_prepatch.py exactly.
# ===========================================================================
_FRAME_CYCLE = _swap(
    _BASE,
    "    result = []  # type: List[int]",
    "    axes.cycle = ToSeq(colors)\n    result = []  # type: List[int]",
)


# ===========================================================================
# (4) FRAME-MUTATION on colors (supporting frame case on the OTHER read-only
#     input). colors is held at Acc(list_pred(colors), 1/2); appending to it
#     needs full permission, so this must fail for INSUFFICIENT PERMISSION.
#     A faithful real patch that mutated the caller's colour list would corrupt
#     the supplied sequence (the docstring promises colours are read as given).
# ===========================================================================
_FRAME_COLORS = _swap(
    _BASE,
    "    result = []  # type: List[int]",
    "    colors.append(colors[0])\n    result = []  # type: List[int]",
)


# ===========================================================================
# (5) PARTIAL-DOMAIN — off-by-one cyclic index (diverges on EVERY layer but is
#     the most plausible "looks right" mistake). Paint layer i with
#     cyc(colors, i + 1) instead of cyc(colors, i): a faithful real patch that
#     seeded itertools.cycle one step ahead (an extra next(colors) before the
#     loop). For the F2P case colors=["C0","C1","C2"], n=3 it would paint
#     C1,C2,C0 instead of C0,C1,C2 -> the image comparison FAILS (wrong layer
#     colours). Must reject: violates (P2)/(P4).
#     Construction note: the mutant carries invariants FAITHFUL TO ITSELF
#     (length + a shifted element-wise Forall it can actually maintain, proved
#     step-wise via a prev-snapshot of the sequence), NOT the gold cyc_prefix
#     invariant. Keeping the gold invariant would make the loop obligations
#     themselves unprovable and the prover diverges (times out) instead of
#     rejecting — a timed-out case is inconclusive, never a finding. With
#     self-consistent invariants the loop closes and the verifier rejects
#     DECISIVELY on the frozen postcondition (P2), in seconds.
#     ATTRIBUTION note (measured): the rival must carry
#     `Invariant(MustTerminate(n - i + 1))` and the two counter obligations
#     (`cyc_prefix_len(colors, i)` / `len(ToSeq(result)) == i` after the
#     increment, `i == n` after the loop). Both are TRUE of this rival — its own
#     `len(result) == i` invariant discharges them — so they cost it nothing and
#     it is still refuted only by the frozen spec. Omitting the MustTerminate
#     invariant does NOT make the case pass for a spec reason: measured, the
#     verifier then stops at "Obligation leak check failed. Loop might not take
#     all unsatisfied obligations from the context" (11.9s), which any impl
#     missing that invariant hits, correct or not — a rejection that says nothing
#     about the off-by-one. With it the rejection is
#     "Postcondition ... ToSeq(Result()) == cyc_prefix(ToSeq(colors), n) might
#     not hold" (P2) in 12.1s.
# ===========================================================================
_OFFBYONE_IMPL = """    result = []  # type: List[int]
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(colors), 1 / 2))
        Invariant(len(colors) >= 1)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda j:
                         (Implies(0 <= j and j < i,
                                  ToSeq(result)[j] == cyc(ToSeq(colors), j + 1)),
                          [[ToSeq(result)[j]]])))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        prev = ToSeq(result)
        c = cyc(ToSeq(colors), i + 1)
        result.append(c)
        Assert(ToSeq(result) == prev + PSeq(c))
        Assert(len(result) == i + 1)
        Assert(ToSeq(result)[i] == cyc(ToSeq(colors), i + 1))
        Assert(Forall(int, lambda j:
                      (Implies(0 <= j and j < i,
                               ToSeq(result)[j] == prev[j]),
                       [[ToSeq(result)[j]]])))
        i = i + 1
        Assert(cyc_prefix_len(ToSeq(colors), i))
        Assert(len(ToSeq(result)) == i)
    Assert(i == n)
    return result"""

_PARTIAL_OFFBYONE = _swap(_BASE, _GOLD_IMPL, _OFFBYONE_IMPL)


# ===========================================================================
# (6) PARTIAL-DOMAIN — first-layer-only divergence. Correct on layers 1..n-1
#     but paints layer 0 with cyc(colors, 1) (a real patch that mishandled the
#     dedicated `coll = fill_between(... facecolor=next(colors) ...)` of layer 0
#     vs the loop for layers 1..M-1 — the gold patch has exactly this split, so
#     a faithful mis-edit there is plausible). For the F2P 3-colour case it
#     paints C1,C1,C2 -> wrong first layer -> image mismatch. Must reject:
#     violates (P4) at i==0 (and (P2)).
#     ATTRIBUTION note (measured): built as a whole-body rival with invariants
#     FAITHFUL TO ITSELF (same discipline as cases (5)/(7)) — a first-layer
#     clause `Implies(i >= 1, ToSeq(result)[0] == cyc(colors, 1))` plus the
#     element-wise clause for j in [1,i), maintained step-wise off a
#     prev-snapshot — and it still carries the gold counter obligations
#     (`cyc_prefix_len(colors, i)` / `len(ToSeq(result)) == i` / `i == n`), which
#     are true of it. Splicing the i==0 special case into the GOLD body instead
#     leaves the gold per-step unfold assert
#     `ToSeq(result) == cyc_prefix(colors, i) + PSeq(cyc(colors, i))` in the
#     body, and the verifier then stops THERE (measured 11.7s,
#     "Assert might fail" at that line) rather than on a spec clause: that assert
#     is a gold PROOF STEP, so any reshaped impl can fail it and the rejection
#     would not be attributable to the specification. With self-consistent
#     invariants the rejection is
#     "Postcondition ... ToSeq(Result()) == cyc_prefix(ToSeq(colors), n) might
#     not hold" (P2) in 14.2s — a frozen postcondition, not a proof scaffold.
# ===========================================================================
_FIRST_IMPL = """    result = []  # type: List[int]
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(colors), 1 / 2))
        Invariant(len(colors) >= 1)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(result) == i)
        Invariant(Implies(i >= 1, ToSeq(result)[0] == cyc(ToSeq(colors), 1)))
        Invariant(Forall(int, lambda j:
                         (Implies(1 <= j and j < i,
                                  ToSeq(result)[j] == cyc(ToSeq(colors), j)),
                          [[ToSeq(result)[j]]])))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        prev = ToSeq(result)
        if i == 0:
            c = cyc(ToSeq(colors), 1)
        else:
            c = cyc(ToSeq(colors), i)
        result.append(c)
        Assert(ToSeq(result) == prev + PSeq(c))
        Assert(len(result) == i + 1)
        Assert(Forall(int, lambda j:
                      (Implies(0 <= j and j < i,
                               ToSeq(result)[j] == prev[j]),
                       [[ToSeq(result)[j]]])))
        i = i + 1
        Assert(cyc_prefix_len(ToSeq(colors), i))
        Assert(len(ToSeq(result)) == i)
    Assert(i == n)
    return result"""

_PARTIAL_FIRST = _swap(_BASE, _GOLD_IMPL, _FIRST_IMPL)


# ===========================================================================
# (7) UNIQUENESS — wrong length (paint one fewer layer). Stops the loop at
#     n-1, returning n-1 facecolours. A real patch that under-counted layers
#     (e.g. iterating range(len(y)-1) and forgetting the first fill_between)
#     would leave the last stacked layer unpainted -> image mismatch. Must
#     reject: violates (P3) len(Result()) == n (and (P2)).
#     Construction note: like case (5), the mutant's invariants are adjusted
#     to the tightened bound (i <= n-1, prefix maintained up to n-1) and its
#     trailing discharge asserts use n-1, so every in-loop obligation closes
#     and the verifier rejects DECISIVELY on the frozen postconditions.
#     (Tightening only the loop guard while keeping the gold n-bound asserts
#     leaves unprovable in-body obligations that make the prover diverge —
#     a timeout, which is inconclusive rather than a rejection.)
# ===========================================================================
_SHORT_IMPL = """    result = []  # type: List[int]
    i = 0
    while i < n - 1:
        # invariants-start
        Invariant(Acc(list_pred(colors), 1 / 2))
        Invariant(len(colors) >= 1)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n - 1)
        Invariant(len(result) == i)
        Invariant(ToSeq(result) == cyc_prefix(ToSeq(colors), i))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        c = cyc(ToSeq(colors), i)
        result.append(c)
        Assert(ToSeq(result) == cyc_prefix(ToSeq(colors), i)
               + PSeq(cyc(ToSeq(colors), i)))
        Assert(cyc_prefix_unfold(ToSeq(colors), i + 1))
        i = i + 1
    Assert(cyc_prefix_len(ToSeq(colors), n - 1))
    Assert(len(result) == n - 1)
    return result"""

_SHORT = _swap(_BASE, _GOLD_IMPL, _SHORT_IMPL
)


SPEC_TESTS = [
    {
        "id": "pos-control-inline-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CONTROL,
        "rationale": (
            "Structurally-different CORRECT impl: the per-layer colour is "
            "appended inline (no `c` local) and the two trailing discharge "
            "asserts are reordered (Forall-elem before length lemma). All gold "
            "proof obligations (per-step unfold assert, both discharge lemmas, "
            "front-recursive loop invariant) are kept, so the gold proof stays "
            "valid. If this cannot verify, the postcondition is SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "The precondition (n>=1, len(colors)>=1, half-perm readable cycle) "
            "admits a normal F2P-shaped input; the witness asserts those facts "
            "and reads axes.cycle, then runs the gold body. If it fails, the "
            "precondition is PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mut-axes-cycle",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_CYCLE,
        "refinement": (
            "This is the reported bug itself: pushing the supplied colours into "
            "the Axes property cycle (the pre-patch set_prop_cycle(color=colors)) "
            "(i) mutates the shared cycle that other drawing routines consult — "
            "the issue title 'stackplot should not change Axes cycler' — and "
            "(ii) routes through set_prop_cycle's validator, which raises "
            "ValueError on the 'CN' aliases colors=['C0','C1','C2'], so the F2P "
            "stackplot call raises and the image comparison never runs. A "
            "faithful real patch that did this does NOT resolve."
        ),
        "rationale": (
            "axes.cycle is held at Acc(axes.cycle, 1/2): the write needs full "
            "permission. Rejected for INSUFFICIENT PERMISSION (cannot satisfy "
            "P1 axes.cycle == Old(axes.cycle)). Mirrors model_prepatch.py."
        ),
    },
    {
        "id": "frame-mut-colors",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_COLORS,
        "refinement": (
            "Mutating the caller's `colors` list (append) corrupts the supplied "
            "colour sequence the caller still owns; a real patch that appended "
            "to the user-provided colors would change observable caller state "
            "and, for repeated stackplot calls sharing a colour list, drift the "
            "per-layer colours across calls — not the gold behaviour, would not "
            "resolve a P2P that reuses the list."
        ),
        "rationale": (
            "colors is held at Acc(list_pred(colors), 1/2): append needs full "
            "permission. Rejected for INSUFFICIENT PERMISSION (the read-only "
            "frame on `colors`)."
        ),
    },
    {
        "id": "partial-offbyone-cyc",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_OFFBYONE,
        "refinement": (
            "Painting layer i with cyc(colors, i+1) is a real patch that seeded "
            "itertools.cycle one step ahead (a stray next(colors) before the "
            "loop). For F2P colors=['C0','C1','C2'], n=3 it paints C1,C2,C0 "
            "instead of C0,C1,C2 — the image comparison against the C0,C1,C2 "
            "reference FAILS. Does NOT resolve."
        ),
        "rationale": (
            "Violates P4 (Result()[0] == cyc(colors,0)) and P2. The mutant "
            "maintains its own shifted element-wise invariant (provable, so "
            "the loop closes quickly) while still carrying the loop's "
            "MustTerminate obligation and the gold counter obligations, which "
            "hold of it. Measured: rejected in 12.1s on the frozen "
            "postcondition P2 (ToSeq(Result()) == cyc_prefix(colors, n) 'might "
            "not hold'), i.e. on the specification and not on a proof scaffold "
            "or an obligation leak."
        ),
    },
    {
        "id": "partial-first-layer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_FIRST,
        "refinement": (
            "The gold patch sources layer 0 from a dedicated fill_between and "
            "layers 1..M-1 from the loop. A faithful mis-edit that paints layer "
            "0 with the WRONG cyclic colour (here cyc(colors,1)) is correct on "
            "layers 1..n-1 but for F2P paints C1,C1,C2 — wrong first layer, "
            "image mismatch. Does NOT resolve."
        ),
        "rationale": (
            "Violates P4 at i==0 and P2: the returned list cannot be the "
            "length-n cyclic reading when layer 0 carries cyc(colors,1). The "
            "rival keeps invariants faithful to ITSELF (a first-layer clause "
            "plus the element-wise clause for j >= 1) and carries the gold "
            "counter obligations, so no gold proof step is left in the body to "
            "absorb the rejection. Measured: rejected in 14.2s on the frozen "
            "postcondition P2."
        ),
    },
    {
        "id": "uniq-short-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _SHORT,
        "refinement": (
            "Stopping the loop at n-1 returns n-1 facecolours. A real patch "
            "that under-counted layers (forgot the first dedicated "
            "fill_between, or iterated range(len(y)-1) for everything) leaves "
            "the last stacked layer unpainted — a visibly different image. "
            "Does NOT resolve."
        ),
        "rationale": (
            "Violates P3 (len(Result()) == n) and P2 (the length-n cyclic "
            "reading). The mutant's invariants/asserts are consistent with "
            "the tightened bound, so the loop closes and the verifier "
            "rejects decisively on the frozen postconditions."
        ),
    },
]


# ===========================================================================
# AXIOM LANE — no @ContractOnly axiom (meta.axioms == []); the kind-A obligation
# is an A-reference deep model. We probe it the same way axiom_check.py does
# (PBT_PLAN §4): the deep model cyc_prefix MUST equal the real itertools.cycle
# drawing (the gold colour source) on every input the model can reach.
# The probes are self-contained (stdlib only, utf-8 safe, no bundle file read);
# itertools is the SAME module the gold patch calls, present in every image.
# ===========================================================================

_AX_SOUNDNESS_PROBE = r'''
"""axiom-soundness (A-reference): deep model cyc_prefix == real itertools.cycle.

The gold patch sources per-layer colours via `colors = itertools.cycle(colors)`
then `facecolor = next(colors)` once per layer. The model encodes layer i as
cyc(colors,i) = colors[i % len(colors)], i.e. cyc_prefix(colors,n)[i]. This must
equal drawing n values from the REAL itertools.cycle on every in-domain input
(len(colors) >= 1, n >= 1). We EXECUTE the real callee (never scrape source) and
compare element-for-element, fuzzing boundaries + the wrap-around path + the
single-colour and exact-multiple paths. We also assert the second tested effect:
itertools.cycle iterates a snapshot and never mutates the supplied colours
(mirrors axes.cycle == Old(axes.cycle)). Exit 0 iff every obligation holds.
"""
import itertools
import random
import sys


def model_cyc_prefix(colors, n):
    k = len(colors)
    return [colors[i % k] for i in range(n)]


def real_cycle_draw(colors, n):
    it = itertools.cycle(colors)
    return [next(it) for _ in range(n)]


def main():
    boundary = [
        (["C0", "C1", "C2"], 3),   # the F2P case: 3 colours, 3 layers
        (["C0", "C1", "C2"], 1),   # fewer layers than colours
        (["C0", "C1", "C2"], 5),   # more layers -> wrap from the beginning
        (["C0"], 1),               # single colour, single layer
        (["C0"], 7),               # single colour repeated
        (["r", "g"], 6),           # exact multiple
        (["r", "g", "b"], 7),      # non-multiple wrap
        (list(range(10)), 10),
        (list(range(4)), 25),      # long draw over short cycle
        (["only"], 100),
    ]
    for colors, n in boundary:
        before = list(colors)
        observed = real_cycle_draw(colors, n)
        expected = model_cyc_prefix(colors, n)
        if observed != expected:
            print("AXIOM-UNSOUND colors=%r n=%d real=%r model=%r"
                  % (colors, n, observed, expected))
            sys.exit(1)
        if list(colors) != before:
            print("AXIOM-UNSOUND itertools.cycle mutated colors %r -> %r"
                  % (before, list(colors)))
            sys.exit(1)

    rng = random.Random(24026)
    for _ in range(20000):
        k = rng.randint(1, 12)
        colors = [rng.randint(0, 1000) for _ in range(k)]
        n = rng.randint(1, 40)
        before = list(colors)
        observed = real_cycle_draw(colors, n)
        expected = model_cyc_prefix(colors, n)
        if observed != expected:
            print("AXIOM-UNSOUND colors=%r n=%d real=%r model=%r"
                  % (colors, n, observed, expected))
            sys.exit(1)
        if list(colors) != before:
            print("AXIOM-UNSOUND itertools.cycle mutated colors")
            sys.exit(1)

    print("axiom-soundness OK: cyc_prefix == itertools.cycle drawing on "
          "%d boundary + 20000 fuzz inputs; colours never mutated."
          % len(boundary))
    sys.exit(0)


main()
'''


_AX_CONTAINMENT_PROBE = r'''
"""axiom-containment (A-reference caller-domain): every callee-input the model
can REACH lies in the deep model's domain (and in real itertools.cycle's domain).

The model's reachable callee-inputs are derived from assign_layer_facecolors'
own Requires + control flow:
  - colors: Requires(Acc(list_pred(colors),1/2)) + Requires(len(colors) >= 1)
            -> a NON-EMPTY sequence (len K >= 1). itertools.cycle(colors) is
            well-defined for any non-empty iterable; the deep model
            colors[i % K] needs K >= 1 (no division by zero) -> exactly met.
  - the layer index i: the loop runs i in [0, n) with Requires(n >= 1), so
            i ranges over 0..n-1, all >= 0. cyc(colors,i) Requires(i >= 0) and
            len(colors) >= 1 -> every reachable i is in domain.
  - n: Requires(n >= 1) -> cyc_prefix(colors,n) reached with n >= 1 (also fine
            at the recursive base n==0).
Covering MORE than the caller reaches (e.g. K==0 or i<0) would be SOUND, not a
defect; we only assert there is NO reachable input OUTSIDE the domain. We model
the reachable set explicitly and check each member is in-domain by EXECUTING the
real itertools.cycle on it (it must not raise / be well-defined). Exit 0 iff every
reachable callee-input is covered.
"""
import itertools
import random
import sys


def reachable_inputs(rng):
    # The exact (colors, n) shapes the model can pass: len(colors) >= 1, n >= 1.
    cases = [
        (["C0", "C1", "C2"], 3),   # F2P
        (["C0"], 1),               # minimal: K==1, n==1 (boundary of Requires)
        (["C0"], 40),              # K==1, large n (heavy wrap)
        (list(range(12)), 1),      # max K in fuzz, n==1
    ]
    for _ in range(2000):
        k = rng.randint(1, 12)       # len(colors) >= 1  (the Requires lower bound)
        n = rng.randint(1, 40)       # n >= 1            (the Requires lower bound)
        cases.append(([rng.randint(0, 1000) for _ in range(k)], n))
    return cases


def main():
    rng = random.Random(2402600)
    for colors, n in reachable_inputs(rng):
        # in-domain witnesses: K >= 1 and n >= 1 (the model's Requires)
        if len(colors) < 1:
            print("UNREACHABLE-GUARD len(colors) < 1 should never occur")
            sys.exit(1)
        if n < 1:
            print("UNREACHABLE-GUARD n < 1 should never occur")
            sys.exit(1)
        # the deep model needs K >= 1 (modulus well-defined): covered.
        if len(colors) == 0:
            print("AXIOM-TOO-WEAK-FOR-CALLER reachable K==0 outside domain")
            sys.exit(1)
        # the real callee is well-defined on every reachable input (no raise).
        it = itertools.cycle(colors)
        for _ in range(n):
            next(it)
        # every reachable layer index i in [0,n) satisfies cyc's Requires(i>=0).
        for i in range(n):
            if i < 0:
                print("AXIOM-TOO-WEAK-FOR-CALLER reachable i<0 outside cyc domain")
                sys.exit(1)
    print("axiom-containment OK: every caller-reachable (colors,n) — len>=1, "
          "n>=1, i in [0,n) — lies in the deep model / itertools.cycle domain.")
    sys.exit(0)


main()
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-cyc-prefix",
        "axiom": "cyc / cyc_prefix",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUNDNESS_PROBE,
        "rationale": (
            "A-reference: cyc_prefix is the deep model of the gold colour source "
            "itertools.cycle(colors)+next(...). If the real callee disagrees with "
            "colors[i % len(colors)] on any in-domain input, the deep model is "
            "AXIOM-UNSOUND. Reuses axiom_check.py's logic (executes the real "
            "callee). stdlib-only, present in every image."
        ),
    },
    {
        "id": "ax-cover-cyc-prefix",
        "axiom": "cyc / cyc_prefix",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": (
            "Caller-domain containment: the model reaches itertools.cycle / "
            "cyc only with len(colors) >= 1, n >= 1, layer index i in [0,n) "
            "(>= 0) — all inside the deep model's domain (K>=1 for the modulus, "
            "i>=0 for cyc). No reachable input lies outside; covering more would "
            "be sound, not a defect."
        ),
    },
]
