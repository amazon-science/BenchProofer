"""Twin-artifact model for django__django-14608.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection of validation messages that are not attached to any individual
  member of a group renders with a marker tag in addition to the generic list
  tag, so a custom renderer can tell these group-wide messages apart from the
  per-member ones. Concretely, after the group's whole-clean step finishes, the
  collection holding those group-wide messages carries the rendered class
  attribute "errorlist nonform" (the generic class "errorlist" followed by the
  marker "nonform"), instead of the bare "errorlist".

  This holds on EVERY outcome of the whole-clean step. The held messages are
  exactly those the step produces:
    (1) the step accepts the data and nothing flagged the group as a whole:
        the collection stays empty;
    (2) the step accepts the data but the group as a whole was flagged once
        before the acceptance check: the collection holds exactly that single
        group-wide message;
    (3) the step rejects the data: the collection is rebuilt to carry exactly
        the rejection messages (replacing any earlier group-wide message).
  In every case the rendered class attribute is "errorlist nonform".

The message collection is modelled as a minimal class carrying only the two
touched, observable fields: its rendered class attribute and its held items,
both as `List[int]` of Unicode code points. The unchanged collection
constructor's rule for the class attribute — no marker tag yields the generic
class, a marker tag `t` yields the generic class, a space, then `t` — is
modelled deeply by the pure function `class_attr`, validated equal to the real
constructor out-of-band by axiom_check.py (G-AX), NOT consumed as an axiom.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class MessageCollection:
    def __init__(self, css_class: List[int], items: List[int]) -> None:
        Requires(Acc(list_pred(css_class)))
        Requires(Acc(list_pred(items)))
        Ensures(Acc(self.css_class) and self.css_class is css_class)  # type: ignore
        Ensures(Acc(self.items) and self.items is items)  # type: ignore
        self.css_class = css_class
        self.items = items


# axioms-start
# (no consumed @ContractOnly axioms: the only callee whose behaviour the proof
#  relies on — the collection constructor's class-attribute rule — is modelled
#  DEEPLY by the pure function `class_attr` below and validated == the real
#  constructor out-of-band by axiom_check.py / G-AX, so it is an A-reference,
#  not an A-consumed axiom.)
# axioms-end


# pure-start
@Pure
def generic_class() -> PSeq[int]:
    # 'errorlist' — the generic list class every such collection carries.
    return PSeq(101, 114, 114, 111, 114, 108, 105, 115, 116)


@Pure
def nonform_tag() -> PSeq[int]:
    # 'nonform' — the marker tag distinguishing group-wide messages.
    return PSeq(110, 111, 110, 102, 111, 114, 109)


@Pure
def class_attr(tag: PSeq[int]) -> PSeq[int]:
    """The rendered class attribute the collection constructor produces from an
    optional marker tag: an empty tag yields just the generic class; a non-empty
    tag `t` yields the generic class, a single space (U+0020), then `t`."""
    if len(tag) == 0:
        return generic_class()
    return generic_class() + PSeq(32) + tag
# pure-end


def finish_group_clean(collection: MessageCollection,
                       group_flagged: bool,
                       group_message: int,
                       rejected: bool,
                       rejection_messages: List[int]) -> None:
    # pre-conditions-start
    Requires(Acc(collection.css_class))
    Requires(Acc(collection.items))
    Requires(Acc(list_pred(rejection_messages), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(collection.css_class))
    Ensures(Acc(collection.items))
    Ensures(Acc(list_pred(rejection_messages), 1 / 2))
    Ensures(Acc(list_pred(collection.css_class)))
    Ensures(Acc(list_pred(collection.items)))
    # The collection's rendered class attribute carries the marker tag in
    # addition to the generic class, on EVERY outcome of the whole-clean step.
    Ensures(ToSeq(collection.css_class) == class_attr(nonform_tag()))
    # The held messages are exactly the step's product:
    #   - not rejected and nothing flagged the group as a whole: empty;
    #   - not rejected but the group as a whole was flagged once before the
    #     rejection check: exactly that single group-wide message;
    #   - rejected: exactly the rejection messages (the rebuild replaces any
    #     earlier group-wide message).
    Ensures(Implies(not rejected and not group_flagged,
                    len(collection.items) == 0))
    Ensures(Implies(not rejected and group_flagged,
                    ToSeq(collection.items) == PSeq(group_message)))
    Ensures(Implies(rejected,
                    ToSeq(collection.items) == ToSeq(rejection_messages)))
    # post-conditions-end
    # impl-start
    # init site: rebuild the collection empty, with the marker tag.
    empty = []  # type: List[int]
    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
    collection.css_class = init_class
    collection.items = empty
    if group_flagged:
        # a single group-wide message is appended to the collection before the
        # rejection check (the collection is NOT rebuilt here, so the marker
        # class set at the init site is preserved).
        collection.items = collection.items + [group_message]
    if rejected:
        # rejection site: rebuild the collection from the rejection messages,
        # again with the marker tag (this replaces any earlier group-wide
        # message held in the collection).
        items_copy = []  # type: List[int]
        i = 0
        while i < len(rejection_messages):
            # invariants-start
            Invariant(Acc(list_pred(rejection_messages), 1 / 2))
            Invariant(Acc(list_pred(items_copy)))
            Invariant(0 <= i and i <= len(rejection_messages))
            Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
            # invariants-end
            items_copy = items_copy + [rejection_messages[i]]
            i = i + 1
        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
        collection.css_class = rej_class
        collection.items = items_copy
    # impl-end
