# properties.py — PBT falsification battery for django__django-16527.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) parses. Spec cases are full model.py variants that share
# the FROZEN spec byte-for-byte (region-surgery edits ONLY inside
# # impl-start/# impl-end) and are checked by Nagini verify + same_spec. There
# are no @ContractOnly axioms / A-reference deep models in this bundle, so
# AXIOM_TESTS = [].
#
# DEFENDED SURFACE (read from model.py / refinement.md / instance.json):
#   save_as_new_visible(is_popup, may_add, may_change, editing_existing,
#                       save_as_enabled) -> bool
#   Load-bearing postcondition (a *biconditional* pinning ALL 2^5 inputs):
#       Result() == (not is_popup and may_add and editing_existing
#                                  and save_as_enabled)
#   The gold patch changed the permission operand from has_change_permission
#   (== may_change here) to has_add_permission (== may_add). The F2P test
#   `test_submit_row_save_as_new_add_permission_required` builds two viewers:
#     - change-but-not-add (may_add=False, may_change=True, is_popup=False,
#       editing_existing=True, save_as_enabled=True) -> control MUST be hidden;
#     - add-and-change (may_add=True, ...) -> control MUST be shown.
#
# Why most weakness classes are N/A here (justified in StructuredOutput.assessment):
#   * FRAME-MUTATION: every parameter is an immutable `bool` passed by value;
#     there is NO `Acc(x,1/2)` read-only reference in the Requires, so there is
#     no permission to overwrite. Not applicable — replaced by honest positive
#     controls + partial-domain rivals.
#   * UNGROUNDED-ORACLE ECHO: the postcondition's oracle is the GROUNDED boolean
#     formula over the args themselves (fully unfolded, no @Pure helper, no
#     opaque marker). There is nothing to "echo" without doing the work — any
#     impl satisfying `== formula` IS the formula. So no wrong echo exists;
#     instead we supply the cheapest honest impl as a positive control.
#   * CONTROL-FLOW-EFFECT: pure total value function, no raise / no side effect /
#     no early return path distinguishable from the value. N/A.
#
# The biconditional makes the spec maximally tight: ANY impl whose value differs
# from the formula on even one of the 32 assignments must be rejected. The
# uniqueness rivals below each diverge on the F2P discriminating input (or a
# neighbour), so a faithful real patch with that logic would FAIL the F2P.

from pathlib import Path

INSTANCE = "django__django-16527"
FLOAT_ENCODING = None  # meta.json float_encoding is null; the function is pure boolean logic

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact gold impl-region body (verbatim between # impl-start / # impl-end).
_GOLD_IMPL = (
    "    show_save_as_new = (\n"
    "        not is_popup and may_add and editing_existing and save_as_enabled\n"
    "    )\n"
    "    return show_save_as_new"
)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found in base")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(new_body: str) -> str:
    """Return _BASE with the gold impl body replaced by new_body (edits ONLY
    inside the impl region; spec_view is untouched => same_spec holds)."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


SPEC_TESTS = [
    # ----------------------------------------------------------------- soundness
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different but LOGICALLY IDENTICAL: conjuncts reordered and
        # the local binding reshaped (parenthesised pairing differs from gold).
        # Conjunction is commutative/associative so the value is unchanged; the
        # verifier discharges this without any induction lemma. Keeps no framing
        # asserts because there is no loop / @Pure fold to frame.
        "module": _impl(
            "    visible = (\n"
            "        (editing_existing and save_as_enabled)\n"
            "        and (may_add and (not is_popup))\n"
            "    )\n"
            "    return visible"
        ),
        "rationale": (
            "a structurally-different but logically-equal impl (reordered + "
            "re-parenthesised conjuncts) MUST verify against the biconditional "
            "postcondition; if it cannot => SPEC-TOO-STRONG. No lemma needed: "
            "boolean and is commutative/associative, auto-discharged."
        ),
    },
    {
        "id": "pos-control-cheapest-inline",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest honest impl: return the formula inline with no local.
        # This is the grounded-oracle positive control standing in for the
        # (non-existent) ungrounded-echo case.
        "module": _impl(
            "    return not is_popup and may_add and editing_existing and save_as_enabled"
        ),
        "rationale": (
            "cheapest faithful impl (inline return of the grounded formula) must "
            "verify; this is the honest positive control replacing the N/A "
            "ungrounded-oracle echo (the oracle is the grounded formula itself)."
        ),
    },
    # -------------------------------------------------------------- admissibility
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        # A caller asserts the precondition (trivial: plain bools) admits the F2P
        # add-and-change viewer and that the postcondition yields the expected
        # True for it. The impl is the gold impl; the assertions exercise the
        # Requires/Ensures on a concrete F2P-shaped input.
        "module": _impl(
            _GOLD_IMPL
            + "\n\n\n"
            "def _admiss_caller() -> None:\n"
            "    # F2P add-and-change viewer on a real change page with save_as on.\n"
            "    out = save_as_new_visible(False, True, True, True, True)\n"
            "    Assert(out == True)\n"
            "    # F2P change-but-not-add viewer: control MUST be withheld.\n"
            "    out2 = save_as_new_visible(False, False, True, True, True)\n"
            "    Assert(out2 == False)"
        ),
        "rationale": (
            "the precondition (all plain bools, nothing mutated) must admit a "
            "normal F2P-shaped input and the postcondition must pin the expected "
            "True/False; if the caller cannot verify => PRECOND-TOO-STRONG."
        ),
    },
    # -------------------------------------------------- uniqueness (the real bug)
    {
        "id": "weak-prepatch-may-change",
        "kind": "uniqueness",
        "expect": "reject",
        # The ACTUAL bug / model_prepatch: gate on may_change (change permission)
        # instead of may_add (add permission). Diverges from the formula on every
        # input where add- and change-permission disagree.
        "module": _impl(
            "    show_save_as_new = (\n"
            "        not is_popup and may_change and editing_existing and save_as_enabled\n"
            "    )\n"
            "    return show_save_as_new"
        ),
        "refinement": (
            "its faithful real patch keeps the pre-patch `and has_change_permission` "
            "(== may_change) gate. On the F2P change-but-not-add viewer "
            "(has_add_permission=False, has_change_permission=True, change=True, "
            "save_as=True, is_popup=False) it yields show_save_as_new=True, but the "
            "F2P test asserts it is False => FAIL_TO_PASS NOT resolved."
        ),
        "rationale": (
            "rejected by the biconditional postcondition Result() == (... may_add "
            "...): may_change != may_add on the discriminating inputs, so Ensures "
            "fails. Exactly the discriminator the spec must sense (G-DIFF)."
        ),
    },
    {
        "id": "weak-add-or-change",
        "kind": "uniqueness",
        "expect": "reject",
        # 'Both permissions count': gate on (may_add or may_change). Equals gold
        # whenever may_add is True, but admits the change-only viewer
        # (may_add=False, may_change=True) where gold is False.
        "module": _impl(
            "    show_save_as_new = (\n"
            "        not is_popup and (may_add or may_change) and editing_existing and save_as_enabled\n"
            "    )\n"
            "    return show_save_as_new"
        ),
        "refinement": (
            "its faithful real patch would gate on `(has_add_permission or "
            "has_change_permission)`. The hints_text explicitly says checking "
            "has_add_permission ALONE is enough; an OR gate still shows the control "
            "to the F2P change-but-not-add viewer (add=False, change=True) -> "
            "show_save_as_new=True, but the F2P asserts False => NOT resolved."
        ),
        "rationale": (
            "rejected by the biconditional: at (is_popup=F, may_add=F, may_change=T, "
            "editing_existing=T, save_as_enabled=T) the impl is True while the "
            "formula (gating on may_add) is False — Ensures fails on that "
            "assignment of the 2^5 cube."
        ),
    },
    {
        "id": "weak-drop-add-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: drop the permission gate entirely. Agrees with gold on
        # every input where may_add is True; diverges (returns True vs False)
        # whenever a non-popup, editing-existing, enabled viewer lacks add perm.
        "module": _impl(
            "    show_save_as_new = (\n"
            "        not is_popup and editing_existing and save_as_enabled\n"
            "    )\n"
            "    return show_save_as_new"
        ),
        "refinement": (
            "its faithful real patch drops the `and has_add_permission` gate "
            "altogether (regression to no-permission-check). On the F2P "
            "change-but-not-add viewer it yields True (the page is a real change "
            "page with save_as on) but the F2P asserts False => NOT resolved; it "
            "also re-opens the original CVE-shaped bug the patch fixes."
        ),
        "rationale": (
            "rejected by the biconditional: when (is_popup=F, may_add=F, "
            "editing_existing=T, save_as_enabled=T) the impl is True while the "
            "formula is False (may_add=F kills it) — Ensures fails."
        ),
    },
    {
        "id": "weak-flip-popup-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # Supporting near-miss (single-operand corruption that still carries a
        # real refinement): use `is_popup` instead of `not is_popup`.
        "module": _impl(
            "    show_save_as_new = (\n"
            "        is_popup and may_add and editing_existing and save_as_enabled\n"
            "    )\n"
            "    return show_save_as_new"
        ),
        "refinement": (
            "its faithful real patch would gate on `is_popup` rather than "
            "`not is_popup`, withholding the control on real change pages and "
            "showing it only in popups. The F2P add-and-change viewer runs on a "
            "non-popup change page and expects show_save_as_new=True; this impl "
            "yields False => FAIL_TO_PASS NOT resolved."
        ),
        "rationale": (
            "rejected by the biconditional: at the F2P add-and-change input "
            "(is_popup=F, may_add=T, editing_existing=T, save_as_enabled=T) the "
            "impl is False while the formula is True — Ensures fails."
        ),
    },
]

# No @ContractOnly axioms, no A-reference deep models: the visibility is pure
# boolean logic over context flags read as the identity (mapping.md §3,
# refinement.md §B). axiom_check.py validates the only soundness obligation (the
# exhaustive 2^5 boolean equality of model formula == gold expression), which is
# a static check, not a real-callee probe. Hence no axiom lane.
AXIOM_TESTS = []
