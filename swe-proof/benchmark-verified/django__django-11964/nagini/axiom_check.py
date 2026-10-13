#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11964.

The bundle consumes NO `@ContractOnly` axiom: the rendering of an enumerated
choice member to text is modelled DEEPLY as the member's own value text (an
element-for-element copy of `value_text`). G-AX therefore validates the single
A-reference behind that deep model against the REAL Python semantics:

  (A-reference) `value_text` is the standard string coercion `str(value)` of the
      member's underlying value. The deep model claims that rendering a member
      to text returns exactly `str(value)`, character for character, and NOT the
      default diagnostic "Owner.NAME" qualified label.

This script reconstructs the patched member rendering with a minimal stand-in
for the real enum-backed choice class — the same construction the gold patch
edits: a `Choices` enum whose `__str__` returns `str(self.value)`, plus the
integer-valued and text-valued mix-in subclasses (`IntegerChoices`,
`TextChoices`) the issue is about — exercises it on boundary + fuzz integer and
text values, and asserts:

  1. the rendered text == real Python `str(value)` (the A-reference is sound);
  2. the rendered text is NOT the default "Owner.NAME" label whenever the value
     text differs from that label (the discriminating behaviour the fix adds);
  3. the model's code-point encoding of `value_text` matches `str(value)`.

Imports only the Python standard library (`enum`, `random`, `sys`) — the same
`enum` machinery the gold patch builds on. Exit 0 iff every obligation holds.
"""
import enum
import random
import sys


# --- reconstruction of the PATCHED behaviour (gold patch, deep model) --------
#
# Mirrors django/db/models/enums.py after the fix: a Choices enum whose __str__
# returns str(self.value), with the same int / str mix-in subclasses the issue
# names. We do not import Django (the eval container has it); we reproduce the
# behaviour under change on the stdlib enum the patch is layered on, so the
# A-reference is checked against real str().

class Choices(enum.Enum):
    def __str__(self):
        # the gold patch: use the value when cast to str
        return str(self.value)


class IntegerChoices(int, Choices):
    pass


class TextChoices(str, Choices):
    pass


def default_qualified_label(member):
    """The default enum diagnostic rendering 'Owner.NAME' (pre-patch __str__)."""
    return "%s.%s" % (type(member).__name__, member.name)


def codepoints(s):
    return [ord(ch) for ch in s]


def check_member(member):
    """Assert the patched rendering == str(value) and the model encoding holds."""
    rendered = str(member)                      # patched __str__ -> str(value)
    value_text = str(member.value)              # real Python str() of the value
    # (1) A-reference: rendering equals the standard string coercion of value.
    assert rendered == value_text, (
        "rendering unsound for %r (%r): str(member)=%r, str(value)=%r"
        % (member, type(member).__mro__, rendered, value_text))
    # (3) model code-point encoding of value_text agrees with str(value).
    assert codepoints(rendered) == codepoints(value_text), (
        "code-point encoding mismatch for %r" % (member,))
    # (2) discriminating: whenever value text != the default label, the patched
    # rendering must NOT be that label (the pre-patch behaviour the fix removes).
    label = default_qualified_label(member)
    if value_text != label:
        assert rendered != label, (
            "rendering still produced the diagnostic label %r for %r" % (label, member))


def build_text(name, mapping):
    return TextChoices(name, mapping)


def build_int(name, mapping):
    return IntegerChoices(name, mapping)


def main():
    members_checked = 0

    # --- boundary text values (each its own single-member enum) --------------
    text_boundaries = [
        ("EMPTY", ""),
        ("FR", "FR"),
        ("first", "first"),
        ("second", "second"),
        ("X", "X"),
        ("space", "a b"),
        ("dot", "a.b"),
        ("unicode", "café"),
        ("digits", "12345"),
        ("punct", "!$&'()*+,;="),
    ]
    for nm, val in text_boundaries:
        E = build_text("Txt", {"M": val})
        check_member(E["M"])
        members_checked += 1

    # --- boundary integer values ---------------------------------------------
    int_boundaries = [0, 1, 2, 3, 4, 9, 10, 42, 100, 999, 2 ** 31, -7]
    for v in int_boundaries:
        E = build_int("Int", {"M": v})
        check_member(E["M"])
        members_checked += 1

    # --- multi-member enums mirroring the F2P test fixtures ------------------
    Suit = build_int("Suit", {"DIAMOND": 1, "SPADE": 2, "HEART": 3, "CLUB": 4})
    for m in Suit:
        check_member(m)
        members_checked += 1
    Year = build_text("YearInSchool",
                       {"FRESHMAN": "FR", "SOPHOMORE": "SO", "JUNIOR": "JR",
                        "SENIOR": "SR", "GRADUATE": "GR"})
    for m in Year:
        check_member(m)
        members_checked += 1

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(11964)
    alphabet = "abcdefABCDEF0123456789 .,;:'\"!&<>_-éπ•"
    for _ in range(20000):
        if rng.random() < 0.5:
            n = rng.randint(0, 16)
            val = "".join(rng.choice(alphabet) for _ in range(n))
            E = build_text("Fz", {"M": val})
            check_member(E["M"])
        else:
            v = rng.randint(-(10 ** 6), 10 ** 6)
            E = build_int("FzI", {"M": v})
            check_member(E["M"])
        members_checked += 1

    print("G-AX OK: patched member rendering == str(value) (A-reference) and "
          "is never the default 'Owner.NAME' label, over %d members "
          "(boundary + 20000 fuzz)." % members_checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
