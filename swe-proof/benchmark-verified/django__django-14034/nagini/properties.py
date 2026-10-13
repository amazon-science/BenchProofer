# properties.py — PBT falsification battery for django__django-14034.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: edits live ONLY
# inside the single # impl-start / # impl-end region, which spec_view elides —
# so same_spec holds by construction) and are checked by Nagini verify; axiom
# cases are real-callee probes checked in Docker.
#
# DEFENDED SURFACE (what this spec protects — see model.py / refinement.md):
#
#   build_required_attrs(out, widget_mark, field_required, form_marks,
#                        is_partial_multi, field_disabled, subs) -> None
#     A VOID, mutating operation. It writes:
#        out.required_attr / out.disabled_attr   (Result2 tri-state slots, FULL perm)
#        subs[k].marker                           (per-constituent slot, FULL perm)
#     It only READS (HALF permission, directive 5):
#        Acc(list_pred(subs), 1/2)                <-- list spine read-only
#        subs[k].widget_mark   @ 1/2              <-- READ-ONLY constituent input
#        subs[k].field_required @ 1/2             <-- READ-ONLY constituent input
#     So has_readonly_input is TRUE => the FRAME-MUTATION probe is MANDATORY.
#
#   The guard is g = widget_mark and field_required and form_marks. The
#   load-bearing postcondition is four-way:
#     (disabled)  Implies(field_disabled, out.disabled_attr==1)
#                 Implies(not field_disabled, out.disabled_attr==-1)
#     (regime A)  g and is_partial_multi      -> out.required_attr==-1 AND
#                   Forall k: subs[k].marker == constituent_marker(
#                       subs[k].widget_mark, subs[k].field_required)
#     (regime B)  g and not is_partial_multi  -> out.required_attr==1 AND
#                   Forall k: subs[k].marker==-1
#     (guard off) not g                       -> out.required_attr==-1 AND
#                   Forall k: subs[k].marker==-1
#
#   ORACLE GROUNDING: constituent_marker is a @Pure helper that is the fully
#   unfolded boolean product of the two READ-ONLY inputs
#   (`if widget_mark and field_required: return 1; return 0`). It is NOT an
#   opaque answer-key oracle — there is no separately-supplied "right answer" an
#   impl could echo without doing the work; the regime-A clause already pins the
#   marker to a function of the args. Hence the UNGROUNDED-ORACLE-ECHO class is
#   N/A: the cheapest honest regime-A impl IS the gold per-constituent if/else,
#   and its positive control is a reorder + branch-flip (case 1). See assessment.
#
#   The BEHAVIOURAL DISCRIMINATOR (the bug fix, this ticket): in regime A
#   (required MultiValueField, require_all_fields=False, MultiWidget) the patch
#   does NOT set the aggregate `required` and instead sets EACH subwidget's
#   required attr to `use_required_attribute(initial) and subfield.required`. The
#   pre-patch always set the aggregate `required` (so EVERY subinput rendered
#   `required`). The F2P (test_render_required_attributes) asserts the FIRST
#   (required) subinput carries `required` and the SECOND (optional) one does
#   NOT. The aggregate-required rival (case 4) and the per-constituent
#   ignore-field_required rival (case 5) ARE that pre-patch / wrong behaviour.
#
#   CONTROL-FLOW-EFFECT class is N/A: build_required_attrs returns None and never
#   raises; the only effects are the slot/marker mutations, all captured by the
#   value abstraction (the tri-state ints + per-constituent marker). There is no
#   raise/return difference invisible to the abstraction to discriminate with a
#   capability token. See assessment.
#
#   No @ContractOnly axioms (meta.axioms == []). The deep models
#   constituent_marker + the rendering rule are A-references already validated ==
#   the REAL Widget.use_required_attribute and the REAL attrs.html template by
#   axiom_check.py (G-AX): 112 (widget kind x initial x required) combinations +
#   20000 boolean fuzz + F2P regime-A and regime-B reproduced end-to-end against
#   the REAL patched build_widget_attrs, exit 0. That IS the real-callee axiom
#   lane for this instance; re-encoding it as a Docker probe would duplicate, not
#   strengthen, it. Hence AXIOM_TESTS = []. See assessment.
from pathlib import Path

INSTANCE = "django__django-14034"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# The ONE impl region (between # impl-start / # impl-end). Editing only this
# block keeps spec_view (hence same_spec) byte-identical. The invariants region
# is NESTED inside impl and is also elided by spec_view, so it is part of the
# editable surface — but we keep the gold invariants VERBATIM on every variant
# whose loop they still frame, so a rejection is attributable to the impl
# change, not to a dropped loop invariant (pilot failure mode #2).
# ===========================================================================
_IMPL_GOLD = """    if widget_mark and field_required and form_marks:
        if is_partial_multi:
            i = 0
            while i < len(subs):
                # invariants-start
                Invariant(Acc(list_pred(subs), 1 / 2))
                Invariant(0 <= i and i <= len(subs))
                Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(subs),
                    Acc(subs[k].widget_mark, 1 / 2) and Acc(subs[k].field_required, 1 / 2)
                    and Acc(subs[k].marker)),
                    [[subs[k]]])))
                Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                    subs[k].marker == constituent_marker(subs[k].widget_mark, subs[k].field_required)),
                    [[subs[k]]])))
                Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(subs),
                    subs[k].marker == -1), [[subs[k]]])))
                Invariant(MustTerminate(len(subs) - i + 1))
                # invariants-end
                sub = subs[i]
                if sub.widget_mark and sub.field_required:
                    sub.marker = 1
                else:
                    sub.marker = 0
                i = i + 1
        else:
            out.required_attr = 1
    if field_disabled:
        out.disabled_attr = 1"""

assert _IMPL_GOLD in _BASE, "impl anchor drift: build_required_attrs body not verbatim"


# ===========================================================================
# (1) POSITIVE CONTROL — structurally different but CORRECT (verify).
# Two value-neutral reshapes:
#   (a) the INDEPENDENT `if field_disabled` block is hoisted to the TOP of the
#       body (it touches only out.disabled_attr, so it commutes with the
#       required-marker logic);
#   (b) the per-constituent branch is FLIPPED: test the negation first and
#       assign 0, else assign 1 — same value as `1 if (wm and fr) else 0`.
# Every gold loop invariant is kept VERBATIM (they still frame the same loop).
# If a faithful, structurally-different correct impl could NOT verify against
# this spec => SPEC-TOO-STRONG.
# ===========================================================================
_IMPL_POS = """    if field_disabled:
        out.disabled_attr = 1
    if widget_mark and field_required and form_marks:
        if is_partial_multi:
            i = 0
            while i < len(subs):
                # invariants-start
                Invariant(Acc(list_pred(subs), 1 / 2))
                Invariant(0 <= i and i <= len(subs))
                Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(subs),
                    Acc(subs[k].widget_mark, 1 / 2) and Acc(subs[k].field_required, 1 / 2)
                    and Acc(subs[k].marker)),
                    [[subs[k]]])))
                Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                    subs[k].marker == constituent_marker(subs[k].widget_mark, subs[k].field_required)),
                    [[subs[k]]])))
                Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(subs),
                    subs[k].marker == -1), [[subs[k]]])))
                Invariant(MustTerminate(len(subs) - i + 1))
                # invariants-end
                sub = subs[i]
                if not (sub.widget_mark and sub.field_required):
                    sub.marker = 0
                else:
                    sub.marker = 1
                i = i + 1
        else:
            out.required_attr = 1"""

# ===========================================================================
# (2) ADMISSIBILITY — the precondition admits a normal F2P-shaped input (verify).
# We cannot add a top-level caller (that leaves the impl region and breaks
# same_spec). Instead, in-region, re-derive that the Requires facts are usable
# and reach a normal (non-raising) return: assert the half-permission spine is
# readable (len(subs) >= 0) and the two full-permission output slots arrive at
# their required initial state (out.required_attr == -1 and out.disabled_attr ==
# -1, from the Requires) before running the gold body. If the precondition were
# vacuous / over-strong these facts could not be established for a normal input
# => PRECOND-TOO-STRONG. The gold body (unchanged) then verifies on top.
# ===========================================================================
_IMPL_ADMISS = """    Assert(len(subs) >= 0)
    Assert(out.required_attr == -1 and out.disabled_attr == -1)
    if widget_mark and field_required and form_marks:
        if is_partial_multi:
            i = 0
            while i < len(subs):
                # invariants-start
                Invariant(Acc(list_pred(subs), 1 / 2))
                Invariant(0 <= i and i <= len(subs))
                Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(subs),
                    Acc(subs[k].widget_mark, 1 / 2) and Acc(subs[k].field_required, 1 / 2)
                    and Acc(subs[k].marker)),
                    [[subs[k]]])))
                Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                    subs[k].marker == constituent_marker(subs[k].widget_mark, subs[k].field_required)),
                    [[subs[k]]])))
                Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(subs),
                    subs[k].marker == -1), [[subs[k]]])))
                Invariant(MustTerminate(len(subs) - i + 1))
                # invariants-end
                sub = subs[i]
                if sub.widget_mark and sub.field_required:
                    sub.marker = 1
                else:
                    sub.marker = 0
                i = i + 1
        else:
            out.required_attr = 1
    if field_disabled:
        out.disabled_attr = 1"""

# ===========================================================================
# (3) FRAME-MUTATION — write to a READ-ONLY constituent input (reject).
# MANDATORY: subs[k].widget_mark / subs[k].field_required are held at HALF
# permission (Acc(...,1/2)); the operation may only READ them. Inside the
# regime-A loop, after reading sub = subs[i] (in-bounds via 0 <= i < len(subs)),
# we write the VALUE-NEUTRAL self-assignment sub.field_required =
# sub.field_required. The read is fine at 1/2, but the WRITE needs FULL
# permission, which the Requires never grants => Nagini rejects for INSUFFICIENT
# PERMISSION. The gold invariants/asserts are kept VERBATIM so the rejection is
# attributable to the write, not to a spec change. A byte-fuzzer never thinks to
# mutate the input — this is the project's #1 weakness class.
# ===========================================================================
_IMPL_FRAME = """    if widget_mark and field_required and form_marks:
        if is_partial_multi:
            i = 0
            while i < len(subs):
                # invariants-start
                Invariant(Acc(list_pred(subs), 1 / 2))
                Invariant(0 <= i and i <= len(subs))
                Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(subs),
                    Acc(subs[k].widget_mark, 1 / 2) and Acc(subs[k].field_required, 1 / 2)
                    and Acc(subs[k].marker)),
                    [[subs[k]]])))
                Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                    subs[k].marker == constituent_marker(subs[k].widget_mark, subs[k].field_required)),
                    [[subs[k]]])))
                Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(subs),
                    subs[k].marker == -1), [[subs[k]]])))
                Invariant(MustTerminate(len(subs) - i + 1))
                # invariants-end
                sub = subs[i]
                sub.field_required = sub.field_required
                if sub.widget_mark and sub.field_required:
                    sub.marker = 1
                else:
                    sub.marker = 0
                i = i + 1
        else:
            out.required_attr = 1
    if field_disabled:
        out.disabled_attr = 1"""

# ===========================================================================
# (4) AGGREGATE-IN-REGIME-A — the PRE-PATCH bug (reject). This is exactly
# model_prepatch.py: in regime A (guard holds AND is_partial_multi) set the
# AGGREGATE marker out.required_attr = 1 (and do not set per-constituent
# markers), the old unconditional `attrs['required'] = True`. The regime-A
# postcondition pins out.required_attr == -1 (aggregate marker NOT applied) AND
# subs[k].marker == constituent_marker(...); the verifier reports the
# aggregate-slot clause first => reject. Keep gold framing where it still holds
# (no loop here; the regime-A body is just the aggregate assignment).
# ===========================================================================
_IMPL_PREPATCH = """    if widget_mark and field_required and form_marks:
        out.required_attr = 1
    if field_disabled:
        out.disabled_attr = 1"""

# ===========================================================================
# (5) PARTIAL-DOMAIN / drop field_required (reject). Keep the per-constituent
# loop and its invariants, but in the body IGNORE the subfield's own required
# flag: assign sub.marker = 1 iff sub.widget_mark (dropping the `and
# sub.field_required` term). This is the per-constituent analogue of the
# pre-patch bug: an OPTIONAL subfield (field_required False) whose widget reports
# the marker (widget_mark True — every TextInput does) wrongly receives marker 1.
# The regime-A clause subs[k].marker == constituent_marker(widget_mark,
# field_required) requires constituent_marker(True, False) == 0, so the
# invariant cannot re-close after the offending element => reject. This diverges
# exactly on the optional-subfield sub-domain (the second input in the F2P).
# ===========================================================================
_IMPL_PARTIAL = """    if widget_mark and field_required and form_marks:
        if is_partial_multi:
            i = 0
            while i < len(subs):
                # invariants-start
                Invariant(Acc(list_pred(subs), 1 / 2))
                Invariant(0 <= i and i <= len(subs))
                Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(subs),
                    Acc(subs[k].widget_mark, 1 / 2) and Acc(subs[k].field_required, 1 / 2)
                    and Acc(subs[k].marker)),
                    [[subs[k]]])))
                Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                    subs[k].marker == constituent_marker(subs[k].widget_mark, subs[k].field_required)),
                    [[subs[k]]])))
                Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(subs),
                    subs[k].marker == -1), [[subs[k]]])))
                Invariant(MustTerminate(len(subs) - i + 1))
                # invariants-end
                sub = subs[i]
                if sub.widget_mark:
                    sub.marker = 1
                else:
                    sub.marker = 0
                i = i + 1
        else:
            out.required_attr = 1
    if field_disabled:
        out.disabled_attr = 1"""

# ===========================================================================
# (6) REGIME-B MISS — drop the aggregate marker in regime B (reject). In regime
# B (guard holds AND not is_partial_multi) the gold sets out.required_attr = 1;
# this rival leaves it unset (deletes the `else: out.required_attr = 1`). The
# regime-B postcondition pins out.required_attr == 1, so it fails => reject. This
# isolates the regime-B aggregate clause (ordinary required fields).
# ===========================================================================
_IMPL_REGIMEB = """    if widget_mark and field_required and form_marks:
        if is_partial_multi:
            i = 0
            while i < len(subs):
                # invariants-start
                Invariant(Acc(list_pred(subs), 1 / 2))
                Invariant(0 <= i and i <= len(subs))
                Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(subs),
                    Acc(subs[k].widget_mark, 1 / 2) and Acc(subs[k].field_required, 1 / 2)
                    and Acc(subs[k].marker)),
                    [[subs[k]]])))
                Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                    subs[k].marker == constituent_marker(subs[k].widget_mark, subs[k].field_required)),
                    [[subs[k]]])))
                Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(subs),
                    subs[k].marker == -1), [[subs[k]]])))
                Invariant(MustTerminate(len(subs) - i + 1))
                # invariants-end
                sub = subs[i]
                if sub.widget_mark and sub.field_required:
                    sub.marker = 1
                else:
                    sub.marker = 0
                i = i + 1
    if field_disabled:
        out.disabled_attr = 1"""

# ===========================================================================
# (7) DISABLED DROP — frame/observable miss on the disabled slot (reject). Get
# the mandatory marker exactly right but DELETE the `if field_disabled:
# out.disabled_attr = 1` block. The postcondition Implies(field_disabled,
# out.disabled_attr == 1) then fails for a disabled field => reject. The disabled
# assignment is unchanged by the patch (tag I) but the spec pins it for frame
# exactness; a rival that drops it is observably wrong on disabled fields.
# ===========================================================================
_IMPL_NODISABLED = """    if widget_mark and field_required and form_marks:
        if is_partial_multi:
            i = 0
            while i < len(subs):
                # invariants-start
                Invariant(Acc(list_pred(subs), 1 / 2))
                Invariant(0 <= i and i <= len(subs))
                Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(subs),
                    Acc(subs[k].widget_mark, 1 / 2) and Acc(subs[k].field_required, 1 / 2)
                    and Acc(subs[k].marker)),
                    [[subs[k]]])))
                Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                    subs[k].marker == constituent_marker(subs[k].widget_mark, subs[k].field_required)),
                    [[subs[k]]])))
                Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(subs),
                    subs[k].marker == -1), [[subs[k]]])))
                Invariant(MustTerminate(len(subs) - i + 1))
                # invariants-end
                sub = subs[i]
                if sub.widget_mark and sub.field_required:
                    sub.marker = 1
                else:
                    sub.marker = 0
                i = i + 1
        else:
            out.required_attr = 1"""


SPEC_TESTS = [
    {
        "id": "pos-control-hoist-disabled-flip-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_POS),
        "rationale": "Structurally different but correct: the independent "
                     "`if field_disabled` block is hoisted to the top (commutes — "
                     "touches only out.disabled_attr) and the per-constituent branch "
                     "is flipped (test the negation first, assign 0, else 1 — same "
                     "value as `1 if (wm and fr) else 0`). Every gold loop invariant "
                     "is kept verbatim. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility-readonly-spine-and-init-slots",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_ADMISS),
        "rationale": "In-region re-derivation that the precondition admits a normal "
                     "F2P-shaped input: the half-permission spine is readable "
                     "(len(subs) >= 0) and the two full-permission output slots arrive "
                     "in their required initial state (out.required_attr == -1 and "
                     "out.disabled_attr == -1, from the Requires) before the gold body "
                     "runs and reaches a normal return. If the precondition were "
                     "vacuous or over-strong these could not be established => "
                     "PRECOND-TOO-STRONG. Source: the Requires (initial-state + "
                     "half-permission spine).",
    },
    {
        "id": "frame-mutation-write-field_required",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_FRAME),
        "refinement": "A faithful real patch that wrote back into a read-only "
                      "constituent input — e.g. assigned to subfield.required (or to "
                      "the subwidget's use_required_attribute result) while building "
                      "the per-constituent marker — would mutate the subfield's own "
                      "mandatory flag. That flag drives MultiValueField.clean / "
                      "is_valid (the validation loop over self.fields), so corrupting "
                      "it would change whether the form validates. The F2P "
                      "(test_render_required_attributes) asserts the SECOND "
                      "PartiallyRequiredForm ({'f_0':'','f_1':''}) is NOT valid; a "
                      "patch that mutated subfield.required would alter that outcome "
                      "and would NOT faithfully resolve the F2P.",
        "rationale": "subs[k].field_required is held at Acc(...,1/2). The value-neutral "
                     "self-assignment sub.field_required = sub.field_required reads "
                     "(ok at 1/2) then WRITES, which needs FULL permission the Requires "
                     "never grants => Nagini rejects for INSUFFICIENT PERMISSION. "
                     "Source: the permission system + the Acc(subs[k].field_required, "
                     "1/2) Requires. Gold invariants kept verbatim so the rejection is "
                     "attributable to the write.",
    },
    {
        "id": "aggregate-in-regime-a-prepatch-bug",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_PREPATCH),
        "refinement": "This IS the pre-patch behaviour (model_prepatch.py): inside the "
                      "guard always set the AGGREGATE `required` (attrs['required'] = "
                      "True), no per-constituent branch. For the F2P scenario (required "
                      "MultiValueField, require_all_fields=False, two TextInputs) it "
                      "renders the aggregate `required`, so BOTH subinputs carry "
                      "`required`. test_render_required_attributes asserts the SECOND "
                      "(optional) subinput '<input ... name=\"f_1\" id=\"id_f_1\">' has "
                      "NO `required`, so the faithful pre-patch does NOT resolve "
                      "(this is exactly the reported bug).",
        "rationale": "In regime A this sets out.required_attr = 1, but the regime-A "
                     "postcondition pins out.required_attr == -1 (aggregate marker NOT "
                     "applied) AND subs[k].marker == constituent_marker(...); the "
                     "verifier reports the aggregate-slot clause first => reject. "
                     "Source: the regime-A out.required_attr == -1 postcondition "
                     "clause (the G-DIFF discriminator).",
    },
    {
        "id": "partial-domain-ignore-field_required",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_PARTIAL),
        "refinement": "A faithful real patch that assigned subwidget.attrs['required'] "
                      "= subwidget.use_required_attribute(self.initial) ALONE (dropping "
                      "the `and subfield.required` term) would set `required` on every "
                      "subwidget whose widget reports it — including the OPTIONAL "
                      "subfield. In the F2P both subwidgets are TextInputs "
                      "(use_required_attribute is True), so the SECOND (optional) "
                      "subinput would wrongly carry `required`. "
                      "test_render_required_attributes asserts '<input ... name=\"f_1\" "
                      "id=\"id_f_1\">' has NO `required`, so the patch does NOT resolve. "
                      "It diverges precisely on the optional-subfield sub-domain.",
        "rationale": "Assigning sub.marker = 1 iff sub.widget_mark (ignoring "
                     "sub.field_required) violates the regime-A clause subs[k].marker "
                     "== constituent_marker(widget_mark, field_required) for any "
                     "constituent with widget_mark True and field_required False "
                     "(constituent_marker(True, False) == 0, rival gives 1); the loop "
                     "invariant cannot re-close after that element => reject. Source: "
                     "the per-constituent regime-A postcondition clause.",
    },
    {
        "id": "regime-b-drop-aggregate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_REGIMEB),
        "refinement": "A faithful real patch that omitted the `else: attrs['required'] "
                      "= True` branch would stop setting the aggregate `required` for "
                      "ORDINARY required fields (regime B — the common, non-MVF case). "
                      "Required single-widget fields would silently lose their "
                      "`required` HTML attribute, regressing the broad required-field "
                      "rendering the existing suite depends on (e.g. the unchanged "
                      "required-attribute behaviour the P2P forms_tests rely on); the "
                      "patch would not resolve without breaking those.",
        "rationale": "Deleting `else: out.required_attr = 1` leaves out.required_attr "
                     "== -1 in regime B, but the regime-B postcondition pins "
                     "out.required_attr == 1 => reject. Source: the regime-B aggregate "
                     "postcondition clause.",
    },
    {
        "id": "disabled-slot-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_NODISABLED),
        "refinement": "A faithful real patch that dropped the unchanged `if "
                      "self.field.disabled: attrs['disabled'] = True` block would stop "
                      "emitting the `disabled` attribute for disabled fields, an "
                      "observable regression the P2P suite covers "
                      "(test_clean_disabled_multivalue / disabled-field rendering). "
                      "The patch would not resolve without breaking disabled-field "
                      "behaviour.",
        "rationale": "Deleting the `if field_disabled` block leaves out.disabled_attr "
                     "== -1 even when field_disabled is True, but the postcondition "
                     "pins Implies(field_disabled, out.disabled_attr == 1) => reject. "
                     "Source: the disabled postcondition clause (frame exactness).",
    },
]

# No Docker AXIOM_TESTS: meta.axioms == [] (no @ContractOnly axiom). The deep
# models constituent_marker + the rendering rule are A-references already
# validated == the REAL Widget.use_required_attribute and the REAL attrs.html
# template by axiom_check.py (G-AX): 112 (widget kind x initial x required)
# combinations + 20000 boolean fuzz + the F2P regime-A and regime-B scenarios
# reproduced end-to-end against the REAL patched BoundField.build_widget_attrs,
# imports Django + stdlib only, exit 0. That established real-callee check IS the
# axiom lane for this instance; re-encoding it as a Docker probe would duplicate,
# not strengthen, it. See 'assessment' in the structured return.
AXIOM_TESTS = []
