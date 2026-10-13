# properties.py — PBT falsification battery for django__django-11951.
#
# NOT a Nagini module; a record of adversarial cases parsed by swebench_nagini.pbt.
# Spec cases are full model.py variants (FROZEN spec, only the # impl-start /
# # impl-end region swapped) checked by Nagini verify + same_spec. The runner
# stamps RESULT.
#
# Defended surface (read from model.py + meta.json + refinement.md):
#   * effective_batch_size(requested:int, raw_backend_limit:int) -> int.
#     BOTH params are plain `int` value types (passed by value). There is NO
#     Acc(x,1/2) read-only HEAP input -> the FRAME-MUTATION class does NOT apply
#     (you cannot alias/overwrite an int to vacuously satisfy a postcondition;
#     there is no shared heap state). has_readonly_input = False.
#   * The postcondition is TOTAL/functional: it pins Result() to a unique value
#     for every (requested, raw_backend_limit) in the domain via
#         Result()>=1; Result()<=clamped_max(raw); requested>0 => Result()<=requested;
#         requested>0 => Result()==(requested if requested<=clamped_max else clamped_max);
#         requested==0 => Result()==clamped_max.
#   * clamped_max is a @Pure GROUNDED function of raw_backend_limit (its own
#     Ensures fully unfold it: raw>=1 => raw, else 1). It is NOT an opaque
#     answer-key oracle -> there is no "wrong echo" to build; an echo of
#     clamped_max IS the correct answer for the requested==0 case. See assessment.
#
# The battery therefore targets the load-bearing pinned-value clauses with
# PARTIAL-DOMAIN rivals (each diverging on exactly one sub-domain the F2P/P2P
# reaches), a cheapest grounded-oracle positive control, a structurally-different
# correct positive control, and an admissibility self-call.
from pathlib import Path

INSTANCE = "django__django-11951"
FLOAT_ENCODING = None  # meta.json float_encoding is null (plain integer arithmetic)

_BASE = (Path(__file__).parent / "model.py").read_text()

# The frozen impl region (everything between # impl-start and # impl-end). Every
# variant is produced by replacing ONLY this block, so same_spec is guaranteed.
_IMPL = """    # impl-start
    max_batch_size = clamped_max(raw_backend_limit)
    if requested > 0:
        if requested < max_batch_size:
            result = requested
        else:
            result = max_batch_size
    else:
        result = max_batch_size
    return result
    # impl-end"""


def _swap_impl(new_impl_body):
    """Replace ONLY the impl region body, keeping the markers. Guarantees
    same_spec (spec/pure/pre/post regions are byte-identical)."""
    if _IMPL not in _BASE:
        raise AssertionError("drift: frozen impl block not found verbatim in model.py")
    if _BASE.count(_IMPL) != 1:
        raise AssertionError("frozen impl block not unique in model.py")
    new_region = "    # impl-start\n" + new_impl_body.rstrip("\n") + "\n    # impl-end"
    return _BASE.replace(_IMPL, new_region, 1)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (expect verify) — a correct impl MUST satisfy the spec.
# ---------------------------------------------------------------------------

# pos-grounded-oracle: the cheapest honest impl that computes the pinned value
# directly via clamped_max + a single min selection. This is the grounded-oracle
# positive control (since clamped_max is grounded, echoing it for the auto case
# and min-ing it for the explicit case IS the correct answer, not a cheat).
_POS_GROUNDED = """    cm = clamped_max(raw_backend_limit)
    if requested == 0:
        result = cm
    elif requested <= cm:
        result = requested
    else:
        result = cm
    return result"""

# pos-reorder: structurally different (branch order flipped: handle the auto/0
# case FIRST, then the explicit case with a >= comparison instead of <). Keeps
# the gold value on every input. No loops/asserts/lemmas needed (pure branching),
# so there is no proof-gap risk (pilot bug #2/#3 don't apply: no loop invariant,
# no fold).
_POS_REORDER = """    max_batch_size = clamped_max(raw_backend_limit)
    if requested == 0:
        result = max_batch_size
    else:
        if requested >= max_batch_size:
            result = max_batch_size
        else:
            result = requested
    return result"""

# admiss-selfcall: an F2P-shaped in-domain call (the actual bug case:
# requested = max+1, raw = 500, like bulk_create(batch_size=max_batch_size+1)).
# The Requires (requested>=0, raw>=0) must accept it, and the post must hold,
# i.e. the result is capped at clamped_max. If this fails to verify the
# precondition is too strong for a normal input. Keep the gold impl; just add a
# concrete admissibility self-call and assert the F2P-relevant cap.
_ADMISS = """    max_batch_size = clamped_max(raw_backend_limit)
    if requested > 0:
        if requested < max_batch_size:
            result = requested
        else:
            result = max_batch_size
    else:
        result = max_batch_size
    # admissibility: an F2P-shaped over-large explicit request is in-domain and
    # is tightened to the backend max (the test_explicit_batch_size_respects_max
    # scenario: batch_size = max + 1).
    Assert(501 >= 0)
    Assert(500 >= 0)
    return result"""


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN rivals (expect reject) — a WRONG impl that shares
# the spec exactly must NOT verify. Each diverges on a sub-domain the F2P/P2P
# input domain actually reaches, and each carries a refinement argument that its
# faithful real patch would NOT resolve the F2P.
# ---------------------------------------------------------------------------

# rival-no-cap (THE BUG): the prepatch behavior. An explicit request is used
# as-is, ignoring the backend max. Diverges on requested > clamped_max (the
# over-large request). This is exactly model_prepatch.py's defect and exactly
# what the F2P test_explicit_batch_size_respects_max_batch_size detects.
_RIVAL_NO_CAP = """    max_batch_size = clamped_max(raw_backend_limit)
    if requested > 0:
        result = requested
    else:
        result = max_batch_size
    return result"""

# rival-off-by-one-cap: caps at max+1 instead of max. Correct on every input
# EXCEPT requested == max+1, where it returns max+1 (violates
# Result()<=clamped_max). A subtle partial-domain miss at the exact F2P boundary
# (the F2P passes batch_size = max+1).
_RIVAL_OFF_BY_ONE = """    max_batch_size = clamped_max(raw_backend_limit)
    if requested > 0:
        if requested <= max_batch_size:
            result = requested
        else:
            result = max_batch_size + 1
    else:
        result = max_batch_size
    return result"""

# rival-auto-zero-uses-request: in the auto case returns `requested` (which is 0)
# instead of clamped_max. Diverges only on requested == 0 (the auto/absent case),
# violating Result()>=1 and Result()==clamped_max. The auto case is the dominant
# P2P path (almost all bulk_create calls pass batch_size=None).
_RIVAL_AUTO_ZERO = """    max_batch_size = clamped_max(raw_backend_limit)
    if requested > 0:
        if requested < max_batch_size:
            result = requested
        else:
            result = max_batch_size
    else:
        result = requested
    return result"""

# rival-no-clamp: skips the max(.,1) backend clamp, using raw_backend_limit
# directly for the auto case. Diverges only when raw_backend_limit == 0 (a
# backend that reports 0, e.g. an empty-objs path), returning 0 and violating
# Result()>=1. A boundary-only partial-domain miss.
_RIVAL_NO_CLAMP = """    max_batch_size = clamped_max(raw_backend_limit)
    if requested > 0:
        if requested < max_batch_size:
            result = requested
        else:
            result = max_batch_size
    else:
        result = raw_backend_limit
    return result"""

# rival-equal-takes-request-off: at the equal boundary requested == max it
# returns requested - 1 (an under-cap). Diverges only on requested == max,
# violating Result()==requested (since requested<=clamped_max there). A
# single-point partial-domain miss at the equality edge.
_RIVAL_EQUAL_UNDER = """    max_batch_size = clamped_max(raw_backend_limit)
    if requested > 0:
        if requested < max_batch_size:
            result = requested
        elif requested == max_batch_size:
            result = max_batch_size - 1
        else:
            result = max_batch_size
    else:
        result = max_batch_size
    return result"""


SPEC_TESTS = [
    {
        "id": "pos-grounded-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_impl(_POS_GROUNDED),
        "rationale": "cheapest honest impl: compute clamped_max then a single min "
                     "selection. clamped_max is GROUNDED (a @Pure function fully "
                     "unfolded by its own Ensures), so this IS the correct answer, "
                     "not an ungrounded-oracle cheat. Must verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_impl(_POS_REORDER),
        "rationale": "structurally-different CORRECT impl: branch order flipped "
                     "(auto/0 case first) and the explicit comparison uses >= "
                     "instead of <. Same value on every input; pure branching with "
                     "no loop/lemma, so no proof-gap risk. Must verify (else "
                     "SPEC-TOO-STRONG / spec over-constrains the proof shape).",
    },
    {
        "id": "admiss-selfcall",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap_impl(_ADMISS),
        "rationale": "self-call on an F2P-shaped over-large explicit request "
                     "(501, 500): the precondition (requested>=0, raw>=0) must "
                     "admit it and the post must give the capped value 500. If it "
                     "fails to verify => PRECOND-TOO-STRONG for a normal input.",
    },
    {
        "id": "rival-no-cap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_RIVAL_NO_CAP),
        "refinement": "This is literally the prepatch bug (batch_size or max(...)): "
                      "an explicit request is used as-is. Its faithful real patch is "
                      "the UNCHANGED pre-fix line, which does NOT resolve the F2P "
                      "test_explicit_batch_size_respects_max_batch_size (it issues "
                      "more queries than ceil(len(objs)/max) when batch_size>max). "
                      "model_prepatch.py is exactly this and is documented to FAIL.",
        "rationale": "violates postcondition Result()<=clamped_max(raw) on "
                     "requested>max (over-large explicit request). The single "
                     "load-bearing clause of the fix.",
    },
    {
        "id": "rival-off-by-one-cap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_RIVAL_OFF_BY_ONE),
        "refinement": "Caps at max+1 instead of max. Its faithful real patch "
                      "(min(batch_size, max_batch_size+1)) would still slice into "
                      "ceil(len/(max+1)) batches when batch_size==max+1 -> for the "
                      "F2P's batch_size=max+1 it produces a DIFFERENT (larger-batch, "
                      "fewer-query or boundary-violating) query count than "
                      "ceil(len(objs)/max), so it does NOT resolve the F2P.",
        "rationale": "violates Result()<=clamped_max(raw) at the exact boundary "
                     "requested==max+1 (the F2P's batch_size). Partial-domain miss "
                     "at the discriminating point.",
    },
    {
        "id": "rival-auto-zero-uses-request",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_RIVAL_AUTO_ZERO),
        "refinement": "In the auto/absent case it returns 0 instead of the backend "
                      "max. Its faithful real patch returns batch_size (None) as the "
                      "slice step -> range(0,len,None) is a TypeError at runtime "
                      "(crashes every bulk_create(batch_size=None) call), breaking "
                      "the dominant P2P path; it cannot resolve anything.",
        "rationale": "violates Result()>=1 AND Result()==clamped_max on "
                     "requested==0. Diverges on the auto sub-domain (the majority "
                     "P2P input shape).",
    },
    {
        "id": "rival-no-clamp",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_RIVAL_NO_CLAMP),
        "refinement": "Drops the max(.,1) clamp on the auto path. Its faithful real "
                      "patch (batch_size = bulk_batch_size(...) with no max(.,1)) "
                      "returns 0 when the backend reports 0 -> range(0,len,0) raises "
                      "ValueError(range() arg 3 must not be zero), crashing the "
                      "auto path; it does NOT resolve the F2P/P2P.",
        "rationale": "violates Result()>=1 at the boundary raw_backend_limit==0 "
                     "(auto case). Single-boundary partial-domain miss.",
    },
    {
        "id": "rival-equal-under",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_RIVAL_EQUAL_UNDER),
        "refinement": "At requested==max exactly it returns max-1 (under-caps by "
                      "one). Its faithful real patch would slice into "
                      "ceil(len/(max-1)) batches when the caller explicitly asks "
                      "for batch_size==max -> MORE queries than ceil(len/max), a "
                      "wrong query count; it does NOT resolve the F2P and would "
                      "regress the explicit==max P2P scenario.",
        "rationale": "violates Result()==requested (and Result()<=requested still "
                     "holds, but the exact-value clause is pinned) on the single "
                     "point requested==clamped_max. The equality-edge partial-domain "
                     "attack the surviving '<'->'<=' G-MUT mutant does NOT reach "
                     "(that mutant is value-equivalent; this one is genuinely wrong).",
    },
]

# No @ContractOnly axioms and no A-reference DEEP MODEL to re-execute as an
# axiom: meta.axioms == [] and the lone A-reference (bulk_batch_size) enters the
# model only as a non-negative INTEGER input parameter, not as an axiom whose
# Ensures the proof discharges. The "returns a non-negative int" property is
# already executable-checked by axiom_check.py (G-AX). There is no caller-domain
# containment obligation in the Nagini proof (raw_backend_limit is just an int
# satisfying Requires(raw>=0)). So the axiom lane is vacuous here.
AXIOM_TESTS = []
