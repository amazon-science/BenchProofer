# properties.py — PBT falsification battery for scikit-learn__scikit-learn-25102.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that SHARE the frozen spec (only text INSIDE the single
# `# impl-start`/`# impl-end` region of `select_columns` differs — guaranteed by
# region-surgery via _swap) and are checked by Nagini verify + markers.same_spec.
# Axiom cases are real-callee probes run in the instance image (Docker).
#
# Defended surface — `select_columns(df: Frame, mask: List[int]) -> Frame`
# (models SelectorMixin._transform's DataFrame column subset; gold:
# `_safe_indexing(X, mask, axis=1)` / the new `X.iloc[:, :0]` empty branch):
#   Requires (ALL inputs READ-ONLY, half permission):
#     Acc(df.index, 1/2), Acc(df.descs, 1/2)
#     Acc(list_pred(df.index), 1/2), Acc(list_pred(df.descs), 1/2)
#     Acc(list_pred(mask), 1/2)
#     len(df.descs) == len(mask)
#   Ensures (the two LOAD-BEARING clauses):
#     (1) ToSeq(Result().descs) == kept_descs(ToSeq(df.descs), ToSeq(mask))
#         -- per-column descriptors of the RETAINED columns, in input order,
#            each carried over UNCHANGED (never a single coerced shared value).
#     (2) ToSeq(Result().index) == ToSeq(df.index)
#         -- the output keeps the input's OWN row labels for ANY retained count
#            including zero.
#   plus the read-only permissions are RETURNED at 1/2 (inputs never mutated).
#
# Oracle character: `kept_descs` is a @Pure FRONT-RECURSIVE fold over the INPUT
# args (df.descs, mask) — it is fully GROUNDED in the inputs, not an opaque
# answer-key. There is therefore no "wrong value to echo": any impl that pins
# Result().descs to kept_descs(ToSeq(df.descs), ToSeq(mask)) is doing the genuine
# per-column compress. The ungrounded-oracle-echo slot is consequently filled by
# an HONEST cheapest-impl positive control (see 'assessment').
#
# This bundle has NO @ContractOnly axiom (meta.axioms == []); kept_descs +
# _copy_labels are A-REFERENCE deep models, validated == the real unchanged
# callee `sklearn.utils._safe_indexing(X, mask, axis=1)` (and the post-patch
# `X.iloc[:, :0]` empty branch) by G-AX. The AXIOM_TESTS below re-run that
# real-callee soundness + caller-domain containment check in-container.
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-25102"
FLOAT_ENCODING = None   # meta.json float_encoding is null (List[int] carrier; no floats)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen impl region (between `# impl-start` and `# impl-end` of
# select_columns). EVERY variant is produced by _swap on a substring that lies
# ENTIRELY inside this region (the loop body, the invariants nested in impl, or
# the local-init block), so the spec view — axioms / pure / pre / post / the
# Frame & _copy_labels signatures — is untouched => same_spec holds.
# ---------------------------------------------------------------------------


# ===========================================================================
# 1. FRAME-MUTATION (MANDATORY — every input is read-only Acc(...,1/2)).
#    Rival WRITES to the read-only input container (df.descs) in place to plant
#    the answer. A store df.descs[i-1] = d needs FULL list_pred(df.descs)
#    permission; the spec lends only Acc(list_pred(df.descs), 1/2) (re-asserted
#    in the loop Invariant and re-granted by the postcondition). Must REJECT for
#    INSUFFICIENT PERMISSION. The gold invariants/asserts are kept verbatim so
#    the rejection is attributable to the WRITE, not to a broken proof.
# ===========================================================================
_frame_mutation = _swap(
    _BASE,
    """        d = df.descs[i - 1]
        m = mask[i - 1]""",
    """        d = df.descs[i - 1]
        m = mask[i - 1]
        # frame-mutation attack: overwrite the read-only input container in place
        # (touch the descriptor we just read). Needs FULL permission on
        # list_pred(df.descs); only Acc(...,1/2) is held => must fail on the store.
        df.descs[i - 1] = d""",
)


# ===========================================================================
# 2. PER-COLUMN HOMOGENISATION (the prepatch bug, restated as a uniqueness
#    rival; reject). Instead of carrying over each retained column's OWN
#    descriptor (`d = df.descs[i-1]`), stamp EVERY kept column with one shared
#    descriptor df.descs[0] (the first column's). This is exactly
#    model_prepatch.py's `X[:, safe_mask(X, mask)]` NumPy coercion. The
#    descriptor invariant is relaxed to be self-consistent with the wrong impl
#    so the rejection is attributable to POST clause (1), not a broken invariant.
# ===========================================================================
_homogenise = _swap(
    _BASE,
    """        d = df.descs[i - 1]
        m = mask[i - 1]""",
    """        d = df.descs[0]   # homogenisation: ALL kept columns get column 0's descriptor
        m = mask[i - 1]""",
)
# relax the exact-compress invariant (it no longer holds with the homogenised d);
# keep only the framing perm on new_descs so the rejection lands on POST (1).
_homogenise = _swap(
    _homogenise,
    """        Invariant(ToSeq(new_descs) ==
                  kept_descs(ToSeq(df.descs).drop(i), ToSeq(mask).drop(i)))""",
    """        Invariant(len(new_descs) >= 0)   # exact-compress invariant dropped (impl homogenises)""",
)
# the per-element relate-asserts about df.descs[i-1] are no longer needed for the
# (now-relaxed) descriptor invariant; the mask asserts stay valid. Drop only the
# descs-head asserts that referenced the original `d`-as-head reasoning so the
# variant still translates (the kept asserts remain TRUE statements).
_homogenise = _swap(
    _homogenise,
    """        Assert(ToSeq(df.descs).drop(i - 1)[0] == d)
        Assert(ToSeq(mask).drop(i - 1)[0] == m)
        Assert(ToSeq(df.descs).drop(i - 1).drop(1) == ToSeq(df.descs).drop(i))
        Assert(ToSeq(mask).drop(i - 1).drop(1) == ToSeq(mask).drop(i))""",
    """        Assert(ToSeq(mask).drop(i - 1)[0] == m)
        Assert(ToSeq(mask).drop(i - 1).drop(1) == ToSeq(mask).drop(i))""",
)


# ===========================================================================
# 3. MASK SUB-DOMAIN IGNORED (partial-domain; reject). Correct on every column
#    EXCEPT the first (position 0 = the i==1 step): there, ignore the mask flag
#    and always KEEP the column. Diverges from kept_descs whenever mask[0]==0.
#    The exact-compress invariant is relaxed at the boundary so the rejection
#    lands on POST (1) (the result includes a column the mask dropped).
# ===========================================================================
_mask_subdomain = _swap(
    _BASE,
    """        d = df.descs[i - 1]
        m = mask[i - 1]""",
    """        d = df.descs[i - 1]
        m = mask[i - 1]
        if i == 1:
            m = 1   # partial-domain: force-keep column 0 regardless of its mask flag""",
)
_mask_subdomain = _swap(
    _mask_subdomain,
    """        Invariant(ToSeq(new_descs) ==
                  kept_descs(ToSeq(df.descs).drop(i), ToSeq(mask).drop(i)))""",
    """        Invariant(len(new_descs) >= 0)   # exact-compress invariant dropped (col 0 force-kept)""",
)
_mask_subdomain = _swap(
    _mask_subdomain,
    """        Assert(ToSeq(df.descs).drop(i - 1)[0] == d)
        Assert(ToSeq(mask).drop(i - 1)[0] == m)
        Assert(ToSeq(df.descs).drop(i - 1).drop(1) == ToSeq(df.descs).drop(i))
        Assert(ToSeq(mask).drop(i - 1).drop(1) == ToSeq(mask).drop(i))""",
    """        Assert(ToSeq(df.descs).drop(i - 1)[0] == d)
        Assert(ToSeq(df.descs).drop(i - 1).drop(1) == ToSeq(df.descs).drop(i))
        Assert(ToSeq(mask).drop(i - 1).drop(1) == ToSeq(mask).drop(i))""",
)


# ===========================================================================
# 4. POSITIONAL RE-INDEX (the SECOND prepatch bug, restated; reject). Instead of
#    carrying over the input's own row labels (_copy_labels(df.index)), return a
#    FRESH empty index (a stand-in for the NumPy positional [0..n-1] relabel that
#    drops the DataFrame's own .index). This is model_prepatch_2.py. The index
#    invariant is relaxed to the empty witness so the rejection lands on POST (2)
#    (ToSeq(Result().index) == ToSeq(df.index)).
# ===========================================================================
_positional_index = _swap(
    _BASE,
    """    new_index = _copy_labels(df.index)  # type: List[int]""",
    """    new_index = []  # type: List[int]   # positional re-index: drop the input's own labels""",
)
_positional_index = _swap(
    _positional_index,
    """        Invariant(ToSeq(new_index) == ToSeq(df.index))""",
    """        Invariant(ToSeq(new_index) == PSeq(0).take(0))   # new_index stays empty (labels dropped)""",
)


# ===========================================================================
# 5. POSITIVE CONTROL — soundness (verify). Structurally different but CORRECT.
#    (a) reorder the two independent local initialisers (new_descs list before
#        new_index copy), and
#    (b) reshape the keep-test `if m != 0:` into the logically identical
#        `if not (m == 0):`.
#    The BACKWARD loop direction and the front-recursive kept_descs unfold are
#    preserved (a forward-append would need an f(a+b) fold lemma — AVOID #3), and
#    every gold invariant/assert is kept verbatim, so the gold proof still
#    discharges. MUST VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================
_pos_control = _swap(
    _BASE,
    """    new_index = _copy_labels(df.index)  # type: List[int]
    new_descs = []  # type: List[int]
    i = len(df.descs)""",
    """    new_descs = []  # type: List[int]   # reordered: build the descs accumulator first
    new_index = _copy_labels(df.index)  # type: List[int]
    i = len(df.descs)""",
)
_pos_control = _swap(
    _pos_control,
    """        if m != 0:
            new_descs = [d] + new_descs""",
    """        if not (m == 0):   # reshaped keep-test: logically identical to m != 0
            new_descs = [d] + new_descs""",
)


# ===========================================================================
# 6. POSITIVE CONTROL — cheapest honest impl (verify). Inline the read of the
#    current descriptor at its only use (drop the `d` temporary) and carry the
#    mask flag the same way. Genuinely does the per-column compress; keeps the
#    backward loop + every invariant. Doubles as the GROUNDED-ORACLE positive
#    control: kept_descs is a function of the inputs, so the only way to satisfy
#    POST (1) is to do the real work — there is no wrong echo. MUST VERIFY.
# ===========================================================================
_cheapest = _swap(
    _BASE,
    """        d = df.descs[i - 1]
        m = mask[i - 1]""",
    """        m = mask[i - 1]""",
)
# the relate-asserts and the keep-branch referenced `d`; re-bind d inline so the
# proof terms are byte-identical to the gold proof (same value, no temp upfront).
_cheapest = _swap(
    _cheapest,
    """        Assert(ToSeq(df.descs).drop(i - 1)[0] == d)""",
    """        Assert(ToSeq(df.descs).drop(i - 1)[0] == df.descs[i - 1])""",
)
_cheapest = _swap(
    _cheapest,
    """        if m != 0:
            new_descs = [d] + new_descs""",
    """        if m != 0:
            new_descs = [df.descs[i - 1]] + new_descs""",
)


# ===========================================================================
# 7. ADMISSIBILITY (verify). Build a fresh, F2P-shaped in-domain input at the top
#    of the impl — a Frame over fresh length-3 index/descs plus a matching
#    length-3 mask — and ASSERT every Requires conjunct of select_columns for it,
#    including the half permissions (establishable because the probe lists are
#    FRESH, i.e. held at full perm) and the length agreement
#    len(descs) == len(mask). The original df permissions are untouched. If the
#    Requires were too strong for a normal input, some conjunct would fail to
#    establish. MUST VERIFY (else PRECOND-TOO-STRONG).
#
#    Assert-style rather than a recursive self-call: select_columns now carries
#    Requires(MustTerminate(3)) (total correctness), and Nagini demands a callee's
#    obligation level be STRICTLY below its caller's, so an equal-level self-call
#    is rejected by the obligation system ("Callee select_columns might not take
#    all unsatisfied obligations from the caller") — an artifact of the
#    termination spec, unrelated to the value preconditions this case probes. The
#    container constructor remains a REAL call site (level 1 < 3), so its own
#    Requires are still discharged for these arguments; the postcondition facts
#    the old self-call read back are already pinned by POST (1)/(2) on this shape.
# ===========================================================================
_admiss = _swap(
    _BASE,
    """    new_index = _copy_labels(df.index)  # type: List[int]
    new_descs = []  # type: List[int]
    i = len(df.descs)""",
    """    # admissibility witness: the precondition admits a normal F2P-shaped input
    # (one row label per row, one descriptor per column, mask length == #cols).
    _pidx = [10, 11, 12]  # type: List[int]
    _pdsc = [7, 8, 9]  # type: List[int]
    _pmask = [1, 0, 1]  # type: List[int]
    _probe = Frame(_pidx, _pdsc, ToSeq(_pidx), ToSeq(_pdsc))  # type: Frame
    # every Requires conjunct of select_columns, for that input
    Assert(Acc(_probe.index, 1 / 2) and Acc(_probe.descs, 1 / 2))
    Assert(Acc(list_pred(_probe.index), 1 / 2)
           and Acc(list_pred(_probe.descs), 1 / 2))
    Assert(Acc(list_pred(_pmask), 1 / 2))
    Assert(len(_probe.descs) == len(_pmask))
    # and it really is a non-degenerate F2P shape: three labelled rows, three
    # columns, and a mask that both keeps and drops.
    Assert(len(_probe.index) == 3 and len(_probe.descs) == 3)
    Assert(ToSeq(_pmask)[0] != 0 and ToSeq(_pmask)[1] == 0)
    new_index = _copy_labels(df.index)  # type: List[int]
    new_descs = []  # type: List[int]
    i = len(df.descs)""",
)


SPEC_TESTS = [
    {
        "id": "frame-mutation-write-descs",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_mutation,
        "refinement": (
            "Writing df.descs[i-1] = d mutates the read-only input container; the "
            "spec lends only Acc(list_pred(df.descs),1/2). A faithful real patch "
            "that mutated the caller's DataFrame columns in place (instead of "
            "_safe_indexing returning a fresh selection) would corrupt X for the "
            "caller; SelectorMixin._transform must NOT alter its input X. The F2P "
            "tests compare output.dtypes against the ORIGINAL X.dtypes (e.g. "
            "`assert dtype == X.dtypes[name]`); an in-place mutation of X would "
            "make those a no-op or corrupt X, so it would NOT resolve. A verifying "
            "rival here would be a verify-not-resolve break."
        ),
        "rationale": (
            "Rejection comes from the PERMISSION SYSTEM: the store df.descs[i-1]=d "
            "requires FULL list_pred(df.descs) permission, but only the read "
            "half-perm Acc(list_pred(df.descs),1/2) is held (Requires + the loop "
            "Invariant + the postcondition all pin it at 1/2). Insufficient "
            "permission, not a postcondition value mismatch."
        ),
    },
    {
        "id": "homogenise-shared-descriptor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _homogenise,
        "refinement": (
            "Stamping every retained column with column 0's descriptor is exactly "
            "the pre-patch `X[:, safe_mask(X, mask)]` NumPy coercion (homogenises "
            "all dtypes), which model_prepatch.py reproduces. On the F2P frames "
            "(float32 / category / float64 mixtures) the output dtypes would all "
            "collapse to one value, so `assert dtype == X.dtypes[name]` fails for "
            "every column whose dtype differs from column 0's — would NOT resolve."
        ),
        "rationale": (
            "Rejection from POST clause (1): ToSeq(Result().descs) == "
            "kept_descs(ToSeq(df.descs), ToSeq(mask)). kept_descs carries each "
            "kept column's OWN descriptor df.descs[i-1]; planting df.descs[0] for "
            "all kept columns differs whenever two retained descriptors differ. "
            "The exact-compress invariant was relaxed to a self-consistent framing "
            "perm so the rejection is attributable to the POST, not the invariant."
        ),
    },
    {
        "id": "mask-subdomain-force-keep-col0",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _mask_subdomain,
        "refinement": (
            "Force-keeping column 0 regardless of its mask flag retains a column "
            "the selector dropped. On a fixture where get_support() drops the "
            "first feature (e.g. StepSelector ranking keeps positions 2/3/4), the "
            "output would carry an extra leading column with the wrong dtype/name; "
            "the F2P `assert_array_equal(output.columns, [...])` and the per-name "
            "dtype check would fail — would NOT resolve."
        ),
        "rationale": (
            "Rejection from POST clause (1): kept_descs keeps a column iff its mask "
            "flag is set; the impl includes column 0 even when mask[0]==0, so "
            "ToSeq(Result().descs) has an extra leading element on that sub-domain. "
            "The compress invariant was relaxed so the rejection lands on the POST."
        ),
    },
    {
        "id": "positional-reindex-drop-labels",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _positional_index,
        "refinement": (
            "Returning a fresh (here empty) index drops the DataFrame's OWN row "
            "labels — exactly the pre-patch `np.empty(...).reshape((n,0))` / bare "
            "NumPy payload that re-labels rows positionally, which "
            "model_prepatch_2.py reproduces. The F2P empty-mask case asserts "
            "`assert_array_equal(output0.index, X.index)`; a dropped/positional "
            "index fails it — would NOT resolve."
        ),
        "rationale": (
            "Rejection from POST clause (2): ToSeq(Result().index) == "
            "ToSeq(df.index). new_index is empty, not the input's labels. The index "
            "invariant was relaxed to the empty witness so the rejection is "
            "attributable to the POST, not a broken invariant."
        ),
    },
    {
        "id": "pos-control-reorder-and-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_control,
        "rationale": (
            "Structurally different (descs accumulator initialised before the "
            "index copy; keep-test written `not (m == 0)`) but behaviourally "
            "identical. BACKWARD loop direction and the front-recursive kept_descs "
            "unfold are preserved, and all gold invariants/asserts are kept "
            "verbatim, so the gold proof discharges. MUST verify, else "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-cheapest-inline-descs",
        "kind": "soundness",
        "expect": "verify",
        "module": _cheapest,
        "rationale": (
            "Cheapest honest impl: drop the `d` temporary and read df.descs[i-1] "
            "inline at its uses; loop/invariants unchanged. Genuinely does the "
            "per-column compress. Doubles as the GROUNDED-ORACLE positive control "
            "— kept_descs is a fold over the inputs, so POST (1) can only be met by "
            "doing the real work (no wrong echo exists). MUST verify, else "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admissibility-f2p-shaped-frame",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss,
        "rationale": (
            "A fresh length-3 Frame + length-3 mask (F2P-shaped: one row label per "
            "row, one descriptor per column, len(descs)==len(mask)) with EVERY "
            "Requires conjunct asserted for it — the half-perms (established from "
            "full perm on the fresh lists), the length agreement, and the "
            "non-degenerate mask that both keeps and drops. MUST verify, else "
            "PRECOND-TOO-STRONG (the precondition would reject a normal input). "
            "Assert-style rather than a self-call: under Requires(MustTerminate(3)) "
            "an equal-level recursive self-call is rejected by the obligation "
            "system, an artifact unrelated to the value preconditions; the "
            "postcondition facts the self-call read back are already pinned by "
            "POST (1)/(2) on this shape."
        ),
    },
]


# ===========================================================================
# AXIOM lane — A-REFERENCE deep model (NO @ContractOnly axiom in this bundle).
# kept_descs (per-column compress) + _copy_labels (index carry-over) are
# validated == the real UNCHANGED callee sklearn.utils._safe_indexing(X, mask,
# axis=1) and the post-patch empty branch X.iloc[:, :0]. We re-run G-AX's
# real-callee soundness check in-container (the bundle's axiom_check.py is NOT
# mounted, so the probe is self-contained; encoding=utf-8 is irrelevant here as
# we build the frames programmatically with no file reads).
#
# Caller config: the deep model describes the DataFrame branch of _transform,
# reached only when `preserve_X = hasattr(X, "iloc") and output_config=="pandas"`
# (i.e. set_output(transform="pandas") on a DataFrame). Under that config the
# real selection is _safe_indexing(X, mask, axis=1) -> _pandas_indexing ->
# X.loc[:, mask], which keeps each column's own dtype + X's index; the empty
# branch is X.iloc[:, :0]. apply_gold=True so the post-patch _transform world.
# ===========================================================================

_AX_SOUND_PROBE = r'''
import random
import sys

import numpy as np
import pandas as pd

from sklearn.utils import _safe_indexing


# --- the deep model (kept_descs compress + index carry-over), plain Python ----
def kept_descs(dtypes, mask):
    return [d for d, m in zip(dtypes, mask) if m]


def model_select(df_index, df_dtypes, mask):
    return list(df_index), kept_descs(df_dtypes, mask)


# --- the REAL post-patch column selection (the branches the model covers) -----
def real_postpatch(X, mask):
    if not mask.any():
        if hasattr(X, "iloc"):
            return X.iloc[:, :0]
        return np.empty(0, dtype=X.dtype).reshape((X.shape[0], 0))
    return _safe_indexing(X, mask, axis=1)


# --- the PRE-patch (buggy) selection: numpy homogenises, empty branch raises ---
def real_prepatch(X, mask):
    if not mask.any():
        return np.empty(0, dtype=X.dtype).reshape((X.shape[0], 0))
    return X.values[:, mask]


def labels(seq):
    return [str(x) for x in list(seq)]


def make_df(index, col_dtypes):
    n = len(index)
    data = {}
    for j, dt in enumerate(col_dtypes):
        name = "c%d" % j
        if str(dt) == "category":
            data[name] = pd.Series(
                [("a" if (k % 2 == 0) else "b") for k in range(n)],
                index=list(index), dtype="category")
        else:
            data[name] = pd.Series(np.arange(n).astype(dt), index=list(index))
    return pd.DataFrame(data, index=list(index))


fail = []


def check_select_case(index, col_dtypes, mask):
    df = make_df(index, col_dtypes)
    df_dtypes = list(df.dtypes)
    real = real_postpatch(df, np.asarray(mask, dtype=bool))
    if not hasattr(real, "iloc"):
        fail.append("non-empty mask lost the dataframe nature: %r" % (type(real),))
        return
    m_idx, m_dtypes = model_select(list(index), df_dtypes, [bool(b) for b in mask])
    if labels(m_idx) != labels(real.index) or labels(real.index) != labels(index):
        fail.append("index disagreement (non-empty) idx=%r mask=%r model=%r real=%r"
                    % (index, mask, labels(m_idx), labels(real.index)))
    if [str(d) for d in m_dtypes] != [str(d) for d in real.dtypes]:
        fail.append("dtype disagreement (non-empty) cols=%r mask=%r model=%r real=%r"
                    % (col_dtypes, mask, m_dtypes, list(real.dtypes)))


def check_empty_case(index, col_dtypes):
    df = make_df(index, col_dtypes)
    mask = np.zeros(len(col_dtypes), dtype=bool)
    real = real_postpatch(df, mask)
    if not hasattr(real, "iloc"):
        fail.append("empty mask lost the dataframe nature: %r" % (type(real),))
        return
    m_idx, m_dtypes = model_select(list(index), list(df.dtypes), [False] * len(col_dtypes))
    if labels(m_idx) != labels(real.index) or labels(real.index) != labels(index):
        fail.append("index disagreement (empty) idx=%r model=%r real=%r"
                    % (index, labels(m_idx), labels(real.index)))
    if m_dtypes != [] or len(list(real.dtypes)) != 0:
        fail.append("empty mask must yield zero columns model=%r real=%r"
                    % (m_dtypes, list(real.dtypes)))
    if real.shape != (len(index), 0):
        fail.append("empty mask shape != (n,0): %r" % (real.shape,))


# (1) DEEP-MODEL FIDELITY over a boundary battery -----------------------------
dtype_palettes = [
    [np.float32, np.float64],
    [np.float32, "category", np.float64],
    [np.int32, np.int64, np.float32, "category"],
    ["category", "category"],
    [np.float64],
]
index_choices = [[0, 1, 2], [0, 1, 2, 3, 4], [10, 11, 12]]
for palette in dtype_palettes:
    ncols = len(palette)
    for index in index_choices:
        masks = [
            [True] * ncols,
            [k % 2 == 0 for k in range(ncols)],
            [k == ncols - 1 for k in range(ncols)],
            [k == 0 for k in range(ncols)],
        ]
        for mask in masks:
            if any(mask):
                check_select_case(index, palette, mask)
    check_empty_case([0, 1, 2], palette)

# (2) DISCRIMINATING DIVERGENCE: pre-patch homogenises; deep model keeps each ---
index = [0, 1, 2]
het = [np.float32, "category", np.float64]
df = make_df(index, het)
post = real_postpatch(df, np.array([True, True, True]))
post_dtypes = [str(d) for d in post.dtypes]
if post_dtypes != ["float32", "category", "float64"]:
    fail.append("post-patch must keep each column's own dtype; got %r" % (post_dtypes,))
pre = real_prepatch(df, np.array([True, True, True]))
if hasattr(pre, "dtypes"):
    fail.append("pre-patch numpy selection must NOT be a dataframe")
elif str(pre.dtype) == "category" or len(set(post_dtypes)) < 2:
    fail.append("pre-patch homogenises to one non-category dtype; het case needs >=2")
# pre-patch empty branch references the absent DataFrame.dtype
raised = False
try:
    real_prepatch(df, np.zeros(3, dtype=bool))
except AttributeError:
    raised = True
if not raised:
    fail.append("pre-patch empty branch must reference the absent DataFrame.dtype")

# (3) randomized fuzz ---------------------------------------------------------
rng = random.Random(25102)
base_dtypes = [np.float16, np.float32, np.float64, np.int32, np.int64, "category"]
for _ in range(1500):
    ncols = rng.randint(1, 6)
    palette = [rng.choice(base_dtypes) for _ in range(ncols)]
    nrows = rng.randint(2, 6)
    idx = list(range(nrows)) if rng.random() < 0.5 else [100 + k for k in range(nrows)]
    mask = [rng.random() < 0.5 for _ in range(ncols)]
    if any(mask):
        check_select_case(idx, palette, mask)
    else:
        check_empty_case(idx, palette)
    if fail:
        break

if fail:
    print("AXIOM-UNSOUND:", "; ".join(fail[:5]))
    sys.exit(1)
print("axiom-soundness OK: deep model (kept_descs compress + index carry-over) "
      "== real post-patch _safe_indexing(X, mask, axis=1) / X.iloc[:, :0] over "
      "the boundary battery + 1500 fuzz configs; each kept column keeps its OWN "
      "dtype and X's index is preserved (incl. empty mask). Pre-patch numpy "
      "selection homogenises all dtypes and its empty branch references the "
      "absent DataFrame.dtype -- diverging on EXACTLY the heterogeneous case.")
sys.exit(0)
'''


_AX_CONTAIN_PROBE = r'''
import sys

import numpy as np
import pandas as pd

from sklearn.utils import _safe_indexing


# AXIOM-CONTAINMENT for the A-reference deep model. Enumerate EXACTLY the
# callee-inputs the MODEL can reach and assert each lies in the real callee's
# domain. The model's Requires + control flow constrain the callee input to:
#   - X is a labelled container (a DataFrame: the preserve_X branch is reached
#     only when hasattr(X, "iloc"));
#   - mask is a boolean array with len(mask) == X.shape[1] (the precondition
#     len(df.descs) == len(mask), i.e. one flag per column);
#   - axis == 1 (column selection).
# The real callee _safe_indexing(X, mask, axis=1) on a DataFrame + boolean key
# dispatches to _pandas_indexing -> X.loc[:, mask]; its domain is "any boolean
# mask of length n_columns" plus the empty (all-False) mask routed to X.iloc[:, :0]
# in _transform. We assert every reachable (mask) shape -- including the
# boundary all-True / all-False / single-column cases -- is accepted by the real
# callee without error. Covering MORE (e.g. integer keys, axis=0) than the model
# reaches is SOUND, not a defect.
fail = []


def make_df(index, ncols):
    data = {}
    for j in range(ncols):
        data["c%d" % j] = pd.Series(np.arange(len(index)).astype(float),
                                    index=list(index))
    return pd.DataFrame(data, index=list(index))


# every boolean mask of length n_columns the model can pass:
for ncols in range(1, 6):
    df = make_df([0, 1, 2], ncols)
    # exhaustively enumerate all 2**ncols boolean masks (the whole reachable set)
    for bits in range(2 ** ncols):
        mask = np.array([(bits >> k) & 1 for k in range(ncols)], dtype=bool)
        try:
            if mask.any():
                out = _safe_indexing(df, mask, axis=1)   # the non-empty branch
                if not hasattr(out, "iloc"):
                    fail.append("reachable mask=%r gave a non-dataframe %r"
                                % (mask.tolist(), type(out)))
            else:
                out = df.iloc[:, :0]                     # the empty branch
                if out.shape != (3, 0):
                    fail.append("empty branch shape != (3,0): %r" % (out.shape,))
        except Exception as e:
            fail.append("reachable callee-input mask=%r raised %r"
                        % (mask.tolist(), e))
    if fail:
        break

# confirm the precondition len(mask)==n_columns is exactly what _safe_indexing
# (X.loc[:, mask]) requires: a mismatched-length boolean mask is OUT of domain
# for both the model (precondition) and the callee, so the model never reaches it.
df = make_df([0, 1, 2], 3)
mismatched = np.array([True, False], dtype=bool)   # len 2 != 3 columns
out_of_domain_for_callee = False
try:
    _safe_indexing(df, mismatched, axis=1)
except Exception:
    out_of_domain_for_callee = True
if not out_of_domain_for_callee:
    # not a hard failure (the callee being more lenient is sound), but the model
    # never passes a mismatched mask (len(df.descs)==len(mask) precondition), so
    # containment still holds. Record only as info; no append.
    pass

if fail:
    print("AXIOM-TOO-WEAK-FOR-CALLER:", "; ".join(fail[:5]))
    sys.exit(1)
print("axiom-containment OK: every boolean mask of length n_columns the model "
      "can reach (exhaustively, all 2**n masks for n=1..5, incl. all-True / "
      "all-False / single) is in the real _safe_indexing(X, mask, axis=1) domain "
      "(empty mask routed to X.iloc[:, :0]); the len(df.descs)==len(mask) "
      "precondition keeps the model inside that domain. Covering more (int keys, "
      "axis=0) than the caller reaches is SOUND.")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-deepmodel-vs-safe-indexing",
        "axiom": "kept_descs+_copy_labels (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "The deep model kept_descs (per-column descriptor compress) + index "
            "carry-over must equal the real unchanged callee _safe_indexing(X, "
            "mask, axis=1) (DataFrame + boolean mask -> X.loc[:, mask]) and the "
            "post-patch empty branch X.iloc[:, :0], over heterogeneous-dtype frames "
            "/ non-empty + empty masks / non-trivial indices. If the real callee "
            "disagreed (homogenised a dtype or dropped the index) -> AXIOM-UNSOUND. "
            "Also exhibits the pre-patch homogenisation / absent-.dtype divergence."
        ),
    },
    {
        "id": "ax-contain-mask-domain",
        "axiom": "kept_descs+_copy_labels (A-reference deep model)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": (
            "Every callee-input the model can reach -- a DataFrame X with a boolean "
            "mask of length n_columns (the precondition len(df.descs)==len(mask)), "
            "axis=1, plus the all-False mask routed to X.iloc[:, :0] -- lies in the "
            "real _safe_indexing domain (enumerated exhaustively for n=1..5). A "
            "reachable mask shape outside that domain would be "
            "AXIOM-TOO-WEAK-FOR-CALLER; none exists. Covering more than the caller "
            "reaches (integer keys, axis=0) is SOUND."
        ),
    },
]
