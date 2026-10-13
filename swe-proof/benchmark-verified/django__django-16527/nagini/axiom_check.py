#!/usr/bin/env python3
"""G-AX soundness check for django__django-16527.

This bundle consumes NO axioms: the modeled `show_save_as_new` visibility is
pure boolean logic over five rendering-context flags (mapping.md §3,
refinement.md §B). There is therefore no `@ContractOnly` callee Ensures to fuzz
against a real callee.

What remains to validate is the single nontrivial soundness obligation of the
refinement: the R-refinement of mapping.md §2 — that the modeled boolean formula

    Result == (not is_popup and may_add and editing_existing and save_as_enabled)

equals Python's OWN native evaluation of the gold expression bound to
`"show_save_as_new"` in `submit_row`:

    not is_popup and has_add_permission and change and save_as

— for every assignment of the five booleans. Since the domain is finite
(2^5 = 32 assignments), this is checked EXHAUSTIVELY, not merely fuzzed. Also
confirms the bundle's discriminator: the pre-patch expression (which gates on
`has_change_permission`) differs from the gold on exactly the inputs where add-
and change-permission disagree.

stdlib-only; exit 0 iff sound.
"""
import itertools
import sys


def model_formula(is_popup, may_add, may_change, editing_existing, save_as_enabled):
    # The verified model.py impl, transcribed (it ignores may_change).
    return not is_popup and may_add and editing_existing and save_as_enabled


def gold_expression(is_popup, has_add_permission, has_change_permission, change, save_as):
    # The gold patch.diff expression, verbatim semantics.
    return not is_popup and has_add_permission and change and save_as


def prepatch_expression(is_popup, has_add_permission, has_change_permission, change, save_as):
    # The pre-patch (buggy) repo expression, verbatim semantics.
    return not is_popup and has_change_permission and change and save_as


def main():
    violations = 0
    discriminating = 0
    for is_popup, may_add, may_change, change, save_as in itertools.product(
        (False, True), repeat=5
    ):
        m = model_formula(is_popup, may_add, may_change, change, save_as)
        g = gold_expression(is_popup, may_add, may_change, change, save_as)
        if bool(m) is not bool(g):
            violations += 1
            print(
                "MISMATCH model!=gold at "
                f"is_popup={is_popup} may_add={may_add} may_change={may_change} "
                f"change={change} save_as={save_as}: model={m} gold={g}",
                file=sys.stderr,
            )
        # Sanity: the model must be a genuine bool equal to the gold bool.
        if not isinstance(m, bool) or not isinstance(g, bool):
            violations += 1
            print("NON-BOOL result", file=sys.stderr)
        # Track that the prepatch genuinely differs from gold somewhere
        # (the spec must be able to sense the bug): it differs exactly when
        # add- and change-permission disagree and the other guards are open.
        p = prepatch_expression(is_popup, may_add, may_change, change, save_as)
        if bool(p) is not bool(g):
            discriminating += 1

    if violations:
        print(f"UNSOUND: {violations} violation(s) over the 2^5 boolean cube",
              file=sys.stderr)
        return 1

    if discriminating == 0:
        print(
            "DEGENERATE: pre-patch expression never differs from gold — "
            "the spec could not sense the bug",
            file=sys.stderr,
        )
        return 1

    print(
        "SOUND: model formula == gold expression on all 32 boolean assignments; "
        f"pre-patch (change-permission gating) differs from gold on "
        f"{discriminating} of them (the discriminating inputs)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
