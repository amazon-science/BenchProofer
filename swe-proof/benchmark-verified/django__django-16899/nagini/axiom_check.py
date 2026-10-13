#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16899.

There is NO consumed `@ContractOnly` callee axiom in this bundle: the only
behaviour under change is the SHAPE of the diagnostic message, modelled DEEPLY
in model.py (the `diagnostic_message` concatenation + the `check_reference`
impl). G-AX therefore validates the **A-reference**: that the deep model — the
marker-abstracted concatenation

    seg_intro + label + seg_refers + value + seg_which_not
        + cls + seg_or_attr + model_label + seg_end

with the five fixed-prose markers standing (per the mapping.md bijection) for
the five literal prose pieces of the post-patch template — reproduces the REAL
Python `%`-formatting of the gold post-patch template, and that the value
occupies its own interpolated segment immediately after the label (the
discriminating postcondition B in refinement.md).

It also confirms the PRE-patch template (the function under change before the
fix) does NOT name the value, so the differential is real.

Imports nothing repo-specific: only the standard library. Exit 0 iff sound.
"""
import random
import sys

# --- the five fixed prose pieces of the post-patch template (mapping.md §2) --
# Order: intro, [label], refers, [value], which_not, [cls], or_attr,
#        [model_label], end
SEG_INTRO = "The value of '"
SEG_REFERS = "' refers to '"
SEG_WHICH_NOT = "', which is not a callable, an attribute of '"
SEG_OR_ATTR = "', or an attribute of '"
SEG_END = "'."

# The REAL post-patch and pre-patch templates (verbatim from checks.py).
NEW_TEMPLATE = (
    "The value of '%s' refers to '%s', which is not a callable, "
    "an attribute of '%s', or an attribute of '%s'."
)
OLD_TEMPLATE = (
    "The value of '%s' is not a callable, an attribute of "
    "'%s', or an attribute of '%s'."
)


def deep_model_message(label, value, cls, model_label):
    """Reference of model.py's deep model `diagnostic_message`, with the
    fixed-prose markers expanded to their literal pieces (the mapping.md
    bijection). Concatenation order is identical to model.py."""
    return (SEG_INTRO + label + SEG_REFERS + value + SEG_WHICH_NOT
            + cls + SEG_OR_ATTR + model_label + SEG_END)


def real_new_message(label, value, cls, model_label):
    """The REAL post-patch message: Python `%`-formatting of the gold
    template with the four arguments in gold order (label, field_name,
    cls, model_label)."""
    return NEW_TEMPLATE % (label, value, cls, model_label)


def real_old_message(label, cls, model_label):
    """The REAL pre-patch message (no value argument)."""
    return OLD_TEMPLATE % (label, cls, model_label)


def check_reference_equiv(label, value, cls, model_label):
    """A-reference: deep model == real post-patch `%`-formatting."""
    dm = deep_model_message(label, value, cls, model_label)
    rm = real_new_message(label, value, cls, model_label)
    assert dm == rm, (
        "deep model unsound: model=%r real=%r (label=%r value=%r cls=%r "
        "model_label=%r)" % (dm, rm, label, value, cls, model_label))


def check_value_position(label, value, cls, model_label):
    """Discriminating postcondition B: the value occupies its own contiguous
    segment at offset len(SEG_INTRO)+len(label)+len(SEG_REFERS)."""
    msg = real_new_message(label, value, cls, model_label)
    start = len(SEG_INTRO) + len(label) + len(SEG_REFERS)
    assert msg[start:start + len(value)] == value, (
        "value not at its interpolation slot: %r at %d in %r"
        % (value, start, msg))


def check_old_omits_value(label, value, cls, model_label):
    """The PRE-patch message must NOT name the value (the differential)."""
    old = real_old_message(label, cls, model_label)
    # the offending value must be absent from the old message UNLESS it
    # happens to be a substring of label/cls/model_label (which the fuzz
    # avoids by using a marker token), so for distinct tokens it is absent.
    if value and value not in (label + cls + model_label):
        assert value not in old, (
            "pre-patch message unexpectedly contains value %r: %r"
            % (value, old))


def main():
    # Boundary cases drawn from the real test suite plus edges.
    boundary = [
        # (label, field_name/value, cls, model_label) -- from the F2P tests
        ("readonly_fields[1]", "nonexistent", "SongAdmin", "admin_checks.Song"),
        ("readonly_fields[0]", "i_dont_exist", "CityInline", "admin_checks.City"),
        # edges
        ("readonly_fields[0]", "", "A", "app.M"),                   # empty value
        ("", "x", "", ""),                                          # empty others
        ("L", "V", "C", "ML"),                                      # single chars
        ("readonly_fields[10]", "field_with_underscores", "X", "y.Z"),
        ("l'abel", "va'lue", "C'ls", "m.L'b"),                      # apostrophes
        ("a%sb", "c%sd", "e%sf", "g%sh"),                           # percent in data
        ("é", "•", "ç", "ñ"),                   # non-ascii
    ]
    for (lab, val, cls, ml) in boundary:
        check_reference_equiv(lab, val, cls, ml)
        check_value_position(lab, val, cls, ml)
        check_old_omits_value(lab, val, cls, ml)

    # Randomized fuzz.
    rng = random.Random(16899)
    alphabet = list("abcdefghij ABC_.[]0123456789'%é•")
    for _ in range(20000):
        def tok():
            n = rng.randint(0, 16)
            return "".join(rng.choice(alphabet) for _ in range(n))
        lab, val, cls, ml = tok(), tok(), tok(), tok()
        check_reference_equiv(lab, val, cls, ml)
        check_value_position(lab, val, cls, ml)

    print("G-AX OK: diagnostic_message deep model (== real post-patch "
          "%%-formatting) sound on %d boundary + 20000 fuzz inputs; value "
          "occupies its own segment; pre-patch template omits the value."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
