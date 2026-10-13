# properties.py — PBT manifest for astropy__astropy-13236.
#
# NOT a Nagini module. A record of adversarially-reasoned falsification cases the
# runner (swebench_nagini.pbt) executes against the FROZEN spec in model.py.
#
# Defended surface (read model.py + refinement.md + mapping.md):
#   select_column_kind(is_column, is_mixin, data0_is_mixin, elem_cls_builds,
#                       is_ndarray, is_structured, is_masked, has_dtype,
#                       seq_masked, is_none) -> int
# All inputs are primitive `bool` (passed BY VALUE); the output is an int kind
# code. There is NO mutable / read-only Acc(x,1/2) parameter, so the frame-
# mutation class is vacuous here (see 'assessment' — nothing to overwrite, no
# permission obligation in play). The whole patch is the DELETION of the
# structured-ndarray override; the load-bearing pin is
#   Ensures(Result() == selected_kind(...))             # master clause
# plus the two explicit discriminating clauses pinning that a structured,
# non-mixin, non-data0-mixin array is classified by mask-status ALONE
# (KIND_MASKED if masked else KIND_COLUMN) and is NOT diverted to KIND_MIXIN;
# the layout-independence clause pinning that the multi-field bit never changes
# the selected kind on ANY arm; the already-a-column clauses pinning that an
# input that is already a column object keeps its own column nature (KIND_MASKED
# if masked else KIND_COLUMN) and is never re-classified by a later rule; and
# the sequence-of-mixins clause pinning that the element mixin kind is selected
# only when a column of the element's class can actually be built from the whole
# sequence.
#
# The spec also obliges the selection to TERMINATE (Requires(MustTerminate(1))).
# Without it every value clause above is claimed only of runs that reach the
# return, so a rival that never decides a kind on the structured-array family
# satisfies them vacuously there and VERIFIES while its faithful patch hangs the
# F2P test. That is the 'weak-nonterminating-on-structured' reject case below;
# it was a measured hole, not a hypothetical one.
#
# `selected_kind` is a @Pure TOTAL function of the very input booleans (fully
# unfolded; no opaque oracle / answer-key). So an "ungrounded-oracle echo" is
# NOT a real attack: echoing selected_kind(...) literally IS doing the correct
# work — there is no WRONG echo to exhibit. We therefore replace the echo class
# with an honest cheapest-impl positive control (kind="soundness", expect
# verify) and document this in 'assessment'. No @ContractOnly axiom and no
# A-reference deep model exist (meta.axioms == []), so AXIOM_TESTS == [].

from pathlib import Path

INSTANCE = "astropy__astropy-13236"
FLOAT_ENCODING = None  # meta.json float_encoding is null (pure bool/int decision)

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact frozen impl region body (between # impl-start / # impl-end). Every
# variant is produced by _swap on THIS block only, so same_spec is guaranteed.
_GOLD_IMPL = """    if is_column:
        if is_masked:
            return KIND_MASKED()
        return KIND_COLUMN()
    data_is_mixin = is_mixin
    if data_is_mixin:
        return KIND_MIXIN()
    if data0_is_mixin and elem_cls_builds:
        return KIND_SEQ_MIXIN()
    if data0_is_mixin:
        return KIND_COLUMN()
    if is_masked:
        return KIND_MASKED()
    if (not is_none) and (not has_dtype) and seq_masked:
        return KIND_MASKED()
    return KIND_COLUMN()"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# Sanity: the gold impl block is present exactly once in the base model.
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block drifted from model.py"


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — structurally different but CORRECT.
# Reorders/reshapes the cascade WITHOUT changing the decision: computes the kind
# into a single local via a different control shape (value-selecting cascade in
# REVERSE precedence so the highest-priority guard overwrites last), then
# returns it. No loop, no @Pure fold, so there is no induction-lemma /
# forward-append hazard (avoid-bug #2/#3 are N/A). It still satisfies
# Result()==selected_kind because the overwrite order preserves first-match
# precedence: already-a-column (split by masked) > mixin > (data0_is_mixin,
# split by elem_cls_builds) > masked > dtype-less masked-sequence > column.
_POS_IMPL = """    # structurally-different correct impl: single result local, branches
    # rephrased as a value-selecting cascade (same first-match order as the
    # frozen selected_kind), returned once.
    kind = KIND_COLUMN()
    if (not is_none) and (not has_dtype) and seq_masked:
        kind = KIND_MASKED()
    if is_masked:
        kind = KIND_MASKED()
    if data0_is_mixin:
        if elem_cls_builds:
            kind = KIND_SEQ_MIXIN()
        else:
            kind = KIND_COLUMN()
    if is_mixin:
        kind = KIND_MIXIN()
    if is_column:
        if is_masked:
            kind = KIND_MASKED()
        else:
            kind = KIND_COLUMN()
    return kind"""

# ---------------------------------------------------------------------------
# ADMISSIBILITY — a self-call on an F2P-shaped input (unmasked structured
# ndarray: is_ndarray & is_structured, not column/mixin/data0/masked/none, with
# the Requires domain facts holding) must establish the precondition. Asserts
# the returned kind is the expected KIND_COLUMN for that input. If the call site
# cannot establish Requires for this normal input => PRECOND-TOO-STRONG.
#
# The call is made from a HELPER carrying a strictly higher termination measure
# than the specified selection, because the spec now obliges the selection to
# terminate: a caller may only invoke a callee whose measure is lower, so an
# in-body self-call at the same measure would be rejected for an obligation
# LEAK (a property of the call graph) rather than for the precondition, and the
# PRECOND-TOO-STRONG finding would not be attributable. Fault-injected control:
# adding a domain-narrowing `Requires(not is_structured)` makes this case fail
# with "The precondition of method select_column_kind might not hold", so the
# detector is live rather than a rubber stamp.
_ADMISS_IMPL = """    if is_column:
        if is_masked:
            return KIND_MASKED()
        return KIND_COLUMN()
    data_is_mixin = is_mixin
    if data_is_mixin:
        return KIND_MIXIN()
    if data0_is_mixin and elem_cls_builds:
        return KIND_SEQ_MIXIN()
    if data0_is_mixin:
        return KIND_COLUMN()
    if is_masked:
        return KIND_MASKED()
    if (not is_none) and (not has_dtype) and seq_masked:
        return KIND_MASKED()
    return KIND_COLUMN()


def _admissibility_probe() -> int:
    # Admissibility witness, called from a strictly higher termination
    # measure: the precondition must accept a normal F2P-shaped input (an
    # unmasked structured ndarray: not column/mixin/data0_mixin/masked/none;
    # ndarray => has_dtype; a dtyped input never takes the sequence-conversion
    # path so seq_masked is False; elem_cls_builds is False since the
    # sequence-of-mixins case does not apply). If the call site cannot
    # establish the precondition for this ordinary input => PRECOND-TOO-STRONG.
    Requires(MustTerminate(2))
    Ensures(Result() == KIND_COLUMN())
    witness = select_column_kind(False, False, False, False, True, True, False,
                                 True, False, False)
    Assert(witness == KIND_COLUMN())
    return witness"""

# ---------------------------------------------------------------------------
# ADMISSIBILITY #2 — a self-call on a sequence-of-mixins input whose element
# class DOES build (data0_is_mixin & elem_cls_builds, e.g. a list of two Time
# objects). This is the second live shape of the sequence arm, and the one the
# repaired precondition's sixth conjunct
# (elem_cls_builds => data0_is_mixin and not is_column) must still admit. If
# that conjunct were mis-stated so this ordinary input fell out of the domain,
# the case fails with "The precondition ... might not hold" =>
# PRECOND-TOO-STRONG.
_ADMISS2_IMPL = """    if is_column:
        if is_masked:
            return KIND_MASKED()
        return KIND_COLUMN()
    data_is_mixin = is_mixin
    if data_is_mixin:
        return KIND_MIXIN()
    if data0_is_mixin and elem_cls_builds:
        return KIND_SEQ_MIXIN()
    if data0_is_mixin:
        return KIND_COLUMN()
    if is_masked:
        return KIND_MASKED()
    if (not is_none) and (not has_dtype) and seq_masked:
        return KIND_MASKED()
    return KIND_COLUMN()


def _admissibility_probe_seq() -> int:
    # Admissibility witness for the sequence-of-mixins shape whose element
    # class builds: a dtype-less list whose first element is a mixin, not a
    # column, not itself a mixin, not masked, not None, and the element-class
    # construction succeeds. All nine Requires conjuncts hold, so the call site
    # must be able to establish the precondition, and the spec then pins the
    # element mixin kind.
    Requires(MustTerminate(2))
    Ensures(Result() == KIND_SEQ_MIXIN())
    witness = select_column_kind(False, False, True, True, False, False, False,
                                 False, False, False)
    Assert(witness == KIND_SEQ_MIXIN())
    return witness"""

# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN #1 — the PRE-PATCH rival (the canonical attack).
# Re-introduces the deleted structured-ndarray override: a non-column,
# non-mixin, ndarray, structured input is forced into KIND_MIXIN. This is
# exactly model_prepatch.py's defect. It is correct on the entire non-structured
# domain but diverges on the structured-array sub-domain. expect=reject: the
# master clause Result()==selected_kind (which never consults is_structured)
# forces KIND_MASKED/KIND_COLUMN there, and the two explicit discriminating
# clauses pin it.
_REJ_PREPATCH_IMPL = """    # PRE-PATCH rival: re-adds the deleted structured-ndarray override that
    # diverts a non-column non-mixin structured ndarray into KIND_MIXIN.
    data_is_mixin = is_mixin
    if (not is_column) and (not data_is_mixin) and is_ndarray and is_structured:
        data_is_mixin = True
    if is_column:
        if is_masked:
            return KIND_MASKED()
        return KIND_COLUMN()
    if data_is_mixin:
        return KIND_MIXIN()
    if data0_is_mixin and elem_cls_builds:
        return KIND_SEQ_MIXIN()
    if data0_is_mixin:
        return KIND_COLUMN()
    if is_masked:
        return KIND_MASKED()
    if (not is_none) and (not has_dtype) and seq_masked:
        return KIND_MASKED()
    return KIND_COLUMN()"""

# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN #2 — masked-structured-only override. A subtler
# rival: it diverts ONLY the masked structured sub-case to KIND_MIXIN, leaving
# the unmasked structured case correct (so it passes test_ndarray_mixin[False]
# but fails test_structured_masked_column). expect=reject via the
# is_masked discriminating clause (KIND_MASKED).
_REJ_MASKED_STRUCT_IMPL = """    # rival diverging ONLY on masked structured arrays -> KIND_MIXIN.
    data_is_mixin = is_mixin
    if (not is_column) and (not data_is_mixin) and is_ndarray \
            and is_structured and is_masked:
        data_is_mixin = True
    if is_column:
        if is_masked:
            return KIND_MASKED()
        return KIND_COLUMN()
    if data_is_mixin:
        return KIND_MIXIN()
    if data0_is_mixin and elem_cls_builds:
        return KIND_SEQ_MIXIN()
    if data0_is_mixin:
        return KIND_COLUMN()
    if is_masked:
        return KIND_MASKED()
    if (not is_none) and (not has_dtype) and seq_masked:
        return KIND_MASKED()
    return KIND_COLUMN()"""

# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN #3 — unmasked-structured-only override. The
# complementary half: diverts ONLY the UNMASKED structured sub-case to
# KIND_MIXIN (passes test_structured_masked_column, fails
# test_ndarray_mixin[False]). expect=reject via the not-is_masked
# discriminating clause (KIND_COLUMN).
_REJ_UNMASKED_STRUCT_IMPL = """    # rival diverging ONLY on UNMASKED structured arrays -> KIND_MIXIN.
    data_is_mixin = is_mixin
    if (not is_column) and (not data_is_mixin) and is_ndarray \
            and is_structured and (not is_masked):
        data_is_mixin = True
    if is_column:
        if is_masked:
            return KIND_MASKED()
        return KIND_COLUMN()
    if data_is_mixin:
        return KIND_MIXIN()
    if data0_is_mixin and elem_cls_builds:
        return KIND_SEQ_MIXIN()
    if data0_is_mixin:
        return KIND_COLUMN()
    if is_masked:
        return KIND_MASKED()
    if (not is_none) and (not has_dtype) and seq_masked:
        return KIND_MASKED()
    return KIND_COLUMN()"""

# ---------------------------------------------------------------------------
# UNIQUENESS / first-match-ORDER flip — a value-level structural attack. Checks
# the masked branch BEFORE the data0_is_mixin sequence-mixin branch. This
# diverges on the sub-domain {not column, data0_is_mixin, is_masked}: the gold
# cascade selects KIND_SEQ_MIXIN (data0 wins, it precedes masked) but this rival
# returns KIND_MASKED. expect=reject via the master clause Result()==
# selected_kind, whose first-match order puts data0_is_mixin before is_masked.
_REJ_ORDER_IMPL = """    # rival with the masked / data0-mixin guards in the WRONG order.
    if is_column:
        if is_masked:
            return KIND_MASKED()
        return KIND_COLUMN()
    data_is_mixin = is_mixin
    if data_is_mixin:
        return KIND_MIXIN()
    if is_masked:
        return KIND_MASKED()
    if data0_is_mixin and elem_cls_builds:
        return KIND_SEQ_MIXIN()
    if data0_is_mixin:
        return KIND_COLUMN()
    if (not is_none) and (not has_dtype) and seq_masked:
        return KIND_MASKED()
    return KIND_COLUMN()"""

# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN #4 — dropped masked-sequence clause. A rival that
# omits the dtype-less masked-sequence branch entirely: a non-None input
# without a dtype whose sequence conversion carries masked entries falls
# through to KIND_COLUMN instead of KIND_MASKED. It agrees with the gold
# cascade everywhere else (all structured-array cases included). expect=reject
# via the master clause: selected_kind returns KIND_MASKED on
# {not mixin, not data0, not masked, not none, not has_dtype, seq_masked}.
_REJ_NO_SEQ_MASKED_IMPL = """    # rival dropping the dtype-less masked-sequence branch -> KIND_COLUMN.
    if is_column:
        if is_masked:
            return KIND_MASKED()
        return KIND_COLUMN()
    data_is_mixin = is_mixin
    if data_is_mixin:
        return KIND_MIXIN()
    if data0_is_mixin and elem_cls_builds:
        return KIND_SEQ_MIXIN()
    if data0_is_mixin:
        return KIND_COLUMN()
    if is_masked:
        return KIND_MASKED()
    return KIND_COLUMN()"""

# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN #5 — UNCONDITIONAL sequence-of-mixins arm. A
# rival that selects the element mixin kind for EVERY non-column input whose
# first element is a mixin, ignoring whether a column of that element's class
# can actually be built from the whole sequence. It agrees with the desired
# cascade everywhere else (every structured-array case included), so it is a
# genuine partial-domain rival on exactly the sub-domain
# {not column, not mixin, data0_is_mixin, not elem_cls_builds}. expect=reject
# via the master clause and the explicit sequence-of-mixins clause, both of
# which demand KIND_COLUMN there.
_REJ_UNCOND_SEQ_MIXIN_IMPL = """    # rival taking the element mixin kind for EVERY sequence whose first
    # element is a mixin, whether or not that construction can succeed.
    if is_column:
        if is_masked:
            return KIND_MASKED()
        return KIND_COLUMN()
    data_is_mixin = is_mixin
    if data_is_mixin:
        return KIND_MIXIN()
    if data0_is_mixin:
        return KIND_SEQ_MIXIN()
    if is_masked:
        return KIND_MASKED()
    if (not is_none) and (not has_dtype) and seq_masked:
        return KIND_MASKED()
    return KIND_COLUMN()"""


# ---------------------------------------------------------------------------
# UNIQUENESS / VACUOUS-BY-NONTERMINATION — a rival that never decides a kind
# for the structured-array family at all: on exactly the inputs the change is
# about (an unmasked structured array that is neither an existing column nor a
# mixin) it runs on forever instead of returning. Every value postcondition is
# then claimed only of runs that reach the return, so on that family it holds
# vacuously and the rival satisfies the value clauses without ever selecting a
# column kind. It agrees with the desired cascade on every other input.
# expect=reject via the termination obligation the precondition states.
_REJ_NONTERMINATING_IMPL = """    # rival that never decides a kind on the structured-array family.
    if is_structured and is_ndarray and (not is_column) and (not is_mixin) \
            and (not data0_is_mixin) and (not is_masked):
        while True:
            pass
    if is_column:
        if is_masked:
            return KIND_MASKED()
        return KIND_COLUMN()
    data_is_mixin = is_mixin
    if data_is_mixin:
        return KIND_MIXIN()
    if data0_is_mixin and elem_cls_builds:
        return KIND_SEQ_MIXIN()
    if data0_is_mixin:
        return KIND_COLUMN()
    if is_masked:
        return KIND_MASKED()
    if (not is_none) and (not has_dtype) and seq_masked:
        return KIND_MASKED()
    return KIND_COLUMN()"""


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN #6 — flattened already-a-column arm. The rival
# decides an input that is already a column object as the ordinary column kind
# UNCONDITIONALLY, dropping the masked distinction inside that arm. It is
# correct on every non-column input and on every UNMASKED column, and wrong on
# exactly {is_column, is_masked}: an already-masked column object would be
# re-made as a plain, non-masked column, silently dropping its mask.
# expect=reject via the master clause and the explicit already-a-column clause
# (is_column & is_masked => KIND_MASKED).
_REJ_COL_ARM_FLAT_IMPL = """    # rival deciding EVERY already-a-column input as the plain column kind,
    # ignoring whether that column carries a mask.
    if is_column:
        return KIND_COLUMN()
    data_is_mixin = is_mixin
    if data_is_mixin:
        return KIND_MIXIN()
    if data0_is_mixin and elem_cls_builds:
        return KIND_SEQ_MIXIN()
    if data0_is_mixin:
        return KIND_COLUMN()
    if is_masked:
        return KIND_MASKED()
    if (not is_none) and (not has_dtype) and seq_masked:
        return KIND_MASKED()
    return KIND_COLUMN()"""

# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN #7 — structured-independence violated INSIDE the
# already-a-column arm. The rival agrees with the desired cascade on every
# input whose layout is not multi-field, but diverts an already-a-column input
# that DOES carry a structured layout into the mixin kind. This is the
# structured-array divergence relocated into the one arm the two original
# discriminating clauses did not reach, so it is the sharpest test that the
# structured bit is pinned as irrelevant EVERYWHERE and not only on the
# non-column half. expect=reject via the master clause, the explicit
# already-a-column clauses and the layout-independence clause.
_REJ_COL_ARM_STRUCT_IMPL = """    # rival diverting an already-a-column input into the mixin kind when that
    # column carries a multi-field layout.
    if is_column:
        if is_structured:
            return KIND_MIXIN()
        if is_masked:
            return KIND_MASKED()
        return KIND_COLUMN()
    data_is_mixin = is_mixin
    if data_is_mixin:
        return KIND_MIXIN()
    if data0_is_mixin and elem_cls_builds:
        return KIND_SEQ_MIXIN()
    if data0_is_mixin:
        return KIND_COLUMN()
    if is_masked:
        return KIND_MASKED()
    if (not is_none) and (not has_dtype) and seq_masked:
        return KIND_MASKED()
    return KIND_COLUMN()"""

# ---------------------------------------------------------------------------
# ADMISSIBILITY #3 — a self-call on an already-a-column input that carries a
# mask (the shape the repaired leading arm decides). The three added domain
# facts (is_column => not is_mixin / has_dtype / not is_none) must still admit
# it, and the spec must pin the masked column kind for it. If the call site
# cannot establish the precondition => PRECOND-TOO-STRONG.
_ADMISS3_IMPL = """    if is_column:
        if is_masked:
            return KIND_MASKED()
        return KIND_COLUMN()
    data_is_mixin = is_mixin
    if data_is_mixin:
        return KIND_MIXIN()
    if data0_is_mixin and elem_cls_builds:
        return KIND_SEQ_MIXIN()
    if data0_is_mixin:
        return KIND_COLUMN()
    if is_masked:
        return KIND_MASKED()
    if (not is_none) and (not has_dtype) and seq_masked:
        return KIND_MASKED()
    return KIND_COLUMN()


def _admissibility_probe_masked_column() -> int:
    # Admissibility witness for an input that is ALREADY a masked column
    # object: is_column, is_masked, an ndarray with a dtype, not a mixin, not
    # None, no sequence conversion, no element-class probe. Every Requires
    # conjunct holds, so this ordinary input must stay in the domain and the
    # spec must pin the masked column kind for it.
    Requires(MustTerminate(2))
    Ensures(Result() == KIND_MASKED())
    witness = select_column_kind(True, False, False, False, True, False, True,
                                 True, False, False)
    Assert(witness == KIND_MASKED())
    return witness"""


SPEC_TESTS = [
    {
        "id": "pos-control-reshaped-cascade",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_IMPL),
        "rationale": (
            "A structurally-different but CORRECT impl (single result local, "
            "branches written as a value-selecting cascade in REVERSE precedence "
            "so the highest-priority guard overwrites last — same first-match "
            "semantics as selected_kind: mixin > not-column&data0 (split by "
            "elem_cls_builds) > masked > dtype-less masked-sequence > column). "
            "No loop / no @Pure fold, so no induction lemma is needed. It must "
            "verify; if it cannot satisfy Result()==selected_kind the spec is "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-f2p-unmasked-structured",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS_IMPL),
        "rationale": (
            "Self-call on an F2P-shaped input (unmasked structured ndarray: "
            "is_ndarray & is_structured, not column/mixin/data0/masked/none, "
            "has_dtype, seq_masked False, elem_cls_builds False). All nine "
            "Requires domain facts hold, so the precondition must be "
            "establishable; the asserted result KIND_COLUMN follows from the "
            "spec. If the call site cannot establish Requires => "
            "PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-seq-of-mixin-builds",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS2_IMPL),
        "rationale": (
            "Self-call on the other live shape of the sequence arm: a "
            "dtype-less list whose first element is a mixin and whose "
            "element-class construction SUCCEEDS (data0_is_mixin & "
            "elem_cls_builds, not column/mixin/masked/none). The "
            "Requires conjunct (elem_cls_builds => data0_is_mixin and not "
            "is_column) is satisfied, so this ordinary input must stay in the "
            "domain and the spec must pin KIND_SEQ_MIXIN for it. If the call "
            "site cannot establish Requires => PRECOND-TOO-STRONG (the domain "
            "fact would have narrowed away a real input class)."
        ),
    },
    {
        "id": "weak-prepatch-structured-override",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_PREPATCH_IMPL),
        "refinement": (
            "This is the PRE-PATCH behaviour (re-adds the deleted "
            "structured-ndarray override `data = data.view(NdarrayMixin); "
            "data_is_mixin = True`). Its faithful real patch is the UNPATCHED "
            "_convert_data_to_col, which is precisely what FAILS "
            "test_ndarray_mixin[False] (structured ndarray must become a plain "
            "Column, not NdarrayMixin) and test_structured_masked_column (masked "
            "structured ndarray must become a MaskedColumn) — i.e. it does NOT "
            "resolve. A verifying rival here would be a true verify-not-resolve "
            "break."
        ),
        "rationale": (
            "Rejected by the master clause Result()==selected_kind (selected_kind "
            "never consults is_structured, so it demands KIND_MASKED/KIND_COLUMN "
            "for a non-col non-mixin structured array) AND by both explicit "
            "discriminating postconditions (is_structured&...&is_masked => "
            "KIND_MASKED; ...&not is_masked => KIND_COLUMN). This rival returns "
            "KIND_MIXIN there."
        ),
    },
    {
        "id": "weak-masked-structured-only-override",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_MASKED_STRUCT_IMPL),
        "refinement": (
            "Diverts ONLY masked structured arrays to KIND_MIXIN. Its faithful "
            "real patch keeps the override but guarded by `and is_masked`: a "
            "masked structured ndarray would still become an NdarrayMixin view, "
            "failing test_structured_masked_column (which requires a MaskedColumn "
            "with the per-field mask preserved). It would NOT resolve. (It would "
            "pass test_ndarray_mixin[False], so this is a genuine partial-domain "
            "rival, correct on the unmasked half.)"
        ),
        "rationale": (
            "Rejected by the discriminating clause Implies(is_structured & "
            "is_ndarray & not is_column & not is_mixin & not data0_is_mixin & "
            "is_masked, Result()==KIND_MASKED()); this rival returns KIND_MIXIN."
        ),
    },
    {
        "id": "weak-unmasked-structured-only-override",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_UNMASKED_STRUCT_IMPL),
        "refinement": (
            "Complementary half: diverts ONLY UNMASKED structured arrays to "
            "KIND_MIXIN. Its faithful real patch keeps the override guarded by "
            "`and not is_masked`: an unmasked structured ndarray would still "
            "become an NdarrayMixin, failing test_ndarray_mixin[False] (which "
            "requires a plain Column). It would NOT resolve. (It would pass "
            "test_structured_masked_column — partial-domain, correct on the "
            "masked half.)"
        ),
        "rationale": (
            "Rejected by the discriminating clause Implies(is_structured & "
            "is_ndarray & not is_column & not is_mixin & not data0_is_mixin & "
            "not is_masked, Result()==KIND_COLUMN()); this rival returns "
            "KIND_MIXIN."
        ),
    },
    {
        "id": "weak-branch-order-flip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_ORDER_IMPL),
        "refinement": (
            "Swaps the first-match order so masked is tested before the "
            "data0_is_mixin sequence-mixin branch. Its faithful real patch "
            "reorders the if/elif so the masked branch precedes the "
            "`elif data0_is_mixin:` branch in _convert_data_to_col. A masked "
            "sequence whose elements are mixins (not a Column, data0 a mixin, "
            "masked) would then be built as a MaskedColumn instead of "
            "`data[0].__class__(data)` — diverging from the desired cascade and "
            "from the PASS_TO_PASS mixin/quantity column tests that rely on the "
            "data0_is_mixin branch winning. It would NOT resolve those P2P tests."
        ),
        "rationale": (
            "Rejected by the master clause Result()==selected_kind: selected_kind "
            "evaluates `(not is_column) and data0_is_mixin` BEFORE is_masked, so "
            "on {not column, data0_is_mixin, elem_cls_builds, masked} the spec "
            "demands KIND_SEQ_MIXIN whereas this rival returns KIND_MASKED."
        ),
    },
    {
        "id": "weak-dropped-masked-sequence-branch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_NO_SEQ_MASKED_IMPL),
        "refinement": (
            "Omits the dtype-less masked-sequence branch entirely: a plain "
            "sequence containing masked entries (no dtype attribute, sequence "
            "conversion yields a masked array) would be stored as an ordinary "
            "Column instead of a MaskedColumn. Its faithful real patch would "
            "alter the UNCHANGED sequence-conversion branch of "
            "_convert_data_to_col to always pick the plain column class — "
            "diverging from the real repo's behaviour on such inputs and from "
            "the PASS_TO_PASS masking tests that rely on it. It would NOT "
            "resolve those P2P tests."
        ),
        "rationale": (
            "Rejected by the master clause Result()==selected_kind: on "
            "{not mixin, not data0, not masked, not none, not has_dtype, "
            "seq_masked} the spec demands KIND_MASKED whereas this rival "
            "returns KIND_COLUMN."
        ),
    },
    {
        "id": "weak-unconditional-seq-mixin-arm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_UNCOND_SEQ_MIXIN_IMPL),
        "refinement": (
            "Takes the element mixin kind for EVERY non-column input whose "
            "first element is a mixin, ignoring whether a column of that "
            "element's class can be built from the whole sequence. Its "
            "faithful real patch drops the sequence arm's try/except in "
            "_convert_data_to_col so `data[0].__class__(data)` propagates "
            "instead of falling back to an object-dtype column. A "
            "heterogeneous sequence of mixins (e.g. one whose elements have "
            "incompatible element classes) would then raise instead of being "
            "stored as an ordinary object column, diverging from the real "
            "repo's behaviour on such inputs and from the PASS_TO_PASS tests "
            "that rely on the fallback. It would NOT resolve those P2P tests."
        ),
        "rationale": (
            "Rejected by the master clause Result()==selected_kind and by the "
            "explicit sequence-of-mixins clause Implies(not is_mixin & not "
            "is_column & data0_is_mixin & not elem_cls_builds, "
            "Result()==KIND_COLUMN()): on that sub-domain the spec demands "
            "KIND_COLUMN whereas this rival returns KIND_SEQ_MIXIN. It is "
            "correct on every other input, which makes it a genuine "
            "partial-domain rival."
        ),
    },
    {
        "id": "admiss-already-a-masked-column",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS3_IMPL),
        "rationale": (
            "Self-call on an input that is ALREADY a masked column object "
            "(is_column & is_masked, an ndarray with a dtype, not a mixin, not "
            "None). The three added domain facts (is_column => not is_mixin / "
            "has_dtype / not is_none) hold of it, so the precondition must be "
            "establishable, and the spec pins KIND_MASKED. If the call site "
            "cannot establish Requires => PRECOND-TOO-STRONG (the added domain "
            "facts would have narrowed away a real input class)."
        ),
    },
    {
        "id": "weak-flattened-already-a-column-arm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_COL_ARM_FLAT_IMPL),
        "refinement": (
            "Decides EVERY already-a-column input as the plain column kind, "
            "dropping the masked distinction inside that arm. Its faithful "
            "real patch would make the already-a-column branch of "
            "_convert_data_to_col ask for the plain column class instead of "
            "preserving the object's own class, so adding an existing "
            "MaskedColumn to a table would silently strip its mask — "
            "diverging from the real repo on a large PASS_TO_PASS surface "
            "(every test that round-trips a MaskedColumn through a table). It "
            "is correct on every non-column input and on every unmasked "
            "column, which makes it a genuine partial-domain rival rather "
            "than a broken program, and it would NOT resolve those P2P tests."
        ),
        "rationale": (
            "Rejected by the master clause Result()==selected_kind, whose "
            "leading guard pair decides an already-a-column input by its own "
            "mask status, AND by the explicit clause Implies(is_column and "
            "is_masked, Result()==KIND_MASKED()); this rival returns "
            "KIND_COLUMN there. This is the case that keeps the repaired "
            "leading arm from being a free relaxation: the arm pins a VALUE, "
            "it does not merely exempt the column family from the cascade."
        ),
    },
    {
        "id": "weak-structured-column-to-mixin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_COL_ARM_STRUCT_IMPL),
        "refinement": (
            "Relocates the structured-array divergence into the "
            "already-a-column arm: an existing column object that carries a "
            "multi-field layout is diverted into the mixin kind, while every "
            "input without such a layout is decided exactly as desired. Its "
            "faithful real patch keeps a structured-layout override but "
            "guards it on the input already being a column, so wrapping a "
            "structured array in a column before adding it would still "
            "produce a mixin instead of a column — the very behaviour the "
            "desired selection rules out, and a divergence from the real repo "
            "on the structured-column P2P surface. It would NOT resolve."
        ),
        "rationale": (
            "Rejected by the master clause, by the explicit already-a-column "
            "clauses (is_column & not is_masked => KIND_COLUMN) and by the "
            "layout-independence clause Result()==selected_kind(..., "
            "is_structured:=False, ...); this rival returns KIND_MIXIN there. "
            "It is the sharpest check that the multi-field layout bit is "
            "pinned as irrelevant on EVERY arm, not only on the non-column "
            "half the two original discriminating clauses reached."
        ),
    },
    {
        "id": "weak-nonterminating-on-structured",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_NONTERMINATING_IMPL),
        "refinement": (
            "Never decides a kind for the input family the change is about: on "
            "an unmasked structured array that is neither an existing column "
            "nor a mixin it runs on forever instead of returning. Its faithful "
            "real patch makes _convert_data_to_col loop without terminating on "
            "exactly that input, so `Table([structured_array], names=['a'])` "
            "hangs and test_ndarray_mixin[False] never completes — the F2P test "
            "does not pass, so it does NOT resolve. It is correct on every "
            "other input, which is what makes it a genuine partial-domain "
            "rival rather than a broken program."
        ),
        "rationale": (
            "Rejected by the termination obligation the precondition states: "
            "the selection must be reached in a bounded number of steps for "
            "every admissible input. Without that obligation the value clauses "
            "(Result()==selected_kind and the discriminating structured-array "
            "clauses) are claimed only of runs that reach the return, so this "
            "rival satisfies them VACUOUSLY on the structured family and "
            "verifies — a measured verify-not-resolve hole. Verifier output "
            "with the obligation present: 'Obligation leak check failed. Loop "
            "might not take all unsatisfied obligations from the context.'"
        ),
    },
]

# No @ContractOnly axioms and no A-reference deep models (meta.json axioms == []
# and deep_model_references == []); the modeled delta is a pure boolean decision
# procedure with no opaque callee consumed inside any Ensures. axiom_check.py is
# a decision-EQUIVALENCE check (real callee vs selected_kind), not an axiom
# soundness/containment obligation, so there is nothing for the axiom lane.
AXIOM_TESTS = []
