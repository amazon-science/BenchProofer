# properties.py — PBT manifest for matplotlib__matplotlib-25960. NOT a Nagini
# module; a record of adversarial cases. The runner (swebench_nagini.pbt) parses
# SPEC_TESTS / AXIOM_TESTS, executes each, and stamps RESULT.
#
# Defended surface (read from model.py):
#   grid_cell_placement(nrows, ncols, j, i, wspace, hspace, cw, ch) -> CellRect
#   builds one grid cell's rectangle. The postcondition pins ALL FOUR extents to
#   GROUNDED closed forms of the inputs:
#       Result().left   == col_left(i, wspace, cw)   == i*cw*(1+wspace)
#       Result().right  == col_right(i, wspace, cw)  == i*cw*(1+wspace) + cw
#       Result().bottom == row_bottom(j, hspace, ch) == (1 - j*ch*(1+hspace)) - ch
#       Result().top    == row_top(j, hspace, ch)    ==  1 - j*ch*(1+hspace)
#   plus four grid-fill edge clauses (i==0 => left==0; i==ncols-1 => right==1;
#   j==0 => top==1; j==nrows-1 => bottom==0) and two strictly-positive-gap
#   clauses. The four @Pure helpers (col_left/.../row_bottom) are FULLY UNFOLDED
#   linear functions of the args — they are a GROUNDED oracle, not an answer-key,
#   so there is no "wrong echo": echoing col_left IS doing the correct work.
#   The spec also demands the placement be DELIVERED (a total computation): the
#   obligation in the precondition makes "reaches a normal return in finitely
#   many steps" part of the contract, so the extent clauses are claims about an
#   answer that must exist, not claims discharged vacuously by never producing
#   one. Every rival below is therefore attributable on BOTH channels: the value
#   it returns and whether it returns at all.
#
# Class applicability:
#   * FRAME-MUTATION — N/A. grid_cell_placement takes only float scalars (passed
#     by value, no Acc(x,1/2) read-only reference param) and constructs a FRESH
#     CellRect as Result(); there is no caller-supplied mutable object to
#     overwrite. has_readonly_input = False. (See 'assessment'.)
#   * UNGROUNDED-ORACLE ECHO — N/A as a *wrong* echo: the oracle is grounded in
#     the inputs. We instead include two honest cheapest-impl positive controls
#     (one calls the @Pure helpers directly, one uses an algebraically-equal
#     factored form) — both MUST verify (else SPEC-TOO-STRONG).
#   * CONTROL-FLOW-EFFECT — IN SCOPE, and the sharpest lane here. There is no
#     raise or mutation channel (the value abstraction pins all 4 output fields),
#     but WHETHER THE PLACEMENT IS DELIVERED AT ALL is its own observable: a
#     rival that never reaches a return satisfies every extent clause about the
#     value it would have returned, because that post-state never happens. The
#     spec's delivery obligation is what makes this channel visible, and
#     'weak-nodeliver-*' below are the rivals on it — each returns a rectangle no
#     value clause could object to, on a path it never completes.
#   * PARTIAL-DOMAIN / UNIQUENESS — the real attack surface. Rivals correct on a
#     sub-domain but diverging where the gap factor / row orientation / cell
#     width matters; each must be rejected (else SPEC-TOO-WEAK).
#   * POSITIVE CONTROL + ADMISSIBILITY — present.
#
# All SPEC_TESTS are built by region-surgery (_swap inside # impl-start/# impl-end
# ONLY) so the frozen spec is byte-identical (markers.same_spec True). The axiom
# lane re-runs the REAL GridSpec.get_grid_positions in Docker (A-reference deep
# model soundness, = axiom_check.py / G-AX) under the gold patch's configuration.
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25960"
FLOAT_ENCODING = "real"   # meta.json float_encoding

_BASE = (Path(__file__).parent / "model.py").read_text()

# The frozen gold impl-region body (the only text any variant may replace). Kept
# verbatim so each rival's verify/reject outcome is attributable to the swap.
_GOLD_IMPL = """    # Each cell is offset by whole (cell + gap) steps from the origin; the gap
    # is the (1+wspace)/(1+hspace) separation factor the placement must honour.
    # The grid-fill and positive-gap postconditions follow from the cell-size
    # normalization equations.
    left = i * cw * (1.0 + wspace)
    right = left + cw
    top = 1.0 - j * ch * (1.0 + hspace)
    bottom = top - ch
    return CellRect(left, bottom, right, top)"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _variant(new_impl):
    """Return full model source with the impl-region body replaced by new_impl
    (edits ONLY inside # impl-start/# impl-end => same_spec preserved)."""
    return _swap(_BASE, _GOLD_IMPL, new_impl)


# ----------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — structurally different, behaviourally correct.
# ----------------------------------------------------------------------------

# P1: call the @Pure spec helpers directly. The most natural honest impl that
# satisfies the grounded oracle by ACTUALLY COMPUTING it. Different executable
# shape (helper calls vs inline arithmetic); must verify.
_POS_HELPERS = """    # Honest cheapest impl: compute each extent via the spec's own grounded
    # closed-form helpers (no answer-key — these are linear functions of args).
    left = col_left(i, wspace, cw)
    right = col_right(i, wspace, cw)
    top = row_top(j, hspace, ch)
    bottom = row_bottom(j, hspace, ch)
    return CellRect(left, bottom, right, top)"""

# P2: algebraically-equal FACTORED form via an explicit separation variable
# sep_w = wspace*cw, sep_h = hspace*ch, then left = i*(cw + sep_w). This is
# i*cw*(1+wspace) distributed differently; Z3 (linear real arithmetic) discharges
# the equality. Branch/data-shape reshape, not a loop-direction flip => no
# induction lemma needed (avoids the front-recursive-fold trap).
_POS_FACTORED = """    # Structurally different (explicit per-step separation), same value: the
    # cell-plus-gap step is (cw + wspace*cw) = cw*(1+wspace); rows analogously.
    sep_w = wspace * cw
    sep_h = hspace * ch
    left = i * (cw + sep_w)
    right = left + cw
    top = 1.0 - j * (ch + sep_h)
    bottom = top - ch
    return CellRect(left, bottom, right, top)"""

# ----------------------------------------------------------------------------
# ADMISSIBILITY — a self-call on a concrete in-domain (F2P-shaped) input proves
# the precondition is satisfiable. The 1x1 zero-gap grid (cw=ch=1) discharges the
# normalization equations with pure integer arithmetic (no real-division literal,
# avoiding the (1/d)*d==1 fragility). Then a 2-col zero-gap last-cell instance
# (cw=0.5 => 0.5*2==1) exercises i>0. Result unused; the point is that Requires
# is establishable. If this can't verify => PRECOND-TOO-STRONG.
# The witness is a SEPARATE caller rather than a self-call inside the impl: the
# spec's delivery obligation forbids a method from calling itself at its own
# obligation level (a self-call cannot be shown to make progress), which is the
# obligation doing its job. A distinct caller sitting strictly above that level
# is also the more faithful witness — it is what a real grid-layout caller is —
# and it still has to discharge the WHOLE precondition, normalization equations
# and delivery obligation included, at each concrete grid. The two witnesses are
# unchanged, so the lane's force is unchanged: a witness off the normalization
# would still be rejected here.
_ADMISS = """    left = i * cw * (1.0 + wspace)
    right = left + cw
    top = 1.0 - j * ch * (1.0 + hspace)
    bottom = top - ch
    return CellRect(left, bottom, right, top)


def _admissibility_witness() -> None:
    # A CALLER of the placement, so it must discharge the full precondition --
    # including the delivery obligation -- at concrete in-domain grids.
    Requires(MustTerminate(10))
    Assert(1.0 * (1.0 + 0.0 * (1.0 - 1.0)) == 1.0)        # cw=1 normalizes a 1x1
    _r1 = grid_cell_placement(1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0)
    Assert(0.5 * (2.0 + 0.0 * (2.0 - 1.0)) == 1.0)        # cw=0.5 normalizes 1x2
    _r2 = grid_cell_placement(1.0, 2.0, 0.0, 1.0, 0.0, 0.0, 0.5, 1.0)"""

# ----------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN rivals — same spec, wrong impl. MUST be rejected.
# ----------------------------------------------------------------------------

# R1: gap-less placement = the prepatch behaviour (drops BOTH (1+wspace)/(1+hspace)
# factors). Cells abut; requested spacing has no effect — exactly the reported
# bug. Fails Ensures Result().left == col_left(i,wspace,cw) for any i>0,wspace>0.
_R1_GAPLESS = """    # PREPATCH bug: gap-separation factor dropped on both axes (cells abut).
    left = i * cw
    right = left + cw
    top = 1.0 - j * ch
    bottom = top - ch
    return CellRect(left, bottom, right, top)"""

# R2: horizontal-only gap drop, PINNED to the F2P grid — rows always correct,
# columns gap-less (left = i*cw) exactly on the F2P configuration
# subfigures(2, 3, hspace=0.5, wspace=1/6), correct everywhere else. This is
# the sharpest partial-domain attack (wrong ONLY on the tested input) and the
# concrete guard keeps Z3's refutation search trivial. (The earlier unbranched
# form — gap-less columns everywhere — made Z3 diverge under
# --float-encoding=real: 1200s timeouts, outcome inconclusive => the gate
# errored MALFORMED-TESTS with no verdict. Same defect class, decidable shape.)
# Fails Result().left == col_left(i,wspace,cw) on that grid (cw=0.3: column 1
# starts at 0.3, not 0.35) and the i==ncols-1 => right==1 edge.
_R2_HDROP = """    # Columns laid out gap-less (drops the (1+wspace) factor) on EXACTLY the
    # F2P grid -- subfigures(2, 3, hspace=0.5, wspace=1/6) -- and correct
    # everywhere else (partial-domain wrongness). On that grid cw = 0.3, so
    # column 1 starts at 0.3 instead of col_left(1) = 0.35.
    if nrows == 2.0 and ncols == 3.0 and 6.0 * wspace == 1.0 and hspace == 0.5:
        left = i * cw
    else:
        left = i * cw * (1.0 + wspace)
    right = left + cw
    top = 1.0 - j * ch * (1.0 + hspace)
    bottom = top - ch
    return CellRect(left, bottom, right, top)"""

# R3: rows counted from the BOTTOM instead of the top (vertical reflection),
# PINNED to the F2P grid subfigures(2, 3, hspace=0.5, wspace=1/6): top edge
# = (j+1) cell-steps up on that grid, correct everywhere else. Columns always
# correct. (Same decidability story as R2: the unbranched everywhere-reflected
# form timed Z3 out at 1200s => inconclusive => MALFORMED-TESTS; the concrete
# guard keeps the same defect class refutable in seconds.) Fails
# Result().top == row_top / Result().bottom == row_bottom on that grid
# (ch=0.4: cell (0,0)'s top becomes 0.4, not 1) and the j==0 => top==1 /
# j==nrows-1 => bottom==0 grid-fill edges.
_R3_REFLECT = """    # Rows counted from the BOTTOM (vertical reflection) on EXACTLY the F2P
    # grid -- subfigures(2, 3, hspace=0.5, wspace=1/6) -- and correct
    # everywhere else. On that grid ch = 0.4, so cell (0,0)'s top edge
    # becomes 0.4 instead of 1.
    left = i * cw * (1.0 + wspace)
    right = left + cw
    if nrows == 2.0 and ncols == 3.0 and 6.0 * wspace == 1.0 and hspace == 0.5:
        bottom = j * ch * (1.0 + hspace)
        top = bottom + ch
    else:
        top = 1.0 - j * ch * (1.0 + hspace)
        bottom = top - ch
    return CellRect(left, bottom, right, top)"""

# R4: cell WIDTH inflated to include the gap (right = left + cw*(1+wspace)).
# left edges are correct (so col 0 starts at 0), but each cell overruns into the
# gap. Fails Result().right == col_right and the positive-gap clause
# Result().right < col_left(i+1) (the cells now touch/overlap the next column).
_R4_FATCELL = """    # left edges correct, but the cell width swallows the gap (right too far).
    left = i * cw * (1.0 + wspace)
    right = left + cw * (1.0 + wspace)
    top = 1.0 - j * ch * (1.0 + hspace)
    bottom = top - ch
    return CellRect(left, bottom, right, top)"""

# R5: off-by-one column gap accounting — left = i*cw + (i-1)*wspace*cw style,
# i.e. gap counted as (i-1) gaps for i>=1 but here written so column 0 and 1 are
# correct yet column 2 short by one gap. Concretely: left = i*cw + max(0,i-1)*...
# Nagini has no max; use the cheaper near-miss: gap factor applied to the WIDTH
# of the offset but the offset uses (i) cells and (i) gaps (one gap too many),
# left = i*cw + i*wspace*cw + ... no -> simpler: shift everything by one extra
# half-gap. We model "one extra gap on the left" (left = (i+? )). Keep it a clean
# divergence: left uses (i+1) gaps. Fails Result().left==col_left and i==0=>left==0.
_R5_EXTRAGAP = """    # one extra horizontal gap baked into every left edge (col 0 no longer at 0).
    left = i * cw + (i + 1.0) * wspace * cw
    right = left + cw
    top = 1.0 - j * ch * (1.0 + hspace)
    bottom = top - ch
    return CellRect(left, bottom, right, top)"""

# R6: the DELIVERY channel, unconditional. The placement never reaches a return:
# a loop whose guard is never falsified over the reals (halving a positive
# quantity stays positive), so the returned rectangle is unreachable and every
# extent clause is a statement about a post-state that never occurs. The value
# channel alone cannot object to this — the returned CellRect(0,0,0,0) is never
# compared to anything, because control never gets there. Only the delivery
# obligation in the precondition rejects it.
_R6_NODELIVER = """    # Never delivers: over the reals a positive quantity halved is still
    # positive, so the loop guard never becomes false and the return below is
    # unreachable. Every extent clause is then a claim about a state that never
    # happens.
    k = 1.0
    while k > 0.0:
        Invariant(k > 0.0)
        k = k * 0.5
    return CellRect(0.0, 0.0, 0.0, 0.0)"""

# R7: the DELIVERY channel, PARTIAL-DOMAIN. Correct and delivered on every grid
# EXCEPT the F2P configuration, where it never returns. This is the sharper form:
# a rival can be gold-identical almost everywhere and still fail to place the one
# grid the issue is about, so an obligation that only had to hold on some path
# would let it through. Rejected because the delivery obligation must be
# discharged on EVERY path the precondition admits.
_R7_NODELIVER_PARTIAL = """    # Delivers the correct rectangle on every grid except EXACTLY the F2P
    # configuration -- subfigures(2, 3, hspace=0.5, wspace=1/6) -- on which it
    # never returns at all. Partial delivery is not delivery.
    if nrows == 2.0 and ncols == 3.0 and 6.0 * wspace == 1.0 and hspace == 0.5:
        k = 1.0
        while k > 0.0:
            Invariant(k > 0.0)
            k = k * 0.5
        return CellRect(0.0, 0.0, 0.0, 0.0)
    left = i * cw * (1.0 + wspace)
    right = left + cw
    top = 1.0 - j * ch * (1.0 + hspace)
    bottom = top - ch
    return CellRect(left, bottom, right, top)"""

# P3: OVER-FIT CONTROL for the delivery obligation. A correct placement that
# reaches its answer through a genuine, BOUNDED loop. The obligation demands
# "delivers an answer in finitely many steps", NOT "is straight-line code": if
# this were rejected, the spec would be pinning the gold implementation's loop-
# free shape rather than its behaviour, and correct alternatives would fail.
# Must verify.
_POS_BOUNDED_LOOP = """    # Correct, but reaches the answer after a bounded loop: delivery is about
    # terminating, not about being loop-free.
    n = 3
    while n > 0:
        Invariant(n >= 0)
        Invariant(MustTerminate(n + 1))
        n = n - 1
    left = i * cw * (1.0 + wspace)
    right = left + cw
    top = 1.0 - j * ch * (1.0 + hspace)
    bottom = top - ch
    return CellRect(left, bottom, right, top)"""


SPEC_TESTS = [
    {
        "id": "pos-helpers",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS_HELPERS),
        "rationale": "Honest correct impl computing each extent via the grounded "
                     "@Pure helpers (col_left/.../row_bottom). Different executable "
                     "shape from the gold inline arithmetic; the Ensures are stated "
                     "in terms of these very helpers, so it must verify. If it "
                     "can't => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-factored",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS_FACTORED),
        "rationale": "Structurally different correct impl: explicit separation "
                     "sep_w=wspace*cw, step=(cw+sep_w), so left=i*(cw+sep_w)= "
                     "i*cw*(1+wspace). Pure linear real arithmetic Z3 discharges "
                     "(no induction lemma, no front-recursive fold). Must verify.",
    },
    {
        "id": "pos-bounded-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS_BOUNDED_LOOP),
        "rationale": "OVER-FIT CONTROL for the delivery obligation: a correct "
                     "placement that reaches its answer after a bounded loop. The "
                     "spec demands the placement be DELIVERED (finitely many "
                     "steps), not that it be straight-line code — if this were "
                     "rejected the spec would be pinning the gold implementation's "
                     "loop-free shape and correct alternatives would fail => "
                     "SPEC-TOO-STRONG. Measured: verifies in 12.4s.",
    },
    {
        "id": "admiss-grid",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(_ADMISS),
        "rationale": "Self-calls on concrete in-domain inputs (1x1 cw=ch=1; 1x2 "
                     "zero-gap cw=0.5 last column) prove the precondition — incl. "
                     "the normalization equations — is establishable for normal "
                     "grid inputs. If the Requires can't be met => PRECOND-TOO-STRONG.",
    },
    {
        "id": "weak-gapless-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_R1_GAPLESS),
        "refinement": "This is the PREPATCH behaviour (model_prepatch.py): the "
                      "(1+wspace)/(1+hspace) factor is dropped so cells abut. The "
                      "faithful real patch (build the gridspec but never recompute "
                      "cells from the spacing) is exactly the unfixed code — the "
                      "F2P test_subfigures_wspace_hspace fails (column 1 lands at "
                      "1/3 of the width, not the required 0.35; sub_figs[0,1].bbox "
                      ".min[0] = w/3 != w*0.35). verify here would be verify⇏resolve.",
        "rationale": "Rejected by Ensures Result().left == col_left(i,wspace,cw) "
                     "(carries the (1+wspace) factor) for any i>0, wspace>0; also "
                     "the i==ncols-1 => right==1 grid-fill edge fails.",
    },
    {
        "id": "weak-hdrop-partial",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_R2_HDROP),
        "refinement": "Correct on every row and on every non-F2P grid, but lays "
                      "columns out gap-less (left=i*cw) exactly on the F2P grid "
                      "subfigures(2,3,hspace=0.5,wspace=1/6): column 1 lands at "
                      "w*0.3, not the required w*0.35 — the F2P "
                      "sub_figs[0,1]/[1,1].bbox assertions fail. Partial-domain "
                      "correctness (wrong ONLY on the tested input) is NOT "
                      "resolution.",
        "rationale": "Rejected by Result().left == col_left(i,wspace,cw) on the "
                     "F2P grid (cw=0.3, i=1: 0.3 != 0.35) and the "
                     "i==ncols-1 => right==1 grid-fill edge. Concrete guard keeps "
                     "the refutation decidable (~10s; the unbranched form made Z3 "
                     "time out => MALFORMED-TESTS).",
    },
    {
        "id": "weak-row-reflect",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_R3_REFLECT),
        "refinement": "Columns correct everywhere and rows correct on every "
                      "non-F2P grid, but rows counted from the bottom exactly on "
                      "the F2P grid subfigures(2,3,hspace=0.5,wspace=1/6): cell "
                      "(0,0)'s top becomes ch (=0.4) instead of 1. A real patch "
                      "indexing get_grid_positions rows bottom-up would put "
                      "sub_figs[0,0].bbox.max at h*0.4 not h — the F2P top-row "
                      "assertions (sub_figs[0,*].bbox.max[1]==h) fail.",
        "rationale": "Rejected by Result().top == row_top(j,hspace,ch) / "
                     "Result().bottom == row_bottom(...) on the F2P grid and the "
                     "grid-fill edges j==0 => top==1 / j==nrows-1 => bottom==0. "
                     "Concrete guard keeps the refutation decidable (~8s; the "
                     "unbranched form made Z3 time out => MALFORMED-TESTS).",
    },
    {
        "id": "weak-fatcell-gap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_R4_FATCELL),
        "refinement": "Left edges correct (col 0 at 0), but each cell width "
                      "swallows the gap (right = left + cw*(1+wspace)). A real "
                      "patch using the wrong cell width makes cells overlap the "
                      "gaps — col 0's right would be 0.3*(7/6)=0.35 not 0.3, so "
                      "sub_figs[0,0].bbox.max[0]=w*0.35 != w*0.3: F2P fails.",
        "rationale": "Rejected by Result().right == col_right(i,wspace,cw) "
                     "(=left+cw, not left+cw*(1+wspace)) and the strictly-positive "
                     "horizontal-gap clause Result().right < col_left(i+1,...) "
                     "(the inflated right now reaches the next column's left).",
    },
    {
        "id": "weak-extra-gap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_R5_EXTRAGAP),
        "refinement": "An extra horizontal gap is baked into every left edge "
                      "(left = i*cw + (i+1)*wspace*cw), so even column 0 is pushed "
                      "right by one gap. A real patch with this off-by-one gap "
                      "count breaks the grid-fill (first column no longer at 0) and "
                      "shifts every F2P x-coordinate — sub_figs[*,0].bbox.min[0] "
                      "!= 0. Cheap near-miss SUPPORTING case (still resolution-false).",
        "rationale": "Rejected by the i==0 => Result().left == 0 grid-fill edge "
                     "(col 0 now starts at wspace*cw>0) and by "
                     "Result().left == col_left(i,wspace,cw).",
    },
    {
        "id": "weak-nodeliver-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_R6_NODELIVER),
        "refinement": "The placement never produces an answer: over the reals the "
                      "loop guard is never falsified, so the return is unreachable "
                      "and all four extent clauses describe a post-state that never "
                      "occurs. The faithful real patch is a subfigures() that hangs "
                      "instead of laying the grid out, so the F2P "
                      "test_subfigures_wspace_hspace never reaches an assertion — no "
                      "requested spacing is ever honoured. verify here would be "
                      "verify⇏resolve on the delivery channel.",
        "rationale": "Rejected by the precondition's delivery obligation, which the "
                      "non-progressing loop cannot discharge. NOTE this is the lane "
                      "the value clauses provably CANNOT cover: a rival that never "
                      "returns satisfies every Ensures vacuously, which is why the "
                      "obligation and not another extent equality is what closes it.",
    },
    {
        "id": "weak-nodeliver-partial",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_R7_NODELIVER_PARTIAL),
        "refinement": "Delivers the correct rectangle on every grid EXCEPT the F2P "
                      "configuration subfigures(2,3,hspace=0.5,wspace=1/6), on which "
                      "it never returns. The faithful real patch lays out every other "
                      "grid correctly and hangs on exactly the one the issue reports, "
                      "so the F2P test never completes. Partial delivery is not "
                      "delivery, and this is the shape a rival takes once the "
                      "unconditional divergence is closed.",
        "rationale": "Rejected because the delivery obligation must be discharged on "
                      "EVERY path the precondition admits, not merely on some path; "
                      "the guarded non-progressing branch cannot discharge it. The "
                      "value clauses are satisfied on every path that returns, so no "
                      "extent equality can reject this one either.",
    },
]


# ----------------------------------------------------------------------------
# AXIOM LANE — no @ContractOnly consumed axioms (axioms region empty). The one
# kind-A obligation is the A-REFERENCE deep geometry model: col_left/col_right/
# row_top/row_bottom + the cw/ch normalization MUST equal the REAL routine the
# gold patch invokes, matplotlib.gridspec.GridSpec.get_grid_positions(fig), under
# the caller's actual config (left=0,right=1,bottom=0,top=1, equal ratios — the
# gold patch sets exactly those). A-reference deep models are checked like axiom
# soundness (PBT_PLAN §2.4 / §4). We embed axiom_check.py's logic, fuzz boundary
# + 400 random grids, and assert the real callee == the model closed form. Run
# in Docker with apply_gold=True (the routine is called only on the post-gold
# gridspec construction). Containment: the model can only reach get_grid_positions
# with nrows,ncols>=1, wspace,hspace>=0, equal ratios, left=0/right=1/bottom=0/
# top=1 — exactly the domain the probe fuzzes; get_grid_positions accepts all of
# it (no narrower Requires), so there is no caller-reachable out-of-domain input.
# ----------------------------------------------------------------------------

# Embed the host axiom_check.py oracle into the probe (the runner mounts ONLY the
# probe at /work; model.py / axiom_check.py are NOT in-container — pilot bug #6).
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

_AX_PROBE = _AXIOM_CHECK_SRC + """

# --- PBT driver: re-run the host G-AX oracle in-container under the gold config.
if __name__ != "__pbt__":
    import sys as _sys
    try:
        rc = main()
    except AssertionError as _e:
        print("AXIOM-UNSOUND (A-reference): %s" % _e)
        _sys.exit(1)
    _sys.exit(rc)
"""

AXIOM_TESTS = [
    {
        "id": "ax-ref-getgridpositions",
        "axiom": "col_left/col_right/row_top/row_bottom (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": "A-reference soundness (PBT_PLAN §2.4): runs the REAL "
                     "GridSpec.get_grid_positions(fig) with left=0,right=1,bottom=0,"
                     "top=1 and the requested wspace/hspace (the gold patch's exact "
                     "construction) over 10 boundary grids (incl. the F2P 2x3 "
                     "wspace=1/6 hspace=0.5) + 400 fuzz grids, asserting every cell "
                     "extent equals the model closed form to abs_tol=1e-9. Any "
                     "mismatch => AXIOM-UNSOUND (the deep geometry model is wrong "
                     "about the real callee). Containment: the probe's fuzz domain "
                     "(nrows,ncols in [1,6], wspace/hspace in {0}u[0,2], equal "
                     "ratios, unit span) is exactly what the model can reach, and "
                     "get_grid_positions imposes no narrower Requires => no "
                     "caller-reachable input lies outside the covered domain.",
    },
]
