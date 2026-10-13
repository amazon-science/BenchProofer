# properties.py — PBT falsification battery for django__django-16569. NOT a
# Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant that shares the FROZEN spec exactly
# (markers.same_spec) and edits ONLY inside the # impl-start/# impl-end region;
# the runner re-runs the Nagini verifier on the host and checks the verify/reject
# outcome against `expect`.
#
# Defended surface (model.py + refinement.md + mapping.md + the F2P tests):
#   configure_optional_fields(form: Form, can_order, can_delete, can_delete_extra,
#                             index: Optional[int], initial_form_count: int) -> None
#     Requires(Acc(form.has_order_field) and Acc(form.order_field_prefilled)
#              and Acc(form.has_delete_field))            # FULL perm — form IS the output
#     Requires(Acc(form.aux_keys))                        # ditto: placement sequence
#     Requires(form.has_order_field == False and form.order_field_prefilled == False
#              and form.has_delete_field == False)        # fresh form: nothing present yet
#     Requires(form.aux_keys == empty_key_sequence())     # ... and nothing placed yet
#     Requires(initial_form_count >= 0)                   # read-only non-neg scalar
#     Requires(MustTerminate(2))                          # total correctness: must answer
#     Ensures(Acc(...) [perm preserved])
#     Ensures(form.has_order_field == can_order)                                   # (O)
#     Ensures(form.order_field_prefilled
#             == (can_order and at_initial_position(index, initial_form_count)))   # (P)
#     Ensures(form.has_delete_field
#             == (can_delete and (can_delete_extra
#                                 or at_initial_position(index, initial_form_count))))  # (D)
#     Ensures(form.aux_keys
#             == placed_keys(form.has_order_field, form.has_delete_field))          # (S)
#   @Pure at_initial_position(index, n) := index is not None and index < n
#   @Pure empty_key_sequence() := the empty placement sequence
#   @Pure placed_keys(o, d) := (PSeq(1) if o else <>) + (PSeq(2) if d else <>)
#
# (S) is the PLACEMENT-ORDER clause. A form's fields are an ORDERED mapping whose
# iteration order is what the form RENDERS, so which auxiliary controls a form
# carries does not determine the form: their relative placement is observable
# too. The real hook always places the ordering control ahead of the deletion
# control, and the P2P test 'FormSets with ordering + deletion.'
# (forms_tests.tests.test_formsets.FormsFormsetTestCase.
# test_formset_with_ordering_and_deletion) assertHTMLEqual's the rendered
# as_ul() with `<li>Order: ...>` immediately PRECEDING `<li>Delete: ...>` for
# every form. Without (S) the two placements commute in the model while they do
# NOT commute in the repo, so a rival that grants exactly the right controls in
# the wrong order verifies and yet fails that P2P — the audit's atk_11 was
# exactly that rival. uniq-delete-placed-first pins the rejection; the
# `aux_keys` carrier (token 1 = ordering key, token 2 = deletion key) is what
# makes the two writes non-commutable in the model.
#
# The fix is the None-guard inside (D): pre-patch `index < initial_form_count`
# (no `index is not None`) raises TypeError on the empty_form config
# (can_delete, not can_delete_extra, index is None). The F2P observes exactly
# `assertNotIn("DELETE", formset.empty_form.fields)` (index None) — i.e. (D)
# must evaluate to FALSE there.
#
# Two structural notes that scope the lanes (justified in 'assessment'):
#   * NO read-only Acc(...,1/2) input. The only object input `form` is held at
#     FULL permission because it IS the mutated output; every other param is a
#     pass-by-value scalar (can_*: bool, index: Optional[int], initial_form_count:
#     int). The canonical FRAME-MUTATION probe (overwrite a 1/2-perm input to
#     vacuously satisfy a postcondition, expect insufficient-permission) is
#     therefore N/A here — there is no half-permission input to overwrite, and a
#     scalar reassignment cannot change a postcondition that refers to the
#     parameter's call-time value. has_readonly_input = False.
#   * GROUNDED oracle. (P)/(D) are pinned to `at_initial_position(index, n)`, a
#     @Pure helper that is FULLY UNFOLDED as `index is not None and index < n` —
#     a direct function of the args. There is no opaque answer-key to ECHO: an
#     impl that "echoes" at_initial_position(...) is computing the correct value.
#     So the ungrounded-oracle-echo class has no wrong echo; in its place we add
#     honest cheapest-impl positive controls (expect verify) and the partial-
#     domain / value-boundary uniqueness attacks below.
#   * TERMINATION (total correctness — closes the vacuous-divergence hole). The
#     precondition carries Requires(MustTerminate(2)); the Form constructor
#     carries the strictly smaller Requires(MustTerminate(1)). Nagini is a
#     partial-correctness verifier by default, so WITHOUT the obligation a rival
#     that diverges before returning — bare self-recursion of the contracted
#     routine — satisfies every Ensures VACUOUSLY and verifies (the audit's P1
#     witness). With it, a self-call is rejected (no strictly smaller measure is
#     available: obligation leak), while bounded construction (measure 1 < 2)
#     remains admitted — uniq-selfrec-diverge pins the rejection.
#
# There are NO consumed @ContractOnly axioms (axioms region is comment-only). The
# A-reference (real BaseFormSet.add_fields == model decision) is validated by
# axiom_check.py / G-AX; AXIOM_TESTS carries one containment-style probe that
# asserts every callee-reachable index the model can pass (incl. None) is handled
# by the post-gold callee without raising, mirroring the model's None-graceful
# domain. (No axiom-soundness probe: there is no axiom Ensures to violate.)
from pathlib import Path

INSTANCE = "django__django-16569"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact frozen impl region (verbatim from model.py). We only ever replace text
# BETWEEN # impl-start / # impl-end, guaranteeing same_spec.
# ---------------------------------------------------------------------------
_IMPL_OLD = """    # impl-start
    if can_order:
        if index is not None and index < initial_form_count:
            form.has_order_field = True
            form.order_field_prefilled = True
            form.aux_keys = form.aux_keys + PSeq(1)
        else:
            form.has_order_field = True
            form.aux_keys = form.aux_keys + PSeq(1)
    if can_delete and (
        can_delete_extra or (index is not None and index < initial_form_count)
    ):
        form.has_delete_field = True
        form.aux_keys = form.aux_keys + PSeq(2)
    # impl-end"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1


# ===========================================================================
# POSITIVE CONTROL (soundness) — structurally-DIFFERENT but CORRECT impls that
# MUST verify (else SPEC-TOO-STRONG). Both keep the gold decision logic; they
# only reshape the executable form. No loop / no fold is introduced, so no
# induction lemma is needed (pilot pitfalls #2/#3 avoided).
# ===========================================================================

# pos-control-helper-reorder: compute the initial-position predicate ONCE into a
# local using the very @Pure helper the spec uses, DECIDE the delete branch first
# into a local, then run the ORDER branch before the DELETE branch. The order
# branch is rewritten without the redundant else-arm by setting has_order_field
# whenever can_order and only setting prefilled in the guarded sub-case.
# Behaviourally identical: (O) has_order_field == can_order, (P) prefilled iff
# can_order and at_initial, (D) delete iff can_delete and (extra or at_initial),
# (S) the ordering key still placed ahead of the deletion key. Must verify.
#
# NOTE: the DECISION order is reshuffled but the PLACEMENT order is not, because
# placement order is observable behaviour (S) rather than a free implementation
# choice — see the (S) discussion in the header. A variant that also swaps the
# placements is a genuinely different (and wrong) behaviour and lives in the
# uniqueness lane as uniq-delete-placed-first.
_POS_REORDER = """    # impl-start
    at_init = at_initial_position(index, initial_form_count)  # type: bool
    want_delete = can_delete and (can_delete_extra or at_init)  # type: bool
    if can_order:
        form.has_order_field = True
        form.aux_keys = form.aux_keys + PSeq(1)
        if at_init:
            form.order_field_prefilled = True
    if want_delete:
        form.has_delete_field = True
        form.aux_keys = form.aux_keys + PSeq(2)
    # impl-end"""

# pos-control-flag-fold: collapse both decisions into precomputed booleans, then
# assign each flag from its boolean and derive the whole placement sequence in ONE
# assignment from the @Pure helper (rather than appending key-by-key as the frozen
# impl does). A pure local-variable reshape; identical truth values and identical
# placement order. Must verify (else SPEC-TOO-STRONG) — and it is the control that
# (S) has not been over-fitted to the frozen impl's append-per-branch SHAPE: any
# impl reaching the same placement sequence by any route is admitted.
_POS_FLAGS = """    # impl-start
    at_init = at_initial_position(index, initial_form_count)  # type: bool
    want_order = can_order  # type: bool
    want_prefill = can_order and at_init  # type: bool
    want_delete = can_delete and (can_delete_extra or at_init)  # type: bool
    if want_order:
        form.has_order_field = True
    if want_prefill:
        form.order_field_prefilled = True
    if want_delete:
        form.has_delete_field = True
    form.aux_keys = placed_keys(want_order, want_delete)
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the precondition admits a normal F2P-shaped
# input (else PRECOND-TOO-STRONG). We CANNOT add a separate caller function: a
# new module-level def changes the projected spec view and breaks same_spec.
# Instead the admissibility witness is injected INSIDE the impl region (elided
# from the spec view) as a leading block: construct a fresh Form() and assert the
# exact Requires holds for the canonical F2P input (the empty_form bug config:
# can_delete=True, can_delete_extra=False, index=None, initial_form_count=0). The
# real impl then runs unchanged over the actual params. If the precondition could
# not be established for this legitimate input, the Asserts would fail =>
# PRECOND-TOO-STRONG. (No self-call: under the MustTerminate(2) obligation a
# re-invocation of the contracted routine itself has no strictly smaller measure
# and is rightly rejected — the witness instead establishes each Requires
# conjunct directly; the Form() construction (measure 1 < 2) exercises that the
# termination budget admits the bounded callee.)
# ===========================================================================
_ADMISS = """    # impl-start
    # --- admissibility witness for an F2P-shaped input (elided from spec view) ---
    adm = Form()
    # the fresh-form precondition (Acc + all-False + empty placement + count >= 0)
    # is establishable:
    Assert(Acc(adm.has_order_field) and Acc(adm.order_field_prefilled)
           and Acc(adm.has_delete_field) and Acc(adm.aux_keys))
    Assert(adm.has_order_field == False and adm.order_field_prefilled == False
           and adm.has_delete_field == False)
    Assert(adm.aux_keys == empty_key_sequence())
    # the empty_form bug configuration is a legitimate in-domain input; the
    # precondition (initial_form_count >= 0) is satisfiable by a concrete 0.
    Assert(0 >= 0)
    # --- end admissibility witness; the real impl follows unchanged ---
    if can_order:
        if index is not None and index < initial_form_count:
            form.has_order_field = True
            form.order_field_prefilled = True
            form.aux_keys = form.aux_keys + PSeq(1)
        else:
            form.has_order_field = True
            form.aux_keys = form.aux_keys + PSeq(1)
    if can_delete and (
        can_delete_extra or (index is not None and index < initial_form_count)
    ):
        form.has_delete_field = True
        form.aux_keys = form.aux_keys + PSeq(2)
    # impl-end"""


# ===========================================================================
# UNIQUENESS — rivals that share the spec exactly and change ONLY the impl. Each
# MUST be rejected; a verifying rival is a real verify-but-not-resolve break
# (SPEC-TOO-WEAK). Each carries the refinement argument that its faithful real
# patch would NOT resolve the F2P/P2P.
# ===========================================================================

# uniq-drop-guard: THE BUG. Drop the `index is not None` guard from the DELETE
# branch (exactly model_prepatch.py / the pre-patch code). For index None this
# evaluates `index < initial_form_count` on an Optional[int] — Nagini cannot
# discharge the precondition of `<` (index may be None), so the impl does NOT
# even verify. This is the formal image of the real
# `TypeError: '<' not supported between NoneType and int`.
# Refinement: the faithful real patch IS the pre-patch source; on the empty_form
# config (can_delete, not can_delete_extra, index None) it RAISES TypeError, so
# `print(my_formset.empty_form)` crashes and the F2P
# assertNotIn("DELETE", empty_form.fields) never reaches its assertion — the bug
# the issue reports. It does NOT resolve.
_UNIQ_DROP_GUARD = """    # impl-start
    if can_order:
        if index is not None and index < initial_form_count:
            form.has_order_field = True
            form.order_field_prefilled = True
            form.aux_keys = form.aux_keys + PSeq(1)
        else:
            form.has_order_field = True
            form.aux_keys = form.aux_keys + PSeq(1)
    if can_delete and (can_delete_extra or index < initial_form_count):
        form.has_delete_field = True
        form.aux_keys = form.aux_keys + PSeq(2)
    # impl-end"""

# uniq-none-counts-initial: PARTIAL-DOMAIN. Treat a positionless form (index
# None) as if it occupied an initial position in the DELETE branch: set the
# delete field whenever can_delete and (extra or index is None or at_initial).
# This is None-safe (it short-circuits before `<`), so it has a chance to verify
# — but it VIOLATES (D): for the bug config (can_delete, not extra, index None)
# it sets has_delete_field = True, while (D) with at_initial_position(None,n)==
# False requires FALSE. Rejected by Ensures (D).
# Refinement: its faithful real patch is `self.can_delete_extra or index is None
# or (index is not None and index < initial_form_count)` — the empty_form would
# then CARRY a DELETE field, so the F2P assertNotIn("DELETE", empty_form.fields)
# FAILS. Does NOT resolve.
_UNIQ_NONE_INITIAL = """    # impl-start
    if can_order:
        if index is not None and index < initial_form_count:
            form.has_order_field = True
            form.order_field_prefilled = True
            form.aux_keys = form.aux_keys + PSeq(1)
        else:
            form.has_order_field = True
            form.aux_keys = form.aux_keys + PSeq(1)
    if can_delete and (
        can_delete_extra
        or index is None
        or (index is not None and index < initial_form_count)
    ):
        form.has_delete_field = True
        form.aux_keys = form.aux_keys + PSeq(2)
    # impl-end"""

# uniq-delete-le-boundary: VALUE / boundary double-mask. Use `<=` instead of `<`
# in the DELETE branch's position test. None-safe (guarded), so it can verify
# on most inputs, but at the boundary index == initial_form_count it sets the
# delete field when (D) (which uses `<`) requires it absent. Rejected by (D).
# Refinement: a real patch using `index <= initial_form_count` would give the
# first EXTRA (non-initial) form (position == initial_form_count) a DELETE
# control when can_delete and not can_delete_extra — exactly what
# test_disable_delete_extra_formset_forms (the F2P sibling P2P
# assertNotIn("DELETE", forms[2]) at the initial/extra boundary) forbids. Does
# NOT resolve.
_UNIQ_DELETE_LE = """    # impl-start
    if can_order:
        if index is not None and index < initial_form_count:
            form.has_order_field = True
            form.order_field_prefilled = True
            form.aux_keys = form.aux_keys + PSeq(1)
        else:
            form.has_order_field = True
            form.aux_keys = form.aux_keys + PSeq(1)
    if can_delete and (
        can_delete_extra or (index is not None and index <= initial_form_count)
    ):
        form.has_delete_field = True
        form.aux_keys = form.aux_keys + PSeq(2)
    # impl-end"""

# uniq-prefill-always: PARTIAL-DOMAIN on the ORDERING prefill. Set
# order_field_prefilled = True for EVERY ordered form (drop the position test),
# matching (O) and (D) but VIOLATING (P): for an ordered form that is NOT at an
# initial position (index None, or index >= initial_form_count) (P) requires
# prefilled FALSE. Rejected by Ensures (P).
# Refinement: its faithful real patch builds the ordering IntegerField with
# initial=index+1 in BOTH arms (or unconditionally) — a positionless / extra
# ordered form would then carry a spurious non-None initial. Several P2P
# ordering tests ("Ordering works with blank fieldsets", "Ordering fields are
# allowed to be left blank") observe the blank initial on non-initial forms;
# does NOT resolve.
_UNIQ_PREFILL_ALWAYS = """    # impl-start
    if can_order:
        form.has_order_field = True
        form.order_field_prefilled = True
        form.aux_keys = form.aux_keys + PSeq(1)
    if can_delete and (
        can_delete_extra or (index is not None and index < initial_form_count)
    ):
        form.has_delete_field = True
        form.aux_keys = form.aux_keys + PSeq(2)
    # impl-end"""

# uniq-delete-ignore-extra: CONTROL/decision attack. Drop the can_delete_extra
# disjunct entirely: set the delete field iff can_delete and at_initial_position.
# Correct on the bug config (index None => no delete) but WRONG when
# can_delete_extra is True for an extra/positionless form: (D) requires
# has_delete_field == can_delete there, but this rival gives False. Rejected by
# (D).
# Refinement: a real patch dropping the `self.can_delete_extra or` disjunct
# regresses can_delete_extra=True formsets — extra forms would lose their DELETE
# control. test_can_delete_extra_formset_forms (P2P) asserts the DELETE field IS
# present on extra forms when can_delete_extra; does NOT resolve.
_UNIQ_IGNORE_EXTRA = """    # impl-start
    if can_order:
        if index is not None and index < initial_form_count:
            form.has_order_field = True
            form.order_field_prefilled = True
            form.aux_keys = form.aux_keys + PSeq(1)
        else:
            form.has_order_field = True
            form.aux_keys = form.aux_keys + PSeq(1)
    if can_delete and (index is not None and index < initial_form_count):
        form.has_delete_field = True
        form.aux_keys = form.aux_keys + PSeq(2)
    # impl-end"""

# uniq-order-iff-prefill (supporting): tie has_order_field to the position test
# instead of to can_order — set has_order_field only in the guarded arm, drop
# the else. Violates (O): an ordered non-initial form (index None or index >=
# count) must still HAVE the ordering field (has_order_field == can_order), but
# this rival leaves it False. Rejected by (O).
# Refinement: a real patch that builds the ORDERING field only on initial-
# position forms would omit it from extra/positionless ordered forms entirely —
# the ordering control would vanish from blank/extra forms ("Ordering works with
# blank fieldsets" P2P); does NOT resolve.
_UNIQ_ORDER_IFF_PREFILL = """    # impl-start
    if can_order and (index is not None and index < initial_form_count):
        form.has_order_field = True
        form.order_field_prefilled = True
        form.aux_keys = form.aux_keys + PSeq(1)
    if can_delete and (
        can_delete_extra or (index is not None and index < initial_form_count)
    ):
        form.has_delete_field = True
        form.aux_keys = form.aux_keys + PSeq(2)
    # impl-end"""

# uniq-selfrec-diverge: VACUITY / control-flow-effect. Replace the body with a
# bare self-recursion of the contracted routine. Every Ensures then holds
# VACUOUSLY (no normal exit exists), so under a partial-correctness-only
# contract this rival VERIFIES — exactly the audit's P1 witness (atk_6-shaped
# vacuity: the postconditions are discharged by the recursive call's contract,
# never computed). Rejected by the MustTerminate(2) termination obligation:
# the self-call has no strictly smaller measure, so Nagini reports an
# obligation leak. Without MustTerminate this rival VERIFIED (the pre-fix
# hole).
# Refinement: a real patch whose add_fields recurses into itself
# unconditionally never returns (RecursionError/hang); every F2P/P2P formset
# test errors out — it does NOT resolve.
_UNIQ_SELFREC = """    # impl-start
    configure_optional_fields(
        form, can_order, can_delete, can_delete_extra, index, initial_form_count
    )
    # impl-end"""

# uniq-delete-placed-first: PLACEMENT-ORDER attack — THE AUDIT COUNTEREXAMPLE
# (atk_11). Every DECISION is exactly gold's: (O) has_order_field == can_order,
# (P) prefilled iff can_order and at_initial, (D) delete iff can_delete and
# (extra or at_initial). It deviates ONLY in placing the deletion control on the
# form BEFORE the ordering control. Rejected by Ensures (S): a form granted both
# controls must carry them in placement order ordering-then-deletion, and this
# rival leaves the reverse.
# Refinement: its faithful real patch moves the DELETION_FIELD_NAME insert ahead
# of the ORDERING_FIELD_NAME insert in add_fields. Because form.fields is an
# ORDERED mapping whose iteration order is what the form renders, the patched
# repo then emits `<li>Delete: ...>` before `<li>Order: ...>`. Both F2P tests
# still pass (the positionless-deletion behaviour IS corrected), but the P2P
# 'FormSets with ordering + deletion.'
# (forms_tests.tests.test_formsets.FormsFormsetTestCase.
# test_formset_with_ordering_and_deletion) assertHTMLEqual's as_ul() against HTML
# placing `<li>Order: ...>` immediately BEFORE `<li>Delete: ...>` for all four
# forms, so it FAILS. Executed harness verdict on that faithful patch:
# resolved=False, completed=True, attempts=3, flaky=False. Does NOT resolve.
_UNIQ_DELETE_FIRST = """    # impl-start
    if can_delete and (
        can_delete_extra or (index is not None and index < initial_form_count)
    ):
        form.has_delete_field = True
        form.aux_keys = form.aux_keys + PSeq(2)
    if can_order:
        if index is not None and index < initial_form_count:
            form.has_order_field = True
            form.order_field_prefilled = True
            form.aux_keys = form.aux_keys + PSeq(1)
        else:
            form.has_order_field = True
            form.aux_keys = form.aux_keys + PSeq(1)
    # impl-end"""

# uniq-no-placement: PARTIAL-DOMAIN on the placement sequence. Get all three
# presence/prefill decisions right but never record a control as PLACED (leave the
# placement sequence empty). Rejected by Ensures (S): a form granted a control must
# carry that control's key in its placement sequence.
# Refinement: its faithful real patch decides correctly which auxiliary controls a
# form should get and then never inserts them into form.fields, so neither the
# ORDER nor the DELETE control is rendered at all. Every ordering/deletion P2P
# test that observes those controls in the rendered output (including 'FormSets
# with ordering + deletion.') fails, and the F2P sibling that asserts DELETE IS
# present on initial forms fails too. Does NOT resolve.
_UNIQ_NO_PLACEMENT = """    # impl-start
    if can_order:
        form.has_order_field = True
        if index is not None and index < initial_form_count:
            form.order_field_prefilled = True
    if can_delete and (
        can_delete_extra or (index is not None and index < initial_form_count)
    ):
        form.has_delete_field = True
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-control-helper-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_REORDER),
        "rationale": "branch-reordered + helper-into-local CORRECT impl (delete "
                     "branch first, order branch without redundant else). All "
                     "three Ensures (O)/(P)/(D) still hold; no loop/fold so no "
                     "induction lemma. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-flag-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_FLAGS),
        "rationale": "local-variable reshape: precompute want_order/want_prefill/"
                     "want_delete (each equal to its Ensures RHS) then assign. "
                     "Identical truth values; must verify, else SPEC-TOO-STRONG.",
    },
    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-empty-form",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "in-impl witness builds a fresh Form() and Asserts every "
                     "Requires conjunct for the canonical empty_form bug config "
                     "(can_delete=True, can_delete_extra=False, index=None, "
                     "initial=0). The precondition is establishable for this "
                     "legitimate F2P-shaped input; if not, PRECOND-TOO-STRONG. "
                     "The Form() construction also witnesses that the "
                     "MustTerminate(2) budget admits the bounded (measure 1) "
                     "constructor.",
    },
    # ---- uniqueness (must be rejected; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-drop-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_GUARD),
        "refinement": "this IS the pre-patch source: on (can_delete, not "
                      "can_delete_extra, index None) it raises TypeError "
                      "('<' on NoneType vs int), so empty_form crashes and the "
                      "F2P assertNotIn(\"DELETE\", empty_form.fields) cannot pass "
                      "— does NOT resolve.",
        "rationale": "Nagini cannot discharge the precondition of `<` on an "
                     "Optional[int] index (may be None) in the unguarded delete "
                     "branch — the impl does not verify. Rejection comes from the "
                     "precondition of the `<` operator (formal image of the "
                     "runtime TypeError).",
    },
    {
        "id": "uniq-none-counts-initial",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_NONE_INITIAL),
        "refinement": "real patch `... or index is None or (index is not None "
                      "and index < count)` gives the empty_form a DELETE field, "
                      "so the F2P assertNotIn(\"DELETE\", empty_form.fields) "
                      "FAILS — does NOT resolve.",
        "rationale": "None-safe but VIOLATES Ensures (D): for index None, "
                     "at_initial_position(None,n)==False so (D) requires "
                     "has_delete_field FALSE, but this sets it True. Rejected by "
                     "the deletion-presence postcondition (D).",
    },
    {
        "id": "uniq-delete-le-boundary",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DELETE_LE),
        "refinement": "real patch using `index <= initial_form_count` gives the "
                      "first EXTRA form (position == count) a DELETE control when "
                      "can_delete and not can_delete_extra — the P2P "
                      "assertNotIn(\"DELETE\", forms[i]) at the initial/extra "
                      "boundary fails; does NOT resolve.",
        "rationale": "off-by-one at the boundary index == initial_form_count: (D) "
                     "uses `<` (False there) but the rival's `<=` is True. "
                     "Rejected by the deletion-presence postcondition (D).",
    },
    {
        "id": "uniq-prefill-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_PREFILL_ALWAYS),
        "refinement": "real patch building the ordering IntegerField with "
                      "initial=index+1 in BOTH arms attaches a spurious non-None "
                      "initial to positionless/extra ordered forms; ordering P2P "
                      "tests observe the blank initial on non-initial forms — "
                      "does NOT resolve.",
        "rationale": "VIOLATES Ensures (P): order_field_prefilled must be "
                     "(can_order and at_initial_position), i.e. FALSE for a non-"
                     "initial ordered form, but this sets it True for every "
                     "ordered form. Rejected by the prefill postcondition (P).",
    },
    {
        "id": "uniq-delete-ignore-extra",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_IGNORE_EXTRA),
        "refinement": "real patch dropping the `self.can_delete_extra or` "
                      "disjunct removes the DELETE control from extra forms when "
                      "can_delete_extra is True; test_can_delete_extra_formset_"
                      "forms (P2P) asserts DELETE IS present on extra forms — "
                      "does NOT resolve.",
        "rationale": "VIOLATES Ensures (D): when can_delete_extra is True for an "
                     "extra/positionless form, (D) requires has_delete_field == "
                     "can_delete (True) but the rival gives False. Rejected by "
                     "the deletion-presence postcondition (D).",
    },
    {
        "id": "uniq-order-iff-prefill",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_ORDER_IFF_PREFILL),
        "refinement": "real patch building the ORDERING field only on initial-"
                      "position forms omits it from extra/positionless ordered "
                      "forms; the ordering control vanishes from blank/extra "
                      "forms ('Ordering works with blank fieldsets' P2P) — does "
                      "NOT resolve.",
        "rationale": "VIOLATES Ensures (O): has_order_field must equal can_order "
                     "for every ordered form, but this leaves it False for a non-"
                     "initial ordered form (index None or index >= count). "
                     "Rejected by the ordering-presence postcondition (O).",
    },
    {
        "id": "uniq-selfrec-diverge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_SELFREC),
        "refinement": "a real add_fields that unconditionally recurses into "
                      "itself never returns (RecursionError/hang); every "
                      "F2P/P2P formset test errors out — does NOT resolve. "
                      "This is the audit P1 witness shape: every Ensures held "
                      "vacuously and the rival verified before the "
                      "MustTerminate obligation was added.",
        "rationale": "rejected by the MustTerminate(2) termination obligation: "
                     "the bare self-call has no strictly smaller measure, so "
                     "Nagini reports an obligation leak. Under the pre-fix "
                     "contract (no MustTerminate) this rival VERIFIED — every "
                     "Ensures discharged vacuously by the recursive call's own "
                     "contract. Vacuity / control-flow-effect case.",
    },
    {
        "id": "uniq-delete-placed-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DELETE_FIRST),
        "refinement": "THE AUDIT COUNTEREXAMPLE (atk_11). Its faithful real "
                      "patch moves the DELETION_FIELD_NAME insert ahead of the "
                      "ORDERING_FIELD_NAME insert; since form.fields is an "
                      "ORDERED mapping whose iteration order is rendered, the "
                      "form emits `<li>Delete: ...>` before `<li>Order: ...>`. "
                      "Both F2P PASS but the P2P 'FormSets with ordering + "
                      "deletion.' assertHTMLEqual's Order immediately BEFORE "
                      "Delete and FAILS. Executed harness: resolved=False, "
                      "completed=True, attempts=3, flaky=False — does NOT "
                      "resolve.",
        "rationale": "every presence/prefill DECISION equals gold's; it deviates "
                     "only in the PLACEMENT order of the two controls. Rejected "
                     "by Ensures (S): a form granted both controls must carry "
                     "them ordering-key-then-deletion-key, and this rival leaves "
                     "the reverse. Before (S) existed this rival VERIFIED — it "
                     "is the verify-but-not-resolve hole (S) closes.",
    },
    {
        "id": "uniq-no-placement",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_NO_PLACEMENT),
        "refinement": "real patch that decides the auxiliary controls correctly "
                      "but never inserts them into form.fields renders neither "
                      "the ORDER nor the DELETE control; every ordering/deletion "
                      "P2P observing those controls fails, as does the F2P "
                      "sibling asserting DELETE IS present on initial forms — "
                      "does NOT resolve.",
        "rationale": "VIOLATES Ensures (S): the presence flags are right but the "
                     "placement sequence stays empty, while (S) requires a form "
                     "granted a control to carry that control's key. Pins that "
                     "(S) constrains WHICH keys are placed, not merely their "
                     "relative order.",
    },
]


# ===========================================================================
# AXIOM lane — no consumed @ContractOnly axioms (axioms region is comment-only),
# so there is no axiom Ensures to violate (no axiom-soundness case). The only
# obligation is CONTAINMENT for the A-reference: every index the model can pass
# to the real callee (in particular index None, the modeled fault) must lie in
# the post-gold callee's accepted domain — i.e. add_fields must NOT raise on any
# caller-reachable index, mirroring the model's None-graceful behaviour. The
# probe drives the REAL BaseFormSet.add_fields (post-gold, in-container) over the
# full reachable index domain {None} U {0..initial+2} and the bug flag config,
# asserting no TypeError and that DELETE presence == the model decision. (This is
# a lean restatement of axiom_check.py's containment slice; the full G-AX sweep
# lives in axiom_check.py.) apply_gold=True: the containment claim is about the
# post-gold callee the model abstracts.
# ===========================================================================

_AXIOM_CONTAINMENT_PROBE = r'''
import os, sys

def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            USE_TZ=False,
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={},
            ROOT_URLCONF=__name__,
        )
    django.setup()


def at_initial_position(index, initial):
    return (index is not None) and (index < initial)


def model_decision_delete(can_delete, can_delete_extra, index, initial):
    return can_delete and (can_delete_extra or at_initial_position(index, initial))


def main():
    _configure_django()
    from django import forms
    from django.forms.formsets import (
        formset_factory, DELETION_FIELD_NAME,
    )

    class MyForm(forms.Form):
        my_field = forms.CharField(required=False)

    checked = 0
    problems = []
    bools = [True, False]
    for n_initial in (0, 1, 2, 3):
        initial_data = [{"my_field": "x"} for _ in range(n_initial)]
        for can_order in bools:
            for can_delete in bools:
                for can_delete_extra in bools:
                    FS = formset_factory(
                        form=MyForm, extra=2,
                        can_order=can_order, can_delete=can_delete,
                        can_delete_extra=can_delete_extra,
                    )
                    fs = FS(initial=initial_data or None)
                    initial = fs.initial_form_count()
                    # the FULL caller-reachable index domain incl. None (empty_form)
                    indices = [None] + list(range(0, initial + 3))
                    for index in indices:
                        form = MyForm()
                        # CONTAINMENT: the post-gold callee must accept every
                        # reachable index (incl. None) without raising.
                        try:
                            fs.add_fields(form, index)
                        except TypeError as e:
                            problems.append(
                                "post-gold add_fields RAISED on caller-reachable "
                                "index=%r (initial=%d, can_delete=%s extra=%s): %s"
                                % (index, initial, can_delete, can_delete_extra, e))
                            continue
                        have = DELETION_FIELD_NAME in form.fields
                        want = model_decision_delete(
                            can_delete, can_delete_extra, index, initial)
                        if have != want:
                            problems.append(
                                "DELETE presence != model decision: real=%s "
                                "model=%s (index=%r initial=%d can_delete=%s "
                                "extra=%s)" % (have, want, index, initial,
                                               can_delete, can_delete_extra))
                        checked += 1

    # the issue's exact reproducer must be in-domain (no raise) and DELETE-free
    FS = formset_factory(form=MyForm, can_delete=True, can_delete_extra=False)
    fs = FS(initial=None)
    ef = fs.empty_form  # pre-patch raised TypeError here
    if DELETION_FIELD_NAME in ef.fields:
        problems.append("empty_form (can_delete, no extra) carries DELETE field")

    if problems:
        print("CONTAINMENT FAIL (%d):" % len(problems))
        for p in problems[:40]:
            print("  -", p)
        sys.exit(1)
    print("CONTAINMENT OK: post-gold add_fields accepts every caller-reachable "
          "index (incl. None) without raising and DELETE presence == model "
          "decision over %d configs; empty_form reproducer carries no DELETE."
          % checked)
    sys.exit(0)


if __name__ == "__main__":
    main()
'''


AXIOM_TESTS = [
    {
        "id": "ax-containment-index-domain",
        "axiom": "at_initial_position / add_fields A-reference",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AXIOM_CONTAINMENT_PROBE,
        "rationale": "no @ContractOnly axiom => no axiom-soundness obligation. "
                     "The containment claim: every index the model can pass to "
                     "the real callee (incl. None, the modeled fault) lies in the "
                     "post-gold add_fields accepted domain (no TypeError), and "
                     "the real DELETE presence == the model decision. A reachable "
                     "index outside the accepted domain (a raise) would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER. Mirrors axiom_check.py's "
                     "containment slice.",
    },
]
