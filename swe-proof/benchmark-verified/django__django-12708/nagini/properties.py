"""PBT falsification battery for django__django-12708.

Manifest parsed by swebench_nagini.pbt. Each SPEC_TEST is a full model.py
variant that shares the FROZEN spec (axioms/pure/pre/post-conditions) and edits
ONLY text inside the impl region (# impl-start .. # impl-end, which contains the
nested invariants region). same_spec is therefore guaranteed by region-surgery:
every _swap target lives strictly between # impl-start and # impl-end.

Defended surface (read from model.py + refinement.md + mapping.md + the F2P):
  selected_for_removal(constraints: List[int]) -> int
    Requires(Acc(list_pred(constraints), 1/2))          # READ-ONLY input
    Ensures (Acc(list_pred(constraints), 1/2))          # frame restored
    Ensures (Result() == count_selected(ToSeq(constraints)))   # LOAD-BEARING
    Ensures (Result() >= 0 and Result() <= len(constraints))

  count_selected is GROUNDED: a fully-unfolded front-recursive fold over
  ToSeq(constraints), counting codes with selects(code) = is_index(code) and
  not is_unique(code). It is NOT an opaque answer-key oracle -- there is no
  "wrong echo" that verifies, because echoing it IS doing the work. So the
  ungrounded-oracle class is N/A; we supply an honest cheapest-impl positive
  control (return count_selected(ToSeq(constraints))) instead (see assessment).

  The discriminating bit is `not is_unique(code)` (the gold patch's added
  `'unique': False`). The pre-patch over-broad selection counted every index
  (keeps_any_index / is_index only); on a candidate set carrying a co-located
  UNIQUE constraint (code 3) alongside a plain index (code 1) the two diverge
  -- exactly the F2P scenario test_alter_index_together_remove_with_unique_together
  (count 2 -> ValueError pre-patch; count 1 -> clean removal post-patch).
"""
from pathlib import Path

INSTANCE = "django__django-12708"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen gold branch test inside the impl region (the only place the
# selection filter is spelled out in executable code).
_GOLD_BRANCH = "        if is_index(code) and not is_unique(code):\n            selected = selected + 1"


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (expect verify)
# ---------------------------------------------------------------------------

# pos-control-selects: structurally-different but CORRECT. Keep the backward
# loop, the gold invariants and the two framing asserts VERBATIM (so the gold
# proof obligations are preserved -- pilot bug #2/#3 avoided: no loop-direction
# flip against the front-recursive fold, no dropped framing asserts). Only the
# executable branch test is reshaped to call the @Pure helper `selects`, which
# is DEFINED as exactly `is_index(code) and not is_unique(code)` -- so it is the
# same predicate the spec fold count_selected uses, and the loop invariant
# `selected == count_selected(...drop(i))` still discharges.
_POS_SELECTS = _swap(
    _BASE,
    _GOLD_BRANCH,
    "        if selects(code):\n            selected = selected + 1",
)

# pos-control-cheapest: the honest cheapest impl -- return the grounded fold
# directly. Because the postcondition's oracle count_selected is a function of
# the args (not an opaque key), this DOES do the work and MUST verify. It is the
# positive control that demonstrates the oracle is grounded (no wrong echo).
_POS_CHEAPEST = _swap(
    _BASE,
    """    selected = 0
    i = len(constraints)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(constraints), 1 / 2))
        Invariant(0 <= i and i <= len(constraints))
        Invariant(selected == count_selected(ToSeq(constraints).drop(i)))
        Invariant(selected >= 0 and selected <= len(constraints) - i)
        Invariant(MustTerminate(i + 1))
        # invariants-end
        code = constraints[i - 1]
        Assert(ToSeq(constraints).drop(i - 1)[0] == code)
        Assert(ToSeq(constraints).drop(i - 1).drop(1) == ToSeq(constraints).drop(i))
        if is_index(code) and not is_unique(code):
            selected = selected + 1
        i = i - 1
    return selected""",
    "    return count_selected(ToSeq(constraints))",
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY (expect verify) -- precondition accepts an F2P-shaped input
# ---------------------------------------------------------------------------

# admiss-f2p: a self-contained caller that constructs the exact F2P-shaped
# candidate set -- a co-located UNIQUE constraint (code 3 = index+unique) and a
# plain index (code 1 = index, not unique) -- and calls selected_for_removal,
# asserting the precondition is establishable for it and the result is in
# domain. The new function is appended INSIDE the impl region of the original
# (after the gold `return selected`, before # impl-end) so the frozen spec is
# untouched. If the precondition could not be met for this normal input the
# call site would fail to verify -> PRECOND-TOO-STRONG.
_ADMISS = _swap(
    _BASE,
    "    return selected\n    # impl-end",
    """    return selected


def _admiss_caller() -> None:
    # impl-only helper: build the F2P-shaped candidate set and call the modeled
    # function. list_pred(full) is freshly created here, so Acc(.,1/2) holds.
    cand = [3, 1]  # type: List[int]
    n = selected_for_removal(cand)
    # the precondition admitted a normal input; result is in domain
    Assert(n >= 0)
    Assert(n <= 2)
    # impl-end""",
)


# ---------------------------------------------------------------------------
# FRAME-MUTATION (expect reject) -- MANDATORY: input is read-only Acc(.,1/2)
# ---------------------------------------------------------------------------

# frame-write: a rival that WRITES to the read-only input `constraints` to try
# to satisfy the postcondition vacuously. With only Acc(list_pred(constraints),
# 1/2) a write needs full permission, so this MUST be rejected for INSUFFICIENT
# PERMISSION (not for a value mismatch). The gold counting loop and invariants
# are kept verbatim so the rejection is attributable solely to the write.
# refinement: a faithful real patch that mutates the introspection candidate
# set (e.g. clearing/zeroing entries) before counting would corrupt the
# constraints the removal pipeline operates on and could not resolve the F2P
# (it would not perform the genuine index-vs-unique discrimination, and would
# scribble over django's introspection state).
_FRAME = _swap(
    _BASE,
    "    selected = 0\n    i = len(constraints)",
    "    selected = 0\n    constraints[0] = 0  # frame violation: write to read-only input\n    i = len(constraints)",
)


# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN / over-broad selection (expect reject)
# ---------------------------------------------------------------------------

# weak-overbroad-prepatch: the EXACT pre-patch bug -- drop the `not is_unique`
# conjunct so the rival counts every index (keeps_any_index). It is correct on
# every candidate set with no co-located unique constraint, but diverges on the
# F2P scenario [3, 1]: count 2 instead of 1. Because the loop invariant pins
# `selected == count_selected(...)` (the non-unique-index count), this WRONG
# count cannot satisfy the postcondition -> reject. Must change the invariant
# too, else it is an obvious proof failure rather than a spec sensing; but the
# invariant lives inside the impl region so same_spec is preserved. We make the
# invariant track the rival's own (wrong) running count so the failure surfaces
# at the postcondition Result()==count_selected, not mid-loop.
# refinement: the faithful real patch is the PRE-patch `{'index': True}` kwargs
# (no `unique` filter). On unique_together + index_together on the same columns
# it matches BOTH constraints -> len 2 -> _delete_composed_index raises
# ValueError("Found wrong number (2) of constraints ...") -- exactly the bug the
# F2P reproduces, so it does NOT resolve.
_WEAK_OVERBROAD = _swap(
    _BASE,
    """        Invariant(selected == count_selected(ToSeq(constraints).drop(i)))
        Invariant(selected >= 0 and selected <= len(constraints) - i)
        Invariant(MustTerminate(i + 1))
        # invariants-end
        code = constraints[i - 1]
        Assert(ToSeq(constraints).drop(i - 1)[0] == code)
        Assert(ToSeq(constraints).drop(i - 1).drop(1) == ToSeq(constraints).drop(i))
        if is_index(code) and not is_unique(code):
            selected = selected + 1""",
    """        Invariant(selected == count_any_index(ToSeq(constraints).drop(i)))
        Invariant(selected >= 0 and selected <= len(constraints) - i)
        Invariant(MustTerminate(i + 1))
        # invariants-end
        code = constraints[i - 1]
        Assert(ToSeq(constraints).drop(i - 1)[0] == code)
        Assert(ToSeq(constraints).drop(i - 1).drop(1) == ToSeq(constraints).drop(i))
        if is_index(code):
            selected = selected + 1""",
)


# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN / wrong-bit selection (expect reject)
# ---------------------------------------------------------------------------

# weak-pick-unique: a rival that selects the UNIQUE-and-index constraints
# (is_index AND is_unique) instead of the plain index. Agrees with the gold on
# any set with no co-located unique constraint where there are no plain indexes,
# but on the F2P scenario [3, 1] it counts 1 for the WRONG element (the unique
# constraint) and 0 for the plain index -- selecting code 3, not code 1. The
# postcondition Result()==count_selected (which counts code 1) rejects it.
# refinement: a faithful real patch passing `{'index': True, 'unique': True}`
# would select the UNIQUE constraint for removal, dropping the user's
# unique_together and leaving the plain index -- the F2P asserts the unique
# constraint STILL exists and the plain index is gone, so it would fail.
_WEAK_PICK_UNIQUE = _swap(
    _BASE,
    """        Invariant(selected == count_selected(ToSeq(constraints).drop(i)))
        Invariant(selected >= 0 and selected <= len(constraints) - i)
        Invariant(MustTerminate(i + 1))
        # invariants-end
        code = constraints[i - 1]
        Assert(ToSeq(constraints).drop(i - 1)[0] == code)
        Assert(ToSeq(constraints).drop(i - 1).drop(1) == ToSeq(constraints).drop(i))
        if is_index(code) and not is_unique(code):
            selected = selected + 1""",
    """        Invariant(selected >= 0 and selected <= len(constraints) - i)
        Invariant(MustTerminate(i + 1))
        # invariants-end
        code = constraints[i - 1]
        Assert(ToSeq(constraints).drop(i - 1)[0] == code)
        Assert(ToSeq(constraints).drop(i - 1).drop(1) == ToSeq(constraints).drop(i))
        if is_index(code) and is_unique(code):
            selected = selected + 1""",
)


# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN / first-element drop (expect reject)
# ---------------------------------------------------------------------------

# weak-skip-first: a near-miss that correctly applies selects(code) but guards
# the increment with `i > 1`, never counting the first-processed candidate
# (constraints[0]). Correct on every input whose first element is not a plain
# index, but diverges when constraints[0] is a plain index (code 1): the lone
# plain index [1] is gold-count 1, rival-count 0. (On the F2P set [3,1] the
# first-processed element is code 3, so the divergence is exposed by the
# sub-domain witness [1], not by [3,1] itself -- this is a genuine partial-domain
# attack: correct on most inputs, wrong on the sub-domain where the only plain
# index is first-processed.) The postcondition Result()==count_selected rejects.
# refinement: a real patch that fails to consider the first candidate constraint
# in the column-match loop would miss removing a plain index declared first,
# leaving the index present -- the F2P assertIndexNotExists would fail whenever
# the plain index is the first-iterated constraint.
_WEAK_SKIP = _swap(
    _BASE,
    """        Invariant(selected == count_selected(ToSeq(constraints).drop(i)))
        Invariant(selected >= 0 and selected <= len(constraints) - i)
        Invariant(MustTerminate(i + 1))
        # invariants-end
        code = constraints[i - 1]
        Assert(ToSeq(constraints).drop(i - 1)[0] == code)
        Assert(ToSeq(constraints).drop(i - 1).drop(1) == ToSeq(constraints).drop(i))
        if is_index(code) and not is_unique(code):
            selected = selected + 1
        i = i - 1""",
    """        Invariant(selected >= 0 and selected <= len(constraints) - i)
        Invariant(MustTerminate(i + 1))
        # invariants-end
        code = constraints[i - 1]
        Assert(ToSeq(constraints).drop(i - 1)[0] == code)
        Assert(ToSeq(constraints).drop(i - 1).drop(1) == ToSeq(constraints).drop(i))
        if i > 1 and is_index(code) and not is_unique(code):
            selected = selected + 1
        i = i - 1""",
)


SPEC_TESTS = [
    {
        "id": "pos-control-selects",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_SELECTS,
        "rationale": "structurally-different CORRECT impl: same backward loop, "
        "gold invariants/asserts kept verbatim, branch test reshaped to the "
        "@Pure helper selects(code) (defined as exactly is_index and not "
        "is_unique). Same predicate the spec fold uses, so the invariant "
        "selected==count_selected(...drop(i)) still discharges. Must verify "
        "(else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-control-cheapest",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CHEAPEST,
        "rationale": "honest cheapest impl: return the grounded fold "
        "count_selected(ToSeq(constraints)) directly. The oracle is a function "
        "of the args (grounded, fully unfolded), so returning it IS doing the "
        "work -- it must verify. Demonstrates there is no ungrounded answer-key "
        "to echo.",
    },
    {
        "id": "admiss-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "an impl-region caller builds the F2P-shaped input [3,1] "
        "(co-located unique + plain index) and calls selected_for_removal; the "
        "freshly created list_pred satisfies Acc(.,1/2). If the precondition "
        "could not be established for this normal input the call site would "
        "fail -> PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME,
        "refinement": "a faithful real patch that writes over the introspection "
        "candidate set before counting would corrupt django's introspection "
        "state and would not perform the genuine index-vs-unique "
        "discrimination -- it could not resolve the F2P (and would not be a "
        "legitimate read-only schema-introspection step).",
        "rationale": "input is read-only Acc(list_pred(constraints),1/2); the "
        "write constraints[0]=0 needs full permission. MUST reject for "
        "INSUFFICIENT PERMISSION (permission system), not a value mismatch. "
        "#1 weakness class.",
    },
    {
        "id": "weak-overbroad-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_OVERBROAD,
        "refinement": "the faithful real patch is the PRE-patch {'index': True} "
        "kwargs (drop the 'unique': False conjunct). On unique_together + "
        "index_together on the same columns it matches BOTH constraints -> "
        "len 2 -> _delete_composed_index raises ValueError('Found wrong number "
        "(2) of constraints') -- exactly the bug; does NOT resolve the F2P.",
        "rationale": "drops `not is_unique`, counting count_any_index instead "
        "of count_selected. Diverges on co-located unique [3,1] (2 vs 1). The "
        "postcondition Result()==count_selected(ToSeq(constraints)) rejects the "
        "over-count. (Rejection from the load-bearing postcondition clause.)",
    },
    {
        "id": "weak-pick-unique",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_PICK_UNIQUE,
        "refinement": "a faithful real patch passing {'index': True, 'unique': "
        "True} would select the UNIQUE constraint for removal, dropping the "
        "user's unique_together and leaving the plain index. The F2P asserts the "
        "unique constraint STILL exists and the index is gone -> fails.",
        "rationale": "selects is_index AND is_unique (the wrong bit). On [3,1] "
        "it counts code 3 (1) not code 1, diverging from count_selected. The "
        "postcondition rejects it. (Rejection from Result()==count_selected.)",
    },
    {
        "id": "weak-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_SKIP,
        "refinement": "a real patch that fails to consider the first candidate "
        "constraint in the column-match loop would miss removing a plain index "
        "declared first, leaving the index present -- the F2P's "
        "assertIndexNotExists fails whenever the plain index is first-iterated.",
        "rationale": "guards the increment with `i > 1`, skipping the count for "
        "constraints[0]. Diverges on any set whose only plain index sits at the "
        "first-processed position (e.g. [1]: gold 1, rival 0). The "
        "postcondition Result()==count_selected rejects the under-count. "
        "(Partial-domain: correct on most inputs, wrong on a sub-domain.)",
    },
]


# No @ContractOnly axioms in this bundle (axioms region empty by design; the
# only callee _constraint_names is an A-reference, validated == the real callee
# by axiom_check.py / G-AX). No axiom-soundness / axiom-containment obligation
# to probe in the axiom lane.
AXIOM_TESTS = []
