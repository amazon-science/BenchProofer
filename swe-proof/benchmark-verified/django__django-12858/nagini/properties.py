# properties.py — PBT manifest for django__django-12858. NOT a Nagini module; a
# record of adversarial cases the runner (swebench_nagini.pbt) executes + stamps.
#
# Spec under attack (FROZEN, never touched below): select_reported_paths takes
# three READ-ONLY (Acc(...,1/2)) index-aligned List[int] of 0/1 per examined
# ordering path — reached_field, is_value_op, is_compare_op — and returns a
# fresh fully-owned List[int] whose every element is pinned by the load-bearing
# postcondition clause:
#     Forall k in [0,len): Result()[k] == flag_path(reached_field[k],
#                                          is_value_op[k], is_compare_op[k])
# where the @Pure (spec-region) oracle flag_path reports (1) iff
#     reached_field==0 OR (is_value_op==0 AND is_compare_op==0).
# The gold change is the second disjunct's `is_compare_op==0` conjunct: a segment
# that is a registered comparison operator (Lookup, e.g. 'isnull') but not a
# value-producing operator (Transform) — with a field reached — must be ACCEPTED
# (flag 0). The F2P scenario is exactly the row (reached=1, value=0, compare=1).
#
# Every SPEC_TEST is built by region-surgery: _swap edits ONLY text INSIDE the
# # impl-start / # impl-end region of the frozen model.py, so same_spec is
# guaranteed (the spec view — axioms/pure/pre/post-conditions + signature — is
# byte-identical to model.py). The @Pure flag_path lives OUTSIDE the impl region
# and is never edited (it IS the spec oracle).
from pathlib import Path

INSTANCE = "django__django-12858"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl body (the decision branch + the per-element framing Assert)
# inside the loop. We swap this single block per variant; everything outside the
# # impl-start/# impl-end region (incl. the @Pure flag_path oracle, the pre/post
# conditions) is untouched, so same_spec holds for every case.
_GOLD_DECISION = (
    "        if reached_field[i] == 0 or (is_value_op[i] == 0 and is_compare_op[i] == 0):\n"
    "            errors.append(1)\n"
    "        else:\n"
    "            errors.append(0)\n"
    "        Assert(errors[i] == flag_path(reached_field[i], is_value_op[i],\n"
    "                                      is_compare_op[i]))\n"
)


# ---------------------------------------------------------------------------
# 1. FRAME-MUTATION (MANDATORY — all three inputs are read-only Acc(...,1/2)).
# A rival that WRITES to a read-only input (reached_field) inside the loop to
# "normalise" it before deciding. It only holds Acc(list_pred(reached_field),
# 1/2) (Requires + Invariant), which does NOT grant write permission, so the
# `reached_field[i] = 1` store must be REJECTED for insufficient permission.
# The gold postcondition + invariant are kept verbatim so the rejection is
# attributable to the write, not to a broken proof obligation.
_FRAME_MUT = _swap(
    _BASE,
    _GOLD_DECISION,
    "        # frame-mutation attack: store into a read-only (Acc 1/2) input.\n"
    "        reached_field[i] = 1\n"
    "        if reached_field[i] == 0 or (is_value_op[i] == 0 and is_compare_op[i] == 0):\n"
    "            errors.append(1)\n"
    "        else:\n"
    "            errors.append(0)\n"
    "        Assert(errors[i] == flag_path(reached_field[i], is_value_op[i],\n"
    "                                      is_compare_op[i]))\n",
)


# ---------------------------------------------------------------------------
# 2. PARTIAL-DOMAIN (the prepatch defect — the discriminating F2P sub-domain).
# Correct on EVERY row except (reached=1, value=0, compare=1): there it reports
# (append 1) instead of accepting (append 0), i.e. it ignores the gold's
# is_compare_op conjunct. Equivalent to the pre-patch predicate
# `fld is None or get_transform(part) is None`. Must be REJECTED by the
# postcondition Forall clause on the F2P row.
_PARTIAL_PREPATCH = _swap(
    _BASE,
    _GOLD_DECISION,
    "        # partial-domain attack: drop the gold is_compare_op conjunct so a\n"
    "        # lookup-but-not-transform segment (the 'isnull' F2P row) is wrongly\n"
    "        # reported. Correct on all other rows.\n"
    "        if reached_field[i] == 0 or is_value_op[i] == 0:\n"
    "            errors.append(1)\n"
    "        else:\n"
    "            errors.append(0)\n"
    "        Assert(errors[i] == flag_path(reached_field[i], is_value_op[i],\n"
    "                                      is_compare_op[i]))\n",
)


# ---------------------------------------------------------------------------
# 2b. PARTIAL-DOMAIN (the mirror defect: drop the reached_field guard).
# Reports iff the segment is neither operator kind, IGNORING whether a field was
# reached. Diverges on (reached=0, value=1, *) and (reached=0, *, compare=1):
# those rows the gold reports (flag 1, no field reached) but this accepts (0).
# A faithful real patch matching this would accept a path whose FIRST segment
# already failed to resolve (fld is None) merely because a later name happens to
# match some operator — wrongly suppressing a legitimate models.E015 — so it
# would NOT preserve the P2P "nonexistent field" reporting tests.
_PARTIAL_NOFIELD = _swap(
    _BASE,
    _GOLD_DECISION,
    "        # partial-domain attack: drop the reached_field==0 disjunct, so a\n"
    "        # path with NO field reached is accepted whenever a segment matches\n"
    "        # an operator. Diverges on the reached_field==0 rows.\n"
    "        if is_value_op[i] == 0 and is_compare_op[i] == 0:\n"
    "            errors.append(1)\n"
    "        else:\n"
    "            errors.append(0)\n"
    "        Assert(errors[i] == flag_path(reached_field[i], is_value_op[i],\n"
    "                                      is_compare_op[i]))\n",
)


# ---------------------------------------------------------------------------
# 2c. PARTIAL-DOMAIN supporting near-miss: off-by-one on the LAST path only.
# Computes the gold decision for every path then, for the final index, appends
# the negation. Verifies only if the spec is too weak about the tail element.
# A faithful real patch that mis-decides exactly its last related-field path
# would mis-report whichever ordering reference is examined last (e.g. the
# 'isnull' tail in a multi-path ordering), so it would not resolve.
_PARTIAL_LAST = _swap(
    _BASE,
    _GOLD_DECISION,
    "        # partial-domain near-miss: correct except the final path, where the\n"
    "        # flag is negated.\n"
    "        if reached_field[i] == 0 or (is_value_op[i] == 0 and is_compare_op[i] == 0):\n"
    "            decided = 1  # type: int\n"
    "        else:\n"
    "            decided = 0\n"
    "        if i == len(reached_field) - 1:\n"
    "            decided = 1 - decided\n"
    "        errors.append(decided)\n",
)


# ---------------------------------------------------------------------------
# 5. POSITIVE CONTROL (soundness): a structurally-DIFFERENT but CORRECT impl.
# Same forward loop / append shape (so the front-recursive framing the verifier
# already discharges is preserved), but the decision is restructured: compute an
# explicit `accept` boolean (a field was reached AND the segment is at least one
# operator kind) and append its negation. Boolean-algebra-equal to flag_path:
#   report = not accept = not(reached!=0 and (value!=0 or compare!=0))
#          = reached==0 or (value==0 and compare==0)  == flag_path.
# The gold per-element framing Assert is KEPT verbatim (directive: do not drop a
# framing assert a positive control still needs). MUST verify (else SPEC-TOO-STRONG).
_POS_CONTROL = _swap(
    _BASE,
    _GOLD_DECISION,
    "        # positive control: restructured but boolean-equal decision.\n"
    "        if reached_field[i] != 0 and (is_value_op[i] != 0 or is_compare_op[i] != 0):\n"
    "            errors.append(0)\n"
    "        else:\n"
    "            errors.append(1)\n"
    "        Assert(errors[i] == flag_path(reached_field[i], is_value_op[i],\n"
    "                                      is_compare_op[i]))\n",
)


# ---------------------------------------------------------------------------
# 6. ADMISSIBILITY: the precondition must admit a normal F2P-shaped input. We
# cannot add a separate top-level caller (it would change the signature region
# and break same_spec), so admissibility is exercised IN-region: an added Assert
# proves the F2P row (field reached, segment is a Lookup but not a Transform —
# reached=1, value=0, compare=1, the exact ordering=('test__isnull',) scenario)
# is in-domain and is ACCEPTED (flag 0). If the precondition over-constrained the
# inputs or the spec rejected this legitimate row, the Assert would not verify.
_ADMISS = _swap(
    _BASE,
    "        Assert(errors[i] == flag_path(reached_field[i], is_value_op[i],\n"
    "                                      is_compare_op[i]))\n",
    "        Assert(errors[i] == flag_path(reached_field[i], is_value_op[i],\n"
    "                                      is_compare_op[i]))\n"
    "        # admissibility: the F2P row (field reached, lookup-not-transform) is\n"
    "        # in-domain and is ACCEPTED (flag 0) by the decision.\n"
    "        Assert(Implies(reached_field[i] == 1 and is_value_op[i] == 0 and\n"
    "                       is_compare_op[i] == 1, errors[i] == 0))\n",
)


SPEC_TESTS = [
    {
        "id": "frame-mutation-reached_field",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_MUT,
        "refinement": (
            "The rival writes reached_field[i]=1 (a read-only Acc(...,1/2) input). "
            "Its faithful real patch would overwrite the per-path 'a field was "
            "reached' observation before deciding, so EVERY path would be treated "
            "as field-reached — a path whose first segment failed (fld is None) "
            "would no longer be reported, dropping legitimate models.E015 errors. "
            "That contradicts the P2P 'nonexistent/related field' reporting tests, "
            "so it would not resolve. It must reject for INSUFFICIENT PERMISSION."
        ),
        "rationale": (
            "Rejection comes from the permission system: only Acc(list_pred("
            "reached_field), 1/2) is held (Requires + Invariant), which does not "
            "grant write access; the store `reached_field[i] = 1` needs full "
            "permission. The gold postcondition/invariant are kept verbatim, so the "
            "failure is attributable to the write, not a broken proof obligation."
        ),
    },
    {
        "id": "partial-domain-drop-compare-op",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_PREPATCH,
        "refinement": (
            "This is the pre-patch predicate (reports iff fld is None OR "
            "get_transform is None) — it omits the gold get_lookup conjunct. Its "
            "faithful real patch reports the F2P path ordering=('test__isnull',) "
            "where isnull is a registered Lookup but not a Transform, so "
            "Model.check() != [] and the F2P test "
            "test_ordering_pointing_to_lookup_not_transform FAILS — it does not "
            "resolve. (This is exactly model_prepatch.py's behaviour.)"
        ),
        "rationale": (
            "Rejection comes from the postcondition Forall clause Result()[k] == "
            "flag_path(...) on the row (reached=1, value=0, compare=1): the rival "
            "appends 1 there but flag_path returns 0, so the per-element Assert and "
            "the postcondition both fail."
        ),
    },
    {
        "id": "partial-domain-drop-reached-field",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_NOFIELD,
        "refinement": (
            "Drops the reached_field==0 disjunct: a path whose trailing segment "
            "could not be resolved to a field (fld is None) is accepted whenever "
            "some name matched an operator. The faithful real patch would suppress "
            "legitimate models.E015 errors for genuinely nonexistent fields, "
            "breaking the P2P 'ordering refers to nonexistent field' reporting "
            "tests, so it would not resolve."
        ),
        "rationale": (
            "Rejection comes from the postcondition Forall clause on any "
            "reached_field==0 row (e.g. reached=0, value=1, compare=0): the rival "
            "appends 0 but flag_path returns 1."
        ),
    },
    {
        "id": "partial-domain-last-path-negated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_LAST,
        "refinement": (
            "Negates the flag for the final examined path only. A faithful real "
            "patch that mis-decides exactly the last related-field path would "
            "mis-report whichever ordering reference is examined last (e.g. the "
            "'isnull' tail), flipping its models.E015 presence, so it would not "
            "resolve. Cheap supporting near-miss; carries a real refinement."
        ),
        "rationale": (
            "Rejection comes from the postcondition Forall clause at k = "
            "len-1: the rival appends 1-flag_path(...) there, contradicting "
            "Result()[len-1] == flag_path(...)."
        ),
    },
    {
        "id": "positive-control-restructured-decision",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CONTROL,
        "rationale": (
            "A structurally-different but boolean-equal CORRECT impl: it computes "
            "the accept condition (field reached AND at least one operator kind) "
            "and appends its negation, which equals flag_path by De Morgan. Same "
            "forward-loop/append shape (front-recursive framing preserved) and the "
            "gold per-element Assert is kept verbatim, so the proof discharges. "
            "Must verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admissibility-f2p-row-accepted",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "The precondition admits the F2P-shaped input (three aligned read-only "
            "lists). An added in-loop Assert confirms the F2P row (reached=1, "
            "value=0, compare=1 — field reached, lookup-not-transform) is in-domain "
            "and ACCEPTED (flag 0). Must verify, else PRECOND-TOO-STRONG."
        ),
    },
]


# No @ContractOnly axioms in this bundle (meta.axioms == []). flag_path is an
# A-reference deep model (the per-path decision is modelled deeply), validated by
# axiom_check.py / G-AX against the real post-patch predicate and the real
# Field.get_transform / Field.get_lookup callees — it is NOT a consumed axiom, so
# there is no axiom-soundness / axiom-containment obligation to probe here.
AXIOM_TESTS = []
