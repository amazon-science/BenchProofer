# properties.py — PBT falsification battery for django__django-14608. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside the # impl-start/# impl-end region; the runner re-runs the Nagini
# verifier on the host and checks the verify/reject outcome against `expect`.
#
# Defended surface of this instance (read model.py + refinement.md + mapping.md):
#   finish_group_clean(collection, group_flagged, group_message,
#                       rejected, rejection_messages) -> None
#     Requires(Acc(collection.css_class))                 # FULL — the op rewrites it
#     Requires(Acc(collection.items))                     # FULL — the op rewrites it
#     Requires(Acc(list_pred(rejection_messages), 1/2))   # READ-ONLY (half perm)
#     Ensures(... permissions preserved ...)
#     Ensures(Acc(list_pred(collection.css_class)))
#     Ensures(Acc(list_pred(collection.items)))
#     # THE FIX (load-bearing, holds on EVERY outcome):
#     Ensures(ToSeq(collection.css_class) == class_attr(nonform_tag()))
#     # held-items, three disjoint control cases:
#     Ensures(Implies(not rejected and not group_flagged, len(items)==0))
#     Ensures(Implies(not rejected and group_flagged, ToSeq(items)==PSeq(group_message)))
#     Ensures(Implies(rejected, ToSeq(items)==ToSeq(rejection_messages)))
#
#   The deep model class_attr(tag) = generic_class()        if len(tag)==0
#                                  = generic_class()+PSeq(32)+tag  otherwise.
#   With nonform_tag() == 'nonform' this is the code points of 'errorlist nonform'
#   ([101,114,114,111,114,108,105,115,116,32,110,111,110,102,111,114,109]).
#   class_attr / nonform_tag / generic_class are @Pure and FULLY GROUNDED in
#   literals — there is NO @ContractOnly axiom (meta.axioms == []); the only
#   callee is the UNCHANGED ErrorList class-attribute rule, an A-reference
#   validated == class_attr out-of-band by axiom_check.py / G-AX.
#
# Where the spec's strength comes from:
#   * css_class clause: because class_attr(nonform_tag()) fully unfolds to a fixed
#     PSeq of 17 code points, ANY impl that leaves css_class as the bare
#     'errorlist' (the pre-patch bug) — on EITHER the accepted or the rejected
#     path — fails ToSeq(collection.css_class) == class_attr(nonform_tag()).
#     This is exactly what model_prepatch.py / model_prepatch_2.py reproduce.
#   * items clauses: three disjoint Implies pin the held messages on every path:
#     accepted+unflagged -> empty; accepted+flagged -> the single group_message;
#     rejected -> exactly the rejection_messages (rebuild replaces any earlier
#     group-wide message). Dropping the group_flagged append, or dropping the
#     rejection rebuild, or copying the wrong elements, fails one of these.
#   * permission: rejection_messages is held at Acc(...,1/2) (READ-ONLY). Any
#     impl that WRITES to it (append / index-store) is rejected for INSUFFICIENT
#     PERMISSION — the mandatory frame-mutation probe.
#
# Ungrounded-oracle note: the postcondition is pinned to class_attr(nonform_tag())
# which is a @Pure function of NO inputs that fully unfolds to a literal PSeq;
# there is no opaque answer-key an impl could echo without doing the work — the
# cheapest impl that satisfies the clause IS the honest one (write those exact
# code points). So there is no "wrong echo" attack; instead the soundness lane
# carries honest positive controls (structurally-different correct impls). See
# 'assessment' in the returned verdict.
from pathlib import Path

INSTANCE = "django__django-14608"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact frozen impl region (verbatim from model.py lines 116-147). We only ever
# replace text BETWEEN # impl-start / # impl-end, guaranteeing same_spec.
# ---------------------------------------------------------------------------
_IMPL_OLD = """    # impl-start
    # init site: rebuild the collection empty, with the marker tag.
    empty = []  # type: List[int]
    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
    collection.css_class = init_class
    collection.items = empty
    if group_flagged:
        # a single group-wide message is appended to the collection before the
        # rejection check (the collection is NOT rebuilt here, so the marker
        # class set at the init site is preserved).
        collection.items = collection.items + [group_message]
    if rejected:
        # rejection site: rebuild the collection from the rejection messages,
        # again with the marker tag (this replaces any earlier group-wide
        # message held in the collection).
        items_copy = []  # type: List[int]
        i = 0
        while i < len(rejection_messages):
            # invariants-start
            Invariant(Acc(list_pred(rejection_messages), 1 / 2))
            Invariant(Acc(list_pred(items_copy)))
            Invariant(0 <= i and i <= len(rejection_messages))
            Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
            # invariants-end
            items_copy = items_copy + [rejection_messages[i]]
            i = i + 1
        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
        collection.css_class = rej_class
        collection.items = items_copy
    # impl-end"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1


# ===========================================================================
# POSITIVE CONTROL (soundness) — structurally-DIFFERENT but CORRECT impls that
# MUST verify (else SPEC-TOO-STRONG). Each keeps every gold proof obligation it
# still needs (the loop's take()-fold invariants around the forward append) and
# only reshapes the executable form (branch order / build the css_class via
# generic_class concatenation / use class_attr literal). Pilot pitfalls #2/#3
# avoided: the rejection loop is left front-take/forward-append identical to the
# gold proof, so no new fold lemma is needed.
# ===========================================================================

# pos-control-build-from-concat: instead of the spelled-out 17-element literal,
# build the marker class by concatenating the 'errorlist', space, 'nonform'
# code-point lists at BOTH sites. ToSeq of this list equals
# generic_class() + PSeq(32) + nonform_tag() == class_attr(nonform_tag()), so the
# css_class clause still holds; items handling is identical. A correct impl that
# constructs the class compositionally rather than as one literal must verify.
_POS_CONCAT = """    # impl-start
    # init site: build 'errorlist nonform' compositionally (generic + ' ' + tag).
    empty = []  # type: List[int]
    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116] + [32] + \\
                 [110, 111, 110, 102, 111, 114, 109]  # 'errorlist'+' '+'nonform'
    collection.css_class = init_class
    collection.items = empty
    if group_flagged:
        collection.items = collection.items + [group_message]
    if rejected:
        items_copy = []  # type: List[int]
        i = 0
        while i < len(rejection_messages):
            Invariant(Acc(list_pred(rejection_messages), 1 / 2))
            Invariant(Acc(list_pred(items_copy)))
            Invariant(0 <= i and i <= len(rejection_messages))
            Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
            items_copy = items_copy + [rejection_messages[i]]
            i = i + 1
        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116] + [32] + \\
                    [110, 111, 110, 102, 111, 114, 109]
        collection.css_class = rej_class
        collection.items = items_copy
    # impl-end"""

# pos-control-reorder-rejected-first: handle the rejected case FIRST (early in
# the impl), then the accepted/flagged case in the else branch. Behaviourally
# identical: on rejected we rebuild from rejection_messages with the marker; on
# not-rejected we set empty/flagged with the marker. Branch reorder only — keeps
# the loop and its take-fold invariants. Must verify (else SPEC-TOO-STRONG).
_POS_REORDER = """    # impl-start
    if rejected:
        # rejection site first: rebuild from the rejection messages with marker.
        items_copy = []  # type: List[int]
        i = 0
        while i < len(rejection_messages):
            Invariant(Acc(list_pred(rejection_messages), 1 / 2))
            Invariant(Acc(list_pred(items_copy)))
            Invariant(0 <= i and i <= len(rejection_messages))
            Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
            items_copy = items_copy + [rejection_messages[i]]
            i = i + 1
        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
        collection.css_class = rej_class
        collection.items = items_copy
    else:
        # accepted path: marker class, then empty or the single group message.
        acc_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
        collection.css_class = acc_class
        if group_flagged:
            single = [group_message]  # type: List[int]
            collection.items = single
        else:
            empty = []  # type: List[int]
            collection.items = empty
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the precondition admits a normal F2P-shaped
# input (else PRECOND-TOO-STRONG). We cannot add a module-level caller (that
# changes the spec view and breaks same_spec); instead we inject the
# admissibility witness INSIDE the impl region (elided from the spec view) as a
# leading block that constructs a fresh F2P-shaped MessageCollection plus a
# rejection-message list and asserts the function's exact Requires holds for it
# (the two full-permission field accesses and the 1/2 list_pred on the
# rejection list). The real impl then runs unchanged over the actual params.
# If the precondition could not be established for a legitimate input the
# Asserts fail => PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS = """    # impl-start
    # --- admissibility witness for an F2P-shaped input (elided from spec view) ---
    adm_css = [101, 114, 114, 111, 114, 108, 105, 115, 116]  # type: List[int]
    adm_items = []  # type: List[int]
    adm = MessageCollection(adm_css, adm_items)
    adm_rej = [89, 111, 117]  # type: List[int]
    # the function's Requires is establishable for this concrete input:
    #   Acc(adm.css_class), Acc(adm.items) (full, from the constructor Ensures),
    #   and a half-permission list_pred over a fresh rejection-message list.
    Assert(Acc(adm.css_class))
    Assert(Acc(adm.items))
    Assert(Acc(list_pred(adm_rej), 1 / 2))
    # --- end admissibility witness; the real impl follows unchanged ---
    empty = []  # type: List[int]
    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
    collection.css_class = init_class
    collection.items = empty
    if group_flagged:
        collection.items = collection.items + [group_message]
    if rejected:
        items_copy = []  # type: List[int]
        i = 0
        while i < len(rejection_messages):
            Invariant(Acc(list_pred(rejection_messages), 1 / 2))
            Invariant(Acc(list_pred(items_copy)))
            Invariant(0 <= i and i <= len(rejection_messages))
            Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
            items_copy = items_copy + [rejection_messages[i]]
            i = i + 1
        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
        collection.css_class = rej_class
        collection.items = items_copy
    # impl-end"""


# ===========================================================================
# FRAME-MUTATION (MANDATORY) — rejection_messages is held at Acc(list_pred,1/2),
# i.e. READ-ONLY. A rival that WRITES to it must be REJECTED for INSUFFICIENT
# PERMISSION (not because the value clause fails). We keep ALL the gold value
# obligations satisfiable by the rest of the impl so the rejection is
# attributable solely to the write. A mechanical byte-fuzzer never thinks to
# mutate the input — this is the project's #1 weakness class.
# ===========================================================================

# frame-mutate-append: on the rejected path, mutate rejection_messages in place
# (append a sentinel) before copying. Holding only 1/2 permission, the verifier
# rejects the write for insufficient permission. The css_class/items clauses are
# otherwise fully satisfiable, so a verify here would mean the read-only contract
# is unenforced — SPEC-TOO-WEAK on the permission frame.
_FRAME_APPEND = """    # impl-start
    empty = []  # type: List[int]
    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
    collection.css_class = init_class
    collection.items = empty
    if group_flagged:
        collection.items = collection.items + [group_message]
    if rejected:
        # FRAME MUTATION: write to the read-only (1/2-perm) rejection_messages.
        rejection_messages.append(0)
        items_copy = []  # type: List[int]
        i = 0
        while i < len(rejection_messages):
            Invariant(Acc(list_pred(rejection_messages), 1 / 2))
            Invariant(Acc(list_pred(items_copy)))
            Invariant(0 <= i and i <= len(rejection_messages))
            Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
            items_copy = items_copy + [rejection_messages[i]]
            i = i + 1
        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
        collection.css_class = rej_class
        collection.items = items_copy
    # impl-end"""

# frame-mutate-store: index-assign into the read-only rejection_messages
# (rejection_messages[0] = group_message) on the rejected path before reading.
# Same defect: a store into a 1/2-permission list must be rejected for
# insufficient permission. Supporting frame-mutation variant (a different write
# shape than append) so the rejection is robustly attributable to the write.
_FRAME_STORE = """    # impl-start
    empty = []  # type: List[int]
    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
    collection.css_class = init_class
    collection.items = empty
    if group_flagged:
        collection.items = collection.items + [group_message]
    if rejected:
        # FRAME MUTATION: index-store into the read-only (1/2-perm) input.
        rejection_messages[0] = group_message
        items_copy = []  # type: List[int]
        i = 0
        while i < len(rejection_messages):
            Invariant(Acc(list_pred(rejection_messages), 1 / 2))
            Invariant(Acc(list_pred(items_copy)))
            Invariant(0 <= i and i <= len(rejection_messages))
            Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
            items_copy = items_copy + [rejection_messages[i]]
            i = i + 1
        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
        collection.css_class = rej_class
        collection.items = items_copy
    # impl-end"""


# ===========================================================================
# UNIQUENESS — rivals that share the spec exactly and change ONLY the impl. Each
# MUST be rejected; a verifying rival is a real verify-but-not-resolve break
# (SPEC-TOO-WEAK). Each carries the refinement argument that its faithful real
# patch would NOT resolve the F2P/P2P.
# ===========================================================================

# uniq-no-marker-init: THE PRE-PATCH BUG at the init site. Leave css_class as the
# bare 'errorlist' (no marker) at the init site. This is exactly
# model_prepatch_2.py. On the accepted path the css_class clause
# ToSeq == class_attr(nonform_tag()) ('errorlist nonform') fails. Rejected.
_UNIQ_NO_MARKER_INIT = """    # impl-start
    empty = []  # type: List[int]
    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116]  # 'errorlist' only
    collection.css_class = init_class
    collection.items = empty
    if group_flagged:
        collection.items = collection.items + [group_message]
    if rejected:
        items_copy = []  # type: List[int]
        i = 0
        while i < len(rejection_messages):
            Invariant(Acc(list_pred(rejection_messages), 1 / 2))
            Invariant(Acc(list_pred(items_copy)))
            Invariant(0 <= i and i <= len(rejection_messages))
            Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
            items_copy = items_copy + [rejection_messages[i]]
            i = i + 1
        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
        collection.css_class = rej_class
        collection.items = items_copy
    # impl-end"""

# uniq-no-marker-rejected: THE PRE-PATCH BUG at the exception site. Leave
# css_class as the bare 'errorlist' (no marker) on the REJECTED path. This is
# exactly model_prepatch.py. On the rejected path the css_class clause fails.
# Rejected. (Disjoint control path from uniq-no-marker-init — both pre-patch
# bugs are caught.)
_UNIQ_NO_MARKER_REJECTED = """    # impl-start
    empty = []  # type: List[int]
    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
    collection.css_class = init_class
    collection.items = empty
    if group_flagged:
        collection.items = collection.items + [group_message]
    if rejected:
        items_copy = []  # type: List[int]
        i = 0
        while i < len(rejection_messages):
            Invariant(Acc(list_pred(rejection_messages), 1 / 2))
            Invariant(Acc(list_pred(items_copy)))
            Invariant(0 <= i and i <= len(rejection_messages))
            Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
            items_copy = items_copy + [rejection_messages[i]]
            i = i + 1
        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116]  # 'errorlist' only
        collection.css_class = rej_class
        collection.items = items_copy
    # impl-end"""

# uniq-wrong-marker: use a DIFFERENT marker ('nonfield', the FORM non-field
# class) instead of 'nonform'. css_class becomes 'errorlist nonfield', which is
# NOT class_attr(nonform_tag()) ('errorlist nonform'). Rejected by the css_class
# clause. This is the partial-but-wrong fix a developer might write by analogy
# with forms' nonfield class — it would render the wrong CSS class and fail the
# F2P str(...) == '<ul class="errorlist nonform">...' assertion.
_UNIQ_WRONG_MARKER = """    # impl-start
    empty = []  # type: List[int]
    # 'errorlist nonfield' (wrong marker — forms' non-field class, not nonform)
    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                  110, 111, 110, 102, 105, 101, 108, 100]
    collection.css_class = init_class
    collection.items = empty
    if group_flagged:
        collection.items = collection.items + [group_message]
    if rejected:
        items_copy = []  # type: List[int]
        i = 0
        while i < len(rejection_messages):
            Invariant(Acc(list_pred(rejection_messages), 1 / 2))
            Invariant(Acc(list_pred(items_copy)))
            Invariant(0 <= i and i <= len(rejection_messages))
            Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
            items_copy = items_copy + [rejection_messages[i]]
            i = i + 1
        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                     110, 111, 110, 102, 105, 101, 108, 100]
        collection.css_class = rej_class
        collection.items = items_copy
    # impl-end"""

# uniq-drop-group-append: PARTIAL-DOMAIN. Omit the group_flagged append. Correct
# on the unflagged-accepted and rejected sub-domains, but on the accepted+flagged
# sub-domain the held items stay empty instead of [group_message]. Rejected by
# Ensures(Implies(not rejected and group_flagged, ToSeq(items)==PSeq(group_message))).
# This is the narrowed model the verdict's DEFECT 1 caught: an impl that does not
# model the unchanged management-form-invalid append leaves a spec-observed field
# wrong on a reachable accepted path.
_UNIQ_DROP_GROUP = """    # impl-start
    empty = []  # type: List[int]
    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
    collection.css_class = init_class
    collection.items = empty
    if rejected:
        items_copy = []  # type: List[int]
        i = 0
        while i < len(rejection_messages):
            Invariant(Acc(list_pred(rejection_messages), 1 / 2))
            Invariant(Acc(list_pred(items_copy)))
            Invariant(0 <= i and i <= len(rejection_messages))
            Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
            items_copy = items_copy + [rejection_messages[i]]
            i = i + 1
        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
        collection.css_class = rej_class
        collection.items = items_copy
    # impl-end"""

# uniq-skip-rejected-rebuild: PARTIAL-DOMAIN / control-omission. Drop the entire
# `if rejected:` rebuild. Correct on the accepted path (empty / single message),
# but on the rejected path the held items are NOT rebuilt from rejection_messages
# (they keep the accepted-path content — empty or the single group message).
# Rejected by Ensures(Implies(rejected, ToSeq(items)==ToSeq(rejection_messages))):
# the verifier cannot prove the accepted-path items equal an arbitrary
# rejection_messages list. Corresponds to a patch that forgot to populate
# non_form_errors from e.error_list on the exception path — the F2P
# non_form_errors() == ['...'] assertion would fail.
_UNIQ_SKIP_REJECTED = """    # impl-start
    empty = []  # type: List[int]
    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
    collection.css_class = init_class
    collection.items = empty
    if group_flagged:
        collection.items = collection.items + [group_message]
    # impl-end"""

# uniq-rejected-copy-prefix: VALUE-LEVEL partial copy. On the rejected path copy
# all rejection_messages EXCEPT the last element (loop bound i < len-1). The
# held items then equal rejection_messages.take(len-1), not the full list.
# Rejected by Ensures(Implies(rejected, ToSeq(items)==ToSeq(rejection_messages)))
# on any rejection list of length >= 1 (drops the last message). Corresponds to
# an off-by-one in copying e.error_list — the non_form_errors() list would be
# missing its last message and the F2P equality fails.
_UNIQ_COPY_PREFIX = """    # impl-start
    empty = []  # type: List[int]
    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
    collection.css_class = init_class
    collection.items = empty
    if group_flagged:
        collection.items = collection.items + [group_message]
    if rejected:
        items_copy = []  # type: List[int]
        i = 0
        while i < len(rejection_messages) - 1:
            Invariant(Acc(list_pred(rejection_messages), 1 / 2))
            Invariant(Acc(list_pred(items_copy)))
            Invariant(0 <= i and i <= len(rejection_messages))
            Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
            items_copy = items_copy + [rejection_messages[i]]
            i = i + 1
        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
        collection.css_class = rej_class
        collection.items = items_copy
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-control-build-from-concat",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_CONCAT),
        "rationale": "structurally-different CORRECT impl: build the marker class "
                     "compositionally ('errorlist' + ' ' + 'nonform' as code-point "
                     "list concatenations) at both sites instead of one spelled-out "
                     "17-element literal. ToSeq of the concatenation equals "
                     "generic_class()+PSeq(32)+nonform_tag() == class_attr(nonform_tag()), "
                     "so the css_class clause holds; items handling and the loop "
                     "invariants are byte-identical to gold (no new fold lemma — pilot "
                     "pitfalls #2/#3 avoided). If a faithful correct impl cannot verify "
                     "=> SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-reorder-rejected-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_REORDER),
        "rationale": "branch-reorder CORRECT impl: handle the rejected case first "
                     "(rebuild from rejection_messages with marker) then the accepted "
                     "case in the else branch (marker class; empty or single "
                     "group_message). Behaviourally identical on every control case; the "
                     "rejection loop keeps the gold take-fold invariants and forward "
                     "append, so no new lemma is needed. Must verify (else "
                     "SPEC-TOO-STRONG).",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region (elided "
                     "from the spec view, so same_spec holds) builds a fresh F2P-shaped "
                     "MessageCollection (css_class='errorlist', empty items) and a "
                     "concrete rejection-message list, then asserts the function's exact "
                     "Requires holds: Acc(adm.css_class) and Acc(adm.items) (full, from "
                     "the constructor Ensures) and Acc(list_pred(adm_rej),1/2). The real "
                     "impl then runs unchanged. If the precondition could not be "
                     "established for a legitimate input the Asserts fail => "
                     "PRECOND-TOO-STRONG.",
    },

    # ---- frame mutation (MANDATORY; read-only rejection_messages; must reject) ----
    {
        "id": "frame-mutate-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_APPEND),
        "refinement": "the real e.error_list (the caught ValidationError's message "
                      "list) is the source the exception site reads to populate "
                      "non_form_errors; a faithful patch never MUTATES e.error_list — "
                      "it constructs a fresh ErrorList from it. An impl that appended to "
                      "e.error_list would corrupt the caught exception's own message "
                      "list (observable by any later handler / re-raise) and is not the "
                      "gold behaviour; it does not correspond to a resolving patch.",
        "rationale": "rejected by the PERMISSION SYSTEM: rejection_messages is held at "
                     "Acc(list_pred(rejection_messages),1/2) (read-only); the in-place "
                     "append requires full permission, which the function does not hold. "
                     "All value clauses are otherwise satisfiable, so the rejection is "
                     "attributable solely to the write — the read-only frame is "
                     "enforced.",
    },
    {
        "id": "frame-mutate-store",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_STORE),
        "refinement": "an index-store into e.error_list (rejection_messages[0]=...) "
                      "would overwrite the first caught rejection message in place — "
                      "again mutating the shared exception object rather than building a "
                      "fresh collection. The gold patch reads e.error_list read-only; a "
                      "patch that wrote into it is not faithful and would not resolve "
                      "(and could change the messages other consumers observe).",
        "rationale": "rejected by the PERMISSION SYSTEM: an index-store into a "
                     "1/2-permission list_pred requires full permission. Supporting "
                     "frame-mutation variant (a different write shape than append) so "
                     "the rejection is robustly attributable to the read-only-input "
                     "write.",
    },

    # ---- uniqueness: the two pre-patch bugs (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-no-marker-init",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_NO_MARKER_INIT),
        "refinement": "this IS model_prepatch_2.py / the pre-patch init site "
                      "self.error_class() with no marker. The F2P "
                      "test_formset_validate_max_flag / _min_flag / test_non_form_errors "
                      "assert str(formset.non_form_errors()) == "
                      "'<ul class=\\\"errorlist nonform\\\">...'; the admin F2P "
                      "test_non_form_errors_is_errorlist compares against "
                      "ErrorList([...], error_class='nonform'). With the init site "
                      "rendering the bare 'errorlist' the rendered class is "
                      "'errorlist' (not 'errorlist nonform') on the accepted/default "
                      "collection and those assertions fail — the faithful pre-patch "
                      "code does NOT resolve.",
        "rationale": "rejected by Ensures(ToSeq(collection.css_class) == "
                     "class_attr(nonform_tag())): class_attr(nonform_tag()) fully "
                     "unfolds to the 17 code points of 'errorlist nonform'; the bare "
                     "'errorlist' (9 code points) on the accepted path is provably "
                     "unequal.",
    },
    {
        "id": "uniq-no-marker-rejected",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_NO_MARKER_REJECTED),
        "refinement": "this IS model_prepatch.py / the pre-patch exception site "
                      "self.error_class(e.error_list) with no marker. On the rejection "
                      "path (which the max/min/clean() F2P tests exercise) the rendered "
                      "class is the bare 'errorlist', so str(formset.non_form_errors()) "
                      "is '<ul class=\\\"errorlist\\\">...' and the F2P equality against "
                      "'errorlist nonform' fails — the faithful pre-patch code does NOT "
                      "resolve.",
        "rationale": "rejected by Ensures(ToSeq(collection.css_class) == "
                     "class_attr(nonform_tag())) on the rejected path: the bare "
                     "'errorlist' code points are provably unequal to the 'errorlist "
                     "nonform' code points. Disjoint control path from "
                     "uniq-no-marker-init — both pre-patch sites are caught.",
    },
    {
        "id": "uniq-wrong-marker",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_WRONG_MARKER),
        "refinement": "passing error_class='nonfield' (the FORM non-field class) by "
                      "analogy instead of 'nonform' renders class='errorlist nonfield'. "
                      "The F2P tests assert the exact string '<ul class=\\\"errorlist "
                      "nonform\\\">...' and the admin test compares to "
                      "ErrorList(error_class='nonform'); a 'nonfield' marker produces a "
                      "different class attribute and those assertions fail — a "
                      "wrong-marker patch does NOT resolve.",
        "rationale": "rejected by Ensures(ToSeq(collection.css_class) == "
                     "class_attr(nonform_tag())): nonform_tag() is the fixed code points "
                     "of 'nonform'; 'errorlist nonfield' is provably unequal to "
                     "'errorlist nonform'. Targets the grounded css_class oracle "
                     "(no opaque value to echo).",
    },

    # ---- partial-domain (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-drop-group-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_GROUP),
        "refinement": "omitting the group_flagged append models the narrowed pre-DEFECT-1 "
                      "impl: it does NOT leave the single management-form-invalid "
                      "message in the collection on the accepted-flagged path. The "
                      "unchanged real append (self._non_form_errors.append(error) when "
                      "the management form is invalid) DOES leave that message; a patch "
                      "that dropped it would change the held messages on a reachable "
                      "accepted path (P2P test_customize_management_form_error / "
                      "test_management_form_invalid_data observe that message), so it is "
                      "not faithful.",
        "rationale": "rejected by Ensures(Implies(not rejected and group_flagged, "
                     "ToSeq(collection.items) == PSeq(group_message))): with the append "
                     "dropped the held items are empty on the accepted-flagged "
                     "sub-domain, not PSeq(group_message). Partial-domain attack (correct "
                     "elsewhere, wrong on accepted+flagged).",
    },
    {
        "id": "uniq-skip-rejected-rebuild",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_SKIP_REJECTED),
        "refinement": "dropping the entire rejected rebuild corresponds to a patch that "
                      "forgot to populate non_form_errors from e.error_list on the "
                      "except ValidationError path. The F2P tests reject the formset and "
                      "assert non_form_errors() == ['Please submit at most/at least ...'] "
                      "(the rejection messages); with no rebuild the collection stays "
                      "empty/single-message and that assertion fails — does NOT resolve.",
        "rationale": "rejected by Ensures(Implies(rejected, ToSeq(collection.items) == "
                     "ToSeq(rejection_messages))): on the rejected path the held items "
                     "are the accepted-path content (empty or [group_message]), which "
                     "the verifier cannot prove equal to an arbitrary rejection_messages "
                     "list. Partial-domain attack on the rejected sub-domain.",
    },
    {
        "id": "uniq-rejected-copy-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_COPY_PREFIX),
        "refinement": "copying all but the last rejection message (loop bound "
                      "i < len-1) corresponds to an off-by-one when rebuilding the "
                      "collection from e.error_list: the resulting non_form_errors() "
                      "list would be missing its final message, so the F2P equality "
                      "non_form_errors() == ['...the full list...'] fails — does NOT "
                      "resolve on any rejection list of length >= 1.",
        "rationale": "rejected by Ensures(Implies(rejected, ToSeq(collection.items) == "
                     "ToSeq(rejection_messages))): the held items equal "
                     "rejection_messages.take(len-1) (the loop's final invariant), which "
                     "is provably unequal to the full rejection_messages whenever its "
                     "length is >= 1. Value-level partial-copy attack.",
    },
]


# ===========================================================================
# AXIOM LANE — meta.axioms == [] (NO @ContractOnly axiom consumed). The only
# callee whose behaviour the proof relies on is the UNCHANGED ErrorList
# class-attribute rule, modeled DEEPLY by the @Pure class_attr and validated
# == the real callee out-of-band by axiom_check.py / G-AX (an A-reference). We
# carry that A-reference soundness check here as an axiom-soundness probe (the
# deep model must equal the real callee on every caller-reachable tag), plus a
# containment probe (the model only ever passes the empty tag and nonform_tag()
# to class_attr — both inside the rule's domain). The runner mounts ONLY the
# probe at /work, so we embed the bundle's axiom_check.py logic directly (it
# imports only Django, which IS present in the instance image), per pilot
# pitfall #6. open(..., encoding='utf-8') everywhere per pilot pitfall #5.
# ===========================================================================

# axiom-soundness (A-reference): execute the REAL django.forms.utils.ErrorList
# and assert class_attr(tag) == ErrorList(error_class=tag).error_class for the
# no-tag case, the nonform marker, and 2000 fuzzed marker tags, plus the exact
# rendered '<ul class="errorlist nonform">...' string the F2P tests check. This
# is the bundle's axiom_check.py logic embedded verbatim-in-spirit. Any mismatch
# => the deep model is unsound (AXIOM-UNSOUND for the A-reference). The rule is
# flag-independent (ErrorList.error_class depends on no setting), so apply_gold
# is harmless (ErrorList itself is UNCHANGED by the patch).
_AX_SOUNDNESS_PROBE = r'''
import random
import sys


_GENERIC = "errorlist"   # generic_class() -> code points of 'errorlist'
_TAG = "nonform"         # nonform_tag()    -> code points of 'nonform'


def class_attr(tag):
    """Reference of model.py's deep model class_attr, on strings (the empty
    string models the empty List[int] / no marker tag)."""
    if len(tag) == 0:
        return _GENERIC
    return _GENERIC + " " + tag


def main():
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(USE_I18N=False, USE_L10N=False, INSTALLED_APPS=[])
        django.setup()
        from django.forms.utils import ErrorList
    except Exception as exc:
        print("AXIOM-SOUNDNESS FAIL: Django not importable/configurable: %r" % (exc,))
        return 1

    # (1) no marker tag -> the generic class only.
    el_none = ErrorList()
    assert el_none.error_class == class_attr(""), (
        "class_attr deep model unsound for no-tag: ErrorList().error_class=%r, "
        "model gives %r" % (el_none.error_class, class_attr("")))
    el_none2 = ErrorList(error_class=None)
    assert el_none2.error_class == class_attr(""), (
        "class_attr deep model unsound for error_class=None: %r vs %r"
        % (el_none2.error_class, class_attr("")))

    # (2) the marker tag this benchmark uses -> 'errorlist nonform'.
    el_tag = ErrorList(error_class=_TAG)
    assert el_tag.error_class == class_attr(_TAG), (
        "class_attr deep model unsound for tag=%r: ErrorList.error_class=%r, "
        "model gives %r" % (_TAG, el_tag.error_class, class_attr(_TAG)))
    assert el_tag.error_class == "errorlist nonform", (
        "the marker tag did not render as the expected class: %r"
        % (el_tag.error_class,))

    # (3) fuzz arbitrary marker tags: the rule must hold for any tag.
    rng = random.Random(14608)
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_0123456789"
    fuzz_tags = ["", "nonform", "nonfield", "a", "x y", "errorlist"]
    for _ in range(2000):
        n = rng.randint(1, 16)
        fuzz_tags.append("".join(rng.choice(alphabet) for _ in range(n)))
    for tag in fuzz_tags:
        el = ErrorList(error_class=(tag if tag != "" else None))
        assert el.error_class == class_attr(tag), (
            "class_attr deep model unsound for tag=%r: ErrorList.error_class=%r, "
            "model gives %r" % (tag, el.error_class, class_attr(tag)))

    # (4) the rendered list (str / as_ul) carries the marker class verbatim —
    # exactly the string the F2P tests assert.
    el_items = ErrorList(["Please submit at most 1 form."], error_class="nonform")
    rendered = str(el_items)
    assert rendered == (
        '<ul class="errorlist nonform"><li>Please submit at most 1 form.</li>'
        '</ul>'), (
        "rendered non-form error list did not match expected: %r" % (rendered,))
    el_empty = ErrorList(error_class="nonform")
    assert el_empty.error_class == "errorlist nonform", (
        "empty collection did not carry the marker class: %r"
        % (el_empty.error_class,))

    print("AXIOM-SOUNDNESS OK: class_attr deep model (== ErrorList "
          "class-attribute rule) sound on %d marker-tag observations + the "
          "rendered-list witness." % (len(fuzz_tags),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

# axiom-containment: the model only ever evaluates class_attr at TWO tags — the
# empty tag (never reached at a live call: the impl always passes the nonform
# marker; the empty branch exists only in the pure definition) and nonform_tag()
# ('nonform'). Both lie inside the real ErrorList class-attribute rule's domain
# (it accepts None / absent / any str marker). We confirm operationally that the
# exact tags the model can pass — '' and 'nonform' — are accepted by the real
# callee and produce the modeled class attribute, so no caller-reachable tag
# lies outside the rule's domain. (The rule covering MORE — any str — is SOUND,
# not a defect; the caller reaches a subset.)
_AX_CONTAINMENT_PROBE = r'''
import sys


_GENERIC = "errorlist"
_TAG = "nonform"


def class_attr(tag):
    if len(tag) == 0:
        return _GENERIC
    return _GENERIC + " " + tag


def main():
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(USE_I18N=False, USE_L10N=False, INSTALLED_APPS=[])
        django.setup()
        from django.forms.utils import ErrorList
    except Exception as exc:
        print("AXIOM-CONTAINMENT FAIL: Django not importable/configurable: %r"
              % (exc,))
        return 1

    # The exact tags the model can reach: '' (the empty-tag branch of the pure
    # definition) and 'nonform' (nonform_tag(), what the impl actually passes).
    reachable_tags = ["", _TAG]
    for tag in reachable_tags:
        # the real callee accepts this tag (None for the empty tag) and produces
        # exactly the modeled class attribute -> the tag is inside the rule's
        # domain.
        el = ErrorList(error_class=(tag if tag != "" else None))
        assert el.error_class == class_attr(tag), (
            "AXIOM-TOO-WEAK-FOR-CALLER: caller-reachable tag %r is not handled by "
            "the real ErrorList rule consistently with the deep model: "
            "ErrorList.error_class=%r, model gives %r"
            % (tag, el.error_class, class_attr(tag)))

    print("AXIOM-CONTAINMENT OK: every class_attr tag the model can reach "
          "(%r) lies inside the real ErrorList class-attribute rule's domain "
          "(it accepts None/absent/any str marker) and yields the modeled class "
          "attribute. The caller reaches a subset of the rule's domain; no "
          "reachable tag is outside it." % (reachable_tags,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-class_attr",
        "axiom": "class_attr",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # ErrorList is UNCHANGED by the patch; apply_gold harmless
        "probe": _AX_SOUNDNESS_PROBE,
        "rationale": "the deep model class_attr (an A-reference, NOT a consumed axiom) "
                     "must equal the real django.forms.utils.ErrorList class-attribute "
                     "rule on every caller-reachable tag. The probe executes the REAL "
                     "ErrorList over the no-tag case, the nonform marker, 2000 fuzz "
                     "tags, and the exact rendered '<ul class=\"errorlist nonform\">...' "
                     "string the F2P tests check; any mismatch => the deep model is "
                     "unsound (the A-reference fails). This is the bundle's "
                     "axiom_check.py logic embedded (the runner mounts only the probe; "
                     "the logic imports only Django, present in-container).",
    },
    {
        "id": "ax-cover-class_attr",
        "axiom": "class_attr",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": "the model evaluates class_attr only at the empty tag and "
                     "nonform_tag() ('nonform'); both lie inside the real ErrorList "
                     "rule's domain (it accepts None/absent/any str marker). The probe "
                     "confirms the real callee accepts exactly those reachable tags and "
                     "produces the modeled class attribute. A caller-reachable tag "
                     "outside the rule's domain would be AXIOM-TOO-WEAK-FOR-CALLER; none "
                     "exists (the rule covering more is sound, not a defect).",
    },
]
