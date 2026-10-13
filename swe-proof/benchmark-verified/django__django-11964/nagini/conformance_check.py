#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11964 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant) stripped. The bundle has no @Pure helper
functions and no @ContractOnly callees; the impl is a plain element-for-element
copy loop over the member's value text, so it executes directly.

ORACLE: the REAL patched repo behaviour the model models per mapping.md — the
textual coercion of an enumerated-choice member, i.e. ``str(member)`` for a
member of ``django.db.models.enums.Choices`` (and its ``IntegerChoices`` /
``TextChoices`` int/str mix-in subclasses). The gate applies patch.diff to
/testbed before this script runs and sets PYTHONPATH=/testbed, so importing
``django.db.models.enums`` resolves the patched classes.

Type bridge (mapping.md section 2): the repo-side text is a ``str``; the model
carrier is ``List[int]`` of Unicode code points via ``ord``. The member
stand-in ``Member`` carries exactly the two touched character sequences:
``value_text`` (the textual rendering of the member's underlying value,
lowered as ``[ord(c) for c in str(member.value)]`` — the A-reference coercion
already validated by axiom_check.py / G-AX) and ``qualified_label`` (the
default diagnostic "Owner.NAME" rendering, lowered the same way). The bridge
is a bijection on each sequence, so members are generated repo-side and
lowered per call.

Input domain: render_to_text's precondition demands only readable member
fields at fractional permission, so every constructed member lowers to a
Requires-satisfying input. Generation covers the issue's fixture shapes
(multi-member integer and text enumerations), boundary values (empty text,
unicode, punctuation, dots and spaces; zero, negative, and huge integers) and
randomized fuzz over both value kinds.

>= 1e5 Requires-satisfying inputs: boundary cases + sweep + 100000 fuzz
members. Pinned fuzz seed: 119640.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 119640
N_FUZZ = 100000


# --- the model's Member stand-in (contracts stripped) --------------------------

class Member(object):
    def __init__(self):
        # value_text: the textual rendering of the member's underlying value.
        self.value_text = []
        # qualified_label: the diagnostic "Owner.NAME" rendering of the member.
        self.qualified_label = []


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def render_to_text(self):
    result = []
    i = 0
    while i < len(self.value_text):
        result.append(self.value_text[i])
        i = i + 1
    return result


# --- bridge: real repo member -> model Member ----------------------------------

def codepoints(s):
    return [ord(ch) for ch in s]


def lower_member(member):
    """Lower a real enum-backed choice member to the model's Member stand-in
    per mapping.md: value_text carries str(member.value) as code points (the
    G-AX-validated A-reference coercion); qualified_label carries the default
    diagnostic 'Owner.NAME' rendering."""
    m = Member()
    m.value_text = codepoints(str(member.value))
    m.qualified_label = codepoints("%s.%s" % (type(member).__name__, member.name))
    return m


# --- differential driver --------------------------------------------------------

def check(member):
    """Run shadow and oracle on one real member; return an error string on
    disagreement, else None."""
    shadow = render_to_text(lower_member(member))
    real = str(member)              # the patched textual coercion (oracle)
    real_cps = codepoints(real)
    if shadow != real_cps:
        return ("DISAGREEMENT on member %r (value %r, name %r):\n"
                "  shadow (impl region) code points = %r\n"
                "  real str(member) = %r (code points %r)"
                % (member, member.value, member.name, shadow, real, real_cps))
    return None


def main():
    from django.db.models.enums import Choices, IntegerChoices, TextChoices

    def build_text(name, mapping):
        return TextChoices(name, mapping)

    def build_int(name, mapping):
        return IntegerChoices(name, mapping)

    checked = 0
    failures = 0

    def run(member):
        err = check(member)
        if err:
            print(err)
            return False
        return True

    # --- boundary text values (each its own single-member enum) --------------
    text_boundaries = [
        "", "FR", "first", "second", "X",
        "a b", "a.b", "café", "12345", "!$&'()*+,;=",
        "Owner.NAME", "Txt.M",              # value text colliding with a label shape
        " ", "  leading", "trailing  ", "new\nline", "tab\tsep",
        "•", "\U0001F600", "éπ",
    ]
    for val in text_boundaries:
        E = build_text("Txt", {"M": val})
        if not run(E["M"]):
            return 1
        checked += 1

    # --- boundary integer values ----------------------------------------------
    int_boundaries = [0, 1, -1, 2, 3, 4, 9, 10, 42, 100, 999, 1000,
                      -7, -999, 10 ** 6, -(10 ** 6), 2 ** 31, 2 ** 31 - 1,
                      -(2 ** 31), 2 ** 63, 10 ** 18]
    for v in int_boundaries:
        E = build_int("Int", {"M": v})
        if not run(E["M"]):
            return 1
        checked += 1

    # --- plain Choices (no int/str mix-in) with assorted value kinds ----------
    plain = Choices("Plain", {"A": 1, "B": "two", "C": 3.5})
    for m in plain:
        if not run(m):
            return 1
        checked += 1

    # --- multi-member enums mirroring the issue's fixture shapes --------------
    Suit = build_int("Suit", {"DIAMOND": 1, "SPADE": 2, "HEART": 3, "CLUB": 4})
    for m in Suit:
        if not run(m):
            return 1
        checked += 1
    Year = build_text("YearInSchool",
                      {"FRESHMAN": "FR", "SOPHOMORE": "SO", "JUNIOR": "JR",
                       "SENIOR": "SR", "GRADUATE": "GR"})
    for m in Year:
        if not run(m):
            return 1
        checked += 1

    # --- per-code-point sweep: single-char text values across ASCII + a band
    # of non-ASCII / astral code points --------------------------------------
    sweep_cps = list(range(32, 127)) + [0xa0, 0xe9, 0x2022, 0x2028,
                                        0x3000, 0x1F600]
    for cp in sweep_cps:
        E = build_text("Sw", {"M": chr(cp)})
        if not run(E["M"]):
            return 1
        checked += 1

    # --- randomized fuzz (pinned seed), batched up to 10 members per enum
    # class; the enum-backed choice classes reject duplicate values, so each
    # batch keeps only distinct values -------------------------------------
    rng = random.Random(SEED)
    alphabet = "abcdefABCDEF0123456789 .,;:'\"!&<>_-éπ•"
    while checked < N_FUZZ + 200:
        mapping = {}
        seen = set()
        if rng.random() < 0.5:
            for k in range(10):
                n = rng.randint(0, 16)
                val = "".join(rng.choice(alphabet) for _ in range(n))
                if val not in seen:
                    seen.add(val)
                    mapping["M%d" % k] = val
            E = build_text("Fz", mapping)
        else:
            for k in range(10):
                val = rng.randint(-(10 ** 9), 10 ** 9)
                if val not in seen:
                    seen.add(val)
                    mapping["M%d" % k] = val
            E = build_int("FzI", mapping)
        for nm in mapping:
            if not run(E[nm]):
                return 1
            checked += 1

    print("G-CONF OK: shadow impl == real patched member-to-text coercion on "
          "%d members (boundary + sweep + >=%d fuzz, seed %d); 0 disagreements."
          % (checked, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": failures,
                      "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
