"""Twin-artifact model for django__django-11964.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An enumerated-choice member carries two pieces of textual identity:

    * the textual rendering of its underlying VALUE (e.g. the choice value
      "first" of a text choice, or the decimal "1" of an integer choice), and

    * a default, diagnostic qualified label of the form "Owner.NAME" naming the
      member within its enumeration.

  When such a member is rendered to text for ordinary use — i.e. coerced to a
  string for templates, persistence and outbound payloads — the result MUST be
  the rendering of the member's VALUE, character for character, and NOT the
  diagnostic "Owner.NAME" label. Concretely, coercing a member to text yields a
  sequence of characters equal to the textual rendering of that member's value.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]` via `ToSeq`. The member
is a minimal read-only object exposing only the two touched character
sequences. No callee is axiomatized: the rendering is the member's own value
text, modelled deeply as an element-for-element copy. The textual coercion of
the value itself (the standard string coercion) is validated against its real
Python semantics out-of-band by axiom_check.py (G-AX) as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The rendering returns the member's own value text, which
# is modelled deeply as an element-for-element copy of the value's character
# sequence. The standard string coercion that produces that value text from the
# underlying value (decimal digits for an integer value, the characters
# themselves for a text value) is an A-reference: it is validated equal to real
# Python str() out-of-band by axiom_check.py (G-AX), not consumed here.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class Member:
    def __init__(self) -> None:
        Ensures(Acc(self.value_text) and Acc(list_pred(self.value_text)))  # type: ignore
        Ensures(len(self.value_text) == 0)  # type: ignore
        Ensures(Acc(self.qualified_label) and Acc(list_pred(self.qualified_label)))  # type: ignore
        Ensures(len(self.qualified_label) == 0)  # type: ignore
        # value_text: the textual rendering of the member's underlying value.
        self.value_text = []  # type: List[int]
        # qualified_label: the diagnostic "Owner.NAME" rendering of the member.
        self.qualified_label = []  # type: List[int]


def render_to_text(self: Member) -> List[int]:
    # pre-conditions-start
    # The member is read-only: both of its character sequences are required
    # (and ensured) only at fractional permission, so a rendering that mutated
    # the member to satisfy its postcondition vacuously is rejected.
    Requires(Acc(self.value_text, 1 / 2) and Acc(list_pred(self.value_text), 1 / 2))
    Requires(Acc(self.qualified_label, 1 / 2) and Acc(list_pred(self.qualified_label), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # The member is left exactly as it was (returned at the same fractional
    # permission, with the same contents).
    Ensures(Acc(self.value_text, 1 / 2) and Acc(list_pred(self.value_text), 1 / 2))
    Ensures(Acc(self.qualified_label, 1 / 2) and Acc(list_pred(self.qualified_label), 1 / 2))
    Ensures(len(self.value_text) == Old(len(self.value_text)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.value_text),
                                            self.value_text[k] == Old(self.value_text[k])))))
    Ensures(len(self.qualified_label) == Old(len(self.qualified_label)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.qualified_label),
                                            self.qualified_label[k] == Old(self.qualified_label[k])))))

    # The result is a freshly owned character sequence.
    Ensures(Acc(list_pred(Result())))
    # The discriminating guarantee: the rendered text equals the member's VALUE
    # text, character for character — NOT the diagnostic "Owner.NAME" label.
    Ensures(ToSeq(Result()) == ToSeq(self.value_text))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: the default member rendering produces the diagnostic
    # "Owner.NAME" qualified label rather than the member's value text.
    result = []  # type: List[int]
    i = 0
    while i < len(self.qualified_label):
        # invariants-start
        Invariant(Acc(self.value_text, 1 / 2) and Acc(list_pred(self.value_text), 1 / 2))
        Invariant(Acc(self.qualified_label, 1 / 2) and Acc(list_pred(self.qualified_label), 1 / 2))
        Invariant(len(self.value_text) == Old(len(self.value_text)))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.value_text),
                                                  self.value_text[k] == Old(self.value_text[k])))))
        Invariant(len(self.qualified_label) == Old(len(self.qualified_label)))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.qualified_label),
                                                  self.qualified_label[k] == Old(self.qualified_label[k])))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(self.qualified_label))
        Invariant(len(result) == i)
        Invariant(ToSeq(result) == ToSeq(self.qualified_label).take(i))
        # invariants-end
        result.append(self.qualified_label[i])
        i = i + 1
    return result
    # impl-end
