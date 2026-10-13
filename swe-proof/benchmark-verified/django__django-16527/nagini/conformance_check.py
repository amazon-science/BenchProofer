#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16527 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (the impl region contains no Requires/Ensures at runtime — the
contracts live in the marker regions — so the copy is byte-for-byte the impl
body). No PSeq, no @Pure helpers, no @ContractOnly callees: the impl is pure
boolean logic over five bool parameters.

ORACLE: the REAL patched repo function the model models per mapping.md §1 —
`django.contrib.admin.templatetags.admin_modify.submit_row`, observed at the
`"show_save_as_new"` entry of the Context it returns. The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched module importable.

Type bridge (mapping.md §2): each model bool parameter is the identity image
of one rendering-context flag —
    is_popup          <-> context["is_popup"]
    may_add           <-> context["has_add_permission"]
    may_change        <-> context["has_change_permission"]
    editing_existing  <-> context["change"]
    save_as_enabled   <-> context["save_as"]
and the model's bool return value is the identity image of the
`"show_save_as_new"` Context entry. `submit_row` also reads further context
keys (add / view / delete permission flags, inline-formset flag, show_*
options); those are OUTSIDE the modeled expression, so they are fuzzed freely
to confirm the observed entry is independent of them.

Input domain: the Requires region admits every assignment of the five bools
(no constraint beyond the types), so the modeled domain is the full 2^5 cube.
Boundary cases: the ENTIRE 2^5 cube exhaustively (crossed with a few settings
of the surrounding flags). Fuzz: 100_000 random full-context assignments,
pinned seed 16527.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plus Django from /testbed as the oracle).
"""
import itertools
import json
import random
import sys

SEED = 16527
N_FUZZ = 100_000


# --- the impl region of model.py, verbatim, no contract calls to strip -------

def save_as_new_visible(
    is_popup,
    may_add,
    may_change,
    editing_existing,
    save_as_enabled,
):
    show_save_as_new = (
        not is_popup and may_add and editing_existing and save_as_enabled
    )
    return show_save_as_new


# --- bridge: model parameters -> rendering context ---------------------------

# Context keys submit_row reads that are OUTSIDE the modeled expression.
EXTRA_KEYS = (
    "add",
    "has_view_permission",
    "has_delete_permission",
    "has_editable_inline_admin_formsets",
    "show_save",
    "show_save_and_add_another",
    "show_save_and_continue",
    "show_delete",
)


def build_context(is_popup, may_add, may_change, editing_existing,
                  save_as_enabled, extras):
    ctx = {
        "is_popup": is_popup,
        "has_add_permission": may_add,
        "has_change_permission": may_change,
        "change": editing_existing,
        "save_as": save_as_enabled,
    }
    ctx.update(extras)
    return ctx


def check_one(submit_row, flags, extras):
    """Run shadow and oracle on one full context; return an error string on
    disagreement, else None."""
    is_popup, may_add, may_change, editing_existing, save_as_enabled = flags
    shadow = save_as_new_visible(
        is_popup, may_add, may_change, editing_existing, save_as_enabled
    )
    result_ctx = submit_row(
        build_context(is_popup, may_add, may_change, editing_existing,
                      save_as_enabled, extras)
    )
    real = result_ctx["show_save_as_new"]
    if bool(shadow) is not bool(real):
        return ("DISAGREEMENT\n"
                "  flags: is_popup=%r may_add=%r may_change=%r "
                "editing_existing=%r save_as_enabled=%r\n"
                "  extras=%r\n  shadow=%r\n  real=%r"
                % (is_popup, may_add, may_change, editing_existing,
                   save_as_enabled, extras, shadow, real))
    return None


def boundary_extras():
    """A few fixed settings of the non-modeled context flags."""
    all_true = {k: True for k in EXTRA_KEYS}
    all_false = {k: False for k in EXTRA_KEYS}
    mixed = dict(all_true)
    mixed.update({"add": False, "show_save": False})
    return [all_true, all_false, mixed]


def rand_extras(rng):
    return {k: rng.random() < 0.5 for k in EXTRA_KEYS}


def main():
    # Django needs settings configured before template machinery runs.
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(USE_TZ=False)
        django.setup()
    # REAL patched repo function (mapping.md §1).
    from django.contrib.admin.templatetags.admin_modify import submit_row

    checked = 0

    # Boundary: the exhaustive 2^5 cube of the modeled flags, crossed with
    # fixed settings of the surrounding flags.
    n_boundary = 0
    for extras in boundary_extras():
        for flags in itertools.product((False, True), repeat=5):
            err = check_one(submit_row, flags, extras)
            if err:
                print(err)
                return 1
            checked += 1
            n_boundary += 1

    # Fuzz: pinned-seed random full-context assignments.
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        flags = tuple(rng.random() < 0.5 for _ in range(5))
        err = check_one(submit_row, flags, rand_extras(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real submit_row['show_save_as_new'] on "
          "%d inputs (%d boundary incl. the exhaustive 2^5 cube + %d fuzz, "
          "seed %d)." % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
