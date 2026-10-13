"""Twin-artifact model for matplotlib__matplotlib-25287.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a secondary annotation that accompanies an axis derives its foreground
  colour from configuration, the colour it should take is the explicitly
  configured label colour. The configured label colour may carry a distinguished
  sentinel value meaning "do not override; defer to the base colour"; in that
  one case, and only that case, the base colour is used instead.

  Formally, for two configured colour values `base_color` and `label_color`
  (each a sequence of code points naming a colour), the effective colour of the
  derived annotation is:

      effective(base_color, label_color)
        = base_color              if label_color is the sentinel `inherit`
        = label_color             otherwise

This rule is applied at two independent configuration sites that differ only in
which pair of base/label colour values they read; both are modelled, each as its
own contracted function, because each is independently observable.

Colour names are modelled as `List[int]` of code points (Nagini bans `str`
indexing); the sentinel `inherit` is the constant code-point sequence for that
word. The result is a fresh sequence whose contents equal the chosen input's
contents. There are no axiomatized callees: the selection is expressed directly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def sentinel_inherit() -> PSeq[int]:
    # the code points of the word that means "defer to the base colour"
    # i n h e r i t
    return PSeq(105, 110, 104, 101, 114, 105, 116)


@Pure
def effective_color(base_color: PSeq[int], label_color: PSeq[int]) -> PSeq[int]:
    """The colour the derived annotation should take: the explicit label colour,
    except when the label colour is the sentinel, in which case the base
    colour."""
    if label_color == sentinel_inherit():
        return base_color
    return label_color
# pure-end


def offset_color_primary(base_color: List[int], label_color: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base_color), 1 / 2))
    Requires(Acc(list_pred(label_color), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base_color), 1 / 2))
    Ensures(Acc(list_pred(label_color), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The chosen colour is the label colour unless that is the sentinel, in
    # which case it is the base colour.
    Ensures(ToSeq(Result()) == effective_color(ToSeq(base_color), ToSeq(label_color)))
    Ensures(Implies(ToSeq(label_color) == sentinel_inherit(),
                    ToSeq(Result()) == ToSeq(base_color)))
    Ensures(Implies(ToSeq(label_color) != sentinel_inherit(),
                    ToSeq(Result()) == ToSeq(label_color)))
    # post-conditions-end
    # impl-start
    if ToSeq(label_color) == sentinel_inherit():
        tick_color = list(base_color)  # type: List[int]
    else:
        tick_color = list(label_color)
    return tick_color
    # impl-end


def offset_color_secondary(base_color: List[int], label_color: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base_color), 1 / 2))
    Requires(Acc(list_pred(label_color), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base_color), 1 / 2))
    Ensures(Acc(list_pred(label_color), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == effective_color(ToSeq(base_color), ToSeq(label_color)))
    Ensures(Implies(ToSeq(label_color) == sentinel_inherit(),
                    ToSeq(Result()) == ToSeq(base_color)))
    Ensures(Implies(ToSeq(label_color) != sentinel_inherit(),
                    ToSeq(Result()) == ToSeq(label_color)))
    # post-conditions-end
    # impl-start
    # pre-patch skeleton (secondary site): the derived annotation always takes
    # the base colour, never the configured label colour. Fails whenever the
    # label colour is not the sentinel.
    tick_color = list(base_color)  # type: List[int]
    return tick_color
    # impl-end
