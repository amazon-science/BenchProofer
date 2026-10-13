# properties.py — PBT manifest for sympy__sympy-15976. NOT a Nagini module; a
# record of adversarial cases the runner (swebench_nagini.pbt) parses. Each SPEC
# case is a full model.py variant that SHARES the frozen spec byte-for-byte (only
# the # impl-start/# impl-end region is edited via _swap) and is checked by Nagini
# verify + same_spec. There are no @ContractOnly axioms in this bundle
# (meta.axioms == []; the structural choice is modelled deeply and validated by
# axiom_check.py / G-AX as an A-reference), so AXIOM_TESTS == [].
#
# Defended surface (what print_symbol's postcondition actually pins):
#   (P1) Acc(node_pred(Result()))                                  result owned
#   (P2) node_tag(Result())   == root_tag_for(has_subs, has_supers)        root kind
#   (P3) node_ctags(Result()) == child_tags_for(has_subs, has_supers,
#                                               subs_multi, supers_multi)  direct kids
#   (P4) node_bold(Result())  == bold                              bold-on-root marker
#   (P5) Requires(MustTerminate(2))                    TOTALITY of the rendering
#   read-only input: name : List[int] at Acc(list_pred(name), 1/2),
#                    re-ensured at 1/2  ->  FRAME-MUTATION surface.
# (P5) makes (P1)-(P4) obligations on EVERY invocation rather than only on the
# invocations that reach a return. Without it Nagini proves PARTIAL correctness
# and a rival that never yields a tree discharges (P1)-(P4) vacuously — the
# NON-PRODUCTION family in the reject lane below (self-delegation, diverging
# loop after a wrong build, unbounded countdown after a correct build). Those
# rivals never yield a tree, so their faithful patches hang or blow the stack and
# cannot resolve; (P5) is the only clause that rejects them, because they do not
# contradict (P2)-(P4) — they simply never reach the point of being judged by
# them. The paired accept-lane case pos-control-measured-loop brackets (P5) from
# the other side: a correct impl that assembles the child list with a real loop
# carrying a measure still verifies, so totality is not a covert ban on loops.
# (P2)/(P3) are pinned to FULLY-GROUNDED @Pure oracles (root_tag_for /
# child_tags_for / sub_group_tag / sup_group_tag are total functions of the flag
# args, no opaque
# answer-key), so there is NO wrong-echo: echoing root_tag_for(...) IS the
# correct answer. The uniqueness attacks are therefore PARTIAL-DOMAIN rivals that
# get the cheap branches right but diverge on one sub-domain that the gold patch /
# F2P test_presentation_symbol pins exactly.

from pathlib import Path

INSTANCE = "sympy__sympy-15976"
FLOAT_ENCODING = None   # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The gold impl body (everything strictly BETWEEN "# impl-start" and
# "# impl-end"). We swap on this exact block so every edit stays inside the impl
# region and the frozen spec (axioms/pure/pre/post) is never touched.
# ---------------------------------------------------------------------------
_GOLD_IMPL = '''    x = None  # type: Optional[MNode]
    sub_g = sub_group_tag(subs_multi)
    sup_g = sup_group_tag(supers_multi)
    if not has_supers:
        if not has_subs:
            # bare identifier: the name is its own text content, no element child
            kids = []  # type: List[int]
            x = MNode(TAG_MI, kids)
        else:
            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
            x = MNode(TAG_MSUB, kids)
    else:
        if not has_subs:
            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
            x = MNode(TAG_MSUP, kids)
        else:
            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
            x = MNode(TAG_MSUBSUP, kids)
    # Set the bold marker on the produced root (touches only the marker; the
    # element kind and child kinds are unchanged).
    ct = node_ctags(x)
    tg = node_tag(x)
    Unfold(node_pred(x))
    x.bold = bold
    Fold(node_pred(x))
    Assert(node_ctags(x) == ct)
    Assert(node_tag(x) == tg)
    return x'''

assert _GOLD_IMPL in _BASE, "gold impl block drifted from model.py"


def _impl(body):
    """Return a full model.py variant whose impl region is `body`."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = [

    # -------------------------------------------------------------------
    # 1. POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT.
    #    The gold walks the four branches top-down (supers-outer). This
    #    variant computes the root tag / child list from a flat branch order
    #    rerooted on has_subs first, and builds `kids` by appending instead
    #    of literal lists. No framing lemma is dropped: the bold mutation
    #    keeps the gold ct/tg pins. It MUST verify (else SPEC-TOO-STRONG:
    #    the spec would reject a faithful re-shaping of the gold build).
    # -------------------------------------------------------------------
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl('''    sub_g = sub_group_tag(subs_multi)
    sup_g = sup_group_tag(supers_multi)
    kids = []  # type: List[int]
    root = TAG_MI
    # Branch on subscripts first (gold branches on supers first): a structural
    # reorder that lands on the identical (root, kids) per root_tag_for /
    # child_tags_for.
    if has_subs:
        kids.append(TAG_MNAME)
        kids.append(sub_g)
        if has_supers:
            kids.append(sup_g)
            root = TAG_MSUBSUP
        else:
            root = TAG_MSUB
    else:
        if has_supers:
            kids.append(TAG_MNAME)
            kids.append(sup_g)
            root = TAG_MSUP
        else:
            root = TAG_MI            # bare identifier: no element child
    x = MNode(root, kids)
    ct = node_ctags(x)
    tg = node_tag(x)
    Unfold(node_pred(x))
    x.bold = bold
    Fold(node_pred(x))
    Assert(node_ctags(x) == ct)
    Assert(node_tag(x) == tg)
    return x'''),
        "rationale": "a correct but structurally-reordered impl (branch on "
                     "has_subs first, append-built kids) must verify; the gold "
                     "ct/tg framing asserts around the bold write are kept so no "
                     "proof obligation is dropped. Failure => SPEC-TOO-STRONG.",
    },

    # -------------------------------------------------------------------
    # 2. ADMISSIBILITY — the precondition admits a normal F2P-shaped input and
    #    the four postcondition clauses are JOINTLY SATISFIABLE on it.
    #    test_presentation_symbol pins x_2 (subs only, single part) ->
    #    msub[mi, mi]. We witness that class in-region: a fresh name list at
    #    full permission meets the read-only fractional Requires, and a tree
    #    carrying the required root kind / ordered children / marker is actually
    #    CONSTRUCTIBLE in bounded time. MUST verify (else PRECOND-TOO-STRONG).
    #    Note this witness is built directly rather than via a self-call: the
    #    totality obligation (P5) puts the callee's level at or above the
    #    caller's for a self-call, so a self-delegating witness is (correctly)
    #    unprovable — see the non-production reject cases below. Building the
    #    witness inline is the stronger check anyway: it exhibits an actual
    #    satisfying tree instead of appealing to the method's own contract,
    #    which is what makes it non-vacuous (Assert(False) in this block fails).
    # -------------------------------------------------------------------
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl('''    x = None  # type: Optional[MNode]
    sub_g = sub_group_tag(subs_multi)
    sup_g = sup_group_tag(supers_multi)
    if not has_supers:
        if not has_subs:
            kids = []  # type: List[int]
            x = MNode(TAG_MI, kids)
        else:
            kids = [TAG_MNAME, sub_g]
            x = MNode(TAG_MSUB, kids)
    else:
        if not has_subs:
            kids = [TAG_MNAME, sup_g]
            x = MNode(TAG_MSUP, kids)
        else:
            kids = [TAG_MNAME, sub_g, sup_g]
            x = MNode(TAG_MSUBSUP, kids)
    ct = node_ctags(x)
    tg = node_tag(x)
    Unfold(node_pred(x))
    x.bold = bold
    Fold(node_pred(x))
    Assert(node_ctags(x) == ct)
    Assert(node_tag(x) == tg)
    # Admissibility: a representative F2P input (x_2: subs only, single part)
    # is in-domain — a fresh empty name list at full permission is a legitimate
    # read-only argument — and the whole postcondition is satisfiable there.
    probe = []  # type: List[int]
    Assert(Acc(list_pred(probe), 1 / 2))
    wkids = [TAG_MNAME, sub_group_tag(False)]  # type: List[int]
    w = MNode(root_tag_for(True, False), wkids)
    Unfold(node_pred(w))
    w.bold = True
    Fold(node_pred(w))
    Assert(node_tag(w) == root_tag_for(True, False))
    Assert(node_tag(w) == TAG_MSUB)
    Assert(node_ctags(w) == child_tags_for(True, False, False, False))
    Assert(node_bold(w) == True)
    return x'''),
        "rationale": "the precondition Acc(list_pred(name),1/2) must accept a "
                     "normal F2P-shaped input (x_2 -> msub) and the four "
                     "clauses must be jointly satisfiable on it — witnessed by "
                     "an actually-constructed msub[mname, sub-one] tree with the "
                     "marker set, reached in bounded time. Failure => "
                     "PRECOND-TOO-STRONG (or a vacuously-False Requires).",
    },

    # -------------------------------------------------------------------
    # 3. FRAME-MUTATION (MANDATORY: name is read-only at Acc(list_pred,1/2)).
    #    A rival that WRITES to the read-only `name` list. There is no honest
    #    reason to mutate the name (the structural choice is abstracted to the
    #    flags), so a real patch doing this would be a behaviour-changing edit
    #    to a read-only argument — it cannot resolve. The spec MUST reject for
    #    INSUFFICIENT PERMISSION (write needs full list_pred(name), only 1/2
    #    held). All gold invariants are kept verbatim so the rejection is
    #    attributable solely to the write.
    # -------------------------------------------------------------------
    {
        "id": "frame-mutate-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl('''    x = None  # type: Optional[MNode]
    sub_g = sub_group_tag(subs_multi)
    sup_g = sup_group_tag(supers_multi)
    # FRAME VIOLATION: append to the read-only `name` list. Only Acc(...,1/2)
    # is held, so this write cannot be justified -> insufficient permission.
    name.append(0)
    if not has_supers:
        if not has_subs:
            kids = []  # type: List[int]
            x = MNode(TAG_MI, kids)
        else:
            kids = [TAG_MNAME, sub_g]
            x = MNode(TAG_MSUB, kids)
    else:
        if not has_subs:
            kids = [TAG_MNAME, sup_g]
            x = MNode(TAG_MSUP, kids)
        else:
            kids = [TAG_MNAME, sub_g, sup_g]
            x = MNode(TAG_MSUBSUP, kids)
    ct = node_ctags(x)
    tg = node_tag(x)
    Unfold(node_pred(x))
    x.bold = bold
    Fold(node_pred(x))
    Assert(node_ctags(x) == ct)
    Assert(node_tag(x) == tg)
    return x'''),
        "refinement": "a faithful patch that mutates sym.name's backing list "
                      "would corrupt the read-only symbol name (split_super_sub "
                      "consumes name unchanged across the patch); the gold fix "
                      "only removes the outer <mi> wrapper and never writes the "
                      "name, so any name-mutating real patch diverges from gold "
                      "and would not resolve test_presentation_symbol / P2P.",
        "rationale": "rejection comes from the PERMISSION SYSTEM: `name` is held "
                     "at Acc(list_pred(name),1/2) (read-only); list.append needs "
                     "full permission. The gold postcondition re-ensures the same "
                     "1/2 perm, so the write is unjustifiable.",
    },

    # -------------------------------------------------------------------
    # 4. PARTIAL-DOMAIN: bare-identifier branch reverts to the PRE-PATCH bug.
    #    Correct on every sub/super branch, but on the bare-identifier domain
    #    (no subs, no supers — F2P "x", "alpha") this rival is identical to the
    #    gold; the divergence is engineered on the SUBS-ONLY domain instead:
    #    it keeps the root mi but moves the structural element inside. This is
    #    exactly the pre-patch skeleton on one branch. MUST be rejected by (P2)
    #    node_tag == root_tag_for (mi != msub).
    # -------------------------------------------------------------------
    {
        "id": "partial-domain-subs-prepatch-root",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl('''    x = None  # type: Optional[MNode]
    sub_g = sub_group_tag(subs_multi)
    sup_g = sup_group_tag(supers_multi)
    if not has_supers:
        if not has_subs:
            kids = []  # type: List[int]
            x = MNode(TAG_MI, kids)
        else:
            # PARTIAL-DOMAIN DIVERGENCE (subs-only): the PRE-PATCH bug -> root
            # stays an <mi> wrapping the structural msub as its single child.
            kids = [TAG_MSUB]
            x = MNode(TAG_MI, kids)
    else:
        if not has_subs:
            kids = [TAG_MNAME, sup_g]
            x = MNode(TAG_MSUP, kids)
        else:
            kids = [TAG_MNAME, sub_g, sup_g]
            x = MNode(TAG_MSUBSUP, kids)
    ct = node_ctags(x)
    tg = node_tag(x)
    Unfold(node_pred(x))
    x.bold = bold
    Fold(node_pred(x))
    Assert(node_ctags(x) == ct)
    Assert(node_tag(x) == tg)
    return x'''),
        "refinement": "this IS the pre-patch behaviour on the subs-only domain "
                      "(outer <mi> wrapping the msub) — exactly the regression "
                      "F2P test_presentation_symbol catches: it expects the root "
                      "nodeName 'msub' with children [mi, mi] for x_2, but this "
                      "yields root 'mi' with a single 'msub' child. A real patch "
                      "doing this would fail test_presentation_symbol => not "
                      "resolved.",
        "rationale": "rejection from postcondition (P2) node_tag(Result()) == "
                     "root_tag_for(True, False) == TAG_MSUB, but this returns "
                     "TAG_MI; and independently (P3) child_tags_for == [mi, "
                     "group] != [msub].",
    },

    # -------------------------------------------------------------------
    # 5. PARTIAL-DOMAIN: group-kind collapse on the MULTI sub-domain.
    #    Renders every group as a bare identifier (ignores subs_multi /
    #    supers_multi), so on single-part groups it matches gold but on a
    #    MULTI-part group (F2P "x_2_a" -> msub[mi, mrow], "x^2^a" ->
    #    msup[mi, mrow]) it produces [mi, mi] instead of [mi, mrow]. MUST be
    #    rejected by (P3) node_ctags == child_tags_for.
    # -------------------------------------------------------------------
    {
        "id": "partial-domain-group-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl('''    x = None  # type: Optional[MNode]
    # GROUP-KIND COLLAPSE: always emit the SINGLE-part code for each group,
    # dropping the multi-part mrow distinction (ignores subs_multi /
    # supers_multi).
    sub_g = TAG_SUB_ONE
    sup_g = TAG_SUP_ONE
    if not has_supers:
        if not has_subs:
            kids = []  # type: List[int]
            x = MNode(TAG_MI, kids)
        else:
            kids = [TAG_MNAME, sub_g]
            x = MNode(TAG_MSUB, kids)
    else:
        if not has_subs:
            kids = [TAG_MNAME, sup_g]
            x = MNode(TAG_MSUP, kids)
        else:
            kids = [TAG_MNAME, sub_g, sup_g]
            x = MNode(TAG_MSUBSUP, kids)
    ct = node_ctags(x)
    tg = node_tag(x)
    Unfold(node_pred(x))
    x.bold = bold
    Fold(node_pred(x))
    Assert(node_ctags(x) == ct)
    Assert(node_tag(x) == tg)
    return x'''),
        "refinement": "this collapses join's mrow-for-many to a bare mi. A real "
                      "patch doing this would render a multi-part subscript "
                      "(x_2_a, x^2^a) as a single <mi> instead of the <mrow> the "
                      "unchanged join produces and test_presentation_symbol pins "
                      "(it asserts childNodes[1].nodeName == 'mrow') => not "
                      "resolved.",
        "rationale": "rejection from postcondition (P3) node_ctags(Result()) == "
                     "child_tags_for(...): for subs_multi=True it requires "
                     "[TAG_MNAME, sub_group_tag(True)==TAG_SUB_ROW] but this "
                     "returns [TAG_MNAME, TAG_SUB_ONE].",
    },

    # -------------------------------------------------------------------
    # 6. PARTIAL-DOMAIN / value-double-mask: swap sub/super child ORDER on the
    #    combined (msubsup) domain. Correct root tag, correct child KINDS as a
    #    multiset on the single-part case (both groups are mi) — but on a name
    #    whose groups differ in kind (one single -> mi, one multi -> mrow) the
    #    order matters: gold pins [mi, subs-group, supers-group]. This rival
    #    appends supers before subs. MUST be rejected by (P3) sequence equality.
    # -------------------------------------------------------------------
    {
        "id": "partial-domain-combined-order-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl('''    x = None  # type: Optional[MNode]
    sub_g = sub_group_tag(subs_multi)
    sup_g = sup_group_tag(supers_multi)
    if not has_supers:
        if not has_subs:
            kids = []  # type: List[int]
            x = MNode(TAG_MI, kids)
        else:
            kids = [TAG_MNAME, sub_g]
            x = MNode(TAG_MSUB, kids)
    else:
        if not has_subs:
            kids = [TAG_MNAME, sup_g]
            x = MNode(TAG_MSUP, kids)
        else:
            # ORDER SWAP (combined kind): gold appends subs-group then
            # supers-group; this swaps them.
            kids = [TAG_MNAME, sup_g, sub_g]
            x = MNode(TAG_MSUBSUP, kids)
    ct = node_ctags(x)
    tg = node_tag(x)
    Unfold(node_pred(x))
    x.bold = bold
    Fold(node_pred(x))
    Assert(node_ctags(x) == ct)
    Assert(node_tag(x) == tg)
    return x'''),
        "refinement": "msubsup is positional: childNodes[1] is the subscript, "
                      "childNodes[2] the superscript. Gold appends join(subs) "
                      "before join(supers). A patch that swaps them would, on a "
                      "name like x__3_2 / x^3_2 where one group is multi (mrow) "
                      "and the other single (mi), place the wrong group in the "
                      "subscript/superscript slot — a visibly different DOM tree "
                      "that test_presentation_symbol's ordered childNodes check "
                      "rejects => not resolved.",
        "rationale": "rejection from postcondition (P3) node_ctags(Result()) == "
                     "child_tags_for(...) which is the ORDERED PSeq [TAG_MNAME, "
                     "sub_group_tag(subs_multi), sup_group_tag(supers_multi)]; "
                     "this returns the sequence with the last two swapped. Each "
                     "group's code names the part list it renders, so the "
                     "swapped sequence is unequal for EVERY multiplicity "
                     "combination, including both-single and both-multi.",
    },

    # -------------------------------------------------------------------
    # 7. PARTIAL-DOMAIN / bold drop on the bold sub-domain. Sets the bold
    #    marker only when there ARE sub/superscripts (skips it for the bare
    #    identifier). P2P test_print_matrix_symbol exercises the bold path; a
    #    bare bold symbol would lose its mathvariant. MUST be rejected by (P4)
    #    node_bold == bold on the bare-identifier domain.
    # -------------------------------------------------------------------
    {
        "id": "partial-domain-bold-drop-bare",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl('''    x = None  # type: Optional[MNode]
    sub_g = sub_group_tag(subs_multi)
    sup_g = sup_group_tag(supers_multi)
    eff_bold = bold
    if not has_supers:
        if not has_subs:
            kids = []  # type: List[int]
            x = MNode(TAG_MI, kids)
            # BOLD DROP on the bare-identifier domain: silently ignore bold.
            eff_bold = False
        else:
            kids = [TAG_MNAME, sub_g]
            x = MNode(TAG_MSUB, kids)
    else:
        if not has_subs:
            kids = [TAG_MNAME, sup_g]
            x = MNode(TAG_MSUP, kids)
        else:
            kids = [TAG_MNAME, sub_g, sup_g]
            x = MNode(TAG_MSUBSUP, kids)
    ct = node_ctags(x)
    tg = node_tag(x)
    Unfold(node_pred(x))
    x.bold = eff_bold
    Fold(node_pred(x))
    Assert(node_ctags(x) == ct)
    Assert(node_tag(x) == tg)
    return x'''),
        "refinement": "the gold moves the bold setAttribute to the END onto the "
                      "produced root for EVERY kind, including a bare identifier. "
                      "A patch that only sets bold when sub/superscripts exist "
                      "would drop mathvariant='bold' on a plain bold symbol — "
                      "the bold-on-root path P2P test_print_matrix_symbol / the "
                      "bold cases in test_presentation_symbol observe => not "
                      "resolved.",
        "rationale": "rejection from postcondition (P4) node_bold(Result()) == "
                     "bold; on the bare-identifier domain with bold=True this "
                     "returns node_bold == False != True.",
    },

    # -------------------------------------------------------------------
    # 8. PARTIAL-DOMAIN / SAME-KIND slot swap on the combined domain. The
    #    sharpest rival: it swaps the subscript and superscript group slots
    #    ONLY where the two groups take the SAME element kind (both one-part,
    #    or both several-part), so every child's element kind and the whole
    #    ordered kind-multiset are indistinguishable from gold — only the ROLE
    #    filling each slot differs. Case 6 above swaps unconditionally and is
    #    caught on the differing-multiplicity domain by element kind alone;
    #    this one is invisible to any observation that records element kind
    #    without role, which is exactly the sub-domain F2P
    #    test_presentation_symbol pins for x^3_2 / x__3_2 (both scripts single
    #    part). MUST be rejected by (P3) node_ctags == child_tags_for.
    # -------------------------------------------------------------------
    {
        "id": "partial-domain-samekind-slot-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl('''    x = None  # type: Optional[MNode]
    sub_g = sub_group_tag(subs_multi)
    sup_g = sup_group_tag(supers_multi)
    if not has_supers:
        if not has_subs:
            kids = []  # type: List[int]
            x = MNode(TAG_MI, kids)
        else:
            kids = [TAG_MNAME, sub_g]
            x = MNode(TAG_MSUB, kids)
    else:
        if not has_subs:
            kids = [TAG_MNAME, sup_g]
            x = MNode(TAG_MSUP, kids)
        else:
            # SAME-KIND SLOT SWAP: only where both groups render to the same
            # element kind, put the superscript group in the subscript slot and
            # vice versa. Element kinds and their order are then identical to
            # gold; only which part list each slot renders differs.
            if subs_multi == supers_multi:
                kids = [TAG_MNAME, sup_g, sub_g]
            else:
                kids = [TAG_MNAME, sub_g, sup_g]
            x = MNode(TAG_MSUBSUP, kids)
    ct = node_ctags(x)
    tg = node_tag(x)
    Unfold(node_pred(x))
    x.bold = bold
    Fold(node_pred(x))
    Assert(node_ctags(x) == ct)
    Assert(node_tag(x) == tg)
    return x'''),
        "refinement": "msubsup is positional: childNodes[1] renders the "
                      "subscript parts and childNodes[2] the superscript parts. "
                      "Gold appends join(subs) before join(supers) "
                      "unconditionally. A patch swapping them on the same-kind "
                      "domain renders x^3_2 (subs=['2'], supers=['3'], both "
                      "single) as msubsup[mi'x', mi'3', mi'2'] — every nodeName "
                      "matches gold, but F2P test_presentation_symbol asserts "
                      "childNodes[1].childNodes[0].nodeValue == '2' and "
                      "childNodes[2].childNodes[0].nodeValue == '3', so the "
                      "subscript and superscript render transposed => not "
                      "resolved. The same holds for x^3^b_2_a on the both-multi "
                      "domain.",
        "rationale": "rejection from postcondition (P3) node_ctags(Result()) == "
                     "child_tags_for(...), the ORDERED PSeq [TAG_MNAME, "
                     "sub_group_tag(subs_multi), sup_group_tag(supers_multi)]. "
                     "Because each group's code names the part list it renders "
                     "rather than only the element kind it takes, the two group "
                     "slots carry DISTINCT codes for every multiplicity "
                     "combination (TAG_SUB_ONE != TAG_SUP_ONE and TAG_SUB_ROW != "
                     "TAG_SUP_ROW), so the swapped sequence is unequal even on "
                     "the same-kind domain where an element-kind-only "
                     "observation would see no difference.",
    },

    # -------------------------------------------------------------------
    # 9. NON-PRODUCTION / self-delegation. Produces NO tree at all: it hands the
    #    same arguments straight back to the renderer and returns whatever comes
    #    out. Every structural clause (P1)-(P4) is discharged verbatim by the
    #    callee's own contract, so this rival is invisible to any amount of
    #    strengthening of (P2)/(P3)/(P4) — it never contradicts them, it just
    #    never does the work. MUST be rejected by (P5): a self-call cannot sit
    #    strictly below the caller's own termination level.
    # -------------------------------------------------------------------
    {
        "id": "nonproduction-self-delegation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl('''    # NON-PRODUCTION: delegate to the renderer itself and return its answer.
    # Constructs nothing; the callee contract discharges every structural clause.
    r = print_symbol(name, has_subs, has_supers, subs_multi, supers_multi, bold)
    return r'''),
        "refinement": "the faithful patch is `return self._print_Symbol(sym, "
                      "style=style)` as the whole body — unbounded recursion. "
                      "Every presentation-MathML render of any Symbol raises "
                      "RecursionError, so F2P test_presentation_symbol errors "
                      "and the bulk of the presentation P2P suite errors with "
                      "it => not resolved. It renders no markup whatsoever, so "
                      "it is wrong on the entire domain, not on a sub-domain.",
        "rationale": "rejection from (P5) Requires(MustTerminate(2)): the "
                     "self-call would need a level strictly below the caller's "
                     "own, which an identical signature cannot supply — Nagini "
                     "reports 'Obligation leak check failed. Callee "
                     "print_symbol might not take all unsatisfied obligations "
                     "from the caller.' No structural clause is violated, which "
                     "is exactly why the totality obligation is the only thing "
                     "that can reject it.",
    },

    # -------------------------------------------------------------------
    # 10. NON-PRODUCTION / diverging loop AFTER a wrong build. This is the
    #     sharpest of the family: it builds the PRE-PATCH tree (root always an
    #     identifier wrapping the structural element — the exact reported bug),
    #     then spins forever so the post-loop state is infeasible and the wrong
    #     construction is never observed at the return. Strengthening the
    #     structural clauses cannot touch it: the clauses ARE violated by the
    #     tree it builds, but the violation sits behind an unreachable return.
    #     MUST be rejected by (P5).
    # -------------------------------------------------------------------
    {
        "id": "nonproduction-diverge-after-wrong-build",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl('''    x = None  # type: Optional[MNode]
    kids = []  # type: List[int]
    if not has_supers:
        if not has_subs:
            pass
        else:
            kids = [TAG_MSUB]
    else:
        if not has_subs:
            kids = [TAG_MSUP]
        else:
            kids = [TAG_MSUBSUP]
    x = MNode(TAG_MI, kids)          # PRE-PATCH wrong root
    ct = node_ctags(x)
    tg = node_tag(x)
    Unfold(node_pred(x))
    x.bold = bold
    Fold(node_pred(x))
    Assert(node_ctags(x) == ct)
    Assert(node_tag(x) == tg)
    # NON-PRODUCTION: spin forever, so the return below is never reached and the
    # wrong tree above is never observed against the postcondition.
    spin = 0
    while spin >= 0:
        Invariant(spin >= 0)
        Invariant(Acc(node_pred(x)))
        Invariant(Acc(list_pred(name), 1 / 2))
        spin = spin + 1
    return x'''),
        "refinement": "the faithful patch keeps the pre-patch outer identifier "
                      "wrapper AND adds a non-terminating loop before the "
                      "return, so every presentation render hangs. F2P "
                      "test_presentation_symbol never completes and the "
                      "presentation P2P tests hang with it => not resolved. It "
                      "is doubly wrong: the tree is the reported bug and the "
                      "renderer never returns it.",
        "rationale": "rejection from (P5): Nagini reports 'Obligation leak "
                     "check failed. Loop might not take all unsatisfied "
                     "obligations from the context' — the loop carries no "
                     "decreasing measure, so it cannot discharge the caller's "
                     "termination obligation. Without (P5) the structural "
                     "clauses are satisfied VACUOUSLY (the return is "
                     "unreachable), which is why (P2)/(P3) alone cannot reject "
                     "this even though the tree it builds violates both.",
    },

    # -------------------------------------------------------------------
    # 11. NON-PRODUCTION / unbounded countdown with a correct build. Builds the
    #     CORRECT tree, then loops on a counter that decreases but has no lower
    #     bound, so it still never terminates. Probes whether (P5) is satisfied
    #     by the mere presence of a decreasing quantity rather than by a
    #     genuine measure. MUST be rejected by (P5).
    # -------------------------------------------------------------------
    {
        "id": "nonproduction-unbounded-countdown",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl('''    x = None  # type: Optional[MNode]
    sub_g = sub_group_tag(subs_multi)
    sup_g = sup_group_tag(supers_multi)
    if not has_supers:
        if not has_subs:
            kids = []  # type: List[int]
            x = MNode(TAG_MI, kids)
        else:
            kids = [TAG_MNAME, sub_g]
            x = MNode(TAG_MSUB, kids)
    else:
        if not has_subs:
            kids = [TAG_MNAME, sup_g]
            x = MNode(TAG_MSUP, kids)
        else:
            kids = [TAG_MNAME, sub_g, sup_g]
            x = MNode(TAG_MSUBSUP, kids)
    ct = node_ctags(x)
    tg = node_tag(x)
    Unfold(node_pred(x))
    x.bold = bold
    Fold(node_pred(x))
    Assert(node_ctags(x) == ct)
    Assert(node_tag(x) == tg)
    # NON-PRODUCTION: the counter strictly DECREASES every pass but is bounded
    # by nothing below, so the loop runs forever and the tree is never yielded.
    down = 0
    while down <= 0:
        Invariant(down <= 0)
        Invariant(Acc(node_pred(x)))
        Invariant(Acc(list_pred(name), 1 / 2))
        down = down - 1
    return x'''),
        "refinement": "the faithful patch builds the right markup and then "
                      "loops forever before returning it, so no presentation "
                      "render ever completes: F2P test_presentation_symbol "
                      "hangs => not resolved. The tree is right and the "
                      "renderer is still wrong, which is precisely the case a "
                      "purely structural specification cannot see.",
        "rationale": "rejection from (P5): a strictly decreasing counter is not "
                     "a measure unless it is bounded below, so the loop cannot "
                     "supply a positive decreasing bound on the remaining "
                     "iterations and the obligation leaks. Confirms (P5) is not "
                     "discharged by the presence of a decreasing quantity "
                     "alone.",
    },

    # -------------------------------------------------------------------
    # 12. SOUNDNESS / second positive control: a CORRECT impl that builds the
    #     child-kind list with a real bounded LOOP rather than a literal, and
    #     discharges the totality obligation with a proper measure. This is the
    #     companion to cases 9-11: those three establish that (P5) rejects
    #     rivals that never yield a tree; this one establishes that (P5) is
    #     nonetheless DISCHARGE-ABLE by a faithful implementation whose control
    #     flow is not straight-line, so the obligation is not a back-door
    #     restriction to loop-free code. It MUST verify (else SPEC-TOO-STRONG:
    #     the totality clause would have outlawed correct implementations
    #     instead of only non-producing ones).
    # -------------------------------------------------------------------
    {
        "id": "pos-control-measured-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl('''    sub_g = sub_group_tag(subs_multi)
    sup_g = sup_group_tag(supers_multi)
    # The required child-kind list for this flag combination, then built up by
    # copying it one slot at a time under a decreasing measure — a correct impl
    # whose control flow is a genuine loop rather than a literal list.
    want = []  # type: List[int]
    root = TAG_MI
    if not has_supers:
        if not has_subs:
            root = TAG_MI
        else:
            want = [TAG_MNAME, sub_g]
            root = TAG_MSUB
    else:
        if not has_subs:
            want = [TAG_MNAME, sup_g]
            root = TAG_MSUP
        else:
            want = [TAG_MNAME, sub_g, sup_g]
            root = TAG_MSUBSUP
    goal = ToSeq(want)  # type: PSeq[int]
    kids = []  # type: List[int]
    i = 0
    n = len(goal)
    while i < n:
        Invariant(Acc(list_pred(want), 1 / 2) and Acc(list_pred(kids)))
        Invariant(Acc(list_pred(name), 1 / 2))
        Invariant(goal == ToSeq(want) and n == len(goal))
        Invariant(0 <= i and i <= n)
        Invariant(ToSeq(kids) == goal.take(i))
        # At most n - i passes remain; i grows by exactly 1 each pass and n is
        # loop-invariant, so the bound strictly decreases, and the + 1 keeps it
        # positive on the final pass (0 remaining).
        Invariant(MustTerminate(n - i + 1))
        kids.append(goal[i])
        Assert(ToSeq(kids) == goal.take(i) + PSeq(goal[i]))
        Assert(goal.take(i) + PSeq(goal[i]) == goal.take(i + 1))
        i = i + 1
    Assert(ToSeq(kids) == goal.take(n))
    Assert(goal.take(n) == goal)
    x = MNode(root, kids)
    ct = node_ctags(x)
    tg = node_tag(x)
    Unfold(node_pred(x))
    x.bold = bold
    Fold(node_pred(x))
    Assert(node_ctags(x) == ct)
    Assert(node_tag(x) == tg)
    return x'''),
        "rationale": "a CORRECT impl whose child list is assembled by a bounded "
                     "loop carrying its own measure must verify. Together with "
                     "cases 9-11 this brackets the totality clause: it rejects "
                     "implementations that never yield a tree, and it does not "
                     "reject implementations that yield the right tree via a "
                     "loop. Failure => SPEC-TOO-STRONG (totality collapsed into "
                     "a straight-line-code requirement).",
    },
]


# ===========================================================================
# AXIOM LANE
# ===========================================================================
# meta.json axioms == []  (no @ContractOnly). The structural choice is modelled
# DEEPLY (root_tag_for / child_tags_for / sub_group_tag / sup_group_tag + the
# verified print_symbol
# builder) and the unchanged callees (split_super_sub, the nested join) are
# A-references validated by axiom_check.py / G-AX, NOT consumed axioms. There is
# therefore no per-axiom Requires-domain to fuzz here. (axiom_check.py already
# runs the real split_super_sub + the fixed _print_Symbol on 13 named F2P + 4000
# fuzz names; that is the G-AX A-reference soundness check, not a PBT axiom case.)
AXIOM_TESTS = []  # type: list
