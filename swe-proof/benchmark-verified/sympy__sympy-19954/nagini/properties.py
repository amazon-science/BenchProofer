"""properties.py — PBT falsification manifest for sympy__sympy-19954.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    prune_parallel(blocks, nums, reps, flag) -> (List[int], List[int], List[int])

(the deep model of the gold patch's inner pruning hunk in
`PermutationGroup.minimal_blocks`: prune THREE parallel candidate lists by ONE
shared per-position boolean removal mask, taken from a single snapshot, so the
three results stay aligned). Its load-bearing contract:

    # READ-ONLY half-permission on all four inputs (preserved across the call):
    Requires/Ensures(Acc(list_pred(blocks), 1/2)) ... (nums, reps, flag)
    # full permission on the three fresh outputs:
    Ensures(Acc(list_pred(Result()[0/1/2])))
    # THE DISCRIMINATING CLAUSES — each output is the SAME mask-filter of its
    # own input under the ONE shared flag:
    Ensures(ToSeq(Result()[0]) == filtered(ToSeq(blocks), ToSeq(flag)))
    Ensures(ToSeq(Result()[1]) == filtered(ToSeq(nums),   ToSeq(flag)))
    Ensures(ToSeq(Result()[2]) == filtered(ToSeq(reps),   ToSeq(flag)))
    # the alignment consequence — all three lengths equal kept(flag):
    Ensures(len(Result()[0]) == kept(ToSeq(flag)))   ... ([1], [2])
    Ensures(len(Result()[0]) == len(Result()[1]) == len(Result()[2]))

What the spec actually defends, and the attacks it must survive:

  * READ-ONLY INPUTS (the #1 weakness class). All four parameters carry
    `Acc(list_pred(x), 1/2)` in BOTH Requires and Ensures — half permission,
    so the body may READ them but may NOT write to them. A rival that mutates an
    input (append / index-store) to make a postcondition true vacuously must be
    rejected by the PERMISSION SYSTEM (insufficient permission to write through a
    1/2 predicate), not by a value clause. The FRAME-MUTATION case is therefore
    MANDATORY and a byte-fuzzer never finds it.

  * GROUNDED ORACLE — `filtered` / `kept` are `@Pure` front-recursive folds, each
    a fully-unfolded function of (the input list, the flag). They are NOT an
    opaque answer-key marker: there is no `oracle(x)` value an impl could `return`
    to echo the answer without doing the work (a `PSeq` cannot be materialised
    into a `List[int]` inside the impl; the output list must be BUILT element by
    element and PROVEN equal to the fold). So UNGROUNDED-ORACLE-ECHO is N/A —
    instead the positive controls confirm the cheapest HONEST impl that satisfies
    the three `filtered` pins is exactly a per-position fold over the shared flag.

  * THE DISCRIMINATING CONTENT (the substance of the issue / G-DIFF) is that ALL
    THREE lists are pruned by the SAME shared mask in a single consistent
    snapshot, so they stay length-aligned (`kept(flag)`) and per-position
    parallel. The pre-patch deleted `blocks`/`num_blocks` IN PLACE
    (`del num_blocks[i], blocks[i]`) WHILE the scan was still running, so a second
    removal landed on a shifted index — either running off the end (the reported
    `IndexError`) or discarding the WRONG position — while `rep_blocks` was pruned
    separately afterwards. That is a DESYNCHRONISATION of the three lists. Every
    uniqueness rival reproduces a desync / wrong-mask / wrong-position prune that
    one of the `filtered`/`kept` clauses must catch. The headline rival is the
    pre-patch behaviour (`model_prepatch.py`): prune `reps` correctly but let only
    the FIRST flagged removal take effect on `blocks`/`nums`.

  * NO CONTROL-FLOW / RAISE / SIDE-EFFECT difference is invisible to the value
    abstraction: the function only RETURNS a 3-tuple of fresh lists (full perm),
    and the value clauses pin each component exactly; the inputs are framed
    read-only. There is no exception channel or external side effect the spec
    abstracts away, so CONTROL-FLOW-EFFECT is N/A (justified in 'assessment').

  * NO axiomatized external callee — the `axioms` region is empty and
    `meta.axioms == []`. The changed prune is modelled DEEPLY by `filtered`/`kept`
    (A-reference deep models validated == real Python list-comprehension semantics
    by axiom_check.py / G-AX, out-of-band). There is nothing to run the real
    callee against, so AXIOM_TESTS = [] (the deep-model soundness lives in G-AX).

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`) that
edits ONLY inside `# impl-start`/`# impl-end` (which the spec-view elides ENTIRELY
— including the nested `# invariants-start`/`# invariants-end` block), so
`markers.same_spec` is guaranteed and any rejection comes from the
POST-CONDITIONS / PERMISSION SYSTEM catching wrong behaviour, never from a
tampered spec. CAUTION honoured (PLAN §5a.3): the gold proof is a BACKWARD loop
(i from len(flag) down to 0) that FRONT-PREPENDs survivors, matching the
front-recursive `filtered`; every positive control KEEPS the backward direction
and ALL the framing `Assert(... drop(i-1) ... == ... drop(i))` lines (PLAN §5a.2)
— a forward-append rival would need an `f(a+b)==f(a)+f(b)` lemma the verifier
cannot auto-discharge and would fail for a PROOF reason, so it is NOT used as a
positive control (it appears only as a labelled reject case where non-verification
is expected).
"""
from pathlib import Path

INSTANCE = "sympy__sympy-19954"
FLOAT_ENCODING = None  # meta.json float_encoding is null


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
# Region landmarks (all strictly INSIDE # impl-start / # impl-end).
# The spec view elides the WHOLE impl region (and the nested invariants block),
# so swapping any of these leaves same_spec invariant; a rejection is then
# attributable solely to the swapped body / permission, not to a touched contract.
# ---------------------------------------------------------------------------

# The gold loop body's removal-decision branch (the heart of the prune).
_GOLD_BRANCH = """        if f:
            # flagged for removal at this position: drop it from every list.
            out_blocks = out_blocks
            out_nums = out_nums
            out_reps = out_reps
        else:
            out_blocks = [b] + out_blocks
            out_nums = [n] + out_nums
            out_reps = [r] + out_reps
        i = i - 1"""

# The gold output prologue (the three empty accumulators).
_GOLD_PROLOGUE = """    out_blocks = []  # type: List[int]
    out_nums = []  # type: List[int]
    out_reps = []  # type: List[int]
    i = len(flag)"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) Structurally-DIFFERENT but CORRECT — BRANCH REORDER. The gold body tests
# `if f:` (skip) ... `else:` (prepend). This control tests the SURVIVOR case
# first (`if not f:` prepend) then the removal case (`else:` skip). Same backward
# direction, same front-prepend, all framing asserts kept verbatim, only the two
# branch arms swapped. The verifier still has exactly one unfold of filtered/kept
# available per step, so the gold proof goes through. If this fails to verify, the
# postcondition is over-fit to the exact gold branch order => SPEC-TOO-STRONG.
_POS_REORDER_BRANCH = """        if not f:
            out_blocks = [b] + out_blocks
            out_nums = [n] + out_nums
            out_reps = [r] + out_reps
        else:
            # flagged for removal at this position: drop it from every list.
            out_blocks = out_blocks
            out_nums = out_nums
            out_reps = out_reps
        i = i - 1"""
_POS_REORDER = _swap(_BASE, _GOLD_BRANCH, _POS_REORDER_BRANCH)

# (5b) Structurally-DIFFERENT but CORRECT — LOCAL-VARIABLE RESHAPE. Instead of two
# parallel rebindings inside each arm, bind the per-step new heads through typed
# locals first, then prepend. Same backward fold, same shared decision `f`, same
# framing asserts; only the executable shape (an intermediate single-element list
# local per output) changes. If this fails, the spec is over-fit to the exact
# `[b] + out_blocks` spelling => SPEC-TOO-STRONG.
_POS_RESHAPE_BRANCH = """        if f:
            # flagged for removal at this position: drop it from every list.
            out_blocks = out_blocks
            out_nums = out_nums
            out_reps = out_reps
        else:
            head_b = [b]  # type: List[int]
            head_n = [n]  # type: List[int]
            head_r = [r]  # type: List[int]
            out_blocks = head_b + out_blocks
            out_nums = head_n + out_nums
            out_reps = head_r + out_reps
        i = i - 1"""
_POS_RESHAPE = _swap(_BASE, _GOLD_BRANCH, _POS_RESHAPE_BRANCH)

# (6) ADMISSIBILITY. The precondition demands four parallel half-permission lists
# of equal length to `flag`. A self-call must be able to ESTABLISH that Requires
# for a normal F2P-shaped input. We build two equal-length empty lists/flag in
# typed locals and self-invoke (an in-domain, trivially-parallel input — the
# n == 0 boundary of the real prune, which the F2P traverses). If the self-call
# fails to establish the Requires for a legitimate input => PRECOND-TOO-STRONG.
# The call's result is discarded; the gold prologue/loop/return follow unchanged.
_ADMISS_PROLOGUE = """    _eb = []  # type: List[int]
    _en = []  # type: List[int]
    _er = []  # type: List[int]
    _ef = []  # type: List[bool]
    Assert(Acc(list_pred(_eb), 1 / 2))
    Assert(Acc(list_pred(_en), 1 / 2))
    Assert(Acc(list_pred(_er), 1 / 2))
    Assert(Acc(list_pred(_ef), 1 / 2))
    Assert(len(_eb) == len(_ef))
    Assert(len(_en) == len(_ef))
    Assert(len(_er) == len(_ef))
    Assert(len(ToSeq(_eb)) == len(ToSeq(_ef)))
    Assert(len(ToSeq(_en)) == len(ToSeq(_ef)))
    Assert(len(ToSeq(_er)) == len(ToSeq(_ef)))
    out_blocks = []  # type: List[int]
    out_nums = []  # type: List[int]
    out_reps = []  # type: List[int]
    i = len(flag)"""
_ADMISS = _swap(_BASE, _GOLD_PROLOGUE, _ADMISS_PROLOGUE)


# ===========================================================================
# FRAME-MUTATION RIVALS (read-only inputs; MANDATORY) — expect "reject"
# ===========================================================================

# (1) FRAME-MUTATION via APPEND on a read-only input. The body APPENDS to `blocks`
# (held at Acc(list_pred(blocks), 1/2) — write requires FULL permission). A wrong
# real patch that mutated the shared input `blocks` in place to line it up before
# rebuilding would write through that half-permission and must be rejected for
# INSUFFICIENT PERMISSION. The gold value clauses are kept verbatim so the
# rejection is attributable to the WRITE, not to a value mismatch. (If this
# verified, the spec would not actually pin the inputs read-only and an impl could
# clobber the caller's parallel lists — a real frame defect.)
_FRAME_APPEND = """    out_blocks = []  # type: List[int]
    out_nums = []  # type: List[int]
    out_reps = []  # type: List[int]
    blocks.append(0)
    i = len(flag)"""
_RIVAL_FRAME_APPEND = _swap(_BASE, _GOLD_PROLOGUE, _FRAME_APPEND)

# (1b) FRAME-MUTATION via INDEX-STORE on a read-only input. The body assigns
# `flag[0] = False` (an index-store through the half-permission `flag` predicate).
# A wrong real patch that zeroed/normalised the shared mask in place would write
# through that 1/2 permission and must be rejected for INSUFFICIENT PERMISSION.
# Guarded by `len(flag) > 0` so it is a genuine write attempt on the non-empty
# domain (the F2P traverses non-empty lists). Gold value clauses kept verbatim.
_FRAME_STORE = """    out_blocks = []  # type: List[int]
    out_nums = []  # type: List[int]
    out_reps = []  # type: List[int]
    if len(flag) > 0:
        flag[0] = False
    i = len(flag)"""
_RIVAL_FRAME_STORE = _swap(_BASE, _GOLD_PROLOGUE, _FRAME_STORE)


# ===========================================================================
# UNIQUENESS / DESYNC RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (2) PREPATCH DESYNC — the headline rival, the EXACT issue (model_prepatch.py
# semantics). `reps` is pruned correctly by the shared flag, but `blocks`/`nums`
# only have their FIRST flagged removal take effect: a `done` latch suppresses
# every subsequent skip, so on >=2 flagged positions blocks/nums keep a position
# that the shared mask removed — they DESYNC from reps. Implemented backward with
# the same framing asserts so the only change is the desync in the blocks/nums
# arm. Rejection source: `ToSeq(Result()[0]) == filtered(ToSeq(blocks), ToSeq(flag))`
# (and transitively `len(Result()[0]) == kept(ToSeq(flag))` and the cross-length
# alignment) — on a >=2-flag input out_blocks has the wrong length / wrong members.
_RIVAL_DESYNC_PROLOGUE = """    out_blocks = []  # type: List[int]
    out_nums = []  # type: List[int]
    out_reps = []  # type: List[int]
    done = False
    i = len(flag)"""
_RIVAL_DESYNC_BRANCH = """        if f:
            # reps prunes correctly; blocks/nums only drop the FIRST flagged one
            # (the pre-patch in-place-del desync: a second removal misfires).
            if done:
                out_blocks = [b] + out_blocks
                out_nums = [n] + out_nums
            else:
                out_blocks = out_blocks
                out_nums = out_nums
            done = True
            out_reps = out_reps
        else:
            out_blocks = [b] + out_blocks
            out_nums = [n] + out_nums
            out_reps = [r] + out_reps
        i = i - 1"""
_RIVAL_DESYNC = _swap(
    _swap(_BASE, _GOLD_PROLOGUE, _RIVAL_DESYNC_PROLOGUE),
    _GOLD_BRANCH, _RIVAL_DESYNC_BRANCH)

# (3) WRONG-MASK RIVAL — prune `nums` by the COMPLEMENT of the flag (keep when
# flagged) while `blocks`/`reps` use the correct flag. A faithful real patch that
# applied an inverted / different mask to `num_blocks` than to blocks/rep_blocks
# would desync num_blocks from the other two: the alignment `S.order()` invariant
# the F2P checks would break (num_blocks no longer parallels the surviving
# blocks). Backward, framing asserts kept. Rejection source:
# `ToSeq(Result()[1]) == filtered(ToSeq(nums), ToSeq(flag))` — out_nums keeps the
# flagged (removed) positions and drops the surviving ones, the opposite filter.
_RIVAL_WRONGMASK_BRANCH = """        if f:
            # blocks/reps drop the flagged position; nums WRONGLY keeps it.
            out_blocks = out_blocks
            out_nums = [n] + out_nums
            out_reps = out_reps
        else:
            # nums WRONGLY drops the surviving position.
            out_blocks = [b] + out_blocks
            out_nums = out_nums
            out_reps = [r] + out_reps
        i = i - 1"""
_RIVAL_WRONGMASK = _swap(_BASE, _GOLD_BRANCH, _RIVAL_WRONGMASK_BRANCH)

# (4) PARTIAL-DOMAIN — IGNORE-THE-FLAG rival: keep EVERY position in all three
# lists (never remove). Correct on the all-survive sub-domain (no flag set) but
# diverges the moment ANY position is flagged. A faithful real patch that simply
# never applied the mask (left `blocks`/`num_blocks`/`rep_blocks` unpruned) would
# carry the non-minimal block systems forward, so `minimal_blocks()` returns too
# many systems and `sylow_subgroup(p=2)` has the wrong order (the F2P asserts
# `S.order() == 4`) — FAILS the F2P. Backward, framing asserts kept. Rejection
# source: all three `filtered` clauses (out length is len(flag), not kept(flag),
# whenever a flag is True) and the kept(flag) length clauses.
_RIVAL_KEEPALL_BRANCH = """        if f:
            # WRONG: ignore the removal flag, keep the position anyway.
            out_blocks = [b] + out_blocks
            out_nums = [n] + out_nums
            out_reps = [r] + out_reps
        else:
            out_blocks = [b] + out_blocks
            out_nums = [n] + out_nums
            out_reps = [r] + out_reps
        i = i - 1"""
_RIVAL_KEEPALL = _swap(_BASE, _GOLD_BRANCH, _RIVAL_KEEPALL_BRANCH)

# (5) PARTIAL-DOMAIN (cheap supporting case, real refinement) — DROP-EVERYTHING
# rival: remove EVERY position from all three lists. Correct on the all-removed
# sub-domain (every flag set, output empty) but diverges as soon as any position
# survives. A faithful real patch that over-pruned (removed survivors too) would
# discard minimal block systems that should remain, again giving
# `sylow_subgroup` the wrong order — FAILS the F2P. Backward, framing asserts
# kept. Rejection source: the three `filtered` clauses (out is empty, but
# filtered keeps the False-flagged positions) and the kept(flag) clauses.
_RIVAL_DROPALL_BRANCH = """        if f:
            # flagged for removal at this position: drop it from every list.
            out_blocks = out_blocks
            out_nums = out_nums
            out_reps = out_reps
        else:
            # WRONG: drop the surviving position too.
            out_blocks = out_blocks
            out_nums = out_nums
            out_reps = out_reps
        i = i - 1"""
_RIVAL_DROPALL = _swap(_BASE, _GOLD_BRANCH, _RIVAL_DROPALL_BRANCH)


SPEC_TESTS = [
    # ---- positive controls (must verify) ----
    {"id": "pos-control-branch-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different but CORRECT impl: the two branch arms are "
                  "swapped (test `if not f:` prepend first, then `else:` skip). Same "
                  "backward direction and front-prepend matching the front-recursive "
                  "filtered/kept, all framing asserts kept verbatim (PLAN §5a.2), so the "
                  "gold proof still discharges with one unfold per step. Must verify; if "
                  "it fails the postcondition is over-fit to the gold branch order => "
                  "SPEC-TOO-STRONG."},
    {"id": "pos-control-local-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_RESHAPE,
     "rationale": "structurally-different but CORRECT impl: the survivor head is bound "
                  "through typed single-element locals (head_b/head_n/head_r) before "
                  "prepending, instead of the inline `[b] + out_blocks`. Same backward "
                  "fold, same shared decision, framing asserts kept. If it fails the spec "
                  "is over-fit to the exact prepend spelling => SPEC-TOO-STRONG."},
    {"id": "admiss-selfcall-empty-parallel", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "the precondition demands four equal-length half-permission parallel "
                  "lists; a self-call on four empty (hence trivially equal-length, "
                  "trivially parallel) lists — the n==0 boundary the F2P traverses — must "
                  "establish that Requires. If the self-call cannot establish the "
                  "precondition for a legitimate input => PRECOND-TOO-STRONG."},

    # ---- frame-mutation rivals (read-only inputs; must reject) ----
    {"id": "frame-mutate-append-blocks", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_APPEND,
     "refinement": "a real patch that APPENDED to the shared input list `blocks` in place "
                   "(e.g. to pad it before rebuilding) mutates the caller's parallel "
                   "candidate list mid-routine; `minimal_blocks` keeps using `blocks` "
                   "afterwards, so a clobbered `blocks` corrupts the block systems and "
                   "`sylow_subgroup(p=2)` would not have order 4 — FAILS the F2P. The "
                   "frame defect is exactly what the read-only 1/2 permission forbids.",
     "rationale": "rejection from the PERMISSION SYSTEM: `blocks` is held at "
                  "Acc(list_pred(blocks), 1/2); `blocks.append(0)` requires FULL "
                  "permission to write, which the body does not hold => INSUFFICIENT "
                  "PERMISSION. The gold value clauses are unchanged, so the rejection is "
                  "attributable solely to the write on the read-only input."},
    {"id": "frame-mutate-store-flag", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_STORE,
     "refinement": "a real patch that normalised the shared mask in place (e.g. "
                   "`blocks_remove_mask[0] = False`) writes through the read-only flag and "
                   "would change the removal decision other call sites depend on; the "
                   "snapshot is meant to be a single consistent read-only mask, so "
                   "mutating it desyncs the prune — non-resolving and unfaithful.",
     "rationale": "rejection from the PERMISSION SYSTEM: `flag` is held at "
                  "Acc(list_pred(flag), 1/2); the index-store `flag[0] = False` requires "
                  "FULL permission => INSUFFICIENT PERMISSION. Gold value clauses kept "
                  "verbatim, so the rejection is attributable to the write on the "
                  "read-only mask."},

    # ---- uniqueness / desync rivals (must reject) ----
    {"id": "prepatch-desync-blocks-nums", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DESYNC,
     "refinement": "this IS the issue (model_prepatch.py): prune reps correctly but let "
                   "only the FIRST flagged removal take effect on blocks/num_blocks (the "
                   "pre-patch in-place `del num_blocks[i], blocks[i]` desync, where a "
                   "second removal landed on a shifted index). On the F2P "
                   "`DihedralGroup(18/50).sylow_subgroup(p=2)` two or more positions are "
                   "flagged, so blocks/num_blocks keep a non-minimal system the mask "
                   "removed (or run off the end with IndexError) — definitively "
                   "non-resolving (the reported crash).",
     "rationale": "rejection from `ToSeq(Result()[0]) == filtered(ToSeq(blocks), "
                  "ToSeq(flag))`: on a >=2-flag input out_blocks retains a flagged "
                  "position, so it differs from the shared-mask filter; transitively "
                  "`len(Result()[0]) == kept(ToSeq(flag))` and the cross-length alignment "
                  "`len(Result()[0]) == len(Result()[2])` also fail."},
    {"id": "wrong-mask-nums-inverted", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONGMASK,
     "refinement": "a real patch that applied a DIFFERENT / inverted mask to `num_blocks` "
                   "than to blocks/rep_blocks desyncs num_blocks from the other two "
                   "parallel lists — the k-th surviving num no longer matches the k-th "
                   "surviving block, so the block-system bookkeeping `minimal_blocks` "
                   "returns is corrupt and `sylow_subgroup(p=2)` order != 4 — FAILS the "
                   "F2P.",
     "rationale": "rejection from `ToSeq(Result()[1]) == filtered(ToSeq(nums), "
                  "ToSeq(flag))`: out_nums keeps the True-flagged positions and drops the "
                  "False-flagged ones (the complement filter), contradicting the required "
                  "shared-flag filter; the `len(Result()[1]) == kept(ToSeq(flag))` and "
                  "cross-alignment clauses also fail on any mixed-flag input."},
    {"id": "partial-keep-all", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_KEEPALL,
     "refinement": "a real patch that never applied the mask (left all three lists "
                   "unpruned) carries every non-minimal block system forward, so "
                   "`minimal_blocks()` returns too many systems and `sylow_subgroup(p=2)` "
                   "has the wrong order (F2P asserts S.order()==4) — FAILS the F2P. "
                   "Correct only on the no-flag sub-domain.",
     "rationale": "rejection from the three `filtered` clauses: on any input with a True "
                  "flag the outputs keep len(flag) elements but filtered keeps only the "
                  "False-flagged ones, so out != filtered and `len(Result()[k]) == "
                  "kept(ToSeq(flag))` fails (len(flag) != kept when any flag is True)."},
    {"id": "partial-drop-all", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROPALL,
     "refinement": "a real patch that over-pruned (removed survivors too) discards minimal "
                   "block systems that must remain, again giving `sylow_subgroup(p=2)` the "
                   "wrong order — FAILS the F2P. Cheap supporting case (correct only on "
                   "the all-flag sub-domain) carrying a real refinement.",
     "rationale": "rejection from the three `filtered` clauses: the outputs are always "
                  "empty, but filtered keeps the False-flagged positions, so on any input "
                  "with a surviving position out != filtered and `len(Result()[k]) == "
                  "kept(ToSeq(flag))` fails (0 != kept when any flag is False)."},
]


# ===========================================================================
# AXIOM LANE — NONE.
# ===========================================================================
# `meta.axioms == []` and the model.py `axioms` region is empty: there is NO
# @ContractOnly external callee. The changed prune is modelled DEEPLY by the
# @Pure folds `filtered` / `kept` (A-reference deep models). Their soundness
# (== real Python list-comprehension semantics, with the pre-patch in-place
# deletion confirmed to diverge on >=2-flag inputs) is validated out-of-band by
# axiom_check.py (G-AX), not by a consumed axiom. There is no real library callee
# to run in Docker against an Ensures, so the axiom lane is vacuous here.
AXIOM_TESTS = []
