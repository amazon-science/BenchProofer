"""Twin-artifact model for sphinx-doc__sphinx-7454.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a single textual type name appearing in a parsed type annotation is
  turned into a resolvable cross-reference, the reference must carry two
  pieces of information derived from that text:

    (1) its TARGET is exactly the text itself (the name being referred to is
        carried through unchanged), and

    (2) its REFERENCE KIND distinguishes the singleton value name from an
        ordinary type name. The text consisting of the four code points of the
        singleton value name (capital-N, lower-o, lower-n, lower-e) is
        classified as a VALUE reference; every other text is classified as a
        TYPE reference. The two kinds are distinct constant tags, so a value
        name and a type name of identical spelling would still be classified
        differently — but here the spelling itself decides the kind.

  This makes the singleton value name resolve like the other built-in names
  occurring in signatures, rather than being treated as an ordinary type and
  failing to resolve.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); a cross-reference is a minimal object exposing only the two touched
fields (its kind tag and its target). The two constant kind tags and the
discriminating name are spelled out deeply as code-point sequences; no callee
is axiomatized (the classification is pure structure logic).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the classification of a name into a reference-kind tag
# and the carry-through of the target are pure structure logic, modelled
# deeply over `List[int]` code points. The constructor of the cross-reference
# node is unchanged by the behaviour under specification.
# axioms-end


# pure-start
@Pure
def name_value() -> PSeq[int]:
    # the singleton value name, as Unicode code points
    return PSeq(78, 111, 110, 101)


@Pure
def tag_value() -> PSeq[int]:
    # the constant kind tag for a value reference, as Unicode code points
    return PSeq(111, 98, 106)


@Pure
def tag_type() -> PSeq[int]:
    # the constant kind tag for an ordinary type reference, as code points
    return PSeq(99, 108, 97, 115, 115)


@Pure
def kind_for(text: PSeq[int]) -> PSeq[int]:
    """The reference-kind tag for a name: the value tag exactly when the name
    is the singleton value name, the type tag otherwise."""
    if text == name_value():
        return tag_value()
    return tag_type()
# pure-end


class CrossReference:
    def __init__(self) -> None:
        Ensures(Acc(self.kind) and Acc(list_pred(self.kind)))      # type: ignore
        Ensures(Acc(self.target) and Acc(list_pred(self.target)))  # type: ignore
        Ensures(ToSeq(self.kind) == PSeq(0).take(0))               # type: ignore
        Ensures(ToSeq(self.target) == PSeq(0).take(0))             # type: ignore
        self.kind = []    # type: List[int]
        self.target = []  # type: List[int]


def make_cross_reference(text: List[int]) -> CrossReference:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(Result().kind) and Acc(list_pred(Result().kind)))      # type: ignore
    Ensures(Acc(Result().target) and Acc(list_pred(Result().target)))  # type: ignore
    # The reference carries the name through unchanged as its target.
    Ensures(ToSeq(Result().target) == ToSeq(text))                     # type: ignore
    # The reference kind is the value tag exactly when the name is the
    # singleton value name, and the type tag otherwise.
    Ensures(ToSeq(Result().kind) == kind_for(ToSeq(text)))             # type: ignore
    # Spelled out so the discriminating value/type split is pinned directly:
    Ensures(Implies(ToSeq(text) == name_value(),
                    ToSeq(Result().kind) == tag_value()))             # type: ignore
    Ensures(Implies(ToSeq(text) != name_value(),
                    ToSeq(Result().kind) == tag_type()))              # type: ignore
    # post-conditions-end
    # impl-start
    ref = CrossReference()
    target = []  # type: List[int]
    i = 0
    while i < len(text):
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(target)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(target) == ToSeq(text).take(i))
        # invariants-end
        target = target + [text[i]]
        i = i + 1
    Assert(ToSeq(text).take(len(text)) == ToSeq(text))
    ref.target = target
    if ToSeq(text) == name_value():
        ref.kind = [111, 98, 106]
    else:
        ref.kind = [99, 108, 97, 115, 115]
    return ref
    # impl-end
