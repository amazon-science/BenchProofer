"""properties.py — PBT falsification manifest for matplotlib__matplotlib-24177.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template.

The function under spec
-----------------------
    enclosing_upper_bound(verts: List[int]) -> int

models the gold patch's single hunk in `_AxesBase._update_patch_limits`
(`lib/matplotlib/axes/_base.py:2437`): the per-segment vertex gather changes from
`p.iter_bezier()` (default `simplify=None` -> appearance-preserving condensation
that can DROP an interior extreme) to `p.iter_bezier(simplify=False)` (gathers
EVERY vertex). The gathered max/min then sizes the autoscaled data limit. The
model abstracts one axis of the gather to `List[int]` and returns the enclosing
upper end (the per-axis maximum); the lower bound is symmetric (negate).

The READ-ONLY input + the load-bearing postcondition (model.py:121-134)
-----------------------------------------------------------------------
  Requires(Acc(list_pred(verts), 1/2))   <- READ-ONLY (half permission)
  Requires(len(verts) >= 1)
  Ensures (Acc(list_pred(verts), 1/2))    <- gives the half-permission back
  (P_dom) Forall k in [0,len): Result() >= verts[k]     ENCLOSING / dominance
  (P_att) Exists j in [0,len): Result() == verts[j]      ATTAINED / tightness

`verts` is read-only (`Acc(list_pred(verts), 1/2)` in both Requires and Ensures),
so the FRAME-MUTATION attack (directive 5) APPLIES and is MANDATORY: a rival that
WRITES to `verts` (e.g. to flatten the array so a stale bound trivially
dominates) must be REJECTED for INSUFFICIENT PERMISSION, before any postcondition
is considered.

(P_dom) is the discriminating clause: it is exactly what `model_prepatch.py`
(the gather-over-condensation regression) FAILS — the membership-only
condensation cannot cover a dropped extreme, so `Result() >= verts[k]` is
unprovable for the dropped k (meta.json G-DIFF). (P_att) is the tightness clause
that pins the bound to a real datum, excluding any `max + padding`
over-approximation.

The @Pure helper `seq_max` is GROUNDED, not an answer-key oracle
----------------------------------------------------------------
The postcondition is NOT pinned to an opaque oracle. `seq_max(s)` is a TOTAL
front-recursive fold fully unfolded in the contract (`s[0]` if len==1 else
`_imax(s[0], seq_max(s.drop(1)))`); it IS the maximum of the input sequence.
`enclosing_upper_bound`'s postcondition references only `Result()` and `verts[k]`
(not `seq_max` directly), and the impl proves it via the two verified lemmas
`lemma_seq_max_dominates` (dominance) and `lemma_seq_max_attained` (attained).
Echoing `return seq_max(ToSeq(verts))` therefore IS the correct answer — there is
NO wrong echo of an ungrounded oracle. Hence ungrounded-oracle ECHO (directive 2)
does NOT apply; instead we supply the honest cheapest-correct positive control
(`return seq_max(ToSeq(verts))` after the two lemma calls) which MUST verify.
Stated in the StructuredOutput assessment.

No control-flow / raise / side-effect difference is observable
--------------------------------------------------------------
`enclosing_upper_bound` is TOTAL over its precondition domain (`len(verts) >= 1`):
it always returns an int, never raises, and has no side effect (the input is
read-only). The real gather likewise has no raise path on the F2P/P2P domain (a
non-empty step-outline path). The value abstraction (the returned int) fully
captures the behaviour, so there is no capability-token discriminator to build.
The control-flow-effect class therefore does NOT apply to this instance; stated
in 'assessment'.

Axiom lane
----------
meta.axioms = [subsel_len, subsel_at] (two @ContractOnly axioms, kind A-consumed)
+ one A-reference deep model `seq_max`. CRUCIAL: the two @ContractOnly axioms are
consumed ONLY by `model_prepatch.py` (the pre-patch gather over the condensation);
the POST-patch `enclosing_upper_bound` impl folds over ALL of `verts` and never
calls them. The single soundness obligation the verified model relies on is the
A-reference: the deep `seq_max` model == the real full gather
(`Path.iter_bezier(simplify=False)`) max. The AXIOM_TESTS REUSE + strengthen
axiom_check.py (which the runner does NOT mount in-container, so the probe is
SELF-CONTAINED: axiom_check.py's source is read on the HOST at manifest-load time
and embedded into the probe string):
 (1) axiom-soundness drives the GENUINE matplotlib `Path.iter_bezier` on the
     boundary outlines, the EXACT F2P regression fixture, and 4000 fuzz outlines,
     asserting (a) the condensed gather's MEMBERSHIP + count bound (the A-consumed
     subsel_*), (b) the full gather encloses every vertex (the A-reference
     seq_max), (c) the discriminating witness (the condensation drops the
     interior y-extreme while the full gather captures it).
 (2) axiom-containment confirms every callee-input the MODEL can reach (the model
     only ever folds the max over the FULL non-empty gather — len(verts) >= 1 ->
     seq_max's Requires len(s) >= 1; the prepatch's subsel_at indices all lie in
     [0, subsel_len) by construction) lies in the callee's domain.
The callee `Path.iter_bezier` is UNCHANGED by the gold patch (the patch only
flips a keyword at the call site in `_base.py`), so apply_gold=False.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`) that
edits ONLY text inside `enclosing_upper_bound`'s `# impl-start` / `# impl-end`
body, so `markers.same_spec` is GUARANTEED and a rejection is attributable to the
POSTCONDITION / the permission system, never to a tampered spec. The two lemmas'
own impl regions are NOT touched (their Ensures are frozen spec; editing them
would only create a proof gap, not test the spec). Each `expect:"reject"` rival
carries the refinement argument that its faithful real patch would NOT resolve
the F2P (`test_small_autoscale`).
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24177"
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
# Anchors inside enclosing_upper_bound's impl region (each unique in model.py).
# ---------------------------------------------------------------------------

# The ENTIRE gold impl body (between # impl-start and # impl-end). Used for
# whole-body rivals whose wrong return value makes the loop / framing asserts
# irrelevant (they are replaced wholesale so a rejection is never a mislabeled
# dangling-reference translation error).
_GOLD_FULL_BODY = """    # impl-start
    lemma_seq_max_dominates(ToSeq(verts))
    best = verts[len(verts) - 1]
    i = len(verts) - 1
    sq = ToSeq(verts)  # type: PSeq[int]
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(verts), 1 / 2))
        Invariant(0 <= i and i < len(verts))
        Invariant(best == seq_max(ToSeq(verts).drop(i)))
        # Carries the element count across the scan, so the enclosing method's
        # own measure is still known once the scan is done and the lemmas below
        # can still be applied.
        Invariant(sq == ToSeq(verts))
        # The scan counts down to 0, so i + 1 stays positive and strictly
        # decreases each step.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(verts).drop(i - 1)[0] == verts[i - 1])
        Assert(ToSeq(verts).drop(i - 1).drop(1) == ToSeq(verts).drop(i))
        if verts[i - 1] > best:
            best = verts[i - 1]
        i = i - 1
    Assert(i == 0)
    Assert(ToSeq(verts).drop(0) == ToSeq(verts))
    Assert(best == seq_max(ToSeq(verts)))
    lemma_seq_max_dominates(ToSeq(verts))
    lemma_seq_max_attained(ToSeq(verts))
    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
                                          seq_max(ToSeq(verts)) >= ToSeq(verts)[k]))))
    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
                                          ToSeq(verts)[k] == verts[k]))))
    return best
    # impl-end"""

# The gold loop comparison step (unique inside the impl region) — for the
# value-mask rival that keeps the whole loop scaffold + framing asserts.
_GOLD_CMP_STEP = """        if verts[i - 1] > best:
            best = verts[i - 1]
        i = i - 1"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) STRUCTURAL positive control: drop the explicit loop and return
# `seq_max(ToSeq(verts))` directly. This is the HONEST cheapest-correct impl
# (seq_max IS the maximum). It keeps the two lemma calls (which discharge P_dom
# and P_att against seq_max) and the verbatim per-element bridge
# Assert(Forall k. ToSeq(verts)[k] == verts[k]) that connects seq_max(ToSeq(verts))
# to verts[k] — exactly the gold proof obligations, minus the loop machinery the
# loop only existed to establish (best == seq_max). seq_max is front-recursive and
# the lemmas are proven by front recursion, so NO new induction lemma is needed
# (directive 3 trap avoided: there is no forward-append here). If this CORRECT
# impl fails to verify, the postcondition is over-fit to the loop form =>
# SPEC-TOO-STRONG.
_POS_DIRECT = _swap(_BASE, _GOLD_FULL_BODY, """    # impl-start
    lemma_seq_max_dominates(ToSeq(verts))
    lemma_seq_max_attained(ToSeq(verts))
    res = seq_max(ToSeq(verts))  # type: int
    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
                                          ToSeq(verts)[k] == verts[k]))))
    return res
    # impl-end""")

# (5b) BRANCH-REORDER positive control: keep the entire backward-loop scaffold and
# all framing asserts VERBATIM, but rewrite the comparison `verts[i-1] > best` as
# the logically-equivalent `not (verts[i-1] <= best)`. Same behaviour, different
# executable shape; the front-recursive loop invariant
# (best == seq_max(ToSeq(verts).drop(i))) is discharged exactly as before. If it
# fails => SPEC-TOO-STRONG (over-fit to the `>` spelling).
_POS_REORDER = _swap(_BASE, _GOLD_CMP_STEP, """        if not (verts[i - 1] <= best):
            best = verts[i - 1]
        i = i - 1""")

# (6) ADMISSIBILITY: the precondition must admit a normal F2P-shaped input. The
# probe ASSERTS, at the top of the impl and BEFORE the first lemma call, that
# every Requires clause of enclosing_upper_bound is establishable there: the
# half-permission is held (so the elements are readable), the non-emptiness holds,
# and the termination measure len(verts) + 1 is positive AND strictly above the
# measure the two lemmas demand of the sequence they are applied to. If the
# precondition could not be met for a legitimate input the asserts would not
# verify => PRECOND-TOO-STRONG. The gold body follows VERBATIM, so the
# postcondition obligation is unchanged.
#
# A self-call is no longer usable as the witness: the method's own obligation is
# a MEASURE over its argument, and a self-call on the SAME input `verts` can
# never be strictly below itself, so Nagini reports `Obligation leak check
# failed. Callee enclosing_upper_bound might not take all unsatisfied obligations
# from the caller.` — a termination fact, not a fact about the precondition's
# domain, so it would attribute nothing. (Measured: the old self-call probe fails
# exactly that way.) Asserting the establishability of each Requires clause is
# the same substitution django__django-14580 uses for this reason.
#
# NEGATIVE CONTROL (proves the probe can fail, i.e. is not a tautology): moving
# the non-emptiness witness OUTSIDE the frozen precondition — asserting
# `len(verts) >= 1` of the TAIL, `Assert(len(ToSeq(verts).drop(1)) >= 1)`, which
# the precondition does NOT give (a one-element input is admissible) — is
# REJECTED by the verifier with
#   error: Assert might fail. Assertion (len(ToSeq(verts).drop(1)) >= 1) might
#   not hold.
# So the asserts below are discharged by the precondition, not by triviality.
_ADMISS = _swap(
    _BASE,
    "    # impl-start\n    lemma_seq_max_dominates(ToSeq(verts))",
    "    # impl-start\n"
    "    # ADMISSIBILITY probe: each Requires clause of this method is\n"
    "    # establishable for a normal non-empty input.\n"
    "    # Requires clause 1: the half-permission is held => elements readable.\n"
    "    Assert(verts[0] == verts[0])\n"
    "    # Requires clause 2: the input is non-empty.\n"
    "    Assert(len(verts) >= 1)\n"
    "    # Requires clause 3: the termination measure is positive, and strictly\n"
    "    # above the measure the lemmas demand of ToSeq(verts).\n"
    "    Assert(len(verts) + 1 > 0)\n"
    "    Assert(len(verts) + 1 > len(ToSeq(verts)))\n"
    "    lemma_seq_max_dominates(ToSeq(verts))",
)


# ===========================================================================
# FRAME-MUTATION (MANDATORY, directive 5) + UNIQUENESS RIVALS (must be REJECTED)
# ===========================================================================

# (FRAME-MUTATION — MANDATORY) The rival OVERWRITES the read-only input element
# `verts[0]` (setting it to `best`, the gathered max) before returning. To assign
# `verts[0] = best` Nagini needs FULL Acc(list_pred(verts)), but both the Requires
# and the loop Invariant grant only Acc(list_pred(verts), 1/2). The write is
# therefore REJECTED for INSUFFICIENT PERMISSION — before any postcondition is
# considered. The gold body (loop + framing asserts) is kept VERBATIM, with the
# write inserted right before `return best`, so the rejection is attributable
# SOLELY to the write.
#
# Refinement (why its faithful real patch would NOT resolve): the half-permission
# abstracts the gold contract that the gather READS the path vertices and forms a
# fresh extent (fed to update_datalim) without mutating the path's own vertex
# array. A real "patch" that overwrote the gathered vertex array in place (e.g.
# clamped vertices to the running max to make the extent trivially enclosing)
# would corrupt the patch's geometry — the rendered/limit-tested path would no
# longer match its data, and `test_small_autoscale` (which compares the autoscaled
# limits against min/max of the ORIGINAL `verts`) would FAIL. So it would NOT
# resolve. The half-permission is exactly the spec defending that read-only
# contract.
_RIVAL_FRAME_MUTATE = _swap(
    _BASE,
    "                                          ToSeq(verts)[k] == verts[k]))))\n"
    "    return best\n"
    "    # impl-end",
    "                                          ToSeq(verts)[k] == verts[k]))))\n"
    "    verts[0] = best\n"
    "    return best\n"
    "    # impl-end",
)

# (uniqueness — PARTIAL-DOMAIN, return the FIRST element) The rival keeps both
# lemma calls (valid) but returns `verts[0]` instead of the gathered max. It is
# CORRECT only on the sub-domain where verts[0] IS the maximum; it satisfies
# P_att (Result() == verts[0], j=0) but VIOLATES P_dom (Result() >= verts[k]) for
# any k with verts[k] > verts[0].
#
# Refinement: its faithful real patch is a gather that keeps only the FIRST
# gathered vertex as the extent seed and never folds the rest (e.g. `extent =
# vertices[0]` with no max over the others). On the F2P regression outline the
# y-extreme (0.33) is on an INTERIOR vertex, not the first (y=0.00), so the
# autoscaled ylim would be 0.00 < 0.33 and `assert ax.get_ylim()[1] >= maxy`
# FAILS. It would NOT resolve. Rejection source: P_dom
# (Forall k. Result() >= verts[k]) at the k carrying the true max.
_RIVAL_RET_FIRST = _swap(_BASE, _GOLD_FULL_BODY, """    # impl-start
    lemma_seq_max_dominates(ToSeq(verts))
    lemma_seq_max_attained(ToSeq(verts))
    return verts[0]
    # impl-end""")

# (uniqueness — PARTIAL-DOMAIN, return the LAST element / the prepatch seed bug)
# The rival returns `verts[len(verts)-1]` (the loop's initial seed) and never
# updates it — exactly the "seed and don't fold" shape. CORRECT only when the last
# element is the maximum; VIOLATES P_dom otherwise. Keeps both lemma calls so the
# rejection is attributable solely to the wrong return value.
#
# Refinement: its faithful real patch is a gather that takes only the LAST gathered
# vertex as the extent (or, equivalently, the appearance-preserving condensation
# whose retained tail vertex undershoots the interior extreme — the model_prepatch
# regression). On the F2P regression outline the last vertex y is 0.00 while the
# true y-max is 0.33, so `assert ax.get_ylim()[1] >= maxy` FAILS — exactly the
# bug the gold patch fixes (G-DIFF). It would NOT resolve. Rejection source: P_dom
# at the interior-extreme index.
_RIVAL_RET_LAST = _swap(_BASE, _GOLD_FULL_BODY, """    # impl-start
    lemma_seq_max_dominates(ToSeq(verts))
    lemma_seq_max_attained(ToSeq(verts))
    return verts[len(verts) - 1]
    # impl-end""")

# (uniqueness — VALUE-MASK / partial-domain on a parity sub-domain) The rival keeps
# the whole backward-loop scaffold and framing asserts, but MASKS the max update on
# odd loop positions: it only lets `best` grow when `i % 2 == 0`. So if the true
# maximum sits at a vertex first encountered at an odd `i`, the gathered bound
# undershoots it. CORRECT on the sub-domain where the max happens to be reached at
# an even index; WRONG otherwise.
#
# Refinement: its faithful real patch is a gather that folds the extent over only
# every-other gathered vertex (e.g. `vertices[::2]`). On a path whose extreme falls
# on a skipped (odd-index) vertex the autoscaled limit undershoots it and
# `test_small_autoscale`'s `>= maxy` assertion FAILS. It would NOT resolve.
# Rejection source: the loop INVARIANT `best == seq_max(ToSeq(verts).drop(i))` can
# no longer be re-established after a skipped update (and ultimately P_dom). NOTE:
# this is expected to reject at the invariant/postcondition; the framing asserts
# are kept verbatim so the rejection is a genuine spec/invariant failure, not a
# dangling reference.
_RIVAL_VALUE_MASK = _swap(_BASE, _GOLD_CMP_STEP, """        if verts[i - 1] > best and i % 2 == 0:
            best = verts[i - 1]
        i = i - 1""")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-direct-seqmax", "kind": "soundness", "expect": "verify",
     "module": _POS_DIRECT,
     "rationale": "honest cheapest-correct, structurally-different impl: drop the explicit "
                  "loop and return seq_max(ToSeq(verts)) directly, discharging P_dom/P_att via "
                  "the two verified lemmas + the verbatim per-element bridge assert. seq_max IS "
                  "the maximum (grounded, front-recursive), so this is correct. If it fails to "
                  "verify, the postcondition is over-fit to the loop form => SPEC-TOO-STRONG."},
    {"id": "pos-branch-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different but CORRECT impl: the loop comparison verts[i-1] > "
                  "best rewritten as the equivalent not (verts[i-1] <= best); the entire "
                  "backward-loop scaffold + framing asserts + front-recursive invariant kept "
                  "verbatim. Must verify, else the spec is over-fit to the `>` spelling => "
                  "SPEC-TOO-STRONG."},
    {"id": "admiss-selfcall", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "the precondition must admit a normal F2P-shaped input, so the probe ASSERTS "
                  "each Requires clause of enclosing_upper_bound is establishable on the "
                  "in-scope input: the half-permission is held (verts[0] readable), the input "
                  "is non-empty, and the termination measure len(verts) + 1 is positive and "
                  "strictly above the measure the lemmas demand of ToSeq(verts). The gold body "
                  "follows verbatim, so the postcondition obligation is unchanged. If the "
                  "Requires could not be met for a legitimate input => PRECOND-TOO-STRONG. "
                  "A self-call is no longer usable as the witness: the obligation is a MEASURE "
                  "over the argument and a self-call on the SAME `verts` is never strictly "
                  "below itself, so it fails with `Obligation leak check failed. Callee "
                  "enclosing_upper_bound might not take all unsatisfied obligations from the "
                  "caller.` — a termination fact that attributes nothing about the domain "
                  "(measured). NEGATIVE CONTROL (the probe is a real check, not a tautology): "
                  "moving the non-emptiness witness outside the frozen precondition, i.e. "
                  "asserting it of the TAIL via Assert(len(ToSeq(verts).drop(1)) >= 1) — which "
                  "a one-element admissible input does not give — is REJECTED with `error: "
                  "Assert might fail. Assertion (len(ToSeq(verts).drop(1)) >= 1) might not "
                  "hold.` (measured)."},

    # ---- frame-mutation (MANDATORY) + uniqueness rivals (must be REJECTED) ----
    {"id": "rival-frame-mutate-verts", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_MUTATE,
     "refinement": "OVERWRITES the read-only input element verts[0] = best before returning. "
                   "The half-permission Acc(list_pred(verts), 1/2) abstracts the gold contract "
                   "that the gather READS the path vertices and forms a FRESH extent (fed to "
                   "update_datalim) without mutating the path's own vertex array. A real patch "
                   "that overwrote the gathered vertex array in place (e.g. clamped vertices to "
                   "the running max so the extent is trivially enclosing) would corrupt the "
                   "path geometry; test_small_autoscale compares the autoscaled limits against "
                   "min/max of the ORIGINAL verts, so it would FAIL. So it would NOT resolve.",
     "rationale": "FRAME-MUTATION (directive 5). Rejection source: the PERMISSION SYSTEM — "
                  "assigning verts[0] needs full Acc(list_pred(verts)) but the precondition "
                  "and loop invariant grant only 1/2, so the write fails for INSUFFICIENT "
                  "PERMISSION before any postcondition is considered. If it verified, a "
                  "mutating impl could satisfy the postcondition vacuously => SPEC-TOO-WEAK."},
    {"id": "rival-return-first", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_RET_FIRST,
     "refinement": "PARTIAL-DOMAIN (first element): returns verts[0] (keeping both lemma calls "
                   "so only the value is wrong). Correct ONLY when verts[0] is the maximum. Its "
                   "faithful real patch is a gather that keeps only the first gathered vertex as "
                   "the extent seed and never folds the rest. On the F2P regression outline the "
                   "y-extreme (0.33) is on an interior vertex (first vertex y=0.00), so the "
                   "autoscaled ylim 0.00 < 0.33 and `assert ax.get_ylim()[1] >= maxy` FAILS. It "
                   "would NOT resolve.",
     "rationale": "Rejection source: P_dom Forall k. Result() >= verts[k] (model.py:128-129), "
                  "violated at the k carrying the true max when verts[0] is not the maximum. "
                  "P_att is satisfiable (j=0), so the rejection is attributable specifically to "
                  "the dominance clause. If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-return-last-seed", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_RET_LAST,
     "refinement": "PARTIAL-DOMAIN / prepatch seed bug: returns verts[len-1] (the loop's "
                   "initial seed) and never folds the rest. Correct ONLY when the last element "
                   "is the maximum. Its faithful real patch is a gather that takes only the last "
                   "gathered vertex (or the appearance-preserving condensation whose retained "
                   "tail undershoots the interior extreme — the model_prepatch regression). On "
                   "the F2P regression outline the last vertex y=0.00 while the true y-max is "
                   "0.33, so `assert ax.get_ylim()[1] >= maxy` FAILS — exactly the bug the gold "
                   "patch fixes (G-DIFF). It would NOT resolve.",
     "rationale": "Rejection source: P_dom Forall k. Result() >= verts[k] (model.py:128-129) "
                  "at the interior-extreme index. If it verified => SPEC-TOO-WEAK (admits the "
                  "seed-and-don't-fold / condensation regression)."},
    {"id": "rival-value-mask-odd", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_VALUE_MASK,
     "refinement": "VALUE-MASK / partial-domain (parity): masks the max update on odd loop "
                   "positions (best only grows when i % 2 == 0), so a maximum first encountered "
                   "at an odd index is dropped. Its faithful real patch is a gather that folds "
                   "the extent over only every-other gathered vertex (vertices[::2]); on a path "
                   "whose extreme falls on a skipped vertex the autoscaled limit undershoots it "
                   "and test_small_autoscale's `>= maxy` assertion FAILS. It would NOT resolve.",
     "rationale": "Rejection source: the loop invariant best == seq_max(ToSeq(verts).drop(i)) "
                  "(model.py:144) can no longer be re-established after a skipped update, so "
                  "Assert(best == seq_max(ToSeq(verts))) and ultimately P_dom fail. The framing "
                  "asserts are kept verbatim so the rejection is a genuine invariant/spec "
                  "failure. If it verified => SPEC-TOO-WEAK (the max is masked on a sub-domain)."},
]


# ===========================================================================
# AXIOM LANE (Docker, real matplotlib callee) — REUSE + strengthen axiom_check.py.
# The runner does NOT mount axiom_check.py in-container, so its source is read on
# the HOST at manifest-load time and EMBEDDED into the probe string. The callee
# `Path.iter_bezier` is UNCHANGED by the gold patch (the patch only flips a
# keyword at the _base.py call site), so apply_gold=False.
# ===========================================================================

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

# (axiom-soundness) Run the EXACT axiom_check.py battery in-container: it drives the
# GENUINE matplotlib Path.iter_bezier over 4 boundary outlines, the EXACT F2P
# regression fixture (test_small_autoscale's 132-vertex array), and 4000 fuzz
# outlines, and asserts: (a) the condensed gather (simplify=None) emits only
# path-vertex values (the A-consumed subsel_at MEMBERSHIP) and never more points
# than the full gather (subsel_len count bound); (b) the full gather
# (simplify=False) max >= every vertex / min <= every vertex (the A-reference deep
# seq_max enclosing property); (c) the discriminating witness — on the F2P fixture
# the condensation's y-max is strictly below the true y-max while the full gather
# captures it. Exit 0 iff all sound. Self-contained (imports only matplotlib.path /
# matplotlib.bezier / numpy); no bundle file mounted in-container.
_AX_SOUNDNESS = _AXIOM_CHECK_SRC

# (axiom-containment) Confirm every callee-input the MODEL can REACH lies in the
# axioms'/deep-model's Requires domain. The model's reachable callee-inputs:
#   * seq_max (A-reference) Requires len(s) >= 1 — the model only ever folds the
#     max over the FULL non-empty gather (enclosing_upper_bound's Requires is
#     len(verts) >= 1; the full gather of a non-empty path is non-empty), so every
#     reachable input is in-domain.
#   * subsel_at (A-consumed, prepatch only) Requires 0 <= idx < subsel_len(verts) —
#     the prepatch only indexes the condensation at idx in [0, subsel_len), which
#     is in-domain by construction, AND subsel_len(verts) <= len(verts) <= the full
#     gather count (so a condensed index never exceeds the full gather extent).
# We execute the real Path.iter_bezier and assert, on the boundary + F2P + fuzz
# outlines, that: a non-empty path yields a non-empty full gather (seq_max domain
# OK), and the condensed gather count is <= the full gather count (subsel index
# domain OK). Covering MORE than the caller reaches (e.g. empty paths, which the
# model never reaches since len(verts) >= 1) is SOUND, not a defect; we positively
# confirm the empty-path edge is OUTSIDE the model's reachable domain. A reachable
# input outside the domain => AXIOM-TOO-WEAK-FOR-CALLER.
_AX_CONTAINMENT = r'''
import random
import sys

import numpy as np
from matplotlib.path import Path


def gather_vertices(path, simplify):
    collected = []
    for curve, code in path.iter_bezier(simplify=simplify):
        _, dzeros = curve.axis_aligned_extrema()
        collected.append(curve([0, *dzeros, 1]))
    if len(collected):
        return np.row_stack(collected)
    return np.empty((0, 2))


def regression_outline():
    verts = np.array([
        [-5.45, 0.00], [-5.45, 0.00], [-5.29, 0.00], [-5.29, 0.00],
        [-0.18, 0.33], [-0.02, 0.33], [0.13, 0.33], [0.29, 0.33],
        [4.77, 0.00], [4.93, 0.00],
    ])
    # use a long-enough outline so should_simplify can fire
    big = []
    x = -5.45
    for _ in range(70):
        x += 0.16
        big.append([x, 0.0])
        big.append([x, 0.33 if -0.2 < x < 0.3 else 0.05])
    return Path(np.array(big))


def random_step_outline(rng):
    n = rng.randint(2, 90)
    verts = []
    x = rng.uniform(-10, 10)
    for _ in range(n):
        x += rng.uniform(0.05, 0.4)
        y = rng.uniform(0.0, 5.0)
        verts.append([x, 0.0])
        verts.append([x, y])
    return Path(np.array(verts))


def check_containment(path):
    raw = path.vertices
    full = gather_vertices(path, simplify=False)
    cond = gather_vertices(path, simplify=None)
    # seq_max (A-reference) Requires len(s) >= 1: the model reaches it only on a
    # NON-EMPTY full gather (its Requires is len(verts) >= 1). A non-empty path
    # must yield a non-empty full gather, else the model could reach seq_max([]).
    if raw.shape[0] >= 1:
        if full.shape[0] < 1:
            print("AXIOM-TOO-WEAK-FOR-CALLER: a non-empty path produced an EMPTY "
                  "full gather, so the model could reach seq_max([]) (outside its "
                  "Requires len(s) >= 1)")
            return False
    # subsel_at (A-consumed) Requires 0 <= idx < subsel_len(verts): the prepatch
    # only indexes the condensation in [0, subsel_len), and subsel_len must not
    # exceed the full gather count (else an index could exceed the full extent).
    if cond.shape[0] > full.shape[0]:
        print("AXIOM-TOO-WEAK-FOR-CALLER: condensed gather count %d exceeds full "
              "gather count %d, so a reachable subsel index could exceed the full "
              "gather extent (subsel_len <= len(verts) violated)"
              % (cond.shape[0], full.shape[0]))
        return False
    return True


def main():
    boundary = [
        Path(np.array([[0.0, 0.0], [1.0, 1.0]])),
        Path(np.array([[0.0, 0.0], [1.0, 2.0], [2.0, 0.0]])),
        Path(np.array([[0.0, 0.0]])),
        regression_outline(),
    ]
    checked = 0
    for path in boundary:
        if not check_containment(path):
            return 1
        checked += 1

    # The empty-path edge (the model NEVER reaches it: len(verts) >= 1) — covering
    # it or not is irrelevant to containment; confirm it is outside the reachable
    # domain (a 0-vertex path yields a 0-count full gather, which seq_max's
    # Requires len(s) >= 1 forbids — the model's precondition excludes this).
    empty = gather_vertices(Path(np.empty((0, 2))), simplify=False)
    if empty.shape[0] != 0:
        print("CONTAINMENT note: empty path unexpectedly produced a non-empty "
              "gather (%d) — harmless, model still excludes len 0" % empty.shape[0])

    rng = random.Random(24177)
    for _ in range(4000):
        path = random_step_outline(rng)
        if not check_containment(path):
            return 1
        checked += 1

    print("CONTAINMENT OK: every reachable callee-input is in-domain over %d "
          "outlines (boundary + F2P-shaped + fuzz): a non-empty path always yields "
          "a non-empty full gather (seq_max Requires len(s) >= 1 satisfied), and the "
          "condensed gather count never exceeds the full gather count (subsel index "
          "domain 0 <= idx < subsel_len <= len(verts) satisfied). The empty-path "
          "edge is OUTSIDE the model's reachable domain (Requires len(verts) >= 1), "
          "which is sound over-coverage, not a containment defect." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

AXIOM_TESTS = [
    {"id": "ax-gather-sound", "axiom": "subsel_at",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": False,
     "probe": _AX_SOUNDNESS,
     "rationale": "REUSES axiom_check.py: drives the REAL Path.iter_bezier over 4 boundary "
                  "outlines + the EXACT F2P regression fixture + 4000 fuzz outlines and asserts "
                  "(a) the condensed gather emits only path-vertex values and never more points "
                  "than the full gather (the A-consumed subsel_at MEMBERSHIP + subsel_len count "
                  "bound), (b) the full gather (simplify=False) max >= every vertex / min <= "
                  "every vertex (the A-reference deep seq_max enclosing property), (c) the "
                  "discriminating witness (the condensation drops the interior y-extreme while "
                  "the full gather captures it). The callee is UNCHANGED by the patch "
                  "(apply_gold=False). Any violation => AXIOM-UNSOUND."},
    {"id": "ax-gather-containment", "axiom": "subsel_at",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": False,
     "probe": _AX_CONTAINMENT,
     "rationale": "every callee-input the model can reach is in-domain: a non-empty path "
                  "(Requires len(verts) >= 1) always yields a non-empty full gather (seq_max "
                  "Requires len(s) >= 1), and the condensed gather count never exceeds the full "
                  "gather count (so the prepatch's subsel index 0 <= idx < subsel_len <= "
                  "len(verts) stays in-domain). The empty-path edge is OUTSIDE the reachable "
                  "domain by the precondition (sound over-coverage). A reachable input outside "
                  "the domain => AXIOM-TOO-WEAK-FOR-CALLER."},
]
