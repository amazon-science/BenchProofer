# properties.py — PBT falsification battery for django__django-14122.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that share the FROZEN spec byte-for-byte (only the impl
# region between `# impl-start` / `# impl-end` is edited — guaranteed by
# region-surgery, so same_spec holds) and are checked by Nagini verify; axiom
# cases are real-callee probes run in Docker.
#
# DEFENDED SURFACE (read model.py):
#   assemble_grouping_key(select_cols, order_cols, order_is_backref,
#                         trailing_cols, ordering_was_requested) -> List[int]
#   * ALL FOUR list inputs are READ-ONLY: held at Acc(list_pred(.), 1/2),
#     Required AND Ensured. => frame-mutation is MANDATORY.
#   * Load-bearing postcondition has TWO clauses:
#       (P1) Implies(ordering_was_requested,
#               Result == select + order_contrib(order_cols, refs) + trailing)
#       (P2) Implies(not ordering_was_requested,           <-- DISCRIMINATING
#               Result == select + trailing)               (no ordering tokens)
#     The whole bug fix lives in P2: a DEFAULT ordering must NOT add its columns
#     to the grouping key (else the aggregation splits into spurious groups —
#     the F2P test `test_default_ordering_does_not_affect_group_by`).
#   * The oracle `order_contrib` is @Pure but GROUNDED: it is the spelled-out
#     non-back-reference fold over the actual `cols`/`refs` args, fully
#     unfolded, NOT an opaque answer-key. There is no wrong value to echo, so
#     there is no ungrounded-oracle-echo attack (see 'assessment'); instead we
#     supply honest positive controls + the partial-domain rivals below.
#
# AXIOM LANE: empty. meta.json `axioms: []`; the only kind-A obligation is the
# A-reference deep model (order_contrib + the guard == patched get_group_by),
# already validated out-of-band by axiom_check.py (G-AX, 14 boundary + 50000
# fuzz). There is no @ContractOnly axiom whose real-callee soundness a probe
# could attack, so AXIOM_TESTS = [].

from pathlib import Path

INSTANCE = "django__django-14122"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Region-surgery: replace the unique `old` with `new`. Raises if `old`
    is absent or not unique, so a silent spec drift can never slip through."""
    if old not in src:
        raise AssertionError(f"drift: anchor not found: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


def _replace_impl(src: str, new_impl_body: str) -> str:
    """Replace everything between `# impl-start` and `# impl-end` (exclusive of
    the markers) with `new_impl_body`. Edits ONLY inside the impl region, so the
    frozen spec_view (and hence same_spec) is untouched."""
    start = "    # impl-start\n"
    end = "    # impl-end"
    i = src.index(start) + len(start)
    j = src.index(end)
    return src[:i] + new_impl_body + src[j:]


# ---------------------------------------------------------------------------
# Anchors inside the frozen impl region (each unique in _BASE).
# ---------------------------------------------------------------------------

# The single changed control-flow node: the guard around the ordering loop.
_GUARD = "    if ordering_was_requested:\n"

# The per-entry back-reference skip (keep entry k iff its ref-flag is 0).
_SKIP = "            if is_ref == 0:\n                result.append(col)\n"

# The two reads at the top of the ordering-loop body.
_READS = "            is_ref = order_is_backref[k]\n            col = order_cols[k]\n"

# The first executable statement of the impl.
_RESULT_INIT = "    result = []  # type: List[int]\n"

# The trailing-source append.
_TRAIL_APPEND = "        result.append(trailing_cols[t])\n"


# ===========================================================================
# (1) POSITIVE CONTROL — branch reshape (verify).  SOUNDNESS.
# Negate-and-swap the per-entry skip: `if is_ref != 0: pass; else: append`.
# Semantically identical to `if is_ref == 0: append`. ALL gold framing asserts
# (the per-step order_contrib unfold, the take(k+1) decompositions) are KEPT
# verbatim, so the loop invariant still discharges. A faithful CORRECT impl
# with a different branch shape MUST verify (else SPEC-TOO-STRONG).
# ===========================================================================
_POS_BRANCH = _swap(
    _BASE, _SKIP,
    "            if is_ref != 0:\n"
    "                pass\n"
    "            else:\n"
    "                result.append(col)\n",
)

# ===========================================================================
# (2) POSITIVE CONTROL — local-variable reshape (verify).  SOUNDNESS.
# Reorder the two reads (col first, then is_ref) and route the appended token
# through a fresh local. Pure structural reshape; both names are still bound
# before every assert that uses them, so the unfold asserts and invariant are
# unchanged. MUST verify.
# ===========================================================================
_POS_RESHAPE = _swap(
    _BASE, _SKIP + "            k = k + 1\n",
    "            if is_ref == 0:\n"
    "                tok = col\n"
    "                result.append(tok)\n"
    "            k = k + 1\n",
)
_POS_RESHAPE = _swap(
    _POS_RESHAPE, _READS,
    "            col = order_cols[k]\n            is_ref = order_is_backref[k]\n",
)

# ===========================================================================
# (3) ADMISSIBILITY — the precondition admits a normal F2P-shaped input (verify).
# Keep the gold impl verbatim and prepend read-asserts on all four
# half-permission inputs (each readable at 1/2) proving the Requires is
# non-vacuous and a normal (non-raising) return is reachable for an F2P-shaped
# call. If this fails, the precondition is unsatisfiable for a legitimate input
# => PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS = _swap(
    _BASE, _RESULT_INIT,
    "    # admissibility: every read-only input is usable at 1/2 permission and\n"
    "    # the precondition is satisfiable for a normal F2P-shaped call.\n"
    "    Assert(len(select_cols) >= 0)\n"
    "    Assert(len(order_cols) >= 0)\n"
    "    Assert(len(order_is_backref) >= 0)\n"
    "    Assert(len(trailing_cols) >= 0)\n"
    "    Assert(len(order_cols) == len(order_is_backref))\n"
    "    Assert(ToSeq(order_cols).take(0) == empty_seq())\n"
    + _RESULT_INIT,
)

# ===========================================================================
# (4) FRAME-MUTATION — write to a read-only input (reject).  MANDATORY.
# All four inputs are held at Acc(list_pred(.), 1/2). Inside the trailing loop
# `trailing_cols[t]` is known in-bounds, so the VALUE-NEUTRAL self-write
# `trailing_cols[t] = trailing_cols[t]` leaves every value (and hence every
# gold invariant/assert) unchanged — yet a list index-store needs FULL
# permission. With only the half-permission the Requires grants, Nagini rejects
# for INSUFFICIENT PERMISSION. The gold proof is kept verbatim so the rejection
# is attributable solely to the write. A byte-fuzzer never thinks to mutate the
# input; this is the project's #1 weakness class.
# refinement: the real get_group_by NEVER mutates `having_group_by`/the SELECT
# or order_by carriers — it only reads them to build a fresh `expressions`
# list. A faithful patch that wrote back into the input list would corrupt the
# shared query carrier and break P2P (the ordering/extra tests reuse it), so it
# would NOT resolve.
# ===========================================================================
_FRAME_MUT = _swap(
    _BASE, _TRAIL_APPEND,
    "        trailing_cols[t] = trailing_cols[t]  # WRITE: needs FULL perm; only 1/2 held\n"
    + _TRAIL_APPEND,
)

# ===========================================================================
# (5) PARTIAL-DOMAIN — drop the guard / fold ordering UNCONDITIONALLY (reject).
# THE canonical discriminator: this is the verbatim PRE-PATCH impl region
# (ordering loop run with NO `if ordering_was_requested:` guard). It satisfies
# clause P1 (requested) but VIOLATES the discriminating clause P2: when
# `not ordering_was_requested` and the ordering contributes a non-back-ref
# token, Result = select + order_contrib + trailing != select + trailing.
# correct on the requested sub-domain, wrong on the default sub-domain.
# refinement: this IS the pre-patch code at base_commit; it fails the F2P test
# `test_default_ordering_does_not_affect_group_by` exactly (a default
# Meta.ordering column leaks into GROUP BY, splitting the aggregation) — the bug
# the gold patch fixes. It does NOT resolve. (= G-DIFF / model_prepatch.py.)
# ===========================================================================
_PREPATCH_IMPL = (Path(__file__).parent / "model_prepatch.py").read_text()
_PREPATCH_BODY = _PREPATCH_IMPL[
    _PREPATCH_IMPL.index("    # impl-start\n") + len("    # impl-start\n"):
    _PREPATCH_IMPL.index("    # impl-end")
]
_UNCOND_FOLD = _replace_impl(_BASE, _PREPATCH_BODY)

# ===========================================================================
# (6) PARTIAL-DOMAIN — inverted guard: fold ordering ONLY on default (reject).
# `if ordering_was_requested:` -> `if not ordering_was_requested:`. Folds the
# ordering source into the key exactly when it must NOT (default ordering) and
# drops it exactly when it must be kept (explicit request). Violates BOTH P1
# (requested but order tokens dropped) and P2 (default but order tokens added),
# whenever the ordering contributes a non-back-ref token.
# refinement: this inverts the patched guard `if not self._meta_ordering:` to
# `if self._meta_ordering:`. It fails the F2P (default still leaks) AND breaks
# the explicit-ordering P2P cases (e.g. order_by aggregation), so it resolves
# nothing.
# ===========================================================================
_GUARD_INVERTED = _swap(_BASE, _GUARD, "    if not ordering_was_requested:\n")

# ===========================================================================
# (7) PARTIAL-DOMAIN — drop the per-entry back-reference skip (reject).
# Append EVERY ordering entry's token regardless of its ref flag. Correct only
# on the sub-domain with no back-references; wrong as soon as one entry is a
# back-reference (order_is_backref[k] != 0): the per-step unfold assert pins the
# contribution to (empty if is_ref!=0 else PSeq(col)), so appending a back-ref
# token breaks the loop invariant `result == select + order_contrib(.take(k))`.
# refinement: drops the `if not is_ref:` skip at compiler.py:131. A back-ref
# ordering entry refers to a column ALREADY in the SELECT/GROUP BY; re-adding it
# yields a wrong (duplicated/extra) GROUP BY column, so the SQL is wrong and the
# ordering P2P (`test_order_by_*`) and the F2P do not resolve.
# ===========================================================================
_DROP_SKIP = _swap(
    _BASE, _SKIP,
    "            if is_ref == 0 or is_ref != 0:\n                result.append(col)\n",
)

# ===========================================================================
# (8) PARTIAL-DOMAIN — invert the back-reference skip: keep ONLY back-refs
# (reject). `if is_ref == 0:` -> `if is_ref != 0:`. Appends exactly the entries
# the spec says to drop and drops exactly the ones to keep. Wrong whenever the
# two classes differ.
# refinement: keeps back-reference ordering columns (already grouped) and drops
# the genuine ones, the exact opposite of compiler.py:131 — wrong GROUP BY for
# every ordering case, resolves nothing.
# ===========================================================================
_INVERT_SKIP = _swap(
    _BASE, "            if is_ref == 0:\n",
    "            if is_ref != 0:\n",
)


SPEC_TESTS = [
    {
        "id": "pos-branch-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_BRANCH,
        "rationale": "structurally-different but CORRECT impl (negate-and-swap "
                     "the per-entry skip) keeping every gold framing assert; "
                     "must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-localvar-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_RESHAPE,
        "rationale": "reorder the two ordering-entry reads and route the token "
                     "through a fresh local; pure structural reshape, gold "
                     "asserts/invariant intact; must verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "all four half-permission inputs are read and a normal "
                     "return is reachable for an F2P-shaped call; the "
                     "precondition is non-vacuous, else PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mutation-trailing-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_MUT,
        "refinement": "the real get_group_by never writes back into its input "
                      "lists (select/order_by/having_group_by); it only reads "
                      "them to build a fresh expressions list. A patch that "
                      "mutated the shared carrier would corrupt later query "
                      "construction and break P2P, so it would not resolve.",
        "rationale": "value-neutral list index-store on a 1/2-permission "
                     "read-only input; rejected for INSUFFICIENT PERMISSION "
                     "(permission system), gold proof kept verbatim so the "
                     "rejection is attributable to the write.",
    },
    {
        "id": "uncond-fold-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNCOND_FOLD,
        "refinement": "this is the verbatim PRE-PATCH impl (ordering loop with "
                      "no guard); it fails the F2P "
                      "test_default_ordering_does_not_affect_group_by exactly — "
                      "a default Meta.ordering column leaks into GROUP BY and "
                      "splits the aggregation. It does not resolve (= G-DIFF).",
        "rationale": "violates the discriminating postcondition clause "
                     "Implies(not ordering_was_requested, Result == select + "
                     "trailing): the ordering tokens are folded in for a "
                     "default ordering.",
    },
    {
        "id": "guard-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _GUARD_INVERTED,
        "refinement": "inverts the patched guard to `if self._meta_ordering:`; "
                      "the default ordering still leaks (fails F2P) and the "
                      "explicit-ordering aggregation P2P breaks (order tokens "
                      "dropped). Resolves nothing.",
        "rationale": "folds the ordering source on exactly the wrong branch; "
                     "violates P1 (requested -> order tokens missing) and P2 "
                     "(default -> order tokens present) whenever the ordering "
                     "contributes a non-back-ref token.",
    },
    {
        "id": "drop-backref-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DROP_SKIP,
        "refinement": "drops the `if not is_ref:` skip (compiler.py:131); a "
                      "back-reference ordering entry points at a column already "
                      "in the SELECT/GROUP BY, so re-adding it yields a wrong "
                      "duplicated GROUP BY column. The ordering P2P and the F2P "
                      "do not resolve.",
        "rationale": "violates the loop invariant result == select + "
                     "order_contrib(.take(k)): the per-step unfold pins entry "
                     "k's contribution to (empty if back-ref else its token), "
                     "but the impl appends every entry's token.",
    },
    {
        "id": "invert-backref-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _INVERT_SKIP,
        "refinement": "keeps exactly the back-reference ordering columns and "
                      "drops the genuine ones — the opposite of compiler.py:131. "
                      "Wrong GROUP BY for every ordering case; resolves nothing.",
        "rationale": "violates the loop invariant: appends the entries the fold "
                     "order_contrib drops and drops the ones it keeps.",
    },
]

# No @ContractOnly axioms and no consumed-axiom soundness obligation: the only
# kind-A item is the A-reference deep model, validated == the patched callee
# out-of-band by axiom_check.py (G-AX). Nothing for a real-callee probe to
# attack here, so the axiom lane is empty.
AXIOM_TESTS = []
