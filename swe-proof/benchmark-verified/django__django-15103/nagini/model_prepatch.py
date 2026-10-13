"""Twin-artifact model for django__django-15103.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A serialized JSON payload is wrapped in an HTML ``<script>`` element of media
  type ``application/json``. The element's identifying attribute is OPTIONAL:

    * When an identifier is supplied (a present, non-empty token), the opening
      tag carries that identifier as an ``id`` attribute, immediately followed
      by the media-type attribute, then the payload, then the closing tag.

    * When no identifier is supplied (absent, or an empty token), the opening
      tag carries ONLY the media-type attribute — the ``id`` attribute and its
      value are absent from the output entirely — followed by the payload and
      the closing tag.

  In both cases the wrapped payload is identical (the same already-serialized
  character sequence); only the presence/absence of the identifying attribute
  differs. The two outputs share the common prefix ``<script`` and the common
  suffix `` type="application/json">`` + payload + ``</script>``.

Wrapping is a bounded, straight-line assembly: the operation MUST terminate
and return the wrapped element (a total-correctness obligation, carried as
MustTerminate in the precondition). An implementation that diverges before
returning would satisfy the value postconditions only vacuously and would
never deliver the rendered markup to the caller.

Character data is modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried over ``PSeq[int]``. The optional
identifier is modelled as ``Optional[List[int]]`` (absent identifier == ``None``;
an empty list models an empty token, which is likewise treated as absent).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized callees: the modelled behaviour is the conditional assembly of
# constant markup around an already-serialized payload. Payload serialization
# and HTML attribute encoding are unchanged callees, not part of the modelled
# operation; see refinement.md / mapping.md.)
# axioms-end


# pure-start
@Pure
def tag_open_with_id() -> PSeq[int]:
    # '<script id="'
    return PSeq(60, 115, 99, 114, 105, 112, 116, 32, 105, 100, 61, 34)


@Pure
def attr_close_and_type() -> PSeq[int]:
    # '" type="application/json">'
    return PSeq(34, 32, 116, 121, 112, 101, 61, 34, 97, 112, 112, 108,
                105, 99, 97, 116, 105, 111, 110, 47, 106, 115, 111, 110, 34, 62)


@Pure
def tag_open_no_id() -> PSeq[int]:
    # '<script type="application/json">'
    return PSeq(60, 115, 99, 114, 105, 112, 116, 32, 116, 121, 112, 101,
                61, 34, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 106, 115, 111, 110, 34, 62)


@Pure
def tag_close() -> PSeq[int]:
    # '</script>'
    return PSeq(60, 47, 115, 99, 114, 105, 112, 116, 62)


@Pure
def prefix_with_id(ident: List[int]) -> PSeq[int]:
    """The opening-tag prefix WHEN an identifier is present: the id-bearing
    opening tag carries the identifier as an id attribute, then the media-type
    attribute."""
    Requires(Acc(list_pred(ident), 1 / 4))
    Ensures(Result() == tag_open_with_id() + ToSeq(ident) + attr_close_and_type())
    return tag_open_with_id() + ToSeq(ident) + attr_close_and_type()
# pure-end


def build_json_script(payload: List[int], element_id: Optional[List[int]]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(payload), 1 / 2))
    Requires(Implies(element_id is not None, Acc(list_pred(element_id), 1 / 2)))
    # Wrapping is a bounded, straight-line assembly: the operation MUST
    # terminate and return the wrapped element (total correctness). A
    # diverging implementation would satisfy the value postconditions only
    # vacuously and would never deliver the rendered markup to the caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(payload), 1 / 2))
    Ensures(Implies(element_id is not None, Acc(list_pred(element_id), 1 / 2)))
    Ensures(Acc(list_pred(Result())))
    # An identifier counts as present iff it is supplied and non-empty; an empty
    # token is treated the same as an absent one.
    # When present: the output is the id-bearing opening tag (carrying the
    # identifier before the media-type), then the payload, then the closing tag.
    Ensures(Implies(
        element_id is not None and len(element_id) > 0,
        ToSeq(Result()) == prefix_with_id(element_id) + ToSeq(payload) + tag_close()))
    # When absent (or empty): the output is the opening tag carrying ONLY the
    # media-type attribute (the id attribute is absent entirely), then the
    # payload, then the closing tag.
    Ensures(Implies(
        element_id is None or len(element_id) == 0,
        ToSeq(Result()) == tag_open_no_id() + ToSeq(payload) + tag_close()))
    # post-conditions-end
    # impl-start
    # PRE-PATCH SKELETON (buggy): the opening tag ALWAYS carries the id
    # attribute, with whatever identifier was supplied (an absent identifier
    # renders as an empty id value). There is no branch that omits the id
    # attribute, so the no-identifier output is the id-bearing tag rather than
    # the id-free one demanded by the specification.
    result = [60, 115, 99, 114, 105, 112, 116, 32, 105, 100, 61, 34]  # type: List[int]
    Assert(ToSeq(result) == tag_open_with_id())
    prefix = tag_open_with_id()  # type: PSeq[int]
    if element_id is not None:
        i = 0
        while i < len(element_id):
            # invariants-start
            Invariant(Acc(list_pred(element_id), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(element_id))
            Invariant(ToSeq(result) == tag_open_with_id() + ToSeq(element_id).take(i))
            # the copy loop consumes the caller's termination obligation with a
            # strictly decreasing measure (len(element_id) - i), discharging
            # MustTerminate(2) from the precondition.
            Invariant(MustTerminate(len(element_id) - i + 1))
            # invariants-end
            result.append(element_id[i])
            i = i + 1
        Assert(ToSeq(element_id).take(len(element_id)) == ToSeq(element_id))
        Assert(ToSeq(result) == tag_open_with_id() + ToSeq(element_id))
        prefix = tag_open_with_id() + ToSeq(element_id)
    Assert(ToSeq(result) == prefix)
    result = result + [34, 32, 116, 121, 112, 101, 61, 34, 97, 112, 112,
                       108, 105, 99, 97, 116, 105, 111, 110, 47, 106, 115,
                       111, 110, 34, 62]
    Assert(ToSeq(result) == prefix + attr_close_and_type())
    base = prefix + attr_close_and_type()  # type: PSeq[int]
    # append the payload, then the closing tag
    j = 0
    while j < len(payload):
        # invariants-start
        Invariant(Acc(list_pred(payload), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(payload))
        Invariant(ToSeq(result) == base + ToSeq(payload).take(j))
        # payload copy loop: strictly decreasing measure (len(payload) - j)
        # discharges MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(payload) - j + 1))
        # invariants-end
        result.append(payload[j])
        j = j + 1
    Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
    result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
    Assert(ToSeq(result) == base + ToSeq(payload) + tag_close())
    return result
    # impl-end
