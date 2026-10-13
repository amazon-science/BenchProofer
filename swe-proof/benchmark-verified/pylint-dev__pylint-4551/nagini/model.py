"""Twin-artifact model for pylint-dev__pylint-4551.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a diagram renders the declared type of an attribute or parameter, it
  must derive a textual type label from the declaration's type annotation and
  then make that label honest about an absent value:

    (1) The textual label of a type annotation is the annotation rendered as
        text. A bare name annotation contributes its name; a subscripted
        annotation (a parametrised generic) contributes its full source text;
        anything else contributes the empty label.

    (2) When the declaration actually carries a declared type, the declared
        default for the value is the absent value (None), AND the textual label
        does not already announce optionality (it does not begin with the
        prefix "Optional"), the label is wrapped to announce optionality: it
        becomes the prefix "Optional", an opening bracket, the original label,
        and a closing bracket.

    (3) In every other case the label is left exactly as derived in (1): a
        present (non-absent) default, OR a label that already begins with
        "Optional", OR a declaration that carries no declared type at all.
        The last case is not an oversight but the point: with nothing declared
        there is no declared type to make honest, so this step announces
        nothing about optionality and contributes the label unchanged. Whether
        a declared type is present is therefore an input the decision reads,
        not something derivable from the label text: a declaration with no
        declared type and one whose declared type renders as no text both
        present the empty label, yet only the latter may be announced optional.

The label is a piece of text, modelled as a `List[int]` of Unicode code points
(carrier) with the specification carried by `PSeq[int]` (Nagini bans `str`
indexing). The "begins with Optional" test is a prefix comparison over the
sequence; the optional-wrapping is a deep, spelled-out concatenation with a
matching verified construction loop -- it is the behaviour under specification,
not an axiom. No library callee is consumed: the rendering of an annotation to
its text (a name's name, a subscript's source text) is validated out-of-band
by axiom_check.py (G-AX) as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# Code points of the word "Optional" and the bracket pair used to wrap a label.
OPT_O = 79   # 'O'
OPT_p = 112  # 'p'
OPT_t = 116  # 't'
OPT_i = 105  # 'i'
OPT_o = 111  # 'o'
OPT_n = 110  # 'n'
OPT_a = 97   # 'a'
OPT_l = 108  # 'l'
LBRACK = 91  # '['
RBRACK = 93  # ']'


# axioms-start
# No consumed axioms. The annotation-to-text rendering (a name's name, a
# subscript's source text) and the optional-wrapping decision ARE the behaviour
# under specification and are modelled deeply (the pure helpers below + the impl
# loop spell them out). The rendering of an annotation node to its text is the
# only library behaviour relied on; it is validated out-of-band by
# axiom_check.py (G-AX) as an A-reference, not consumed as an axiom.
# axioms-end


# pure-start
@Pure
def optional_prefix() -> PSeq[int]:
    """The eight code points of the literal prefix word "Optional"."""
    Ensures(len(Result()) == 8)
    return PSeq(OPT_O, OPT_p, OPT_t, OPT_i, OPT_o, OPT_n, OPT_a, OPT_l)


@Pure
def starts_with_optional(s: PSeq[int]) -> bool:
    """True iff the label text already begins with the prefix "Optional"."""
    return len(s) >= 8 and s.take(8) == optional_prefix()


@Pure
def wrap_optional(base: PSeq[int]) -> PSeq[int]:
    """The optionality-announcing wrap of a label: the prefix "Optional", an
    opening bracket, the original label, a closing bracket."""
    return optional_prefix() + PSeq(LBRACK) + base + PSeq(RBRACK)


@Pure
def label_for(base: PSeq[int], default_is_none: bool,
              declared_type_present: bool) -> PSeq[int]:
    """The final label per (2)/(3): wrap to announce optionality exactly when a
    declared type is present, the default is the absent value, and the label
    does not already begin with "Optional"; otherwise the label is unchanged."""
    if declared_type_present and default_is_none and not starts_with_optional(base):
        return wrap_optional(base)
    return base
# pure-end


def annotation_label(base: List[int], default_is_none: bool,
                     declared_type_present: bool) -> List[int]:
    """Compute the final, honest type label from the declaration's textual type
    label `base` (per (1)), whether the declared default is the absent value,
    and whether the declaration carries a declared type at all.

    `base` is the text already derived from the declared type (a bare name's
    name, or a subscript's source text); see refinement.md / mapping.md for the
    node->text rendering it stands for (an A-reference checked by G-AX). A
    declaration with no declared type carries no such text, and per (3) it is
    announced nothing -- which is why `declared_type_present` is read
    separately from the label rather than inferred from it."""
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    # Deriving the label must COMPLETE: it is a finite computation over a
    # finite piece of text, so it always reaches an answer and never runs
    # forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the optional-wrap decision over the input label.
    Ensures(ToSeq(Result()) == label_for(ToSeq(base), default_is_none,
                                     declared_type_present))
    # Spelled-out consequences of that decision: when wrapping fires, the
    # result is strictly the four pieces in order, longer than the label by the
    # ten wrapper code points ("Optional" is eight, plus "[" and "]"), begins
    # with "Optional[" and ends with "]"; otherwise the result is the label
    # itself.
    Ensures(Implies(
        declared_type_present and default_is_none
        and not starts_with_optional(ToSeq(base)),
        ToSeq(Result()) == optional_prefix() + PSeq(LBRACK)
                            + ToSeq(base) + PSeq(RBRACK)))
    Ensures(Implies(
        declared_type_present and default_is_none
        and not starts_with_optional(ToSeq(base)),
        len(Result()) == len(base) + 10
        and ToSeq(Result()).take(8) == optional_prefix()
        and ToSeq(Result())[8] == LBRACK
        and ToSeq(Result())[len(Result()) - 1] == RBRACK
        and ToSeq(Result()).take(len(Result()) - 1).drop(9) == ToSeq(base)))
    Ensures(Implies(
        not (declared_type_present and default_is_none
             and not starts_with_optional(ToSeq(base))),
        ToSeq(Result()) == ToSeq(base)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
