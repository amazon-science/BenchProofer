# properties.py — PBT falsification battery for django__django-11885.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a full model.py variant produced by REGION SURGERY: only the text
# strictly inside `# impl-start` / `# impl-end` is swapped, so the frozen spec
# (axioms / pure / pre / post-conditions, and the elided invariants) is never
# touched and `same_spec` is guaranteed.
#
# DEFENDED SURFACE (what this spec pins):
#   combined_fast_delete_count(related_tables: List[int]) -> int
#   * Requires/Ensures Acc(list_pred(related_tables), 1/2)  -> READ-ONLY input.
#   * Result() == distinct_count(ToSeq(related_tables))      <- THE load-bearing
#       clause: result equals the number of DISTINCT related-table identities
#       (the number of combined bulk fast-delete removals). distinct_count is a
#       @Pure FRONT-RECURSIVE fold fully GROUNDED in the arg (no opaque oracle),
#       so `return distinct_count(...)` is a *correct* cheapest impl (positive
#       control), NOT a wrong echo — see assessment.
#   * Result() in [0, len], and >= 1 for a non-empty run.
#
# The F2P (test_fast_delete_combined_relationships) deletes a Referrer whose
# SecondReferrer has TWO FKs (referrer, other_referrer) both pointing at
# Referrer, and asserts assertNumQueries(2): the two FK candidates that share
# one related table must collapse into ONE combined removal. In carrier terms
# that is related_tables == [r, r] with distinct_count == 1. Any rival that
# counts 2 there (one-per-candidate) does NOT resolve the F2P.

from pathlib import Path

INSTANCE = "django__django-11885"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact impl-region body of the frozen model (backward fold). Every variant
# is built by replacing THIS block (which lives strictly inside
# # impl-start / # impl-end) with a new body.
_IMPL = """    count = 0
    i = len(related_tables)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(related_tables), 1 / 2))
        Invariant(0 <= i and i <= len(related_tables))
        Invariant(count == distinct_count(ToSeq(related_tables).drop(i)))
        Invariant(count >= 0 and count <= len(related_tables) - i)
        # invariants-end
        table = related_tables[i - 1]
        Assert(ToSeq(related_tables).drop(i - 1)[0] == table)
        Assert(ToSeq(related_tables).drop(i - 1).drop(1) == ToSeq(related_tables).drop(i))
        # A related table is counted at its FIRST occurrence: count it iff it
        # does not appear later in the run (i.e. in the already-processed
        # suffix). This combines the columns of a table that recurs into one
        # removal.
        if not contains(ToSeq(related_tables).drop(i), table):
            count = count + 1
        i = i - 1
    return count"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found in base")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r} occurs {src.count(old)} times")
    return src.replace(old, new, 1)


def _impl_variant(new_body):
    """Build a full model.py whose impl region is `new_body` (everything else,
    incl. the frozen spec, byte-identical to model.py)."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL 1 (soundness): honest cheapest impl. distinct_count is fully
# grounded in the arg, so directly returning it is a *correct* implementation
# that must verify. If it CANNOT, the postcondition is unsatisfiable except by
# the gold proof shape => SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS_DIRECT = """    return distinct_count(ToSeq(related_tables))"""

# ---------------------------------------------------------------------------
# POSITIVE CONTROL 2 (soundness): STRUCTURALLY-DIFFERENT but correct. Same
# backward fold and SAME invariants/framing asserts (kept verbatim — deleting
# them would fail the loop invariant for a PROOF reason, not a spec reason), but
# the executable membership test is reshaped into a local boolean `is_first`
# instead of an inline `if not contains(...)`. A faithful correct restructure
# that keeps the gold proof valid must verify (else SPEC-TOO-STRONG). We do NOT
# flip the loop direction: a forward append against the front-recursive
# distinct_count fold would need an f(a+b)==f(a)+f(b) lemma the verifier cannot
# auto-discharge (that is a proof gap, not a spec defect).
# ---------------------------------------------------------------------------
_POS_RESHAPE = """    count = 0
    i = len(related_tables)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(related_tables), 1 / 2))
        Invariant(0 <= i and i <= len(related_tables))
        Invariant(count == distinct_count(ToSeq(related_tables).drop(i)))
        Invariant(count >= 0 and count <= len(related_tables) - i)
        # invariants-end
        table = related_tables[i - 1]
        Assert(ToSeq(related_tables).drop(i - 1)[0] == table)
        Assert(ToSeq(related_tables).drop(i - 1).drop(1) == ToSeq(related_tables).drop(i))
        is_first = not contains(ToSeq(related_tables).drop(i), table)
        if is_first:
            count = count + 1
        else:
            count = count + 0
        i = i - 1
    return count"""

# ---------------------------------------------------------------------------
# ADMISSIBILITY: a positive-control self-call proving the precondition admits a
# normal F2P-shaped input. Inside the impl region we construct an F2P-shaped run
# [7, 7] (two FK candidates sharing one related table) as a freshly-allocated
# list literal — which establishes full list_pred(probe) permission — then CALL
# combined_fast_delete_count(probe) (whose Requires is only Acc(...,1/2), so the
# call site can hand over half permission) and assert the documented outcome
# r == 1 (the two shared-table candidates collapse to ONE combined removal). The
# function then still returns the real gold fold over its own argument, so the
# function verifies and any failure is purely call-site admissibility. If the
# Requires cannot be established for this legitimate input => PRECOND-TOO-STRONG.
# (Pattern proven in django__django-11119's admiss witness: a `probe = [...]
# # type: List[int]` literal auto-establishes list_pred and is callable.)
# ---------------------------------------------------------------------------
_ADMISS_IMPL = """    probe = [7, 7]  # type: List[int]
    r = combined_fast_delete_count(probe)
    # The two shared-table candidates collapse to ONE combined removal.
    assert r == 1
    count = 0
    i = len(related_tables)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(related_tables), 1 / 2))
        Invariant(0 <= i and i <= len(related_tables))
        Invariant(count == distinct_count(ToSeq(related_tables).drop(i)))
        Invariant(count >= 0 and count <= len(related_tables) - i)
        # invariants-end
        table = related_tables[i - 1]
        Assert(ToSeq(related_tables).drop(i - 1)[0] == table)
        Assert(ToSeq(related_tables).drop(i - 1).drop(1) == ToSeq(related_tables).drop(i))
        if not contains(ToSeq(related_tables).drop(i), table):
            count = count + 1
        i = i - 1
    return count"""

# ---------------------------------------------------------------------------
# FRAME-MUTATION (MANDATORY — input is read-only Acc(...,1/2)). A rival that
# WRITES to the read-only candidate run while otherwise computing the correct
# count. With only half permission held, an assignment related_tables[i-1] = ...
# must be rejected for INSUFFICIENT PERMISSION. The gold framing invariants/
# asserts are kept verbatim so the rejection is attributable solely to the
# write. REFINEMENT: a faithful real patch that mutated the candidate run
# (the ordered list of fast-removable relations) in place during planning would
# corrupt the collector's state and not produce the F2P's assertNumQueries(2);
# it would not resolve.
# ---------------------------------------------------------------------------
_FRAME_MUT = """    count = 0
    i = len(related_tables)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(related_tables), 1 / 2))
        Invariant(0 <= i and i <= len(related_tables))
        Invariant(count == distinct_count(ToSeq(related_tables).drop(i)))
        Invariant(count >= 0 and count <= len(related_tables) - i)
        # invariants-end
        table = related_tables[i - 1]
        Assert(ToSeq(related_tables).drop(i - 1)[0] == table)
        Assert(ToSeq(related_tables).drop(i - 1).drop(1) == ToSeq(related_tables).drop(i))
        # WRITE to the read-only input (only Acc(...,1/2) is held): must be
        # rejected for insufficient permission.
        related_tables[i - 1] = table
        if not contains(ToSeq(related_tables).drop(i), table):
            count = count + 1
        i = i - 1
    return count"""

# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN A: the PRE-PATCH one-removal-per-candidate behaviour. Returns
# len(related_tables) — correct exactly when all identities are distinct, wrong
# whenever any related table recurs. This is precisely the prepatch shape
# (model_prepatch.py) and DIVERGES on the F2P case [r, r] (returns 2, spec
# demands distinct_count == 1). expect=reject: it violates
# Result() == distinct_count(...). REFINEMENT: this is literally the unpatched
# Django (one fast_deletes.append per candidate) — it issues 2 queries for the
# shared-table case, failing assertNumQueries(2); it does NOT resolve the F2P.
# ---------------------------------------------------------------------------
_PARTIAL_LEN = """    count = len(related_tables)
    return count"""

# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN B: counts distinct correctly EXCEPT it never counts the very
# first element of the run (the i==1 step) as a new group. Correct on runs
# whose first element recurs later (a duplicate), but off-by-one (undercounts by
# 1) whenever the first element is unique — e.g. [3, 5] -> returns 1 not 2, and
# the all-distinct F2P-adjacent runs. It also breaks the >=1 lower bound for a
# singleton [r] (returns 0). expect=reject: violates
# Result() == distinct_count(...) on the first-element sub-domain. REFINEMENT:
# dropping the first distinct related model means that table's combined removal
# is never issued — the related rows are not cascade-deleted (an integrity bug),
# and the query count is wrong; it does not resolve.
# ---------------------------------------------------------------------------
_PARTIAL_FIRST = """    count = 0
    i = len(related_tables)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(related_tables), 1 / 2))
        Invariant(0 <= i and i <= len(related_tables))
        Invariant(count == distinct_count(ToSeq(related_tables).drop(i)))
        Invariant(count >= 0 and count <= len(related_tables) - i)
        # invariants-end
        table = related_tables[i - 1]
        Assert(ToSeq(related_tables).drop(i - 1)[0] == table)
        Assert(ToSeq(related_tables).drop(i - 1).drop(1) == ToSeq(related_tables).drop(i))
        if not contains(ToSeq(related_tables).drop(i), table):
            count = count + 1
        i = i - 1
    return count"""

# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN C (value double-mask / wrong predicate direction): counts a
# table at its LAST occurrence test but using the WRONG suffix — it tests
# membership in the FULL processed prefix-plus-self instead of the strict
# suffix, effectively `contains(drop(i-1), table)` which is ALWAYS true (table
# is at position 0 of drop(i-1)), so it NEVER increments -> returns 0 for any
# non-empty run. Violates Result()==distinct_count and the >=1 lower bound.
# REFINEMENT: zero combined removals means no fast-delete query is issued for
# any related table — the cascade silently drops all fast-deletable children;
# assertNumQueries(2) fails (0 such queries) and the delete is incorrect.
# ---------------------------------------------------------------------------
_PARTIAL_ZERO = """    count = 0
    i = len(related_tables)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(related_tables), 1 / 2))
        Invariant(0 <= i and i <= len(related_tables))
        Invariant(count == distinct_count(ToSeq(related_tables).drop(i)))
        Invariant(count >= 0 and count <= len(related_tables) - i)
        # invariants-end
        table = related_tables[i - 1]
        Assert(ToSeq(related_tables).drop(i - 1)[0] == table)
        Assert(ToSeq(related_tables).drop(i - 1).drop(1) == ToSeq(related_tables).drop(i))
        # WRONG: test the suffix INCLUDING self (drop(i-1)), which always
        # contains `table` at index 0 -> the increment never fires.
        if not contains(ToSeq(related_tables).drop(i - 1), table):
            count = count + 1
        i = i - 1
    return count"""


SPEC_TESTS = [
    {
        "id": "pos-direct-grounded-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_variant(_POS_DIRECT),
        "rationale": (
            "distinct_count is a @Pure fold fully grounded in the arg, so "
            "returning it directly is a CORRECT cheapest impl. It satisfies "
            "Result()==distinct_count(...) and the bounds (proved by "
            "distinct_count's own Ensures). Must verify; if not => SPEC-TOO-"
            "STRONG (the postcondition would be unsatisfiable except by the "
            "exact gold loop shape). Also the honest positive control showing "
            "there is no WRONG echo of the oracle (it is grounded, not opaque)."
        ),
    },
    {
        "id": "pos-reshape-local-bool",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_variant(_POS_RESHAPE),
        "rationale": (
            "Structurally-different correct impl: same backward fold + same "
            "invariants and framing asserts kept VERBATIM (so the gold proof "
            "obligations still discharge), only the membership test reshaped "
            "into a local boolean with an explicit else branch. A faithful "
            "restructure must verify; else SPEC-TOO-STRONG. (Loop direction is "
            "kept backward on purpose: a forward append would need a fold "
            "homomorphism lemma the verifier cannot auto-discharge.)"
        ),
    },
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_variant(_ADMISS_IMPL),
        "rationale": (
            "A positive-control self-call builds the F2P-shaped input [7, 7] "
            "(two FK candidates sharing one related table) as a fresh list "
            "literal (auto-establishing list_pred), calls "
            "combined_fast_delete_count (which Requires only Acc(...,1/2), so "
            "half permission is handed over) and asserts the documented "
            "outcome r==1 (one combined removal). If the Requires cannot be "
            "established for this legitimate input => PRECOND-TOO-STRONG. After "
            "the self-call the function still returns the real gold fold over "
            "its own argument, so any failure is purely call-site admissibility."
        ),
    },
    {
        "id": "frame-mutation-write-readonly",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_variant(_FRAME_MUT),
        "refinement": (
            "A faithful real patch that mutated the ordered run of "
            "fast-removable candidate relations in place during fast-delete "
            "planning would corrupt the Collector's state (the candidate list "
            "is consumed read-only by the grouping); it would not produce the "
            "F2P's assertNumQueries(2) and would not resolve."
        ),
        "rationale": (
            "MANDATORY frame-mutation probe. The input is read-only "
            "Acc(list_pred(related_tables), 1/2); the impl writes "
            "related_tables[i-1] = table while holding only half permission. "
            "Nagini must REJECT for INSUFFICIENT PERMISSION (write needs full "
            "permission). Rejection is attributable solely to the write — all "
            "gold framing invariants/asserts are kept verbatim. A byte-fuzzer "
            "never constructs this; it is the project's #1 weakness class."
        ),
    },
    {
        "id": "partial-domain-one-per-candidate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_variant(_PARTIAL_LEN),
        "refinement": (
            "This is literally the PRE-PATCH Django shape: one "
            "self.fast_deletes.append per candidate relation (count == number "
            "of candidates). On the F2P case [r, r] (SecondReferrer's two FKs "
            "to Referrer) it issues 2 fast-delete queries, so "
            "assertNumQueries(2) on the WHOLE delete fails (the combined query "
            "must be 1, total 2 including Referrer's own) — exactly what "
            "model_prepatch.py fails. It does NOT resolve the F2P."
        ),
        "rationale": (
            "Partial-domain rival correct only on all-distinct runs, wrong "
            "whenever a related table recurs. Violates the load-bearing "
            "Result() == distinct_count(ToSeq(related_tables)) (returns "
            "len(related_tables) >= distinct_count, strictly greater on any "
            "duplicate). If it verifies => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "partial-domain-skip-first-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_variant(_PARTIAL_FIRST),
        "refinement": (
            "Stopping the fold at i>1 never counts the first related model in "
            "the run as a new group, so its combined removal is never issued: "
            "those related rows are not cascade-deleted (an integrity bug) and "
            "the query count is short by one. assertNumQueries(2) fails; it "
            "does not resolve."
        ),
        "rationale": (
            "Partial-domain (first-element sub-domain) rival. Undercounts by 1 "
            "whenever the first element is a distinct identity (e.g. [3,5] -> "
            "1, singleton [r] -> 0), violating both Result()==distinct_count "
            "and the Implies(len>0, Result()>=1) lower bound. If it verifies "
            "=> SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "partial-domain-never-increment",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_variant(_PARTIAL_ZERO),
        "refinement": (
            "Testing membership in the suffix INCLUDING self (drop(i-1)) is "
            "always true, so the count never increments -> 0 removals for any "
            "non-empty run. No fast-delete query is issued for any related "
            "table; the cascade silently drops all fast-deletable children and "
            "assertNumQueries(2) fails (0 such queries). It does not resolve."
        ),
        "rationale": (
            "Value double-mask / wrong-suffix rival: returns 0 for any "
            "non-empty run, violating Result()==distinct_count and "
            "Implies(len>0, Result()>=1). If it verifies => SPEC-TOO-WEAK."
        ),
    },
]

# No @ContractOnly axiom is consumed (axioms region is empty; meta.axioms == []).
# The only deep-model reference, distinct_count (A-reference), is the
# fully-unfolded @Pure fold in the FROZEN spec itself and is validated equal to
# the real collections.defaultdict(list) grouping out-of-band by axiom_check.py
# (G-AX, status pass: 11 boundary + 50000 fuzz, no column dropped/duplicated,
# bounds hold). There is no @ContractOnly Ensures for a real callee to violate
# (axiom-soundness N/A) and no model-reachable callee input outside an axiom
# domain (the model reaches no axiomatized callee; axiom-containment N/A). So
# AXIOM_TESTS is empty by construction; see 'assessment'.
AXIOM_TESTS = []
