# properties.py — PBT manifest for django__django-13741. NOT a Nagini module; a
# record of adversarial falsification cases the runner (swebench_nagini.pbt)
# executes. Spec cases are full model.py variants that share the FROZEN spec
# (same_spec; only the impl region differs) and are checked by Nagini verify;
# axiom cases are real-callee Docker probes (none here — no @ContractOnly
# axioms; the two deep models are A-reference, validated by axiom_check.py/G-AX).
#
# Defended surface (from model.py):
#   Both functions carry a MustTerminate precondition: the contract is TOTAL,
#   so an impl that never returns (loop or unbounded recursion) cannot satisfy
#   any postcondition clause vacuously.
#   make_field(required_kw, disabled_kw: Optional[bool]) -> Field
#     Postcondition pins ALL FOUR cases, fully grounded in the args:
#       required_kw is None   -> Result().required == False
#       required_kw not None  -> Result().required == required_kw
#       disabled_kw is None   -> Result().disabled == True   (THE CHANGE / F2P)
#       disabled_kw not None  -> Result().disabled == disabled_kw
#     No read-only inputs (params are plain Optional[bool]; no Acc obligations).
#   differs(self: Field, initial, data: Optional[List[int]]) -> bool
#     READ-ONLY inputs: Requires/Ensures Acc(self.disabled, 1/2),
#       Acc(list_pred(initial), 1/2), Acc(list_pred(data), 1/2)  <-- frame targets
#     Postcondition:
#       self.disabled       -> Result() == False
#       not self.disabled   -> Result() == (norm_seq(initial) != norm_seq(data))
#     norm_seq is a GROUNDED @Pure fold of the args (None->empty, else ToSeq(v));
#     there is no opaque answer-key to echo, so the ungrounded-oracle attack is
#     N/A here (see 'assessment') — the honest cheapest-impl positive control
#     stands in for it.

from pathlib import Path

INSTANCE = "django__django-13741"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Impl regions, verbatim, used as unique anchors for region-surgery. Editing
# ONLY the text between an # impl-start / # impl-end guarantees same_spec.
# ---------------------------------------------------------------------------

# make_field impl region body (model.py, between its impl markers)
_MF_IMPL = """    if required_kw is None:
        required = False
    else:
        required = required_kw
    if disabled_kw is None:
        disabled = True
    else:
        disabled = disabled_kw
    return Field(required, disabled)"""

# differs impl region body (model.py, between its impl markers)
_DF_IMPL = """    if self.disabled:
        return False
    return norm_seq(initial) != norm_seq(data)"""


SPEC_TESTS = [
    # ----------------------------------------------------------------- make_field
    {
        "id": "mf-pos-control-ternary",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE,
            _MF_IMPL,
            "    required = required_kw if required_kw is not None else False\n"
            "    disabled = disabled_kw if disabled_kw is not None else True\n"
            "    return Field(required, disabled)",
        ),
        "rationale": "Structurally-different but behaviourally-identical impl "
        "(ternary conditional expressions instead of if/else statements, and the "
        "named branch placed first). Must verify: the four grounded postcondition "
        "clauses are exactly satisfied. If it failed, the make_field spec would be "
        "SPEC-TOO-STRONG. Keeps no proof obligations beyond the trivial assignment "
        "+ constructor call the gold proof already discharges.",
    },
    {
        "id": "mf-disabled-default-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _MF_IMPL,
            "    if required_kw is None:\n"
            "        required = False\n"
            "    else:\n"
            "        required = required_kw\n"
            "    if disabled_kw is None:\n"
            "        disabled = False\n"          # <-- the pre-patch behaviour
            "    else:\n"
            "        disabled = disabled_kw\n"
            "    return Field(required, disabled)",
        ),
        "refinement": "This is model_prepatch.py's behaviour: an unnamed `disabled` "
        "falls back to the base Field default (False) instead of the patch's True. "
        "The faithful real patch is then `kwargs.setdefault('required', False)` "
        "WITHOUT the added `kwargs.setdefault('disabled', True)` — i.e. the pre-patch "
        "tree. That tree FAILS the F2P `test_readonly_field_has_changed` "
        "(`self.assertIs(field.disabled, True)`), so it does NOT resolve.",
        "rationale": "Rejected by the postcondition clause "
        "`Implies(disabled_kw is None, Result().disabled == True)` (make_field "
        "post-conditions): an unnamed disabled must default True, not False.",
    },
    {
        "id": "mf-required-default-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _MF_IMPL,
            "    if required_kw is None:\n"
            "        required = True\n"           # <-- wrong required default
            "    else:\n"
            "        required = required_kw\n"
            "    if disabled_kw is None:\n"
            "        disabled = True\n"
            "    else:\n"
            "        disabled = disabled_kw\n"
            "    return Field(required, disabled)",
        ),
        "refinement": "Defaults `required` to True. The faithful real patch would "
        "be `kwargs.setdefault('required', True)`, flipping the long-standing "
        "ReadOnlyPasswordHashField default (required=False) that the P2P render/form "
        "tests depend on — a disabled+required field would mark the change form "
        "invalid on an empty hash submission. It would not preserve the existing "
        "optional behaviour and would not faithfully resolve.",
        "rationale": "Rejected by `Implies(required_kw is None, Result().required "
        "== False)` (make_field post-conditions): an unnamed required must default "
        "False. Guards the I-tagged required default A2 against silent drift.",
    },
    {
        "id": "mf-ignore-explicit-disabled",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _MF_IMPL,
            "    if required_kw is None:\n"
            "        required = False\n"
            "    else:\n"
            "        required = required_kw\n"
            "    disabled = True\n"               # <-- always default; ignores explicit kw
            "    return Field(required, disabled)",
        ),
        "refinement": "Hard-codes disabled=True, ignoring an explicitly-passed "
        "`disabled=False`. The faithful real patch would replace "
        "`kwargs.setdefault('disabled', True)` with `kwargs['disabled'] = True`, "
        "which OVERWRITES a caller-supplied value rather than only filling an absent "
        "key. A caller that constructs `ReadOnlyPasswordHashField(disabled=False)` "
        "would silently get a disabled field — a behavioural divergence setdefault "
        "never causes; it breaks the setdefault contract the issue/patch rely on.",
        "rationale": "Rejected by `Implies(disabled_kw is not None, "
        "Result().disabled == disabled_kw)` (make_field post-conditions): an "
        "explicit flag must be preserved. Pins the setdefault-only semantics of A3.",
    },
    {
        "id": "mf-admiss-caller",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE,
            _MF_IMPL,
            "    # admissibility: the F2P-shaped call names neither flag (both\n"
            "    # carriers None). Witness that shape inline and assert the headline\n"
            "    # default the F2P test pins (disabled True, required False) is\n"
            "    # reached on it through the gold flag selection. (A literal\n"
            "    # self-call is no longer usable as the witness: the frozen spec\n"
            "    # carries a termination obligation, and a recursive self-invocation\n"
            "    # cannot present a strictly smaller measure — by design, since a\n"
            "    # never-returning impl was exactly the vacuous-verification escape.)\n"
            "    if required_kw is None:\n"
            "        required = False\n"
            "    else:\n"
            "        required = required_kw\n"
            "    if disabled_kw is None:\n"
            "        disabled = True\n"
            "    else:\n"
            "        disabled = disabled_kw\n"
            "    Assert(Implies(required_kw is None and disabled_kw is None,\n"
            "                   disabled == True and required == False))\n"
            "    return Field(required, disabled)",
        ),
        "rationale": "An inline witness on the F2P-shaped input (both flags unnamed = "
        "both carriers None, exactly `ReadOnlyPasswordHashField()`): an Assert that the "
        "gold flag selection yields disabled=True / required=False there. Must verify: "
        "the precondition (only the termination obligation, which any bounded caller "
        "can present) admits the normal input and the post is establishable. "
        "If it failed => PRECOND-TOO-STRONG.",
    },

    # ------------------------------------------------------------------- differs
    {
        "id": "df-pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE,
            _DF_IMPL,
            "    if not self.disabled:\n"
            "        return norm_seq(initial) != norm_seq(data)\n"
            "    return False",
        ),
        "rationale": "Structurally-different but behaviourally-identical impl: the "
        "enabled branch is placed first (`if not self.disabled: return compare`) with "
        "the disabled short-circuit falling through to `return False`. Must verify "
        "against both post clauses (disabled->False; enabled->the norm_seq "
        "inequality). If it failed => SPEC-TOO-STRONG. No extra proof obligation "
        "beyond what the gold proof already discharges (no induction/lemma).",
    },
    {
        "id": "df-frame-mutate-disabled",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _DF_IMPL,
            "    # FRAME MUTATION: overwrite the read-only self.disabled (held at\n"
            "    # only 1/2 permission) to force the disabled short-circuit and\n"
            "    # satisfy the postcondition vacuously.\n"
            "    self.disabled = True\n"
            "    return False",
        ),
        "refinement": "Writes to `self.disabled`, which differs holds at only "
        "Acc(self.disabled, 1/2) (read-only). The faithful real patch would have "
        "`Field.has_changed` MUTATE `self.disabled = True` and unconditionally return "
        "False — i.e. it would silently force EVERY field (including editable ones) "
        "to ignore submitted data forever. That destroys change detection for all "
        "enabled fields (UserCreationForm/SetPassword/AdminPasswordChange P2P tests "
        "submit and expect change detection), so it does not resolve.",
        "rationale": "MANDATORY frame-mutation probe. Rejected by the permission "
        "system: a half-permission field access `Acc(self.disabled, 1/2)` cannot be "
        "written (insufficient permission). The gold post clauses are kept verbatim "
        "so the rejection is attributable to the write, not a value mismatch. This is "
        "the #1 weakness class a byte-fuzzer never finds.",
    },
    {
        "id": "df-frame-mutate-data",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _DF_IMPL,
            "    # FRAME MUTATION: clear the read-only `data` list (held at only\n"
            "    # 1/2 permission) so the enabled comparison trivially matches\n"
            "    # initial on the cases the prover happens to explore.\n"
            "    if self.disabled:\n"
            "        return False\n"
            "    if data is not None:\n"
            "        data.append(0)  # ILLEGAL write to a read-only input (needs full permission)\n"
            "    return norm_seq(initial) != norm_seq(data)",
        ),
        "refinement": "Mutates the submitted `data` argument (`data.clear()`), held "
        "at only Acc(list_pred(data), 1/2). A faithful real patch in which "
        "has_changed CLEARS its `data` argument before comparing would corrupt the "
        "submitted value in place — the form would later read an emptied value, "
        "breaking every editable-field workflow (UserCreationForm validation, "
        "AdminPasswordChange) that re-reads cleaned data. It does not resolve.",
        "rationale": "Frame-mutation probe on a read-only list input. Rejected by the "
        "permission system: `data.clear()` needs full `list_pred(data)` permission but "
        "only 1/2 is held; also the Ensures must hand back Acc(list_pred(data),1/2) "
        "unchanged. The disabled short-circuit and the comparison are kept so the "
        "rejection is attributable to the in-place write.",
    },
    {
        "id": "df-drop-short-circuit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _DF_IMPL,
            "    return norm_seq(initial) != norm_seq(data)",
        ),
        "refinement": "Drops the disabled short-circuit and always compares. The "
        "faithful real patch would be a `Field.has_changed` WITHOUT the "
        "`if self.disabled: return False` guard. For a disabled field whose initial "
        "and submitted values differ, the real method would then report a change — "
        "the password hash field would be marked changed on every page render where "
        "the hidden submitted value differs from the stored hash. The F2P "
        "`test_readonly_field_has_changed` asserts `has_changed('aaa','bbb')` is "
        "False on the (disabled) field, so this does NOT resolve.",
        "rationale": "Partial-domain attack (correct on enabled fields, wrong on the "
        "disabled sub-domain). Rejected by `Implies(self.disabled, Result() == "
        "False)` (differs post-conditions): on a disabled field with differing "
        "values the comparison returns True, violating the short-circuit clause.",
    },
    {
        "id": "df-always-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _DF_IMPL,
            "    return False",
        ),
        "refinement": "This is model_prepatch_2.py: the deleted bespoke override's "
        "body `return False` unconditionally, ignoring self.disabled. The faithful "
        "real patch would KEEP the `ReadOnlyPasswordHashField.has_changed` override "
        "(`return False`) rather than removing it to inherit the base method. But the "
        "twin-artifact correctness oracle requires the field to inherit the GENERAL "
        "base decision; a constant-False override is unsound as the general field "
        "behaviour (an enabled field with differing values must report a change), "
        "which is the whole point of the fix — relying on `disabled`, not a constant. "
        "G-DIFF wires this to model_prepatch_2.",
        "rationale": "Partial-domain attack (correct on disabled fields, wrong on the "
        "enabled sub-domain). Rejected by `Implies(not self.disabled, Result() == "
        "(norm_seq(initial) != norm_seq(data)))` (differs post-conditions): an "
        "enabled field with differing values must report True.",
    },
    {
        "id": "df-none-not-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _DF_IMPL,
            "    if self.disabled:\n"
            "        return False\n"
            "    # Wrong normalisation: compare raw presence instead of treating\n"
            "    # None as the empty value; an empty list and None should be EQUAL.\n"
            "    if initial is None and data is not None and len(data) == 0:\n"
            "        return True\n"
            "    return norm_seq(initial) != norm_seq(data)",
        ),
        "refinement": "Diverges only on the None-vs-empty sub-domain: reports a "
        "change for an enabled field when initial is None and data is the empty "
        "value, whereas the spec treats None and '' as indistinguishable. The "
        "faithful real patch would be a `has_changed` that did NOT apply the "
        "`initial if initial is not None else ''` (and the data) normalisation — it "
        "would report spurious changes for a field whose stored value is None and "
        "whose submission is empty, the exact case Django's base method guards "
        "against (test_bug_19349_render_with_none_value P2P relies on the empty/None "
        "equivalence). It does not faithfully resolve.",
        "rationale": "Partial-domain attack on the None<->empty boundary. Rejected by "
        "`Implies(not self.disabled, Result() == (norm_seq(initial) != "
        "norm_seq(data)))`: norm_seq maps both None and the empty list to the empty "
        "PSeq, so they are equal — returning True here violates the clause.",
    },
    {
        "id": "df-admiss-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE,
            _DF_IMPL,
            "    # admissibility: the precondition must admit a normal F2P-shaped\n"
            "    # input. Construct the default (disabled) field shape and witness\n"
            "    # that the required read fraction is establishable for it; absent\n"
            "    # (None) values satisfy their guarded list_pred halves trivially.\n"
            "    # (A literal self-call is no longer usable as the witness: the\n"
            "    # frozen spec carries a termination obligation, and a recursive\n"
            "    # self-invocation cannot present a strictly smaller measure — by\n"
            "    # design, since a never-returning impl was exactly the\n"
            "    # vacuous-verification escape.)\n"
            "    g = Field(False, True)             # disabled by default (F2P field)\n"
            "    Assert(g.disabled == True)\n"
            "    Assert(Acc(g.disabled, 1 / 2))\n"
            "    if self.disabled:\n"
            "        return False\n"
            "    return norm_seq(initial) != norm_seq(data)",
        ),
        "rationale": "Construct the F2P-shaped default field (disabled True, the exact "
        "`ReadOnlyPasswordHashField()` shape) and assert the differs precondition's "
        "read fraction Acc(self.disabled,1/2) is establishable for it; the "
        "Implies-guarded list_pred halves are trivially satisfied by absent (None) "
        "values, and the termination obligation is presentable by any bounded caller. "
        "Must verify; if it failed => PRECOND-TOO-STRONG. The original gold differs "
        "body is preserved after the witness.",
    },
]


# No @ContractOnly axioms (meta.json axioms == []) and the two deep models are
# A-reference, validated against the real Django base field by axiom_check.py
# (G-AX). There is no consumed-axiom obligation for the runner to re-probe.
AXIOM_TESTS = []
