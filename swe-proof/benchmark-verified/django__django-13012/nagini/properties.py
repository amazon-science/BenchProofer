# properties.py — PBT falsification battery for django__django-13012.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions regions untouched) and swaps ONLY text inside
# a # impl-start/# impl-end region; the runner checks each with Nagini verify +
# markers.same_spec.
#
# Defended surface (read from model.py + refinement.md + mapping.md + instance.json):
#   wrapper_group_by_cols(node: WrappingNode, request: Optional[int]) -> List[int]
#     the MODELED CHANGED function (the composite ExpressionWrapper's new
#     get_group_by_cols). Its three inputs are READ-ONLY: Requires/Ensures
#     Acc(node.inner_id, 1/2), Acc(node.inner_is_constant, 1/2),
#     Acc(node.node_id, 1/2). Load-bearing postcondition:
#         ToSeq(Result()) == base_group_cols_seq(node.inner_id, node.inner_is_constant)
#     i.e. the composite contributes EXACTLY the WRAPPED node's own answer:
#       [] for a constant, [inner_id] for a column-like node — NEVER [node_id]
#     (the composite itself). The class invariant node.inner_id != node.node_id
#     is what makes "return [node_id]" (the pre-patch bug) a real falsification.
#
#   base_group_by_cols(node_id, is_constant, request) -> List[int]
#     the deep model (A-reference) of the WRAPPED node's own unchanged rule.
#     Requires(MustTerminate(2)) — it must actually answer. Postcondition:
#         ToSeq(Result()) == base_group_cols_seq(node_id, is_constant)
#     base_group_cols_seq is a @Pure helper FULLY GROUNDED in (node_id,
#     is_constant): empty seq if is_constant else PSeq(node_id). It is NOT an
#     opaque answer-key oracle — there is no wrong echo of it that verifies. See
#     'assessment' for the ungrounded-oracle disposition.
#
# F2P: test_empty_group_by  (ExpressionWrapper(Value(3))      -> [])
#      test_non_empty_group_by (ExpressionWrapper(Lower(Value('f'))) -> [expr.expression])
#      Both are inside the modelled family; one is the constant arm, one the
#      column-like arm. The single symbolic postcondition senses BOTH.
#
# No @ContractOnly axiom is consumed (axioms region empty; meta.json axioms==[]).
# The wrapped node's rule is an A-reference deep model validated by axiom_check.py
# (G-AX) against the real Django callees in-container — see AXIOM_TESTS.

from pathlib import Path

INSTANCE = "django__django-13012"
FLOAT_ENCODING = None  # meta.json float_encoding == null


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


_BASE = (Path(__file__).parent / "model.py").read_text()


# ---------------------------------------------------------------------------
# Frozen impl regions (verbatim from model.py) used as unique _swap anchors.
# Only the bytes BETWEEN # impl-start / # impl-end are ever edited, so the
# spec_view (and thus same_spec) is preserved for every variant.
# ---------------------------------------------------------------------------

# base_group_by_cols impl region body (the dichotomy):
_BASE_IMPL = """    if is_constant:
        empty = []  # type: List[int]
        return empty
    one = [node_id]  # type: List[int]
    return one"""

# wrapper_group_by_cols impl region body (the delegation forward):
_WRAP_IMPL = """    cols = base_group_by_cols(node.inner_id, node.inner_is_constant, request)
    return cols"""


# === POSITIVE CONTROL (soundness) =========================================
# Structurally-different but CORRECT impl of base_group_by_cols: branch-REORDER
# — handle the column-like (non-constant) case FIRST and fall through to the
# constant case last. Same executable meaning (the dichotomy is exhaustive on
# bool), no loop, no fold, no induction lemma needed (directive-3 safe). The
# wrapper delegation is untouched. If this cannot verify => SPEC-TOO-STRONG.
_POS_BASE = """    if not is_constant:
        one = [node_id]  # type: List[int]
        return one
    empty = []  # type: List[int]
    return empty"""
POS_REORDER = _swap(_BASE, _BASE_IMPL, _POS_BASE)


# === ADMISSIBILITY ========================================================
# A positive-control CALLER appended as an impl-only helper INSIDE the wrapper's
# impl region (after the gold `return cols`, before # impl-end) — the proven
# django-12708 pattern, so the frozen spec is untouched and every gold obligation
# of wrapper_group_by_cols is preserved verbatim. The helper constructs a
# concrete F2P-shaped WrappingNode (a constant wrapped node, inner_id=7,
# node_id=9 distinct per the invariant) and CALLS wrapper_group_by_cols on it.
# The constructor's Ensures establishes the Acc(.,1/2) half-permissions and the
# invariant inner_id != node_id — exactly wrapper_group_by_cols's Requires — so
# the call site must verify. If the Requires cannot be met for a legitimate
# F2P-shaped node => PRECOND-TOO-STRONG. (No recursion / no Decreases needed.)
_ADMISS_WRAP = """    cols = base_group_by_cols(node.inner_id, node.inner_is_constant, request)
    return cols


def _admiss_caller() -> None:
    # impl-only helper: build an F2P-shaped composite and call the modeled
    # function. The constructor grants Acc(.,1/2) on each field + inner_id !=
    # node_id, which is exactly the Requires of wrapper_group_by_cols.
    probe = WrappingNode(7, True, 9)
    got = wrapper_group_by_cols(probe, None)
    # the precondition admitted a normal input; the result is in domain.
    # NOTE (proof engineering, in-region only): wrapper_group_by_cols's
    # postcondition restores Acc(node.inner_id/inner_is_constant, 1/2) but does
    # not restate their values, so Nagini havocs the *literal* facts
    # (probe.inner_id == 7, probe.inner_is_constant == True) across the call.
    # The caller still holds the half-permissions, so we phrase the result
    # equality over the (still-readable) post-call field reads — exactly the
    # form the postcondition delivers — rather than over the stale literals.
    Assert(Acc(list_pred(got)))
    Assert(ToSeq(got) == base_group_cols_seq(probe.inner_id, probe.inner_is_constant))"""
ADMISS = _swap(_BASE, _WRAP_IMPL, _ADMISS_WRAP)


# === FRAME-MUTATION (MANDATORY: read-only Acc(.,1/2) inputs) ===============
# wrapper_group_by_cols holds node.inner_id / inner_is_constant / node_id at
# HALF permission (read-only). A rival that WRITES to a read-only field —
# overwriting node.inner_id with node.node_id so the wrapped/composite identities
# collide — must fail for INSUFFICIENT PERMISSION (you cannot write with 1/2).
# Every gold obligation is kept verbatim (the delegation still runs and returns),
# so the rejection is attributable to the illegal write, not a value mismatch.
# A byte-fuzzer never thinks to mutate the input; this is the project's #1 class.
# refinement: a faithful real patch that did `self.expression = self` (rebinding
# the wrapped node to the composite itself) before forwarding would make the
# composite contribute ITSELF on the column-like arm — exactly the bug the patch
# fixes; test_non_empty_group_by asserts [expr.expression] (the ORIGINAL wrapped
# node), so the patch would FAIL it and NOT resolve.
# rejection source: the permission system — node.inner_id is Acc(.,1/2), a write
# requires full permission.
_FRAME_WRAP = """    node.inner_id = node.node_id  # FRAME-MUTATION: write to a read-only (1/2) field
    cols = base_group_by_cols(node.inner_id, node.inner_is_constant, request)
    return cols"""
FRAME_WRITE = _swap(_BASE, _WRAP_IMPL, _FRAME_WRAP)


# === UNIQUENESS / REJECT rivals ===========================================

# --- The PRE-PATCH bug, re-expressed: the composite contributes ITSELF.
# Instead of forwarding to the wrapped node, return [node.node_id] (the
# composite's own identity) — exactly the inherited BaseExpression default the
# missing override produced. Reads node_id at 1/2 (legal read), no write, so the
# rejection is purely from the value postcondition.
# refinement: this IS the pre-patch behaviour (no get_group_by_cols override ->
# inherited BaseExpression.get_group_by_cols returns [self]). On the constant arm
# (Value(3)) it yields [the wrapper] not []; test_empty_group_by asserts [] —
# the patch would FAIL it (it is the literal GROUP-BY bug from the issue) and NOT
# resolve. On the column-like arm it yields [the wrapper] not [the wrapped node];
# test_non_empty_group_by asserts [expr.expression] and would also FAIL.
# rejection source: postcondition
#   ToSeq(Result()) == base_group_cols_seq(node.inner_id, node.inner_is_constant)
# together with the invariant node.inner_id != node.node_id: on the column-like
# arm base_group_cols_seq pins [inner_id] but the rival returns [node_id] != it;
# on the constant arm it pins [] but the rival returns [node_id] (non-empty).
_SELF_WRAP = """    me = [node.node_id]  # type: List[int]
    return me"""
RETURN_SELF = _swap(_BASE, _WRAP_IMPL, _SELF_WRAP)


# --- Partial-domain (constant arm): on base_group_by_cols, always return
# [node_id] (drop the constant case). Correct on the column-like arm, WRONG on
# the constant arm (Value(3) -> required [], rival yields [node_id]).
# refinement: a faithful real patch where Value.get_group_by_cols was not
# consulted (e.g. forwarding to BaseExpression's [self] default for constants)
# would put the constant 3 back in the GROUP BY clause — the exact Postgres
# "aggregate functions are not allowed in GROUP BY" failure of the issue;
# test_empty_group_by asserts [] and would FAIL — it would NOT resolve.
# rejection source: the constant arm of the postcondition
#   ToSeq(Result()) == base_group_cols_seq(node_id, is_constant)
# = empty seq when is_constant; the rival returns [node_id] (non-empty).
_PD_CONST = """    one = [node_id]  # type: List[int]
    return one"""
DROP_CONSTANT = _swap(_BASE, _BASE_IMPL, _PD_CONST)


# --- Partial-domain (column-like arm): on base_group_by_cols, always return []
# (drop the column-like case). Correct on the constant arm, WRONG on the
# column-like arm (Lower(Value('f')) -> required [inner_id], rival yields []).
# refinement: a faithful real patch that returned [] for a column-like wrapped
# node would DROP a real grouping column from the GROUP BY clause, changing query
# semantics (the column-like node must group by itself);
# test_non_empty_group_by asserts [expr.expression] and would FAIL — NOT resolve.
# rejection source: the column-like arm of the postcondition
#   ToSeq(Result()) == base_group_cols_seq(node_id, is_constant)
# = PSeq(node_id) when not is_constant; the rival returns [] (length 0 != 1).
_PD_COL = """    empty = []  # type: List[int]
    return empty"""
DROP_COLUMN = _swap(_BASE, _BASE_IMPL, _PD_COL)


# --- Wrong-identity rival: on base_group_by_cols's column-like arm, contribute a
# DIFFERENT node identity (node_id + 1) instead of the node itself. Right shape
# (one-element list, right on the constant arm) but the wrong column.
# refinement: a faithful real patch contributing a different expression object to
# the GROUP BY (e.g. a freshly-built Col rather than `self`) would group by the
# wrong column — the regression test reads back [expr.expression] (identity of
# the wrapped node) and would get a different object; it would NOT resolve.
# rejection source: the column-like arm pins ToSeq(Result()) == PSeq(node_id);
# the rival returns PSeq(node_id + 1) != PSeq(node_id).
_WRONG_ID = """    if is_constant:
        empty = []  # type: List[int]
        return empty
    one = [node_id + 1]  # type: List[int]
    return one"""
WRONG_IDENTITY = _swap(_BASE, _BASE_IMPL, _WRONG_ID)


SPEC_TESTS = [
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_REORDER,
        "rationale": "structurally-different CORRECT impl of base_group_by_cols "
        "(column-like branch handled first, constant branch last) — must verify, "
        "else SPEC-TOO-STRONG. Branch reorder only; no loop/fold/induction "
        "(directive-3 safe). The wrapper delegation is untouched.",
    },
    {
        "id": "admiss-wrapper",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "positive-control caller constructs an F2P-shaped "
        "WrappingNode(7, True, 9) and calls wrapper_group_by_cols on it; the "
        "constructor Ensures establishes the Acc(.,1/2) perms + inner_id!=node_id "
        "that the Requires demands, so the call site must verify — else "
        "PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-write-inner",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_WRITE,
        "refinement": "a faithful real patch doing `self.expression = self` before "
        "forwarding would make the composite contribute ITSELF on the column-like "
        "arm; test_non_empty_group_by asserts [expr.expression] (the ORIGINAL "
        "wrapped node) and would FAIL — it would NOT resolve.",
        "rationale": "MANDATORY frame-mutation probe. node.inner_id is held at "
        "Acc(.,1/2) (read-only); the rival WRITES to it, which requires FULL "
        "permission. Rejection comes from the PERMISSION SYSTEM (insufficient "
        "permission to assign node.inner_id), NOT a value mismatch — every gold "
        "obligation is kept verbatim so the rejection is attributable to the write.",
    },
    {
        "id": "return-self",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RETURN_SELF,
        "refinement": "this is the literal PRE-PATCH behaviour (no override -> "
        "inherited BaseExpression.get_group_by_cols returns [self]); on a constant "
        "(Value(3)) it puts the wrapper in the GROUP BY (the Postgres bug from the "
        "issue), and on a column-like node it contributes the wrapper not the "
        "wrapped node. Both F2P tests assert otherwise and would FAIL — it does "
        "NOT resolve (it IS the bug the patch fixes).",
        "rationale": "rejected by the postcondition ToSeq(Result()) == "
        "base_group_cols_seq(node.inner_id, node.inner_is_constant) together with "
        "the invariant node.inner_id != node.node_id: on the column-like arm the "
        "pin is [inner_id] but the rival returns [node_id] (!=); on the constant "
        "arm the pin is [] but the rival returns the non-empty [node_id]. This is "
        "the decisive discriminator (G-DIFF / the prepatch).",
    },
    {
        "id": "drop-constant",
        "kind": "uniqueness",
        "expect": "reject",
        "module": DROP_CONSTANT,
        "refinement": "a faithful patch that did not consult Value's []-override "
        "for constants (forwarding to BaseExpression's [self] default) would put "
        "the constant 3 back in the GROUP BY — the exact Postgres failure of the "
        "issue; test_empty_group_by asserts [] and would FAIL — NOT resolve.",
        "rationale": "partial-domain: correct on the column-like arm, wrong on the "
        "constant arm. Rejected by the constant arm of the postcondition "
        "ToSeq(Result()) == base_group_cols_seq(node_id, is_constant) (= empty seq "
        "when is_constant); the rival returns the non-empty [node_id].",
    },
    {
        "id": "drop-column",
        "kind": "uniqueness",
        "expect": "reject",
        "module": DROP_COLUMN,
        "refinement": "a faithful patch returning [] for a column-like wrapped node "
        "would DROP a real grouping column from the GROUP BY clause, changing query "
        "semantics; test_non_empty_group_by asserts [expr.expression] and would "
        "FAIL — it would NOT resolve.",
        "rationale": "partial-domain: correct on the constant arm, wrong on the "
        "column-like arm. Rejected by the column-like arm of the postcondition "
        "ToSeq(Result()) == base_group_cols_seq(node_id, is_constant) (= "
        "PSeq(node_id) when not is_constant); the rival returns [] (length 0 != 1).",
    },
    {
        "id": "wrong-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": WRONG_IDENTITY,
        "refinement": "a faithful patch contributing a DIFFERENT expression object "
        "to the GROUP BY for a column-like node (e.g. a freshly built Col instead "
        "of `self`) would group by the wrong column; the regression test reads "
        "back the wrapped node's identity ([expr.expression]) and would get a "
        "different object — it would NOT resolve.",
        "rationale": "value-level: right shape (one-element list), wrong identity. "
        "Rejected by the column-like arm ToSeq(Result()) == PSeq(node_id); the "
        "rival returns PSeq(node_id + 1) != PSeq(node_id).",
    },
]


# === AXIOM LANE ===========================================================
# No @ContractOnly axiom is consumed (model.py axioms region is empty; meta.json
# axioms == []). The wrapped node's grouping-column rule is an A-REFERENCE deep
# model (base_group_by_cols / base_group_cols_seq) validated against the real
# Django callees in-container by axiom_check.py (G-AX). PBT re-runs that exact
# host-validated oracle as a containment + soundness probe:
#   * axiom-soundness   — the deep model base_group_cols_seq EQUALS the real
#     wrapped-node callees (Value.get_group_by_cols -> []; BaseExpression
#     non-aggregate -> [self]) on the modelled family, AND the real composite
#     ExpressionWrapper.get_group_by_cols FORWARDS verbatim (the universal
#     delegation obligation), under the caller's runtime config, fuzzing several
#     aliases incl. a non-trivial one.
#   * axiom-containment — every callee-input the MODEL can reach (the modelled
#     family: non-aggregate constant-or-column-like nodes) lies inside the
#     A-reference's domain (the dichotomy / alias-inertness holds), and the two
#     escaping kinds the model NEVER wraps (Subquery, OrderBy(Col)) genuinely
#     escape, demonstrating the domain boundary is a chosen sound restriction.
# The probe embeds axiom_check.py's source (read on the HOST at load time — the
# runner mounts ONLY the probe at /work, so model.py/axiom_check.py are NOT
# in-container) and runs it post-gold (apply_gold=True: the axiom describes the
# post-patch forwarding behaviour). Exit 0 iff every obligation holds.

_AX_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

_PROBE_SOUNDNESS = (
    "# -*- coding: utf-8 -*-\n"
    "# G-AX soundness probe (django__django-13012): run the host-validated\n"
    "# axiom_check.py oracle against the REAL Django callees in-container.\n"
    "# It asserts: (a) the A-reference deep model base_group_cols_seq EQUALS the\n"
    "# real wrapped-node rule on the modelled family (Value->[], column-like->[self]),\n"
    "# and (b) the real composite ExpressionWrapper.get_group_by_cols FORWARDS\n"
    "# verbatim over ALL wrapped nodes incl. escaping kinds (the universal\n"
    "# delegation soundness obligation), under the caller's config, several aliases.\n"
    "# Exit 0 iff sound (matches G-AX on the gold-applied tree).\n\n"
    + _AX_SRC
)

_PROBE_CONTAINMENT = (
    "# -*- coding: utf-8 -*-\n"
    "# G-AX caller-domain containment probe (django__django-13012).\n"
    "# The MODEL only ever wraps the modelled family (non-aggregate,\n"
    "# constant-or-column-like nodes); axiom_check.py asserts every modelled-family\n"
    "# node observes the dichotomy ([]/[self]) + alias-inertness (so each lies in\n"
    "# the A-reference's domain) AND that the two escaping kinds the model NEVER\n"
    "# wraps (Subquery alias-dependent; OrderBy(Col) non-dichotomy) genuinely\n"
    "# escape — demonstrating the modelled domain is a chosen, sound restriction,\n"
    "# not an oversight (no reachable input lies outside the covered domain).\n"
    "# Exit 0 iff every reachable callee-input is contained.\n\n"
    + _AX_SRC
)


AXIOM_TESTS = [
    {
        "id": "ax-sound-base-group-cols",
        "axiom": "base_group_by_cols / base_group_cols_seq",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_SOUNDNESS,
        "rationale": "A-reference soundness: the deep model base_group_cols_seq must "
        "equal the REAL wrapped-node callees (Value.get_group_by_cols -> []; "
        "BaseExpression non-aggregate -> [self]) on the modelled family, and the "
        "real composite ExpressionWrapper.get_group_by_cols must FORWARD verbatim "
        "(never contribute itself) over all wrapped nodes — the universal delegation "
        "obligation the proof relies on. If the real callee disagrees => the deep "
        "model is unsound (AXIOM-UNSOUND-analogue). Runs post-gold (apply_gold).",
    },
    {
        "id": "ax-contain-modelled-family",
        "axiom": "base_group_by_cols / base_group_cols_seq",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_CONTAINMENT,
        "rationale": "caller-domain containment: every callee-input the model can "
        "reach (the modelled family of non-aggregate constant-or-column-like nodes) "
        "lies inside the A-reference's domain (dichotomy + alias-inertness hold), and "
        "the escaping kinds the model never wraps (Subquery, OrderBy(Col)) are shown "
        "to genuinely escape — so the modelled domain is a sound chosen restriction, "
        "not a reachable input outside the covered domain "
        "(AXIOM-TOO-WEAK-FOR-CALLER-analogue). Runs post-gold (apply_gold).",
    },
]
