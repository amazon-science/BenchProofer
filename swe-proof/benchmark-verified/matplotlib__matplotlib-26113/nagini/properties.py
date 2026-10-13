"""properties.py — PBT falsification manifest for matplotlib__matplotlib-26113.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical"). This battery is
reasoned from THIS spec's defended surface, not stamped out by a corruption
template.

The function under spec
-----------------------
    populated_bins(occupancies: List[int], threshold: int) -> List[bool]

models the per-bin populated/cleared decision in `Axes.hexbin`'s value-
aggregation (`C is not None`) branch — the gold one-operator change
`len(acc) > mincnt` -> `len(acc) >= mincnt` (lib/matplotlib/axes/_axes.py:5017).
Each per-hexagon C-value list `acc` is abstracted to its occupancy
`occ = len(acc)` (int); the accum entry (a real reduced value vs `np.nan`,
observed only through `~np.isnan(accum)`) is abstracted to a `bool`
populated-flag. The result is the list of per-bin populated-flags.

MODELED DOMAIN: `Requires(threshold >= 1)` — the documented positive-threshold
regime (the library docstring says `mincnt : int > 0`; the F2P test observes
mincnt=1). At threshold 0 (the unset default) an EMPTY bin passes
`len(acc) >= 0` and the observable populated decision then depends on the
aggregator's value on an empty list (default np.mean -> NaN, cleared; sum ->
0.0, populated) — a payload-dependent effect the occupancy-only abstraction
cannot carry, hence out of the modeled boundary (see model.py docstring /
mapping.md §2a). On threshold >= 1 every kept bin is nonempty and the decision
is exactly the occupancy comparison in both regimes.

The READ-ONLY input — FRAME-MUTATION applies (MANDATORY, directive 5)
---------------------------------------------------------------------
`occupancies` is read-only: Requires(Acc(list_pred(occupancies), 1/2)) and the
postcondition GIVES BACK that half-permission (Ensures(Acc(list_pred(
occupancies), 1/2))). So the frame-mutation attack APPLIES and is MANDATORY: an
impl that WRITES to `occupancies` (e.g. to satisfy a postcondition vacuously)
must be REJECTED for INSUFFICIENT PERMISSION — assigning `occupancies[i] = ...`
needs full Acc(list_pred(occupancies)) but the precondition grants only 1/2.

The load-bearing postcondition clauses (model.py:67-75)
-------------------------------------------------------
  (P1) Acc(list_pred(occupancies), 1/2)              — gives the read perm back
  (P2) Acc(list_pred(Result()))                      — full perm on the result
  (P3) len(Result()) == len(occupancies)             — the length clause
  (P4) Forall k in [0,len): Result()[k] == decision_agg(occupancies[k], t)
                          and Result()[k] == decision_count(occupancies[k], t)
       — the DISCRIMINATING + cross-regime-consistency clause. decision_agg ==
         (occ >= t); decision_count == not(occ < t). The conjunct senses the
         `>` -> `>=` change (model_prepatch's `occ > t` FAILS this at occ == t,
         e.g. occ == t == 1, the headline mincnt=1 witness) AND folds in the
         consistency the F2P test observes (the value-aggregation regime's
         decision must equal the bare-count regime's).

The two @Pure oracles are GROUNDED, not an answer-key
-----------------------------------------------------
`decision_agg(occ, t) == occ >= t` and `decision_count(occ, t) == not (occ < t)`
are TOTAL functions of the args, fully UNFOLDED in the contract (no opaque
answer-key, no marker). The postcondition pins Result()[k] to BOTH. There is
therefore NO ungrounded oracle an impl could echo WITHOUT doing the work —
echoing `decision_agg(occupancies[k], threshold)` IS the correct answer, and any
echo that disagrees with the grounded `occ >= t` / `not(occ < t)` is rejected.
Hence ungrounded-oracle ECHO (directive 2) does NOT apply; instead we supply an
honest cheapest-correct positive control (the `not (occ < t)` decision_count
form, semantically identical to `occ >= t`) which MUST verify. Stated in the
StructuredOutput assessment.

No control-flow / raise / side-effect difference is observable
--------------------------------------------------------------
`populated_bins` is total over its precondition domain (any List[int] / any int
threshold; it never raises and has no side effect other than building the fresh
result list). The real `hexbin` accum comprehension is likewise total (an int
comparison `len(acc) >= mincnt`; `reduce_C_function` runs on the kept bins, NaN
on the rest, both abstracted to a bool). There is no raise/return/side-effect
difference invisible to the value abstraction, so the control-flow-effect class
(directive 4) does NOT apply to this spec. Stated in 'assessment'.

Axiom lane
----------
meta.axioms == [] (NO @ContractOnly axiom — see axioms-start/end in model.py).
The single soundness obligation is the A-reference: the deep model `decision_agg`
== the real `hexbin` value-aggregation decision, and the value-aggregation regime
coincides with the bare-count regime, over the MODELED (occupancy, threshold >= 1)
domain. The AXIOM_TESTS reuse + STRENGTHEN axiom_check.py (which the runner does
NOT mount in-container, so the probes are SELF-CONTAINED, numpy-only):
(1) axiom-soundness drives the REAL numpy accum construction exactly as
`_axes.py:5016-5020` / `5002-5003` compute it — with the library's DEFAULT
aggregator np.mean AND a structurally different finite aggregator (sum) — and
asserts the deep model matches AND the two regimes coincide over boundary + fuzz
on threshold >= 1, incl. the headline mincnt=1 witnesses; it ALSO witnesses that
at the out-of-domain threshold 0 the empty-bin decision is aggregator-dependent
(np.mean -> NaN cleared, sum -> 0.0 populated), i.e. model.py's `threshold >= 1`
precondition is load-bearing; (2) axiom-containment confirms every (occupancy,
threshold) callee-input the MODEL can reach (occ = len(acc) >= 0, threshold >= 1
by the precondition) lies in the real decision's (total) domain.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`) that
edits ONLY text inside `populated_bins`'s `# impl-start` / `# impl-end` body, so
`markers.same_spec` is GUARANTEED (the frozen spec — signature, pre/post, the two
@Pure oracles — is never touched) and a rejection is attributable to the
POSTCONDITION / the permission system, never to a tampered spec. The gold loop
invariants are kept VERBATIM in every variant (directive 2) so a reject is never a
mislabeled proof gap, and the variants keep the lightweight index-Forall shape
(no PSeq theory) so their Z3 phase stays comparable to gold (~32s) under
concurrent-verifier load (meta.verify note). Each `expect:"reject"` rival carries
the refinement argument that its faithful real patch would NOT resolve the F2P.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-26113"
FLOAT_ENCODING = None  # meta.json float_encoding is null (integer comparison only)

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
# Anchors inside populated_bins's impl region (each unique in model.py).
# ---------------------------------------------------------------------------

# The gold loop body (the three statements after `# invariants-end`, building
# `result`). This is the only region we touch; invariants are kept verbatim.
_GOLD_BODY = """        occ = occupancies[i]
        flag = occ >= threshold
        result.append(flag)
        i = i + 1"""

# The impl-start anchor (the first two impl lines) — used to PREPEND the
# admissibility self-call without disturbing the loop.
_IMPL_START_ANCHOR = """    result = []  # type: List[bool]
    i = 0"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) decision_count-FORM positive control. Compute the populated flag as
# `not (occ < threshold)` — the bare-count regime's form (decision_count) —
# instead of `occ >= threshold` (decision_agg). The two are the SAME integer
# relation, so this is a structurally-different but semantically-identical CORRECT
# impl. The gold loop invariant pins result[k] to decision_agg (occ >= t); the
# verifier discharges it from `not (occ < t)` by pure integer reasoning (NO
# induction lemma — directive 3 N/A), and the postcondition's decision_count
# conjunct is then trivially met. If this CORRECT impl fails to verify, the
# postcondition is over-fit to the literal `>=` operator => SPEC-TOO-STRONG.
_POS_NOTLT_BODY = """        occ = occupancies[i]
        flag = not (occ < threshold)
        result.append(flag)
        i = i + 1"""
_POS_NOTLT = _swap(_BASE, _GOLD_BODY, _POS_NOTLT_BODY)

# (5b) LOCAL-RESHAPE positive control. Read the occupancy into a typed local,
# compute the flag via the grounded @Pure oracle `decision_agg` directly (a
# different data shape: oracle call instead of an inline comparison), and append.
# Same behaviour. The invariant — result[k] == decision_agg(occupancies[k], t) —
# is discharged identically (the appended value IS decision_agg(occ, t)). If it
# fails => SPEC-TOO-STRONG (over-fit to the inline-comparison code form).
_POS_LOCAL_BODY = """        occ = occupancies[i]
        flag = decision_agg(occ, threshold)
        result.append(flag)
        i = i + 1"""
_POS_LOCAL = _swap(_BASE, _GOLD_BODY, _POS_LOCAL_BODY)

# (6) ADMISSIBILITY. A self-call on the in-scope F2P-shaped input must establish
# the precondition (a List[int] under half-permission + an int threshold). We
# prepend the call BEFORE the loop, on the SAME in-scope inputs (occupancies,
# threshold). The caller holds Acc(list_pred(occupancies), 1/2) — EXACTLY the
# callee's Requires; the self-call consumes that half-permission and the callee's
# Ensures GIVES IT BACK, so the subsequent loop runs unchanged with the perm it
# still holds. We Assert the probe's length to pin that the call site succeeded.
# If the call site cannot establish the Requires for a legitimate input =>
# PRECOND-TOO-STRONG.
_ADMISS_PREFIX = (
    "    _probe = populated_bins(occupancies, threshold)\n"
    "    Assert(len(_probe) == len(occupancies))\n"
    + _IMPL_START_ANCHOR
)
_ADMISS = _swap(_BASE, _IMPL_START_ANCHOR, _ADMISS_PREFIX)


# ===========================================================================
# UNIQUENESS / FRAME-MUTATION RIVALS (must be REJECTED)
# ===========================================================================

# (FRAME-MUTATION — MANDATORY, directive 5) The rival WRITES to the read-only
# input `occupancies[i]` (clamping the occupancy up to the threshold so the
# subsequent `occ >= threshold` is vacuously satisfiable) before reading it back.
# To assign `occupancies[i] = ...` Nagini needs FULL permission on `occupancies`,
# but the precondition grants only Acc(list_pred(occupancies), 1/2). The write is
# therefore REJECTED for INSUFFICIENT PERMISSION — before any postcondition is even
# considered. The gold invariants/structure are kept VERBATIM so the rejection is
# attributable solely to the write.
#
# Refinement (why its faithful real patch would NOT resolve): the read-only
# half-permission abstracts the gold patch's contract that the accum comprehension
# READS each hexagon's accumulated C-value list `acc` (through `len(acc)`) and the
# resolved `mincnt`, and leaves the per-hexagon point lists untouched (the kept/
# cleared decision goes into a FRESH `accum` array — mapping.md §A4). A real
# "patch" that mutated the per-hexagon accumulation lists in place (e.g. clamped or
# padded an `acc` so a sparse bin counts as populated) would CHANGE which bins
# survive `~np.isnan(accum)` AND corrupt the aggregated value `reduce_C_function(
# acc)` for that bin — rendering a hexbin that differs from both the bare-count
# regime and the user's intent, so the F2P
# test_hexbin_mincnt_behavior_upon_C_parameter[png] (C-given == C-absent at
# mincnt=1) would FAIL. It would NOT resolve. The half-permission is exactly the
# spec defending that read-only contract.
_RIVAL_FRAME_MUTATE_BODY = """        occ = occupancies[i]
        if occ < threshold:
            occupancies[i] = threshold
        flag = occupancies[i] >= threshold
        result.append(flag)
        i = i + 1"""
_RIVAL_FRAME_MUTATE = _swap(_BASE, _GOLD_BODY, _RIVAL_FRAME_MUTATE_BODY)

# (uniqueness — PRE-PATCH bug, the strict `>`) The rival uses the pre-patch
# comparison `occ > threshold` — exactly model_prepatch.py. It satisfies P1/P2/P3
# and the length invariant, but VIOLATES the per-element loop invariant /
# postcondition conjunct at the boundary occ == threshold (e.g. occ == threshold
# == 1: gold says populated (True), `>` says cleared (False)).
#
# Refinement: this IS the pre-patch behaviour. Its faithful real patch is the
# unmodified `len(acc) > mincnt`, under which the C-given hexbin with mincnt=1
# keeps only bins with count >= 2 while the C-absent hexbin keeps count >= 1, so
# the F2P test_hexbin_mincnt_behavior_upon_C_parameter[png] (which renders the two
# identically) FAILS. It would NOT resolve (this is exactly the bug the patch
# fixes, G-DIFF; model_prepatch.py reproduces it and fails verification).
_RIVAL_PREPATCH_BODY = """        occ = occupancies[i]
        flag = occ > threshold
        result.append(flag)
        i = i + 1"""
_RIVAL_PREPATCH = _swap(_BASE, _GOLD_BODY, _RIVAL_PREPATCH_BODY)

# (uniqueness — OVER-INCLUSIVE off-by-one, the other direction) The rival keeps
# one bin too MANY: `occ >= threshold - 1` (equivalently `occ > threshold - 2`),
# so a bin with occ == threshold - 1 is wrongly populated. It satisfies P1/P2/P3
# but violates P4 at occ == threshold - 1 (gold: cleared / False; rival:
# populated / True), for any threshold >= 1.
#
# Refinement: its faithful real patch is the comparison `len(acc) >= mincnt - 1`
# (an over-relaxed threshold). With mincnt=2 it would keep count==1 bins that the
# bare-count regime (count >= 2) clears, so the C-given and C-absent hexbins
# DIFFER and the F2P consistency assertion FAILS; more generally it populates bins
# the bare-count regime clears at every threshold >= 1. It would NOT resolve.
# Rejection source: P4's decision_agg conjunct (occ >= t) at occ == t-1.
_RIVAL_OFF_BY_ONE_BODY = """        occ = occupancies[i]
        flag = occ >= threshold - 1
        result.append(flag)
        i = i + 1"""
_RIVAL_OFF_BY_ONE = _swap(_BASE, _GOLD_BODY, _RIVAL_OFF_BY_ONE_BODY)

# (uniqueness — CONSTANT, ignores occupancy entirely) The rival marks EVERY bin
# populated (flag = True), independent of occupancy and threshold. It satisfies
# P1/P2/P3 but violates P4 on any cleared bin (occ < threshold; e.g. an empty bin
# occ == 0 with threshold == 1 must be False).
#
# Refinement: its faithful real patch drops the comparison entirely (always emit
# `reduce_C_function(acc)`, never `np.nan`). Then `~np.isnan(accum)` keeps EVERY
# hexagon — including the empty out-of-data bins the `[1:]` slice and mincnt are
# meant to drop — so the C-given hexbin shows spurious populated hexagons the
# C-absent (count >= 1) hexbin does not. The F2P
# test_hexbin_mincnt_behavior_upon_C_parameter[png] FAILS. It would NOT resolve.
# Rejection source: P4 (Result()[k] == decision_agg/decision_count) on the
# occ < threshold sub-domain.
_RIVAL_CONST_TRUE_BODY = """        occ = occupancies[i]
        flag = True
        result.append(flag)
        i = i + 1"""
_RIVAL_CONST_TRUE = _swap(_BASE, _GOLD_BODY, _RIVAL_CONST_TRUE_BODY)

# (uniqueness — PARTIAL-DOMAIN, first element) The rival is CORRECT on every bin
# except index 0, for which it uses the pre-patch strict `>` (clearing an occ == t
# first bin that should be populated). It diverges ONLY on the first-bin
# sub-domain — the kind of bug a fuzzer that only checks "most" elements misses.
#
# Refinement: its faithful real patch special-cases the first hexagon of the accum
# comprehension (e.g. `acc0` handled by the old `> mincnt`, the rest by `>=`).
# Under it the first hexagon with count == mincnt == 1 is dropped from the C-given
# render but kept in the C-absent render, so the F2P consistency
# test_hexbin_mincnt_behavior_upon_C_parameter[png] FAILS at that hexagon. It would
# NOT resolve. Rejection source: P4 at k == 0 when occupancies[0] == threshold.
_RIVAL_PARTIAL_FIRST_BODY = """        occ = occupancies[i]
        if i == 0:
            flag = occ > threshold
        else:
            flag = occ >= threshold
        result.append(flag)
        i = i + 1"""
_RIVAL_PARTIAL_FIRST = _swap(_BASE, _GOLD_BODY, _RIVAL_PARTIAL_FIRST_BODY)

# (uniqueness — PARTIAL-DOMAIN, length / drop the last bin) The rival resolves
# every emitted bin correctly but DROPS the final bin (the loop appends only while
# i + 1 < len), producing a result one element short. It meets P4 element-wise on
# the indices it DOES emit but violates P3 (len(Result()) == len(occupancies)).
#
# Refinement: its faithful real patch is an accum comprehension that omits the last
# hexagon (an off-by-one over the per-hexagon lists, e.g. `for acc in
# Cs_at_i[1:-1]`). The rendered hexbin is missing the final hexagon's cell, so the
# F2P/P2P image comparisons (the rendered figure must match the C-absent figure
# pixel-for-pixel) FAIL. It would NOT resolve. Rejection source: P3
# (len(Result()) == len(occupancies)) — the loop-exit invariant len(result) == i
# with i == len(occupancies) cannot hold when the last index is skipped.
_RIVAL_DROP_LAST_BODY = """        if i + 1 < len(occupancies):
            occ = occupancies[i]
            flag = occ >= threshold
            result.append(flag)
        i = i + 1"""
_RIVAL_DROP_LAST = _swap(_BASE, _GOLD_BODY, _RIVAL_DROP_LAST_BODY)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-decision-count-form", "kind": "soundness", "expect": "verify",
     "module": _POS_NOTLT,
     "rationale": "structurally-different but CORRECT impl computing the populated flag "
                  "as `not (occ < threshold)` (the decision_count form) instead of "
                  "`occ >= threshold` (decision_agg); the two are the same integer relation. "
                  "Gold loop invariants kept verbatim; the invariant result[k] == "
                  "decision_agg(occupancies[k], t) is discharged by pure integer reasoning "
                  "(no induction lemma). If this CORRECT impl fails to verify, the "
                  "postcondition is over-fit to the literal `>=` operator => SPEC-TOO-STRONG."},
    {"id": "pos-oracle-local-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_LOCAL,
     "rationale": "structurally-different but CORRECT impl: read occ into a local and "
                  "compute the flag via the grounded @Pure oracle decision_agg(occ, threshold) "
                  "directly (oracle call instead of an inline comparison), then append. "
                  "Invariants verbatim. Must verify, else the spec is over-fit to the "
                  "inline-comparison code form => SPEC-TOO-STRONG."},
    {"id": "admiss-selfcall", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "a self-call populated_bins(occupancies, threshold) on the in-scope "
                  "F2P-shaped input (a List[int] under the half-permission the caller holds "
                  "and the callee Ensures back, plus an int threshold) must establish the "
                  "precondition and return a len(occupancies)-long list; if the call site "
                  "cannot establish the Requires for a legitimate input => PRECOND-TOO-STRONG."},

    # ---- frame-mutation (MANDATORY) + uniqueness rivals (must be REJECTED) ----
    {"id": "rival-frame-mutate-occupancies", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_MUTATE,
     "refinement": "WRITES to the read-only input occupancies[i] (clamping a sparse bin's "
                   "occupancy up to the threshold) then reads it back to satisfy the "
                   "comparison vacuously. The half-permission Acc(list_pred(occupancies), 1/2) "
                   "abstracts the gold contract that the accum comprehension READS each "
                   "hexagon's C-value list through len(acc) and builds a FRESH accum array "
                   "(mapping.md §A4) — it never mutates the per-hexagon point lists. A real "
                   "patch that clamped/padded an `acc` in place would change which bins survive "
                   "~np.isnan(accum) AND corrupt reduce_C_function(acc) for that bin, so the "
                   "C-given hexbin would differ from the C-absent hexbin and the F2P "
                   "test_hexbin_mincnt_behavior_upon_C_parameter[png] would FAIL — it would NOT "
                   "resolve.",
     "rationale": "FRAME-MUTATION (directive 5). Rejection source: the PERMISSION SYSTEM — "
                  "assigning occupancies[i] needs full Acc(list_pred(occupancies)) but the "
                  "precondition grants only 1/2, so the write fails for INSUFFICIENT PERMISSION "
                  "before any postcondition is considered. If it verified, a mutating impl "
                  "could satisfy the postcondition vacuously => SPEC-TOO-WEAK."},
    {"id": "rival-prepatch-strict-gt", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PREPATCH,
     "refinement": "uses the pre-patch strict comparison occ > threshold — exactly "
                   "model_prepatch.py. Its faithful real patch is the unmodified "
                   "`len(acc) > mincnt`, under which the C-given hexbin with mincnt=1 keeps "
                   "only count>=2 bins while the C-absent hexbin keeps count>=1, so the F2P "
                   "test_hexbin_mincnt_behavior_upon_C_parameter[png] (which renders the two "
                   "identically) FAILS. It would NOT resolve (this is the bug the patch fixes, "
                   "G-DIFF; model_prepatch.py reproduces it and fails verification).",
     "rationale": "Rejection source: the DISCRIMINATING postcondition conjunct P4 "
                  "Result()[k] == decision_agg(occupancies[k], threshold) "
                  "(== occ >= t) and == decision_count(...) (model.py:72-75), violated at the "
                  "boundary occ == threshold (e.g. occ == threshold == 1): gold True, `>` "
                  "False. If it verified => SPEC-TOO-WEAK (admits the pre-patch off-by-one)."},
    {"id": "rival-off-by-one-over-inclusive", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OFF_BY_ONE,
     "refinement": "keeps one bin too MANY (occ >= threshold - 1), the opposite-direction "
                   "off-by-one from the pre-patch bug. Its faithful real patch is "
                   "`len(acc) >= mincnt - 1` (an over-relaxed threshold); with mincnt=2 it "
                   "populates count==1 bins the bare-count regime (count>=2) clears, so the "
                   "C-given and C-absent hexbins DIFFER and the F2P consistency assertion "
                   "FAILS. It would NOT resolve. Rejection source: P4's decision_agg conjunct "
                   "(occ >= t) at occ == t-1 (gold False, rival True).",
     "rationale": "Rejection source: postcondition conjunct P4 Result()[k] == "
                  "decision_agg(occupancies[k], threshold) (occ >= t), violated on the "
                  "occ == threshold-1 sub-domain for any threshold >= 1. If it verified => "
                  "SPEC-TOO-WEAK (admits an over-inclusive threshold)."},
    {"id": "rival-constant-true", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_CONST_TRUE,
     "refinement": "marks EVERY bin populated (flag = True), ignoring occupancy and threshold. "
                   "Its faithful real patch drops the comparison entirely (always emit "
                   "reduce_C_function(acc), never np.nan), so ~np.isnan(accum) keeps every "
                   "hexagon — including the empty out-of-data bins mincnt is meant to drop — and "
                   "the C-given hexbin shows spurious hexagons the C-absent (count>=1) hexbin "
                   "does not. The F2P test_hexbin_mincnt_behavior_upon_C_parameter[png] FAILS. "
                   "It would NOT resolve.",
     "rationale": "Rejection source: postcondition conjunct P4 (Result()[k] == "
                  "decision_agg / decision_count, model.py:72-75), violated on every cleared "
                  "bin (occ < threshold; e.g. occ==0, threshold==1 must be False). If it "
                  "verified => SPEC-TOO-WEAK (a constant impl satisfies the postcondition "
                  "vacuously)."},
    {"id": "rival-partial-first-bin", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_FIRST,
     "refinement": "PARTIAL-DOMAIN (first element): correct on every bin except index 0, for "
                   "which it uses the pre-patch strict `>` (clearing an occ==threshold first "
                   "bin that should be populated). Its faithful real patch special-cases the "
                   "first hexagon of the accum comprehension (first via old `> mincnt`, the "
                   "rest via `>=`); the first count==mincnt==1 hexagon is dropped from the "
                   "C-given render but kept in the C-absent render, so the F2P consistency "
                   "test FAILS at that hexagon. It would NOT resolve.",
     "rationale": "partial-domain on the k==0 sub-domain. Rejection source: P4 at k==0 when "
                  "occupancies[0] == threshold (Result()[0] == decision_agg(occupancies[0], "
                  "threshold), model.py:72-75). If it verified => SPEC-TOO-WEAK (drops the "
                  "first bin's decision)."},
    {"id": "rival-drop-last-bin", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_LAST,
     "refinement": "PARTIAL-DOMAIN (length): resolves every emitted bin correctly but DROPS "
                   "the final bin, returning a list one element short. Its faithful real patch "
                   "is an accum comprehension that omits the last hexagon (off-by-one over the "
                   "per-hexagon lists, e.g. Cs_at_i[1:-1]); the rendered hexbin is missing the "
                   "final hexagon's cell, so the F2P/P2P image comparison FAILS. It would NOT "
                   "resolve. Rejection source: P3 len(Result()) == len(occupancies) "
                   "(model.py:69).",
     "rationale": "Rejection source: P3 len(Result()) == len(occupancies) (model.py:69) — the "
                  "loop-exit invariant len(result) == i with i == len(occupancies) cannot hold "
                  "when the last index is skipped. If it verified => SPEC-TOO-WEAK (length not "
                  "pinned)."},
]


# ===========================================================================
# AXIOM LANE (Docker, real numpy callee) — the A-reference soundness +
# containment obligation. meta.axioms == [] (NO @ContractOnly axiom); the single
# soundness obligation is the deep model decision_agg == the real hexbin
# value-aggregation decision, and the value-aggregation regime coincides with the
# bare-count regime. These reuse + STRENGTHEN axiom_check.py (which the runner does
# NOT mount in-container, so the probes are SELF-CONTAINED, numpy-only). The
# decision is an integer comparison; numpy is present in every matplotlib image
# (the library hexbin itself depends on it). apply_gold is irrelevant to the
# decision logic (we reproduce both the pre/post comparison here), but the model
# describes POST-gold behaviour, so apply_gold=True to be faithful to PLAN §4.
# ===========================================================================

# (axiom-soundness) Reproduce the REAL hexbin accum decision exactly as
# lib/matplotlib/axes/_axes.py:5016-5020 (value-aggregation, `C is not None`) and
# :5002-5003 (bare-count, `C is None`) compute it, with numpy, and assert:
#   (a) the deep model decision_agg(occ, t) == occ >= t == the real
#       value-aggregation populated decision (read back via ~np.isnan(accum), the
#       very mask hexbin applies at good_idxs = ~np.isnan(accum)) — with the
#       library's DEFAULT aggregator np.mean AND a structurally different finite
#       aggregator (sum), pinning aggregator-independence on the modeled domain,
#   (b) the value-aggregation decision == the bare-count decision for every
#       (occupancy, threshold >= 1) (the consistency the postcondition Forall
#       encodes and the F2P test observes), and
#   (c) OUT-OF-DOMAIN witness: at threshold 0 the empty-bin decision IS
#       aggregator-dependent (np.mean -> NaN cleared; sum -> 0.0 populated; the
#       bare-count regime keeps it), i.e. model.py's `threshold >= 1`
#       precondition is load-bearing, not cosmetic,
# over boundary thresholds/occupancies + 20000 randomized fuzz + the headline
# mincnt=1 witnesses, all on the MODELED domain threshold >= 1. Exit 0 iff every
# obligation holds. Any mismatch => the A-reference deep model is UNSOUND.
# Self-contained (numpy + stdlib only); no file reads (no codec concern).
_AX_SOUNDNESS = r'''
import random
import sys
import warnings

try:
    import numpy as np
except ImportError as exc:
    print("AXIOM probe: numpy not importable (%r) — must run in the instance image"
          % (exc,))
    sys.exit(1)


def decision_agg(occ, t):
    """model.py pure decision_agg: value-aggregation regime, populated iff occ>=t."""
    return occ >= t


def decision_count(occ, t):
    """model.py pure decision_count: bare-count regime, populated iff not(occ<t)."""
    return not (occ < t)


def real_agg_populated(occ, mincnt, reduce_C_function=np.mean):
    """REAL value-aggregation (C is not None) accum decision for one bin, exactly
    as the post-patch source: reduce_C_function(acc) if len(acc) >= mincnt else
    np.nan, then good_idxs = ~np.isnan(accum) decides which bins survive.
    Default aggregator = the library's default, np.mean."""
    acc = [1.0] * occ                       # a concrete C-value list of length occ
    if mincnt is None:
        mincnt = 0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")     # np.mean([]) warns and yields NaN
        accum = np.array(
            [reduce_C_function(acc) if len(acc) >= mincnt else np.nan], float)
    good = ~np.isnan(accum)
    return bool(good[0])


def real_count_populated(occ, mincnt):
    """REAL bare-count (C is None) accum decision for one bin, exactly as the
    source: the bin count goes into accum, then if mincnt is not None:
    accum[accum < mincnt] = np.nan; the bin survives iff it is not NaN."""
    accum = np.array([occ], float)
    if mincnt is not None:
        accum[accum < mincnt] = np.nan
    good = ~np.isnan(accum)
    return bool(good[0])


def check(occ, t):
    model_agg = bool(decision_agg(occ, t))
    for red, red_name in ((np.mean, "np.mean (default)"), (sum, "sum")):
        real_agg = real_agg_populated(occ, t, red)
        if model_agg != real_agg:
            print("AXIOM-UNSOUND: decision_agg deep model != real hexbin "
                  "value-aggregation decision at occ=%r mincnt=%r "
                  "(reduce_C_function=%s): model=%r real=%r"
                  % (occ, t, red_name, model_agg, real_agg))
            return False
    real_cnt = real_count_populated(occ, t)
    if model_agg != real_cnt:
        print("AXIOM-UNSOUND (regime inconsistency): value-aggregation populated=%r but "
              "bare-count populated=%r at occ=%r mincnt=%r" % (model_agg, real_cnt, occ, t))
        return False
    if bool(decision_count(occ, t)) != real_cnt:
        print("AXIOM-UNSOUND: decision_count deep model != real bare-count decision at "
              "occ=%r mincnt=%r" % (occ, t))
        return False
    return True


def main():
    # MODELED domain: threshold >= 1 (model.py Requires; docstring `mincnt: int > 0`)
    boundary_occ = [0, 1, 2, 3, 5, 10]
    boundary_t = [1, 2, 3, 5, 10]
    n_boundary = 0
    for t in boundary_t:
        for occ in boundary_occ:
            if not check(occ, t):
                return 1
            n_boundary += 1

    # headline witness: mincnt=1 keeps count>=1 in BOTH regimes (the issue's case)
    if real_agg_populated(1, 1) is not True or real_count_populated(1, 1) is not True:
        print("AXIOM-UNSOUND: mincnt=1 must keep an occ=1 bin in both regimes")
        return 1
    if real_agg_populated(0, 1) is not False or real_count_populated(0, 1) is not False:
        print("AXIOM-UNSOUND: mincnt=1 must clear an occ=0 bin in both regimes")
        return 1

    rng = random.Random(26113)
    for _ in range(20000):
        occ = rng.randint(0, 50)
        t = rng.randint(1, 50)
        if not check(occ, t):
            return 1

    # OUT-OF-DOMAIN boundary witness (threshold 0 / unset default): the empty-bin
    # decision is aggregator-dependent — the default np.mean clears it (NaN), sum
    # keeps it (0.0), the bare-count regime keeps it — so the occupancy-only
    # abstraction genuinely cannot cover threshold 0; model.py's `threshold >= 1`
    # precondition is load-bearing.
    if real_agg_populated(0, 0, np.mean) is not False:
        print("AXIOM-UNSOUND: expected default-aggregator empty bin CLEARED at mincnt=0")
        return 1
    if real_agg_populated(0, 0, sum) is not True:
        print("AXIOM-UNSOUND: expected sum-aggregator empty bin POPULATED at mincnt=0")
        return 1
    if real_count_populated(0, 0) is not True or real_count_populated(0, None) is not True:
        print("AXIOM-UNSOUND: bare-count must keep an empty bin at mincnt=0/None")
        return 1
    # nonempty bins agree with the model even at mincnt=0 (finite aggregate):
    for occ in (1, 2, 5):
        if real_agg_populated(occ, 0) is not True or real_count_populated(occ, 0) is not True:
            print("AXIOM-UNSOUND: nonempty bin at mincnt=0 must be populated (occ=%r)" % occ)
            return 1

    print("AXIOM-SOUND: decision_agg deep model == real hexbin value-aggregation decision "
          "(np.mean default AND sum aggregators), decision_count == real bare-count "
          "decision, and the two regimes coincide, over %d boundary + 20000 fuzz "
          "(occupancy, mincnt) pairs on the modeled domain mincnt >= 1 incl. mincnt=1 "
          "witnesses; mincnt=0 empty-bin aggregator dependence confirmed OUT of domain "
          "(precondition threshold >= 1 is load-bearing)." % n_boundary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

# (axiom-containment) Every (occupancy, threshold) callee-input the MODEL can
# REACH lies in the real decision's domain. The model's Requires admits ANY
# List[int] occupancies (each element any int) and any int threshold >= 1 (the
# `Requires(threshold >= 1)` modeled boundary); in practice the modeled callee —
# the accum comprehension — only ever sees occ = len(acc) >= 0 (a list length,
# NONNEGATIVE) and mincnt a positive int (the documented `mincnt: int > 0`
# regime). The real decision (an int comparison fed to np.array(..., float) /
# ~np.isnan) is TOTAL on all of these — it never raises and is well-defined for
# every (occ, mincnt) the model can produce; on the modeled domain every kept
# bin is nonempty so its aggregate (np.mean of a nonempty finite list) is a real
# value. We enumerate the reachable boundary witnesses (occ in
# {0,1,t-1,t,t+1,t+2}, t in {1,2,3}) and confirm the real decision evaluates
# without error and matches the model — i.e. every caller-reachable input is
# INSIDE the callee domain. Covering negative occupancies (a list length is
# never negative) or thresholds < 1 (excluded by the precondition — the
# documented regime is mincnt > 0, and threshold 0's empty-bin decision is
# aggregator-dependent, see axiom-soundness) is not required; the model never
# reaches them. A reachable input the real decision could not handle =>
# AXIOM-TOO-WEAK-FOR-CALLER.
_AX_CONTAINMENT = r'''
import sys

try:
    import numpy as np
except ImportError as exc:
    print("CONTAINMENT probe: numpy not importable (%r) — must run in image" % (exc,))
    sys.exit(1)


def real_agg_populated(occ, mincnt, reduce_C_function=np.mean):
    acc = [1.0] * occ
    if mincnt is None:
        mincnt = 0
    accum = np.array(
        [reduce_C_function(acc) if len(acc) >= mincnt else np.nan], float)
    return bool((~np.isnan(accum))[0])


def real_count_populated(occ, mincnt):
    accum = np.array([occ], float)
    if mincnt is not None:
        accum[accum < mincnt] = np.nan
    return bool((~np.isnan(accum))[0])


def main():
    # reachable callee-inputs: occ = len(acc) is NONNEGATIVE; threshold (mincnt)
    # is a POSITIVE int (model.py Requires(threshold >= 1), matching the
    # documented `mincnt: int > 0` regime). Boundary witnesses around the
    # comparison.
    reachable = []
    for t in [1, 2, 3]:
        for occ in sorted({0, 1, t - 1, t, t + 1, t + 2}):
            if occ < 0:
                continue            # a list length is never negative — not reachable
            reachable.append((occ, t))

    checked = 0
    for occ, t in reachable:
        try:
            a_mean = real_agg_populated(occ, t, np.mean)
            a_sum = real_agg_populated(occ, t, sum)
            c = real_count_populated(occ, t)
        except Exception as exc:
            print("AXIOM-TOO-WEAK-FOR-CALLER: reachable model callee-input "
                  "(occ=%r mincnt=%r) is OUTSIDE the real decision domain (raised %r)"
                  % (occ, t, exc))
            return 1
        # and the model agrees on every reachable input (containment + agreement)
        if a_mean != (occ >= t) or a_sum != (occ >= t) or c != (not (occ < t)):
            print("AXIOM-TOO-WEAK-FOR-CALLER (or unsound): reachable input "
                  "(occ=%r mincnt=%r) -> real agg(mean)=%r agg(sum)=%r count=%r != model"
                  % (occ, t, a_mean, a_sum, c))
            return 1
        checked += 1

    print("CONTAINMENT OK: every reachable model callee-input (occ = len(acc) >= 0, "
          "mincnt a positive int per the Requires(threshold >= 1) modeled boundary) "
          "lies in the real hexbin decision's (total) domain and the deep model agrees "
          "there (%d witnesses incl. comparison boundaries, np.mean and sum "
          "aggregators). Negative occupancies are unreachable (a list length is never "
          "negative) and thresholds < 1 are excluded by the precondition (documented "
          "regime is mincnt > 0; threshold 0's empty-bin decision is aggregator-"
          "dependent — see axiom-soundness), so not covering them is sound, not a "
          "defect." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

AXIOM_TESTS = [
    {"id": "ax-decision-agg-sound", "axiom": "decision_agg_deep_model",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_SOUNDNESS,
     "rationale": "the bundle's single soundness obligation: the deep model decision_agg "
                  "(occ >= t) must equal the REAL hexbin value-aggregation accum decision "
                  "(len(acc) >= mincnt with the DEFAULT reduce_C_function=np.mean AND with sum, "
                  "read back via ~np.isnan(accum)) AND coincide with the bare-count regime "
                  "decision (accum[accum < mincnt] = np.nan), over boundary + 20000 fuzz "
                  "(occupancy, mincnt) pairs on the MODELED domain mincnt >= 1 incl. the "
                  "headline mincnt=1 witnesses; plus the out-of-domain mincnt=0 witness that "
                  "the empty-bin decision is aggregator-dependent (np.mean NaN vs sum 0.0), "
                  "justifying the Requires(threshold >= 1) boundary. The model describes "
                  "POST-gold behaviour, so apply_gold=True. Any mismatch => the A-reference "
                  "is UNSOUND (AXIOM-UNSOUND)."},
    {"id": "ax-decision-agg-containment", "axiom": "decision_agg_deep_model",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _AX_CONTAINMENT,
     "rationale": "every (occupancy, threshold) the model can reach (occ = len(acc) >= 0; "
                  "mincnt a positive int per the Requires(threshold >= 1) modeled boundary) "
                  "lies in the real hexbin decision's total domain and the deep model agrees "
                  "there (np.mean and sum aggregators). Negative occupancies are unreachable "
                  "(a list length is never negative) and thresholds < 1 are excluded by the "
                  "precondition (documented regime mincnt > 0; threshold 0's empty-bin "
                  "decision is aggregator-dependent), so not covering them is SOUND "
                  "over-restriction, not AXIOM-TOO-WEAK-FOR-CALLER."},
]
