# properties.py — PBT manifest for sympy__sympy-21596. NOT a Nagini module; a
# record of adversarial falsification cases. The runner (swebench_nagini.pbt)
# executes each and stamps RESULT.
#
# Defended surface (read from model.py / refinement.md / mapping.md):
#   collect_real_indices(base, keep, drop) filters a base domain of integer
#   indices: index k survives iff k is in `keep` AND k is not in `drop`
#   (per-index, order-preserving). The LOAD-BEARING postcondition is
#       ToSeq(Result()) == kept_seq(ToSeq(base), ToSeq(keep), ToSeq(drop))
#   which pins the result EXACTLY to a structural front-recursive filter of the
#   real input carriers. There is NO opaque oracle: kept_seq is a function of
#   the args, fully unfolded, so there is no "wrong echo" to build (see
#   assessment) — instead we provide an honest positive control.
#
#   ALL THREE inputs (base, keep, drop) carry Acc(list_pred(.,), 1/2) — they are
#   READ-ONLY. Result() carries full permission. => FRAME-MUTATION is mandatory.
#
#   The impl is a BACKWARD loop (i = len(base) .. 1) prepending [c] + result,
#   matched against the FRONT-recursive kept_seq via the invariant
#       ToSeq(result) == kept_seq(ToSeq(base).drop(i), ...).
#   A forward-append positive control would need an f(a+b)==f(a)+f(b) lemma the
#   verifier cannot auto-discharge, so every positive control KEEPS the backward
#   shape, the two framing Asserts, and the invariant (only locals are reshaped).
#
# There are NO @ContractOnly axioms (meta.axioms == []). The survives/kept_seq
# deep model is an A-reference validated by axiom_check.py against the real fixed
# imageset(...).intersect(S.Reals). We re-run that real-callee soundness check in
# Docker (apply_gold=True) as an axiom-soundness probe.
from pathlib import Path

INSTANCE = "sympy__sympy-21596"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors INSIDE the impl region (lines 83-101). Editing only these preserves
# same_spec (spec_view elides the whole impl span).
# ---------------------------------------------------------------------------
GOLD_GUARD = "        if survives(c, ToSeq(keep), ToSeq(drop)):\n            result = [c] + result\n"
# `result = []` now appears in BOTH modeled functions; anchor on the unique
# decl + the following `i = len(base)` to target collect_real_indices only.
GOLD_DECL = "    result = []  # type: List[int]\n    i = len(base)\n"

# Anchors inside the SECOND modeled function collect_real_indices_two_step:
# the difference step (step 2, base_set -=) guard. Unique to that function.
TWO_STEP_DROP_GUARD = (
    "        if not contains(ToSeq(drop), d):\n"
    "            result = [d] + result\n"
)


# ===========================================================================
# SPEC LANE
# ===========================================================================

# --- 1. POSITIVE CONTROL (soundness): structurally-different but CORRECT ----
# Reshape only LOCALS: hoist the survives() decision into a typed boolean local
# `take` and branch on it, instead of calling survives() inline in the if-test.
# The backward loop, both framing Asserts, the prepend, and every invariant are
# kept VERBATIM so the gold proof still discharges. If a faithful correct impl
# of this shape cannot verify => SPEC-TOO-STRONG.
POS_CONTROL = _swap(
    _BASE, GOLD_GUARD,
    "        take = survives(c, ToSeq(keep), ToSeq(drop))  # type: bool\n"
    "        if take:\n"
    "            result = [c] + result\n",
)

# --- 2. ADMISSIBILITY: the Requires admits a normal F2P-shaped input --------
# Gold impl, but prepend an entry Assert that the loop's base-case invariant
# (empty result == kept_seq of the empty base suffix) is ESTABLISHABLE from the
# given read-only inputs. If the precondition were too strong (could not be
# established for an F2P-shaped input) this entry reasoning would fail.
ADMISS = _swap(
    _BASE, GOLD_DECL,
    "    result = []  # type: List[int]\n"
    "    Assert(ToSeq(result) == kept_seq(ToSeq(base).drop(len(base)),\n"
    "                                     ToSeq(keep), ToSeq(drop)))\n"
    "    i = len(base)\n",
)

# --- 3. FRAME-MUTATION (uniqueness, MANDATORY): write a read-only input -----
# `base` is Acc(list_pred(base), 1/2) (read-only). This rival writes back to
# base (base[i-1] = c — a value-preserving no-op write) while keeping every gold
# invariant/assert VERBATIM, so the ONLY new obligation is a full write
# permission on `base`. With 1/2 permission the write MUST be rejected for
# insufficient permission. If it verified, the spec would not actually protect
# the read-only inputs.
FRAME_MUT = _swap(
    _BASE, GOLD_GUARD,
    "        base[i - 1] = c  # ILLEGAL: only Acc(list_pred(base), 1/2) held\n"
    "        if survives(c, ToSeq(keep), ToSeq(drop)):\n"
    "            result = [c] + result\n",
)

# --- 4. PARTIAL-DOMAIN (uniqueness): the prepatch collapse bug --------------
# Drop the keep conjunct: retain every index that is merely NOT in `drop`
# (survives degrades to `not contains(drop, c)`). This is EXACTLY the pre-fix
# aggregation (model_prepatch.py): correct on indices that are in keep or in
# drop, but WRONG on a base index absent from both (e.g. index 2 in the issue,
# which it keeps but gold excludes). Must be rejected by the kept_seq equality.
PARTIAL_NO_KEEP = _swap(
    _BASE, GOLD_GUARD,
    "        if not contains(ToSeq(drop), c):\n"
    "            result = [c] + result\n",
)

# --- 5. VALUE-LEVEL DOUBLE-MASK (uniqueness): drop the drop conjunct ---------
# Retain every index that is in `keep`, ignoring `drop` (survives degrades to
# `contains(keep, c)`). Diverges precisely on an index that is BOTH a keep-root
# and a denominator pole — the F2P-7 EmptySet case n/(n**2-9)+... where the kept
# index is also a pole and gold drops it. Must be rejected by kept_seq equality.
DROP_IGNORED = _swap(
    _BASE, GOLD_GUARD,
    "        if contains(ToSeq(keep), c):\n"
    "            result = [c] + result\n",
)

# --- 6. PARTIAL-DOMAIN (boundary): correct except the FIRST base element -----
# survives gates correctly EXCEPT it unconditionally also keeps the element at
# base position 0 (i == 1, the last loop step). For an input whose first index
# does NOT survive (e.g. base[0] in `drop` and not in `keep`), this over-keeps a
# single boundary index. Must be rejected by kept_seq equality.
BOUNDARY = _swap(
    _BASE, GOLD_GUARD,
    "        if survives(c, ToSeq(keep), ToSeq(drop)) or i == 1:\n"
    "            result = [c] + result\n",
)

# --- 7. POSITIVE CONTROL on the TWO-STEP function (soundness): correct -------
# In collect_real_indices_two_step's step 2 (difference), hoist the not-in-drop
# decision into a typed boolean local `take` and branch on it, instead of the
# inline `not contains(ToSeq(drop), d)`. Every invariant, framing Assert, the
# lemma call, and step 1 are kept VERBATIM so the proof still discharges. Must
# verify, else the WIDENED spec is too strong.
TWO_STEP_POS = _swap(
    _BASE, TWO_STEP_DROP_GUARD,
    "        take = not contains(ToSeq(drop), d)  # type: bool\n"
    "        if take:\n"
    "            result = [d] + result\n",
)

# --- 8. TWO-STEP DROP-COLLAPSE (uniqueness): the prepatch bug on step 2 -------
# Collapse the difference step (step 2, base_set -=) into a no-op: every index
# that survived the intersection step is kept unconditionally, never tested
# against the drop collection. This is the model_prepatch.py witness on the new
# function. WRONG on an index that is in BOTH keep and drop (e.g. F2P-7's pole
# index 3): the gold removes it via `base_set -= ...` but this keeps it. Must be
# rejected by the postcondition ToSeq(Result()) == drop_filter(keep_filter(...)).
TWO_STEP_DROP_COLLAPSE = _swap(
    _BASE, TWO_STEP_DROP_GUARD,
    "        if True:  # difference step collapsed to a no-op (pre-fix bug)\n"
    "            result = [d] + result\n",
)


SPEC_TESTS = [
    {
        "id": "pos-control-hoist-local",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_CONTROL,
        "rationale": (
            "structurally-different CORRECT impl: the survives() decision is "
            "hoisted into a typed boolean local `take` and the branch tests it, "
            "instead of calling survives() inline. Backward loop, both framing "
            "Asserts, prepend, and all invariants kept verbatim so the gold "
            "proof still discharges. Must verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-base-case",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": (
            "the read-only precondition (three Acc(.,1/2) inputs) must admit a "
            "normal F2P-shaped input: the entry Assert proves the loop base-case "
            "invariant (empty result == kept_seq of the empty base suffix) is "
            "establishable. If it could not be, PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mutation-write-base",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_MUT,
        "refinement": (
            "A faithful real patch never destructively writes back into the "
            "index/base collections: sympy Sets are immutable and the gold patch "
            "computes a NEW base_set via &=/-=; an impl that mutates its input "
            "domain in place is not the gold behaviour and would corrupt the "
            "imageset re-expression, so it would not resolve "
            "test_imageset_intersect_real."
        ),
        "rationale": (
            "base carries only Acc(list_pred(base), 1/2); `base[i-1] = c` needs "
            "full write permission. Rejection comes from the PERMISSION SYSTEM "
            "(insufficient permission to write base), not from a value mismatch "
            "— every gold invariant/assert is kept verbatim so the rejection is "
            "attributable solely to the write."
        ),
    },
    {
        "id": "partial-domain-collapse-no-keep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARTIAL_NO_KEEP,
        "refinement": (
            "This is the pre-fix collapse bug verbatim (model_prepatch.py): the "
            "keep filter is a no-op, so any base index not in `drop` is kept "
            "regardless of keep-membership. Its faithful real patch keeps index "
            "2 in the issue's S1.intersect(Reals) (2 in result == True) which is "
            "exactly the bug test_imageset_intersect_real asserts False — it "
            "does NOT resolve the F2P."
        ),
        "rationale": (
            "rejected by the postcondition kept_seq equality clause: "
            "ToSeq(Result()) must equal kept_seq, which requires BOTH "
            "contains(keep,c) AND not contains(drop,c); a base index in neither "
            "collection (e.g. 2) is kept here but excluded by kept_seq."
        ),
    },
    {
        "id": "value-double-mask-ignore-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": DROP_IGNORED,
        "refinement": (
            "Ignoring `drop` keeps an index that is both a keep-root and a "
            "denominator pole. The F2P-7 case n/(n**2-9)+(n-3)(n+1)i/(2n+2) is "
            "EmptySet because its kept root is also a pole; a real patch that "
            "skipped the denominator subtraction (`base_set -= ...`) would "
            "return that pole index's image and fail the EmptySet assertion of "
            "test_imageset_intersect_real."
        ),
        "rationale": (
            "rejected by the kept_seq equality clause: survives requires `not "
            "contains(drop,c)`; an index in both keep and drop survives here but "
            "is excluded by kept_seq (the `not contains(drop,.)` conjunct)."
        ),
    },
    {
        "id": "partial-domain-keep-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": BOUNDARY,
        "refinement": (
            "Always retaining the first base element (i==1 step) over-keeps a "
            "single boundary index whenever base[0] does not survive (e.g. a "
            "leading index that is a denominator pole or simply absent from "
            "keep). The faithful real patch would include a non-real / pole "
            "image at the domain boundary, changing the finite result set and "
            "failing test_imageset_intersect_real's exact-set assertions."
        ),
        "rationale": (
            "rejected by the kept_seq equality clause: kept_seq decides base[0] "
            "by survives(base[0],...) alone, with no positional exception; the "
            "`or i == 1` over-keep makes ToSeq(Result()) diverge from kept_seq "
            "on any input whose first index does not survive."
        ),
    },
    {
        "id": "two-step-pos-control-hoist-drop",
        "kind": "soundness",
        "expect": "verify",
        "module": TWO_STEP_POS,
        "rationale": (
            "structurally-different CORRECT impl of the WIDENED two-step "
            "function: the difference-step decision is hoisted into a typed "
            "boolean local `take` and the branch tests it, instead of the inline "
            "`not contains(ToSeq(drop), d)`. Step 1, every invariant, the framing "
            "Asserts and the lemma call are kept verbatim so the proof still "
            "discharges. Must verify, else the WIDENED spec is too strong."
        ),
    },
    {
        "id": "two-step-drop-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": TWO_STEP_DROP_COLLAPSE,
        "refinement": (
            "Collapsing the difference step (base_set -=) into a no-op is the "
            "model_prepatch.py witness on the new function: it keeps every index "
            "that survived the intersection step, never applying the drop "
            "collection. Its faithful real patch omits the gold's "
            "`base_set -= _solution_union(denoms(f), n)`, so the F2P-7 case "
            "n/(n**2-9)+... returns the pole index 3's image instead of EmptySet "
            "and fails test_imageset_intersect_real's EmptySet assertion."
        ),
        "rationale": (
            "rejected by the step-2 loop invariant / postcondition "
            "ToSeq(Result()) == drop_filter(keep_filter(ToSeq(base), ToSeq(keep)), "
            "ToSeq(drop)): an index in both keep and drop survives step 1 and is "
            "kept by the collapsed step but is excluded by drop_filter (the "
            "not-contains(drop,.) conjunct), so the result diverges."
        ),
    },
]


# ===========================================================================
# AXIOM LANE
# ===========================================================================
# meta.axioms == [] (NO @ContractOnly axiom). But survives/kept_seq is an
# A-reference deep model validated against the REAL fixed
# imageset(...).intersect(S.Reals) by axiom_check.py. We re-run that real-callee
# soundness check IN-CONTAINER (apply_gold=True): it asserts the index-level
# biconditional survives(k,keep,drop) == gold_keeps(k) on the in-scope F2P cases
# + fuzz, and that the out-of-scope (non-linear imaginary part) cases are flagged
# (containment: every reachable input the model claims is in the modeled
# all-linear-factor regime; non-linear factors are reported out-of-scope, not
# silently passed). This is BOTH soundness (the model never over/under-keeps an
# in-regime index vs the real callee) and containment (out-of-regime inputs are
# excluded from the claim).
#
# Per pilot rule 6: the runner mounts ONLY the probe at /work, so axiom_check.py
# is NOT in-container. We read its source on the HOST at load time and embed it
# into the probe string verbatim.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

_AX_PROBE = (
    "# Embedded axiom_check.py (read on HOST at manifest-load; the runner does\n"
    "# not mount bundle files). Runs against the gold-patched sympy in-container.\n"
    + _AXIOM_CHECK_SRC
)

AXIOM_TESTS = [
    {
        "id": "ax-ref-survives-kept_seq",
        "axiom": "survives/kept_seq (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": (
            "The deep model survives/kept_seq is validated == the real fixed "
            "imageset(Lambda(n,f),base).intersect(S.Reals) at the INDEX level "
            "(biconditional both directions, no value-realness mask) on the 6 "
            "in-scope F2P cases + 400 distinct-linear-factor fuzz cases; the 1 "
            "out-of-scope quadratic-imaginary-part F2P case and 120 repeated-root "
            "fuzz cases are flagged out-of-scope (containment: the model only "
            "claims the all-linear-factor regime). keep = real per-factor "
            "solve_linear roots of numer(im); drop = ALL real denominator-zero "
            "indices (covers the non-linear-denominator EmptySet case). Exit 0 "
            "iff the model matches the real callee on every caller-reachable "
            "in-regime index; if it disagreed => A-reference unsound."
        ),
    },
]
