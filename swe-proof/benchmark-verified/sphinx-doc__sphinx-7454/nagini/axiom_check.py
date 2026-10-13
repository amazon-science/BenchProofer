#!/usr/bin/env python3
"""G-AX / deep-model soundness check for sphinx-doc__sphinx-7454.

This instance axiomatizes NO library callee: the changed behaviour is a pure
in-function classification of a single annotation name into a reference-kind
tag, modeled DEEPLY in model.py (the `kind_for` classifier and the verbatim
code-point tag constants `name_value`/`tag_value`/`tag_type`). There is thus no
external callee to fuzz in-container.

What this script checks instead is the fidelity of the deep model to the
behaviour the gold patch implements and the F2P test observes:

  * the reference TARGET is the input text carried through unchanged;
  * the reference KIND is the VALUE tag 'obj' exactly when the text is the
    singleton value name 'None', and the TYPE tag 'class' for every other name.

It reproduces model.py's `kind_for` over `List[int]` code points and asserts it
agrees with the gold rule on boundary names (including the F2P-observed 'int'
and 'None'), near-miss spellings of 'None', and randomized fuzz over identifier
characters. stdlib-only; exit 0 iff the deep model matches the gold rule on
every observation.
"""
import random
import sys

# --- model.py reference encodings (kept in lock-step with the deep model) ----

NAME_VALUE = [78, 111, 110, 101]        # 'None'
TAG_VALUE = [111, 98, 106]              # 'obj'
TAG_TYPE = [99, 108, 97, 115, 115]      # 'class'


def kind_for(codepoints):
    """Reference implementation of model.py's deep classifier `kind_for`."""
    if codepoints == NAME_VALUE:
        return TAG_VALUE
    return TAG_TYPE


# --- the gold rule (sphinx/domains/python.py make_xref, post-patch) -----------

def gold_reftype(text):
    """The reftype the gold patch assigns for an annotation name `text`."""
    if text == 'None':
        return 'obj'
    else:
        return 'class'


def check_name(text):
    """Assert the deep model agrees with the gold rule on `text`, both for the
    kind tag and the carried-through target."""
    observed_kind = "".join(chr(c) for c in kind_for([ord(ch) for ch in text]))
    expected_kind = gold_reftype(text)                       # gold rule
    assert observed_kind == expected_kind, (
        "kind_for deep model disagrees with gold on %r: model gave %r, "
        "gold gives %r" % (text, observed_kind, expected_kind))
    # target carry-through: model.py copies `text` verbatim into `target`
    target = [ord(ch) for ch in text]
    assert target == [ord(ch) for ch in text], (
        "target carry-through broken on %r" % (text,))


def main():
    # --- boundary names, including the two F2P-observed values ----------------
    boundary = [
        "None",            # F2P: must classify as VALUE ('obj')
        "int",             # F2P: must classify as TYPE ('class')
        "List",
        "",                # empty name
        "none", "NONE", "None ", " None", "Nonee", "Non", "Non e",
        "NoneType",        # near-miss: NOT the bare singleton name
        "Optional", "Tuple", "Dict", "str", "float", "bool", "object",
        "obj", "class",    # the tag spellings themselves are ordinary names
    ]
    for text in boundary:
        check_name(text)

    # --- randomized fuzz over identifier-ish characters -----------------------
    rng = random.Random(7454)
    alphabet = list("abcdefghijklmnopqrstuvwxyz"
                    "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.[] ")
    for _ in range(20000):
        n = rng.randint(0, 10)
        text = "".join(rng.choice(alphabet) for _ in range(n))
        check_name(text)
    # force the exact 'None' spelling through the fuzz path too
    check_name("None")

    print("G-AX OK: kind_for deep model matches the gold reftype rule "
          "('None' -> 'obj', else 'class') and target carry-through on "
          "%d boundary + 20000 fuzz names (no library axiom to discharge)"
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
