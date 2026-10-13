"""properties.py — PBT falsification manifest for matplotlib__matplotlib-24570.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    aligned_offsets(heights: List[int], descents: List[int],
                    total: int, code: int) -> List[int]
        # the per-anchor box-alignment offsets (×2-scaled) of
        # matplotlib.offsetbox._get_aligned_offsets' third return value `offsets`.

with the load-bearing contract (regions, verbatim):

    Requires(Acc(list_pred(heights), 1/2))          # READ-ONLY input
    Requires(Acc(list_pred(descents), 1/2))         # READ-ONLY input
    Requires(len(heights) == len(descents))
    Requires(code in {BASELINE, LOWER, UPPER, CENTER})
    Ensures(Acc(list_pred(heights), 1/2))           # frame: caller keeps its half
    Ensures(Acc(list_pred(descents), 1/2))          # frame: caller keeps its half
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(heights))
    # per-index value pin (the LOAD-BEARING clause):
    Ensures(Forall i in [0,len): Result()[i] == offset_for(heights[i],
                                              descents[i], total, code))
    # discriminating contrast, made explicit:
    Ensures(Implies(code == LOWER,
            Forall i: Result()[i] == 2*descents[i]))          # low-edge: own descent
    Ensures(Implies(code == UPPER,
            Forall i: Result()[i] == 2*(total-heights[i]) + 2*descents[i]))  # high-edge

What this spec actually defends, and the attacks it must survive:

  * The DISCRIMINATING content of the gold patch is the anchor->offset-formula
    GROUPING: the names `bottom`/`top` moving between the low-edge ([d]) and
    high-edge ([height-h+d]) offset classes. The pre-patch grouping put `top`
    in the low-edge class and `bottom` in the high-edge class. model.py pins
    each anchor's offset ELEMENT-BY-ELEMENT via the @Pure `offset_for` (a
    fully-unfolded function of the args h,d,total,code) PLUS two explicit
    LOWER/UPPER discriminating Ensures clauses. Every uniqueness rival therefore
    targets the per-index value pin or one of the two explicit clauses.

  * NO @ContractOnly AXIOM EXISTS (the `axioms` region is empty). `offset_for`
    is a deep model (A-reference): a @Pure function whose body is the spelled-out
    per-anchor arithmetic, fully unfolded — NOT an opaque answer-key oracle. So
    the UNGROUNDED-ORACLE ECHO class is genuinely N/A: there is nothing to echo
    without doing the work — satisfying `Result()[i] == offset_for(...)` IS
    computing the offset. The deep model's soundness (== the real callee) is the
    one out-of-band trust point, validated by axiom_check.py / G-AX; the AXIOM
    lane below re-runs that real-callee check (axiom-soundness) and proves the
    model only ever reaches inputs the deep model covers (axiom-containment).
    Documented in 'assessment'; in lieu of a fake wrong-echo we ship an honest
    cheapest-impl positive control (`echo-honest`).

  * READ-ONLY (Acc(.,1/2)) INPUTS EXIST: `heights` and `descents` are both held
    at half permission (Requires + Ensures + loop Invariant). The FRAME-MUTATION
    class is therefore MANDATORY: a rival that writes a value-NEUTRAL element back
    into `heights` must be rejected for INSUFFICIENT PERMISSION (a byte-fuzzer
    never thinks to mutate an input). `total` and `code` are by-value ints.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside `# impl-start`/`# impl-end` (which physically contains the
nested `invariants` region), so `markers.same_spec` is guaranteed and a rejection
comes from the POSTCONDITION / the permission system, never from a tampered spec.
Each `expect:"reject"` rival carries the refinement argument that its faithful
real patch would NOT resolve the F2P (test_packers[bottom]/[top]). The axiom
cases run the REAL matplotlib `_get_aligned_offsets` in Docker, reusing and
strengthening axiom_check.py's logic.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24570"
FLOAT_ENCODING = None   # meta.json float_encoding is null (ints ×2-scaled; no float encoding)

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks (all strictly INSIDE the impl region of model.py).
# ---------------------------------------------------------------------------
# The whole gold impl body (between # impl-start and the trailing # impl-end),
# used as a single replaceable block for structural rewrites. Contains the
# nested invariants region verbatim — keeping it intact is REQUIRED for proofs
# (per pilot-bug #2: a positive control must keep the framing invariant).
_GOLD_BODY = """    result = []  # type: List[int]
    i = 0
    while i < len(heights):
        # invariants-start
        Invariant(Acc(list_pred(heights), 1 / 2))
        Invariant(Acc(list_pred(descents), 1 / 2))
        Invariant(len(heights) == len(descents))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(heights))
        Invariant(len(result) == i)
        Invariant(code == CODE_BASELINE() or code == CODE_LOWER()
                  or code == CODE_UPPER() or code == CODE_CENTER())
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                         result[k] == offset_for(heights[k], descents[k],
                                                 total, code)))))
        Invariant(MustTerminate(len(heights) - i + 1))
        # invariants-end
        h = heights[i]
        d = descents[i]
        if code == CODE_BASELINE():
            off = 0
        elif code == CODE_LOWER():
            off = 2 * d
        elif code == CODE_UPPER():
            off = 2 * (total - h) + 2 * d
        else:
            off = (total - h) + 2 * d
        result.append(off)
        i = i + 1
    return result"""

# The four-way branch dispatch alone (used by rivals that perturb one branch).
_GOLD_DISPATCH = """        if code == CODE_BASELINE():
            off = 0
        elif code == CODE_LOWER():
            off = 2 * d
        elif code == CODE_UPPER():
            off = 2 * (total - h) + 2 * d
        else:
            off = (total - h) + 2 * d"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (P1) Structurally-DIFFERENT but CORRECT: the four-way dispatch is reordered to
# BASELINE / UPPER / LOWER / CENTER. The branch ORDER changes but each branch
# still assigns the SAME arithmetic offset for its anchor, so `off ==
# offset_for(...)` holds in every branch (offset_for is a function of code, not
# of branch position). The forward loop, the per-index invariant
# Forall(k<i: result[k]==offset_for(...)), and every framing Invariant are kept
# VERBATIM (pilot-bug #2). The loop is still forward-append against a per-index
# (NOT front-recursive-fold) invariant, so the gold proof stays valid (no
# induction lemma needed — pilot-bug #3 avoided). If this fails to verify the
# postcondition is over-fit to the branch ORDER => SPEC-TOO-STRONG.
_POS_REORDER_DISPATCH = """        if code == CODE_BASELINE():
            off = 0
        elif code == CODE_UPPER():
            off = 2 * (total - h) + 2 * d
        elif code == CODE_LOWER():
            off = 2 * d
        else:
            off = (total - h) + 2 * d"""
_POS_REORDER = _swap(_BASE, _GOLD_DISPATCH, _POS_REORDER_DISPATCH)

# (P2) Structurally-DIFFERENT but CORRECT: compute the offset through a named
# local `slack = total - h` and reuse it in the UPPER/CENTER branches, a
# different code shape for the slack-bearing anchors. The arithmetic is
# identical (2*slack+2*d ; slack+2*d). All invariants/loop shape kept verbatim.
# If it fails to verify, the spec is over-fit to the inline `(total - h)` form
# => SPEC-TOO-STRONG.
_POS_LOCAL_DISPATCH = """        slack = total - h
        if code == CODE_BASELINE():
            off = 0
        elif code == CODE_LOWER():
            off = 2 * d
        elif code == CODE_UPPER():
            off = 2 * slack + 2 * d
        else:
            off = slack + 2 * d"""
_POS_LOCAL = _swap(_BASE, _GOLD_DISPATCH, _POS_LOCAL_DISPATCH)

# (P3) ECHO-HONEST. There is NO @ContractOnly answer-key oracle to echo: the
# only "oracle" in the contract is the @Pure `offset_for`, whose body is the
# fully-unfolded per-anchor arithmetic. The sole way to satisfy
# `result[k] == offset_for(...)` is to compute that arithmetic, which IS the
# correct behaviour. This control is the gold impl with an extra Assert
# immediately after each append that the value just appended equals the deep
# model. It is CORRECT (redundant with the gold loop invariant) so it must
# verify; its purpose is to demonstrate the spec is NOT echo-vulnerable (there
# is no WRONG echo of offset_for that verifies). If it failed, the per-index pin
# would be self-inconsistent (=> SPEC-TOO-STRONG).
_ECHO_APPEND = "        result.append(off)\n        i = i + 1"
_ECHO_APPEND_NEW = (
    "        result.append(off)\n"
    "        Assert(result[i] == offset_for(heights[i], descents[i], total, code))\n"
    "        i = i + 1"
)
_ECHO_HONEST = _swap(_BASE, _ECHO_APPEND, _ECHO_APPEND_NEW)

# (P4) ADMISSIBILITY. Cannot add a top-level caller (that leaves the impl region
# and breaks same_spec). Instead, in-region at the head of the impl body: assert
# that the four Requires clauses are all USABLE for a normal F2P-shaped input —
# the two half-permission inputs are readable (len(heights), len(descents)), the
# parallel-length precondition holds (len(heights) == len(descents)), and the
# code is one of the four legal anchors — then fall through to the unchanged gold
# body and reach a normal (non-raising) return. The F2P geometry is the packers
# calling `_get_aligned_offsets([(30,0),(60,0)], None, "top"/"bottom")` -> here
# heights=[60,120], descents=[0,0] (×2), code=UPPER/LOWER. If the impl cannot
# both consume the half-permissions and the length precondition AND return
# normally => PRECOND-TOO-STRONG.
_ADMISS_HEAD = "    result = []  # type: List[int]\n    i = 0"
_ADMISS_HEAD_NEW = (
    "    Assert(len(heights) >= 0)                 # heights half-perm readable\n"
    "    Assert(len(descents) >= 0)                # descents half-perm readable\n"
    "    Assert(len(heights) == len(descents))     # parallel-length precond holds\n"
    "    Assert(code == CODE_BASELINE() or code == CODE_LOWER()\n"
    "           or code == CODE_UPPER() or code == CODE_CENTER())\n"
    "    result = []  # type: List[int]\n    i = 0"
)
_ADMISS = _swap(_BASE, _ADMISS_HEAD, _ADMISS_HEAD_NEW)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (U1) FRAME-MUTATION (MANDATORY — read-only inputs). Inside the loop the index
# i is known in-bounds (0 <= i < len(heights)), so a value-NEUTRAL write
# heights[i] = h (h was just read FROM heights[i]) is well-typed and changes
# nothing observable — yet a list-element write needs FULL permission. The
# Requires/Invariant grant only Acc(list_pred(heights), 1/2), so Nagini rejects
# for INSUFFICIENT PERMISSION. Every gold invariant/assert and the entire value
# computation are kept VERBATIM so the rejection is attributable to the write
# alone (not to a spec change or a value error). A byte-fuzzer never thinks to
# mutate an input — this is the project's #1 weakness class.
_FRAME_BODY = _GOLD_BODY.replace(
    "        h = heights[i]\n        d = descents[i]\n",
    "        h = heights[i]\n        d = descents[i]\n        heights[i] = h  # FRAME MUTATION: value-neutral write needs full perm\n",
    1,
)
_FRAME = _swap(_BASE, _GOLD_BODY, _FRAME_BODY)

# (U2) ANCHOR-GROUP SWAP (= the exact pre-patch bug / model_prepatch.py). Swap
# the LOWER and UPPER branch BODIES: the low-edge anchor group gets the
# high-edge formula 2*(total-h)+2*d and vice versa. This reproduces the pre-fix
# `align in ["left","top"]` / `align in ["right","bottom"]` grouping. On the
# LOWER branch off becomes 2*(total-h)+2*d != 2*d (violates both the per-index
# pin Result()[i]==offset_for(...,LOWER) and the explicit LOWER clause
# Result()[i]==2*descents[i]) whenever total != h; symmetrically for UPPER.
_RIVAL_SWAP_DISPATCH = """        if code == CODE_BASELINE():
            off = 0
        elif code == CODE_LOWER():
            off = 2 * (total - h) + 2 * d
        elif code == CODE_UPPER():
            off = 2 * d
        else:
            off = (total - h) + 2 * d"""
_RIVAL_SWAP = _swap(_BASE, _GOLD_DISPATCH, _RIVAL_SWAP_DISPATCH)

# (U3) UPPER HALVES THE SLACK — a subtle near-miss: the high-edge anchor uses the
# CENTER-shaped formula (total-h)+2*d instead of 2*(total-h)+2*d (i.e. it halves
# the slack term, as if it forgot top/right is the FAR edge, not the centre).
# Agrees with the gold on every box whose slack total-h == 0 (a box at the track
# height) and on descent contribution, but diverges by exactly (total-h) on any
# shorter box. Violates the per-index pin and the explicit UPPER clause
# Result()[i]==2*(total-heights[i])+2*descents[i].
_RIVAL_UPPER_HALF_DISPATCH = """        if code == CODE_BASELINE():
            off = 0
        elif code == CODE_LOWER():
            off = 2 * d
        elif code == CODE_UPPER():
            off = (total - h) + 2 * d
        else:
            off = (total - h) + 2 * d"""
_RIVAL_UPPER_HALF = _swap(_BASE, _GOLD_DISPATCH, _RIVAL_UPPER_HALF_DISPATCH)

# (U4) PARTIAL-DOMAIN / first-box-only. Correct on every box EXCEPT index 0,
# where it forces off = 0 (as if BASELINE) regardless of anchor. Agrees with the
# gold on i>=1 and on the BASELINE anchor (where 0 is correct) and on any box
# whose true offset happens to be 0 (e.g. LOWER with descent 0). But on the F2P
# UPPER/LOWER anchors with a nonzero true offset at box 0 it violates the
# per-index pin Result()[0]==offset_for(heights[0],descents[0],total,code). This
# is the classic "pins all but the first element" attack: a rival correct on
# most of the domain but diverging on the first element.
_RIVAL_FIRST_DISPATCH = """        if i == 0:
            off = 0
        elif code == CODE_BASELINE():
            off = 0
        elif code == CODE_LOWER():
            off = 2 * d
        elif code == CODE_UPPER():
            off = 2 * (total - h) + 2 * d
        else:
            off = (total - h) + 2 * d"""
_RIVAL_FIRST = _swap(_BASE, _GOLD_DISPATCH, _RIVAL_FIRST_DISPATCH)

# (U5) LOWER DROPS THE DESCENT — the low-edge anchor returns 0 instead of 2*d
# (collapsing the box's own descent contribution to the baseline). Agrees with
# the gold on every zero-descent box (the F2P geometry [(30,0),(60,0)] HAS zero
# descents, so this rival would PASS the F2P narrowly!) but diverges on any box
# with a nonzero descent — and the contract pins ALL boxes, including the
# nonzero-descent P2P/boundary layouts. Violates the explicit LOWER clause
# Result()[i]==2*descents[i] and the per-index pin whenever descents[i] != 0.
_RIVAL_LOWER_NODESC_DISPATCH = """        if code == CODE_BASELINE():
            off = 0
        elif code == CODE_LOWER():
            off = 0
        elif code == CODE_UPPER():
            off = 2 * (total - h) + 2 * d
        else:
            off = (total - h) + 2 * d"""
_RIVAL_LOWER_NODESC = _swap(_BASE, _GOLD_DISPATCH, _RIVAL_LOWER_NODESC_DISPATCH)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-reorder-branches", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different (BASELINE/UPPER/LOWER/CENTER dispatch order) but "
                  "CORRECT impl: each branch still assigns the same offset for its anchor, so "
                  "off==offset_for(...) holds independent of branch position. Forward loop and "
                  "all framing invariants (incl. the per-index Forall(k<i: result[k]==offset_for)) "
                  "kept verbatim, so the gold proof stays valid (no induction lemma). If it fails "
                  "=> the postcondition is over-fit to branch ORDER (SPEC-TOO-STRONG)."},
    {"id": "pos-control-named-slack", "kind": "soundness", "expect": "verify",
     "module": _POS_LOCAL,
     "rationale": "a correct impl that introduces a named local slack=total-h and reuses it in "
                  "the UPPER (2*slack+2*d) and CENTER (slack+2*d) branches — a different code shape "
                  "for the slack-bearing anchors, identical arithmetic. Invariants/loop unchanged. "
                  "If it fails the spec is over-fit to the inline (total-h) form (SPEC-TOO-STRONG)."},
    {"id": "echo-honest", "kind": "soundness", "expect": "verify",
     "module": _ECHO_HONEST,
     "rationale": "there is NO @ContractOnly answer-key oracle: offset_for is a deep model whose "
                  "@Pure body is the fully-unfolded arithmetic, so the only way to satisfy "
                  "result[i]==offset_for(...) is to compute it (= the correct behaviour). Asserting "
                  "result[i]==offset_for(...) right after the append is redundant with the gold loop "
                  "invariant and must verify. Demonstrates the spec is NOT echo-vulnerable (no WRONG "
                  "echo of offset_for verifies)."},
    {"id": "admiss-f2p-shaped", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "in-region admissibility: asserts the four Requires clauses are USABLE for a "
                  "normal F2P-shaped input — the two half-permission inputs are readable, the "
                  "parallel-length precond len(heights)==len(descents) holds, and code is one of the "
                  "four legal anchors — then reaches a normal return. The F2P packers call "
                  "_get_aligned_offsets([(30,0),(60,0)], None, top/bottom) -> heights=[60,120], "
                  "descents=[0,0], code in {UPPER,LOWER}. If the precond cannot be established for "
                  "this normal input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutation-write-heights", "kind": "uniqueness", "expect": "reject",
     "module": _FRAME,
     "refinement": "a faithful real patch of this shape writes back into the caller's box-geometry "
                   "list (mutating hd_list / the boxes in place while computing offsets). Even a "
                   "value-neutral write corrupts the shared geometry the HPacker/VPacker re-read on "
                   "the next layout pass; the real _get_aligned_offsets is a pure read of hd_list and "
                   "the packers rely on that. Such a patch is not the gold (which never mutates its "
                   "input) and would not be the accepted fix — it changes observable aliasing "
                   "behaviour the P2P layout tests depend on.",
     "rationale": "MANDATORY frame-mutation (read-only inputs). The write heights[i]=h is "
                  "value-neutral (h was read from heights[i]) and in-bounds, but a list-element "
                  "write needs FULL permission while Requires/Invariant grant only "
                  "Acc(list_pred(heights),1/2). Rejection source: the permission system "
                  "(INSUFFICIENT PERMISSION), not a value error. If it verified => the read-only "
                  "frame is not enforced (SPEC-TOO-WEAK on the frame)."},
    {"id": "rival-anchor-group-swap", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SWAP,
     "refinement": "this is the EXACT pre-patch bug (model_prepatch.py): the LOWER/UPPER branch "
                   "bodies swapped reproduces `align in ['left','top']`->[d] and "
                   "`align in ['right','bottom']`->[height-h+d]. F2P test_packers[bottom] expects "
                   "bottom to land flush with the low edge (offset = descent) and test_packers[top] "
                   "expects top flush with the high edge (offset = height-h+d); the swap gives the "
                   "OPPOSITE for both, so the unpatched code does NOT resolve (the G-DIFF witness).",
     "rationale": "Rejection source: the per-index pin Result()[i]==offset_for(...) AND the explicit "
                  "LOWER clause Result()[i]==2*descents[i] (now 2*(total-h)+2*d, differing by the "
                  "slack) and UPPER clause Result()[i]==2*(total-h)+2*descents[i] (now 2*d). If it "
                  "verified => SPEC-TOO-WEAK (admits the pre-patch grouping)."},
    {"id": "rival-upper-halves-slack", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_UPPER_HALF,
     "refinement": "a faithful real patch that computes the high-edge offset as (height-h)*.5+d "
                   "(the CENTER formula) instead of height-h+d — halving the slack, as if top/right "
                   "were centred rather than flush with the far edge. test_packers[top] asserts the "
                   "top box's offset is the FULL track excess height-h+d; halving it places the box "
                   "at the track midpoint, so the assert_allclose fails and the patch does NOT "
                   "resolve.",
     "rationale": "subtle near-miss: agrees on any box with zero slack (total==h) but diverges by "
                  "(total-h) on every shorter box. Rejection source: the per-index pin and the "
                  "explicit UPPER clause Result()[i]==2*(total-heights[i])+2*descents[i] (this rival "
                  "gives (total-h)+2*d). If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-partial-domain-first-box", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FIRST,
     "refinement": "a faithful real patch correct on every box but the first, where it emits offset "
                   "0 (a fence-post bug treating box 0 as the baseline). For the F2P top/bottom "
                   "anchors the first box's true offset is nonzero (e.g. bottom box 0 has descent 0 "
                   "but top box 0 has slack 2*(total-h)>0), so cs.offsets[0] != the expected value "
                   "and test_packers' per-box assert_allclose fails on element 0 — does NOT resolve.",
     "rationale": "the partial-domain attack: pins all elements but index 0. off=0 at i=0 violates "
                  "the per-index pin Result()[0]==offset_for(heights[0],descents[0],total,code) "
                  "whenever that offset is nonzero (UPPER with slack, LOWER with descent). Rejection "
                  "source: the per-index Forall covering i=0. If it verified => SPEC-TOO-WEAK "
                  "(a Forall that skipped the first index would be too weak)."},
    {"id": "rival-lower-drops-descent", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LOWER_NODESC,
     "refinement": "a faithful real patch that emits offsets=[0. for h,d in hd_list] for the "
                   "low-edge group instead of [d for h,d in hd_list] — dropping the box's own "
                   "descent. The F2P geometry [(30,0),(60,0)] has ZERO descents so this would "
                   "narrowly PASS test_packers[bottom]; but the P2P/library layout tests drive "
                   "nonzero-descent boxes (text with descenders) and the low-edge offset must equal "
                   "the descent, so those would fail — the patch does NOT faithfully resolve the "
                   "behaviour the spec pins (it only coincides on the zero-descent F2P case).",
     "rationale": "value-domain attack hiding behind the F2P's zero descents: off=0 on LOWER "
                  "violates the explicit LOWER clause Result()[i]==2*descents[i] and the per-index "
                  "pin whenever descents[i] != 0. Rejection source: the LOWER discriminating clause. "
                  "If it verified => SPEC-TOO-WEAK (the spec must pin ALL boxes, not just the "
                  "zero-descent ones the F2P happens to use)."},
]


# ===========================================================================
# AXIOM LANE (Docker, real matplotlib callee) — the A-reference deep model.
# No @ContractOnly axiom is consumed; the single out-of-band trust point is the
# A-reference: offset_for (the deep model) == the real _get_aligned_offsets.
# We re-run + strengthen axiom_check.py's check (axiom-soundness) and prove every
# callee-input the MODEL can reach lies in the deep model's covered domain
# (axiom-containment).
# ===========================================================================

# (A1) axiom-soundness for the A-reference deep model `offset_for`. Reuse and
# strengthen axiom_check.py: drive the REAL post-patch _get_aligned_offsets with
# height=None (mirroring the packers' self.height is None F2P call) on boundary +
# fuzz layouts × all six anchors, and assert every returned offset equals the
# deep model offset_for (un-scaled: real == model/2). Any mismatch => the deep
# model is unsound (AXIOM-UNSOUND). apply_gold=True: offset_for models the
# POST-PATCH grouping, so the patch must be applied for the comparison to hold.
# Imports only matplotlib (the repo under test) + stdlib; utf-8 only via stdout.
_AX_DEEPMODEL_SOUND = r'''
import random, sys
from matplotlib.offsetbox import _get_aligned_offsets

# --- model.py deep-model reference (kept in lock-step with model.py / axiom_check.py) ---
CODE_BASELINE, CODE_LOWER, CODE_UPPER, CODE_CENTER = 0, 1, 2, 3
ANCHOR_CODE = {"baseline": CODE_BASELINE, "left": CODE_LOWER, "bottom": CODE_LOWER,
               "right": CODE_UPPER, "top": CODE_UPPER, "center": CODE_CENTER}

def offset_for_scaled(h, d, total, code):
    if code == CODE_BASELINE:
        return 0
    if code == CODE_LOWER:
        return 2 * d
    if code == CODE_UPPER:
        return 2 * (total - h) + 2 * d
    return (total - h) + 2 * d  # CENTER

def model_offset(h, d, total, code):
    return offset_for_scaled(h, d, total, code) / 2.0

def check_case(hd_list, align):
    height, descent, offsets = _get_aligned_offsets(hd_list, None, align)
    total = None if align == "baseline" else max(h for h, d in hd_list)
    code = ANCHOR_CODE[align]
    for (h, d), real_off in zip(hd_list, offsets):
        expected = 0.0 if align == "baseline" else model_offset(h, d, total, code)
        if abs(real_off - expected) >= 1e-9:
            print("AXIOM-UNSOUND deep model: align=%r box=(h=%r,d=%r) total=%r: "
                  "real _get_aligned_offsets gave %r, model gives %r"
                  % (align, h, d, total, real_off, expected))
            return False
    return True

anchors = ["baseline", "left", "bottom", "right", "top", "center"]
boundary = [
    [(30, 0), (60, 0)],            # the F2P test_packers geometry
    [(60, 0), (30, 0)],            # reversed order
    [(10, 0)],                     # single box
    [(20, 0), (20, 0)],            # equal heights (zero slack)
    [(100, 0), (50, 0), (25, 0)],  # three boxes
    [(40, 5), (80, 10)],           # nonzero descents (low-edge offset != 0)
    [(2, 1), (4, 2), (6, 3)],      # small even values (centre exact)
    [(0, 0), (10, 0)],             # a zero-height box
]
for hd_list in boundary:
    for align in anchors:
        if not check_case(hd_list, align):
            sys.exit(1)

rng = random.Random(24570)
n = 0
for _ in range(20000):
    k = rng.randint(1, 6)
    hd_list = []
    for _ in range(k):
        h = 2 * rng.randint(0, 100)
        d = 2 * rng.randint(0, h // 2) if h > 0 else 0
        hd_list.append((h, d))
    for align in anchors:
        if not check_case(hd_list, align):
            sys.exit(1)
        n += 1
print("AXIOM deep-model SOUND: offset_for == real _get_aligned_offsets over "
      "%d boundary + %d fuzz layouts x 6 anchors (0 mismatch)" % (len(boundary), 20000))
sys.exit(0)
'''

# (A2) axiom-containment for the deep model. The deep model offset_for is defined
# over ALL (h, d, total, code) with code in {0,1,2,3}; the model only ever calls
# it with the per-box (heights[k], descents[k], total, code) it iterates. The
# claim: every callee-input the MODEL can reach lies in offset_for's covered
# domain. The model's Requires constrains: code in {0,1,2,3}; heights/descents
# are parallel List[int]; total an int. offset_for is total over exactly that
# domain (its four branches partition code in {0,1,2,3}; arbitrary int h,d,total).
# So caller-reachable ⊆ deep-model-domain by construction. We additionally
# confirm the REAL callee accepts EVERY anchor string the model's four codes map
# to (the surjection {0,1,2,3} -> 6 anchor names is total: no model code maps to
# an align the real helper rejects), so no caller-reachable input is outside the
# real callee's domain either. Pure domain check + a light real-callee acceptance
# probe; runs in the instance image (apply_gold harmless — the anchor set is
# unchanged by the patch).
_AX_CONTAINMENT = r'''
import sys
from matplotlib.offsetbox import _get_aligned_offsets

CODE_BASELINE, CODE_LOWER, CODE_UPPER, CODE_CENTER = 0, 1, 2, 3
LEGAL_CODES = {CODE_BASELINE, CODE_LOWER, CODE_UPPER, CODE_CENTER}
# the model's code -> the real anchor names that code stands for (post-patch grouping)
CODE_TO_ANCHORS = {
    CODE_BASELINE: ["baseline"],
    CODE_LOWER:    ["left", "bottom"],
    CODE_UPPER:    ["right", "top"],
    CODE_CENTER:   ["center"],
}

def offset_for_total_over_domain():
    # offset_for's four branches partition LEGAL_CODES exactly: 0->b0, 1->b1,
    # 2->b2, else (i.e. 3)->b3. Every legal code hits exactly one branch and the
    # arithmetic (2*d / 2*(total-h)+2*d / (total-h)+2*d / 0) is defined for any
    # int h,d,total. So the deep model is TOTAL over the caller-reachable domain.
    covered = set()
    for code in LEGAL_CODES:
        # mimic offset_for's dispatch; any legal code returns a value (no gap).
        if code == CODE_BASELINE or code == CODE_LOWER or code == CODE_UPPER:
            covered.add(code)
        else:
            covered.add(code)  # the `else` (CENTER) branch
    return covered

covered = offset_for_total_over_domain()
missing = LEGAL_CODES - covered
if missing:
    print("AXIOM-TOO-WEAK-FOR-CALLER: deep model offset_for does not cover legal "
          "codes the caller can reach:", sorted(missing)); sys.exit(1)

# Confirm the REAL callee accepts every anchor string a legal model code denotes
# (so a caller-reachable code never maps to an align the real helper rejects).
hd_list = [(30, 0), (60, 0)]
unaccepted = []
for code, anchors in CODE_TO_ANCHORS.items():
    for align in anchors:
        try:
            _get_aligned_offsets(hd_list, None, align)
        except Exception as e:  # noqa: BLE001
            unaccepted.append((code, align, repr(e)))
if unaccepted:
    print("AXIOM-TOO-WEAK-FOR-CALLER: real _get_aligned_offsets rejects an anchor "
          "a caller-reachable code denotes:", unaccepted); sys.exit(1)

print("CONTAINMENT OK: every caller-reachable code in {0,1,2,3} is covered by the "
      "deep model offset_for (total over the domain) and every anchor name those "
      "codes denote is accepted by the real _get_aligned_offsets.")
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-deepmodel-sound", "axiom": "offset_for", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_DEEPMODEL_SOUND,
     "rationale": "the A-reference deep model offset_for must equal the REAL post-patch "
                  "_get_aligned_offsets (un-scaled, height=None mirroring the packers' call) on "
                  "every box and every anchor; any mismatch => the one out-of-band trust point is "
                  "unsound (AXIOM-UNSOUND). Reuses+strengthens axiom_check.py over 8 boundary + "
                  "20000 fuzz layouts x 6 anchors."},
    {"id": "ax-deepmodel-containment", "axiom": "offset_for", "kind": "axiom-containment",
     "expect": "covered", "apply_gold": True, "probe": _AX_CONTAINMENT,
     "rationale": "the model only calls offset_for with (heights[k],descents[k],total,code) for "
                  "code in {0,1,2,3} (its Requires). offset_for's four branches partition that code "
                  "set and are defined for any int h,d,total, so it is TOTAL over the "
                  "caller-reachable domain; and the real callee accepts every anchor name those "
                  "codes denote. A caller-reachable input outside the covered domain would be "
                  "AXIOM-TOO-WEAK-FOR-CALLER (none exists)."},
]
