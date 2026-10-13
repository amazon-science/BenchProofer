#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_buttonFlags
against the patch.diff behaviour (post-patch submit_row flag computation).

The impl region is all R/I (no A-tagged op), so this runs a real fuzz. The shadow
reproduces the impl op-for-op (the seven derived boolean flags). We diff that
against an independent reconstruction of the post-patch `submit_row` flag logic
transcribed straight from the patched source. Inputs are the 13 booleans; we
enumerate all 2^13 combinations exhaustively (8192) and then add random fill to
exceed 10^5 inputs. Zero disagreements required.

stdlib-only. exit 0 iff zero disagreements.
"""
import itertools
import random
import sys

SEED = 16527
N_RANDOM = 120_000

FIELDS = [
    "add", "change", "is_popup", "save_as", "show_save",
    "show_save_and_add_another", "show_save_and_continue",
    "has_add_permission", "has_change_permission", "has_view_permission",
    "has_editable_inline_admin_formsets", "has_delete_permission", "show_delete",
]


def shadow(c: dict) -> dict:
    """R/I shadow of implementation_buttonFlags (op-for-op)."""
    can_save = (
        (c["has_change_permission"] and c["change"])
        or (c["has_add_permission"] and c["add"])
        or c["has_editable_inline_admin_formsets"]
    )
    can_save_and_add_another = (
        c["has_add_permission"]
        and not c["is_popup"]
        and (not c["save_as"] or c["add"])
        and can_save
        and c["show_save_and_add_another"]
    )
    can_save_and_continue = (
        not c["is_popup"]
        and can_save
        and c["has_view_permission"]
        and c["show_save_and_continue"]
    )
    can_change = c["has_change_permission"] or c["has_editable_inline_admin_formsets"]
    return {
        "can_change": can_change,
        "show_delete_link": (
            not c["is_popup"] and c["has_delete_permission"]
            and c["change"] and c["show_delete"]
        ),
        "show_save_as_new": (
            not c["is_popup"] and c["has_add_permission"]
            and c["change"] and c["save_as"]
        ),
        "show_save_and_add_another": can_save_and_add_another,
        "show_save_and_continue": can_save_and_continue,
        "show_save": c["show_save"] and can_save,
        "show_close": not (c["show_save"] and can_save),
    }


def patched(c: dict) -> dict:
    """Independent reconstruction transcribed from the patched submit_row
    (django/contrib/admin/templatetags/admin_modify.py, post-patch)."""
    add = c["add"]
    change = c["change"]
    is_popup = c["is_popup"]
    save_as = c["save_as"]
    show_save = c["show_save"]
    show_save_and_add_another = c["show_save_and_add_another"]
    show_save_and_continue = c["show_save_and_continue"]
    has_add_permission = c["has_add_permission"]
    has_change_permission = c["has_change_permission"]
    has_view_permission = c["has_view_permission"]
    has_editable_inline_admin_formsets = c["has_editable_inline_admin_formsets"]
    can_save = (
        (has_change_permission and change)
        or (has_add_permission and add)
        or has_editable_inline_admin_formsets
    )
    can_save_and_add_another = (
        has_add_permission
        and not is_popup
        and (not save_as or add)
        and can_save
        and show_save_and_add_another
    )
    can_save_and_continue = (
        not is_popup and can_save and has_view_permission and show_save_and_continue
    )
    can_change = has_change_permission or has_editable_inline_admin_formsets
    return {
        "can_change": can_change,
        "show_delete_link": (
            not is_popup and c["has_delete_permission"]
            and change and c["show_delete"]
        ),
        "show_save_as_new": (
            not is_popup and has_add_permission and change and save_as
        ),
        "show_save_and_add_another": can_save_and_add_another,
        "show_save_and_continue": can_save_and_continue,
        "show_save": show_save and can_save,
        "show_close": not (show_save and can_save),
    }


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []
    count = 0

    def check(c):
        nonlocal disagreements, count
        count += 1
        g, w = shadow(c), patched(c)
        if g != w:
            disagreements += 1
            if len(examples) < 10:
                examples.append((c, g, w))

    # Exhaustive enumeration of all 2^13 boolean input combinations.
    for combo in itertools.product([False, True], repeat=len(FIELDS)):
        check(dict(zip(FIELDS, combo)))

    # Random fill to exceed 10^5 inputs.
    for _ in range(N_RANDOM):
        check({f: rng.random() < 0.5 for f in FIELDS})

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for c, g, w in examples:
            print(f"  in={c!r}\n    shadow={g!r}\n    patched={w!r}")
        return 1

    print(f"G-CONF OK: {count} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
