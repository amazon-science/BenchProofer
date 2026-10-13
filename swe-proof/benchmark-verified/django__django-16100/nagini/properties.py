# properties.py — PBT falsification battery for django__django-16100.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant that shares the FROZEN spec (only
# the # impl-start..# impl-end region — including its nested invariants — is
# edited, guaranteeing markers.same_spec) and is checked by the Nagini verifier.
# Each AXIOM_TESTS case is a self-contained probe run in the instance Docker
# image.
#
# Defended surface (reasoned, not mechanical):
#   apply_batch(original, newvals, fails) — three READ-ONLY inputs carrying
#   Acc(list_pred(·), 1/2); a full-permission List[int] Result(). The
#   load-bearing postcondition is the Forall-k clause
#       Result()[k] == committed_value(original[k], newvals[k], any_fails(fails,0))
#   whose verdict any_fails(fails, 0) is BATCH-GLOBAL (computed at index 0, the
#   SAME for every row). That is the all-or-nothing content of the gold patch
#   (wrap the list-editable save loop in transaction.atomic): a failure ANYWHERE
#   discards EVERY replacement, with no committed prefix.
#
# Oracle groundedness: committed_value / any_fails are @Pure but FULLY GROUNDED
# in the args (a recursive fold over `fails` and a ternary on the row values) —
# there is no opaque answer-key to echo, so the ungrounded-oracle-echo class is
# N/A; it is replaced by an honest cheapest-impl positive control. See the
# module-level assessment string at the bottom for the full per-class rationale.

from pathlib import Path

INSTANCE = "django__django-16100"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors INSIDE the impl region (between # impl-start and # impl-end). Editing
# only these keeps markers.same_spec True (the spec_view elides the whole impl
# region, nested invariants included).
# ---------------------------------------------------------------------------

# The commit-loop branch that writes each row's committed value.
_COMMIT_BRANCH = """        old_seq = ToSeq(result)
        if failed:
            result = result + [original[j]]
        else:
            result = result + [newvals[j]]"""

# The first (staging) loop that sets `failed` once a failing edit is reached.
_STAGE_LOOP_BREAK = """        if fails[i] == 1:
            # This edit's processing raises: the batch fails as a whole and the
            # grouped writes are discarded.
            failed = True
            break
        i = i + 1"""


# ===========================================================================
# 1. POSITIVE CONTROL (soundness) — a structurally-different CORRECT impl that
#    MUST verify. Reorder the commit-loop branches (test `not failed` first) and
#    reshape with an explicit local. Keeps the front-recursive any_fails proof
#    obligations and every framing assert verbatim, so it is a SPEC test, not a
#    proof-gap test. If a faithful correct impl can't verify => SPEC-TOO-STRONG.
# ===========================================================================
_POS = _swap(
    _BASE,
    _COMMIT_BRANCH,
    """        old_seq = ToSeq(result)
        committed = 0  # type: int
        if not failed:
            committed = newvals[j]
            result = result + [committed]
        else:
            committed = original[j]
            result = result + [committed]""",
)


# ===========================================================================
# 2. ADMISSIBILITY — the precondition must admit a normal, F2P-shaped input.
#    Stage an inline self-call on the two-row F2P witness (orig=[4,2],
#    new=[9,5], fails=[0,1] — first form succeeds, second raises) and Assert the
#    all-or-nothing verdict it predicts (both rows revert: committed == [4,2]).
#    Built with FRESH lists so the read-only 1/2 permission on the outer inputs
#    is untouched. If the Requires can't be established for this legitimate input
#    => PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS_CALL = """    # admissibility probe: a normal F2P-shaped batch is in-domain.
    ao = [4, 2]  # type: List[int]
    an = [9, 5]  # type: List[int]
    af = [0, 1]  # type: List[int]
    Assert(Acc(list_pred(ao), 1 / 2))
    Assert(Acc(list_pred(an), 1 / 2))
    Assert(Acc(list_pred(af), 1 / 2))
    Assert(len(ao) == len(an))
    Assert(len(ao) == len(af))
    # second edit fails -> batch-global verdict True -> every row reverts.
    failed = False
    i = 0"""
_ADMISS = _swap(_BASE, "    failed = False\n    i = 0", _ADMISS_CALL)


# ===========================================================================
# 3. FRAME-MUTATION (MANDATORY — three read-only inputs). A rival that WRITES to
#    a read-only input. Here it overwrites `original[j]` in place before reading
#    it, then commits the (correct) values. The spec keeps Acc(list_pred(
#    original), 1/2) — half permission — so an in-place write is REJECTED for
#    INSUFFICIENT PERMISSION, regardless of the value claim. A byte fuzzer never
#    thinks to mutate the input.
#    refinement: a real patch that mutates the persistent store rows in place
#    while "rolling back" is not what transaction.atomic does (it discards staged
#    writes; it does not author the stored values via the model objects passed
#    in). Such a patch would corrupt the rows on the success path and would not
#    faithfully implement the atomic grouping; it would not be the gold edit and
#    is excluded by the read-only contract.
# ===========================================================================
_FRAME = _swap(
    _BASE,
    _COMMIT_BRANCH,
    """        old_seq = ToSeq(result)
        if failed:
            original[j] = original[j]  # WRITE to a read-only (1/2-perm) input
            result = result + [original[j]]
        else:
            result = result + [newvals[j]]""",
)


# ===========================================================================
# 4. PARTIAL-DOMAIN (the PREPATCH bug) — committed-prefix rival. Use the LOCAL
#    tail verdict any_fails(fails, j) for each row instead of the batch-global
#    any_fails(fails, 0). On a mid-batch failure (first failing edit at index
#    >= 1) the rows BEFORE the failure see a False local verdict and keep their
#    replacement (a committed prefix), while the postcondition pins the
#    batch-global verdict (True for all). This must REJECT against the Forall-k
#    clause.
#    refinement: this IS the pre-patch behaviour (per-write autocommit) — the
#    gold patch's whole point is to remove the committed prefix. The F2P
#    scenario side_effect=[None, DatabaseError] (first form succeeds, second
#    raises) would persist the first form's edit under this rival (a.load==9),
#    but the test asserts a.load==4. So a faithful real patch of this shape FAILS
#    the F2P. Rejection comes from the batch-global any_fails(fails,0) in the
#    postcondition.
# ===========================================================================
_PARTIAL_PREFIX = _swap(
    _BASE,
    _COMMIT_BRANCH,
    """        old_seq = ToSeq(result)
        if fails[j] == 1 or any_fails(ToSeq(fails), j + 1):  # LOCAL tail, not global
            result = result + [original[j]]
        else:
            result = result + [newvals[j]]""",
)


# ===========================================================================
# 5. PARTIAL-DOMAIN (first-row special-case) — a rival that ignores the
#    batch-global verdict for ROW 0 only and always commits newvals[0]. Correct
#    on the all-success domain and on any batch whose intended row-0 value is its
#    replacement, but WRONG on a failing batch (row 0 must revert to original[0]).
#    The F2P first scenario (side_effect=DatabaseError on the first form) is
#    exactly this: row 0 must revert to a.load==4, but this rival commits the
#    replacement (9). Must REJECT against the Forall-k clause at k==0.
#    refinement: a real patch that special-cases the first edited form to persist
#    unconditionally would leave a.load==9 on the first F2P scenario; the test
#    asserts a.load==4. It is not the gold atomic-wrap and fails the F2P.
# ===========================================================================
_PARTIAL_FIRST = _swap(
    _BASE,
    _COMMIT_BRANCH,
    """        old_seq = ToSeq(result)
        if j == 0:
            result = result + [newvals[j]]  # row 0 always commits its replacement
        elif failed:
            result = result + [original[j]]
        else:
            result = result + [newvals[j]]""",
)


# ===========================================================================
# 6. SUPPORTING near-miss (commit-condition inversion) — commit newvals on
#    failure / original on success (verdict flipped). Cheap mechanical mutant
#    that any tight postcondition rejects; kept only as a supporting positive
#    that the runner discriminates verdict polarity.
#    refinement: a patch that commits replacements precisely when the batch
#    FAILED and reverts on success is nonsensical w.r.t. transaction.atomic and
#    would fail every F2P assertion (both scenarios expect originals preserved on
#    failure). Rejection comes from committed_value's polarity in the postcond.
# ===========================================================================
_FLIP = _swap(
    _BASE,
    _COMMIT_BRANCH,
    """        old_seq = ToSeq(result)
        if failed:
            result = result + [newvals[j]]  # flipped: commit replacement on FAILURE
        else:
            result = result + [original[j]]""",
)


SPEC_TESTS = [
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS,
        "rationale": (
            "structurally-different but CORRECT impl: commit loop tests `not "
            "failed` first and binds the committed value to a typed local before "
            "appending. Keeps the front-recursive any_fails proof and every "
            "framing assert verbatim, so it must verify; else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-f2p-witness",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the F2P-shaped witness orig=[4,2] new=[9,5] fails=[0,1] (second edit "
            "raises) establishes the Requires for a normal input: every clause is "
            "asserted AT the witness. It is asserted rather than exercised by a "
            "self-call because the model carries Requires(MustTerminate(2)) and a "
            "same-level self-call on a non-shrinking argument is an obligation leak "
            "Nagini is right to refuse. If the precond rejects this legitimate input "
            "=> PRECOND-TOO-STRONG. NEGATIVE CONTROL (measured): move the witness "
            "outside the frozen len(original)==len(fails) clause, af = [0, 1, 1] "
            "against ao = [4, 2], and the probe REJECTS: `Assert might fail. "
            "Assertion (len(ao) == len(af)) might not hold.` The asserted domain is "
            "a real check on this precondition, not a restatement of it."
        ),
    },
    {
        "id": "frame-mutate-original",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME,
        "refinement": (
            "a real patch that writes the persistent store rows in place while "
            "'rolling back' is not transaction.atomic (which discards staged "
            "writes, it does not re-author stored values via the passed-in model "
            "objects); on the success path it would corrupt the rows. It is not "
            "the gold edit and would not faithfully resolve the F2P."
        ),
        "rationale": (
            "MANDATORY frame-mutation: writes `original[j]` although the spec "
            "keeps Acc(list_pred(original), 1/2). Must fail for INSUFFICIENT "
            "PERMISSION (the half-permission read-only contract), independent of "
            "the value claim."
        ),
    },
    {
        "id": "partial-prefix-local-verdict",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_PREFIX,
        "refinement": (
            "this IS the pre-patch behaviour: a LOCAL per-row tail verdict leaves "
            "a committed prefix on a mid-batch failure. The F2P scenario "
            "side_effect=[None, DatabaseError] (first form succeeds, second "
            "raises) would persist the first form's edit (a.load==9), but the test "
            "asserts a.load==4. A faithful real patch of this shape FAILS the F2P."
        ),
        "rationale": (
            "uses any_fails(fails, j) (local) instead of the batch-global "
            "any_fails(fails, 0). REJECTED inside the commit loop at "
            "model.py:161-162, on the assertion that pins the row just appended to "
            "the batch-global verdict (ToSeq(result) == old_seq + "
            "PSeq(committed_value(..., any_fails(ToSeq(fails), 0)))) -- the per-row "
            "restatement of the postcondition Forall-k clause, which is the clause "
            "that forbids a committed prefix. Measured verbatim: `Assert might fail` "
            "on that assertion. If it VERIFIES => SPEC-TOO-WEAK (a batch could "
            "commit the rows before the first failure)."
        ),
    },
    {
        "id": "partial-first-row-always-commit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_FIRST,
        "refinement": (
            "special-casing the first edited form to persist unconditionally "
            "leaves a.load==9 on the F2P first scenario (side_effect=DatabaseError "
            "on the first form), where the test asserts a.load==4. Not the gold "
            "atomic-wrap; fails the F2P."
        ),
        "rationale": (
            "row 0 always commits newvals[0], ignoring the batch-global verdict. "
            "Rejected by the Forall-k clause at k==0 on any failing batch "
            "(committed_value(orig[0], new[0], True) == orig[0])."
        ),
    },
    {
        "id": "support-verdict-flip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FLIP,
        "refinement": (
            "commits replacements precisely when the batch FAILED and reverts on "
            "success — nonsensical w.r.t. transaction.atomic; both F2P scenarios "
            "expect originals preserved on failure, so it fails the F2P."
        ),
        "rationale": (
            "SUPPORTING near-miss: flips committed_value polarity. Rejected by the "
            "postcondition's committed_value(orig,new,any_fails) on the failure "
            "branch."
        ),
    },
]


# ===========================================================================
# AXIOM lane. meta.json axioms == [] (NO consumed @ContractOnly axiom). The
# correctness of this bundle rests on the A-reference deep model
# committed_value/any_fails == the real django.db.transaction.atomic
# commit/rollback verdict (deep_model_references[0], checked by G-AX /
# axiom_check.py). The kind here is axiom-soundness on that A-reference: run the
# REAL transaction.atomic block over in-memory SQLite, inject a failure at each
# position (and none) + F2P witnesses + fuzz, and assert the committed rows ==
# the deep model. The probe embeds axiom_check.py's own logic (it is NOT mounted
# in-container; the runner mounts only the probe), CALLS the real callee (never
# scrapes source), and opens nothing on disk (no codec risk).
# ===========================================================================

# Read the bundle oracle on the HOST at manifest-load time and embed its source.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")

AXIOM_TESTS = [
    {
        "id": "ax-ref-atomic-rollback-soundness",
        "axiom": "committed_value / any_fails (A-reference: transaction.atomic)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": (
            "AXIOM-UNSOUND if the deep model committed_value/any_fails disagrees "
            "with the real django.db.transaction.atomic commit/rollback verdict "
            "on any in-domain batch. The probe stages a batch of row writes inside "
            "a REAL atomic block over in-memory SQLite, injects a failure at every "
            "position (and none) + the two F2P witnesses + 2000 fuzz batches, reads "
            "the committed rows back, and asserts they equal the deep model (full "
            "replacement on success, full revert with NO committed prefix on any "
            "failure). Exit 0 iff sound. This is the A-reference soundness G-AX "
            "checks; there is no consumed axiom so axiom-containment is N/A."
        ),
    },
]
