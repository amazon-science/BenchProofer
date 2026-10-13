# properties.py — PBT manifest for sympy__sympy-23413. NOT a Nagini module; a
# record of adversarially-reasoned falsification cases. The runner
# (swebench_nagini.pbt) writes each SPEC_TESTS[*]["module"] to a temp file,
# runs Nagini verify on the HOST, and checks same_spec against the frozen
# model.py. Every variant is built by region-surgery: _swap edits ONLY the text
# INSIDE the # impl-start / # impl-end markers, so the frozen spec
# (axioms/pure/pre/post-conditions + signatures) is never touched and same_spec
# is guaranteed.
#
# Defended surface (model.py leftmost_pivot_column(found: List[int], n: int)):
#   * found is READ-ONLY: held at Acc(list_pred(found), 1/2) in BOTH Requires
#     and Ensures (only half permission). => FRAME-MUTATION probe is MANDATORY.
#   * Load-bearing postcondition (the clause the prepatch bug fails):
#       Implies(pivot_count(found, len(found)) <= n,
#               Result() == n - pivot_count(found, len(found)))   # ALL rows
#       Implies(pivot_count(found, len(found))  > n, Result() == 0)  # clamp
#       0 <= Result() and Result() <= n
#     pivot_count is a GROUNDED @Pure fold over `found` (front-recursive, fully
#     unfoldable by the verifier) — NOT an opaque answer-key. There is no wrong
#     "echo": the oracle is a function of the args. So UNGROUNDED-ORACLE-ECHO is
#     N/A (see 'assessment'); instead we ship an honest cheapest-impl positive
#     control (pos-branchless).
#   * Result is a plain int; no raise / return-channel / side-effect difference
#     invisible to the value abstraction => CONTROL-FLOW-EFFECT is N/A.
#   * The real bug (prepatch): only the bottom min(len(found), n) rows are
#     examined, so a pivot in a TOP row of a tall matrix is undercounted. That is
#     the discriminating behaviour; the partial-domain rivals reproduce it.
from pathlib import Path

INSTANCE = "sympy__sympy-23413"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The EXACT current impl-region body (between the # impl-start / # impl-end
# marker lines, which are NOT part of this string and are never edited). Every
# rival replaces this whole block with its own body; nothing outside the impl
# region changes, so same_spec holds by construction.
_IMPL = """\
    k = n
    i = 0
    while i < len(found):
        # invariants-start
        Invariant(Acc(list_pred(found), 1 / 2))
        Invariant(0 <= i and i <= len(found))
        Invariant(0 <= k and k <= n)
        Invariant(valid_flags(ToSeq(found)))
        # k = max(0, n - pivots among the first i rows)
        Invariant(Implies(pivot_count(ToSeq(found), i) <= n,
                          k == n - pivot_count(ToSeq(found), i)))
        Invariant(Implies(pivot_count(ToSeq(found), i) > n, k == 0))
        # invariants-end
        if k == 0:
            # Every column already holds a pivot; no further rows can help.
            # pivot_count is monotone, so the full count is still >= n.
            Assert(pivot_count_monotone(ToSeq(found), i, len(found)))
            break
        c = found[i]
        Assert(ToSeq(found)[i] == c)
        Assert(pivot_count(ToSeq(found), i + 1)
               == ToSeq(found)[(i + 1) - 1] + pivot_count(ToSeq(found), (i + 1) - 1))
        if c == 1:
            k = k - 1
        i = i + 1
    return k"""

if _IMPL not in _BASE:
    raise AssertionError("impl-region anchor drifted from model.py")


# =====================================================================
# 1. FRAME-MUTATION  (MANDATORY — found is read-only at Acc(...,1/2))
# =====================================================================
# A rival that WRITES to the read-only input `found` while otherwise computing
# the gold marker. Half-permission (1/2) is insufficient to mutate a list
# element, so Nagini must REJECT for INSUFFICIENT PERMISSION. The gold
# invariants/asserts are kept verbatim so the rejection is attributable to the
# write `found[i] = c`, not to a proof gap. (The write is a no-op value-wise:
# it stores back the same `c` it just read, so the postcondition would still be
# satisfied IF the permission existed — this isolates the permission failure.)
_FRAME_MUT = """\
    k = n
    i = 0
    while i < len(found):
        # invariants-start
        Invariant(Acc(list_pred(found), 1 / 2))
        Invariant(0 <= i and i <= len(found))
        Invariant(0 <= k and k <= n)
        Invariant(valid_flags(ToSeq(found)))
        # k = max(0, n - pivots among the first i rows)
        Invariant(Implies(pivot_count(ToSeq(found), i) <= n,
                          k == n - pivot_count(ToSeq(found), i)))
        Invariant(Implies(pivot_count(ToSeq(found), i) > n, k == 0))
        # invariants-end
        if k == 0:
            Assert(pivot_count_monotone(ToSeq(found), i, len(found)))
            break
        c = found[i]
        found[i] = c  # ILLEGAL: only Acc(list_pred(found), 1/2) held
        Assert(ToSeq(found)[i] == c)
        Assert(pivot_count(ToSeq(found), i + 1)
               == ToSeq(found)[(i + 1) - 1] + pivot_count(ToSeq(found), (i + 1) - 1))
        if c == 1:
            k = k - 1
        i = i + 1
    return k"""


# =====================================================================
# 2. PARTIAL-DOMAIN  (the real bug: examine only bottom min(len(found), n) rows)
# =====================================================================
# This is the prepatch skeleton itself (model_prepatch.py): it caps the loop at
# rows = min(len(found), n), so a pivot in a top row beyond min(m, n) is never
# counted. On found=[1,0,1], n=2 it returns 1 but the spec demands 0. It must be
# REJECTED on the postcondition Result() == n - pivot_count(found, len(found)).
_PARTIAL_MIN = """\
    rows = len(found)
    if n < rows:
        rows = n
    k = n
    i = 0
    while i < rows:
        # invariants-start
        Invariant(Acc(list_pred(found), 1 / 2))
        Invariant(0 <= rows and rows <= len(found))
        Invariant(0 <= i and i <= rows)
        Invariant(0 <= k and k <= n)
        Invariant(valid_flags(ToSeq(found)))
        Invariant(k == n - pivot_count(ToSeq(found), i))
        # invariants-end
        c = found[i]
        Assert(ToSeq(found)[i] == c)
        Assert(pivot_count(ToSeq(found), i + 1)
               == ToSeq(found)[(i + 1) - 1] + pivot_count(ToSeq(found), (i + 1) - 1))
        if c == 1:
            k = k - 1
        i = i + 1
    return k"""


# =====================================================================
# 3. PARTIAL-DOMAIN  (skip the FIRST/bottom row — i starts at 1)
# =====================================================================
# Correct on every matrix whose bottom row yields no pivot (found[0] == 0), but
# diverges whenever the bottom row IS a pivot (found[0] == 1): it never
# decrements k for that pivot, so it over-reports the marker by 1. On
# found=[1,0], n=2 the gold marker is 1 but this returns 2. Must be REJECTED.
_SKIP_FIRST = """\
    k = n
    i = 1 if len(found) > 0 else 0
    while i < len(found):
        # invariants-start
        Invariant(Acc(list_pred(found), 1 / 2))
        Invariant(0 <= i and i <= len(found))
        Invariant(0 <= k and k <= n)
        Invariant(valid_flags(ToSeq(found)))
        # invariants-end
        if k == 0:
            break
        c = found[i]
        if c == 1:
            k = k - 1
        i = i + 1
    return k"""


# =====================================================================
# 4. UNIQUENESS  (no clamp at 0 — drop the k==0 break, allow k to go negative)
# =====================================================================
# Returns n - (all-rows pivot count) WITHOUT clamping at 0. When there are more
# pivots than columns (pivot_count > n, e.g. found=[1,1,1], n=2) the gold marker
# is 0 but this returns a negative k, violating BOTH 0 <= Result() and the
# clamp clause Implies(pivot_count > n, Result() == 0). Must be REJECTED.
_NO_CLAMP = """\
    k = n
    i = 0
    while i < len(found):
        # invariants-start
        Invariant(Acc(list_pred(found), 1 / 2))
        Invariant(0 <= i and i <= len(found))
        Invariant(valid_flags(ToSeq(found)))
        Invariant(k == n - pivot_count(ToSeq(found), i))
        # invariants-end
        c = found[i]
        Assert(ToSeq(found)[i] == c)
        Assert(pivot_count(ToSeq(found), i + 1)
               == ToSeq(found)[(i + 1) - 1] + pivot_count(ToSeq(found), (i + 1) - 1))
        if c == 1:
            k = k - 1
        i = i + 1
    return k"""


# =====================================================================
# 5. POSITIVE CONTROL  (soundness — branchless decrement; MUST verify)
# =====================================================================
# Structurally different from the gold impl: the `if c == 1: k = k - 1` branch
# is replaced by the branchless `k = k - c`. Since valid_flags pins c in {0,1}
# (and Assert(ToSeq(found)[i] == c) re-establishes it), k - c == k - found[i],
# and pivot_count(found, i+1) == c + pivot_count(found, i), so every gold
# invariant/assert still discharges. We KEEP the per-element pin and the
# pivot_count unfold assert (directive: a positive control must retain the
# framing it still needs). Forward loop direction is kept (the @Pure fold is
# front-recursive — a backward flip would need a fold-split lemma the verifier
# can't auto-discharge). MUST verify; if it cannot => SPEC-TOO-STRONG.
_POS_BRANCHLESS = """\
    k = n
    i = 0
    while i < len(found):
        # invariants-start
        Invariant(Acc(list_pred(found), 1 / 2))
        Invariant(0 <= i and i <= len(found))
        Invariant(0 <= k and k <= n)
        Invariant(valid_flags(ToSeq(found)))
        Invariant(Implies(pivot_count(ToSeq(found), i) <= n,
                          k == n - pivot_count(ToSeq(found), i)))
        Invariant(Implies(pivot_count(ToSeq(found), i) > n, k == 0))
        # invariants-end
        if k == 0:
            Assert(pivot_count_monotone(ToSeq(found), i, len(found)))
            break
        c = found[i]
        Assert(ToSeq(found)[i] == c)
        Assert(pivot_count(ToSeq(found), i + 1)
               == ToSeq(found)[(i + 1) - 1] + pivot_count(ToSeq(found), (i + 1) - 1))
        k = k - c
        i = i + 1
    return k"""


# =====================================================================
# 6. POSITIVE CONTROL  (soundness — reordered guard / hoisted local; MUST verify)
# =====================================================================
# A second structurally-different-but-correct shape: the k==0 break is hoisted
# to a `while i < len(found) and k != 0` guard plus an explicit per-iteration
# decrement local `dec`. The body keeps the gold framing asserts. Because the
# loop exits when k == 0 OR i reaches the end, on a normal exit either i ==
# len(found) (full count) or k == 0 (monotone => full count >= n), matching the
# postcondition. MUST verify (else SPEC-TOO-STRONG). We keep the monotone lemma
# Assert for the k==0 exit path inside the loop body before the natural step.
_POS_GUARD = """\
    k = n
    i = 0
    while i < len(found):
        # invariants-start
        Invariant(Acc(list_pred(found), 1 / 2))
        Invariant(0 <= i and i <= len(found))
        Invariant(0 <= k and k <= n)
        Invariant(valid_flags(ToSeq(found)))
        Invariant(Implies(pivot_count(ToSeq(found), i) <= n,
                          k == n - pivot_count(ToSeq(found), i)))
        Invariant(Implies(pivot_count(ToSeq(found), i) > n, k == 0))
        # invariants-end
        if k == 0:
            Assert(pivot_count_monotone(ToSeq(found), i, len(found)))
            break
        Assert(ToSeq(found)[i] == found[i])
        Assert(pivot_count(ToSeq(found), i + 1)
               == ToSeq(found)[(i + 1) - 1] + pivot_count(ToSeq(found), (i + 1) - 1))
        dec = found[i]
        k = k - dec
        i = i + 1
    return k"""


# =====================================================================
# 7. ADMISSIBILITY  (precondition admits a normal F2P-shaped input; MUST verify)
# =====================================================================
# Before the real work, re-invoke leftmost_pivot_column on the SAME in-domain
# input it received (`found`, `n`): the precondition Acc(list_pred(found),1/2) +
# valid_flags(ToSeq(found)) + n >= 0 are exactly what we already hold, so the
# self-call establishes Requires and the returned 1/2 permission is restored
# before the loop. This is a genuine, representative (caller-supplied, F2P-
# shaped) admissibility witness. If the call site cannot establish Requires for
# a legitimate input => PRECOND-TOO-STRONG. (No Decreases in the gold model, so
# the self-call carries no termination obligation under Nagini's default.)
_ADMISS = """\
    _adm = leftmost_pivot_column(found, n)
    Assert(0 <= _adm and _adm <= n)
    k = n
    i = 0
    while i < len(found):
        # invariants-start
        Invariant(Acc(list_pred(found), 1 / 2))
        Invariant(0 <= i and i <= len(found))
        Invariant(0 <= k and k <= n)
        Invariant(valid_flags(ToSeq(found)))
        Invariant(Implies(pivot_count(ToSeq(found), i) <= n,
                          k == n - pivot_count(ToSeq(found), i)))
        Invariant(Implies(pivot_count(ToSeq(found), i) > n, k == 0))
        # invariants-end
        if k == 0:
            Assert(pivot_count_monotone(ToSeq(found), i, len(found)))
            break
        c = found[i]
        Assert(ToSeq(found)[i] == c)
        Assert(pivot_count(ToSeq(found), i + 1)
               == ToSeq(found)[(i + 1) - 1] + pivot_count(ToSeq(found), (i + 1) - 1))
        if c == 1:
            k = k - 1
        i = i + 1
    return k"""


SPEC_TESTS = [
    {
        "id": "frame-mut-write-found",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _FRAME_MUT),
        "refinement": (
            "Its faithful real patch would MUTATE the input DomainMatrix entries "
            "of `A` (the read-only operand abstracted to `found`) to compute the "
            "marker. The gold patch never writes the per-row pivot-outcome source "
            "in place to decide k; a patch that did would corrupt the caller's "
            "matrix and could not produce the gold retained submatrix on the F2P "
            "matrices (test_hermite_normal / test_issue_23410), so it would NOT "
            "resolve. The write is value-preserving here, so a VERIFYING result "
            "would mean the spec lets a mutating impl satisfy the postcondition "
            "vacuously — a verify-without-permission-discipline break."
        ),
        "rationale": (
            "MUST be rejected for INSUFFICIENT PERMISSION: the precondition grants "
            "only Acc(list_pred(found), 1/2) and the postcondition re-Ensures 1/2, "
            "so `found[i] = c` (a write needing full permission) is not frameable. "
            "Rejection comes from the fractional-permission system, not the value "
            "postcondition (the gold invariants/asserts are kept verbatim)."
        ),
    },
    {
        "id": "partial-domain-min-rows",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _PARTIAL_MIN),
        "refinement": (
            "This IS the pre-patch buggy routine (rows = min(m, n); "
            "for i in range(m-1, m-1-rows, -1)). Its faithful real patch is the "
            "base_commit code, which drops the top pivot column: "
            "Matrix([[1,12],[0,8],[0,5]]) -> [[12],[8],[5]] instead of "
            "[[1,0],[0,8],[0,5]], failing test_issue_23410 and test_hermite_normal "
            "(the [[2,7],[0,0],[0,0]] -> 1-col case). It does NOT resolve."
        ),
        "rationale": (
            "Rejected on the load-bearing postcondition "
            "Implies(pivot_count(found,len(found)) <= n, "
            "Result() == n - pivot_count(found,len(found))): capping the loop at "
            "min(len(found), n) undercounts pivots in top rows, so on found=[1,0,1], "
            "n=2 it returns 1 while the spec (all-rows count = 2) demands 0. This is "
            "exactly the G-DIFF clause (model_prepatch.py:92-93)."
        ),
    },
    {
        "id": "partial-domain-skip-bottom-row",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _SKIP_FIRST),
        "refinement": (
            "A real patch that began the row loop at the second-from-bottom row "
            "(range(m-1, ...) but skipping index m-1) would never reduce against "
            "the bottom row's pivot, retaining one extra column. On the issue "
            "matrix family (e.g. the row3 hint [[0,12],[0,8],[1,5]] whose only "
            "pivot is in a non-bottom row vs a bottom-pivot matrix) it gives the "
            "wrong retained submatrix, so it would NOT resolve the F2P."
        ),
        "rationale": (
            "Rejected on the postcondition: it is correct exactly when found[0]==0 "
            "but diverges when the bottom row is a pivot (found[0]==1) — it omits "
            "that pivot's decrement, returning n while the spec demands "
            "n - pivot_count(found, len(found)). Partial-domain over the "
            "bottom-row sub-domain."
        ),
    },
    {
        "id": "uniqueness-no-clamp-negative-k",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _NO_CLAMP),
        "refinement": (
            "A real patch that removed the `if k == 0: break` guard would, on a "
            "matrix with more pivot rows than columns (n < m with n pivots already "
            "found, e.g. the test_hermite_normal [[2,7],[0,0],[0,0]] / a full-pivot "
            "tall matrix), let k underflow past 0 and slice with a negative column "
            "index — producing a wrongly-shaped (or erroring) submatrix that does "
            "NOT match the gold HNF, so it would NOT resolve."
        ),
        "rationale": (
            "Rejected on TWO postcondition clauses: 0 <= Result() and "
            "Implies(pivot_count(found,len(found)) > n, Result() == 0). On "
            "found=[1,1,1], n=2 (pivot_count=3 > n=2) it returns -1, violating both "
            "the lower bound and the clamp. The k==0 break is the gold patch's new "
            "hunk; dropping it is a real omission."
        ),
    },
    {
        "id": "pos-control-branchless",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL, _POS_BRANCHLESS),
        "rationale": (
            "A correct, structurally-different impl: `if c == 1: k = k - 1` is "
            "replaced by the branchless `k = k - c`. valid_flags pins c in {0,1} "
            "and the gold framing (per-element pin + pivot_count unfold assert + "
            "monotone lemma on the k==0 exit) is kept verbatim, so the loop "
            "invariant still discharges. MUST verify (else SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "pos-control-hoisted-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL, _POS_GUARD),
        "rationale": (
            "A second correct reshape: the decrement goes through an explicit "
            "local `dec = found[i]` (so the per-element value is read once and the "
            "k==0 monotone-lemma assert sits before the natural step). Same forward "
            "direction, same gold framing kept. MUST verify (else SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "admissibility-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL, _ADMISS),
        "rationale": (
            "Re-invokes leftmost_pivot_column on the SAME caller-supplied "
            "in-domain (found, n): the precondition (Acc 1/2 + valid_flags + "
            "n >= 0) is exactly what is already held, the 1/2 permission is "
            "returned, and Ensures gives 0 <= _adm <= n. The precondition admits a "
            "normal F2P-shaped input (else PRECOND-TOO-STRONG)."
        ),
    },
]


# No @ContractOnly axioms in this bundle (meta.axioms == []; the axioms region
# is empty). The changed marker logic is modeled DEEPLY (pivot_count fold + the
# verified loop) and validated against the real callee out-of-band by
# axiom_check.py / G-AX. There is no consumed-axiom Ensures and no A-reference
# deep model whose soundness rides on a contract the proof consumes. The axiom
# lane is therefore N/A here. (The deep-model-vs-real-callee cross-check is
# G-AX's job, already PASS at apply_gold=True; re-encoding it as a PBT probe
# would duplicate G-AX, not falsify a different obligation.)
AXIOM_TESTS = []
