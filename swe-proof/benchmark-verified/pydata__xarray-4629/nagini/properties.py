# properties.py — PBT falsification battery for pydata__xarray-4629.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions regions untouched) and swaps ONLY text inside
# the # impl-start/# impl-end region (the loop invariants live inside that region
# and are elided by spec_view, so editing them keeps same_spec). The runner
# checks each with Nagini verify + markers.same_spec.
#
# Defended surface (read from model.py + refinement.md + mapping.md + instance):
#   combine_attrs(variable_attrs: List[List[int]], mode: int) -> List[int]
#   combines per-source attribute mappings into one for a combined object.
#     DROP     -> a fresh EMPTY mapping.
#     OVERRIDE -> a faithful, INDEPENDENT copy of the leading source mapping
#                 variable_attrs[0]: same content, DISTINCT object.
#   The decisive observable is OBJECT IDENTITY (fresh copy vs shared reference),
#   carried by Nagini reference identity + the fractional-permission discipline.
#
#   BOTH inputs are READ-ONLY (half permission), so frame-mutation is the #1
#   attack and is MANDATORY here (two flavours below):
#     Requires(Acc(list_pred(variable_attrs), 1/2))      # the outer collection
#     Requires(Acc(list_pred(variable_attrs[0]), 1/2))   # the leading source map
#
#   Load-bearing postcondition clauses (where rejections come from):
#     P1  Acc(list_pred(Result()))                       FULL perm on the result
#     P2  Implies(mode==OVERRIDE, Result() is not variable_attrs[0])  distinct obj
#     P3  Implies(mode==OVERRIDE, ToSeq(Result())==ToSeq(variable_attrs[0]))  copy
#     P4  Implies(mode==DROP, len(Result())==0)          drop -> empty
#     F   Acc(list_pred(variable_attrs),1/2) & Acc(list_pred(variable_attrs[0]),1/2)
#         returned to caller -> the read-only inputs are framed unchanged.
#   P1 is the heart: full perm on Result() while the source keeps 1/2 makes
#   aliasing impossible (1 + 1/2 > 1) — a result that IS variable_attrs[0]
#   cannot verify. There is NO @Pure oracle / answer-key to echo: the OVERRIDE
#   target ToSeq(variable_attrs[0]) is the input itself (grounded) — see
#   'assessment' re ungrounded-oracle-echo (N/A; replaced by an honest positive
#   control).
#
# F2P: test_merge_attrs_override_copy — merges with combine_attrs='override',
#      mutates ds3.attrs['x']=2, asserts ds1.x==0 (the source is untouched).
# meta.json axioms == [] and there are no @ContractOnly imports -> AXIOM_TESTS=[]
# (the lone deep-model reference dict(variable_attrs[0]) is validated out-of-band
# by axiom_check.py / G-AX, which is the host-run A-reference check, not a
# per-input Docker probe).

from pathlib import Path

INSTANCE = "pydata__xarray-4629"
FLOAT_ENCODING = None  # meta.json float_encoding == null


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen impl region (between # impl-start / # impl-end). Every rival edits
# ONLY text in this block; the loop invariants are part of it and are elided by
# spec_view, so changing them never breaks same_spec.
# ---------------------------------------------------------------------------
_IMPL = """    if mode == DROP:
        empty = []  # type: List[int]
        return empty
    src = variable_attrs[0]  # type: List[int]
    result = []  # type: List[int]
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(result is not src)
        Invariant(0 <= i and i <= len(src))
        Invariant(len(result) == i)
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        Invariant(MustTerminate(len(src) - i + 1))
        # invariants-end
        result.append(src[i])
        i = i + 1
    return result"""


# === POSITIVE CONTROL (soundness) =========================================
# Branch-reorder + local-variable reshape: handle the OVERRIDE path first and
# fall through to the DROP return last, and hoist the loop bound into a local
# `n`. Same executable meaning, EVERY gold invariant kept verbatim (the forward-
# append matches the front/prefix fold ToSeq(src).take(i), so no f(a+b) lemma is
# needed — directive-3 safe; we keep the SAME loop direction). If a faithful
# structurally-different correct impl cannot verify -> SPEC-TOO-STRONG.
_POS_IMPL = """    if mode == OVERRIDE:
        src = variable_attrs[0]  # type: List[int]
        result = []  # type: List[int]
        n = len(src)  # type: int
        i = 0
        while i < n:
            # invariants-start
            Invariant(Acc(list_pred(src), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(result is not src)
            Invariant(n == len(src))
            Invariant(0 <= i and i <= len(src))
            Invariant(len(result) == i)
            Invariant(ToSeq(result) == ToSeq(src).take(i))
            Invariant(MustTerminate(n - i + 1))
            # invariants-end
            result.append(src[i])
            i = i + 1
        return result
    empty = []  # type: List[int]
    return empty"""

POS_REORDER = _swap(_BASE, _IMPL, _POS_IMPL)


# === ADMISSIBILITY ========================================================
# A separate top-level caller would break same_spec (spec_view only elides the
# impl region — anything at module level enters the spec signature). So the
# admissibility check lives INSIDE the impl region, inserted right after
# # impl-start, BEFORE any gold obligation (so all following obligations are kept
# verbatim). A self-recursive call would need a Decreases the spec lacks (a proof
# gap, not a spec defect), so we instead exercise the Requires PREDICATES on the
# concrete F2P-shaped input the caller already holds: len(variable_attrs)>0, the
# half-permission predicates on both the collection and the leading source, and
# the F2P content shape (a 1-entry leading mapping ToSeq(...)[0] readable). If
# this block cannot verify, the precondition is unsatisfiable for a normal input
# -> PRECOND-TOO-STRONG.
_ADMISS_BLOCK = """    # impl-start
    # ADMISSIBILITY PROBE: the F2P calls merge([ds1, ds2], 'override') where
    # ds1.attrs == {"x": 0} -> a non-empty collection whose leading mapping has
    # one entry. Assert the Requires predicates are establishable on exactly that
    # shape (the read-only collection + the read-only leading source), so a
    # normal F2P input is admitted (else PRECOND-TOO-STRONG).
    Assert(len(variable_attrs) > 0)
    Assert(mode == DROP or mode == OVERRIDE)
    Assert(Acc(list_pred(variable_attrs), 1 / 2))
    Assert(Acc(list_pred(variable_attrs[0]), 1 / 2))"""

ADMISS = _swap(_BASE, "    # impl-start", _ADMISS_BLOCK)


# === FRAME-MUTATION rivals (MANDATORY: both inputs are read-only) =========

# --- F1: OVERRIDE impl that WRITES to the read-only leading source
# variable_attrs[0] (clears then refills it) to "produce" the copy in place.
# It holds only Acc(list_pred(variable_attrs[0]), 1/2), so any write needs full
# permission it does not have -> rejected for INSUFFICIENT PERMISSION. A byte
# fuzzer never thinks to mutate the input; this is the project's #1 weakness.
# refinement: a real patch that mutated variable_attrs[0] in place (e.g.
# `variable_attrs[0].clear(); return variable_attrs[0]`) and returned it would
# corrupt the leading SOURCE's attrs and still alias them; F2P
# test_merge_attrs_override_copy mutates ds3.attrs['x'] and asserts ds1.x==0 —
# an in-place-mutating/aliasing patch fails it and does NOT resolve.
# rejection source: the permission system — the impl lacks full perm on
# variable_attrs[0] (Requires gives only 1/2); also breaks frame clause F.
_F1_IMPL = """    if mode == DROP:
        empty = []  # type: List[int]
        return empty
    src = variable_attrs[0]  # type: List[int]
    # FRAME-MUTATION RIVAL: write to the READ-ONLY leading source. Only 1/2
    # permission is held, so this requires full permission it does not have.
    src.append(0)
    return src"""

FRAME_WRITE_SOURCE = _swap(_BASE, _IMPL, _F1_IMPL)


# --- F2: OVERRIDE impl that WRITES to the read-only outer collection
# variable_attrs (appends a mapping) before building the copy. It holds only
# Acc(list_pred(variable_attrs), 1/2) -> the write needs full permission it lacks
# -> rejected for INSUFFICIENT PERMISSION. Keeps the correct distinct-copy return
# so the rejection is attributable solely to the input write.
# refinement: a real patch that mutated the `variable_attrs` list passed by
# merge_attrs (the per-source attrs collection) would corrupt the merge inputs
# the surrounding merge pipeline still reads; the P2P merge tests
# (test_merge_datasets / test_merge_arrays_attrs_*) would observe the altered
# source collection and fail — it would NOT resolve.
# rejection source: the permission system — only 1/2 permission on
# variable_attrs; also breaks frame clause F (the collection must be returned
# unchanged).
_F2_IMPL = """    if mode == DROP:
        empty = []  # type: List[int]
        return empty
    src = variable_attrs[0]  # type: List[int]
    # FRAME-MUTATION RIVAL: write to the READ-ONLY outer collection. Only 1/2
    # permission is held on variable_attrs, so this append lacks the needed
    # full permission.
    extra = []  # type: List[int]
    variable_attrs.append(extra)
    result = []  # type: List[int]
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(result is not src)
        Invariant(0 <= i and i <= len(src))
        Invariant(len(result) == i)
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        Invariant(MustTerminate(len(src) - i + 1))
        # invariants-end
        result.append(src[i])
        i = i + 1
    return result"""

FRAME_WRITE_OUTER = _swap(_BASE, _IMPL, _F2_IMPL)


# === UNIQUENESS / IDENTITY rivals =========================================

# --- A: ALIAS RETURN — the exact PRE-PATCH bug: OVERRIDE returns the leading
# source object itself (`return variable_attrs[0]`). Content equality (P3) holds
# trivially, but P1 (full perm on Result()) + the retained 1/2 on the source sum
# past 1 on the SAME object, and P2 (Result() is not variable_attrs[0]) is false.
# refinement: this is LITERALLY the pre-patch `return variable_attrs[0]`; F2P
# test_merge_attrs_override_copy mutates ds3.attrs['x']=2 and asserts ds1.x==0,
# but with the alias ds1.x becomes 2 — the test fails, so it does NOT resolve
# (it is exactly the bug the gold patch fixes).
# rejection source: P1 Acc(list_pred(Result())) (insufficient permission, 1+1/2>1)
# and P2 Result() is not variable_attrs[0].
_ALIAS_IMPL = """    if mode == DROP:
        empty = []  # type: List[int]
        return empty
    # ALIAS-RETURN RIVAL (pre-patch bug): hand back the leading source object
    # itself instead of an independent copy.
    return variable_attrs[0]"""

ALIAS_RETURN = _swap(_BASE, _IMPL, _ALIAS_IMPL)


# --- B: DROP returns a non-empty mapping. Reaches the OVERRIDE copy path for
# BOTH modes (ignores `mode`), so DROP yields a content-equal copy of the source
# instead of the empty mapping. Correct on OVERRIDE; diverges on the DROP
# sub-domain. (partial-domain over the mode tag.)
# refinement: a real patch whose 'drop' branch returned dict(variable_attrs[0])
# (or variable_attrs[0]) instead of {} would carry the leading source's attrs
# into the merged product under combine_attrs='drop'; the P2P merge tests that
# exercise attribute dropping (test_merge_arrays_attrs / _variables) assert empty
# (or default) merged attrs and would fail — it would NOT resolve.
# rejection source: P4 Implies(mode==DROP, len(Result())==0).
_DROP_NONEMPTY_IMPL = """    src = variable_attrs[0]  # type: List[int]
    result = []  # type: List[int]
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(result is not src)
        Invariant(0 <= i and i <= len(src))
        Invariant(len(result) == i)
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        Invariant(MustTerminate(len(src) - i + 1))
        # invariants-end
        result.append(src[i])
        i = i + 1
    # DROP-NON-EMPTY RIVAL: this copy is returned for DROP too (mode ignored).
    return result"""

DROP_NONEMPTY = _swap(_BASE, _IMPL, _DROP_NONEMPTY_IMPL)


# --- C: PARTIAL-DOMAIN copy that DROPS THE LAST entry — stop the prefix copy one
# short (while i < len(src) - 1). The loop keeps the gold front/prefix-fold
# invariant verbatim (result == ToSeq(src).take(i)), so it verifies internally
# and yields the right DISTINCT-object/full-permission shape; only the result's
# CONTENT is short by one entry. Correct (vacuously) on an empty/1-entry source's
# prefix but omits the trailing attribute on any source of length >= 2, so it is a
# faithful copy on a strict sub-domain only.
# refinement: a real patch like `dict(list(variable_attrs[0].items())[:-1])`
# would drop the LAST attribute of the leading source; the merged product would
# be MISSING that attr — the merge-attrs P2P tests compare the merged attrs to
# the multi-entry source and would fail — it would NOT resolve.
# rejection source: P3 Implies(mode==OVERRIDE, ToSeq(Result())==ToSeq(
# variable_attrs[0])) — the copy must reproduce the WHOLE content; take(len-1) is
# a proper prefix, not the whole.
_SKIP_LAST_IMPL = """    if mode == DROP:
        empty = []  # type: List[int]
        return empty
    src = variable_attrs[0]  # type: List[int]
    result = []  # type: List[int]
    i = 0
    # PARTIAL-DOMAIN RIVAL: stop one entry short (drop the trailing attribute).
    while i < len(src) - 1:
        # invariants-start
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(result is not src)
        Invariant(0 <= i and i <= len(src))
        Invariant(len(result) == i)
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        Invariant(MustTerminate(len(src) - i + 1))
        # invariants-end
        result.append(src[i])
        i = i + 1
    return result"""

SKIP_LAST = _swap(_BASE, _IMPL, _SKIP_LAST_IMPL)


# --- D: EMPTY-COPY rival — OVERRIDE returns a FRESH empty mapping (a distinct
# object, full permission), short-circuiting the copy loop. Satisfies P1/P2
# (fresh distinct object) but NOT P3 unless the source is empty. Correct on an
# empty leading source; diverges on every non-empty one (the F2P's {"x":0}).
# refinement: a real patch whose 'override' branch returned {} (a fresh empty
# dict) would make the merged product carry NO attrs; F2P reads ds3.x and merge-
# attrs P2P tests assert the leading source's attrs are present — they would fail
# — it would NOT resolve.
# rejection source: P3 ToSeq(Result())==ToSeq(variable_attrs[0]) (content must
# match the full source; an empty result only matches an empty source).
_EMPTY_COPY_IMPL = """    if mode == DROP:
        empty = []  # type: List[int]
        return empty
    src = variable_attrs[0]  # type: List[int]
    # EMPTY-COPY RIVAL: a fresh distinct empty mapping, NOT the source's content.
    fresh = []  # type: List[int]
    return fresh"""

EMPTY_COPY = _swap(_BASE, _IMPL, _EMPTY_COPY_IMPL)


SPEC_TESTS = [
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_REORDER,
        "rationale": "structurally-different CORRECT impl (OVERRIDE branch handled "
        "first, DROP return last, loop bound hoisted into a local `n`) keeping every "
        "gold invariant verbatim and the SAME forward-append loop direction (so the "
        "front/prefix fold ToSeq(src).take(i) needs no f(a+b) lemma — directive-3 "
        "safe). Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "asserts the Requires predicates (len>0, mode in {DROP,OVERRIDE}, "
        "the half-permission predicates on the read-only collection and leading "
        "source) are establishable on the F2P-shaped input — the precondition must "
        "admit a normal merge(['override']) call, else PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-write-source",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_WRITE_SOURCE,
        "refinement": "a real patch that mutated variable_attrs[0] in place and "
        "returned it (e.g. clear()+refill, or just returned the aliased source) would "
        "corrupt the leading SOURCE's attrs and still share them; F2P "
        "test_merge_attrs_override_copy mutates ds3.attrs['x']=2 and asserts ds1.x==0 "
        "— an in-place-mutating/aliasing patch fails it and does NOT resolve.",
        "rationale": "MANDATORY frame-mutation: rejected by the PERMISSION SYSTEM — "
        "the impl holds only Acc(list_pred(variable_attrs[0]), 1/2) and the append "
        "to `src` (== variable_attrs[0]) needs full permission it does not have; also "
        "breaks frame clause F (the read-only leading source must be returned "
        "unchanged).",
    },
    {
        "id": "frame-write-outer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_WRITE_OUTER,
        "refinement": "a real patch that mutated the per-source attrs collection "
        "`variable_attrs` (passed in by merge_attrs) would corrupt the inputs the "
        "surrounding merge pipeline still reads; the P2P merge tests "
        "(test_merge_datasets / test_merge_arrays_attrs_*) would observe the altered "
        "source collection and fail — it would NOT resolve.",
        "rationale": "MANDATORY frame-mutation (outer collection): rejected by the "
        "PERMISSION SYSTEM — the impl holds only Acc(list_pred(variable_attrs), 1/2) "
        "and the append to variable_attrs needs full permission it lacks; also breaks "
        "frame clause F.",
    },
    {
        "id": "alias-return",
        "kind": "uniqueness",
        "expect": "reject",
        "module": ALIAS_RETURN,
        "refinement": "this is LITERALLY the pre-patch `return variable_attrs[0]`; F2P "
        "test_merge_attrs_override_copy mutates ds3.attrs['x']=2 and asserts ds1.x==0, "
        "but with the alias ds1.x becomes 2 — the test fails, so it does NOT resolve "
        "(exactly the bug the gold patch fixes).",
        "rationale": "rejected by P1 Acc(list_pred(Result())) (insufficient permission: "
        "full perm on Result() + the source's retained 1/2 sum past 1 on the SAME "
        "object) AND P2 Result() is not variable_attrs[0]. This is the G-DIFF witness "
        "made into a same-spec rival.",
    },
    {
        "id": "drop-nonempty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": DROP_NONEMPTY,
        "refinement": "a real patch whose 'drop' branch returned dict(variable_attrs[0]) "
        "(or the source) instead of {} would carry the leading source's attrs into the "
        "merged product under combine_attrs='drop'; the P2P merge tests exercising "
        "attribute dropping (test_merge_arrays_attrs / _variables) assert empty/default "
        "merged attrs and would fail — it would NOT resolve.",
        "rationale": "partial-domain over the mode tag: rejected by P4 "
        "Implies(mode==DROP, len(Result())==0) — DROP must yield an EMPTY mapping, but "
        "this rival returns a content-equal copy of the source for DROP too.",
    },
    {
        "id": "skip-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SKIP_LAST,
        "refinement": "a real patch like `dict(list(variable_attrs[0].items())[:-1])` "
        "would drop the LAST attribute of the leading source; the merged product would "
        "be missing that attr — the merge-attrs P2P tests compare the merged attrs to "
        "a multi-entry source and would fail — it would NOT resolve.",
        "rationale": "partial-domain (faithful only on a 0/1-entry source): the loop "
        "keeps the gold prefix-fold invariant verbatim so it verifies internally, but "
        "P3 Implies(mode==OVERRIDE, ToSeq(Result())==ToSeq(variable_attrs[0])) rejects "
        "it — take(len-1) is a proper prefix, not the whole content.",
    },
    {
        "id": "empty-copy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": EMPTY_COPY,
        "refinement": "a real patch whose 'override' branch returned {} (a fresh empty "
        "dict) would make the merged product carry NO attrs; F2P reads ds3.x and the "
        "merge-attrs P2P tests assert the leading source's attrs are present in the "
        "override result — they would fail — it would NOT resolve.",
        "rationale": "partial-domain (correct only on an EMPTY source): a fresh empty "
        "result satisfies P1/P2 (distinct, full permission) but fails P3 "
        "ToSeq(Result())==ToSeq(variable_attrs[0]) on every non-empty source. Shows P3 "
        "(content) is independent of P1/P2 (identity) — both are load-bearing.",
    },
]


# No @ContractOnly axioms (meta.json axioms == []; the model imports no
# @ContractOnly) and no consumed deep-model axiom. The single A-reference deep
# model — the per-entry copy loop standing in for dict(variable_attrs[0]) — is a
# HOST-run equality check (axiom_check.py / G-AX over 6 boundary + 20000 fuzz
# inputs), not a per-input Docker probe with a contract Requires/Ensures domain.
# There is therefore nothing for the axiom lane to run in-container.
AXIOM_TESTS = []
