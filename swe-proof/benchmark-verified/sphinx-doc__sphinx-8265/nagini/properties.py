# properties.py — PBT falsification battery for sphinx-doc__sphinx-8265.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT onto. Spec cases are full
# model.py variants that share the FROZEN spec (same_spec) and differ ONLY
# inside the # impl-start / # impl-end regions (region surgery guarantees
# same_spec). Each is checked by Nagini verify on the host.
#
# DEFENDED SURFACE (read model.py + refinement.md + mapping.md):
#   Two pure renderers over IMMUTABLE Nagini value sequences:
#     tuple_render(elts: PSeq[PSeq[int]]) -> PSeq[int]
#       post: Implies(len>0, Result == '(' + join_comma(elts) + ')')
#             Implies(len==0, Result == '()')          [PSeq(40,41)]
#     subscript_render(value, elts, index_is_member_group, slice_rendered)
#       pre:  Implies(index_is_member_group, len(elts) > 0)
#       post: Implies(group,     Result == value '[' join_comma(elts) ']')
#             Implies(not group, Result == value '[' slice_rendered ']')
#   join_comma is a @Pure helper GROUNDED in the input (a fully-unfolded
#   front-recursive fold of `elts`), validated == real ', '.join by
#   axiom_check.py. There is NO @ContractOnly axiom (meta.axioms == []),
#   so AXIOM_TESTS = [].
#
# WHY frame-mutation is N/A: every input is a PSeq / PSeq[PSeq[int]], i.e. an
#   immutable Nagini value type carried by SHARE — there is no Acc(x, k)
#   permission and no mutating method (.append/__setitem__) on a PSeq. A rival
#   cannot "overwrite a read-only input" because no input is a mutable object
#   with a write permission. The frame-mutation attack class simply does not
#   exist on this surface; see 'assessment'. (has_readonly_input = False.)
#
# WHY ungrounded-oracle echo is N/A: the only oracle in the postcondition is
#   join_comma(elts), which is a pure FUNCTION OF THE INPUT (fully unfolded over
#   elts). "Echoing" it IS doing the work — there is no answer-key marker an
#   impl could parrot to verify a WRONG output. So instead this lane is covered
#   by the honest cheapest-impl positive control (pos-tuple-cheapest).
#
# WHY control-flow-effect is N/A: both functions are total pure value functions
#   with no raise/side-effect/return-channel difference; Result() is the entire
#   observable. There is nothing invisible to the value abstraction.
#
# The live attack surface is PARTIAL-DOMAIN / uniqueness: each postcondition is
# a conjunction of guarded Implies clauses, so a rival can be correct on one
# branch and wrong on the other. Those are the reasoned rejects below; the two
# gold prepatch bugs (bare-join tuple, parenthesised index) are reproduced as
# the load-bearing F2P/P2P discriminators.

from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8265"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The two gold impl blocks (verbatim, each unique in _BASE). All rivals are
# built by _swap-ing ONLY text that lives strictly between the impl markers.
# ---------------------------------------------------------------------------

_TUPLE_GOLD = (
    "    if len(elts) > 0:\n"
    "        body = join_comma(elts)  # type: PSeq[int]\n"
    "        result = (PSeq(40) + body) + PSeq(41)  # type: PSeq[int]\n"
    "    else:\n"
    "        result = PSeq(40, 41)\n"
    "    return result\n"
)

_SUBSCRIPT_GOLD = (
    "    if index_is_member_group:\n"
    "        body = join_comma(elts)  # type: PSeq[int]\n"
    "    else:\n"
    "        body = slice_rendered\n"
    "    result = ((value + PSeq(91)) + body) + PSeq(93)  # type: PSeq[int]\n"
    "    return result\n"
)


# === Positive controls (soundness): structurally different but CORRECT ======

# Reorder branches: handle the empty group FIRST, then the non-empty one, and
# build the wrapped result without the intermediate `body` local. Same value,
# different executable shape. No induction/lemma needed — join_comma(elts) is
# used in exactly one place exactly as the spec uses it, so the verifier
# discharges the equality directly.
_POS_TUPLE = _swap(
    _BASE, _TUPLE_GOLD,
    "    if len(elts) == 0:\n"
    "        result = PSeq(40, 41)  # type: PSeq[int]\n"
    "    else:\n"
    "        result = (PSeq(40) + join_comma(elts)) + PSeq(41)\n"
    "    return result\n",
)

# Honest cheapest impl that just builds the wrapped join inline (covers the
# 'ungrounded oracle echo' lane: the join is grounded, so the cheapest faithful
# impl IS correct and MUST verify). Single-expression return-shape reshape.
_POS_TUPLE_CHEAPEST = _swap(
    _BASE, _TUPLE_GOLD,
    "    if len(elts) > 0:\n"
    "        result = (PSeq(40) + join_comma(elts)) + PSeq(41)  # type: PSeq[int]\n"
    "    else:\n"
    "        result = PSeq(40, 41)\n"
    "    return result\n",
)

# subscript_render reorder: handle the non-group case first, and precompute the
# common prefix `value + '['` into a local. Same value, different shape; keeps
# join_comma(elts) used identically to the spec on the group branch.
_POS_SUBSCRIPT = _swap(
    _BASE, _SUBSCRIPT_GOLD,
    "    prefix = value + PSeq(91)  # type: PSeq[int]\n"
    "    if not index_is_member_group:\n"
    "        body = slice_rendered  # type: PSeq[int]\n"
    "    else:\n"
    "        body = join_comma(elts)\n"
    "    result = (prefix + body) + PSeq(93)  # type: PSeq[int]\n"
    "    return result\n",
)


# === Admissibility: a positive-control CALLER establishes the Requires ======
# subscript_render's only precondition is Implies(index_is_member_group,
# len(elts) > 0). Inside tuple_render's impl (a legal call site) we call
# subscript_render with an F2P/P2P-shaped in-domain input: a base 'x' (PSeq),
# index_is_member_group=True and a non-empty `elts`, plus a False/empty case.
# If the precondition could NOT be established for these legitimate inputs the
# call would fail to verify => PRECOND-TOO-STRONG. The gold tuple_render body
# still computes `result`, so on the spec side nothing changes.
_ADMISS = _swap(
    _BASE, _TUPLE_GOLD,
    "    # admissibility caller: subscript_render must accept normal inputs.\n"
    "    # `_g` is type-declared ONCE before the branch; carrying a `# type:`\n"
    "    # comment on the same local in BOTH arms is a Nagini type-check error\n"
    "    # ('Name _g already defined'), which is a probe bug, not a precond\n"
    "    # failure. With one declaration the in-domain call verifies.\n"
    "    _g = PSeq(0).take(0)  # type: PSeq[int]\n"
    "    if len(elts) > 0:\n"
    "        _g = subscript_render(PSeq(120), elts, True, PSeq(49))\n"
    "        body = join_comma(elts)  # type: PSeq[int]\n"
    "        result = (PSeq(40) + body) + PSeq(41)  # type: PSeq[int]\n"
    "    else:\n"
    "        _g = subscript_render(PSeq(120), elts, False, PSeq(49))\n"
    "        result = PSeq(40, 41)\n"
    "    return result\n",
)


# === Uniqueness / partial-domain rivals (expect REJECT) =====================

# R1 (= the F2P bug, model_prepatch.py): a non-empty group renders as the BARE
# comma-and-space join with NO surrounding round brackets. Correct on the empty
# sub-domain, wrong on the non-empty one. This is exactly the issue: (1, 2, 3)
# rendering back as `1, 2, 3`. Must be rejected by the tuple_render non-empty
# postcondition clause.
_R_TUPLE_BARE = _swap(
    _BASE, _TUPLE_GOLD,
    "    if len(elts) > 0:\n"
    "        result = join_comma(elts)  # type: PSeq[int]\n"
    "    else:\n"
    "        result = PSeq(40, 41)\n"
    "    return result\n",
)

# R2 (partial-domain, EMPTY sub-domain): correct on the non-empty group, but the
# empty group renders as a single '(' instead of '()'. Pins only the non-empty
# half of the F2P/P2P domain; the empty-tuple P2P test `()-()` would fail.
_R_TUPLE_EMPTY = _swap(
    _BASE, _TUPLE_GOLD,
    "    if len(elts) > 0:\n"
    "        body = join_comma(elts)  # type: PSeq[int]\n"
    "        result = (PSeq(40) + body) + PSeq(41)  # type: PSeq[int]\n"
    "    else:\n"
    "        result = PSeq(40)  # WRONG: '(' instead of '()'\n"
    "    return result\n",
)

# R3 (= the coupling bug, model_prepatch_2.py): a simple-group INDEX body keeps
# an inner pair of round brackets, so an index renders as base[(m0, m1)] not
# base[m0, m1]. Correct on the non-group branch, wrong on the group branch.
# Must be rejected by subscript_render's group-branch postcondition. This is the
# P2P regression guard (Tuple[int, int]).
_R_SUB_PARENS = _swap(
    _BASE, _SUBSCRIPT_GOLD,
    "    if index_is_member_group:\n"
    "        body = (PSeq(40) + join_comma(elts)) + PSeq(41)  # type: PSeq[int]\n"
    "    else:\n"
    "        body = slice_rendered\n"
    "    result = ((value + PSeq(91)) + body) + PSeq(93)  # type: PSeq[int]\n"
    "    return result\n",
)

# R4 (partial-domain, NON-GROUP sub-domain): correct on the group branch, but a
# non-group index DROPS the index body, rendering base[] instead of base[body].
# Pins only the group half; any non-simple-tuple subscript (e.g. x[1], os.path
# subscripts) would render wrong, breaking those P2P unparse rows.
_R_SUB_DROP = _swap(
    _BASE, _SUBSCRIPT_GOLD,
    "    if index_is_member_group:\n"
    "        body = join_comma(elts)  # type: PSeq[int]\n"
    "    else:\n"
    "        body = PSeq(0).take(0)  # WRONG: drops the index body -> base[]\n"
    "    result = ((value + PSeq(91)) + body) + PSeq(93)  # type: PSeq[int]\n"
    "    return result\n",
)

# R5 (partial-domain, supporting near-miss): group index uses ' ,' (space then
# comma) ordering — a wrong separator only inside the index body. Correct on the
# non-group branch; the group branch yields base[m0 ,m1] (wrong) — wait: this is
# built by swapping the join for an explicit wrong-separator fold. We instead
# pin the WRONG separator at the tuple-render group: a trailing extra ')'.
# (Cheap supporting case; still carries a real refinement.)
_R_TUPLE_EXTRA = _swap(
    _BASE, _TUPLE_GOLD,
    "    if len(elts) > 0:\n"
    "        body = join_comma(elts)  # type: PSeq[int]\n"
    "        result = ((PSeq(40) + body) + PSeq(41)) + PSeq(41)  # WRONG: extra ')'\n"
    "    else:\n"
    "        result = PSeq(40, 41)\n"
    "    return result\n",
)


SPEC_TESTS = [
    # --- positive controls (soundness) ---
    {
        "id": "pos-tuple-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_TUPLE,
        "rationale": "tuple_render with branches reordered (empty-first) and the "
                     "wrapped join built inline must verify; join_comma(elts) is "
                     "used exactly as the spec uses it so no extra lemma is needed. "
                     "If it cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-tuple-cheapest",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_TUPLE_CHEAPEST,
        "rationale": "the cheapest honest impl returns '(' + join_comma(elts) + ')' "
                     "inline. Covers the (N/A) ungrounded-oracle lane: the oracle is "
                     "grounded, so the cheapest faithful impl is correct and MUST verify.",
    },
    {
        "id": "pos-subscript-prefix",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_SUBSCRIPT,
        "rationale": "subscript_render with the non-group branch handled first and a "
                     "precomputed `value + '['` prefix local must verify (same value, "
                     "different shape). Else SPEC-TOO-STRONG.",
    },
    # --- admissibility ---
    {
        "id": "admiss-subscript-precond",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "a positive-control caller invokes subscript_render with an "
                     "in-domain F2P/P2P-shaped input (group=True with non-empty elts, "
                     "and group=False), establishing Implies(group, len(elts)>0). If "
                     "the Requires could not be established for a legitimate input the "
                     "call would not verify => PRECOND-TOO-STRONG.",
    },
    # --- uniqueness / partial-domain rivals (must be REJECTED) ---
    {
        "id": "rival-tuple-bare-join",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_TUPLE_BARE,
        "refinement": "This is the literal pre-patch bug (model_prepatch.py): a "
                      "non-empty tuple renders as the bare join `1, 2, 3` with no "
                      "round brackets. Its faithful real patch is the unchanged "
                      "pre-patch visit_Tuple, which FAILS the F2P test "
                      "test_unparse[(1, 2, 3)-(1, 2, 3)] (it produces `1, 2, 3`). "
                      "So if it verified, that would be verify-without-resolve.",
        "rationale": "rejected by tuple_render's non-empty postcondition clause "
                     "Implies(len>0, Result == '(' + join_comma(elts) + ')').",
    },
    {
        "id": "rival-tuple-empty-open",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_TUPLE_EMPTY,
        "refinement": "Correct on every non-empty tuple but renders the empty tuple "
                      "as '(' instead of '()'. Its faithful real patch (visit_Tuple "
                      "else-branch returning '(') would FAIL the P2P test "
                      "test_unparse[()-()]. A partial-domain rival pinning only the "
                      "non-empty half of the domain.",
        "rationale": "rejected by tuple_render's empty postcondition clause "
                     "Implies(len==0, Result == PSeq(40,41)).",
    },
    {
        "id": "rival-subscript-inner-parens",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_SUB_PARENS,
        "refinement": "This is the coupling pre-patch bug (model_prepatch_2.py): a "
                      "simple-tuple index renders as base[(m0, m1)] (inner round "
                      "brackets) instead of base[m0, m1]. Its faithful real patch is "
                      "the pre-patch visit_Subscript which — once site 1 parenthesises "
                      "tuples — renders Tuple[(int, int)] and FAILS the P2P test "
                      "test_unparse[Tuple[int, int]-Tuple[int, int]]. verify-without-resolve.",
        "rationale": "rejected by subscript_render's group-branch postcondition "
                     "Implies(group, Result == value '[' join_comma(elts) ']').",
    },
    {
        "id": "rival-subscript-drop-body",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_SUB_DROP,
        "refinement": "Correct on the simple-tuple index branch but a non-group index "
                      "drops its body, rendering base[] instead of base[body]. Its "
                      "faithful real patch would FAIL every P2P unparse row whose "
                      "subscript index is not a simple tuple (e.g. a single-element "
                      "Tuple[int] / generic single-arg subscripts) by emitting an empty "
                      "index. A partial-domain rival pinning only the group half.",
        "rationale": "rejected by subscript_render's non-group postcondition clause "
                     "Implies(not group, Result == value '[' slice_rendered ']').",
    },
    {
        "id": "rival-tuple-extra-paren",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_TUPLE_EXTRA,
        "refinement": "Cheap supporting near-miss: a non-empty tuple gains a redundant "
                      "trailing ')'. Its faithful real patch would render '(1, 2, 3))' "
                      "and FAIL the F2P test. Carries a real refinement (it does not "
                      "resolve) and confirms the postcondition is an EXACT equality, "
                      "not a prefix/containment check.",
        "rationale": "rejected by tuple_render's non-empty postcondition: the exact "
                     "structural equality has one closing ')' (PSeq(41)), not two.",
    },
]


# No @ContractOnly axioms and no A-reference deep model consumed AS AN AXIOM:
# meta.axioms == []. join_comma is a deep model validated == ', '.join out-of-band
# by axiom_check.py (G-AX), which the PBT axiom lane would only duplicate. The
# join is grounded in the input and total, so there is no caller-reachable input
# outside any axiom domain (there is no axiom). AXIOM_TESTS therefore empty.
AXIOM_TESTS = []
