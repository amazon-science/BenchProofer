"""Twin-artifact model for sphinx-doc__sphinx-9281.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single routine produces a human-readable textual description of an
  arbitrary value, dispatching on the value's category:

    * a key/value mapping, an unordered collection, and an immutable
      unordered collection each have their own established rendering;
    * a member of an enumerated type is rendered as its owning type's name,
      a single dot, then the member's own name -- e.g. the member ``FOO`` of
      enumerated type ``MyEnum`` renders as the code points of ``MyEnum.FOO``
      -- so the rendering is a stable, re-usable reference to the member
      rather than the value-revealing fallback text;
    * every other value falls back to its generic textual form.

  The categories are mutually exclusive: at most one rendering rule applies,
  and a value that is a member of an enumerated type takes the enumerated-type
  rule, never the generic fallback.

Values are modelled as a minimal object carrying a category tag plus the
relevant text fragments as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing). The category tag is an integer:

    0 = mapping, 1 = collection, 2 = immutable collection,
    3 = enumerated-type member, 4 = any other value.

The owning-type name and the member name are the two fragments the
enumerated-type rendering composes; the renderings of the other categories and
the generic fallback are carried as opaque code-point sequences, since those
rules are unchanged by this behaviour. The pure sequence theory ``PSeq[int]``
carries the specification.

Producing the description is a bounded computation over the finitely many code
points of the relevant fragments: it MUST terminate and return its rendered
text (a total-correctness obligation, carried as MustTerminate in the
precondition). An implementation that diverges before returning would satisfy
the value postconditions only vacuously and would never deliver the rendering.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Value:
    def __init__(self, kind: int, class_name: List[int], member_name: List[int],
                 category_text: List[int], fallback_text: List[int]) -> None:
        Requires(Acc(list_pred(class_name), 1 / 2))
        Requires(Acc(list_pred(member_name), 1 / 2))
        Requires(Acc(list_pred(category_text), 1 / 2))
        Requires(Acc(list_pred(fallback_text), 1 / 2))
        Ensures(Acc(self.kind) and self.kind == kind)  # type: ignore
        Ensures(Acc(self.class_name) and self.class_name is class_name)  # type: ignore
        Ensures(Acc(self.member_name) and self.member_name is member_name)  # type: ignore
        Ensures(Acc(self.category_text) and self.category_text is category_text)  # type: ignore
        Ensures(Acc(self.fallback_text) and self.fallback_text is fallback_text)  # type: ignore
        Ensures(Acc(list_pred(class_name), 1 / 2))
        Ensures(Acc(list_pred(member_name), 1 / 2))
        Ensures(Acc(list_pred(category_text), 1 / 2))
        Ensures(Acc(list_pred(fallback_text), 1 / 2))
        self.kind = kind
        self.class_name = class_name
        self.member_name = member_name
        self.category_text = category_text
        self.fallback_text = fallback_text


# axioms-start
# (no consumed @ContractOnly axioms: the renderings of the unchanged
# categories and the generic fallback are carried as opaque sequences on the
# value object; the enumerated-type composition is modelled deeply below.)
# axioms-end


# pure-start
@Pure
def dot() -> PSeq[int]:
    # the single separator code point U+002E '.'
    return PSeq(46)


@Pure
def enum_rendering(class_name: PSeq[int], member_name: PSeq[int]) -> PSeq[int]:
    """The rendering of an enumerated-type member: the owning type's name, a
    dot, then the member's name."""
    return class_name + dot() + member_name
# pure-end


def describe(value: Value) -> List[int]:
    # pre-conditions-start
    Requires(Acc(value.kind, 1 / 2))  # type: ignore
    Requires(Acc(value.class_name, 1 / 2))  # type: ignore
    Requires(Acc(value.member_name, 1 / 2))  # type: ignore
    Requires(Acc(value.category_text, 1 / 2))  # type: ignore
    Requires(Acc(value.fallback_text, 1 / 2))  # type: ignore
    Requires(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
    Requires(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
    Requires(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
    Requires(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
    # TERMINATION: the rendering must actually ANSWER — copying/composing the
    # finitely many code points of the relevant fragments is a bounded
    # computation. Nagini is a partial-correctness verifier by default, so
    # without this obligation a non-terminating implementation (an endless
    # loop before the return) satisfies every value postcondition vacuously
    # while sharing the spec; the real routine always returns its rendered
    # text.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(value.kind, 1 / 2))  # type: ignore
    Ensures(Acc(value.class_name, 1 / 2))  # type: ignore
    Ensures(Acc(value.member_name, 1 / 2))  # type: ignore
    Ensures(Acc(value.category_text, 1 / 2))  # type: ignore
    Ensures(Acc(value.fallback_text, 1 / 2))  # type: ignore
    Ensures(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
    Ensures(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
    Ensures(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
    Ensures(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
    Ensures(Acc(list_pred(Result())))
    # A member of an enumerated type (tag 3) is rendered as
    # owning-type-name "." member-name, NOT by the generic fallback rendering.
    Ensures(Implies(value.kind == 3,  # type: ignore
                    ToSeq(Result()) == enum_rendering(ToSeq(value.class_name),  # type: ignore
                                                      ToSeq(value.member_name))))  # type: ignore
    # The three established collection-style renderings (tags 0/1/2) are unchanged.
    Ensures(Implies(value.kind == 0,  # type: ignore
                    ToSeq(Result()) == ToSeq(value.category_text)))  # type: ignore
    Ensures(Implies(value.kind == 1,  # type: ignore
                    ToSeq(Result()) == ToSeq(value.category_text)))  # type: ignore
    Ensures(Implies(value.kind == 2,  # type: ignore
                    ToSeq(Result()) == ToSeq(value.category_text)))  # type: ignore
    # Any other value (tag 4) falls back to its generic textual form.
    Ensures(Implies(value.kind == 4,  # type: ignore
                    ToSeq(Result()) == ToSeq(value.fallback_text)))  # type: ignore
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if value.kind == 0 or value.kind == 1 or value.kind == 2:  # type: ignore
        i = 0
        while i < len(value.category_text):  # type: ignore
            # invariants-start
            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(result)))
            Invariant(value.kind == 0 or value.kind == 1 or value.kind == 2)  # type: ignore
            Invariant(0 <= i and i <= len(value.category_text))  # type: ignore
            Invariant(ToSeq(result) == ToSeq(value.category_text).take(i))  # type: ignore
            # The loop consumes the termination obligation: the remaining
            # count is the strictly decreasing, bounded-below measure.
            Invariant(MustTerminate(len(value.category_text) - i))  # type: ignore
            # invariants-end
            result.append(value.category_text[i])  # type: ignore
            i = i + 1
        Assert(i == len(value.category_text))  # type: ignore
        Assert(ToSeq(value.category_text).take(i) == ToSeq(value.category_text))  # type: ignore
        return result
    else:
        # PRE-PATCH dispatch: there is NO enumerated-type branch, so a member
        # of an enumerated type (tag 3) falls through to the generic textual
        # form together with every other value.
        i = 0
        while i < len(value.fallback_text):  # type: ignore
            # invariants-start
            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(result)))
            Invariant(value.kind != 0 and value.kind != 1 and  # type: ignore
                      value.kind != 2)  # type: ignore
            Invariant(0 <= i and i <= len(value.fallback_text))  # type: ignore
            Invariant(ToSeq(result) == ToSeq(value.fallback_text).take(i))  # type: ignore
            # The loop consumes the termination obligation: the remaining
            # count is the strictly decreasing, bounded-below measure.
            Invariant(MustTerminate(len(value.fallback_text) - i))  # type: ignore
            # invariants-end
            result.append(value.fallback_text[i])  # type: ignore
            i = i + 1
        Assert(i == len(value.fallback_text))  # type: ignore
        Assert(ToSeq(value.fallback_text).take(i) == ToSeq(value.fallback_text))  # type: ignore
        return result
    # impl-end
