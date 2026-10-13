#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15467.

The bundle models ONE behavior: the placeholder-label (`empty_label`) resolution
in `ModelAdmin.formfield_for_foreignkey`
(`django/contrib/admin/options.py`). Its Lean implementation
(`implementation_emptyLabel`) resolves the placeholder from three inputs:

    radioBranch : bool            -- the single-choice (radio) control is the one being built
    blank       : bool            -- db_field.blank (the relation is optional)
    provided    : str | None      -- the caller-supplied empty_label (None == absent)

post-patch resolution:
    if radioBranch:
        empty_label = (provided if provided is not None else NONE_LABEL) if blank else None
    else:
        empty_label = provided        # carried through untouched

This script transliterates that R/I impl into Python (`shadow_empty_label`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
post-patch behavior of the changed assignment — `kwargs.get("empty_label",
_("None")) if db_field.blank else None`, executed only in the radio branch.

We do NOT stand up Django's ModelAdmin / form machinery (heavy, and the modeled
value is a pure decision over two booleans and an optional string). `_("None")`
is the literal "None" in the default/test locale (NONE_LABEL).

The full categorical input space is small: radioBranch in {T,F} x blank in {T,F}
x provided in {None} ∪ STRINGS. The edge set enumerates ALL boolean combinations
against a representative string panel (including the default text "None" itself
and the F2P custom label), and the fuzz loop additionally samples >=1e5 random
inputs over a wide alphabet of provided strings.

stdlib-only. Pinned seed: 15467 (also recorded in mapping.md).
"""
import random
import sys

SEED = 15467
N = 120_000
NONE_LABEL = "None"  # _("None") in the default/test locale

# A panel of caller-supplied placeholder values to exercise. Includes None
# (absent), the default text itself ("None"), the F2P custom label, empty
# string, and assorted unicode / whitespace strings.
PROVIDED_PANEL = [
    None,
    "None",
    "Custom empty label",
    "",
    " ",
    "—",
    "Ninguno",
    "0",
    "None ",
    "n/a",
]


# --- ORACLE: the post-patch behavior, faithful in-process replica -----------
# Mirrors the changed assignment, reached only inside the radio branch.
def oracle_empty_label(radio_branch, blank, provided):
    # Before the radio branch, kwargs["empty_label"] is whatever the caller
    # passed (modeled as `provided`); absent -> None.
    empty_label = provided
    if radio_branch:
        # kwargs["empty_label"] = (kwargs.get("empty_label", _("None"))
        #                          if db_field.blank else None)
        if blank:
            empty_label = provided if provided is not None else NONE_LABEL
        else:
            empty_label = None
    return empty_label


# --- SHADOW: transliteration of the Lean R/I impl ---------------------------
# implementation_emptyLabel: provided.getD noneLabel == provided if some else NONE_LABEL.
def shadow_empty_label(radio_branch, blank, provided):
    empty_label = provided
    if radio_branch:
        if blank:
            empty_label = (provided if provided is not None else NONE_LABEL)
        else:
            empty_label = None
    return empty_label


def check(radio_branch, blank, provided):
    o = oracle_empty_label(radio_branch, blank, provided)
    s = shadow_empty_label(radio_branch, blank, provided)
    return o == s, o, s


def main():
    checked = 0
    disagreements = 0
    first_bad = None

    # --- exhaustive edge set: all bool combos x the provided panel ----------
    for radio_branch in (False, True):
        for blank in (False, True):
            for provided in PROVIDED_PANEL:
                ok, o, s = check(radio_branch, blank, provided)
                checked += 1
                if not ok:
                    disagreements += 1
                    if first_bad is None:
                        first_bad = (radio_branch, blank, provided, o, s)

    # --- fuzz ----------------------------------------------------------------
    rng = random.Random(SEED)
    alphabet = "abcdefghijklmnopqrstuvwxyz None_—0 "
    for _ in range(N):
        radio_branch = rng.random() < 0.5
        blank = rng.random() < 0.5
        r = rng.random()
        if r < 0.2:
            provided = None
        elif r < 0.3:
            provided = NONE_LABEL
        else:
            length = rng.randint(0, 24)
            provided = "".join(rng.choice(alphabet) for _ in range(length))
        ok, o, s = check(radio_branch, blank, provided)
        checked += 1
        if not ok:
            disagreements += 1
            if first_bad is None:
                first_bad = (radio_branch, blank, provided, o, s)

    if disagreements == 0:
        print(f"checked={checked} disagreements=0; status=pass")
        sys.exit(0)
    else:
        print(f"checked={checked} disagreements={disagreements}; status=fail")
        print(f"first disagreement: {first_bad!r}")
        sys.exit(1)


if __name__ == "__main__":
    main()
