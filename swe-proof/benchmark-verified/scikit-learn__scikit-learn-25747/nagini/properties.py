"""properties.py — PBT falsification manifest for scikit-learn__scikit-learn-25747.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical"). This battery is
reasoned from THIS spec's defended surface, not stamped out by a corruption
template.

ONE function is under spec:

    wrap_in_container(data_is_frame: bool, df: Frame,
                      columns: Optional[List[int]], index: Optional[List[int]],
                      nrows: int, ncols: int) -> Frame

modeling the gold patch to `sklearn.utils._set_output._wrap_in_pandas_container`
(it places transformed data into a labelled tabular container so the configured
output format is honoured). The carrier: `pandas.DataFrame` -> `Frame(index,
columns)`; each label axis -> `List[int]` of label codes; values via `PSeq[int]`
through `ToSeq`; `isinstance(...,pd.DataFrame)` -> the bool `data_is_frame`; the
keyword args `columns`/`index` -> `Optional[List[int]]`; the payload shape
(`shape[0]`/`shape[1]`) -> `nrows`/`ncols`.

PERMISSIONS (the defended surface):

  * `df` is FULL permission (`Acc(df.index)`, `Acc(list_pred(df.index))`, …) —
    it is the mutable container being relabelled (the gold patch writes
    `data_to_wrap.columns = columns`).
  * `columns` and `index` are READ-ONLY supplied label sets, each lent at HALF
    permission `Acc(list_pred(columns), 1/2)` / `Acc(list_pred(index), 1/2)`
    (conditionally, when not None) and returned at the SAME fraction (never
    mutated). So the FRAME-MUTATION / insufficient-permission attack DOES apply
    and is MANDATORY: a rival that WRITES to a supplied label set to satisfy a
    postcondition vacuously must be rejected for INSUFFICIENT PERMISSION (you
    need full perm to write through a `1/2` list predicate). This is the
    project's #1 weakness class and a byte-fuzzer never finds it.

LOAD-BEARING postcondition (wrap_in_container):

    # frame branch (already-a-container input):
    Implies(data_is_frame, Result() is df)                                 # same object
    Implies(data_is_frame, ToSeq(Result().index) == Old(ToSeq(df.index)))  # INDEX KEPT
    Implies(data_is_frame and columns is not None,
            ToSeq(Result().columns) == opt_seq(columns))                   # columns refreshed
    Implies(data_is_frame and columns is None,
            ToSeq(Result().columns) == Old(ToSeq(df.columns)))             # columns kept
    # array branch (not-a-container input):
    Implies(not data_is_frame and index is not None,
            ToSeq(Result().index) == opt_seq(index))                       # supplied rows
    Implies(not data_is_frame and index is None,
            is_range(ToSeq(Result().index), nrows))                        # default RangeIndex(nrows)
    Implies(not data_is_frame and columns is not None,
            ToSeq(Result().columns) == opt_seq(columns))                   # supplied cols
    Implies(not data_is_frame and columns is None,
            is_range(ToSeq(Result().columns), ncols))                      # default RangeIndex(ncols)

What this spec defends, and the attacks it must survive:

  * The DISCRIMINATING clause is the frame-branch
    `ToSeq(Result().index) == Old(ToSeq(df.index))`: an already-a-container input
    keeps its OWN row labels, regardless of any supplied `index`. The whole
    content of the gold patch is the DELETION of `data_to_wrap.index = index`.
    `model_prepatch.py` re-introduces that write and FAILS exactly this clause
    (G-DIFF). The F2P test `test_set_output_pandas_keep_index` fits a transformer
    that re-indexes its DataFrame output to `["s0","s1"]`, passes the original
    `index=[0,1]` to the wrapper, and asserts `X_trans.index == ["s0","s1"]` (the
    container's OWN re-index is kept, NOT overwritten with the original).

  * The oracle is GROUNDED in the inputs. `opt_seq(x)` unfolds to `ToSeq(x)` (the
    supplied set's own values) and `is_range(s,n)` is a fully-unfolded predicate
    (`len(s)==n` and `s[k]==k`); both `Old(ToSeq(df.index))` and
    `Old(ToSeq(df.columns))` are the container's own entry values. There is NO
    opaque `@Pure` answer-key a wrong impl could ECHO without doing the work: to
    satisfy the array branch you must actually copy the supplied set or fill the
    real default positional range. So there is no ungrounded-echo rival; the
    cheapest honest impl (the positive controls) still has to build the right
    labels per axis/branch. (See `assessment`.)

  * There is no raise / return / side-effect difference invisible to the value
    abstraction: the entire observable behaviour is the returned `Frame`'s two
    label axes (`Result().index`, `Result().columns`) plus the same-object
    identity `Result() is df` on the frame branch — all pinned by the
    postcondition. The control-flow-effect class is N/A here (no capability-token
    rival needed). (See `assessment`.)

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
editing ONLY text strictly inside the SINGLE `# impl-start`/`# impl-end` region
of `wrap_in_container` (lines 132-170 of model.py). The frozen spec
(axioms/pure/pre/post-conditions) AND the proof-scaffold helpers `_copy_labels`
/ `_range_labels` (which live OUTSIDE the impl region and are therefore part of
the spec view) are NEVER touched, so `markers.same_spec` is guaranteed and a
rejection comes from the POSTCONDITION / the permission system, never from a
tampered spec. Each `expect:"reject"` rival carries the refinement argument that
its faithful real patch would NOT resolve the F2P. This bundle has NO
@ContractOnly axiom (the label-routing rule is modeled DEEPLY); the deep model
is validated == the real post-patch `_wrap_in_pandas_container` by axiom_check.py
(G-AX, A-reference), out of the PBT lane's scope — so AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-25747"
FLOAT_ENCODING = None  # meta.json float_encoding is null (no floats; List[int])

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace the UNIQUE occurrence of an impl-region substring. Assert it is
    found and unique so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(
            f"properties.py: substring not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks — the WHOLE impl body of wrap_in_container, strictly between
# its # impl-start and # impl-end. Occurs exactly once. The helpers
# _copy_labels / _range_labels are NOT touched (they are outside the impl
# region and so part of the spec view).
# ---------------------------------------------------------------------------

_IMPL = """    if data_is_frame:
        if columns is not None:
            refreshed = _copy_labels(columns)  # type: List[int]
            df.columns = refreshed
        # The supplied row labels are intentionally NOT applied here: the
        # container keeps its own row labels.
        return df
    new_index = []  # type: List[int]
    if index is not None:
        new_index = _copy_labels(index)
    else:
        new_index = _range_labels(nrows)
    new_columns = []  # type: List[int]
    if columns is not None:
        new_columns = _copy_labels(columns)
    else:
        new_columns = _range_labels(ncols)
    gi = ToSeq(new_index)    # type: PSeq[int]
    gc = ToSeq(new_columns)  # type: PSeq[int]
    result = Frame(new_index, new_columns, gi, gc)  # type: Frame
    # Tie the constructed label values to the supplied label values (or the
    # default positional labelling when none is supplied): the copy / fill
    # preserved each intended sequence, so the fresh container's labels equal
    # opt_seq of the supplied sets, or range_labels of the payload shape.
    if index is not None:
        Assert(gi == opt_seq(index))
        Assert(ToSeq(result.index) == opt_seq(index))
    else:
        Assert(is_range(gi, nrows))
        Assert(is_range(ToSeq(result.index), nrows))
    if columns is not None:
        Assert(gc == opt_seq(columns))
        Assert(ToSeq(result.columns) == opt_seq(columns))
    else:
        Assert(is_range(gc, ncols))
        Assert(is_range(ToSeq(result.columns), ncols))
    return result"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) Structurally-different but CORRECT array branch: COMPUTE THE COLUMN AXIS
# FIRST, then the index axis (the two axes are independent), and reorder the
# closing per-axis framing asserts to match (columns block before index block).
# Same observable Frame; the supplied/default choice per axis is unchanged. ALL
# gold framing asserts (gi/gc == opt_seq / is_range, and the result.index/.columns
# pins around the Frame construction) are KEPT verbatim, only the ORDER of the two
# independent axis computations changes (pilot trap #2 avoided: nothing dropped;
# trap #3 avoided: no loop-direction flip — the helpers are untouched). If it
# fails to verify the spec is over-fit to the index-first ordering => SPEC-TOO-STRONG.
_IMPL_AXES_REORDERED = """    if data_is_frame:
        if columns is not None:
            refreshed = _copy_labels(columns)  # type: List[int]
            df.columns = refreshed
        # The supplied row labels are intentionally NOT applied here: the
        # container keeps its own row labels.
        return df
    new_columns = []  # type: List[int]
    if columns is not None:
        new_columns = _copy_labels(columns)
    else:
        new_columns = _range_labels(ncols)
    new_index = []  # type: List[int]
    if index is not None:
        new_index = _copy_labels(index)
    else:
        new_index = _range_labels(nrows)
    gi = ToSeq(new_index)    # type: PSeq[int]
    gc = ToSeq(new_columns)  # type: PSeq[int]
    result = Frame(new_index, new_columns, gi, gc)  # type: Frame
    if columns is not None:
        Assert(gc == opt_seq(columns))
        Assert(ToSeq(result.columns) == opt_seq(columns))
    else:
        Assert(is_range(gc, ncols))
        Assert(is_range(ToSeq(result.columns), ncols))
    if index is not None:
        Assert(gi == opt_seq(index))
        Assert(ToSeq(result.index) == opt_seq(index))
    else:
        Assert(is_range(gi, nrows))
        Assert(is_range(ToSeq(result.index), nrows))
    return result"""
_POS_AXES_REORDERED = _swap(_BASE, _IMPL, _IMPL_AXES_REORDERED)

# (5b) Structurally-different but CORRECT frame branch: replace the nested-if
# column refresh with a flat guard using a local boolean, and hoist the
# early-return into an explicit branch. Identical control flow (refresh columns
# iff a set is supplied, never touch the index, return the same df). The array
# branch is kept verbatim with all its framing asserts. If it fails to verify the
# spec is over-fit to the nested-if shape of the frame branch => SPEC-TOO-STRONG.
_IMPL_FRAME_RESHAPED = """    if data_is_frame:
        has_cols = columns is not None  # type: bool
        if has_cols:
            refreshed = _copy_labels(columns)  # type: List[int]
            df.columns = refreshed
        # The supplied row labels are intentionally NOT applied here: the
        # container keeps its own row labels.
        return df
    new_index = []  # type: List[int]
    if index is not None:
        new_index = _copy_labels(index)
    else:
        new_index = _range_labels(nrows)
    new_columns = []  # type: List[int]
    if columns is not None:
        new_columns = _copy_labels(columns)
    else:
        new_columns = _range_labels(ncols)
    gi = ToSeq(new_index)    # type: PSeq[int]
    gc = ToSeq(new_columns)  # type: PSeq[int]
    result = Frame(new_index, new_columns, gi, gc)  # type: Frame
    if index is not None:
        Assert(gi == opt_seq(index))
        Assert(ToSeq(result.index) == opt_seq(index))
    else:
        Assert(is_range(gi, nrows))
        Assert(is_range(ToSeq(result.index), nrows))
    if columns is not None:
        Assert(gc == opt_seq(columns))
        Assert(ToSeq(result.columns) == opt_seq(columns))
    else:
        Assert(is_range(gc, ncols))
        Assert(is_range(ToSeq(result.columns), ncols))
    return result"""
_POS_FRAME_RESHAPED = _swap(_BASE, _IMPL, _IMPL_FRAME_RESHAPED)

# (6) ADMISSIBILITY. Before the gold body runs, an F2P-shaped in-domain input is
# built and EVERY Requires conjunct of wrap_in_container is asserted for it: a
# fresh container (df_probe) at full permission plus a supplied index/columns
# whose halves are therefore establishable, and a non-negative payload shape —
# exactly the F2P shape (a DataFrame input with a supplied original index). The
# gold body is then kept verbatim. If a conjunct could not be established for a
# normal input => PRECOND-TOO-STRONG. (The probe builds its own Frame + label
# lists so it does not consume any permission the gold body still needs.)
#
# Assert-style rather than the self-call this case used before: wrap_in_container
# now carries Requires(MustTerminate(3)) (total correctness), and Nagini demands a
# callee's obligation level be STRICTLY below its caller's, so an equal-level
# self-call is rejected by the obligation system ("Callee wrap_in_container might
# not take all unsatisfied obligations from the caller") — an artifact of the
# termination spec, unrelated to the value preconditions this case probes. The
# container constructor is still a REAL call site (level 1 < 3), so its own
# Requires are discharged for these arguments.
_IMPL_ADMISS = """    idx_probe = [0, 1]  # type: List[int]
    col_probe = [0, 1, 2]  # type: List[int]
    di = ToSeq(idx_probe)  # type: PSeq[int]
    dc = ToSeq(col_probe)  # type: PSeq[int]
    df_probe = Frame(idx_probe, col_probe, di, dc)  # type: Frame
    sup_index = [7, 8]  # type: List[int]
    sup_cols = [9, 9, 9]  # type: List[int]
    Assert(Acc(df_probe.index) and Acc(df_probe.columns))
    Assert(Acc(list_pred(df_probe.index)) and Acc(list_pred(df_probe.columns)))
    Assert(Implies(sup_cols is not None, Acc(list_pred(sup_cols), 1 / 2)))
    Assert(Implies(sup_index is not None, Acc(list_pred(sup_index), 1 / 2)))
    Assert(2 >= 0 and 3 >= 0)
    Assert(len(df_probe.index) == 2 and len(df_probe.columns) == 3)
    Assert(len(sup_index) == 2 and len(sup_cols) == 3)
    if data_is_frame:
        if columns is not None:
            refreshed = _copy_labels(columns)  # type: List[int]
            df.columns = refreshed
        # The supplied row labels are intentionally NOT applied here: the
        # container keeps its own row labels.
        return df
    new_index = []  # type: List[int]
    if index is not None:
        new_index = _copy_labels(index)
    else:
        new_index = _range_labels(nrows)
    new_columns = []  # type: List[int]
    if columns is not None:
        new_columns = _copy_labels(columns)
    else:
        new_columns = _range_labels(ncols)
    gi = ToSeq(new_index)    # type: PSeq[int]
    gc = ToSeq(new_columns)  # type: PSeq[int]
    result = Frame(new_index, new_columns, gi, gc)  # type: Frame
    if index is not None:
        Assert(gi == opt_seq(index))
        Assert(ToSeq(result.index) == opt_seq(index))
    else:
        Assert(is_range(gi, nrows))
        Assert(is_range(ToSeq(result.index), nrows))
    if columns is not None:
        Assert(gc == opt_seq(columns))
        Assert(ToSeq(result.columns) == opt_seq(columns))
    else:
        Assert(is_range(gc, ncols))
        Assert(is_range(ToSeq(result.columns), ncols))
    return result"""
_POS_ADMISS = _swap(_BASE, _IMPL, _IMPL_ADMISS)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) THE BUG ITSELF — re-introduce the deleted index write in the frame branch
# (exactly model_prepatch.py): when an index is supplied, overwrite the
# container's OWN row labels with it. `df` is FULL permission, so the write is
# LEGAL; it is rejected on the VALUE postcondition
# Implies(data_is_frame, ToSeq(Result().index) == Old(ToSeq(df.index))) — the
# discriminating index-preservation clause that is the whole content of the fix.
_IMPL_PREPATCH_INDEX_WRITE = """    if data_is_frame:
        if columns is not None:
            refreshed = _copy_labels(columns)  # type: List[int]
            df.columns = refreshed
        # PRE-PATCH BUG: the supplied row labels ARE applied here, overwriting the
        # container's own row labels.
        if index is not None:
            relabelled = _copy_labels(index)  # type: List[int]
            df.index = relabelled
        return df
    new_index = []  # type: List[int]
    if index is not None:
        new_index = _copy_labels(index)
    else:
        new_index = _range_labels(nrows)
    new_columns = []  # type: List[int]
    if columns is not None:
        new_columns = _copy_labels(columns)
    else:
        new_columns = _range_labels(ncols)
    gi = ToSeq(new_index)    # type: PSeq[int]
    gc = ToSeq(new_columns)  # type: PSeq[int]
    result = Frame(new_index, new_columns, gi, gc)  # type: Frame
    if index is not None:
        Assert(gi == opt_seq(index))
        Assert(ToSeq(result.index) == opt_seq(index))
    else:
        Assert(is_range(gi, nrows))
        Assert(is_range(ToSeq(result.index), nrows))
    if columns is not None:
        Assert(gc == opt_seq(columns))
        Assert(ToSeq(result.columns) == opt_seq(columns))
    else:
        Assert(is_range(gc, ncols))
        Assert(is_range(ToSeq(result.columns), ncols))
    return result"""
_RIVAL_PREPATCH = _swap(_BASE, _IMPL, _IMPL_PREPATCH_INDEX_WRITE)

# (2) FRAME-MUTATION on the read-only `columns` (MANDATORY). Inside the frame
# branch, where `columns is not None`, write back through the supplied set
# (columns[0] = columns[0], value-wise a no-op) under a `len(columns) > 0` guard
# so the index is provably in-range — leaving INSUFFICIENT PERMISSION as the sole
# blocker. `columns` is Acc(list_pred(columns), 1/2): WRITING a list element needs
# FULL permission, which the caller does not hold. The gold body is otherwise kept
# verbatim, so the rejection is attributable solely to the frame write.
_IMPL_FRAME_MUTATE_COLUMNS = """    if data_is_frame:
        if columns is not None:
            if len(columns) > 0:
                columns[0] = columns[0]
            refreshed = _copy_labels(columns)  # type: List[int]
            df.columns = refreshed
        # The supplied row labels are intentionally NOT applied here: the
        # container keeps its own row labels.
        return df
    new_index = []  # type: List[int]
    if index is not None:
        new_index = _copy_labels(index)
    else:
        new_index = _range_labels(nrows)
    new_columns = []  # type: List[int]
    if columns is not None:
        new_columns = _copy_labels(columns)
    else:
        new_columns = _range_labels(ncols)
    gi = ToSeq(new_index)    # type: PSeq[int]
    gc = ToSeq(new_columns)  # type: PSeq[int]
    result = Frame(new_index, new_columns, gi, gc)  # type: Frame
    if index is not None:
        Assert(gi == opt_seq(index))
        Assert(ToSeq(result.index) == opt_seq(index))
    else:
        Assert(is_range(gi, nrows))
        Assert(is_range(ToSeq(result.index), nrows))
    if columns is not None:
        Assert(gc == opt_seq(columns))
        Assert(ToSeq(result.columns) == opt_seq(columns))
    else:
        Assert(is_range(gc, ncols))
        Assert(is_range(ToSeq(result.columns), ncols))
    return result"""
_RIVAL_FRAME_MUTATE_COLUMNS = _swap(_BASE, _IMPL, _IMPL_FRAME_MUTATE_COLUMNS)

# (2b) FRAME-MUTATION on the read-only `index` (MANDATORY, second read-only
# surface). In the array branch, where `index is not None`, write back through the
# supplied set (index[0] = index[0], value-wise a no-op) under a `len(index) > 0`
# guard. `index` is Acc(list_pred(index), 1/2): the element write needs FULL
# permission, which the caller does not hold. The gold body is otherwise kept
# verbatim so the rejection is attributable solely to the frame write.
_IMPL_FRAME_MUTATE_INDEX = """    if data_is_frame:
        if columns is not None:
            refreshed = _copy_labels(columns)  # type: List[int]
            df.columns = refreshed
        # The supplied row labels are intentionally NOT applied here: the
        # container keeps its own row labels.
        return df
    new_index = []  # type: List[int]
    if index is not None:
        if len(index) > 0:
            index[0] = index[0]
        new_index = _copy_labels(index)
    else:
        new_index = _range_labels(nrows)
    new_columns = []  # type: List[int]
    if columns is not None:
        new_columns = _copy_labels(columns)
    else:
        new_columns = _range_labels(ncols)
    gi = ToSeq(new_index)    # type: PSeq[int]
    gc = ToSeq(new_columns)  # type: PSeq[int]
    result = Frame(new_index, new_columns, gi, gc)  # type: Frame
    if index is not None:
        Assert(gi == opt_seq(index))
        Assert(ToSeq(result.index) == opt_seq(index))
    else:
        Assert(is_range(gi, nrows))
        Assert(is_range(ToSeq(result.index), nrows))
    if columns is not None:
        Assert(gc == opt_seq(columns))
        Assert(ToSeq(result.columns) == opt_seq(columns))
    else:
        Assert(is_range(gc, ncols))
        Assert(is_range(ToSeq(result.columns), ncols))
    return result"""
_RIVAL_FRAME_MUTATE_INDEX = _swap(_BASE, _IMPL, _IMPL_FRAME_MUTATE_INDEX)

# (3) PARTIAL-DOMAIN — frame branch skips the column refresh entirely (return df
# without ever setting df.columns). Correct on the index axis (kept) and on the
# whole array branch, and accidentally correct on the (data_is_frame,
# columns is None) sub-domain (where columns must be kept anyway), but WRONG on
# the (data_is_frame, columns is not None) sub-domain: the refreshed column labels
# are never applied. Violates Implies(data_is_frame and columns is not None,
# ToSeq(Result().columns) == opt_seq(columns)).
_IMPL_NO_COLUMN_REFRESH = """    if data_is_frame:
        # PARTIAL-DOMAIN BUG: the supplied columns are NOT applied; the container
        # keeps its own columns even when a replacement set is supplied.
        return df
    new_index = []  # type: List[int]
    if index is not None:
        new_index = _copy_labels(index)
    else:
        new_index = _range_labels(nrows)
    new_columns = []  # type: List[int]
    if columns is not None:
        new_columns = _copy_labels(columns)
    else:
        new_columns = _range_labels(ncols)
    gi = ToSeq(new_index)    # type: PSeq[int]
    gc = ToSeq(new_columns)  # type: PSeq[int]
    result = Frame(new_index, new_columns, gi, gc)  # type: Frame
    if index is not None:
        Assert(gi == opt_seq(index))
        Assert(ToSeq(result.index) == opt_seq(index))
    else:
        Assert(is_range(gi, nrows))
        Assert(is_range(ToSeq(result.index), nrows))
    if columns is not None:
        Assert(gc == opt_seq(columns))
        Assert(ToSeq(result.columns) == opt_seq(columns))
    else:
        Assert(is_range(gc, ncols))
        Assert(is_range(ToSeq(result.columns), ncols))
    return result"""
_RIVAL_NO_COLUMN_REFRESH = _swap(_BASE, _IMPL, _IMPL_NO_COLUMN_REFRESH)

# (3b) PARTIAL-DOMAIN — array branch sizes the default row labelling to `ncols`
# instead of `nrows` on the index=None corner (the previously-blind None corner
# that panel D1 closed with the is_range clauses). Correct whenever an index IS
# supplied, and accidentally correct when nrows == ncols (a square payload), but
# WRONG on the (not data_is_frame, index is None, nrows != ncols) sub-domain:
# the row axis gets range(ncols) rather than the gold RangeIndex(nrows). Violates
# Implies(not data_is_frame and index is None, is_range(ToSeq(Result().index),
# nrows)).
_IMPL_INDEX_WRONG_SIZE = """    if data_is_frame:
        if columns is not None:
            refreshed = _copy_labels(columns)  # type: List[int]
            df.columns = refreshed
        # The supplied row labels are intentionally NOT applied here: the
        # container keeps its own row labels.
        return df
    new_index = []  # type: List[int]
    if index is not None:
        new_index = _copy_labels(index)
    else:
        new_index = _range_labels(ncols)
    new_columns = []  # type: List[int]
    if columns is not None:
        new_columns = _copy_labels(columns)
    else:
        new_columns = _range_labels(ncols)
    gi = ToSeq(new_index)    # type: PSeq[int]
    gc = ToSeq(new_columns)  # type: PSeq[int]
    result = Frame(new_index, new_columns, gi, gc)  # type: Frame
    if index is not None:
        Assert(gi == opt_seq(index))
        Assert(ToSeq(result.index) == opt_seq(index))
    else:
        Assert(is_range(gi, nrows))
        Assert(is_range(ToSeq(result.index), nrows))
    if columns is not None:
        Assert(gc == opt_seq(columns))
        Assert(ToSeq(result.columns) == opt_seq(columns))
    else:
        Assert(is_range(gc, ncols))
        Assert(is_range(ToSeq(result.columns), ncols))
    return result"""
_RIVAL_INDEX_WRONG_SIZE = _swap(_BASE, _IMPL, _IMPL_INDEX_WRONG_SIZE)

# (4) PARTIAL-DOMAIN — array branch SWAPS the two supplied axes: stamp the
# supplied `index` onto the column axis and the supplied `columns` onto the row
# axis (and the default labels likewise swapped to keep the proof asserts about
# new_index/new_columns coherent). Accidentally correct only on the fully-
# symmetric corner (index is None and columns is None and nrows == ncols); wrong
# the moment a set is supplied for an axis or the shape is non-square. Violates
# the array-branch opt_seq / is_range clauses for both axes.
_IMPL_AXES_SWAPPED = """    if data_is_frame:
        if columns is not None:
            refreshed = _copy_labels(columns)  # type: List[int]
            df.columns = refreshed
        # The supplied row labels are intentionally NOT applied here: the
        # container keeps its own row labels.
        return df
    new_index = []  # type: List[int]
    if columns is not None:
        new_index = _copy_labels(columns)
    else:
        new_index = _range_labels(ncols)
    new_columns = []  # type: List[int]
    if index is not None:
        new_columns = _copy_labels(index)
    else:
        new_columns = _range_labels(nrows)
    gi = ToSeq(new_index)    # type: PSeq[int]
    gc = ToSeq(new_columns)  # type: PSeq[int]
    result = Frame(new_index, new_columns, gi, gc)  # type: Frame
    if index is not None:
        Assert(gi == opt_seq(index))
        Assert(ToSeq(result.index) == opt_seq(index))
    else:
        Assert(is_range(gi, nrows))
        Assert(is_range(ToSeq(result.index), nrows))
    if columns is not None:
        Assert(gc == opt_seq(columns))
        Assert(ToSeq(result.columns) == opt_seq(columns))
    else:
        Assert(is_range(gc, ncols))
        Assert(is_range(ToSeq(result.columns), ncols))
    return result"""
_RIVAL_AXES_SWAPPED = _swap(_BASE, _IMPL, _IMPL_AXES_SWAPPED)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-array-axes-reordered", "kind": "soundness", "expect": "verify",
     "module": _POS_AXES_REORDERED,
     "rationale": "structurally-different but semantically identical array branch: the two "
                  "INDEPENDENT axis computations (columns vs index) are reordered (columns first) and "
                  "their closing per-axis framing asserts reordered to match. The supplied/default "
                  "choice per axis and the resulting Frame are unchanged. ALL gold framing asserts "
                  "(gi/gc == opt_seq / is_range and the result.index/.columns pins) are kept verbatim "
                  "(pilot trap #2 avoided); the _copy_labels/_range_labels helpers are untouched, so "
                  "no front-recursive-fold lemma is needed (trap #3 avoided). If it fails to verify, "
                  "the postcondition is over-fit to the index-first ordering => SPEC-TOO-STRONG. Also "
                  "a cheapest honest impl: no echoable oracle, it must build the right labels per axis."},
    {"id": "pos-frame-branch-reshaped", "kind": "soundness", "expect": "verify",
     "module": _POS_FRAME_RESHAPED,
     "rationale": "a correct frame branch with a DIFFERENT shape: the nested column-refresh guard is "
                  "hoisted through a local boolean `has_cols`, semantics identical (refresh columns "
                  "iff a set is supplied, never touch the index, return the same df). The array branch "
                  "and every framing assert are kept verbatim. If it fails to verify the spec is "
                  "over-fit to the literal nested-if shape of the frame branch => SPEC-TOO-STRONG."},
    {"id": "admiss-self-call-frame-input", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "an F2P-shaped in-domain input (a fresh container df_probe plus a supplied "
                  "index/columns — the F2P shape: a DataFrame input with a supplied original index) "
                  "with EVERY Requires conjunct asserted for it: Acc(df.index)/Acc(df.columns) + the "
                  "list predicates + the conditional 1/2 perms for the supplied sets + nrows/ncols>=0, "
                  "plus the non-degenerate shape (2 rows, 3 columns). The probe builds its own Frame "
                  "and label lists so it consumes no permission the gold body still needs. If a "
                  "conjunct could not be established for a normal wrapper input => PRECOND-TOO-STRONG. "
                  "Assert-style rather than a self-call: under Requires(MustTerminate(3)) an "
                  "equal-level recursive self-call is rejected by the obligation system, an artifact "
                  "unrelated to the value preconditions."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-prepatch-index-write", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PREPATCH,
     "refinement": "this re-introduces the deleted write (model_prepatch.py verbatim): in the "
                   "already-a-container branch it overwrites df.index with the supplied index. Its "
                   "faithful real patch is the UNCHANGED pre-patch _wrap_in_pandas_container, which "
                   "executes `if index is not None: data_to_wrap.index = index`. That is exactly the "
                   "bug the F2P test asserts against: test_set_output_pandas_keep_index fits a "
                   "transformer that re-indexes its DataFrame output to ['s0','s1'], the wrapper is "
                   "called with the original index=[0,1], and the test asserts X_trans.index == "
                   "['s0','s1']. The pre-patch write would overwrite the kept ['s0','s1'] with [0,1] "
                   "(and in the reporter's aggregation scenario raise ValueError: Length mismatch) — "
                   "it would NOT resolve.",
     "rationale": "the DISCRIMINATING bug this patch fixes (mirrors G-DIFF / model_prepatch.py). "
                  "df is FULL permission so the write is LEGAL; rejection source: the VALUE "
                  "postcondition Implies(data_is_frame, ToSeq(Result().index) == Old(ToSeq(df.index))) "
                  "— overwriting df.index makes Result().index == opt_seq(index), not the container's "
                  "Old(ToSeq(df.index)). If it verified => SPEC-TOO-WEAK (admits the very bug)."},
    {"id": "rival-frame-mutate-columns", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_MUTATE_COLUMNS,
     "refinement": "in the frame branch it writes through the read-only supplied `columns` "
                   "(columns[0] = columns[0]; value-wise a no-op) under a len>0 guard before copying. "
                   "A faithful real patch that mutated the caller's supplied column array in place "
                   "would corrupt a label set the caller still holds (sklearn passes "
                   "estimator.get_feature_names_out() output / a user list it may reuse) — an illegal "
                   "aliasing side effect outside the documented contract; such a patch is not the gold "
                   "fix and the P2P suite (which reuses the supplied columns object) would observe the "
                   "mutation. It would NOT resolve. The no-op value is irrelevant: the WRITE is illegal.",
     "rationale": "FRAME-MUTATION (MANDATORY, the #1 weakness class). `columns` is held at "
                  "Acc(list_pred(columns), 1/2) (read-only, returned at the same fraction); the "
                  "element write columns[0]=... needs FULL write permission, which the caller does "
                  "not hold. The len>0 guard makes the index provably in-range, so INSUFFICIENT "
                  "PERMISSION is the sole blocker. Rejection source: the PERMISSION SYSTEM, not the "
                  "postcondition. The rest of the gold body is kept verbatim, so the rejection is "
                  "attributable solely to the frame write. If it verified => the read-only contract "
                  "is unsound."},
    {"id": "rival-frame-mutate-index", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_MUTATE_INDEX,
     "refinement": "in the array branch it writes through the read-only supplied `index` "
                   "(index[0] = index[0]; value-wise a no-op) under a len>0 guard before copying. A "
                   "faithful real patch mutating the caller's supplied index array in place would "
                   "corrupt a label set the caller still holds (the wrapper is called with "
                   "getattr(original_input,'index',None) — the original input's index, which the "
                   "caller keeps) — an illegal aliasing side effect, not the gold fix. It would NOT "
                   "resolve. The no-op value is irrelevant: the WRITE itself is illegal.",
     "rationale": "FRAME-MUTATION (MANDATORY, second read-only surface). `index` is held at "
                  "Acc(list_pred(index), 1/2); the element write index[0]=... needs FULL permission. "
                  "The len>0 guard makes the index in-range so INSUFFICIENT PERMISSION is the sole "
                  "blocker. Rejection source: the PERMISSION SYSTEM. The rest of the gold body is kept "
                  "verbatim, so the rejection is attributable solely to the frame write. If it "
                  "verified => the read-only contract is unsound."},
    {"id": "rival-frame-no-column-refresh", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NO_COLUMN_REFRESH,
     "refinement": "in the frame branch it never applies the supplied columns (returns df without "
                   "setting df.columns). A faithful real patch that dropped `if columns is not None: "
                   "data_to_wrap.columns = columns` would leave an already-a-DataFrame output with its "
                   "stale column labels instead of the estimator's feature names. The P2P test "
                   "test__wrap_in_pandas_container_dense_update_columns_and_index passes a DataFrame "
                   "with new_columns and asserts new_df.columns == new_columns; with the refresh "
                   "dropped the columns would be the frame's original ones — it would NOT resolve.",
     "rationale": "PARTIAL-DOMAIN: correct on the index axis and the whole array branch, and "
                  "accidentally correct when columns is None (columns kept anyway), but WRONG on the "
                  "(data_is_frame, columns is not None) sub-domain. Rejection source: the postcondition "
                  "Implies(data_is_frame and columns is not None, ToSeq(Result().columns) == "
                  "opt_seq(columns)) — the unrefreshed columns equal Old(ToSeq(df.columns)) != "
                  "opt_seq(columns) in general. If it verified => SPEC-TOO-WEAK (column refresh "
                  "unpinned on the frame branch)."},
    {"id": "rival-array-index-wrong-size", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_INDEX_WRONG_SIZE,
     "refinement": "in the array branch, on the index=None corner it builds the default row labelling "
                   "sized to ncols instead of nrows (range(ncols), not range(nrows)). A faithful real "
                   "patch that built pd.DataFrame(data, index=range(n_features)) instead of leaving "
                   "index=None (RangeIndex(n_samples)) would mislabel / mis-size the row axis of every "
                   "freshly-wrapped ndarray whose row count differs from its column count — the dense "
                   "P2P paths (test__wrap_in_pandas_container_dense) build frames whose row index must "
                   "be range(n_samples). It would NOT resolve on a non-square payload.",
     "rationale": "PARTIAL-DOMAIN on the previously-blind index=None corner (panel D1 pinned it with "
                  "is_range). Correct whenever an index IS supplied, and accidentally correct when "
                  "nrows == ncols, but WRONG on (not data_is_frame, index is None, nrows != ncols). "
                  "Rejection source: the postcondition Implies(not data_is_frame and index is None, "
                  "is_range(ToSeq(Result().index), nrows)) — range(ncols) has length ncols != nrows, "
                  "failing is_range(..., nrows). The proof Assert(is_range(gi, nrows)) on new_index = "
                  "_range_labels(ncols) is itself unprovable when nrows != ncols. If it verified => "
                  "SPEC-TOO-WEAK (the row-axis default size unpinned)."},
    {"id": "rival-array-axes-swapped", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_AXES_SWAPPED,
     "refinement": "in the array branch it stamps the supplied `columns` onto the row axis and the "
                   "supplied `index` onto the column axis (defaults swapped likewise). A faithful real "
                   "patch that called pd.DataFrame(data, index=columns, columns=index) would put the "
                   "feature names on the rows and the sample index on the columns of every freshly-"
                   "wrapped array — every set_output='pandas' ndarray result would be transposed-"
                   "labelled. The dense P2P (test__wrap_in_pandas_container_dense, asserts index and "
                   "columns each take their OWN supplied set) would fail. It would NOT resolve.",
     "rationale": "PARTIAL-DOMAIN / axis confusion. Accidentally correct only on the fully-symmetric "
                  "corner (index is None and columns is None and nrows == ncols); wrong the moment a "
                  "set is supplied for an axis or the shape is non-square. Rejection source: the array-"
                  "branch postconditions — ToSeq(Result().index) is now opt_seq(columns) (or "
                  "range(ncols)) instead of the required opt_seq(index) / is_range(..., nrows), and "
                  "symmetrically for columns; the proof asserts Assert(gi == opt_seq(index)) on "
                  "new_index = _copy_labels(columns) are unprovable. If it verified => SPEC-TOO-WEAK "
                  "(axes not pinned to their own supplied sets)."},
]

# ===========================================================================
# AXIOM LANE — empty. This bundle consumes NO @ContractOnly axiom (meta.json
# axioms is []): the label-routing rule is modeled DEEPLY by wrap_in_container
# over the two touched facets. The deep model is validated == the real post-patch
# _wrap_in_pandas_container out-of-band by axiom_check.py (G-AX, A-reference:
# boundary battery + 2000 fuzz inputs over real pandas/numpy, both corners of
# both axes, plus the pre-patch divergence raising the reported length-mismatch
# ValueError), which is NOT in the PBT lane's scope. deep_model_references are
# A-reference, so there is no in-domain @Pure axiom soundness/containment
# obligation for PBT to check here.
# ===========================================================================
AXIOM_TESTS = []
