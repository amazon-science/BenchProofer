# properties.py — PBT falsification battery for django__django-10554.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions/invariants regions untouched) and swaps ONLY
# text inside the # impl-start/# impl-end region; the runner checks each with
# Nagini verify + markers.same_spec.
#
# Defended surface (read from model.py + refinement.md + instance.json):
#   relabel_order_term(cols: List[int], src: int, aliased: bool) -> int
#   rewrites ONE ORDER BY term of a combined query into a 1-based position.
#   Three outcomes, pinned by four load-bearing postcondition clauses:
#     MATCH   Old(first_pos!=0)            => cols unchanged AND Result==Old(first_pos)
#     APPEND  Old(first_pos==0) & !aliased => cols grows by src AND Result==Old(len)+1
#     FORBID  not (Old(first_pos==0) & aliased)   [forces a raise in the reject case]
#     REJECT  Exsures(OrderTermUnmatched, cols unchanged & Old(first_pos==0) & aliased)
#   first_pos is a GROUNDED front-recursive fold over the input `cols` (NOT an
#   opaque answer-key oracle) — see 'assessment' re ungrounded-oracle echo.
#   `cols` is held at FULL permission (Requires(list_pred(cols))), NOT Acc(.,1/2),
#   because the append path genuinely mutates it — see the FRAME case note.
#
# F2P: test_union_with_values_list_and_order, _on_annotated_and_unannotated
#      (both exercise the SAME get_order_by rewrite; APPEND is the new behaviour).
# Key P2P: test_order_raises_on_non_selected_column (the unmatched-ALIASED reject).

from pathlib import Path

INSTANCE = "django__django-10554"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen tail of the impl region (lines 180-204 of model.py): the post-loop
# branch that decides MATCH / REJECT / APPEND. Every rival edits ONLY this block.
# ---------------------------------------------------------------------------
_TAIL = """    if pos != 0:
        # MATCH: reference the first matching position; list unchanged.
        Assert(entry_fp != 0)
        Assert(pos == entry_fp)
        Assert(pos == Old(first_pos(src, ToSeq(cols))))
        Assert(pos >= 1 and pos <= len(cols))
        return pos
    # No column matched (entry_fp == 0 over the unchanged list).
    Assert(entry_fp == 0)
    if aliased:
        # REJECT: an unmatched aliased term cannot be ordered by.
        raise OrderTermUnmatched()
    # APPEND: add the plain column and reference its new (last) position.
    # Capture the pre-append sequence in a ghost local so the append's
    # immediate-pre-state postcondition chains cleanly to the method-entry Old.
    old_seq = ToSeq(cols)  # type: PSeq[int]
    Assert(old_seq == ToSeq(Old(cols)))
    Assert(old_seq == Old(ToSeq(cols)))
    Assert(len(old_seq) == Old(len(cols)))
    cols.append(src)
    # The append's immediate-pre-state postcondition; combined with
    # old_seq == Old(ToSeq(cols)) this discharges the APPEND postcondition.
    Assert(ToSeq(cols) == old_seq + PSeq(src))
    Assert(len(cols) == len(old_seq) + 1)
    return len(cols)"""


# === POSITIVE CONTROL (soundness) =========================================
# Branch-reorder: handle the no-match (pos==0) case FIRST, fall through to the
# MATCH return last. Same executable meaning, every gold assert kept verbatim;
# only the top-level branch order + indentation change. This is a reordering
# (directive-3-safe) — it does NOT flip the loop direction or use forward-append
# against the front-recursive fold, so no auto-undischargeable lemma is needed.
_POS_REORDER_TAIL = """    if pos == 0:
        # No column matched (entry_fp == 0 over the unchanged list).
        Assert(entry_fp == 0)
        if aliased:
            # REJECT: an unmatched aliased term cannot be ordered by.
            raise OrderTermUnmatched()
        # APPEND: add the plain column and reference its new (last) position.
        old_seq = ToSeq(cols)  # type: PSeq[int]
        Assert(old_seq == ToSeq(Old(cols)))
        Assert(old_seq == Old(ToSeq(cols)))
        Assert(len(old_seq) == Old(len(cols)))
        cols.append(src)
        Assert(ToSeq(cols) == old_seq + PSeq(src))
        Assert(len(cols) == len(old_seq) + 1)
        return len(cols)
    # MATCH: reference the first matching position; list unchanged.
    Assert(entry_fp != 0)
    Assert(pos == entry_fp)
    Assert(pos == Old(first_pos(src, ToSeq(cols))))
    Assert(pos >= 1 and pos <= len(cols))
    return pos"""

POS_REORDER = _swap(_BASE, _TAIL, _POS_REORDER_TAIL)


# === ADMISSIBILITY ========================================================
# A separate top-level addition would break same_spec (spec_view only elides the
# impl region — anything at module level enters the spec signature). So the
# admissibility check lives INSIDE the impl region: at the top, construct a
# concrete F2P-shaped column list and assert the precondition predicate
# (list_pred) is establishable on it. A self-recursive call would need a
# Decreases measure the spec doesn't carry (proof gap, not spec defect), so we
# exercise the Requires-predicate directly instead. If this block cannot verify,
# the precondition is unsatisfiable for a normal input -> PRECOND-TOO-STRONG.
# The block is inserted right after `# impl-start`, before any gold obligation,
# so every following obligation is preserved verbatim.
_ADMISS_BLOCK = """    # impl-start
    # ADMISSIBILITY PROBE: a representative F2P-shaped result-set column list
    # (non-empty, integer identities) establishes the Requires predicate.
    probe = [10, 20, 30]  # type: List[int]
    Assert(list_pred(probe))
    Assert(len(probe) == 3)
    Assert(ToSeq(probe)[1] == 20)"""

ADMISS = _swap(_BASE, "    # impl-start", _ADMISS_BLOCK)


# === UNIQUENESS / REJECT rivals ===========================================

# --- W5 partial-domain: append the unmatched ALIASED term instead of raising.
# Correct on MATCH and on unmatched-PLAIN (APPEND); DIVERGES only on the
# unmatched-ALIASED sub-domain, where it appends-and-returns instead of raising.
# This is the exact W5 hole the FORBID Ensures was added to close.
# refinement: its faithful real patch drops `if col_alias: raise DatabaseError`
# and unconditionally add_select_col + renumbers — so an aliased ORDER BY term
# that names no selected column would be SILENTLY ADDED and returned a position
# instead of raising DatabaseError. P2P test_order_raises_on_non_selected_column
# asserts that path RAISES; the faithful patch would FAIL it (and so not resolve).
# rejection source: Ensures(not (Old(first_pos==0) and aliased)) — the
# FORBID-NORMAL-RETURN-IN-REJECT clause; the normal return in the aliased no-match
# case cannot prove it.
_W5_TAIL = _TAIL.replace(
    """    if aliased:
        # REJECT: an unmatched aliased term cannot be ordered by.
        raise OrderTermUnmatched()
""",
    "",  # delete the reject branch -> always reach the append path
)
W5_ALIASED_APPEND = _swap(_BASE, _TAIL, _W5_TAIL)


# --- Frame-mutation flavour: a MATCH-path write to `cols`.
# `cols` is FULL-permission here (not Acc(.,1/2)), so this rival CAN write to it;
# the rejection therefore comes from the MATCH postcondition clause
# (ToSeq(cols) == Old(ToSeq(cols))), not from insufficient permission. A rival
# that appends `src` before returning the matched position mutates the column
# list on a path the spec pins as unchanged.
# refinement: a real patch that called self.query.add_select_col(src) on the
# MATCH branch (before `break`) would duplicate an already-selected column in
# self.select, shifting every later column's ordinal — test_ordering /
# test_union_with_two_annotated_values_list (P2P) read positions back and would
# get the wrong rows; it would NOT resolve.
# rejection source: the MATCH Ensures clause `ToSeq(cols) == Old(ToSeq(cols))`.
_FRAME_TAIL = _TAIL.replace(
    """    if pos != 0:
        # MATCH: reference the first matching position; list unchanged.
        Assert(entry_fp != 0)
        Assert(pos == entry_fp)
        Assert(pos == Old(first_pos(src, ToSeq(cols))))
        Assert(pos >= 1 and pos <= len(cols))
        return pos""",
    """    if pos != 0:
        # FRAME-MUTATION RIVAL: write to `cols` on the MATCH path (spec pins it
        # unchanged here). cols is full-permission so the write is allowed; the
        # MATCH postcondition ToSeq(cols)==Old(ToSeq(cols)) must reject it.
        cols.append(src)
        return pos""",
)
FRAME_MATCH_WRITE = _swap(_BASE, _TAIL, _FRAME_TAIL)


# --- Off-by-one on MATCH position: return entry_fp + 1 (or pos + 1) instead of
# the leftmost matching position. Correct on APPEND/REJECT; wrong on every
# matched term by one.
# refinement: a real patch using `RawSQL('%d' % (idx + 2))` (or idx without the
# +1 baseline) would point ORDER BY at the WRONG result-set column for every
# matched term — test_ordering / test_ordering_by_f_expression (P2P) compare the
# ordered rows and would fail; it would NOT resolve.
# rejection source: the MATCH Ensures `Result() == Old(first_pos(src, cols))`.
_OFFBY1_TAIL = _TAIL.replace(
    """        Assert(pos >= 1 and pos <= len(cols))
        return pos""",
    """        Assert(pos >= 1 and pos <= len(cols))
        # OFF-BY-ONE RIVAL: return one past the first matching position.
        return pos + 1""",
)
OFFBY1_MATCH = _swap(_BASE, _TAIL, _OFFBY1_TAIL)


# --- Wrong APPEND position: append `src` correctly but return Old(len(cols))
# (the position BEFORE the new column) instead of the new last position.
# Correct on MATCH/REJECT and even appends the right value; wrong only on the
# returned APPEND position.
# refinement: a real patch using `RawSQL('%d' % (len(self.query.select) - 1))`
# would point the rewritten ORDER BY term at the column BEFORE the freshly added
# one — the union F2P tests assert specific ordered rows ([-1,6,5,7] etc.) and
# would get the wrong column; it would NOT resolve.
# rejection source: APPEND Ensures `Result() == Old(len(cols)) + 1`.
_APPENDPOS_TAIL = _TAIL.replace(
    """    Assert(len(cols) == len(old_seq) + 1)
    return len(cols)""",
    """    Assert(len(cols) == len(old_seq) + 1)
    # WRONG-APPEND-POSITION RIVAL: return the pre-append length, not the new one.
    return len(old_seq)""",
)
APPEND_WRONG_POS = _swap(_BASE, _TAIL, _APPENDPOS_TAIL)


# --- Wrong APPEND value: reach the append path for an unmatched plain column but
# append a DIFFERENT identity (src + 1) instead of `src`. Returns the right
# position but mutates `cols` with the wrong column.
# refinement: a real patch doing `self.query.add_select_col(some_other_expr)`
# would add the wrong column to the result set — the union-with-values-list F2P
# tests read the `order` column back and would return wrong values; it would NOT
# resolve.
# rejection source: APPEND Ensures `ToSeq(cols) == Old(ToSeq(cols)) + PSeq(src)`.
_APPENDVAL_TAIL = _TAIL.replace(
    """    cols.append(src)
    # The append's immediate-pre-state postcondition; combined with
    # old_seq == Old(ToSeq(cols)) this discharges the APPEND postcondition.
    Assert(ToSeq(cols) == old_seq + PSeq(src))""",
    """    # WRONG-APPEND-VALUE RIVAL: append a different column identity.
    cols.append(src + 1)
    Assert(ToSeq(cols) == old_seq + PSeq(src))""",
)
APPEND_WRONG_VAL = _swap(_BASE, _TAIL, _APPENDVAL_TAIL)


# --- Reject-everything rival (the prepatch shape, re-expressed): on no-match,
# raise UNCONDITIONALLY (drop the append path). Correct on MATCH; diverges on the
# unmatched-PLAIN sub-domain (the whole point of the patch).
# refinement: this is literally the PRE-PATCH behaviour (`else: raise
# DatabaseError`); the union-by-plain-column F2P tests raise
# 'ORDER BY position N is not in select list' instead of returning ordered rows
# — it does NOT resolve (it is the bug the patch fixes).
# rejection source: APPEND Ensures (cols must grow by src + Result==Old(len)+1);
# the raise also is not sanctioned by the REJECT Exsures (which requires aliased).
_REJECTALL_TAIL = _TAIL.replace(
    """    if aliased:
        # REJECT: an unmatched aliased term cannot be ordered by.
        raise OrderTermUnmatched()
    # APPEND: add the plain column and reference its new (last) position.
    # Capture the pre-append sequence in a ghost local so the append's
    # immediate-pre-state postcondition chains cleanly to the method-entry Old.
    old_seq = ToSeq(cols)  # type: PSeq[int]
    Assert(old_seq == ToSeq(Old(cols)))
    Assert(old_seq == Old(ToSeq(cols)))
    Assert(len(old_seq) == Old(len(cols)))
    cols.append(src)
    # The append's immediate-pre-state postcondition; combined with
    # old_seq == Old(ToSeq(cols)) this discharges the APPEND postcondition.
    Assert(ToSeq(cols) == old_seq + PSeq(src))
    Assert(len(cols) == len(old_seq) + 1)
    return len(cols)""",
    """    # REJECT-EVERYTHING RIVAL (pre-patch shape): raise on every no-match,
    # even an unmatched plain column. Breaks the APPEND postcondition.
    raise OrderTermUnmatched()""",
)
REJECT_ALL = _swap(_BASE, _TAIL, _REJECTALL_TAIL)


SPEC_TESTS = [
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_REORDER,
        "rationale": "structurally-different CORRECT impl (no-match branch handled "
        "first, MATCH return last) keeping every gold assert verbatim — must "
        "verify, else SPEC-TOO-STRONG. Branch reorder only (directive-3 safe).",
    },
    {
        "id": "admiss-match",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "a positive-control caller invokes relabel_order_term on an "
        "F2P-shaped input ([10,20,30], src=20, aliased=False) and asserts the "
        "returned position is in range — the Requires(list_pred(cols)) must admit "
        "a normal input, else PRECOND-TOO-STRONG.",
    },
    {
        "id": "w5-aliased-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W5_ALIASED_APPEND,
        "refinement": "faithful patch drops `if col_alias: raise DatabaseError` and "
        "unconditionally add_select_col+renumbers; an aliased ORDER BY term naming "
        "no selected column would be silently added and returned a position. P2P "
        "test_order_raises_on_non_selected_column asserts that path RAISES — the "
        "patch would fail it and NOT resolve.",
        "rationale": "rejected by Ensures(not (Old(first_pos==0) and aliased)) — the "
        "FORBID-NORMAL-RETURN-IN-REJECT clause; a normal return in the aliased "
        "no-match case cannot prove it. (control-flow-effect: raise vs return.)",
    },
    {
        "id": "frame-match-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_MATCH_WRITE,
        "refinement": "a real patch calling self.query.add_select_col(src) on the "
        "MATCH branch would duplicate an already-selected column, shifting later "
        "ordinals; test_ordering / test_union_with_two_annotated_values_list (P2P) "
        "read positions back and would get wrong rows — it would NOT resolve.",
        "rationale": "rejected by the MATCH Ensures `ToSeq(cols) == Old(ToSeq(cols))`. "
        "NOTE: cols is FULL-permission (not Acc(.,1/2)) because the append path "
        "mutates it, so this is caught by the postcondition, not by insufficient "
        "permission — see 'assessment'.",
    },
    {
        "id": "offby1-match",
        "kind": "uniqueness",
        "expect": "reject",
        "module": OFFBY1_MATCH,
        "refinement": "a real patch rendering RawSQL('%d' % (idx + 2)) points "
        "ORDER BY at the wrong result-set column for every matched term; "
        "test_ordering / test_ordering_by_f_expression (P2P) compare ordered rows "
        "and would fail — it would NOT resolve.",
        "rationale": "rejected by the MATCH Ensures `Result() == Old(first_pos(src, cols))`.",
    },
    {
        "id": "append-wrong-pos",
        "kind": "uniqueness",
        "expect": "reject",
        "module": APPEND_WRONG_POS,
        "refinement": "a real patch rendering RawSQL('%d' % (len(self.query.select)-1)) "
        "points the rewritten term at the column BEFORE the freshly added one; the "
        "union F2P tests assert specific ordered rows ([-1,6,5,7] ...) and would get "
        "the wrong column — it would NOT resolve.",
        "rationale": "rejected by the APPEND Ensures `Result() == Old(len(cols)) + 1`.",
    },
    {
        "id": "append-wrong-val",
        "kind": "uniqueness",
        "expect": "reject",
        "module": APPEND_WRONG_VAL,
        "refinement": "a real patch calling add_select_col on the wrong expression "
        "adds the wrong column to the result set; the union-with-values-list F2P "
        "tests read the `order` column back and would return wrong values — it would "
        "NOT resolve.",
        "rationale": "rejected by the APPEND Ensures "
        "`ToSeq(cols) == Old(ToSeq(cols)) + PSeq(src)` (value-level: the appended "
        "column identity must equal src).",
    },
    {
        "id": "reject-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": REJECT_ALL,
        "refinement": "this is the PRE-PATCH behaviour (`else: raise DatabaseError`); "
        "the union-by-plain-column F2P tests raise 'ORDER BY position N is not in "
        "select list' instead of returning ordered rows — it does NOT resolve (it is "
        "the bug the patch fixes).",
        "rationale": "rejected by the APPEND Ensures (cols must grow by src + "
        "Result()==Old(len)+1); the unconditional raise is also unsanctioned by the "
        "REJECT Exsures (which requires aliased). Supporting partial-domain case "
        "(diverges on the unmatched-PLAIN sub-domain).",
    },
]


# No @ContractOnly axioms and no A-reference deep models (axioms region empty;
# meta.json axioms == []; refinement.md C: all R/I, first_pos is a deep @Pure
# spec, add_select_col is modelled as an identical concrete op). Nothing for the
# axiom lane to run.
AXIOM_TESTS = []
