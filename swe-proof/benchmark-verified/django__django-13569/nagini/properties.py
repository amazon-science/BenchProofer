"""PBT falsification battery for django__django-13569.

NOT a Nagini module: a manifest of adversarial cases the runner
(swebench_nagini.pbt) executes. Each SPEC_TESTS entry is a full model.py
variant built by region-surgery: ONLY the text inside an # impl-start/#
impl-end region is swapped, so the frozen spec (axioms/pure/pre/post/invariant
regions) is byte-for-byte identical and `same_spec` holds by construction.

Defended surface (see model.py):

  random_group_by_cols(colid) -- the grouping columns a single
    non-deterministic (Random) ordering term offers. NO read-only input
    (colid: int by value). Load-bearing postcondition: len(Result()) == 0
    (equivalently ToSeq(Result()) == offered_cols(1, colid), the empty PSeq).
    The oracle offered_cols(1, colid) is GROUNDED -- it fully unfolds, by the
    @Pure definition, to the empty sequence for any non-zero first arg; there is
    no opaque answer-key to echo. So the ungrounded-oracle-echo class does NOT
    apply here; the honest positive control plays the soundness role.

  group_by_columns_for_ordering(nondet, ref, cols) -- gathers, in order, each
    term's contribution, skipping reference terms. THREE read-only inputs at
    Acc(list_pred(.), 1/2) -> FRAME-MUTATION is MANDATORY. Load-bearing
    postcondition: ToSeq(Result()) == gathered(ToSeq(nondet), ToSeq(ref),
    ToSeq(cols)). The oracle gathered(...) is GROUNDED (a pure front-fold fully
    unfolded over the args).

There are NO @ContractOnly axioms (axioms region holds only a note). The two
A-references (random_group_by_cols->[] ; offered_cols/gathered == real gather)
are validated by axiom_check.py / G-AX, not consumed by the proof. They are NOT
re-probed here (the spec lane does not depend on an axiom Ensures); AXIOM_TESTS
is therefore empty and the axiom lane is N/A for this instance.
"""
from pathlib import Path

INSTANCE = "django__django-13569"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: %r" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r" % (old,))
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The two gold impl regions, verbatim, used as the anchors for region-surgery.
# Only text BETWEEN these anchors (i.e. inside an impl region) is ever edited.
# ---------------------------------------------------------------------------

_RGBC_IMPL = """    # impl-start
    result = []  # type: List[int]
    return result
    # impl-end"""

_GBCO_IMPL = """    # impl-start
    result = []  # type: List[int]
    i = len(nondet)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(nondet), 1 / 2))
        Invariant(Acc(list_pred(ref), 1 / 2))
        Invariant(Acc(list_pred(cols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(ref) == len(nondet) and len(cols) == len(nondet))
        Invariant(0 <= i and i <= len(nondet))
        # `result` already holds the columns gathered from the tail [i, n).
        Invariant(ToSeq(result) == gathered(ToSeq(nondet).drop(i),
                                            ToSeq(ref).drop(i),
                                            ToSeq(cols).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        # The tail starting at j = i-1 is non-empty (i > 0, lengths equal), so
        # unfolding `gathered` on it takes the recursive branch. Link the list
        # values to the head elements of the dropped tails so the unfold's
        # internal head reads agree with the branch taken below.
        Assert(len(ToSeq(nondet).drop(i - 1)) == len(nondet) - (i - 1))
        Assert(ToSeq(nondet).drop(i - 1)[0] == nondet[i - 1])
        Assert(ToSeq(ref).drop(i - 1)[0] == ref[i - 1])
        Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
        Assert(ToSeq(nondet).drop(i - 1).drop(1) == ToSeq(nondet).drop(i))
        Assert(ToSeq(ref).drop(i - 1).drop(1) == ToSeq(ref).drop(i))
        Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
        if ref[i - 1] != 0:
            # A reference term offers nothing: gathered(tail j) == gathered(i).
            result = result
        elif nondet[i - 1] != 0:
            contributed = random_group_by_cols(cols[i - 1])
            # `offered_cols(nondet[i-1], ...)` and `offered_cols(1, ...)` agree:
            # both arguments are non-zero, so both are the empty sequence.
            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
                   offered_cols(1, cols[i - 1]))
            result = contributed + result
        else:
            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
                   PSeq(cols[i - 1]))
            result = [cols[i - 1]] + result
        i = i - 1
    return result
    # impl-end"""

# Sanity: the anchors must be present exactly once in the frozen model.
assert _BASE.count(_RGBC_IMPL) == 1, "RGBC impl anchor drift"
assert _BASE.count(_GBCO_IMPL) == 1, "GBCO impl anchor drift"


# ===========================================================================
# random_group_by_cols cases
# ===========================================================================

# --- POSITIVE CONTROL (soundness): structurally-different CORRECT impl. ------
# The gold builds the empty list directly. A correct, differently-shaped impl:
# branch on whether colid is positive and build the empty result both ways
# (the value is empty regardless). Keeps len(Result())==0 and
# ToSeq(Result())==offered_cols(1, colid) (the empty seq). MUST verify.
_RGBC_POS = """    # impl-start
    result = []  # type: List[int]
    if colid > 0:
        result = result
    else:
        result = result
    return result
    # impl-end"""

# --- UNIQUENESS / partial-domain (reject): the prepatch bug echo. -----------
# A non-deterministic term offers ITSELF (the inherited BaseExpression default
# `[self]`), injecting RANDOM() into the GROUP BY. Length 1, not 0. Faithful
# real patch: NO override of Random.get_group_by_cols -> the inherited default
# returns [self] -> `GROUP BY ..., RANDOM()` -> the F2P
# test_aggregation_random_ordering FAILS (rows not grouped). Must REJECT
# (fails len(Result()) == 0).
_RGBC_SELF = """    # impl-start
    result = [colid]  # type: List[int]
    return result
    # impl-end"""


# ===========================================================================
# group_by_columns_for_ordering cases
# ===========================================================================

# --- POSITIVE CONTROL (soundness): branch-reorder, same backward loop. ------
# Reorder the dispatch: test the deterministic (else) condition first via an
# explicit `if`, then the non-deterministic, then the reference skip last.
# Keeps the backward loop, ALL framing asserts, and every gold invariant -- so
# the front-recursive `gathered` unfold still discharges. Only the executable
# branch ORDER changes (the computed value per term is identical). MUST verify.
_GBCO_POS = """    # impl-start
    result = []  # type: List[int]
    i = len(nondet)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(nondet), 1 / 2))
        Invariant(Acc(list_pred(ref), 1 / 2))
        Invariant(Acc(list_pred(cols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(ref) == len(nondet) and len(cols) == len(nondet))
        Invariant(0 <= i and i <= len(nondet))
        # `result` already holds the columns gathered from the tail [i, n).
        Invariant(ToSeq(result) == gathered(ToSeq(nondet).drop(i),
                                            ToSeq(ref).drop(i),
                                            ToSeq(cols).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(len(ToSeq(nondet).drop(i - 1)) == len(nondet) - (i - 1))
        Assert(ToSeq(nondet).drop(i - 1)[0] == nondet[i - 1])
        Assert(ToSeq(ref).drop(i - 1)[0] == ref[i - 1])
        Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
        Assert(ToSeq(nondet).drop(i - 1).drop(1) == ToSeq(nondet).drop(i))
        Assert(ToSeq(ref).drop(i - 1).drop(1) == ToSeq(ref).drop(i))
        Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
        if ref[i - 1] == 0 and nondet[i - 1] == 0:
            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
                   PSeq(cols[i - 1]))
            result = [cols[i - 1]] + result
        elif ref[i - 1] == 0:
            contributed = random_group_by_cols(cols[i - 1])
            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
                   offered_cols(1, cols[i - 1]))
            result = contributed + result
        else:
            # A reference term offers nothing: gathered(tail j) == gathered(i).
            result = result
        i = i - 1
    return result
    # impl-end"""

# --- ADMISSIBILITY (verify): a positive-control caller establishing the ------
# precondition for a normal F2P-shaped input (3 equal-length lists; one
# random, one deterministic, one reference -- the exact shape the F2P query
# produces) then self-calling. If the Requires cannot be met for this input,
# PRECOND-TOO-STRONG. Built inside random_group_by_cols' impl region as a
# self-contained helper-free assertion of admissibility: we keep the gold
# random_group_by_cols impl and ASSERT its postcondition is establishable, plus
# bind a representative equal-length triple to show the gathering precondition
# (len(ref)==len(nondet)==len(cols)) is satisfiable. (Surgery stays inside the
# impl region; the spec is untouched.)
_RGBC_ADMISS = """    # impl-start
    result = []  # type: List[int]
    # Admissibility witness: a normal F2P-shaped ordering list has three
    # index-aligned, equal-length descriptor lists. Build one and assert the
    # length precondition of group_by_columns_for_ordering is satisfiable for
    # it -- the precondition admits a normal input (else PRECOND-TOO-STRONG).
    nd = [1, 0, 0]   # type: List[int]
    rf = [0, 0, 1]   # type: List[int]
    cl = [7, 9, 9]   # type: List[int]
    Assert(len(rf) == len(nd) and len(cl) == len(nd))
    Assert(len(nd) == 3)
    return result
    # impl-end"""

# --- UNIQUENESS / weakness (reject): the ACTUAL bug -- include the random ----
# term's column. In the non-deterministic branch, contribute [cols[i-1]]
# instead of the empty random_group_by_cols(...). Faithful real patch: the
# gathering loop extends with the Random expr's [self] (no override) -> RANDOM()
# enters GROUP BY -> F2P FAILS (the bug the issue reports). Must REJECT: the
# gathered value then contains cols[i-1] for the nondet term, but
# offered_cols(nondet[i-1], ...) is the EMPTY seq, so
# ToSeq(Result()) != gathered(...). Rejection comes from postcondition clause
# ToSeq(Result()) == gathered(...).
_GBCO_INCLUDE_RANDOM = """    # impl-start
    result = []  # type: List[int]
    i = len(nondet)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(nondet), 1 / 2))
        Invariant(Acc(list_pred(ref), 1 / 2))
        Invariant(Acc(list_pred(cols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(ref) == len(nondet) and len(cols) == len(nondet))
        Invariant(0 <= i and i <= len(nondet))
        Invariant(ToSeq(result) == gathered(ToSeq(nondet).drop(i),
                                            ToSeq(ref).drop(i),
                                            ToSeq(cols).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(len(ToSeq(nondet).drop(i - 1)) == len(nondet) - (i - 1))
        Assert(ToSeq(nondet).drop(i - 1)[0] == nondet[i - 1])
        Assert(ToSeq(ref).drop(i - 1)[0] == ref[i - 1])
        Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
        Assert(ToSeq(nondet).drop(i - 1).drop(1) == ToSeq(nondet).drop(i))
        Assert(ToSeq(ref).drop(i - 1).drop(1) == ToSeq(ref).drop(i))
        Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
        if ref[i - 1] != 0:
            result = result
        else:
            # BUG: contribute the term's own column even for a non-deterministic
            # term -- exactly the pre-patch leak of RANDOM() into the GROUP BY.
            result = [cols[i - 1]] + result
        i = i - 1
    return result
    # impl-end"""

# --- UNIQUENESS / partial-domain (reject): correct on every term EXCEPT the --
# first-processed (last-index) term, which it silently drops. The backward loop
# starts at i = len(nondet) - 1 (instead of len(nondet)), so the term at the
# highest index never contributes. Correct on all OTHER terms; diverges only on
# a non-empty list whose last term is non-reference. Faithful real patch: a
# gather loop that skips the last order_by term -> the GROUP BY misses that
# term's column (or, for the F2P, this is just a wrong loop bound) -> grouping
# differs from gold -> F2P/P2P FAILS. Must REJECT: on the prefix-missing the
# last term, ToSeq(Result()) != gathered(...). Rejection from the loop bound
# making the invariant ToSeq(result)==gathered(.drop(i)) unestablishable at
# entry (i starts at n-1, but result starts empty == gathered(.drop(n))).
_GBCO_DROP_LAST = """    # impl-start
    result = []  # type: List[int]
    i = len(nondet) - 1
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(nondet), 1 / 2))
        Invariant(Acc(list_pred(ref), 1 / 2))
        Invariant(Acc(list_pred(cols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(ref) == len(nondet) and len(cols) == len(nondet))
        Invariant(0 <= i and i <= len(nondet))
        Invariant(ToSeq(result) == gathered(ToSeq(nondet).drop(i),
                                            ToSeq(ref).drop(i),
                                            ToSeq(cols).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(len(ToSeq(nondet).drop(i - 1)) == len(nondet) - (i - 1))
        Assert(ToSeq(nondet).drop(i - 1)[0] == nondet[i - 1])
        Assert(ToSeq(ref).drop(i - 1)[0] == ref[i - 1])
        Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
        Assert(ToSeq(nondet).drop(i - 1).drop(1) == ToSeq(nondet).drop(i))
        Assert(ToSeq(ref).drop(i - 1).drop(1) == ToSeq(ref).drop(i))
        Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
        if ref[i - 1] != 0:
            result = result
        elif nondet[i - 1] != 0:
            contributed = random_group_by_cols(cols[i - 1])
            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
                   offered_cols(1, cols[i - 1]))
            result = contributed + result
        else:
            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
                   PSeq(cols[i - 1]))
            result = [cols[i - 1]] + result
        i = i - 1
    return result
    # impl-end"""

# --- FRAME-MUTATION (reject for INSUFFICIENT PERMISSION): write a read-only ---
# input. The gathering loop's three carriers (nondet/ref/cols) are
# Acc(list_pred(.), 1/2) -- READ-ONLY. A rival that WRITES into `cols` to make
# the gathered value come out right (here: zero out the last column so the
# gathered seq "matches") must FAIL: a write needs full permission, but the
# precondition grants only 1/2. Gold invariants/postcondition kept verbatim so
# the rejection is attributable to the write, NOT to a broken proof. Faithful
# real patch: the gather loop must not mutate the order_by list -- a patch that
# overwrites order_by entries to fix grouping is not the gold fix and would
# corrupt ORDER BY, breaking aggregation tests (P2P) -> would NOT resolve. Must
# REJECT for insufficient permission (the half-permission frame condition).
_GBCO_FRAME_MUT = """    # impl-start
    result = []  # type: List[int]
    # FRAME MUTATION: write to the read-only input `cols` (granted only 1/2
    # permission). This must be rejected for insufficient permission.
    cols[0] = 0
    i = len(nondet)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(nondet), 1 / 2))
        Invariant(Acc(list_pred(ref), 1 / 2))
        Invariant(Acc(list_pred(cols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(ref) == len(nondet) and len(cols) == len(nondet))
        Invariant(0 <= i and i <= len(nondet))
        Invariant(ToSeq(result) == gathered(ToSeq(nondet).drop(i),
                                            ToSeq(ref).drop(i),
                                            ToSeq(cols).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(len(ToSeq(nondet).drop(i - 1)) == len(nondet) - (i - 1))
        Assert(ToSeq(nondet).drop(i - 1)[0] == nondet[i - 1])
        Assert(ToSeq(ref).drop(i - 1)[0] == ref[i - 1])
        Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
        Assert(ToSeq(nondet).drop(i - 1).drop(1) == ToSeq(nondet).drop(i))
        Assert(ToSeq(ref).drop(i - 1).drop(1) == ToSeq(ref).drop(i))
        Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
        if ref[i - 1] != 0:
            result = result
        elif nondet[i - 1] != 0:
            contributed = random_group_by_cols(cols[i - 1])
            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
                   offered_cols(1, cols[i - 1]))
            result = contributed + result
        else:
            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
                   PSeq(cols[i - 1]))
            result = [cols[i - 1]] + result
        i = i - 1
    return result
    # impl-end"""


SPEC_TESTS = [
    # ---- random_group_by_cols ------------------------------------------------
    {
        "id": "rgbc-pos-control",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _RGBC_IMPL, _RGBC_POS),
        "rationale": "structurally-different CORRECT impl of random_group_by_cols "
                     "(branch on colid sign, build empty both ways); the value is "
                     "still the empty list, so len(Result())==0 and "
                     "ToSeq(Result())==offered_cols(1,colid) hold. Must verify, "
                     "else SPEC-TOO-STRONG.",
    },
    {
        "id": "rgbc-admiss",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _RGBC_IMPL, _RGBC_ADMISS),
        "rationale": "asserts a normal F2P-shaped ordering list (three equal-length "
                     "descriptor lists, one random/one deterministic/one reference) "
                     "satisfies the length precondition of "
                     "group_by_columns_for_ordering; the precondition admits a "
                     "normal input. Must verify, else PRECOND-TOO-STRONG.",
    },
    {
        "id": "rgbc-self-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _RGBC_IMPL, _RGBC_SELF),
        "refinement": "this IS the pre-patch behaviour: with no override, Random "
                      "inherits BaseExpression.get_group_by_cols which returns "
                      "[self] (length 1). The faithful real patch (no override) "
                      "emits GROUP BY ..., RANDOM(), so rows are NOT grouped and the "
                      "F2P test_aggregation_random_ordering FAILS -> would NOT "
                      "resolve.",
        "rationale": "rejected by postcondition clause len(Result())==0 (and "
                     "ToSeq(Result())==offered_cols(1,colid), the empty seq): a "
                     "length-1 result violates both. If it verified, SPEC-TOO-WEAK.",
    },
    # ---- group_by_columns_for_ordering --------------------------------------
    {
        "id": "gbco-pos-control",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GBCO_IMPL, _GBCO_POS),
        "rationale": "branch-REORDER positive control: dispatch deterministic-leaf "
                     "first, then non-deterministic, then reference-skip last. Keeps "
                     "the backward loop, every gold framing Assert and Invariant "
                     "(so the front-recursive `gathered` unfold still discharges); "
                     "only the executable branch order changes, the per-term value "
                     "is identical. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "gbco-frame-mutation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GBCO_IMPL, _GBCO_FRAME_MUT),
        "refinement": "writing into the order_by carrier to coerce the grouping is "
                      "NOT the gold fix; mutating ORDER BY terms in get_group_by "
                      "would corrupt ordering and break the 67 P2P aggregation tests "
                      "-> would NOT resolve. The gold patch reads the terms only.",
        "rationale": "the three inputs are Acc(list_pred(.), 1/2) = READ-ONLY; the "
                     "write `cols[0] = 0` needs full permission, so it is rejected "
                     "for INSUFFICIENT PERMISSION by the fractional-permission frame "
                     "condition. Gold invariants/postcondition kept verbatim so the "
                     "rejection is attributable to the write. A byte-fuzzer never "
                     "constructs this.",
    },
    {
        "id": "gbco-include-random",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GBCO_IMPL, _GBCO_INCLUDE_RANDOM),
        "refinement": "contributing the non-deterministic term's own column is "
                      "exactly the pre-patch leak: RANDOM() enters the GROUP BY, "
                      "rows are not grouped, and the F2P "
                      "test_aggregation_random_ordering FAILS -> would NOT resolve.",
        "rationale": "rejected by postcondition ToSeq(Result())==gathered(...): for "
                      "a non-deterministic term offered_cols(nondet[k],...) is the "
                      "EMPTY seq, so the gathered oracle omits cols[k]; the rival "
                      "includes it, so the values differ. If it verified, "
                      "SPEC-TOO-WEAK.",
    },
    {
        "id": "gbco-drop-last-term",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GBCO_IMPL, _GBCO_DROP_LAST),
        "refinement": "a gather loop whose bound silently drops the highest-index "
                      "order_by term omits that term's column from the GROUP BY "
                      "(or, for a deterministic last term, loses a needed grouping "
                      "column) -> grouping differs from gold -> the F2P/P2P "
                      "aggregation tests FAIL -> would NOT resolve.",
        "rationale": "PARTIAL-DOMAIN: correct on every term except the "
                      "first-processed (last-index) one, which is never visited "
                      "(loop starts at i=len-1). Rejected by the loop invariant "
                      "ToSeq(result)==gathered(ToSeq(.).drop(i)): on entry result is "
                      "empty but gathered(.drop(len-1)) need not be empty, so the "
                      "invariant is not established. If it verified, SPEC-TOO-WEAK.",
    },
]


# No @ContractOnly axioms and no consumed axioms (axioms region is a note only).
# The two A-references (random_group_by_cols->[] ; offered_cols/gathered == the
# real order-by gather) are validated out-of-band by axiom_check.py / G-AX and
# are NOT consumed by the proof, so there is no axiom Ensures the spec lane
# relies on. The axiom lane is therefore N/A for this instance.
AXIOM_TESTS = []  # type: list
