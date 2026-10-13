# properties.py — PBT falsification battery for sphinx-doc__sphinx-10449.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS entry is a FULL model.py variant whose ONLY change is inside an
# `# impl-start`/`# impl-end` region (so the frozen spec — axioms/pure/pre/post-
# conditions/signatures — is byte-identical and `markers.same_spec` holds). The
# runner verifies each variant with Nagini and compares the outcome to `expect`.
#
# Defended surface (read carefully before reading the cases):
#   * suppress_for_kind(object_kind)            -> bool
#       read-only input Acc(list_pred(object_kind), 1/2)
#       post: Result() == (ToSeq(object_kind) == seq_class())          [grounded]
#   * has_return_field_in(fields)               -> bool
#       read-only input Acc(list_pred(fields), 1/2)
#       post: Result() == has_return_field(ToSeq(fields))              [grounded]
#   * append_return_type(fields, has_return, return_annotation, suppress_void_return)
#       read-only inputs Acc(list_pred(fields),1/2), Acc(list_pred(return_annotation),1/2)
#       THE FIX SITE. Two load-bearing post-clauses:
#         (E) emit-decision iff:
#             (Result() is not None) ==
#                 (has_return and not has_return_field(ToSeq(fields))
#                  and not (suppress_void_return and ToSeq(return_annotation)==seq_none()))
#         (C) content pin (only when a field is produced):
#             opt_seq(Result()) == ToSeq(return_annotation)
#       plus Acc(list_pred(Result())) full perm on the produced field.
#
# F2P: tests/test_ext_autodoc_configs.py::test_autodoc_typehints_description_with_documented_init
# The test asserts a documented class whose __init__ returns None NO LONGER emits
# a "Return type:\n None" field under autodoc_typehints_description_target='all'.
# Gold change = thread suppress_rtype=True for objtype=='class' (suppress_for_kind)
# and, in modify_field_list, skip the rtype append exactly when
# annotation=='None' and suppress_rtype (append_return_type clause E), while still
# rendering the object's OWN return annotation when a field IS emitted (clause C).

from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-10449"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found in model.py")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact gold impl-region anchors (verbatim from model.py; uniqueness-checked).
# ---------------------------------------------------------------------------

# append_return_type gold impl region body (between # impl-start / # impl-end)
_APP_GOLD = """\
    no_return_field = not has_return_field_in(fields)
    Assert(no_return_field == (not has_return_field(ToSeq(fields))))
    if has_return and no_return_field:
        suppressed_none = ToSeq(return_annotation) == seq_none() and suppress_void_return
        if suppressed_none:
            return None
        # Render the field with the object's own return annotation as content.
        field = []  # type: List[int]
        j = 0
        while j < len(return_annotation):
            # invariants-start
            Invariant(Acc(list_pred(return_annotation), 1 / 2))
            Invariant(Acc(list_pred(field)))
            Invariant(0 <= j and j <= len(return_annotation))
            Invariant(ToSeq(field) == ToSeq(return_annotation).take(j))
            Invariant(not suppressed_none)
            Invariant(suppressed_none
                      == (ToSeq(return_annotation) == seq_none() and suppress_void_return))
            Invariant(MustTerminate(len(return_annotation) - j + 1))
            # invariants-end
            Assert(ToSeq(return_annotation).take(j + 1).drop(j)[0]
                   == return_annotation[j])
            Assert(ToSeq(return_annotation).take(j + 1)
                   == ToSeq(return_annotation).take(j) + PSeq(return_annotation[j]))
            field.append(return_annotation[j])
            j = j + 1
        Assert(ToSeq(return_annotation).take(len(return_annotation))
               == ToSeq(return_annotation))
        Assert(ToSeq(field) == ToSeq(return_annotation))
        Assert(has_return and no_return_field and not suppressed_none)
        return field
    return None"""

# has_return_field_in gold impl region body
_HRF_GOLD = """\
    found = False
    i = len(fields)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(fields), 1 / 2))
        Invariant(0 <= i and i <= len(fields))
        Invariant(found == has_return_field(ToSeq(fields).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
        Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
        if is_return_field(fields[i - 1]):
            found = True
        i = i - 1
    return found"""

# suppress_for_kind gold impl region body
_SUP_GOLD = "    return ToSeq(object_kind) == seq_class()"


# sanity: all three anchors are present exactly once in _BASE
for _a in (_APP_GOLD, _HRF_GOLD, _SUP_GOLD):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor not unique in model.py: count={_BASE.count(_a)}")


# ===========================================================================
# SPEC CASES
# ===========================================================================

SPEC_TESTS = []


# --- 1. POSITIVE CONTROL (soundness): structurally-different CORRECT impl -----
# Reorders the short-circuit `and` operands in the append-guard AND in the
# `suppressed_none` computation. This changes evaluation order / structure while
# keeping every gold invariant and Assert byte-for-byte, so the gold proof stays
# valid (no induction lemma needed). A faithful correct impl MUST verify; if it
# cannot, the spec is SPEC-TOO-STRONG.
_POS_APP = """\
    no_return_field = not has_return_field_in(fields)
    Assert(no_return_field == (not has_return_field(ToSeq(fields))))
    if no_return_field and has_return:
        suppressed_none = suppress_void_return and ToSeq(return_annotation) == seq_none()
        if suppressed_none:
            return None
        # Render the field with the object's own return annotation as content.
        field = []  # type: List[int]
        j = 0
        while j < len(return_annotation):
            # invariants-start
            Invariant(Acc(list_pred(return_annotation), 1 / 2))
            Invariant(Acc(list_pred(field)))
            Invariant(0 <= j and j <= len(return_annotation))
            Invariant(ToSeq(field) == ToSeq(return_annotation).take(j))
            Invariant(not suppressed_none)
            Invariant(suppressed_none
                      == (ToSeq(return_annotation) == seq_none() and suppress_void_return))
            Invariant(MustTerminate(len(return_annotation) - j + 1))
            # invariants-end
            Assert(ToSeq(return_annotation).take(j + 1).drop(j)[0]
                   == return_annotation[j])
            Assert(ToSeq(return_annotation).take(j + 1)
                   == ToSeq(return_annotation).take(j) + PSeq(return_annotation[j]))
            field.append(return_annotation[j])
            j = j + 1
        Assert(ToSeq(return_annotation).take(len(return_annotation))
               == ToSeq(return_annotation))
        Assert(ToSeq(field) == ToSeq(return_annotation))
        Assert(has_return and no_return_field and not suppressed_none)
        return field
    return None"""

SPEC_TESTS.append({
    "id": "pos-control-reorder-guard",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _APP_GOLD, _POS_APP),
    "rationale": ("A correct impl that only reorders the short-circuit `and` "
                  "operands in the append-guard and in the suppressed_none test "
                  "(every gold invariant/Assert kept verbatim) must verify; the "
                  "two clauses are commutative so the gold proof stays valid. "
                  "If it cannot verify the spec is SPEC-TOO-STRONG."),
})


# --- 2. ADMISSIBILITY: F2P-shaped in-domain input is accepted -----------------
# In-region caller (kept inside append_return_type's impl so the spec view is
# unchanged): builds the exact F2P shape — a 'class' kind, an empty field list,
# the 'None' return annotation, suppress=True — and exercises the helpers'
# preconditions on fresh full-permission inputs, asserting their grounded
# results, THEN runs the gold body unchanged. If the Requires cannot be
# established for this legitimate input it is PRECOND-TOO-STRONG.
_ADM_APP = """\
    # admissibility prelude: F2P-shaped inputs (class kind + 'None' return) are
    # in-domain for the helpers' preconditions.
    ok = []  # type: List[int]
    ok.append(99)
    ok.append(108)
    ok.append(97)
    ok.append(115)
    ok.append(115)
    Assert(ToSeq(ok) == seq_class())
    sup = suppress_for_kind(ok)
    Assert(sup)
    empty_fl = []  # type: List[int]
    has_rf = has_return_field_in(empty_fl)
    Assert(not has_rf)
""" + _APP_GOLD

SPEC_TESTS.append({
    "id": "admissibility-f2p-shape",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(_BASE, _APP_GOLD, _ADM_APP),
    "rationale": ("A within-region caller constructs the F2P input shape (a "
                  "'class' object kind, an empty field list) and feeds it to "
                  "suppress_for_kind and has_return_field_in, asserting their "
                  "grounded results, then runs the gold body. Verifies iff the "
                  "preconditions admit a normal F2P-shaped input; else "
                  "PRECOND-TOO-STRONG."),
})


# --- 3. FRAME-MUTATION (uniqueness): write a read-only input ------------------
# MANDATORY: append_return_type holds only Acc(list_pred(return_annotation),1/2).
# A rival that WRITES to return_annotation (here, mutating it to seq_none() so
# the content pin is trivially met for the None case) must be REJECTED for
# INSUFFICIENT PERMISSION — `.append` on a 1/2-permission list is illegal. Gold
# post-clauses kept verbatim so the rejection is attributable to the write.
_FRAME_APP = """\
    # FRAME-MUTATION ATTACK: overwrite the read-only return_annotation input.
    return_annotation.append(0)
""" + _APP_GOLD

SPEC_TESTS.append({
    "id": "frame-mutation-return-annotation",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _APP_GOLD, _FRAME_APP),
    "refinement": ("A faithful real patch cannot mutate annotations['return'] "
                   "(it is the documented object's own return string, owned by "
                   "the shared annotations dict read across every field_list); "
                   "writing it would corrupt the rendered text for sibling "
                   "documented members and diverge from gold, so it would not "
                   "resolve the F2P."),
    "rationale": ("return_annotation is read-only (Acc(...,1/2)); `.append` "
                  "needs full permission, so Nagini rejects for insufficient "
                  "permission. If it verified, the spec would admit a vacuous "
                  "input-overwrite => SPEC-TOO-WEAK."),
})

# supporting frame-mutation on has_return_field_in (writes read-only `fields`).
_FRAME_HRF = """\
    fields.append(1)
""" + _HRF_GOLD

SPEC_TESTS.append({
    "id": "frame-mutation-fields-helper",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _HRF_GOLD, _FRAME_HRF),
    "refinement": ("The 'return' presence scan is read-only over the existing "
                   "field_list node; a real patch that appended a synthetic "
                   "rtype-marker field into the node before scanning would emit "
                   "a spurious 'Return type' field and fail the F2P / P2P "
                   "rendering assertions."),
    "rationale": ("fields is Acc(list_pred(fields),1/2); `.append` requires full "
                  "permission => rejected for insufficient permission. Supporting "
                  "frame-mutation case."),
})


# --- 4. PARTIAL-DOMAIN (uniqueness): prepatch behaviour (no suppression) ------
# Drops the suppressed_none early-return: the rtype field is appended whenever
# has_return and no_return_field, ignoring suppress_void_return entirely. This is
# the PRE-PATCH skeleton. It is correct on every input EXCEPT the (suppress_void
# _return and annotation=='None') sub-domain — exactly the F2P case — where it
# emits a field the gold suppresses, violating emit-decision clause (E).
_PD_NOSUPP = """\
    no_return_field = not has_return_field_in(fields)
    Assert(no_return_field == (not has_return_field(ToSeq(fields))))
    if has_return and no_return_field:
        # PRE-PATCH: append unconditionally; no suppression of a 'None' return
        # type for a container kind.
        field = []  # type: List[int]
        j = 0
        while j < len(return_annotation):
            # invariants-start
            Invariant(Acc(list_pred(return_annotation), 1 / 2))
            Invariant(Acc(list_pred(field)))
            Invariant(0 <= j and j <= len(return_annotation))
            Invariant(ToSeq(field) == ToSeq(return_annotation).take(j))
            Invariant(MustTerminate(len(return_annotation) - j + 1))
            # invariants-end
            Assert(ToSeq(return_annotation).take(j + 1).drop(j)[0]
                   == return_annotation[j])
            Assert(ToSeq(return_annotation).take(j + 1)
                   == ToSeq(return_annotation).take(j) + PSeq(return_annotation[j]))
            field.append(return_annotation[j])
            j = j + 1
        Assert(ToSeq(return_annotation).take(len(return_annotation))
               == ToSeq(return_annotation))
        Assert(ToSeq(field) == ToSeq(return_annotation))
        return field
    return None"""

SPEC_TESTS.append({
    "id": "partial-domain-no-suppression",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _APP_GOLD, _PD_NOSUPP),
    "refinement": ("This is exactly the pre-patch modify_field_list (no "
                   "suppress_rtype gate): for a documented class whose __init__ "
                   "returns None it appends 'Return type:\\n None', which is the "
                   "literal lines the F2P test deletes. The faithful patch FAILS "
                   "the F2P assertion."),
    "rationale": ("Violates emit-decision clause (E) on the sub-domain "
                  "suppress_void_return and ToSeq(return_annotation)==seq_none(): "
                  "(Result() is not None) is True but the RHS is False. If it "
                  "verified, SPEC-TOO-WEAK (admits the unfixed behaviour)."),
})


# --- 5. PARTIAL-DOMAIN (uniqueness): over-suppress (ignores annotation=='None')
# Suppresses whenever suppress_void_return is True, regardless of the return
# annotation. Correct on the None case, WRONG on a class with a non-None return
# annotation (e.g. a classmethod-style 'int' return), where gold still emits the
# field. Violates clause (E) on that sub-domain.
_PD_OVER = """\
    no_return_field = not has_return_field_in(fields)
    Assert(no_return_field == (not has_return_field(ToSeq(fields))))
    if has_return and no_return_field:
        # OVER-SUPPRESS: drop the annotation=='None' guard; suppress for any
        # return type whenever suppression is requested.
        if suppress_void_return:
            return None
        field = []  # type: List[int]
        j = 0
        while j < len(return_annotation):
            # invariants-start
            Invariant(Acc(list_pred(return_annotation), 1 / 2))
            Invariant(Acc(list_pred(field)))
            Invariant(0 <= j and j <= len(return_annotation))
            Invariant(ToSeq(field) == ToSeq(return_annotation).take(j))
            Invariant(not suppress_void_return)
            Invariant(MustTerminate(len(return_annotation) - j + 1))
            # invariants-end
            Assert(ToSeq(return_annotation).take(j + 1).drop(j)[0]
                   == return_annotation[j])
            Assert(ToSeq(return_annotation).take(j + 1)
                   == ToSeq(return_annotation).take(j) + PSeq(return_annotation[j]))
            field.append(return_annotation[j])
            j = j + 1
        Assert(ToSeq(return_annotation).take(len(return_annotation))
               == ToSeq(return_annotation))
        Assert(ToSeq(field) == ToSeq(return_annotation))
        return field
    return None"""

SPEC_TESTS.append({
    "id": "partial-domain-over-suppress",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _APP_GOLD, _PD_OVER),
    "refinement": ("A patch that suppressed the rtype field for ANY return type "
                   "of a class (not just 'None') would strip legitimate 'Return "
                   "type' fields from documented classes with a real return "
                   "annotation, regressing the P2P rendering tests and "
                   "contradicting the gold's `annotation == 'None' and "
                   "suppress_rtype` guard."),
    "rationale": ("Violates clause (E) on the sub-domain suppress_void_return "
                  "and ToSeq(return_annotation)!=seq_none(): RHS is True (a field "
                  "should be emitted) but Result() is None. If it verified, "
                  "SPEC-TOO-WEAK."),
})


# --- 6. CONTENT-WRONG (uniqueness): right decision, wrong rendered text -------
# Emits the field on exactly the right inputs (clause E satisfied) but renders
# fixed 'None' text instead of the object's OWN return annotation — the latent
# pre-patch transcription bug the gold also corrects (it used a leftover loop
# variable as the content). Violates content pin clause (C).
_CONTENT_WRONG = """\
    no_return_field = not has_return_field_in(fields)
    Assert(no_return_field == (not has_return_field(ToSeq(fields))))
    if has_return and no_return_field:
        suppressed_none = ToSeq(return_annotation) == seq_none() and suppress_void_return
        if suppressed_none:
            return None
        # CONTENT BUG: render a fixed 'None' string, not the object's OWN return
        # annotation.
        field = []  # type: List[int]
        field.append(78)
        field.append(111)
        field.append(110)
        field.append(101)
        Assert(ToSeq(field) == seq_none())
        return field
    return None"""

SPEC_TESTS.append({
    "id": "content-wrong-fixed-none",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _APP_GOLD, _CONTENT_WRONG),
    "refinement": ("Rendering a fixed 'None' (or any other name's annotation) "
                   "instead of annotations['return'] is precisely the pre-patch "
                   "transcription defect: a documented method returning 'int' "
                   "would render 'Return type: None'. Such a patch fails the F2P "
                   "/ P2P text assertions."),
    "rationale": ("Decision clause (E) holds but content pin (C) "
                  "opt_seq(Result()) == ToSeq(return_annotation) fails whenever "
                  "ToSeq(return_annotation) != seq_none(). If it verified, "
                  "SPEC-TOO-WEAK on the rendered content."),
})


# --- 7. CONTROL-FLOW-EFFECT: not applicable — documented in assessment --------
# append_return_type's only observable effect is its return value (None vs the
# produced field's content). There is no raise / side-effect channel separate
# from the value abstraction (the docutils node mutation is abstracted INTO the
# Optional[List[int]] return). No capability-token rival is meaningful here.


# ===========================================================================
# AXIOM CASES — none. meta.json: axioms == [], deep_model_references == [],
# G-AX vacuous, no @ContractOnly callees, no axiom_check.py. The whole changed
# behaviour is boolean/sequence logic modelled deeply.
# ===========================================================================

AXIOM_TESTS = []
